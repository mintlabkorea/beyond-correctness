#!/usr/bin/env python3
"""Frozen adjudication for G-SIGN-M3.

`iclr_latex_v3/SCHEMA_PAIR_GENERALIZATION_PREREGISTRATION_V1.md`:
GS-P1 flipped-vs-documented separates with no negative endpoint;
GS-P2 random-vs-documented > 0 and smaller than GS-P1;
GS-P3 free-vs-documented does NOT separate (no utility).
nRMSE lower is better; gain = lesion - documented.  Hierarchical
bootstrap over endpoints then cells, 10k reps, seed 20260819.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 20260819
WIN_THRESHOLD = 0.60
METRIC = "query_sd_normalized_rmse"


def load_cells(root: Path) -> dict[str, list[dict]]:
    cells: dict[str, list[dict]] = {}
    for path in sorted(root.glob("*/support_*/seed_*/metrics.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        cells.setdefault(record["endpoint"], []).append(record["arms"])
    return cells


def gains(cells, arm: str, reference: str) -> dict[str, np.ndarray]:
    return {e: np.array([a[arm][METRIC] - a[reference][METRIC] for a in arms])
            for e, arms in cells.items()}


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
    flat = np.concatenate([values[e] for e in sorted(values)])
    low, high = hierarchical_ci(values)
    per_endpoint = {e: float(np.mean(v)) for e, v in values.items()}
    best = max(per_endpoint, key=per_endpoint.get)
    rest = [v for e, v in values.items() if e != best]
    drop_best = float(np.mean(np.concatenate(rest))) if rest else float("nan")
    return {
        "mean_gain": float(np.mean(flat)), "ci95": [low, high],
        "win_rate": float(np.mean(flat > 0.0)), "n_cells": int(len(flat)),
        "per_endpoint_mean": per_endpoint,
        "n_endpoints_negative": sum(1 for v in per_endpoint.values() if v < 0),
        "drop_best_endpoint_mean": drop_best,
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

    p1 = analyze(gains(cells, "sign_flipped", "sign_documented"))
    p2 = analyze(gains(cells, "sign_random", "sign_documented"))
    p3 = analyze(gains(cells, "free", "sign_documented"))
    summary = {
        "probe_root": str(root), "task": "M3_nhkn2hrs",
        "metric": f"{METRIC} (lower is better); gain = lesion - documented",
        "endpoints": sorted(cells),
        "bootstrap": {"reps": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED,
                      "hierarchy": "endpoints then cells"},
        "GS_P1_identification_flipped": p1,
        "GS_P2_neutral_random": p2,
        "GS_P3_utility_vs_free": p3,
        "GS_P1_pass": bool(p1["separated"] and p1["n_endpoints_negative"] == 0),
        "GS_P2_pass": bool(p2["mean_gain"] > 0.0
                           and p2["mean_gain"] < p1["mean_gain"]),
        "GS_P3_pass_no_utility": bool(not p3["separated"]),
    }
    (root / "SUMMARY_V1.json").write_text(
        json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
