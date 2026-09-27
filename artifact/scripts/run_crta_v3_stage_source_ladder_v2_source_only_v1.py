#!/usr/bin/env python3
"""Real-data source-informativeness ladder v2 — SOURCE-ONLY M axis.

Same corruption construction and namespaces as v1
(`run_crta_v3_stage_source_informativeness_ladder_v1.py`: the v1
derangement / cycle-order seeds are reused so cells are comparable), but
the engine is the source-only fork
(`run_crta_v3_m1m2_stage_factorial_source_only_v1.py`): support labels are
documented-mapped and target features harmonized in EVERY arm; the M axis
changes only the source side.  α=0 is refit under the new semantics.
Prereg: iclr_latex_v3/STAGE_SOURCE_LADDER_V2_SOURCE_ONLY_PREREGISTRATION_V1.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "scripts/run_crta_v3_stage_source_informativeness_ladder_v1.py"
ENGINE = ROOT / "scripts/run_crta_v3_m1m2_stage_factorial_source_only_v1.py"
FROZEN_ENGINE = ROOT / "scripts/run_crta_v3_m1m2_stage_factorial_v1.py"
REGISTRY = ROOT / "scripts/crta_v3_stage_endpoint_registry_v1.py"
PREREG = (ROOT /
          "iclr_latex_v3/STAGE_SOURCE_LADDER_V2_SOURCE_ONLY_PREREGISTRATION_V1.md")
DEFAULT_OUT = ROOT / "experiments/crta_v3_stage_source_ladder_v2_source_only_v1"
ALPHAS = (0.00, 0.25, 0.50, 0.75, 1.00)
TARGET_COHORT = {"nh2kn": "knhanes", "kn2nh": "nhanes"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    v1 = None
    import importlib.util
    spec = importlib.util.spec_from_file_location("stage_source_ladder_v1_for_v2", V1)
    v1 = importlib.util.module_from_spec(spec)
    sys.modules["stage_source_ladder_v1_for_v2"] = v1
    spec.loader.exec_module(v1)

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--direction", required=True, choices=sorted(TARGET_COHORT))
    parser.add_argument("--alphas", nargs="*", type=float, default=list(ALPHAS))
    parser.add_argument("--targets", nargs="*", default=None)
    parser.add_argument("--seeds", nargs="*", type=int, default=None)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--nhanes-parquet", type=Path, default=v1.DEFAULT_NHANES)
    parser.add_argument("--knhanes-parquet", type=Path, default=v1.DEFAULT_KNHANES)
    args = parser.parse_args()
    for alpha in args.alphas:
        if not any(abs(alpha - a) < 1e-9 for a in ALPHAS):
            raise SystemExit(f"alpha {alpha} not in the frozen v2 ladder")

    provenance = {
        "runner_sha256": sha256_file(Path(__file__)),
        "v1_runner_sha256": sha256_file(V1),
        "engine_fork_sha256": sha256_file(ENGINE),
        "frozen_engine_sha256": sha256_file(FROZEN_ENGINE),
        "registry_sha256": sha256_file(REGISTRY),
        "mcr_ladder_sha256": sha256_file(v1.MCR_LADDER),
        "prereg_sha256": sha256_file(PREREG),
        "nhanes_sha256": sha256_file(args.nhanes_parquet),
        "knhanes_sha256": sha256_file(args.knhanes_parquet),
        "derange_namespace": v1.DERANGE_NS,
        "cycle_namespace": v1.CYCLE_NS,
        "m_axis": "source_only",
    }
    ladder_mod = v1.load("mcr_source_ladder_frozen_v2", v1.MCR_LADDER)
    # point the v1 configure/wrap machinery at the fork
    v1.ENGINE = ENGINE

    for alpha in args.alphas:
        started = time.time()
        sf = v1.configure_engine(args.direction, alpha)
        sf.TARGET_COHORT = TARGET_COHORT[args.direction]
        targets = args.targets or list(sf.TARGETS)
        seeds = args.seeds or list(sf.SEEDS)
        provider = v1.PermProvider(ladder_mod, args.direction, alpha)
        original_load = sf._load

        def patched_load(name, path, _orig=original_load, _prov=provider):
            module = _orig(name, path)
            if name == "crta_bench_stage":
                module.build_single_target_table = v1.wrap_builder(
                    module.build_single_target_table, _prov)
            return module

        sf._load = patched_load
        out_dir = args.out_root / args.direction / f"alpha_{alpha:.2f}"
        sys.argv = ["stage_source_ladder_v2",
                    "--nhanes-parquet", str(args.nhanes_parquet),
                    "--knhanes-parquet", str(args.knhanes_parquet),
                    "--out-root", str(out_dir), "--support-rows", "256",
                    "--threads", str(args.threads),
                    "--targets", *targets, "--seeds", *[str(s) for s in seeds]]
        rc = sf.main()
        if rc not in (0, None):
            raise RuntimeError(f"engine failed for alpha={alpha}: rc={rc}")
        audit_path = out_dir / "PERMUTATION_AUDIT_V1.json"
        merged: dict = {"direction": args.direction, "alpha": alpha,
                        "arms": list(v1.LADDER_ARMS), **provenance, "cells": {}}
        if audit_path.is_file():
            existing = json.loads(audit_path.read_text())
            for key in ("runner_sha256", "engine_fork_sha256", "prereg_sha256"):
                if existing.get(key) != provenance[key]:
                    raise RuntimeError(f"{audit_path} provenance mismatch; archive it first")
            merged["cells"].update(existing.get("cells", {}))
        merged["cells"].update(provider.audit)
        merged["wall_seconds"] = round(time.time() - started, 1)
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text(json.dumps(merged, indent=1, sort_keys=True))
        print(json.dumps({"direction": args.direction, "alpha": alpha,
                          "new_cells": len(provider.audit),
                          "wall_seconds": merged["wall_seconds"]}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
