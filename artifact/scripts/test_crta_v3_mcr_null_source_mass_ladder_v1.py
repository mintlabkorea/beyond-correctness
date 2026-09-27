#!/usr/bin/env python3
"""Synthetic invariants for the triggered null-source mass ladder."""

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


class FakeBase:
    @staticmethod
    def stable_seed(*parts):
        return 314159


def main() -> int:
    runner = load(
        "mcr_null_mass_runner_test",
        ROOT / "scripts/run_crta_v3_mcr_null_source_mass_ladder_v1.py")
    selected = runner.nested_source_positions(
        FakeBase(), "additive", 0, 2048)
    assert len(selected[128]) == 128
    assert len(selected[512]) == 512
    assert len(selected[2048]) == 2048
    assert set(selected[128]).issubset(set(selected[512]))
    assert set(selected[512]).issubset(set(selected[2048]))
    assert np.array_equal(selected[2048], np.arange(2048))

    summary = load(
        "mcr_null_mass_summary_test",
        ROOT / "scripts/summarize_crta_v3_mcr_null_source_mass_ladder_v1.py")
    assert summary.classify(True, True).startswith("conflict_present_by_128")
    assert "unconfirmed" in summary.classify(True, False)
    assert "extreme_regime" in summary.classify(False, True)
    assert summary.classify(False, False).endswith("unresolved")
    values = {"m1c1rf": -1.1, "m1c0rf": -1.0,
              "m0c1rf": -1.0, "m0c0rf": -1.0}
    assert np.isclose(summary.interaction(values), -0.1)
    print("MCR null-source mass ladder synthetic invariants: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
