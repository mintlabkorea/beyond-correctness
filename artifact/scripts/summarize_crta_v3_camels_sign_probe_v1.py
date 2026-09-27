#!/usr/bin/env python3
"""Frozen adjudication for G-SIGN-CAMELS.

`SCHEMA_PAIR_GENERALIZATION_PREREGISTRATION_V1.md` section 5:
GC-P1 flipped-vs-documented separates (no support level negative);
GC-P2 free-vs-documented separates (utility expected in this domain);
GC-P3 random-vs-documented separates (content beyond regularization
capacity).  Primary metric log1p_rmse (lower better); mean_basin_nse
reported alongside.  Gain = lesion - documented.  Bootstrap over support
levels then seeds, 10k reps, seed 20260819.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 20260819
WIN_THRESHOLD = 0.60
PRIMARY = "log1p_rmse"
SECONDARY = "mean_basin_nse"


def load_cells(root: Path) -> dict[str, list[dict]]:
    cells: dict[str, list[dict]] = {}
    for path in sorted(root.glob("support_*/seed_*/metrics.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        cells.setdefault(str(record["support_basins"]), []).append(record["arms"])
    return cells


def gains(cells, arm: str, reference: str, metric: str, lower_better: bool):
    sign = 1.0 if lower_better else -1.0
    return {k: np.array([sign * (a[arm][metric] - a[reference][metric])
                         for a in arms]) for k, arms in cells.items()}


def hierarchical_ci(values: dict[str, np.ndarray]) -> tuple[float, float]:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    keys = sorted(values)
    means = np.empty(BOOTSTRAP_REPS)
    for rep in range(BOOTSTRAP_REPS):
        chosen = rng.choice(len(keys), size=len(keys), replace=True)
        parts = [rng.choice(values[keys[i]], size=len(values[keys[i]]),
                            replace=True) for i in chosen]
        means[rep] = float(np.mean(np.concatenate(parts)))
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def analyze(values: dict[str, np.ndarray]) -> dict:
    flat = np.concatenate([values[k] for k in sorted(values)])
    low, high = hierarchical_ci(values)
    per_level = {k: float(np.mean(v)) for k, v in values.items()}
    best = max(per_level, key=per_level.get)
    rest = [v for k, v in values.items() if k != best]
    drop_best = float(np.mean(np.concatenate(rest))) if rest else float("nan")
    return {
        "mean_gain": float(np.mean(flat)), "ci95": [low, high],
        "win_rate": float(np.mean(flat > 0.0)), "n_cells": int(len(flat)),
        "per_support_level_mean": per_level,
        "n_levels_negative": sum(1 for v in per_level.values() if v < 0),
        "drop_best_level_mean": drop_best,
        "separated": bool(float(np.mean(flat)) > 0.0 and low > 0.0
                          and float(np.mean(flat > 0.0)) >= WIN_THRESHOLD
                          and drop_best > 0.0),
    }


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <probe_root>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    cells = load_cells(root)
    if not cells:
        print("no completed cells", file=sys.stderr)
        return 1

    p1 = analyze(gains(cells, "sign_flipped", "sign_documented", PRIMARY, True))
    p2 = analyze(gains(cells, "free", "sign_documented", PRIMARY, True))
    p3 = analyze(gains(cells, "sign_random", "sign_documented", PRIMARY, True))
    summary = {
        "probe_root": str(root), "task": "N1_camels_us2gb",
        "primary_metric": f"{PRIMARY} (lower better); gain = lesion - documented",
        "bootstrap": {"reps": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED,
                      "hierarchy": "support levels then seeds"},
        "GC_P1_identification_flipped": p1,
        "GC_P2_utility_vs_free": p2,
        "GC_P3_content_vs_random": p3,
        "GC_P1_pass": bool(p1["separated"] and p1["n_levels_negative"] == 0),
        "GC_P2_pass": bool(p2["separated"]),
        "GC_P3_pass": bool(p3["separated"]),
        "secondary_nse": {
            "flipped_vs_documented": analyze(
                gains(cells, "sign_flipped", "sign_documented", SECONDARY, False)),
            "free_vs_documented": analyze(
                gains(cells, "free", "sign_documented", SECONDARY, False)),
            "random_vs_documented": analyze(
                gains(cells, "sign_random", "sign_documented", SECONDARY, False)),
        },
    }
    (root / "SUMMARY_V1.json").write_text(
        json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
