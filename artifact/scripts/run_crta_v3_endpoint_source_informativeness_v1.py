#!/usr/bin/env python3
"""Run arm-disjoint source informativeness and target-only endpoint arms."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BASE_RUNNER = ROOT / "scripts/run_crta_v3_m1m2_stage_factorial_v1.py"
REGISTRY = ROOT / "scripts/crta_v3_stage_endpoint_registry_v1.py"
PREREG = ROOT / "iclr_latex_v3/ENDPOINT_SOURCE_INFORMATIVENESS_PREREGISTRATION_V1.md"
BENCH = Path(os.environ.get(
    "CRTA_BENCH_ROOT",
    "data/benchmark",
))
EXPECTED = {
    "nhanes": "345163df04c0d153215eb3b5cb5c9a167f448d900019b323933db0ab6d551112",
    "knhanes": "34762e6e8d2cc20ae7bb2b2b8ea62d2d8c3508ee05a7ed20bc785d5576908ccd",
}
DIRECTIONS = ("nh2kn", "kn2nh")
SEEDS = tuple(range(50, 60))
K = 256
ARMS = ("source_only_correct", "target_only_correct")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def configure(direction: str) -> Any:
    sf = load(f"endpoint_info_base_{direction}", BASE_RUNNER)
    registry = load(f"endpoint_info_registry_{direction}", REGISTRY)
    registry.configure(sf)
    if direction == "kn2nh":
        sf.BENCHMARK_ID = "std_cross_kn2nh_shared_anchorreset_fewshot_v1"
        sf.PIPELINE_LABEL_MAPS = {
            target: {"source": maps["target"], "target": maps["source"]}
            for target, maps in sf.PIPELINE_LABEL_MAPS.items()
        }
        sf.EVAL_LABEL_MAPS = {
            target: ({1: 1, 2: 1, 3: 0}
                     if target == "current_smoking_status"
                     else {1: 1, 2: 0})
            for target in sf.TARGETS
        }
        sf.LABEL_ITEMS = {
            target: {"source": sides["target"], "target": sides["source"]}
            for target, sides in sf.LABEL_ITEMS.items()
        }
    return sf


def validate_references(reference_root: Path, targets: list[str],
                        seeds: list[int]) -> dict[str, Any]:
    missing = []
    observed = []
    for target in targets:
        for seed in seeds:
            path = reference_root / target / f"seed_{seed}" / "metrics.json"
            if not path.is_file():
                missing.append(str(path))
                continue
            record = json.loads(path.read_text())
            if record.get("target") != target or int(record.get("seed")) != seed:
                raise RuntimeError(f"reference identity mismatch: {path}")
            if str(K) not in record.get("auroc", {}):
                raise RuntimeError(f"reference lacks K={K}: {path}")
            observed.append(path)
    if missing:
        raise RuntimeError(f"missing {len(missing)} reference cells; first={missing[0]}")
    return {"reference_cells": len(observed), "expected_cells": len(targets) * len(seeds)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--direction", choices=DIRECTIONS, required=True)
    parser.add_argument("--nhanes-parquet", type=Path, required=True)
    parser.add_argument("--knhanes-parquet", type=Path, required=True)
    parser.add_argument("--reference-root", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--targets", nargs="*", default=None)
    parser.add_argument("--seeds", nargs="*", type=int, default=list(SEEDS))
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    for key, path in (("nhanes", args.nhanes_parquet),
                      ("knhanes", args.knhanes_parquet)):
        observed = sha256_file(path)
        if observed != EXPECTED[key]:
            raise RuntimeError(f"{key} parquet SHA-256 mismatch: {observed}")

    sf = configure(args.direction)
    targets = list(args.targets) if args.targets else list(sf.TARGETS)
    unknown = sorted(set(targets) - set(sf.TARGETS))
    if unknown:
        raise RuntimeError(f"unknown targets: {unknown}")
    if any(seed not in SEEDS for seed in args.seeds):
        raise RuntimeError(f"seeds outside frozen set: {args.seeds}")
    reference_check = validate_references(args.reference_root, targets, args.seeds)
    provenance = {
        "runner_sha256": sha256_file(Path(__file__)),
        "base_runner_sha256": sha256_file(BASE_RUNNER),
        "registry_sha256": sha256_file(REGISTRY),
        "prereg_sha256": sha256_file(PREREG),
        "nhanes_sha256": EXPECTED["nhanes"],
        "knhanes_sha256": EXPECTED["knhanes"],
    }
    if args.validate_only:
        print(json.dumps({
            "direction": args.direction,
            "targets": len(targets),
            "seeds": len(args.seeds),
            **reference_check,
            "provenance": provenance,
        }, indent=1, sort_keys=True))
        return 0

    from sklearn.metrics import roc_auc_score
    from xgboost import XGBRegressor

    sys.path.insert(0, str(BENCH / "scripts"))
    benchmark = load(f"endpoint_info_benchmark_{args.direction}",
                     BENCH / "scripts/build_benchmark_table.py")
    original_load_yaml = benchmark.load_yaml
    original_rule_index = benchmark.load_questionnaire_rule_index
    original_recode = benchmark.recode_questionnaire_series
    manifest_path = Path(benchmark.DEFAULT_DATASET_MANIFEST).resolve()

    def load_yaml_patched(path):
        value = original_load_yaml(path)
        if Path(path).resolve() == manifest_path:
            value["datasets"]["nhanes"]["parquet"] = str(args.nhanes_parquet)
            value["datasets"]["knhanes"]["parquet"] = str(args.knhanes_parquet)
            for target, (nh_col, kn_col) in sf.TARGETS.items():
                value.setdefault("targets", {})[target] = {
                    "label": target, "nhanes": nh_col, "knhanes": kn_col}
        if isinstance(value, dict) and "feature_sets" in value:
            value["feature_sets"][sf.FEATURE_SET] = {
                "description": "endpoint source informativeness exact a11 representation",
                "feature_mode": "explicit_slots", "slots": list(sf.ALL_SLOTS)}
        if isinstance(value, dict) and "target_sets" in value:
            value["target_sets"][sf.TARGET_SET] = {
                "description": "frozen ten endpoint panel",
                "targets": list(sf.TARGETS)}
        return value

    def recode_dispatch(series, rule_id):
        try:
            spec = json.loads(rule_id)
        except (TypeError, ValueError):
            return original_recode(series, rule_id)
        values = pd.to_numeric(series, errors="coerce")
        out = pd.Series(np.nan, index=series.index, dtype="float64")
        for code, value in spec["map"].items():
            out[values == float(code)] = float(value)
        return out

    benchmark.load_yaml = load_yaml_patched
    benchmark.recode_questionnaire_series = recode_dispatch
    benchmark.load_questionnaire_rule_index = original_rule_index
    args.out_root.mkdir(parents=True, exist_ok=True)

    def build(target: str, seed: int) -> dict[str, Any]:
        bundle = benchmark.build_single_target_table(
            benchmark_id=sf.BENCHMARK_ID, target_name=target,
            fewshot_frac=0.10, seed=seed,
            target_set_override=sf.TARGET_SET,
            feature_set_override=sf.FEATURE_SET,
        )
        x_train = bundle["X_train"].reset_index(drop=True)
        x_test = bundle["X_test"].reset_index(drop=True)
        if f"slot__{target}" in x_train.columns:
            raise RuntimeError(f"endpoint slot leaked into features: {target}")
        slots = {}
        for slot in sf.ALL_SLOTS:
            if slot == target:
                continue
            column = f"slot__{slot}"
            slots[slot] = (
                pd.to_numeric(x_train[column], errors="coerce").to_numpy(np.float64),
                pd.to_numeric(x_test[column], errors="coerce").to_numpy(np.float64),
            )
        origin = np.asarray(bundle["train_origin"], dtype=object)
        return {
            "slots": slots,
            "y_train": pd.to_numeric(
                bundle["y_train"], errors="coerce").to_numpy(np.float64),
            "y_test": pd.to_numeric(
                bundle["y_test"], errors="coerce").to_numpy(np.float64),
            "n_source": int(np.sum(origin == "source")),
        }

    for target in targets:
        base_slots = [s for s in sf.BASE_CLINICAL + sf.SURVEY_SLOTS if s != target]
        feature_slots = base_slots + list(sf.MEMBER_SLOTS)
        for seed in args.seeds:
            out = args.out_root / target / f"seed_{seed}"
            if (out / "metrics.json").is_file():
                existing = json.loads((out / "metrics.json").read_text())
                if any(existing.get(key) != provenance[key] for key in (
                        "runner_sha256", "base_runner_sha256", "registry_sha256",
                        "prereg_sha256", "nhanes_sha256", "knhanes_sha256")):
                    raise RuntimeError(
                        f"existing cell has stale provenance; archive before resume: {out}")
                continue
            started = time.time()
            bundle = build(target, seed)
            n_source = bundle["n_source"]
            n_train = len(bundle["y_train"])
            n_pool = n_train - n_source
            pick = np.sort(np.random.default_rng(seed * 131 + K).choice(
                n_pool, size=min(K, n_pool), replace=False))
            support_rows = np.arange(n_source, n_train)[pick]

            x_source = np.column_stack([
                bundle["slots"][slot][0][:n_source] for slot in feature_slots])
            x_support = np.column_stack([
                bundle["slots"][slot][0][support_rows] for slot in feature_slots])
            x_query = np.column_stack([
                bundle["slots"][slot][1] for slot in feature_slots])
            y_source = sf.map_values(
                bundle["y_train"][:n_source],
                sf.PIPELINE_LABEL_MAPS[target]["source"])
            y_support = sf.map_values(
                bundle["y_train"][support_rows],
                sf.PIPELINE_LABEL_MAPS[target]["target"])
            y_eval = sf.map_values(bundle["y_test"], sf.EVAL_LABEL_MAPS[target])
            eval_keep = np.isfinite(y_eval)
            if len(np.unique(y_eval[eval_keep])) < 2:
                raise RuntimeError(f"degenerate query labels: {target}, {seed}")

            arm_data = {
                "source_only_correct": (x_source, y_source),
                "target_only_correct": (x_support, y_support),
            }
            results = {}
            counts = {}
            class_counts = {}
            for arm, (x_fit, y_fit) in arm_data.items():
                keep = np.isfinite(y_fit)
                if keep.sum() == 0:
                    raise RuntimeError(f"invalid fit labels: {target}, {seed}, {arm}")
                model = XGBRegressor(
                    n_estimators=300, max_depth=6, learning_rate=0.05,
                    subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0,
                    n_jobs=args.threads, random_state=seed, tree_method="hist",
                )
                model.fit(x_fit[keep], y_fit[keep],
                          sample_weight=np.ones(int(keep.sum())))
                pred = model.predict(x_query[eval_keep])
                results[arm] = float(roc_auc_score(y_eval[eval_keep], pred))
                counts[arm] = int(keep.sum())
                class_counts[arm] = int(len(np.unique(y_fit[keep])))

            reference_path = (args.reference_root / target / f"seed_{seed}"
                              / "metrics.json")
            reference = json.loads(reference_path.read_text())
            if (int(reference["n_source"]) != n_source
                    or int(reference["n_pool"]) != n_pool
                    or int(reference["n_eval"]) != int(eval_keep.sum())):
                raise RuntimeError(f"split/count mismatch with reference: {reference_path}")

            out.mkdir(parents=True, exist_ok=True)
            payload = {
                "experiment": "endpoint_source_informativeness_v1",
                "direction": args.direction,
                "target": target,
                "seed": seed,
                "support_k": K,
                "arms": list(ARMS),
                "auroc": results,
                "fit_rows": counts,
                "fit_unique_label_counts": class_counts,
                "n_source": n_source,
                "n_pool": n_pool,
                "n_eval": int(eval_keep.sum()),
                "reference_metrics_sha256": sha256_file(reference_path),
                "reference_a11_auroc": float(
                    reference["auroc"][str(K)]["a11_stage_columns"]),
                "wall_seconds": round(time.time() - started, 3),
                **provenance,
            }
            (out / "metrics.json").write_text(
                json.dumps(payload, indent=1, sort_keys=True) + "\n")
            print(json.dumps({
                "direction": args.direction, "target": target, "seed": seed,
                "wall_seconds": payload["wall_seconds"], "done": True,
            }), flush=True)

    print(json.dumps({"status": "complete", "direction": args.direction}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
