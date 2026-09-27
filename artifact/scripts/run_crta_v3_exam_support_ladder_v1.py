#!/usr/bin/env python3
"""Examination correspondence utility across labeled target support.

Protocol: experiments/crta_v3_exam_support_ladder_v1/PROTOCOL_V1.md.

Sweeps K in {64, 256, 1024} over the frozen thirteen-endpoint examination
panel with the three frozen arms only.  Everything else -- cells, splits,
seeds, columns, learner, weights, support-draw convention -- is taken
verbatim from `run_crta_v3_exam_reference_sensitivity_v2.py`, so the K=256
rung must reproduce the published per-cell nRMSE bit-identically.
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
V2_RUNNER = ROOT / "scripts/run_crta_v3_exam_reference_sensitivity_v2.py"
DEFAULT_OUT = ROOT / "experiments/crta_v3_exam_support_ladder_v1"
PROTOCOL = DEFAULT_OUT / "PROTOCOL_V1.md"

# Protocol: the three frozen arms and only those.  The alternative
# references are excluded so that no reference can be selected afterwards.
ARMS = ("S_shared_bridge", "W_deranged_bridge", "R_domain_local")
SUPPORT_LADDER = (64, 256, 1024)
PRIMARY_K = 256
TARGET_SET = "objective_broader_validation_targets_v2"
PANEL = {
    "A": ("glucose", "waist_cm", "triglycerides", "sbp", "dbp",
          "total_cholesterol"),
    "B": ("alt", "bun"),
    "C": ("creatinine", "hemoglobin", "hematocrit", "rbc", "wbc"),
}
ALL_TARGETS = tuple(t for group in ("A", "B", "C") for t in PANEL[group])
CLASS_OF = {t: g for g, ts in PANEL.items() for t in ts}
# Protocol: the pre-existing pool rule at the largest rung of the ladder.
MIN_POOL = 4 * max(SUPPORT_LADDER)
# Protocol diagnostic: at K=64 a support row carries weight n_source/K = 348
# to 939 against min_child_weight=1, so one target row can found a leaf, and
# the exposure is asymmetric between the shared and the target-local column.
# This forces at least eight distinct target rows behind any target-only
# leaf at every rung and changes nothing else.  Class A only, and
# non-verdict-bearing.
DIAGNOSTIC_MCW_ROWS = 8.0
DIAGNOSTIC_CLASSES = ("A",)


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nhanes-parquet", type=Path, required=True)
    parser.add_argument("--knhanes-parquet", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--targets", nargs="*", default=None)
    parser.add_argument("--seeds", nargs="*", type=int, default=None)
    parser.add_argument("--support-rows", nargs="*", type=int,
                        default=list(SUPPORT_LADDER))
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--no-diagnostic", action="store_true",
                        help="skip the class-A min_child_weight diagnostic ladder")
    args = parser.parse_args()

    base = load_module("exam_ladder_base", BASE_RUNNER)
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
        "v2_runner_sha256": sha256_file(V2_RUNNER),
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
        "crta_bench_exam_ladder", base.BENCH / "scripts/build_benchmark_table.py")
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
            target_set_override=TARGET_SET,
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

    targets = args.targets or list(ALL_TARGETS)
    seeds = args.seeds or list(base.SEEDS)
    ladder = [int(k) for k in args.support_rows]
    run_diagnostic = not args.no_diagnostic
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
            if n_pool < MIN_POOL:
                raise RuntimeError(
                    f"{target}: pool {n_pool} below the frozen floor {MIN_POOL}")
            y_test = bundle["y_test"]
            query_sd = float(np.std(y_test, ddof=0))

            members = [slot for slot in base.MEMBER_SLOTS if slot != target]
            permutation = base.member_permutation(members, target, seed)
            base_slots_used = [s for s in base.BASE_SLOTS if s != target]

            scores: dict[str, dict[str, float]] = {}
            diagnostic: dict[str, dict[str, dict[str, float]]] = {}
            min_child_weights: dict[str, float] = {}
            shapes: dict[str, list[int]] = {}
            supports: dict[str, int] = {}

            for support_k in ladder:
                # Frozen convention: the generator is seeded with K, so the
                # rungs are independent draws rather than nested subsets.
                pick = np.sort(np.random.default_rng(seed * 131 + support_k).choice(
                    n_pool, size=min(support_k, n_pool), replace=False))
                support_rows = np.arange(n_source, n_train)[pick]
                fit_rows = np.concatenate([np.arange(n_source), support_rows])
                y_fit = bundle["y_train"][fit_rows]
                # Frozen convention: the target block's total weight is
                # n_source at every K, so K varies the number of distinct
                # labeled target rows at fixed aggregate target influence.
                weights = np.concatenate([
                    np.ones(n_source),
                    np.full(len(support_rows),
                            n_source / max(len(support_rows), 1))])
                supports[str(support_k)] = int(len(support_rows))

                def shared_block(source_slot: str, target_slot: str):
                    source = bundle["slots"][source_slot][0][:n_source]
                    target_side = bundle["slots"][target_slot][0][support_rows]
                    query = bundle["slots"][target_slot][1]
                    return np.concatenate([source, target_side]), query

                base_fit, base_query = [], []
                for slot in base_slots_used:
                    fit, query = shared_block(slot, slot)
                    base_fit.append(fit)
                    base_query.append(query)

                arm_parts = {arm: (list(base_fit), list(base_query))
                             for arm in ARMS}
                for slot in members:
                    correct_fit, correct_query = shared_block(slot, slot)
                    wrong_fit, wrong_query = shared_block(slot, permutation[slot])
                    missing_fit = np.full(len(correct_fit), np.nan)
                    missing_query = np.full(len(correct_query), np.nan)

                    arm_parts["S_shared_bridge"][0].extend(
                        [correct_fit, missing_fit])
                    arm_parts["S_shared_bridge"][1].extend(
                        [correct_query, missing_query])
                    arm_parts["W_deranged_bridge"][0].extend(
                        [wrong_fit, missing_fit])
                    arm_parts["W_deranged_bridge"][1].extend(
                        [wrong_query, missing_query])

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

                # Frozen config first, so its fits are unaffected by the
                # diagnostic existing at all.
                configs = {"primary": None}
                if CLASS_OF.get(target) in DIAGNOSTIC_CLASSES and run_diagnostic:
                    configs["diag_mcw"] = (
                        DIAGNOSTIC_MCW_ROWS * n_source / support_k)

                for config, min_child_weight in configs.items():
                    cell_scores = {}
                    for arm in ARMS:
                        x_fit = np.column_stack(arm_parts[arm][0])
                        x_query = np.column_stack(arm_parts[arm][1])
                        member_block = x_fit[:, len(base_slots_used):]
                        if not np.all(
                                np.isfinite(member_block).sum(1) <= len(members)):
                            raise RuntimeError(
                                f"{arm} duplicates observed member values")
                        extra = ({} if min_child_weight is None
                                 else {"min_child_weight": min_child_weight})
                        model = XGBRegressor(
                            n_estimators=300, max_depth=6, learning_rate=0.05,
                            subsample=0.8, colsample_bytree=1.0, reg_lambda=1.0,
                            n_jobs=args.threads, random_state=seed,
                            tree_method="hist", **extra)
                        model.fit(x_fit, y_fit, sample_weight=weights)
                        prediction = model.predict(x_query)
                        cell_scores[arm] = float(
                            np.sqrt(np.mean((y_test - prediction) ** 2))
                            / query_sd)
                        if config == "primary":
                            shapes[f"{support_k}:{arm}"] = [
                                int(x_fit.shape[0]), int(x_fit.shape[1])]
                    if config == "primary":
                        scores[str(support_k)] = cell_scores
                    else:
                        diagnostic.setdefault(config, {})[str(support_k)] = \
                            cell_scores
                        min_child_weights[str(support_k)] = min_child_weight

            out.mkdir(parents=True, exist_ok=True)
            (out / "metrics.json").write_text(json.dumps({
                "task": "crta_v3_exam_support_ladder_v1",
                "target": target, "target_class": CLASS_OF.get(target, "?"),
                "target_set": TARGET_SET, "min_pool_floor": MIN_POOL,
                "base_slots_used": base_slots_used,
                "seed": seed, "support_ladder": ladder,
                "primary_k": PRIMARY_K, "support_rows_drawn": supports,
                "metric": "query_sd_normalized_rmse (lower is better)",
                "arms": list(ARMS),
                "n_source": n_source, "n_pool": n_pool,
                "n_query": int(len(y_test)), "member_slots": members,
                "target_derangement": permutation,
                "matrix_shapes": shapes,
                "xgb": {"n_estimators": 300, "max_depth": 6,
                        "learning_rate": 0.05, "subsample": 0.8,
                        "colsample_bytree": 1.0, "reg_lambda": 1.0,
                        "threads": args.threads},
                "nrmse": scores,
                "nrmse_diagnostic": diagnostic,
                "diagnostic_min_child_weight": min_child_weights,
                "diagnostic_min_child_weight_rows": DIAGNOSTIC_MCW_ROWS,
                "diagnostic_classes": list(DIAGNOSTIC_CLASSES),
                "wall_seconds": round(time.time() - started, 1),
                **provenance,
            }, indent=1, sort_keys=True) + "\n", encoding="utf-8")
            print(json.dumps({"target": target, "seed": seed,
                              "wall_seconds": round(time.time() - started, 1),
                              "scores": scores}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
