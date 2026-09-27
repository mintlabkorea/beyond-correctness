#!/usr/bin/env python3
"""Exploratory ten-endpoint conditional-C analysis from existing XGB cells.

The evidence cells predate the freeze.  This script never labels the result
confirmatory; see CONDITIONAL_C_HISTGB_CONFIRMATION_FREEZE_V1.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import norm, t


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOTS = {
    "nh2kn": ROOT / "experiments/crta_v3_stage_endpoint_expansion_nh2kn_v1",
    "kn2nh": ROOT / "experiments/crta_v3_stage_endpoint_expansion_kn2nh_v1",
}
DEFAULT_OUT = (
    ROOT / "experiments/crta_v3_conditional_c_exploratory_v1/SUMMARY_V1.json"
)
PROTOCOL = ROOT / "iclr_latex_v3/CONDITIONAL_C_HISTGB_CONFIRMATION_FREEZE_V1.md"
K = "256"
N_BOOT = 10_000
BOOT_SEED = 20260827
FACTORIAL_ARMS = (
    "a00_base",
    "a01_columns",
    "a10_stage",
    "a11_stage_columns",
)


def corrected_auroc(value: float) -> float:
    return max(float(value), 1.0 - float(value))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load_direction(root: Path, direction: str) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for path in sorted(root.glob("*/seed_*/metrics.json")):
        cell = json.loads(path.read_text(encoding="utf-8"))
        if str(cell.get("primary_k")) != K:
            raise RuntimeError(f"unexpected primary K in {path}")
        arms = cell["auroc"][K]
        value = float(arms["a11_stage_columns"]) - float(arms["a10_stage"])
        if not math.isfinite(value):
            raise RuntimeError(f"nonfinite contrast in {path}")
        endpoint = str(cell["target"])
        out.setdefault(endpoint, []).append(value)
    counts = {endpoint: len(values) for endpoint, values in out.items()}
    if len(out) != 10 or set(counts.values()) != {10}:
        raise RuntimeError(f"incomplete {direction} panel: {counts}")
    return out


def load_factorial_direction(
    root: Path, direction: str,
) -> dict[str, list[dict[str, float]]]:
    """Load the same completed cells without selecting one factorial contrast."""
    out: dict[str, list[dict[str, float]]] = {}
    for path in sorted(root.glob("*/seed_*/metrics.json")):
        cell = json.loads(path.read_text(encoding="utf-8"))
        if str(cell.get("primary_k")) != K:
            raise RuntimeError(f"unexpected primary K in {path}")
        arms = cell["auroc"][K]
        values = {arm: float(arms[arm]) for arm in FACTORIAL_ARMS}
        if not all(math.isfinite(value) for value in values.values()):
            raise RuntimeError(f"nonfinite arm value in {path}")
        endpoint = str(cell["target"])
        out.setdefault(endpoint, []).append(values)
    counts = {endpoint: len(values) for endpoint, values in out.items()}
    if len(out) != 10 or set(counts.values()) != {10}:
        raise RuntimeError(f"incomplete {direction} factorial panel: {counts}")
    return out


def factorial_transparency(
    directions: dict[str, dict[str, list[dict[str, float]]]],
) -> dict[str, Any]:
    endpoint_sets = [set(panel) for panel in directions.values()]
    if not endpoint_sets or any(value != endpoint_sets[0] for value in endpoint_sets):
        raise RuntimeError("factorial direction endpoint sets differ")
    endpoints = sorted(endpoint_sets[0])
    rows: dict[str, Any] = {}
    vectors = {
        "c_given_measurement_off_raw": [],
        "c_given_measurement_supplied_raw": [],
        "mc_interaction_raw": [],
        "c_given_measurement_off_folded": [],
        "c_given_measurement_supplied_folded": [],
        "mc_interaction_folded": [],
    }
    for endpoint in endpoints:
        direction_arm_means = {
            direction: {
                arm: float(np.mean([cell[arm] for cell in panel[endpoint]]))
                for arm in FACTORIAL_ARMS
            }
            for direction, panel in directions.items()
        }
        arm_means = {
            arm: float(np.mean([
                direction_arm_means[direction][arm] for direction in directions
            ]))
            for arm in FACTORIAL_ARMS
        }
        direction_arm_folded_means = {
            direction: {
                arm: float(np.mean([
                    corrected_auroc(cell[arm]) for cell in panel[endpoint]
                ]))
                for arm in FACTORIAL_ARMS
            }
            for direction, panel in directions.items()
        }
        arm_folded_means = {
            arm: float(np.mean([
                direction_arm_folded_means[direction][arm]
                for direction in directions
            ]))
            for arm in FACTORIAL_ARMS
        }
        c_off = arm_means["a01_columns"] - arm_means["a00_base"]
        c_supplied = arm_means["a11_stage_columns"] - arm_means["a10_stage"]
        interaction = c_supplied - c_off
        c_off_folded = (
            arm_folded_means["a01_columns"] - arm_folded_means["a00_base"]
        )
        c_supplied_folded = (
            arm_folded_means["a11_stage_columns"]
            - arm_folded_means["a10_stage"]
        )
        interaction_folded = c_supplied_folded - c_off_folded
        vectors["c_given_measurement_off_raw"].append(c_off)
        vectors["c_given_measurement_supplied_raw"].append(c_supplied)
        vectors["mc_interaction_raw"].append(interaction)
        vectors["c_given_measurement_off_folded"].append(c_off_folded)
        vectors["c_given_measurement_supplied_folded"].append(c_supplied_folded)
        vectors["mc_interaction_folded"].append(interaction_folded)
        rows[endpoint] = {
            "arm_means_raw_auroc": arm_means,
            "arm_means_folded_auroc": arm_folded_means,
            "direction_arm_means_raw_auroc": direction_arm_means,
            "direction_arm_means_folded_auroc": direction_arm_folded_means,
            "a01_minus_a00": c_off,
            "a11_minus_a10": c_supplied,
            "interaction_raw": interaction,
            "folded_a01_minus_a00": c_off_folded,
            "folded_a11_minus_a10": c_supplied_folded,
            "interaction_folded": interaction_folded,
        }

    contrasts = {}
    for name, values in vectors.items():
        array = np.asarray(values, dtype=np.float64)
        contrasts[name] = {
            "mean": float(np.mean(array)),
            "median": float(np.median(array)),
            "positive_endpoint_clusters": int(np.sum(array > 0)),
            "intervals": bootstrap_intervals(array),
        }
    return {
        "metrics": {
            "raw": "raw AUROC; no arm-wise folding",
            "folded": "f(A)=max(A,1-A), applied per cell before differencing",
        },
        "aggregation": (
            "seed mean within direction-endpoint; equal mean of two directions; "
            "endpoint cluster is independent unit"
        ),
        "endpoint_rows": rows,
        "contrasts": contrasts,
    }


def endpoint_estimates(
    directions: dict[str, dict[str, list[float]]],
) -> tuple[list[str], np.ndarray, dict[str, Any]]:
    endpoint_sets = [set(panel) for panel in directions.values()]
    if not endpoint_sets or any(value != endpoint_sets[0] for value in endpoint_sets):
        raise RuntimeError("direction endpoint sets differ")
    endpoints = sorted(endpoint_sets[0])
    estimates = []
    audit: dict[str, Any] = {}
    for endpoint in endpoints:
        direction_means = {
            direction: float(np.mean(panel[endpoint]))
            for direction, panel in directions.items()
        }
        estimate = float(np.mean(list(direction_means.values())))
        estimates.append(estimate)
        audit[endpoint] = {
            "direction_means": direction_means,
            "endpoint_cluster_estimate": estimate,
            "seed_values": {
                direction: [float(value) for value in panel[endpoint]]
                for direction, panel in directions.items()
            },
        }
    return endpoints, np.asarray(estimates, dtype=np.float64), audit


def bootstrap_intervals(values: np.ndarray) -> dict[str, Any]:
    n = len(values)
    theta = float(np.mean(values))
    se = float(np.std(values, ddof=1) / np.sqrt(n))
    rng = np.random.default_rng(BOOT_SEED)
    indices = rng.integers(0, n, size=(N_BOOT, n))
    samples = values[indices]
    means = np.mean(samples, axis=1)

    percentile = np.quantile(means, [0.025, 0.975])

    # BCa interval for the endpoint-cluster mean.
    less = (float(np.sum(means < theta)) + 0.5 * float(np.sum(means == theta))) / N_BOOT
    less = float(np.clip(less, 1.0 / (2 * N_BOOT), 1.0 - 1.0 / (2 * N_BOOT)))
    z0 = float(norm.ppf(less))
    jack = np.asarray([np.mean(np.delete(values, index)) for index in range(n)])
    jack_bar = float(np.mean(jack))
    centered = jack_bar - jack
    denominator = 6.0 * float(np.sum(centered**2) ** 1.5)
    acceleration = float(np.sum(centered**3) / denominator) if denominator > 0 else 0.0
    adjusted = []
    for alpha in (0.025, 0.975):
        za = float(norm.ppf(alpha))
        adjusted_alpha = float(
            norm.cdf(z0 + (z0 + za) / (1.0 - acceleration * (z0 + za)))
        )
        adjusted.append(float(np.clip(adjusted_alpha, 0.0, 1.0)))
    bca = np.quantile(means, adjusted)

    # Studentized endpoint bootstrap; discard only degenerate resamples.
    sample_se = np.std(samples, axis=1, ddof=1) / np.sqrt(n)
    valid = sample_se > 0
    t_star = (means[valid] - theta) / sample_se[valid]
    t_quantiles = np.quantile(t_star, [0.025, 0.975])
    studentized = np.asarray(
        [theta - float(t_quantiles[1]) * se, theta - float(t_quantiles[0]) * se]
    )

    critical = float(t.ppf(0.975, df=n - 1))
    t_interval = np.asarray([theta - critical * se, theta + critical * se])
    return {
        "student_t_ci95": t_interval.tolist(),
        "percentile_bootstrap_ci95": percentile.tolist(),
        "bca_bootstrap_ci95": bca.tolist(),
        "studentized_bootstrap_ci95": studentized.tolist(),
        "bca": {"bias_correction": z0, "acceleration": acceleration,
                "adjusted_quantiles": adjusted},
        "bootstrap_reps": N_BOOT,
        "bootstrap_seed": BOOT_SEED,
        "studentized_valid_draws": int(np.sum(valid)),
        "standard_error": se,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nh2kn-root", type=Path, default=DEFAULT_ROOTS["nh2kn"])
    parser.add_argument("--kn2nh-root", type=Path, default=DEFAULT_ROOTS["kn2nh"])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    roots = {"nh2kn": args.nh2kn_root, "kn2nh": args.kn2nh_root}
    directions = {
        direction: load_direction(path, direction)
        for direction, path in roots.items()
    }
    endpoints, estimates, audit = endpoint_estimates(directions)
    factorial = factorial_transparency({
        direction: load_factorial_direction(path, direction)
        for direction, path in roots.items()
    })
    best_index = int(np.argmax(estimates))
    intervals = bootstrap_intervals(estimates)
    payload = {
        "analysis_status": "exploratory_existing_xgb_cells_observed_before_freeze",
        "estimand": "AUROC(a11_stage_columns)-AUROC(a10_stage) conditional on supplied measurement",
        "not_estimand": "standalone correspondence utility",
        "learner": "xgboost_hist_d6_n300_regression_ranked",
        "support_k": int(K),
        "aggregation": "seed mean within direction-endpoint; equal mean of two directions; endpoint cluster is independent unit",
        "n_endpoint_clusters": len(endpoints),
        "n_direction_endpoint_cells": 2 * len(endpoints),
        "n_seed_cells": 20 * len(endpoints),
        "mean": float(np.mean(estimates)),
        "median": float(np.median(estimates)),
        "positive_endpoint_clusters": int(np.sum(estimates > 0)),
        "best_endpoint": endpoints[best_index],
        "drop_best_mean": float(np.mean(np.delete(estimates, best_index))),
        "endpoint_estimates": audit,
        "factorial_four_arm_transparency": factorial,
        "intervals": intervals,
        "provenance": {
            "protocol": str(PROTOCOL),
            "protocol_sha256": sha256_file(PROTOCOL),
            "runner_sha256": sha256_file(Path(__file__)),
            "roots": {key: str(value) for key, value in roots.items()},
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({
        "mean": payload["mean"],
        "student_t_ci95": intervals["student_t_ci95"],
        "a01_minus_a00_raw": factorial["contrasts"]["c_given_measurement_off_raw"],
        "a11_minus_a10_raw": factorial["contrasts"]["c_given_measurement_supplied_raw"],
        "mc_interaction_raw": factorial["contrasts"]["mc_interaction_raw"],
        "a01_minus_a00_folded": factorial["contrasts"]["c_given_measurement_off_folded"],
        "a11_minus_a10_folded": factorial["contrasts"]["c_given_measurement_supplied_folded"],
        "mc_interaction_folded": factorial["contrasts"]["mc_interaction_folded"],
        "bca_ci95": intervals["bca_bootstrap_ci95"],
        "positive_endpoint_clusters": payload["positive_endpoint_clusters"],
        "drop_best_mean": payload["drop_best_mean"],
        "written": str(args.out),
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
