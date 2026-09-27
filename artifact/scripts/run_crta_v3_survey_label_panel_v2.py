#!/usr/bin/env python3
"""Survey-label panel v2: the extraction-v2 llm table.

Thin wrapper around the frozen v1 runner
(`run_crta_v3_survey_label_panel_v1.py`): identical design and
adjudication, with the llm table read from the v2 documented responses
and the placebo rng namespace bumped so the wrong tables are fresh draws.
Design: `iclr_latex_v3/M1M2_SURVEY_LABEL_PANEL_V2_ADDENDUM_PREREGISTRATION.md`.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    panel = _load("panel_v1_for_v2",
                  ROOT / "scripts/run_crta_v3_survey_label_panel_v1.py")
    panel.LLM_RESPONSE_DIR = (
        ROOT / "experiments/crta_v3_measurement_layer_v1/harmon_responses_v2")
    panel.LLM_SAMPLES = (
        "raw_documented_v2_s1.txt", "raw_documented_v2_s2.txt",
        "raw_documented_v2_s3.txt")

    original_rng = panel.derived_rng
    panel.derived_rng = lambda key: original_rng(
        key.replace("label_panel_v1", "label_panel_v2"))
    return panel.main()


if __name__ == "__main__":
    raise SystemExit(main())
