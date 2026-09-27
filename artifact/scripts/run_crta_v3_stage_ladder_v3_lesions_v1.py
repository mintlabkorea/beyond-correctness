#!/usr/bin/env python3
"""Real-data M×C ladders v3: source-feature rendering corruption (A2),
source-feature column-wise permutation (A1), support-label corruption (B),
on the source-only M-axis engine fork.  Dose 0 is the v2 α=0 tree.
Prereg: iclr_latex_v3/STAGE_LADDER_V3_LESIONS_PREREGISTRATION_V1.md.
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
V1 = ROOT / "scripts/run_crta_v3_stage_source_informativeness_ladder_v1.py"
V2 = ROOT / "scripts/run_crta_v3_stage_source_ladder_v2_source_only_v1.py"
ENGINE = ROOT / "scripts/run_crta_v3_m1m2_stage_factorial_source_only_v1.py"
PREREG = ROOT / "iclr_latex_v3/STAGE_LADDER_V3_LESIONS_PREREGISTRATION_V1.md"
DEFAULT_OUT = ROOT / "experiments/crta_v3_stage_ladder_v3_lesions_v1"
DOSES = (0.25, 0.50, 0.75, 1.00)
LESIONS = ("source_feature_render", "source_feature_colperm", "support_label")
SURVEY_SLOTS = ("sex", "education_level", "diabetes_history",
                "hypertension_history", "current_smoking_status")
NS = {"source_feature_render": ("stage_ladder_v3_render_order", "stage_ladder_v3_render_params"),
      "source_feature_colperm": ("stage_ladder_v3_colperm", "stage_ladder_v3_colperm_cycle_order"),
      "support_label": ("stage_ladder_v3_support", "stage_ladder_v3_support_cycle_order")}


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha_arr(a: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def nested_perm(ladder, stable_seed, derange_key: tuple, order_key: tuple,
                n: int, dose: float) -> np.ndarray:
    rng = np.random.default_rng(stable_seed(*derange_key))
    identity = np.arange(n)
    full = None
    for _ in range(1000):
        cand = rng.permutation(n)
        if np.all(cand != identity):
            full = cand
            break
    if full is None:
        raise RuntimeError("no derangement found")
    cycles = ladder.permutation_cycles(full)
    order = np.random.default_rng(stable_seed(*order_key)).permutation(len(cycles))
    target = int(round(dose * n))
    perm = ladder.partial_permutation(full, target, order)
    if dose >= 1.0 and not np.array_equal(perm, full):
        raise AssertionError("dose 1 must reproduce the derangement")
    return perm


class LesionProvider:
    def __init__(self, ladder, stable_seed, lesion: str, direction: str, dose: float):
        self.ladder, self.ss, self.lesion, self.direction, self.dose = ladder, stable_seed, lesion, direction, float(dose)
        self.audit: dict[str, dict] = {}

    # --- A1
    def colperms(self, target: str, seed: int, columns: list[str], n: int) -> dict[str, np.ndarray]:
        ns, ns_order = NS["source_feature_colperm"]
        out = {}
        for col in columns:
            out[col] = nested_perm(self.ladder, self.ss, (ns, self.direction, target, seed, col),
                                   (ns_order, self.direction, target, seed, col), n, self.dose)
        return out

    # --- A2
    def render_plan(self, target: str, seed: int, slots: list[str]) -> tuple[list[str], dict[str, dict]]:
        ns_order, ns_params = NS["source_feature_render"]
        order_rng = np.random.default_rng(self.ss(ns_order, self.direction, target, seed))
        order = [slots[i] for i in order_rng.permutation(len(slots))]
        k = int(np.ceil(self.dose * len(slots)))
        params = {}
        for slot in order[:k]:
            rng = np.random.default_rng(self.ss(ns_params, self.direction, target, seed, slot))
            if slot in SURVEY_SLOTS:
                params[slot] = {"kind": "code_permutation", "perm_seed": int(rng.integers(0, 2**31 - 1))}
            else:
                params[slot] = {"kind": "affine",
                                "scale": float(np.exp(rng.uniform(np.log(0.25), np.log(4.0)))),
                                "offset_sd": float(rng.uniform(-2.0, 2.0))}
        return order, params

    # --- B
    def pool_perm(self, target: str, seed: int, n_pool: int) -> np.ndarray:
        ns, ns_order = NS["support_label"]
        return nested_perm(self.ladder, self.ss, (ns, self.direction, target, seed),
                           (ns_order, self.direction, target, seed), n_pool, self.dose)


def apply_code_permutation(values: np.ndarray, perm_seed: int) -> np.ndarray:
    observed = np.unique(values[np.isfinite(values)])
    if len(observed) < 2:
        return values
    rng = np.random.default_rng(perm_seed)
    for _ in range(1000):
        p = rng.permutation(len(observed))
        if not np.array_equal(p, np.arange(len(observed))):
            break
    mapping = {float(observed[i]): float(observed[p[i]]) for i in range(len(observed))}
    out = values.copy()
    finite = np.isfinite(values)
    out[finite] = np.vectorize(lambda v: mapping[float(v)])(values[finite])
    return out


def wrap_builder(orig, provider: LesionProvider):
    def wrapped(**kwargs):
        bundle = orig(**kwargs)
        target, seed = kwargs["target_name"], int(kwargs["seed"])
        origin = np.asarray(bundle["train_origin"], dtype=object)
        n_source = int(np.sum(origin == "source"))
        n_train = len(origin)
        if n_source <= 0 or not bool(np.all(origin[:n_source] == "source")):
            raise AssertionError("source rows must be a prefix of train")
        key = f"{target}|seed_{seed}"
        if "__v3_pristine" not in bundle:
            bundle["__v3_pristine"] = {"X_train": bundle["X_train"].copy(), "y_train": bundle["y_train"].copy()}
        X = bundle["__v3_pristine"]["X_train"].copy()
        y = bundle["__v3_pristine"]["y_train"].copy()
        feature_cols = [c for c in X.columns if str(c).startswith("slot__")]
        entry: dict = {"dose": provider.dose, "n_source": n_source, "n_pool": n_train - n_source,
                       "lesion": provider.lesion}
        if provider.lesion == "source_feature_colperm":
            perms = provider.colperms(target, seed, feature_cols, n_source)
            entry["column_perm_sha256"] = {}
            for col, perm in perms.items():
                vals = X[col].to_numpy(copy=True)
                vals[:n_source] = vals[:n_source][perm]
                X[col] = vals
                entry["column_perm_sha256"][col] = sha_arr(perm.astype("<i8"))
                entry["moved"] = int(np.sum(perm != np.arange(n_source)))
        elif provider.lesion == "source_feature_render":
            slots = [c.split("slot__", 1)[1] for c in feature_cols]
            order, params = provider.render_plan(target, seed, slots)
            entry["slot_order"] = order
            entry["params"] = params
            for slot, p in params.items():
                col = f"slot__{slot}"
                vals = pd.to_numeric(X[col], errors="coerce").to_numpy(dtype=np.float64, copy=True)
                src = vals[:n_source]
                if p["kind"] == "affine":
                    m, sd = float(np.nanmean(src)), float(np.nanstd(src))
                    if not np.isfinite(sd) or sd == 0:
                        sd = 1.0
                    src_new = m + p["scale"] * (src - m) + p["offset_sd"] * sd
                else:
                    src_new = apply_code_permutation(src, p["perm_seed"])
                vals[:n_source] = src_new
                X[col] = vals
        elif provider.lesion == "support_label":
            n_pool = n_train - n_source
            perm = provider.pool_perm(target, seed, n_pool)
            yv = y.to_numpy(copy=True) if hasattr(y, "to_numpy") else np.asarray(y).copy()
            pool = yv[n_source:].copy()
            yv[n_source:] = pool[perm]
            y = pd.Series(yv, index=y.index) if hasattr(y, "index") else yv
            entry["pool_perm_sha256"] = sha_arr(perm.astype("<i8"))
            entry["moved"] = int(np.sum(perm != np.arange(n_pool)))
        else:
            raise ValueError(provider.lesion)
        bundle["X_train"] = X
        bundle["y_train"] = y
        provider.audit[key] = entry
        return bundle
    return wrapped


def main() -> int:
    v1 = _load("stage_ladder_v1_for_v3", V1)
    v2 = _load("stage_ladder_v2_for_v3", V2)
    ladder = v1.load("mcr_source_ladder_frozen_v3", v1.MCR_LADDER)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lesion", required=True, choices=LESIONS)
    parser.add_argument("--direction", required=True, choices=sorted(v2.TARGET_COHORT))
    parser.add_argument("--doses", nargs="*", type=float, default=list(DOSES))
    parser.add_argument("--targets", nargs="*", default=None)
    parser.add_argument("--seeds", nargs="*", type=int, default=None)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--nhanes-parquet", type=Path, default=v1.DEFAULT_NHANES)
    parser.add_argument("--knhanes-parquet", type=Path, default=v1.DEFAULT_KNHANES)
    args = parser.parse_args()
    for d in args.doses:
        if not any(abs(d - x) < 1e-9 for x in DOSES):
            raise SystemExit(f"dose {d} not frozen")
    provenance = {"runner_sha256": v1.sha256_file(Path(__file__)),
                  "engine_fork_sha256": v1.sha256_file(ENGINE),
                  "v1_runner_sha256": v1.sha256_file(V1), "v2_runner_sha256": v1.sha256_file(V2),
                  "mcr_ladder_sha256": v1.sha256_file(v1.MCR_LADDER),
                  "prereg_sha256": v1.sha256_file(PREREG),
                  "nhanes_sha256": v1.sha256_file(args.nhanes_parquet),
                  "knhanes_sha256": v1.sha256_file(args.knhanes_parquet),
                  "lesion": args.lesion, "m_axis": "source_only"}
    v1.ENGINE = ENGINE
    for dose in args.doses:
        started = time.time()
        sf = v1.configure_engine(args.direction, dose)
        sf.TARGET_COHORT = v2.TARGET_COHORT[args.direction]
        targets = args.targets or list(sf.TARGETS)
        seeds = args.seeds or list(sf.SEEDS)
        provider = LesionProvider(ladder, v1.stable_seed, args.lesion, args.direction, dose)
        original_load = sf._load

        def patched_load(name, path, _orig=original_load, _prov=provider):
            module = _orig(name, path)
            if name == "crta_bench_stage":
                module.build_single_target_table = wrap_builder(module.build_single_target_table, _prov)
            return module

        sf._load = patched_load
        out_dir = args.out_root / args.lesion / args.direction / f"dose_{dose:.2f}"
        sys.argv = ["stage_ladder_v3", "--nhanes-parquet", str(args.nhanes_parquet),
                    "--knhanes-parquet", str(args.knhanes_parquet), "--out-root", str(out_dir),
                    "--support-rows", "256", "--threads", str(args.threads),
                    "--targets", *targets, "--seeds", *[str(s) for s in seeds]]
        rc = sf.main()
        if rc not in (0, None):
            raise RuntimeError(f"engine failed: {rc}")
        audit_path = out_dir / "LESION_AUDIT_V1.json"
        merged = {"direction": args.direction, "dose": dose, **provenance, "cells": {}}
        if audit_path.is_file():
            existing = json.loads(audit_path.read_text())
            if existing.get("runner_sha256") != provenance["runner_sha256"]:
                raise RuntimeError(f"{audit_path} provenance mismatch; archive it first")
            merged["cells"].update(existing.get("cells", {}))
        merged["cells"].update(provider.audit)
        merged["wall_seconds"] = round(time.time() - started, 1)
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text(json.dumps(merged, indent=1, sort_keys=True))
        print(json.dumps({"lesion": args.lesion, "direction": args.direction, "dose": dose,
                          "new_cells": len(provider.audit), "wall_seconds": merged["wall_seconds"]}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
