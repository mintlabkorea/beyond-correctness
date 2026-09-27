#!/usr/bin/env python3
"""Score the open-model knowledge panel (G1) against the frozen predictions.

`iclr_latex_v3/KNOWLEDGE_PANEL_OPENMODEL_PREREGISTRATION_V1.md`:
G1-P1 documentation constrains (valid-code accuracy on documented items),
G1-P2 the v2 reverse-coding convention transfers (1=yes/2=no binaries),
G1-P3 the 7 frozen sign pairs are recovered with zero flips.
Robust parsing: strips <think> blocks and code fences; unparsable
responses are recorded, not silently dropped.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "experiments/crta_v3_knowledge_panel_v1/runs"
NHKN_KEY = Path(
    "data/benchmark/"
    "relation_sources/common/questionnaire_value_harmonization_rules_v1.csv")
NHKN_PROMPT = ROOT / (
    "experiments/crta_v3_measurement_layer_v1/harmon_prompts_v2/"
    "prompt_documented_v2.txt")
KLOSA_MANIFEST = ROOT / (
    "experiments/crta_v3_klosa_measurement_extraction_v2/prompts/"
    "PROMPT_MANIFEST.json")
KLOSA_CODEBOOK = ROOT / (
    "iclr_latex_v3/method_contract/v1/medical_documents/v1/native_sources/"
    "klosa/klosa_wave9_structured_codebook.xlsx")
REV_ITEMS = ("NHANES::DIQ010", "NHANES::BPQ020", "NHANES::SMQ040")
SIGN_PAIRS = {
    ("age", "sbp"): 1, ("dbp", "sbp"): 1, ("sbp", "dbp"): 1,
    ("hba1c", "glucose"): 1, ("total_cholesterol", "triglycerides"): 1,
    ("triglycerides", "total_cholesterol"): 1, ("weight_kg", "waist_cm"): 1,
}


def parse_json(path: Path):
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    text = re.sub(r"```(?:json)?", "", text)
    start = text.find("{")
    if start < 0:
        return None
    for end in range(len(text) - 1, start, -1):
        if text[end] == "}":
            try:
                return json.loads(text[start:end + 1])
            except ValueError:
                continue
    return None


def norm(name: str) -> str:
    return str(name).split("(")[0].strip().lower()


def nhkn_truth():
    rows = list(csv.DictReader(NHKN_KEY.open(encoding="utf-8-sig")))
    truth = {r["item_id"]: sorted(float(v) for v in r["valid_codes"].split("|"))
             for r in rows}
    prompt = NHKN_PROMPT.read_text(encoding="utf-8")
    documented = set()
    for block in prompt.split("- item_id: ")[1:]:
        item = block.split("\n")[0].strip()
        if "(none available)" not in block.split("codebook value text:")[1].split("\n")[0]:
            documented.add(item)
    return truth, documented


def klosa_truth():
    manifest = json.loads(KLOSA_MANIFEST.read_text(encoding="utf-8"))
    wb = openpyxl.load_workbook(KLOSA_CODEBOOK, read_only=True)
    book = {}
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        for i, row in enumerate(rows):
            head = str(row[0]).strip().lower() if row and row[0] is not None else ""
            if not head.startswith("w09"):
                continue
            codes = []
            j = i + 1
            while j < len(rows) and (rows[j][0] is None or not str(rows[j][0]).strip()):
                text = " ".join(str(c).strip() for c in rows[j]
                                if c is not None and str(c).strip())
                match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\b", text)
                if match:
                    codes.append(float(match.group(1)))
                j += 1
            if codes:
                book[head] = sorted(set(codes))
    truth = {}
    for entry in manifest["provenance"]:
        if entry["has_codebook_values"] and entry["codebook_key"] in book:
            truth[entry["item_id"]] = book[entry["codebook_key"]]
    return truth


def main() -> int:
    nh_truth, nh_documented = nhkn_truth()
    kl_truth = klosa_truth()
    models = sorted(p.name for p in RUNS.iterdir() if p.is_dir())
    report = {"models": models, "per_model": {}, "sign_pair_votes": {},
              "adjacency_votes": {}}

    for model in models:
        entry = {}
        for prompt, truth, documented in (
                ("meas_nhkn_v2", nh_truth, nh_documented),
                ("meas_klosa_v2", kl_truth, set(kl_truth))):
            payload = parse_json(RUNS / model / prompt / "raw_response.txt")
            if payload is None or "items" not in payload:
                entry[prompt] = {"parsed": False}
                continue
            items = {i["item_id"]: i for i in payload["items"]}
            scored = matched = 0
            for item_id, valid in truth.items():
                if item_id not in items or item_id not in documented:
                    continue
                scored += 1
                got = sorted(float(v) for v in items[item_id].get("valid_codes", []))
                matched += int(got == valid)
            record = {"parsed": True, "documented_scored": scored,
                      "documented_valid_match": matched,
                      "rate": round(matched / scored, 3) if scored else None}
            if prompt == "meas_nhkn_v2":
                record["reverse_flags"] = {
                    item.split("::")[1]: bool(
                        items[item]["requires_reverse_coding"])
                    if item in items else None
                    for item in REV_ITEMS}
            entry[prompt] = record

        payload = parse_json(RUNS / model / "sign_v1" / "raw_response.txt")
        if payload and "pairs" in payload:
            got = {(norm(p.get("feature", "")), norm(p.get("target", ""))):
                   p.get("direction") for p in payload["pairs"]}
            entry["sign_v1"] = {"parsed": True, "n_pairs": len(got)}
            for pair, true_sign in SIGN_PAIRS.items():
                report["sign_pair_votes"].setdefault(
                    "|".join(pair), {})[model] = got.get(pair)
        else:
            entry["sign_v1"] = {"parsed": False}

        payload = parse_json(RUNS / model / "adj_v1" / "raw_response.txt")
        if payload and "pairs" in payload:
            entry["adj_v1"] = {"parsed": True}
            for p in payload["pairs"]:
                key = "|".join(sorted((norm(p.get("a", "")), norm(p.get("b", "")))))
                report["adjacency_votes"].setdefault(key, {})[model] = (
                    p.get("adjacency"))
        else:
            entry["adj_v1"] = {"parsed": False}
        report["per_model"][model] = entry

    parsable_nh = [m for m in models
                   if report["per_model"][m]["meas_nhkn_v2"].get("parsed")]
    p1_rates_nh = {m: report["per_model"][m]["meas_nhkn_v2"]["rate"]
                   for m in parsable_nh}
    p1_rates_kl = {m: report["per_model"][m]["meas_klosa_v2"].get("rate")
                   for m in models
                   if report["per_model"][m]["meas_klosa_v2"].get("parsed")}
    p2 = {item.split("::")[1]: sum(
        1 for m in parsable_nh
        if report["per_model"][m]["meas_nhkn_v2"]["reverse_flags"].get(
            item.split("::")[1]) is True) for item in REV_ITEMS}
    p3 = {}
    flips = 0
    for pair, votes in report["sign_pair_votes"].items():
        values = [v for v in votes.values() if v in (-1, 0, 1)]
        correct = sum(1 for v in values if v == 1)
        flipped = sum(1 for v in values if v == -1)
        flips += flipped
        p3[pair] = {"correct": correct, "zero": values.count(0),
                    "flipped": flipped, "n": len(values)}
    report["verdicts"] = {
        "G1_P1_valid_code_rates": {"nhkn_documented": p1_rates_nh,
                                   "klosa_documented": p1_rates_kl,
                                   "majority_ge_080_klosa": sum(
                                       1 for r in p1_rates_kl.values()
                                       if r is not None and r >= 0.8)},
        "G1_P2_reverse_flag_counts": {**p2, "n_parsable": len(parsable_nh)},
        "G1_P3_sign_pairs": {**p3, "total_flips": flips},
        "llama4_scout": "missing/failed (recorded per prereg)",
    }
    out = ROOT / "experiments/crta_v3_knowledge_panel_v1/SCORE_V1.json"
    out.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(json.dumps(report["verdicts"], indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
