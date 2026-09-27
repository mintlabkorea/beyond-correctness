#!/usr/bin/env python3
"""Adjudicate the label-permuted-source falsification of M x C."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "experiments/crta_v3_mcr_null_source_v1"
ORIGINAL_SUMMARY = (
    ROOT / "experiments/crta_v3_mcr_factorial_semisynth_v1/SUMMARY_V1.json"
)
FAMILIES = ("additive", "pairwise", "sparse")
BACKBONES = ("xgb", "histgb")
ARMS = ("m1c1rf", "m1c0rf", "m0c1rf", "m0c0rf")
K = "32"
EXPECTED_REALIZATIONS = set(range(20))
REPS = 10000
SEED = 20260820
MARGIN = 0.05


def q(arms: dict[str, Any], arm: str) -> float:
    return -float(arms[arm]["nmse"])


def interaction(arms: dict[str, Any]) -> float:
    return (q(arms, "m1c1rf") - q(arms, "m1c0rf")
            - q(arms, "m0c1rf") + q(arms, "m0c0rf"))


def stats(values: np.ndarray, key: str) -> dict[str, Any]:
    seed = int(hashlib.sha256(
        f"mcr_null_source_v1|{SEED}|{key}".encode()
    ).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    means = values[rng.integers(0, len(values), size=(REPS, len(values)))].mean(1)
    lo, hi = (float(np.quantile(means, 0.025)),
              float(np.quantile(means, 0.975)))
    mean = float(values.mean())
    contains_zero = bool(lo <= 0 <= hi)
    ci_within_margin = bool(lo > -MARGIN and hi < MARGIN)
    return {
        "mean": mean,
        "ci95": [lo, hi],
        "win": float(np.mean(values > 0)),
        "n": len(values),
        "ci_contains_zero": contains_zero,
        "mean_within_margin": bool(abs(mean) < MARGIN),
        "ci_within_equivalence_margin": ci_within_margin,
        "falsification_pass": bool(contains_zero and ci_within_margin),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()

    cells = [json.loads(path.read_text())
             for path in sorted(args.root.glob("*/r*/metrics.json"))]
    provenance = {
        (cell.get("runner_sha256"), cell.get("base_runner_sha256"),
         cell.get("prereg_sha256"), cell.get("input_sha256"))
        for cell in cells
    }
    if len(provenance) > 1:
        raise RuntimeError("mixed provenance in null-source result tree")
    complete = bool(cells) and all(
        {cell["realization"] for cell in cells if cell["family"] == family}
        == EXPECTED_REALIZATIONS
        for family in FAMILIES
    )
    checks = {
        "all_label_multisets_identical": bool(cells) and all(
            cell["source_label_intervention"]["label_multiset_identical"]
            for cell in cells),
        "all_permutations_have_zero_fixed_points": bool(cells) and all(
            cell["source_label_intervention"]["fixed_points"] == 0
            for cell in cells),
        "max_abs_feature_label_corr_after": max((
            cell["source_label_intervention"][
                "max_abs_true_source_feature_label_corr_after"
            ] for cell in cells
        ), default=None),
    }

    results: dict[str, Any] = {}
    for backbone in BACKBONES:
        results[backbone] = {}
        for family in FAMILIES:
            values = np.asarray([
                interaction(cell["results"][K][backbone])
                for cell in cells if cell["family"] == family
            ], dtype=float)
            if len(values):
                results[backbone][family] = stats(
                    values, f"{backbone}|{family}")

    original = json.loads(ORIGINAL_SUMMARY.read_text())
    original_reference = {
        backbone: {
            family: original["primary"][f"{backbone}_K{K}"][
                "P4_MC_interaction"
            ][family]
            for family in FAMILIES
        }
        for backbone in BACKBONES
    }
    grid_pass = bool(
        complete
        and checks["all_label_multisets_identical"]
        and checks["all_permutations_have_zero_fixed_points"]
        and all(results[backbone][family]["falsification_pass"]
                for backbone in BACKBONES for family in FAMILIES)
    )
    verdict: dict[str, Any]
    if complete:
        verdict = {
            "NULL_SOURCE_P1_equivalent_to_zero_all_6_strata": grid_pass,
            "status": "pass" if grid_pass else "fail_quarantine_MCxC_mechanism_claim",
        }
    else:
        verdict = {"status": "incomplete_verdict_withheld"}

    payload = {
        "complete": complete,
        "n_cells": len(cells),
        "metric": "Q=-MSE/Var(y_query)",
        "estimand": "Q(m1c1rf)-Q(m1c0rf)-Q(m0c1rf)+Q(m0c0rf)",
        "bootstrap": {
            "unit": "realization within fixed family",
            "reps": REPS,
            "seed": SEED,
        },
        "equivalence_margin": [-MARGIN, MARGIN],
        "construction_checks": checks,
        "results": results,
        "original_signal_source_reference": original_reference,
        "verdict": verdict,
        "provenance_variants": [list(item) for item in sorted(provenance)],
    }
    args.root.mkdir(parents=True, exist_ok=True)
    out = args.root / "SUMMARY_V1.json"
    out.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"written": str(out), "verdict": verdict}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
