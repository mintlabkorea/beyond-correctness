#!/usr/bin/env python3
"""Summarize frozen proposer banks, runtime activity, provenance, and overlap."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def concept_signature(candidate: Mapping[str, Any]) -> str:
    value = {
        side: sorted(member["column_id"] for member in candidate["members"][side])
        for side in ("source", "target")
    }
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def endpoint_signature(endpoint: Mapping[str, Any]) -> dict[str, Any]:
    return {key: endpoint[key] for key in sorted(endpoint)}


def relation_signature(candidate: Mapping[str, Any]) -> str:
    value = {
        "operation": candidate["operation"],
        "bindings": {
            side: {
                key: endpoint_signature(endpoint)
                for key, endpoint in sorted(
                    candidate["bindings"][side]["arguments"].items()
                )
            }
            for side in ("source", "target")
        },
    }
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def candidate_evidence(candidate: Mapping[str, Any], kind: str) -> list[str]:
    spans: set[str] = set()
    if kind == "concept":
        for side in ("source", "target"):
            for member in candidate["members"][side]:
                spans.update(member["evidence_span_ids"])
    else:
        for side in ("source", "target"):
            spans.update(candidate["bindings"][side]["evidence_span_ids"])
    return sorted(spans)


def concept_active(
    candidate: Mapping[str, Any], runtime_maps: Mapping[str, Mapping[str, str | None]]
) -> bool:
    return all(
        runtime_maps[side].get(member["column_id"], member["column_id"]) is not None
        for side in ("source", "target")
        for member in candidate["members"][side]
    )


def relation_active(
    candidate: Mapping[str, Any],
    concepts: Mapping[str, Mapping[str, Any]],
    runtime_maps: Mapping[str, Mapping[str, str | None]],
) -> bool:
    for side in ("source", "target"):
        for endpoint in candidate["bindings"][side]["arguments"].values():
            if endpoint["kind"] == "column":
                if runtime_maps[side].get(endpoint["id"], endpoint["id"]) is None:
                    return False
            elif not concept_active(concepts[endpoint["id"]], runtime_maps):
                return False
    return True


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return 1.0 if not union else len(left & right) / len(union)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument(
        "--manifest-name",
        choices=("generation_manifest.json", "transport_normalization_manifest.json"),
        default="generation_manifest.json",
    )
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--runtime-maps", type=Path)
    parser.add_argument("--runtime-map-key")
    parser.add_argument("--reference-run", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if bool(args.runtime_maps) != bool(args.runtime_map_key):
        raise ValueError("--runtime-maps and --runtime-map-key must be paired")
    payload = load_json(args.payload)
    span_index = {span["span_id"]: span for span in payload["evidence_spans"]}
    if args.runtime_maps:
        runtime_maps = load_json(args.runtime_maps)[args.runtime_map_key]
    else:
        runtime_maps = {
            table["table_id"]: {
                column["column_id"]: column["column_id"]
                for column in table["columns"]
            }
            for table in payload["tables"]
        }

    manifests = sorted(args.run_root.rglob(args.manifest_name))
    model_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    provenance_rows: list[dict[str, Any]] = []
    signatures: dict[str, dict[str, set[str]]] = {}
    for manifest_path in manifests:
        manifest = load_json(manifest_path)
        generation_manifest = manifest
        if args.manifest_name == "transport_normalization_manifest.json":
            source = Path(manifest["source_run_dir"]) / "generation_manifest.json"
            generation_manifest = load_json(source)
        if manifest.get("schema_pair_id") != payload["schema_pair_id"]:
            continue
        run_dir = manifest_path.parent
        run_id = str(run_dir.relative_to(args.run_root))
        ledger_path = run_dir / "decision_ledger.json"
        ledger = load_json(ledger_path) if ledger_path.exists() else None
        summary = ledger["summary"] if ledger else {}
        model_rows.append(
            {
                "run_id": run_id,
                "provider": manifest.get("provider"),
                "model": manifest.get("model"),
                "return_code": generation_manifest.get("return_code"),
                "strict_json_parse": generation_manifest.get("strict_json_parse"),
                "track_status": manifest.get("status"),
                "normalization_action": manifest.get("normalization_action"),
                "input_tokens": generation_manifest.get("runtime", {}).get("input_tokens"),
                "generated_tokens": generation_manifest.get("runtime", {}).get("generated_tokens"),
                "proposed_concepts": summary.get("proposed_concepts", 0),
                "accepted_concepts": summary.get("accepted_concepts", 0),
                "proposed_relations": summary.get("proposed_relations", 0),
                "accepted_relations": summary.get("accepted_relations", 0),
                "abstentions": summary.get("abstentions", 0),
                "ledger_exists": ledger is not None,
            }
        )
        signatures[run_id] = {"concept": set(), "relation": set()}
        if ledger is None:
            continue
        accepted = ledger["accepted_bank"]
        concept_index = {
            item["candidate_id"]: item
            for item in accepted.get("concept_candidates", [])
        }
        groups: Iterable[tuple[str, Mapping[str, Any]]] = (
            [("concept", item) for item in concept_index.values()]
            + [
                ("relation", item)
                for item in accepted.get("relation_candidates", [])
            ]
        )
        for kind, candidate in groups:
            active = (
                concept_active(candidate, runtime_maps)
                if kind == "concept"
                else relation_active(candidate, concept_index, runtime_maps)
            )
            signature = (
                concept_signature(candidate)
                if kind == "concept"
                else relation_signature(candidate)
            )
            signatures[run_id][kind].add(signature)
            evidence_ids = candidate_evidence(candidate, kind)
            documents = sorted(
                {span_index[span_id]["document_id"] for span_id in evidence_ids}
            )
            candidate_rows.append(
                {
                    "run_id": run_id,
                    "model": manifest.get("model"),
                    "kind": kind,
                    "candidate_id": candidate["candidate_id"],
                    "canonical_name": candidate["canonical_name"],
                    "rank": candidate["rank"],
                    "confidence": candidate["confidence"],
                    "runtime_active": active,
                    "evidence_span_count": len(evidence_ids),
                    "document_count": len(documents),
                    "signature": signature,
                }
            )
            for span_id in evidence_ids:
                span = span_index[span_id]
                provenance_rows.append(
                    {
                        "run_id": run_id,
                        "model": manifest.get("model"),
                        "kind": kind,
                        "candidate_id": candidate["candidate_id"],
                        "span_id": span_id,
                        "document_id": span["document_id"],
                        "applies_to": ";".join(span["applies_to"]),
                        "location": span["location"],
                        "span_sha256": span["sha256"],
                    }
                )

    reference_id = str(args.reference_run.relative_to(args.run_root))
    if reference_id not in signatures:
        raise ValueError(f"Reference run was not summarized: {reference_id}")
    overlap_rows: list[dict[str, Any]] = []
    for run_id, by_kind in sorted(signatures.items()):
        for kind in ("concept", "relation"):
            reference = signatures[reference_id][kind]
            current = by_kind[kind]
            overlap_rows.append(
                {
                    "run_id": run_id,
                    "reference_run_id": reference_id,
                    "kind": kind,
                    "accepted_count": len(current),
                    "reference_count": len(reference),
                    "intersection_count": len(current & reference),
                    "union_count": len(current | reference),
                    "jaccard": jaccard(current, reference),
                }
            )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    dump_csv(
        args.out_dir / "model_summary.csv",
        model_rows,
        list(model_rows[0]) if model_rows else ["run_id"],
    )
    dump_csv(
        args.out_dir / "accepted_candidates.csv",
        candidate_rows,
        list(candidate_rows[0]) if candidate_rows else ["run_id"],
    )
    dump_csv(
        args.out_dir / "evidence_provenance.csv",
        provenance_rows,
        list(provenance_rows[0]) if provenance_rows else ["run_id"],
    )
    dump_csv(
        args.out_dir / "overlap_vs_reference.csv",
        overlap_rows,
        list(overlap_rows[0]) if overlap_rows else ["run_id"],
    )
    summary = {
        "schema_pair_id": payload["schema_pair_id"],
        "reference_run_id": reference_id,
        "run_count": len(model_rows),
        "accepted_candidate_count": len(candidate_rows),
        "evidence_provenance_row_count": len(provenance_rows),
    }
    (args.out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
