#!/usr/bin/env python3
"""Validate and summarize all 24 global TabLLM references at K=512."""

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
PROTOCOL = ROOT / "iclr_latex_v3/TABLLM_ALL_REFERENCE_K512_FREEZE_V1.md"
RUNNER = ROOT / "scripts/run_tabllm_all_reference_k512_v1.py"
MANIFEST = ROOT / "experiments/tabllm_reference_space_v1/REFERENCE_MANIFEST_V1.json"
MANIFEST_SHA256 = "7fe208e544a954ebd2c15e273473d604107a22e49230631101466ab97097d8da"
DATASETS = (
    "bank", "blood", "calhousing", "car", "creditg",
    "diabetes", "heart", "income", "jungle",
)
SEEDS = (42, 1024, 0, 1, 32)
REFERENCES = tuple(f"ref_{index:02d}" for index in range(24))
PRIOR_REFERENCES = ("ref_22", "ref_04")
NEW_REFERENCES = tuple(
    reference
    for reference in REFERENCES
    if reference not in {"ref_00", *PRIOR_REFERENCES}
)
REPS = 10_000
BOOTSTRAP_SEED = 20260904
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
    return float(
        roc_auc_score(labels, probabilities, multi_class="ovr", average="macro")
    )


def validate_cell(
    root: Path,
    arm: str,
    dataset: str,
    seed: int,
    expected_status: str,
    input_hashes: dict[str, str],
    prefix: str,
) -> tuple[dict[str, Any], float, np.ndarray, np.ndarray, float]:
    cell = root / arm / dataset / "k512" / f"seed{seed}"
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
        "shot": 512,
        "seed": seed,
        "n_train": 512,
    }
    for key, value in expected.items():
        if metrics.get(key) != value:
            raise RuntimeError(
                f"{metrics_path}: {key}={metrics.get(key)!r}, expected {value!r}"
            )
    if metrics["training"]["planned_steps"] != 3840 or metrics[
        "training"
    ]["executed_steps"] != 3840:
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
    recomputed_accuracy = float(
        accuracy_score(labels, np.argmax(probabilities, axis=1))
    )
    metric_error = max(
        abs(recomputed_auc - float(metrics["metrics"]["auc"])),
        abs(recomputed_accuracy - float(metrics["metrics"]["accuracy"])),
    )
    if metric_error > 1e-12:
        raise RuntimeError(f"metric recomputation mismatch: {metrics_path}")
    return metrics, recomputed_auc, row_ids, labels, metric_error


def load_zero_utilities(
    path: Path,
) -> tuple[dict[tuple[str, str], dict[str, float]], str]:
    rows: dict[tuple[str, str], dict[str, float]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            reference = row["reference_id"]
            dataset = row["dataset"]
            if reference in REFERENCES and dataset in DATASETS:
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


def source_for_reference(
    reference: str,
    canonical_root: Path,
    prior_root: Path,
    new_root: Path,
) -> tuple[Path, str, str, str]:
    if reference == "ref_00":
        return (
            canonical_root,
            "list_stable_anonymous",
            "frozen_ranon_support_ladder_evidence",
            "canonical",
        )
    if reference in PRIOR_REFERENCES:
        return (
            prior_root,
            reference,
            "frozen_reference_envelope_support_ladder_evidence",
            "prior",
        )
    return new_root, reference, "frozen_all_reference_k512_evidence", "new"


def write_csv(summary: dict[str, Any], path: Path) -> None:
    fields = [
        "reference_id", "utility_k0", "utility_k512", "decay_0_to_512",
        "bootstrap_ci_low", "bootstrap_ci_high", "t_ci_low", "t_ci_high",
        "positive_dataset_decay_count", "drop_car_decay",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for reference in REFERENCES:
            record = summary["references"][reference]
            decay = record["decay_0_to_512"]
            writer.writerow({
                "reference_id": reference,
                "utility_k0": record["macro_utility_k0"],
                "utility_k512": record["macro_utility_k512"],
                "decay_0_to_512": decay["estimate"],
                "bootstrap_ci_low": decay["dataset_bootstrap_ci95"][0],
                "bootstrap_ci_high": decay["dataset_bootstrap_ci95"][1],
                "t_ci_low": decay["student_t_ci95_df8"][0],
                "t_ci_high": decay["student_t_ci95_df8"][1],
                "positive_dataset_decay_count": record[
                    "positive_dataset_decay_count"
                ],
                "drop_car_decay": record["drop_car_decay_0_to_512"],
            })


def write_report(summary: dict[str, Any], path: Path) -> None:
    envelope = summary["minimum_decay_envelope"]
    lines = [
        "# TabLLM exhaustive 24-reference K=512 sensitivity — results v1",
        "",
        f"Verdict: **{summary['sensitivity_verdict']}**.",
        "",
        "This is a post-result exhaustive sensitivity over the frozen 24-member",
        "global-construction library. It has not been incorporated into the manuscript.",
        "",
        "| Reference | u(0) | u(512) | Decay | Bootstrap 95% CI | t 95% CI |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for reference in REFERENCES:
        record = summary["references"][reference]
        decay = record["decay_0_to_512"]
        bci = decay["dataset_bootstrap_ci95"]
        tci = decay["student_t_ci95_df8"]
        lines.append(
            f"| `{reference}` | {record['macro_utility_k0']:+.4f} | "
            f"{record['macro_utility_k512']:+.4f} | {decay['estimate']:+.4f} | "
            f"[{bci[0]:+.4f}, {bci[1]:+.4f}] | "
            f"[{tci[0]:+.4f}, {tci[1]:+.4f}] |"
        )
    lines.extend([
        "",
        f"Observed decay range: `{summary['decay_range'][0]:+.4f}` to "
        f"`{summary['decay_range'][1]:+.4f}`.",
        f"K=512 utility range: `{summary['utility_k512_range'][0]:+.4f}` to "
        f"`{summary['utility_k512_range'][1]:+.4f}`.",
        f"Minimum-decay shared-bootstrap 95% interval: "
        f"`[{envelope['dataset_bootstrap_ci95'][0]:+.4f}, "
        f"{envelope['dataset_bootstrap_ci95'][1]:+.4f}]`.",
        f"All per-reference bootstrap and t lower bounds positive: "
        f"`{summary['all_interval_lower_bounds_positive']}`.",
        "",
        f"Validated new cells: {summary['validation']['new_evidence_cell_count']}/945; "
        f"reused K=512 cells: {summary['validation']['reused_k512_cell_count']}/180.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--new-root", type=Path, required=True)
    parser.add_argument("--prior-root", type=Path, required=True)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--zero-csv", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, required=True)
    args = parser.parse_args()

    if sha256_file(MANIFEST) != MANIFEST_SHA256:
        raise RuntimeError("reference manifest hash mismatch")
    frozen_manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    zero, zero_hash = load_zero_utilities(args.zero_csv)
    input_hashes = {"zero/reference_utilities.csv": zero_hash}
    intended = np.zeros((len(DATASETS), len(SEEDS)), dtype=np.float64)
    references = np.zeros(
        (len(REFERENCES), len(DATASETS), len(SEEDS)), dtype=np.float64
    )
    max_metric_error = 0.0
    contracts: dict[str, dict[str, Any] | None] = {
        "canonical": None, "prior": None, "new": None,
    }

    for d, dataset in enumerate(DATASETS):
        for s, seed in enumerate(SEEDS):
            s_metrics, s_auc, s_rows, s_labels, error = validate_cell(
                args.canonical_root,
                "list_template",
                dataset,
                seed,
                "frozen_ranon_support_ladder_evidence",
                input_hashes,
                "canonical",
            )
            intended[d, s] = s_auc
            max_metric_error = max(max_metric_error, error)
            pairing = (
                s_metrics["train_membership_row_ids_sha256"],
                s_metrics["test_row_ids_sha256"],
                s_metrics["initial_trainable_state_sha256"],
            )
            for r, reference in enumerate(REFERENCES):
                root, arm, status, source = source_for_reference(
                    reference, args.canonical_root, args.prior_root, args.new_root
                )
                metrics, estimate, rows, labels, error = validate_cell(
                    root, arm, dataset, seed, status, input_hashes, source
                )
                references[r, d, s] = estimate
                max_metric_error = max(max_metric_error, error)
                candidate = frozen_manifest["datasets"][dataset]["candidates"][reference]
                if reference != "ref_00":
                    expected = {
                        "reference_id": reference,
                        "reference_manifest_sha256": MANIFEST_SHA256,
                        "reference_permutation": candidate[
                            "line_to_identifier_index_zero_based"
                        ],
                        "reference_template_sha256": candidate["template_sha256"],
                        "protobuf_python_implementation": "python",
                    }
                    if source == "new":
                        expected.update({
                            "protocol_sha256": sha256_file(PROTOCOL),
                            "runner_sha256": sha256_file(RUNNER),
                        })
                    for field, expected_value in expected.items():
                        if metrics.get(field) != expected_value:
                            raise RuntimeError(
                                f"provenance mismatch {field}: {dataset}/{seed}/{reference}"
                            )
                fields = {key: metrics[key] for key in (
                    "protocol_sha256", "runner_sha256", "split_manifest_sha256",
                    "tabllm_commit", "tfew_execution_commit",
                    "raw_and_serialization_tree_sha256", "ia3_checkpoint_sha256",
                )}
                if contracts[source] is None:
                    contracts[source] = fields
                elif contracts[source] != fields:
                    raise RuntimeError(f"{source} cells do not share one contract")
                ref_pairing = (
                    metrics["train_membership_row_ids_sha256"],
                    metrics["test_row_ids_sha256"],
                    metrics["initial_trainable_state_sha256"],
                )
                if ref_pairing != pairing:
                    raise RuntimeError(f"pairing hash mismatch: {dataset}/{seed}/{reference}")
                if not np.array_equal(s_rows, rows) or not np.array_equal(s_labels, labels):
                    raise RuntimeError(
                        f"prediction membership mismatch: {dataset}/{seed}/{reference}"
                    )

    dataset_u0 = np.asarray([
        [zero[(reference, dataset)]["utility"] for dataset in DATASETS]
        for reference in REFERENCES
    ], dtype=np.float64)
    dataset_u512 = (intended[None, :, :] - references).mean(axis=2)
    dataset_decay = dataset_u0 - dataset_u512
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    selections = rng.integers(0, len(DATASETS), size=(REPS, len(DATASETS)))
    reference_summary: dict[str, Any] = {}
    all_lower_positive = True
    for r, reference in enumerate(REFERENCES):
        decay = interval_record(dataset_decay[r], selections)
        all_lower_positive = all_lower_positive and (
            decay["dataset_bootstrap_ci95"][0] > 0
            and decay["student_t_ci95_df8"][0] > 0
        )
        reference_summary[reference] = {
            "macro_utility_k0": float(dataset_u0[r].mean()),
            "macro_utility_k512": float(dataset_u512[r].mean()),
            "decay_0_to_512": decay,
            "positive_dataset_decay_count": int(np.sum(dataset_decay[r] > 0)),
            "drop_car_decay_0_to_512": float(
                np.delete(dataset_decay[r], DATASETS.index("car")).mean()
            ),
            "datasets": {
                dataset: {
                    "utility_k0": float(dataset_u0[r, d]),
                    "utility_k512": float(dataset_u512[r, d]),
                    "decay_0_to_512": float(dataset_decay[r, d]),
                }
                for d, dataset in enumerate(DATASETS)
            },
        }

    decay_estimates = dataset_decay.mean(axis=1)
    u0_estimates = dataset_u0.mean(axis=1)
    u512_estimates = dataset_u512.mean(axis=1)
    bootstrap_decay_by_reference = dataset_decay[:, selections].mean(axis=2).T
    minimum_draws = bootstrap_decay_by_reference.min(axis=1)
    observed_min_index = int(np.argmin(decay_estimates))
    sign_robust = bool(np.all(decay_estimates > 0))
    payload = {
        "analysis_status": "postresult_all_24_global_reference_k512_complete",
        "sensitivity_verdict": (
            "SIGN_ROBUST_ACROSS_ALL_24_GLOBAL_REFERENCES"
            if sign_robust
            else "SIGN_NOT_ROBUST_ACROSS_ALL_24_GLOBAL_REFERENCES"
        ),
        "postresult_disclosure": (
            "all zero-shot outcomes and three K=512 references were known before this extension"
        ),
        "panel": list(DATASETS),
        "seeds": list(SEEDS),
        "support": 512,
        "references": reference_summary,
        "zero_shot_utility_range": [
            float(u0_estimates.min()), float(u0_estimates.max())
        ],
        "utility_k512_range": [
            float(u512_estimates.min()), float(u512_estimates.max())
        ],
        "decay_range": [
            float(decay_estimates.min()), float(decay_estimates.max())
        ],
        "minimum_decay_envelope": {
            "observed_reference": REFERENCES[observed_min_index],
            "observed_minimum": float(decay_estimates[observed_min_index]),
            "dataset_bootstrap_ci95": [
                float(value) for value in np.quantile(minimum_draws, [0.025, 0.975])
            ],
            "bootstrap_draw_mean": float(minimum_draws.mean()),
        },
        "reference_level_u0_u512_pearson": float(
            np.corrcoef(u0_estimates, u512_estimates)[0, 1]
        ),
        "all_interval_lower_bounds_positive": bool(all_lower_positive),
        "validation": {
            "new_evidence_cell_count": len(NEW_REFERENCES) * len(DATASETS) * len(SEEDS),
            "reused_k512_cell_count": (
                1 + len(PRIOR_REFERENCES) + 1
            ) * len(DATASETS) * len(SEEDS),
            "paired_cell_group_count": len(DATASETS) * len(SEEDS),
            "references_per_paired_group": len(REFERENCES),
            "all_pairing_hashes_match": True,
            "maximum_metric_recompute_error": max_metric_error,
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
            "reference_manifest_sha256": MANIFEST_SHA256,
            "contracts": contracts,
            "input_sha256": input_hashes,
        },
    }

    args.out_root.mkdir(parents=True, exist_ok=True)
    summary_path = args.out_root / "SUMMARY_V1.json"
    csv_path = args.out_root / "reference_endpoint_decays_v1.csv"
    report_path = args.out_root / "RESULTS_V1.md"
    run_manifest_path = args.out_root / "RUN_MANIFEST_V1.md"
    summary_path.write_text(
        json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_csv(payload, csv_path)
    write_report(payload, report_path)
    run_manifest_path.write_text(
        "\n".join([
            "# TabLLM exhaustive global-reference K=512 run manifest v1",
            "",
            "- Protocol: `iclr_latex_v3/TABLLM_ALL_REFERENCE_K512_FREEZE_V1.md`",
            f"- New evidence cells: {payload['validation']['new_evidence_cell_count']}/945",
            f"- Reused K=512 cells: {payload['validation']['reused_k512_cell_count']}/180",
            f"- Verdict: `{payload['sensitivity_verdict']}`",
            "- Manuscript integration: not performed",
            "",
        ]),
        encoding="utf-8",
    )
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
        json.dumps(artifact_manifest, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "verdict": payload["sensitivity_verdict"],
        "decay_range": payload["decay_range"],
        "utility_k512_range": payload["utility_k512_range"],
        "minimum_decay_envelope": payload["minimum_decay_envelope"],
        "all_interval_lower_bounds_positive": all_lower_positive,
        "written": [str(path) for path in (
            summary_path, csv_path, report_path, run_manifest_path, artifact_path
        )],
    }, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
