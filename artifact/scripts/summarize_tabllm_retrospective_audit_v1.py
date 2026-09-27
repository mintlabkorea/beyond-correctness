#!/usr/bin/env python3
"""Summarize the frozen TabLLM four-arm audit with paired example inference."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "iclr_latex_v3/TABLLM_RETROSPECTIVE_AUDIT_FREEZE_V1.md"
DATASETS = (
    "bank", "blood", "calhousing", "car", "creditg",
    "diabetes", "heart", "income", "jungle",
)
ARMS = (
    "list_template", "list_permuted_names",
    "list_only_values", "list_stable_anonymous",
)
SEEDS = (42, 1024, 0, 1, 32)
REPS = 10_000
BOOTSTRAP_SEED = 20260827
PUBLISHED = {
    "bank": (0.60, 0.64, 0.56),
    "blood": (0.56, 0.52, 0.45),
    "calhousing": (0.61, 0.54, 0.58),
    "car": (0.79, 0.39, 0.48),
    "creditg": (0.53, 0.44, 0.66),
    "diabetes": (0.64, 0.56, 0.55),
    "heart": (0.52, 0.57, 0.40),
    "income": (0.79, 0.65, 0.73),
    "jungle": (0.63, 0.40, 0.58),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load_predictions(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            rows.append(json.loads(line))
    rows.sort(key=lambda row: int(row["row_id"]))
    return (
        np.asarray([int(row["row_id"]) for row in rows], dtype=np.int64),
        np.asarray([int(row["label"]) for row in rows], dtype=np.int64),
        np.asarray([row["class_probabilities"] for row in rows], dtype=np.float64),
    )


def binary_auc_and_influence(labels: np.ndarray, scores: np.ndarray) -> tuple[float, np.ndarray]:
    positive = labels.astype(bool)
    pos_scores = scores[positive]
    neg_scores = scores[~positive]
    if not len(pos_scores) or not len(neg_scores):
        raise ValueError("AUROC requires both classes")
    sorted_neg = np.sort(neg_scores)
    less_neg = np.searchsorted(sorted_neg, pos_scores, side="left")
    equal_neg = np.searchsorted(sorted_neg, pos_scores, side="right") - less_neg
    v10 = (less_neg + 0.5 * equal_neg) / len(neg_scores)
    theta = float(v10.mean())
    sorted_pos = np.sort(pos_scores)
    less_equal_pos = np.searchsorted(sorted_pos, neg_scores, side="right")
    less_pos = np.searchsorted(sorted_pos, neg_scores, side="left")
    equal_pos = less_equal_pos - less_pos
    v01 = (len(pos_scores) - less_equal_pos + 0.5 * equal_pos) / len(pos_scores)
    influence = np.empty(len(labels), dtype=np.float64)
    influence[positive] = (v10 - theta) / len(pos_scores)
    influence[~positive] = (v01 - theta) / len(neg_scores)
    return theta, influence


def macro_auc_and_influence(labels: np.ndarray, probabilities: np.ndarray) -> tuple[float, np.ndarray]:
    class_count = probabilities.shape[1]
    if class_count == 2:
        # Match the released reader and runner exactly: binary AUROC uses the
        # probability of class 1, rather than averaging two nominally
        # complementary one-vs-rest curves (float32 ties can differ slightly).
        return binary_auc_and_influence(labels == 1, probabilities[:, 1])
    estimates = []
    influence = np.zeros(len(labels), dtype=np.float64)
    for class_id in range(class_count):
        estimate, class_influence = binary_auc_and_influence(
            labels == class_id, probabilities[:, class_id]
        )
        estimates.append(estimate)
        influence += class_influence / class_count
    return float(np.mean(estimates)), influence


def effect_matrix(arm_values: np.ndarray) -> np.ndarray:
    supplied, wrong, published_ref, anonymous_ref = arm_values.T
    return np.column_stack([
        supplied - wrong,
        supplied - anonymous_ref,
        anonymous_ref - wrong,
        supplied - published_ref,
        published_ref - wrong,
    ])


def interval(values: np.ndarray) -> list[float]:
    return [float(x) for x in np.quantile(values, [0.025, 0.975])]


def psd_covariance(matrix: np.ndarray) -> np.ndarray:
    matrix = (matrix + matrix.T) / 2
    values, vectors = np.linalg.eigh(matrix)
    values = np.clip(values, 0.0, None)
    return (vectors * values) @ vectors.T


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path,
        default=ROOT / "experiments/tabllm_retrospective_audit_v1",
    )
    parser.add_argument("--split-manifest", type=Path, required=True)
    parser.add_argument(
        "--out", type=Path,
        default=ROOT / "experiments/tabllm_retrospective_audit_v1/SUMMARY_V1.json",
    )
    args = parser.parse_args()
    manifest = json.loads(args.split_manifest.read_text(encoding="utf-8"))
    rng = np.random.default_rng(BOOTSTRAP_SEED)

    dataset_points = []
    dataset_covariances = []
    dataset_summaries: dict[str, Any] = {}
    input_hashes: dict[str, str] = {}
    max_metric_recompute_error = 0.0
    max_identity_error = 0.0
    published_cell_errors = []

    for dataset in DATASETS:
        arm_data = {}
        metric_data = {}
        for arm in ARMS:
            cell = args.root / arm / dataset
            metrics_path = cell / "metrics.json"
            predictions_path = cell / "predictions.jsonl.gz"
            if not metrics_path.is_file() or not predictions_path.is_file():
                raise FileNotFoundError(f"missing completed cell: {cell}")
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            if metrics.get("analysis_status") != "retrospective_published_style_reproduction":
                raise RuntimeError(f"inadmissible analysis status in {metrics_path}")
            arm_data[arm] = load_predictions(predictions_path)
            metric_data[arm] = metrics
            input_hashes[str(metrics_path.relative_to(args.root))] = sha256_file(metrics_path)
            input_hashes[str(predictions_path.relative_to(args.root))] = sha256_file(predictions_path)

        canonical_ids, canonical_labels, _ = arm_data[ARMS[0]]
        for arm in ARMS[1:]:
            ids, labels, _ = arm_data[arm]
            if not np.array_equal(ids, canonical_ids) or not np.array_equal(labels, canonical_labels):
                raise RuntimeError(f"unpaired predictions for {dataset}/{arm}")
        row_lookup = {int(row_id): index for index, row_id in enumerate(canonical_ids)}
        influence_by_row = np.zeros((len(canonical_ids), len(ARMS)), dtype=np.float64)
        seed_estimates = np.zeros((len(SEEDS), len(ARMS)), dtype=np.float64)
        for seed_index, seed in enumerate(SEEDS):
            members = manifest["datasets"][dataset]["test_row_ids"][str(seed)]
            positions = np.asarray([row_lookup[int(row_id)] for row_id in members], dtype=int)
            labels = canonical_labels[positions]
            for arm_index, arm in enumerate(ARMS):
                probabilities = arm_data[arm][2][positions]
                estimate, influence = macro_auc_and_influence(labels, probabilities)
                seed_estimates[seed_index, arm_index] = estimate
                influence_by_row[positions, arm_index] += influence / len(SEEDS)
                reported = float(metric_data[arm]["metrics"][str(seed)]["auc"])
                max_metric_recompute_error = max(
                    max_metric_recompute_error, abs(estimate - reported)
                )

        point = seed_estimates.mean(axis=0)
        covariance = psd_covariance(influence_by_row.T @ influence_by_row)
        arm_draws = rng.multivariate_normal(point, covariance, size=REPS)
        effect_point = effect_matrix(point[None, :])[0]
        effect_draws = effect_matrix(arm_draws)
        max_identity_error = max(
            max_identity_error,
            abs(effect_point[0] - effect_point[1] - effect_point[2]),
            abs(effect_point[0] - effect_point[3] - effect_point[4]),
        )
        published_values = np.asarray(PUBLISHED[dataset])
        reproduced_published_arms = point[[0, 1, 2]]
        published_cell_errors.extend(
            np.abs(reproduced_published_arms - published_values).tolist()
        )
        names = (
            "content", "utility_anonymous", "wrong_harm_anonymous",
            "utility_published_reference", "wrong_harm_published_reference",
        )
        effects = {
            name: {"estimate": float(effect_point[i]), "ci95": interval(effect_draws[:, i])}
            for i, name in enumerate(names)
        }
        dataset_summaries[dataset] = {
            "arm_mean_auc": {arm: float(point[i]) for i, arm in enumerate(ARMS)},
            "effects": effects,
            "harm_share_anonymous": (
                float(effect_point[2] / effect_point[0]) if effect_point[0] > 0 else None
            ),
            "published_printed_auc": {
                arm: float(published_values[i]) for i, arm in enumerate(ARMS[:3])
            },
            "published_arm_absolute_errors": {
                arm: float(abs(reproduced_published_arms[i] - published_values[i]))
                for i, arm in enumerate(ARMS[:3])
            },
        }
        dataset_points.append(point)
        dataset_covariances.append(covariance)

    dataset_points_array = np.asarray(dataset_points)
    macro_arm_point = dataset_points_array.mean(axis=0)
    selected = rng.integers(0, len(DATASETS), size=(REPS, len(DATASETS)))
    macro_arm_draws = np.zeros((REPS, len(ARMS)), dtype=np.float64)
    for position in range(len(DATASETS)):
        selected_here = selected[:, position]
        for dataset_index in range(len(DATASETS)):
            mask = selected_here == dataset_index
            count = int(mask.sum())
            if count:
                macro_arm_draws[mask] += rng.multivariate_normal(
                    dataset_points_array[dataset_index],
                    dataset_covariances[dataset_index],
                    size=count,
                )
    macro_arm_draws /= len(DATASETS)
    macro_effect_point = effect_matrix(macro_arm_point[None, :])[0]
    macro_effect_draws = effect_matrix(macro_arm_draws)
    effect_names = (
        "content", "utility_anonymous", "wrong_harm_anonymous",
        "utility_published_reference", "wrong_harm_published_reference",
    )
    macro_effects = {
        name: {
            "estimate": float(macro_effect_point[index]),
            "ci95": interval(macro_effect_draws[:, index]),
        }
        for index, name in enumerate(effect_names)
    }
    positive_content = [
        dataset for dataset in DATASETS
        if dataset_summaries[dataset]["effects"]["content"]["estimate"] > 0
    ]
    harm_dominant = [
        dataset for dataset in positive_content
        if dataset_summaries[dataset]["effects"]["wrong_harm_anonymous"]["estimate"]
        > dataset_summaries[dataset]["effects"]["utility_anonymous"]["estimate"]
    ]
    utility_sign_reversals = [
        dataset for dataset in positive_content
        if dataset_summaries[dataset]["effects"]["utility_anonymous"]["estimate"] < 0
    ]
    harm_shares = [
        dataset_summaries[dataset]["harm_share_anonymous"]
        for dataset in positive_content
    ]
    payload = {
        "analysis_status": "frozen_retrospective_published_style_reproduction",
        "inference": {
            "method": (
                "paired example-level Gaussian multiplier bootstrap using "
                "AUROC influence functions; shared example weights across "
                "overlapping fixed test splits; macro resamples datasets then examples"
            ),
            "reps": REPS,
            "seed": BOOTSTRAP_SEED,
        },
        "primary_reference": "list_stable_anonymous",
        "macro": {
            "arm_mean_auc": {
                arm: float(macro_arm_point[index]) for index, arm in enumerate(ARMS)
            },
            "effects": macro_effects,
        },
        "heterogeneity": {
            "positive_content_count": len(positive_content),
            "positive_content_datasets": positive_content,
            "harm_dominant_count": len(harm_dominant),
            "harm_dominant_datasets": harm_dominant,
            "utility_sign_reversal_count": len(utility_sign_reversals),
            "utility_sign_reversal_datasets": utility_sign_reversals,
            "harm_share_median": float(np.median(harm_shares)) if harm_shares else None,
            "harm_share_range": (
                [float(min(harm_shares)), float(max(harm_shares))]
                if harm_shares else None
            ),
        },
        "datasets": dataset_summaries,
        "reproduction_diagnostic": {
            "published_cells_within_0_015": int(
                np.sum(np.asarray(published_cell_errors) <= 0.015)
            ),
            "published_cell_count": len(published_cell_errors),
            "maximum_absolute_error_from_printed_value": float(max(published_cell_errors)),
            "maximum_metric_recompute_error": max_metric_recompute_error,
            "maximum_identity_error": max_identity_error,
        },
        "provenance": {
            "protocol_sha256": sha256_file(PROTOCOL),
            "summarizer_sha256": sha256_file(Path(__file__)),
            "split_manifest_sha256": sha256_file(args.split_manifest),
            "input_sha256": input_hashes,
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "macro_effects": macro_effects,
        "heterogeneity": payload["heterogeneity"],
        "reproduction_diagnostic": payload["reproduction_diagnostic"],
        "written": str(args.out),
    }, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
