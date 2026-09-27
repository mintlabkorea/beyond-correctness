#!/usr/bin/env python3
"""F: form x lesion-severity, matched, all arms fit in one process per cell.

Frozen design: `iclr_latex_v3/FORM_LESION_MATCHED_PREREGISTRATION_V1.md`.
Seven arms on identical cells: free; value form (documented / random
pairs / documented-with-negated-differences); constraint form
(documented / random slots+signs / flipped signs).  The negated-value arm
tests the mechanistic claim that a tree cannot represent direction
information carried by an added feature.
"""

from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PAM = ROOT / "scripts/run_crta_v3_pam_constraint_relations_v1.py"
ARMS = ("free", "val_documented", "val_random", "val_documented_negated",
        "sign_documented", "sign_random", "sign_flipped")
# Frozen documented pairs (undirected) and their signs, from
# run_crta_v3_m1m2_monotone_anchor_v1.py DOCUMENTED_SIGNS.
DOC_PAIRS = (
    ("age", "sbp"), ("dbp", "sbp"), ("hba1c", "glucose"),
    ("total_cholesterol", "triglycerides"), ("weight_kg", "waist_cm"),
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def value_block(arrays: dict[str, np.ndarray], pairs, negate: bool
                ) -> list[np.ndarray]:
    block = []
    for a, b in pairs:
        va, vb = arrays[a], arrays[b]
        block.append((vb - va) if negate else (va - vb))
        block.append(va * vb)  # symmetric; no negated counterpart exists
    return block


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nhanes-parquet", type=Path, required=True)
    parser.add_argument("--knhanes-parquet", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--targets", nargs="*", default=None)
    parser.add_argument("--seeds", nargs="*", type=int, default=None)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()

    pam = _load("pam_for_form_lesion", PAM)
    for key, path in (("nhanes", args.nhanes_parquet),
                      ("knhanes", args.knhanes_parquet)):
        observed = pam.sha256_file(path)
        if observed != pam.EXPECTED[key]:
            raise RuntimeError(f"{key} parquet SHA-256 mismatch: {observed}")

    from xgboost import XGBRegressor

    sys.path.insert(0, str(pam.BENCH / "scripts"))
    benchmark = _load("crta_bench_form_lesion",
                      pam.BENCH / "scripts/build_benchmark_table.py")
    original_load_yaml = benchmark.load_yaml
    manifest_path = Path(benchmark.DEFAULT_DATASET_MANIFEST).resolve()

    def load_yaml_patched(path):
        value = original_load_yaml(path)
        if Path(path).resolve() == manifest_path:
            value["datasets"]["nhanes"]["parquet"] = str(args.nhanes_parquet)
            value["datasets"]["knhanes"]["parquet"] = str(args.knhanes_parquet)
        if isinstance(value, dict) and "feature_sets" in value:
            value["feature_sets"][pam.FEATURE_SET] = {
                "description": "pam_constraint_v1 injected feature set",
                "feature_mode": "explicit_slots", "slots": list(pam.ALL_SLOTS)}
        return value

    benchmark.load_yaml = load_yaml_patched
    args.out_root.mkdir(parents=True, exist_ok=True)

    targets = args.targets or list(pam.TARGETS)
    seeds = args.seeds or list(pam.SEEDS)
    for target in targets:
        feature_names = [s for s in pam.ALL_SLOTS if s != target]
        doc_pairs = [p for p in DOC_PAIRS
                     if target not in p and all(m in feature_names for m in p)]
        member_pool = [s for s in pam.MEMBER_SLOTS if s != target]
        pair_pool = [tuple(sorted(p)) for p in
                     itertools.combinations(member_pool, 2)]
        doc_set = {tuple(sorted(p)) for p in doc_pairs}
        doc_signs = pam.DOCUMENTED_SIGNS.get(target, {})

        for seed in seeds:
            out = args.out_root / target / f"seed_{seed}"
            if (out / "metrics.json").is_file():
                continue
            t0 = time.time()

            rng_pairs = pam.derived_rng(
                f"form_lesion_v1|val_random|{target}|{seed}")
            random_pairs = None
            for _ in range(1000):
                pick = rng_pairs.choice(len(pair_pool), size=len(doc_pairs),
                                        replace=False)
                candidate = [pair_pool[int(k)] for k in sorted(pick)]
                if set(candidate) != doc_set:
                    random_pairs = candidate
                    break
            if random_pairs is None:
                raise RuntimeError("no random pair draw found")

            rng_signs = pam.derived_rng(
                f"form_lesion_v1|sign_random|{target}|{seed}")
            random_slots = rng_signs.choice(
                len(feature_names), size=max(len(doc_signs), 1), replace=False)
            sign_random = [0] * len(feature_names)
            for k in random_slots:
                sign_random[int(k)] = int(rng_signs.choice([-1, 1]))
            sign_doc = [0] * len(feature_names)
            sign_flip = [0] * len(feature_names)
            for feature, sign in doc_signs.items():
                if feature in feature_names:
                    index = feature_names.index(feature)
                    sign_doc[index] = int(sign)
                    sign_flip[index] = -int(sign)

            bundle = benchmark.build_single_target_table(
                benchmark_id=pam.BENCHMARK_ID, target_name=target,
                fewshot_frac=0.10, seed=seed,
                target_set_override="objective_anchor_targets_v1_safe",
                feature_set_override=pam.FEATURE_SET,
            )
            x_train = bundle["X_train"].reset_index(drop=True)
            x_test = bundle["X_test"].reset_index(drop=True)
            fit_arrays = {s: pd.to_numeric(
                x_train[f"slot__{s}"], errors="coerce").to_numpy(np.float64)
                for s in feature_names}
            query_arrays = {s: pd.to_numeric(
                x_test[f"slot__{s}"], errors="coerce").to_numpy(np.float64)
                for s in feature_names}
            y_train = pd.to_numeric(
                bundle["y_train"], errors="coerce").to_numpy(np.float64)
            y_test = pd.to_numeric(
                bundle["y_test"], errors="coerce").to_numpy(np.float64)
            origin = np.asarray(bundle["train_origin"], dtype=object)
            n_source = int(np.sum(origin == "source"))
            n_pool = len(y_train) - n_source
            query_sd = float(np.std(y_test, ddof=0))

            base_fit = np.column_stack([fit_arrays[s] for s in feature_names])
            base_query = np.column_stack(
                [query_arrays[s] for s in feature_names])

            def stack(block_fit, block_query):
                return (np.column_stack([base_fit] + [b[:, None] for b in block_fit]),
                        np.column_stack([base_query] + [b[:, None] for b in block_query]))

            designs = {
                "free": (base_fit, base_query, {}),
                "sign_documented": (base_fit, base_query,
                                    {"monotone_constraints": tuple(sign_doc)}),
                "sign_random": (base_fit, base_query,
                                {"monotone_constraints": tuple(sign_random)}),
                "sign_flipped": (base_fit, base_query,
                                 {"monotone_constraints": tuple(sign_flip)}),
            }
            for arm, pairs, negate in (
                    ("val_documented", doc_pairs, False),
                    ("val_random", random_pairs, False),
                    ("val_documented_negated", doc_pairs, True)):
                fit_matrix, query_matrix = stack(
                    value_block(fit_arrays, pairs, negate),
                    value_block(query_arrays, pairs, negate))
                designs[arm] = (fit_matrix, query_matrix, {})

            results: dict = {}
            for K in pam.SUPPORT_ROWS:
                pick_rows = np.sort(np.random.default_rng(seed * 131 + K).choice(
                    n_pool, size=min(K, n_pool), replace=False))
                rows = np.arange(n_source, len(y_train))[pick_rows]
                fit_rows = np.concatenate([np.arange(n_source), rows])
                y_fit = y_train[fit_rows]
                weights = np.concatenate([
                    np.ones(n_source),
                    np.full(len(rows), n_source / max(len(rows), 1)),
                ])
                results[str(K)] = {}
                for arm in ARMS:
                    fit_matrix, query_matrix, params = designs[arm]
                    model = XGBRegressor(
                        n_estimators=300, max_depth=6, learning_rate=0.05,
                        subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0,
                        n_jobs=args.threads, random_state=seed,
                        tree_method="hist", **params,
                    )
                    model.fit(fit_matrix[fit_rows], y_fit, sample_weight=weights)
                    pred = model.predict(query_matrix)
                    results[str(K)][arm] = float(
                        np.sqrt(np.mean((y_test - pred) ** 2)) / query_sd)

            out.mkdir(parents=True, exist_ok=True)
            (out / "metrics.json").write_text(json.dumps({
                "target": target, "seed": seed,
                "metric": "query_sd_normalized_rmse (lower is better)",
                "arms": list(ARMS), "primary_k": pam.PRIMARY_K,
                "documented_pairs": [list(p) for p in doc_pairs],
                "random_pairs": [list(p) for p in random_pairs],
                "documented_signs": doc_signs,
                "n_source": n_source, "n_pool": n_pool,
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
