#!/usr/bin/env python3
"""Two-phase real-data reconstruction/utility falsification experiment.

The ``proxy`` phase cannot access outcome arrays in this module.  The ``utility``
phase is refused until the outcome-free predictions have been written and sealed.
See experiments/crta_v3_real_value_reconstruction_falsification_v1/PROTOCOL_V1.md.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from xgboost import XGBRegressor


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/crta_v3_real_value_reconstruction_falsification_v1"
PROTOCOL = EXP / "PROTOCOL_V1.md"
MANIFEST = EXP / "FROZEN_MANIFEST_V1.json"
PROXY_ROWS = EXP / "PROXY_ROWS_V1.json"
PREDICTIONS = EXP / "PREDICTIONS_BEFORE_OUTCOMES_V1.json"
PROXY_SEAL = EXP / "PROXY_SEAL_V1.json"
UTILITY_ROWS = EXP / "UTILITY_ROWS_V1.json"
SUMMARY = EXP / "SUMMARY_V1.json"

MEDICAL_BUILDER = Path(
    "data/benchmark/"
    "scripts/build_benchmark_table.py"
)
MEDICAL_NH = Path(
    "data/nhanes_knhanes/datasets/nhanes/processed/L3/"
    "L3_1714_ge9.parquet"
)
MEDICAL_KN = Path(
    "data/nhanes_knhanes/datasets/knhanes/processed/L3/"
    "L3_9815_pr90_with_mpls.parquet"
)
MEDICAL_MANIFEST = Path(
    "data/benchmark_project/tasks/"
    "cross_cohort_noncorepred/current/manifests/manifest.yaml"
)
CAMELS_SCREEN = ROOT / "scripts/run_crta_v3_camels_native_screen_v1.py"
CAMELS_NATIVE = ROOT / "experiments/crta_v3_camels_native_screen_v1/data"
CAMELS_EXT = ROOT / "experiments/crta_v3_camels_query_extension_v1/data"
CAMELS_PAYLOAD = (
    ROOT / "iclr_latex_v3/method_contract/v1/payloads/"
    "camels_us_to_gb_native_v1/proposer_input.json"
)

NOISE_SIGMAS = (0.0, 0.125, 0.25, 0.5, 1.0, 2.0, 4.0)
MEDICAL_TARGETS = ("glucose", "waist_cm", "triglycerides", "total_cholesterol")
MEDICAL_SEEDS = tuple(range(50, 55))
CAMELS_SEEDS = tuple(range(20, 25))
MEDICAL_K = 256
CAMELS_SUPPORT = 5
BOOTSTRAP_SEED = 20260903
BOOTSTRAP_REPS = 10_000
RESOLUTION = {"medical_nh2kn": 0.0095, "camels_120": 0.0015}
R2_GATE = 0.95

BASE_SLOTS = (
    "age", "creatinine", "rbc", "wbc", "hemoglobin", "hematocrit",
    "sex", "education_level", "diabetes_history", "hypertension_history",
    "current_smoking_status",
)
MEMBER_SLOTS = (
    "height_cm", "weight_kg", "waist_cm", "sbp", "dbp", "glucose",
    "hba1c", "total_cholesterol", "triglycerides",
)
ALL_SLOTS = BASE_SLOTS + MEMBER_SLOTS
MEDICAL_BENCHMARK = "std_cross_nh2kn_shared_anchorreset_fewshot_v1"
MEDICAL_FEATURE_SET = "real_value_proxy_pam_all_v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def rng_for(key: str) -> np.random.Generator:
    seed = int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:16], 16)
    return np.random.default_rng(seed)


def robust_fit(raw: np.ndarray, mask: np.ndarray) -> tuple[float, float]:
    fit = np.asarray(raw, dtype=np.float64)[np.asarray(mask, dtype=bool)]
    fit = fit[np.isfinite(fit)]
    if not len(fit):
        return 0.0, 1.0
    center = float(np.median(fit))
    q25, q75 = np.quantile(fit, [0.25, 0.75])
    scale = float(q75 - q25)
    if not np.isfinite(scale) or scale <= 1e-8:
        scale = float(np.std(fit))
    if not np.isfinite(scale) or scale <= 1e-8:
        scale = 1.0
    return center, scale


def robust_value(raw: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    raw = np.asarray(raw, dtype=np.float64)
    center, scale = robust_fit(raw, mask)
    observed = np.isfinite(raw)
    value = np.zeros(len(raw), dtype=np.float32)
    value[observed] = np.clip((raw[observed] - center) / scale, -10.0, 10.0)
    return value, observed.astype(np.float32)


def xgb(seed: int, depth: int, threads: int) -> XGBRegressor:
    return XGBRegressor(
        objective="reg:squarederror",
        n_estimators=300,
        max_depth=depth,
        learning_rate=0.05,
        min_child_weight=1.0 if depth == 6 else 5.0,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_lambda=1.0,
        random_state=seed,
        n_jobs=threads,
        tree_method="hist",
    )


def r2_score(y: np.ndarray, pred: np.ndarray) -> float:
    y = np.asarray(y, dtype=np.float64)
    pred = np.asarray(pred, dtype=np.float64)
    finite = np.isfinite(y) & np.isfinite(pred)
    y, pred = y[finite], pred[finite]
    denom = float(np.square(y - y.mean()).sum())
    return 1.0 - float(np.square(y - pred).sum()) / denom if denom > 0 else 0.0


def dependency_paths() -> dict[str, Path]:
    return {
        "runner": Path(__file__).resolve(),
        "protocol": PROTOCOL,
        "medical_builder": MEDICAL_BUILDER,
        "medical_nhanes": MEDICAL_NH,
        "medical_knhanes": MEDICAL_KN,
        "medical_dataset_manifest": MEDICAL_MANIFEST,
        "camels_screen": CAMELS_SCREEN,
        "camels_native_source": CAMELS_NATIVE / "source.pkl",
        "camels_native_target": CAMELS_NATIVE / "target.pkl",
        "camels_native_split": CAMELS_NATIVE / "split_manifest.json",
        "camels_extension_target": CAMELS_EXT / "target.pkl",
        "camels_extension_split": CAMELS_EXT / "split_manifest.json",
        "camels_payload": CAMELS_PAYLOAD,
    }


def design_dict() -> dict[str, Any]:
    return {
        "experiment": "crta_v3_real_value_reconstruction_falsification_v1",
        "frozen_before_outcome_utility": True,
        "noise_sigmas_iqr": list(NOISE_SIGMAS),
        "medical": {
            "direction": "nhanes_to_knhanes",
            "targets": list(MEDICAL_TARGETS),
            "excluded_leaky_targets": ["sbp", "dbp"],
            "seeds": list(MEDICAL_SEEDS),
            "support_rows": MEDICAL_K,
            "relation": "slot__sbp - slot__dbp",
            "resolution_band": RESOLUTION["medical_nh2kn"],
        },
        "camels": {
            "direction": "camels_us_to_camels_gb",
            "seeds": list(CAMELS_SEEDS),
            "support_basins": CAMELS_SUPPORT,
            "query_basins": 120,
            "relation": "pet_mean / p_mean",
            "noise_closure": ["pet_mean", "p_mean", "aridity"],
            "resolution_band": RESOLUTION["camels_120"],
        },
        "zero_noise_r2_gate": R2_GATE,
        "bootstrap": {"seed": BOOTSTRAP_SEED, "repetitions": BOOTSTRAP_REPS},
        "track_b_numeric_proxy": False,
    }


def freeze() -> None:
    if MANIFEST.exists():
        raise RuntimeError(f"manifest already exists: {MANIFEST}")
    paths = dependency_paths()
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing frozen inputs: " + ", ".join(missing))
    manifest = {
        "created_unix": time.time(),
        "design": design_dict(),
        "files": {
            name: {"path": str(path), "sha256": sha256_file(path)}
            for name, path in paths.items()
        },
    }
    write_json(MANIFEST, manifest)
    print(json.dumps({"status": "frozen", "manifest": str(MANIFEST),
                      "manifest_sha256": sha256_file(MANIFEST)}), flush=True)


def validate_manifest() -> dict[str, Any]:
    manifest = read_json(MANIFEST)
    if manifest["design"] != design_dict():
        raise RuntimeError("runtime design differs from frozen design")
    for name, record in manifest["files"].items():
        path = Path(record["path"])
        observed = sha256_file(path)
        if observed != record["sha256"]:
            raise RuntimeError(f"frozen hash mismatch for {name}: {observed}")
    return manifest


def load_medical_benchmark():
    benchmark = load_module("real_value_proxy_medical_benchmark", MEDICAL_BUILDER)
    original_load_yaml = benchmark.load_yaml
    manifest_path = Path(benchmark.DEFAULT_DATASET_MANIFEST).resolve()

    def load_yaml_patched(path):
        value = original_load_yaml(path)
        if Path(path).resolve() == manifest_path:
            value["datasets"]["nhanes"]["parquet"] = str(MEDICAL_NH)
            value["datasets"]["knhanes"]["parquet"] = str(MEDICAL_KN)
        if isinstance(value, dict) and "feature_sets" in value:
            value["feature_sets"][MEDICAL_FEATURE_SET] = {
                "description": "frozen real-value proxy feature set",
                "feature_mode": "explicit_slots",
                "slots": list(ALL_SLOTS),
            }
        return value

    benchmark.load_yaml = load_yaml_patched
    return benchmark


def medical_cell(benchmark, target: str, seed: int, include_outcomes: bool) -> dict[str, Any]:
    # The benchmark builder fixes task-eligible rows.  In proxy mode this module
    # never indexes the returned y arrays; only X and the frozen origin labels are used.
    bundle = benchmark.build_single_target_table(
        benchmark_id=MEDICAL_BENCHMARK,
        target_name=target,
        fewshot_frac=0.10,
        seed=seed,
        target_set_override="objective_anchor_targets_v1_safe",
        feature_set_override=MEDICAL_FEATURE_SET,
    )
    train = bundle["X_train"].reset_index(drop=True)
    query = bundle["X_test"].reset_index(drop=True)
    origin = np.asarray(bundle["train_origin"], dtype=object)
    n_source = int(np.sum(origin == "source"))
    n_pool = len(train) - n_source
    pick = np.sort(np.random.default_rng(seed * 131 + MEDICAL_K).choice(
        n_pool, size=min(MEDICAL_K, n_pool), replace=False))
    support_rows = n_source + pick
    feature_names = [slot for slot in ALL_SLOTS if slot != target]
    columns = [f"slot__{slot}" for slot in feature_names]
    source_frame = train.iloc[:n_source][columns].apply(pd.to_numeric, errors="coerce")
    target_frame = pd.concat(
        [train.iloc[support_rows][columns], query[columns]], ignore_index=True
    ).apply(pd.to_numeric, errors="coerce")
    source_x = source_frame.to_numpy(np.float64)
    target_x = target_frame.to_numpy(np.float64)
    n_support = len(pick)
    source_mask = np.ones(len(source_x), dtype=bool)
    target_mask = np.arange(len(target_x)) < n_support
    sbp_i, dbp_i = feature_names.index("sbp"), feature_names.index("dbp")
    source_rel, source_avail = robust_value(source_x[:, sbp_i] - source_x[:, dbp_i], source_mask)
    target_rel, target_avail = robust_value(target_x[:, sbp_i] - target_x[:, dbp_i], target_mask)
    result: dict[str, Any] = {
        "target": target,
        "seed": seed,
        "feature_names": feature_names,
        "source_x": source_x,
        "target_x": target_x,
        "source_relation": source_rel,
        "source_availability": source_avail,
        "target_relation": target_rel,
        "target_availability": target_avail,
        "n_source": n_source,
        "n_support": n_support,
        "n_query": len(query),
        "weights": np.concatenate([
            np.ones(n_source), np.full(n_support, n_source / max(n_support, 1))
        ]),
    }
    if include_outcomes:
        y_train = pd.to_numeric(bundle["y_train"], errors="coerce").to_numpy(np.float64)
        result["source_y"] = y_train[:n_source]
        result["support_y"] = y_train[support_rows]
        result["query_y"] = pd.to_numeric(
            bundle["y_test"], errors="coerce").to_numpy(np.float64)
    return result


def add_medical_noise(cell: dict[str, Any], sigma: float) -> tuple[np.ndarray, np.ndarray]:
    source = cell["source_x"].copy()
    target = cell["target_x"].copy()
    n_support = cell["n_support"]
    for name in ("sbp", "dbp"):
        index = cell["feature_names"].index(name)
        for side, values, fit_mask in (
            ("source", source, np.ones(len(source), dtype=bool)),
            ("target", target, np.arange(len(target)) < n_support),
        ):
            _, scale = robust_fit(values[:, index], fit_mask)
            eps = rng_for(
                f"real-value-noise-v1|medical|{cell['target']}|{cell['seed']}|{side}|{name}"
            ).standard_normal(len(values))
            observed = np.isfinite(values[:, index])
            values[observed, index] += sigma * scale * eps[observed]
    return source.astype(np.float32), target.astype(np.float32)


def medical_proxy_rows(threads: int) -> list[dict[str, Any]]:
    benchmark = load_medical_benchmark()
    rows: list[dict[str, Any]] = []
    for target in MEDICAL_TARGETS:
        for seed in MEDICAL_SEEDS:
            cell = medical_cell(benchmark, target, seed, include_outcomes=False)
            n_support = cell["n_support"]
            for sigma in NOISE_SIGMAS:
                sx, tx = add_medical_noise(cell, sigma)
                train_x = np.vstack([sx, tx[:n_support]])
                train_z = np.concatenate([
                    cell["source_relation"], cell["target_relation"][:n_support]
                ])
                model = xgb(seed, depth=6, threads=threads)
                model.fit(train_x, train_z, sample_weight=cell["weights"])
                pred = model.predict(tx[n_support:]).astype(np.float64)
                score = r2_score(cell["target_relation"][n_support:], pred)
                row = {"setting": "medical_nh2kn", "target": target, "seed": seed,
                       "sigma": sigma, "reconstruction_r2": score,
                       "n_query": cell["n_query"]}
                rows.append(row)
                print(json.dumps({"phase": "proxy", **row}), flush=True)
    return rows


def medical_utility_rows(threads: int) -> list[dict[str, Any]]:
    benchmark = load_medical_benchmark()
    rows: list[dict[str, Any]] = []
    for target in MEDICAL_TARGETS:
        for seed in MEDICAL_SEEDS:
            cell = medical_cell(benchmark, target, seed, include_outcomes=True)
            n_support = cell["n_support"]
            train_y = np.concatenate([cell["source_y"], cell["support_y"]])
            query_y = cell["query_y"]
            query_sd = float(np.std(query_y, ddof=0))
            for sigma in NOISE_SIGMAS:
                sx, tx = add_medical_noise(cell, sigma)
                base_train = np.vstack([sx, tx[:n_support]])
                base_query = tx[n_support:]
                zeros_train = np.zeros((len(base_train), 2), dtype=np.float32)
                zeros_query = np.zeros((len(base_query), 2), dtype=np.float32)
                rel_train = np.column_stack([
                    np.concatenate([cell["source_relation"], cell["target_relation"][:n_support]]),
                    np.concatenate([cell["source_availability"], cell["target_availability"][:n_support]]),
                ]).astype(np.float32)
                rel_query = np.column_stack([
                    cell["target_relation"][n_support:], cell["target_availability"][n_support:]
                ]).astype(np.float32)
                ref = xgb(seed, depth=6, threads=threads)
                intended = xgb(seed, depth=6, threads=threads)
                ref.fit(np.column_stack([base_train, zeros_train]), train_y,
                        sample_weight=cell["weights"])
                intended.fit(np.column_stack([base_train, rel_train]), train_y,
                             sample_weight=cell["weights"])
                ref_pred = ref.predict(np.column_stack([base_query, zeros_query]))
                int_pred = intended.predict(np.column_stack([base_query, rel_query]))
                ref_metric = float(np.sqrt(np.mean(np.square(query_y - ref_pred))) / query_sd)
                int_metric = float(np.sqrt(np.mean(np.square(query_y - int_pred))) / query_sd)
                row = {"setting": "medical_nh2kn", "target": target, "seed": seed,
                       "sigma": sigma, "reference_metric": ref_metric,
                       "intended_metric": int_metric, "utility": ref_metric - int_metric,
                       "metric": "query_sd_normalized_rmse"}
                rows.append(row)
                print(json.dumps({"phase": "utility", **row}), flush=True)
    return rows


def load_camels_context(include_outcomes: bool) -> dict[str, Any]:
    screen = load_module("real_value_proxy_camels_screen", CAMELS_SCREEN)
    source = pd.read_pickle(CAMELS_NATIVE / "source.pkl").reset_index(drop=True)
    target_frozen = pd.read_pickle(CAMELS_NATIVE / "target.pkl").reset_index(drop=True)
    target_ext = pd.read_pickle(CAMELS_EXT / "target.pkl").reset_index(drop=True)
    split = read_json(CAMELS_NATIVE / "split_manifest.json")
    ext_split = read_json(CAMELS_EXT / "split_manifest.json")
    if split["split_salt"] != ext_split["split_salt"]:
        raise RuntimeError("CAMELS extension split salt mismatch")
    payload = read_json(CAMELS_PAYLOAD)
    source_ids = screen.eligible_ids(payload, "source")
    target_ids = screen.eligible_ids(payload, "target")
    derived = sorted({c for frame in (source, target_frozen) for c in frame.columns
                      if "__trailmean_" in c})
    base_features = sorted(set(source_ids) | set(target_ids) | set(derived))
    query_ids = [*split["target_query_basin_ids"], *ext_split["target_query_basin_ids"]]
    if len(query_ids) != 120 or len(set(query_ids)) != 120:
        raise RuntimeError("expected exactly 120 unique CAMELS query basins")
    result = {"screen": screen, "source": source,
              "target_all": pd.concat([target_frozen, target_ext], ignore_index=True),
              "split": split, "query_ids": query_ids, "base_features": base_features}
    if not include_outcomes:
        # Outcome columns remain physically present in frozen pickle files, but no
        # value from them is indexed, hashed, summarized, or returned by proxy code.
        pass
    return result


def camels_base(frame: pd.DataFrame, fit_mask: np.ndarray, features: list[str],
                sigma: float, key: str) -> np.ndarray:
    output = np.zeros((len(frame), len(features) * 2 + 4), dtype=np.float32)
    gauges = frame["gauge_id"].astype(str).to_numpy()
    unique_gauges = sorted(set(gauges))
    closure = {"pet_mean", "p_mean", "aridity"}
    for index, name in enumerate(features):
        raw = (pd.to_numeric(frame[name], errors="coerce").to_numpy(np.float64)
               if name in frame else np.full(len(frame), np.nan))
        if name in closure:
            _, noise_scale = robust_fit(raw, fit_mask)
            draws = rng_for(f"real-value-noise-v1|camels|{key}|{name}").standard_normal(
                len(unique_gauges))
            noise = dict(zip(unique_gauges, draws))
            eps = np.asarray([noise[g] for g in gauges], dtype=np.float64)
            observed = np.isfinite(raw)
            raw = raw.copy()
            raw[observed] += sigma * noise_scale * eps[observed]
        value, availability = robust_value(raw, fit_mask)
        output[:, index * 2] = value
        output[:, index * 2 + 1] = availability
    date = pd.to_datetime(frame["date"])
    radians = 2 * np.pi * (date.dt.dayofyear.to_numpy(np.float64) - 1) / 365.25
    offset = len(features) * 2
    output[:, offset:offset + 4] = np.column_stack([
        np.sin(radians), np.cos(radians), np.sin(2 * radians), np.cos(2 * radians)
    ]).astype(np.float32)
    return output


def camels_relation(frame: pd.DataFrame, fit_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    pet = pd.to_numeric(frame["pet_mean"], errors="coerce").to_numpy(np.float64)
    precip = pd.to_numeric(frame["p_mean"], errors="coerce").to_numpy(np.float64)
    raw = np.divide(pet, precip, out=np.full(len(frame), np.nan),
                    where=np.isfinite(precip) & (np.abs(precip) > 1e-12))
    return robust_value(raw, fit_mask)


def camels_cell(context: dict[str, Any], seed: int, include_outcomes: bool) -> dict[str, Any]:
    screen, split = context["screen"], context["split"]
    support_ids = screen.support_order(split["target_support_pool_basin_ids"], seed)[
        :CAMELS_SUPPORT]
    target = context["target_all"]
    target = target[target["gauge_id"].astype(str).isin(
        [*map(str, support_ids), *map(str, context["query_ids"])])].reset_index(drop=True)
    support_mask = target["gauge_id"].astype(str).isin(map(str, support_ids)).to_numpy()
    query_mask = target["gauge_id"].astype(str).isin(map(str, context["query_ids"])).to_numpy()
    source = context["source"]
    source_mask = np.ones(len(source), dtype=bool)
    source_rel, source_avail = camels_relation(source, source_mask)
    target_rel, target_avail = camels_relation(target, support_mask)
    result = {"seed": seed, "source": source, "target": target,
              "support_mask": support_mask, "query_mask": query_mask,
              "source_relation": source_rel, "source_availability": source_avail,
              "target_relation": target_rel, "target_availability": target_avail,
              "features": context["base_features"], "support_ids": support_ids}
    if include_outcomes:
        result["source_y"] = np.log1p(pd.to_numeric(
            source["discharge_mm_day"], errors="coerce").to_numpy(np.float64))
        result["target_y"] = np.log1p(pd.to_numeric(
            target["discharge_mm_day"], errors="coerce").to_numpy(np.float64))
    return result


def camels_design(cell: dict[str, Any], sigma: float) -> tuple[np.ndarray, np.ndarray]:
    source_base = camels_base(
        cell["source"], np.ones(len(cell["source"]), dtype=bool), cell["features"],
        sigma, f"seed={cell['seed']}|source")
    target_base = camels_base(
        cell["target"], cell["support_mask"], cell["features"], sigma,
        f"seed={cell['seed']}|target")
    return source_base, target_base


def camels_proxy_rows(threads: int) -> list[dict[str, Any]]:
    context = load_camels_context(include_outcomes=False)
    rows: list[dict[str, Any]] = []
    for seed in CAMELS_SEEDS:
        cell = camels_cell(context, seed, include_outcomes=False)
        support, query = cell["support_mask"], cell["query_mask"]
        for sigma in NOISE_SIGMAS:
            sx, tx = camels_design(cell, sigma)
            train_x = np.vstack([sx, tx[support]])
            train_z = np.concatenate([cell["source_relation"], cell["target_relation"][support]])
            weights = np.concatenate([
                np.ones(len(sx)), np.full(int(support.sum()), 10.0)
            ])
            model = xgb(seed, depth=6, threads=threads)
            model.fit(train_x, train_z, sample_weight=weights)
            pred = model.predict(tx[query]).astype(np.float64)
            basin_frame = pd.DataFrame({
                "gauge_id": cell["target"].loc[query, "gauge_id"].astype(str).to_numpy(),
                "truth": cell["target_relation"][query], "prediction": pred,
            }).groupby("gauge_id", sort=True).mean(numeric_only=True)
            score = r2_score(basin_frame["truth"].to_numpy(),
                             basin_frame["prediction"].to_numpy())
            row = {"setting": "camels_120", "seed": seed,
                   "support_basins": CAMELS_SUPPORT, "sigma": sigma,
                   "reconstruction_r2": score, "n_query_basins": len(basin_frame)}
            rows.append(row)
            print(json.dumps({"phase": "proxy", **row}), flush=True)
    return rows


def camels_utility_rows(threads: int) -> list[dict[str, Any]]:
    context = load_camels_context(include_outcomes=True)
    rows: list[dict[str, Any]] = []
    for seed in CAMELS_SEEDS:
        cell = camels_cell(context, seed, include_outcomes=True)
        support, query = cell["support_mask"], cell["query_mask"]
        train_y = np.concatenate([cell["source_y"], cell["target_y"][support]])
        weights = np.concatenate([
            np.ones(len(cell["source_y"])), np.full(int(support.sum()), 10.0)
        ])
        for sigma in NOISE_SIGMAS:
            sx, tx = camels_design(cell, sigma)
            base_train = np.vstack([sx, tx[support]])
            base_query = tx[query]
            rel_train = np.column_stack([
                np.concatenate([cell["source_relation"], cell["target_relation"][support]]),
                np.concatenate([cell["source_availability"], cell["target_availability"][support]]),
            ]).astype(np.float32)
            rel_query = np.column_stack([
                cell["target_relation"][query], cell["target_availability"][query]
            ]).astype(np.float32)
            zeros_train = np.zeros_like(rel_train)
            zeros_query = np.zeros_like(rel_query)
            ref = xgb(seed, depth=6, threads=threads)
            intended = xgb(seed, depth=6, threads=threads)
            ref.fit(np.column_stack([base_train, zeros_train]), train_y, sample_weight=weights)
            intended.fit(np.column_stack([base_train, rel_train]), train_y,
                         sample_weight=weights)
            ref_log = np.maximum(ref.predict(np.column_stack([base_query, zeros_query])), 0.0)
            int_log = np.maximum(intended.predict(np.column_stack([base_query, rel_query])), 0.0)
            query_y = cell["target_y"][query]
            ref_metric = float(np.sqrt(np.mean(np.square(query_y - ref_log))))
            int_metric = float(np.sqrt(np.mean(np.square(query_y - int_log))))
            row = {"setting": "camels_120", "seed": seed,
                   "support_basins": CAMELS_SUPPORT, "sigma": sigma,
                   "reference_metric": ref_metric, "intended_metric": int_metric,
                   "utility": ref_metric - int_metric, "metric": "log1p_rmse"}
            rows.append(row)
            print(json.dumps({"phase": "utility", **row}), flush=True)
    return rows


def seal_proxy(rows: list[dict[str, Any]]) -> None:
    predictions: dict[str, Any] = {
        "manifest_sha256": sha256_file(MANIFEST),
        "outcomes_accessed_by_proxy_module": False,
        "controlled_slope_transferred": False,
        "settings": {},
    }
    frame = pd.DataFrame(rows)
    for setting, part in frame.groupby("setting", sort=True):
        rung = part.groupby("sigma", sort=True)["reconstruction_r2"].mean()
        zero_r2 = float(rung.loc[0.0])
        gate = zero_r2 >= R2_GATE
        order = [float(x) for x in rung.sort_values(ascending=False).index]
        predictions["settings"][setting] = {
            "mean_reconstruction_r2_by_sigma": {
                str(float(k)): float(v) for k, v in rung.items()},
            "zero_noise_r2": zero_r2,
            "zero_noise_gate_passed": bool(gate),
            "utility_prediction": (
                {"kind": "absolute_mean_at_most_resolution",
                 "threshold": RESOLUTION[setting]} if gate else
                {"kind": "uninformative_gate_not_met"}
            ),
            "ladder_prediction": {
                "utility_increases_with_one_minus_r2": True,
                "predicted_sigma_order_from_most_to_least_reconstructible": order,
                "criterion": "cluster_bootstrap_95pct_lower_mean_cell_spearman_gt_0",
            },
        }
    write_json(PREDICTIONS, predictions)
    write_json(PROXY_SEAL, {
        "manifest_sha256": sha256_file(MANIFEST),
        "proxy_rows_sha256": sha256_file(PROXY_ROWS),
        "predictions_sha256": sha256_file(PREDICTIONS),
    })


def validate_proxy_seal() -> None:
    validate_manifest()
    seal = read_json(PROXY_SEAL)
    expected = {
        "manifest_sha256": sha256_file(MANIFEST),
        "proxy_rows_sha256": sha256_file(PROXY_ROWS),
        "predictions_sha256": sha256_file(PREDICTIONS),
    }
    if seal != expected:
        raise RuntimeError("proxy prediction seal mismatch; refusing outcome utility")


def summarize() -> dict[str, Any]:
    validate_proxy_seal()
    proxy = pd.DataFrame(read_json(PROXY_ROWS))
    utility = pd.DataFrame(read_json(UTILITY_ROWS))
    merged = proxy.merge(
        utility,
        on=[c for c in ("setting", "target", "seed", "support_basins", "sigma")
            if c in proxy.columns and c in utility.columns],
        validate="one_to_one",
    )
    predictions = read_json(PREDICTIONS)
    result: dict[str, Any] = {
        "manifest_sha256": sha256_file(MANIFEST),
        "proxy_seal_sha256": sha256_file(PROXY_SEAL),
        "settings": {},
        "paper_tex_modified": False,
    }
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    for setting, part in merged.groupby("setting", sort=True):
        cell_cols = ["seed"] + (["target"] if "target" in part and part["target"].notna().any() else [])
        cell_rhos = []
        for _, cell in part.groupby(cell_cols, sort=True):
            rho = float(spearmanr(1.0 - cell["reconstruction_r2"], cell["utility"]).statistic)
            cell_rhos.append(rho)
        values = np.asarray(cell_rhos, dtype=np.float64)
        boot = np.mean(values[rng.integers(0, len(values), size=(BOOTSTRAP_REPS, len(values)))], axis=1)
        zero = part[part["sigma"] == 0.0]
        mean_utility = float(zero["utility"].mean())
        prediction = predictions["settings"][setting]["utility_prediction"]
        endpoint_pass = None
        if prediction["kind"] == "absolute_mean_at_most_resolution":
            endpoint_pass = abs(mean_utility) <= float(prediction["threshold"])
        rung = part.groupby("sigma", sort=True).agg(
            reconstruction_r2=("reconstruction_r2", "mean"),
            utility=("utility", "mean"),
            reference_metric=("reference_metric", "mean"),
            intended_metric=("intended_metric", "mean"),
        ).reset_index()
        result["settings"][setting] = {
            "n_cells": len(values),
            "zero_noise": {
                "mean_reconstruction_r2": float(zero["reconstruction_r2"].mean()),
                "mean_utility": mean_utility,
                "absolute_mean_utility": abs(mean_utility),
                "prediction": prediction,
                "falsification_check_passed": endpoint_pass,
            },
            "ladder": {
                "mean_cell_spearman": float(values.mean()),
                "cell_spearman_values": values.tolist(),
                "bootstrap_95pct": [float(np.quantile(boot, 0.025)),
                                     float(np.quantile(boot, 0.975))],
                "criterion_met": bool(np.quantile(boot, 0.025) > 0),
                "rung_means": rung.to_dict(orient="records"),
            },
        }
    write_json(SUMMARY, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("freeze", "proxy", "utility", "summarize"))
    parser.add_argument("--threads", type=int, default=8)
    args = parser.parse_args()
    if args.phase == "freeze":
        freeze()
    elif args.phase == "proxy":
        validate_manifest()
        if UTILITY_ROWS.exists():
            raise RuntimeError("utility output already exists; proxy phase must precede it")
        rows = [*medical_proxy_rows(args.threads), *camels_proxy_rows(args.threads)]
        write_json(PROXY_ROWS, rows)
        seal_proxy(rows)
        print(json.dumps({"status": "proxy_sealed", "rows": len(rows),
                          "seal_sha256": sha256_file(PROXY_SEAL)}), flush=True)
    elif args.phase == "utility":
        validate_proxy_seal()
        if UTILITY_ROWS.exists():
            raise RuntimeError(f"utility output already exists: {UTILITY_ROWS}")
        rows = [*medical_utility_rows(args.threads), *camels_utility_rows(args.threads)]
        write_json(UTILITY_ROWS, rows)
        print(json.dumps({"status": "utility_complete", "rows": len(rows),
                          "sha256": sha256_file(UTILITY_ROWS)}), flush=True)
    else:
        print(json.dumps(summarize(), indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
