#!/usr/bin/env python3
"""Adjudicate the triggered alpha=1 source-mass ladder."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


FAMILIES = ("additive", "pairwise", "sparse")
BACKBONES = ("xgb", "histgb")
ARMS = ("m1c1rf", "m1c0rf", "m0c1rf", "m0c0rf")
MASSES = (128, 512, 2048)
K = "32"
REPS = 10_000
SEED = 20260820


def interaction(values: dict[str, float]) -> float:
    return (values["m1c1rf"] - values["m1c0rf"]
            - values["m0c1rf"] + values["m0c0rf"])


def q_internal(record: dict, mass: int, backbone: str, arm: str) -> float:
    return -float(record["results"][str(mass)][backbone][arm]["nmse"])


def q_null(record: dict, backbone: str, arm: str) -> float:
    return -float(record["results"][K][backbone][arm]["nmse"])


def bootstrap_mean(values: np.ndarray, key: str) -> tuple[float, list[float]]:
    seed = int(hashlib.sha256(
        f"mcr_null_mass|{SEED}|{key}".encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    chosen = rng.integers(0, len(values), size=(REPS, len(values)))
    means = values[chosen].mean(axis=1)
    lo, hi = np.quantile(means, [0.025, 0.975])
    return float(values.mean()), [float(lo), float(hi)]


def load_cells(root: Path) -> dict[tuple[str, int], dict]:
    cells = {}
    for path in sorted(root.glob("*/r*/metrics.json")):
        record = json.loads(path.read_text())
        key = (record["family"], int(record["realization"]))
        if key in cells:
            raise RuntimeError(f"duplicate cell {key}")
        cells[key] = record
    return cells


def classify(b1: bool, b2: bool) -> str:
    if b1 and b2:
        return "conflict_present_by_128_and_amplified_by_mass"
    if b1:
        return "conflict_present_by_128_mass_amplification_unconfirmed"
    if b2:
        return "harm_emerges_with_source_mass_extreme_regime_matters"
    return "mass_versus_collision_unresolved"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--internal-root", type=Path, required=True)
    parser.add_argument("--null-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    internal = load_cells(args.internal_root)
    null = load_cells(args.null_root)
    expected = {(f, r) for f in FAMILIES for r in range(20)}
    if set(internal) != expected or not expected.issubset(null):
        raise RuntimeError(
            f"incomplete grid internal={len(internal)} null={len(null)}")

    provenance = set()
    max_after_corr = 0.0
    for record in internal.values():
        provenance.add(tuple(record[key] for key in (
            "runner_sha256", "base_runner_sha256", "null_runner_sha256",
            "prereg_sha256", "trigger_summary_sha256", "input_sha256")))
        if not record["source_position_sets_nested"]:
            raise RuntimeError("source position nesting failed")
        if record["full_derangement_sha256"] != null[
                (record["family"], int(record["realization"]))
        ]["source_label_intervention"]["permutation_sha256"]:
            raise RuntimeError("full derangement hash mismatch")
        for audit in record["construction"].values():
            if audit["fixed_points"] != 0 or not audit["label_multiset_identical"]:
                raise RuntimeError("subset derangement construction failed")
            max_after_corr = max(
                max_after_corr,
                float(audit["max_abs_source_feature_label_corr_after"]))
    if len(provenance) != 1:
        raise RuntimeError("multiple provenance tuples")

    strata = {}
    b1_passes, b2_passes = [], []
    x = np.log2(np.asarray(MASSES, dtype=np.float64))
    for family in FAMILIES:
        strata[family] = {}
        for backbone in BACKBONES:
            curves = []
            for realization in range(20):
                key = (family, realization)
                curve = []
                for mass in MASSES:
                    if mass == 2048:
                        values = {
                            arm: q_null(null[key], backbone, arm) for arm in ARMS}
                    else:
                        values = {
                            arm: q_internal(internal[key], mass, backbone, arm)
                            for arm in ARMS}
                    curve.append(interaction(values))
                curves.append(curve)
            array = np.asarray(curves, dtype=np.float64)
            slopes = np.asarray([
                np.polyfit(x, curve, deg=1)[0] for curve in array
            ], dtype=np.float64)
            mean_128, ci_128 = bootstrap_mean(
                array[:, 0], f"{family}|{backbone}|I128")
            mean_slope, slope_ci = bootstrap_mean(
                slopes, f"{family}|{backbone}|slope")
            delta = array[:, 2] - array[:, 0]
            mean_delta, delta_ci = bootstrap_mean(
                delta, f"{family}|{backbone}|delta")
            b1 = bool(mean_128 < 0 and ci_128[1] < 0)
            b2 = bool(mean_slope < 0 and slope_ci[1] < 0)
            b1_passes.append(b1)
            b2_passes.append(b2)
            strata[family][backbone] = {
                "mean_I_MC_by_source_mass": {
                    str(m): float(v) for m, v in zip(MASSES, array.mean(axis=0))},
                "I_MC_128_mean": mean_128,
                "I_MC_128_ci95": ci_128,
                "mean_log2_mass_slope": mean_slope,
                "slope_ci95": slope_ci,
                "I_2048_minus_I_128_mean": mean_delta,
                "I_2048_minus_I_128_ci95": delta_ci,
                "B1_stratum_pass": b1,
                "B2_stratum_pass": b2,
            }

    b1_grid = bool(all(b1_passes))
    b2_grid = bool(all(b2_passes))
    payload = {
        "complete": True,
        "triggered_by_frozen_rule": True,
        "new_source_masses": [128, 512],
        "reused_observed_mass": 2048,
        "n_independent_realizations": 60,
        "construction": {
            "cells": len(internal),
            "one_provenance_tuple": True,
            "max_abs_deranged_source_feature_label_corr": max_after_corr,
        },
        "strata": strata,
        "verdicts": {
            "B1_low_mass_conflict_all_six": b1_grid,
            "B2_mass_amplification_all_six": b2_grid,
            "classification": classify(b1_grid, b2_grid),
        },
        "provenance_tuple": list(next(iter(provenance))),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps({
        "written": str(args.out), "verdicts": payload["verdicts"],
    }, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
