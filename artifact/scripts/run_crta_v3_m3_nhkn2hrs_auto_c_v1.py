#!/usr/bin/env python3
"""Launch the frozen M3 NHANES+KNHANES -> HRS Base/Auto-C matrix.

This file is intentionally a small, standard-library-only authorization gate.
It must validate the independently reviewed HRS provider response before it
imports the runtime module that can open participant-level parquet objects.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCOPE_ID = "crta_v3_m3_nhkn2hrs_auto_c_utility_v1"
AUTH_VALIDATOR = ROOT / "scripts" / "validate_hrs_ai_authorization.py"
EXPECTED_AUTH_VALIDATOR_SHA256 = (
    "d38d383a6ddf6a3e104db491a9e5cb0f04f74fa9594831c24a66742ecb754dee"
)
RUNTIME = ROOT / "scripts" / "crta_v3_m3_nhkn2hrs_runtime_v1.py"
DEFAULT_PLAN = (
    ROOT
    / "experiments/crta_v3_all_llm_all_task_utility_v1/execution_plan/"
    "M3_M6_PRIMARY_ELIGIBLE_BANK_STAGING_PLAN.json"
)
DEFAULT_AUDIT = (
    ROOT
    / "experiments/crta_v3_all_llm_all_task_utility_v1/audit/"
    "all_llm_future_task_banks_primary_v1/AUDIT.json"
)
DEFAULT_TASK_MANIFEST = (
    ROOT / "iclr_latex_v3/task_manifests/all_llm_all_task_utility_v1.json"
)
DEFAULT_ELIGIBILITY_OVERLAY = (
    ROOT / "iclr_latex_v3/task_manifests/M3_M6_PRIMARY_BANK_ELIGIBILITY_OVERLAY_V1.json"
)
DEFAULT_PAYLOAD = (
    ROOT
    / "iclr_latex_v3/method_contract/v1/payloads/"
    "medical_nhkn_hrs_registry_documents_v1/proposer_input.json"
)
DEFAULT_DSL = ROOT / "iclr_latex_v3/method_contract/v1/dsl/dsl_v1.json"
DEFAULT_RUNTIME_MAP = (
    ROOT
    / "iclr_latex_v3/method_contract/v1/compiler/"
    "runtime_schema_maps_m3_nhkn_hrs_v1.json"
)
DEFAULT_COMPILER = (
    ROOT / "iclr_latex_v3/method_contract/v1/compiler/compile_bank.py"
)
DEFAULT_OUT_ROOT = (
    Path(
        "data/private/crta_v3/"
        "m3_nhkn2hrs_auto_c_v1"
    )
)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


SOURCE_CAP_DEFAULT = 4_096


def _source_cap(value: str) -> "int | None":
    """Parse one ladder rung.  'uncapped' is the top rung and has no integer."""
    if value.strip().lower() == "uncapped":
        return None
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("source cap must be positive or 'uncapped'")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-cap",
        type=_source_cap,
        default=SOURCE_CAP_DEFAULT,
        help=(
            "Source-budget ladder rung: 4096, 16384, or 'uncapped'.  Each rung "
            "writes to its own private leaf; omitting this reproduces the "
            "executed L0 run."
        ),
    )
    parser.add_argument(
        "--leakage-block-policy",
        choices=("none", "compiler", "compiler_base"),
        default="none",
        help=(
            "Near-definitional proxy exclusion.  'none' reproduces the executed "
            "pre-fix configuration; 'compiler' blocks proxies in the compiler "
            "forbidden set only; 'compiler_base' also drops them from Base, "
            "which is the full M4/M5 criterion.  Every policy other than 'none' "
            "writes to its own private leaf."
        ),
    )
    parser.add_argument("--hrs-ai-authorization", type=Path, required=True)
    parser.add_argument("--source-parquet", type=Path, required=True)
    parser.add_argument("--hrs-snapshot", type=Path, required=True)
    parser.add_argument("--bank-plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--bank-audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--task-manifest", type=Path, default=DEFAULT_TASK_MANIFEST)
    parser.add_argument(
        "--eligibility-overlay", type=Path, default=DEFAULT_ELIGIBILITY_OVERLAY
    )
    parser.add_argument("--payload", type=Path, default=DEFAULT_PAYLOAD)
    parser.add_argument("--dsl", type=Path, default=DEFAULT_DSL)
    parser.add_argument("--runtime-map", type=Path, default=DEFAULT_RUNTIME_MAP)
    parser.add_argument("--compiler", type=Path, default=DEFAULT_COMPILER)
    parser.add_argument(
        "--out-root",
        type=Path,
        default=None,
        help="Defaults to the frozen leaf for the requested source-budget rung.",
    )
    parser.add_argument("--n-jobs", type=int, default=8)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument(
        "--skip-complete",
        action="store_true",
        help="Skip only hash-verified complete cells; any mismatch fails closed.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Any artifact created after authorization must default to owner-only
    # permissions.  The runtime also enforces this boundary independently.
    os.umask(0o077)

    # Do not inspect source/target paths, import pandas/pyarrow/xgboost, or
    # create output directories before this exact authorization call passes.
    if _sha256_file(AUTH_VALIDATOR) != EXPECTED_AUTH_VALIDATOR_SHA256:
        raise RuntimeError("pinned HRS authorization validator SHA-256 mismatch")
    validator = _load_module("crta_v3_m3_hrs_authorization", AUTH_VALIDATOR)
    authorization = validator.validate(
        args.hrs_ai_authorization,
        SCOPE_ID,
    )

    # The process is CPU-only.  Hiding all accelerators before importing
    # XGBoost is stronger than merely avoiding physical GPU 1 in a flag.
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["NVIDIA_VISIBLE_DEVICES"] = "none"
    os.environ["XGBOOST_USE_CUDA"] = "0"

    runtime = _load_module("crta_v3_m3_nhkn2hrs_runtime", RUNTIME)
    # Bind the forbidden-set policy first: it selects the private leaf suffix
    # that bind_source_cap then freezes.
    runtime.bind_leakage_block_policy(args.leakage_block_policy)
    # Bind the rung before the runtime validates any private path; its
    # path-security helpers close over the task root.
    root = runtime.bind_source_cap(args.source_cap)
    if getattr(args, "out_root", None) is None:
        args.out_root = root
    return int(runtime.run(args, authorization))


if __name__ == "__main__":
    raise SystemExit(main())
