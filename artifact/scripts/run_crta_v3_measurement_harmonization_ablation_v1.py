#!/usr/bin/env python3
"""M1/M2 measurement-harmonization ablation, at the builder's own call site.

The benchmark builder applies the questionnaire harmonization table before any
method sees a row (`load_questionnaire_rule_index()`; single call site at
build_benchmark_table.py:317).  This experiment injects a different table per
arm at exactly that point and holds everything else fixed:

    raw             empty index -- harmonization ablated, conflicts live
    pipeline_table  the six operative rows exactly as applied today
    llm_table       the isolated session's documented-arm table, translated
                    by the frozen rule (majority of 3 samples; valid codes
                    identity, reverse iff flagged, all else NaN)
    placebo_table   capacity-matched wrong table, redrawn per (target, seed)

Design, verdict rules, and the insensitivity gate are frozen in
`iclr_latex_v3/M1M2_MEASUREMENT_HARMONIZATION_ABLATION_PREREGISTRATION_V1.md`
before any cell was executed.  Verdicts are against `placebo_table`, not
`raw`.  Metric: query-SD-normalized RMSE (lower is better).

Preflight (mandatory, runs before any training): the `pipeline_table` build
must equal the unpatched default build exactly, and the `raw` build must
differ from it on at least one survey column.
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
TARGETS = ("glucose", "waist_cm", "triglycerides", "sbp", "dbp", "total_cholesterol")
SEEDS = tuple(range(50, 60))
SUPPORT_ROWS = (64, 256, 1024)
PRIMARY_K = 256
ARMS = ("raw", "pipeline_table", "llm_table", "placebo_table")
SURVEY_SLOTS = ("sex", "education_level", "diabetes_history")

LLM_RESPONSE_DIR = (
    ROOT / "experiments/crta_v3_measurement_layer_v1/harmon_responses_v1"
)
LLM_SAMPLES = ("raw_documented_s1.txt", "raw_documented_s2.txt", "raw_documented_s3.txt")

# The six harmonization rows bound by the three survey slots.  Keys are the
# builder's (dataset_name.lower(), source_column) index keys.
BOUND_ITEMS: dict[tuple[str, str], str] = {
    ("nhanes", "RIAGENDR"): "NHANES::RIAGENDR",
    ("knhanes", "ALL__sex"): "KNHANES::ALL__sex",
    ("nhanes", "DMDEDUC2"): "NHANES::DMDEDUC2",
    ("knhanes", "ALL__educ"): "KNHANES::ALL__educ",
    ("nhanes", "DIQ010"): "NHANES::DIQ010",
    ("knhanes", "ALL__de1_dg"): "KNHANES::ALL__de1_dg",
}

# Transcribed from `recode_questionnaire_series` for the bound rows; the
# preflight proves the transcription exact against the unpatched builder.
PIPELINE_SPEC: dict[tuple[str, str], dict] = {
    ("nhanes", "RIAGENDR"): {"kind": "identity"},
    ("knhanes", "ALL__sex"): {"kind": "identity"},
    ("nhanes", "DMDEDUC2"): {"kind": "map", "map": {1: 1, 2: 2, 3: 3, 4: 4, 5: 5}},
    ("knhanes", "ALL__educ"): {
        "kind": "map",
        "map": {1: 1, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 5, 8: 5},
    },
    ("nhanes", "DIQ010"): {"kind": "map", "map": {1: 1, 2: 0}},
    ("knhanes", "ALL__de1_dg"): {"kind": "map", "map": {1: 1, 0: 0}},
}

# Documented code pools for the placebo generator (executable_item_rules.csv:
# valid_codes | missing_or_sentinel_codes).  Outputs are the pipeline row's
# output multiset over its valid codes.
PLACEBO_BASIS: dict[tuple[str, str], dict] = {
    ("nhanes", "RIAGENDR"): {"valid": [1, 2], "sentinel": [], "outputs": [1, 2]},
    ("knhanes", "ALL__sex"): {"valid": [1, 2], "sentinel": [], "outputs": [1, 2]},
    ("nhanes", "DMDEDUC2"): {
        "valid": [1, 2, 3, 4, 5], "sentinel": [7, 9], "outputs": [1, 2, 3, 4, 5],
    },
    ("knhanes", "ALL__educ"): {
        "valid": [1, 2, 3, 4, 5, 6, 7, 8], "sentinel": [88, 99],
        "outputs": [1, 1, 2, 3, 4, 5, 5, 5],
    },
    ("nhanes", "DIQ010"): {"valid": [1, 2], "sentinel": [3, 7, 9], "outputs": [1, 0]},
    ("knhanes", "ALL__de1_dg"): {"valid": [0, 1], "sentinel": [8, 9], "outputs": [0, 1]},
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def derived_rng(key: str) -> np.random.Generator:
    return np.random.default_rng(int(hashlib.sha256(key.encode()).hexdigest()[:16], 16))


def apply_spec(series: pd.Series, spec: dict) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    if spec["kind"] == "identity":
        return values.astype("float64")
    out = pd.Series(np.nan, index=series.index, dtype="float64")
    for code, value in spec["map"].items():
        out[values == float(code)] = float(value)
    return out


def make_rule_index(specs: dict[tuple[str, str], dict]) -> dict:
    return {
        key: {"harmonized_value_rule": json.dumps(spec, sort_keys=True)}
        for key, spec in specs.items()
    }


def spec_interpreter(series: pd.Series, rule_id: str) -> pd.Series:
    return apply_spec(series, json.loads(rule_id))


def load_llm_spec() -> tuple[dict[tuple[str, str], dict], dict]:
    """Frozen translation: field-wise majority of 3 documented samples;
    valid codes identity (reversed iff flagged), all else NaN."""
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

    specs: dict[tuple[str, str], dict] = {}
    audit: dict[str, dict] = {}
    for key, item_id in BOUND_ITEMS.items():
        valid = sorted(float(v) for v in majority("valid_codes", item_id))
        reverse = bool(majority("requires_reverse_coding", item_id))
        if reverse and valid:
            pivot = min(valid) + max(valid)
            mapping = {v: pivot - v for v in valid}
        else:
            mapping = {v: v for v in valid}
        specs[key] = {"kind": "map", "map": mapping}
        audit[item_id] = {
            "valid_codes": valid,
            "missing_or_sentinel_codes": majority("missing_or_sentinel_codes", item_id),
            "requires_reverse_coding": reverse,
            "unanimous": all(
                sample[item_id]["valid_codes"] == parsed[0][item_id]["valid_codes"]
                and sample[item_id]["requires_reverse_coding"]
                == parsed[0][item_id]["requires_reverse_coding"]
                for sample in parsed
            ),
        }
    return specs, audit


def make_placebo_spec(target: str, seed: int) -> dict[tuple[str, str], dict]:
    specs: dict[tuple[str, str], dict] = {}
    for (cohort, item), basis in PLACEBO_BASIS.items():
        rng = derived_rng(f"placebo_v1|{target}|{seed}|{cohort}|{item}")
        pool = sorted(set(basis["valid"]) | set(basis["sentinel"]))
        n_mask = len(basis["sentinel"])
        masked = set(
            rng.choice(np.asarray(pool, dtype=float), size=n_mask, replace=False).tolist()
        ) if n_mask else set()
        kept = [code for code in pool if code not in masked]
        outputs = list(rng.permutation(np.asarray(basis["outputs"], dtype=float)))
        if len(kept) != len(outputs):
            raise RuntimeError(f"placebo capacity mismatch for {cohort}/{item}")
        specs[(cohort, item)] = {
            "kind": "map",
            "map": {float(c): float(v) for c, v in zip(kept, outputs)},
        }
    return specs


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def build_bundle(benchmark, target: str, seed: int):
    return benchmark.build_single_target_table(
        benchmark_id=BENCHMARK_ID, target_name=target,
        fewshot_frac=0.10, seed=seed,
        target_set_override="objective_anchor_targets_v1_safe",
        feature_set_override=FEATURE_SET,
    )


def bundle_matrices(bundle, target: str):
    x_train = bundle["X_train"].reset_index(drop=True)
    x_test = bundle["X_test"].reset_index(drop=True)
    feat_cols = [c for c in x_train.columns if c.startswith("slot__")]
    feat_cols = [c for c in feat_cols if c != f"slot__{target}"]
    x_all = x_train[feat_cols].apply(pd.to_numeric, errors="coerce").to_numpy(np.float64)
    x_q = x_test[feat_cols].apply(pd.to_numeric, errors="coerce").to_numpy(np.float64)
    y_train = pd.to_numeric(bundle["y_train"], errors="coerce").to_numpy(np.float64)
    y_test = pd.to_numeric(bundle["y_test"], errors="coerce").to_numpy(np.float64)
    origin = np.asarray(bundle["train_origin"], dtype=object)
    return feat_cols, x_all, x_q, y_train, y_test, int(np.sum(origin == "source"))


def assert_inline_harmonization_absent(benchmark) -> None:
    manifest = benchmark.load_yaml(benchmark.DEFAULT_DATASET_MANIFEST)
    feature_cfg = benchmark.load_yaml(benchmark.CONFIG_DIR / "feature_sets.yaml")
    slots = feature_cfg["feature_sets"][FEATURE_SET]["slots"]
    for slot in slots:
        mapping = manifest["slots"].get(slot, {})
        if isinstance(mapping.get("harmonization"), dict):
            raise RuntimeError(
                f"slot {slot} carries inline harmonization; the raw arm would not be raw"
            )


def preflight(benchmark, llm_specs) -> dict:
    """pipeline_table must reproduce the default build exactly; raw must not."""
    target, seed = "glucose", 50
    benchmark_load = benchmark.load_questionnaire_rule_index
    benchmark_recode = benchmark.recode_questionnaire_series

    default_bundle = build_bundle(benchmark, target, seed)
    _, x_default, xq_default, y_tr_d, y_te_d, _ = bundle_matrices(default_bundle, target)

    benchmark.recode_questionnaire_series = spec_interpreter
    try:
        benchmark.load_questionnaire_rule_index = (
            lambda path=None: make_rule_index(PIPELINE_SPEC)
        )
        pipeline_bundle = build_bundle(benchmark, target, seed)
        cols, x_pipe, xq_pipe, y_tr_p, y_te_p, _ = bundle_matrices(pipeline_bundle, target)

        benchmark.load_questionnaire_rule_index = lambda path=None: {}
        raw_bundle = build_bundle(benchmark, target, seed)
        _, x_raw, _, _, _, _ = bundle_matrices(raw_bundle, target)
    finally:
        benchmark.load_questionnaire_rule_index = benchmark_load
        benchmark.recode_questionnaire_series = benchmark_recode

    def equal(a: np.ndarray, b: np.ndarray) -> bool:
        return a.shape == b.shape and bool(
            np.all((a == b) | (np.isnan(a) & np.isnan(b)))
        )

    if not (equal(x_default, x_pipe) and equal(xq_default, xq_pipe)
            and equal(y_tr_d, y_tr_p) and equal(y_te_d, y_te_p)):
        raise RuntimeError(
            "preflight FAIL: pipeline_table build does not reproduce the default build"
        )
    survey_cols = [i for i, c in enumerate(cols)
                   if c in {f"slot__{s}" for s in SURVEY_SLOTS}]
    changed = [cols[i] for i in survey_cols
               if not equal(x_default[:, i], x_raw[:, i])]
    if not changed:
        raise RuntimeError(
            "preflight FAIL: raw build equals the default build on every survey column; "
            "the ablation does not bite"
        )
    return {"pipeline_reproduces_default": True, "raw_changes_columns": changed}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nhanes-parquet", type=Path, required=True)
    parser.add_argument("--knhanes-parquet", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--targets", nargs="*", default=list(TARGETS))
    parser.add_argument("--seeds", nargs="*", type=int, default=list(SEEDS))
    parser.add_argument("--support-rows", nargs="*", type=int, default=list(SUPPORT_ROWS))
    parser.add_argument("--threads", type=int, default=4)
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

    assert_inline_harmonization_absent(benchmark)
    llm_specs, llm_audit = load_llm_spec()

    args.out_root.mkdir(parents=True, exist_ok=True)
    (args.out_root / "ARM_TABLES_V1.json").write_text(json.dumps({
        "pipeline_table": {f"{c}/{i}": s for (c, i), s in PIPELINE_SPEC.items()},
        "llm_table": {f"{c}/{i}": s for (c, i), s in llm_specs.items()},
        "llm_translation_audit": llm_audit,
        "placebo": "per (target, seed); generator frozen in the preregistration",
    }, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    report = preflight(benchmark, llm_specs)
    print(json.dumps({"preflight": report}), flush=True)

    original_recode = benchmark.recode_questionnaire_series
    benchmark.recode_questionnaire_series = spec_interpreter

    for target in args.targets:
        for seed in args.seeds:
            out = args.out_root / target / f"seed_{seed}"
            if (out / "metrics.json").is_file():
                continue
            t0 = time.time()

            arm_specs = {
                "raw": None,
                "pipeline_table": PIPELINE_SPEC,
                "llm_table": llm_specs,
                "placebo_table": make_placebo_spec(target, seed),
            }
            per_arm: dict[str, dict] = {}
            n_source_seen, n_pool_seen = None, None
            for arm in ARMS:
                specs = arm_specs[arm]
                benchmark.load_questionnaire_rule_index = (
                    (lambda path=None: {}) if specs is None
                    else (lambda path=None, s=specs: make_rule_index(s))
                )
                bundle = build_bundle(benchmark, target, seed)
                _, x_all, x_q, y_train, y_test, n_source = bundle_matrices(bundle, target)
                n_pool = len(x_all) - n_source
                if n_source_seen is None:
                    n_source_seen, n_pool_seen = n_source, n_pool
                elif (n_source, n_pool) != (n_source_seen, n_pool_seen):
                    raise RuntimeError(
                        f"arm {arm} changed the split: {n_source}/{n_pool} "
                        f"vs {n_source_seen}/{n_pool_seen}"
                    )
                per_arm[arm] = {
                    "x_all": x_all, "x_q": x_q,
                    "y_train": y_train, "y_test": y_test, "n_source": n_source,
                }

            query_sd = float(np.std(per_arm["raw"]["y_test"], ddof=0))
            results: dict = {}
            for K in args.support_rows:
                pick = np.sort(np.random.default_rng(seed * 131 + K).choice(
                    n_pool_seen, size=min(K, n_pool_seen), replace=False))
                results[str(K)] = {}
                for arm in ARMS:
                    data = per_arm[arm]
                    n_source = data["n_source"]
                    rows = np.arange(n_source, len(data["x_all"]))[pick]
                    x_fit = np.vstack([data["x_all"][:n_source], data["x_all"][rows]])
                    y_fit = np.concatenate(
                        [data["y_train"][:n_source], data["y_train"][rows]])
                    w = np.concatenate([
                        np.ones(n_source),
                        np.full(len(rows), n_source / max(len(rows), 1)),
                    ])
                    model = XGBRegressor(
                        n_estimators=300, max_depth=6, learning_rate=0.05,
                        subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0,
                        n_jobs=args.threads, random_state=seed,
                        tree_method="hist",
                    )
                    model.fit(x_fit, y_fit, sample_weight=w)
                    pred = model.predict(data["x_q"])
                    results[str(K)][arm] = float(
                        np.sqrt(np.mean((data["y_test"] - pred) ** 2)) / query_sd)

            out.mkdir(parents=True, exist_ok=True)
            (out / "metrics.json").write_text(json.dumps({
                "target": target, "seed": seed,
                "benchmark_id": BENCHMARK_ID, "feature_set": FEATURE_SET,
                "metric": "query_sd_normalized_rmse (lower is better)",
                "backbone": "xgboost_hist_d6_n300",
                "arms": list(ARMS), "primary_k": PRIMARY_K,
                "n_source": n_source_seen, "n_pool": n_pool_seen,
                "n_query": int(len(per_arm["raw"]["x_q"])),
                "placebo_spec": {
                    f"{c}/{i}": s for (c, i), s in arm_specs["placebo_table"].items()
                },
                "wall_seconds": round(time.time() - t0, 1),
                "nrmse": results,
            }, indent=1, sort_keys=True) + "\n", encoding="utf-8")
            print(json.dumps({"target": target, "seed": seed,
                              "wall_seconds": round(time.time() - t0, 1),
                              "done": True}), flush=True)

    benchmark.recode_questionnaire_series = original_recode
    print(json.dumps({"status": "complete"}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
