#!/usr/bin/env python3
"""Frozen adjudicator for exhaustive N5 finite-lesion calibration."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "experiments/crta_v3_mcr_n5_exhaustive_v1"
DEFAULT_ORIGINAL = ROOT / "experiments/crta_v3_mcr_factorial_semisynth_v1"
FAMILIES = ("additive", "pairwise", "sparse")
BACKBONES = ("xgb", "histgb")
EXPECTED = 20
REPS = 10000
MC_REPS = 100000


def bootstrap(values: np.ndarray, key: str) -> dict:
    seed = int(hashlib.sha256(f"n5ex|20260820|{key}".encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    means = values[rng.integers(0, len(values), size=(REPS, len(values)))].mean(1)
    lo, hi = np.quantile(means, [0.025, 0.975])
    return {"mean": float(values.mean()), "ci95": [float(lo), float(hi)],
            "win": float(np.mean(values > 0)), "n": len(values),
            "separated": bool(lo > 0 and np.mean(values > 0) >= 0.60)}


def original_n5(root: Path, family: str, backbone: str) -> float | None:
    values = []
    for p in sorted(root.glob(f"primary/{family}/r*/metrics.json")):
        c = json.loads(p.read_text())
        arms = c["results"]["32"][backbone]
        values.append(-float(arms["m1c0r1"]["nmse"])
                      + float(arms["c_deranged2"]["nmse"]))
    return float(np.mean(values)) if values else None


def calibration(cells: list[dict], backbone: str, key: str,
                observed: float | None) -> dict:
    seed = int(hashlib.sha256(f"n5mc|20260820|{key}".encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    simulations = np.zeros(MC_REPS)
    cell_sd = []
    for cell in cells:
        q = -np.asarray(cell["results"][backbone]["deranged_nmse"], dtype=float)
        cell_sd.append(float(q.std(ddof=0)))
        a = rng.integers(0, len(q), size=MC_REPS)
        b = rng.integers(0, len(q) - 1, size=MC_REPS)
        b = b + (b >= a)
        simulations += q[a] - q[b]
    simulations /= len(cells)
    abs_sim = np.abs(simulations)
    out = {
        "mean_cell_lesion_sd": float(np.mean(cell_sd)),
        "signed_quantiles": [float(x) for x in np.quantile(
            simulations, [0.005, 0.025, 0.975, 0.995])],
        "absolute_q95_q99": [float(x) for x in np.quantile(abs_sim, [0.95, 0.99])],
    }
    if observed is not None:
        out["original_two_draw_mean"] = observed
        out["two_sided_tail_probability"] = float(np.mean(abs_sim >= abs(observed)))
        out["within_preregistered_margin_0p05"] = bool(abs(observed) <= 0.05)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--original-root", type=Path, default=DEFAULT_ORIGINAL)
    args = ap.parse_args()
    cells = [json.loads(p.read_text())
             for p in sorted(args.root.glob("*/r*/metrics.json"))]
    complete = all(len([c for c in cells if c["family"] == f]) == EXPECTED
                   for f in FAMILIES)
    sections = {}
    for backbone in BACKBONES:
        sections[backbone] = {}
        for family in FAMILIES:
            fam = [c for c in cells if c["family"] == family]
            if not fam:
                continue
            p2 = np.asarray([
                -c["results"][backbone]["correct_nmse"]
                - np.mean(-np.asarray(c["results"][backbone]["deranged_nmse"]))
                for c in fam])
            observed = original_n5(args.original_root, family, backbone)
            sections[backbone][family] = {
                "P2_correct_vs_lesion_average": bootstrap(
                    p2, f"{backbone}|{family}|p2"),
                "two_draw_calibration": calibration(
                    fam, backbone, f"{backbone}|{family}", observed),
            }
        sections[backbone]["all_families_P2_separated"] = bool(all(
            sections[backbone][f]["P2_correct_vs_lesion_average"]["separated"]
            for f in FAMILIES if f in sections[backbone]))
    verdict = ({
        "N5_P1_correct_beats_finite_lesion_average_both_backbones": bool(all(
            sections[b]["all_families_P2_separated"] for b in BACKBONES)),
        "N5_P2_original_draws_within_margin_all": bool(all(
            sections[b][f]["two_draw_calibration"].get(
                "within_preregistered_margin_0p05", False)
            for b in BACKBONES for f in FAMILIES)),
    } if complete else {"status": "incomplete — verdicts withheld"})
    payload = {"n_cells": len(cells), "complete": complete,
               "monte_carlo_reps": MC_REPS, "verdicts": verdict,
               "results": sections}
    out = args.root / "SUMMARY_V1.json"
    out.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"written": str(out), "verdicts": verdict}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
