#!/usr/bin/env python3
"""Adjudicate the expanded-panel examination reference sensitivity.

Reuses the frozen summarizer's inference by import.  Applies the protocol's
coherence bar and strongest-reference rule, and reports every contrast on
the full 13-endpoint panel and on the class-A (original six) restriction.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FROZEN_SUMMARIZER = ROOT / "scripts/summarize_crta_v3_exam_no_bridge_reference_v1.py"
DEFAULT_ROOT = ROOT / "experiments/crta_v3_exam_reference_sensitivity_v2"
V1_ROOT = ROOT / "experiments/crta_v3_exam_reference_sensitivity_v1"

SUPPLIED = "S_shared_bridge"
WRONG = "W_deranged_bridge"
REFERENCES = ("R_domain_local", "R_domain_offset", "R_target_local_only")
V1_SHARED_ARMS = (SUPPLIED, WRONG, "R_domain_local", "R_domain_offset",
                  "S_unpadded", "W_unpadded")
EXPECTED_CELLS = 130


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def group(cells, left, right, keep=None):
    out: dict[str, list] = {}
    for cell in cells:
        if keep and cell.get("target_class") not in keep:
            continue
        value = float(cell["nrmse"][right]) - float(cell["nrmse"][left])
        out.setdefault(cell["target"], []).append(value)
    return {k: np.asarray(v, dtype=float) for k, v in out.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=DEFAULT_ROOT)
    args = parser.parse_args()
    frozen = load("exam_frozen_summarizer", FROZEN_SUMMARIZER)

    cells = [json.loads(p.read_text(encoding="utf-8"))
             for p in sorted(args.root.glob("*/seed_*/metrics.json"))]
    if len(cells) != EXPECTED_CELLS:
        raise RuntimeError(f"expected {EXPECTED_CELLS} cells, found {len(cells)}")

    # --- integrity: class A must reproduce v1 bit-identically -----------
    worst, n_cmp, exact = 0.0, 0, 0
    for cell in cells:
        if cell.get("target_class") != "A":
            continue
        path = V1_ROOT / cell["target"] / f"seed_{cell['seed']}/metrics.json"
        if not path.is_file():
            continue
        published = json.loads(path.read_text(encoding="utf-8"))["nrmse"]
        for arm in V1_SHARED_ARMS:
            delta = abs(cell["nrmse"][arm] - published[arm])
            worst = max(worst, delta)
            n_cmp += 1
            exact += int(delta < 1e-15)
    integrity = {"class_A_reproduces_v1": {
        "n_comparisons": n_cmp, "bit_identical": exact,
        "worst_abs_delta_nrmse": worst,
        "pass": bool(n_cmp > 0 and exact == n_cmp)}}

    rng = np.random.default_rng(frozen.BOOTSTRAP_SEED)
    index = [0]

    def evaluate(left, right, keep=None):
        groups = group(cells, left, right, keep)
        record = frozen.analyze(groups, rng)
        spread = float(np.std(list(record["per_endpoint_mean"].values())))
        if spread > 0.0:
            record["interval_sensitivities"] = frozen.interval_sensitivities(
                record["per_endpoint_mean"],
                frozen.BOOTSTRAP_SEED + 100 + index[0])
        else:
            record["interval_sensitivities"] = {
                "status": "degenerate: zero between-endpoint variance"}
        index[0] += 1
        return record

    # --- coherence bar, then the strongest-reference rule ---------------
    mean_nrmse = {ref: float(np.mean([c["nrmse"][ref] for c in cells]))
                  for ref in REFERENCES}
    coherence = {ref: evaluate(ref, WRONG) for ref in REFERENCES}
    admissible = [ref for ref in REFERENCES if coherence[ref]["separated"]]
    selected = (min(admissible, key=lambda r: mean_nrmse[r])
                if admissible else None)

    panels = {"full_13_endpoints": None, "class_A_original_six": ("A",)}
    contrasts: dict = {}
    for panel_name, keep in panels.items():
        block = {"content_S_minus_W": evaluate(SUPPLIED, WRONG, keep)}
        for ref in REFERENCES:
            block[f"utility_S_minus_{ref}"] = evaluate(SUPPLIED, ref, keep)
            block[f"coherence_{ref}_minus_W"] = evaluate(ref, WRONG, keep)
        block["desc_padding_S_minus_S_unpadded"] = evaluate(
            SUPPLIED, "S_unpadded", keep)
        contrasts[panel_name] = block

    per_class = {}
    for cls in ("A", "B", "C"):
        sub = [c for c in cells if c.get("target_class") == cls]
        per_class[cls] = {
            "n_endpoints": len({c["target"] for c in sub}),
            "targets": sorted({c["target"] for c in sub}),
            "utility_vs_R_domain_local_mean": float(np.mean(
                [c["nrmse"]["R_domain_local"] - c["nrmse"][SUPPLIED]
                 for c in sub])),
            "content_mean": float(np.mean(
                [c["nrmse"][WRONG] - c["nrmse"][SUPPLIED] for c in sub])),
        }

    primary_key = f"utility_S_minus_{selected}" if selected else None
    primary = (contrasts["full_13_endpoints"][primary_key]
               if primary_key else None)
    verdicts = {
        "reference_mean_nrmse": mean_nrmse,
        "coherence_bar_pass": {r: bool(coherence[r]["separated"])
                               for r in REFERENCES},
        "admissible_references": admissible,
        "selected_strongest_reference": selected,
        "selection_rule": ("lowest pooled mean nRMSE among references that "
                           "pass the coherence bar; chosen once globally"),
        "survives_strongest_coherent_reference": bool(
            primary and primary["separated"]),
    }
    if not integrity["class_A_reproduces_v1"]["pass"]:
        verdicts = {"status": "class-A reproduction failed — verdicts withheld"}

    summary = {
        "analysis_status": "frozen-before-execution expanded-panel extension",
        "protocol": "experiments/crta_v3_exam_reference_sensitivity_v2/PROTOCOL_V1.md",
        "metric": "query_sd_normalized_rmse (lower is better); "
                  "gain = right arm minus left arm, positive favours the left",
        "bootstrap": {"reps": frozen.BOOTSTRAP_REPS,
                      "seed": frozen.BOOTSTRAP_SEED,
                      "hierarchy": "endpoints then paired seeds"},
        "n_cells": len(cells),
        "n_endpoints": len({c["target"] for c in cells}),
        "hosts": sorted({c.get("host", "?") for c in cells}),
        "integrity": integrity,
        "per_class": per_class,
        "contrasts": contrasts,
        "verdicts": verdicts,
    }
    out = args.root / "SUMMARY_V1.json"
    out.write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps({"written": str(out), "integrity": integrity,
                      "verdicts": verdicts}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
