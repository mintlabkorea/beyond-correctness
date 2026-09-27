#!/usr/bin/env python3
"""Examination reference-construction sensitivity: two alternative no-bridge
references beside the frozen one.

Protocol: experiments/crta_v3_exam_reference_sensitivity_v1/PROTOCOL_V1.md.
Reuses the frozen three-arm runner's cells, splits, seeds, and learner and
adds `R_domain_offset` (R2: disjoint-range single column, no induced
missingness) and `S_unpadded`/`W_unpadded` (R3: padding control).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE_RUNNER = ROOT / "scripts/run_crta_v3_m1m2_layer_ladder_v1.py"
FROZEN_RUNNER = ROOT / "scripts/run_crta_v3_exam_no_bridge_reference_v1.py"
DEFAULT_OUT = ROOT / "experiments/crta_v3_exam_reference_sensitivity_v1"
PROTOCOL = DEFAULT_OUT / "PROTOCOL_V1.md"

FROZEN_ARMS = ("S_shared_bridge", "W_deranged_bridge", "R_domain_local")
NEW_ARMS = ("R_domain_offset", "S_unpadded", "W_unpadded")
ARMS = FROZEN_ARMS + NEW_ARMS
PRIMARY_K = 256
OFFSET_MULTIPLIER = 10.0  # protocol: offset = 10 * (fit max - fit min + 1)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    import hashlib
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def offset_source(source_values: np.ndarray, target_fit: np.ndarray,
                  target_query: np.ndarray, slot: str) -> tuple[np.ndarray, float]:
    """Shift source values into a range disjoint from every target value.

    The offset is computed from the fit frame only and never consults a
    label.  Disjointness is then asserted against the query as well; a
    violation aborts rather than being patched (protocol section on R2).
    """
    fit_all = np.concatenate([source_values, target_fit])
    finite = fit_all[np.isfinite(fit_all)]
    if finite.size == 0:
        return source_values.copy(), 0.0
    offset = OFFSET_MULTIPLIER * (float(np.max(finite)) - float(np.min(finite)) + 1.0)
    shifted = source_values + offset
    target_all = np.concatenate([target_fit, target_query])
    target_finite = target_all[np.isfinite(target_all)]
    shifted_finite = shifted[np.isfinite(shifted)]
    if shifted_finite.size and target_finite.size:
        if not float(np.min(shifted_finite)) > float(np.max(target_finite)):
            raise RuntimeError(
                f"{slot}: offset source range is not disjoint from the target "
                f"range (min shifted {np.min(shifted_finite)} <= max target "
                f"{np.max(target_finite)})")
    return shifted, offset


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nhanes-parquet", type=Path, required=True)
    parser.add_argument("--knhanes-parquet", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--targets", nargs="*", default=None)
    parser.add_argument("--seeds", nargs="*", type=int, default=None)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()

    base = load_module("exam_sens_base", BASE_RUNNER)
    for key, path in (("nhanes", args.nhanes_parquet),
                      ("knhanes", args.knhanes_parquet)):
        observed = base.sha256_file(path)
        if observed != base.EXPECTED[key]:
            raise RuntimeError(f"{key} parquet SHA-256 mismatch: {observed}")
    base.verify_bank()

    from xgboost import XGBRegressor
    import platform
    import sklearn
    import xgboost

    provenance = {
        "runner_sha256": sha256_file(Path(__file__)),
        "frozen_runner_sha256": sha256_file(FROZEN_RUNNER),
        "base_runner_sha256": sha256_file(BASE_RUNNER),
        "protocol_sha256": sha256_file(PROTOCOL),
        "versions": {"xgboost": xgboost.__version__,
                     "sklearn": sklearn.__version__,
                     "numpy": np.__version__, "pandas": pd.__version__,
                     "python": platform.python_version()},
        "host": platform.node(),
        "threads": args.threads,
    }

    sys.path.insert(0, str(base.BENCH / "scripts"))
    benchmark = load_module(
        "crta_bench_exam_sens", base.BENCH / "scripts/build_benchmark_table.py")
    original_load_yaml = benchmark.load_yaml
    manifest_path = Path(benchmark.DEFAULT_DATASET_MANIFEST).resolve()

    def load_yaml_patched(path):
        value = original_load_yaml(path)
        if Path(path).resolve() == manifest_path:
            value["datasets"]["nhanes"]["parquet"] = str(args.nhanes_parquet)
            value["datasets"]["knhanes"]["parquet"] = str(args.knhanes_parquet)
        if isinstance(value, dict) and "feature_sets" in value:
            value["feature_sets"][base.FEATURE_SET] = {
                "description": "no-bridge v1 source materialization",
                "feature_mode": "explicit_slots",
                "slots": list(base.ALL_SLOTS),
            }
        return value

    benchmark.load_yaml = load_yaml_patched
    benchmark.load_questionnaire_rule_index = lambda path=None: {}

    def build(target: str, seed: int) -> dict:
        bundle = benchmark.build_single_target_table(
            benchmark_id=base.BENCHMARK_ID, target_name=target,
            fewshot_frac=0.10, seed=seed,
            target_set_override="objective_anchor_targets_v1_safe",
            feature_set_override=base.FEATURE_SET)
        x_train = bundle["X_train"].reset_index(drop=True)
        x_test = bundle["X_test"].reset_index(drop=True)
        slots = {}
        for slot in base.ALL_SLOTS:
            if slot == target:
                continue
            column = f"slot__{slot}"
            slots[slot] = (
                pd.to_numeric(x_train[column], errors="coerce").to_numpy(np.float64),
                pd.to_numeric(x_test[column], errors="coerce").to_numpy(np.float64))
        origin = np.asarray(bundle["train_origin"], dtype=object)
        return {"slots": slots,
                "y_train": pd.to_numeric(bundle["y_train"], errors="coerce")
                .to_numpy(np.float64),
                "y_test": pd.to_numeric(bundle["y_test"], errors="coerce")
                .to_numpy(np.float64),
                "n_source": int(np.sum(origin == "source"))}

    targets = args.targets or list(base.TARGETS)
    seeds = args.seeds or list(base.SEEDS)
    args.out_root.mkdir(parents=True, exist_ok=True)
    print(json.dumps(provenance), flush=True)

    for target in targets:
        for seed in seeds:
            out = args.out_root / target / f"seed_{seed}"
            if (out / "metrics.json").is_file():
                existing = json.loads((out / "metrics.json").read_text())
                if any(existing.get(k) != provenance[k] for k in
                       ("runner_sha256", "protocol_sha256", "threads")):
                    raise RuntimeError(
                        f"{out}/metrics.json does not match current provenance; "
                        "archive that tree before resuming.")
                continue
            started = time.time()
            bundle = build(target, seed)
            n_source = bundle["n_source"]
            n_train = len(bundle["y_train"])
            n_pool = n_train - n_source
            pick = np.sort(np.random.default_rng(seed * 131 + PRIMARY_K).choice(
                n_pool, size=min(PRIMARY_K, n_pool), replace=False))
            support_rows = np.arange(n_source, n_train)[pick]
            fit_rows = np.concatenate([np.arange(n_source), support_rows])
            y_fit = bundle["y_train"][fit_rows]
            y_test = bundle["y_test"]
            query_sd = float(np.std(y_test, ddof=0))
            weights = np.concatenate([
                np.ones(n_source),
                np.full(len(support_rows), n_source / max(len(support_rows), 1))])

            members = [slot for slot in base.MEMBER_SLOTS if slot != target]
            permutation = base.member_permutation(members, target, seed)

            def shared_block(source_slot: str, target_slot: str):
                source = bundle["slots"][source_slot][0][:n_source]
                target = bundle["slots"][target_slot][0][support_rows]
                query = bundle["slots"][target_slot][1]
                return np.concatenate([source, target]), query

            base_fit, base_query = [], []
            for slot in base.BASE_SLOTS:
                fit, query = shared_block(slot, slot)
                base_fit.append(fit)
                base_query.append(query)

            arm_parts = {arm: (list(base_fit), list(base_query)) for arm in ARMS}
            offsets = {}
            for slot in members:
                correct_fit, correct_query = shared_block(slot, slot)
                wrong_fit, wrong_query = shared_block(slot, permutation[slot])
                missing_fit = np.full(len(correct_fit), np.nan)
                missing_query = np.full(len(correct_query), np.nan)

                # --- frozen arms, byte-for-byte the frozen construction ---
                arm_parts["S_shared_bridge"][0].extend([correct_fit, missing_fit])
                arm_parts["S_shared_bridge"][1].extend([correct_query, missing_query])
                arm_parts["W_deranged_bridge"][0].extend([wrong_fit, missing_fit])
                arm_parts["W_deranged_bridge"][1].extend([wrong_query, missing_query])

                source_values = bundle["slots"][slot][0][:n_source]
                target_values = bundle["slots"][slot][0][support_rows]
                target_query = bundle["slots"][slot][1]
                source_local_fit = np.concatenate([
                    source_values, np.full(len(support_rows), np.nan)])
                target_local_fit = np.concatenate([
                    np.full(n_source, np.nan), target_values])
                source_local_query = np.full(len(y_test), np.nan)
                arm_parts["R_domain_local"][0].extend(
                    [source_local_fit, target_local_fit])
                arm_parts["R_domain_local"][1].extend(
                    [source_local_query, target_query])

                # --- R2: one column, source shifted into a disjoint range ---
                shifted, offset = offset_source(
                    source_values, target_values, target_query, slot)
                offsets[slot] = offset
                arm_parts["R_domain_offset"][0].extend(
                    [np.concatenate([shifted, target_values]), missing_fit])
                arm_parts["R_domain_offset"][1].extend(
                    [target_query, missing_query])

                # --- R3: the frozen shared arms without the inert pad ---
                arm_parts["S_unpadded"][0].append(correct_fit)
                arm_parts["S_unpadded"][1].append(correct_query)
                arm_parts["W_unpadded"][0].append(wrong_fit)
                arm_parts["W_unpadded"][1].append(wrong_query)

            scores, shapes = {}, {}
            for arm in ARMS:
                x_fit = np.column_stack(arm_parts[arm][0])
                x_query = np.column_stack(arm_parts[arm][1])
                member_block = x_fit[:, len(base.BASE_SLOTS):]
                if not np.all(np.isfinite(member_block).sum(1) <= len(members)):
                    raise RuntimeError(f"{arm} duplicates observed member values")
                model = XGBRegressor(
                    n_estimators=300, max_depth=6, learning_rate=0.05,
                    subsample=0.8, colsample_bytree=1.0, reg_lambda=1.0,
                    n_jobs=args.threads, random_state=seed, tree_method="hist")
                model.fit(x_fit, y_fit, sample_weight=weights)
                prediction = model.predict(x_query)
                scores[arm] = float(
                    np.sqrt(np.mean((y_test - prediction) ** 2)) / query_sd)
                shapes[arm] = [int(x_fit.shape[0]), int(x_fit.shape[1])]

            out.mkdir(parents=True, exist_ok=True)
            (out / "metrics.json").write_text(json.dumps({
                "task": "crta_v3_exam_reference_sensitivity_v1",
                "target": target, "seed": seed, "support_rows": PRIMARY_K,
                "metric": "query_sd_normalized_rmse (lower is better)",
                "arms": list(ARMS), "frozen_arms": list(FROZEN_ARMS),
                "new_arms": list(NEW_ARMS),
                "n_source": n_source, "n_pool": n_pool,
                "n_query": int(len(y_test)), "member_slots": members,
                "target_derangement": permutation,
                "matrix_shapes": shapes, "offsets": offsets,
                "offset_multiplier": OFFSET_MULTIPLIER,
                "xgb": {"n_estimators": 300, "max_depth": 6,
                        "learning_rate": 0.05, "subsample": 0.8,
                        "colsample_bytree": 1.0, "reg_lambda": 1.0,
                        "threads": args.threads},
                "nrmse": scores,
                "wall_seconds": round(time.time() - started, 1),
                **provenance,
            }, indent=1, sort_keys=True) + "\n", encoding="utf-8")
            print(json.dumps({"target": target, "seed": seed,
                              "wall_seconds": round(time.time() - started, 1),
                              "scores": scores}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
