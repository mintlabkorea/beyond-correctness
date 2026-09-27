#!/usr/bin/env python3
"""Summarize the examination domain-local no-bridge three-arm audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.stats import norm, t


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "experiments/crta_v3_exam_no_bridge_reference_v1"
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 20260828
CONTRASTS = {
    "content_S_minus_W": ("S_shared_bridge", "W_deranged_bridge"),
    "utility_S_minus_R": ("S_shared_bridge", "R_domain_local"),
    "reference_minus_wrong_R_minus_W": (
        "R_domain_local", "W_deranged_bridge"),
}


def analyze(groups: dict[str, np.ndarray], rng: np.random.Generator) -> dict:
    endpoints = sorted(groups)
    flat = np.concatenate([groups[key] for key in endpoints])
    means = {key: float(np.mean(groups[key])) for key in endpoints}
    best = max(means, key=means.get)
    drop_best = float(np.mean(np.concatenate(
        [groups[key] for key in endpoints if key != best])))
    draws = np.empty(BOOTSTRAP_REPS)
    for index in range(BOOTSTRAP_REPS):
        chosen = rng.integers(0, len(endpoints), size=len(endpoints))
        values = []
        for endpoint_index in chosen:
            block = groups[endpoints[int(endpoint_index)]]
            values.append(block[rng.integers(0, len(block), size=len(block))])
        draws[index] = float(np.mean(np.concatenate(values)))
    low, high = np.quantile(draws, [0.025, 0.975])
    mean = float(np.mean(flat))
    win = float(np.mean(flat > 0.0))
    return {
        "mean": mean,
        "ci95": [float(low), float(high)],
        "win": win,
        "drop_best_endpoint_mean": drop_best,
        "n_endpoints": len(endpoints),
        "n_cells": len(flat),
        "per_endpoint_mean": means,
        "separated": bool(
            mean > 0.0 and low > 0.0 and win >= 0.60 and drop_best > 0.0),
    }


def interval_sensitivities(endpoint_means: dict[str, float], seed: int) -> dict:
    values = np.asarray(list(endpoint_means.values()), dtype=float)
    n_units = len(values)
    estimate = float(np.mean(values))
    standard_error = float(np.std(values, ddof=1) / np.sqrt(n_units))
    critical = float(t.ppf(0.975, n_units - 1))
    student_t = [estimate - critical * standard_error,
                 estimate + critical * standard_error]

    rng = np.random.default_rng(seed)
    indices = rng.integers(0, n_units, size=(BOOTSTRAP_REPS, n_units))
    draws = values[indices]
    draw_means = draws.mean(axis=1)
    ordered = np.sort(draw_means)

    less = float(np.mean(draw_means < estimate))
    z0 = float(norm.ppf(np.clip(
        less, 1.0 / (2 * BOOTSTRAP_REPS),
        1.0 - 1.0 / (2 * BOOTSTRAP_REPS))))
    jackknife = (values.sum() - values) / (n_units - 1)
    differences = jackknife.mean() - jackknife
    denominator = 6.0 * np.power(np.sum(differences ** 2), 1.5)
    acceleration = (float(np.sum(differences ** 3) / denominator)
                    if denominator > 0 else 0.0)

    def adjusted(alpha: float) -> float:
        z_alpha = float(norm.ppf(alpha))
        return float(norm.cdf(
            z0 + (z0 + z_alpha)
            / (1.0 - acceleration * (z0 + z_alpha))))

    bca = np.quantile(ordered, [adjusted(0.025), adjusted(0.975)])

    draw_se = draws.std(axis=1, ddof=1) / np.sqrt(n_units)
    valid = draw_se > 1e-12
    t_star = (draw_means[valid] - estimate) / draw_se[valid]
    quantiles = np.quantile(t_star, [0.025, 0.975])
    studentized = [estimate - float(quantiles[1]) * standard_error,
                   estimate - float(quantiles[0]) * standard_error]
    return {
        "student_t_cluster_mean": [float(value) for value in student_t],
        "bca_cluster_mean": [float(value) for value in bca],
        "studentized_cluster_bootstrap": studentized,
        "bootstrap_reps": BOOTSTRAP_REPS,
        "seed": seed,
        "studentized_valid_fraction": float(np.mean(valid)),
    }


def leave_one_endpoint_out(
        groups: dict[str, np.ndarray], seed: int) -> dict:
    """Repeat the frozen hierarchical bootstrap after each endpoint omission."""
    endpoints = sorted(groups)
    rows = {}
    for index, omitted in enumerate(endpoints):
        retained = {
            key: values for key, values in groups.items() if key != omitted}
        record = analyze(retained, np.random.default_rng(seed + index))
        rows[omitted] = {
            "mean": record["mean"],
            "ci95": record["ci95"],
            "win": record["win"],
            "n_endpoints": record["n_endpoints"],
            "n_cells": record["n_cells"],
            "separated": record["separated"],
        }
    minimum = min(rows, key=lambda key: rows[key]["ci95"][0])
    return {
        "analysis_status": "post-result leave-one-endpoint-out sensitivity",
        "bootstrap": {
            "reps": BOOTSTRAP_REPS,
            "seed_base": seed,
            "hierarchy": "retained endpoints then seeds",
        },
        "rows": rows,
        "all_lower_bounds_above_zero": all(
            row["ci95"][0] > 0.0 for row in rows.values()),
        "minimum_lower_bound": {
            "omitted": minimum,
            "value": rows[minimum]["ci95"][0],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=DEFAULT_ROOT)
    args = parser.parse_args()
    cells = []
    for path in sorted(args.root.glob("*/seed_*/metrics.json")):
        cells.append(json.loads(path.read_text(encoding="utf-8")))
    if len(cells) != 60:
        raise RuntimeError(f"expected 60 cells, found {len(cells)}")

    grouped = {name: {} for name in CONTRASTS}
    for cell in cells:
        scores = cell["nrmse"]
        for name, (left, right) in CONTRASTS.items():
            # Higher-is-better gain for lower-is-better nRMSE.
            value = float(scores[right]) - float(scores[left])
            grouped[name].setdefault(cell["target"], []).append(value)

    rng = np.random.default_rng(BOOTSTRAP_SEED)
    contrast_summaries = {}
    for index, (name, endpoint_groups) in enumerate(grouped.items()):
        arrays = {
            key: np.asarray(values, dtype=float)
            for key, values in endpoint_groups.items()}
        record = analyze(
            arrays, rng)
        record["interval_sensitivities"] = interval_sensitivities(
            record["per_endpoint_mean"], BOOTSTRAP_SEED + 100 + index)
        record["leave_one_endpoint_out"] = leave_one_endpoint_out(
            arrays, BOOTSTRAP_SEED + 1_000 + 100 * index)
        contrast_summaries[name] = record

    summary = {
        "analysis_status": "post-result reference-construction extension",
        "bootstrap": {"reps": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED,
                      "hierarchy": "endpoints then seeds"},
        "reference": (
            "domain-local member columns preserve values and width while "
            "removing shared cross-domain member identity"),
        "contrasts": contrast_summaries,
    }
    out = args.root / "SUMMARY_V1.json"
    out.write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
