#!/usr/bin/env python3
"""Run a frozen CRTA prompt artifact with a local Hugging Face causal LM."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def strict_json(raw: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(raw.strip())
    except json.JSONDecodeError as exc:
        return None, str(exc)
    if not isinstance(value, dict):
        return None, "Top-level response is not a JSON object"
    return value, None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt-artifact", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument(
        "--cuda-device",
        type=int,
        choices=(2, 3),
        default=2,
        help="Physical CUDA device. This project permits only GPUs 2 and 3.",
    )
    parser.add_argument("--max-new-tokens", type=int, default=16384)
    parser.add_argument("--attn-implementation", default="eager")
    parser.add_argument(
        "--yarn-factor",
        type=float,
        default=None,
        help="Optional static YaRN factor for an explicitly long-context retry.",
    )
    parser.add_argument(
        "--context-limit-override",
        type=int,
        default=None,
        help="Context limit paired with --yarn-factor; never used for ordinary prompts.",
    )
    parser.add_argument(
        "--json-object-prefill",
        action="store_true",
        help="Prefill the assistant turn with '{' and prepend it to decoded output.",
    )
    return parser.parse_args()


def run_generation(args: argparse.Namespace) -> int:
    if args.out_dir.exists() and any(args.out_dir.iterdir()):
        print(f"Refusing to overwrite non-empty run directory: {args.out_dir}", file=sys.stderr)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)

    import torch
    import transformers
    from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

    if (args.yarn_factor is None) != (args.context_limit_override is None):
        raise ValueError("--yarn-factor and --context-limit-override must be supplied together")
    if args.yarn_factor is not None and args.yarn_factor <= 1:
        raise ValueError("--yarn-factor must exceed 1")
    if args.context_limit_override is not None and args.context_limit_override <= 0:
        raise ValueError("--context-limit-override must be positive")

    artifact = json.loads(args.prompt_artifact.read_text(encoding="utf-8"))
    messages = artifact.get("messages", [])
    if [item.get("role") for item in messages] != ["system", "user"]:
        raise ValueError("Prompt artifact must contain exactly one system and one user message")

    tokenizer = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True)
    template_messages = messages
    chat_kwargs = {
        "return_tensors": "pt",
        "return_dict": True,
        "enable_thinking": False,
    }
    if args.json_object_prefill:
        template_messages = [*messages, {"role": "assistant", "content": "{"}]
        chat_kwargs.update({"add_generation_prompt": False, "continue_final_message": True})
    else:
        chat_kwargs["add_generation_prompt"] = True
    try:
        encoded = tokenizer.apply_chat_template(template_messages, **chat_kwargs)
        thinking_disabled = True
    except TypeError:
        chat_kwargs.pop("enable_thinking")
        encoded = tokenizer.apply_chat_template(template_messages, **chat_kwargs)
        thinking_disabled = None

    input_ids = encoded["input_ids"] if isinstance(encoded, Mapping) else encoded
    attention_mask = encoded.get("attention_mask") if isinstance(encoded, Mapping) else None
    input_tokens = int(input_ids.shape[-1])

    started = datetime.now(timezone.utc)
    config = AutoConfig.from_pretrained(args.model_path, local_files_only=True)
    if args.yarn_factor is not None:
        current_rope = (
            getattr(config, "rope_parameters", None)
            or getattr(config, "rope_scaling", None)
            or {}
        )
        rope_theta = current_rope.get(
            "rope_theta", getattr(config, "rope_theta", None)
        )
        rope_parameters = {
            "rope_type": "yarn",
            "factor": args.yarn_factor,
            "original_max_position_embeddings": 32768,
        }
        if rope_theta is not None:
            # transformers>=5 stores the base in ``rope_parameters``.  Dropping
            # it makes YaRN initialization evaluate ``None ** Tensor``.
            rope_parameters["rope_theta"] = rope_theta
        if hasattr(config, "rope_parameters"):
            config.rope_parameters = rope_parameters
        else:
            config.rope_scaling = rope_parameters
        config.max_position_embeddings = args.context_limit_override
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        local_files_only=True,
        config=config,
        torch_dtype=torch.bfloat16,
        attn_implementation=args.attn_implementation,
        device_map={"": args.cuda_device},
    )
    model.eval()
    input_device = next(model.parameters()).device
    input_ids = input_ids.to(input_device)
    if attention_mask is not None:
        attention_mask = attention_mask.to(input_device)

    context_limit = int(getattr(model.config, "max_position_embeddings", 0) or 0)
    if not context_limit:
        text_config = getattr(model.config, "text_config", None)
        context_limit = int(
            getattr(text_config, "max_position_embeddings", 0) or 0
        )
    effective_max_new = args.max_new_tokens
    if context_limit:
        effective_max_new = min(effective_max_new, context_limit - input_tokens)
    if effective_max_new <= 0:
        raise ValueError(f"Prompt has {input_tokens} tokens but model context limit is {context_limit}")

    with torch.inference_mode():
        generated = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=effective_max_new,
            do_sample=False,
            use_cache=True,
            pad_token_id=tokenizer.eos_token_id,
        )
    generated_tokens = int(generated.shape[-1] - input_tokens)
    raw = tokenizer.decode(generated[0, input_tokens:], skip_special_tokens=True)
    if args.json_object_prefill:
        raw = "{" + raw
    finished = datetime.now(timezone.utc)

    (args.out_dir / "raw_response.txt").write_text(raw, encoding="utf-8")
    parsed, parse_error = strict_json(raw)
    if parsed is not None:
        (args.out_dir / "raw_candidate_bank.json").write_text(
            json.dumps(parsed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    manifest = {
        "contract_version": artifact["contract_version"],
        "schema_pair_id": artifact["schema_pair_id"],
        "provider": "huggingface_local",
        "model": args.model_id,
        "model_path": str(args.model_path),
        "transport": (
            "transformers_apply_chat_template_assistant_json_prefill"
            if args.json_object_prefill
            else "transformers_apply_chat_template"
        ),
        "role_transport": (
            "native_system_user_assistant_prefill"
            if args.json_object_prefill
            else "native_system_user"
        ),
        "role_transport_confounded": bool(args.json_object_prefill),
        "tools_requested": "disabled",
        "external_retrieval_requested": "disabled",
        "thinking_disabled": thinking_disabled,
        "native_structured_output": False,
        "decoding": {
            "do_sample": False,
            "requested_max_new_tokens": args.max_new_tokens,
            "effective_max_new_tokens": effective_max_new,
            "attn_implementation": args.attn_implementation,
            "json_object_prefill": bool(args.json_object_prefill),
            "yarn_factor": args.yarn_factor,
            "context_limit_override": args.context_limit_override,
        },
        "runtime": {
            "torch_version": torch.__version__,
            "transformers_version": transformers.__version__,
            "cuda_device": args.cuda_device,
            "input_device": str(input_device),
            "context_limit": context_limit,
            "input_tokens": input_tokens,
            "generated_tokens": generated_tokens,
        },
        "started_at_utc": started.isoformat(),
        "finished_at_utc": finished.isoformat(),
        "elapsed_seconds": round((finished - started).total_seconds(), 3),
        "prompt_hashes": artifact["hashes"],
        "prompt_variant": artifact.get("prompt_variant", "one_shot"),
        "recovery": artifact.get("recovery"),
        "raw_response_sha256": sha256_text(raw),
        "raw_response_chars": len(raw),
        "strict_json_parse": parsed is not None,
        "strict_json_error": parse_error,
        "return_code": 0 if parsed is not None else 3,
    }
    (args.out_dir / "generation_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"model": args.model_id, "schema_pair_id": artifact["schema_pair_id"], "input_tokens": input_tokens, "generated_tokens": generated_tokens, "strict_json_parse": parsed is not None}, sort_keys=True))
    return 0 if parsed is not None else 3


def main() -> int:
    args = parse_args()
    wrapper_started = datetime.now(timezone.utc)
    try:
        return run_generation(args)
    except Exception as exc:
        # Runtime failures happen before an LLM response exists and must not be
        # confused with invalid JSON.  Persist a mechanical failure record so
        # OOM/loader/backend failures remain auditable without output repair.
        args.out_dir.mkdir(parents=True, exist_ok=True)
        artifact = json.loads(args.prompt_artifact.read_text(encoding="utf-8"))
        failed = datetime.now(timezone.utc)
        manifest = {
            "contract_version": artifact["contract_version"],
            "schema_pair_id": artifact["schema_pair_id"],
            "provider": "huggingface_local",
            "model": args.model_id,
            "model_path": str(args.model_path),
            "transport": "transformers_apply_chat_template",
            "native_structured_output": False,
            "decoding": {
                "do_sample": False,
                "requested_max_new_tokens": args.max_new_tokens,
                "attn_implementation": args.attn_implementation,
                "json_object_prefill": bool(args.json_object_prefill),
                "yarn_factor": args.yarn_factor,
                "context_limit_override": args.context_limit_override,
            },
            "runtime": {"cuda_device": args.cuda_device},
            "started_at_utc": wrapper_started.isoformat(),
            "finished_at_utc": failed.isoformat(),
            "elapsed_seconds": round((failed - wrapper_started).total_seconds(), 3),
            "prompt_hashes": artifact["hashes"],
            "prompt_variant": artifact.get("prompt_variant", "one_shot"),
            "recovery": artifact.get("recovery"),
            "strict_json_parse": False,
            "strict_json_error": None,
            "return_code": 4,
            "generation_failure": {
                "exception_type": type(exc).__name__,
                "message": str(exc),
            },
        }
        (args.out_dir / "generation_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
