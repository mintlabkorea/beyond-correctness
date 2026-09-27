#!/usr/bin/env python3
"""Frozen adjudication for PAM hierarchical gating v2.

Implements `iclr_latex_v3/M1M2_PAM_HIERARCHICAL_GATING_PREREGISTRATION_V2.md`:
V-BETWEEN-CONTENT: h_gated vs h_gated_pl; V-BETWEEN-VALUE: h_gated vs
adj_concept (within-only); descriptive: h_gated vs free.  nRMSE lower is
better; gain = reference - arm.  Bootstrap and separation rule as PAM v1.
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
            record["nrmse"][PRIMARY_K]
        )
    return cells


def paired_gains(cells, arm: str, reference: str) -> dict[str, np.ndarray]:
    return {
        target: np.array([
            by_seed[seed][reference] - by_seed[seed][arm]
            for seed in sorted(by_seed)
        ])
        for target, by_seed in cells.items()
    }


def hierarchical_ci(gains):
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    targets = sorted(gains)
    means = np.empty(BOOTSTRAP_REPS)
    for rep in range(BOOTSTRAP_REPS):
        chosen = rng.choice(len(targets), size=len(targets), replace=True)
        parts = [rng.choice(gains[targets[i]], size=len(gains[targets[i]]),
                            replace=True) for i in chosen]
        means[rep] = float(np.mean(np.concatenate(parts)))
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def analyze(gains, with_verdict: bool = True) -> dict:
    flat = np.concatenate([gains[t] for t in sorted(gains)])
    mean_gain = float(np.mean(flat))
    win = float(np.mean(flat > 0.0))
    ci_low, ci_high = hierarchical_ci(gains)
    per_target = {t: float(np.mean(v)) for t, v in gains.items()}
    best = max(per_target, key=per_target.get)
    rest = [v for t, v in gains.items() if t != best]
    drop_best = float(np.mean(np.concatenate(rest))) if rest else float("nan")
    result = {
        "mean_gain": mean_gain, "ci95": [ci_low, ci_high], "win_rate": win,
        "n_pairs": int(len(flat)), "per_target_mean": per_target,
        "best_target": best, "drop_best_target_mean": drop_best,
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

    adjacency = json.loads(
        (root / "ADJACENCY_MAJORITY.json").read_text(encoding="utf-8"))
    summary = {
        "experiment_root": str(root),
        "metric": "query_sd_normalized_rmse (lower is better); "
                  "gain = reference - arm",
        "primary_k": int(PRIMARY_K), "n_cells": n_cells,
        "targets_present": sorted(cells),
        "coupled_pairs": adjacency["coupled_pairs"],
        "bootstrap": {"reps": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED,
                      "hierarchy": "targets then seeds"},
        "V_BETWEEN_CONTENT": analyze(
            paired_gains(cells, "h_gated", "h_gated_pl")),
        "V_BETWEEN_VALUE": analyze(
            paired_gains(cells, "h_gated", "adj_concept")),
        "desc_h_gated_vs_free": analyze(
            paired_gains(cells, "h_gated", "free"), with_verdict=False),
    }
    (root / "SUMMARY_V1.json").write_text(
        json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
