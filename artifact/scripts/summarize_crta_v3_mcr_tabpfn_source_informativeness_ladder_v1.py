#!/usr/bin/env python3
"""Adjudicate the five-point MCR-T (TabPFN) source-informativeness ladder.

Frozen rule (prereg P1-T): per family, the realization-level Spearman
correlation between alpha and I_MC(alpha) over the five levels must have a
negative mean and a 10,000-replicate realization-bootstrap CI95 below zero.
The primary verdict is the intersection of the three family strata.
alpha=0 comes from the frozen MCR-T factorial; the four doses come from the
ladder runner.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

FAMILIES = ("additive", "pairwise", "sparse")
ARMS = ("m1c1rf", "m1c0rf", "m0c1rf", "m0c0rf")
ALPHAS = (0.0, 0.25, 0.50, 0.75, 1.0)
REPS = 10_000
SEED = 20260820
N_REALIZATIONS = 20


def interaction(values: dict[str, float]) -> float:
    return (values["m1c1rf"] - values["m1c0rf"]
            - values["m0c1rf"] + values["m0c0rf"])


def q_alpha0(record: dict, arm: str) -> float:
    return -float(record["results"][arm]["nmse"])


def q_dose(record: dict, alpha: float, arm: str) -> float:
    return -float(record["results"][f"{alpha:.2f}"][arm]["nmse"])


def bootstrap_mean(values: np.ndarray, key: str) -> tuple[float, list[float]]:
    seed = int(hashlib.sha256(
        f"mcr_tabpfn_info_ladder|{SEED}|{key}".encode()).hexdigest()[:8], 16)
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
    parser.add_argument("--ladder-root", type=Path, required=True)
    parser.add_argument("--alpha0-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    ladder = load_cells(args.ladder_root)
    alpha0 = load_cells(args.alpha0_root)
    expected = {(family, realization)
                for family in FAMILIES for realization in range(N_REALIZATIONS)}
    if set(ladder) != expected or not expected.issubset(alpha0):
        raise RuntimeError(
            f"incomplete grid ladder={len(ladder)} alpha0={len(alpha0)}")

    provenance = set()
    max_moved_error = 0
    max_after_corr = 0.0
    for record in ladder.values():
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
                raise RuntimeError("permutation construction failed")
            if not (construction["matches_tree_ladder"]
                    or construction["matches_null_derangement"]):
                raise RuntimeError("dose is not anchored to a frozen permutation")
            max_moved_error = max(max_moved_error, abs(
                int(construction["realized_moved_rows"])
                - int(construction["target_moved_rows"])))
            max_after_corr = max(
                max_after_corr,
                float(construction["max_abs_source_feature_label_corr"]))
    if len(provenance) != 1 or max_moved_error > 1:
        raise RuntimeError("provenance or moved-count construction failure")

    strata = {}
    p1_passes = []
    for family in FAMILIES:
        realization_curves = []
        rhos = []
        for realization in range(N_REALIZATIONS):
            key = (family, realization)
            curve = []
            for alpha in ALPHAS:
                if alpha == 0.0:
                    values = {arm: q_alpha0(alpha0[key], arm) for arm in ARMS}
                else:
                    values = {arm: q_dose(ladder[key], alpha, arm)
                              for arm in ARMS}
                curve.append(interaction(values))
            realization_curves.append(curve)
            rhos.append(float(spearmanr(ALPHAS, curve).statistic))
        curves = np.asarray(realization_curves, dtype=np.float64)
        rho_values = np.asarray(rhos, dtype=np.float64)
        mean_rho, rho_ci = bootstrap_mean(rho_values, f"{family}|tabpfn|rho")
        mean_curve = curves.mean(axis=0).tolist()
        crossing = first_crossing(mean_curve)
        p1 = bool(mean_rho < 0 and rho_ci[1] < 0)
        p1_passes.append(p1)
        strata[family] = {
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
            "P1T_stratum_pass": p1,
        }

    payload = {
        "complete": True,
        "backbone": "tabpfn_7_regressor",
        "prior_observed": {
            "tree_ladder_verdict": True,
            "tabpfn_alpha0": True,
        },
        "new_doses": [0.25, 0.50, 0.75, 1.00],
        "n_realizations_per_family": N_REALIZATIONS,
        "construction": {
            "cells": len(ladder),
            "one_provenance_tuple": True,
            "max_moved_count_error": max_moved_error,
            "max_abs_partial_source_feature_label_corr": max_after_corr,
        },
        "strata": strata,
        "verdicts": {
            "P1T_all_three_family_strata_negative_monotone": bool(all(p1_passes)),
            "strata_passing": int(sum(p1_passes)),
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
