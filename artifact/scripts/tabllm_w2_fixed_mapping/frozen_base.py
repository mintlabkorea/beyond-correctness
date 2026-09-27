#!/usr/bin/env python3
"""Standalone B200-compatible IA3 runner for the frozen TabLLM R_anon ladder.

The historical T-Few trainer depends on PyTorch-Lightning 1.5 and CUDA-era
packages that cannot execute on the B200 host.  This runner ports orchestration
only.  Its sampling, three-term loss, Adafactor schedule, step count, scoring,
and stable-anonymous serialization are frozen in
iclr_latex_v3/TABLLM_RANON_SUPPORT_LADDER_FREEZE_V1.md.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import gzip
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import os
import platform
import random
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from datasets import Dataset
from sklearn.metrics import accuracy_score, roc_auc_score
from torch.utils.data import DataLoader, Dataset as TorchDataset
from transformers import Adafactor, AutoModelForSeq2SeqLM, AutoTokenizer


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "iclr_latex_v3/TABLLM_RANON_SUPPORT_LADDER_FREEZE_V1.md"
DATASETS = (
    "bank", "blood", "calhousing", "car", "creditg",
    "diabetes", "heart", "income", "jungle",
)
ARMS = ("list_template", "list_stable_anonymous")
SHOTS = (0, 4, 32, 512)
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
TRAINABLE_PATTERN = re.compile(r".*lora_b.*")
TRAIN_BATCH_SIZE = 4
EPOCHS = 30
LEARNING_RATE = 0.003
WARMUP_RATIO = 0.06
GRAD_CLIP = 1.0
MAX_LENGTH = 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_strings(values: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(value.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def sha256_ints(values: Iterable[int]) -> str:
    return hashlib.sha256(np.asarray(list(values), dtype=np.int64).tobytes()).hexdigest()


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
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def tensor_bytes(tensor: torch.Tensor) -> bytes:
    value = tensor.detach().cpu().contiguous()
    return value.view(torch.uint8).numpy().tobytes()


def state_hash(state: dict[str, torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for name in sorted(state):
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(tensor_bytes(state[name]))
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
    frame["label"] = frame["label"].astype(int)
    return frame


def build_notes(tabllm: Any, frame: pd.DataFrame, dataset: str, arm: str) -> list[str]:
    if arm not in ARMS:
        raise ValueError(arm)
    template = getattr(tabllm, f"template_{dataset}_list")
    config = getattr(tabllm, f"template_config_{dataset}_list")
    if arm == "list_stable_anonymous":
        template = anonymous_template(template)
    generator = tabllm.NoteTemplate(template, **config)
    return [
        tabllm.NoteGenerator.clean_note(generator.substitute(row))
        for _, row in frame.iterrows()
    ]


def split_members(frame: pd.DataFrame, seed: int) -> tuple[list[int], list[int]]:
    dataset = Dataset.from_dict({
        "row_id": frame["row_id"].astype(int).tolist(),
        "label": frame["label"].astype(int).tolist(),
    })
    split = dataset.train_test_split(test_size=0.20, seed=seed)
    return (
        [int(value) for value in split["train"]["row_id"]],
        [int(value) for value in split["test"]["row_id"]],
    )


def balanced_few_shot_members(
    frame: pd.DataFrame, train_row_ids: list[int], shot: int, seed: int
) -> list[int]:
    if shot == 0:
        return []
    labels = [int(frame.loc[row_id, "label"]) for row_id in train_row_ids]
    label_values = list(set(labels))  # released reader semantics for integer labels
    per_label = shot // len(label_values)
    counts = [per_label] * (len(label_values) - 1)
    counts.append(shot - sum(counts))
    selected: list[int] = []
    saved = np.random.get_state()
    np.random.seed(seed)
    for label, count in zip(label_values, counts):
        positions = [index for index, value in enumerate(labels) if value == label]
        sampled_positions = np.random.choice(positions, count).tolist()
        selected.extend(train_row_ids[int(position)] for position in sampled_positions)
    np.random.set_state(saved)
    saved = np.random.get_state()
    np.random.seed(seed)
    np.random.shuffle(selected)
    np.random.set_state(saved)
    if len(selected) != shot:
        raise RuntimeError(f"few-shot selection returned {len(selected)} != {shot}")
    return [int(value) for value in selected]


def verify_split_manifest(
    split_manifest: dict[str, Any], dataset: str, seed: int, test_row_ids: list[int]
) -> None:
    expected = split_manifest["datasets"][dataset]["test_row_ids"][str(seed)]
    if [int(value) for value in expected] != test_row_ids:
        raise RuntimeError(f"frozen test membership mismatch for {dataset}/seed{seed}")


def set_seeds(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


class PreparedTrainDataset(TorchDataset):
    def __init__(
        self,
        tokenizer: Any,
        prompts: list[str],
        labels: list[int],
        choices: tuple[str, ...],
        row_ids: list[int],
    ) -> None:
        self.input_ids = [
            tokenizer(
                prompt, return_tensors="pt", truncation=True,
                max_length=MAX_LENGTH, add_special_tokens=True,
            ).input_ids.squeeze(0)
            for prompt in prompts
        ]
        self.choice_ids = [
            tokenizer(
                choice, return_tensors="pt", truncation=True,
                add_special_tokens=True,
            ).input_ids.squeeze(0)
            for choice in choices
        ]
        self.target_ids = [self.choice_ids[int(label)] for label in labels]
        self.labels = [int(value) for value in labels]
        self.row_ids = [int(value) for value in row_ids]

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, index: int) -> tuple[Any, ...]:
        return (
            self.input_ids[index], self.target_ids[index], self.choice_ids,
            self.labels[index], self.row_ids[index],
        )


def make_collate(pad_token_id: int):
    def collate(batch: list[tuple[Any, ...]]) -> dict[str, torch.Tensor]:
        input_ids, target_ids, choice_ids, labels, row_ids = zip(*batch)
        inputs = torch.nn.utils.rnn.pad_sequence(
            input_ids, batch_first=True, padding_value=pad_token_id
        )
        targets = torch.nn.utils.rnn.pad_sequence(
            target_ids, batch_first=True, padding_value=pad_token_id
        )
        flat_choices = [choice for choices in choice_ids for choice in choices]
        num_choices = {len(choices) for choices in choice_ids}
        if len(num_choices) != 1:
            raise RuntimeError("variable answer-choice count within a batch")
        count = next(iter(num_choices))
        padded_choices = torch.nn.utils.rnn.pad_sequence(
            flat_choices, batch_first=True, padding_value=pad_token_id
        ).view(len(batch), count, -1).contiguous()
        return {
            "input_ids": inputs,
            "target_ids": targets,
            "answer_choices_ids": padded_choices,
            "labels": torch.as_tensor(labels, dtype=torch.long),
            "row_ids": torch.as_tensor(row_ids, dtype=torch.long),
        }
    return collate


def load_model(
    model_path: Path, tfew_root: Path, checkpoint: Path, device: str
) -> tuple[Any, Any, dict[str, torch.Tensor], dict[str, Any]]:
    sys.path.insert(0, str(tfew_root))
    from src.models.modify_model import modify_transformer

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    tokenizer.model_max_length = MAX_LENGTH
    # The released compatibility scorer loads the base T0 weights as bfloat16.
    # IA3 tensors are inserted afterward in FP32, preserving master precision
    # for Adafactor updates while forward passes use bfloat16 autocast.
    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_path, low_cpu_mem_usage=True, torch_dtype=torch.bfloat16
    )
    config = type("IA3Config", (), {
        "lora_scaling_rank": 1,
        "lora_rank": 0,
        "lora_init_scale": 0.0,
        "lora_modules": ".*SelfAttention|.*EncDecAttention|.*DenseReluDense",
        "lora_layers": "k|v|wi_1.*",
        "trainable_param_names": ".*lora_b.*",
        "model_modifier": "lora",
    })()
    model = modify_transformer(model, config)
    checkpoint_state = torch.load(checkpoint, map_location="cpu", weights_only=False)
    result = model.load_state_dict(checkpoint_state, strict=False)
    if result.unexpected_keys:
        raise RuntimeError(f"unexpected IA3 keys: {result.unexpected_keys[:10]}")
    if len(checkpoint_state) != 192 or any(
        not name.endswith("lora_b") for name in checkpoint_state
    ):
        raise RuntimeError("released checkpoint is not the expected 192-key IA3 state")
    model.to(device=device)
    trainable_names = []
    for name, parameter in model.named_parameters():
        is_trainable = bool(TRAINABLE_PATTERN.fullmatch(name))
        parameter.requires_grad = is_trainable
        if is_trainable:
            trainable_names.append(name)
    if sorted(trainable_names) != sorted(checkpoint_state):
        raise RuntimeError("trainable IA3 parameter names differ from checkpoint keys")
    # ``modify_transformer`` also inserts frozen ``multi_lora_a`` tensors in
    # the process default dtype.  They are part of the forward graph, so cast
    # every frozen parameter back to the base model's bfloat16 storage while
    # retaining FP32 only for the 192 trainable ``lora_b`` master tensors.
    for parameter in model.parameters():
        if not parameter.requires_grad:
            parameter.data = parameter.data.to(dtype=torch.bfloat16)
    non_bfloat_frozen = [
        name for name, parameter in model.named_parameters()
        if not parameter.requires_grad and parameter.dtype != torch.bfloat16
    ]
    non_float_trainable = [
        name for name, parameter in model.named_parameters()
        if parameter.requires_grad and parameter.dtype != torch.float32
    ]
    if non_bfloat_frozen or non_float_trainable:
        raise RuntimeError(
            "unexpected mixed-precision parameter layout: "
            f"non_bfloat_frozen={non_bfloat_frozen[:5]}, "
            f"non_float_trainable={non_float_trainable[:5]}"
        )
    initial_state = {
        name: parameter.detach().cpu().clone()
        for name, parameter in model.named_parameters() if parameter.requires_grad
    }
    audit = {
        "checkpoint_key_count": len(checkpoint_state),
        "checkpoint_parameter_count": int(sum(v.numel() for v in checkpoint_state.values())),
        "missing_base_model_key_count": len(result.missing_keys),
        "initial_trainable_state_sha256": state_hash(initial_state),
        "parameter_dtype": str(next(model.parameters()).dtype),
        "trainable_parameter_dtype": str(next(
            parameter for parameter in model.parameters() if parameter.requires_grad
        ).dtype),
        "trainable_tensor_count": len(trainable_names),
        "trainable_parameter_count": int(sum(
            parameter.numel() for parameter in model.parameters()
            if parameter.requires_grad
        )),
        "frozen_parameter_count": int(sum(
            parameter.numel() for parameter in model.parameters()
            if not parameter.requires_grad
        )),
        "precision_layout": "frozen=bfloat16, trainable_ia3=float32",
    }
    return tokenizer, model, initial_state, audit


def reset_trainable_state(
    model: Any, initial_state: dict[str, torch.Tensor]
) -> str:
    result = model.load_state_dict(initial_state, strict=False)
    if result.unexpected_keys:
        raise RuntimeError(f"reset produced unexpected keys: {result.unexpected_keys[:10]}")
    current = {
        name: parameter.detach().cpu().clone()
        for name, parameter in model.named_parameters() if parameter.requires_grad
    }
    digest = state_hash(current)
    expected = state_hash(initial_state)
    if digest != expected:
        raise RuntimeError("IA3 checkpoint reset is not exact")
    return digest


def linear_schedule(optimizer: Any, total_steps: int) -> Any:
    warmup_steps = total_steps * WARMUP_RATIO

    def lr_lambda(step: int) -> float:
        if step < warmup_steps:
            return float(step) / float(max(1, warmup_steps))
        return max(
            0.0,
            float(total_steps - step) / float(max(1, total_steps - warmup_steps)),
        )

    return torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)


def three_term_loss(model: Any, batch: dict[str, torch.Tensor], pad_id: int) -> tuple[torch.Tensor, dict[str, float]]:
    input_ids = batch["input_ids"]
    choices_ids = batch["answer_choices_ids"]
    labels = batch["labels"]
    batch_size, num_choices = choices_ids.size()[:2]
    flat_choices = choices_ids.flatten(0, 1)
    attention = (input_ids != pad_id).float()
    hidden = model.encoder(input_ids=input_ids, attention_mask=attention)[0]
    hidden = hidden.unsqueeze(1).repeat(1, num_choices, 1, 1).flatten(0, 1)
    attention = attention.unsqueeze(1).repeat(1, num_choices, 1).flatten(0, 1)
    decoder_input = torch.cat(
        [torch.zeros_like(flat_choices[:, :1]), flat_choices[:, :-1]], dim=1
    )
    decoder_attention = (decoder_input == decoder_input).float()
    lm_target = flat_choices - 100 * (flat_choices == pad_id).long()
    output = model(
        attention_mask=attention,
        encoder_outputs=[hidden],
        decoder_input_ids=decoder_input,
        decoder_attention_mask=decoder_attention,
        use_cache=False,
    )
    token_losses = F.cross_entropy(
        output.logits.flatten(0, 1), lm_target.flatten(0, 1), reduction="none"
    ).view(batch_size, num_choices, -1)
    choice_scores = token_losses.sum(dim=-1)
    choice_scores = choice_scores / (choices_ids != pad_id).sum(dim=-1).clamp_min(1)
    selected_logits = output.logits.view(
        batch_size, num_choices, *output.logits.size()[1:]
    )[range(batch_size), labels].flatten(0, 1)
    selected_targets = lm_target.view(batch_size, num_choices, -1)[
        range(batch_size), labels
    ].flatten(0, 1)
    lm_loss = F.cross_entropy(selected_logits, selected_targets)
    mc_loss = F.cross_entropy(-choice_scores, labels)
    cand_loglikely = -token_losses
    cand_loglikely += (lm_target < 0).view(batch_size, num_choices, -1) * -100
    cand_loglikely[range(batch_size), labels] = -100
    unlikely_loss = -torch.log(1 - torch.exp(cand_loglikely) + 1e-2).sum()
    unlikely_loss = unlikely_loss / (cand_loglikely != -100).sum().clamp_min(1)
    loss = lm_loss + mc_loss + unlikely_loss
    return loss, {
        "loss": float(loss.detach().float().cpu()),
        "lm_loss": float(lm_loss.detach().float().cpu()),
        "mc_loss": float(mc_loss.detach().float().cpu()),
        "unlikely_loss": float(unlikely_loss.detach().float().cpu()),
    }


def train_cell(
    model: Any,
    tokenizer: Any,
    dataset: PreparedTrainDataset,
    seed: int,
    shot: int,
    device: str,
    max_steps: int,
) -> dict[str, Any]:
    if shot == 0:
        return {
            "planned_steps": 0, "executed_steps": 0, "loss_first": None,
            "loss_last": None, "batch_order_sha256": sha256_ints([]),
        }
    planned_steps = EPOCHS * (shot // TRAIN_BATCH_SIZE)
    executed_steps = min(planned_steps, max_steps) if max_steps else planned_steps
    set_seeds(seed)
    generator = torch.Generator()
    generator.manual_seed(seed)
    loader = DataLoader(
        dataset,
        batch_size=TRAIN_BATCH_SIZE,
        shuffle=True,
        generator=generator,
        collate_fn=make_collate(tokenizer.pad_token_id),
        drop_last=True,
        num_workers=0,
    )
    trainable = [parameter for parameter in model.parameters() if parameter.requires_grad]
    optimizer = Adafactor(
        trainable,
        lr=LEARNING_RATE,
        weight_decay=0.0,
        scale_parameter=True,
        relative_step=False,
        warmup_init=False,
    )
    scheduler = linear_schedule(optimizer, planned_steps)
    iterator = iter(loader)
    losses: list[dict[str, float]] = []
    batch_order: list[int] = []
    model.train()
    optimizer.zero_grad(set_to_none=True)
    for step in range(executed_steps):
        try:
            batch = next(iterator)
        except StopIteration:
            iterator = iter(loader)
            batch = next(iterator)
        batch_order.extend(int(value) for value in batch["row_ids"].tolist())
        batch = {key: value.to(device) for key, value in batch.items()}
        with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
            loss, parts = three_term_loss(model, batch, tokenizer.pad_token_id)
        if not torch.isfinite(loss):
            raise RuntimeError(f"nonfinite loss at step {step}: {parts}")
        loss.backward()
        gradient_norm = torch.nn.utils.clip_grad_norm_(trainable, GRAD_CLIP)
        if not torch.isfinite(gradient_norm):
            raise RuntimeError(f"nonfinite gradient norm at step {step}")
        optimizer.step()
        scheduler.step()
        optimizer.zero_grad(set_to_none=True)
        parts["gradient_norm_pre_clip"] = float(gradient_norm.detach().float().cpu())
        parts["lr"] = float(optimizer.param_groups[0]["lr"])
        losses.append(parts)
        if step == 0 or step + 1 == executed_steps or (step + 1) % 100 == 0:
            print(json.dumps({"step": step + 1, "steps": executed_steps, **parts}), flush=True)
    return {
        "planned_steps": planned_steps,
        "executed_steps": executed_steps,
        "loss_first": losses[0] if losses else None,
        "loss_last": losses[-1] if losses else None,
        "batch_order_sha256": sha256_ints(batch_order),
    }


@torch.inference_mode()
def score_texts(
    tokenizer: Any,
    model: Any,
    prompts: list[str],
    choices: tuple[str, ...],
    batch_size: int,
    device: str,
) -> np.ndarray:
    choice_tokens = tokenizer(
        list(choices), return_tensors="pt", padding=True, truncation=True,
        add_special_tokens=True,
    ).input_ids
    count = len(choices)
    outputs = []
    model.eval()
    for start in range(0, len(prompts), batch_size):
        texts = prompts[start:start + batch_size]
        encoded = tokenizer(
            texts, return_tensors="pt", padding=True, truncation=True,
            max_length=MAX_LENGTH, add_special_tokens=True,
        )
        input_ids = encoded.input_ids.to(device)
        attention = encoded.attention_mask.to(device)
        size = len(texts)
        choices_ids = choice_tokens.to(device).unsqueeze(0).expand(size, -1, -1)
        flat = choices_ids.reshape(size * count, -1)
        # Deliberately no autocast here: the frozen compatibility scorer stores
        # every evaluation parameter in bfloat16 and executes directly.  The
        # surrounding temporary-state context enforces that same layout.
        hidden = model.encoder(input_ids=input_ids, attention_mask=attention)[0]
        hidden = hidden.unsqueeze(1).expand(-1, count, -1, -1).reshape(
            size * count, hidden.shape[1], hidden.shape[2]
        )
        repeated_attention = attention.unsqueeze(1).expand(-1, count, -1).reshape(
            size * count, -1
        )
        decoder_input = torch.cat([torch.zeros_like(flat[:, :1]), flat[:, :-1]], dim=1)
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
        ).view(size, count, -1)
        token_count = (choices_ids != tokenizer.pad_token_id).sum(dim=-1).clamp_min(1)
        scores = losses.sum(dim=-1) / token_count
        outputs.append(torch.softmax(-scores, dim=-1).cpu().numpy().astype(np.float64))
    return np.concatenate(outputs, axis=0)


def compute_metrics(labels: np.ndarray, probabilities: np.ndarray) -> dict[str, float]:
    prediction = np.argmax(probabilities, axis=1)
    if probabilities.shape[1] == 2:
        auc = roc_auc_score(labels, probabilities[:, 1])
    else:
        auc = roc_auc_score(labels, probabilities, multi_class="ovr", average="macro")
    return {
        "auc": float(auc),
        "accuracy": float(accuracy_score(labels, prediction)),
    }


def save_checkpoint(path: Path, model: Any) -> str:
    state = {
        name: parameter.detach().cpu()
        for name, parameter in model.named_parameters() if parameter.requires_grad
    }
    temporary = path.with_suffix(path.suffix + ".tmp")
    torch.save(state, temporary)
    os.replace(temporary, path)
    return sha256_file(path)


@contextmanager
def temporary_bfloat16_trainable_state(model: Any):
    """Match the frozen all-bfloat16 scorer without losing FP32 IA3 masters."""
    trainable = [
        parameter for parameter in model.parameters() if parameter.requires_grad
    ]
    original = [parameter.detach().clone() for parameter in trainable]
    try:
        for parameter in trainable:
            parameter.data = parameter.data.to(dtype=torch.bfloat16)
        yield
    finally:
        for parameter, value in zip(trainable, original):
            parameter.data = value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tabllm-root", type=Path, required=True)
    parser.add_argument("--tfew-root", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--split-manifest", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--datasets", nargs="+", choices=DATASETS, default=list(DATASETS))
    parser.add_argument("--arms", nargs="+", choices=ARMS, default=list(ARMS))
    parser.add_argument("--shots", nargs="+", type=int, choices=SHOTS, default=list(SHOTS))
    parser.add_argument("--seeds", nargs="+", type=int, choices=SEEDS, default=list(SEEDS))
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--eval-batch-size", type=int, default=16)
    parser.add_argument("--num-shards", type=int, default=1)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--max-steps", type=int, default=0)
    parser.add_argument("--eval-limit", type=int, default=0)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    if not (0 <= args.shard_index < args.num_shards):
        raise ValueError("shard-index must be in [0,num-shards)")
    if len(set(args.arms)) != len(args.arms):
        raise ValueError("arms must be unique")
    if len(set(args.shots)) != len(args.shots):
        raise ValueError("shots must be unique")
    if any(shot and shot % TRAIN_BATCH_SIZE for shot in args.shots):
        raise ValueError("every nonzero shot count must be divisible by batch size 4")

    split_manifest = json.loads(args.split_manifest.read_text(encoding="utf-8"))
    sys.path.insert(0, str(args.tabllm_root))
    tabllm = load_module(
        "tabllm_ranon_ladder_create_external_v1",
        args.tabllm_root / "create_external_datasets.py",
    )
    runner_path = Path(__file__).resolve()
    source_paths = [
        path for path in (args.tabllm_root / "datasets").rglob("*") if path.is_file()
    ] + [
        args.tabllm_root / "create_external_datasets.py",
        args.tabllm_root / "helper/external_datasets_variables.py",
        args.tabllm_root / "helper/note_generator.py",
        args.tabllm_root / "helper/note_template.py",
    ]
    common = {
        "protocol_sha256": sha256_file(PROTOCOL),
        "runner_sha256": sha256_file(runner_path),
        "split_manifest_sha256": sha256_file(args.split_manifest),
        "tabllm_commit": git_commit(args.tabllm_root),
        "tfew_execution_commit": git_commit(args.tfew_root),
        "raw_and_serialization_tree_sha256": aggregate_tree_hash(args.tabllm_root, source_paths),
        "ia3_checkpoint_sha256": sha256_file(args.checkpoint),
        "model_path": str(args.model_path.resolve()),
        "versions": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "transformers": importlib.metadata.version("transformers"),
            "datasets": importlib.metadata.version("datasets"),
            "scikit_learn": importlib.metadata.version("scikit-learn"),
        },
        "training_contract": {
            "epochs": EPOCHS,
            "batch_size": TRAIN_BATCH_SIZE,
            "lr": LEARNING_RATE,
            "optimizer": "Adafactor(scale_parameter=True, relative_step=False)",
            "scheduler": "linear_decay_with_warmup",
            "warmup_ratio": WARMUP_RATIO,
            "gradient_clip": GRAD_CLIP,
            "loss": "lm + multiple_choice + unlikely",
            "length_norm": 1,
            "max_length": MAX_LENGTH,
            "compute_dtype": (
                "bfloat16 base and autocast with FP32 IA3 master parameters; "
                "temporary bfloat16 IA3 evaluation copy"
            ),
        },
    }

    prepared: dict[str, dict[str, Any]] = {}
    preparation_report: dict[str, Any] = {}
    for dataset in args.datasets:
        frame = build_full_dataset(tabllm, args.tabllm_root, dataset)
        notes = {arm: build_notes(tabllm, frame, dataset, arm) for arm in args.arms}
        split_data = {}
        for seed in args.seeds:
            train_rows, test_rows = split_members(frame, seed)
            verify_split_manifest(split_manifest, dataset, seed, test_rows)
            memberships = {
                shot: balanced_few_shot_members(frame, train_rows, shot, seed)
                for shot in args.shots
            }
            split_data[seed] = {
                "train_rows": train_rows,
                "test_rows": test_rows,
                "memberships": memberships,
            }
        prepared[dataset] = {"frame": frame, "notes": notes, "splits": split_data}
        preparation_report[dataset] = {
            "n_full": len(frame),
            "labels_sha256": sha256_ints(frame["label"].astype(int).tolist()),
            "note_sha256": {arm: sha256_strings(notes[arm]) for arm in args.arms},
            "test_membership_sha256": {
                str(seed): sha256_ints(split_data[seed]["test_rows"]) for seed in args.seeds
            },
            "few_shot_membership_sha256": {
                str(seed): {
                    str(shot): sha256_ints(split_data[seed]["memberships"][shot])
                    for shot in args.shots
                } for seed in args.seeds
            },
        }
    if args.prepare_only:
        print(json.dumps({
            "status": "prepare_only_pass",
            "common": common,
            "datasets": preparation_report,
        }, sort_keys=True))
        return 0

    cells = [
        (dataset, shot, seed, arm)
        for dataset in args.datasets
        for shot in args.shots
        for seed in args.seeds
        for arm in args.arms
    ]
    assigned = [
        cell for index, cell in enumerate(cells)
        if index % args.num_shards == args.shard_index
    ]
    pending = []
    for dataset, shot, seed, arm in assigned:
        cell = args.out_root / arm / dataset / f"k{shot}" / f"seed{seed}"
        metrics_path = cell / "metrics.json"
        if metrics_path.is_file():
            existing = json.loads(metrics_path.read_text(encoding="utf-8"))
            if existing.get("runner_sha256") != common["runner_sha256"] or existing.get(
                "protocol_sha256"
            ) != common["protocol_sha256"]:
                raise RuntimeError(f"stale cached cell under changed contract: {cell}")
            continue
        pending.append((dataset, shot, seed, arm))
    if not pending:
        print(json.dumps({"status": "cached", "assigned_cells": len(assigned)}))
        return 0

    tokenizer, model, initial_state, model_audit = load_model(
        args.model_path, args.tfew_root, args.checkpoint, args.device
    )
    common["model_audit"] = model_audit
    for dataset, shot, seed, arm in pending:
        started = time.perf_counter()
        reset_hash = reset_trainable_state(model, initial_state)
        item = prepared[dataset]
        frame: pd.DataFrame = item["frame"]
        notes: list[str] = item["notes"][arm]
        split = item["splits"][seed]
        train_rows = split["memberships"][shot]
        test_rows = split["test_rows"]
        if args.eval_limit:
            test_rows = test_rows[:args.eval_limit]
        train_prompts = [notes[row_id] + "\n\n" + QUESTIONS[dataset] for row_id in train_rows]
        train_labels = [int(frame.loc[row_id, "label"]) for row_id in train_rows]
        train_dataset = PreparedTrainDataset(
            tokenizer, train_prompts, train_labels, CHOICES[dataset], train_rows
        )
        training = train_cell(
            model, tokenizer, train_dataset, seed, shot, args.device, args.max_steps
        )
        test_prompts = [notes[row_id] + "\n\n" + QUESTIONS[dataset] for row_id in test_rows]
        with temporary_bfloat16_trainable_state(model):
            probabilities = score_texts(
                tokenizer, model, test_prompts, CHOICES[dataset],
                args.eval_batch_size, args.device,
            )
        labels = frame.loc[test_rows, "label"].astype(int).to_numpy()
        metrics = compute_metrics(labels, probabilities)
        cell = args.out_root / arm / dataset / f"k{shot}" / f"seed{seed}"
        cell.mkdir(parents=True, exist_ok=True)
        predictions_path = cell / "predictions.jsonl.gz"
        # A fixed gzip timestamp makes content hashes meaningful across repeated
        # smoke runs and independent evidence shards.
        with predictions_path.open("wb") as raw_handle, gzip.GzipFile(
            fileobj=raw_handle, mode="wb", mtime=0
        ) as gzip_handle, io.TextIOWrapper(gzip_handle, encoding="utf-8") as handle:
            for index, row_id in enumerate(test_rows):
                handle.write(json.dumps({
                    "dataset": dataset,
                    "arm": arm,
                    "shot": shot,
                    "seed": seed,
                    "row_id": int(row_id),
                    "label": int(labels[index]),
                    "prediction": int(np.argmax(probabilities[index])),
                    "class_probabilities": probabilities[index].tolist(),
                    "prompt_sha256": hashlib.sha256(
                        test_prompts[index].encode("utf-8")
                    ).hexdigest(),
                }, sort_keys=True) + "\n")
        checkpoint_path = cell / "ia3_finish.pt"
        checkpoint_hash = save_checkpoint(checkpoint_path, model)
        current_state = {
            name: parameter.detach().cpu().clone()
            for name, parameter in model.named_parameters() if parameter.requires_grad
        }
        analysis_status = (
            "engineering_smoke_inadmissible"
            if args.max_steps or args.eval_limit
            else "frozen_ranon_support_ladder_evidence"
        )
        payload = {
            **common,
            "analysis_status": analysis_status,
            "dataset": dataset,
            "arm": arm,
            "shot": shot,
            "seed": seed,
            "train_membership_row_ids_sha256": sha256_ints(train_rows),
            "train_membership_with_replacement": len(set(train_rows)) != len(train_rows),
            "test_row_ids_sha256": sha256_ints(test_rows),
            "train_prompt_sha256": sha256_strings(train_prompts),
            "test_prompt_sha256": sha256_strings(test_prompts),
            "initial_trainable_state_sha256": reset_hash,
            "final_trainable_state_sha256": state_hash(current_state),
            "predictions_sha256": sha256_file(predictions_path),
            "trained_checkpoint_sha256": checkpoint_hash,
            "n_train": len(train_rows),
            "n_train_unique": len(set(train_rows)),
            "n_test": len(test_rows),
            "training": training,
            "metrics": metrics,
            "wall_seconds": round(time.perf_counter() - started, 3),
        }
        temporary = cell / "metrics.json.tmp"
        temporary.write_text(
            json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(temporary, cell / "metrics.json")
        print(json.dumps({
            "dataset": dataset, "arm": arm, "shot": shot, "seed": seed,
            "auc": metrics["auc"], "steps": training["executed_steps"],
            "status": analysis_status, "wall_seconds": payload["wall_seconds"],
        }), flush=True)
    print(json.dumps({
        "status": "complete",
        "shard_index": args.shard_index,
        "completed_now": len(pending),
        "assigned_cells": len(assigned),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
