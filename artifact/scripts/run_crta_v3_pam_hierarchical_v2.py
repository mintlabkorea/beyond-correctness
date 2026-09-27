#!/usr/bin/env python3
"""PAM hierarchical gating v2: within-group + selectively-between channels.

Frozen design: `iclr_latex_v3/M1M2_PAM_HIERARCHICAL_GATING_PREREGISTRATION_V2.md`.
Computes two arms per cell (`h_gated`, `h_gated_pl`) and copies the reused
arms (`free`, `adj_concept`, `pl_adj`) from the PAM v1 cells (identical
splits).  The between-group channel opens cross-concept member interactions
only for the extracted coupled pairs (majority of 3 isolated samples).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ADJ_DIR = ROOT / "experiments/crta_v3_concept_adjacency_extraction_v1/responses"
V1_RUNNER = ROOT / "scripts/run_crta_v3_pam_constraint_relations_v1.py"
REUSED_ARMS = ("free", "adj_concept", "pl_adj")
NEW_ARMS = ("h_gated", "h_gated_pl")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_coupled_pairs(concepts: list[str]) -> tuple[list[tuple[str, str]], dict]:
    samples = []
    for path in sorted(ADJ_DIR.glob("raw_s*.txt")):
        match = re.search(r"\{.*\}", path.read_text(encoding="utf-8"), re.S)
        if not match:
            continue
        try:
            payload = json.loads(match.group(0))
        except ValueError:
            continue
        samples.append({
            frozenset((p["a"], p["b"])): p for p in payload["pairs"]
        })
    if len(samples) < 2:
        raise RuntimeError("fewer than 2 parseable adjacency samples")

    all_pairs = [frozenset(p) for p in itertools.combinations(concepts, 2)]
    majority, audit = {}, []
    for pair in all_pairs:
        votes = [s[pair]["adjacency"] for s in samples if pair in s]
        if not votes:
            raise RuntimeError(f"pair missing from every sample: {sorted(pair)}")
        value = next((v for v in votes if votes.count(v) >= 2), votes[0])
        majority[pair] = int(value)
        audit.append({"pair": sorted(pair), "votes": votes, "majority": int(value)})
    coupled = [tuple(sorted(p)) for p, v in majority.items() if v == 1]
    return coupled, {"n_samples": len(samples), "pairs": audit}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nhanes-parquet", type=Path, required=True)
    parser.add_argument("--knhanes-parquet", type=Path, required=True)
    parser.add_argument("--v1-root", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--targets", nargs="*", default=None)
    parser.add_argument("--seeds", nargs="*", type=int, default=None)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()

    v1 = _load("pam_v1_for_v2", V1_RUNNER)
    for key, path in (("nhanes", args.nhanes_parquet), ("knhanes", args.knhanes_parquet)):
        observed = v1.sha256_file(path)
        if observed != v1.EXPECTED[key]:
            raise RuntimeError(f"{key} parquet SHA-256 mismatch: {observed}")

    from xgboost import XGBRegressor

    sys.path.insert(0, str(v1.BENCH / "scripts"))
    benchmark = _load("crta_bench_pam2", v1.BENCH / "scripts/build_benchmark_table.py")
    original_load_yaml = benchmark.load_yaml
    manifest_path = Path(benchmark.DEFAULT_DATASET_MANIFEST).resolve()

    def load_yaml_patched(path):
        value = original_load_yaml(path)
        if Path(path).resolve() == manifest_path:
            value["datasets"]["nhanes"]["parquet"] = str(args.nhanes_parquet)
            value["datasets"]["knhanes"]["parquet"] = str(args.knhanes_parquet)
        if isinstance(value, dict) and "feature_sets" in value:
            value["feature_sets"][v1.FEATURE_SET] = {
                "description": "pam_constraint_v1 injected feature set",
                "feature_mode": "explicit_slots", "slots": list(v1.ALL_SLOTS)}
        return value

    benchmark.load_yaml = load_yaml_patched

    concepts = list(v1.GROUPS)
    coupled, audit = load_coupled_pairs(concepts)
    if len(coupled) in (0, 6):
        raise RuntimeError(
            f"degenerate concept graph ({len(coupled)}/6 coupled); "
            "per the prereg gate this experiment must not run")
    args.out_root.mkdir(parents=True, exist_ok=True)
    (args.out_root / "ADJACENCY_MAJORITY.json").write_text(
        json.dumps({"coupled_pairs": coupled, **audit}, indent=1) + "\n",
        encoding="utf-8")

    all_pairs = [tuple(sorted(p)) for p in itertools.combinations(concepts, 2)]

    def gated_groups(feature_names, groups_e, pairs):
        base = v1.interaction_groups(feature_names, groups_e)
        index = {name: i for i, name in enumerate(feature_names)}
        base_idx = [index[s] for s in feature_names if s in v1.BASE_SLOTS]
        for a, b in pairs:
            merged = [index[m] for m in groups_e[a] + groups_e[b] if m in index]
            if merged:
                base.append(sorted(base_idx + merged))
        return base

    targets = args.targets or list(v1.TARGETS)
    seeds = args.seeds or list(v1.SEEDS)
    for target in targets:
        feature_names = [s for s in v1.ALL_SLOTS if s != target]
        groups_e = {name: [m for m in group if m != target]
                    for name, group in v1.GROUPS.items()}
        for seed in seeds:
            out = args.out_root / target / f"seed_{seed}"
            if (out / "metrics.json").is_file():
                continue
            v1_cell = args.v1_root / target / f"seed_{seed}" / "metrics.json"
            if not v1_cell.is_file():
                raise RuntimeError(f"v1 cell missing: {v1_cell}")
            v1_metrics = json.loads(v1_cell.read_text(encoding="utf-8"))
            t0 = time.time()

            rng = v1.derived_rng(f"pam_v2|pl_pairs|{target}|{seed}")
            for _ in range(1000):
                pick = rng.choice(len(all_pairs), size=len(coupled), replace=False)
                placebo_pairs = [all_pairs[int(k)] for k in sorted(pick)]
                if set(placebo_pairs) != set(coupled):
                    break
            else:
                raise RuntimeError("no placebo pair draw found")

            bundle = benchmark.build_single_target_table(
                benchmark_id=v1.BENCHMARK_ID, target_name=target,
                fewshot_frac=0.10, seed=seed,
                target_set_override="objective_anchor_targets_v1_safe",
                feature_set_override=v1.FEATURE_SET,
            )
            x_train = bundle["X_train"].reset_index(drop=True)
            x_test = bundle["X_test"].reset_index(drop=True)
            x_all = x_train[[f"slot__{s}" for s in feature_names]].apply(
                pd.to_numeric, errors="coerce").to_numpy(np.float64)
            x_q = x_test[[f"slot__{s}" for s in feature_names]].apply(
                pd.to_numeric, errors="coerce").to_numpy(np.float64)
            y_train = pd.to_numeric(
                bundle["y_train"], errors="coerce").to_numpy(np.float64)
            y_test = pd.to_numeric(
                bundle["y_test"], errors="coerce").to_numpy(np.float64)
            origin = np.asarray(bundle["train_origin"], dtype=object)
            n_source = int(np.sum(origin == "source"))
            n_pool = len(x_all) - n_source
            query_sd = float(np.std(y_test, ddof=0))

            arm_groups = {
                "h_gated": gated_groups(feature_names, groups_e, coupled),
                "h_gated_pl": gated_groups(feature_names, groups_e, placebo_pairs),
            }

            results: dict = {}
            for K in v1.SUPPORT_ROWS:
                pick_rows = np.sort(np.random.default_rng(seed * 131 + K).choice(
                    n_pool, size=min(K, n_pool), replace=False))
                rows = np.arange(n_source, len(x_all))[pick_rows]
                x_fit = np.vstack([x_all[:n_source], x_all[rows]])
                y_fit = np.concatenate([y_train[:n_source], y_train[rows]])
                weights = np.concatenate([
                    np.ones(n_source),
                    np.full(len(rows), n_source / max(len(rows), 1)),
                ])
                results[str(K)] = {
                    arm: v1_metrics["nrmse"][str(K)][arm] for arm in REUSED_ARMS
                }
                for arm in NEW_ARMS:
                    model = XGBRegressor(
                        n_estimators=300, max_depth=6, learning_rate=0.05,
                        subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0,
                        n_jobs=args.threads, random_state=seed,
                        tree_method="hist",
                        interaction_constraints=json.dumps(arm_groups[arm]),
                    )
                    model.fit(x_fit, y_fit, sample_weight=weights)
                    pred = model.predict(x_q)
                    results[str(K)][arm] = float(
                        np.sqrt(np.mean((y_test - pred) ** 2)) / query_sd)

            out.mkdir(parents=True, exist_ok=True)
            (out / "metrics.json").write_text(json.dumps({
                "target": target, "seed": seed,
                "metric": "query_sd_normalized_rmse (lower is better)",
                "arms": list(REUSED_ARMS) + list(NEW_ARMS),
                "primary_k": v1.PRIMARY_K,
                "coupled_pairs": coupled, "placebo_pairs": placebo_pairs,
                "reused_from_v1": str(v1_cell),
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
