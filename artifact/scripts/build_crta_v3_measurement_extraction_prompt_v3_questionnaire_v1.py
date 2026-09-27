#!/usr/bin/env python3
"""Build the v3 NHANES/KNHANES measurement-extraction prompt: the frozen v2
prompt (nhkn-harmon-extraction-2.0.0, sha d0ec7ec0...) with the NHANES
questionnaire items' `codebook value text: (none available)` lines replaced
by the value-table TEXT extracted from the governed CDC snapshot acquired on
2026-08-25 (DIQ_J, BPQ_J, SMQ_J).  Nothing else in the prompt changes; the
diff against v2 is exactly the substituted lines.  Also renders the panel
runner artifact (system + user messages, hashes, schema_pair_id).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "experiments/crta_v3_measurement_layer_v1/harmon_prompts_v2/prompt_documented_v2.txt"
V2_SHA = "d0ec7ec0f6eeb8be65791de9cc2e08081ca9f5272a314151476d61abb2622a9e"
TABLES = ROOT / "experiments/crta_v3_measurement_layer_v1/nhanes_value_tables_questionnaire_v1.csv"
OUT = ROOT / "experiments/crta_v3_measurement_layer_v1/harmon_prompts_v3"
SYSTEM = (
    "You are a careful biomedical data annotator. Follow the output "
    "contract in the user message exactly: return one JSON object and "
    "nothing else - no prose, no code fences, no reasoning text before "
    "or after the JSON."
)


def main() -> int:
    text = V2.read_text(encoding="utf-8")
    if hashlib.sha256(text.encode()).hexdigest() != V2_SHA:
        raise SystemExit("v2 prompt hash mismatch")
    tables = pd.read_csv(TABLES)
    values = {str(r["variable"]).strip().upper(): str(r["value_table_text"]).strip()
              for _, r in tables.iterrows()}
    lines = text.split("\n")
    substituted = []
    for i, line in enumerate(lines):
        if line.startswith("- item_id: NHANES::"):
            var = line.split("NHANES::", 1)[1].strip()
            for j in range(i + 1, min(i + 6, len(lines))):
                if lines[j].strip() == "codebook value text: (none available)" and var in values:
                    # keep the value-table text on one line, strip the trailing html fragment
                    vt = values[var].split("<h3", 1)[0].strip()
                    lines[j] = f"  codebook value text: {vt}"
                    substituted.append(var)
                    break
    out_text = "\n".join(lines)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "prompt_documented_v3.txt").write_text(out_text, encoding="utf-8")
    sha = hashlib.sha256(out_text.encode()).hexdigest()
    artifact = {
        "contract_version": "crta-knowledge-panel-1.0.0",
        "prompt_id": "meas_nhkn_v3",
        "schema_pair_id": "nhanes_knhanes_survey_measurement_v1",
        "generation_config": {"do_sample": False, "max_new_tokens": 8192},
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": out_text}],
        "hashes": {"system_sha256": hashlib.sha256(SYSTEM.encode()).hexdigest(),
                   "user_sha256": sha,
                   "messages_sha256": hashlib.sha256(json.dumps(
                       [{"role": "system", "content": SYSTEM},
                        {"role": "user", "content": out_text}],
                       ensure_ascii=False, sort_keys=True).encode()).hexdigest()},
    }
    (OUT / "artifact_meas_nhkn_v3.json").write_text(
        json.dumps(artifact, ensure_ascii=False, indent=1), encoding="utf-8")
    manifest = {"prompt_version": "nhkn-harmon-extraction-3.0.0",
                "derivation": "v2 prompt verbatim; NHANES questionnaire value text substituted from the 2026-08-25 governed CDC snapshot (DIQ_J, BPQ_J, SMQ_J)",
                "v2_sha256": V2_SHA, "prompt_sha256": sha, "chars": len(out_text),
                "substituted_items": substituted,
                "value_tables_sha256": hashlib.sha256(TABLES.read_bytes()).hexdigest()}
    (OUT / "PROMPT_MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print(json.dumps(manifest, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
