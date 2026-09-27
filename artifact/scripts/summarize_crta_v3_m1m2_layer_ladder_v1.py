#!/usr/bin/env python3
"""Frozen adjudication for the M1/M2 layer ladder.

Implements, verbatim, the rules of
`iclr_latex_v3/M1M2_LAYER_LADDER_PREREGISTRATION_V1.md` (frozen before any
cell ran):

- R1/R2/R3: each rung vs its capacity-matched placebo
- D1/D2/D3: each rung vs the standing `is_target` arm
- separation = mean gain > 0, 95% hierarchical-bootstrap CI excludes 0,
  win >= 0.60, mean > 0 with the best target dropped
- descriptive: marginals, leave-one-out (loo_measurement is an alias of
  rung2_grouping), is_target vs rung0
- gate coupling: if the harmonization-ablation summary reports the
  insensitivity gate fired, rung 3 / R3 / D3 are labelled
  "measurement not measurable on this testbed" and carry no verdict
- every contrast is also reported per endpoint

Gain = reference nRMSE - arm nRMSE (positive = arm better; lower is better).

usage: summarize... <ladder_root> [--ablation-summary PATH]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

PRIMARY_K = "256"
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 20260819
WIN_THRESHOLD = 0.60

CONTRASTS = {
    "R1_columns_vs_placebo": ("rung1_columns", "pl_columns"),
    "R2_grouping_vs_placebo": ("rung2_grouping", "pl_grouping"),
    "R3_measurement_vs_placebo": ("rung3_measurement", "pl_measurement"),
    "D1_columns_vs_is_target": ("rung1_columns", "is_target"),
    "D2_grouping_vs_is_target": ("rung2_grouping", "is_target"),
    "D3_measurement_vs_is_target": ("rung3_measurement", "is_target"),
}
DESCRIPTIVE = {
    "marginal_columns": ("rung1_columns", "rung0_base"),
    "marginal_grouping": ("rung2_grouping", "rung1_columns"),
    "marginal_measurement": ("rung3_measurement", "rung2_grouping"),
    "is_target_vs_base": ("is_target", "rung0_base"),
    "loo_columns_vs_full": ("rung3_measurement", "loo_columns"),
    "loo_grouping_vs_full": ("rung3_measurement", "loo_grouping"),
    "loo_measurement_vs_full": ("rung3_measurement", "loo_measurement"),
}


def load_cells(root: Path):
    cells: dict[str, dict[int, dict]] = {}
    drops: dict[str, dict] = {}
    for path in sorted(root.glob("*/seed_*/metrics.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        cells.setdefault(record["target"], {})[int(record["seed"])] = (
            record["nrmse"][PRIMARY_K]
        )
        drops[record["target"]] = record.get("dropped_members_by_group", {})
    return cells, drops


def paired_gains(cells, arm: str, reference: str) -> dict[str, np.ndarray]:
    return {
        target: np.array([
            by_seed[seed][reference] - by_seed[seed][arm]
            for seed in sorted(by_seed)
        ])
        for target, by_seed in cells.items()
    }


def hierarchical_ci(gains: dict[str, np.ndarray]) -> tuple[float, float]:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    targets = sorted(gains)
    means = np.empty(BOOTSTRAP_REPS)
    for rep in range(BOOTSTRAP_REPS):
        chosen = rng.choice(len(targets), size=len(targets), replace=True)
        parts = []
        for index in chosen:
            seed_gains = gains[targets[index]]
            parts.append(rng.choice(seed_gains, size=len(seed_gains), replace=True))
        means[rep] = float(np.mean(np.concatenate(parts)))
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def analyze(gains: dict[str, np.ndarray], with_verdict: bool) -> dict:
    flat = np.concatenate([gains[t] for t in sorted(gains)])
    mean_gain = float(np.mean(flat))
    win = float(np.mean(flat > 0.0))
    ci_low, ci_high = hierarchical_ci(gains)
    per_target = {t: float(np.mean(v)) for t, v in gains.items()}
    best_target = max(per_target, key=per_target.get)
    rest = [v for t, v in gains.items() if t != best_target]
    drop_best = float(np.mean(np.concatenate(rest))) if rest else float("nan")
    result = {
        "mean_gain": mean_gain, "ci95": [ci_low, ci_high], "win_rate": win,
        "n_pairs": int(len(flat)), "per_target_mean": per_target,
        "best_target": best_target, "drop_best_target_mean": drop_best,
    }
    if with_verdict:
        result["separated"] = bool(
            mean_gain > 0.0 and ci_low > 0.0
            and win >= WIN_THRESHOLD and drop_best > 0.0
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--ablation-summary", type=Path, default=None)
    args = parser.parse_args()

    cells, drops = load_cells(args.root)
    n_cells = sum(len(v) for v in cells.values())
    if n_cells == 0:
        print("no completed cells")
        return 1

    gate_fired = None
    if args.ablation_summary and args.ablation_summary.is_file():
        ablation = json.loads(args.ablation_summary.read_text(encoding="utf-8"))
        gate_fired = bool(ablation.get("gate_testbed_insensitive"))

    summary: dict = {
        "experiment_root": str(args.root),
        "metric": "query_sd_normalized_rmse (lower is better); gain = reference - arm",
        "primary_k": int(PRIMARY_K), "n_cells": n_cells,
        "targets_present": sorted(cells),
        "bootstrap": {"reps": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED,
                      "hierarchy": "targets then seeds"},
        "relation_layer": "not evaluable on these corpora -- declared boundary, "
                          "see preregistration section 0",
        "member_drop_by_target": drops,
        "ablation_gate_fired": gate_fired,
    }

    measurement_muted = gate_fired is True
    for name, (arm, reference) in CONTRASTS.items():
        with_verdict = not (measurement_muted and name.startswith(("R3", "D3")))
        summary[name] = analyze(paired_gains(cells, arm, reference), with_verdict)
        if not with_verdict:
            summary[name]["verdict_suppressed"] = (
                "measurement not measurable on this testbed "
                "(harmonization-ablation insensitivity gate fired)"
            )
    for name, (arm, reference) in DESCRIPTIVE.items():
        summary[name] = analyze(paired_gains(cells, arm, reference), False)

    (args.root / "SUMMARY_V1.json").write_text(
        json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
