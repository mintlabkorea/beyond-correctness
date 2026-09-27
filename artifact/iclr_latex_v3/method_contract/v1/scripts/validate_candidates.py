#!/usr/bin/env python3
"""Validate and mechanically accept CRTA v1 concept/relation candidates."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator


CONTRACT_VERSION = "crta-1.0.0"
NUMERIC_DTYPES = {"numeric", "integer"}
POSITIVE_DOMAINS = {"positive", "nonnegative"}
CONCEPT_CHANNELS = {"mean", "std", "range", "observed_fraction"}
ROOT = Path(__file__).resolve().parents[1]


class ContractError(RuntimeError):
    """Raised when a whole input/output artifact violates its JSON contract."""


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"Cannot read JSON {path}: {exc}") from exc


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def object_hash(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def schema_validate(instance: Any, schema: dict[str, Any], label: str) -> None:
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path))
    if not errors:
        return
    lines = []
    for error in errors[:30]:
        location = "/".join(str(part) for part in error.absolute_path) or "<root>"
        lines.append(f"{location}: {error.message}")
    if len(errors) > 30:
        lines.append(f"... {len(errors) - 30} more schema errors")
    raise ContractError(f"{label} JSON Schema validation failed:\n" + "\n".join(lines))


def _duplicates(values: list[str]) -> set[str]:
    counts = Counter(values)
    return {value for value, count in counts.items() if count > 1}


def build_context(payload: dict[str, Any]) -> dict[str, Any]:
    problems: list[str] = []
    if payload["contract_version"] != CONTRACT_VERSION:
        problems.append("input contract_version mismatch")

    table_ids = [table["table_id"] for table in payload["tables"]]
    if sorted(table_ids) != ["source", "target"]:
        problems.append("tables must contain exactly one source and one target")

    spans: dict[str, dict[str, Any]] = {}
    for span in payload["evidence_spans"]:
        span_id = span["span_id"]
        if span_id in spans:
            problems.append(f"duplicate evidence span_id: {span_id}")
        spans[span_id] = span
        actual_hash = hashlib.sha256(span["text"].encode("utf-8")).hexdigest()
        if actual_hash != span["sha256"]:
            problems.append(f"evidence hash mismatch: {span_id}")
        if span["candidate_eligible"] and span["exclusion_reason"] is not None:
            problems.append(f"eligible span has exclusion_reason: {span_id}")
        if not span["candidate_eligible"] and not span["exclusion_reason"]:
            problems.append(f"ineligible span lacks exclusion_reason: {span_id}")

    columns: dict[str, dict[str, dict[str, Any]]] = {"source": {}, "target": {}}
    for table in payload["tables"]:
        side = table["table_id"]
        for column in table["columns"]:
            column_id = column["column_id"]
            if column_id in columns[side]:
                problems.append(f"duplicate column_id in {side}: {column_id}")
            columns[side][column_id] = column
            for span_id in column["evidence_span_ids"]:
                span = spans.get(span_id)
                if span is None:
                    problems.append(f"column {side}/{column_id} references unknown span: {span_id}")
                elif side not in span["applies_to"]:
                    problems.append(f"column {side}/{column_id} references out-of-scope span: {span_id}")

            if column["candidate_eligible"] and column["role"] != "feature":
                problems.append(f"only feature columns may be candidate_eligible: {side}/{column_id}")
            if column["dtype"] in NUMERIC_DTYPES and column["role"] == "feature" and column["unit"] is None:
                # Unitless variables are represented explicitly with dimension=dimensionless.
                problems.append(f"numeric feature lacks explicit unit metadata: {side}/{column_id}")

    if problems:
        raise ContractError("Input integrity validation failed:\n" + "\n".join(f"- {item}" for item in problems))

    return {"columns": columns, "spans": spans}


def evidence_reasons(
    span_ids: list[str], side: str, spans: dict[str, dict[str, Any]]
) -> set[str]:
    reasons: set[str] = set()
    if not span_ids:
        reasons.add("R_RELATION_EVIDENCE_MISSING")
        return reasons
    for span_id in span_ids:
        span = spans.get(span_id)
        if span is None:
            reasons.add("R_EVIDENCE_NOT_FOUND")
            continue
        if not span["candidate_eligible"]:
            reasons.add("R_EVIDENCE_INELIGIBLE")
        if side not in span["applies_to"]:
            reasons.add("R_EVIDENCE_SCOPE")
    return reasons


def validate_concept(
    candidate: dict[str, Any], context: dict[str, Any]
) -> tuple[set[str], tuple[Any, ...]]:
    reasons: set[str] = set()
    members_by_side = candidate["members"]
    source_count = len(members_by_side["source"])
    target_count = len(members_by_side["target"])
    if source_count == 0 or target_count == 0:
        reasons.add("R_CONCEPT_NOT_CROSS_SCHEMA")
    if source_count + target_count < 3 or max(source_count, target_count) < 2:
        reasons.add("R_CONCEPT_NOT_GROUP")

    fingerprint_parts: list[tuple[str, tuple[str, ...]]] = []
    for side in ("source", "target"):
        members = members_by_side[side]
        member_ids = [member["column_id"] for member in members]
        if _duplicates(member_ids):
            reasons.add("R_DUPLICATE_MEMBER")
        fingerprint_parts.append((side, tuple(sorted(member_ids))))

        for member in members:
            column_id = member["column_id"]
            column = context["columns"][side].get(column_id)
            if column is None:
                reasons.add("R_COLUMN_NOT_FOUND")
                reasons.update(evidence_reasons(member["evidence_span_ids"], side, context["spans"]))
                continue
            if not column["candidate_eligible"]:
                reasons.add("R_COLUMN_INELIGIBLE")
            if column["role"] != "feature":
                reasons.add("R_LEAKAGE_ROLE")
            linked = set(member["evidence_span_ids"]).issubset(set(column["evidence_span_ids"]))
            if not linked:
                reasons.add("R_MEMBER_EVIDENCE_NOT_LINKED")
            reasons.update(evidence_reasons(member["evidence_span_ids"], side, context["spans"]))

    return reasons, tuple(fingerprint_parts)


def endpoint_metadata(
    ref: dict[str, Any],
    side: str,
    argument_role: str,
    context: dict[str, Any],
    accepted_concepts: set[str],
) -> tuple[dict[str, Any], set[str]]:
    reasons: set[str] = set()
    kind = ref["kind"]
    if kind == "concept":
        if ref["id"] not in accepted_concepts:
            reasons.add("R_REF_NOT_ACCEPTED")
        if ref.get("channel") not in CONCEPT_CHANNELS:
            reasons.add("R_ARGUMENT_SET_MISMATCH")
        if argument_role != "value":
            reasons.add("R_TEMPORAL_CONTEXT_ROLE")
        return {
            "kind": "concept",
            "id": ref["id"],
            "dimension": "standardized",
            "dtype": "numeric",
            "value_domain": "real",
        }, reasons

    column = context["columns"][side].get(ref["id"])
    if column is None:
        reasons.add("R_COLUMN_NOT_FOUND")
        return {
            "kind": "column",
            "id": ref["id"],
            "dimension": None,
            "dtype": None,
            "value_domain": "unknown",
        }, reasons

    if argument_role == "value":
        if not column["candidate_eligible"]:
            reasons.add("R_COLUMN_INELIGIBLE")
        if column["role"] != "feature":
            reasons.add("R_LEAKAGE_ROLE")
        if column["dtype"] not in NUMERIC_DTYPES:
            reasons.add("R_NON_NUMERIC_ARGUMENT")
    elif argument_role == "group_key":
        if column["role"] != "group_key":
            reasons.add("R_TEMPORAL_CONTEXT_ROLE")
    elif argument_role == "time_index":
        if column["role"] != "time_index":
            reasons.add("R_TEMPORAL_CONTEXT_ROLE")
    else:
        reasons.add("R_ARGUMENT_SET_MISMATCH")

    unit = column["unit"]
    dimension = unit["dimension"] if unit is not None else None
    if argument_role == "value" and dimension in {None, "unknown"}:
        reasons.add("R_UNIT_DIMENSION_UNKNOWN")
    if argument_role == "group_key":
        dimension = "group_key"
    elif argument_role == "time_index":
        dimension = "time_index"

    return {
        "kind": "column",
        "id": ref["id"],
        "dimension": dimension,
        "dtype": column["dtype"],
        "value_domain": column["value_domain"],
    }, reasons


def validate_parameters(parameters: dict[str, Any], spec: dict[str, Any]) -> set[str]:
    reasons: set[str] = set()
    expected = spec["parameters"]
    if set(parameters) != set(expected):
        reasons.add("R_PARAMETER_MISMATCH")
        return reasons
    for name, rule in expected.items():
        value = parameters[name]
        if rule["type"] == "integer" and (isinstance(value, bool) or not isinstance(value, int)):
            reasons.add("R_PARAMETER_MISMATCH")
            continue
        if "minimum" in rule and value < rule["minimum"]:
            reasons.add("R_PARAMETER_MISMATCH")
        if "maximum" in rule and value > rule["maximum"]:
            reasons.add("R_PARAMETER_MISMATCH")
    return reasons


def relation_fingerprint(candidate: dict[str, Any]) -> tuple[Any, ...]:
    direction = candidate["direction"]
    binding_parts = []
    for side in ("source", "target"):
        arguments = candidate["bindings"][side]["arguments"]
        if direction in {"symmetric", "set"}:
            normalized = tuple(sorted(json.dumps(ref, sort_keys=True) for ref in arguments.values()))
        else:
            normalized = tuple(
                (name, json.dumps(ref, sort_keys=True)) for name, ref in sorted(arguments.items())
            )
        binding_parts.append((side, normalized))
    return (
        candidate["operation"]["name"],
        candidate["semantic_type"],
        tuple(sorted(candidate["operation"]["parameters"].items())),
        tuple(binding_parts),
    )


def validate_relation(
    candidate: dict[str, Any],
    context: dict[str, Any],
    accepted_concepts: set[str],
    dsl: dict[str, Any],
) -> tuple[set[str], tuple[Any, ...]]:
    reasons: set[str] = set()
    operation_name = candidate["operation"]["name"]
    spec = dsl["operations"].get(operation_name)
    if spec is None:
        reasons.add("R_UNKNOWN_OPERATION")
        return reasons, relation_fingerprint(candidate)

    if candidate["semantic_type"] not in spec["semantic_types"]:
        reasons.add("R_SEMANTIC_TYPE_MISMATCH")
    if candidate["direction"] != spec["direction"]:
        reasons.add("R_DIRECTION_MISMATCH")
    reasons.update(validate_parameters(candidate["operation"]["parameters"], spec))

    expected_arguments = set(spec["arguments"])
    source_arguments = candidate["bindings"]["source"]["arguments"]
    target_arguments = candidate["bindings"]["target"]["arguments"]
    if set(source_arguments) != expected_arguments or set(target_arguments) != expected_arguments:
        reasons.add("R_ARGUMENT_SET_MISMATCH")

    metadata: dict[str, dict[str, dict[str, Any]]] = {"source": {}, "target": {}}
    for side in ("source", "target"):
        binding = candidate["bindings"][side]
        reasons.update(evidence_reasons(binding["evidence_span_ids"], side, context["spans"]))
        for argument in sorted(expected_arguments & set(binding["arguments"])):
            endpoint, endpoint_reasons = endpoint_metadata(
                binding["arguments"][argument],
                side,
                spec["argument_roles"][argument],
                context,
                accepted_concepts,
            )
            metadata[side][argument] = endpoint
            reasons.update(endpoint_reasons)

        value_ids = [
            endpoint["id"]
            for argument, endpoint in metadata[side].items()
            if spec["argument_roles"][argument] == "value"
        ]
        if len(value_ids) != len(set(value_ids)):
            reasons.add("R_DUPLICATE_ENDPOINT")

    for argument in expected_arguments:
        if argument not in metadata["source"] or argument not in metadata["target"]:
            continue
        source_endpoint = metadata["source"][argument]
        target_endpoint = metadata["target"][argument]
        if source_endpoint["kind"] != target_endpoint["kind"]:
            reasons.add("R_ENDPOINT_KIND_MISMATCH")
        if source_endpoint["kind"] == "concept" and source_endpoint["id"] != target_endpoint["id"]:
            reasons.add("R_ENDPOINT_KIND_MISMATCH")
        if source_endpoint["dimension"] != target_endpoint["dimension"]:
            reasons.add("R_UNIT_CONTRACT")

    for side in ("source", "target"):
        for group in spec["same_dimension_groups"]:
            dimensions = {
                metadata[side][argument]["dimension"]
                for argument in group
                if argument in metadata[side]
            }
            if len(dimensions) > 1:
                reasons.add("R_UNIT_CONTRACT")

        for argument in spec["positive_arguments"]:
            endpoint = metadata[side].get(argument)
            if endpoint is not None and endpoint["value_domain"] not in POSITIVE_DOMAINS:
                reasons.add("R_VALUE_DOMAIN")

    return reasons, relation_fingerprint(candidate)


def materialize(
    payload: dict[str, Any], raw_bank: dict[str, Any], dsl: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    decisions: list[dict[str, Any]] = []
    accepted_concepts: list[dict[str, Any]] = []
    accepted_relations: list[dict[str, Any]] = []
    accepted_concept_ids: set[str] = set()
    concept_fingerprints: set[tuple[Any, ...]] = set()
    relation_fingerprints: set[tuple[Any, ...]] = set()

    all_candidates = raw_bank["concept_candidates"] + raw_bank["relation_candidates"]
    duplicate_ids = _duplicates([candidate["candidate_id"] for candidate in all_candidates])
    duplicate_concept_ranks = _duplicates(
        [str(candidate["rank"]) for candidate in raw_bank["concept_candidates"]]
    )
    duplicate_relation_ranks = _duplicates(
        [str(candidate["rank"]) for candidate in raw_bank["relation_candidates"]]
    )

    for candidate in sorted(raw_bank["concept_candidates"], key=lambda item: (item["rank"], item["candidate_id"])):
        reasons, fingerprint = validate_concept(candidate, context)
        if candidate["candidate_id"] in duplicate_ids:
            reasons.add("R_DUPLICATE_ID")
        if str(candidate["rank"]) in duplicate_concept_ranks:
            reasons.add("R_DUPLICATE_RANK")
        if fingerprint in concept_fingerprints:
            reasons.add("R_DUPLICATE_CANDIDATE")
        if not reasons and len(accepted_concepts) >= payload["candidate_budgets"]["max_concepts"]:
            reasons.add("R_BUDGET_EXCEEDED")
        accepted = not reasons
        if accepted:
            accepted_concepts.append(candidate)
            accepted_concept_ids.add(candidate["candidate_id"])
            concept_fingerprints.add(fingerprint)
        decisions.append({
            "candidate_id": candidate["candidate_id"],
            "kind": "concept",
            "rank": candidate["rank"],
            "decision": "accepted" if accepted else "rejected",
            "reason_codes": [] if accepted else sorted(reasons),
        })

    for candidate in sorted(raw_bank["relation_candidates"], key=lambda item: (item["rank"], item["candidate_id"])):
        reasons, fingerprint = validate_relation(candidate, context, accepted_concept_ids, dsl)
        if candidate["candidate_id"] in duplicate_ids:
            reasons.add("R_DUPLICATE_ID")
        if str(candidate["rank"]) in duplicate_relation_ranks:
            reasons.add("R_DUPLICATE_RANK")
        if fingerprint in relation_fingerprints:
            reasons.add("R_DUPLICATE_CANDIDATE")
        if not reasons and len(accepted_relations) >= payload["candidate_budgets"]["max_relations"]:
            reasons.add("R_BUDGET_EXCEEDED")
        accepted = not reasons
        if accepted:
            accepted_relations.append(candidate)
            relation_fingerprints.add(fingerprint)
        decisions.append({
            "candidate_id": candidate["candidate_id"],
            "kind": "relation",
            "rank": candidate["rank"],
            "decision": "accepted" if accepted else "rejected",
            "reason_codes": [] if accepted else sorted(reasons),
        })

    reason_counts = Counter(
        reason
        for decision in decisions
        for reason in decision["reason_codes"]
    )
    return {
        "contract_version": CONTRACT_VERSION,
        "dsl_version": dsl["dsl_version"],
        "schema_pair_id": payload["schema_pair_id"],
        "artifact_hashes": {
            "proposer_input_sha256": object_hash(payload),
            "raw_candidate_bank_sha256": object_hash(raw_bank),
            "dsl_sha256": object_hash(dsl),
        },
        "accepted_bank": {
            "concept_candidates": accepted_concepts,
            "relation_candidates": accepted_relations,
        },
        "decisions": decisions,
        "abstentions": raw_bank["abstentions"],
        "summary": {
            "proposed_concepts": len(raw_bank["concept_candidates"]),
            "accepted_concepts": len(accepted_concepts),
            "proposed_relations": len(raw_bank["relation_candidates"]),
            "accepted_relations": len(accepted_relations),
            "abstentions": len(raw_bank["abstentions"]),
            "rejection_reason_counts": dict(sorted(reason_counts.items())),
        },
    }


def validate_and_materialize(
    input_path: Path,
    output_path: Path,
    dsl_path: Path | None = None,
    input_schema_path: Path | None = None,
    output_schema_path: Path | None = None,
) -> dict[str, Any]:
    dsl_path = dsl_path or ROOT / "dsl" / "dsl_v1.json"
    input_schema_path = input_schema_path or ROOT / "schemas" / "proposer_input.schema.json"
    output_schema_path = output_schema_path or ROOT / "schemas" / "candidate_bank.schema.json"

    payload = load_json(input_path)
    raw_bank = load_json(output_path)
    dsl = load_json(dsl_path)
    input_schema = load_json(input_schema_path)
    output_schema = load_json(output_schema_path)

    Draft7Validator.check_schema(input_schema)
    Draft7Validator.check_schema(output_schema)
    schema_validate(payload, input_schema, "proposer input")
    schema_validate(raw_bank, output_schema, "candidate bank")

    if raw_bank["contract_version"] != payload["contract_version"]:
        raise ContractError("output contract_version does not match input")
    if raw_bank["schema_pair_id"] != payload["schema_pair_id"]:
        raise ContractError("output schema_pair_id does not match input")
    if dsl["contract_version"] != payload["contract_version"]:
        raise ContractError("DSL contract_version does not match input")

    context = build_context(payload)
    return materialize(payload, raw_bank, dsl, context)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Proposer input JSON")
    parser.add_argument("--output", type=Path, required=True, help="Raw LLM candidate-bank JSON")
    parser.add_argument("--dsl", type=Path, default=ROOT / "dsl" / "dsl_v1.json")
    parser.add_argument("--input-schema", type=Path, default=ROOT / "schemas" / "proposer_input.schema.json")
    parser.add_argument("--output-schema", type=Path, default=ROOT / "schemas" / "candidate_bank.schema.json")
    parser.add_argument("--decision-ledger", type=Path, help="Optional accepted-bank/decision JSON path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        ledger = validate_and_materialize(
            args.input,
            args.output,
            args.dsl,
            args.input_schema,
            args.output_schema,
        )
    except ContractError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.decision_ledger:
        args.decision_ledger.parent.mkdir(parents=True, exist_ok=True)
        args.decision_ledger.write_text(
            json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(ledger["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
