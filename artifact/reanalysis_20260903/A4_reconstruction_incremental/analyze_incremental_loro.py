#!/usr/bin/env python3
"""Paired realization bootstrap for incremental LORO R2 and conditional slopes."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
INPUT = REPO / "experiments/crta_v3_reconstruction_utility_proxy_v1/CELL_RUNG_PROXY_V1.csv"
PARENT = REPO / "experiments/crta_v3_reconstruction_utility_proxy_v1/SUMMARY_V1.json"
REPS = 10_000
SEED = 20260903


def stable_rng(key: str) -> np.random.Generator:
    h = hashlib.sha256(f"incremental_loro|{SEED}|{key}".encode()).hexdigest()
    return np.random.default_rng(int(h[:8], 16))


def fit_line(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return np.linalg.lstsq(np.column_stack([np.ones(len(x)), x]), y, rcond=None)[0]


def loro_predictions(g: pd.DataFrame, field: str) -> np.ndarray:
    pred = np.empty(len(g))
    r = g.realization.to_numpy()
    x = g[field].to_numpy(float); y = g.utility.to_numpy(float)
    for held in sorted(np.unique(r)):
        train = r != held; test = ~train
        beta = fit_line(x[train], y[train])
        pred[test] = beta[0] + beta[1] * x[test]
    return pred


def r2(y: np.ndarray, pred: np.ndarray) -> float:
    return 1.0 - float(np.sum((y-pred)**2)) / float(np.sum((y-y.mean())**2))


def conditional_design(g: pd.DataFrame) -> np.ndarray:
    levels = sorted(g.rho_removed.unique())
    fixed = [(g.rho_removed.to_numpy() == level).astype(float) for level in levels[1:]]
    return np.column_stack([np.ones(len(g)), g.reconstruction_r2.to_numpy(float), *fixed])


def main() -> int:
    data = pd.read_csv(INPUT).sort_values(
        ["family", "backbone", "support", "realization", "k"]
    ).reset_index(drop=True)
    parent = json.loads(PARENT.read_text())["strata"]
    summary_rows = []
    delta_draw_rows = []
    conditional_draw_rows = []
    max_parent_error = 0.0

    for (family, backbone, support), original in data.groupby(
            ["family", "backbone", "support"], sort=True):
        g = original.reset_index(drop=True)
        tag = f"{family}|{backbone}|K={support}"
        y = g.utility.to_numpy(float)
        recon_pred = loro_predictions(g, "reconstruction_r2")
        fraction_pred = loro_predictions(g, "rho_removed")
        recon_r2 = r2(y, recon_pred); fraction_r2 = r2(y, fraction_pred)
        max_parent_error = max(
            max_parent_error,
            abs(recon_r2 - parent[tag]["loro_new_realization_prediction_from_reconstruction"]["r2"]),
            abs(fraction_r2 - parent[tag]["loro_new_realization_prediction_from_removed_fraction"]["r2"]),
        )
        point_delta = recon_r2 - fraction_r2
        conditional_x = conditional_design(g)
        point_conditional = float(np.linalg.lstsq(conditional_x, y, rcond=None)[0][1])
        clusters = sorted(g.realization.unique())
        positions = {c: np.flatnonzero(g.realization.to_numpy() == c) for c in clusters}
        rng = stable_rng(tag)
        deltas = np.empty(REPS); slopes = np.empty(REPS)
        for b in range(REPS):
            chosen = rng.choice(clusters, size=len(clusters), replace=True)
            index = np.concatenate([positions[int(c)] for c in chosen])
            yy = y[index]
            deltas[b] = r2(yy, recon_pred[index]) - r2(yy, fraction_pred[index])
            slopes[b] = np.linalg.lstsq(conditional_x[index], y[index], rcond=None)[0][1]
        lo, hi = np.quantile(deltas, [.025, .975])
        slo, shi = np.quantile(slopes, [.025, .975])
        summary_rows.append({
            "family": family, "backbone": backbone, "K": int(support),
            "n_observations": len(g), "n_realizations": len(clusters),
            "loro_r2_reconstruction": recon_r2,
            "loro_r2_removed_fraction": fraction_r2,
            "delta_r2": point_delta, "delta_ci95_low": float(lo),
            "delta_ci95_high": float(hi),
            "bootstrap_probability_delta_gt_zero": float(np.mean(deltas > 0)),
            "conditional_reconstruction_slope": point_conditional,
            "conditional_slope_ci95_low": float(slo),
            "conditional_slope_ci95_high": float(shi),
        })
        delta_draw_rows.extend({"stratum": tag, "draw": b, "delta_r2": float(v)}
                               for b, v in enumerate(deltas))
        conditional_draw_rows.extend({"stratum": tag, "draw": b, "slope": float(v)}
                                     for b, v in enumerate(slopes))

    if max_parent_error > 1e-12:
        raise AssertionError(f"LORO reproduction mismatch: {max_parent_error}")
    for name, rows in (("reconstruction_incremental_r2.csv", summary_rows),
                       ("bootstrap_deltas.csv", delta_draw_rows),
                       ("conditional_slope_bootstrap.csv", conditional_draw_rows)):
        with (HERE / name).open("w", newline="") as f:
            w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
    payload = {
        "status": "complete", "results": summary_rows,
        "bootstrap": {
            "reps": REPS, "seed": SEED, "unit": "realization cluster",
            "delta_method": (
                "Resample realization blocks and recompute both R2 values from the same "
                "fixed leave-one-realization-out predictions; take paired difference."
            ),
        },
        "conditional_model": (
            "utility ~ reconstruction_r2 + categorical(rho_removed); realization-cluster "
            "percentile bootstrap"
        ),
        "max_parent_loro_r2_error": max_parent_error,
        "scope": "controlled computed-relation-value benchmark only",
        "machine_readable_outputs": ["reconstruction_incremental_r2.csv",
                                     "bootstrap_deltas.csv",
                                     "conditional_slope_bootstrap.csv"],
        "sources": [str(INPUT.relative_to(REPO)), str(PARENT.relative_to(REPO)),
                    "scripts/analyze_crta_v3_reconstruction_utility_proxy_v1.py"],
    }
    (HERE / "summary.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"written": ["reconstruction_incremental_r2.csv", "bootstrap_deltas.csv",
                                  "conditional_slope_bootstrap.csv", "summary.json"],
                      "results": summary_rows}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
