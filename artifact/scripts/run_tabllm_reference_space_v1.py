#!/usr/bin/env python3
"""Score a frozen space of tightly matched stable-anonymous TabLLM references."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import math
import platform
import re
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
BASE_RUNNER = ROOT / "scripts/run_tabllm_retrospective_audit_v1.py"
SUMMARIZER = ROOT / "scripts/summarize_tabllm_reference_space_v1.py"
PROTOCOL = ROOT / "iclr_latex_v3/TABLLM_ADMISSIBLE_REFERENCE_SPACE_FREEZE_V1.md"
DATASETS = (
    "bank", "blood", "calhousing", "car", "creditg",
    "diabetes", "heart", "income", "jungle",
)
SEEDS = (42, 1024, 0, 1, 32)
REFERENCE_COUNT = 24
REFERENCE_IDS = tuple(f"ref_{index:02d}" for index in range(REFERENCE_COUNT))
CANONICAL_TOLERANCE = 1e-12


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BASE = load_module("tabllm_reference_space_base_v1", BASE_RUNNER)


def sha256_file(path: Path) -> str:
    return BASE.sha256_file(path)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_ints(values: list[int]) -> str:
    return hashlib.sha256(np.asarray(values, dtype=np.int64).tobytes()).hexdigest()


def template_parts(list_template: str) -> tuple[list[str], list[str]]:
    labels: list[str] = []
    tails: list[str] = []
    for line in list_template.splitlines():
        match = re.match(r"^- (.*?): (?=\$\{)(.*)$", line)
        if match is None:
            raise RuntimeError(f"unexpected List Template line: {line!r}")
        labels.append(match.group(1))
        tails.append(match.group(2))
    if not labels:
        raise RuntimeError("empty List Template")
    return labels, tails


def dataset_seed(dataset: str) -> int:
    digest = hashlib.sha256(
        f"tabllm-reference-space-v1/{dataset}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], byteorder="little", signed=False)


def reference_permutations(dataset: str, feature_count: int) -> list[tuple[int, ...]]:
    if math.factorial(feature_count) < REFERENCE_COUNT:
        raise RuntimeError(
            f"{dataset} has fewer than {REFERENCE_COUNT} possible bijections"
        )
    identity = tuple(range(feature_count))
    permutations = [identity]
    seen = {identity}
    rng = np.random.default_rng(dataset_seed(dataset))
    while len(permutations) < REFERENCE_COUNT:
        candidate = tuple(int(value) for value in rng.permutation(feature_count))
        if candidate not in seen:
            seen.add(candidate)
            permutations.append(candidate)
    return permutations


def anonymous_template(list_template: str, permutation: tuple[int, ...]) -> str:
    labels, tails = template_parts(list_template)
    if len(permutation) != len(labels) or set(permutation) != set(range(len(labels))):
        raise RuntimeError("invalid anonymous-identifier permutation")
    return "\n".join(
        f"- feature_{permutation[index] + 1:03d}: {tail}"
        for index, tail in enumerate(tails)
    )


def reference_manifest(tabllm: Any, tabllm_root: Path) -> dict[str, Any]:
    datasets: dict[str, Any] = {}
    for dataset in DATASETS:
        template = getattr(tabllm, f"template_{dataset}_list")
        labels, tails = template_parts(template)
        permutations = reference_permutations(dataset, len(labels))
        candidates: dict[str, Any] = {}
        templates: list[str] = []
        identifier_set = [f"feature_{index + 1:03d}" for index in range(len(labels))]
        for reference_id, permutation in zip(REFERENCE_IDS, permutations):
            rendered = anonymous_template(template, permutation)
            rendered_labels, rendered_tails = template_parts(rendered)
            if rendered_tails != tails:
                raise RuntimeError(f"placeholder/tail mutation: {dataset}/{reference_id}")
            if sorted(rendered_labels) != identifier_set:
                raise RuntimeError(f"identifier-set mutation: {dataset}/{reference_id}")
            if any(label in set(labels) for label in rendered_labels):
                raise RuntimeError(f"original label retained: {dataset}/{reference_id}")
            templates.append(rendered)
            candidates[reference_id] = {
                "line_to_identifier_index_zero_based": list(permutation),
                "template_sha256": sha256_text(rendered),
            }
        if templates[0] != BASE.anonymous_template(template):
            raise RuntimeError(f"canonical template mismatch: {dataset}")
        if len(set(templates)) != REFERENCE_COUNT:
            raise RuntimeError(f"non-unique templates: {dataset}")

        frame = BASE.build_full_dataset(tabllm, tabllm_root, dataset)
        splits = BASE.test_rows(frame)
        union = sorted(set().union(*(set(rows) for rows in splits.values())))
        datasets[dataset] = {
            "feature_count": len(labels),
            "possible_bijection_count": math.factorial(len(labels)),
            "complete_space": math.factorial(len(labels)) == REFERENCE_COUNT,
            "original_label_sha256": sha256_text("\n".join(labels)),
            "placeholder_and_tail_sha256": sha256_text("\n".join(tails)),
            "identifier_set": identifier_set,
            "candidate_count": len(candidates),
            "unique_template_count": len(set(templates)),
            "n_full": len(frame),
            "test_sizes": {str(seed): len(splits[seed]) for seed in SEEDS},
            "test_row_ids_sha256": {
                str(seed): sha256_ints(splits[seed]) for seed in SEEDS
            },
            "test_union_size": len(union),
            "test_union_sha256": sha256_ints(union),
            "candidates": candidates,
        }
    return {
        "status": "frozen_reference_manifest_pre_scoring",
        "generator": {
            "algorithm": "numpy.default_rng_PCG64_unique_permutations",
            "seed_rule": (
                "uint64_little_endian_first8_sha256_bytes_of_"
                "tabllm-reference-space-v1/<dataset>"
            ),
            "reference_count": REFERENCE_COUNT,
            "canonical_reference": "ref_00",
            "numpy_version": np.__version__,
        },
        "protocol_sha256": sha256_file(PROTOCOL),
        "runner_sha256": sha256_file(Path(__file__)),
        "summarizer_sha256": sha256_file(SUMMARIZER),
        "base_runner_sha256": sha256_file(BASE_RUNNER),
        "tabllm_commit": BASE.git_commit(tabllm_root),
        "datasets": datasets,
        "admissibility_audit": {
            "all_candidate_counts_exact": all(
                item["candidate_count"] == REFERENCE_COUNT
                for item in datasets.values()
            ),
            "all_templates_unique_within_dataset": all(
                item["unique_template_count"] == REFERENCE_COUNT
                for item in datasets.values()
            ),
            "canonical_matches_prior_builder": True,
            "same_identifier_set_within_dataset": True,
            "same_line_order_placeholders_punctuation_and_values": True,
            "original_feature_labels_removed": True,
            "within_dataset_identity_stable_across_rows": True,
        },
    }


def build_notes(
    tabllm: Any,
    frame: Any,
    dataset: str,
    permutation: tuple[int, ...],
) -> list[str]:
    template = getattr(tabllm, f"template_{dataset}_list")
    config = getattr(tabllm, f"template_config_{dataset}_list")
    generator = tabllm.NoteTemplate(anonymous_template(template, permutation), **config)
    return [
        tabllm.NoteGenerator.clean_note(generator.substitute(row))
        for _, row in frame.iterrows()
    ]


def validate_cached_cell(
    path: Path, protocol_hash: str, runner_hash: str, manifest_hash: str
) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "protocol_sha256": protocol_hash,
        "runner_sha256": runner_hash,
        "reference_manifest_sha256": manifest_hash,
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise RuntimeError(f"stale cached cell {path}: {key}")
    if payload.get("analysis_status") != "frozen_reference_space_evidence":
        raise RuntimeError(f"inadmissible cached cell: {path}")
    return payload


def assert_canonical_gate(
    out_root: Path, protocol_hash: str, runner_hash: str, manifest_hash: str
) -> None:
    for dataset in DATASETS:
        path = out_root / "ref_00" / dataset / "metrics.json"
        if not path.is_file():
            raise RuntimeError(f"canonical gate incomplete: {path}")
        payload = validate_cached_cell(
            path, protocol_hash, runner_hash, manifest_hash
        )
        audit = payload.get("canonical_reproduction_audit", {})
        if audit.get("status") != "canonical_reproduction_pass":
            raise RuntimeError(f"canonical gate failed: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tabllm-root", type=Path, required=True)
    parser.add_argument("--tfew-root", type=Path, required=True)
    parser.add_argument("--checkpoint-source-root", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument(
        "--out-root", type=Path,
        default=ROOT / "experiments/tabllm_reference_space_v1/evidence_v1",
    )
    parser.add_argument("--datasets", nargs="+", choices=DATASETS, default=list(DATASETS))
    parser.add_argument(
        "--reference-ids", nargs="+", choices=REFERENCE_IDS,
        default=list(REFERENCE_IDS),
    )
    parser.add_argument("--device", default="cuda:1")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--smoke-examples", type=int, default=0)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    if len(args.datasets) != len(set(args.datasets)):
        raise ValueError("datasets must be unique")
    if len(args.reference_ids) != len(set(args.reference_ids)):
        raise ValueError("reference IDs must be unique")
    if not args.smoke_examples and args.device != "cuda:1":
        raise ValueError("the frozen evidence device is cuda:1")

    sys.path.insert(0, str(args.tabllm_root))
    tabllm = load_module(
        "tabllm_reference_space_data_v1",
        args.tabllm_root / "create_external_datasets.py",
    )
    generated_manifest = reference_manifest(tabllm, args.tabllm_root)
    args.out_root.mkdir(parents=True, exist_ok=True)
    if args.prepare_only:
        path = args.out_root / "REFERENCE_MANIFEST_V1.json"
        path.write_text(
            json.dumps(generated_manifest, indent=1, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({
            "status": "prepare_only_pass",
            "manifest": str(path),
            "manifest_sha256": sha256_file(path),
            "admissibility_audit": generated_manifest["admissibility_audit"],
        }, indent=1, sort_keys=True))
        return 0
    if args.manifest is None or not args.manifest.is_file():
        raise ValueError("--manifest is required for scoring")
    frozen_manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if frozen_manifest != generated_manifest:
        raise RuntimeError("generated reference manifest differs from frozen manifest")

    protocol_hash = sha256_file(PROTOCOL)
    runner_hash = sha256_file(Path(__file__))
    manifest_hash = sha256_file(args.manifest)
    provenance = {
        "analysis_status": (
            "engineering_smoke_inadmissible"
            if args.smoke_examples else "frozen_reference_space_evidence"
        ),
        "tabllm_commit": BASE.git_commit(args.tabllm_root),
        "tfew_execution_commit": BASE.git_commit(args.tfew_root),
        "checkpoint_source_tfew_commit": BASE.git_commit(args.checkpoint_source_root),
        "protocol_sha256": protocol_hash,
        "runner_sha256": runner_hash,
        "base_runner_sha256": sha256_file(BASE_RUNNER),
        "reference_manifest_sha256": manifest_hash,
        "ia3_checkpoint_sha256": sha256_file(args.checkpoint),
        "model_path": str(args.model_path.resolve()),
        "versions": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "numpy": np.__version__,
            "transformers": importlib.metadata.version("transformers"),
            "datasets": importlib.metadata.version("datasets"),
            "scikit_learn": importlib.metadata.version("scikit-learn"),
        },
        "scoring": {
            "length_normalization": 1,
            "max_input_tokens": 1024,
            "test_split_seeds": list(SEEDS),
            "test_fraction": 0.20,
            "batch_size": args.batch_size,
            "device": args.device,
        },
    }

    prepared: dict[str, Any] = {}
    for dataset in args.datasets:
        frame = BASE.build_full_dataset(tabllm, args.tabllm_root, dataset)
        splits = BASE.test_rows(frame)
        union = sorted(set().union(*(set(rows) for rows in splits.values())))
        if args.smoke_examples:
            union = union[:args.smoke_examples]
        manifest_item = frozen_manifest["datasets"][dataset]
        if not args.smoke_examples:
            if len(union) != manifest_item["test_union_size"]:
                raise RuntimeError(f"test union size mismatch: {dataset}")
            if sha256_ints(union) != manifest_item["test_union_sha256"]:
                raise RuntimeError(f"test union membership mismatch: {dataset}")
            for seed in SEEDS:
                if sha256_ints(splits[seed]) != manifest_item[
                    "test_row_ids_sha256"
                ][str(seed)]:
                    raise RuntimeError(f"test split membership mismatch: {dataset}/{seed}")
        prepared[dataset] = (frame, splits, union)

    existing_count = 0
    for reference_id in args.reference_ids:
        for dataset in args.datasets:
            path = args.out_root / reference_id / dataset / "metrics.json"
            if path.is_file():
                if not args.smoke_examples:
                    validate_cached_cell(path, protocol_hash, runner_hash, manifest_hash)
                existing_count += 1
    if existing_count == len(args.reference_ids) * len(args.datasets):
        print(json.dumps({
            "status": "cached",
            "cells": existing_count,
            "out_root": str(args.out_root),
        }))
        return 0

    tokenizer, model, checkpoint_audit = BASE.load_model(
        args.model_path, args.tfew_root, args.checkpoint, args.device
    )
    provenance["checkpoint_audit"] = checkpoint_audit

    completed_now = 0
    for reference_id in args.reference_ids:
        if reference_id != "ref_00" and not args.smoke_examples:
            assert_canonical_gate(
                args.out_root, protocol_hash, runner_hash, manifest_hash
            )
        for dataset in args.datasets:
            out = args.out_root / reference_id / dataset
            metrics_path = out / "metrics.json"
            if metrics_path.is_file():
                continue
            frame, splits, union = prepared[dataset]
            permutation = tuple(
                frozen_manifest["datasets"][dataset]["candidates"][reference_id][
                    "line_to_identifier_index_zero_based"
                ]
            )
            notes = build_notes(tabllm, frame, dataset, permutation)
            prompts = [
                notes[row_id] + "\n\n" + BASE.QUESTIONS[dataset]
                for row_id in union
            ]
            started = time.perf_counter()
            probabilities = BASE.score_texts(
                tokenizer, model, prompts, BASE.CHOICES[dataset],
                args.batch_size, args.device,
            )
            labels = frame.loc[union, "label"].astype(int).to_numpy()
            row_ids = np.asarray(union, dtype=np.int64)
            out.mkdir(parents=True, exist_ok=True)
            predictions_path = out / "predictions.jsonl.gz"
            with predictions_path.open("wb") as raw_handle, gzip.GzipFile(
                fileobj=raw_handle, mode="wb", mtime=0
            ) as gzip_handle, io.TextIOWrapper(
                gzip_handle, encoding="utf-8"
            ) as handle:
                for index, row_id in enumerate(row_ids):
                    handle.write(json.dumps({
                        "dataset": dataset,
                        "reference_id": reference_id,
                        "row_id": int(row_id),
                        "label": int(labels[index]),
                        "prediction": int(np.argmax(probabilities[index])),
                        "class_probabilities": probabilities[index].tolist(),
                        "prompt_sha256": sha256_text(prompts[index]),
                    }, sort_keys=True) + "\n")
            metrics = (
                {"status": "withheld_for_smoke"}
                if args.smoke_examples
                else BASE.metrics_for_splits(labels, row_ids, probabilities, splits)
            )
            canonical_audit = None
            if reference_id == "ref_00" and not args.smoke_examples:
                frozen_path = args.canonical_root / dataset / "metrics.json"
                frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
                comparisons: dict[str, Any] = {}
                maximum_error = 0.0
                for seed in SEEDS:
                    observed = metrics[str(seed)]
                    expected = frozen["metrics"][str(seed)]
                    error = abs(float(observed["auc"]) - float(expected["auc"]))
                    maximum_error = max(maximum_error, error)
                    if observed["test_row_ids_sha256"] != expected[
                        "test_row_ids_sha256"
                    ]:
                        raise RuntimeError(
                            f"canonical membership mismatch: {dataset}/{seed}"
                        )
                    comparisons[str(seed)] = {
                        "observed_auc": observed["auc"],
                        "frozen_auc": expected["auc"],
                        "absolute_auc_error": error,
                        "test_row_ids_sha256": observed["test_row_ids_sha256"],
                    }
                canonical_audit = {
                    "status": (
                        "canonical_reproduction_pass"
                        if maximum_error <= CANONICAL_TOLERANCE
                        else "canonical_reproduction_fail"
                    ),
                    "maximum_absolute_auc_error": maximum_error,
                    "tolerance": CANONICAL_TOLERANCE,
                    "frozen_metrics_sha256": sha256_file(frozen_path),
                    "comparisons": comparisons,
                }
            payload = {
                **provenance,
                "dataset": dataset,
                "reference_id": reference_id,
                "permutation": list(permutation),
                "template_sha256": frozen_manifest["datasets"][dataset][
                    "candidates"
                ][reference_id]["template_sha256"],
                "choices": list(BASE.CHOICES[dataset]),
                "n_full": len(frame),
                "n_scored_union": len(union),
                "predictions_sha256": sha256_file(predictions_path),
                "wall_seconds": round(time.perf_counter() - started, 3),
                "metrics": metrics,
            }
            if canonical_audit is not None:
                payload["canonical_reproduction_audit"] = canonical_audit
            metrics_path.write_text(
                json.dumps(payload, indent=1, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            print(json.dumps({
                "dataset": dataset,
                "reference_id": reference_id,
                "wall_seconds": payload["wall_seconds"],
                "canonical_status": (
                    None if canonical_audit is None else canonical_audit["status"]
                ),
            }), flush=True)
            completed_now += 1
            if canonical_audit is not None and canonical_audit[
                "status"
            ] != "canonical_reproduction_pass":
                raise RuntimeError(f"canonical reproduction failed: {dataset}")

    print(json.dumps({
        "status": "complete",
        "completed_now": completed_now,
        "total_requested": len(args.reference_ids) * len(args.datasets),
        "out_root": str(args.out_root),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
