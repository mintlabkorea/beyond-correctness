#!/usr/bin/env python3
"""Run the label-permuted-source falsification of the M x C interaction."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
BASE_RUNNER = ROOT / "scripts/run_crta_v3_mcr_factorial_semisynth_v1.py"
PREREG = ROOT / "iclr_latex_v3/MCR_NULL_SOURCE_PREREGISTRATION_V1.md"
ORIGINAL_ROOT = ROOT / "experiments/crta_v3_mcr_factorial_semisynth_v1"
DEFAULT_OUT = ROOT / "experiments/crta_v3_mcr_null_source_v1"
ARMS = ("m1c1rf", "m1c0rf", "m0c1rf", "m0c0rf")
FAMILIES = ("additive", "pairwise", "sparse")
BACKBONES = ("xgb", "histgb")
K = 32
N_REALIZATIONS = 20
RNG_NS = "mcr_null_source_v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load_base() -> Any:
    name = "crta_v3_mcr_factorial_semisynth_frozen_base"
    spec = importlib.util.spec_from_file_location(name, BASE_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import base runner: {BASE_RUNNER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def derangement(base: Any, family: str, realization: int, n: int) -> np.ndarray:
    rng = np.random.default_rng(base.stable_seed(RNG_NS, family, realization))
    identity = np.arange(n)
    for _ in range(1000):
        perm = rng.permutation(n)
        if np.all(perm != identity):
            return perm
    raise RuntimeError("could not draw a source-label derangement")


def max_abs_corr(x: np.ndarray, y: np.ndarray) -> float:
    values = []
    for column in x.T:
        if np.std(column) == 0 or np.std(y) == 0:
            continue
        values.append(abs(float(np.corrcoef(column, y)[0, 1])))
    return max(values, default=0.0)


def original_cell(family: str, realization: int) -> dict[str, Any]:
    path = ORIGINAL_ROOT / "primary" / family / f"r{realization:02d}" / "metrics.json"
    if not path.is_file():
        raise RuntimeError(f"missing original frozen cell: {path}")
    return json.loads(path.read_text())


def run_cell(base: Any, panel: Any, family: str, realization: int,
             threads: int) -> dict[str, Any]:
    cell = base.build_cell(panel, "primary", family, realization, (K,))
    frozen = original_cell(family, realization)
    if base.json_ready(cell.audit) != frozen["audit"]:
        raise RuntimeError("rebuilt cell audit differs from the frozen primary cell")
    if cell.name_accuracy != frozen["name_match_accuracy"]:
        raise RuntimeError("rebuilt name audit differs from the frozen primary cell")

    source_y = np.asarray(cell.y[cell.source_rows], dtype=np.float64)
    perm = derangement(base, family, realization, len(source_y))
    shuffled_y = source_y[perm]
    if not np.array_equal(np.sort(source_y), np.sort(shuffled_y)):
        raise AssertionError("source-label multiset changed during permutation")

    reference = base.arm_matrices(cell, "m1c1rf", K, weighted=False)
    reference_x = reference[0][:len(source_y), :len(base.FEATURES)]
    correlations = {
        "max_abs_true_source_feature_label_corr_before": max_abs_corr(
            reference_x, source_y),
        "max_abs_true_source_feature_label_corr_after": max_abs_corr(
            reference_x, shuffled_y),
    }

    y_query = np.asarray(cell.y[cell.query_rows], dtype=np.float64)
    query_var = float(np.var(y_query, ddof=0))
    if query_var <= 0:
        raise RuntimeError("non-positive query variance")
    results: dict[str, Any] = {str(K): {}}
    for backbone in BACKBONES:
        results[str(K)][backbone] = {}
        for arm in ARMS:
            x_fit, y_fit, weights, x_query, constraints = base.arm_matrices(
                cell, arm, K, weighted=False)
            if not np.array_equal(y_fit[:len(source_y)], source_y):
                raise AssertionError("unexpected original source labels")
            null_y_fit = y_fit.copy()
            null_y_fit[:len(source_y)] = shuffled_y
            prediction = base.fit_predict(
                backbone, x_fit, null_y_fit, weights, x_query, constraints,
                seed=realization, threads=threads)
            mse = float(np.mean((y_query - prediction) ** 2))
            results[str(K)][backbone][arm] = {
                "nmse": mse / query_var,
                "nrmse": float(np.sqrt(mse / query_var)),
            }

    return {
        "experiment": "mcr_null_source_label_derangement_v1",
        "family": family,
        "realization": realization,
        "support_k": K,
        "n_source": len(source_y),
        "n_query": len(y_query),
        "arms": list(ARMS),
        "backbones": list(BACKBONES),
        "source_label_intervention": {
            "namespace": RNG_NS,
            "fixed_points": int(np.sum(perm == np.arange(len(perm)))),
            "permutation_sha256": hashlib.sha256(
                perm.astype("<i8", copy=False).tobytes()).hexdigest(),
            "label_multiset_identical": True,
            **correlations,
        },
        "original_cell_provenance": {
            "runner_sha256": frozen["runner_sha256"],
            "input_sha256": frozen["input_sha256"],
            "prereg_sha256": frozen["prereg_sha256"],
        },
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=None)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--families", nargs="*", default=list(FAMILIES))
    parser.add_argument("--realizations", nargs="*", type=int,
                        default=list(range(N_REALIZATIONS)))
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    base = load_base()
    input_path = args.input or base.DEFAULT_INPUT
    os.environ.setdefault("OMP_NUM_THREADS", str(args.threads))
    import sklearn
    import xgboost

    provenance = {
        "runner_sha256": sha256_file(Path(__file__)),
        "base_runner_sha256": sha256_file(BASE_RUNNER),
        "prereg_sha256": sha256_file(PREREG),
        "input_sha256": sha256_file(input_path),
        "versions": {
            "numpy": np.__version__,
            "sklearn": sklearn.__version__,
            "xgboost": xgboost.__version__,
        },
    }
    panel = base.load_panel(input_path)
    print(json.dumps({
        "rows_source": int(len(panel.source_index)),
        "rows_target": int(len(panel.target_index)),
        **provenance,
    }), flush=True)
    if args.validate_only:
        return 0

    for family in args.families:
        if family not in FAMILIES:
            raise ValueError(f"unknown family: {family}")
        for realization in args.realizations:
            if realization not in range(N_REALIZATIONS):
                raise ValueError(f"realization out of range: {realization}")
            out_dir = args.out_root / family / f"r{realization:02d}"
            metrics_path = out_dir / "metrics.json"
            if metrics_path.is_file():
                existing = json.loads(metrics_path.read_text())
                mismatch = (
                    any(existing.get(key) != provenance[key] for key in
                        ("runner_sha256", "base_runner_sha256",
                         "prereg_sha256", "input_sha256"))
                    or existing.get("family") != family
                    or existing.get("realization") != realization
                )
                if mismatch:
                    raise RuntimeError(
                        f"{metrics_path} does not match current provenance/path")
                continue
            started = time.time()
            payload = run_cell(base, panel, family, realization, args.threads)
            payload["wall_seconds"] = round(time.time() - started, 1)
            payload.update(provenance)
            out_dir.mkdir(parents=True, exist_ok=True)
            metrics_path.write_text(
                json.dumps(base.json_ready(payload), indent=1, sort_keys=True)
                + "\n")
            print(json.dumps({
                "family": family,
                "realization": realization,
                "wall_seconds": payload["wall_seconds"],
            }), flush=True)
    print(json.dumps({"status": "complete"}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
