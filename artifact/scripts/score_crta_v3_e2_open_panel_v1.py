#!/usr/bin/env python3
"""Score the E2 open-panel responses (v3 prompt with acquired NHANES value
tables) against the frozen harmonization key, and adjudicate E2-P1.

Per model: parse the raw response JSON; for the six label items (and the
extra NHANES SMQ020) report valid-code exact match, reverse-coding flag
(requires_reverse_coding or ordinal_direction == higher_is_less), and the
`basis` field.  E2-P1: at least one model flags reverse coding for all of
NHANES DIQ010/BPQ020/SMQ040 with basis "documentation".
Prereg: iclr_latex_v3/E2_QUESTIONNAIRE_VALUE_TABLE_OPEN_PANEL_PREREGISTRATION_V1.md.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "experiments/crta_v3_e2_open_panel_v1/runs"
KEY = Path("data/benchmark/"
           "relation_sources/common/questionnaire_value_harmonization_rules_v1.csv")
LABEL_ITEMS = ("NHANES::DIQ010", "KNHANES::ALL__de1_dg", "NHANES::BPQ020",
               "KNHANES::ALL__di1_dg", "NHANES::SMQ040", "KNHANES::ALL__bs3_1")
NHANES_REVERSE_ITEMS = ("NHANES::DIQ010", "NHANES::BPQ020", "NHANES::SMQ040")


def parse_response(text: str) -> dict | None:
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return None
    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        return None
    return {str(item.get("item_id")): item for item in items if isinstance(item, dict)}


def codes(value) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        return {v.strip() for v in value.split("|") if v.strip()}
    return {str(int(v)) if float(v).is_integer() else str(v) for v in value if v is not None}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=RUNS)
    parser.add_argument("--key", type=Path, default=KEY)
    parser.add_argument("--out", type=Path,
                        default=ROOT / "experiments/crta_v3_e2_open_panel_v1/E2_SCORE_V1.json")
    args = parser.parse_args()
    key = pd.read_csv(args.key)
    key_index = {str(row["item_id"]): row for _, row in key.iterrows()}
    models: dict[str, dict] = {}
    for run in sorted(args.runs.glob("*/")):
        raw = run / "raw_response.txt"
        if not raw.is_file():
            continue
        items = parse_response(raw.read_text(encoding="utf-8", errors="replace"))
        record: dict = {"parsed": items is not None, "items": {}}
        if items is not None:
            for item_id in LABEL_ITEMS + ("NHANES::SMQ020",):
                it = items.get(item_id)
                if it is None:
                    record["items"][item_id] = {"present": False}
                    continue
                valid = codes(it.get("valid_codes"))
                k = key_index.get(item_id)
                key_valid = codes(k["valid_codes"]) if k is not None else None
                reverse = bool(it.get("requires_reverse_coding")) or (
                    it.get("ordinal_direction") == "higher_is_less")
                record["items"][item_id] = {
                    "present": True, "valid_codes": sorted(valid),
                    "valid_codes_match_key": (valid == key_valid) if key_valid is not None else None,
                    "reverse": reverse, "basis": it.get("basis"),
                    "ordinal_direction": it.get("ordinal_direction"),
                }
            record["all_label_items_nonempty"] = all(
                record["items"].get(i, {}).get("present") and record["items"][i]["valid_codes"]
                for i in LABEL_ITEMS)
            record["nhanes_reverse_documented"] = all(
                record["items"].get(i, {}).get("present")
                and record["items"][i]["reverse"]
                and record["items"][i]["basis"] == "documentation"
                for i in NHANES_REVERSE_ITEMS)
            record["nhanes_reverse_any_basis"] = all(
                record["items"].get(i, {}).get("present") and record["items"][i]["reverse"]
                for i in NHANES_REVERSE_ITEMS)
        models[run.name] = record
    n_doc = sum(1 for m in models.values() if m.get("nhanes_reverse_documented"))
    n_any = sum(1 for m in models.values() if m.get("nhanes_reverse_any_basis"))
    payload = {"n_models": len(models), "models": models,
               "E2_P1": {"n_models_reverse_all_three_documented": n_doc,
                         "n_models_reverse_all_three_any_basis": n_any,
                         "prior_panel": "0/7", "pass": bool(n_doc >= 1)},
               "materializable_models": sorted(k for k, m in models.items()
                                               if m.get("all_label_items_nonempty"))}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1, sort_keys=True))
    print(json.dumps({"E2_P1": payload["E2_P1"],
                      "materializable": payload["materializable_models"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
