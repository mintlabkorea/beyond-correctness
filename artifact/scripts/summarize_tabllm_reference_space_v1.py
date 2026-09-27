#!/usr/bin/env python3
"""Summarize the frozen TabLLM admissible-reference space audit."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "iclr_latex_v3/TABLLM_ADMISSIBLE_REFERENCE_SPACE_FREEZE_V1.md"
RUNNER = ROOT / "scripts/run_tabllm_reference_space_v1.py"
DATASETS = (
    "bank", "blood", "calhousing", "car", "creditg",
    "diabetes", "heart", "income", "jungle",
)
SEEDS = (42, 1024, 0, 1, 32)
REFERENCE_IDS = tuple(f"ref_{index:02d}" for index in range(24))
SESOI = 0.02
MC_DRAWS = 1_000_000
MC_SEED = 20260903
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 20260904


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def interval(values: np.ndarray) -> list[float]:
    return [float(value) for value in np.quantile(values, [0.025, 0.975])]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--intended-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--out-root", type=Path,
        default=ROOT / "experiments/tabllm_reference_space_v1",
    )
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    expected_hashes = {
        "protocol_sha256": sha256_file(PROTOCOL),
        "runner_sha256": sha256_file(RUNNER),
        "summarizer_sha256": sha256_file(Path(__file__)),
        "base_runner_sha256": sha256_file(
            ROOT / "scripts/run_tabllm_retrospective_audit_v1.py"
        ),
    }
    for key, value in expected_hashes.items():
        if manifest.get(key) != value:
            raise RuntimeError(f"manifest {key} mismatch")
    manifest_hash = sha256_file(args.manifest)

    intended: dict[str, dict[int, float]] = {}
    for dataset in DATASETS:
        payload = load_json(args.intended_root / dataset / "metrics.json")
        intended[dataset] = {
            seed: float(payload["metrics"][str(seed)]["auc"])
            for seed in SEEDS
        }

    utility = np.empty((len(DATASETS), len(REFERENCE_IDS)), dtype=np.float64)
    reference_auc = np.empty_like(utility)
    artifact_hashes: dict[str, str] = {}
    row_records: list[dict[str, Any]] = []
    for dataset_index, dataset in enumerate(DATASETS):
        intended_mean = float(np.mean(list(intended[dataset].values())))
        for reference_index, reference_id in enumerate(REFERENCE_IDS):
            cell = args.evidence_root / reference_id / dataset
            metrics_path = cell / "metrics.json"
            predictions_path = cell / "predictions.jsonl.gz"
            if not metrics_path.is_file() or not predictions_path.is_file():
                raise FileNotFoundError(f"incomplete cell: {cell}")
            payload = load_json(metrics_path)
            for key, value in {
                "analysis_status": "frozen_reference_space_evidence",
                "protocol_sha256": expected_hashes["protocol_sha256"],
                "runner_sha256": expected_hashes["runner_sha256"],
                "base_runner_sha256": expected_hashes["base_runner_sha256"],
                "reference_manifest_sha256": manifest_hash,
                "dataset": dataset,
                "reference_id": reference_id,
            }.items():
                if payload.get(key) != value:
                    raise RuntimeError(f"cell mismatch {cell}: {key}")
            expected_candidate = manifest["datasets"][dataset]["candidates"][
                reference_id
            ]
            if payload.get("permutation") != expected_candidate[
                "line_to_identifier_index_zero_based"
            ]:
                raise RuntimeError(f"permutation mismatch: {cell}")
            if payload.get("template_sha256") != expected_candidate["template_sha256"]:
                raise RuntimeError(f"template mismatch: {cell}")
            if sha256_file(predictions_path) != payload.get("predictions_sha256"):
                raise RuntimeError(f"prediction hash mismatch: {cell}")
            for seed in SEEDS:
                observed_hash = payload["metrics"][str(seed)]["test_row_ids_sha256"]
                expected_split_hash = manifest["datasets"][dataset][
                    "test_row_ids_sha256"
                ][str(seed)]
                if observed_hash != expected_split_hash:
                    raise RuntimeError(f"test membership mismatch: {cell}/{seed}")
            if reference_id == "ref_00":
                audit = payload.get("canonical_reproduction_audit", {})
                if audit.get("status") != "canonical_reproduction_pass":
                    raise RuntimeError(f"canonical reproduction failed: {cell}")

            ref_mean = float(payload["metrics"]["mean"]["auc"])
            u_value = intended_mean - ref_mean
            reference_auc[dataset_index, reference_index] = ref_mean
            utility[dataset_index, reference_index] = u_value
            row_records.append({
                "dataset": dataset,
                "reference_id": reference_id,
                "intended_auc": intended_mean,
                "reference_auc": ref_mean,
                "utility": u_value,
            })
            artifact_hashes[
                f"{reference_id}/{dataset}/metrics.json"
            ] = sha256_file(metrics_path)
            artifact_hashes[
                f"{reference_id}/{dataset}/predictions.jsonl.gz"
            ] = sha256_file(predictions_path)

    dataset_min = utility.min(axis=1)
    dataset_max = utility.max(axis=1)
    dataset_span = dataset_max - dataset_min
    dataset_summaries: dict[str, Any] = {}
    for index, dataset in enumerate(DATASETS):
        values = utility[index]
        dataset_summaries[dataset] = {
            "canonical_utility": float(values[0]),
            "minimum_utility": float(values.min()),
            "minimum_reference_id": REFERENCE_IDS[int(np.argmin(values))],
            "maximum_utility": float(values.max()),
            "maximum_reference_id": REFERENCE_IDS[int(np.argmax(values))],
            "span": float(np.ptp(values)),
            "mean": float(values.mean()),
            "sd_population": float(values.std(ddof=0)),
            "iqr": float(np.quantile(values, 0.75) - np.quantile(values, 0.25)),
            "sign_change_across_references": bool(values.min() <= 0 <= values.max()),
            "positive_reference_count": int(np.sum(values > 0)),
            "candidate_count": len(values),
            "complete_permutation_space": manifest["datasets"][dataset][
                "complete_space"
            ],
        }

    macro_by_aligned_index = utility.mean(axis=0)
    lower = float(dataset_min.mean())
    upper = float(dataset_max.mean())
    span = upper - lower
    canonical = float(utility[:, 0].mean())

    analytic_uniform_mean = float(utility.mean(axis=1).mean())
    analytic_uniform_sd = float(
        np.sqrt(np.sum(utility.var(axis=1, ddof=0))) / len(DATASETS)
    )
    rng = np.random.default_rng(MC_SEED)
    monte_carlo = np.zeros(MC_DRAWS, dtype=np.float64)
    for dataset_index in range(len(DATASETS)):
        choices = rng.integers(0, len(REFERENCE_IDS), size=MC_DRAWS)
        monte_carlo += utility[dataset_index, choices]
    monte_carlo /= len(DATASETS)
    quantile_levels = [0.025, 0.10, 0.50, 0.90, 0.975]
    monte_carlo_quantiles = {
        str(level): float(value)
        for level, value in zip(quantile_levels, np.quantile(monte_carlo, quantile_levels))
    }

    bootstrap_rng = np.random.default_rng(BOOTSTRAP_SEED)
    indices = bootstrap_rng.integers(
        0, len(DATASETS), size=(BOOTSTRAP_DRAWS, len(DATASETS))
    )
    bootstrap_lower = dataset_min[indices].mean(axis=1)
    bootstrap_upper = dataset_max[indices].mean(axis=1)
    bootstrap_span = dataset_span[indices].mean(axis=1)

    if lower > 0 and span < SESOI:
        verdict = "STABLE_WITHIN_TIGHT_SPACE"
    elif lower > 0 and span >= SESOI:
        verdict = "MAGNITUDE_SENSITIVE_SIGN_ROBUST"
    elif lower <= 0 <= upper:
        verdict = "SIGN_SENSITIVE"
    else:
        verdict = "DIRECTIONAL_ENVELOPE_OUTSIDE_FROZEN_LABELS"

    summary = {
        "analysis_status": "frozen_reference_space_complete",
        "verdict": verdict,
        "cell_count": len(DATASETS) * len(REFERENCE_IDS),
        "dataset_count": len(DATASETS),
        "reference_count": len(REFERENCE_IDS),
        "seed_count": len(SEEDS),
        "estimand": "mean_seed_AUROC_intended_minus_reference",
        "sesoi": SESOI,
        "canonical_macro_utility": canonical,
        "combinatorial_macro_envelope": {
            "lower": lower,
            "upper": upper,
            "span": span,
            "lower_dataset_bootstrap_95_ci": interval(bootstrap_lower),
            "upper_dataset_bootstrap_95_ci": interval(bootstrap_upper),
            "span_dataset_bootstrap_95_ci": interval(bootstrap_span),
        },
        "aligned_reference_index_macro_distribution": {
            "values": {
                reference_id: float(macro_by_aligned_index[index])
                for index, reference_id in enumerate(REFERENCE_IDS)
            },
            "mean": float(macro_by_aligned_index.mean()),
            "sd_population": float(macro_by_aligned_index.std(ddof=0)),
            "minimum": float(macro_by_aligned_index.min()),
            "maximum": float(macro_by_aligned_index.max()),
            "iqr": float(
                np.quantile(macro_by_aligned_index, 0.75)
                - np.quantile(macro_by_aligned_index, 0.25)
            ),
        },
        "independent_uniform_product_space": {
            "analytic_mean": analytic_uniform_mean,
            "analytic_sd": analytic_uniform_sd,
            "monte_carlo_draws": MC_DRAWS,
            "monte_carlo_seed": MC_SEED,
            "quantiles": monte_carlo_quantiles,
            "canonical_percentile": float(np.mean(monte_carlo <= canonical)),
        },
        "dataset_bootstrap": {
            "draws": BOOTSTRAP_DRAWS,
            "seed": BOOTSTRAP_SEED,
            "unit": "dataset",
        },
        "datasets": dataset_summaries,
        "validation": {
            "complete_cells": True,
            "all_prediction_hashes_match": True,
            "all_template_and_permutation_hashes_match": True,
            "all_test_memberships_match": True,
            "all_canonical_groups_reproduce": True,
            "protocol_sha256": expected_hashes["protocol_sha256"],
            "runner_sha256": expected_hashes["runner_sha256"],
            "summarizer_sha256": sha256_file(Path(__file__)),
            "reference_manifest_sha256": manifest_hash,
        },
    }

    args.out_root.mkdir(parents=True, exist_ok=True)
    with (args.out_root / "reference_utilities.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row_records[0]))
        writer.writeheader()
        writer.writerows(row_records)
    (args.out_root / "SUMMARY_V1.json").write_text(
        json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    artifact_manifest = {
        "status": "complete_evidence_artifact_manifest",
        "file_count": len(artifact_hashes),
        "files": artifact_hashes,
    }
    (args.out_root / "ARTIFACT_MANIFEST_V1.json").write_text(
        json.dumps(artifact_manifest, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report_lines = [
        "# TabLLM admissible-reference space audit — results v1",
        "",
        f"Frozen verdict: **{verdict}**.",
        "",
        f"Canonical macro utility: `{canonical:+.4f}` AUROC.",
        (
            "Combinatorial macro reference envelope: "
            f"`[{lower:+.4f}, {upper:+.4f}]` (span `{span:.4f}`)."
        ),
        (
            "Independent-uniform product-space SD: "
            f"`{analytic_uniform_sd:.4f}`; 95% Monte Carlo interval "
            f"`[{monte_carlo_quantiles['0.025']:+.4f}, "
            f"{monte_carlo_quantiles['0.975']:+.4f}]`."
        ),
        f"Canonical percentile in that product space: `{np.mean(monte_carlo <= canonical):.3f}`.",
        "",
        "The envelope is a prespecified sensitivity summary over the frozen",
        "candidate library. Its extremal members are not selected as revised",
        "references, and the result is limited to this tightly matched anonymous-",
        "identifier space and fixed nine-dataset panel.",
        "",
        "## Dataset envelopes",
        "",
        "| Dataset | Canonical | Minimum | Maximum | Span | Positive refs |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for dataset in DATASETS:
        item = dataset_summaries[dataset]
        report_lines.append(
            f"| {dataset} | {item['canonical_utility']:+.4f} | "
            f"{item['minimum_utility']:+.4f} | {item['maximum_utility']:+.4f} | "
            f"{item['span']:.4f} | {item['positive_reference_count']}/24 |"
        )
    (args.out_root / "RESULTS_V1.md").write_text(
        "\n".join(report_lines) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
