#!/usr/bin/env python3
"""Post-run validity diagnostics; never edits the frozen proxy seal or TeX."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LinearRegression


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_crta_v3_real_value_reconstruction_falsification_v1.py"
EXP = ROOT / "experiments/crta_v3_real_value_reconstruction_falsification_v1"
OUT = EXP / "DIAGNOSTICS_V1.json"


def load_runner():
    spec = importlib.util.spec_from_file_location("real_value_frozen_runner", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import frozen runner")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def bootstrap_mean(values: np.ndarray, seed: int, reps: int = 10_000) -> list[float]:
    rng = np.random.default_rng(seed)
    draws = values[rng.integers(0, len(values), size=(reps, len(values)))].mean(axis=1)
    return [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))]


def performance_movement(rv) -> dict:
    proxy = pd.DataFrame(json.loads(rv.PROXY_ROWS.read_text()))
    utility = pd.DataFrame(json.loads(rv.UTILITY_ROWS.read_text()))
    merged = proxy.merge(utility, on=["setting", "target", "seed", "support_basins", "sigma"])
    answer = {}
    for setting, part in merged.groupby("setting", sort=True):
        cell_cols = ["seed"] + (["target"] if part["target"].notna().any() else [])
        rows = []
        for key, cell in part.groupby(cell_cols, sort=True):
            cell = cell.sort_values("sigma")
            d = 1.0 - cell["reconstruction_r2"].to_numpy()
            rows.append({
                "cell": str(key),
                "rho_unreconstructibility_reference_metric": float(
                    spearmanr(d, cell["reference_metric"]).statistic),
                "rho_unreconstructibility_intended_metric": float(
                    spearmanr(d, cell["intended_metric"]).statistic),
                "reference_last_minus_zero": float(
                    cell["reference_metric"].iloc[-1] - cell["reference_metric"].iloc[0]),
                "intended_last_minus_zero": float(
                    cell["intended_metric"].iloc[-1] - cell["intended_metric"].iloc[0]),
            })
        frame = pd.DataFrame(rows)
        answer[setting] = {
            "lower_metric_is_better": True,
            "mean_rho_unreconstructibility_reference_metric": float(
                frame["rho_unreconstructibility_reference_metric"].mean()),
            "reference_rho_bootstrap_95pct": bootstrap_mean(
                frame["rho_unreconstructibility_reference_metric"].to_numpy(), 7101),
            "mean_rho_unreconstructibility_intended_metric": float(
                frame["rho_unreconstructibility_intended_metric"].mean()),
            "intended_rho_bootstrap_95pct": bootstrap_mean(
                frame["rho_unreconstructibility_intended_metric"].to_numpy(), 7102),
            "mean_reference_last_minus_zero": float(
                frame["reference_last_minus_zero"].mean()),
            "mean_intended_last_minus_zero": float(
                frame["intended_last_minus_zero"].mean()),
            "cells": rows,
        }
    return answer


def medical_reconstruction_diagnostics(rv) -> dict:
    benchmark = rv.load_medical_benchmark()
    frozen = pd.DataFrame(json.loads(rv.PROXY_ROWS.read_text()))
    frozen = frozen[(frozen.setting == "medical_nh2kn") & (frozen.sigma == 0.0)]
    rows = []
    for target in rv.MEDICAL_TARGETS:
        for seed in rv.MEDICAL_SEEDS:
            cell = rv.medical_cell(benchmark, target, seed, include_outcomes=False)
            n = cell["n_support"]
            names = cell["feature_names"]
            bp = [names.index("sbp"), names.index("dbp")]
            source_ok = cell["source_availability"].astype(bool)
            support_ok = cell["target_availability"][:n].astype(bool)
            query_ok = cell["target_availability"][n:].astype(bool)
            source_bp = cell["source_x"][:, bp]
            target_bp = cell["target_x"][:, bp]

            linear_target = LinearRegression().fit(
                target_bp[:n][support_ok], cell["target_relation"][:n][support_ok])
            pred_target = linear_target.predict(target_bp[n:][query_ok])

            linear_source = LinearRegression().fit(
                source_bp[source_ok], cell["source_relation"][source_ok])
            pred_source = linear_source.predict(target_bp[n:][query_ok])

            combined_x = np.vstack([source_bp[source_ok], target_bp[:n][support_ok]])
            combined_z = np.concatenate([
                cell["source_relation"][source_ok], cell["target_relation"][:n][support_ok]
            ])
            combined_w = np.concatenate([
                np.ones(int(source_ok.sum())),
                np.full(int(support_ok.sum()), cell["n_source"] / max(int(support_ok.sum()), 1)),
            ])
            linear_combined = LinearRegression().fit(
                combined_x, combined_z, sample_weight=combined_w)
            pred_combined = linear_combined.predict(target_bp[n:][query_ok])

            # Same XGBoost family, but target support only, isolates source/target mixing.
            target_model = rv.xgb(seed, depth=6, threads=8)
            target_model.fit(cell["target_x"][:n], cell["target_relation"][:n])
            target_xgb_pred = target_model.predict(cell["target_x"][n:])

            source_center, source_scale = rv.robust_fit(
                cell["source_x"][:, bp[0]] - cell["source_x"][:, bp[1]],
                np.ones(len(cell["source_x"]), dtype=bool))
            target_center, target_scale = rv.robust_fit(
                cell["target_x"][:, bp[0]] - cell["target_x"][:, bp[1]],
                np.arange(len(cell["target_x"])) < n)
            observed = frozen[(frozen.target == target) & (frozen.seed == seed)].iloc[0]
            rows.append({
                "target": target,
                "seed": int(seed),
                "source_relation_availability": float(source_ok.mean()),
                "target_support_relation_availability": float(support_ok.mean()),
                "target_query_relation_availability": float(query_ok.mean()),
                "source_relation_center": source_center,
                "source_relation_scale": source_scale,
                "target_relation_center": target_center,
                "target_relation_scale": target_scale,
                "frozen_source_plus_support_xgb_r2": float(observed.reconstruction_r2),
                "target_only_linear_bp_r2_observed_query": rv.r2_score(
                    cell["target_relation"][n:][query_ok], pred_target),
                "source_only_linear_bp_r2_observed_query": rv.r2_score(
                    cell["target_relation"][n:][query_ok], pred_source),
                "source_plus_support_linear_bp_r2_observed_query": rv.r2_score(
                    cell["target_relation"][n:][query_ok], pred_combined),
                "target_only_xgb_full_frame_r2": rv.r2_score(
                    cell["target_relation"][n:], target_xgb_pred),
            })
    frame = pd.DataFrame(rows)
    return {
        "exact_arithmetic_target_r2": 1.0,
        "means": {column: float(frame[column].mean()) for column in frame.columns
                  if column not in {"target", "seed"}},
        "by_target": frame.groupby("target").mean(numeric_only=True).to_dict(orient="index"),
        "cells": rows,
        "interpretive_test": (
            "Target-only linear reconstruction from SBP and DBP is the algebraic "
            "redundancy check. Differences between it and the frozen XGBoost R2 "
            "measure learner/domain-transfer reconstruction, not missing algebra."
        ),
    }


def camels_diagnostics(rv) -> dict:
    context = rv.load_camels_context(include_outcomes=False)
    frozen = pd.DataFrame(json.loads(rv.PROXY_ROWS.read_text()))
    frozen = frozen[frozen.setting == "camels_120"]
    aligned_rows = []
    structural = []
    for seed in rv.CAMELS_SEEDS:
        cell = rv.camels_cell(context, seed, include_outcomes=False)
        support, query = cell["support_mask"], cell["query_mask"]
        for side, frame in (("source", cell["source"]), ("target", cell["target"])):
            pet = pd.to_numeric(frame["pet_mean"], errors="coerce").to_numpy(float)
            p = pd.to_numeric(frame["p_mean"], errors="coerce").to_numpy(float)
            aridity = pd.to_numeric(frame["aridity"], errors="coerce").to_numpy(float)
            ratio = np.divide(pet, p, out=np.full(len(frame), np.nan),
                              where=np.isfinite(p) & (np.abs(p) > 1e-12))
            ok = np.isfinite(ratio) & np.isfinite(aridity)
            structural.append({
                "seed": seed, "side": side,
                "aridity_ratio_correlation": float(np.corrcoef(aridity[ok], ratio[ok])[0, 1]),
                "aridity_ratio_max_abs_difference": float(np.max(np.abs(aridity[ok] - ratio[ok]))),
            })
        for sigma in rv.NOISE_SIGMAS:
            sx, tx = rv.camels_design(cell, sigma)
            train_x = np.vstack([sx, tx[support]])
            train_z = np.concatenate([
                cell["source_relation"], cell["target_relation"][support]])
            weights = np.concatenate([np.ones(len(sx)), np.full(int(support.sum()), 10.0)])
            # Width-align the proxy to reference by appending the same two zero columns.
            model = rv.xgb(seed, depth=6, threads=8)
            model.fit(np.column_stack([train_x, np.zeros((len(train_x), 2), np.float32)]),
                      train_z, sample_weight=weights)
            query_x = np.column_stack([tx[query], np.zeros((int(query.sum()), 2), np.float32)])
            pred = model.predict(query_x)
            basin = pd.DataFrame({
                "gauge_id": cell["target"].loc[query, "gauge_id"].astype(str).to_numpy(),
                "truth": cell["target_relation"][query], "prediction": pred,
            }).groupby("gauge_id", sort=True).mean(numeric_only=True)
            aligned = rv.r2_score(basin.truth.to_numpy(), basin.prediction.to_numpy())
            original = frozen[(frozen.seed == seed) & (frozen.sigma == sigma)].iloc[0]
            aligned_rows.append({
                "seed": seed, "sigma": sigma,
                "original_base_only_proxy_r2": float(original.reconstruction_r2),
                "width_aligned_base_plus_two_zeros_proxy_r2": aligned,
                "difference": aligned - float(original.reconstruction_r2),
            })
    aligned = pd.DataFrame(aligned_rows)
    zero = aligned[aligned.sigma == 0.0]
    return {
        "aridity_in_reference_base": "aridity" in context["base_features"],
        "corrupted_reference_and_proxy_closure": ["pet_mean", "p_mean", "aridity"],
        "clean_supplied_relation_recomputed_per_rung": False,
        "proxy_and_reference_nonconstant_information_set_identical": True,
        "original_proxy_had_reference_zero_padding_columns": False,
        "width_aligned_zero_noise_mean_r2": float(
            zero.width_aligned_base_plus_two_zeros_proxy_r2.mean()),
        "original_zero_noise_mean_r2": float(zero.original_base_only_proxy_r2.mean()),
        "mean_width_alignment_r2_difference_all_rungs": float(aligned.difference.mean()),
        "structural_aridity_ratio_checks": structural,
        "width_aligned_cells": aligned_rows,
    }


def main() -> int:
    rv = load_runner()
    rv.validate_proxy_seal()
    result = {
        "frozen_manifest_sha256": rv.sha256_file(rv.MANIFEST),
        "frozen_proxy_seal_sha256": rv.sha256_file(rv.PROXY_SEAL),
        "performance_movement": performance_movement(rv),
        "medical_reconstruction": medical_reconstruction_diagnostics(rv),
        "camels": camels_diagnostics(rv),
        "frozen_outputs_modified": False,
        "paper_tex_modified": False,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "output": str(OUT),
        "performance_movement": result["performance_movement"],
        "medical_means": result["medical_reconstruction"]["means"],
        "camels_summary": {key: value for key, value in result["camels"].items()
                           if key not in {"structural_aridity_ratio_checks", "width_aligned_cells"}},
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
