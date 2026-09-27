#!/usr/bin/env python3
"""Fixed-width noisy-proxy recoverability ladder for MCR relation values.

Execution is deliberately phased:
  freeze -> proxy -> utility -> summarize

The utility phase refuses to run before all outcome-free reconstruction files
have been sealed.  See the frozen protocol in the matching experiment folder.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import multiprocessing as mp
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MCR_RUNNER = ROOT / "scripts/run_crta_v3_mcr_factorial_semisynth_v1.py"
EXP = ROOT / "experiments/crta_v3_mcr_noisy_proxy_recoverability_v1"
PROTOCOL = EXP / "PROTOCOL_V1.md"
MANIFEST = EXP / "FROZEN_MANIFEST_V1.json"
PROXY_ROOT = EXP / "proxy"
UTILITY_ROOT = EXP / "utility"
PROXY_SEAL = EXP / "PROXY_SEAL_V1.json"
SUMMARY = EXP / "SUMMARY_V1.json"
ROWS_CSV = EXP / "CELL_DOSE_V1.csv"
REPORT = EXP / "REPORT_V1.md"

FROZEN_INPUT_SHA256 = (
    "6af2215c72a65ecc306e5c4d3d9af5b61b16a073dd5aa4c0f33b178741245a25"
)
FAMILIES = ("pairwise", "sparse")
SUPPORTS = (32, 512)
BACKBONES = ("xgb", "histgb")
REALIZATIONS = tuple(range(20))
NOISE_SIGMAS = (0.0, 0.125, 0.25, 0.5, 1.0, 2.0, 4.0)
N_BASE = 8
NOISE_NAMESPACE = "mcr_noisy_proxy_v1"
BOOTSTRAP_NAMESPACE = "mcr_noisy_proxy_bootstrap_v1"
BOOTSTRAP_REPS = 10_000


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


mcr = _load("mcr_core_noisy_proxy_v1", MCR_RUNNER)
PANEL = None
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


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def design_dict() -> dict[str, Any]:
    return {
        "experiment": "crta_v3_mcr_noisy_proxy_recoverability_v1",
        "declared_post_result_diagnostic": True,
        "families": list(FAMILIES),
        "realizations": list(REALIZATIONS),
        "supports": list(SUPPORTS),
        "backbones": list(BACKBONES),
        "noise_sigmas_source_iqr": list(NOISE_SIGMAS),
        "noise_namespace": NOISE_NAMESPACE,
        "base_feature_count": N_BASE,
        "pooling": "unweighted",
        "proxy": {
            "target": "exact clean compiled operation value",
            "fit_rows": "frozen source plus target support",
            "score_rows": "held-out target query",
            "metric": "mean unclipped operation-level R2",
            "sealed_before_utility": True,
        },
        "utility": "nMSE(reference) - nMSE(intended)",
        "bootstrap": {
            "unit": "realization",
            "repetitions": BOOTSTRAP_REPS,
            "namespace": BOOTSTRAP_NAMESPACE,
        },
    }


def freeze() -> None:
    if MANIFEST.exists():
        raise RuntimeError(f"manifest already exists: {MANIFEST}")
    input_path = Path(mcr.DEFAULT_INPUT)
    if sha256_file(input_path) != FROZEN_INPUT_SHA256:
        raise RuntimeError("input panel is not the frozen MCR panel")
    dependencies = {
        "runner": Path(__file__).resolve(),
        "protocol": PROTOCOL,
        "mcr_runner": MCR_RUNNER,
        "input_panel": input_path,
    }
    missing = [str(path) for path in dependencies.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing dependencies: " + ", ".join(missing))
    manifest = {
        "created_unix": time.time(),
        "design": design_dict(),
        "files": {
            name: {"path": str(path), "sha256": sha256_file(path)}
            for name, path in dependencies.items()
        },
    }
    write_json(MANIFEST, manifest)
    print(json.dumps({
        "status": "frozen",
        "manifest": str(MANIFEST),
        "sha256": sha256_file(MANIFEST),
    }), flush=True)


def validate_manifest() -> dict[str, Any]:
    if not MANIFEST.is_file():
        raise RuntimeError("run the freeze phase first")
    manifest = read_json(MANIFEST)
    if manifest["design"] != design_dict():
        raise RuntimeError("runtime design differs from frozen design")
    for name, record in manifest["files"].items():
        path = Path(record["path"])
        observed = sha256_file(path)
        if observed != record["sha256"]:
            raise RuntimeError(
                f"frozen dependency changed: {name}: {observed} != {record['sha256']}"
            )
    return manifest


def constituents_of(cell: Any) -> list[int]:
    features: set[int] = set()
    for a, b, _operation, _sign in cell.relations["true"].pair_terms:
        features.add(int(a))
        features.add(int(b))
    result = sorted(features)
    if not result:
        raise AssertionError("no pairwise constituents")
    return result


def source_scale(values: np.ndarray) -> float:
    finite = np.asarray(values, dtype=np.float64)
    finite = finite[np.isfinite(finite)]
    if len(finite) < 100:
        raise RuntimeError("too few finite source values for noise scaling")
    q25, q75 = np.quantile(finite, [0.25, 0.75])
    scale = float(q75 - q25)
    if not np.isfinite(scale) or scale <= 1e-8:
        scale = float(np.std(finite, ddof=0))
    if not np.isfinite(scale) or scale <= 1e-8:
        scale = 1.0
    return scale


def clean_frames(cell: Any, support: int) -> dict[str, Any]:
    """Build frozen true-decoded frames without reading cell.y."""
    source = mcr.decode(cell.source_rendered, cell.source_tables["true"])
    support_frame = cell.target_decoded_support[support]
    query = cell.target_decoded_query
    fit = np.vstack([source, support_frame])
    fit_rows = np.concatenate([cell.source_rows, cell.supports[support]])
    op_fit, constraints = mcr.compile_design(fit, cell.relations["op_only"])
    op_query, query_constraints = mcr.compile_design(
        query, cell.relations["op_only"]
    )
    if any(constraints) or any(query_constraints):
        raise AssertionError("relation-value arms must not carry constraints")
    if fit.shape[1] != N_BASE or query.shape[1] != N_BASE:
        raise AssertionError("unexpected base width")
    n_op = op_fit.shape[1] - N_BASE
    if n_op <= 0 or op_query.shape[1] - N_BASE != n_op:
        raise AssertionError("unexpected operation width")
    if not np.array_equal(op_fit[:, :N_BASE], fit, equal_nan=True):
        raise AssertionError("compiled fit base block changed")
    if not np.array_equal(op_query[:, :N_BASE], query, equal_nan=True):
        raise AssertionError("compiled query base block changed")
    return {
        "source": source,
        "fit": fit,
        "query": query,
        "fit_rows": fit_rows,
        "query_rows": cell.query_rows,
        "op_fit": op_fit[:, N_BASE:],
        "op_query": op_query[:, N_BASE:],
        "n_op": n_op,
    }


def noisy_base(
    clean: dict[str, Any], family: str, realization: int,
    constituents: list[int], sigma: float,
) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    fit = clean["fit"].copy()
    query = clean["query"].copy()
    scales: dict[str, float] = {}
    panel_n = len(PANEL.z)
    for feature in constituents:
        scale = source_scale(clean["source"][:, feature])
        scales[str(feature)] = scale
        rng = np.random.default_rng(stable_seed(
            NOISE_NAMESPACE, family, realization, feature
        ))
        epsilon = rng.standard_normal(panel_n)
        fit_ok = np.isfinite(fit[:, feature])
        query_ok = np.isfinite(query[:, feature])
        fit[fit_ok, feature] += (
            sigma * scale * epsilon[clean["fit_rows"]][fit_ok]
        )
        query[query_ok, feature] += (
            sigma * scale * epsilon[clean["query_rows"]][query_ok]
        )

    nonconstituents = sorted(set(range(N_BASE)) - set(constituents))
    if not np.array_equal(
        fit[:, nonconstituents], clean["fit"][:, nonconstituents], equal_nan=True
    ):
        raise AssertionError("nonconstituent fit values changed")
    if not np.array_equal(
        query[:, nonconstituents], clean["query"][:, nonconstituents],
        equal_nan=True,
    ):
        raise AssertionError("nonconstituent query values changed")
    if not np.array_equal(np.isnan(fit), np.isnan(clean["fit"])):
        raise AssertionError("fit missingness mask changed")
    if not np.array_equal(np.isnan(query), np.isnan(clean["query"])):
        raise AssertionError("query missingness mask changed")
    if np.isinf(fit).any() or np.isinf(query).any():
        raise AssertionError("noise introduced infinity")
    if sigma == 0.0:
        if not np.array_equal(fit, clean["fit"], equal_nan=True):
            raise AssertionError("zero-dose fit is not exact")
        if not np.array_equal(query, clean["query"], equal_nan=True):
            raise AssertionError("zero-dose query is not exact")
    return fit, query, scales


def reconstruction_r2(
    backbone: str, noisy_fit: np.ndarray, op_fit: np.ndarray,
    noisy_query: np.ndarray, op_query: np.ndarray, realization: int,
) -> dict[str, Any]:
    per_operation = []
    for operation_index in range(op_fit.shape[1]):
        train_ok = np.isfinite(op_fit[:, operation_index])
        query_ok = np.isfinite(op_query[:, operation_index])
        if int(train_ok.sum()) < 100 or int(query_ok.sum()) < 100:
            raise RuntimeError("too few finite operation values")
        prediction = mcr.fit_predict(
            backbone,
            noisy_fit[train_ok],
            op_fit[train_ok, operation_index],
            np.ones(int(train_ok.sum()), dtype=np.float64),
            noisy_query[query_ok],
            tuple([0] * N_BASE),
            seed=realization,
            threads=THREADS,
        )
        truth = op_query[query_ok, operation_index]
        sse = float(np.square(truth - prediction).sum())
        sst = float(np.square(truth - truth.mean()).sum())
        if not np.isfinite(sst) or sst <= 0:
            raise RuntimeError("degenerate operation query variance")
        per_operation.append({
            "operation_index": operation_index,
            "r2": 1.0 - sse / sst,
            "normalized_mse": sse / sst,
            "n_fit": int(train_ok.sum()),
            "n_query": int(query_ok.sum()),
        })
    return {
        "reconstruction_r2": float(np.mean([x["r2"] for x in per_operation])),
        "per_operation": per_operation,
    }


def common_cell(family: str, realization: int) -> tuple[Any, list[int]]:
    if PANEL is None:
        raise RuntimeError("worker panel not initialized")
    cell = mcr.build_cell(PANEL, "primary", family, realization, SUPPORTS)
    constituents = constituents_of(cell)
    return cell, constituents


def cell_path(root: Path, family: str, realization: int) -> Path:
    return root / family / f"r{realization:02d}.json"


def base_provenance() -> dict[str, Any]:
    return {
        "manifest_sha256": sha256_file(MANIFEST),
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "protocol_sha256": sha256_file(PROTOCOL),
        "mcr_runner_sha256": sha256_file(MCR_RUNNER),
        "input_sha256": sha256_file(Path(mcr.DEFAULT_INPUT)),
        "noise_namespace": NOISE_NAMESPACE,
        "threads": THREADS,
    }


def validate_existing(path: Path, phase: str) -> bool:
    if not path.is_file():
        return False
    payload = read_json(path)
    expected = base_provenance()
    if payload.get("phase") != phase:
        raise RuntimeError(f"wrong phase in {path}")
    for key, value in expected.items():
        if payload.get(key) != value:
            raise RuntimeError(f"provenance mismatch for {key} in {path}")
    return True


def proxy_cell(task: tuple[str, int]) -> str:
    family, realization = task
    path = cell_path(PROXY_ROOT, family, realization)
    if validate_existing(path, "proxy"):
        return f"{family} r{realization:02d} proxy cached"
    started = time.time()
    cell, constituents = common_cell(family, realization)
    results: dict[str, Any] = {}
    n_op_seen = None
    scales_seen = None
    for support in SUPPORTS:
        clean = clean_frames(cell, support)
        n_op_seen = clean["n_op"]
        results[str(support)] = {}
        noisy_by_sigma = {}
        for sigma in NOISE_SIGMAS:
            noisy_fit, noisy_query, scales = noisy_base(
                clean, family, realization, constituents, sigma
            )
            if scales_seen is not None and scales != scales_seen:
                raise AssertionError("source noise scales changed across supports")
            scales_seen = scales
            noisy_by_sigma[str(sigma)] = (noisy_fit, noisy_query)
        for backbone in BACKBONES:
            results[str(support)][backbone] = {}
            for sigma in NOISE_SIGMAS:
                noisy_fit, noisy_query = noisy_by_sigma[str(sigma)]
                results[str(support)][backbone][str(sigma)] = reconstruction_r2(
                    backbone, noisy_fit, clean["op_fit"], noisy_query,
                    clean["op_query"], realization
                )
    payload = {
        "phase": "proxy",
        "outcome_values_read_by_proxy_fit": 0,
        "family": family,
        "realization": realization,
        "constituents": constituents,
        "n_operations": int(n_op_seen),
        "source_iqr_scales": scales_seen,
        "supports": list(SUPPORTS),
        "backbones": list(BACKBONES),
        "noise_sigmas": list(NOISE_SIGMAS),
        "results": results,
        "wall_seconds": round(time.time() - started, 3),
        **base_provenance(),
    }
    write_json(path, payload)
    return f"{family} r{realization:02d} proxy done ({payload['wall_seconds']}s)"


def expected_tasks() -> list[tuple[str, int]]:
    return [(family, realization) for family in FAMILIES for realization in REALIZATIONS]


def seal_proxy() -> None:
    records = []
    for family, realization in expected_tasks():
        path = cell_path(PROXY_ROOT, family, realization)
        if not validate_existing(path, "proxy"):
            raise RuntimeError(f"missing proxy cell: {path}")
        records.append({"path": str(path), "sha256": sha256_file(path)})
    seal = {
        "status": "sealed_before_utility",
        "manifest_sha256": sha256_file(MANIFEST),
        "n_cells": len(records),
        "files": records,
    }
    if PROXY_SEAL.exists():
        existing = read_json(PROXY_SEAL)
        if existing != seal:
            raise RuntimeError("existing proxy seal differs from current proxy files")
    else:
        write_json(PROXY_SEAL, seal)
    print(json.dumps({
        "status": "proxy_complete_and_sealed",
        "n_cells": len(records),
        "seal": str(PROXY_SEAL),
        "sha256": sha256_file(PROXY_SEAL),
    }), flush=True)


def validate_proxy_seal() -> dict[str, Any]:
    if not PROXY_SEAL.is_file():
        raise RuntimeError("utility is blocked until proxy phase is sealed")
    seal = read_json(PROXY_SEAL)
    if seal.get("manifest_sha256") != sha256_file(MANIFEST):
        raise RuntimeError("proxy seal manifest mismatch")
    if seal.get("n_cells") != len(expected_tasks()):
        raise RuntimeError("proxy seal is incomplete")
    for record in seal["files"]:
        path = Path(record["path"])
        if sha256_file(path) != record["sha256"]:
            raise RuntimeError(f"proxy file changed after seal: {path}")
    return seal


def utility_cell(task: tuple[str, int]) -> str:
    family, realization = task
    path = cell_path(UTILITY_ROOT, family, realization)
    if validate_existing(path, "utility"):
        return f"{family} r{realization:02d} utility cached"
    started = time.time()
    cell, constituents = common_cell(family, realization)
    y_query = cell.y[cell.query_rows]
    query_variance = float(np.var(y_query, ddof=0))
    if not np.isfinite(query_variance) or query_variance <= 0:
        raise RuntimeError("degenerate task outcome variance")
    results: dict[str, Any] = {}
    gate_checks = {
        "removal_reference_has_no_relation_value": True,
        "preservation_shared_noisy_base": True,
        "preservation_all_base_columns_present": True,
        "preservation_missingness_unchanged": True,
        "interface_expected_dimensions": True,
        "interface_no_infinity": True,
    }
    for support in SUPPORTS:
        clean = clean_frames(cell, support)
        y_fit = np.concatenate([
            cell.y[cell.source_rows], cell.y[cell.supports[support]]
        ])
        weights = np.ones(len(y_fit), dtype=np.float64)
        results[str(support)] = {}
        noisy_by_sigma = {}
        for sigma in NOISE_SIGMAS:
            noisy_fit, noisy_query, _scales = noisy_base(
                clean, family, realization, constituents, sigma
            )
            intended_fit = np.hstack([noisy_fit, clean["op_fit"]])
            intended_query = np.hstack([noisy_query, clean["op_query"]])
            if not np.array_equal(
                intended_fit[:, :N_BASE], noisy_fit, equal_nan=True
            ) or not np.array_equal(
                intended_query[:, :N_BASE], noisy_query, equal_nan=True
            ):
                gate_checks["preservation_shared_noisy_base"] = False
            if noisy_fit.shape[1] != N_BASE or noisy_query.shape[1] != N_BASE:
                gate_checks["preservation_all_base_columns_present"] = False
            if intended_fit.shape[1] != N_BASE + clean["n_op"]:
                gate_checks["interface_expected_dimensions"] = False
            if np.isinf(intended_fit).any() or np.isinf(intended_query).any():
                gate_checks["interface_no_infinity"] = False
            noisy_by_sigma[str(sigma)] = (
                noisy_fit, noisy_query, intended_fit, intended_query
            )
        for backbone in BACKBONES:
            results[str(support)][backbone] = {}
            for sigma in NOISE_SIGMAS:
                noisy_fit, noisy_query, intended_fit, intended_query = (
                    noisy_by_sigma[str(sigma)]
                )
                arm_results = {}
                for arm, x_fit, x_query in (
                    ("reference", noisy_fit, noisy_query),
                    ("intended", intended_fit, intended_query),
                ):
                    prediction = mcr.fit_predict(
                        backbone, x_fit, y_fit, weights, x_query,
                        tuple([0] * x_fit.shape[1]), seed=realization,
                        threads=THREADS,
                    )
                    mse = float(np.square(y_query - prediction).mean())
                    arm_results[arm] = {
                        "nmse": mse / query_variance,
                        "n_features": int(x_fit.shape[1]),
                    }
                results[str(support)][backbone][str(sigma)] = {
                    "arms": arm_results,
                    "utility": (
                        arm_results["reference"]["nmse"]
                        - arm_results["intended"]["nmse"]
                    ),
                }
    if not all(gate_checks.values()):
        raise AssertionError(f"structural gate failure: {gate_checks}")
    payload = {
        "phase": "utility",
        "proxy_seal_sha256": sha256_file(PROXY_SEAL),
        "family": family,
        "realization": realization,
        "constituents": constituents,
        "supports": list(SUPPORTS),
        "backbones": list(BACKBONES),
        "noise_sigmas": list(NOISE_SIGMAS),
        "query_variance": query_variance,
        "gate_checks": gate_checks,
        "results": results,
        "wall_seconds": round(time.time() - started, 3),
        **base_provenance(),
    }
    write_json(path, payload)
    return f"{family} r{realization:02d} utility done ({payload['wall_seconds']}s)"


def run_parallel(function: Any, workers: int) -> None:
    tasks = expected_tasks()
    if workers == 1:
        for task in tasks:
            print(function(task), flush=True)
        return
    with mp.get_context("fork").Pool(processes=workers) as pool:
        for message in pool.imap_unordered(function, tasks):
            print(message, flush=True)


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
    rx, ry = rankdata(x), rankdata(y)
    if np.std(rx) <= 0 or np.std(ry) <= 0:
        return 0.0
    return float(np.corrcoef(rx, ry)[0, 1])


def bootstrap_mean(values: np.ndarray, key: str) -> list[float]:
    rng = np.random.default_rng(stable_seed(BOOTSTRAP_NAMESPACE, key))
    draws = rng.choice(values, size=(BOOTSTRAP_REPS, len(values)), replace=True)
    return [float(x) for x in np.quantile(draws.mean(axis=1), [0.025, 0.975])]


def joined_rows() -> list[dict[str, Any]]:
    validate_proxy_seal()
    rows = []
    for family, realization in expected_tasks():
        proxy_path = cell_path(PROXY_ROOT, family, realization)
        utility_path = cell_path(UTILITY_ROOT, family, realization)
        proxy = read_json(proxy_path)
        utility = read_json(utility_path)
        if utility.get("proxy_seal_sha256") != sha256_file(PROXY_SEAL):
            raise RuntimeError(f"utility was not tied to current proxy seal: {utility_path}")
        if not all(utility["gate_checks"].values()):
            raise RuntimeError(f"gate failure in {utility_path}")
        for support in SUPPORTS:
            for backbone in BACKBONES:
                baseline = utility["results"][str(support)][backbone]["0.0"]
                for sigma in NOISE_SIGMAS:
                    p = proxy["results"][str(support)][backbone][str(sigma)]
                    u = utility["results"][str(support)][backbone][str(sigma)]
                    rows.append({
                        "family": family,
                        "realization": realization,
                        "support": support,
                        "backbone": backbone,
                        "sigma": sigma,
                        "reconstruction_r2": p["reconstruction_r2"],
                        "unreconstructibility": 1.0 - p["reconstruction_r2"],
                        "reference_nmse": u["arms"]["reference"]["nmse"],
                        "intended_nmse": u["arms"]["intended"]["nmse"],
                        "utility": u["utility"],
                        "reference_nmse_change_from_zero": (
                            u["arms"]["reference"]["nmse"]
                            - baseline["arms"]["reference"]["nmse"]
                        ),
                        "intended_nmse_change_from_zero": (
                            u["arms"]["intended"]["nmse"]
                            - baseline["arms"]["intended"]["nmse"]
                        ),
                    })
    return rows


def summarize_stratum(records: list[dict[str, Any]], key: str) -> dict[str, Any]:
    per_realization = []
    for realization in REALIZATIONS:
        cell = sorted(
            [r for r in records if r["realization"] == realization],
            key=lambda r: r["sigma"],
        )
        difficulty = np.asarray([r["unreconstructibility"] for r in cell])
        utility = np.asarray([r["utility"] for r in cell])
        dose = np.asarray([r["sigma"] for r in cell])
        reconstruction = np.asarray([r["reconstruction_r2"] for r in cell])
        per_realization.append({
            "realization": realization,
            "spearman_unreconstructibility_utility": spearman(difficulty, utility),
            "spearman_dose_reconstruction_r2": spearman(dose, reconstruction),
            "spearman_dose_utility": spearman(dose, utility),
        })
    primary = np.asarray([
        r["spearman_unreconstructibility_utility"] for r in per_realization
    ])
    by_sigma = []
    for sigma in NOISE_SIGMAS:
        dose_rows = [r for r in records if r["sigma"] == sigma]
        item: dict[str, Any] = {"sigma": sigma, "n": len(dose_rows)}
        for field in (
            "reconstruction_r2", "utility", "reference_nmse", "intended_nmse",
            "reference_nmse_change_from_zero", "intended_nmse_change_from_zero",
        ):
            values = np.asarray([r[field] for r in dose_rows], dtype=float)
            item[f"mean_{field}"] = float(values.mean())
            item[f"{field}_ci95"] = bootstrap_mean(
                values, f"{key}|sigma={sigma}|{field}"
            )
        by_sigma.append(item)
    ci = bootstrap_mean(primary, f"{key}|primary_spearman")
    return {
        "n_realizations": len(REALIZATIONS),
        "primary_mean_within_realization_spearman": float(primary.mean()),
        "primary_ci95": ci,
        "graded_recoverability_supported": bool(primary.mean() > 0 and ci[0] > 0),
        "mean_within_realization_spearman_dose_reconstruction_r2": float(np.mean([
            r["spearman_dose_reconstruction_r2"] for r in per_realization
        ])),
        "mean_within_realization_spearman_dose_utility": float(np.mean([
            r["spearman_dose_utility"] for r in per_realization
        ])),
        "per_realization": per_realization,
        "by_sigma": by_sigma,
    }


def write_rows_csv(rows: list[dict[str, Any]]) -> None:
    fields = list(rows[0])
    with ROWS_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_report(payload: dict[str, Any]) -> None:
    lines = [
        "# Fixed-width noisy-proxy recoverability ladder",
        "",
        f"Status: **{payload['status']}**",
        "",
        "The proxy phase was completed and cryptographically sealed before the "
        "utility phase. All structural gates passed in all 40 cells.",
        "",
        "| Family | Backbone | K | Mean within-realization Spearman | 95% CI | Supports graded relation? |",
        "|---|---|---:|---:|---:|:---:|",
    ]
    for key, result in payload["strata"].items():
        family, backbone, support = key.split("|")
        low, high = result["primary_ci95"]
        lines.append(
            f"| {family} | {backbone} | {support.split('=')[1]} | "
            f"{result['primary_mean_within_realization_spearman']:+.3f} | "
            f"[{low:+.3f}, {high:+.3f}] | "
            f"{'yes' if result['graded_recoverability_supported'] else 'no'} |"
        )
    lines.extend([
        "",
        f"Global all-eight-strata verdict: **{'pass' if payload['all_eight_strata_support_graded_recoverability'] else 'fail'}**.",
        "",
        "Scope: controlled pairwise/sparse relation-value setting only; this does "
        "not override the previously reported real-data non-replication.",
        "",
    ])
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def summarize() -> None:
    rows = joined_rows()
    rows.sort(key=lambda r: (
        r["family"], r["backbone"], r["support"], r["realization"], r["sigma"]
    ))
    strata = {}
    for family in FAMILIES:
        for backbone in BACKBONES:
            for support in SUPPORTS:
                key = f"{family}|{backbone}|K={support}"
                selected = [
                    r for r in rows
                    if r["family"] == family
                    and r["backbone"] == backbone
                    and r["support"] == support
                ]
                strata[key] = summarize_stratum(selected, key)
    proxy_seconds = sum(
        read_json(cell_path(PROXY_ROOT, f, r))["wall_seconds"]
        for f, r in expected_tasks()
    )
    utility_seconds = sum(
        read_json(cell_path(UTILITY_ROOT, f, r))["wall_seconds"]
        for f, r in expected_tasks()
    )
    payload = {
        "status": "complete",
        "scope": "controlled pairwise/sparse relation-value diagnostic",
        "n_rows": len(rows),
        "n_cells": len(expected_tasks()),
        "proxy_sealed_before_utility": True,
        "proxy_seal_sha256": sha256_file(PROXY_SEAL),
        "all_structural_gates_passed": True,
        "all_eight_strata_support_graded_recoverability": all(
            result["graded_recoverability_supported"] for result in strata.values()
        ),
        "aggregate_worker_seconds": {
            "proxy": proxy_seconds,
            "utility": utility_seconds,
            "total": proxy_seconds + utility_seconds,
        },
        "design": design_dict(),
        "strata": strata,
        "provenance": {
            **base_provenance(),
            "proxy_seal_sha256": sha256_file(PROXY_SEAL),
            "python": platform.python_version(),
            "host": platform.node(),
        },
    }
    write_rows_csv(rows)
    write_json(SUMMARY, payload)
    write_report(payload)
    print(json.dumps({
        "status": "complete",
        "n_rows": len(rows),
        "all_eight_strata_pass": payload[
            "all_eight_strata_support_graded_recoverability"
        ],
        "summary": str(SUMMARY),
        "report": str(REPORT),
    }, indent=2), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "phase", choices=("freeze", "proxy", "utility", "summarize")
    )
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--threads", type=int, default=1)
    args = parser.parse_args()
    if args.workers < 1 or args.threads < 1:
        raise SystemExit("workers and threads must be positive")
    if args.phase == "freeze":
        freeze()
        return 0
    validate_manifest()
    global PANEL, THREADS
    THREADS = args.threads
    PANEL = mcr.load_panel(mcr.DEFAULT_INPUT)
    if args.phase == "proxy":
        run_parallel(proxy_cell, args.workers)
        seal_proxy()
    elif args.phase == "utility":
        validate_proxy_seal()
        run_parallel(utility_cell, args.workers)
    else:
        validate_proxy_seal()
        summarize()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

