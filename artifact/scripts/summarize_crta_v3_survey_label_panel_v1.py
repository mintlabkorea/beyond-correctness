#!/usr/bin/env python3
"""Frozen adjudication for the survey-label measurement panel.

Implements, verbatim,
`iclr_latex_v3/M1M2_SURVEY_LABEL_MEASUREMENT_PANEL_PREREGISTRATION_V1.md`:

- A1: llm_table vs placebo_table (primary verdict)
- A2: pipeline_table vs placebo_table (secondary verdict)
- A3: llm_table vs pipeline_table per target -- checks the pre-declared
  prediction (CI containing 0 for hypertension and smoking, CI below 0 for
  diabetes)
- raw: descriptive only

Metric AUROC, higher is better; gain = arm - reference (positive = arm
better; the sign is flipped vs the nRMSE experiments).  Separation = mean >
0, 95% hierarchical-bootstrap CI excludes 0, win >= 0.60, mean > 0 with the
best target dropped.  Bootstrap: targets then seeds, 10,000 reps, seed
20260819, at K = 256.
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


def load_cells(root: Path) -> dict[str, dict[int, dict]]:
    cells: dict[str, dict[int, dict]] = {}
    for path in sorted(root.glob("*/seed_*/metrics.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        cells.setdefault(record["target"], {})[int(record["seed"])] = (
            record["auroc"][PRIMARY_K]
        )
    return cells


def paired_gains(cells, arm: str, reference: str) -> dict[str, np.ndarray]:
    return {
        target: np.array([
            by_seed[seed][arm] - by_seed[seed][reference]
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


def seed_ci(values: np.ndarray) -> tuple[float, float]:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    means = np.array([
        float(np.mean(rng.choice(values, size=len(values), replace=True)))
        for _ in range(BOOTSTRAP_REPS)
    ])
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
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <experiment_root>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    cells = load_cells(root)
    n_cells = sum(len(v) for v in cells.values())
    if n_cells == 0:
        print("no completed cells", file=sys.stderr)
        return 1

    a3 = paired_gains(cells, "llm_table", "pipeline_table")
    prediction = {}
    for target, values in a3.items():
        low, high = seed_ci(values)
        prediction[target] = {
            "mean": float(np.mean(values)), "ci95": [low, high],
            "predicted": "ci_below_0" if target == "diabetes_history"
                         else "ci_contains_0",
            "observed": ("ci_below_0" if high < 0.0
                         else "ci_above_0" if low > 0.0 else "ci_contains_0"),
        }
        prediction[target]["matches"] = (
            prediction[target]["observed"] == prediction[target]["predicted"]
        )

    summary = {
        "experiment_root": str(root),
        "metric": "auroc (higher is better); gain = arm - reference",
        "primary_k": int(PRIMARY_K), "n_cells": n_cells,
        "targets_present": sorted(cells),
        "bootstrap": {"reps": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED,
                      "hierarchy": "targets then seeds"},
        "A1_llm_vs_placebo": analyze(
            paired_gains(cells, "llm_table", "placebo_table"), True),
        "A2_pipeline_vs_placebo": analyze(
            paired_gains(cells, "pipeline_table", "placebo_table"), True),
        "A3_llm_vs_pipeline_prediction_check": prediction,
        "raw_vs_pipeline_descriptive": analyze(
            paired_gains(cells, "raw", "pipeline_table"), False),
        "raw_absolute_auroc_per_target": {
            target: float(np.mean([
                by_seed[seed]["raw"] for seed in sorted(by_seed)]))
            for target, by_seed in cells.items()
        },
    }

    (root / "SUMMARY_V1.json").write_text(
        json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
