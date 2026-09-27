#!/usr/bin/env python3
"""Validate and summarize the three-reference TabLLM support sensitivity."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "iclr_latex_v3/TABLLM_REFERENCE_ENVELOPE_SUPPORT_LADDER_FREEZE_V1.md"
RUNNER = ROOT / "scripts/run_tabllm_reference_envelope_support_ladder_v1.py"
MANIFEST = ROOT / "experiments/tabllm_reference_space_v1/REFERENCE_MANIFEST_V1.json"
DATASETS = (
    "bank", "blood", "calhousing", "car", "creditg",
    "diabetes", "heart", "income", "jungle",
)
SEEDS = (42, 1024, 0, 1, 32)
SHOTS = (0, 4, 32, 512)
REFERENCES = ("ref_00", "ref_22", "ref_04")
NEW_REFERENCES = ("ref_22", "ref_04")
REFERENCE_ROLES = {"ref_00": "lower_canonical", "ref_22": "center", "ref_04": "upper"}
REPS = 10_000
BOOTSTRAP_SEED = 20260903
T_DF8_975 = 2.306004135204166


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def read_predictions(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            rows.append(json.loads(line))
    return (
        np.asarray([int(row["row_id"]) for row in rows], dtype=np.int64),
        np.asarray([int(row["label"]) for row in rows], dtype=np.int64),
        np.asarray([row["class_probabilities"] for row in rows], dtype=np.float64),
    )


def auc(labels: np.ndarray, probabilities: np.ndarray) -> float:
    if probabilities.shape[1] == 2:
        return float(roc_auc_score(labels, probabilities[:, 1]))
    return float(roc_auc_score(
        labels, probabilities, multi_class="ovr", average="macro"
    ))


def t_interval(values: np.ndarray) -> list[float]:
    mean = float(values.mean())
    half_width = T_DF8_975 * float(values.std(ddof=1)) / math.sqrt(len(values))
    return [mean - half_width, mean + half_width]


def interval_record(values: np.ndarray, selections: np.ndarray) -> dict[str, Any]:
    draws = values[selections].mean(axis=1)
    return {
        "estimate": float(values.mean()),
        "dataset_values": [float(value) for value in values],
        "dataset_bootstrap_ci95": [
            float(value) for value in np.quantile(draws, [0.025, 0.975])
        ],
        "student_t_ci95_df8": t_interval(values),
        "bootstrap_draw_mean": float(draws.mean()),
    }


def validate_cell(
    root: Path,
    arm: str,
    dataset: str,
    shot: int,
    seed: int,
    expected_status: str,
    input_hashes: dict[str, str],
    prefix: str,
) -> tuple[dict[str, Any], float, np.ndarray, np.ndarray, float]:
    cell = root / arm / dataset / f"k{shot}" / f"seed{seed}"
    metrics_path = cell / "metrics.json"
    predictions_path = cell / "predictions.jsonl.gz"
    checkpoint_path = cell / "ia3_finish.pt"
    for path in (metrics_path, predictions_path, checkpoint_path):
        if not path.is_file():
            raise FileNotFoundError(path)
        input_hashes[f"{prefix}/{path.relative_to(root)}"] = sha256_file(path)
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    expected = {
        "analysis_status": expected_status,
        "dataset": dataset,
        "arm": arm,
        "shot": shot,
        "seed": seed,
        "n_train": shot,
    }
    for key, value in expected.items():
        if metrics.get(key) != value:
            raise RuntimeError(
                f"{metrics_path}: {key}={metrics.get(key)!r}, expected {value!r}"
            )
    planned_steps = 30 * (shot // 4)
    if metrics["training"]["planned_steps"] != planned_steps or metrics[
        "training"
    ]["executed_steps"] != planned_steps:
        raise RuntimeError(f"incomplete training: {metrics_path}")
    if metrics["predictions_sha256"] != sha256_file(predictions_path):
        raise RuntimeError(f"prediction hash mismatch: {metrics_path}")
    if metrics["trained_checkpoint_sha256"] != sha256_file(checkpoint_path):
        raise RuntimeError(f"checkpoint hash mismatch: {metrics_path}")
    row_ids, labels, probabilities = read_predictions(predictions_path)
    if len(row_ids) != metrics["n_test"] or len(set(row_ids.tolist())) != len(row_ids):
        raise RuntimeError(f"invalid prediction membership: {predictions_path}")
    if not np.isfinite(probabilities).all():
        raise RuntimeError(f"nonfinite probability: {predictions_path}")
    probability_error = float(np.max(np.abs(probabilities.sum(axis=1) - 1.0)))
    if probability_error > 1e-6:
        raise RuntimeError(f"probability normalization error: {predictions_path}")
    recomputed_auc = auc(labels, probabilities)
    recomputed_accuracy = float(accuracy_score(labels, np.argmax(probabilities, axis=1)))
    metric_error = max(
        abs(recomputed_auc - float(metrics["metrics"]["auc"])),
        abs(recomputed_accuracy - float(metrics["metrics"]["accuracy"])),
    )
    if metric_error > 1e-12:
        raise RuntimeError(f"metric recomputation mismatch: {metrics_path}")
    return metrics, recomputed_auc, row_ids, labels, metric_error


def load_zero_utilities(path: Path) -> tuple[dict[tuple[str, str], dict[str, float]], str]:
    rows: dict[tuple[str, str], dict[str, float]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            reference = row["reference_id"]
            dataset = row["dataset"]
            if reference not in REFERENCES or dataset not in DATASETS:
                continue
            rows[(reference, dataset)] = {
                "intended_auc": float(row["intended_auc"]),
                "reference_auc": float(row["reference_auc"]),
                "utility": float(row["utility"]),
            }
    expected = {(reference, dataset) for reference in REFERENCES for dataset in DATASETS}
    if set(rows) != expected:
        raise RuntimeError(f"zero-shot utility rows incomplete: {set(rows) ^ expected}")
    for value in rows.values():
        if abs(value["intended_auc"] - value["reference_auc"] - value["utility"]) > 1e-12:
            raise RuntimeError("zero-shot utility arithmetic mismatch")
    return rows, sha256_file(path)


def write_dataset_csv(summary: dict[str, Any], path: Path) -> None:
    fields = [
        "reference_id", "selection_role", "dataset", "utility_k0", "utility_k4",
        "utility_k32", "utility_k512", "decay_0_to_512", "decay_4_to_512",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for reference in REFERENCES:
            for dataset in DATASETS:
                record = summary["references"][reference]["datasets"][dataset]
                writer.writerow({
                    "reference_id": reference,
                    "selection_role": REFERENCE_ROLES[reference],
                    "dataset": dataset,
                    **{f"utility_k{shot}": record["utility"][str(shot)] for shot in SHOTS},
                    "decay_0_to_512": record["decay_0_to_512"],
                    "decay_4_to_512": record["decay_4_to_512"],
                })


def format_ci(values: list[float]) -> str:
    return f"[{values[0]:+.4f}, {values[1]:+.4f}]"


def write_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# TabLLM global-reference envelope support ladder — results v1",
        "",
        f"Sensitivity verdict: **{summary['sensitivity_verdict']}**.",
        "",
        "This is a post-result, three-reference sensitivity analysis. It has not been",
        "incorporated into manuscript text, tables, or figures.",
        "",
        "| Reference | Role | u(0) | u(4) | u(32) | u(512) | Decay 0→512 | Bootstrap 95% CI | t 95% CI |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for reference in REFERENCES:
        record = summary["references"][reference]
        utility = record["macro_utility"]
        decay = record["decay_0_to_512"]
        lines.append(
            f"| `{reference}` | {REFERENCE_ROLES[reference]} | "
            + " | ".join(f"{utility[str(shot)]:+.4f}" for shot in SHOTS)
            + f" | {decay['estimate']:+.4f} | {format_ci(decay['dataset_bootstrap_ci95'])}"
            + f" | {format_ci(decay['student_t_ci95_df8'])} |"
        )
    lines.extend([
        "",
        f"Decay magnitude range: `{summary['decay_magnitude_range'][0]:+.4f}` to "
        f"`{summary['decay_magnitude_range'][1]:+.4f}`. All bootstrap and t lower "
        f"bounds positive: `{summary['all_interval_lower_bounds_positive']}`.",
        "",
        f"All {summary['validation']['new_evidence_cell_count']} new cells and "
        f"{summary['validation']['reused_nonzero_cell_count']} reused nonzero cells "
        "passed artifact, step-count, pairing, probability, and metric validation.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_run_manifest(summary: dict[str, Any], path: Path) -> None:
    text = f"""# TabLLM global-reference envelope support ladder v1

- Protocol: `iclr_latex_v3/TABLLM_REFERENCE_ENVELOPE_SUPPORT_LADDER_FREEZE_V1.md`
- Added references: `ref_22` (aligned-range center), `ref_04` (upper endpoint)
- Reused reference: `ref_00` (canonical/lower endpoint)
- New evidence cells: {summary['validation']['new_evidence_cell_count']}/270
- Reused nonzero cells validated: {summary['validation']['reused_nonzero_cell_count']}/270
- Sensitivity verdict: `{summary['sensitivity_verdict']}`
- Decay range: [{summary['decay_magnitude_range'][0]:+.6f}, {summary['decay_magnitude_range'][1]:+.6f}]
- Manuscript integration: not performed

Raw new evidence remains on the B200 execution host. Compact validated outputs
in this directory are covered by `ARTIFACT_MANIFEST_V1.json`.
"""
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--new-root", type=Path, required=True)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--zero-csv", type=Path, required=True)
    parser.add_argument("--canonical-summary", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, required=True)
    args = parser.parse_args()

    manifest_hash = sha256_file(MANIFEST)
    frozen_manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    zero, zero_hash = load_zero_utilities(args.zero_csv)
    input_hashes: dict[str, str] = {
        "zero/reference_utilities.csv": zero_hash,
        "canonical/SUMMARY_V1.json": sha256_file(args.canonical_summary),
    }
    # [dataset, seed, nonzero-shot]
    intended = np.zeros((len(DATASETS), len(SEEDS), 3), dtype=np.float64)
    references = {
        reference: np.zeros_like(intended) for reference in REFERENCES
    }
    pairing: dict[tuple[str, int, int], dict[str, tuple[str, str, str]]] = {}
    max_metric_error = 0.0
    new_contract: dict[str, Any] | None = None
    canonical_contract: dict[str, Any] | None = None

    for d, dataset in enumerate(DATASETS):
        for k, shot in enumerate(SHOTS[1:]):
            for s, seed in enumerate(SEEDS):
                s_metrics, s_auc, s_rows, s_labels, error = validate_cell(
                    args.canonical_root, "list_template", dataset, shot, seed,
                    "frozen_ranon_support_ladder_evidence", input_hashes, "canonical",
                )
                intended[d, s, k] = s_auc
                max_metric_error = max(max_metric_error, error)
                fields = {key: s_metrics[key] for key in (
                    "protocol_sha256", "runner_sha256", "split_manifest_sha256",
                    "tabllm_commit", "tfew_execution_commit",
                    "raw_and_serialization_tree_sha256", "ia3_checkpoint_sha256",
                )}
                if canonical_contract is None:
                    canonical_contract = fields
                elif canonical_contract != fields:
                    raise RuntimeError("reused canonical cells do not share one contract")
                key = (dataset, shot, seed)
                pairing.setdefault(key, {})["list_template"] = (
                    s_metrics["train_membership_row_ids_sha256"],
                    s_metrics["test_row_ids_sha256"],
                    s_metrics["initial_trainable_state_sha256"],
                )

                r0_metrics, r0_auc, r0_rows, r0_labels, error = validate_cell(
                    args.canonical_root, "list_stable_anonymous", dataset, shot, seed,
                    "frozen_ranon_support_ladder_evidence", input_hashes, "canonical",
                )
                references["ref_00"][d, s, k] = r0_auc
                max_metric_error = max(max_metric_error, error)
                pairing[key]["ref_00"] = (
                    r0_metrics["train_membership_row_ids_sha256"],
                    r0_metrics["test_row_ids_sha256"],
                    r0_metrics["initial_trainable_state_sha256"],
                )
                if not np.array_equal(s_rows, r0_rows) or not np.array_equal(s_labels, r0_labels):
                    raise RuntimeError(f"canonical prediction pairing mismatch: {key}")

                for reference in NEW_REFERENCES:
                    metrics, estimate, rows, labels, error = validate_cell(
                        args.new_root, reference, dataset, shot, seed,
                        "frozen_reference_envelope_support_ladder_evidence",
                        input_hashes, "new",
                    )
                    references[reference][d, s, k] = estimate
                    max_metric_error = max(max_metric_error, error)
                    expected_candidate = frozen_manifest["datasets"][dataset]["candidates"][reference]
                    expected_new = {
                        "protocol_sha256": sha256_file(PROTOCOL),
                        "runner_sha256": sha256_file(RUNNER),
                        "reference_manifest_sha256": manifest_hash,
                        "reference_id": reference,
                        "reference_permutation": expected_candidate[
                            "line_to_identifier_index_zero_based"
                        ],
                        "reference_template_sha256": expected_candidate["template_sha256"],
                        "protobuf_python_implementation": "python",
                    }
                    for field, expected_value in expected_new.items():
                        if metrics.get(field) != expected_value:
                            raise RuntimeError(
                                f"new provenance mismatch {field}: {dataset}/{shot}/{seed}/{reference}"
                            )
                    fields = {field: metrics[field] for field in (
                        "protocol_sha256", "runner_sha256", "base_runner_sha256",
                        "reference_manifest_sha256", "split_manifest_sha256",
                        "tabllm_commit", "tfew_execution_commit",
                        "raw_and_serialization_tree_sha256", "ia3_checkpoint_sha256",
                    )}
                    if new_contract is None:
                        new_contract = fields
                    elif new_contract != fields:
                        raise RuntimeError("new cells do not share one contract")
                    pairing[key][reference] = (
                        metrics["train_membership_row_ids_sha256"],
                        metrics["test_row_ids_sha256"],
                        metrics["initial_trainable_state_sha256"],
                    )
                    if not np.array_equal(s_rows, rows) or not np.array_equal(s_labels, labels):
                        raise RuntimeError(f"new prediction pairing mismatch: {key}/{reference}")

    for key, arms in pairing.items():
        baseline = arms["list_template"]
        if set(arms) != {"list_template", *REFERENCES}:
            raise RuntimeError(f"incomplete pairing: {key}")
        if any(value != baseline for arm, value in arms.items() if arm != "list_template"):
            raise RuntimeError(f"pairing hash mismatch: {key}")

    rng = np.random.default_rng(BOOTSTRAP_SEED)
    selections = rng.integers(0, len(DATASETS), size=(REPS, len(DATASETS)))
    reference_summary: dict[str, Any] = {}
    decay_estimates = []
    all_lower_positive = True
    for reference in REFERENCES:
        dataset_utility = np.zeros((len(DATASETS), len(SHOTS)), dtype=np.float64)
        dataset_utility[:, 0] = [zero[(reference, dataset)]["utility"] for dataset in DATASETS]
        dataset_utility[:, 1:] = (intended - references[reference]).mean(axis=1)
        primary_values = dataset_utility[:, 0] - dataset_utility[:, 3]
        secondary_values = dataset_utility[:, 1] - dataset_utility[:, 3]
        primary = interval_record(primary_values, selections)
        secondary = interval_record(secondary_values, selections)
        decay_estimates.append(primary["estimate"])
        all_lower_positive = all_lower_positive and all(
            interval[0] > 0
            for interval in (
                primary["dataset_bootstrap_ci95"], primary["student_t_ci95_df8"]
            )
        )
        reference_summary[reference] = {
            "selection_role": REFERENCE_ROLES[reference],
            "macro_utility": {
                str(shot): float(dataset_utility[:, index].mean())
                for index, shot in enumerate(SHOTS)
            },
            "macro_arm_auc": {
                "0": {
                    "list_template": float(np.mean([
                        zero[(reference, dataset)]["intended_auc"] for dataset in DATASETS
                    ])),
                    reference: float(np.mean([
                        zero[(reference, dataset)]["reference_auc"] for dataset in DATASETS
                    ])),
                },
                **{
                    str(shot): {
                        "list_template": float(intended[:, :, k].mean()),
                        reference: float(references[reference][:, :, k].mean()),
                    }
                    for k, shot in enumerate(SHOTS[1:])
                },
            },
            "decay_0_to_512": primary,
            "decay_4_to_512": secondary,
            "drop_car_decay_0_to_512": float(
                np.delete(primary_values, DATASETS.index("car")).mean()
            ),
            "positive_dataset_decay_count": int(np.sum(primary_values > 0)),
            "macro_point_trajectory_nonincreasing": bool(
                np.all(np.diff(dataset_utility.mean(axis=0)) <= 0)
            ),
            "datasets": {
                dataset: {
                    "utility": {
                        str(shot): float(dataset_utility[d, k])
                        for k, shot in enumerate(SHOTS)
                    },
                    "decay_0_to_512": float(primary_values[d]),
                    "decay_4_to_512": float(secondary_values[d]),
                }
                for d, dataset in enumerate(DATASETS)
            },
        }

    canonical_summary = json.loads(args.canonical_summary.read_text(encoding="utf-8"))
    canonical_error = abs(
        reference_summary["ref_00"]["decay_0_to_512"]["estimate"]
        - float(canonical_summary["primary_decay_0_to_512"]["estimate"])
    )
    if canonical_error > 1e-12:
        raise RuntimeError(f"canonical summary reproduction failed: {canonical_error}")
    sign_robust = all(value > 0 for value in decay_estimates)
    payload = {
        "analysis_status": "postresult_reference_envelope_support_sensitivity_complete",
        "sensitivity_verdict": (
            "SIGN_ROBUST_ACROSS_SELECTED_REFERENCES"
            if sign_robust else "SIGN_NOT_ROBUST_ACROSS_SELECTED_REFERENCES"
        ),
        "postresult_selection_disclosure": (
            "ref_22 and ref_04 were selected after zero-shot reference utilities were known"
        ),
        "panel": list(DATASETS),
        "seeds": list(SEEDS),
        "shots": list(SHOTS),
        "references": reference_summary,
        "decay_magnitude_range": [float(min(decay_estimates)), float(max(decay_estimates))],
        "all_interval_lower_bounds_positive": bool(all_lower_positive),
        "validation": {
            "new_evidence_cell_count": len(DATASETS) * len(SEEDS) * 3 * len(NEW_REFERENCES),
            "reused_nonzero_cell_count": len(DATASETS) * len(SEEDS) * 3 * 2,
            "paired_cell_group_count": len(pairing),
            "all_pairing_hashes_match": True,
            "maximum_metric_recompute_error": max_metric_error,
            "canonical_summary_reproduction_error": canonical_error,
        },
        "inference": {
            "independent_unit": "dataset",
            "bootstrap_reps": REPS,
            "shared_bootstrap_seed": BOOTSTRAP_SEED,
            "student_t_df": 8,
        },
        "provenance": {
            "protocol_sha256": sha256_file(PROTOCOL),
            "runner_sha256": sha256_file(RUNNER),
            "summarizer_sha256": sha256_file(Path(__file__)),
            "reference_manifest_sha256": manifest_hash,
            "new_contract": new_contract,
            "canonical_contract": canonical_contract,
            "input_sha256": input_hashes,
        },
    }
    args.out_root.mkdir(parents=True, exist_ok=True)
    summary_path = args.out_root / "SUMMARY_V1.json"
    csv_path = args.out_root / "dataset_reference_decays_v1.csv"
    report_path = args.out_root / "RESULTS_V1.md"
    run_manifest_path = args.out_root / "RUN_MANIFEST_V1.md"
    summary_path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    write_dataset_csv(payload, csv_path)
    write_report(payload, report_path)
    write_run_manifest(payload, run_manifest_path)
    artifact_manifest = {
        "analysis_status": "validated_compact_artifact_manifest",
        "inputs": input_hashes,
        "outputs": {
            path.name: sha256_file(path)
            for path in (summary_path, csv_path, report_path, run_manifest_path)
        },
    }
    artifact_path = args.out_root / "ARTIFACT_MANIFEST_V1.json"
    artifact_path.write_text(
        json.dumps(artifact_manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "verdict": payload["sensitivity_verdict"],
        "decays": {
            reference: reference_summary[reference]["decay_0_to_512"]["estimate"]
            for reference in REFERENCES
        },
        "decay_range": payload["decay_magnitude_range"],
        "all_interval_lower_bounds_positive": all_lower_positive,
        "written": [str(path) for path in (
            summary_path, csv_path, report_path, run_manifest_path, artifact_path
        )],
    }, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
