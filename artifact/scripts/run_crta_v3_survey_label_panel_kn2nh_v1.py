#!/usr/bin/env python3
"""E4: survey-label panel, reverse direction (KNHANES -> NHANES).

Thin wrapper over the frozen v1 panel runner: benchmark flipped to
kn2nh, label maps and eval side swapped, llm table = the v2 documented
responses.  Design and the frozen asymmetry prediction:
`iclr_latex_v3/OVERNIGHT_EXPANSION_PREREGISTRATION_20260820_V1.md` (E4).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    spec = importlib.util.spec_from_file_location(
        "panel_v1_for_kn2nh",
        ROOT / "scripts/run_crta_v3_survey_label_panel_v1.py")
    panel = importlib.util.module_from_spec(spec)
    sys.modules["panel_v1_for_kn2nh"] = panel
    spec.loader.exec_module(panel)

    panel.BENCHMARK_ID = "std_cross_kn2nh_shared_anchorreset_fewshot_v1"
    # Source is now KNHANES, target is NHANES: swap every side-keyed map.
    panel.PIPELINE_LABEL_MAPS = {
        target: {"source": maps["target"], "target": maps["source"]}
        for target, maps in panel.PIPELINE_LABEL_MAPS.items()
    }
    # Fixed evaluation label: the documented NHANES-side binary.
    panel.EVAL_LABEL_MAPS = {
        "diabetes_history": {1: 1, 2: 0},
        "hypertension_history": {1: 1, 2: 0},
        "current_smoking_status": {1: 1, 2: 1, 3: 0},
    }
    panel.LLM_RESPONSE_DIR = (
        ROOT / "experiments/crta_v3_measurement_layer_v1/harmon_responses_v2")
    panel.LLM_SAMPLES = (
        "raw_documented_v2_s1.txt", "raw_documented_v2_s2.txt",
        "raw_documented_v2_s3.txt")
    panel.LLM_ITEMS = {
        target: (tgt_item, src_item)
        for target, (src_item, tgt_item) in panel.LLM_ITEMS.items()
    }
    original_rng = panel.derived_rng
    panel.derived_rng = lambda key: original_rng(
        key.replace("label_panel_v1", "label_panel_kn2nh_v1"))
    return panel.main()


if __name__ == "__main__":
    raise SystemExit(main())
