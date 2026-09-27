#!/usr/bin/env python3
"""Render the open-model knowledge-panel prompt artifacts (G1).

Four frozen prompts -> runner artifacts (system+user messages), plus the
NEW direction-sign extraction prompt (the missing all-LLM piece of the
narrowing stack).  Output: experiments/crta_v3_knowledge_panel_v1/prompts/
with a hash manifest.  Design:
`iclr_latex_v3/KNOWLEDGE_PANEL_OPENMODEL_PREREGISTRATION_V1.md`.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/crta_v3_knowledge_panel_v1/prompts"

SYSTEM = (
    "You are a careful biomedical data annotator. Follow the output "
    "contract in the user message exactly: return one JSON object and "
    "nothing else - no prose, no code fences, no reasoning text before "
    "or after the JSON."
)

VARIABLES = {
    "age": "age (years)",
    "height_cm": "standing height (cm)",
    "weight_kg": "body weight (kg)",
    "waist_cm": "waist circumference (cm)",
    "sbp": "systolic blood pressure (mmHg)",
    "dbp": "diastolic blood pressure (mmHg)",
    "glucose": "fasting plasma glucose (mg/dL)",
    "hba1c": "glycated hemoglobin HbA1c (%)",
    "creatinine": "serum creatinine (mg/dL)",
    "hemoglobin": "hemoglobin (g/dL)",
    "total_cholesterol": "total cholesterol (mg/dL)",
    "triglycerides": "triglycerides (mg/dL)",
}
TARGETS = ("glucose", "waist_cm", "triglycerides", "sbp", "dbp",
           "total_cholesterol")


def sign_prompt() -> str:
    pairs = [(f, t) for t in TARGETS for f in VARIABLES if f != t]
    lines = [f"- feature: {f} ({VARIABLES[f]})   target: {t} ({VARIABLES[t]})"
             for f, t in pairs]
    return (
        "You are annotating the MARGINAL direction of association between\n"
        "clinical variables in general adult populations.  Downstream code\n"
        "will use your answers as monotonicity constraints in a predictive\n"
        "model, so a wrong nonzero answer is costly and 0 is always safe.\n\n"
        "For each (feature, target) pair below, report direction:\n"
        "1 if it is established, standard clinical knowledge that larger\n"
        "feature values go with larger target values (marginally, in the\n"
        "general population); -1 if larger feature values go with smaller\n"
        "target values; 0 if there is no established monotone marginal\n"
        "association, or it is weak, disputed, or unknown.  Be selective:\n"
        "reserve nonzero for textbook-grade directions.\n\n"
        "PAIRS:\n" + "\n".join(lines) + "\n\n"
        "Return one JSON object and nothing else.  No prose, no code fence.\n\n"
        "{\n"
        '  "pairs": [\n'
        "    {\n"
        '      "feature": "<feature name exactly as given>",\n'
        '      "target": "<target name exactly as given>",\n'
        '      "direction": 1 | 0 | -1,\n'
        '      "basis": "<one short clause naming the mechanism, or the reason for 0>"\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        f"Cover all {len(pairs)} pairs exactly once, in the order given.\n"
    )


def main() -> int:
    sources = {
        "meas_nhkn_v2": ROOT / (
            "experiments/crta_v3_measurement_layer_v1/harmon_prompts_v2/"
            "prompt_documented_v2.txt"),
        "meas_klosa_v2": ROOT / (
            "experiments/crta_v3_klosa_measurement_extraction_v2/prompts/"
            "prompt_documented_v2.txt"),
        "adj_v1": ROOT / (
            "experiments/crta_v3_concept_adjacency_extraction_v1/prompts/"
            "prompt_v1.txt"),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    texts = {name: path.read_text(encoding="utf-8")
             for name, path in sources.items()}
    texts["sign_v1"] = sign_prompt()
    (OUT / "prompt_sign_v1.txt").write_text(texts["sign_v1"], encoding="utf-8")

    manifest = {"system_sha256": hashlib.sha256(SYSTEM.encode()).hexdigest(),
                "prompts": {}}
    for name, text in texts.items():
        artifact = {
            "contract_version": "crta-knowledge-panel-1.0.0",
            "prompt_id": name,
            "generation_config": {"do_sample": False,
                                  "max_new_tokens": 8192},
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": text},
            ],
        }
        path = OUT / f"artifact_{name}.json"
        path.write_text(json.dumps(artifact, ensure_ascii=False, indent=1)
                        + "\n", encoding="utf-8")
        manifest["prompts"][name] = {
            "user_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "chars": len(text),
        }
    (OUT / "ARTIFACT_MANIFEST.json").write_text(
        json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({name: v["user_sha256"][:16]
                      for name, v in manifest["prompts"].items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
