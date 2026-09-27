#!/usr/bin/env python3
"""Decompose TabLLM's published zero-shot List ablation table.

This script uses only the two-decimal means printed in Tables 12--14 of
Hegselmann et al. (2023).  It is a retrospective audit of already published
evidence, not the exact-score reproduction frozen separately in
TABLLM_RETROSPECTIVE_AUDIT_FREEZE_V1.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/tabllm_published_three_arm_v1/SUMMARY_V1.json"
SOURCE = "Hegselmann et al. (2023), Tables 12--14, zero-shot columns"

# S: List Template; W: List Permuted Names; R: List Only Values.
PUBLISHED = {
    "bank": {"S": 0.60, "W": 0.64, "R_pub": 0.56},
    "blood": {"S": 0.56, "W": 0.52, "R_pub": 0.45},
    "california": {"S": 0.61, "W": 0.54, "R_pub": 0.58},
    "car": {"S": 0.79, "W": 0.39, "R_pub": 0.48},
    "credit-g": {"S": 0.53, "W": 0.44, "R_pub": 0.66},
    "diabetes": {"S": 0.64, "W": 0.56, "R_pub": 0.55},
    "heart": {"S": 0.52, "W": 0.57, "R_pub": 0.40},
    "income": {"S": 0.79, "W": 0.65, "R_pub": 0.73},
    "jungle": {"S": 0.63, "W": 0.40, "R_pub": 0.58},
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    rows = {}
    positive_content_shares = []
    utility_dominant = []
    harm_dominant = []
    utility_sign_reversals = []
    wrong_better_than_reference = []
    for dataset, values in PUBLISHED.items():
        content = values["S"] - values["W"]
        utility = values["S"] - values["R_pub"]
        harm = values["R_pub"] - values["W"]
        identity = content - utility - harm
        harm_share = harm / content if content > 0 else None
        if harm_share is not None:
            positive_content_shares.append(harm_share)
        if content > 0 and utility < 0:
            utility_sign_reversals.append(dataset)
        if harm < 0:
            wrong_better_than_reference.append(dataset)
        if content > 0:
            (harm_dominant if harm > utility else utility_dominant).append(dataset)
        rows[dataset] = {
            **values,
            "content_S_minus_W": content,
            "utility_S_minus_R_pub": utility,
            "wrong_harm_R_pub_minus_W": harm,
            "identity_residual": identity,
            "harm_share_given_positive_content": harm_share,
        }

    macro_s = float(np.mean([x["S"] for x in PUBLISHED.values()]))
    macro_w = float(np.mean([x["W"] for x in PUBLISHED.values()]))
    macro_r = float(np.mean([x["R_pub"] for x in PUBLISHED.values()]))
    macro_content = macro_s - macro_w
    macro_utility = macro_s - macro_r
    macro_harm = macro_r - macro_w
    payload = {
        "analysis_status": "retrospective_audit_of_published_rounded_table",
        "source": SOURCE,
        "rounding_caveat": (
            "Inputs are the paper's two-decimal printed means. Exact-score "
            "reproduction and paired example bootstrap are a separate frozen run."
        ),
        "metric": "test AUROC; macro one-versus-rest for Car",
        "arms": {
            "S": "TabLLM List Template",
            "W": "TabLLM List Permuted Names",
            "R_pub": "TabLLM List Only Values",
        },
        "per_dataset": rows,
        "macro_nine_datasets": {
            "S": macro_s,
            "W": macro_w,
            "R_pub": macro_r,
            "content_S_minus_W": macro_content,
            "utility_S_minus_R_pub": macro_utility,
            "wrong_harm_R_pub_minus_W": macro_harm,
            "identity_residual": macro_content - macro_utility - macro_harm,
            "utility_share_of_positive_content": macro_utility / macro_content,
            "wrong_harm_share_of_positive_content": macro_harm / macro_content,
        },
        "prespecified_heterogeneity_descriptives": {
            "positive_content_dataset_count": len(positive_content_shares),
            "harm_share_median": float(np.median(positive_content_shares)),
            "harm_share_range": [
                float(np.min(positive_content_shares)),
                float(np.max(positive_content_shares)),
            ],
            "utility_dominant_count": len(utility_dominant),
            "utility_dominant_datasets": utility_dominant,
            "harm_dominant_count": len(harm_dominant),
            "harm_dominant_datasets": harm_dominant,
            "utility_sign_reversal_count": len(utility_sign_reversals),
            "utility_sign_reversal_datasets": utility_sign_reversals,
            "wrong_better_than_reference_count": len(wrong_better_than_reference),
            "wrong_better_than_reference_datasets": wrong_better_than_reference,
        },
        "provenance": {"summarizer_sha256": sha256_file(Path(__file__))},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload["macro_nine_datasets"], indent=1, sort_keys=True))
    print(json.dumps(payload["prespecified_heterogeneity_descriptives"], indent=1, sort_keys=True))
    print(json.dumps({"written": str(OUT)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
