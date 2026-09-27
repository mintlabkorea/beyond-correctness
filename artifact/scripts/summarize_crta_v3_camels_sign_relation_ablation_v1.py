#!/usr/bin/env python3
"""Adjudicate GC-REL, the CAMELS per-relation sign ablation.

Reuses the frozen v2 adjudicator's clustering unit (query basin), bootstrap
reps/seed and win threshold by importing them, so the numbers here are
comparable to `SUMMARY_V2.json` cell for cell.

One rule is ADDED rather than inherited.  v2's `separated` is one-sided
(mean > 0, CI low > 0): it can only express "the documented sign is
better".  GC-REL-P2 admits an outcome v2 could not represent -- flipping
the PET relation might IMPROVE prediction, meaning the declared direction
is wrong at daily resolution.  `direction()` therefore reports a
three-way verdict on the same interval: degrades / improves / inert.

Preregistration:
`iclr_latex_v3/SCHEMA_PAIR_GENERALIZATION_PREREGISTRATION_V1.md` section 9.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
V2_SUMMARIZER = ROOT / "scripts/summarize_crta_v3_camels_sign_probe_v2.py"
V2_REFERENCE_BOTH_FLIP = 0.18422  # frozen v2 GCv2-P1 log1p_rmse mean gain
P0_TOLERANCE = 1e-5               # GC-REL-P0 bar, on the rounded v2 figure
REFERENCE_ARM = "sign_documented"
SINGLE_FLIP_ARMS = ("flip_precip_only", "flip_pet_only")
METRICS = (("log1p_rmse", True), ("nse", False))
EXPECTED_ARMS = frozenset({"sign_documented", "flip_precip_only",
                           "flip_pet_only", "sign_flipped"})
EXPECTED_CELLS = 60
EXPECTED_BASINS = 12


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


V2 = _load("camels_sign_v2_summary", V2_SUMMARIZER)


def load_basin_combo(root: Path, weights: dict[str, float], metric: str,
                     lower_better: bool) -> dict[str, np.ndarray]:
    """Per-(basin, cell) linear combination of arm metrics.

    All arms are fit on the SAME fold inside one cell, so a per-cell linear
    combination is paired and needs no extra alignment.  `sign` flips the
    orientation so a positive value always means "the documented sign is
    better", matching v2's convention.
    """
    sign = 1.0 if lower_better else -1.0
    per_basin: dict[str, list[float]] = {}
    for path in sorted(root.glob("support_*/seed_*/metrics.json")):
        arms = json.loads(path.read_text(encoding="utf-8"))["arms"]
        basins = arms[REFERENCE_ARM]["per_basin"]
        for basin in basins:
            value = sign * sum(
                w * arms[arm]["per_basin"][basin][metric]
                for arm, w in weights.items())
            if np.isfinite(value):
                per_basin.setdefault(basin, []).append(float(value))
    return {b: np.asarray(v) for b, v in per_basin.items()}


def validate(root: Path) -> dict:
    """Fail loudly on a stale, partial or wrong-arm root.

    Cells are skipped by `metrics.json` existence alone, so a root polluted
    by a smoke run or a different arm set would otherwise be summarised
    silently.
    """
    paths = sorted(root.glob("support_*/seed_*/metrics.json"))
    if len(paths) != EXPECTED_CELLS:
        raise SystemExit(f"{root}: expected {EXPECTED_CELLS} cells, found {len(paths)}")
    for path in paths:
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("addendum") != "GC-REL":
            raise SystemExit(f"{path}: not a GC-REL cell")
        if set(record["arms"]) != EXPECTED_ARMS:
            raise SystemExit(f"{path}: arms {sorted(record['arms'])} != expected")
        for arm in EXPECTED_ARMS:
            if len(record["arms"][arm]["per_basin"]) != EXPECTED_BASINS:
                raise SystemExit(f"{path}: arm {arm} lacks {EXPECTED_BASINS} basins")
    return {"n_cells": len(paths), "arms": sorted(EXPECTED_ARMS),
            "n_basins": EXPECTED_BASINS}


def basin_mean_bootstrap(values: dict[str, np.ndarray]) -> dict:
    """Robustness CI that resamples ONLY the 12 basin means.

    v2's `hierarchical_ci` resamples basins and then, independently, the
    cells inside each drawn basin.  The cells are crossed with basins
    rather than nested in them -- one fitted (support, seed, arm) model is
    scored on all 12 basins -- so that inner resample breaks the shared-cell
    covariance.  Averaging cells within a basin first makes the 12 basin
    means the only resampled unit, which matches the declared population
    unit exactly.  Reported alongside, never in place of, the frozen v2
    interval, so GC-REL stays cell-for-cell comparable with v2.
    """
    rng = np.random.default_rng(V2.BOOTSTRAP_SEED)
    keys = sorted(values)
    per_basin = np.array([float(np.mean(values[k])) for k in keys])
    draws = rng.choice(per_basin, size=(V2.BOOTSTRAP_REPS, len(per_basin)),
                       replace=True).mean(axis=1)
    return {
        "mean_of_basin_means": float(per_basin.mean()),
        "ci95": [float(np.quantile(draws, 0.025)),
                 float(np.quantile(draws, 0.975))],
        "n_basins": len(per_basin),
        "n_basins_negative": int((per_basin < 0).sum()),
    }


def direction(result: dict) -> str:
    """Three-way verdict on the basin-clustered interval."""
    low, high = result["ci95"]
    if low > 0.0:
        return "degrades (documented sign is better)"
    if high < 0.0:
        return "improves (documented sign is WRONG for this relation)"
    return "inert (interval contains zero)"


def contrast(root: Path, weights: dict[str, float]) -> dict:
    out = {}
    for metric, lower_better in METRICS:
        basins = load_basin_combo(root, weights, metric, lower_better)
        result = V2.analyze(basins)
        result.pop("per_basin_mean", None)
        result["direction"] = direction(result)
        robust = basin_mean_bootstrap(basins)
        robust["direction"] = direction(robust)
        result["robustness_basin_mean_bootstrap"] = robust
        out[metric] = result
    return out


def check_p0(root: Path, v2_root: Path | None) -> dict:
    """Reference and both-flip arms must reproduce v2 exactly."""
    both = contrast(root, {"sign_flipped": 1.0, REFERENCE_ARM: -1.0})
    mean = both["log1p_rmse"]["mean_gain"]
    report = {
        "both_flip_mean_gain_log1p_rmse": mean,
        "v2_reference": V2_REFERENCE_BOTH_FLIP,
        "abs_delta": abs(mean - V2_REFERENCE_BOTH_FLIP),
        "reproduces_v2_within_tolerance": bool(
            abs(mean - V2_REFERENCE_BOTH_FLIP) <= P0_TOLERANCE),
    }
    if v2_root is not None:
        worst, compared = 0.0, 0
        for path in sorted(root.glob("support_*/seed_*/metrics.json")):
            twin = v2_root / path.relative_to(root)
            if not twin.is_file():
                continue
            new = json.loads(path.read_text(encoding="utf-8"))["arms"]
            old = json.loads(twin.read_text(encoding="utf-8"))["arms"]
            for arm in (REFERENCE_ARM, "sign_flipped"):
                for basin, values in new[arm]["per_basin"].items():
                    for metric, _ in METRICS:
                        worst = max(worst, abs(
                            values[metric] - old[arm]["per_basin"][basin][metric]))
                        compared += 1
        report["v2_cellwise_cells_compared"] = compared
        report["v2_cellwise_max_abs_delta"] = worst
        report["v2_cellwise_bit_identical"] = bool(worst == 0.0)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--v2-root", type=Path, default=None,
                        help="frozen v2 probe root, for the P0 cell-wise check")
    args = parser.parse_args()

    validated = validate(args.root)
    both = contrast(args.root, {"sign_flipped": 1.0, REFERENCE_ARM: -1.0})
    singles = {arm: contrast(args.root, {arm: 1.0, REFERENCE_ARM: -1.0})
               for arm in SINGLE_FLIP_ARMS}
    # Write D, P, E, B for the documented, precip-flipped, PET-flipped and
    # both-flipped losses.  The single-flip contrasts P-D and E-D are SIMPLE
    # effects: each holds the other relation at its documented direction, so
    # neither is a unique share of the joint effect B-D, and in general
    # (P-D) + (E-D) != B-D.  Two additions close that gap, both computed from
    # arms that already exist:
    #   * the opposite conditional for each relation (B-P is PET's effect given
    #     precipitation already flipped; B-E is precipitation's given PET
    #     flipped), which tests whether a relation is inert only in the
    #     documented context;
    #   * Shapley effects, which average a relation's two conditionals and so
    #     sum EXACTLY to B-D:  phi_P = .5[(P-D)+(B-E)], phi_E = .5[(E-D)+(B-P)].
    interaction = contrast(args.root, {
        "sign_flipped": 1.0, "flip_precip_only": -1.0,
        "flip_pet_only": -1.0, REFERENCE_ARM: 1.0})
    conditionals = {
        "pet_given_flipped_precip_B_minus_P": contrast(args.root, {
            "sign_flipped": 1.0, "flip_precip_only": -1.0}),
        "precip_given_flipped_pet_B_minus_E": contrast(args.root, {
            "sign_flipped": 1.0, "flip_pet_only": -1.0}),
    }
    shapley = {
        "flip_precip_only": contrast(args.root, {
            "flip_precip_only": 0.5, "sign_flipped": 0.5,
            REFERENCE_ARM: -0.5, "flip_pet_only": -0.5}),
        "flip_pet_only": contrast(args.root, {
            "flip_pet_only": 0.5, "sign_flipped": 0.5,
            REFERENCE_ARM: -0.5, "flip_precip_only": -0.5}),
    }

    both_mean = both["log1p_rmse"]["mean_gain"]
    shares = {arm: singles[arm]["log1p_rmse"]["mean_gain"] / both_mean
              for arm in SINGLE_FLIP_ARMS}
    shapley_shares = {arm: shapley[arm]["log1p_rmse"]["mean_gain"] / both_mean
                      for arm in SINGLE_FLIP_ARMS}
    shapley_sum = sum(shapley[arm]["log1p_rmse"]["mean_gain"]
                      for arm in SINGLE_FLIP_ARMS)
    precip = singles["flip_precip_only"]["log1p_rmse"]
    pet = singles["flip_pet_only"]["log1p_rmse"]

    summary = {
        "probe_root": str(args.root),
        "task": "N1_camels_us2gb", "addendum": "GC-REL",
        "clustering": "query basin (independent population unit)",
        "bootstrap": {"reps": V2.BOOTSTRAP_REPS, "seed": V2.BOOTSTRAP_SEED,
                      "win_threshold": V2.WIN_THRESHOLD},
        "validation": validated,
        "GC_REL_P0_pipeline_identity": check_p0(args.root, args.v2_root),
        "both_flip_reference": both,
        "single_flip": singles,
        "interaction_B_minus_P_minus_E_plus_D": interaction,
        "opposite_conditional_effects": conditionals,
        "shapley_effects": shapley,
        "simple_effect_share_of_both_flip_log1p_rmse": shares,
        "shapley_share_of_both_flip_log1p_rmse": shapley_shares,
        "shapley_sums_to_both_flip": {
            "sum_of_shapley_effects": shapley_sum,
            "both_flip_mean_gain": both_mean,
            "abs_delta": abs(shapley_sum - both_mean),
            "exact_within_1e_12": bool(abs(shapley_sum - both_mean) < 1e-12)},
        "attribution_note":
            "simple-effect shares are reported for continuity with the frozen "
            "preregistration but are NOT an identified decomposition; the "
            "Shapley effects are, and they sum exactly to the both-flip effect",
        "GC_REL_P1_pass": bool(precip["separated"]
                               and shares["flip_precip_only"] >= 0.5),
        "GC_REL_P1_pass_shapley": bool(
            shapley["flip_precip_only"]["log1p_rmse"]["separated"]
            and shapley_shares["flip_precip_only"] >= 0.5),
        "GC_REL_P2_pet_inert_in_both_contexts": bool(
            not pet["separated"]
            and not conditionals["pet_given_flipped_precip_B_minus_P"]
                                ["log1p_rmse"]["separated"]),
        "GC_REL_P2_pass_no_pet_identification": bool(not pet["separated"]),
        "GC_REL_P2_case": pet["direction"],
    }
    summary["GC_REL_P0_pass"] = bool(
        summary["GC_REL_P0_pipeline_identity"]["reproduces_v2_within_tolerance"])
    (args.root / "SUMMARY_GC_REL.json").write_text(
        json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
