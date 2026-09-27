#!/usr/bin/env python3
"""Materialize a separate, content-preserving transport-normalized run track."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_ID = "crta-transport-normalization-1.0.0"
VALIDATOR_PATH = ROOT / "scripts" / "validate_candidates.py"
SPEC = importlib.util.spec_from_file_location("crta_validator", VALIDATOR_PATH)
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VALIDATOR)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(raw: str) -> tuple[str | None, str, str | None]:
    stripped = raw.strip()
    try:
        value = json.loads(stripped)
        if not isinstance(value, dict):
            return None, "failed", "top-level JSON value is not an object"
        return stripped, "identity_json_object", None
    except json.JSONDecodeError:
        pass

    prefix, suffix = "```json\n", "\n```"
    if not stripped.startswith(prefix) or not stripped.endswith(suffix):
        return None, "failed", "response is neither a JSON object nor one exact JSON fence"
    inner = stripped[len(prefix) : -len(suffix)]
    try:
        value = json.loads(inner)
    except json.JSONDecodeError as exc:
        return None, "failed", f"fenced content is not complete JSON: {exc}"
    if not isinstance(value, dict):
        return None, "failed", "fenced JSON value is not an object"
    return inner, "extract_single_outer_json_fence", None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict-run-root", type=Path, required=True)
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows: list[dict[str, Any]] = []
    for manifest_path in sorted(args.strict_run_root.rglob("generation_manifest.json")):
        manifest = load_json(manifest_path)
        raw_path = manifest_path.parent / "raw_response.txt"
        if manifest.get("schema_pair_id") != load_json(args.payload)["schema_pair_id"]:
            continue
        relative = manifest_path.parent.relative_to(args.strict_run_root)
        output = args.out_root / relative
        if output.exists() and any(output.iterdir()):
            raise FileExistsError(f"Refusing to overwrite non-empty normalized run: {output}")
        output.mkdir(parents=True, exist_ok=True)

        action, error, normalized_text = "failed", None, None
        if raw_path.exists():
            normalized_text, action, error = normalize(raw_path.read_text(encoding="utf-8"))
        else:
            error = "raw_response.txt does not exist"

        status = "normalization_failed"
        ledger: dict[str, Any] | None = None
        normalized_path = output / "normalized_candidate_bank.json"
        if normalized_text is not None:
            normalized_path.write_text(normalized_text + "\n", encoding="utf-8")
            try:
                ledger = VALIDATOR.validate_and_materialize(args.payload, normalized_path)
                (output / "decision_ledger.json").write_text(
                    json.dumps(ledger, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                status = "materialized"
            except Exception as exc:
                error = str(exc)
                status = "contract_failed"

        normalization_manifest = {
            "protocol_id": PROTOCOL_ID,
            "contract_version": manifest["contract_version"],
            "schema_pair_id": manifest["schema_pair_id"],
            "provider": manifest.get("provider"),
            "model": manifest.get("model"),
            "source_run_dir": str(manifest_path.parent),
            "source_generation_manifest_sha256": hashlib.sha256(
                manifest_path.read_bytes()
            ).hexdigest(),
            "source_raw_response_sha256": (
                hashlib.sha256(raw_path.read_bytes()).hexdigest() if raw_path.exists() else None
            ),
            "normalization_action": action,
            "normalized_candidate_bank_sha256": (
                sha256_text(normalized_text) if normalized_text is not None else None
            ),
            "status": status,
            "error": error,
            "summary": ledger["summary"] if ledger else None,
        }
        (output / "transport_normalization_manifest.json").write_text(
            json.dumps(normalization_manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        rows.append({"run_dir": str(relative), **normalization_manifest})

    args.out_root.mkdir(parents=True, exist_ok=True)
    aggregate = {
        "protocol_id": PROTOCOL_ID,
        "runs": len(rows),
        "materialized": sum(row["status"] == "materialized" for row in rows),
        "normalization_failed": sum(
            row["status"] == "normalization_failed" for row in rows
        ),
        "contract_failed": sum(row["status"] == "contract_failed" for row in rows),
        "results": rows,
    }
    (args.out_root / "run_summary.json").write_text(
        json.dumps(aggregate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: aggregate[key] for key in ("runs", "materialized", "normalization_failed", "contract_failed")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
