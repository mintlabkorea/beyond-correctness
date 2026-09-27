#!/usr/bin/env python3
"""Adjudicate the frozen bidirectional ten-endpoint label-panel extension."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np


K = "256"
DIRECTIONS = ("nh2kn", "kn2nh")
SEEDS = tuple(range(50, 60))
ORIGINAL_TARGETS = (
    "current_smoking_status", "diabetes_history", "hypertension_history")
REPS = 10_000
SEED = 20260820
MIN_COVERAGE = 8


def same_float(a: float, b: float) -> bool:
    if math.isnan(float(a)) and math.isnan(float(b)):
        return True
    return float(a) == float(b)


def load_cells(root: Path) -> dict[tuple[str, int], dict]:
    cells = {}
    for path in sorted(root.glob("*/seed_*/metrics.json")):
        record = json.loads(path.read_text())
        key = (record["target"], int(record["seed"]))
        if key in cells:
            raise RuntimeError(f"duplicate cell {key}")
        cells[key] = record
    return cells


def finite(values) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    return array[np.isfinite(array)]


def clustered_bootstrap(unit_values: dict[str, dict[str, np.ndarray]],
                        key: str) -> list[float]:
    rng = np.random.default_rng(int(hashlib.sha256(
        f"label_panel_10|{SEED}|{key}".encode()).hexdigest()[:8], 16))
    targets = sorted(unit_values)
    means = np.empty(REPS, dtype=np.float64)
    for rep in range(REPS):
        chosen = rng.integers(0, len(targets), size=len(targets))
        clusters = []
        for index in chosen:
            target = targets[int(index)]
            direction_means = []
            for direction in DIRECTIONS:
                values = unit_values[target][direction]
                draw = rng.choice(values, size=len(values), replace=True)
                direction_means.append(float(np.mean(draw)))
            clusters.append(float(np.mean(direction_means)))
        means[rep] = float(np.mean(clusters))
    return [float(x) for x in np.quantile(means, [0.025, 0.975])]


def summarize_values(unit_values: dict[str, dict[str, np.ndarray]],
                     key: str) -> dict:
    per_direction = {
        direction: float(np.mean(np.concatenate([
            unit_values[target][direction] for target in sorted(unit_values)])))
        for direction in DIRECTIONS
    }
    per_endpoint = {
        target: float(np.mean([
            np.mean(unit_values[target][direction]) for direction in DIRECTIONS]))
        for target in sorted(unit_values)
    }
    ordered = sorted(per_endpoint, key=per_endpoint.get, reverse=True)
    pooled = float(np.mean(list(per_endpoint.values())))
    return {
        "mean": pooled,
        "ci95": clustered_bootstrap(unit_values, key),
        "per_direction_mean": per_direction,
        "per_endpoint_mean": per_endpoint,
        "endpoint_win_rate_above_zero": float(np.mean(
            np.asarray(list(per_endpoint.values())) > 0)),
        "endpoint_rate_below_half": float(np.mean(
            np.asarray(list(per_endpoint.values())) < 0.5)),
        "best_endpoint": ordered[0],
        "drop_best_mean": float(np.mean([per_endpoint[t] for t in ordered[1:]])),
        "drop_best_two_mean": float(np.mean([per_endpoint[t] for t in ordered[2:]])),
        "diabetes_excluded_mean": float(np.mean([
            value for target, value in per_endpoint.items()
            if target != "diabetes_history"])),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nh2kn-root", type=Path, required=True)
    parser.add_argument("--kn2nh-root", type=Path, required=True)
    parser.add_argument("--old-nh2kn-root", type=Path, required=True)
    parser.add_argument("--old-kn2nh-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    roots = {"nh2kn": args.nh2kn_root, "kn2nh": args.kn2nh_root}
    old_roots = {
        "nh2kn": args.old_nh2kn_root, "kn2nh": args.old_kn2nh_root}
    cells = {direction: load_cells(root) for direction, root in roots.items()}
    old = {direction: load_cells(root) for direction, root in old_roots.items()}
    targets = sorted(set(key[0] for key in cells["nh2kn"]))
    expected = {(target, seed) for target in targets for seed in SEEDS}
    if len(targets) != 10 or any(set(cells[d]) != expected for d in DIRECTIONS):
        raise RuntimeError("ten-endpoint grid is incomplete")

    old_exact = True
    for direction in DIRECTIONS:
        for target in ORIGINAL_TARGETS:
            for seed in SEEDS:
                new_arms = cells[direction][(target, seed)]["auroc"][K]
                old_arms = old[direction][(target, seed)]["auroc"][K]
                old_exact &= all(same_float(new_arms[arm], old_arms[arm])
                                 for arm in new_arms)

    coverage = {}
    gain_values = {}
    raw_values = {}
    raw_minus_pipeline = {}
    pipeline_values = {}
    added_table_exact = True
    for target in targets:
        coverage[target] = {}
        gain_values[target] = {}
        raw_values[target] = {}
        raw_minus_pipeline[target] = {}
        pipeline_values[target] = {}
        for direction in DIRECTIONS:
            records = [cells[direction][(target, seed)]["auroc"][K]
                       for seed in SEEDS]
            gains = finite([
                record["pipeline_table"] - record["placebo_table"]
                for record in records])
            coverage[target][direction] = int(len(gains))
            gain_values[target][direction] = gains
            raw_values[target][direction] = finite([
                record["raw"] for record in records])
            raw_minus_pipeline[target][direction] = finite([
                record["raw"] - record["pipeline_table"] for record in records])
            pipeline_values[target][direction] = finite([
                record["pipeline_table"] for record in records])
            if target not in ORIGINAL_TARGETS:
                added_table_exact &= all(same_float(
                    record["llm_table"], record["pipeline_table"])
                    for record in records)

    coverage_pass = all(
        coverage[target][direction] >= MIN_COVERAGE
        for target in targets for direction in DIRECTIONS)
    p1 = summarize_values(gain_values, "pipeline_vs_placebo")
    p1["coverage_gate_pass"] = coverage_pass
    p1["separated"] = bool(
        coverage_pass and old_exact and added_table_exact
        and p1["mean"] > 0 and p1["ci95"][0] > 0
        and p1["endpoint_win_rate_above_zero"] >= 0.60
        and p1["drop_best_mean"] > 0
        and p1["diabetes_excluded_mean"] > 0)

    r1 = summarize_values(raw_values, "raw_absolute")
    r1["reversal_separated"] = bool(
        old_exact and added_table_exact
        and r1["mean"] < 0.5 and r1["ci95"][1] < 0.5
        and all(value < 0.5 for value in r1["per_direction_mean"].values())
        and r1["endpoint_rate_below_half"] >= 0.60
        and r1["diabetes_excluded_mean"] < 0.5)

    payload = {
        "complete": True,
        "prior_observation_disclosure": {
            "ten_endpoint_interactions_observed": True,
            "original_three_label_panel_observed": True,
            "new_label_panel_endpoints": 7,
        },
        "n_endpoint_clusters": len(targets),
        "n_direction_units": len(targets) * 2,
        "n_cells": sum(len(value) for value in cells.values()),
        "primary_k": 256,
        "construction": {
            "coverage_by_endpoint_direction": coverage,
            "minimum_finite_pairs_required": MIN_COVERAGE,
            "coverage_gate_pass": coverage_pass,
            "original_three_exact_K256_reproduction": old_exact,
            "added_seven_documented_equals_pipeline_exact": added_table_exact,
            "added_seven_llm_provenance": "codebook_registry_not_llm",
        },
        "P1_pipeline_vs_placebo": p1,
        "R1_raw_absolute_reversal": r1,
        "raw_minus_pipeline_descriptive": summarize_values(
            raw_minus_pipeline, "raw_minus_pipeline"),
        "pipeline_absolute_descriptive": summarize_values(
            pipeline_values, "pipeline_absolute"),
        "llm_table_scope": (
            "literal LLM only for original three; no pooled ten-endpoint LLM claim"),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps({
        "written": str(args.out),
        "construction": payload["construction"],
        "P1_separated": p1["separated"],
        "P1_mean_ci": [p1["mean"], p1["ci95"]],
        "R1_separated": r1["reversal_separated"],
        "R1_mean_ci": [r1["mean"], r1["ci95"]],
    }, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
