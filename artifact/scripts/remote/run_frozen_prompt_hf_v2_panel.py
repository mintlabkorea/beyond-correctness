#!/usr/bin/env python3
"""Run one frozen system/user prompt with content-preserving JSON transport."""

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


def parse_transport(raw: str) -> tuple[dict[str, Any] | None, str | None, str | None]:
    text = raw.strip()
    normalization = "identity"
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```" and lines[0].strip() in {"```", "```json", "```JSON"}:
            text = "\n".join(lines[1:-1]).strip()
            normalization = "single_outer_json_fence_removed"
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, normalization, str(exc)
    if not isinstance(value, dict):
        return None, normalization, "Top-level response is not a JSON object"
    return value, normalization, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt-artifact", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--cuda-device", type=int, choices=(1, 2, 3), required=True)
    parser.add_argument("--max-new-tokens", type=int, default=8192)
    parser.add_argument("--attn-implementation", default="sdpa")
    args = parser.parse_args()
    if args.out_dir.exists() and any(args.out_dir.iterdir()):
        print(f"Refusing to overwrite non-empty run directory: {args.out_dir}", file=sys.stderr)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)

    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    artifact = json.loads(args.prompt_artifact.read_text(encoding="utf-8"))
    messages = artifact.get("messages", [])
    if [item.get("role") for item in messages] != ["system", "user"]:
        raise ValueError("Prompt artifact must contain exactly system,user messages")
    torch.cuda.set_device(args.cuda_device)
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True)
    kwargs = {
        "return_tensors": "pt",
        "return_dict": True,
        "add_generation_prompt": True,
        "enable_thinking": False,
    }
    try:
        encoded = tokenizer.apply_chat_template(messages, **kwargs)
        thinking_disabled: bool | None = True
    except TypeError:
        kwargs.pop("enable_thinking")
        encoded = tokenizer.apply_chat_template(messages, **kwargs)
        thinking_disabled = None
    input_ids = encoded["input_ids"] if isinstance(encoded, Mapping) else encoded
    attention_mask = encoded.get("attention_mask") if isinstance(encoded, Mapping) else None
    input_tokens = int(input_ids.shape[-1])
    load_started = datetime.now(timezone.utc)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        local_files_only=True,
        torch_dtype=torch.bfloat16,
        attn_implementation=args.attn_implementation,
        device_map={"": args.cuda_device},
    )
    model.eval()
    load_finished = datetime.now(timezone.utc)
    input_device = next(model.parameters()).device
    input_ids = input_ids.to(input_device)
    if attention_mask is not None:
        attention_mask = attention_mask.to(input_device)
    context_limit = int(getattr(model.config, "max_position_embeddings", 0) or 0)
    if not context_limit:
        text_config = getattr(model.config, "text_config", None)
        context_limit = int(getattr(text_config, "max_position_embeddings", 0) or 0)
    effective_max_new = args.max_new_tokens
    if context_limit:
        effective_max_new = min(effective_max_new, context_limit - input_tokens)
    if effective_max_new <= 0:
        raise ValueError(f"Prompt has {input_tokens} tokens but context limit is {context_limit}")
    started = datetime.now(timezone.utc)
    with torch.inference_mode():
        generated = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=effective_max_new,
            do_sample=False,
            use_cache=True,
            pad_token_id=tokenizer.eos_token_id,
        )
    finished = datetime.now(timezone.utc)
    raw = tokenizer.decode(generated[0, input_tokens:], skip_special_tokens=True)
    generated_tokens = int(generated.shape[-1] - input_tokens)
    (args.out_dir / "raw_response.txt").write_text(raw, encoding="utf-8")
    parsed, normalization, parse_error = parse_transport(raw)
    if parsed is not None:
        (args.out_dir / "materialized_candidate_bank.json").write_text(
            json.dumps(parsed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    manifest = {
        "contract_version": artifact["contract_version"],
        "schema_pair_id": artifact["schema_pair_id"],
        "provider": "huggingface_local",
        "model": args.model_id,
        "model_path": str(args.model_path),
        "transport": "transformers_apply_chat_template",
        "role_transport": "native_system_user",
        "role_transport_confounded": False,
        "tools_requested": "disabled",
        "external_retrieval_requested": "disabled",
        "thinking_disabled": thinking_disabled,
        "native_structured_output": False,
        "decoding": {
            "do_sample": False,
            "requested_max_new_tokens": args.max_new_tokens,
            "effective_max_new_tokens": effective_max_new,
            "attn_implementation": args.attn_implementation,
        },
        "runtime": {
            "torch_version": torch.__version__,
            "transformers_version": transformers.__version__,
            "physical_cuda_device": args.cuda_device,
            "input_device": str(input_device),
            "context_limit": context_limit,
            "input_tokens": input_tokens,
            "generated_tokens": generated_tokens,
            "model_load_started_at_utc": load_started.isoformat(),
            "model_load_finished_at_utc": load_finished.isoformat(),
        },
        "started_at_utc": started.isoformat(),
        "finished_at_utc": finished.isoformat(),
        "elapsed_seconds": round((finished - started).total_seconds(), 3),
        "prompt_hashes": artifact["hashes"],
        "strict_json_parse": normalization == "identity" and parsed is not None,
        "transport_normalization": normalization,
        "transport_normalization_content_preserving": normalization in {"identity", "single_outer_json_fence_removed"},
        "materialized": parsed is not None,
        "parse_error": parse_error,
        "raw_response_sha256": sha256_text(raw),
        "raw_response_chars": len(raw),
        "return_code": 0 if parsed is not None else 3,
    }
    (args.out_dir / "generation_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "model": args.model_id,
        "schema_pair_id": artifact["schema_pair_id"],
        "input_tokens": input_tokens,
        "generated_tokens": generated_tokens,
        "transport_normalization": normalization,
        "materialized": parsed is not None,
    }, sort_keys=True))
    return int(manifest["return_code"])


if __name__ == "__main__":
    raise SystemExit(main())
