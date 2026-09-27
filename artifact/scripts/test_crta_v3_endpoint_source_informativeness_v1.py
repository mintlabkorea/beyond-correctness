#!/usr/bin/env python3
"""Synthetic invariants for endpoint source-informativeness extension."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    summary = load(
        "endpoint_info_summary_test",
        ROOT / "scripts/summarize_crta_v3_endpoint_source_informativeness_v1.py",
    )
    positive = summary.exact_one_sided_spearman(
        np.arange(5.0), np.arange(5.0), chunk=17)
    assert abs(positive["rho"] - 1.0) < 1e-12
    assert positive["extreme_permutations"] == 1
    assert positive["total_permutations"] == 120
    negative = summary.exact_one_sided_spearman(
        np.arange(5.0), np.arange(4.0, -1.0, -1.0), chunk=19)
    assert abs(negative["rho"] + 1.0) < 1e-12
    assert negative["extreme_permutations"] == 120

    arms = {
        "a11_stage_columns": 0.80,
        "a10_stage": 0.70,
        "a01_columns": 0.60,
        "a00_base": 0.55,
    }
    assert abs(summary.interaction(arms, fold=False) - 0.05) < 1e-12
    assert abs(summary.interaction(arms, fold=True) - 0.05) < 1e-12

    runner = load(
        "endpoint_info_runner_test",
        ROOT / "scripts/run_crta_v3_endpoint_source_informativeness_v1.py",
    )
    forward = runner.configure("nh2kn")
    reverse = runner.configure("kn2nh")
    assert len(forward.TARGETS) == 10 == len(reverse.TARGETS)
    assert forward.PIPELINE_LABEL_MAPS["diabetes_history"]["source"] == {1: 1, 2: 0}
    assert reverse.PIPELINE_LABEL_MAPS["diabetes_history"]["source"] == {1: 1, 0: 0}
    assert reverse.EVAL_LABEL_MAPS["diabetes_history"] == {1: 1, 2: 0}
    print("endpoint source-informativeness synthetic invariants: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
