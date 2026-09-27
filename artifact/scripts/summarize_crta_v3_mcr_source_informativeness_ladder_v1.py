#!/usr/bin/env python3
"""Adjudicate the five-point MCR source-informativeness ladder."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr


FAMILIES = ("additive", "pairwise", "sparse")
BACKBONES = ("xgb", "histgb")
ARMS = ("m1c1rf", "m1c0rf", "m0c1rf", "m0c0rf")
ALPHAS = (0.0, 0.25, 0.50, 0.75, 1.0)
REPS = 10_000
SEED = 20260820
K = "32"


def q(record: dict, backbone: str, arm: str) -> float:
    return -float(record["results"][K][backbone][arm]["nmse"])


def q_internal(record: dict, alpha: float, backbone: str, arm: str) -> float:
    return -float(record["results"][f"{alpha:.2f}"][backbone][arm]["nmse"])


def interaction(values: dict[str, float]) -> float:
    return (values["m1c1rf"] - values["m1c0rf"]
            - values["m0c1rf"] + values["m0c0rf"])


def bootstrap_mean(values: np.ndarray, key: str) -> tuple[float, list[float]]:
    seed = int(hashlib.sha256(f"mcr_info_ladder|{SEED}|{key}".encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    chosen = rng.integers(0, len(values), size=(REPS, len(values)))
    means = values[chosen].mean(axis=1)
    lo, hi = np.quantile(means, [0.025, 0.975])
    return float(values.mean()), [float(lo), float(hi)]


def load_cells(root: Path, internal: bool) -> dict[tuple[str, int], dict]:
    cells = {}
    pattern = "*/r*/metrics.json" if internal else "*/r*/metrics.json"
    for path in sorted(root.glob(pattern)):
        record = json.loads(path.read_text())
        key = (record["family"], int(record["realization"]))
        if key in cells:
            raise RuntimeError(f"duplicate cell {key} in {root}")
        cells[key] = record
    return cells


def first_crossing(curve: list[float]) -> list[float] | None:
    for index in range(len(curve) - 1):
        if curve[index] >= 0 and curve[index + 1] < 0:
            return [ALPHAS[index], ALPHAS[index + 1]]
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--internal-root", type=Path, required=True)
    parser.add_argument("--original-root", type=Path, required=True)
    parser.add_argument("--null-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    internal = load_cells(args.internal_root, internal=True)
    original = load_cells(args.original_root / "primary", internal=False)
    null = load_cells(args.null_root, internal=False)
    expected = {(family, realization) for family in FAMILIES for realization in range(20)}
    if set(internal) != expected or not expected.issubset(original) or not expected.issubset(null):
        raise RuntimeError(
            f"incomplete grid internal={len(internal)} original={len(original)} null={len(null)}")

    provenance = set()
    max_moved_error = 0
    max_after_corr = 0.0
    for record in internal.values():
        provenance.add((
            record["runner_sha256"], record["base_runner_sha256"],
            record["null_runner_sha256"], record["prereg_sha256"],
            record["input_sha256"],
        ))
        if not record.get("nested_corrupted_sets"):
            raise RuntimeError("nested corruption check failed")
        for construction in record["construction"].values():
            if not construction["permutation_bijective"] or not construction[
                    "label_multiset_identical"]:
                raise RuntimeError("partial permutation construction failed")
            max_moved_error = max(max_moved_error, abs(
                int(construction["realized_moved_rows"])
                - int(construction["target_moved_rows"])))
            max_after_corr = max(
                max_after_corr,
                float(construction["max_abs_source_feature_label_corr"]),
            )
    if len(provenance) != 1 or max_moved_error > 1:
        raise RuntimeError("provenance or moved-count construction failure")

    strata = {}
    p1_passes = []
    final_crossings = 0
    for family in FAMILIES:
        strata[family] = {}
        for backbone in BACKBONES:
            realization_curves = []
            rhos = []
            for realization in range(20):
                key = (family, realization)
                curve = []
                for alpha in ALPHAS:
                    if alpha == 0.0:
                        values = {arm: q(original[key], backbone, arm) for arm in ARMS}
                    elif alpha == 1.0:
                        values = {arm: q(null[key], backbone, arm) for arm in ARMS}
                    else:
                        values = {
                            arm: q_internal(internal[key], alpha, backbone, arm)
                            for arm in ARMS
                        }
                    curve.append(interaction(values))
                realization_curves.append(curve)
                rhos.append(float(spearmanr(ALPHAS, curve).statistic))
            curves = np.asarray(realization_curves, dtype=np.float64)
            rho_values = np.asarray(rhos, dtype=np.float64)
            mean_rho, rho_ci = bootstrap_mean(rho_values, f"{family}|{backbone}|rho")
            mean_curve = curves.mean(axis=0).tolist()
            crossing = first_crossing(mean_curve)
            if crossing == [0.75, 1.0]:
                final_crossings += 1
            p1 = bool(mean_rho < 0 and rho_ci[1] < 0)
            p1_passes.append(p1)
            strata[family][backbone] = {
                "mean_realization_spearman": mean_rho,
                "spearman_ci95": rho_ci,
                "realization_spearman": rho_values.tolist(),
                "mean_I_MC_by_alpha": {
                    f"{alpha:.2f}": float(value)
                    for alpha, value in zip(ALPHAS, mean_curve)
                },
                "adjacent_mean_changes": {
                    f"{ALPHAS[i]:.2f}->{ALPHAS[i+1]:.2f}": float(
                        mean_curve[i + 1] - mean_curve[i])
                    for i in range(len(ALPHAS) - 1)
                },
                "first_positive_to_negative_crossing": crossing,
                "P1_stratum_pass": p1,
            }

    p1_grid = bool(all(p1_passes))
    b_triggered = bool((not p1_grid) or final_crossings >= 4)
    trigger_reason = []
    if not p1_grid:
        trigger_reason.append("P1_failed_in_at_least_one_stratum")
    if final_crossings >= 4:
        trigger_reason.append("at_least_four_strata_cross_only_in_0.75_to_1.00")
    payload = {
        "complete": True,
        "prior_observed_endpoints": {"alpha_0": True, "alpha_1": True},
        "new_internal_alphas": [0.25, 0.50, 0.75],
        "n_independent_realizations": 60,
        "paired_backbones": list(BACKBONES),
        "construction": {
            "cells": len(internal),
            "one_provenance_tuple": True,
            "max_moved_count_error": max_moved_error,
            "max_abs_partial_source_feature_label_corr": max_after_corr,
        },
        "strata": strata,
        "verdicts": {
            "A_P1_all_six_negative_monotone": p1_grid,
            "final_interval_crossing_strata": final_crossings,
            "B_mass_ladder_triggered": b_triggered,
            "B_trigger_reasons": trigger_reason,
        },
        "provenance_tuple": list(next(iter(provenance))),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps({
        "written": str(args.out),
        "verdicts": payload["verdicts"],
    }, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
