#!/usr/bin/env python3
"""Reference-minus-matched-wrong contrast for every Table 2 row.

Reuses each experiment's frozen summary module (same loader, same paired
cells, same hierarchical bootstrap, same seed) so the new column is computed
from the original cells rather than from the two published intervals.
Positive = matched-wrong is worse than the reference.
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(".")
sys.path.insert(0, str(REPO / "scripts"))

out: dict[str, dict] = {}

def rec(name: str, mean: float, ci: list[float], n: int, extra: dict | None = None) -> None:
    out[name] = {"mean": float(mean), "ci95": [float(ci[0]), float(ci[1])], "n_cells": int(n), **(extra or {})}
    print(f"{name:42s} {mean:+.4f} [{ci[0]:+.4f}, {ci[1]:+.4f}]  n={n}")

# ---------------- M: focused polarity (AUROC, higher better) ----------------
m = importlib.import_module("summarize_crta_v3_survey_label_panel_v1")
cells = m.load_cells(REPO / "experiments/crta_v3_survey_label_panel_v1")
content = m.analyze(m.paired_gains(cells, "pipeline_table", "placebo_table"), True)
util = m.analyze(m.paired_gains(cells, "pipeline_table", "raw"), False)
harm = m.analyze(m.paired_gains(cells, "raw", "placebo_table"), False)   # raw - placebo
print("M check content", content["mean_gain"], content["ci95"]); print("M check utility", util["mean_gain"], util["ci95"])
rec("M_focused_raw_minus_placebo", harm["mean_gain"], harm["ci95"], harm["n_pairs"],
    {"per_target_mean": harm["per_target_mean"], "win_rate": harm["win_rate"],
     "identity_content_minus_utility": content["mean_gain"] - util["mean_gain"]})

# ---------------- C: survey binding XGB (AUROC) ----------------
s = importlib.import_module("summarize_crta_v3_m1m2_stage_factorial_v1")
cells = s.load_cells(REPO / "experiments/crta_v3_m1m2_stage_factorial_v1")
content = s.analyze(s.cellwise(cells, lambda c: c["a11_stage_columns"] - c["pl_columns_at_stage"]))
util = s.analyze(s.cellwise(cells, lambda c: c["a11_stage_columns"] - c["a10_stage"]), with_verdict=False)
harm = s.analyze(s.cellwise(cells, lambda c: c["a10_stage"] - c["pl_columns_at_stage"]), with_verdict=False)
print("C-XGB check content", content["mean_gain"], content["ci95"]); print("C-XGB check utility", util["mean_gain"], util["ci95"])
rec("C_survey_xgb_stage_minus_deranged", harm["mean_gain"], harm["ci95"], harm["n_pairs"],
    {"per_target_mean": harm["per_target_mean"], "win_rate": harm["win_rate"],
     "identity_content_minus_utility": content["mean_gain"] - util["mean_gain"]})

# ---------------- C: survey binding HistGB (AUROC) ----------------
b = importlib.import_module("summarize_crta_v3_binding_backbone_generality_v1")
cells = b.load_cells(REPO / "experiments/crta_v3_binding_backbone_generality_v1")
# frozen completeness gate of the S5 adjudicator: exactly 10 seeds per target
_counts: dict[str, int] = {}
for _cell in cells:
    _counts[_cell["target"]] = _counts.get(_cell["target"], 0) + 1
assert sorted(_counts.values()) == [10, 10, 10], f"HistGB panel incomplete: {_counts}"
content = b.hierarchical(b.contrast_by_target(cells, ("a11_stage_columns", "pl_columns_at_stage"), "256"), "256|S5_P1_binding_content")
util = b.hierarchical(b.contrast_by_target(cells, ("a11_stage_columns", "a10_stage"), "256"), "256|S5_P2_columns_on_stage")
frozen_desc = b.hierarchical(b.contrast_by_target(cells, ("pl_columns_at_stage", "a10_stage"), "256"), "256|desc_deranged_vs_base")
harm_same_draw = b.hierarchical(b.contrast_by_target(cells, ("a10_stage", "pl_columns_at_stage"), "256"), "256|desc_deranged_vs_base")
harm_new_key = b.hierarchical(b.contrast_by_target(cells, ("a10_stage", "pl_columns_at_stage"), "256"), "256|harm_reference_vs_wrong")
print("C-Hist check content", content["mean"], content["ci95"]); print("C-Hist check utility", util["mean"], util["ci95"])
print("C-Hist frozen desc_deranged_vs_base", frozen_desc["mean"], frozen_desc["ci95"])
rec("C_survey_histgb_stage_minus_deranged", harm_same_draw["mean"], harm_same_draw["ci95"], harm_same_draw["n"],
    {"target_means": harm_same_draw["target_means"], "win": harm_same_draw["win"],
     "alt_seedkey_ci95": harm_new_key["ci95"],
     "identity_content_minus_utility": content["mean"] - util["mean"]})

# ---------------- R: NHANES-KNHANES (+rep) nRMSE lower better ----------------
p = importlib.import_module("summarize_crta_v3_pam_constraint_relations_v1")
for tag, root in (("R_nhkn", "experiments/crta_v3_pam_constraint_relations_v1"),
                  ("R_nhkn_rep1", "experiments/crta_v3_pam_constraint_relations_v1_rep1")):
    cells = p.load_cells(REPO / root)
    content = p.analyze(p.paired_gains(cells, "sign_documented", "pl_sign_flip"))
    util = p.analyze(p.paired_gains(cells, "sign_documented", "free"), with_verdict=False)
    # paired_gains(arm, reference) = reference - arm  ->  pl_sign_flip - free  (positive = flipped worse)
    harm = p.analyze(p.paired_gains(cells, "free", "pl_sign_flip"), with_verdict=False)
    print(tag, "check content", content["mean_gain"], content["ci95"]); print(tag, "check utility", util["mean_gain"], util["ci95"])
    rec(f"{tag}_flipped_minus_free", harm["mean_gain"], harm["ci95"], harm["n_pairs"],
        {"per_target_mean": harm["per_target_mean"], "win_rate": harm["win_rate"],
         "identity_content_minus_utility": content["mean_gain"] - util["mean_gain"]})

# ---------------- R: HRS sign probe ----------------
h = importlib.import_module("summarize_crta_v3_m3_sign_probe_v1")
cells = h.load_cells(REPO / "experiments/crta_v3_m3_sign_probe_v1")
content = h.analyze(h.gains(cells, "sign_flipped", "sign_documented"))
util = h.analyze(h.gains(cells, "free", "sign_documented"))
harm = h.analyze(h.gains(cells, "sign_flipped", "free"))   # flipped - free
print("HRS check content", content["mean_gain"], content["ci95"]); print("HRS check utility", util["mean_gain"], util["ci95"])
rec("R_hrs_flipped_minus_free", harm["mean_gain"], harm["ci95"], harm["n_cells"],
    {"per_endpoint_mean": harm["per_endpoint_mean"], "win_rate": harm["win_rate"],
     "identity_content_minus_utility": content["mean_gain"] - util["mean_gain"]})

# ---------------- R: CAMELS 12 basins ----------------
c = importlib.import_module("summarize_crta_v3_camels_sign_probe_v2")
root = REPO / "experiments/crta_v3_camels_sign_probe_v2"
content = c.analyze(c.load_basin_gains(root, "sign_flipped", "sign_documented", "log1p_rmse", True))
util = c.analyze(c.load_basin_gains(root, "free", "sign_documented", "log1p_rmse", True))
harm = c.analyze(c.load_basin_gains(root, "sign_flipped", "free", "log1p_rmse", True))
print("CAM12 check content", content["mean_gain"], content["ci95"]); print("CAM12 check utility", util["mean_gain"], util["ci95"])
rec("R_camels12_flipped_minus_free", harm["mean_gain"], harm["ci95"], harm["n_basin_cells"],
    {"n_basins": harm["n_basins"], "n_basins_negative": harm["n_basins_negative"], "win_rate": harm["win_rate"],
     "identity_content_minus_utility": content["mean_gain"] - util["mean_gain"]})

# ---------------- R: CAMELS 120 basins ----------------
x = importlib.import_module("summarize_crta_v3_camels_query_extension_v1")
root = REPO / "experiments/crta_v3_camels_query_extension_v1/probe"
# frozen replication gate of the extension adjudicator: every cell must have passed
_gates = [json.loads(p.read_text())["replication_gate"]["passed"] for p in sorted(root.glob("support_*/seed_*/metrics.json"))]
assert _gates and all(_gates), "CAMELS-120 replication gate missing or failed"
content = x.analyze(x.load_basin_gains(root, "sign_documented", "sign_flipped"))
util = x.analyze(x.load_basin_gains(root, "sign_documented", "free"))
harm = x.analyze(x.load_basin_gains(root, "free", "sign_flipped"))   # ref - arm = flipped - free
print("CAM120 check content", content["mean"], content["ci95"]); print("CAM120 check utility", util["mean"], util["ci95"])
rec("R_camels120_flipped_minus_free", harm["mean"], harm["ci95"], harm["n_cells"],
    {"n_clusters": harm["n_clusters"], "basins_negative": harm["basins_negative"], "win": harm["win"],
     "identity_content_minus_utility": content["mean"] - util["mean"]})

Path(sys.argv[1]).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
print("written", sys.argv[1])
