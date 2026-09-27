#!/usr/bin/env python3
"""Synthetic and configuration tests for the ten-endpoint label panel."""

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
        "label_panel_10_runner_test",
        ROOT / "scripts/run_crta_v3_survey_label_panel_endpoint_expansion_v1.py")
    for direction in ("nh2kn", "kn2nh"):
        panel, _ = runner.configure(direction)
        specs = panel.load_llm_label_specs()
        assert len(panel.TARGETS) == 10
        assert panel.SUPPORT_ROWS == (256,)
        assert set(specs) == set(panel.TARGETS)
        for target in set(panel.TARGETS) - runner.ORIGINAL_TARGETS:
            assert all(specs[target][side]["provenance"]
                       == "codebook_registry_not_llm"
                       for side in ("source", "target"))
            assert specs[target]["source"]["map"] == (
                {1.0: 1.0, 2.0: 0.0} if direction == "nh2kn"
                else {0.0: 0.0, 1.0: 1.0})

    summary = load(
        "label_panel_10_summary_test",
        ROOT / "scripts/summarize_crta_v3_survey_label_panel_endpoint_expansion_v1.py")
    units = {
        f"e{i}": {direction: np.asarray([0.1, 0.2, 0.3])
                   for direction in summary.DIRECTIONS}
        for i in range(10)}
    result = summary.summarize_values(units, "synthetic")
    assert np.isclose(result["mean"], 0.2)
    assert result["drop_best_mean"] > 0
    assert summary.same_float(float("nan"), float("nan"))
    print("Ten-endpoint survey-label panel synthetic invariants: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
