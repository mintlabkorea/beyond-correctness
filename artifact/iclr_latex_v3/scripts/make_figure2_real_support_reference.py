#!/usr/bin/env python3
# Proposed caption: Target-support attenuation across controlled and real settings.
# (a) Controlled pairwise-XGB predictive utility at the largest tested
# measurement difference.
# (b) TabLLM feature-name utility relative to the name-masked reference across
# labeled adaptation examples, averaged over nine datasets.
# (c) Examination-transfer correspondence utility for the six-target directional-
# replication and 13-target exploratory panels. Error bars are stored 95% CIs.
# Metrics and support definitions differ across panels; equal tick spacing
# indicates evaluated support levels, not equal numerical increments.
"""Regenerate only the three-panel Figure 2 through the main plotting pipeline."""
import hashlib
import json
from pathlib import Path

import make_main_figures as mf


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    sources = [mf.REPO_ROOT / "experiments" / name / "SUMMARY_V1.json" for name in (
        "crta_v3_mcr_mismatch_support_ladder_v1",
        "tabllm_ranon_support_ladder_v1",
        "crta_v3_exam_support_ladder_v1",
    )]
    mf.make_real_support_reference_figure()
    outputs = [mf.OUT_DIR / f"figure2_real_support_reference.{ext}" for ext in ("pdf", "png")]
    provenance = {
        "panel_order": ["a: controlled pairwise XGB", "b: TabLLM", "c: examination transfer"],
        "intervals": "Stored 95% confidence intervals; no re-estimation",
        "sources": {str(p.relative_to(mf.REPO_ROOT)): digest(p) for p in sources},
        "scripts": {str(p.relative_to(mf.REPO_ROOT)): digest(p) for p in
                    [Path(__file__).resolve(), Path(mf.__file__).resolve()]},
        "outputs": {str(p.relative_to(mf.REPO_ROOT)): digest(p) for p in outputs},
    }
    manifest = mf.OUT_DIR / "figure2_real_support_reference_provenance.json"
    manifest.write_text(json.dumps(provenance, indent=2) + "\n")
    print("Sources:", *sources, sep="\n  ")
    print("Pipeline: make_main_figures.make_real_support_reference_figure")
    print("Outputs:", *outputs, manifest, sep="\n  ")


if __name__ == "__main__":
    main()
