#!/usr/bin/env python3
"""Adjudicate the CAMELS query-basin extension (X1-X3, X-MDE).

Frozen rules: `iclr_latex_v3/CAMELS_QUERY_EXTENSION_PREREGISTRATION_V1.md`.
Query basin is the independent cluster; hierarchical basin bootstrap
(10,000 reps, seed 20260819); separation = mean > 0 and CI95 low > 0 and
win >= 0.60; log1p-RMSE is the verdict metric.  X-MDE re-runs the E1a
injection (delta added to the documented arm, grid 0..0.05 step 0.0005)
on the extended cluster set.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "experiments/crta_v3_camels_query_extension_v1/probe"
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 20260819
WIN_THRESHOLD = 0.60
MDE_GRID = np.round(np.arange(0.0, 0.0501, 0.0005), 5)
FROZEN_QUERY_COUNT = 12


def load_basin_gains(root: Path, arm: str, reference: str
                     ) -> dict[str, np.ndarray]:
    groups: dict[str, list[float]] = {}
    for path in sorted(root.glob("support_*/seed_*/metrics.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        arms = record["arms"]
        for basin, ref_values in arms[reference]["per_basin"].items():
            value = (float(ref_values["log1p_rmse"])
                     - float(arms[arm]["per_basin"][basin]["log1p_rmse"]))
            if np.isfinite(value):
                groups.setdefault(basin, []).append(value)
    return {k: np.asarray(v) for k, v in groups.items()}


def hierarchical_ci(groups: dict[str, np.ndarray], seed: int
                    ) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    keys = sorted(groups)
    means = np.empty(BOOTSTRAP_REPS)
    for rep in range(BOOTSTRAP_REPS):
        chosen = rng.choice(len(keys), size=len(keys), replace=True)
        parts = [rng.choice(groups[keys[i]], size=len(groups[keys[i]]),
                            replace=True) for i in chosen]
        means[rep] = float(np.mean(np.concatenate(parts)))
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def analyze(groups: dict[str, np.ndarray]) -> dict:
    flat = np.concatenate([groups[k] for k in sorted(groups)])
    low, high = hierarchical_ci(groups, BOOTSTRAP_SEED)
    per_basin_means = {k: float(np.mean(v)) for k, v in groups.items()}
    return {
        "n_clusters": len(groups),
        "n_cells": int(len(flat)),
        "mean": float(np.mean(flat)),
        "ci95": [low, high],
        "win": float(np.mean(flat > 0.0)),
        "basins_negative": int(sum(1 for v in per_basin_means.values()
                                   if v < 0)),
        "separated": bool(float(np.mean(flat)) > 0.0 and low > 0.0
                          and float(np.mean(flat > 0.0)) >= WIN_THRESHOLD),
    }


def separated_with_delta(groups: dict[str, np.ndarray], delta: float) -> bool:
    shifted = {k: v + float(delta) for k, v in groups.items()}
    flat = np.concatenate([shifted[k] for k in sorted(shifted)])
    low, _ = hierarchical_ci(shifted, BOOTSTRAP_SEED)
    return bool(float(np.mean(flat)) > 0.0 and low > 0.0
                and float(np.mean(flat > 0.0)) >= WIN_THRESHOLD)


def mde(groups: dict[str, np.ndarray]) -> float | None:
    for delta in MDE_GRID:
        if separated_with_delta(groups, float(delta)):
            return float(delta)
    return None


def subgroup(groups: dict[str, np.ndarray], frozen_basins: set[str],
             keep_frozen: bool) -> dict[str, np.ndarray]:
    return {k: v for k, v in groups.items()
            if (k in frozen_basins) == keep_frozen}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--frozen-manifest", type=Path, default=(
        ROOT / "experiments/crta_v3_camels_native_screen_v1/data/"
        "split_manifest.json"))
    args = parser.parse_args()

    frozen_basins = set(map(str, json.loads(args.frozen_manifest.read_text())
                            ["target_query_basin_ids"]))
    if len(frozen_basins) != FROZEN_QUERY_COUNT:
        raise RuntimeError("unexpected frozen query basin count")

    gates = []
    for path in sorted(args.root.glob("support_*/seed_*/metrics.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        gates.append(record["replication_gate"]["passed"])
    if not gates or not all(gates):
        raise RuntimeError("replication gate missing or failed")

    contrasts = {
        "X1_content_documented_vs_flipped": ("sign_documented", "sign_flipped"),
        "X2_utility_documented_vs_free": ("sign_documented", "free"),
        "X3_content_documented_vs_random": ("sign_documented", "sign_random"),
    }
    sections = {}
    for name, (arm, reference) in contrasts.items():
        groups = load_basin_gains(args.root, arm, reference)
        sections[name] = {
            "extended": analyze(groups),
            "frozen_12_only": analyze(subgroup(groups, frozen_basins, True)),
            "extension_only": analyze(subgroup(groups, frozen_basins, False)),
        }

    utility_groups = load_basin_gains(args.root, "sign_documented", "free")
    mde_extended = mde(utility_groups)
    mde_frozen = mde(subgroup(utility_groups, frozen_basins, True))

    payload = {
        "clustering": "query basin (independent population unit)",
        "bootstrap": {"reps": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED},
        "replication_gate_cells": len(gates),
        "sections": sections,
        "X_MDE": {
            "grid_step": 0.0005,
            "extended_clusters": mde_extended,
            "frozen_12_clusters_recomputed": mde_frozen,
        },
        "verdicts": {
            "X1_content_separated": sections[
                "X1_content_documented_vs_flipped"]["extended"]["separated"],
            "X2_utility_separated": sections[
                "X2_utility_documented_vs_free"]["extended"]["separated"],
            "X3_random_content_separated": sections[
                "X3_content_documented_vs_random"]["extended"]["separated"],
        },
    }
    out_path = args.root.parent / "SUMMARY_V1.json"
    out_path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({"verdicts": payload["verdicts"],
                      "X_MDE": payload["X_MDE"],
                      "written": str(out_path)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
