#!/usr/bin/env python3
"""Freeze the prompts for the measurement-table extraction experiment.

`questionnaire_value_harmonization_rules_v1.csv` is a hand-authored table of 17
survey items that the benchmark applies to every row **before any method sees
data**: valid codes, sentinel codes, ordinal direction, and a reverse-coding
flag, per cohort.  It is the measurement layer of the original design, paid for
by hand and never credited.  This experiment asks whether a model can produce
it.

Two arms:

    documented      each item's cohort codebook entry is supplied where one
                    exists.  Only the KNHANES codebook states value meanings
                    (7 of 9 KNHANES items match by name); the local NHANES
                    corpus carries none, so its 8 items get name and label only.
    knowledge_only  name and label only for all 17 items -- a ceiling arm whose
                    output comes from the model's own survey-instrument prior.

Scoring is exact-match against the frozen table on four fields, reported
separately for items that had codebook text and items that did not, so the
documentation contribution is separable from the prior.

The prompt is outcome-blind: it never states how many items are ordinal, which
need reversing, that a key exists, or that any item matters more than another.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KEY_CSV = Path(
    "data/benchmark"
    "/relation_sources/common/questionnaire_value_harmonization_rules_v1.csv"
)
KNHANES_CODEBOOK = Path(
    "data/external 2020-2024"
    "/9_KHANES_codebook.csv"
)
NHANES_SURFACE = Path(
    "data/nhanes_knhanes/tasks/standard_benchmark/current/results"
    "/nh_controlled_aux_v0/stage4_codebook_surface_corpus_v0.csv"
)

OUTPUT_CONTRACT = """
Return one JSON object and nothing else.  No prose, no code fence.

{
  "items": [
    {
      "item_id": "<exactly as given>",
      "response_type": "binary" | "ordinal" | "categorical" | "continuous",
      "valid_codes": [<the numeric codes that carry a real answer>],
      "missing_or_sentinel_codes": [<codes meaning refused / don't know / not applicable>],
      "ordinal_direction": "higher_is_more" | "higher_is_less" | "unordered",
      "requires_reverse_coding": true | false,
      "basis": "documentation" | "prior"
    }
  ]
}

`ordinal_direction` describes what a LARGER code number means for the quantity
the item measures: "higher_is_more" if a larger code means more of it,
"higher_is_less" if a larger code means less of it, "unordered" if the codes are
categories with no magnitude ordering.  `requires_reverse_coding` is true when
the code order runs opposite to the quantity's natural direction.  Set `basis`
to "documentation" only when the supplied codebook text determines your answer,
and to "prior" when you are relying on knowledge of the instrument.
""".strip()

DOCUMENTED_INSTRUCTIONS = """
You are building a value-harmonization table for survey items drawn from two
cohort studies, NHANES (United States) and KNHANES (Korea).  Downstream code
will use this table to decide which numeric codes are real answers, which are
non-answers to be masked, and whether a code ordering runs opposite to the
quantity being measured.

For each item below, report the four fields in the output contract.  Where a
codebook entry is supplied, it is authoritative; where none is supplied, say so
by setting `basis` to "prior" rather than inventing a citation.  Report every
item; do not skip any.
""".strip()

KNOWLEDGE_ONLY_INSTRUCTIONS = """
You are building a value-harmonization table for survey items drawn from two
cohort studies, NHANES (United States) and KNHANES (Korea).  No codebook text is
supplied.  Answer from your knowledge of these instruments.

For each item below, report the four fields in the output contract.  Report every
item; do not skip any.  `basis` will be "prior" throughout.
""".strip()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def knhanes_index() -> dict[str, tuple[str, str]]:
    cb = pd.read_csv(KNHANES_CODEBOOK, encoding="utf-8", on_bad_lines="skip",
                     low_memory=False)
    return {str(r["변수명"]).strip().lower(): (str(r["변수설명"]), str(r["내용"]))
            for _, r in cb.iterrows()}


NHANES_VALUE_TABLES = ROOT / "experiments/crta_v3_measurement_layer_v1/nhanes_value_tables_v1.csv"


def nhanes_index() -> dict[str, tuple[str, str]]:
    """Label from the local surface corpus, value text from the CDC snapshot.

    The surface corpus has labels for every variable but no value meanings; the
    governed CDC snapshot has value tables for the nine acquired components.
    """
    df = pd.read_csv(NHANES_SURFACE, low_memory=False)
    labels = {str(r["raw_variable_name"]).strip().upper(): str(r["codebook_label"])
              for _, r in df.iterrows() if pd.notna(r.get("raw_variable_name"))}
    values: dict[str, str] = {}
    if NHANES_VALUE_TABLES.is_file():
        vt = pd.read_csv(NHANES_VALUE_TABLES)
        values = {str(r["variable"]).strip().upper(): str(r["value_table_text"])
                  for _, r in vt.iterrows()}
    return {k: (labels.get(k, ""), values.get(k, "")) for k in set(labels) | set(values)}


def build(arm: str) -> tuple[str, list[dict]]:
    key = pd.read_csv(KEY_CSV)
    kn, nh = knhanes_index(), nhanes_index()
    lines, provenance = [], []
    for _, r in key.iterrows():
        item_id = str(r["item_id"])
        raw = str(r["raw_item_name"])
        cohort = str(r["cohort_name"])
        label, content = "", ""
        if cohort == "KNHANES":
            hit = kn.get(re.sub(r"^(all__|ffq__)", "", raw.strip().lower()))
            if hit:
                label, content = hit
        else:
            label, content = nh.get(raw.strip().upper(), ("", ""))
        has_doc = bool(content.strip()) and content.strip().lower() != "nan"
        provenance.append({"item_id": item_id, "cohort": cohort,
                           "has_codebook_values": has_doc})
        block = [f"- item_id: {item_id}", f"  cohort: {cohort}",
                 f"  variable: {raw}"]
        if label and label.lower() != "nan":
            block.append(f"  label: {label}")
        if arm == "documented" and has_doc:
            block.append(f"  codebook value text: {content}")
        elif arm == "documented":
            block.append("  codebook value text: (none available)")
        lines.append("\n".join(block))

    head = (DOCUMENTED_INSTRUCTIONS if arm == "documented"
            else KNOWLEDGE_ONLY_INSTRUCTIONS)
    return "\n\n".join([head, "ITEMS:\n" + "\n".join(lines), OUTPUT_CONTRACT]), provenance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"key_csv": str(KEY_CSV), "arms": {}}
    for arm in ("documented", "knowledge_only"):
        text, prov = build(arm)
        path = args.out_dir / f"prompt_{arm}.txt"
        path.write_text(text, encoding="utf-8")
        manifest["arms"][arm] = {"prompt_sha256": sha256_text(text),
                                 "chars": len(text)}
        manifest["provenance"] = prov
        print(f"{arm:<16} {len(text):>7} chars  sha {sha256_text(text)[:16]}")
    n_doc = sum(1 for p in manifest["provenance"] if p["has_codebook_values"])
    print(f"items: {len(manifest['provenance'])}  with codebook values: {n_doc}")
    (args.out_dir / "PROMPT_MANIFEST.json").write_text(
        json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
