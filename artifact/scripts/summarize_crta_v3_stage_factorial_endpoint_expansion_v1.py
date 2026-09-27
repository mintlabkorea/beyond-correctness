#!/usr/bin/env python3
"""Artifact-robust adjudication of the ten-endpoint bidirectional expansion."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

REPS = 10000
SEED = 20260820
K = "256"
SENSITIVITY_EXCLUSION_LADDER = (
    ("all_endpoints", ()),
    ("exclude_diabetes", ("diabetes_history",)),
    ("exclude_diabetes_and_heart_attack",
     ("diabetes_history", "heart_attack_history")),
)


def load(root: Path, direction: str) -> dict[tuple[str, str], np.ndarray]:
    grouped = {}
    for p in sorted(root.glob("*/seed_*/metrics.json")):
        rec = json.loads(p.read_text())
        arms = rec["auroc"][K]
        grouped.setdefault((direction, rec["target"]), []).append(arms)
    return {k: np.asarray(v, dtype=object) for k, v in grouped.items()}


def interaction(arms: dict, corrected: bool) -> float:
    f = (lambda x: max(float(x), 1.0 - float(x))) if corrected else float
    return ((f(arms["a11_stage_columns"]) - f(arms["a10_stage"]))
            - (f(arms["a01_columns"]) - f(arms["a00_base"])))


def analyze(units: dict[tuple[str, str], np.ndarray], corrected: bool,
            key: str) -> dict:
    values = {u: np.asarray([interaction(a, corrected) for a in arr])
              for u, arr in units.items()}
    flat = np.concatenate(list(values.values()))
    seed = int(hashlib.sha256(f"endpoint_exp|{SEED}|{key}".encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    names = sorted(values)
    means = np.empty(REPS)
    for rep in range(REPS):
        chosen = rng.integers(0, len(names), size=len(names))
        sample = []
        for i in chosen:
            x = values[names[i]]
            sample.append(x[rng.integers(0, len(x), size=len(x))])
        means[rep] = np.concatenate(sample).mean()
    lo, hi = np.quantile(means, [0.025, 0.975])
    per_unit = {f"{d}:{t}": float(x.mean()) for (d, t), x in values.items()}
    best = max(per_unit, key=per_unit.get)
    drop = np.concatenate([x for u, x in values.items()
                           if f"{u[0]}:{u[1]}" != best]).mean()
    return {"mean": float(flat.mean()), "ci95": [float(lo), float(hi)],
            "win": float(np.mean(flat > 0)), "n_units": len(values),
            "n_seed_cells": len(flat), "per_unit_mean": per_unit,
            "drop_best_unit_mean": float(drop),
            "separated": bool(lo > 0 and np.mean(flat > 0) >= 0.60 and drop > 0)}


def endpoint_clustered_sensitivity(
        units: dict[tuple[str, str], np.ndarray]) -> dict:
    """Post-hoc robustness check that clusters the two directions by endpoint.

    The frozen primary analysis treats endpoint-direction pairs as units.  This
    sensitivity first averages seeds within each direction and then averages
    the two directions within endpoint.  It bootstraps the resulting endpoint
    clusters, so paired directions are never resampled independently.
    """
    unit_means = {
        (direction, target): float(np.mean([
            interaction(arms, corrected=True) for arms in arr
        ]))
        for (direction, target), arr in units.items()
    }
    targets = sorted({target for _, target in unit_means})
    cluster_means = {
        target: float(np.mean([
            value for (direction, name), value in unit_means.items()
            if name == target
        ]))
        for target in targets
    }
    directions = sorted({direction for direction, _ in unit_means})
    if len(directions) != 2:
        raise ValueError(f"expected two directions, got {directions}")
    direction_correlation = float(np.corrcoef(
        [unit_means[(directions[0], target)] for target in targets],
        [unit_means[(directions[1], target)] for target in targets],
    )[0, 1])

    ladder = {}
    for label, excluded in SENSITIVITY_EXCLUSION_LADDER:
        kept = [target for target in targets if target not in excluded]
        values = np.asarray([cluster_means[target] for target in kept])
        rng = np.random.default_rng(SEED)
        chosen = rng.integers(0, len(values), size=(REPS, len(values)))
        bootstrap_means = values[chosen].mean(axis=1)
        lo, hi = np.quantile(bootstrap_means, [0.025, 0.975])
        best_index = int(np.argmax(values))
        drop_best_mean = float(np.delete(values, best_index).mean())
        win = float(np.mean(values > 0))
        ladder[label] = {
            "excluded_endpoints": list(excluded),
            "n_endpoint_clusters": len(values),
            "mean": float(values.mean()),
            "ci95": [float(lo), float(hi)],
            "win": win,
            "best_endpoint": kept[best_index],
            "drop_best_endpoint_mean": drop_best_mean,
            "ci_excludes_zero": bool(lo > 0 or hi < 0),
            "separated_under_analogous_rule": bool(
                values.mean() > 0 and lo > 0 and win >= 0.60
                and drop_best_mean > 0
            ),
        }

    full_mean = ladder["all_endpoints"]["mean"]
    no_diabetes_mean = ladder["exclude_diabetes"]["mean"]
    return {
        "analysis_status": "post_hoc_sensitivity_stricter_than_frozen_unit_analysis",
        "bootstrap_unit": "endpoint_cluster_mean_over_two_directions",
        "bootstrap_reps": REPS,
        "bootstrap_seed": SEED,
        "direction_order_for_correlation": directions,
        "cross_direction_endpoint_correlation": direction_correlation,
        "per_endpoint_cluster_mean": cluster_means,
        "negative_endpoint_clusters": sorted(
            target for target, value in cluster_means.items() if value < 0
        ),
        "diabetes_removal_relative_mean_reduction": float(
            (full_mean - no_diabetes_mean) / full_mean
        ),
        "exclusion_ladder": ladder,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--nh2kn-root", type=Path, required=True)
    ap.add_argument("--kn2nh-root", type=Path, required=True)
    args = ap.parse_args()
    forward = load(args.nh2kn_root, "nh2kn")
    reverse = load(args.kn2nh_root, "kn2nh")
    pooled = {**forward, **reverse}
    expected = 10
    complete = (len(forward) == expected and len(reverse) == expected
                and all(len(v) == 10 for v in pooled.values()))
    result = {
        "forward_raw": analyze(forward, False, "forward_raw") if forward else None,
        "forward_corrected": analyze(forward, True, "forward_corrected") if forward else None,
        "reverse_raw": analyze(reverse, False, "reverse_raw") if reverse else None,
        "reverse_corrected": analyze(reverse, True, "reverse_corrected") if reverse else None,
        "pooled_raw": analyze(pooled, False, "pooled_raw") if pooled else None,
        "pooled_corrected": analyze(pooled, True, "pooled_corrected") if pooled else None,
    }
    sensitivity = (endpoint_clustered_sensitivity(pooled)
                   if complete else None)
    verdict = ({
        "ENDPOINT_P1_pooled_corrected_separates": result["pooled_corrected"]["separated"],
        "ENDPOINT_P2_corrected_positive_both_directions": bool(
            result["forward_corrected"]["mean"] > 0
            and result["reverse_corrected"]["mean"] > 0),
        "ENDPOINT_P3_raw_pooled_separates": result["pooled_raw"]["separated"],
    } if complete else {"status": "incomplete — verdicts withheld"})
    payload = {
        "complete": complete,
        "primary_k": int(K),
        "verdicts": verdict,
        "results": result,
        "post_hoc_sensitivity": {
            "pooled_corrected_endpoint_clustered": sensitivity,
        },
    }
    for root in (args.nh2kn_root, args.kn2nh_root):
        root.mkdir(parents=True, exist_ok=True)
    out = args.nh2kn_root.parent / "crta_v3_stage_endpoint_expansion_SUMMARY_V1.json"
    out.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"written": str(out), "verdicts": verdict}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
