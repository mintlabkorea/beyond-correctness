#!/usr/bin/env python3
"""Compiler-specificity stage B: downstream damage of forced false
bindings in the frozen NHANES->KNHANES stage factorial.

For dose k in {1,3,5,9}, the first k member slots of a frozen
outcome-blind order have their KNHANES raw column replaced (in the
benchmark manifest, at load time) by the stage-A forced false binding.
Only the `a11_stage_columns` arm is fit; the correct arm is read from
the frozen expansion tree.
Prereg: iclr_latex_v3/DECOY_COMPILER_SPECIFICITY_PREREGISTRATION_V1.md.
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

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "scripts/run_crta_v3_m1m2_stage_factorial_v1.py"
REGISTRY = ROOT / "scripts/crta_v3_stage_endpoint_registry_v1.py"
PREREG = ROOT / "iclr_latex_v3/DECOY_COMPILER_SPECIFICITY_PREREGISTRATION_V1.md"
STAGE_A = ROOT / "experiments/crta_v3_decoy_compiler_specificity_v1/STAGE_A_MATCHER_V1.json"
DEFAULT_OUT = ROOT / "experiments/crta_v3_decoy_compiler_specificity_v1/stage_b"
DEFAULT_NHANES = Path(
    "data/external1/medical_fm/datasets/NHANES_levels/L3_1714_ge9.parquet")
DEFAULT_KNHANES = Path(
    "data/nhanes_knhanes/datasets/knhanes/processed/L3/"
    "L3_9815_pr90_with_mpls.parquet")
ORDER_NS = "decoy_stage_b_order_v1"
DOSES = (1, 3, 5, 9)
REGIME = "name_unit_codebook"
ARM = "a11_stage_columns"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def stable_seed(*parts) -> int:
    payload = "|".join(str(p) for p in parts).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "little") % (2 ** 32 - 1)


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def member_order(members: tuple[str, ...]) -> list[str]:
    rng = np.random.default_rng(stable_seed(ORDER_NS))
    return [members[i] for i in rng.permutation(len(members))]


def configure_engine(dose: int, bindings: dict[str, str]):
    tag = f"k{dose}"
    sf = load(f"decoy_stage_b_engine_{tag}", ENGINE)
    registry = load(f"decoy_stage_b_registry_{tag}", REGISTRY)
    registry.configure(sf)
    original_rng = sf.derived_rng
    sf.derived_rng = lambda key: original_rng(
        key.replace("stage_factorial_v1", "stage_endpoint_expansion_nh2kn_v1"))
    sf.ARMS = (ARM,)
    original_load = sf._load

    def patched_load(name, path, _orig=original_load):
        module = _orig(name, path)
        if name == "crta_bench_stage":
            true_load_yaml = module.load_yaml
            manifest_path = Path(module.DEFAULT_DATASET_MANIFEST).resolve()

            def load_yaml_decoy(p):
                value = true_load_yaml(p)
                if Path(p).resolve() == manifest_path:
                    for member, decoy in bindings.items():
                        slot = value["slots"][member]
                        if slot.get("harmonization") or slot.get("aggregation"):
                            raise AssertionError(f"{member} carries inline rules")
                        slot["knhanes"] = decoy
                return value
            module.load_yaml = load_yaml_decoy
        return module

    sf._load = patched_load
    return sf


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doses", nargs="*", type=int, default=list(DOSES))
    parser.add_argument("--targets", nargs="*", default=None)
    parser.add_argument("--seeds", nargs="*", type=int, default=None)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--stage-a", type=Path, default=STAGE_A)
    parser.add_argument("--nhanes-parquet", type=Path, default=DEFAULT_NHANES)
    parser.add_argument("--knhanes-parquet", type=Path, default=DEFAULT_KNHANES)
    args = parser.parse_args()

    stage_a = json.loads(args.stage_a.read_text())
    forced = stage_a["sweeps"][REGIME]["forced_false_bindings"]
    provenance = {
        "runner_sha256": sha256_file(Path(__file__)),
        "engine_sha256": sha256_file(ENGINE),
        "registry_sha256": sha256_file(REGISTRY),
        "prereg_sha256": sha256_file(PREREG),
        "stage_a_sha256": sha256_file(args.stage_a),
        "nhanes_sha256": sha256_file(args.nhanes_parquet),
        "knhanes_sha256": sha256_file(args.knhanes_parquet),
    }
    probe = load("decoy_stage_b_probe", ENGINE)
    order = member_order(tuple(probe.MEMBER_SLOTS))
    if sorted(order) != sorted(forced):
        raise RuntimeError("stage-A bindings do not cover the member slots")

    for dose in args.doses:
        if dose not in DOSES:
            raise SystemExit(f"dose {dose} not frozen")
        bindings = {m: forced[m] for m in order[:dose]}
        started = time.time()
        sf = configure_engine(dose, bindings)
        targets = args.targets or list(sf.TARGETS)
        seeds = args.seeds or list(sf.SEEDS)
        out_dir = args.out_root / f"k{dose}"
        sys.argv = ["decoy_stage_b",
                    "--nhanes-parquet", str(args.nhanes_parquet),
                    "--knhanes-parquet", str(args.knhanes_parquet),
                    "--out-root", str(out_dir),
                    "--support-rows", "256", "--threads", str(args.threads),
                    "--targets", *targets, "--seeds", *[str(s) for s in seeds]]
        rc = sf.main()
        if rc not in (0, None):
            raise RuntimeError(f"engine failed at dose {dose}: rc={rc}")
        audit = {"dose": dose, "member_order": order, "bindings": bindings,
                 "regime": REGIME, "arm": ARM, **provenance,
                 "wall_seconds": round(time.time() - started, 1)}
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "BINDING_AUDIT_V1.json").write_text(
            json.dumps(audit, indent=1, sort_keys=True))
        print(json.dumps({"dose": dose, "bindings": bindings,
                          "wall_seconds": audit["wall_seconds"]}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
