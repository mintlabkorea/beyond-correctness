#!/usr/bin/env python3
"""Validate and summarize the frozen generic-lexical TabLLM zero-shot audit."""

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


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "iclr_latex_v3/TABLLM_GENERIC_LEXICAL_ZERO_SHOT_FREEZE_V1.md"
RUNNER = ROOT / "scripts/run_tabllm_generic_lexical_zero_v1.py"
BASE_RUNNER = ROOT / "scripts/run_tabllm_retrospective_audit_v1.py"
SUMMARIZER = Path(__file__).resolve()
DATASETS = (
    "bank", "blood", "calhousing", "car", "creditg",
    "diabetes", "heart", "income", "jungle",
)
SEEDS = (42, 1024, 0, 1, 32)
GENERIC_ARM = "list_generic_lexical"
INTENDED_ARM = "list_template"
ANONYMOUS_ARM = "list_stable_anonymous"
MATERIALITY = 0.02
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 20260907


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def finite_float(value: Any, label: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise RuntimeError(f"non-finite {label}: {value}")
    return number


def validate_prediction_file(path: Path, metrics: dict[str, Any], dataset: str) -> None:
    if sha256_file(path) != metrics["predictions_sha256"]:
        raise RuntimeError(f"prediction hash mismatch: {path}")
    seen: set[int] = set()
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("dataset") != dataset or record.get("arm") != GENERIC_ARM:
                raise RuntimeError(f"prediction identity mismatch: {path}")
            row_id = int(record["row_id"])
            if row_id in seen:
                raise RuntimeError(f"duplicate row_id {row_id}: {path}")
            seen.add(row_id)
            probabilities = np.asarray(record["class_probabilities"], dtype=float)
            if not np.all(np.isfinite(probabilities)):
                raise RuntimeError(f"non-finite probabilities: {path}/{row_id}")
            if abs(float(probabilities.sum()) - 1.0) > 1e-6:
                raise RuntimeError(f"unnormalized probabilities: {path}/{row_id}")
            if len(str(record.get("prompt_sha256", ""))) != 64:
                raise RuntimeError(f"invalid prompt hash: {path}/{row_id}")
    if len(seen) != int(metrics["n_scored_union"]):
        raise RuntimeError(f"prediction row count mismatch: {path}")


def validate_generic(
    path: Path,
    payload: dict[str, Any],
    intended: dict[str, Any],
    anonymous: dict[str, Any],
    dataset: str,
) -> None:
    expected_hashes = {
        "protocol_sha256": sha256_file(PROTOCOL),
        "runner_sha256": sha256_file(RUNNER),
        "base_runner_sha256": sha256_file(BASE_RUNNER),
    }
    for key, expected in expected_hashes.items():
        if payload.get(key) != expected:
            raise RuntimeError(f"{dataset}: {key} mismatch")
    if payload.get("analysis_status") != "frozen_generic_lexical_zero_shot_evidence":
        raise RuntimeError(f"{dataset}: inadmissible analysis status")
    if payload.get("dataset") != dataset or payload.get("arm") != GENERIC_ARM:
        raise RuntimeError(f"{dataset}: generic identity mismatch")
    if payload.get("reference_family") != "generic_lexical":
        raise RuntimeError(f"{dataset}: reference family mismatch")
    if not all(payload.get("template_audit", {}).values()):
        raise RuntimeError(f"{dataset}: template audit failed")
    scoring = payload.get("scoring", {})
    expected_scoring = {
        "length_normalization": 1,
        "max_input_tokens": 1024,
        "test_split_seeds": list(SEEDS),
        "test_fraction": 0.2,
        "batch_size": 16,
        "device": "cuda:3",
    }
    if scoring != expected_scoring:
        raise RuntimeError(f"{dataset}: scoring contract mismatch")
    if payload.get("protobuf_python_implementation") != "python":
        raise RuntimeError(f"{dataset}: protobuf compatibility setting missing")
    for reused_name, reused in (("intended", intended), ("anonymous", anonymous)):
        for key in (
            "tabllm_commit", "tfew_execution_commit",
            "checkpoint_source_tfew_commit", "raw_and_serialization_tree_sha256",
            "ia3_checkpoint_sha256", "versions", "n_full", "n_scored_union", "choices",
        ):
            if payload.get(key) != reused.get(key):
                raise RuntimeError(f"{dataset}: {key} differs from {reused_name}")
        for seed in SEEDS:
            observed = payload["metrics"][str(seed)]
            expected = reused["metrics"][str(seed)]
            for key in ("n_test", "test_row_ids_sha256"):
                if observed.get(key) != expected.get(key):
                    raise RuntimeError(
                        f"{dataset}/{seed}: {key} differs from {reused_name}"
                    )
            finite_float(observed["auc"], f"{dataset}/{seed}/auc")
    validate_prediction_file(path.parent / "predictions.jsonl.gz", payload, dataset)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generic-root", type=Path, required=True)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument(
        "--out-root", type=Path,
        default=ROOT / "experiments/tabllm_generic_lexical_zero_v1",
    )
    args = parser.parse_args()

    rows: list[dict[str, Any]] = []
    input_paths: list[Path] = []
    for dataset in DATASETS:
        generic_path = args.generic_root / GENERIC_ARM / dataset / "metrics.json"
        intended_path = args.canonical_root / INTENDED_ARM / dataset / "metrics.json"
        anonymous_path = args.canonical_root / ANONYMOUS_ARM / dataset / "metrics.json"
        generic = load_json(generic_path)
        intended = load_json(intended_path)
        anonymous = load_json(anonymous_path)
        validate_generic(generic_path, generic, intended, anonymous, dataset)
        intended_auc = finite_float(intended["metrics"]["mean"]["auc"], "intended")
        anonymous_auc = finite_float(anonymous["metrics"]["mean"]["auc"], "anonymous")
        generic_auc = finite_float(generic["metrics"]["mean"]["auc"], "generic")
        u_anonymous = intended_auc - anonymous_auc
        u_generic = intended_auc - generic_auc
        rows.append({
            "dataset": dataset,
            "intended_auc": intended_auc,
            "stable_anonymous_auc": anonymous_auc,
            "generic_lexical_auc": generic_auc,
            "u_anonymous": u_anonymous,
            "u_generic": u_generic,
            "delta_u_generic_minus_anonymous": u_generic - u_anonymous,
            "utility_sign_changed": (u_anonymous > 0) != (u_generic > 0),
            "wall_seconds": finite_float(generic["wall_seconds"], "wall_seconds"),
        })
        input_paths.extend([
            generic_path, generic_path.parent / "predictions.jsonl.gz",
            intended_path, anonymous_path,
        ])

    u_anonymous_values = np.asarray([row["u_anonymous"] for row in rows])
    u_generic_values = np.asarray([row["u_generic"] for row in rows])
    delta_values = u_generic_values - u_anonymous_values
    macro_anonymous = float(u_anonymous_values.mean())
    macro_generic = float(u_generic_values.mean())
    delta = float(delta_values.mean())
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    indices = rng.integers(0, len(DATASETS), size=(BOOTSTRAP_DRAWS, len(DATASETS)))
    bootstrap_delta = delta_values[indices].mean(axis=1)
    interval = np.percentile(bootstrap_delta, [2.5, 97.5]).tolist()

    if macro_anonymous > 0 and macro_generic > 0 and abs(delta) < MATERIALITY:
        verdict = "MACRO_STABLE_ACROSS_ANONYMOUS_AND_GENERIC_LEXICAL"
    elif not (macro_anonymous > 0 and macro_generic > 0):
        verdict = "MACRO_SIGN_DEPENDS_ON_REFERENCE_FAMILY"
    else:
        verdict = "MATERIAL_MACRO_REFERENCE_FAMILY_SHIFT"

    summary = {
        "status": "complete_validated_generic_lexical_zero_shot_audit",
        "verdict": verdict,
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "protocol_sha256": sha256_file(PROTOCOL),
        "runner_sha256": sha256_file(RUNNER),
        "base_runner_sha256": sha256_file(BASE_RUNNER),
        "summarizer_sha256": sha256_file(SUMMARIZER),
        "datasets": list(DATASETS),
        "new_evidence_group_count": len(rows),
        "all_new_groups_validated": True,
        "macro": {
            "u_anonymous": macro_anonymous,
            "u_generic_lexical": macro_generic,
            "delta_u_generic_minus_anonymous": delta,
            "absolute_delta": abs(delta),
            "materiality_scale": MATERIALITY,
            "paired_dataset_bootstrap_95pct": interval,
            "bootstrap_draws": BOOTSTRAP_DRAWS,
            "bootstrap_seed": BOOTSTRAP_SEED,
        },
        "dataset_sign_change_count": sum(row["utility_sign_changed"] for row in rows),
        "total_scoring_wall_seconds": sum(row["wall_seconds"] for row in rows),
        "rows": rows,
    }

    args.out_root.mkdir(parents=True, exist_ok=True)
    summary_path = args.out_root / "SUMMARY_V1.json"
    csv_path = args.out_root / "DATASET_RESULTS_V1.csv"
    report_path = args.out_root / "RESULTS_V1.md"
    summary_path.write_text(
        json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "# TabLLM generic-lexical zero-shot reference audit — results v1",
        "",
        f"Frozen verdict: **{verdict}**.",
        "",
        f"- Stable-anonymous macro utility: `{macro_anonymous:+.6f}`",
        f"- Generic-lexical macro utility: `{macro_generic:+.6f}`",
        f"- Generic-minus-anonymous utility shift: `{delta:+.6f}`",
        f"- Paired dataset-bootstrap 95% interval: `[{interval[0]:+.6f}, {interval[1]:+.6f}]`",
        f"- Dataset-level utility sign changes: `{summary['dataset_sign_change_count']}/9`",
        f"- New scoring wall time: `{summary['total_scoring_wall_seconds']:.1f}` seconds",
        "",
        "| Dataset | u(anonymous) | u(generic lexical) | Shift | Sign changed |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['dataset']} | {row['u_anonymous']:+.6f} | "
            f"{row['u_generic']:+.6f} | "
            f"{row['delta_u_generic_minus_anonymous']:+.6f} | "
            f"{str(row['utility_sign_changed'])} |"
        )
    lines.extend([
        "",
        "This fixed-panel zero-shot audit does not test target-support attenuation",
        "or invariance over arbitrary lexical reference families.",
    ])
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    manifest_entries = []
    for path in sorted(set(input_paths + [
        PROTOCOL, RUNNER, BASE_RUNNER, SUMMARIZER,
        summary_path, csv_path, report_path,
    ])):
        try:
            label = str(path.relative_to(ROOT))
        except ValueError:
            label = str(path)
        manifest_entries.append({
            "path": label,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    manifest = {
        "status": "complete_artifact_manifest",
        "entries": manifest_entries,
    }
    (args.out_root / "ARTIFACT_MANIFEST_V1.json").write_text(
        json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
