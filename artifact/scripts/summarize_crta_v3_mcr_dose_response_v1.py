#!/usr/bin/env python3
"""Adjudicator for MCR-D (per-layer corruption dose-response).

Frozen rules: `iclr_latex_v3/MCR_DOSE_RESPONSE_PREREGISTRATION_V1.md`.
Per axis x family: per-realization Spearman rho(dose, nMSE), then a
realization-level bootstrap of the mean rho (10,000 reps, seed
20260820).  MCR-D-P1 per axis = mean rho > 0 and CI95 excludes 0 and
win >= 0.60 in all three families.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "experiments/crta_v3_mcr_dose_response_v1"

FAMILIES = ("additive", "pairwise", "sparse")
AXES = ("m", "c", "r")
EXPECTED_REALIZATIONS = 20
BOOTSTRAP_REPS = 10000
BOOTSTRAP_SEED = 20260820
WIN_THRESHOLD = 0.60


def bootstrap_stats(values: np.ndarray, seed_key: str) -> dict[str, Any]:
    seed = int(hashlib.sha256(
        f"mcr_d|{BOOTSTRAP_SEED}|{seed_key}".encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    samples = values[rng.integers(0, len(values),
                                  size=(BOOTSTRAP_REPS, len(values)))]
    means = samples.mean(axis=1)
    mean = float(values.mean())
    lower, upper = (float(np.quantile(means, 0.025)),
                    float(np.quantile(means, 0.975)))
    win = float(np.mean(values > 0))
    return {"mean_rho": mean, "ci95": [lower, upper], "win": win,
            "n": int(len(values)),
            "separated": bool(mean > 0 and lower > 0
                              and win >= WIN_THRESHOLD)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()

    cells = [json.loads(p.read_text())
             for p in sorted(args.root.glob("*/r*/metrics.json"))]
    cells = [c for c in cells if c["family"] in FAMILIES]
    provenance = {(c.get("runner_sha256"), c.get("mcr_runner_sha256"),
                   c.get("input_sha256"), c.get("prereg_sha256"))
                  for c in cells}
    if len(provenance) > 1:
        raise RuntimeError("mixed provenance; archive the tree.")
    expected = set(range(EXPECTED_REALIZATIONS))
    complete = all(
        {c["realization"] for c in cells if c["family"] == f} == expected
        for f in FAMILIES)

    sections: dict[str, Any] = {}
    curves: dict[str, Any] = {}
    for axis in AXES:
        sections[axis] = {}
        curves[axis] = {}
        for family in FAMILIES:
            fam_cells = [c for c in cells if c["family"] == family]
            if not fam_cells:
                continue
            rhos = []
            for cell in fam_cells:
                dose_map = cell["results"][axis]
                doses = sorted(dose_map, key=float)
                values = [dose_map[d] for d in doses]
                rho = spearmanr([float(d) for d in doses], values).statistic
                rhos.append(0.0 if np.isnan(rho) else float(rho))
            sections[axis][family] = bootstrap_stats(
                np.asarray(rhos), f"{axis}|{family}")
            doses_all = sorted(
                {d for c in fam_cells for d in c["results"][axis]},
                key=float)
            curves[axis][family] = {
                d: float(np.mean([c["results"][axis][d] for c in fam_cells
                                  if d in c["results"][axis]]))
                for d in doses_all
            }
        sections[axis]["all_families_separated"] = bool(all(
            sections[axis][f]["separated"] for f in FAMILIES
            if f in sections[axis]))
    verdicts = ({f"MCR_D_P1_{axis}": sections[axis]["all_families_separated"]
                 for axis in AXES}
                if complete else
                {"status": "incomplete — verdicts withheld"})
    payload = {
        "n_cells": len(cells),
        "bootstrap": {"reps": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED},
        "verdicts": verdicts,
        "spearman": sections,
        "mean_nmse_curves": curves,
    }
    out_path = args.root / "SUMMARY_V1.json"
    out_path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({"verdicts": verdicts, "n_cells": len(cells),
                      "written": str(out_path)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
