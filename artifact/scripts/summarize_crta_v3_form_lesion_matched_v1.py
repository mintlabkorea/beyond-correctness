#!/usr/bin/env python3
"""Frozen adjudication for F (form x lesion-severity, matched).

`iclr_latex_v3/FORM_LESION_MATCHED_PREREGISTRATION_V1.md`:
F-C3 direction expressibility in value form (|effect| < 0.001, CI ni 0),
F-C1a value-form content at neutral lesion, F-C1b constraint-form content
at the MATCHED neutral lesion, F-C2 constraint-form content at the
adversarial lesion; F-P2 = per-cell paired (F-C1b - F-C1a) > 0.
nRMSE lower is better; gain = lesion - documented.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

PRIMARY_K = "256"
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 20260819
WIN_THRESHOLD = 0.60
NOOP_EPSILON = 0.001


def load_cells(root: Path) -> dict[str, dict[int, dict]]:
    cells: dict[str, dict[int, dict]] = {}
    for path in sorted(root.glob("*/seed_*/metrics.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        cells.setdefault(record["target"], {})[int(record["seed"])] = (
            record["nrmse"][PRIMARY_K])
    return cells


def cellwise(cells, formula) -> dict[str, np.ndarray]:
    return {t: np.array([formula(by[s]) for s in sorted(by)])
            for t, by in cells.items()}


def hierarchical_ci(gains: dict[str, np.ndarray]) -> tuple[float, float]:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    targets = sorted(gains)
    means = np.empty(BOOTSTRAP_REPS)
    for rep in range(BOOTSTRAP_REPS):
        chosen = rng.choice(len(targets), size=len(targets), replace=True)
        parts = [rng.choice(gains[targets[i]], size=len(gains[targets[i]]),
                            replace=True) for i in chosen]
        means[rep] = float(np.mean(np.concatenate(parts)))
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def analyze(gains: dict[str, np.ndarray], with_verdict: bool = True) -> dict:
    flat = np.concatenate([gains[t] for t in sorted(gains)])
    low, high = hierarchical_ci(gains)
    per_target = {t: float(np.mean(v)) for t, v in gains.items()}
    best = max(per_target, key=per_target.get)
    rest = [v for t, v in gains.items() if t != best]
    drop_best = float(np.mean(np.concatenate(rest))) if rest else float("nan")
    result = {"mean_gain": float(np.mean(flat)), "ci95": [low, high],
              "win_rate": float(np.mean(flat > 0.0)),
              "per_target_mean": per_target, "drop_best_target_mean": drop_best}
    if with_verdict:
        result["separated"] = bool(
            result["mean_gain"] > 0.0 and low > 0.0
            and result["win_rate"] >= WIN_THRESHOLD and drop_best > 0.0)
    return result


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <experiment_root>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    cells = load_cells(root)
    if not cells:
        print("no completed cells", file=sys.stderr)
        return 1

    c3 = analyze(cellwise(cells, lambda c: (
        c["val_documented_negated"] - c["val_documented"])), with_verdict=False)
    c1a = analyze(cellwise(cells, lambda c: c["val_random"] - c["val_documented"]))
    c1b = analyze(cellwise(cells, lambda c: c["sign_random"] - c["sign_documented"]))
    c2 = analyze(cellwise(cells, lambda c: c["sign_flipped"] - c["sign_documented"]))
    paired = analyze(cellwise(cells, lambda c: (
        (c["sign_random"] - c["sign_documented"])
        - (c["val_random"] - c["val_documented"]))))
    p3 = analyze(cellwise(cells, lambda c: (
        (c["sign_flipped"] - c["sign_documented"])
        - (c["sign_random"] - c["sign_documented"]))), with_verdict=False)

    summary = {
        "experiment_root": str(root),
        "metric": "query_sd_normalized_rmse (lower is better); "
                  "gain = lesion - documented",
        "primary_k": int(PRIMARY_K),
        "n_cells": sum(len(v) for v in cells.values()),
        "bootstrap": {"reps": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED,
                      "hierarchy": "targets then seeds"},
        "F_C3_value_direction_expressibility": c3,
        "F_C1a_value_content_neutral_lesion": c1a,
        "F_C1b_constraint_content_matched_neutral_lesion": c1b,
        "F_C2_constraint_content_adversarial_lesion": c2,
        "F_P1_direction_inexpressible_in_value_form": bool(
            abs(c3["mean_gain"]) < NOOP_EPSILON
            and c3["ci95"][0] <= 0.0 <= c3["ci95"][1]),
        "F_P2_constraint_expresses_more_at_matched_severity": {
            "paired_difference": paired, "pass": bool(paired["separated"])},
        "F_P3_adversarial_worse_than_neutral": {
            "paired_difference": p3, "pass": bool(p3["ci95"][0] > 0.0)},
    }
    (root / "SUMMARY_V1.json").write_text(
        json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
