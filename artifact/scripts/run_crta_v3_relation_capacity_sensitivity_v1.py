#!/usr/bin/env python3
"""Frozen one-factor-at-a-time XGBoost relation-capacity sensitivity."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
PARENT_RUNNER = ROOT / "scripts/run_crta_v3_mcr_factorial_semisynth_v1.py"
PROTOCOL = ROOT / "iclr_latex_v3/RELATION_CAPACITY_SENSITIVITY_FREEZE_V1.md"
DEFAULT_INPUT = Path(
    "data/foundation/artifacts/foundation_v2/"
    "raw_adapter_source_locks_v2_3_20260724/"
    "nhanes_common_panel_source_lock_v2/nhanes_common_panel_tokens_v2.parquet"
)
DEFAULT_OUT = ROOT / "experiments/crta_v3_relation_capacity_sensitivity_v1"
FAMILIES = ("additive", "pairwise", "sparse")
SUPPORTS = (32, 512)
N_REALIZATIONS = 20
CONFIGS: dict[str, dict[str, float | int]] = {
    "depth2": {"max_depth": 2, "n_estimators": 300, "reg_lambda": 1.0},
    "depth4": {"max_depth": 4, "n_estimators": 300, "reg_lambda": 1.0},
    "baseline": {"max_depth": 6, "n_estimators": 300, "reg_lambda": 1.0},
    "depth8": {"max_depth": 8, "n_estimators": 300, "reg_lambda": 1.0},
    "depth12": {"max_depth": 12, "n_estimators": 300, "reg_lambda": 1.0},
    "l2_0": {"max_depth": 6, "n_estimators": 300, "reg_lambda": 0.0},
    "l2_10": {"max_depth": 6, "n_estimators": 300, "reg_lambda": 10.0},
    "trees100": {"max_depth": 6, "n_estimators": 100, "reg_lambda": 1.0},
    "trees1000": {"max_depth": 6, "n_estimators": 1000, "reg_lambda": 1.0},
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load_parent() -> Any:
    spec = importlib.util.spec_from_file_location("relation_capacity_parent_v1", PARENT_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {PARENT_RUNNER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def fit_predict(
    x_fit: np.ndarray,
    y_fit: np.ndarray,
    weights: np.ndarray,
    x_query: np.ndarray,
    constraints: tuple[int, ...],
    seed: int,
    threads: int,
    config: dict[str, float | int],
) -> np.ndarray:
    from xgboost import XGBRegressor

    active = any(constraints)
    model = XGBRegressor(
        tree_method="hist",
        max_depth=int(config["max_depth"]),
        n_estimators=int(config["n_estimators"]),
        learning_rate=0.05,
        min_child_weight=20,
        reg_lambda=float(config["reg_lambda"]),
        n_jobs=threads,
        random_state=seed,
        verbosity=0,
        monotone_constraints=(tuple(constraints) if active else None),
    )
    model.fit(x_fit, y_fit, sample_weight=weights)
    prediction = np.asarray(model.predict(x_query), dtype=np.float64)
    if not np.isfinite(prediction).all():
        raise RuntimeError("nonfinite prediction")
    return prediction


def run_cell(
    parent: Any,
    panel: Any,
    family: str,
    realization: int,
    supports: list[int],
    config_ids: list[str],
    threads: int,
) -> dict[str, Any]:
    cell = parent.build_cell(panel, "primary", family, realization, tuple(supports))
    query_y = np.asarray(cell.y[cell.query_rows], dtype=np.float64)
    query_var = float(np.var(query_y, ddof=0))
    if query_var <= 0 or not np.isfinite(query_var):
        raise RuntimeError("invalid query variance")
    arms = ["m1c1rf", "m1c1r1"]
    if family != "additive":
        arms.insert(1, "r_op_only")
    results: dict[str, Any] = {}
    for support in supports:
        results[str(support)] = {}
        matrices = {
            arm: parent.arm_matrices(cell, arm, support, weighted=False)
            for arm in arms
        }
        for config_id in config_ids:
            config = CONFIGS[config_id]
            results[str(support)][config_id] = {}
            for arm in arms:
                x_fit, y_fit, weights, x_query, constraints = matrices[arm]
                started = time.perf_counter()
                prediction = fit_predict(
                    x_fit, y_fit, weights, x_query, constraints,
                    realization, threads, config,
                )
                mse = float(np.mean((query_y - prediction) ** 2))
                results[str(support)][config_id][arm] = {
                    "nmse": mse / query_var,
                    "q": -mse / query_var,
                    "fit_seconds": round(time.perf_counter() - started, 3),
                }
                print(json.dumps({
                    "family": family, "realization": realization,
                    "support": support, "config": config_id, "arm": arm,
                    "nmse": mse / query_var,
                }), flush=True)
    return {
        "family": family,
        "realization": realization,
        "supports": supports,
        "config_ids": config_ids,
        "configurations": {key: CONFIGS[key] for key in config_ids},
        "arms": arms,
        "query_variance": query_var,
        "cell_audit": parent.json_ready(cell.audit),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--families", nargs="+", choices=FAMILIES, default=list(FAMILIES))
    parser.add_argument("--realizations", nargs="+", type=int, default=list(range(N_REALIZATIONS)))
    parser.add_argument("--supports", nargs="+", type=int, default=list(SUPPORTS))
    parser.add_argument("--config-ids", nargs="+", choices=tuple(CONFIGS), default=list(CONFIGS))
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()
    if any(value < 0 or value >= N_REALIZATIONS for value in args.realizations):
        raise ValueError("realizations must be in [0, 19]")
    if any(value not in SUPPORTS for value in args.supports):
        raise ValueError(f"supports must be drawn from {SUPPORTS}")
    if len(args.config_ids) != len(set(args.config_ids)):
        raise ValueError("config IDs must be unique")
    os.environ.setdefault("OMP_NUM_THREADS", str(args.threads))
    import xgboost

    parent = load_parent()
    provenance = {
        "analysis_status": "review_triggered_post_result_capacity_sensitivity",
        "input_sha256": sha256_file(args.input),
        "protocol_sha256": sha256_file(PROTOCOL),
        "parent_runner_sha256": sha256_file(PARENT_RUNNER),
        "runner_sha256": sha256_file(Path(__file__)),
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "xgboost": xgboost.__version__,
        },
    }
    panel = parent.load_panel(args.input)
    for family in args.families:
        for realization in args.realizations:
            out = args.out_root / family / f"r{realization:02d}"
            metrics_path = out / "metrics.json"
            if metrics_path.is_file():
                existing = json.loads(metrics_path.read_text(encoding="utf-8"))
                identity = ("input_sha256", "protocol_sha256", "parent_runner_sha256",
                            "runner_sha256")
                if (
                    any(existing.get(key) != provenance[key] for key in identity)
                    or existing.get("family") != family
                    or existing.get("realization") != realization
                    or existing.get("supports") != list(args.supports)
                    or existing.get("config_ids") != list(args.config_ids)
                ):
                    raise RuntimeError(f"cached cell conflicts with frozen run: {metrics_path}")
                continue
            started = time.perf_counter()
            payload = run_cell(
                parent, panel, family, realization, list(args.supports),
                list(args.config_ids), args.threads,
            )
            payload.update(provenance)
            payload["wall_seconds"] = round(time.perf_counter() - started, 3)
            out.mkdir(parents=True, exist_ok=True)
            metrics_path.write_text(
                json.dumps(parent.json_ready(payload), indent=1, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            print(json.dumps({"family": family, "realization": realization,
                              "wall_seconds": payload["wall_seconds"]}), flush=True)
    print(json.dumps({"status": "complete"}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
