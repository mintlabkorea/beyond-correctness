#!/usr/bin/env python3
"""Synthetic construction tests for the MCR informativeness ladder."""

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
    runner = load(
        "mcr_info_ladder_runner_test",
        ROOT / "scripts/run_crta_v3_mcr_source_informativeness_ladder_v1.py",
    )
    # destination->source cycles: (0 1 2 3 4), (5 6 7), (8 9)
    full = np.asarray([1, 2, 3, 4, 0, 6, 7, 5, 9, 8], dtype=np.int64)
    cycles = runner.permutation_cycles(full)
    assert sorted(map(len, cycles)) == [2, 3, 5]
    order = np.asarray([0, 1, 2], dtype=np.int64)
    prior = set()
    for target in (2, 4, 6, 8, 10):
        partial = runner.partial_permutation(full, target, order)
        assert np.array_equal(np.sort(partial), np.arange(10))
        moved = set(np.flatnonzero(partial != np.arange(10)).tolist())
        assert abs(len(moved) - target) <= 1
        assert prior.issubset(moved)
        prior = moved
    assert np.array_equal(runner.partial_permutation(full, 10, order), full)

    summary = load(
        "mcr_info_ladder_summary_test",
        ROOT / "scripts/summarize_crta_v3_mcr_source_informativeness_ladder_v1.py",
    )
    assert summary.first_crossing([0.4, 0.2, -0.1, -0.2, -0.3]) == [0.25, 0.50]
    assert summary.first_crossing([0.4, 0.2, 0.1, 0.01, -0.3]) == [0.75, 1.0]
    assert summary.first_crossing([0.4, 0.2, 0.1, 0.01, 0.0]) is None
    print("MCR source-informativeness ladder synthetic invariants: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
