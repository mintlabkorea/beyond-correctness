#!/usr/bin/env python3
"""S5: the binding contrast on a SECOND backbone (sklearn HistGB).

Frozen design and verdicts:
`iclr_latex_v3/BINDING_BACKBONE_GENERALITY_PREREGISTRATION_V1.md`.

The stage factorial's L0-on cells with three arms (base / correct
binding / deranged binding), refit with HistGradientBoostingRegressor.
The derangement draws reuse the executed run's RNG keys, so the lesion
is bit-identical to the XGBoost cells.  Metric: AUROC against the fixed
codebook-documented target-side binary (higher is better).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BENCH = Path(os.environ.get(
    "CRTA_BENCH_ROOT",
    "data/benchmark",
))
EXPECTED = {
    "nhanes": "345163df04c0d153215eb3b5cb5c9a167f448d900019b323933db0ab6d551112",
    "knhanes": "34762e6e8d2cc20ae7bb2b2b8ea62d2d8c3508ee05a7ed20bc785d5576908ccd",
}
BENCHMARK_ID = "std_cross_nh2kn_shared_anchorreset_fewshot_v1"
FEATURE_SET = "stage_factorial_all_v1"  # injected at load time
TARGET_SET = "stage_factorial_targets_v1"  # injected at load time
SEEDS = tuple(range(50, 60))
SUPPORT_ROWS = (64, 256, 1024)
PRIMARY_K = 256

BASE_CLINICAL = ("age", "creatinine", "rbc", "wbc", "hemoglobin", "hematocrit")
SURVEY_SLOTS = (
    "sex", "education_level", "diabetes_history", "hypertension_history",
    "current_smoking_status",
)
MEMBER_SLOTS = (
    "height_cm", "weight_kg", "waist_cm", "sbp", "dbp",
    "glucose", "hba1c", "total_cholesterol", "triglycerides",
)
ALL_SLOTS = BASE_CLINICAL + SURVEY_SLOTS + MEMBER_SLOTS

TARGETS: dict[str, tuple[str, str]] = {
    "diabetes_history": ("DIQ010", "ALL__de1_dg"),
    "hypertension_history": ("BPQ020", "ALL__di1_dg"),
    "current_smoking_status": ("SMQ040", "ALL__bs3_1"),
}
PIPELINE_LABEL_MAPS: dict[str, dict[str, dict[float, float]]] = {
    "diabetes_history": {"source": {1: 1, 2: 0}, "target": {1: 1, 0: 0}},
    "hypertension_history": {"source": {1: 1, 2: 0}, "target": {1: 1, 0: 0}},
    "current_smoking_status": {
        "source": {1: 1, 2: 1, 3: 0}, "target": {1: 1, 2: 1, 3: 0, 4: 0}},
}
EVAL_LABEL_MAPS: dict[str, dict[float, float]] = {
    "diabetes_history": {1: 1, 0: 0},
    "hypertension_history": {1: 1, 0: 0},
    "current_smoking_status": {1: 1, 2: 1, 3: 0, 4: 0},
}
ARMS = ("a10_stage", "a11_stage_columns", "pl_columns_at_stage")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def derived_rng(key: str) -> np.random.Generator:
    return np.random.default_rng(int(hashlib.sha256(key.encode()).hexdigest()[:16], 16))


def map_values(values: np.ndarray, mapping: dict[float, float]) -> np.ndarray:
    out = np.full(len(values), np.nan)
    for code, value in mapping.items():
        out[values == float(code)] = float(value)
    return out


def make_member_permutation(target: str, seed: int) -> dict[str, str]:
    """Identical keying to the executed stage factorial: the same lesion."""
    rng = derived_rng(f"stage_factorial_v1|pl_col|{target}|{seed}")
    members = list(MEMBER_SLOTS)
    for _ in range(1000):
        perm = list(rng.permutation(members))
        if all(a != b for a, b in zip(members, perm)):
            return {a: str(b) for a, b in zip(members, perm)}
    raise RuntimeError("no derangement found")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nhanes-parquet", type=Path, required=True)
    parser.add_argument("--knhanes-parquet", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--targets", nargs="*", default=list(TARGETS))
    parser.add_argument("--seeds", nargs="*", type=int, default=list(SEEDS))
    parser.add_argument("--support-rows", nargs="*", type=int,
                        default=list(SUPPORT_ROWS))
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()

    for key, path in (("nhanes", args.nhanes_parquet),
                      ("knhanes", args.knhanes_parquet)):
        observed = sha256_file(path)
        if observed != EXPECTED[key]:
            raise RuntimeError(f"{key} parquet SHA-256 mismatch: {observed}")

    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.metrics import roc_auc_score
    from threadpoolctl import threadpool_limits

    sys.path.insert(0, str(BENCH / "scripts"))
    benchmark = _load("crta_bench_s5", BENCH / "scripts/build_benchmark_table.py")
    original_load_yaml = benchmark.load_yaml
    manifest_path = Path(benchmark.DEFAULT_DATASET_MANIFEST).resolve()

    def load_yaml_patched(path):
        value = original_load_yaml(path)
        if Path(path).resolve() == manifest_path:
            value["datasets"]["nhanes"]["parquet"] = str(args.nhanes_parquet)
            value["datasets"]["knhanes"]["parquet"] = str(args.knhanes_parquet)
            for target, (nh_col, kn_col) in TARGETS.items():
                value.setdefault("targets", {})[target] = {
                    "label": target, "nhanes": nh_col, "knhanes": kn_col}
        if isinstance(value, dict) and "feature_sets" in value:
            value["feature_sets"][FEATURE_SET] = {
                "description": "s5 injected feature set",
                "feature_mode": "explicit_slots", "slots": list(ALL_SLOTS)}
        if isinstance(value, dict) and "target_sets" in value:
            value["target_sets"][TARGET_SET] = {
                "description": "s5 injected targets",
                "targets": list(TARGETS)}
        return value

    benchmark.load_yaml = load_yaml_patched
    args.out_root.mkdir(parents=True, exist_ok=True)

    for target in args.targets:
        base_slots = [s for s in BASE_CLINICAL + SURVEY_SLOTS if s != target]
        for seed in args.seeds:
            out = args.out_root / target / f"seed_{seed}"
            if (out / "metrics.json").is_file():
                continue
            t0 = time.time()

            bundle = benchmark.build_single_target_table(
                benchmark_id=BENCHMARK_ID, target_name=target,
                fewshot_frac=0.10, seed=seed,
                target_set_override=TARGET_SET,
                feature_set_override=FEATURE_SET,
            )
            x_train = bundle["X_train"].reset_index(drop=True)
            x_test = bundle["X_test"].reset_index(drop=True)
            if f"slot__{target}" in x_train.columns:
                raise RuntimeError(f"endpoint slot leaked: {target}")
            slots = {}
            for slot in ALL_SLOTS:
                if slot == target:
                    continue
                column = f"slot__{slot}"
                slots[slot] = (
                    pd.to_numeric(x_train[column], errors="coerce"
                                  ).to_numpy(np.float64),
                    pd.to_numeric(x_test[column], errors="coerce"
                                  ).to_numpy(np.float64),
                )
            origin = np.asarray(bundle["train_origin"], dtype=object)
            n_source = int(np.sum(origin == "source"))
            y_raw_train = pd.to_numeric(
                bundle["y_train"], errors="coerce").to_numpy(np.float64)
            y_raw_test = pd.to_numeric(
                bundle["y_test"], errors="coerce").to_numpy(np.float64)
            n_pool = len(y_raw_train) - n_source

            y_eval = map_values(y_raw_test, EVAL_LABEL_MAPS[target])
            eval_mask = np.isfinite(y_eval)
            if len(np.unique(y_eval[eval_mask])) < 2:
                raise RuntimeError(f"degenerate eval label for {target}")
            label_maps = PIPELINE_LABEL_MAPS[target]
            col_perm = make_member_permutation(target, seed)

            results: dict = {}
            for K in args.support_rows:
                pick = np.sort(np.random.default_rng(seed * 131 + K).choice(
                    n_pool, size=min(K, n_pool), replace=False))
                sup_rows = np.arange(n_source, len(y_raw_train))[pick]
                results[str(K)] = {}
                for arm in ARMS:
                    permuted = arm == "pl_columns_at_stage"
                    fit_parts, query_parts = [], []
                    for slot in base_slots:
                        train_col = slots[slot][0]
                        fit_parts.append(np.concatenate(
                            [train_col[:n_source], train_col[sup_rows]]))
                        query_parts.append(slots[slot][1])
                    if arm != "a10_stage":
                        for slot in MEMBER_SLOTS:
                            target_slot = col_perm[slot] if permuted else slot
                            fit_parts.append(np.concatenate([
                                slots[slot][0][:n_source],
                                slots[target_slot][0][sup_rows]]))
                            query_parts.append(slots[target_slot][1])
                    y_src = map_values(y_raw_train[:n_source],
                                       label_maps["source"])
                    y_sup = map_values(y_raw_train[sup_rows],
                                       label_maps["target"])
                    src_keep = np.isfinite(y_src)
                    sup_keep = np.isfinite(y_sup)
                    if src_keep.sum() == 0 or sup_keep.sum() == 0:
                        results[str(K)][arm] = float("nan")
                        continue
                    keep = np.concatenate([src_keep, sup_keep])
                    x_fit = np.column_stack(fit_parts)[keep]
                    x_query = np.column_stack(query_parts)
                    y_fit = np.concatenate([y_src[src_keep], y_sup[sup_keep]])
                    weights = np.concatenate([
                        np.ones(int(src_keep.sum())),
                        np.full(int(sup_keep.sum()),
                                float(src_keep.sum())
                                / max(int(sup_keep.sum()), 1)),
                    ])
                    model = HistGradientBoostingRegressor(
                        max_iter=300, max_depth=6, learning_rate=0.05,
                        min_samples_leaf=20, l2_regularization=1.0,
                        random_state=seed, early_stopping=False,
                    )
                    with threadpool_limits(limits=max(args.threads, 1)):
                        model.fit(x_fit, y_fit, sample_weight=weights)
                        pred = model.predict(x_query[eval_mask])
                    results[str(K)][arm] = float(
                        roc_auc_score(y_eval[eval_mask], pred))

            out.mkdir(parents=True, exist_ok=True)
            (out / "metrics.json").write_text(json.dumps({
                "target": target, "seed": seed,
                "benchmark_id": BENCHMARK_ID, "feature_set": FEATURE_SET,
                "metric": "auroc_vs_documented_target_binary (higher is better)",
                "backbone": "sklearn_histgb_d6_i300",
                "arms": list(ARMS), "primary_k": PRIMARY_K,
                "n_source": n_source, "n_pool": n_pool,
                "n_eval": int(eval_mask.sum()),
                "pl_columns_permutation": col_perm,
                "wall_seconds": round(time.time() - t0, 1),
                "auroc": results,
            }, indent=1, sort_keys=True, default=str) + "\n",
                encoding="utf-8")
            print(json.dumps({"target": target, "seed": seed,
                              "wall_seconds": round(time.time() - t0, 1),
                              "done": True}), flush=True)

    print(json.dumps({"status": "complete"}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
