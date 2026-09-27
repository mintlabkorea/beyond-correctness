#!/usr/bin/env python3
"""Frozen adjudication for E1, the direction-constraint support sweep.

Implements `OVERNIGHT_EXPANSION_PREREGISTRATION_20260820_V1.md` E1:
- E1-P1 (slope): per-cell paired difference of gain(sign vs free) at K=16
  minus at K=1024, hierarchical CI must exclude 0 above.
- E1-P2 (crossover): gain(sign vs free) CI > 0 at K=16 AND (mean <= 0 or
  CI contains 0) at K=1024.
- E1-P3 (content everywhere): gain(sign vs flip) CI > 0 at every K.
nRMSE lower is better; gain = reference - arm (positive = arm better).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

K_GRID = ("16", "32", "64", "128", "256", "1024")
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 20260819


def load_cells(root: Path) -> dict[str, dict[int, dict]]:
    cells: dict[str, dict[int, dict]] = {}
    for path in sorted(root.glob("*/seed_*/metrics.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        cells.setdefault(record["target"], {})[int(record["seed"])] = record["nrmse"]
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
        parts = [rng.choice(gains[targets[i]], size=len(gains[targets[i]]),
                            replace=True) for i in chosen]
        means[rep] = float(np.mean(np.concatenate(parts)))
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def stat(gains: dict[str, np.ndarray]) -> dict:
    flat = np.concatenate([gains[t] for t in sorted(gains)])
    low, high = hierarchical_ci(gains)
    return {
        "mean": float(np.mean(flat)), "ci95": [low, high],
        "win_rate": float(np.mean(flat > 0.0)),
        "per_target_mean": {t: float(np.mean(v)) for t, v in gains.items()},
    }


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <experiment_root>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    cells = load_cells(root)
    if not cells:
        print("no completed cells", file=sys.stderr)
        return 1

    curve_sign_free, curve_sign_flip = {}, {}
    for K in K_GRID:
        curve_sign_free[K] = stat(cellwise(cells, lambda c, K=K: (
            c[K]["free"] - c[K]["sign_documented"])))
        curve_sign_flip[K] = stat(cellwise(cells, lambda c, K=K: (
            c[K]["pl_sign_flip"] - c[K]["sign_documented"])))

    slope = stat(cellwise(cells, lambda c: (
        (c["16"]["free"] - c["16"]["sign_documented"])
        - (c["1024"]["free"] - c["1024"]["sign_documented"]))))

    p1 = bool(slope["ci95"][0] > 0.0)
    k16, k1024 = curve_sign_free["16"], curve_sign_free["1024"]
    p2 = bool(k16["ci95"][0] > 0.0
              and (k1024["mean"] <= 0.0
                   or k1024["ci95"][0] <= 0.0 <= k1024["ci95"][1]))
    p3_per_k = {K: bool(v["ci95"][0] > 0.0) for K, v in curve_sign_flip.items()}
    crossover = None
    for i in range(len(K_GRID) - 1):
        if (curve_sign_free[K_GRID[i]]["mean"] > 0.0
                >= curve_sign_free[K_GRID[i + 1]]["mean"]):
            crossover = f"between K={K_GRID[i]} and K={K_GRID[i+1]}"

    summary = {
        "experiment_root": str(root),
        "metric": "query_sd_normalized_rmse (lower is better); "
                  "gain = reference - arm",
        "n_cells": sum(len(v) for v in cells.values()),
        "bootstrap": {"reps": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED,
                      "hierarchy": "targets then seeds"},
        "curve_sign_vs_free_by_K": curve_sign_free,
        "curve_sign_vs_flip_by_K": curve_sign_flip,
        "E1_P1_slope": {"stat": slope, "pass": p1},
        "E1_P2_crossover": {"K16": k16, "K1024": k1024, "pass": p2,
                            "observed_crossover": crossover},
        "E1_P3_content_at_every_K": {"per_K": p3_per_k,
                                     "pass": bool(all(p3_per_k.values()))},
    }
    (root / "SUMMARY_V1.json").write_text(
        json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
