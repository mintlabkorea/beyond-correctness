#!/usr/bin/env python3
"""Run basin-safe Base/Auto-C/Auto-R/Auto-Full CAMELS development screens."""

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
from xgboost import XGBRegressor


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "iclr_latex_v3/method_contract/v1"
DATA_ROOT = ROOT / "experiments/crta_v3_camels_native_screen_v1/data"
OUT_ROOT = ROOT / "experiments/crta_v3_camels_native_screen_v1/results"
PAYLOAD_PATH = CONTRACT / "payloads/camels_us_to_gb_native_v1/proposer_input.json"
DSL_PATH = CONTRACT / "dsl/dsl_v1.json"
BANK_PATH = (
    CONTRACT
    / "runs/proposer_bank_camels_v1/models/gpt-5.6-sol/"
    "camels_us_to_gb_native_v1_attempt_02/decision_ledger.json"
)
RANDOM_ROOT = (
    CONTRACT
    / "runs/control_banks_camels_v1/capacity_matched_random/"
    "camels_us_to_gb_native_v1"
)
ARMS = (
    "target_only",
    "base",
    "auto_concept",
    "auto_relation",
    "auto_full",
    "random_concept",
    "random_full",
    "wrong_auto_binding_concept",
    "wrong_auto_binding_full",
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


COMPILER = load_module("crta_camels_compile_bank", CONTRACT / "compiler/compile_bank.py")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--support-basins", type=int, choices=[1, 3, 5], required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--arms", nargs="+", choices=ARMS, default=list(ARMS))
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    parser.add_argument("--out-root", type=Path, default=OUT_ROOT)
    parser.add_argument("--n-jobs", type=int, default=8)
    parser.add_argument("--target-weight", type=float, default=10.0)
    parser.add_argument("--payload-path", type=Path, default=PAYLOAD_PATH)
    parser.add_argument("--dsl-path", type=Path, default=DSL_PATH)
    parser.add_argument("--bank-path", type=Path, default=BANK_PATH)
    parser.add_argument("--experiment-id", default="crta_v3_camels_native_screen_v1")
    parser.add_argument(
        "--evaluation-role",
        choices=["development_screen", "confirmatory", "task_benchmark", "cross_model_extension"],
        default="development_screen",
    )
    parser.add_argument("--skip-existing", action="store_true")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frame_sha256(frame: pd.DataFrame, columns: list[str]) -> str:
    values = pd.util.hash_pandas_object(frame[columns], index=False).to_numpy(np.uint64)
    digest = hashlib.sha256()
    digest.update(json.dumps(columns).encode("utf-8"))
    digest.update(values.tobytes())
    return digest.hexdigest()


def support_order(ids: list[str], seed: int) -> list[str]:
    return sorted(
        ids,
        key=lambda gauge: hashlib.sha256(
            f"crta-camels-support-v1|{seed}|{gauge}".encode("utf-8")
        ).hexdigest(),
    )


def eligible_ids(payload: dict[str, Any], side: str) -> list[str]:
    table = next(table for table in payload["tables"] if table["table_id"] == side)
    return [column["column_id"] for column in table["columns"] if column["candidate_eligible"]]


def robust_channels(
    frame: pd.DataFrame, fit_mask: np.ndarray, feature_names: list[str]
) -> tuple[np.ndarray, list[dict[str, Any]]]:
    output = np.zeros((len(frame), len(feature_names) * 2 + 4), dtype=np.float32)
    records: list[dict[str, Any]] = []
    for index, name in enumerate(feature_names):
        raw = (
            pd.to_numeric(frame[name], errors="coerce").to_numpy(np.float64)
            if name in frame
            else np.full(len(frame), np.nan, dtype=np.float64)
        )
        support = raw[fit_mask]
        support = support[np.isfinite(support)]
        if len(support):
            center = float(np.median(support))
            q25, q75 = np.quantile(support, [0.25, 0.75])
            scale = float(q75 - q25)
            if not np.isfinite(scale) or scale <= 1.0e-8:
                scale = float(np.std(support))
            if not np.isfinite(scale) or scale <= 1.0e-8:
                scale = 1.0
        else:
            center, scale = 0.0, 1.0
        observed = np.isfinite(raw)
        value = np.zeros(len(frame), dtype=np.float32)
        value[observed] = np.clip((raw[observed] - center) / scale, -10.0, 10.0)
        output[:, index * 2] = value
        output[:, index * 2 + 1] = observed.astype(np.float32)
        records.append(
            {
                "feature": name,
                "center": center,
                "scale": scale,
                "fit_observations": int(len(support)),
            }
        )
    date = pd.to_datetime(frame["date"])
    radians = 2.0 * np.pi * (date.dt.dayofyear.to_numpy(np.float64) - 1.0) / 365.25
    offset = len(feature_names) * 2
    output[:, offset] = np.sin(radians)
    output[:, offset + 1] = np.cos(radians)
    output[:, offset + 2] = np.sin(2.0 * radians)
    output[:, offset + 3] = np.cos(2.0 * radians)
    return output, records


def metrics(frame: pd.DataFrame, prediction_mm_day: np.ndarray) -> dict[str, float]:
    y = frame["discharge_mm_day"].to_numpy(np.float64)
    log_y = np.log1p(y)
    log_prediction = np.log1p(prediction_mm_day)
    basin_nse: list[float] = []
    for _, positions in frame.groupby("gauge_id", sort=True).indices.items():
        indices = np.asarray(positions, dtype=np.int64)
        denominator = float(np.square(y[indices] - y[indices].mean()).sum())
        if denominator > 0:
            basin_nse.append(
                1.0
                - float(np.square(y[indices] - prediction_mm_day[indices]).sum())
                / denominator
            )
    return {
        "log1p_rmse": float(np.sqrt(np.mean(np.square(log_y - log_prediction)))),
        "rmse_mm_day": float(np.sqrt(np.mean(np.square(y - prediction_mm_day)))),
        "mae_mm_day": float(np.mean(np.abs(y - prediction_mm_day))),
        "mean_basin_nse": float(np.mean(basin_nse)),
        "median_basin_nse": float(np.median(basin_nse)),
    }


def main() -> int:
    args = parse_args()
    started = time.perf_counter()
    source_path = args.data_root / "source.pkl"
    target_path = args.data_root / "target.pkl"
    split_path = args.data_root / "split_manifest.json"
    source = pd.read_pickle(source_path).reset_index(drop=True)
    target = pd.read_pickle(target_path).reset_index(drop=True)
    split = load_json(split_path)
    support_ids = support_order(split["target_support_pool_basin_ids"], args.seed)[
        : args.support_basins
    ]
    query_ids = split["target_query_basin_ids"]
    target = target[target["gauge_id"].isin([*support_ids, *query_ids])].reset_index(drop=True)
    support_mask = target["gauge_id"].isin(support_ids).to_numpy()
    query_mask = target["gauge_id"].isin(query_ids).to_numpy()
    if set(target.loc[support_mask, "gauge_id"]) & set(target.loc[query_mask, "gauge_id"]):
        raise ValueError("Support/query basin leakage")
    source_fit = np.ones(len(source), dtype=bool)

    payload = load_json(args.payload_path)
    dsl = load_json(args.dsl_path)
    ledger = load_json(args.bank_path)
    accepted_bank = ledger["accepted_bank"]
    random_bank_path = RANDOM_ROOT / f"seed_{args.seed}/decision_ledger.json"
    random_arms = {
        "random_concept",
        "random_full",
        "wrong_auto_binding_concept",
        "wrong_auto_binding_full",
    }
    needs_random_bank = any(arm in random_arms for arm in args.arms)
    random_bank = (
        load_json(random_bank_path)["accepted_bank"] if needs_random_bank else None
    )
    source_ids = eligible_ids(payload, "source")
    target_ids = eligible_ids(payload, "target")
    derived = sorted(
        {
            column
            for frame in (source, target)
            for column in frame.columns
            if "__trailmean_" in column
        }
    )
    base_features = sorted(set(source_ids) | set(target_ids) | set(derived))
    source_base, source_base_fit = robust_channels(source, source_fit, base_features)
    target_base, target_base_fit = robust_channels(target, support_mask, base_features)
    source_y = np.log1p(source["discharge_mm_day"].to_numpy(np.float64))
    target_y = np.log1p(target["discharge_mm_day"].to_numpy(np.float64))

    for arm in args.arms:
        output = (
            args.out_root
            / f"support_{args.support_basins}"
            / f"seed_{args.seed}"
            / arm
        )
        if args.skip_existing and (output / "summary.json").exists():
            print(json.dumps({"status": "skip", "output": str(output)}), flush=True)
            continue
        compiler_arm = {
            "target_only": "base",
            "base": "base",
            "auto_concept": "concept",
            "auto_relation": "relation",
            "auto_full": "full",
            "random_concept": "concept",
            "random_full": "full",
            "wrong_auto_binding_concept": "concept",
            "wrong_auto_binding_full": "full",
        }[arm]
        source_bank = (
            random_bank if arm in {"random_concept", "random_full"} else accepted_bank
        )
        target_bank = (
            random_bank
            if arm in random_arms
            else accepted_bank
        )
        if source_bank is None or target_bank is None:
            raise ValueError(f"Random bank is required for arm {arm}")
        source_compiled = COMPILER.compile_bank(
            source,
            source_fit,
            source_bank,
            payload,
            dsl,
            side="source",
            arm=compiler_arm,
        )
        target_compiled = COMPILER.compile_bank(
            target,
            support_mask,
            target_bank,
            payload,
            dsl,
            side="target",
            arm=compiler_arm,
        )
        source_design = np.column_stack([source_base, source_compiled.values])
        target_design = np.column_stack([target_base, target_compiled.values])
        if arm == "target_only":
            train_x = target_design[support_mask]
            train_y = target_y[support_mask]
            weights = np.ones(len(train_y), dtype=np.float64)
            source_rows_used = 0
        else:
            train_x = np.vstack([source_design, target_design[support_mask]])
            train_y = np.concatenate([source_y, target_y[support_mask]])
            weights = np.concatenate(
                [
                    np.ones(len(source_y), dtype=np.float64),
                    np.full(int(support_mask.sum()), args.target_weight, dtype=np.float64),
                ]
            )
            source_rows_used = len(source_y)
        model = XGBRegressor(
            objective="reg:squarederror",
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            min_child_weight=5.0,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_lambda=1.0,
            random_state=args.seed,
            n_jobs=args.n_jobs,
            tree_method="hist",
        )
        model.fit(train_x, train_y, sample_weight=weights)
        prediction_log = model.predict(target_design[query_mask]).astype(np.float64)
        prediction = np.maximum(np.expm1(prediction_log), 0.0)
        query_frame = target.loc[query_mask, ["gauge_id", "date", "discharge_mm_day"]].copy()
        query_frame["prediction_mm_day"] = prediction
        result_metrics = metrics(query_frame, prediction)

        output.mkdir(parents=True, exist_ok=True)
        query_frame.to_csv(output / "predictions.csv", index=False)
        compiler_manifest = {
            "source": source_compiled.metadata,
            "target": target_compiled.metadata,
            "base_features": base_features,
            "source_base_fit": source_base_fit,
            "target_base_fit": target_base_fit,
        }
        (output / "compiler_manifest.json").write_text(
            json.dumps(compiler_manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        summary = {
            "experiment": args.experiment_id,
            "evaluation_role": args.evaluation_role,
            "direction": "camels_us_to_camels_gb_v2_native",
            "target": "daily_specific_discharge_mm_day",
            "split_unit": "gauge_id",
            "support_basin_count": args.support_basins,
            "support_basin_ids": support_ids,
            "query_basin_ids": query_ids,
            "source_train_sha256": frame_sha256(source, ["gauge_id", "date"]),
            "target_support_sha256": frame_sha256(
                target.loc[support_mask], ["gauge_id", "date"]
            ),
            "query_sha256": frame_sha256(
                target.loc[query_mask], ["gauge_id", "date"]
            ),
            "query_y_sha256": frame_sha256(
                target.loc[query_mask], ["gauge_id", "date", "discharge_mm_day"]
            ),
            "seed": args.seed,
            "arm": arm,
            "metrics": result_metrics,
            "source_rows_used": source_rows_used,
            "target_support_rows": int(support_mask.sum()),
            "target_query_rows": int(query_mask.sum()),
            "base_feature_width": int(source_base.shape[1]),
            "bank_interface_width": int(source_compiled.values.shape[1]),
            "target_weight": args.target_weight,
            "estimator": {
                "name": "XGBRegressor",
                "n_estimators": 300,
                "max_depth": 6,
                "learning_rate": 0.05,
                "min_child_weight": 5.0,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "n_jobs": args.n_jobs,
            },
            "payload": str(args.payload_path),
            "payload_sha256": sha256(args.payload_path),
            "bank": str(args.bank_path) if arm != "base" else None,
            "bank_sha256": sha256(args.bank_path) if arm != "base" else None,
            "source_bank": (
                None
                if arm == "base"
                else str(random_bank_path)
                if arm in {"random_concept", "random_full"}
                else str(args.bank_path)
            ),
            "target_bank": (
                None
                if arm == "base"
                else str(random_bank_path)
                if arm in random_arms
                else str(args.bank_path)
            ),
            "random_control_bank_sha256": (
                sha256(random_bank_path)
                if arm
                in {
                    "random_concept",
                    "random_full",
                    "wrong_auto_binding_concept",
                    "wrong_auto_binding_full",
                }
                else None
            ),
            "control_definition": (
                "capacity_matched_random_both_sides"
                if arm in {"random_concept", "random_full"}
                else "source_auto_target_capacity_matched_random"
                if arm
                in {"wrong_auto_binding_concept", "wrong_auto_binding_full"}
                else None
            ),
            "dsl": str(args.dsl_path),
            "dsl_sha256": sha256(args.dsl_path),
            "source_data_sha256": sha256(source_path),
            "target_data_sha256": sha256(target_path),
            "split_manifest_sha256": sha256(split_path),
            "predictions_sha256": sha256(output / "predictions.csv"),
            "runtime_seconds_from_start": time.perf_counter() - started,
        }
        (output / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
