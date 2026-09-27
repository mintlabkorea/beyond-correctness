#!/usr/bin/env python3
"""Frozen adjudication for G-SIGN-CAMELS v2 (addendum GC-v2).

`SCHEMA_PAIR_GENERALIZATION_PREREGISTRATION_V1.md` section 6.  Clusters
over QUERY BASINS (the independent population unit), not support levels.
GCv2-P1 identification separates with no basin negative; GCv2-P2 utility
does not separate; GCv2-P3 content-vs-random must separate on BOTH
log1p_rmse (lower better) and NSE (higher better), otherwise the
contrast is declared metric-dependent and not carryable.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 20260819
WIN_THRESHOLD = 0.60


def load_basin_gains(root: Path, arm: str, reference: str, metric: str,
                     lower_better: bool) -> dict[str, np.ndarray]:
    """gain per (basin, cell); positive = documented better."""
    sign = 1.0 if lower_better else -1.0
    per_basin: dict[str, list[float]] = {}
    for path in sorted(root.glob("support_*/seed_*/metrics.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        arms = record["arms"]
        for basin, lesion in arms[arm]["per_basin"].items():
            base = arms[reference]["per_basin"][basin]
            value = sign * (lesion[metric] - base[metric])
            if np.isfinite(value):
                per_basin.setdefault(basin, []).append(float(value))
    return {b: np.asarray(v) for b, v in per_basin.items()}


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
    per_basin = {k: float(np.mean(v)) for k, v in values.items()}
    best = max(per_basin, key=per_basin.get)
    rest = [v for k, v in values.items() if k != best]
    drop_best = float(np.mean(np.concatenate(rest))) if rest else float("nan")
    return {
        "mean_gain": float(np.mean(flat)), "ci95": [low, high],
        "win_rate": float(np.mean(flat > 0.0)),
        "n_basins": len(values), "n_basin_cells": int(len(flat)),
        "n_basins_negative": sum(1 for v in per_basin.values() if v < 0),
        "per_basin_mean": per_basin, "drop_best_basin_mean": drop_best,
        "separated": bool(float(np.mean(flat)) > 0.0 and low > 0.0
                          and float(np.mean(flat > 0.0)) >= WIN_THRESHOLD
                          and drop_best > 0.0),
    }


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <probe_root>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])

    def contrast(arm: str) -> dict:
        return {
            "log1p_rmse": analyze(load_basin_gains(
                root, arm, "sign_documented", "log1p_rmse", True)),
            "nse": analyze(load_basin_gains(
                root, arm, "sign_documented", "nse", False)),
        }

    p1 = contrast("sign_flipped")
    p2 = contrast("free")
    p3 = contrast("sign_random")
    p3_both = bool(p3["log1p_rmse"]["separated"] and p3["nse"]["separated"])

    summary = {
        "probe_root": str(root), "task": "N1_camels_us2gb",
        "clustering": "query basin (independent population unit)",
        "bootstrap": {"reps": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED},
        "GCv2_P1_identification": p1,
        "GCv2_P2_utility": p2,
        "GCv2_P3_content_vs_random": p3,
        "GCv2_P1_pass": bool(p1["log1p_rmse"]["separated"]
                             and p1["log1p_rmse"]["n_basins_negative"] == 0),
        "GCv2_P2_pass_no_utility": bool(not p2["log1p_rmse"]["separated"]),
        "GCv2_P3_pass_both_metrics": p3_both,
        "GCv2_P3_verdict": ("content carries beyond capacity" if p3_both
                            else "metric-dependent; not carryable"),
    }
    (root / "SUMMARY_V2.json").write_text(
        json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
