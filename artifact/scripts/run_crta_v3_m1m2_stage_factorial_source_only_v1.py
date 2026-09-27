#!/usr/bin/env python3
"""SOURCE-ONLY M-AXIS FORK (2026-08-25) of the frozen M1/M2 stage factorial.

Minimal, audited modifications relative to run_crta_v3_m1m2_stage_factorial_v1.py:
  (1) build() gains mode "off_source": the questionnaire rule index keeps only
      the TARGET cohort's rows, so target-side features stay harmonized while
      source-side features are raw;
  (2) the "off" bundle is built with mode "off_source" and the "wrong" bundle
      is not built (its arms are never fit here);
  (3) arms a00_base / a01_columns use label maps {source: identity,
      target: documented map}, so support labels are documented-mapped in
      every arm and the M axis touches the source side only.
TARGET_COHORT must be set by the caller ("knhanes" for nh2kn, "nhanes" for kn2nh).

Original docstring follows.
M1/M2 measurement-stage factorial: supervision x information interaction.

Frozen design and verdicts:
`iclr_latex_v3/M1M2_STAGE_FACTORIAL_PREREGISTRATION_V1.md`.

L0 (stage) = the operative pipeline table on features (default builder) and
labels; L0 off = harmonization-ablated build with identity labels.  L1 =
the nh2kn bank's 9 member slots as raw columns.  L2 = 12 deterministic
within-concept numeric relations (6 pairs x {difference, safe ratio}).
Metric: AUROC against the fixed codebook-documented target-side binary
(higher is better), identical across arms.  Nine arms per cell; placebos
for stage, binding, and relations; standing is_target arm.
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
TARGET_COHORT: str | None = None  # set by the caller per direction
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
# Within-concept ordered pairs of the gpt-5.6-sol bank's four concepts.
RELATION_PAIRS = (
    ("height_cm", "weight_kg"), ("height_cm", "waist_cm"),
    ("weight_kg", "waist_cm"), ("sbp", "dbp"), ("glucose", "hba1c"),
    ("total_cholesterol", "triglycerides"),
)

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

# Documented pools for the wrong-table generator (executable_item_rules.csv);
# outputs are each pipeline row's output multiset over its valid codes.
PLACEBO_BASIS: dict[tuple[str, str], dict] = {
    ("nhanes", "RIAGENDR"): {"valid": [1, 2], "sentinel": [], "outputs": [1, 2]},
    ("knhanes", "ALL__sex"): {"valid": [1, 2], "sentinel": [], "outputs": [1, 2]},
    ("nhanes", "DMDEDUC2"): {
        "valid": [1, 2, 3, 4, 5], "sentinel": [7, 9], "outputs": [1, 2, 3, 4, 5]},
    ("knhanes", "ALL__educ"): {
        "valid": [1, 2, 3, 4, 5, 6, 7, 8], "sentinel": [88, 99],
        "outputs": [1, 1, 2, 3, 4, 5, 5, 5]},
    ("nhanes", "DIQ010"): {"valid": [1, 2], "sentinel": [3, 7, 9], "outputs": [1, 0]},
    ("knhanes", "ALL__de1_dg"): {"valid": [0, 1], "sentinel": [8, 9], "outputs": [0, 1]},
    ("nhanes", "BPQ020"): {"valid": [1, 2], "sentinel": [7, 9], "outputs": [1, 0]},
    ("knhanes", "ALL__di1_dg"): {"valid": [0, 1], "sentinel": [8, 9], "outputs": [0, 1]},
    ("nhanes", "SMQ040"): {"valid": [1, 2, 3], "sentinel": [7, 9], "outputs": [1, 1, 0]},
    ("knhanes", "ALL__bs3_1"): {
        "valid": [1, 2, 3, 4], "sentinel": [8, 9], "outputs": [1, 1, 0, 0]},
}
# (cohort, raw column) label rows per target, for the wrong-label maps.
LABEL_ITEMS: dict[str, dict[str, tuple[str, str]]] = {
    "diabetes_history": {
        "source": ("nhanes", "DIQ010"), "target": ("knhanes", "ALL__de1_dg")},
    "hypertension_history": {
        "source": ("nhanes", "BPQ020"), "target": ("knhanes", "ALL__di1_dg")},
    "current_smoking_status": {
        "source": ("nhanes", "SMQ040"), "target": ("knhanes", "ALL__bs3_1")},
}

ARMS = (
    "a00_base", "a01_columns", "a10_stage", "a11_stage_columns",
    "a11r_stage_columns_relations", "pl_stage_at_columns",
    "pl_columns_at_stage", "pl_relations_at_stage", "is_target",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def derived_rng(key: str) -> np.random.Generator:
    return np.random.default_rng(int(hashlib.sha256(key.encode()).hexdigest()[:16], 16))


def map_values(values: np.ndarray, mapping: dict[float, float] | None) -> np.ndarray:
    if mapping is None:
        return values.astype(np.float64)
    out = np.full(len(values), np.nan)
    for code, value in mapping.items():
        out[values == float(code)] = float(value)
    return out


def permuted_map(basis: dict, rng: np.random.Generator) -> dict[float, float]:
    pool = sorted(set(basis["valid"]) | set(basis["sentinel"]))
    n_mask = len(basis["sentinel"])
    masked = set(
        rng.choice(np.asarray(pool), size=n_mask, replace=False).tolist()
    ) if n_mask else set()
    kept = [code for code in pool if code not in masked]
    outputs = list(rng.permutation(np.asarray(basis["outputs"], dtype=float)))
    if len(kept) != len(outputs):
        raise RuntimeError("placebo capacity mismatch")
    return {float(c): float(v) for c, v in zip(kept, outputs)}


def make_wrong_stage(target: str, seed: int):
    """Coherently wrong table: feature specs for the builder + label maps."""
    feature_specs: dict[tuple[str, str], dict] = {}
    for (cohort, item), basis in PLACEBO_BASIS.items():
        rng = derived_rng(f"stage_factorial_v1|pl_stage|{target}|{seed}|{cohort}|{item}")
        feature_specs[(cohort, item)] = {
            "kind": "map", "map": permuted_map(basis, rng)}
    label_maps = {}
    for side, (cohort, item) in LABEL_ITEMS[target].items():
        label_maps[side] = feature_specs[(cohort, item)]["map"]
    return feature_specs, label_maps


def relation_features(arrays: dict[str, np.ndarray],
                      pairs, ops=("difference", "ratio")) -> list[np.ndarray]:
    features = []
    for a, b in pairs:
        va, vb = arrays[a], arrays[b]
        for op in ops:
            if op == "difference":
                features.append(va - vb)
            else:
                with np.errstate(all="ignore"):
                    ratio = np.where(np.abs(vb) > 1e-8, va / vb, np.nan)
                features.append(ratio)
    return features


def make_random_pairs(target: str, seed: int) -> tuple[tuple[str, str], ...]:
    pool = [s for s in ALL_SLOTS if s != target]
    rng = derived_rng(f"stage_factorial_v1|pl_rel|{target}|{seed}")
    true_set = {frozenset(p) for p in RELATION_PAIRS}
    for _ in range(1000):
        pairs = []
        while len(pairs) < len(RELATION_PAIRS):
            a, b = rng.choice(pool, size=2, replace=False)
            if frozenset((str(a), str(b))) not in {frozenset(p) for p in pairs}:
                pairs.append((str(a), str(b)))
        if {frozenset(p) for p in pairs} != true_set:
            return tuple(pairs)
    raise RuntimeError("no random pair draw found")


def make_member_permutation(target: str, seed: int) -> dict[str, str]:
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
    benchmark = _load("crta_bench_stage", BENCH / "scripts/build_benchmark_table.py")
    original_load_yaml = benchmark.load_yaml
    original_rule_index = benchmark.load_questionnaire_rule_index
    original_recode = benchmark.recode_questionnaire_series
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
                "description": "stage_factorial_v1 injected feature set",
                "feature_mode": "explicit_slots", "slots": list(ALL_SLOTS)}
        if isinstance(value, dict) and "target_sets" in value:
            value["target_sets"][TARGET_SET] = {
                "description": "stage_factorial_v1 injected targets",
                "targets": list(TARGETS)}
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
    args.out_root.mkdir(parents=True, exist_ok=True)

    def build(target: str, seed: int, mode: str, wrong_specs=None) -> dict:
        if mode == "on":
            benchmark.load_questionnaire_rule_index = original_rule_index
        elif mode == "off":
            benchmark.load_questionnaire_rule_index = lambda path=None: {}
        elif mode == "off_source":
            if TARGET_COHORT not in ("nhanes", "knhanes"):
                raise RuntimeError("TARGET_COHORT must be set for off_source")
            full_index = original_rule_index()
            kept = {key: value for key, value in full_index.items()
                    if str(key[0]).lower() == TARGET_COHORT}
            if not kept or len(kept) == len(full_index):
                raise RuntimeError("off_source index filter is degenerate")
            benchmark.load_questionnaire_rule_index = (
                lambda path=None, i=kept: i)
        else:
            index = {
                key: {"harmonized_value_rule": json.dumps(spec, sort_keys=True)}
                for key, spec in wrong_specs.items()
            }
            benchmark.load_questionnaire_rule_index = (
                lambda path=None, i=index: i)
        bundle = benchmark.build_single_target_table(
            benchmark_id=BENCHMARK_ID, target_name=target,
            fewshot_frac=0.10, seed=seed,
            target_set_override=TARGET_SET, feature_set_override=FEATURE_SET,
        )
        x_train = bundle["X_train"].reset_index(drop=True)
        x_test = bundle["X_test"].reset_index(drop=True)
        if f"slot__{target}" in x_train.columns:
            raise RuntimeError(f"endpoint slot leaked into features: {target}")
        slots = {}
        for slot in ALL_SLOTS:
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

    for target in args.targets:
        base_slots = [s for s in BASE_CLINICAL + SURVEY_SLOTS if s != target]
        for seed in args.seeds:
            out = args.out_root / target / f"seed_{seed}"
            if (out / "metrics.json").is_file():
                continue
            t0 = time.time()

            wrong_specs, wrong_labels = make_wrong_stage(target, seed)
            bundles = {
                "off": build(target, seed, "off_source"),
                "on": build(target, seed, "on"),
            }
            n_source = bundles["off"]["n_source"]
            n_train = len(bundles["off"]["y_train"])
            n_pool = n_train - n_source
            y_raw_train = bundles["off"]["y_train"]
            y_raw_test = bundles["off"]["y_test"]
            for name, bundle in bundles.items():
                if bundle["n_source"] != n_source or not np.allclose(
                        bundle["y_train"], y_raw_train, equal_nan=True):
                    raise RuntimeError(f"bundle {name} changed split or labels")

            y_eval = map_values(y_raw_test, EVAL_LABEL_MAPS[target])
            eval_mask = np.isfinite(y_eval)
            if len(np.unique(y_eval[eval_mask])) < 2:
                raise RuntimeError(f"degenerate eval label for {target}")

            col_perm = make_member_permutation(target, seed)
            random_pairs = make_random_pairs(target, seed)

            arm_config = {
                "a00_base": ("off", {"source": None,
                                     "target": PIPELINE_LABEL_MAPS[target]["target"]},
                             "base", None),
                "a01_columns": ("off", {"source": None,
                                        "target": PIPELINE_LABEL_MAPS[target]["target"]},
                                "base+members", None),
                "a10_stage": ("on", PIPELINE_LABEL_MAPS[target], "base", None),
                "a11_stage_columns": (
                    "on", PIPELINE_LABEL_MAPS[target], "base+members", None),
                "a11r_stage_columns_relations": (
                    "on", PIPELINE_LABEL_MAPS[target], "base+members",
                    RELATION_PAIRS),
                "pl_stage_at_columns": (
                    "wrong", wrong_labels, "base+members", None),
                "pl_columns_at_stage": (
                    "on", PIPELINE_LABEL_MAPS[target], "base+members_permuted",
                    None),
                "pl_relations_at_stage": (
                    "on", PIPELINE_LABEL_MAPS[target], "base+members",
                    random_pairs),
                "is_target": (
                    "on", PIPELINE_LABEL_MAPS[target], "base+indicator", None),
            }

            results: dict = {}
            for K in args.support_rows:
                pick = np.sort(np.random.default_rng(seed * 131 + K).choice(
                    n_pool, size=min(K, n_pool), replace=False))
                sup_rows = np.arange(n_source, n_train)[pick]
                results[str(K)] = {}
                for arm in ARMS:
                    mode, label_maps, feature_mode, rel_pairs = arm_config[arm]
                    if mode not in bundles:
                        raise RuntimeError(f"arm {arm} needs bundle {mode}, not built in the source-only fork")
                    bundle = bundles[mode]

                    def fit_query(slot, permute=False):
                        source_slot = slot
                        target_slot = col_perm[slot] if (
                            permute and slot in col_perm) else slot
                        train_src = bundle["slots"][source_slot][0]
                        train_tgt = bundle["slots"][target_slot][0]
                        fit = np.concatenate(
                            [train_src[:n_source], train_tgt[sup_rows]])
                        return fit, bundle["slots"][target_slot][1]

                    permuted = feature_mode == "base+members_permuted"
                    fit_parts, query_parts = [], []
                    fit_arrays, query_arrays = {}, {}
                    for slot in base_slots:
                        fit, query = fit_query(slot)
                        fit_parts.append(fit)
                        query_parts.append(query)
                        fit_arrays[slot], query_arrays[slot] = fit, query
                    if feature_mode.startswith("base+members"):
                        for slot in MEMBER_SLOTS:
                            fit, query = fit_query(slot, permute=permuted)
                            fit_parts.append(fit)
                            query_parts.append(query)
                            fit_arrays[slot], query_arrays[slot] = fit, query
                    if rel_pairs is not None:
                        fit_parts.extend(
                            relation_features(fit_arrays, rel_pairs))
                        query_parts.extend(
                            relation_features(query_arrays, rel_pairs))
                    if feature_mode == "base+indicator":
                        fit_parts.append(np.concatenate(
                            [np.zeros(n_source), np.ones(len(sup_rows))]))
                        query_parts.append(np.ones(len(y_raw_test)))

                    if label_maps is None:
                        y_src = y_raw_train[:n_source].astype(np.float64)
                        y_sup = y_raw_train[sup_rows].astype(np.float64)
                    else:
                        y_src = map_values(
                            y_raw_train[:n_source], label_maps["source"])
                        y_sup = map_values(
                            y_raw_train[sup_rows], label_maps["target"])
                    src_keep = np.isfinite(y_src)
                    sup_keep = np.isfinite(y_sup)
                    if src_keep.sum() == 0 or sup_keep.sum() == 0:
                        results[str(K)][arm] = float("nan")
                        continue
                    x_fit = np.column_stack(
                        [part for part in fit_parts])
                    x_query = np.column_stack(
                        [part for part in query_parts])
                    keep = np.concatenate([src_keep, sup_keep])
                    x_fit = x_fit[keep]
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
                    pred = model.predict(x_query[eval_mask])
                    results[str(K)][arm] = float(
                        roc_auc_score(y_eval[eval_mask], pred))

            out.mkdir(parents=True, exist_ok=True)
            (out / "metrics.json").write_text(json.dumps({
                "target": target, "seed": seed,
                "benchmark_id": BENCHMARK_ID, "feature_set": FEATURE_SET,
                "metric": "auroc_vs_documented_target_binary (higher is better)",
                "backbone": "xgboost_hist_d6_n300_regression_ranked",
                "m_axis": "source_only_fork_v1", "target_cohort": TARGET_COHORT,
                "arms": list(ARMS), "primary_k": PRIMARY_K,
                "n_source": n_source, "n_pool": n_pool,
                "n_eval": int(eval_mask.sum()),
                "pl_columns_permutation": col_perm,
                "pl_relation_pairs": [list(p) for p in random_pairs],
                "wrong_label_maps": wrong_labels,
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
