#!/usr/bin/env python3
"""Frozen adjudication for the M1/M2 measurement-harmonization ablation.

Implements, verbatim, the verdict rules of
`iclr_latex_v3/M1M2_MEASUREMENT_HARMONIZATION_ABLATION_PREREGISTRATION_V1.md`
(written before any cell was executed):

- gate first: |mean(pipeline_table - raw)| < 0.001 nRMSE at K=256
  => "testbed insensitive -- not evaluable"; V1/V2 numbers reported, no verdict
- V1: pipeline_table vs placebo_table
- V2: llm_table vs placebo_table
  separated iff mean gain > 0, 95% hierarchical-bootstrap CI excludes 0,
  win >= 0.60, and mean gain > 0 with the single best target dropped
- V3 (descriptive): pipeline_table vs llm_table

Gain = placebo (or comparator) nRMSE - arm nRMSE; positive = arm better.
Bootstrap: resample targets, then seeds within target; 10,000 reps, seed
20260819.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

PRIMARY_K = "256"
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 20260819
GATE_EPSILON = 0.001
WIN_THRESHOLD = 0.60


def load_cells(root: Path) -> dict[str, dict[int, dict]]:
    cells: dict[str, dict[int, dict]] = {}
    for path in sorted(root.glob("*/seed_*/metrics.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        cells.setdefault(record["target"], {})[int(record["seed"])] = (
            record["nrmse"][PRIMARY_K]
        )
    return cells


def paired_gains(cells: dict, arm: str, reference: str) -> dict[str, np.ndarray]:
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


def adjudicate(gains: dict[str, np.ndarray]) -> dict:
    flat = np.concatenate([gains[t] for t in sorted(gains)])
    mean_gain = float(np.mean(flat))
    win = float(np.mean(flat > 0.0))
    ci_low, ci_high = hierarchical_ci(gains)
    per_target = {t: float(np.mean(v)) for t, v in gains.items()}
    best_target = max(per_target, key=per_target.get)
    drop_best = float(np.mean(np.concatenate(
        [v for t, v in gains.items() if t != best_target])))
    separated = (
        mean_gain > 0.0 and ci_low > 0.0
        and win >= WIN_THRESHOLD and drop_best > 0.0
    )
    return {
        "mean_gain": mean_gain, "ci95": [ci_low, ci_high], "win_rate": win,
        "n_pairs": int(len(flat)), "per_target_mean": per_target,
        "best_target": best_target, "drop_best_target_mean": drop_best,
        "separated": bool(separated),
    }


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <experiment_root>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    cells = load_cells(root)
    n_cells = sum(len(v) for v in cells.values())
    if n_cells == 0:
        print("no completed cells", file=sys.stderr)
        return 1

    gate_gains = paired_gains(cells, "pipeline_table", "raw")
    gate_mean = float(np.mean(np.concatenate(list(gate_gains.values()))))
    insensitive = abs(gate_mean) < GATE_EPSILON

    summary = {
        "experiment_root": str(root),
        "metric": "query_sd_normalized_rmse (lower is better); gain = reference - arm",
        "primary_k": int(PRIMARY_K),
        "n_cells": n_cells,
        "targets_present": sorted(cells),
        "bootstrap": {"reps": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED,
                      "hierarchy": "targets then seeds"},
        "gate_pipeline_minus_raw_mean": gate_mean,
        "gate_testbed_insensitive": bool(insensitive),
        "V1_pipeline_vs_placebo": adjudicate(
            paired_gains(cells, "pipeline_table", "placebo_table")),
        "V2_llm_vs_placebo": adjudicate(
            paired_gains(cells, "llm_table", "placebo_table")),
        "V3_pipeline_vs_llm_descriptive": adjudicate(
            paired_gains(cells, "pipeline_table", "llm_table")),
    }
    if insensitive:
        summary["verdict"] = (
            "testbed insensitive -- not evaluable; V1/V2 carry no interpretation"
        )
        summary["V1_pipeline_vs_placebo"]["separated"] = None
        summary["V2_llm_vs_placebo"]["separated"] = None

    (root / "SUMMARY_V1.json").write_text(
        json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
