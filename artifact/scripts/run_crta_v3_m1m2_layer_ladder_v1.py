#!/usr/bin/env python3
"""M1/M2 layer ladder: column set -> grouping -> measurement, with placebos.

Design and verdict rules are frozen in
`iclr_latex_v3/M1M2_LAYER_LADDER_PREREGISTRATION_V1.md` before any cell was
executed.  Ten arms per cell (relation is declared not evaluable, not an
arm):

    rung0_base          11 non-member slots, raw survey values
    rung1_columns       + the bank's 8 remaining member slots (raw)
    rung2_grouping      + 4x4 concept channels (true grouping)
    rung3_measurement   rung2 with the LLM canonicalization on survey slots
    pl_columns          rung1, target-side member values derangement-permuted
    pl_grouping         rung1 + channels from a wrong partition (same sizes)
    pl_measurement      rung3 with a capacity-matched wrong table
    is_target           rung0 + a 0/1 target-cohort indicator
    loo_columns         rung3 minus raw member columns
    loo_grouping        rung3 minus grouping channels
    (loo_measurement == rung2_grouping; alias, not refit)

Surface: the harmonization-ablated benchmark (rule index emptied / replaced
at build_benchmark_table.py:317, as in the ablation experiment).  Concept
channels mirror compile_bank.py's math exactly; target-side standardization
parameters are fit on the K support rows only (the M4 convention).
Metric: query-SD-normalized RMSE (lower is better).
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
BANK_LEDGER = ROOT / (
    "iclr_latex_v3/method_contract/v1/runs/proposer_bank_v2/models/gpt-5.6-sol/"
    "medical_nhanes_knhanes_full_documents_v2_attempt_02/decision_ledger.json"
)
EXPECTED_BANK_SHA256 = (
    "cd1e230ed919acbdfaa0614e4064ffa52d69c324988640f93242f900e9b121c9"
)
BENCHMARK_ID = "std_cross_nh2kn_shared_anchorreset_fewshot_v1"
FEATURE_SET = "ladder_all_slots_v1"  # injected at load time, never written to disk
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
SURVEY_SLOTS = (
    "sex", "education_level", "diabetes_history", "hypertension_history",
    "current_smoking_status",
)
GROUPS: dict[str, tuple[str, ...]] = {
    "body_measurements": ("height_cm", "weight_kg", "waist_cm"),
    "first_reading_blood_pressure": ("sbp", "dbp"),
    "diabetes_test_measurements": ("glucose", "hba1c"),
    "blood_lipid_measurements": ("total_cholesterol", "triglycerides"),
}
# The bank binds raw columns; on this surface every binding coincides with
# the manifest slot pairing.  Asserted against the ledger at startup.
RAW_MEMBERS = {
    "body_measurements": {
        "source": {"BMXHT", "BMXWT", "BMXWAIST"},
        "target": {"ALL__he_ht", "ALL__he_wt", "ALL__he_wc"},
    },
    "first_reading_blood_pressure": {
        "source": {"BPXSY1", "BPXDI1"},
        "target": {"ALL__he_sbp1", "ALL__he_dbp1"},
    },
    "diabetes_test_measurements": {
        "source": {"LBXGLU", "LBXGH"},
        "target": {"ALL__he_glu", "ALL__he_hba1c"},
    },
    "blood_lipid_measurements": {
        "source": {"LBXTC", "LBXSTR"},
        "target": {"ALL__he_chol", "ALL__he_tg"},
    },
}

LLM_RESPONSE_DIR = (
    ROOT / "experiments/crta_v3_measurement_layer_v1/harmon_responses_v1"
)
LLM_SAMPLES = ("raw_documented_s1.txt", "raw_documented_s2.txt", "raw_documented_s3.txt")
BOUND_ITEMS: dict[tuple[str, str], str] = {
    ("nhanes", "RIAGENDR"): "NHANES::RIAGENDR",
    ("knhanes", "ALL__sex"): "KNHANES::ALL__sex",
    ("nhanes", "DMDEDUC2"): "NHANES::DMDEDUC2",
    ("knhanes", "ALL__educ"): "KNHANES::ALL__educ",
    ("nhanes", "DIQ010"): "NHANES::DIQ010",
    ("knhanes", "ALL__de1_dg"): "KNHANES::ALL__de1_dg",
    ("nhanes", "BPQ020"): "NHANES::BPQ020",
    ("knhanes", "ALL__di1_dg"): "KNHANES::ALL__di1_dg",
    ("nhanes", "SMQ040"): "NHANES::SMQ040",
    ("knhanes", "ALL__bs3_1"): "KNHANES::ALL__bs3_1",
}

ARMS = (
    "rung0_base", "rung1_columns", "rung2_grouping", "rung3_measurement",
    "pl_columns", "pl_grouping", "pl_measurement", "is_target",
    "loo_columns", "loo_grouping",
)
ARM_BUNDLE = {
    "rung0_base": "raw", "rung1_columns": "raw", "rung2_grouping": "raw",
    "pl_columns": "raw", "pl_grouping": "raw", "is_target": "raw",
    "rung3_measurement": "meas", "loo_columns": "meas", "loo_grouping": "meas",
    "pl_measurement": "plmeas",
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
    out = pd.Series(np.nan, index=series.index, dtype="float64")
    if spec["kind"] == "canon":
        valid = [float(v) for v in spec["valid"]]
        lo, hi = min(valid), max(valid)
        for v in valid:
            oriented = (lo + hi - v) if spec["reverse"] else v
            out[values == v] = (oriented - lo) / (hi - lo) if hi > lo else 0.0
        return out
    for code, value in spec["map"].items():
        out[values == float(code)] = float(value)
    return out


def spec_interpreter(series: pd.Series, rule_id: str) -> pd.Series:
    return apply_spec(series, json.loads(rule_id))


def make_rule_index(specs: dict[tuple[str, str], dict]) -> dict:
    return {
        key: {"harmonized_value_rule": json.dumps(spec, sort_keys=True)}
        for key, spec in specs.items()
    }


def load_llm_measurement() -> dict[tuple[str, str], dict]:
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
    for key, item_id in BOUND_ITEMS.items():
        valid = sorted(float(v) for v in majority("valid_codes", item_id))
        reverse = bool(majority("requires_reverse_coding", item_id)) or (
            majority("ordinal_direction", item_id) == "higher_is_less"
        )
        specs[key] = {
            "kind": "canon", "valid": valid, "reverse": reverse,
            "sentinel": sorted(
                float(v) for v in majority("missing_or_sentinel_codes", item_id)),
        }
    return specs


def canon_outputs(spec: dict) -> list[float]:
    valid = spec["valid"]
    lo, hi = min(valid), max(valid)
    outs = []
    for v in valid:
        oriented = (lo + hi - v) if spec["reverse"] else v
        outs.append((oriented - lo) / (hi - lo) if hi > lo else 0.0)
    return outs


def make_placebo_measurement(
    meas: dict[tuple[str, str], dict], target: str, seed: int
) -> dict[tuple[str, str], dict]:
    specs: dict[tuple[str, str], dict] = {}
    for (cohort, item), spec in meas.items():
        rng = derived_rng(f"ladder_v1|pl_meas|{target}|{seed}|{cohort}|{item}")
        pool = sorted(set(spec["valid"]) | set(spec["sentinel"]))
        n_mask = len(spec["sentinel"])
        masked = set(
            rng.choice(np.asarray(pool), size=n_mask, replace=False).tolist()
        ) if n_mask else set()
        kept = [code for code in pool if code not in masked]
        outputs = list(rng.permutation(np.asarray(canon_outputs(spec))))
        if len(kept) != len(outputs):
            raise RuntimeError(f"placebo capacity mismatch for {cohort}/{item}")
        specs[(cohort, item)] = {
            "kind": "map", "map": {float(c): float(v) for c, v in zip(kept, outputs)},
        }
    return specs


def member_permutation(members: list[str], target: str, seed: int) -> dict[str, str]:
    """Fixed-point-free permutation of the member slots (target-side lesion)."""
    rng = derived_rng(f"ladder_v1|pl_col|{target}|{seed}")
    for _ in range(1000):
        perm = list(rng.permutation(members))
        if all(a != b for a, b in zip(members, perm)):
            return dict(zip(members, perm))
    raise RuntimeError("no derangement found")


def wrong_partition(
    groups: dict[str, list[str]], target: str, seed: int
) -> dict[str, list[str]]:
    """Random partition of the same members with the same size profile."""
    rng = derived_rng(f"ladder_v1|pl_grp|{target}|{seed}")
    members = sorted(m for group in groups.values() for m in group)
    sizes = [len(group) for group in groups.values()]
    names = list(groups)
    true_partition = {frozenset(group) for group in groups.values() if group}
    for _ in range(1000):
        shuffled = list(rng.permutation(members))
        parts, cursor = [], 0
        for size in sizes:
            parts.append(shuffled[cursor:cursor + size])
            cursor += size
        if {frozenset(p) for p in parts if p} != true_partition:
            return dict(zip(names, [sorted(p) for p in parts]))
    raise RuntimeError("no wrong partition found")


def robust_fit(values: np.ndarray, mask: np.ndarray) -> tuple[float, float]:
    support = values[mask]
    support = support[np.isfinite(support)]
    if not len(support):
        return 0.0, 1.0
    center = float(np.median(support))
    q25, q75 = np.quantile(support, [0.25, 0.75])
    scale = float(q75 - q25)
    if not np.isfinite(scale) or scale <= 1.0e-8:
        scale = float(np.std(support))
    if not np.isfinite(scale) or scale <= 1.0e-8:
        scale = 1.0
    return center, scale


def concept_channels(
    member_arrays: dict[str, tuple[np.ndarray, np.ndarray]],
    groups: dict[str, list[str]],
    n_source: int,
) -> tuple[np.ndarray, np.ndarray]:
    """4 channels per group over robust-standardized members (compile_bank math).

    member_arrays: slot -> (fit_block, query_block); fit_block rows are
    [source_train..., support...].  Source params fit on source rows, target
    params fit on the support rows only, applied to support and query.
    """
    n_fit = len(next(iter(member_arrays.values()))[0]) if member_arrays else 0
    n_query = len(next(iter(member_arrays.values()))[1]) if member_arrays else 0
    fit_out, query_out = [], []
    for group_members in groups.values():
        z_fit, z_query = [], []
        for member in group_members:
            fit_block, query_block = member_arrays[member]
            src_mask = np.zeros(len(fit_block), dtype=bool)
            src_mask[:n_source] = True
            c_s, s_s = robust_fit(fit_block, src_mask)
            c_t, s_t = robust_fit(fit_block, ~src_mask)
            z_f = np.full(len(fit_block), np.nan)
            src_obs = src_mask & np.isfinite(fit_block)
            tgt_obs = (~src_mask) & np.isfinite(fit_block)
            z_f[src_obs] = np.clip((fit_block[src_obs] - c_s) / s_s, -10.0, 10.0)
            z_f[tgt_obs] = np.clip((fit_block[tgt_obs] - c_t) / s_t, -10.0, 10.0)
            z_q = np.full(len(query_block), np.nan)
            q_obs = np.isfinite(query_block)
            z_q[q_obs] = np.clip((query_block[q_obs] - c_t) / s_t, -10.0, 10.0)
            z_fit.append(z_f)
            z_query.append(z_q)

        for block, out, n_rows in ((z_fit, fit_out, n_fit), (z_query, query_out, n_query)):
            if not block:
                out.append(np.zeros((n_rows, 4), dtype=np.float64))
                continue
            matrix = np.column_stack(block)
            observed = np.isfinite(matrix)
            counts = observed.sum(axis=1)
            safe = np.where(observed, matrix, 0.0)
            mean = np.divide(safe.sum(axis=1), counts,
                             out=np.zeros(len(matrix)), where=counts > 0)
            centered = np.where(observed, matrix - mean[:, None], 0.0)
            std = np.sqrt(np.divide(np.square(centered).sum(axis=1), counts,
                                    out=np.zeros(len(matrix)), where=counts > 0))
            row_min = np.min(np.where(observed, matrix, np.inf), axis=1)
            row_max = np.max(np.where(observed, matrix, -np.inf), axis=1)
            value_range = np.where(counts > 0, row_max - row_min, 0.0)
            obs_frac = counts / matrix.shape[1]
            out.append(np.column_stack([mean, std, value_range, obs_frac]))
    return np.hstack(fit_out), np.hstack(query_out)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def verify_bank() -> None:
    observed = sha256_file(BANK_LEDGER)
    if observed != EXPECTED_BANK_SHA256:
        raise RuntimeError(f"bank ledger SHA-256 mismatch: {observed}")
    ledger = json.loads(BANK_LEDGER.read_text(encoding="utf-8"))
    candidates = {
        c["canonical_name"]: c for c in ledger["accepted_bank"]["concept_candidates"]
    }
    if set(candidates) != set(RAW_MEMBERS):
        raise RuntimeError(f"bank concepts changed: {sorted(candidates)}")
    for name, sides in RAW_MEMBERS.items():
        for side, expected_cols in sides.items():
            observed_cols = {
                m["column_id"] for m in candidates[name]["members"][side]
            }
            if observed_cols != expected_cols:
                raise RuntimeError(f"bank membership changed: {name}/{side}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nhanes-parquet", type=Path, required=True)
    parser.add_argument("--knhanes-parquet", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--targets", nargs="*", default=list(TARGETS))
    parser.add_argument("--seeds", nargs="*", type=int, default=list(SEEDS))
    parser.add_argument("--support-rows", nargs="*", type=int, default=list(SUPPORT_ROWS))
    parser.add_argument("--threads", type=int, default=3)
    args = parser.parse_args()

    for key, path in (("nhanes", args.nhanes_parquet), ("knhanes", args.knhanes_parquet)):
        observed = sha256_file(path)
        if observed != EXPECTED[key]:
            raise RuntimeError(f"{key} parquet SHA-256 mismatch: {observed}")
    verify_bank()

    from xgboost import XGBRegressor

    sys.path.insert(0, str(BENCH / "scripts"))
    benchmark = _load("crta_bench_ladder", BENCH / "scripts/build_benchmark_table.py")
    original_load_yaml = benchmark.load_yaml
    manifest_path = Path(benchmark.DEFAULT_DATASET_MANIFEST).resolve()

    def load_yaml_patched(path):
        value = original_load_yaml(path)
        if Path(path).resolve() == manifest_path:
            value["datasets"]["nhanes"]["parquet"] = str(args.nhanes_parquet)
            value["datasets"]["knhanes"]["parquet"] = str(args.knhanes_parquet)
        if isinstance(value, dict) and "feature_sets" in value:
            value["feature_sets"][FEATURE_SET] = {
                "description": "ladder_v1 injected feature set (all 20 shared slots)",
                "feature_mode": "explicit_slots",
                "slots": list(ALL_SLOTS),
            }
        return value

    benchmark.load_yaml = load_yaml_patched
    benchmark.recode_questionnaire_series = spec_interpreter

    meas_specs = load_llm_measurement()
    args.out_root.mkdir(parents=True, exist_ok=True)
    (args.out_root / "MEASUREMENT_TABLE_V1.json").write_text(json.dumps(
        {f"{c}/{i}": s for (c, i), s in meas_specs.items()},
        indent=1, sort_keys=True) + "\n", encoding="utf-8")

    def build(target: str, seed: int, rule_specs) -> dict:
        benchmark.load_questionnaire_rule_index = (
            (lambda path=None: {}) if rule_specs is None
            else (lambda path=None, s=rule_specs: make_rule_index(s))
        )
        bundle = benchmark.build_single_target_table(
            benchmark_id=BENCHMARK_ID, target_name=target,
            fewshot_frac=0.10, seed=seed,
            target_set_override="objective_anchor_targets_v1_safe",
            feature_set_override=FEATURE_SET,
        )
        x_train = bundle["X_train"].reset_index(drop=True)
        x_test = bundle["X_test"].reset_index(drop=True)
        slots = {}
        for slot in ALL_SLOTS:
            if slot == target:
                continue  # the builder drops the endpoint's own slot from X
            column = f"slot__{slot}"
            slots[slot] = (
                pd.to_numeric(x_train[column], errors="coerce").to_numpy(np.float64),
                pd.to_numeric(x_test[column], errors="coerce").to_numpy(np.float64),
            )
        origin = np.asarray(bundle["train_origin"], dtype=object)
        return {
            "slots": slots,
            "y_train": pd.to_numeric(bundle["y_train"], errors="coerce").to_numpy(np.float64),
            "y_test": pd.to_numeric(bundle["y_test"], errors="coerce").to_numpy(np.float64),
            "n_source": int(np.sum(origin == "source")),
        }

    for target in args.targets:
        for seed in args.seeds:
            out = args.out_root / target / f"seed_{seed}"
            if (out / "metrics.json").is_file():
                continue
            t0 = time.time()

            plmeas_specs = make_placebo_measurement(meas_specs, target, seed)
            bundles = {
                "raw": build(target, seed, None),
                "meas": build(target, seed, meas_specs),
                "plmeas": build(target, seed, plmeas_specs),
            }
            n_source = bundles["raw"]["n_source"]
            n_train = len(bundles["raw"]["y_train"])
            n_pool = n_train - n_source
            for name, bundle in bundles.items():
                if bundle["n_source"] != n_source or len(bundle["y_train"]) != n_train:
                    raise RuntimeError(f"bundle {name} changed the split")
                if not np.allclose(bundle["y_train"], bundles["raw"]["y_train"],
                                   equal_nan=True):
                    raise RuntimeError(f"bundle {name} changed the labels")

            members_e = [m for m in MEMBER_SLOTS if m != target]
            groups_e = {name: [m for m in group if m != target]
                        for name, group in GROUPS.items()}
            dropped = {name: [m for m in group if m == target]
                       for name, group in GROUPS.items()}
            col_perm = member_permutation(members_e, target, seed)
            grp_wrong = wrong_partition(groups_e, target, seed)

            y_train = bundles["raw"]["y_train"]
            y_test = bundles["raw"]["y_test"]
            query_sd = float(np.std(y_test, ddof=0))
            results: dict = {}

            for K in args.support_rows:
                pick = np.sort(np.random.default_rng(seed * 131 + K).choice(
                    n_pool, size=min(K, n_pool), replace=False))
                sup_rows = np.arange(n_source, n_train)[pick]
                fit_rows = np.concatenate([np.arange(n_source), sup_rows])
                y_fit = y_train[fit_rows]
                weights = np.concatenate([
                    np.ones(n_source),
                    np.full(len(sup_rows), n_source / max(len(sup_rows), 1)),
                ])
                results[str(K)] = {}

                def slot_blocks(bundle, slot, permute_target_side=False):
                    source_slot = slot
                    target_slot = col_perm[slot] if permute_target_side else slot
                    train_src = bundle["slots"][source_slot][0]
                    train_tgt = bundle["slots"][target_slot][0]
                    fit = np.concatenate([train_src[:n_source], train_tgt[sup_rows]])
                    query = bundle["slots"][target_slot][1]
                    return fit, query

                for arm in ARMS:
                    bundle = bundles[ARM_BUNDLE[arm]]
                    permuted = arm == "pl_columns"
                    fit_parts, query_parts = [], []

                    for slot in BASE_SLOTS:
                        fit, query = slot_blocks(bundle, slot)
                        fit_parts.append(fit)
                        query_parts.append(query)

                    if arm not in ("rung0_base", "is_target", "loo_columns"):
                        for slot in members_e:
                            fit, query = slot_blocks(
                                bundle, slot, permute_target_side=permuted)
                            fit_parts.append(fit)
                            query_parts.append(query)

                    if arm in ("rung2_grouping", "rung3_measurement",
                               "pl_grouping", "pl_measurement", "loo_columns"):
                        grouping = grp_wrong if arm == "pl_grouping" else groups_e
                        member_arrays = {
                            slot: slot_blocks(bundle, slot) for slot in members_e
                        }
                        chan_fit, chan_query = concept_channels(
                            member_arrays, grouping, n_source)
                        fit_parts.extend(chan_fit.T)
                        query_parts.extend(chan_query.T)

                    if arm == "is_target":
                        fit_parts.append(np.concatenate(
                            [np.zeros(n_source), np.ones(len(sup_rows))]))
                        query_parts.append(np.ones(len(y_test)))

                    x_fit = np.column_stack(fit_parts)
                    x_query = np.column_stack(query_parts)
                    model = XGBRegressor(
                        n_estimators=300, max_depth=6, learning_rate=0.05,
                        subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0,
                        n_jobs=args.threads, random_state=seed,
                        tree_method="hist",
                    )
                    model.fit(x_fit, y_fit, sample_weight=weights)
                    pred = model.predict(x_query)
                    results[str(K)][arm] = float(
                        np.sqrt(np.mean((y_test - pred) ** 2)) / query_sd)
                results[str(K)]["loo_measurement"] = results[str(K)]["rung2_grouping"]

            out.mkdir(parents=True, exist_ok=True)
            (out / "metrics.json").write_text(json.dumps({
                "target": target, "seed": seed,
                "benchmark_id": BENCHMARK_ID, "feature_set": FEATURE_SET,
                "metric": "query_sd_normalized_rmse (lower is better)",
                "backbone": "xgboost_hist_d6_n300",
                "arms": list(ARMS) + ["loo_measurement (alias of rung2_grouping)"],
                "primary_k": PRIMARY_K,
                "n_source": n_source, "n_pool": n_pool, "n_query": int(len(y_test)),
                "member_slots": members_e,
                "dropped_members_by_group": dropped,
                "pl_columns_permutation": col_perm,
                "pl_grouping_partition": grp_wrong,
                "pl_measurement_table": {
                    f"{c}/{i}": s for (c, i), s in plmeas_specs.items()},
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
