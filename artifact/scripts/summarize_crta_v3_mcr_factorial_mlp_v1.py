#!/usr/bin/env python3
"""Adjudicator for MCR-N (MLP subset of the MCR factorial).

Frozen rules: `iclr_latex_v3/MCR_MLP_PREREGISTRATION_V1.md`.
Q = -nMSE; fixed family strata; per-family realization bootstrap
(10,000 reps, seed 20260820); separation = mean > 0 and CI95 excludes 0
and win >= 0.60.  Verdicts N1-N3 require all three families at K=32;
N4 both pairwise families at K=32.  K=512 repeats each contrast as a
confirmatory replication.  Evaluability gate: a family x K stratum whose
mean m1c1rf nMSE is >= 1.0 has its verdicts declared non-evaluable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "experiments/crta_v3_mcr_factorial_mlp_v1"

FAMILIES = ("additive", "pairwise", "sparse")
OP_FAMILIES = ("pairwise", "sparse")
SUPPORT_KS = ("32", "512")
PRIMARY_K = "32"
EXPECTED_REALIZATIONS = 20
BOOTSTRAP_REPS = 10000
BOOTSTRAP_SEED = 20260820
WIN_THRESHOLD = 0.60

CellFn = Callable[[dict[str, Any]], float]


def q(arms: dict[str, Any], name: str) -> float:
    return -float(arms[name]["nmse"])


CONTRASTS: dict[str, tuple[CellFn, tuple[str, ...]]] = {
    "N1_measurement": (lambda a: q(a, "m1c1rf") - q(a, "m0c1rf"), FAMILIES),
    "N2_correspondence": (lambda a: q(a, "m1c1rf") - q(a, "m1c0rf"),
                          FAMILIES),
    "N3_MC_interaction": (lambda a: q(a, "m1c1rf") - q(a, "m1c0rf")
                          - q(a, "m0c1rf") + q(a, "m0c0rf"), FAMILIES),
    "N4_op_value_content": (lambda a: q(a, "rop_true") - q(a, "rop_random"),
                            OP_FAMILIES),
}
DESCRIPTIVE = {
    "op_values_over_free": (lambda a: q(a, "rop_true") - q(a, "m1c1rf"),
                            OP_FAMILIES),
}


def bootstrap_stats(values: np.ndarray, seed_key: str) -> dict[str, Any]:
    seed = int(hashlib.sha256(
        f"mcr_n|{BOOTSTRAP_SEED}|{seed_key}".encode()).hexdigest()[:8], 16)
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

    evaluable: dict[str, dict[str, Any]] = {}
    for support_k in SUPPORT_KS:
        evaluable[support_k] = {}
        for family in FAMILIES:
            values = [c["results"][support_k]["m1c1rf"]["nmse"]
                      for c in cells if c["family"] == family]
            mean_ref = float(np.mean(values)) if values else float("nan")
            evaluable[support_k][family] = {
                "mean_m1c1rf_nmse": mean_ref,
                "beats_intercept": bool(values and mean_ref < 1.0),
            }

    sections: dict[str, Any] = {}
    verdicts: dict[str, Any] = {}
    for support_k in SUPPORT_KS:
        sections[support_k] = {}
        for name, (fn, wanted) in {**CONTRASTS, **DESCRIPTIVE}.items():
            per_family: dict[str, Any] = {}
            for family in wanted:
                values = np.asarray([
                    fn(c["results"][support_k])
                    for c in cells if c["family"] == family
                ], dtype=float)
                if len(values):
                    per_family[family] = bootstrap_stats(
                        values, f"{name}|{family}|{support_k}")
                    per_family[family]["evaluable"] = (
                        evaluable[support_k][family]["beats_intercept"])
            gate_ok = all(evaluable[support_k][f]["beats_intercept"]
                          for f in wanted)
            separated_all = bool(
                per_family and gate_ok and all(
                    per_family[f]["separated"] for f in wanted
                    if f in per_family) and len(
                    [f for f in wanted if f in per_family]) == len(wanted))
            per_family["all_families_separated"] = separated_all
            per_family["all_families_evaluable"] = bool(gate_ok)
            sections[support_k][name] = per_family
            if name in CONTRASTS and support_k == PRIMARY_K:
                verdicts[name] = ("non-evaluable" if not gate_ok
                                  else separated_all)

    arm_means = {}
    for support_k in SUPPORT_KS:
        arm_means[support_k] = {}
        for family in FAMILIES:
            fam_cells = [c for c in cells if c["family"] == family]
            if fam_cells:
                arm_means[support_k][family] = {
                    arm: float(np.mean(
                        [c["results"][support_k][arm]["nmse"]
                         for c in fam_cells]))
                    for arm in fam_cells[0]["results"][support_k]
                }
    if not complete:
        verdicts = {"status": "incomplete — verdicts withheld"}
    payload = {
        "n_cells": len(cells),
        "bootstrap": {"reps": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED},
        "primary_support_k": PRIMARY_K,
        "evaluability_gate": evaluable,
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
