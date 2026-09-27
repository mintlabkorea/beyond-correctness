#!/usr/bin/env python3
"""Run the frozen ten-endpoint extension of the survey-label panel."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts/run_crta_v3_survey_label_panel_v1.py"
REGISTRY = ROOT / "scripts/crta_v3_stage_endpoint_registry_v1.py"
PREREG = ROOT / "iclr_latex_v3/SURVEY_LABEL_PANEL_ENDPOINT_EXPANSION_PREREGISTRATION_V1.md"
ORIGINAL_TARGETS = {
    "diabetes_history", "hypertension_history", "current_smoking_status"}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def added_documented_specs(direction: str, targets) -> dict:
    forward = {
        "source": {
            "map": {1.0: 1.0, 2.0: 0.0}, "valid": [1.0, 2.0],
            "sentinel": [7.0, 9.0], "reverse": True,
            "provenance": "codebook_registry_not_llm"},
        "target": {
            "map": {0.0: 0.0, 1.0: 1.0}, "valid": [0.0, 1.0],
            "sentinel": [8.0, 9.0], "reverse": False,
            "provenance": "codebook_registry_not_llm"},
    }
    if direction == "kn2nh":
        forward = {"source": forward["target"], "target": forward["source"]}
    return {
        target: {
            side: {key: (dict(value) if key == "map" else list(value)
                         if key in ("valid", "sentinel") else value)
                   for key, value in spec.items()}
            for side, spec in forward.items()
        }
        for target in targets if target not in ORIGINAL_TARGETS
    }


def configure(direction: str):
    if direction not in ("nh2kn", "kn2nh"):
        raise ValueError(f"unknown direction {direction}")
    panel = load(f"label_panel_base_{direction}", BASE)
    registry = load(f"label_panel_registry_{direction}", REGISTRY)
    panel.TARGETS = dict(registry.ENDPOINTS)
    panel.TARGET_SET = "survey_label_panel_endpoint_expansion_v1"
    panel.SUPPORT_ROWS = (256,)

    source_binary = {1: 1, 2: 0}
    target_binary = {1: 1, 0: 0}
    pipeline = {
        target: {"source": dict(source_binary), "target": dict(target_binary)}
        for target in panel.TARGETS
    }
    pipeline["current_smoking_status"] = {
        "source": {1: 1, 2: 1, 3: 0},
        "target": {1: 1, 2: 1, 3: 0, 4: 0},
    }
    eval_maps = {target: dict(target_binary) for target in panel.TARGETS}
    eval_maps["current_smoking_status"] = {1: 1, 2: 1, 3: 0, 4: 0}

    if direction == "kn2nh":
        panel.BENCHMARK_ID = "std_cross_kn2nh_shared_anchorreset_fewshot_v1"
        pipeline = {
            target: {"source": maps["target"], "target": maps["source"]}
            for target, maps in pipeline.items()
        }
        eval_maps = {
            target: ({1: 1, 2: 1, 3: 0}
                     if target == "current_smoking_status" else {1: 1, 2: 0})
            for target in panel.TARGETS
        }
        panel.LLM_RESPONSE_DIR = (
            ROOT / "experiments/crta_v3_measurement_layer_v1/harmon_responses_v2")
        panel.LLM_SAMPLES = (
            "raw_documented_v2_s1.txt", "raw_documented_v2_s2.txt",
            "raw_documented_v2_s3.txt")
        panel.LLM_ITEMS = {
            target: (target_item, source_item)
            for target, (source_item, target_item) in panel.LLM_ITEMS.items()
        }
        original_rng = panel.derived_rng
        panel.derived_rng = lambda key: original_rng(
            key.replace("label_panel_v1", "label_panel_kn2nh_v1"))

    panel.PIPELINE_LABEL_MAPS = pipeline
    panel.EVAL_LABEL_MAPS = eval_maps
    original_load_specs = panel.load_llm_label_specs

    def hybrid_specs():
        specs = original_load_specs()
        for target in ORIGINAL_TARGETS:
            for side in ("source", "target"):
                specs[target][side]["provenance"] = "isolated_llm_majority"
        specs.update(added_documented_specs(direction, panel.TARGETS))
        if set(specs) != set(panel.TARGETS):
            raise RuntimeError("hybrid label-table registry is incomplete")
        return specs

    panel.load_llm_label_specs = hybrid_specs
    return panel, registry


def pop_option(name: str) -> str | None:
    if name not in sys.argv:
        return None
    index = sys.argv.index(name)
    if index + 1 >= len(sys.argv):
        raise RuntimeError(f"missing value for {name}")
    value = sys.argv[index + 1]
    del sys.argv[index:index + 2]
    return value


def main() -> int:
    direction = pop_option("--direction")
    if direction is None:
        raise RuntimeError("--direction {nh2kn,kn2nh} is required")
    validate_only = "--validate-only" in sys.argv
    if validate_only:
        sys.argv.remove("--validate-only")
    panel, registry = configure(direction)
    if validate_only:
        specs = panel.load_llm_label_specs()
        print(json.dumps({
            "direction": direction,
            "targets": list(panel.TARGETS),
            "support_rows": list(panel.SUPPORT_ROWS),
            "original_llm_targets": sorted(ORIGINAL_TARGETS),
            "added_table_provenance": "codebook_registry_not_llm",
            "hashes": {
                "runner_sha256": sha256_file(Path(__file__)),
                "base_sha256": sha256_file(BASE),
                "registry_sha256": sha256_file(REGISTRY),
                "prereg_sha256": sha256_file(PREREG),
            },
            "spec_targets": sorted(specs),
        }, indent=1, sort_keys=True))
        return 0
    return panel.main()


if __name__ == "__main__":
    raise SystemExit(main())
