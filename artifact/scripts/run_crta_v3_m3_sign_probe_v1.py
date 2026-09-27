#!/usr/bin/env python3
"""G-SIGN-M3: direction-constraint identification on a second schema pair.

Imports the frozen M3 runtime (nhkn -> HRS) unmodified and reuses its
loaders, keyed splits, base features, estimator and metrics, so cells are
identical to the published M3 runs.  Three arms per cell: `free`,
`sign_documented`, `sign_flipped` (same slots, negated) plus
`sign_random` (matched-neutral lesion).  Design and predictions:
`iclr_latex_v3/SCHEMA_PAIR_GENERALIZATION_PREREGISTRATION_V1.md`.

Aggregate metrics only; no person-level value, row, identifier, or
row-level prediction is written.
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

os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["NVIDIA_VISIBLE_DEVICES"] = "none"

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "scripts/crta_v3_m3_nhkn2hrs_runtime_v1.py"
RUNTIME_MAP = ROOT / (
    "iclr_latex_v3/method_contract/v1/compiler/"
    "runtime_schema_maps_m3_nhkn_hrs_v1.json")
PRIV = Path("data/private/crta_v3/m3_inputs_v1")
SOURCE_PARQUET = PRIV / "nhkn_canonical_source_v1.parquet"
HRS_SNAPSHOT = PRIV / "hrs_v1_concept_transfer_snapshot.parquet"
ARMS = ("free", "sign_documented", "sign_flipped", "sign_random")

# The frozen nh/kn documented sign table, restricted to M3's endpoints and
# to features present in M3's Base (identical clinical variables, so the
# knowledge transfers verbatim; pairs whose partner is leakage-blocked for
# an endpoint are dropped automatically below).
DOCUMENTED_SIGNS: dict[str, dict[str, int]] = {
    "sbp": {"age": 1, "dbp": 1},
    "dbp": {"sbp": 1},
    "glucose": {"hba1c": 1},
    "hba1c": {"glucose": 1},
    "total_cholesterol": {"triglycerides": 1},
    "hemoglobin": {"hematocrit": 1, "rbc": 1},
    "hematocrit": {"hemoglobin": 1, "rbc": 1},
    "rbc": {"hemoglobin": 1, "hematocrit": 1},
    "creatinine": {"bun": 1},
    "bun": {"creatinine": 1},
}


def derived_rng(key: str) -> np.random.Generator:
    return np.random.default_rng(int(hashlib.sha256(key.encode()).hexdigest()[:16], 16))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--endpoints", nargs="*", default=None)
    parser.add_argument("--seeds", nargs="*", type=int, default=None)
    parser.add_argument("--n-jobs", type=int, default=2)
    args = parser.parse_args()

    rt = _load("crta_v3_m3_runtime_for_probe", RUNTIME)
    from xgboost import XGBRegressor
    runtime_map = json.loads(RUNTIME_MAP.read_text(encoding="utf-8"))
    source_all = rt.load_source_adapter(SOURCE_PARQUET)
    target_all = rt.load_target_snapshot(
        HRS_SNAPSHOT, runtime_map["target"].values())

    endpoints = args.endpoints or [e for e in rt.ENDPOINTS if e in DOCUMENTED_SIGNS]
    seeds = args.seeds or list(rt.SEEDS)
    args.out_root.mkdir(parents=True, exist_ok=True)

    for endpoint in endpoints:
        features = list(rt.base_features(endpoint))
        signs_doc = [0] * len(features)
        signs_flip = [0] * len(features)
        used = []
        for feature, sign in DOCUMENTED_SIGNS.get(endpoint, {}).items():
            column = f"slot__{feature}"
            if column in features:
                index = features.index(column)
                signs_doc[index] = int(sign)
                signs_flip[index] = -int(sign)
                used.append(feature)
        if not used:
            print(json.dumps({"endpoint": endpoint,
                              "skipped": "no documented feature survives Base"}),
                  flush=True)
            continue

        for fraction in rt.SUPPORT_FRACTIONS:
            for seed in seeds:
                tag = f"support_{fraction:.2f}".replace(".", "p")
                cell = args.out_root / endpoint / tag / f"seed_{seed}"
                if (cell / "metrics.json").is_file():
                    continue
                t0 = time.time()

                source = rt.select_source_cap(source_all, endpoint, seed, None)
                target, support_mask, query_mask = rt.make_target_split(
                    target_all, endpoint, seed, fraction)
                source_base = rt.numeric_matrix(source, features)
                target_base = rt.numeric_matrix(target, features)
                column = rt.TARGET_COLUMN[endpoint]
                source_y = np.asarray(source[column], dtype=np.float64)
                target_y = np.asarray(target[column], dtype=np.float64)
                width = rt.INTERFACE_WIDTH
                n_support = int(support_mask.sum())
                x_train = np.vstack([
                    np.column_stack([
                        source_base,
                        np.zeros((len(source), width), dtype=np.float32)]),
                    np.column_stack([
                        target_base[support_mask],
                        np.zeros((n_support, width), dtype=np.float32)]),
                ])
                y_train = np.concatenate([source_y, target_y[support_mask]])
                weights = np.concatenate([
                    np.ones(len(source)),
                    np.full(n_support, rt.TARGET_WEIGHT)])
                x_query = np.column_stack([
                    target_base[query_mask],
                    np.zeros((int(query_mask.sum()), width), dtype=np.float32)])
                query_y = target_y[query_mask]

                rng = derived_rng(f"m3_sign_probe_v1|{endpoint}|{fraction}|{seed}")
                signs_random = [0] * len(features)
                for k in rng.choice(len(features), size=len(used), replace=False):
                    signs_random[int(k)] = int(rng.choice([-1, 1]))
                # The interface block is all-zero; constraints there are 0.
                pad = [0] * width
                arm_constraints = {
                    "free": None,
                    "sign_documented": tuple(signs_doc + pad),
                    "sign_flipped": tuple(signs_flip + pad),
                    "sign_random": tuple(signs_random + pad),
                }

                metrics: dict[str, dict] = {}
                for arm in ARMS:
                    constraints = arm_constraints[arm]
                    if constraints is None:
                        prediction = rt.fit_predict_cpu(
                            x_train, y_train, weights, x_query, seed,
                            args.n_jobs)
                    else:
                        # The runtime's fit_predict_cpu takes no constraint
                        # argument; replicate its frozen estimator exactly and
                        # add only monotone_constraints.
                        spec = rt.FROZEN_ESTIMATOR
                        model = XGBRegressor(
                            objective="reg:squarederror",
                            n_estimators=spec.n_estimators,
                            max_depth=spec.max_depth,
                            learning_rate=spec.learning_rate,
                            min_child_weight=spec.min_child_weight,
                            subsample=spec.subsample,
                            colsample_bytree=spec.colsample_bytree,
                            reg_lambda=spec.reg_lambda,
                            random_state=seed, n_jobs=args.n_jobs,
                            tree_method="hist", verbosity=0,
                            monotone_constraints=constraints,
                        )
                        model.fit(x_train, y_train, sample_weight=weights)
                        prediction = np.asarray(
                            model.predict(x_query), dtype=np.float64)
                    metrics[arm] = rt.regression_metrics(query_y, prediction)

                cell.mkdir(parents=True, exist_ok=True)
                (cell / "metrics.json").write_text(json.dumps({
                    "endpoint": endpoint, "support_fraction": fraction,
                    "seed": seed, "task": "M3_nhkn2hrs",
                    "constrained_features": used,
                    "n_source": int(len(source)), "n_support": n_support,
                    "n_query": int(query_mask.sum()),
                    "arms": metrics,
                    "wall_seconds": round(time.time() - t0, 1),
                }, indent=1, sort_keys=True) + "\n", encoding="utf-8")
                print(json.dumps({"endpoint": endpoint, "fraction": fraction,
                                  "seed": seed,
                                  "wall_seconds": round(time.time() - t0, 1),
                                  "done": True}), flush=True)

    print(json.dumps({"status": "complete"}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
