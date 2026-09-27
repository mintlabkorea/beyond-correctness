#!/usr/bin/env python3
"""E2: survey-label panel on TabPFN (backbone generality, local GPU).

Same arms and cells as the label panel (llm table = extraction v2), same
fixed documented eval label; backbone TabPFN 7.0.0 in-context regression
instead of XGBoost.  Declared differences: no sample weights (API), the
source context is subsampled to 8,192 rows per cell (deterministic).
Cell metrics use the panel's schema so the frozen panel summarizer
adjudicates unchanged.  Design and predictions:
`iclr_latex_v3/OVERNIGHT_EXPANSION_PREREGISTRATION_20260820_V1.md` (E2).
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
SOURCE_CONTEXT_ROWS = 8_192
PREDICT_CHUNK = 512


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
    parser.add_argument("--targets", nargs="*", default=None)
    parser.add_argument("--seeds", nargs="*", type=int, default=None)
    parser.add_argument("--support-rows", nargs="*", type=int, default=None)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    panel = _load("panel_v1_for_tabpfn",
                  ROOT / "scripts/run_crta_v3_survey_label_panel_v1.py")
    panel.LLM_RESPONSE_DIR = (
        ROOT / "experiments/crta_v3_measurement_layer_v1/harmon_responses_v2")
    panel.LLM_SAMPLES = (
        "raw_documented_v2_s1.txt", "raw_documented_v2_s2.txt",
        "raw_documented_v2_s3.txt")
    original_rng = panel.derived_rng
    panel.derived_rng = lambda key: original_rng(
        key.replace("label_panel_v1", "label_panel_tabpfn_v1"))

    for key, path in (("nhanes", args.nhanes_parquet), ("knhanes", args.knhanes_parquet)):
        observed = panel.sha256_file(path)
        if observed != panel.EXPECTED[key]:
            raise RuntimeError(f"{key} parquet SHA-256 mismatch: {observed}")

    from sklearn.metrics import roc_auc_score
    from tabpfn import TabPFNRegressor

    sys.path.insert(0, str(panel.BENCH / "scripts"))
    benchmark = _load("crta_bench_tabpfn",
                      panel.BENCH / "scripts/build_benchmark_table.py")
    original_load_yaml = benchmark.load_yaml
    manifest_path = Path(benchmark.DEFAULT_DATASET_MANIFEST).resolve()

    def load_yaml_patched(path):
        value = original_load_yaml(path)
        if Path(path).resolve() == manifest_path:
            value["datasets"]["nhanes"]["parquet"] = str(args.nhanes_parquet)
            value["datasets"]["knhanes"]["parquet"] = str(args.knhanes_parquet)
            for target, (nh_col, kn_col) in panel.TARGETS.items():
                value.setdefault("targets", {})[target] = {
                    "label": target, "nhanes": nh_col, "knhanes": kn_col}
        if isinstance(value, dict) and "target_sets" in value:
            value["target_sets"][panel.TARGET_SET] = {
                "description": "injected survey-label panel v1",
                "targets": list(panel.TARGETS)}
        return value

    benchmark.load_yaml = load_yaml_patched

    llm_specs = panel.load_llm_label_specs()
    args.out_root.mkdir(parents=True, exist_ok=True)

    targets = args.targets or list(panel.TARGETS)
    seeds = args.seeds or list(panel.SEEDS)
    support_rows = args.support_rows or list(panel.SUPPORT_ROWS)

    for target in targets:
        for seed in seeds:
            out = args.out_root / target / f"seed_{seed}"
            if (out / "metrics.json").is_file():
                continue
            t0 = time.time()
            bundle = benchmark.build_single_target_table(
                benchmark_id=panel.BENCHMARK_ID, target_name=target,
                fewshot_frac=0.10, seed=seed,
                target_set_override=panel.TARGET_SET,
                feature_set_override=panel.FEATURE_SET,
            )
            x_train = bundle["X_train"].reset_index(drop=True)
            x_test = bundle["X_test"].reset_index(drop=True)
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

            y_eval = panel.map_values(y_raw_test, panel.EVAL_LABEL_MAPS[target])
            eval_mask = np.isfinite(y_eval)

            sub_rng = panel.derived_rng(f"tabpfn_subsample|{target}|{seed}")
            sub_idx = np.sort(sub_rng.choice(
                n_source, size=min(SOURCE_CONTEXT_ROWS, n_source), replace=False))

            placebo_maps = panel.make_placebo_label_maps(llm_specs, target, seed)
            arm_label_maps = {
                "raw": {"source": None, "target": None},
                "pipeline_table": panel.PIPELINE_LABEL_MAPS[target],
                "llm_table": {
                    side: llm_specs[target][side]["map"]
                    for side in ("source", "target")},
                "placebo_table": placebo_maps,
            }

            results: dict = {}
            for K in support_rows:
                pick = np.sort(np.random.default_rng(seed * 131 + K).choice(
                    n_pool, size=min(K, n_pool), replace=False))
                sup_rows = np.arange(n_source, len(x_all))[pick]
                results[str(K)] = {}
                for arm in panel.ARMS:
                    maps = arm_label_maps[arm]
                    y_src = panel.map_values(
                        y_raw_train[:n_source][sub_idx], maps["source"])
                    y_sup = panel.map_values(y_raw_train[sup_rows], maps["target"])
                    src_keep = np.isfinite(y_src)
                    sup_keep = np.isfinite(y_sup)
                    if src_keep.sum() == 0 or sup_keep.sum() == 0:
                        results[str(K)][arm] = float("nan")
                        continue
                    ctx_x = np.vstack([
                        x_all[:n_source][sub_idx][src_keep],
                        x_all[sup_rows][sup_keep]])
                    ctx_y = np.concatenate([y_src[src_keep], y_sup[sup_keep]])
                    model = TabPFNRegressor(device=args.device, random_state=seed)
                    model.fit(ctx_x, ctx_y)
                    parts = []
                    x_query = x_q[eval_mask]
                    for lo in range(0, len(x_query), PREDICT_CHUNK):
                        parts.append(np.asarray(
                            model.predict(x_query[lo:lo + PREDICT_CHUNK]),
                            dtype=np.float64))
                    pred = np.concatenate(parts)
                    results[str(K)][arm] = float(
                        roc_auc_score(y_eval[eval_mask], pred))

            out.mkdir(parents=True, exist_ok=True)
            (out / "metrics.json").write_text(json.dumps({
                "target": target, "seed": seed,
                "benchmark_id": panel.BENCHMARK_ID,
                "feature_set": panel.FEATURE_SET,
                "target_set": panel.TARGET_SET,
                "metric": "auroc_vs_documented_target_binary (higher is better)",
                "backbone": f"tabpfn_7.0.0_incontext_src{SOURCE_CONTEXT_ROWS}_unweighted",
                "arms": list(panel.ARMS), "primary_k": panel.PRIMARY_K,
                "n_source": n_source, "n_pool": n_pool,
                "n_eval": int(eval_mask.sum()),
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
