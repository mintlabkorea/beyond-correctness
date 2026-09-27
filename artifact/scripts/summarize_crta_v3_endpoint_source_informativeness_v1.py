#!/usr/bin/env python3
"""Adjudicate the ten-endpoint source-informativeness prediction."""

from __future__ import annotations

import argparse
import itertools
import json
import math
from itertools import islice
from pathlib import Path

import numpy as np
from scipy.stats import rankdata, spearmanr


K = "256"
DIRECTIONS = ("nh2kn", "kn2nh")
SEEDS = tuple(range(50, 60))
LOW_SEEDS = frozenset(range(50, 55))
HIGH_SEEDS = frozenset(range(55, 60))
ARMS = ("a11_stage_columns", "a10_stage", "a01_columns", "a00_base")


def corrected(value: float) -> float:
    value = float(value)
    return max(value, 1.0 - value)


def interaction(arms: dict[str, float], fold: bool = True) -> float:
    f = corrected if fold else float
    return ((f(arms["a11_stage_columns"]) - f(arms["a10_stage"]))
            - (f(arms["a01_columns"]) - f(arms["a00_base"])))


def rho(x: np.ndarray, y: np.ndarray) -> float:
    value = float(spearmanr(x, y).statistic)
    if not np.isfinite(value):
        raise RuntimeError("undefined Spearman correlation")
    return value


def exact_one_sided_spearman(x: np.ndarray, y: np.ndarray,
                             chunk: int = 100_000) -> dict[str, float | int]:
    """Exact conditional permutation p for rho(x,y) >= observed."""
    if len(x) != len(y):
        raise ValueError("length mismatch")
    rx = rankdata(x, method="average").astype(np.float64)
    ry = rankdata(y, method="average").astype(np.float64)
    cx = rx - rx.mean()
    cy = ry - ry.mean()
    denom = float(np.sqrt(np.sum(cx * cx) * np.sum(cy * cy)))
    if denom <= 0:
        raise RuntimeError("constant rank vector")
    observed_dot = float(np.dot(cx, cy))
    observed_rho = observed_dot / denom
    iterator = itertools.permutations(cy.tolist())
    extreme = 0
    total = 0
    while True:
        batch = list(islice(iterator, chunk))
        if not batch:
            break
        values = np.asarray(batch, dtype=np.float64) @ cx
        extreme += int(np.sum(values >= observed_dot - 1e-12))
        total += len(batch)
    expected = math.factorial(len(x))
    if total != expected:
        raise AssertionError(f"permutation count {total} != {expected}")
    return {
        "rho": observed_rho,
        "one_sided_exact_p": extreme / total,
        "extreme_permutations": extreme,
        "total_permutations": total,
    }


def load_extension(root: Path, direction: str) -> dict[tuple[str, int], dict]:
    records = {}
    for path in sorted(root.glob("*/seed_*/metrics.json")):
        record = json.loads(path.read_text())
        if record.get("direction") != direction:
            raise RuntimeError(f"direction mismatch: {path}")
        key = (record["target"], int(record["seed"]))
        if key in records:
            raise RuntimeError(f"duplicate extension cell: {key}")
        records[key] = record
    return records


def load_reference(root: Path) -> dict[tuple[str, int], dict]:
    records = {}
    for path in sorted(root.glob("*/seed_*/metrics.json")):
        record = json.loads(path.read_text())
        key = (record["target"], int(record["seed"]))
        if key in records:
            raise RuntimeError(f"duplicate reference cell: {key}")
        records[key] = record
    return records


def half(values: list[dict], seeds: frozenset[int], key: str) -> float:
    selected = [record[key] for record in values if record["seed"] in seeds]
    if len(selected) != 5:
        raise RuntimeError(f"expected five values for {key}, got {len(selected)}")
    return float(np.mean(selected))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nh2kn-root", type=Path, required=True)
    parser.add_argument("--kn2nh-root", type=Path, required=True)
    parser.add_argument("--nh2kn-reference", type=Path, required=True)
    parser.add_argument("--kn2nh-reference", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    extension = {
        "nh2kn": load_extension(args.nh2kn_root, "nh2kn"),
        "kn2nh": load_extension(args.kn2nh_root, "kn2nh"),
    }
    reference = {
        "nh2kn": load_reference(args.nh2kn_reference),
        "kn2nh": load_reference(args.kn2nh_reference),
    }
    targets = sorted(set(key[0] for key in reference["nh2kn"])
                     & set(key[0] for key in reference["kn2nh"]))
    expected_keys = {(target, seed) for target in targets for seed in SEEDS}
    if len(targets) != 10:
        raise RuntimeError(f"expected ten targets, got {targets}")
    for direction in DIRECTIONS:
        if set(extension[direction]) != expected_keys:
            raise RuntimeError(f"incomplete extension {direction}")
        if not expected_keys.issubset(reference[direction]):
            raise RuntimeError(f"incomplete reference {direction}")

    per_direction: dict[str, dict[str, dict[str, float]]] = {
        direction: {} for direction in DIRECTIONS}
    detailed: dict[str, list[dict]] = {}
    provenance = set()
    for direction in DIRECTIONS:
        for target in targets:
            cells = []
            for seed in SEEDS:
                ext = extension[direction][(target, seed)]
                ref = reference[direction][(target, seed)]
                arms = {arm: float(ref["auroc"][K][arm]) for arm in ARMS}
                source_auc = float(ext["auroc"]["source_only_correct"])
                target_auc = float(ext["auroc"]["target_only_correct"])
                reference_a11 = float(ref["auroc"][K]["a11_stage_columns"])
                if abs(reference_a11 - float(ext["reference_a11_auroc"])) > 1e-15:
                    raise RuntimeError("reference a11 mismatch")
                cells.append({
                    "seed": seed,
                    "source_score": source_auc - 0.5,
                    "source_auc": source_auc,
                    "target_auc": target_auc,
                    "interaction_corrected": interaction(arms, fold=True),
                    "interaction_raw": interaction(arms, fold=False),
                    "utility_corrected": corrected(reference_a11) - corrected(target_auc),
                    "utility_raw": reference_a11 - target_auc,
                })
                provenance.add((
                    ext["runner_sha256"], ext["base_runner_sha256"],
                    ext["registry_sha256"], ext["prereg_sha256"],
                ))
            detailed[f"{direction}:{target}"] = cells
            per_direction[direction][target] = {
                "source_score": float(np.mean([c["source_score"] for c in cells])),
                "source_auc": float(np.mean([c["source_auc"] for c in cells])),
                "interaction_corrected": float(np.mean([
                    c["interaction_corrected"] for c in cells])),
                "interaction_raw": float(np.mean([c["interaction_raw"] for c in cells])),
                "target_utility_corrected": float(np.mean([
                    c["utility_corrected"] for c in cells])),
                "target_utility_raw": float(np.mean([c["utility_raw"] for c in cells])),
            }

    if len(provenance) != 1:
        raise RuntimeError(f"multiple provenance tuples: {len(provenance)}")

    clusters = {}
    for target in targets:
        clusters[target] = {
            key: float(np.mean([per_direction[d][target][key] for d in DIRECTIONS]))
            for key in per_direction["nh2kn"][target]
        }
    source = np.asarray([clusters[t]["source_score"] for t in targets])
    outcome = np.asarray([clusters[t]["interaction_corrected"] for t in targets])
    primary = exact_one_sided_spearman(source, outcome)
    diabetes_key = "diabetes_history"
    no_diabetes = [i for i, target in enumerate(targets) if target != diabetes_key]
    diabetes_excluded_rho = rho(source[no_diabetes], outcome[no_diabetes])
    leave_one_out = {}
    for i, target in enumerate(targets):
        keep = [j for j in range(len(targets)) if j != i]
        leave_one_out[target] = rho(source[keep], outcome[keep])
    primary["diabetes_excluded_rho"] = diabetes_excluded_rho
    primary["verdict_pass"] = bool(
        primary["rho"] > 0
        and primary["one_sided_exact_p"] < 0.05
        and diabetes_excluded_rho > 0
    )

    direction_results = {}
    for direction in DIRECTIONS:
        x = np.asarray([per_direction[direction][t]["source_score"] for t in targets])
        y = np.asarray([
            per_direction[direction][t]["interaction_corrected"] for t in targets])
        direction_results[direction] = {"rho": rho(x, y)}

    crossfit = {}
    for proxy_name, proxy_seeds, outcome_seeds in (
        ("proxy_50_54_vs_interaction_55_59", LOW_SEEDS, HIGH_SEEDS),
        ("proxy_55_59_vs_interaction_50_54", HIGH_SEEDS, LOW_SEEDS),
    ):
        proxy_values, outcome_values = [], []
        for target in targets:
            per_d_proxy, per_d_outcome = [], []
            for direction in DIRECTIONS:
                cells = detailed[f"{direction}:{target}"]
                per_d_proxy.append(half(cells, proxy_seeds, "utility_corrected"))
                per_d_outcome.append(half(
                    cells, outcome_seeds, "interaction_corrected"))
            proxy_values.append(float(np.mean(per_d_proxy)))
            outcome_values.append(float(np.mean(per_d_outcome)))
        crossfit[proxy_name] = rho(np.asarray(proxy_values), np.asarray(outcome_values))
    crossfit["mean_rho"] = float(np.mean(list(crossfit.values())))
    crossfit["status"] = "descriptive_part_whole_coupled_secondary"

    payload = {
        "complete": True,
        "prior_observation_disclosure": (
            "The existing ten-endpoint MxC outcomes were observed before this study."
        ),
        "n_endpoint_clusters": len(targets),
        "n_direction_units": len(targets) * len(DIRECTIONS),
        "n_new_cells": sum(len(records) for records in extension.values()),
        "new_fits_per_cell": 2,
        "primary": primary,
        "leave_one_endpoint_out_rho": leave_one_out,
        "direction_secondary": direction_results,
        "target_only_crossfit_secondary": crossfit,
        "endpoint_clusters": clusters,
        "per_direction": per_direction,
        "provenance_tuple": list(next(iter(provenance))),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps({
        "written": str(args.out),
        "primary": primary,
        "crossfit_secondary": crossfit,
    }, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
