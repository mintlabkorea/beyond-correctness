#!/usr/bin/env python3
"""W5-R: matched exchangeable-random wrong control on the frozen PAM cells.

Frozen design and verdicts:
`iclr_latex_v3/RELATION_MATCHED_RANDOM_WRONG_PREREGISTRATION_V1.md`.

Re-fits `free`, `sign_documented`, `pl_sign_flip` (replication gate against the
frozen PAM cells) and adds D = 5 matched-count random-direction arms
`sign_random_1..5` per cell.  The frozen PAM runner is imported unmodified for
bundle construction, constants, the sign-vector builder and the keyed RNG.
Arms differ only in `monotone_constraints`.  Metric: query-SD-normalized RMSE
(lower is better).  Aggregate metrics only.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PAM_RUNNER = ROOT / "scripts/run_crta_v3_pam_constraint_relations_v1.py"
PREREG = ROOT / "iclr_latex_v3/RELATION_MATCHED_RANDOM_WRONG_PREREGISTRATION_V1.md"
RNG_NS = "relation_random_wrong_v1"
N_DRAWS = 5
REPLICATION_TOL = 1e-9
GATE_ARMS = ("free", "sign_documented", "pl_sign_flip")
SEED_SETS: dict[str, tuple[int, ...]] = {
    "v1": tuple(range(50, 60)),
    "rep1": tuple(range(60, 70)),
}
FROZEN_ROOTS: dict[str, Path] = {
    "v1": ROOT / "experiments/crta_v3_pam_constraint_relations_v1",
    "rep1": ROOT / "experiments/crta_v3_pam_constraint_relations_v1_rep1",
}


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pam = _load("crta_pam_v1_frozen", PAM_RUNNER)


def random_arm_names(n_draws: int = N_DRAWS) -> tuple[str, ...]:
    return tuple(f"sign_random_{d}" for d in range(1, n_draws + 1))


def random_sign_vectors(feature_names: list[str], target: str, seed: int,
                        n_draws: int = N_DRAWS) -> list[tuple[int, ...]]:
    """D distinct matched-count random-direction vectors for one cell.

    k = number of documented features present; k distinct slots drawn uniformly
    from the endpoint's feature list excluding the documented features, each
    with an independent sign in {-1, +1}; a draw equal to an earlier draw of
    the same cell is rejected (frozen rule, prereg section 2)."""
    documented = pam.sign_vector(feature_names, target, flip=False)
    flipped = pam.sign_vector(feature_names, target, flip=True)
    k = int(sum(1 for s in documented if s != 0))
    if k < 1:
        raise ValueError(f"no documented relation present for {target}")
    # exchangeable slots exclude the documented features, so a draw can never
    # contain a correct (or reversed) documented relation (prereg section 2)
    candidates = np.array([i for i, s in enumerate(documented) if s == 0])
    forbidden = {documented, flipped}
    draws: list[tuple[int, ...]] = []
    for draw in range(1, n_draws + 1):
        rng = pam.derived_rng(f"{RNG_NS}|sign_random|{target}|{seed}|{draw}")
        found = None
        for _ in range(1000):
            slots = rng.choice(candidates, size=k, replace=False)
            signs = rng.choice((-1, 1), size=k)
            vector = [0] * len(feature_names)
            for slot, sign in zip(slots, signs):
                vector[int(slot)] = int(sign)
            candidate = tuple(vector)
            if candidate not in forbidden:
                found = candidate
                break
        if found is None:
            raise RuntimeError(f"no admissible random draw for {target}/{seed}/{draw}")
        forbidden.add(found)
        draws.append(found)
    return draws


def gate_against_frozen(frozen: dict, results: dict, support_rows) -> dict:
    """Compare re-fit gate arms with the frozen PAM cell at every K."""
    worst = 0.0
    compared = 0
    for K in support_rows:
        key = str(K)
        for arm in GATE_ARMS:
            delta = abs(float(frozen["nrmse"][key][arm]) - float(results[key][arm]))
            worst = max(worst, delta)
            compared += 1
    return {"passed": bool(worst <= REPLICATION_TOL), "worst_abs_delta_nrmse": worst,
            "n_comparisons": compared, "tolerance": REPLICATION_TOL}


def cell_complete(path: Path, arms: tuple[str, ...], support_rows) -> bool:
    if not path.is_file():
        return False
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return all(arm in record.get("nrmse", {}).get(str(K), {})
               for K in support_rows for arm in arms)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nhanes-parquet", type=Path, required=True)
    parser.add_argument("--knhanes-parquet", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--seed-set", choices=sorted(SEED_SETS), required=True)
    parser.add_argument("--targets", nargs="*", default=list(pam.TARGETS))
    parser.add_argument("--seeds", nargs="*", type=int, default=None)
    parser.add_argument("--support-rows", nargs="*", type=int,
                        default=list(pam.SUPPORT_ROWS))
    parser.add_argument("--draws", type=int, default=N_DRAWS)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--frozen-root", type=Path, default=None,
                        help="override the frozen PAM root used by the gate")
    args = parser.parse_args()

    seeds = tuple(args.seeds) if args.seeds else SEED_SETS[args.seed_set]
    frozen_root = args.frozen_root or FROZEN_ROOTS[args.seed_set]
    parquet_sha = {}
    for key, path in (("nhanes", args.nhanes_parquet), ("knhanes", args.knhanes_parquet)):
        observed = pam.sha256_file(path)
        if observed != pam.EXPECTED[key]:
            raise RuntimeError(f"{key} parquet SHA-256 mismatch: {observed}")
        parquet_sha[key] = observed

    import sklearn
    import xgboost
    from xgboost import XGBRegressor

    provenance = {
        "prereg_sha256": pam.sha256_file(PREREG),
        "runner_sha256": pam.sha256_file(Path(__file__).resolve()),
        "pam_runner_sha256": pam.sha256_file(PAM_RUNNER),
        "parquet_sha256": parquet_sha,
        "versions": {"xgboost": xgboost.__version__, "numpy": np.__version__,
                     "pandas": pd.__version__, "sklearn": sklearn.__version__,
                     "python": platform.python_version()},
        "host": platform.node(),
        "threads": args.threads,
    }

    sys.path.insert(0, str(pam.BENCH / "scripts"))
    benchmark = _load("crta_bench_rrw", pam.BENCH / "scripts/build_benchmark_table.py")
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
    random_arms = random_arm_names(args.draws)
    arms = GATE_ARMS + random_arms
    out_base = args.out_root / args.seed_set
    out_base.mkdir(parents=True, exist_ok=True)

    for target in args.targets:
        feature_names = [s for s in pam.ALL_SLOTS if s != target]
        for seed in seeds:
            out = out_base / target / f"seed_{seed}"
            if cell_complete(out / "metrics.json", arms, args.support_rows):
                continue
            frozen_path = frozen_root / target / f"seed_{seed}" / "metrics.json"
            if not frozen_path.is_file():
                raise FileNotFoundError(f"frozen PAM cell missing: {frozen_path}")
            frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
            t0 = time.time()

            bundle = benchmark.build_single_target_table(
                benchmark_id=pam.BENCHMARK_ID, target_name=target,
                fewshot_frac=0.10, seed=seed,
                target_set_override="objective_anchor_targets_v1_safe",
                feature_set_override=pam.FEATURE_SET,
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
            if int(frozen["n_source"]) != n_source or int(frozen["n_pool"]) != n_pool:
                raise RuntimeError(f"cell construction drift at {target}/{seed}: "
                                   f"n_source {n_source} vs {frozen['n_source']}, "
                                   f"n_pool {n_pool} vs {frozen['n_pool']}")

            signs_doc = pam.sign_vector(feature_names, target, flip=False)
            signs_flip = pam.sign_vector(feature_names, target, flip=True)
            randoms = random_sign_vectors(feature_names, target, seed, args.draws)
            arm_params = {
                "free": {},
                "sign_documented": {"monotone_constraints": signs_doc},
                "pl_sign_flip": {"monotone_constraints": signs_flip},
            }
            for name, vector in zip(random_arms, randoms):
                arm_params[name] = {"monotone_constraints": vector}

            results: dict = {}
            for K in args.support_rows:
                pick = np.sort(np.random.default_rng(seed * 131 + K).choice(
                    n_pool, size=min(K, n_pool), replace=False))
                rows = np.arange(n_source, len(x_all))[pick]
                x_fit = np.vstack([x_all[:n_source], x_all[rows]])
                y_fit = np.concatenate([y_train[:n_source], y_train[rows]])
                weights = np.concatenate([
                    np.ones(n_source),
                    np.full(len(rows), n_source / max(len(rows), 1)),
                ])
                results[str(K)] = {}
                for arm in arms:
                    model = XGBRegressor(
                        n_estimators=300, max_depth=6, learning_rate=0.05,
                        subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0,
                        n_jobs=args.threads, random_state=seed,
                        tree_method="hist", **arm_params[arm],
                    )
                    model.fit(x_fit, y_fit, sample_weight=weights)
                    pred = model.predict(x_q)
                    results[str(K)][arm] = float(
                        np.sqrt(np.mean((y_test - pred) ** 2)) / query_sd)

            gate = gate_against_frozen(frozen, results, args.support_rows)
            out.mkdir(parents=True, exist_ok=True)
            (out / "metrics.json").write_text(json.dumps({
                "target": target, "seed": seed, "seed_set": args.seed_set,
                "benchmark_id": pam.BENCHMARK_ID, "feature_set": pam.FEATURE_SET,
                "metric": "query_sd_normalized_rmse (lower is better)",
                "backbone": "xgboost_hist_d6_n300",
                "arms": list(arms), "primary_k": pam.PRIMARY_K,
                "n_draws": args.draws,
                "n_source": n_source, "n_pool": n_pool,
                "n_query": int(len(y_test)),
                "feature_names": feature_names,
                "documented_signs": pam.DOCUMENTED_SIGNS[target],
                "n_constrained": int(sum(1 for s in signs_doc if s != 0)),
                "sign_vectors": {"sign_documented": list(signs_doc),
                                 "pl_sign_flip": list(signs_flip),
                                 **{name: list(v) for name, v in zip(random_arms, randoms)}},
                "replication_gate": gate,
                "frozen_cell": str(frozen_path.relative_to(ROOT)),
                "provenance": provenance,
                "wall_seconds": round(time.time() - t0, 1),
                "nrmse": results,
            }, indent=1, sort_keys=True) + "\n", encoding="utf-8")
            print(json.dumps({"seed_set": args.seed_set, "target": target,
                              "seed": seed, "gate": gate["passed"],
                              "worst_delta": gate["worst_abs_delta_nrmse"],
                              "wall_seconds": round(time.time() - t0, 1),
                              "done": True}), flush=True)

    print(json.dumps({"status": "complete", "seed_set": args.seed_set}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
