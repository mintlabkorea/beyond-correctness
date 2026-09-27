#!/usr/bin/env python3
"""Adjudicator for MCR-T (TabPFN subset of the MCR factorial).

Frozen rules: `iclr_latex_v3/MCR_TABPFN_PREREGISTRATION_V1.md`.
Q = -nMSE; fixed family strata; per-family realization bootstrap
(10,000 reps, seed 20260820); separation = mean > 0 and CI95 excludes 0
and win >= 0.60.  T1-T3 require all three families; T4 both pairwise
families.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "experiments/crta_v3_mcr_factorial_tabpfn_v1"

FAMILIES = ("additive", "pairwise", "sparse")
OP_FAMILIES = ("pairwise", "sparse")
EXPECTED_REALIZATIONS = 20
BOOTSTRAP_REPS = 10000
BOOTSTRAP_SEED = 20260820
WIN_THRESHOLD = 0.60

CellFn = Callable[[dict[str, Any]], float]


def q(arms: dict[str, Any], name: str) -> float:
    return -float(arms[name]["nmse"])


CONTRASTS: dict[str, tuple[CellFn, tuple[str, ...]]] = {
    "T1_measurement": (lambda a: q(a, "m1c1rf") - q(a, "m0c1rf"), FAMILIES),
    "T2_correspondence": (lambda a: q(a, "m1c1rf") - q(a, "m1c0rf"),
                          FAMILIES),
    "T3_MC_interaction": (lambda a: q(a, "m1c1rf") - q(a, "m1c0rf")
                          - q(a, "m0c1rf") + q(a, "m0c0rf"), FAMILIES),
    "T4_op_value_content": (lambda a: q(a, "rop_true") - q(a, "rop_random"),
                            OP_FAMILIES),
}


def bootstrap_stats(values: np.ndarray, seed_key: str) -> dict[str, Any]:
    seed = int(hashlib.sha256(
        f"mcr_t|{BOOTSTRAP_SEED}|{seed_key}".encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    samples = values[rng.integers(0, len(values),
                                  size=(BOOTSTRAP_REPS, len(values)))]
    means = samples.mean(axis=1)
    mean = float(values.mean())
    lower, upper = (float(np.quantile(means, 0.025)),
                    float(np.quantile(means, 0.975)))
    win = float(np.mean(values > 0))
    return {"mean": mean, "ci95": [lower, upper], "win": win,
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
    for name, (fn, wanted) in CONTRASTS.items():
        per_family: dict[str, Any] = {}
        for family in wanted:
            values = np.asarray([
                fn(c["results"]) for c in cells if c["family"] == family
            ], dtype=float)
            if len(values):
                per_family[family] = bootstrap_stats(values,
                                                     f"{name}|{family}")
        per_family["all_families_separated"] = bool(
            per_family and all(
                per_family[f]["separated"] for f in wanted
                if f in per_family) and len(
                [f for f in wanted if f in per_family]) == len(wanted))
        sections[name] = per_family
    arm_means = {}
    for family in FAMILIES:
        fam_cells = [c for c in cells if c["family"] == family]
        if fam_cells:
            arm_means[family] = {
                arm: float(np.mean([c["results"][arm]["nmse"]
                                    for c in fam_cells]))
                for arm in fam_cells[0]["results"]
            }
    verdicts = ({name: sections[name]["all_families_separated"]
                 for name in CONTRASTS}
                if complete else
                {"status": "incomplete — verdicts withheld"})
    payload = {
        "n_cells": len(cells),
        "bootstrap": {"reps": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED},
        "verdicts": verdicts,
        "sections": sections,
        "arm_mean_nmse": arm_means,
    }
    out_path = args.root / "SUMMARY_V1.json"
    out_path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({"verdicts": verdicts, "n_cells": len(cells),
                      "written": str(out_path)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
