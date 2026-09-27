#!/usr/bin/env python3
"""Score extracted harmonization tables against the hand-authored key.

The key is `questionnaire_value_harmonization_rules_v1.csv`, 17 survey items
that the benchmark builder applies to every row before any method sees data.
It was written by a person; this asks whether a model can produce it.

Four fields are scored per item, all exact-match:

    valid_codes                set equality against `valid_codes` ("1|2|3")
    missing_or_sentinel_codes  set equality against `missing_or_sentinel_codes`
    ordinal_direction          string equality
    requires_reverse_coding    boolean equality

Results are split by whether the prompt supplied codebook value text for that
item, so the documentation contribution is separable from the model's prior.
`requires_reverse_coding` is reported separately as well: it is true for exactly
one item in the key, so an all-false answer scores 16/17 on that field and the
aggregate would hide the miss.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd

KEY_CSV = Path(
    "data/benchmark"
    "/relation_sources/common/questionnaire_value_harmonization_rules_v1.csv"
)
FIELDS = ("valid_codes", "missing_or_sentinel_codes", "ordinal_direction",
          "requires_reverse_coding")


def extract_json(raw: str) -> dict | None:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if fence:
        text = fence.group(1)
    start = text.find("{")
    if start < 0:
        return None
    depth, in_str, esc = 0, False, False
    for i, ch in enumerate(text[start:], start):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def codeset(value) -> set[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return set()
    if isinstance(value, (list, tuple)):
        items = value
    else:
        items = re.split(r"[|,\s]+", str(value))
    out = set()
    for item in items:
        s = str(item).strip()
        if not s or s.lower() in ("nan", "none"):
            continue
        out.add(str(int(float(s))) if re.fullmatch(r"-?\d+(\.0+)?", s) else s)
    return out


def as_bool(value) -> bool:
    return str(value).strip().lower() in ("true", "1", "yes")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--responses", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    key = pd.read_csv(KEY_CSV).set_index("item_id")
    prov = {p["item_id"]: p["has_codebook_values"]
            for p in json.loads(args.manifest.read_text())["provenance"]}
    report: dict = {"n_items": len(key), "arms": {}}

    for path in sorted(args.responses.glob("raw_*.txt")):
        arm = path.stem[len("raw_"):]
        obj = extract_json(path.read_text(encoding="utf-8", errors="replace"))
        print("=" * 74)
        print(f"ARM: {arm}")
        print("=" * 74)
        if obj is None:
            print("  strict JSON parse: FAILED")
            report["arms"][arm] = {"parse": "failed"}
            continue
        got = {str(it.get("item_id")): it for it in obj.get("items", [])}
        counts = {f: {"doc": [0, 0], "nodoc": [0, 0]} for f in FIELDS}
        reverse_rows = []
        missing = []
        for item_id, row in key.iterrows():
            g = got.get(item_id)
            bucket = "doc" if prov.get(item_id) else "nodoc"
            if g is None:
                missing.append(item_id)
                for f in FIELDS:
                    counts[f][bucket][1] += 1
                continue
            checks = {
                "valid_codes": codeset(g.get("valid_codes")) == codeset(row["valid_codes"]),
                "missing_or_sentinel_codes":
                    codeset(g.get("missing_or_sentinel_codes")) == codeset(row["missing_or_sentinel_codes"]),
                "ordinal_direction":
                    str(g.get("ordinal_direction", "")).strip() == str(row["ordinal_direction"]).strip(),
                "requires_reverse_coding":
                    as_bool(g.get("requires_reverse_coding")) == as_bool(row["requires_reverse_coding"]),
            }
            for f, ok in checks.items():
                counts[f][bucket][0] += int(ok)
                counts[f][bucket][1] += 1
            if as_bool(row["requires_reverse_coding"]) or as_bool(g.get("requires_reverse_coding")):
                reverse_rows.append((item_id, as_bool(row["requires_reverse_coding"]),
                                     as_bool(g.get("requires_reverse_coding"))))
        print(f"  items returned: {len(got)}/{len(key)}"
              + (f"   MISSING: {missing}" if missing else ""))
        print(f"  {'field':<28}{'with codebook':>16}{'without':>12}{'overall':>12}")
        arm_report = {"parse": "ok", "returned": len(got), "fields": {}}
        for f in FIELDS:
            d, n = counts[f]["doc"], counts[f]["nodoc"]
            tot = (d[0] + n[0], d[1] + n[1])
            print(f"  {f:<28}{d[0]:>7}/{d[1]:<8}{n[0]:>5}/{n[1]:<6}"
                  f"{tot[0]:>6}/{tot[1]:<5} ({tot[0]/max(tot[1],1):.2f})")
            arm_report["fields"][f] = {"doc": d, "nodoc": n, "total": list(tot)}
        print("  reverse-coding items (key True or predicted True):")
        for item_id, truth, pred in reverse_rows:
            flag = "OK " if truth == pred else "MISS"
            print(f"    {flag} {item_id:<26} key={truth} predicted={pred}")
        arm_report["reverse_rows"] = reverse_rows
        report["arms"][arm] = arm_report
        print()

    if args.out:
        args.out.write_text(json.dumps(report, indent=1, sort_keys=True, default=str)
                            + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
