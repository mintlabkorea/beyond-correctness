#!/usr/bin/env python3
"""Run the frozen ten-endpoint HistGB conditional-C confirmation.

This wrapper configures the audited S5 HistGB implementation for one transfer
direction, reuses the exact endpoint-expansion derangements, and appends
provenance plus an exact lesion-identity check to every completed cell.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_RUNNER = ROOT / "scripts/run_crta_v3_binding_backbone_generality_v1.py"
REGISTRY = ROOT / "scripts/crta_v3_stage_endpoint_registry_v1.py"
PROTOCOL = ROOT / "iclr_latex_v3/CONDITIONAL_C_HISTGB_CONFIRMATION_FREEZE_V1.md"
DEFAULT_NHANES = Path(
    "data/nhanes_knhanes/datasets/nhanes/processed/L3/L3_1714_ge9.parquet"
)
DEFAULT_KNHANES = Path(
    "data/nhanes_knhanes/datasets/knhanes/processed/L3/"
    "L3_9815_pr90_with_mpls.parquet"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def configure(base: Any, registry: Any, direction: str) -> None:
    endpoints = dict(registry.ENDPOINTS)
    base.TARGETS = endpoints
    source_binary = {1: 1, 2: 0}
    target_binary = {1: 1, 0: 0}
    forward_maps = {
        target: {"source": dict(source_binary), "target": dict(target_binary)}
        for target in endpoints
    }
    forward_maps["current_smoking_status"] = {
        "source": {1: 1, 2: 1, 3: 0},
        "target": {1: 1, 2: 1, 3: 0, 4: 0},
    }
    forward_eval = {target: dict(target_binary) for target in endpoints}
    forward_eval["current_smoking_status"] = {1: 1, 2: 1, 3: 0, 4: 0}

    if direction == "nh2kn":
        base.BENCHMARK_ID = "std_cross_nh2kn_shared_anchorreset_fewshot_v1"
        base.PIPELINE_LABEL_MAPS = forward_maps
        base.EVAL_LABEL_MAPS = forward_eval
        namespace = "stage_endpoint_expansion_nh2kn_v1"
    else:
        base.BENCHMARK_ID = "std_cross_kn2nh_shared_anchorreset_fewshot_v1"
        base.PIPELINE_LABEL_MAPS = {
            target: {"source": maps["target"], "target": maps["source"]}
            for target, maps in forward_maps.items()
        }
        base.EVAL_LABEL_MAPS = {
            target: (
                {1: 1, 2: 1, 3: 0}
                if target == "current_smoking_status"
                else {1: 1, 2: 0}
            )
            for target in endpoints
        }
        namespace = "stage_endpoint_expansion_kn2nh_v1"

    original_rng = base.derived_rng
    base.derived_rng = lambda key: original_rng(
        key.replace("stage_factorial_v1", namespace)
    )
    base.SUPPORT_ROWS = (256,)
    base.PRIMARY_K = 256


def enrich_and_validate(
    out_root: Path, xgb_root: Path, direction: str, provenance: dict[str, Any]
) -> None:
    paths = sorted(out_root.glob("*/seed_*/metrics.json"))
    if len(paths) != 100:
        raise RuntimeError(f"expected 100 completed cells, found {len(paths)}")
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        xgb_path = xgb_root / path.parent.parent.name / path.parent.name / "metrics.json"
        xgb = json.loads(xgb_path.read_text(encoding="utf-8"))
        if payload["pl_columns_permutation"] != xgb["pl_columns_permutation"]:
            raise RuntimeError(f"derangement mismatch: {path}")
        if set(payload["auroc"]) != {"256"}:
            raise RuntimeError(f"unexpected support budgets: {path}")
        payload["confirmation_provenance"] = {
            **provenance,
            "direction": direction,
            "xgb_derangement_source": str(xgb_path),
            "xgb_derangement_exact_match": True,
        }
        path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n",
                        encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--direction", choices=("nh2kn", "kn2nh"), required=True)
    parser.add_argument("--nhanes-parquet", type=Path, default=DEFAULT_NHANES)
    parser.add_argument("--knhanes-parquet", type=Path, default=DEFAULT_KNHANES)
    parser.add_argument("--out-root", type=Path)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--targets", nargs="*")
    parser.add_argument("--seeds", nargs="*", type=int)
    args = parser.parse_args()

    out_root = args.out_root or (
        ROOT / f"experiments/crta_v3_conditional_c_histgb_{args.direction}_v1"
    )
    xgb_root = ROOT / f"experiments/crta_v3_stage_endpoint_expansion_{args.direction}_v1"
    base = load("conditional_c_histgb_base_v1", BASE_RUNNER)
    registry = load("conditional_c_histgb_registry_v1", REGISTRY)
    configure(base, registry, args.direction)

    provenance = {
        "analysis_status": "review_triggered_confirmation_frozen_after_exploratory_xgb",
        "protocol_sha256": sha256_file(PROTOCOL),
        "wrapper_sha256": sha256_file(Path(__file__)),
        "base_runner_sha256": sha256_file(BASE_RUNNER),
        "registry_sha256": sha256_file(REGISTRY),
    }

    forwarded = [
        str(BASE_RUNNER),
        "--nhanes-parquet", str(args.nhanes_parquet),
        "--knhanes-parquet", str(args.knhanes_parquet),
        "--out-root", str(out_root),
        "--support-rows", "256",
        "--threads", str(args.threads),
    ]
    if args.targets:
        forwarded.extend(["--targets", *args.targets])
    if args.seeds:
        forwarded.extend(["--seeds", *map(str, args.seeds)])
    original_argv = sys.argv
    try:
        sys.argv = forwarded
        status = int(base.main())
    finally:
        sys.argv = original_argv
    if status != 0:
        return status
    # Full-grid executions only.  Smokes are deliberately incomplete and are
    # validated by their finite output rather than enriched as evidence.
    if args.targets is None and args.seeds is None:
        enrich_and_validate(out_root, xgb_root, args.direction, provenance)
    print(json.dumps({"status": "complete", "direction": args.direction,
                      "out_root": str(out_root)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
