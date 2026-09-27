#!/usr/bin/env python3
"""Run the frozen four-arm TransTab identity-bridge decomposition."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_RUNNER = ROOT / "scripts/run_crta_v3_mcr_transtab_c_v1.py"
PROTOCOL = ROOT / "iclr_latex_v3/MCR_TRANSTAB_BRIDGE_DECOMPOSITION_FREEZE_V1.md"
DEFAULT_OUT = ROOT / "experiments/crta_v3_mcr_transtab_bridge_decomposition_v1"
ARMS = ("correct", "shared_anonymous", "distinct_anonymous", "c_wrong")


def load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def rename_frame(frame: Any, namespace: str) -> Any:
    result = frame.copy()
    result.columns = [f"{namespace}{index:04d}" for index in range(len(result.columns))]
    return result


def main() -> int:
    base = load("mcr_transtab_bridge_base_v1", BASE_RUNNER)
    original_semantic_loader = base.load_semantic_runner

    def semantic_loader():
        semantic = original_semantic_loader()
        original_arm_frames = semantic.arm_frames

        def arm_frames(parent, cell, family, realization, support_k, arm):
            if arm in ("correct", "c_wrong"):
                return original_arm_frames(
                    parent, cell, family, realization, support_k, arm
                )
            source, support, query = original_arm_frames(
                parent, cell, family, realization, support_k, "correct"
            )
            if arm == "shared_anonymous":
                return (
                    rename_frame(source, "x"),
                    rename_frame(support, "x"),
                    rename_frame(query, "x"),
                )
            if arm == "distinct_anonymous":
                return (
                    rename_frame(source, "a"),
                    rename_frame(support, "b"),
                    rename_frame(query, "b"),
                )
            raise ValueError(f"unknown arm: {arm}")

        semantic.arm_frames = arm_frames
        return semantic

    base.load_semantic_runner = semantic_loader
    base.PROTOCOL = PROTOCOL
    base.DEFAULT_OUT = DEFAULT_OUT
    base.ARMS = ARMS
    # The inherited main records the executing wrapper rather than the helper.
    base.__file__ = str(Path(__file__).resolve())
    return int(base.main())


if __name__ == "__main__":
    raise SystemExit(main())
