#!/usr/bin/env python3
"""G-SIGN-CAMELS v2: basin-clustered, higher-powered re-run (addendum GC-v2).

Imports the frozen CAMELS native-screen runner unmodified and reuses its
loaders, basin-level split, robust channels, estimator and metrics; only
the monotone-constraint vector varies across arms.  The documented
directions are the water-balance core (Q = P - ET - dS): precipitation
family +1, potential-evapotranspiration family -1, everything else 0
(temperature, radiation, snow water equivalent and day length are left
unconstrained because their sign is regime-dependent).

Design and predictions:
`iclr_latex_v3/SCHEMA_PAIR_GENERALIZATION_PREREGISTRATION_V1.md` (G-SIGN-CAMELS).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCREEN = ROOT / "scripts/run_crta_v3_camels_native_screen_v1.py"
DATA = ROOT / "experiments/crta_v3_camels_native_screen_v1/data"
ARMS = ("free", "sign_documented", "sign_flipped", "sign_random")
TARGET_WEIGHT = 10.0
SEEDS = tuple(range(20, 40))
SUPPORT_BASINS = (1, 3, 5)

# Water-balance direction knowledge, on the raw feature name prefixes.
POSITIVE_PREFIXES = ("prcp", "precipitation_")
NEGATIVE_PREFIXES = ("pet_", "peti_")


def documented_sign(feature: str) -> int:
    """+1 for precipitation-family, -1 for PET-family, 0 otherwise.

    Trailing-mean derivatives inherit their parent's direction because the
    transform is a positive-weighted average.
    """
    stem = feature.split("__")[0]
    if any(stem.startswith(p) for p in POSITIVE_PREFIXES):
        return 1
    if any(stem.startswith(p) for p in NEGATIVE_PREFIXES):
        return -1
    return 0


def derived_rng(key: str) -> np.random.Generator:
    return np.random.default_rng(int(hashlib.sha256(key.encode()).hexdigest()[:16], 16))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--seeds", nargs="*", type=int, default=None)
    parser.add_argument("--support-basins", nargs="*", type=int, default=None)
    parser.add_argument("--n-jobs", type=int, default=2)
    args = parser.parse_args()

    screen = _load("camels_screen_for_probe", SCREEN)
    from xgboost import XGBRegressor

    source = pd.read_pickle(DATA / "source.pkl").reset_index(drop=True)
    target_all = pd.read_pickle(DATA / "target.pkl").reset_index(drop=True)
    split = screen.load_json(DATA / "split_manifest.json")
    payload = screen.load_json(screen.PAYLOAD_PATH)

    source_ids = screen.eligible_ids(payload, "source")
    target_ids = screen.eligible_ids(payload, "target")
    derived = sorted({
        column for frame in (source, target_all) for column in frame.columns
        if "__trailmean_" in column})
    base_features = sorted(set(source_ids) | set(target_ids) | set(derived))
    signs_doc_raw = [documented_sign(f) for f in base_features]
    n_constrained = sum(1 for s in signs_doc_raw if s != 0)
    if n_constrained == 0:
        raise RuntimeError("no documented feature present in the CAMELS Base")

    def expand(raw_signs: list[int]) -> tuple[int, ...]:
        """Value channel gets the sign; observed-indicator and the four
        seasonality columns get 0 (see robust_channels layout)."""
        vector: list[int] = []
        for sign in raw_signs:
            vector.extend([int(sign), 0])
        vector.extend([0, 0, 0, 0])
        return tuple(vector)

    args.out_root.mkdir(parents=True, exist_ok=True)
    seeds = args.seeds or list(SEEDS)
    supports = args.support_basins or list(SUPPORT_BASINS)

    for n_support in supports:
        for seed in seeds:
            cell = args.out_root / f"support_{n_support}" / f"seed_{seed}"
            if (cell / "metrics.json").is_file():
                continue
            t0 = time.time()

            support_ids = screen.support_order(
                split["target_support_pool_basin_ids"], seed)[:n_support]
            query_ids = split["target_query_basin_ids"]
            target = target_all[target_all["gauge_id"].isin(
                [*support_ids, *query_ids])].reset_index(drop=True)
            support_mask = target["gauge_id"].isin(support_ids).to_numpy()
            query_mask = target["gauge_id"].isin(query_ids).to_numpy()
            source_fit = np.ones(len(source), dtype=bool)

            source_base, _ = screen.robust_channels(
                source, source_fit, base_features)
            target_base, _ = screen.robust_channels(
                target, support_mask, base_features)
            source_y = np.log1p(
                pd.to_numeric(source["discharge_mm_day"],
                              errors="coerce").to_numpy(np.float64))
            target_y = np.log1p(
                pd.to_numeric(target["discharge_mm_day"],
                              errors="coerce").to_numpy(np.float64))
            finite = np.isfinite(source_y)
            source_base, source_y = source_base[finite], source_y[finite]

            train_x = np.vstack([source_base, target_base[support_mask]])
            train_y = np.concatenate([source_y, target_y[support_mask]])
            weights = np.concatenate([
                np.ones(len(source_y)),
                np.full(int(support_mask.sum()), TARGET_WEIGHT)])
            query_x = target_base[query_mask]

            rng = derived_rng(f"camels_sign_v1|{n_support}|{seed}")
            signs_random_raw = [0] * len(base_features)
            for k in rng.choice(len(base_features), size=n_constrained,
                                replace=False):
                signs_random_raw[int(k)] = int(rng.choice([-1, 1]))
            arm_constraints = {
                "free": None,
                "sign_documented": expand(signs_doc_raw),
                "sign_flipped": expand([-s for s in signs_doc_raw]),
                "sign_random": expand(signs_random_raw),
            }

            cell_metrics: dict[str, dict] = {}
            for arm in ARMS:
                constraints = arm_constraints[arm]
                params = {} if constraints is None else {
                    "monotone_constraints": constraints}
                model = XGBRegressor(
                    objective="reg:squarederror", n_estimators=300,
                    max_depth=6, learning_rate=0.05, min_child_weight=5.0,
                    subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0,
                    random_state=seed, n_jobs=args.n_jobs,
                    tree_method="hist", **params)
                model.fit(train_x, train_y, sample_weight=weights)
                prediction = np.maximum(
                    np.expm1(model.predict(query_x).astype(np.float64)), 0.0)
                frame = target.loc[query_mask,
                                   ["gauge_id", "date", "discharge_mm_day"]].copy()
                cell_metrics[arm] = screen.metrics(frame, prediction)
                # Per-basin breakdown: the query basin is the independent
                # unit for the v2 addendum's clustering.
                per_basin: dict[str, dict[str, float]] = {}
                observed = frame["discharge_mm_day"].to_numpy(np.float64)
                for basin, positions in frame.groupby(
                        "gauge_id", sort=True).indices.items():
                    index = np.asarray(positions, dtype=np.int64)
                    y = observed[index]
                    yhat = prediction[index]
                    denominator = float(np.square(y - y.mean()).sum())
                    per_basin[str(basin)] = {
                        "log1p_rmse": float(np.sqrt(np.mean(np.square(
                            np.log1p(y) - np.log1p(yhat))))),
                        "nse": (1.0 - float(np.square(y - yhat).sum())
                                / denominator) if denominator > 0 else float("nan"),
                    }
                cell_metrics[arm]["per_basin"] = per_basin

            cell.mkdir(parents=True, exist_ok=True)
            (cell / "metrics.json").write_text(json.dumps({
                "task": "N1_camels_us2gb", "support_basins": n_support,
                "seed": seed,
                "n_constrained_features": n_constrained,
                "constrained_features": [f for f, s in zip(base_features,
                                                           signs_doc_raw) if s],
                "n_base_features": len(base_features),
                "n_source_rows": int(len(source_y)),
                "n_support_rows": int(support_mask.sum()),
                "n_query_rows": int(query_mask.sum()),
                "arms": cell_metrics,
                "wall_seconds": round(time.time() - t0, 1),
            }, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
            print(json.dumps({"support_basins": n_support, "seed": seed,
                              "wall_seconds": round(time.time() - t0, 1),
                              "done": True}), flush=True)

    print(json.dumps({"status": "complete"}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
