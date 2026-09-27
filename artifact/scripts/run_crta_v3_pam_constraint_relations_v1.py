#!/usr/bin/env python3
"""PAM-form constraint relations: adjacency and sign knowledge as capacity
removal, on the default M1/M2 benchmark surface.

Frozen design and verdicts:
`iclr_latex_v3/M1M2_PAM_CONSTRAINT_RELATIONS_PREREGISTRATION_V1.md`.
Arms differ only in XGBoost constraint parameters (monotone_constraints,
interaction_constraints); one build per cell.  Metric: query-SD-normalized
RMSE (lower is better).
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
FEATURE_SET = "pam_constraint_all_v1"  # injected at load time
TARGETS = ("glucose", "waist_cm", "triglycerides", "sbp", "dbp", "total_cholesterol")
SEEDS = tuple(range(50, 60))
SUPPORT_ROWS = (64, 256, 1024)
PRIMARY_K = 256

BASE_SLOTS = (
    "age", "creatinine", "rbc", "wbc", "hemoglobin", "hematocrit",
    "sex", "education_level", "diabetes_history", "hypertension_history",
    "current_smoking_status",
)
MEMBER_SLOTS = (
    "height_cm", "weight_kg", "waist_cm", "sbp", "dbp",
    "glucose", "hba1c", "total_cholesterol", "triglycerides",
)
ALL_SLOTS = BASE_SLOTS + MEMBER_SLOTS
GROUPS: dict[str, tuple[str, ...]] = {
    "body_measurements": ("height_cm", "weight_kg", "waist_cm"),
    "first_reading_blood_pressure": ("sbp", "dbp"),
    "diabetes_test_measurements": ("glucose", "hba1c"),
    "blood_lipid_measurements": ("total_cholesterol", "triglycerides"),
}
# Frozen sign table (run_crta_v3_m1m2_monotone_anchor_v1.py DOCUMENTED_SIGNS).
DOCUMENTED_SIGNS: dict[str, dict[str, int]] = {
    "sbp": {"age": 1, "dbp": 1},
    "dbp": {"sbp": 1},
    "glucose": {"hba1c": 1},
    "triglycerides": {"total_cholesterol": 1},
    "total_cholesterol": {"triglycerides": 1},
    "waist_cm": {"weight_kg": 1},
}
ARMS = ("free", "adj_concept", "pl_adj", "sign_documented", "pl_sign_flip",
        "adj_sign")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def derived_rng(key: str) -> np.random.Generator:
    return np.random.default_rng(int(hashlib.sha256(key.encode()).hexdigest()[:16], 16))


def wrong_partition(groups: dict[str, list[str]], target: str, seed: int
                    ) -> dict[str, list[str]]:
    rng = derived_rng(f"pam_v1|pl_adj|{target}|{seed}")
    members = sorted(m for group in groups.values() for m in group)
    sizes = [len(group) for group in groups.values()]
    names = list(groups)
    true_partition = {frozenset(g) for g in groups.values() if g}
    for _ in range(1000):
        shuffled = list(rng.permutation(members))
        parts, cursor = [], 0
        for size in sizes:
            parts.append([str(x) for x in shuffled[cursor:cursor + size]])
            cursor += size
        if {frozenset(p) for p in parts if p} != true_partition:
            return dict(zip(names, parts))
    raise RuntimeError("no wrong partition found")


def interaction_groups(feature_names: list[str],
                       partition: dict[str, list[str]]) -> list[list[int]]:
    index = {name: i for i, name in enumerate(feature_names)}
    base_idx = [index[s] for s in feature_names if s in BASE_SLOTS]
    groups = []
    for members in partition.values():
        present = [index[m] for m in members if m in index]
        if present:
            groups.append(sorted(base_idx + present))
    return groups


def sign_vector(feature_names: list[str], target: str, flip: bool
                ) -> tuple[int, ...]:
    signs = {name: 0 for name in feature_names}
    for feature, sign in DOCUMENTED_SIGNS[target].items():
        if feature in signs:
            signs[feature] = -sign if flip else sign
    return tuple(signs[name] for name in feature_names)


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
    parser.add_argument("--support-rows", nargs="*", type=int, default=list(SUPPORT_ROWS))
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()

    for key, path in (("nhanes", args.nhanes_parquet), ("knhanes", args.knhanes_parquet)):
        observed = sha256_file(path)
        if observed != EXPECTED[key]:
            raise RuntimeError(f"{key} parquet SHA-256 mismatch: {observed}")

    from xgboost import XGBRegressor

    sys.path.insert(0, str(BENCH / "scripts"))
    benchmark = _load("crta_bench_pam", BENCH / "scripts/build_benchmark_table.py")
    original_load_yaml = benchmark.load_yaml
    manifest_path = Path(benchmark.DEFAULT_DATASET_MANIFEST).resolve()

    def load_yaml_patched(path):
        value = original_load_yaml(path)
        if Path(path).resolve() == manifest_path:
            value["datasets"]["nhanes"]["parquet"] = str(args.nhanes_parquet)
            value["datasets"]["knhanes"]["parquet"] = str(args.knhanes_parquet)
        if isinstance(value, dict) and "feature_sets" in value:
            value["feature_sets"][FEATURE_SET] = {
                "description": "pam_constraint_v1 injected feature set",
                "feature_mode": "explicit_slots", "slots": list(ALL_SLOTS)}
        return value

    benchmark.load_yaml = load_yaml_patched
    args.out_root.mkdir(parents=True, exist_ok=True)

    for target in args.targets:
        feature_names = [s for s in ALL_SLOTS if s != target]
        groups_e = {name: [m for m in group if m != target]
                    for name, group in GROUPS.items()}
        for seed in args.seeds:
            out = args.out_root / target / f"seed_{seed}"
            if (out / "metrics.json").is_file():
                continue
            t0 = time.time()

            bundle = benchmark.build_single_target_table(
                benchmark_id=BENCHMARK_ID, target_name=target,
                fewshot_frac=0.10, seed=seed,
                target_set_override="objective_anchor_targets_v1_safe",
                feature_set_override=FEATURE_SET,
            )
            x_train = bundle["X_train"].reset_index(drop=True)
            x_test = bundle["X_test"].reset_index(drop=True)
            x_all = x_train[[f"slot__{s}" for s in feature_names]].apply(
                pd.to_numeric, errors="coerce").to_numpy(np.float64)
            x_q = x_test[[f"slot__{s}" for s in feature_names]].apply(
                pd.to_numeric, errors="coerce").to_numpy(np.float64)
            y_train = pd.to_numeric(
                bundle["y_train"], errors="coerce").to_numpy(np.float64)
            y_test = pd.to_numeric(
                bundle["y_test"], errors="coerce").to_numpy(np.float64)
            origin = np.asarray(bundle["train_origin"], dtype=object)
            n_source = int(np.sum(origin == "source"))
            n_pool = len(x_all) - n_source
            query_sd = float(np.std(y_test, ddof=0))

            wrong = wrong_partition(groups_e, target, seed)
            adj_true = interaction_groups(feature_names, groups_e)
            adj_wrong = interaction_groups(feature_names, wrong)
            signs_doc = sign_vector(feature_names, target, flip=False)
            signs_flip = sign_vector(feature_names, target, flip=True)

            # xgboost 3.x requires the interaction spec as a JSON string when
            # fitting on bare numpy arrays.
            adj_true_s = json.dumps(adj_true)
            adj_wrong_s = json.dumps(adj_wrong)
            arm_params = {
                "free": {},
                "adj_concept": {"interaction_constraints": adj_true_s},
                "pl_adj": {"interaction_constraints": adj_wrong_s},
                "sign_documented": {"monotone_constraints": signs_doc},
                "pl_sign_flip": {"monotone_constraints": signs_flip},
                "adj_sign": {"interaction_constraints": adj_true_s,
                             "monotone_constraints": signs_doc},
            }

            results: dict = {}
            for K in args.support_rows:
                pick = np.sort(np.random.default_rng(seed * 131 + K).choice(
                    n_pool, size=min(K, n_pool), replace=False))
                rows = np.arange(n_source, len(x_all))[pick]
                x_fit = np.vstack([x_all[:n_source], x_all[rows]])
                y_fit = np.concatenate([y_train[:n_source], y_train[rows]])
                weights = np.concatenate([
                    np.ones(n_source),
                    np.full(len(rows), n_source / max(len(rows), 1)),
                ])
                results[str(K)] = {}
                for arm in ARMS:
                    model = XGBRegressor(
                        n_estimators=300, max_depth=6, learning_rate=0.05,
                        subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0,
                        n_jobs=args.threads, random_state=seed,
                        tree_method="hist", **arm_params[arm],
                    )
                    model.fit(x_fit, y_fit, sample_weight=weights)
                    pred = model.predict(x_q)
                    results[str(K)][arm] = float(
                        np.sqrt(np.mean((y_test - pred) ** 2)) / query_sd)

            out.mkdir(parents=True, exist_ok=True)
            (out / "metrics.json").write_text(json.dumps({
                "target": target, "seed": seed,
                "benchmark_id": BENCHMARK_ID, "feature_set": FEATURE_SET,
                "metric": "query_sd_normalized_rmse (lower is better)",
                "backbone": "xgboost_hist_d6_n300",
                "arms": list(ARMS), "primary_k": PRIMARY_K,
                "n_source": n_source, "n_pool": n_pool,
                "n_query": int(len(y_test)),
                "documented_signs": DOCUMENTED_SIGNS[target],
                "pl_adj_partition": wrong,
                "wall_seconds": round(time.time() - t0, 1),
                "nrmse": results,
            }, indent=1, sort_keys=True) + "\n", encoding="utf-8")
            print(json.dumps({"target": target, "seed": seed,
                              "wall_seconds": round(time.time() - t0, 1),
                              "done": True}), flush=True)

    print(json.dumps({"status": "complete"}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
