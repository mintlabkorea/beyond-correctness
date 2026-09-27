#!/usr/bin/env python3
"""Survey-label measurement panel: the conflict sits on the training labels.

Frozen design and verdicts:
`iclr_latex_v3/M1M2_SURVEY_LABEL_MEASUREMENT_PANEL_PREREGISTRATION_V1.md`.
Features are the default pipeline-harmonized benchmark surface, identical in
every arm; only the training-label mapping varies (raw / pipeline_table /
llm_table / placebo_table).  Targets are injected survey endpoints carrying
raw codes.  Metric: AUROC on target queries against the fixed
codebook-documented target-side binary (higher is better).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
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
FEATURE_SET = "shared_clinical_plus_survey_v1"
TARGET_SET = "survey_label_panel_v1"  # injected at load time
SEEDS = tuple(range(50, 60))
SUPPORT_ROWS = (64, 256, 1024)
PRIMARY_K = 256
ARMS = ("raw", "pipeline_table", "llm_table", "placebo_table")

# target -> (nhanes raw column, knhanes raw column)
TARGETS: dict[str, tuple[str, str]] = {
    "diabetes_history": ("DIQ010", "ALL__de1_dg"),
    "hypertension_history": ("BPQ020", "ALL__di1_dg"),
    "current_smoking_status": ("SMQ040", "ALL__bs3_1"),
}

# Transcribed operative pipeline rules (recode_questionnaire_series).
PIPELINE_LABEL_MAPS: dict[str, dict[str, dict[float, float]]] = {
    "diabetes_history": {
        "source": {1: 1, 2: 0}, "target": {1: 1, 0: 0},
    },
    "hypertension_history": {
        "source": {1: 1, 2: 0}, "target": {1: 1, 0: 0},
    },
    "current_smoking_status": {
        "source": {1: 1, 2: 1, 3: 0}, "target": {1: 1, 2: 1, 3: 0, 4: 0},
    },
}

# Fixed evaluation label: codebook-documented target-side binary.
EVAL_LABEL_MAPS: dict[str, dict[float, float]] = {
    "diabetes_history": {1: 1, 0: 0},
    "hypertension_history": {1: 1, 0: 0},
    "current_smoking_status": {1: 1, 2: 1, 3: 0, 4: 0},
}

LLM_RESPONSE_DIR = (
    ROOT / "experiments/crta_v3_measurement_layer_v1/harmon_responses_v1"
)
LLM_SAMPLES = ("raw_documented_s1.txt", "raw_documented_s2.txt", "raw_documented_s3.txt")
# target -> (source item_id, target item_id)
LLM_ITEMS: dict[str, tuple[str, str]] = {
    "diabetes_history": ("NHANES::DIQ010", "KNHANES::ALL__de1_dg"),
    "hypertension_history": ("NHANES::BPQ020", "KNHANES::ALL__di1_dg"),
    "current_smoking_status": ("NHANES::SMQ040", "KNHANES::ALL__bs3_1"),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def derived_rng(key: str) -> np.random.Generator:
    return np.random.default_rng(int(hashlib.sha256(key.encode()).hexdigest()[:16], 16))


def load_llm_label_specs() -> dict[str, dict[str, dict]]:
    parsed = []
    for name in LLM_SAMPLES:
        text = (LLM_RESPONSE_DIR / name).read_text(encoding="utf-8")
        payload = json.loads(re.search(r"\{.*\}", text, re.S).group(0))
        parsed.append({item["item_id"]: item for item in payload["items"]})

    def majority(field: str, item_id: str):
        votes = [json.dumps(sample[item_id][field]) for sample in parsed]
        for vote in votes:
            if votes.count(vote) >= 2:
                return json.loads(vote)
        return json.loads(votes[0])

    specs: dict[str, dict[str, dict]] = {}
    for target, (src_item, tgt_item) in LLM_ITEMS.items():
        specs[target] = {}
        for side, item_id in (("source", src_item), ("target", tgt_item)):
            valid = sorted(float(v) for v in majority("valid_codes", item_id))
            reverse = bool(majority("requires_reverse_coding", item_id)) or (
                majority("ordinal_direction", item_id) == "higher_is_less"
            )
            lo, hi = min(valid), max(valid)
            mapping = {}
            for v in valid:
                oriented = (lo + hi - v) if reverse else v
                mapping[v] = (oriented - lo) / (hi - lo) if hi > lo else 0.0
            specs[target][side] = {
                "map": mapping,
                "valid": valid,
                "sentinel": sorted(
                    float(v) for v in majority("missing_or_sentinel_codes", item_id)),
                "reverse": reverse,
            }
    return specs


def make_placebo_label_maps(
    llm_specs: dict[str, dict[str, dict]], target: str, seed: int
) -> dict[str, dict[float, float]]:
    maps: dict[str, dict[float, float]] = {}
    for side, spec in llm_specs[target].items():
        rng = derived_rng(f"label_panel_v1|pl|{target}|{seed}|{side}")
        pool = sorted(set(spec["valid"]) | set(spec["sentinel"]))
        n_mask = len(spec["sentinel"])
        masked = set(
            rng.choice(np.asarray(pool), size=n_mask, replace=False).tolist()
        ) if n_mask else set()
        kept = [code for code in pool if code not in masked]
        outputs = list(rng.permutation(np.asarray(
            [spec["map"][v] for v in spec["valid"]])))
        if len(kept) != len(outputs):
            raise RuntimeError(f"placebo capacity mismatch: {target}/{side}")
        maps[side] = {float(c): float(v) for c, v in zip(kept, outputs)}
    return maps


def map_values(values: np.ndarray, mapping: dict[float, float] | None) -> np.ndarray:
    if mapping is None:
        return values.astype(np.float64)
    out = np.full(len(values), np.nan)
    for code, value in mapping.items():
        out[values == float(code)] = float(value)
    return out


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

    from sklearn.metrics import roc_auc_score
    from xgboost import XGBRegressor

    sys.path.insert(0, str(BENCH / "scripts"))
    benchmark = _load("crta_bench_panel", BENCH / "scripts/build_benchmark_table.py")
    original_load_yaml = benchmark.load_yaml
    manifest_path = Path(benchmark.DEFAULT_DATASET_MANIFEST).resolve()

    def load_yaml_patched(path):
        value = original_load_yaml(path)
        if Path(path).resolve() == manifest_path:
            value["datasets"]["nhanes"]["parquet"] = str(args.nhanes_parquet)
            value["datasets"]["knhanes"]["parquet"] = str(args.knhanes_parquet)
            for target, (nh_col, kn_col) in TARGETS.items():
                value.setdefault("targets", {})[target] = {
                    "label": target, "nhanes": nh_col, "knhanes": kn_col,
                }
        if isinstance(value, dict) and "target_sets" in value:
            value["target_sets"][TARGET_SET] = {
                "description": "injected survey-label panel v1",
                "targets": list(TARGETS),
            }
        return value

    benchmark.load_yaml = load_yaml_patched

    llm_specs = load_llm_label_specs()
    args.out_root.mkdir(parents=True, exist_ok=True)
    (args.out_root / "LLM_LABEL_TABLE_V1.json").write_text(json.dumps(
        llm_specs, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")

    for target in args.targets:
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
                raise RuntimeError(f"endpoint slot leaked into features: {target}")
            feat_cols = [c for c in x_train.columns if c.startswith("slot__")]
            x_all = x_train[feat_cols].apply(
                pd.to_numeric, errors="coerce").to_numpy(np.float64)
            x_q = x_test[feat_cols].apply(
                pd.to_numeric, errors="coerce").to_numpy(np.float64)
            y_raw_train = pd.to_numeric(
                bundle["y_train"], errors="coerce").to_numpy(np.float64)
            y_raw_test = pd.to_numeric(
                bundle["y_test"], errors="coerce").to_numpy(np.float64)
            origin = np.asarray(bundle["train_origin"], dtype=object)
            n_source = int(np.sum(origin == "source"))
            n_pool = len(x_all) - n_source

            y_eval = map_values(y_raw_test, EVAL_LABEL_MAPS[target])
            eval_mask = np.isfinite(y_eval)
            if len(np.unique(y_eval[eval_mask])) < 2:
                raise RuntimeError(f"degenerate eval label for {target}")

            placebo_maps = make_placebo_label_maps(llm_specs, target, seed)
            arm_label_maps: dict[str, dict[str, dict[float, float] | None]] = {
                "raw": {"source": None, "target": None},
                "pipeline_table": PIPELINE_LABEL_MAPS[target],
                "llm_table": {
                    side: llm_specs[target][side]["map"] for side in ("source", "target")
                },
                "placebo_table": placebo_maps,
            }

            results: dict = {}
            for K in args.support_rows:
                pick = np.sort(np.random.default_rng(seed * 131 + K).choice(
                    n_pool, size=min(K, n_pool), replace=False))
                sup_rows = np.arange(n_source, len(x_all))[pick]
                results[str(K)] = {}
                for arm in ARMS:
                    maps = arm_label_maps[arm]
                    y_src = map_values(y_raw_train[:n_source], maps["source"])
                    y_sup = map_values(y_raw_train[sup_rows], maps["target"])
                    src_keep = np.isfinite(y_src)
                    sup_keep = np.isfinite(y_sup)
                    if src_keep.sum() == 0 or sup_keep.sum() == 0:
                        results[str(K)][arm] = float("nan")
                        continue
                    x_fit = np.vstack([
                        x_all[:n_source][src_keep], x_all[sup_rows][sup_keep]])
                    y_fit = np.concatenate([y_src[src_keep], y_sup[sup_keep]])
                    weights = np.concatenate([
                        np.ones(int(src_keep.sum())),
                        np.full(int(sup_keep.sum()),
                                float(src_keep.sum()) / max(int(sup_keep.sum()), 1)),
                    ])
                    model = XGBRegressor(
                        n_estimators=300, max_depth=6, learning_rate=0.05,
                        subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0,
                        n_jobs=args.threads, random_state=seed,
                        tree_method="hist",
                    )
                    model.fit(x_fit, y_fit, sample_weight=weights)
                    pred = model.predict(x_q[eval_mask])
                    results[str(K)][arm] = float(
                        roc_auc_score(y_eval[eval_mask], pred))

            out.mkdir(parents=True, exist_ok=True)
            (out / "metrics.json").write_text(json.dumps({
                "target": target, "seed": seed,
                "benchmark_id": BENCHMARK_ID, "feature_set": FEATURE_SET,
                "target_set": TARGET_SET,
                "metric": "auroc_vs_documented_target_binary (higher is better)",
                "backbone": "xgboost_hist_d6_n300_regression_ranked",
                "arms": list(ARMS), "primary_k": PRIMARY_K,
                "n_source": n_source, "n_pool": n_pool,
                "n_eval": int(eval_mask.sum()),
                "eval_prevalence": float(np.mean(y_eval[eval_mask])),
                "placebo_label_maps": placebo_maps,
                "wall_seconds": round(time.time() - t0, 1),
                "auroc": results,
            }, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
            print(json.dumps({"target": target, "seed": seed,
                              "wall_seconds": round(time.time() - t0, 1),
                              "done": True}), flush=True)

    print(json.dumps({"status": "complete"}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
