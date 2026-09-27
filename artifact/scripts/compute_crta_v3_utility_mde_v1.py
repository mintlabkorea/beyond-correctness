#!/usr/bin/env python3
"""E1a: minimum detectable effect of the utility contrast.

For each dataset whose utility contrast returned a null, add a constant
improvement delta to the documented arm's per-cell metric and re-run the
frozen separation rule (mean > 0, hierarchical CI excluding 0, win >=
0.60, drop-best > 0).  Report the smallest delta at which the verdict
flips.  Turns "no utility" into "utility < MDE".

Design: `iclr_latex_v3/UTILITY_CONTRAST_POSITIVE_CONTROL_PREREGISTRATION_V1.md`.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 20260819
WIN_THRESHOLD = 0.60
GRID = np.round(np.arange(0.0, 0.0501, 0.0005), 5)


def hierarchical_ci(groups: dict[str, np.ndarray]) -> tuple[float, float]:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    keys = sorted(groups)
    means = np.empty(BOOTSTRAP_REPS)
    for rep in range(BOOTSTRAP_REPS):
        chosen = rng.choice(len(keys), size=len(keys), replace=True)
        parts = [rng.choice(groups[keys[i]], size=len(groups[keys[i]]),
                            replace=True) for i in chosen]
        means[rep] = float(np.mean(np.concatenate(parts)))
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def separated(groups: dict[str, np.ndarray]) -> bool:
    flat = np.concatenate([groups[k] for k in sorted(groups)])
    low, _ = hierarchical_ci(groups)
    per_group = {k: float(np.mean(v)) for k, v in groups.items()}
    best = max(per_group, key=per_group.get)
    rest = [v for k, v in groups.items() if k != best]
    drop_best = float(np.mean(np.concatenate(rest))) if rest else float("nan")
    return bool(float(np.mean(flat)) > 0.0 and low > 0.0
                and float(np.mean(flat > 0.0)) >= WIN_THRESHOLD
                and drop_best > 0.0)


def mde(groups: dict[str, np.ndarray]) -> float | None:
    """Smallest constant added to the documented arm that flips the verdict."""
    for delta in GRID:
        shifted = {k: v + float(delta) for k, v in groups.items()}
        if separated(shifted):
            return float(delta)
    return None


def pam_groups() -> dict[str, np.ndarray]:
    """nh<->kn: free - sign_documented at K=256, clustered by target."""
    groups: dict[str, list[float]] = {}
    for path in (ROOT / "experiments/crta_v3_pam_constraint_relations_v1").glob(
            "*/seed_*/metrics.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        cell = record["nrmse"]["256"]
        groups.setdefault(record["target"], []).append(
            cell["free"] - cell["sign_documented"])
    return {k: np.asarray(v) for k, v in groups.items()}


def m3_groups() -> dict[str, np.ndarray]:
    groups: dict[str, list[float]] = {}
    for path in (ROOT / "experiments/crta_v3_m3_sign_probe_v1").glob(
            "*/support_*/seed_*/metrics.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        arms = record["arms"]
        groups.setdefault(record["endpoint"], []).append(
            arms["free"]["query_sd_normalized_rmse"]
            - arms["sign_documented"]["query_sd_normalized_rmse"])
    return {k: np.asarray(v) for k, v in groups.items()}


def camels_groups(root: Path) -> dict[str, np.ndarray]:
    groups: dict[str, list[float]] = {}
    for path in root.glob("support_*/seed_*/metrics.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        arms = record["arms"]
        for basin, free in arms["free"]["per_basin"].items():
            documented = arms["sign_documented"]["per_basin"][basin]
            value = free["log1p_rmse"] - documented["log1p_rmse"]
            if np.isfinite(value):
                groups.setdefault(basin, []).append(value)
    return {k: np.asarray(v) for k, v in groups.items()}


def main() -> int:
    datasets = {
        "nhkn_pam_K256": pam_groups(),
        "m3_nhkn2hrs": m3_groups(),
        "camels_v2_handkey": camels_groups(
            ROOT / "experiments/crta_v3_camels_sign_probe_v2"),
        "camels_llm_table": camels_groups(
            ROOT / "experiments/crta_v3_camels_sign_probe_llm_v1"),
    }
    report = {}
    for name, groups in datasets.items():
        if not groups:
            report[name] = {"error": "no cells"}
            continue
        flat = np.concatenate([groups[k] for k in sorted(groups)])
        observed = float(np.mean(flat))
        detected = mde(groups)
        report[name] = {
            "n_clusters": len(groups), "n_cells": int(len(flat)),
            "observed_utility_gain": round(observed, 6),
            "mde": detected,
            "observed_over_mde": (round(observed / detected, 3)
                                  if detected else None),
            "statement": (f"the rule detects a true utility of "
                          f"{detected:.4f} nRMSE or larger; the observed "
                          f"effect was {observed:.4f}"
                          if detected else
                          "no delta up to 0.05 flips the verdict"),
        }
        print(f"{name:22s} clusters {len(groups):3d} cells {len(flat):4d} "
              f"observed {observed:+.5f} MDE {detected}")
    out = ROOT / "experiments/crta_v3_utility_mde_v1"
    out.mkdir(parents=True, exist_ok=True)
    (out / "MDE_V1.json").write_text(
        json.dumps(report, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
