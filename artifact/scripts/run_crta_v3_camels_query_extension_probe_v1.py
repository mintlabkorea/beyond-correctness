#!/usr/bin/env python3
"""CAMELS query-basin extension probe: frozen v2 fits, extended query set.

Frozen design: `iclr_latex_v3/CAMELS_QUERY_EXTENSION_PREREGISTRATION_V1.md`.

Rebuilds the exact G-SIGN-CAMELS v2 cells — same source rows, support pool,
support draws, seeds, robust channels (calibrated on support rows only),
XGBoost configuration, and arms — and evaluates each fitted arm on the
frozen 12 query basins plus the hash-continuation extension basins.
Extension basins enter only as query rows, so every fit is byte-identical
to the frozen probe; a replication gate asserts the per-basin metrics on
the original 12 basins reproduce the frozen values within 1e-9.
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
PROBE_V2 = ROOT / "scripts/run_crta_v3_camels_sign_probe_v2.py"
PREREG = ROOT / "iclr_latex_v3/CAMELS_QUERY_EXTENSION_PREREGISTRATION_V1.md"
DATA = ROOT / "experiments/crta_v3_camels_native_screen_v1/data"
EXT_DATA = ROOT / "experiments/crta_v3_camels_query_extension_v1/data"
FROZEN_PROBE_ROOT = ROOT / "experiments/crta_v3_camels_sign_probe_v2"
DEFAULT_OUT = ROOT / "experiments/crta_v3_camels_query_extension_v1/probe"
ARMS = ("free", "sign_documented", "sign_flipped", "sign_random")
TARGET_WEIGHT = 10.0
SEEDS = tuple(range(20, 40))
SUPPORT_BASINS = (1, 3, 5)
REPLICATION_TOL = 1e-9


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def per_basin_metrics(frame: pd.DataFrame, prediction: np.ndarray
                      ) -> dict[str, dict[str, float]]:
    per_basin: dict[str, dict[str, float]] = {}
    observed = frame["discharge_mm_day"].to_numpy(np.float64)
    for basin, positions in frame.groupby("gauge_id", sort=True).indices.items():
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
    return per_basin


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--seeds", nargs="*", type=int, default=None)
    parser.add_argument("--support-basins", nargs="*", type=int, default=None)
    parser.add_argument("--n-jobs", type=int, default=2)
    args = parser.parse_args()

    screen = _load("camels_screen_for_ext", SCREEN)
    probe = _load("camels_probe_v2_for_ext", PROBE_V2)
    from xgboost import XGBRegressor

    source = pd.read_pickle(DATA / "source.pkl").reset_index(drop=True)
    target_frozen = pd.read_pickle(DATA / "target.pkl").reset_index(drop=True)
    target_ext = pd.read_pickle(EXT_DATA / "target.pkl").reset_index(drop=True)
    split = screen.load_json(DATA / "split_manifest.json")
    ext_manifest = screen.load_json(EXT_DATA / "split_manifest.json")
    payload = screen.load_json(screen.PAYLOAD_PATH)

    if list(target_frozen.columns) != list(target_ext.columns):
        raise RuntimeError("extension target columns differ from frozen target")
    frozen_ids = set(split["target_query_basin_ids"]) | set(
        split["target_support_pool_basin_ids"])
    ext_query_ids = sorted(ext_manifest["target_query_basin_ids"])
    if ext_manifest["target_support_pool_basin_ids"]:
        raise RuntimeError("extension must not carry a support pool")
    if frozen_ids & set(ext_query_ids):
        raise RuntimeError("extension basins overlap the frozen split")
    if ext_manifest["split_salt"] != split["split_salt"]:
        raise RuntimeError("extension used a different split salt")

    target_all = pd.concat([target_frozen, target_ext], ignore_index=True)

    provenance = {
        "runner_sha256": sha256_file(Path(__file__)),
        "screen_sha256": sha256_file(SCREEN),
        "probe_v2_sha256": sha256_file(PROBE_V2),
        "prereg_sha256": sha256_file(PREREG),
        "frozen_target_sha256": sha256_file(DATA / "target.pkl"),
        "ext_target_sha256": sha256_file(EXT_DATA / "target.pkl"),
        "n_extension_basins": len(ext_query_ids),
    }

    source_ids = screen.eligible_ids(payload, "source")
    target_ids = screen.eligible_ids(payload, "target")
    derived = sorted({
        column for frame in (source, target_frozen) for column in frame.columns
        if "__trailmean_" in column})
    base_features = sorted(set(source_ids) | set(target_ids) | set(derived))
    signs_doc_raw = [probe.documented_sign(f) for f in base_features]
    n_constrained = sum(1 for s in signs_doc_raw if s != 0)
    if n_constrained == 0:
        raise RuntimeError("no documented feature present in the CAMELS Base")

    def expand(raw_signs: list[int]) -> tuple[int, ...]:
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
            frozen_cell_path = (FROZEN_PROBE_ROOT / f"support_{n_support}"
                                / f"seed_{seed}" / "metrics.json")
            frozen_cell = json.loads(frozen_cell_path.read_text())
            t0 = time.time()

            support_ids = screen.support_order(
                split["target_support_pool_basin_ids"], seed)[:n_support]
            query_ids = [*split["target_query_basin_ids"], *ext_query_ids]
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

            rng = probe.derived_rng(f"camels_sign_v1|{n_support}|{seed}")
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
            max_replication_error = 0.0
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
                per_basin = per_basin_metrics(frame, prediction)
                frozen_pb = frozen_cell["arms"][arm]["per_basin"]
                for basin, frozen_values in frozen_pb.items():
                    for metric, frozen_value in frozen_values.items():
                        error = abs(per_basin[basin][metric]
                                    - float(frozen_value))
                        max_replication_error = max(max_replication_error,
                                                    error)
                        if error > REPLICATION_TOL:
                            raise RuntimeError(
                                f"replication gate failed: arm {arm} basin "
                                f"{basin} {metric} differs by {error}")
                cell_metrics[arm] = {"per_basin": per_basin}

            cell.mkdir(parents=True, exist_ok=True)
            (cell / "metrics.json").write_text(json.dumps({
                "task": "camels_query_extension_v1",
                "support_basins": n_support,
                "seed": seed,
                "n_constrained_features": n_constrained,
                "n_base_features": len(base_features),
                "n_query_basins": len(query_ids),
                "n_extension_basins": len(ext_query_ids),
                "replication_gate": {
                    "tolerance": REPLICATION_TOL,
                    "max_abs_error": max_replication_error,
                    "passed": True,
                },
                "frozen_cell_sha256": sha256_file(frozen_cell_path),
                "arms": cell_metrics,
                "wall_seconds": round(time.time() - t0, 1),
                **provenance,
            }, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
            print(json.dumps({"support_basins": n_support, "seed": seed,
                              "wall_seconds": round(time.time() - t0, 1),
                              "done": True}), flush=True)

    print(json.dumps({"status": "complete"}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
