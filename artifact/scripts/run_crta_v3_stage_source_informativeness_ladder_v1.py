#!/usr/bin/env python3
"""Real-data M×C source-informativeness ladder over the frozen ten-endpoint
stage factorial.

Per (direction, endpoint, seed) a no-fixed-point derangement of the source
block's raw training labels is nested-dosed at α ∈ {.25,.50,.75,1.00} via
the frozen MCR ladder's cycle-prefix construction, injected before label
mapping so every arm inherits the same corrupted pairing.  Arms restricted
to the four interaction cells.  α=0 is read from the frozen expansion
trees and never refit.
Prereg: iclr_latex_v3/STAGE_SOURCE_INFORMATIVENESS_LADDER_PREREGISTRATION_V1.md.
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
ENGINE = ROOT / "scripts/run_crta_v3_m1m2_stage_factorial_v1.py"
REGISTRY = ROOT / "scripts/crta_v3_stage_endpoint_registry_v1.py"
MCR_LADDER = ROOT / "scripts/run_crta_v3_mcr_source_informativeness_ladder_v1.py"
PREREG = (ROOT /
          "iclr_latex_v3/STAGE_SOURCE_INFORMATIVENESS_LADDER_PREREGISTRATION_V1.md")
DEFAULT_OUT = ROOT / "experiments/crta_v3_stage_source_informativeness_ladder_v1"
DEFAULT_NHANES = Path(
    "data/external1/medical_fm/datasets/NHANES_levels/L3_1714_ge9.parquet")
DEFAULT_KNHANES = Path(
    "data/nhanes_knhanes/datasets/knhanes/processed/L3/"
    "L3_9815_pr90_with_mpls.parquet")

DERANGE_NS = "stage_source_ladder_v1"
CYCLE_NS = "stage_source_ladder_cycle_order_v1"
ALPHAS = (0.25, 0.50, 0.75, 1.00)
LADDER_ARMS = ("a00_base", "a01_columns", "a10_stage", "a11_stage_columns")
DIRECTION_NS = {"nh2kn": "stage_endpoint_expansion_nh2kn_v1",
                "kn2nh": "stage_endpoint_expansion_kn2nh_v1"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def stable_seed(*parts) -> int:
    """The MCR runner's seed convention, byte-identical."""
    payload = "|".join(str(part) for part in parts).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8],
                          "little") % (2 ** 32 - 1)


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def full_derangement(direction: str, target: str, seed: int,
                     n: int) -> np.ndarray:
    rng = np.random.default_rng(
        stable_seed(DERANGE_NS, direction, target, seed))
    identity = np.arange(n)
    for _ in range(1000):
        perm = rng.permutation(n)
        if np.all(perm != identity):
            return perm
    raise RuntimeError("could not draw a source-label derangement")


class PermProvider:
    """Deterministic per-(endpoint, seed) partial permutation at one α."""

    def __init__(self, ladder_mod, direction: str, alpha: float):
        self.ladder = ladder_mod
        self.direction = direction
        self.alpha = float(alpha)
        self.cache: dict[tuple[str, int], tuple[np.ndarray, int]] = {}
        self.audit: dict[str, dict] = {}

    def get(self, target: str, seed: int, n: int) -> np.ndarray:
        key = (target, seed)
        if key in self.cache:
            perm, n_cached = self.cache[key]
            if n_cached != n:
                raise AssertionError(
                    f"n_source changed across builds for {key}")
            return perm
        full = full_derangement(self.direction, target, seed, n)
        cycles = self.ladder.permutation_cycles(full)
        order = np.random.default_rng(
            stable_seed(CYCLE_NS, self.direction, target, seed)
        ).permutation(len(cycles))
        target_moved = int(round(self.alpha * n))
        perm = self.ladder.partial_permutation(full, target_moved, order)
        if self.alpha >= 1.0 and not np.array_equal(perm, full):
            raise AssertionError("alpha=1 must reproduce the derangement")
        moved = int(np.sum(perm != np.arange(n)))
        self.audit[f"{target}|seed_{seed}"] = {
            "alpha": self.alpha,
            "n_source": n,
            "target_moved": target_moved,
            "moved": moved,
            "permutation_sha256": hashlib.sha256(
                perm.astype("<i8").tobytes()).hexdigest(),
            "full_derangement_sha256": hashlib.sha256(
                full.astype("<i8").tobytes()).hexdigest(),
        }
        self.cache[key] = (perm, n)
        return perm


def wrap_builder(orig, provider: PermProvider):
    def wrapped(**kwargs):
        bundle = orig(**kwargs)
        target = kwargs["target_name"]
        seed = int(kwargs["seed"])
        origin = np.asarray(bundle["train_origin"], dtype=object)
        n_source = int(np.sum(origin == "source"))
        if n_source <= 0 or not bool(np.all(origin[:n_source] == "source")):
            raise AssertionError("source rows must be a prefix of train")
        y = bundle["y_train"]
        is_series = hasattr(y, "iloc")
        if "__ladder_pristine_y" in bundle:
            pristine = bundle["__ladder_pristine_y"]
        else:
            pristine = y.copy() if is_series else np.asarray(y).copy()
            bundle["__ladder_pristine_y"] = pristine
        vals = (pristine.to_numpy(copy=True) if is_series
                else np.asarray(pristine).copy())
        perm = provider.get(target, seed, n_source)
        source_block = vals[:n_source].copy()
        vals[:n_source] = source_block[perm]
        if is_series:
            bundle["y_train"] = pd.Series(vals, index=y.index)
        else:
            bundle["y_train"] = vals
        return bundle
    return wrapped


def configure_engine(direction: str, alpha: float):
    tag = f"{direction}_{alpha:.2f}".replace(".", "p")
    sf = load(f"stage_ladder_base_{tag}", ENGINE)
    registry = load(f"stage_ladder_registry_{tag}", REGISTRY)
    registry.configure(sf)
    if direction == "kn2nh":
        sf.BENCHMARK_ID = "std_cross_kn2nh_shared_anchorreset_fewshot_v1"
        sf.PIPELINE_LABEL_MAPS = {
            target: {"source": maps["target"], "target": maps["source"]}
            for target, maps in sf.PIPELINE_LABEL_MAPS.items()
        }
        sf.EVAL_LABEL_MAPS = {
            target: ({1: 1, 2: 1, 3: 0}
                     if target == "current_smoking_status" else {1: 1, 2: 0})
            for target in sf.TARGETS
        }
        sf.LABEL_ITEMS = {
            target: {"source": sides["target"], "target": sides["source"]}
            for target, sides in sf.LABEL_ITEMS.items()
        }
    original_rng = sf.derived_rng
    namespace = DIRECTION_NS[direction]
    sf.derived_rng = lambda key: original_rng(
        key.replace("stage_factorial_v1", namespace))
    sf.ARMS = LADDER_ARMS
    return sf


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--direction", required=True,
                        choices=sorted(DIRECTION_NS))
    parser.add_argument("--alphas", nargs="*", type=float,
                        default=list(ALPHAS))
    parser.add_argument("--targets", nargs="*", default=None)
    parser.add_argument("--seeds", nargs="*", type=int, default=None)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--nhanes-parquet", type=Path,
                        default=DEFAULT_NHANES)
    parser.add_argument("--knhanes-parquet", type=Path,
                        default=DEFAULT_KNHANES)
    args = parser.parse_args()

    for alpha in args.alphas:
        if not any(abs(alpha - a) < 1e-9 for a in ALPHAS):
            raise SystemExit(f"alpha {alpha} not in the frozen ladder")

    provenance = {
        "runner_sha256": sha256_file(Path(__file__)),
        "engine_sha256": sha256_file(ENGINE),
        "registry_sha256": sha256_file(REGISTRY),
        "mcr_ladder_sha256": sha256_file(MCR_LADDER),
        "prereg_sha256": sha256_file(PREREG),
        "nhanes_sha256": sha256_file(args.nhanes_parquet),
        "knhanes_sha256": sha256_file(args.knhanes_parquet),
        "derange_namespace": DERANGE_NS,
        "cycle_namespace": CYCLE_NS,
    }
    ladder_mod = load("mcr_source_ladder_frozen", MCR_LADDER)

    for alpha in args.alphas:
        started = time.time()
        sf = configure_engine(args.direction, alpha)
        targets = args.targets or list(sf.TARGETS)
        seeds = args.seeds or list(sf.SEEDS)
        provider = PermProvider(ladder_mod, args.direction, alpha)
        original_load = sf._load

        def patched_load(name, path, _orig=original_load, _prov=provider):
            module = _orig(name, path)
            if name == "crta_bench_stage":
                module.build_single_target_table = wrap_builder(
                    module.build_single_target_table, _prov)
            return module

        sf._load = patched_load
        out_dir = args.out_root / args.direction / f"alpha_{alpha:.2f}"
        sys.argv = [
            "stage_source_ladder",
            "--nhanes-parquet", str(args.nhanes_parquet),
            "--knhanes-parquet", str(args.knhanes_parquet),
            "--out-root", str(out_dir),
            "--support-rows", "256",
            "--threads", str(args.threads),
            "--targets", *targets,
            "--seeds", *[str(s) for s in seeds],
        ]
        rc = sf.main()
        if rc not in (0, None):
            raise RuntimeError(f"engine failed for alpha={alpha}: rc={rc}")

        audit_path = out_dir / "PERMUTATION_AUDIT_V1.json"
        merged: dict = {"direction": args.direction, "alpha": alpha,
                        "arms": list(LADDER_ARMS), **provenance,
                        "cells": {}}
        if audit_path.is_file():
            existing = json.loads(audit_path.read_text())
            for key in ("runner_sha256", "engine_sha256", "prereg_sha256"):
                if existing.get(key) != provenance[key]:
                    raise RuntimeError(
                        f"{audit_path} provenance mismatch; archive it first")
            merged["cells"].update(existing.get("cells", {}))
        merged["cells"].update(provider.audit)
        merged["wall_seconds"] = round(time.time() - started, 1)
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text(json.dumps(merged, indent=1, sort_keys=True))
        print(json.dumps({"direction": args.direction, "alpha": alpha,
                          "new_cells": len(provider.audit),
                          "wall_seconds": merged["wall_seconds"]}),
              flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
