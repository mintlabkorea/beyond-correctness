#!/usr/bin/env python3
"""Render the exact CRTA v1 cross-model prompt artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[1]


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def render(
    input_path: Path,
    system_path: Path | None = None,
    user_template_path: Path | None = None,
    output_schema_path: Path | None = None,
    dsl_path: Path | None = None,
    input_schema_path: Path | None = None,
    generation_config_path: Path | None = None,
) -> dict[str, object]:
    system_path = system_path or ROOT / "prompt" / "system.txt"
    user_template_path = user_template_path or ROOT / "prompt" / "user_template.txt"
    output_schema_path = output_schema_path or ROOT / "schemas" / "candidate_bank.schema.json"
    dsl_path = dsl_path or ROOT / "dsl" / "dsl_v1.json"
    input_schema_path = input_schema_path or ROOT / "schemas" / "proposer_input.schema.json"
    generation_config_path = generation_config_path or ROOT / "generation_config.json"

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    output_schema = json.loads(output_schema_path.read_text(encoding="utf-8"))
    dsl = json.loads(dsl_path.read_text(encoding="utf-8"))
    input_schema = json.loads(input_schema_path.read_text(encoding="utf-8"))
    generation_config = json.loads(generation_config_path.read_text(encoding="utf-8"))
    Draft7Validator(input_schema).validate(payload)
    if generation_config["contract_version"] != payload["contract_version"]:
        raise ValueError("Generation config contract_version mismatch")
    if generation_config["candidate_budgets"] != payload["candidate_budgets"]:
        raise ValueError("Input candidate budgets do not match generation config")

    system = system_path.read_text(encoding="utf-8").strip()
    template = user_template_path.read_text(encoding="utf-8").strip()
    replacements = {
        "{{OUTPUT_SCHEMA_JSON}}": canonical_json(output_schema),
        "{{DSL_JSON}}": canonical_json(dsl),
        "{{INPUT_JSON}}": canonical_json(payload),
    }
    user = template
    for placeholder, value in replacements.items():
        count = user.count(placeholder)
        if count != 1:
            raise ValueError(f"Expected one {placeholder} placeholder, found {count}")
        user = user.replace(placeholder, value)
    if any(placeholder in user for placeholder in replacements):
        raise ValueError("Unresolved prompt placeholder")

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    message_text = canonical_json(messages)
    return {
        "contract_version": payload["contract_version"],
        "schema_pair_id": payload["schema_pair_id"],
        "generation_config": generation_config,
        "messages": messages,
        "hashes": {
            "system_prompt_sha256": sha256_text(system),
            "user_prompt_sha256": sha256_text(user),
            "messages_sha256": sha256_text(message_text),
            "input_payload_sha256": sha256_text(canonical_json(payload)),
            "output_schema_sha256": sha256_text(canonical_json(output_schema)),
            "dsl_sha256": sha256_text(canonical_json(dsl)),
            "generation_config_sha256": sha256_text(canonical_json(generation_config)),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    artifact = render(args.input)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(args.out), **artifact["hashes"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
