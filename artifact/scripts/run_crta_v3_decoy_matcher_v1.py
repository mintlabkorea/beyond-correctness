#!/usr/bin/env python3
"""Compiler-specificity negative control, stage A: schema-matcher
abstention when a source variable has NO counterpart.

Reuses the frozen open-world matcher's scoring (name / name+unit /
name+unit+codebook) over the 1,315-column KNHANES universe.  For each of
the nine member queries the counterpart CONSTRUCT is removed from the
candidate pool (every KNHANES column sharing the gold's stem, e.g.
`he_sbp` removes he_sbp1/he_sbp2/...), making the query an orphan.
Per-query top-1 scores and margins are recorded for gold-present and
orphan pools; abstention rules (absolute score threshold, top-1/top-2
margin) are swept and the forced (no-abstention) false bindings are
frozen for stage B.  Deterministic; no fitting.
Prereg: iclr_latex_v3/DECOY_COMPILER_SPECIFICITY_PREREGISTRATION_V1.md.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
MATCHER = ROOT / "scripts/run_crta_v3_open_world_schema_matcher_v1.py"
PREREG = ROOT / "iclr_latex_v3/DECOY_COMPILER_SPECIFICITY_PREREGISTRATION_V1.md"
DEFAULT_OUT = ROOT / "experiments/crta_v3_decoy_compiler_specificity_v1"
THRESHOLDS = tuple(round(x, 3) for x in np.arange(0.0, 1.0001, 0.025))
MARGINS = tuple(round(x, 3) for x in np.arange(0.0, 0.5001, 0.025))
RECALL_TARGET = 8  # of 9 gold-present queries


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def construct_stem(gold: str) -> str:
    """`ALL__he_sbp1` -> `he_sbp`; `ALL__he_hba1c` -> `he_hba1c` (trailing
    digits are stripped only when the name ends in digits after a letter
    run that is not itself a chemistry token)."""
    body = gold.split("__", 1)[1] if "__" in gold else gold
    stem = re.sub(r"\d+$", "", body)
    return stem


def orphan_pool(candidates: list[str], gold: str) -> tuple[list[str], list[str]]:
    stem = construct_stem(gold)
    removed = [c for c in candidates
               if (c.split("__", 1)[1] if "__" in c else c).startswith(stem)]
    if gold not in removed:
        raise AssertionError(f"stem rule failed to remove gold {gold}")
    kept = [c for c in candidates if c not in set(removed)]
    return kept, removed


def top_two(scores: np.ndarray, names: list[str]) -> dict:
    order = np.argsort(-scores)
    best, second = int(order[0]), int(order[1])
    return {"top1": names[best], "top1_score": float(scores[best]),
            "top2": names[second], "top2_score": float(scores[second]),
            "margin": float(scores[best] - scores[second])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    mt = _load("owm_frozen", MATCHER)

    metadata = pd.read_csv(mt.META)
    metadata_index = metadata.set_index(["cohort_name", "raw_var_name"])
    candidates = list(pq.read_schema(mt.KN_PARQUET).names)
    if len(candidates) != mt.POOL_SIZES[-1]:
        raise RuntimeError("candidate universe changed")
    source = [slot[1] for slot in mt.SLOTS]
    gold = [slot[2] for slot in mt.SLOTS]
    slots = [slot[0] for slot in mt.SLOTS]

    # frozen scoring, byte-for-byte the matcher's regimes
    source_names = [mt.norm_id(n) for n in source]
    target_names = [mt.norm_id(n) for n in candidates]
    name_score = mt.text_score(source_names, target_names, "char", (2, 5))
    source_units = [mt.unit(metadata_index, "NHANES", n) for n in source]
    target_units = [mt.unit(metadata_index, "KNHANES", n) for n in candidates]
    unit_score = np.asarray([[float(bool(l) and bool(r) and l == r)
                              for r in target_units] for l in source_units])
    source_docs = [mt.document(metadata_index, "NHANES", n) for n in source]
    target_docs = [mt.document(metadata_index, "KNHANES", n) for n in candidates]
    word_score = mt.text_score(source_docs, target_docs, "word", (1, 2))
    char_score = mt.text_score(source_docs, target_docs, "char_wb", (3, 5))
    regimes = {
        "name_only": name_score,
        "name_plus_unit": 0.80 * name_score + 0.20 * unit_score,
        "name_unit_codebook": (0.35 * name_score + 0.15 * unit_score
                               + 0.25 * word_score + 0.25 * char_score),
    }
    index_of = {c: i for i, c in enumerate(candidates)}

    per_query: dict = {}
    for regime, score in regimes.items():
        per_query[regime] = {}
        for qi, (slot, src, gd) in enumerate(zip(slots, source, gold)):
            full = top_two(score[qi], candidates)
            kept, removed = orphan_pool(candidates, gd)
            kept_idx = np.asarray([index_of[c] for c in kept])
            orphan = top_two(score[qi, kept_idx], kept)
            per_query[regime][slot] = {
                "source": src, "gold": gd, "removed_construct": removed,
                "gold_present": dict(full, gold_is_top1=bool(full["top1"] == gd)),
                "orphan": orphan,
            }

    sweeps: dict = {}
    for regime in regimes:
        rows = per_query[regime]
        thr = []
        for tau in THRESHOLDS:
            recall = sum(1 for r in rows.values()
                         if r["gold_present"]["gold_is_top1"]
                         and r["gold_present"]["top1_score"] >= tau)
            fbr = sum(1 for r in rows.values() if r["orphan"]["top1_score"] >= tau)
            thr.append({"tau": tau, "recall": recall, "false_bindings": fbr})
        mar = []
        for delta in MARGINS:
            recall = sum(1 for r in rows.values()
                         if r["gold_present"]["gold_is_top1"]
                         and r["gold_present"]["margin"] >= delta)
            fbr = sum(1 for r in rows.values() if r["orphan"]["margin"] >= delta)
            mar.append({"delta": delta, "recall": recall, "false_bindings": fbr})
        # registered operating point: largest tau (resp. delta) keeping
        # gold-present recall >= RECALL_TARGET; FBR read there.
        ok_t = [t for t in thr if t["recall"] >= RECALL_TARGET]
        ok_m = [m for m in mar if m["recall"] >= RECALL_TARGET]
        sweeps[regime] = {
            "threshold_curve": thr, "margin_curve": mar,
            "operating_threshold": (max(ok_t, key=lambda t: t["tau"])
                                    if ok_t else None),
            "operating_margin": (max(ok_m, key=lambda m: m["delta"])
                                 if ok_m else None),
            "forced_false_bindings": {s: r["orphan"]["top1"]
                                      for s, r in rows.items()},
            "gold_present_accuracy": sum(
                1 for r in rows.values() if r["gold_present"]["gold_is_top1"]),
        }

    payload = {
        "provenance": {"runner_sha256": sha256_file(Path(__file__)),
                       "matcher_sha256": sha256_file(MATCHER),
                       "prereg_sha256": sha256_file(PREREG),
                       "metadata_sha256": sha256_file(mt.META),
                       "knhanes_sha256": sha256_file(mt.KN_PARQUET)},
        "n_candidates": len(candidates),
        "recall_target": RECALL_TARGET,
        "per_query": per_query,
        "sweeps": sweeps,
    }
    args.out_root.mkdir(parents=True, exist_ok=True)
    (args.out_root / "STAGE_A_MATCHER_V1.json").write_text(
        json.dumps(payload, indent=1, sort_keys=True))
    for regime, s in sweeps.items():
        print(regime, "gold acc", s["gold_present_accuracy"], "| op tau",
              s["operating_threshold"], "| op margin", s["operating_margin"])
        print("   forced false bindings:", s["forced_false_bindings"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
