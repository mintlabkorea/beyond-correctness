#!/usr/bin/env python3
"""Exact-style zero-shot TabLLM audit with a stable-anonymous reference.

The script uses the released TabLLM serialization code and released T-Few
IA3 checkpoint.  It scores the union of the five published 20% test splits
once, then reconstructs each split's AUROC without redundant model inference.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from datasets import Dataset
from sklearn.metrics import accuracy_score, roc_auc_score
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "iclr_latex_v3/TABLLM_RETROSPECTIVE_AUDIT_FREEZE_V1.md"
DATASETS = (
    "bank", "blood", "calhousing", "car", "creditg",
    "diabetes", "heart", "income", "jungle",
)
ARMS = ("list_template", "list_permuted_names", "list_only_values", "list_stable_anonymous")
SEEDS = (42, 1024, 0, 1, 32)
QUESTIONS = {
    "bank": "Does this client subscribe to a term deposit? Yes or no?\nAnswer: ",
    "blood": "Did the person donate blood? Yes or no?\nAnswer: ",
    "calhousing": "Is this house block valuable? Yes or no?\nAnswer: ",
    "car": "How would you rate the decision to buy this car? Unacceptable, acceptable, good or very good?\nAnswer: ",
    "creditg": "Does this person receive a credit? Yes or no?\nAnswer: ",
    "diabetes": "Does this patient have diabetes? Yes or no?\nAnswer: ",
    "heart": "Does the coronary angiography of this patient show a heart disease? Yes or no?\nAnswer: ",
    "income": "Does this person earn more than 50000 dollars per year? Yes or no?\nAnswer: ",
    "jungle": "Does the white player win this two pieces endgame of Jungle Chess? Yes or no?\nAnswer: ",
}
CHOICES = {
    **{dataset: ("No", "Yes") for dataset in DATASETS if dataset != "car"},
    "car": ("Unacceptable", "Acceptable", "Good", "Very good"),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit(path: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
    ).strip()


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def aggregate_tree_hash(root: Path, paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def anonymous_template(list_template: str) -> str:
    lines = list_template.splitlines()
    output = []
    for index, line in enumerate(lines, start=1):
        replaced = re.sub(
            r"^- .*?: (?=\$\{)", f"- feature_{index:03d}: ", line, count=1
        )
        if replaced == line:
            raise RuntimeError(f"could not anonymize list line: {line!r}")
        output.append(replaced)
    return "\n".join(output)


def build_full_dataset(tabllm: Any, tabllm_root: Path, dataset: str) -> pd.DataFrame:
    splits = tabllm.load_train_validation_test(dataset, tabllm_root / "datasets" / dataset)
    frame = pd.concat(list(splits.values()), ignore_index=True)
    frame["row_id"] = np.arange(len(frame), dtype=np.int64)
    return frame


def build_notes(tabllm: Any, frame: pd.DataFrame, dataset: str, arm: str) -> list[str]:
    if arm == "list_template":
        suffix = "list"
    elif arm == "list_permuted_names":
        suffix = "list_permuted"
    elif arm == "list_only_values":
        suffix = "list_values"
    elif arm == "list_stable_anonymous":
        suffix = "list"
    else:
        raise ValueError(arm)
    template = getattr(tabllm, f"template_{dataset}_{suffix}")
    config = getattr(tabllm, f"template_config_{dataset}_{suffix}")
    if arm == "list_stable_anonymous":
        template = anonymous_template(template)
    generator = tabllm.NoteTemplate(template, **config)
    return [
        tabllm.NoteGenerator.clean_note(generator.substitute(row))
        for _, row in frame.iterrows()
    ]


def test_rows(frame: pd.DataFrame) -> dict[int, list[int]]:
    # Mirrors datasets.Dataset.train_test_split(test_size=.20, seed=seed) in
    # CustomCategoricalReader.  The second 50/50 split only reorders the same
    # validation rows and therefore does not change AUROC membership.
    dataset = Dataset.from_dict({"row_id": frame["row_id"].astype(int).tolist()})
    return {
        seed: [int(value) for value in dataset.train_test_split(
            test_size=0.20, seed=seed
        )["test"]["row_id"]]
        for seed in SEEDS
    }


def load_model(model_path: Path, tfew_root: Path, checkpoint: Path, device: str):
    sys.path.insert(0, str(tfew_root))
    from src.models.modify_model import modify_transformer

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    tokenizer.model_max_length = 1024
    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_path, low_cpu_mem_usage=True, torch_dtype=torch.bfloat16
    )
    config = SimpleNamespace(
        lora_scaling_rank=1,
        lora_rank=0,
        lora_init_scale=0.0,
        lora_modules=".*SelfAttention|.*EncDecAttention|.*DenseReluDense",
        lora_layers="k|v|wi_1.*",
        trainable_param_names=".*lora_b.*",
        model_modifier="lora",
    )
    model = modify_transformer(model, config)
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)
    result = model.load_state_dict(state, strict=False)
    if result.unexpected_keys:
        raise RuntimeError(f"unexpected IA3 checkpoint keys: {result.unexpected_keys[:10]}")
    checkpoint_keys = set(state)
    if not checkpoint_keys or any(not key.endswith("lora_b") for key in checkpoint_keys):
        raise RuntimeError("checkpoint is not the released IA3-only state")
    # ``modify_transformer`` creates IA3 scales in the process default dtype
    # even when the base T0 weights were loaded as bfloat16.  Cast the complete
    # modified module after loading the released checkpoint so matrix operands
    # share the same dtype (the released T-Few run also used bfloat16 compute).
    model.to(device=device, dtype=torch.bfloat16)
    model.eval()
    return tokenizer, model, {
        "checkpoint_parameter_count": int(sum(value.numel() for value in state.values())),
        "checkpoint_key_count": len(state),
        "missing_base_model_key_count": len(result.missing_keys),
    }


@torch.inference_mode()
def score_texts(
    tokenizer: Any,
    model: Any,
    texts: list[str],
    choices: tuple[str, ...],
    batch_size: int,
    device: str,
) -> np.ndarray:
    choice_tokens = tokenizer(
        list(choices), return_tensors="pt", padding=True, truncation=True,
        add_special_tokens=True,
    ).input_ids
    num_choices = len(choices)
    all_probabilities = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        encoded = tokenizer(
            batch, return_tensors="pt", padding=True, truncation=True,
            max_length=1024, add_special_tokens=True,
        )
        input_ids = encoded.input_ids.to(device)
        attention = encoded.attention_mask.to(device)
        bs = len(batch)
        choices_ids = choice_tokens.to(device).unsqueeze(0).expand(bs, -1, -1)
        flat = choices_ids.reshape(bs * num_choices, -1)
        hidden = model.encoder(input_ids=input_ids, attention_mask=attention)[0]
        hidden = hidden.unsqueeze(1).expand(-1, num_choices, -1, -1).reshape(
            bs * num_choices, hidden.shape[1], hidden.shape[2]
        )
        repeated_attention = attention.unsqueeze(1).expand(-1, num_choices, -1).reshape(
            bs * num_choices, -1
        )
        decoder_start = int(model.config.decoder_start_token_id or 0)
        decoder_input = torch.cat([
            torch.full_like(flat[:, :1], decoder_start), flat[:, :-1]
        ], dim=1)
        target = flat.masked_fill(flat == tokenizer.pad_token_id, -100)
        output = model(
            attention_mask=repeated_attention,
            encoder_outputs=[hidden],
            decoder_input_ids=decoder_input,
            decoder_attention_mask=torch.ones_like(decoder_input),
            use_cache=False,
        )
        losses = F.cross_entropy(
            output.logits.float().flatten(0, 1), target.flatten(0, 1),
            reduction="none", ignore_index=-100,
        ).view(bs, num_choices, -1)
        token_count = (choices_ids != tokenizer.pad_token_id).sum(dim=-1).clamp_min(1)
        scores = losses.sum(dim=-1) / token_count
        probabilities = torch.softmax(-scores, dim=-1)
        all_probabilities.append(probabilities.cpu().numpy().astype(np.float64))
        print(json.dumps({"scored": min(start + bs, len(texts)), "total": len(texts)}),
              flush=True)
    return np.concatenate(all_probabilities, axis=0)


def metrics_for_splits(
    labels: np.ndarray,
    row_ids: np.ndarray,
    probabilities: np.ndarray,
    splits: dict[int, list[int]],
) -> dict[str, Any]:
    lookup = {int(row_id): index for index, row_id in enumerate(row_ids)}
    output: dict[str, Any] = {}
    for seed, members in splits.items():
        positions = np.asarray([lookup[row_id] for row_id in members], dtype=int)
        y = labels[positions].astype(int)
        prob = probabilities[positions]
        prediction = np.argmax(prob, axis=1)
        if prob.shape[1] == 2:
            auc = float(roc_auc_score(y, prob[:, 1]))
        else:
            auc = float(roc_auc_score(y, prob, multi_class="ovr", average="macro"))
        output[str(seed)] = {
            "auc": auc,
            "accuracy": float(accuracy_score(y, prediction)),
            "n_test": len(y),
            "test_row_ids_sha256": hashlib.sha256(
                np.asarray(members, dtype=np.int64).tobytes()
            ).hexdigest(),
        }
    aucs = [value["auc"] for value in output.values()]
    output["mean"] = {
        "auc": float(np.mean(aucs)),
        "auc_sd_population": float(np.std(aucs, ddof=0)),
        "accuracy": float(np.mean([value["accuracy"] for value in output.values()])),
    }
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tabllm-root", type=Path, required=True)
    parser.add_argument("--tfew-root", type=Path, required=True)
    parser.add_argument("--checkpoint-source-root", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, default=ROOT / "experiments/tabllm_retrospective_audit_v1")
    parser.add_argument("--datasets", nargs="+", choices=DATASETS, default=list(DATASETS))
    parser.add_argument("--arms", nargs="+", choices=ARMS, default=list(ARMS))
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--smoke-examples", type=int, default=0)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    if len(args.arms) != len(set(args.arms)):
        raise ValueError("arms must be unique")
    sys.path.insert(0, str(args.tabllm_root))
    tabllm = load_module("tabllm_create_external_v1", args.tabllm_root / "create_external_datasets.py")

    source_paths = [
        path for path in (args.tabllm_root / "datasets").rglob("*") if path.is_file()
    ] + [
        args.tabllm_root / "create_external_datasets.py",
        args.tabllm_root / "helper/external_datasets_variables.py",
        args.tabllm_root / "helper/note_generator.py",
        args.tabllm_root / "helper/note_template.py",
    ]
    provenance = {
        "analysis_status": (
            "engineering_smoke_inadmissible" if args.smoke_examples
            else "retrospective_published_style_reproduction"
        ),
        "tabllm_commit": git_commit(args.tabllm_root),
        "tfew_execution_commit": git_commit(args.tfew_root),
        "checkpoint_source_tfew_commit": git_commit(args.checkpoint_source_root),
        "protocol_sha256": sha256_file(PROTOCOL),
        "runner_sha256": sha256_file(Path(__file__)),
        "raw_and_serialization_tree_sha256": aggregate_tree_hash(args.tabllm_root, source_paths),
        "ia3_checkpoint_sha256": sha256_file(args.checkpoint),
        "model_path": str(args.model_path.resolve()),
        "versions": {
            "python": platform.python_version(), "torch": torch.__version__,
            "numpy": np.__version__, "pandas": pd.__version__,
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
        "source_discrepancy": (
            "paper text names bigscience/T0pp once; released t011b config and "
            "released IA3 checkpoint use bigscience/T0; this audit follows code. "
            "The TabLLM repository vendors only a subset of T-Few; model "
            "modification is loaded from the corresponding complete upstream "
            "T-Few checkout recorded by tfew_execution_commit."
        ),
    }

    pending = []
    prepared: dict[str, Any] = {}
    for dataset in args.datasets:
        frame = build_full_dataset(tabllm, args.tabllm_root, dataset)
        splits = test_rows(frame)
        union = sorted(set().union(*[set(values) for values in splits.values()]))
        if args.smoke_examples:
            union = union[:args.smoke_examples]
        prepared[dataset] = (frame, splits, union)
        for arm in args.arms:
            path = args.out_root / arm / dataset / "metrics.json"
            if not path.is_file():
                pending.append((dataset, arm))
    if args.prepare_only:
        report = {}
        for dataset in args.datasets:
            frame, splits, union = prepared[dataset]
            arm_hashes = {}
            for arm in args.arms:
                notes = build_notes(tabllm, frame, dataset, arm)
                digest = hashlib.sha256()
                for note in notes:
                    digest.update(note.encode())
                    digest.update(b"\0")
                arm_hashes[arm] = digest.hexdigest()
            report[dataset] = {
                "n_full": len(frame),
                "label_counts": {
                    str(key): int(value)
                    for key, value in frame["label"].value_counts().sort_index().items()
                },
                "test_sizes": {str(seed): len(rows) for seed, rows in splits.items()},
                "n_test_union": len(union),
                "arm_note_hashes": arm_hashes,
            }
        print(json.dumps({"status": "prepare_only", "datasets": report}, sort_keys=True))
        return 0
    if not pending:
        print(json.dumps({"status": "cached", "cells": len(args.datasets) * len(args.arms)}))
        return 0

    tokenizer, model, checkpoint_audit = load_model(
        args.model_path, args.tfew_root, args.checkpoint, args.device
    )
    provenance["checkpoint_audit"] = checkpoint_audit
    for dataset, arm in pending:
        frame, splits, union = prepared[dataset]
        notes = build_notes(tabllm, frame, dataset, arm)
        prompts = [notes[row_id] + "\n\n" + QUESTIONS[dataset] for row_id in union]
        started = time.perf_counter()
        probabilities = score_texts(
            tokenizer, model, prompts, CHOICES[dataset], args.batch_size, args.device
        )
        labels = frame.loc[union, "label"].astype(int).to_numpy()
        row_ids = np.asarray(union, dtype=np.int64)
        out = args.out_root / arm / dataset
        out.mkdir(parents=True, exist_ok=True)
        predictions_path = out / "predictions.jsonl.gz"
        with gzip.open(predictions_path, "wt", encoding="utf-8") as handle:
            for index, row_id in enumerate(row_ids):
                handle.write(json.dumps({
                    "dataset": dataset, "arm": arm, "row_id": int(row_id),
                    "label": int(labels[index]),
                    "prediction": int(np.argmax(probabilities[index])),
                    "class_probabilities": probabilities[index].tolist(),
                    "prompt_sha256": hashlib.sha256(prompts[index].encode()).hexdigest(),
                }, sort_keys=True) + "\n")
        payload = {
            **provenance,
            "dataset": dataset,
            "arm": arm,
            "choices": list(CHOICES[dataset]),
            "n_full": len(frame),
            "n_scored_union": len(union),
            "predictions_sha256": sha256_file(predictions_path),
            "wall_seconds": round(time.perf_counter() - started, 3),
            "metrics": (
                {"status": "withheld_for_smoke"}
                if args.smoke_examples
                else metrics_for_splits(labels, row_ids, probabilities, splits)
            ),
        }
        (out / "metrics.json").write_text(
            json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps({"dataset": dataset, "arm": arm,
                          "wall_seconds": payload["wall_seconds"]}), flush=True)
    print(json.dumps({"status": "complete", "cells": len(pending)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
