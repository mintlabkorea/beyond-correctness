#!/usr/bin/env python3
"""Score the isolated hydrology direction extraction against its frozen key.

The key (water balance) was frozen in the prompt manifest BEFORE the
extraction ran.  Driver names are normalised because models echo the
units back into the name field.  A nonzero answer where the key says 0
is reported as an over-commitment, not an error; a sign opposite to a
nonzero key entry is a flip and is the failure that matters.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/crta_v3_camels_sign_extraction_v1"


def normalise(name: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"\(.*?\)", "", str(name))).strip().lower()


def parse(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return None
    try:
        payload = json.loads(match.group(0))
    except ValueError:
        return None
    return {normalise(d["driver"]): d.get("direction") for d in payload["drivers"]}


def main() -> int:
    manifest = json.loads((EXP / "prompts/PROMPT_MANIFEST.json").read_text())
    key = {normalise(k): v for k, v
           in manifest["reference_key_frozen_before_extraction"].items()}
    samples = [s for s in (parse(p) for p in sorted((EXP / "responses").glob("raw_s*.txt")))
               if s is not None]

    rows = []
    for driver, truth in key.items():
        votes = [s.get(driver) for s in samples]
        present = [v for v in votes if v is not None]
        majority = None
        if present:
            majority = max(set(present), key=present.count)
        rows.append({
            "driver": driver, "key": truth, "votes": votes,
            "majority": majority,
            "match": majority == truth,
            "flip": bool(truth != 0 and majority is not None
                         and majority == -truth),
            "over_commitment": bool(truth == 0 and majority not in (None, 0)),
        })

    nonzero = [r for r in rows if r["key"] != 0]
    summary = {
        "n_samples": len(samples),
        "n_drivers": len(rows),
        "agreement_with_key": f"{sum(1 for r in rows if r['match'])}/{len(rows)}",
        "nonzero_key_recovered": f"{sum(1 for r in nonzero if r['match'])}/{len(nonzero)}",
        "sign_flips": sum(1 for r in rows if r["flip"]),
        "over_commitments": sum(1 for r in rows if r["over_commitment"]),
        "llm_majority_table": {r["driver"]: r["majority"] for r in rows},
        "rows": rows,
    }
    (EXP / "SCORE_V1.json").write_text(
        json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for r in rows:
        print(f"  {r['driver']:52s} key {r['key']:+d} votes {r['votes']} "
              f"majority {r['majority']} match {r['match']}")
    print(json.dumps({k: summary[k] for k in
                      ("n_samples", "agreement_with_key", "nonzero_key_recovered",
                       "sign_flips", "over_commitments")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
