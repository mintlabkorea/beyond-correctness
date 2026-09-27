#!/usr/bin/env python3
"""Frozen adjudicator for the 5x5 M x C corruption surface."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "experiments/crta_v3_mcr_mc_surface_v1"
FAMILIES = ("additive", "pairwise", "sparse")
BACKBONES = ("xgb", "histgb")
DOSES = (0, 2, 4, 6, 8)
REPS = 10000


def stats(values: np.ndarray, key: str) -> dict:
    seed = int(hashlib.sha256(f"mcsurf|20260820|{key}".encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    means = values[rng.integers(0, len(values), (REPS, len(values)))].mean(1)
    lo, hi = np.quantile(means, [0.025, 0.975])
    return {"mean": float(values.mean()), "ci95": [float(lo), float(hi)],
            "win": float(np.mean(values > 0)), "n": len(values),
            "separated": bool(lo > 0 and np.mean(values > 0) >= 0.60)}


def q(cell: dict, backbone: str, m: int, c: int) -> float:
    return -float(cell["results"][backbone][str(m)][str(c)])


def rectangle(cell: dict, backbone: str, lo: int, hi: int,
              clo: int | None = None, chi: int | None = None) -> float:
    clo, chi = (lo if clo is None else clo), (hi if chi is None else chi)
    return (q(cell, backbone, lo, clo) - q(cell, backbone, hi, clo)
            - q(cell, backbone, lo, chi) + q(cell, backbone, hi, chi))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = ap.parse_args()
    cells = [json.loads(p.read_text())
             for p in sorted(args.root.glob("*/r*/metrics.json"))]
    complete = all(len([c for c in cells if c["family"] == f]) == 20
                   for f in FAMILIES)
    results = {}
    for backbone in BACKBONES:
        results[backbone] = {}
        for family in FAMILIES:
            fam = [c for c in cells if c["family"] == family]
            if not fam:
                continue
            moderate = np.asarray([rectangle(c, backbone, 0, 4) for c in fam])
            interior = np.asarray([np.mean([
                rectangle(c, backbone, lo, hi, clo, chi)
                for lo, hi in zip(DOSES[:3], DOSES[1:4])
                for clo, chi in zip(DOSES[:3], DOSES[1:4])]) for c in fam])
            all_adjacent = np.asarray([np.mean([
                rectangle(c, backbone, lo, hi, clo, chi)
                for lo, hi in zip(DOSES[:-1], DOSES[1:])
                for clo, chi in zip(DOSES[:-1], DOSES[1:])]) for c in fam])
            saturation = np.asarray([
                rectangle(c, backbone, 0, 4) - rectangle(c, backbone, 4, 8)
                for c in fam])
            rhos_m, rhos_c = [], []
            for cell in fam:
                rhos_m.extend(spearmanr(DOSES,
                    [cell["results"][backbone][str(m)]["0"] for m in DOSES]).statistic
                    for _ in [0])
                rhos_c.extend(spearmanr(DOSES,
                    [cell["results"][backbone]["0"][str(c)] for c in DOSES]).statistic
                    for _ in [0])
            results[backbone][family] = {
                "I_moderate_0_vs_4": stats(moderate, f"{backbone}|{family}|mod"),
                "I_mean_interior_adjacent": stats(interior, f"{backbone}|{family}|int"),
                "I_mean_all_adjacent": stats(all_adjacent, f"{backbone}|{family}|all"),
                "moderate_minus_extreme_interaction": stats(
                    saturation, f"{backbone}|{family}|sat"),
                "mean_axis_spearman_nmse": {
                    "m_at_c0": float(np.nanmean(rhos_m)),
                    "c_at_m0": float(np.nanmean(rhos_c)),
                },
                "mean_nmse_surface": {
                    str(m): {str(c): float(np.mean([
                        x["results"][backbone][str(m)][str(c)] for x in fam]))
                             for c in DOSES} for m in DOSES},
            }
        results[backbone]["all_families_moderate_separated"] = bool(all(
            results[backbone][f]["I_moderate_0_vs_4"]["separated"]
            for f in FAMILIES if f in results[backbone]))
    verdict = ({
        "MC_SURFACE_P1_moderate_complementarity_both_backbones": bool(all(
            results[b]["all_families_moderate_separated"] for b in BACKBONES))
    } if complete else {"status": "incomplete — verdicts withheld"})
    payload = {"n_cells": len(cells), "complete": complete,
               "verdicts": verdict, "results": results}
    out = args.root / "SUMMARY_V1.json"
    out.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"written": str(out), "verdicts": verdict}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
