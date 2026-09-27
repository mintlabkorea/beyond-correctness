#!/usr/bin/env python3
"""Frozen adjudication for the M1/M2 measurement-stage factorial.

Implements `iclr_latex_v3/M1M2_STAGE_FACTORIAL_PREREGISTRATION_V1.md`:

- I1 (primary): per-cell interaction (a11 - a10) - (a01 - a00), CI must
  exclude 0 above
- I1-sens: same on inversion-corrected AUROC max(A, 1-A) for every arm
- S1: a11 vs pl_stage_at_columns; S2: a11 vs pl_columns_at_stage;
  S3: a11r vs pl_relations_at_stage; D: a11 vs is_target
- descriptive: a11r - a11, a10 - a00, per-target everything

AUROC higher is better; gain = arm - reference.  Hierarchical bootstrap
(targets then seeds, 10,000 reps, seed 20260819) at K = 256; separation =
mean > 0, CI95 excludes 0, win >= 0.60, mean > 0 with best target dropped.
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


def cellwise(cells, formula) -> dict[str, np.ndarray]:
    return {
        target: np.array([formula(by_seed[seed]) for seed in sorted(by_seed)])
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
            values = gains[targets[index]]
            parts.append(rng.choice(values, size=len(values), replace=True))
        means[rep] = float(np.mean(np.concatenate(parts)))
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def analyze(gains: dict[str, np.ndarray], with_verdict: bool = True) -> dict:
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
            and win >= WIN_THRESHOLD and drop_best > 0.0)
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

    def corrected(value: float) -> float:
        return max(value, 1.0 - value)

    summary = {
        "experiment_root": str(root),
        "metric": "auroc (higher is better); gain = arm - reference",
        "primary_k": int(PRIMARY_K), "n_cells": n_cells,
        "targets_present": sorted(cells),
        "bootstrap": {"reps": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED,
                      "hierarchy": "targets then seeds"},
        "I1_interaction": analyze(cellwise(cells, lambda c: (
            (c["a11_stage_columns"] - c["a10_stage"])
            - (c["a01_columns"] - c["a00_base"])))),
        "I1_sens_inversion_corrected": analyze(cellwise(cells, lambda c: (
            (corrected(c["a11_stage_columns"]) - corrected(c["a10_stage"]))
            - (corrected(c["a01_columns"]) - corrected(c["a00_base"]))))),
        "S1_stage_content": analyze(cellwise(cells, lambda c: (
            c["a11_stage_columns"] - c["pl_stage_at_columns"]))),
        "S2_binding_content": analyze(cellwise(cells, lambda c: (
            c["a11_stage_columns"] - c["pl_columns_at_stage"]))),
        "S3_relation_content": analyze(cellwise(cells, lambda c: (
            c["a11r_stage_columns_relations"] - c["pl_relations_at_stage"]))),
        "D_vs_is_target": analyze(cellwise(cells, lambda c: (
            c["a11_stage_columns"] - c["is_target"]))),
        "desc_relations_marginal": analyze(cellwise(cells, lambda c: (
            c["a11r_stage_columns_relations"] - c["a11_stage_columns"])),
            with_verdict=False),
        "desc_stage_marginal_at_base": analyze(cellwise(cells, lambda c: (
            c["a10_stage"] - c["a00_base"])), with_verdict=False),
        "desc_columns_at_stage": analyze(cellwise(cells, lambda c: (
            c["a11_stage_columns"] - c["a10_stage"])), with_verdict=False),
        "desc_columns_off_stage": analyze(cellwise(cells, lambda c: (
            c["a01_columns"] - c["a00_base"])), with_verdict=False),
        "arm_absolute_auroc_means": {
            arm: {t: float(np.mean([
                by_seed[seed][arm] for seed in sorted(by_seed)]))
                for t, by_seed in cells.items()}
            for arm in ("a00_base", "a01_columns", "a10_stage",
                        "a11_stage_columns", "a11r_stage_columns_relations",
                        "is_target")
        },
    }

    (root / "SUMMARY_V1.json").write_text(
        json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
