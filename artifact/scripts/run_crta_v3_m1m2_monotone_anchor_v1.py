#!/usr/bin/env python3
"""Knowledge as CONSTRAINT, not information: monotone-sign anchoring.

Every injection tested on 2026-08-18 added things -- feature columns, attention
bias, embeddings -- and every one was matched by a capacity-equal placebo.  A
monotonicity constraint is the opposite move: it REMOVES capacity.  The
capacity-matched-placebo critique therefore cannot apply; the epistemics invert.

    documented   the declared sign table below
    flipped      same features, every sign negated
    random       same number of constrained features per target, features and
                 signs drawn at random per (target, seed)
    none         unconstrained

Falsifiable prediction, declared before running: at small support (K=32) the
documented signs beat `none`, `flipped` actively HURTS (a wrong constraint must
cost something if constraints bind at all), `random` sits between, and all four
converge as K grows.  If documented ~ random, knowledge-as-constraint fails like
everything before it and is reported as such.

Sign table.  Directions are marginal, prediction-vs-feature, and only pairs
whose direction is essentially settled physiology are constrained; everything
else stays 0.  Frozen here before any run:

    sbp               <- age +1, dbp +1     (BP rises with age; SBP/DBP co-move)
    dbp               <- sbp +1
    glucose           <- hba1c +1           (HbA1c is glycated average glucose)
    triglycerides     <- total_cholesterol +1  (TC includes a VLDL~TG/5 term)
    total_cholesterol <- triglycerides +1
    waist_cm          <- weight_kg +1

Backbones: xgb_support (K rows only -- where a prior can matter) and
xgb_transfer (full source + K rows -- the anchor setting).  TabPFN has no
constraint interface and is omitted.

Metric: query-SD-normalized RMSE (nRMSE, lower is better), full query set.
Data paths are hash-pinned; support subsampling uses the same seeded RNG as the
prior-value harness so cells join on (target, seed, K).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
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
TARGETS = ("glucose", "waist_cm", "triglycerides", "sbp", "dbp", "total_cholesterol")
SEEDS = tuple(range(10, 20))
SUPPORT_ROWS = (32, 64, 128, 256)
TARGET_WEIGHT = 10.0
ALL_SLOTS = (
    "age", "height_cm", "weight_kg", "waist_cm", "sbp", "dbp", "glucose",
    "hba1c", "creatinine", "hemoglobin", "total_cholesterol", "triglycerides",
)
DOCUMENTED_SIGNS: dict[str, dict[str, int]] = {
    "sbp": {"age": 1, "dbp": 1},
    "dbp": {"sbp": 1},
    "glucose": {"hba1c": 1},
    "triglycerides": {"total_cholesterol": 1},
    "total_cholesterol": {"triglycerides": 1},
    "waist_cm": {"weight_kg": 1},
}
ARMS = ("none", "documented", "flipped", "random")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def constraint_vector(target: str, slots: list[str], arm: str,
                      rng: np.random.Generator) -> tuple[int, ...]:
    signs = {s: 0 for s in slots}
    documented = DOCUMENTED_SIGNS[target]
    if arm == "documented":
        for s, v in documented.items():
            signs[s] = v
    elif arm == "flipped":
        for s, v in documented.items():
            signs[s] = -v
    elif arm == "random":
        pick = rng.choice(len(slots), size=len(documented), replace=False)
        for k in pick:
            signs[slots[int(k)]] = int(rng.choice([-1, 1]))
    return tuple(signs[s] for s in slots)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nhanes-parquet", type=Path, required=True)
    parser.add_argument("--knhanes-parquet", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--targets", nargs="*", default=list(TARGETS))
    parser.add_argument("--seeds", nargs="*", type=int, default=list(SEEDS))
    parser.add_argument("--n-jobs", type=int, default=4)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    args = parser.parse_args()

    for key, path in (("nhanes", args.nhanes_parquet), ("knhanes", args.knhanes_parquet)):
        observed = sha256_file(path)
        if observed != EXPECTED[key]:
            raise RuntimeError(f"{key} parquet SHA-256 mismatch: {observed}")

    from xgboost import XGBRegressor
    sys.path.insert(0, str(BENCH / "scripts"))
    benchmark = _load("crta_bench", BENCH / "scripts/build_benchmark_table.py")
    original_load_yaml = benchmark.load_yaml
    manifest_path = Path(benchmark.DEFAULT_DATASET_MANIFEST).resolve()

    def load_yaml_with_runtime_data(path):
        value = original_load_yaml(path)
        if Path(path).resolve() == manifest_path:
            value["datasets"]["nhanes"]["parquet"] = str(args.nhanes_parquet)
            value["datasets"]["knhanes"]["parquet"] = str(args.knhanes_parquet)
        return value

    benchmark.load_yaml = load_yaml_with_runtime_data
    args.out_root.mkdir(parents=True, exist_ok=True)
    cells = [(t, s) for t in args.targets for s in args.seeds]
    selected = [c for i, c in enumerate(cells) if i % args.shard_count == args.shard_index]

    for target, seed in selected:
        out = args.out_root / target / f"seed_{seed}"
        if (out / "metrics.json").is_file():
            continue
        bundle = benchmark.build_single_target_table(
            benchmark_id="std_cross_nh2kn_shared_anchorreset_fewshot_v1",
            target_name=target, fewshot_frac=0.01, seed=seed,
            target_set_override="objective_anchor_targets_v1_safe",
        )
        x_train_f = bundle["X_train"].reset_index(drop=True)
        x_test_f = bundle["X_test"].reset_index(drop=True)
        y_train = pd.to_numeric(bundle["y_train"], errors="coerce").to_numpy(np.float64)
        y_test = pd.to_numeric(bundle["y_test"], errors="coerce").to_numpy(np.float64)
        origin = np.asarray(bundle["train_origin"], dtype=object)
        n_source = int(np.sum(origin == "source"))
        n_pool = len(x_train_f) - n_source
        query_sd = float(np.std(y_test, ddof=0))

        slots = [s for s in ALL_SLOTS if s != target]
        cols = [f"slot__{s}" for s in slots]
        x_all = x_train_f[cols].apply(pd.to_numeric, errors="coerce").to_numpy(np.float64)
        x_q = x_test_f[cols].apply(pd.to_numeric, errors="coerce").to_numpy(np.float64)
        rng = np.random.default_rng(seed * 4409 + hash(target) % 3163)
        vectors = {arm: constraint_vector(target, slots, arm, rng) for arm in ARMS}

        results: dict = {}
        for K in SUPPORT_ROWS:
            pick = np.sort(np.random.default_rng(seed * 131 + K).choice(
                n_pool, size=min(K, n_pool), replace=False))
            sup_idx = np.arange(n_source, len(x_train_f))[pick]
            results[str(K)] = {}
            for backbone in ("xgb_support", "xgb_transfer"):
                if backbone == "xgb_transfer":
                    rows = np.concatenate([np.arange(n_source), sup_idx])
                    weights = np.concatenate(
                        [np.ones(n_source), np.full(len(sup_idx), TARGET_WEIGHT)])
                else:
                    rows, weights = sup_idx, None
                xt, yt = x_all[rows], y_train[rows]
                results[str(K)][backbone] = {}
                for arm in ARMS:
                    model = XGBRegressor(
                        objective="reg:squarederror", n_estimators=300, max_depth=5,
                        learning_rate=0.05, min_child_weight=5.0, subsample=0.8,
                        colsample_bytree=0.8, reg_lambda=1.0, random_state=seed,
                        n_jobs=args.n_jobs, tree_method="hist",
                        monotone_constraints=vectors[arm],
                    )
                    model.fit(xt, yt, sample_weight=weights)
                    pred = model.predict(x_q).astype(np.float64)
                    results[str(K)][backbone][arm] = float(
                        np.sqrt(np.mean((y_test - pred) ** 2)) / query_sd)
        out.mkdir(parents=True, exist_ok=True)
        (out / "metrics.json").write_text(json.dumps({
            "target": target, "seed": seed,
            "metric": "query_sd_normalized_rmse (lower is better)",
            "documented_signs": DOCUMENTED_SIGNS[target],
            "constraint_vectors": {a: list(v) for a, v in vectors.items()},
            "slots": slots, "support_rows": list(SUPPORT_ROWS),
            "nrmse": results,
        }, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"target": target, "seed": seed, "done": True}), flush=True)

    print(json.dumps({"status": "complete"}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
