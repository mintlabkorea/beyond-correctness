#!/usr/bin/env python3
"""Run distractor-open schema-matching curves over the full KNHANES schema."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.optimize import linear_sum_assignment
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "iclr_latex_v3/OPEN_WORLD_SCHEMA_MATCHER_PREREGISTRATION_V1.md"
DEFAULT_OUT = ROOT / "experiments/crta_v3_open_world_schema_matcher_v1"
META = Path(
    "data/benchmark_project/tasks/standard_benchmark/"
    "current/relation_sources/common/variable_metadata_table_draft_v1.csv"
)
KN_PARQUET = Path(
    "data/nhanes_knhanes/datasets/knhanes/processed/L3/"
    "L3_9815_pr90_with_mpls.parquet"
)
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
POOL_SIZES = (9, 17, 33, 65, 129, 257, 513, 1315)
N_DRAWS = 50
RNG_NS = "open_world_schema_matcher_v1"
DOCUMENT_FIELDS = (
    "display_name", "family", "subfamily", "domain", "unit",
    "specimen_system", "visit_module", "codebook_text",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def stable_seed(*parts: Any) -> int:
    digest = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
    return int.from_bytes(digest[:8], "little") % (2**32 - 1)


def norm_id(value: str) -> str:
    return " ".join(re.findall(
        r"[a-z]+|\d+", value.lower().replace("all__", "")
    ))


def norm_unit(value: Any) -> str:
    if pd.isna(value):
        return ""
    return " ".join(re.findall(r"[a-z]+|\d+", str(value).lower()))


def text_score(left: list[str], right: list[str], analyzer: str,
               ngram_range: tuple[int, int]) -> np.ndarray:
    vectorizer = TfidfVectorizer(
        analyzer=analyzer,
        ngram_range=ngram_range,
        lowercase=True,
        strip_accents="unicode",
    )
    matrix = vectorizer.fit_transform(left + right)
    return cosine_similarity(matrix[:len(left)], matrix[len(left):])


def assignment(score: np.ndarray) -> tuple[np.ndarray, float]:
    rows, columns = linear_sum_assignment(-score)
    if len(rows) != score.shape[0]:
        raise RuntimeError("rectangular assignment did not cover every source")
    prediction = np.empty(score.shape[0], dtype=int)
    prediction[rows] = columns
    return prediction, float(score[rows, columns].sum())


def document(index: pd.DataFrame, cohort: str, variable: str) -> str:
    key = (cohort, variable)
    if key not in index.index:
        return ""
    row = index.loc[key]
    return " ".join(
        str(row[field]) for field in DOCUMENT_FIELDS
        if field in row.index and pd.notna(row[field])
    )


def unit(index: pd.DataFrame, cohort: str, variable: str) -> str:
    key = (cohort, variable)
    if key not in index.index:
        return ""
    return norm_unit(index.loc[key, "unit"])


def empirical_summary(values: list[float]) -> dict[str, Any]:
    array = np.asarray(values, dtype=float)
    return {
        "mean_accuracy": float(array.mean()),
        "empirical_q025_q975": [
            float(np.quantile(array, 0.025)),
            float(np.quantile(array, 0.975)),
        ],
        "min_accuracy": float(array.min()),
        "max_accuracy": float(array.max()),
        "draw_accuracies": array.tolist(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    metadata = pd.read_csv(META)
    if metadata.duplicated(["cohort_name", "raw_var_name"]).any():
        raise RuntimeError("metadata contains duplicate cohort/variable keys")
    metadata_index = metadata.set_index(["cohort_name", "raw_var_name"])
    candidates = list(pq.read_schema(KN_PARQUET).names)
    if len(candidates) != len(set(candidates)):
        raise RuntimeError("KNHANES candidate columns are not unique")
    if len(candidates) != POOL_SIZES[-1]:
        raise RuntimeError(
            f"frozen universe expected {POOL_SIZES[-1]} columns, got {len(candidates)}"
        )
    source = [slot[1] for slot in SLOTS]
    gold = [slot[2] for slot in SLOTS]
    if not set(gold).issubset(candidates):
        raise RuntimeError("gold target columns are missing from candidate universe")
    if any(("NHANES", name) not in metadata_index.index for name in source):
        raise RuntimeError("source metadata is incomplete")
    if any(("KNHANES", name) not in metadata_index.index for name in gold):
        raise RuntimeError("gold target metadata is incomplete")

    provenance = {
        "runner_sha256": sha256_file(Path(__file__)),
        "prereg_sha256": sha256_file(PREREG),
        "metadata_sha256": sha256_file(META),
        "knhanes_sha256": sha256_file(KN_PARQUET),
    }
    coverage = {
        "source_metadata_rows": sum(
            ("NHANES", name) in metadata_index.index for name in source),
        "target_candidates_with_metadata": sum(
            ("KNHANES", name) in metadata_index.index for name in candidates),
        "target_candidate_count": len(candidates),
        "gold_targets_with_metadata": sum(
            ("KNHANES", name) in metadata_index.index for name in gold),
    }
    print(json.dumps({"coverage": coverage, "provenance": provenance}, indent=1),
          flush=True)
    if args.validate_only:
        return 0

    source_names = [norm_id(name) for name in source]
    target_names = [norm_id(name) for name in candidates]
    name_score = text_score(source_names, target_names, "char", (2, 5))
    source_units = [unit(metadata_index, "NHANES", name) for name in source]
    target_units = [unit(metadata_index, "KNHANES", name) for name in candidates]
    unit_score = np.asarray([
        [float(bool(left) and bool(right) and left == right)
         for right in target_units]
        for left in source_units
    ])
    source_docs = [document(metadata_index, "NHANES", name) for name in source]
    target_docs = [document(metadata_index, "KNHANES", name)
                   for name in candidates]
    word_score = text_score(source_docs, target_docs, "word", (1, 2))
    char_score = text_score(source_docs, target_docs, "char_wb", (3, 5))
    regimes = {
        "name_only": name_score,
        "name_plus_unit": 0.80 * name_score + 0.20 * unit_score,
        "name_unit_codebook": (
            0.35 * name_score + 0.15 * unit_score
            + 0.25 * word_score + 0.25 * char_score
        ),
    }
    if any(score.min() < -1e-12 or score.max() > 1 + 1e-12
           for score in regimes.values()):
        raise AssertionError("score escaped the frozen [0,1] range")

    global_index = {name: index for index, name in enumerate(candidates)}
    gold_map = dict(zip(source, gold))
    distractors = np.asarray(sorted(set(candidates) - set(gold)), dtype=object)
    draw_values = {
        regime: {str(size): [] for size in POOL_SIZES}
        for regime in regimes
    }
    full_details: dict[str, Any] = {}
    pool_digests: dict[str, dict[str, str]] = {}
    for draw in range(N_DRAWS):
        rng = np.random.default_rng(stable_seed(RNG_NS, draw))
        order = distractors[rng.permutation(len(distractors))]
        pool_digests[str(draw)] = {}
        for size in POOL_SIZES:
            chosen = list(gold) + list(order[:size - len(gold)])
            chosen = sorted(chosen)
            pool_digests[str(draw)][str(size)] = hashlib.sha256(
                "\n".join(chosen).encode()).hexdigest()
            columns = np.asarray([global_index[name] for name in chosen], dtype=int)
            for regime, full_score in regimes.items():
                prediction, objective = assignment(full_score[:, columns])
                mapped = {
                    source[row]: chosen[int(prediction[row])]
                    for row in range(len(source))
                }
                accuracy = sum(
                    mapped[name] == gold_map[name] for name in source
                ) / len(source)
                draw_values[regime][str(size)].append(float(accuracy))
                if size == POOL_SIZES[-1] and draw == 0:
                    full_details[regime] = {
                        "accuracy": float(accuracy),
                        "hits": int(round(accuracy * len(source))),
                        "objective": objective,
                        "mapping": mapped,
                    }

    curves = {
        regime: {
            size: empirical_summary(values)
            for size, values in by_size.items()
        }
        for regime, by_size in draw_values.items()
    }
    closed_perfect = all(
        curves[regime][str(POOL_SIZES[0])]["mean_accuracy"] == 1.0
        for regime in regimes
    )
    full_accuracy = {
        regime: full_details[regime]["accuracy"] for regime in regimes
    }
    payload = {
        "task": "distractor_open_9_by_1315_schema_matching",
        "scope": (
            "nine known source queries; exactly one gold each; no abstention; "
            "not unknown-cardinality ontology discovery"
        ),
        "gold_used_only_for_candidate_inclusion_and_evaluation": True,
        "canonical_var_name_excluded_from_scores": True,
        "pool_sizes": list(POOL_SIZES),
        "n_distractor_draws": N_DRAWS,
        "metadata_coverage": coverage,
        "regime_weights": {
            "name_only": {"name": 1.0},
            "name_plus_unit": {"name": 0.80, "unit": 0.20},
            "name_unit_codebook": {
                "name": 0.35, "unit": 0.15,
                "codebook_word": 0.25, "codebook_char": 0.25,
            },
        },
        "curves": curves,
        "full_universe": full_details,
        "verdicts": {
            "OWM_P1_closed_set_perfect": closed_perfect,
            "OWM_P2_distractors_break_triviality": bool(
                any(value < 8 / 9 for value in full_accuracy.values())
            ),
            "OWM_P3_rich_metadata_rescues": bool(
                full_accuracy["name_unit_codebook"] >= 8 / 9
                and (full_accuracy["name_unit_codebook"]
                     - full_accuracy["name_only"]) >= 2 / 9
            ),
        },
        "pool_sha256_by_draw_and_size": pool_digests,
        "provenance": provenance,
    }
    args.out_root.mkdir(parents=True, exist_ok=True)
    out = args.out_root / "SUMMARY_V1.json"
    out.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps({
        "written": str(out),
        "full_accuracy": full_accuracy,
        "verdicts": payload["verdicts"],
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
