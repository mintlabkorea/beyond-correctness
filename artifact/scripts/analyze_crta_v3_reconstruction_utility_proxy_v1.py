#!/usr/bin/env python3
"""Outcome-blind reconstruction proxy for MCR-RL predictive utility.

For every redundancy-ladder cell and rung, reconstruct each supplied
operation column from the exact reduced base frame seen by the free/reference
arm.  Reconstruction is fit on source + target-support rows and evaluated on
held-out target-query rows.  Neither task outcomes nor reference predictions
enter proxy construction.  The resulting mean operation-level R^2 is then
related to the already-computed utility U = nMSE(free) - nMSE(op_true).

This is an exploratory analysis only; it does not edit manuscript sources.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import multiprocessing as mp
import sys
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MCR_RUNNER = ROOT / "scripts/run_crta_v3_mcr_factorial_semisynth_v1.py"
VR_RUNNER = ROOT / "scripts/run_crta_v3_mcr_value_redundancy_v1.py"
RL_RUNNER = ROOT / "scripts/run_crta_v3_mcr_redundancy_ladder_v1.py"
DEFAULT_LADDER_ROOT = ROOT / "experiments/crta_v3_mcr_redundancy_ladder_v1"
DEFAULT_OUT = ROOT / "experiments/crta_v3_reconstruction_utility_proxy_v1"
FROZEN_INPUT_SHA256 = (
    "6af2215c72a65ecc306e5c4d3d9af5b61b16a073dd5aa4c0f33b178741245a25"
)
FAMILIES = ("pairwise", "sparse")
BACKBONES = ("xgb", "histgb")
SUPPORTS = (32, 512)
REALIZATIONS = tuple(range(20))
BOOTSTRAP_REPS = 10000
BOOTSTRAP_SEED = 20260902


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


mcr = _load("mcr_core_recon_proxy", MCR_RUNNER)
vr = _load("mcr_vr_recon_proxy", VR_RUNNER)
rl = _load("mcr_rl_recon_proxy", RL_RUNNER)
PANEL = None
LADDER_ROOT = DEFAULT_LADDER_ROOT
THREADS = 1


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def stable_seed(*parts: Any) -> int:
    digest = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
    return int.from_bytes(digest[:8], "little") % (2**32 - 1)


def reconstruct_r2(
    backbone: str,
    x_fit: np.ndarray,
    op_fit: np.ndarray,
    x_query: np.ndarray,
    op_query: np.ndarray,
    realization: int,
) -> dict[str, Any]:
    """Held-out-target R^2, fit separately and averaged over op columns."""
    per_op = []
    for j in range(op_fit.shape[1]):
        train_ok = np.isfinite(op_fit[:, j])
        query_ok = np.isfinite(op_query[:, j])
        if train_ok.sum() < 100 or query_ok.sum() < 100:
            raise RuntimeError(
                f"insufficient finite rows for op {j}: "
                f"fit={train_ok.sum()}, query={query_ok.sum()}"
            )
        pred = mcr.fit_predict(
            backbone,
            x_fit[train_ok],
            op_fit[train_ok, j],
            np.ones(int(train_ok.sum()), dtype=np.float64),
            x_query[query_ok],
            tuple([0] * x_fit.shape[1]),
            seed=realization,
            threads=THREADS,
        )
        truth = op_query[query_ok, j]
        sse = float(np.sum((truth - pred) ** 2))
        sst = float(np.sum((truth - np.mean(truth)) ** 2))
        if not np.isfinite(sst) or sst <= 0:
            raise RuntimeError(f"degenerate query operation column {j}")
        per_op.append(
            {
                "op_index": j,
                "r2": 1.0 - sse / sst,
                "normalized_mse": sse / sst,
                "n_fit": int(train_ok.sum()),
                "n_query": int(query_ok.sum()),
            }
        )
    r2 = float(np.mean([item["r2"] for item in per_op]))
    return {
        "reconstruction_r2": r2,
        "unreconstructibility": 1.0 - r2,
        "per_operation": per_op,
    }


def analyze_cell(task: tuple[str, int]) -> list[dict[str, Any]]:
    family, realization = task
    if PANEL is None:
        raise RuntimeError("worker panel was not initialized")
    metrics_path = LADDER_ROOT / family / f"r{realization:02d}/metrics.json"
    stored = json.loads(metrics_path.read_text())
    if stored["input_sha256"] != FROZEN_INPUT_SHA256:
        raise RuntimeError(f"wrong input provenance: {metrics_path}")

    cell = mcr.build_cell(PANEL, "primary", family, realization, SUPPORTS)
    rows = []
    for support in SUPPORTS:
        rungs, _y, _weights, info = rl.build_rungs(
            vr, mcr, cell, family, realization, support
        )
        if info["removal_order"] != stored["removal_order"]:
            raise RuntimeError(f"removal-order mismatch: {metrics_path}")
        n_op = int(info["n_op"])
        for backbone in BACKBONES:
            for rung in rungs:
                x_fit, x_query, _ = rung["arms"]["free"]
                x_op_fit, x_op_query, _ = rung["arms"]["op_true"]
                proxy = reconstruct_r2(
                    backbone,
                    x_fit,
                    x_op_fit[:, -n_op:],
                    x_query,
                    x_op_query[:, -n_op:],
                    realization,
                )
                saved_rung = stored["results"][str(support)][backbone][
                    str(rung["k"])
                ]
                utility = (
                    saved_rung["arms"]["free"]["nmse"]
                    - saved_rung["arms"]["op_true"]["nmse"]
                )
                rows.append(
                    {
                        "family": family,
                        "realization": realization,
                        "support": support,
                        "backbone": backbone,
                        "k": int(rung["k"]),
                        "rho_removed": float(rung["rho"]),
                        "n_pairs_broken": int(rung["n_pairs_broken"]),
                        "n_operations": n_op,
                        "n_base_features": int(x_fit.shape[1]),
                        "utility": float(utility),
                        **proxy,
                    }
                )
    return rows


def ols(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    design = np.column_stack([np.ones(len(x)), x])
    coef = np.linalg.lstsq(design, y, rcond=None)[0]
    pred = design @ coef
    sst = float(np.sum((y - np.mean(y)) ** 2))
    sse = float(np.sum((y - pred) ** 2))
    return {
        "intercept": float(coef[0]),
        "slope": float(coef[1]),
        "r2": 1.0 - sse / sst,
        "pearson_r": float(np.corrcoef(x, y)[0, 1]),
    }


def rankdata(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=float)
    ranks[order] = np.arange(len(values), dtype=float)
    unique, inverse, counts = np.unique(
        values, return_inverse=True, return_counts=True
    )
    sums = np.zeros(len(unique), dtype=float)
    np.add.at(sums, inverse, ranks)
    return (sums / counts)[inverse]


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    return float(np.corrcoef(rankdata(x), rankdata(y))[0, 1])


def leave_one_realization_out(
    records: list[dict[str, Any]], field: str
) -> dict[str, float]:
    y = np.asarray([r["utility"] for r in records], dtype=float)
    predictions = np.empty(len(records), dtype=float)
    realizations = np.asarray([r["realization"] for r in records], dtype=int)
    x = np.asarray([r[field] for r in records], dtype=float)
    for held_out in sorted(set(realizations)):
        train = realizations != held_out
        test = ~train
        fit = ols(x[train], y[train])
        predictions[test] = fit["intercept"] + fit["slope"] * x[test]
    sst = float(np.sum((y - np.mean(y)) ** 2))
    sse = float(np.sum((y - predictions) ** 2))
    return {
        "r2": 1.0 - sse / sst,
        "mae": float(np.mean(np.abs(y - predictions))),
        "rmse": float(np.sqrt(np.mean((y - predictions) ** 2))),
        "prediction_correlation": float(np.corrcoef(predictions, y)[0, 1]),
    }


def cluster_bootstrap(
    records: list[dict[str, Any]], field: str, key: str
) -> dict[str, list[float]]:
    clusters = sorted({int(r["realization"]) for r in records})
    by_cluster = {c: [r for r in records if r["realization"] == c] for c in clusters}
    rng = np.random.default_rng(stable_seed(BOOTSTRAP_SEED, key))
    slopes = np.empty(BOOTSTRAP_REPS, dtype=float)
    corrs = np.empty(BOOTSTRAP_REPS, dtype=float)
    for b in range(BOOTSTRAP_REPS):
        selected = rng.choice(clusters, size=len(clusters), replace=True)
        sample = [r for c in selected for r in by_cluster[int(c)]]
        x = np.asarray([r[field] for r in sample], dtype=float)
        y = np.asarray([r["utility"] for r in sample], dtype=float)
        fit = ols(x, y)
        slopes[b] = fit["slope"]
        corrs[b] = fit["pearson_r"]
    return {
        "slope_ci95": [float(v) for v in np.quantile(slopes, [0.025, 0.975])],
        "pearson_r_ci95": [
            float(v) for v in np.quantile(corrs, [0.025, 0.975])
        ],
    }


def summarize_stratum(records: list[dict[str, Any]], tag: str) -> dict[str, Any]:
    recon = np.asarray([r["reconstruction_r2"] for r in records], dtype=float)
    difficulty = 1.0 - recon
    utility = np.asarray([r["utility"] for r in records], dtype=float)
    per_realization_spearman = []
    for realization in sorted({r["realization"] for r in records}):
        subset = [r for r in records if r["realization"] == realization]
        per_realization_spearman.append(
            spearman(
                np.asarray([r["unreconstructibility"] for r in subset]),
                np.asarray([r["utility"] for r in subset]),
            )
        )
    fit_r2 = ols(recon, utility)
    fit_difficulty = ols(difficulty, utility)
    fit_rho = ols(
        np.asarray([r["rho_removed"] for r in records], dtype=float), utility
    )
    return {
        "n_observations": len(records),
        "n_realizations": len({r["realization"] for r in records}),
        "model_utility_on_reconstruction_r2": {
            **fit_r2,
            **cluster_bootstrap(records, "reconstruction_r2", tag + "|r2"),
        },
        "equivalent_model_utility_on_unreconstructibility": fit_difficulty,
        "loro_new_realization_prediction_from_reconstruction": (
            leave_one_realization_out(records, "reconstruction_r2")
        ),
        "loro_new_realization_prediction_from_removed_fraction": (
            leave_one_realization_out(records, "rho_removed")
        ),
        "removed_fraction_in_sample": fit_rho,
        "mean_within_realization_spearman_difficulty_utility": float(
            np.mean(per_realization_spearman)
        ),
        "range": {
            "reconstruction_r2": [float(np.min(recon)), float(np.max(recon))],
            "utility": [float(np.min(utility)), float(np.max(utility))],
        },
    }


def cross_family(records: list[dict[str, Any]]) -> dict[str, Any]:
    output = {}
    for backbone in BACKBONES:
        for support in SUPPORTS:
            subset = [
                r
                for r in records
                if r["backbone"] == backbone and r["support"] == support
            ]
            for train_family, test_family in (("pairwise", "sparse"), ("sparse", "pairwise")):
                train = [r for r in subset if r["family"] == train_family]
                test = [r for r in subset if r["family"] == test_family]
                x_train = np.asarray(
                    [r["reconstruction_r2"] for r in train], dtype=float
                )
                y_train = np.asarray([r["utility"] for r in train], dtype=float)
                fit = ols(x_train, y_train)
                x_test = np.asarray(
                    [r["reconstruction_r2"] for r in test], dtype=float
                )
                y_test = np.asarray([r["utility"] for r in test], dtype=float)
                pred = fit["intercept"] + fit["slope"] * x_test
                sst = float(np.sum((y_test - np.mean(y_test)) ** 2))
                output[f"{backbone}|K={support}|{train_family}->{test_family}"] = {
                    "r2": 1.0 - float(np.sum((y_test - pred) ** 2)) / sst,
                    "mae": float(np.mean(np.abs(y_test - pred))),
                    "rmse": float(np.sqrt(np.mean((y_test - pred) ** 2))),
                    "prediction_correlation": float(np.corrcoef(pred, y_test)[0, 1]),
                }
    return output


def rung_means(records: list[dict[str, Any]]) -> dict[str, Any]:
    output = {}
    for family in FAMILIES:
        for backbone in BACKBONES:
            for support in SUPPORTS:
                subset = [
                    r
                    for r in records
                    if r["family"] == family
                    and r["backbone"] == backbone
                    and r["support"] == support
                ]
                rows = []
                for k in sorted({r["k"] for r in subset}):
                    cell = [r for r in subset if r["k"] == k]
                    rows.append(
                        {
                            "k": k,
                            "n": len(cell),
                            "mean_reconstruction_r2": float(
                                np.mean([r["reconstruction_r2"] for r in cell])
                            ),
                            "mean_unreconstructibility": float(
                                np.mean([r["unreconstructibility"] for r in cell])
                            ),
                            "mean_utility": float(
                                np.mean([r["utility"] for r in cell])
                            ),
                        }
                    )
                output[f"{family}|{backbone}|K={support}"] = rows
    return output


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "family",
        "realization",
        "support",
        "backbone",
        "k",
        "rho_removed",
        "n_pairs_broken",
        "n_operations",
        "n_base_features",
        "reconstruction_r2",
        "unreconstructibility",
        "utility",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in fields})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ladder-root", type=Path, default=DEFAULT_LADDER_ROOT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--threads", type=int, default=1)
    args = parser.parse_args()

    global PANEL, LADDER_ROOT, THREADS
    LADDER_ROOT = args.ladder_root.resolve()
    THREADS = args.threads
    input_sha = sha256_file(mcr.DEFAULT_INPUT)
    if input_sha != FROZEN_INPUT_SHA256:
        raise SystemExit("input panel is not the frozen MCR panel")
    PANEL = mcr.load_panel(mcr.DEFAULT_INPUT)
    tasks = [(family, realization) for family in FAMILIES for realization in REALIZATIONS]
    if args.workers == 1:
        nested = [analyze_cell(task) for task in tasks]
    else:
        with mp.get_context("fork").Pool(processes=args.workers) as pool:
            nested = list(pool.imap_unordered(analyze_cell, tasks))
    rows = [row for cell_rows in nested for row in cell_rows]
    rows.sort(
        key=lambda r: (
            r["family"],
            r["backbone"],
            r["support"],
            r["realization"],
            r["k"],
        )
    )

    strata = {}
    for family in FAMILIES:
        for backbone in BACKBONES:
            for support in SUPPORTS:
                selected = [
                    r
                    for r in rows
                    if r["family"] == family
                    and r["backbone"] == backbone
                    and r["support"] == support
                ]
                tag = f"{family}|{backbone}|K={support}"
                strata[tag] = summarize_stratum(selected, tag)

    payload = {
        "status": "complete",
        "analysis_scope": "exploratory; no manuscript source was edited",
        "proxy_definition": (
            "For each operation column, fit the same backbone and frozen "
            "hyperparameters used by the downstream ladder on source plus "
            "target-support rows, using only the exact reduced base frame; "
            "evaluate R^2 on held-out target-query rows and average R^2 "
            "uniformly over operation columns. No task outcome, reference "
            "prediction, or utility is used in proxy construction."
        ),
        "utility_definition": "U = nMSE(free) - nMSE(op_true); positive means supplied operations help",
        "bootstrap": {
            "unit": "realization cluster",
            "reps": BOOTSTRAP_REPS,
            "seed": BOOTSTRAP_SEED,
        },
        "n_rows": len(rows),
        "n_cells": len(tasks),
        "provenance": {
            "input_sha256": input_sha,
            "mcr_runner_sha256": sha256_file(MCR_RUNNER),
            "vr_runner_sha256": sha256_file(VR_RUNNER),
            "rl_runner_sha256": sha256_file(RL_RUNNER),
            "analysis_runner_sha256": sha256_file(Path(__file__)),
        },
        "strata": strata,
        "cross_family_prediction": cross_family(rows),
        "rung_means": rung_means(rows),
    }
    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "CELL_RUNG_PROXY_V1.csv", rows)
    (args.out / "SUMMARY_V1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "complete",
                "n_rows": len(rows),
                "summary": str(args.out / "SUMMARY_V1.json"),
                "cells": str(args.out / "CELL_RUNG_PROXY_V1.csv"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
