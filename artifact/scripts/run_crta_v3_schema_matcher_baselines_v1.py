#!/usr/bin/env python3
"""Closed-set strong schema-matching baselines for the nine member slots."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "iclr_latex_v3/SCHEMA_MATCHER_BASELINES_PREREGISTRATION_V1.md"
DEFAULT_OUT = ROOT / "experiments/crta_v3_schema_matcher_baselines_v1"
META = Path("data/benchmark/relation_sources/common/variable_metadata_table_draft_v1.csv")
NH_PARQUET = Path("data/external1/medical_fm/datasets/NHANES_levels/L3_1714_ge9.parquet")
KN_PARQUET = Path("data/nhanes_knhanes/datasets/knhanes/processed/L3/L3_9815_pr90_with_mpls.parquet")
SLOTS = (
    ("height_cm", "BMXHT", "ALL__he_ht"),
    ("weight_kg", "BMXWT", "ALL__he_wt"),
    ("waist_cm", "BMXWAIST", "ALL__he_wc"),
    ("sbp", "BPXSY1", "ALL__he_sbp1"),
    ("dbp", "BPXDI1", "ALL__he_dbp1"),
    ("glucose", "LBXGLU", "ALL__he_glu"),
    ("hba1c", "LBXGH", "ALL__he_hba1c"),
    ("total_cholesterol", "LBXTC", "ALL__he_chol"),
    ("triglycerides", "LBXSTR", "ALL__he_tg"),
)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(8 * 1024 * 1024): h.update(chunk)
    return h.hexdigest()


def norm_id(x: str) -> str:
    return " ".join(re.findall(r"[a-z]+|\d+", x.lower().replace("all__", "")))


def assignment(score: np.ndarray) -> tuple[np.ndarray, float]:
    rows, cols = linear_sum_assignment(-score)
    pred = np.empty(len(rows), dtype=int)
    pred[rows] = cols
    return pred, float(score[rows, cols].sum())


def text_score(left: list[str], right: list[str], analyzer: str,
               ngram_range: tuple[int, int]) -> np.ndarray:
    vec = TfidfVectorizer(analyzer=analyzer, ngram_range=ngram_range,
                          lowercase=True, strip_accents="unicode")
    x = vec.fit_transform(left + right)
    return cosine_similarity(x[:len(left)], x[len(left):])


def profile(path: Path, columns: list[str]) -> np.ndarray:
    d = pd.read_parquet(path, columns=columns)
    out = []
    for c in columns:
        x = pd.to_numeric(d[c], errors="coerce").to_numpy(float)
        x = x[np.isfinite(x)]
        if len(x) == 0:
            raise RuntimeError(f"empty profile: {c}")
        lo, hi = np.quantile(x, [0.001, 0.999])
        x = x[(x >= lo) & (x <= hi)]
        q = np.quantile(x, [0.05, 0.25, 0.5, 0.75, 0.95])
        out.append(np.r_[q, np.log(max(q[3] - q[1], 1e-6))])
    return np.asarray(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    meta = pd.read_csv(META)
    nh = [x[1] for x in SLOTS]
    kn = [x[2] for x in SLOTS]
    selected = meta[meta.raw_var_name.isin(nh + kn)].set_index("raw_var_name")
    if len(selected) != 18:
        raise RuntimeError("metadata panel is incomplete")
    raw_score = text_score([norm_id(x) for x in nh], [norm_id(x) for x in kn],
                           "char", (2, 5))
    fields = ["display_name", "family", "subfamily", "domain",
              "unit", "specimen_system", "visit_module", "codebook_text"]
    def document(c: str, use_metadata: bool) -> str:
        if not use_metadata:
            return norm_id(c)
        return " ".join(str(selected.loc[c, f]) for f in fields
                        if pd.notna(selected.loc[c, f]))
    metadata_score = text_score([document(x, True) for x in nh],
                                [document(x, True) for x in kn],
                                "word", (1, 2))
    char_metadata_score = text_score([document(x, True) for x in nh],
                                     [document(x, True) for x in kn],
                                     "char_wb", (3, 5))
    pn, pk = profile(NH_PARQUET, nh), profile(KN_PARQUET, kn)
    # Pairwise robust relative difference. Unit-incompatible pairs receive
    # a fixed penalty; no canonical names or gold pair ids enter the score.
    scale = np.maximum(np.abs(pn[:, None, :]) + np.abs(pk[None, :, :]), 1.0)
    dist = np.mean(np.abs(pn[:, None, :] - pk[None, :, :]) / scale, axis=2)
    units_nh = [str(selected.loc[x, "unit"]).lower() for x in nh]
    units_kn = [str(selected.loc[x, "unit"]).lower() for x in kn]
    unit_ok = np.asarray([[a == b for b in units_kn] for a in units_nh], float)
    profile_score = -dist + unit_ok
    hybrid = 0.55 * metadata_score + 0.20 * char_metadata_score + 0.25 * (
        (profile_score - profile_score.min()) /
        max(profile_score.max() - profile_score.min(), 1e-12))
    methods = {"raw_id_char_tfidf": raw_score,
               "codebook_word_tfidf": metadata_score,
               "codebook_char_tfidf": char_metadata_score,
               "unit_distribution_profile": profile_score,
               "hybrid_metadata_profile": hybrid}
    results = {}
    for name, score in methods.items():
        pred, objective = assignment(score)
        mapping = {nh[i]: kn[int(pred[i])] for i in range(9)}
        hits = [int(pred[i] == i) for i in range(9)]
        results[name] = {"accuracy": float(np.mean(hits)), "hits": sum(hits),
                         "objective": objective, "mapping": mapping,
                         "perfect_mapping_implies_downstream_arm": (
                             "a11_stage_columns" if all(hits) else None)}
    payload = {
        "task": "closed_set_bipartite_9x9_member_schema_matching",
        "gold_used_only_for_evaluation": True,
        "canonical_var_name_excluded_from_matcher_inputs": True,
        "slots": [x[0] for x in SLOTS], "results": results,
        "strong_baseline_pass": bool(any(
            r["accuracy"] >= 8 / 9 for r in results.values()
            if r is not results["raw_id_char_tfidf"])),
        "provenance": {"runner_sha256": sha(Path(__file__)),
                       "prereg_sha256": sha(PREREG),
                       "metadata_sha256": sha(META),
                       "nhanes_sha256": sha(NH_PARQUET),
                       "knhanes_sha256": sha(KN_PARQUET)},
    }
    args.out_root.mkdir(parents=True, exist_ok=True)
    out = args.out_root / "SUMMARY_V1.json"
    out.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"written": str(out), "accuracies": {
        k: v["accuracy"] for k, v in results.items()}}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
