#!/usr/bin/env python3
"""Validate every generated proposer run and write a compact run summary."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_candidates.py"
SPEC = importlib.util.spec_from_file_location("crta_validate_candidates", VALIDATOR_PATH)
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VALIDATOR)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--payload-root", type=Path, default=ROOT / "payloads")
    return parser.parse_args()


def payload_index(payload_root: Path) -> dict[str, Path]:
    index: dict[str, Path] = {}
    for path in sorted(payload_root.glob("*/proposer_input.json")):
        schema_pair_id = load_json(path)["schema_pair_id"]
        if schema_pair_id in index:
            raise RuntimeError(f"Duplicate payload schema_pair_id: {schema_pair_id}")
        index[schema_pair_id] = path
    return index


def main() -> int:
    args = parse_args()
    payloads = payload_index(args.payload_root)
    rows: list[dict[str, Any]] = []
    for manifest_path in sorted((args.run_root / "models").glob("*/*/generation_manifest.json")):
        run_dir = manifest_path.parent
        manifest = load_json(manifest_path)
        schema_pair_id = manifest["schema_pair_id"]
        strict_json_parse = bool(manifest.get("strict_json_parse"))
        row: dict[str, Any] = {
            "model": manifest["model"],
            "provider": manifest["provider"],
            "schema_pair_id": schema_pair_id,
            "run_dir": str(run_dir),
            # Older local-run manifests predate the explicit return_code field.
            # Their runner contract exits 3 when strict JSON parsing fails.
            "return_code": manifest.get("return_code", 0 if strict_json_parse else 3),
            "strict_json_parse": strict_json_parse,
            "role_transport": manifest.get("role_transport", "unknown"),
            "messages_sha256": manifest["prompt_hashes"]["messages_sha256"],
            "status": "generation_failed",
            "proposed_concepts": None,
            "accepted_concepts": None,
            "proposed_relations": None,
            "accepted_relations": None,
            "abstentions": None,
            "rejection_reason_counts": None,
            "error": manifest.get("strict_json_error"),
        }
        raw_bank_path = run_dir / "raw_candidate_bank.json"
        if raw_bank_path.exists() and schema_pair_id in payloads:
            try:
                ledger = VALIDATOR.validate_and_materialize(payloads[schema_pair_id], raw_bank_path)
            except Exception as exc:
                row["status"] = "contract_failed"
                row["error"] = str(exc)
                (run_dir / "acceptance_error.txt").write_text(str(exc) + "\n", encoding="utf-8")
            else:
                (run_dir / "decision_ledger.json").write_text(
                    json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
                row.update(ledger["summary"])
                row["status"] = "materialized"
                row["error"] = None
        elif schema_pair_id not in payloads:
            row["error"] = f"No payload found for schema_pair_id={schema_pair_id}"
        rows.append(row)

    args.run_root.mkdir(parents=True, exist_ok=True)
    (args.run_root / "run_summary.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    fieldnames = list(rows[0]) if rows else ["model", "provider", "schema_pair_id", "status"]
    with (args.run_root / "run_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            serialized = dict(row)
            if isinstance(serialized.get("rejection_reason_counts"), dict):
                serialized["rejection_reason_counts"] = json.dumps(
                    serialized["rejection_reason_counts"], ensure_ascii=False, sort_keys=True
                )
            writer.writerow(serialized)

    print(json.dumps({"runs": len(rows), "materialized": sum(row["status"] == "materialized" for row in rows), "generation_failed": sum(row["status"] == "generation_failed" for row in rows), "contract_failed": sum(row["status"] == "contract_failed" for row in rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
