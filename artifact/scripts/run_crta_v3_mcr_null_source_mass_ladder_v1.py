#!/usr/bin/env python3
"""Run the two new internal masses of the triggered alpha=1 source-mass ladder."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
BASE_RUNNER = ROOT / "scripts/run_crta_v3_mcr_factorial_semisynth_v1.py"
NULL_RUNNER = ROOT / "scripts/run_crta_v3_mcr_null_source_v1.py"
PREREG = ROOT / "iclr_latex_v3/MCR_NULL_SOURCE_MASS_LADDER_PREREGISTRATION_V1.md"
TRIGGER_SUMMARY = ROOT / "experiments/crta_v3_mcr_source_informativeness_ladder_v1/SUMMARY_V1.json"
ORIGINAL_ROOT = ROOT / "experiments/crta_v3_mcr_factorial_semisynth_v1"
NULL_ROOT = ROOT / "experiments/crta_v3_mcr_null_source_v1"
DEFAULT_OUT = ROOT / "experiments/crta_v3_mcr_null_source_mass_ladder_v1"
DEFAULT_INPUT = Path(
    "data/foundation/artifacts/foundation_v2/"
    "raw_adapter_source_locks_v2_3_20260724/"
    "nhanes_common_panel_source_lock_v2/nhanes_common_panel_tokens_v2.parquet"
)
FAMILIES = ("additive", "pairwise", "sparse")
BACKBONES = ("xgb", "histgb")
ARMS = ("m1c1rf", "m1c0rf", "m0c1rf", "m0c0rf")
NEW_MASSES = (128, 512)
ALL_MASSES = (128, 512, 2048)
K = 32
N_REALIZATIONS = 20
ROW_NS = "mcr_null_source_mass_ladder_rows_v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def nested_source_positions(base: Any, family: str, realization: int,
                            n_total: int) -> dict[int, np.ndarray]:
    rng = np.random.default_rng(base.stable_seed(ROW_NS, family, realization))
    order = rng.permutation(n_total)
    selected = {
        mass: np.sort(order[:mass]).astype(np.int64, copy=False)
        for mass in ALL_MASSES
    }
    sets = {mass: set(values.tolist()) for mass, values in selected.items()}
    if not sets[128].issubset(sets[512]) or not sets[512].issubset(sets[2048]):
        raise AssertionError("source position sets are not nested")
    if not np.array_equal(selected[2048], np.arange(n_total)):
        raise AssertionError("full mass does not recover the frozen source block")
    return selected


def load_cell(root: Path, family: str, realization: int,
              original: bool) -> tuple[Path, dict[str, Any]]:
    if original:
        path = root / "primary" / family / f"r{realization:02d}" / "metrics.json"
    else:
        path = root / family / f"r{realization:02d}" / "metrics.json"
    if not path.is_file():
        raise RuntimeError(f"missing frozen cell: {path}")
    return path, json.loads(path.read_text())


def max_abs_corr(x: np.ndarray, y: np.ndarray) -> float:
    values = []
    for column in x.T:
        if np.std(column) == 0 or np.std(y) == 0:
            continue
        values.append(abs(float(np.corrcoef(column, y)[0, 1])))
    return max(values, default=0.0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--families", nargs="*", default=list(FAMILIES))
    parser.add_argument("--realizations", nargs="*", type=int,
                        default=list(range(N_REALIZATIONS)))
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if not set(args.families).issubset(FAMILIES):
        raise RuntimeError(f"invalid families: {args.families}")
    if any(r not in range(N_REALIZATIONS) for r in args.realizations):
        raise RuntimeError(f"invalid realizations: {args.realizations}")

    trigger = json.loads(TRIGGER_SUMMARY.read_text())
    if not trigger["verdicts"]["B_mass_ladder_triggered"]:
        raise RuntimeError("the frozen B trigger did not fire")
    base = load("mcr_mass_base", BASE_RUNNER)
    null = load("mcr_mass_null", NULL_RUNNER)
    panel = base.load_panel(args.input)
    provenance = {
        "runner_sha256": sha256_file(Path(__file__)),
        "base_runner_sha256": sha256_file(BASE_RUNNER),
        "null_runner_sha256": sha256_file(NULL_RUNNER),
        "prereg_sha256": sha256_file(PREREG),
        "trigger_summary_sha256": sha256_file(TRIGGER_SUMMARY),
        "input_sha256": sha256_file(args.input),
    }
    for family in args.families:
        for realization in args.realizations:
            load_cell(ORIGINAL_ROOT, family, realization, original=True)
            load_cell(NULL_ROOT, family, realization, original=False)
    if args.validate_only:
        print(json.dumps({
            "expected_cells": len(args.families) * len(args.realizations),
            "new_masses": list(NEW_MASSES),
            "reused_mass": 2048,
            "provenance": provenance,
        }, indent=1, sort_keys=True))
        return 0

    for family in args.families:
        for realization in args.realizations:
            out = args.out_root / family / f"r{realization:02d}" / "metrics.json"
            if out.is_file():
                existing = json.loads(out.read_text())
                if any(existing.get(k) != v for k, v in provenance.items()):
                    raise RuntimeError(f"provenance mismatch at {out}")
                continue
            started = time.time()
            original_path, original = load_cell(
                ORIGINAL_ROOT, family, realization, original=True)
            null_path, null_cell = load_cell(
                NULL_ROOT, family, realization, original=False)
            cell = base.build_cell(panel, "primary", family, realization, (K,))
            if base.json_ready(cell.audit) != original["audit"]:
                raise RuntimeError("rebuilt cell audit differs from original")

            source_y = np.asarray(cell.y[cell.source_rows], dtype=np.float64)
            if len(source_y) != 2048:
                raise RuntimeError(f"unexpected full source mass {len(source_y)}")
            positions = nested_source_positions(
                base, family, realization, len(source_y))
            full_perm = null.derangement(base, family, realization, len(source_y))
            full_hash = hashlib.sha256(
                full_perm.astype("<i8", copy=False).tobytes()).hexdigest()
            if full_hash != null_cell["source_label_intervention"]["permutation_sha256"]:
                raise RuntimeError("full derangement does not match frozen null")

            y_query = np.asarray(cell.y[cell.query_rows], dtype=np.float64)
            query_var = float(np.var(y_query, ddof=0))
            if query_var <= 0:
                raise RuntimeError("non-positive query variance")
            reference = base.arm_matrices(cell, "m1c1rf", K, weighted=False)
            reference_x = reference[0][:len(source_y), :len(base.FEATURES)]

            construction: dict[str, Any] = {}
            results: dict[str, Any] = {}
            for mass in NEW_MASSES:
                selected = positions[mass]
                subset_y = source_y[selected]
                perm = null.derangement(base, family, realization, mass)
                if np.any(perm == np.arange(mass)):
                    raise AssertionError("subset derangement has fixed points")
                shuffled_y = subset_y[perm]
                if not np.array_equal(np.sort(subset_y), np.sort(shuffled_y)):
                    raise AssertionError("subset label multiset changed")
                construction[str(mass)] = {
                    "selected_positions_sha256": hashlib.sha256(
                        selected.astype("<i8", copy=False).tobytes()).hexdigest(),
                    "derangement_sha256": hashlib.sha256(
                        perm.astype("<i8", copy=False).tobytes()).hexdigest(),
                    "fixed_points": int(np.sum(perm == np.arange(mass))),
                    "label_multiset_identical": True,
                    "max_abs_source_feature_label_corr_after": max_abs_corr(
                        reference_x[selected], shuffled_y),
                }
                results[str(mass)] = {}
                for backbone in BACKBONES:
                    results[str(mass)][backbone] = {}
                    for arm in ARMS:
                        x_fit, y_fit, _, x_query, constraints = base.arm_matrices(
                            cell, arm, K, weighted=False)
                        if not np.array_equal(y_fit[:len(source_y)], source_y):
                            raise AssertionError("unexpected original source labels")
                        mass_x = np.vstack([
                            x_fit[selected], x_fit[len(source_y):],
                        ])
                        mass_y = np.concatenate([
                            shuffled_y, y_fit[len(source_y):],
                        ])
                        prediction = base.fit_predict(
                            backbone, mass_x, mass_y, np.ones(len(mass_y)),
                            x_query, constraints, seed=realization,
                            threads=args.threads)
                        mse = float(np.mean((y_query - prediction) ** 2))
                        results[str(mass)][backbone][arm] = {
                            "nmse": mse / query_var,
                            "nrmse": float(np.sqrt(mse / query_var)),
                        }

            payload = {
                "experiment": "mcr_null_source_mass_ladder_v1",
                "family": family,
                "realization": realization,
                "support_k": K,
                "new_source_masses": list(NEW_MASSES),
                "reused_source_mass": 2048,
                "arms": list(ARMS),
                "backbones": list(BACKBONES),
                "source_position_sets_nested": True,
                "full_derangement_sha256": full_hash,
                "construction": construction,
                "results": results,
                "original_metrics_sha256": sha256_file(original_path),
                "null_metrics_sha256": sha256_file(null_path),
                "wall_seconds": round(time.time() - started, 3),
                **provenance,
            }
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
            print(json.dumps({
                "family": family, "realization": realization,
                "wall_seconds": payload["wall_seconds"], "done": True,
            }), flush=True)
    print(json.dumps({"status": "complete"}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
