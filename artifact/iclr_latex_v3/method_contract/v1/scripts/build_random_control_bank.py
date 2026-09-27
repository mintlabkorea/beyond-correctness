#!/usr/bin/env python3
"""Build deterministic capacity-matched random banks that pass CRTA acceptance."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_candidates.py"
SPEC = importlib.util.spec_from_file_location("crta_validate_candidates", VALIDATOR_PATH)
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VALIDATOR)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_json(value: Any) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--accepted-ledger", type=Path, required=True)
    parser.add_argument("--dsl", type=Path, default=ROOT / "dsl" / "dsl_v1.json")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--runtime-maps", type=Path)
    parser.add_argument("--runtime-map-key")
    parser.add_argument("--forbidden-source", action="append", default=[])
    parser.add_argument("--forbidden-target", action="append", default=[])
    parser.add_argument("--max-sampling-attempts", type=int, default=128)
    return parser.parse_args()


def tables(payload: Mapping[str, Any]) -> dict[str, dict[str, Mapping[str, Any]]]:
    return {
        table["table_id"]: {column["column_id"]: column for column in table["columns"]}
        for table in payload["tables"]
    }


def eligible_features(index: Mapping[str, Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [
        column
        for column in index.values()
        if column["role"] == "feature" and column["candidate_eligible"]
    ]


def runtime_available(
    column_id: str,
    side: str,
    runtime_maps: Mapping[str, Mapping[str, str | None]] | None,
) -> bool:
    if runtime_maps is None:
        return True
    return runtime_maps[side].get(column_id) is not None


def evidence(column: Mapping[str, Any]) -> list[str]:
    spans = list(column.get("evidence_span_ids", []))
    if not spans:
        raise ValueError(f"Random-control column lacks evidence: {column['column_id']}")
    return spans


def choose_without_replacement(
    rng: np.random.Generator,
    pool: list[Mapping[str, Any]],
    count: int,
    excluded_ids: set[str],
) -> list[Mapping[str, Any]]:
    preferred = [column for column in pool if column["column_id"] not in excluded_ids]
    candidates = preferred if len(preferred) >= count else pool
    if len(candidates) < count:
        raise ValueError(f"Random pool has {len(candidates)} columns but needs {count}")
    selected = rng.choice(len(candidates), size=count, replace=False)
    return [candidates[int(index)] for index in selected]


def random_concepts(
    rng: np.random.Generator,
    originals: list[Mapping[str, Any]],
    index: Mapping[str, Mapping[str, Mapping[str, Any]]],
    runtime_maps: Mapping[str, Mapping[str, str | None]] | None,
    forbidden: Mapping[str, set[str]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for candidate in originals:
        item = deepcopy(candidate)
        item["canonical_name"] = f"random_control_{candidate['candidate_id']}"
        item["description"] = (
            "Capacity-matched random valid concept; membership was sampled before downstream fitting."
        )
        item["confidence"] = 0.0
        for side in ("source", "target"):
            count = len(candidate["members"][side])
            original_ids = {member["column_id"] for member in candidate["members"][side]}
            original_blocked = bool(original_ids & forbidden[side])
            original_active = not original_blocked and any(
                runtime_available(column_id, side, runtime_maps)
                for column_id in original_ids
            )
            pool = eligible_features(index[side])
            if original_blocked:
                forced_ids = sorted(original_ids & forbidden[side])
                forced = index[side][forced_ids[0]]
                remaining_pool = [
                    column
                    for column in pool
                    if column["column_id"] not in forbidden[side]
                ]
                selected = [forced] + choose_without_replacement(
                    rng,
                    remaining_pool,
                    count - 1,
                    original_ids | {forced["column_id"]},
                )
                rng.shuffle(selected)
            else:
                pool = [
                    column
                    for column in pool
                    if column["column_id"] not in forbidden[side]
                    and runtime_available(column["column_id"], side, runtime_maps)
                    == original_active
                ]
                selected = choose_without_replacement(rng, pool, count, original_ids)
            item["members"][side] = [
                {
                    "column_id": column["column_id"],
                    "evidence_span_ids": evidence(column),
                }
                for column in selected
            ]
        output.append(item)
    return output


def dimension(column: Mapping[str, Any]) -> str | None:
    unit = column.get("unit")
    return None if not unit else str(unit["dimension"])


def pools_by_dimension(
    index: Mapping[str, Mapping[str, Mapping[str, Any]]]
) -> dict[str, dict[str, list[Mapping[str, Any]]]]:
    output: dict[str, dict[str, list[Mapping[str, Any]]]] = {}
    for side in ("source", "target"):
        for column in eligible_features(index[side]):
            if column["dtype"] not in {"numeric", "integer"}:
                continue
            dim = dimension(column)
            if dim is None:
                continue
            output.setdefault(dim, {"source": [], "target": []})[side].append(column)
    return output


def random_relations(
    rng: np.random.Generator,
    originals: list[Mapping[str, Any]],
    index: Mapping[str, Mapping[str, Mapping[str, Any]]],
    dsl: Mapping[str, Any],
    runtime_maps: Mapping[str, Mapping[str, str | None]] | None,
    forbidden: Mapping[str, set[str]],
) -> list[dict[str, Any]]:
    dimension_pools = pools_by_dimension(index)
    output: list[dict[str, Any]] = []
    for candidate in originals:
        item = deepcopy(candidate)
        item["canonical_name"] = f"random_control_{candidate['candidate_id']}"
        item["description"] = (
            "Capacity-matched random valid relation; typed endpoints were sampled before downstream fitting."
        )
        item["confidence"] = 0.0
        operation = dsl["operations"][candidate["operation"]["name"]]
        value_args = [
            name for name in operation["arguments"] if operation["argument_roles"][name] == "value"
        ]
        groups = [list(group) for group in operation["same_dimension_groups"]]
        grouped = {name for group in groups for name in group}
        groups.extend([[name] for name in value_args if name not in grouped])
        for side in ("source", "target"):
            if any(
                endpoint["kind"] != "column"
                for endpoint in candidate["bindings"][side]["arguments"].values()
            ):
                raise ValueError(
                    "Runtime-matched random controls currently require direct-column relation endpoints"
                )
        selected_by_side: dict[str, dict[str, Mapping[str, Any]]] = {
            "source": {},
            "target": {},
        }
        used: dict[str, set[str]] = {"source": set(), "target": set()}
        for group in groups:
            expected: dict[str, tuple[bool, bool, set[str]]] = {}
            for side in ("source", "target"):
                original_ids = {
                    candidate["bindings"][side]["arguments"][argument]["id"]
                    for argument in group
                }
                blocked = bool(original_ids & forbidden[side])
                active = not blocked and all(
                    runtime_available(column_id, side, runtime_maps)
                    for column_id in original_ids
                )
                expected[side] = (blocked, active, original_ids)
            dimensions = [
                dim
                for dim, side_pools in dimension_pools.items()
                if all(
                    (
                        any(
                            column["column_id"] in expected[side][2] & forbidden[side]
                            for column in side_pools[side]
                        )
                        and len(side_pools[side]) >= len(group)
                        if expected[side][0]
                        else len(
                            [
                                column
                                for column in side_pools[side]
                                if column["column_id"] not in forbidden[side]
                                and runtime_available(
                                    column["column_id"], side, runtime_maps
                                )
                                == expected[side][1]
                            ]
                        )
                        >= len(group)
                    )
                    for side in ("source", "target")
                )
            ]
            rng.shuffle(dimensions)
            chosen = None
            for dim in dimensions:
                if all(
                    len(
                        [
                            column
                            for column in dimension_pools[dim][side]
                            if column["column_id"] not in used[side]
                            and (
                                column["column_id"] in expected[side][2] & forbidden[side]
                                if expected[side][0]
                                else column["column_id"] not in forbidden[side]
                                and runtime_available(
                                    column["column_id"], side, runtime_maps
                                )
                                == expected[side][1]
                            )
                        ]
                    )
                    >= (1 if expected[side][0] else len(group))
                    for side in ("source", "target")
                ):
                    chosen = dim
                    break
            if chosen is None:
                raise ValueError(
                    f"No common unit dimension can support relation group {group}"
                )
            for side in ("source", "target"):
                blocked, active, original_ids = expected[side]
                same_dimension = [
                    column
                    for column in dimension_pools[chosen][side]
                    if column["column_id"] not in used[side]
                ]
                if blocked:
                    forced_candidates = [
                        column
                        for column in same_dimension
                        if column["column_id"] in original_ids & forbidden[side]
                    ]
                    if not forced_candidates:
                        raise ValueError("Could not preserve forbidden relation endpoint")
                    forced = forced_candidates[0]
                    remainder = [
                        column
                        for column in same_dimension
                        if column["column_id"] not in forbidden[side]
                    ]
                    picked = [forced] + choose_without_replacement(
                        rng, remainder, len(group) - 1, original_ids
                    )
                    rng.shuffle(picked)
                else:
                    available = [
                        column
                        for column in same_dimension
                        if column["column_id"] not in forbidden[side]
                        and runtime_available(column["column_id"], side, runtime_maps)
                        == active
                    ]
                    picked = choose_without_replacement(
                        rng, available, len(group), original_ids
                    )
                for argument, column in zip(group, picked):
                    selected_by_side[side][argument] = column
                    used[side].add(column["column_id"])

        # Current accepted v1 banks contain only value arguments. Structural
        # temporal roles are retained from the original if introduced later.
        for side in ("source", "target"):
            arguments = deepcopy(candidate["bindings"][side]["arguments"])
            for argument, column in selected_by_side[side].items():
                arguments[argument] = {"kind": "column", "id": column["column_id"]}
            selected_columns = list(selected_by_side[side].values())
            spans = sorted({span for column in selected_columns for span in evidence(column)})
            item["bindings"][side] = {
                "arguments": arguments,
                "evidence_span_ids": spans,
            }
        output.append(item)
    return output


def main() -> int:
    args = parse_args()
    payload = load_json(args.payload)
    ledger = load_json(args.accepted_ledger)
    dsl = load_json(args.dsl)
    accepted = ledger["accepted_bank"]
    index = tables(payload)
    if bool(args.runtime_maps) != bool(args.runtime_map_key):
        raise ValueError("--runtime-maps and --runtime-map-key must be provided together")
    runtime_maps = None
    if args.runtime_maps:
        runtime_maps = load_json(args.runtime_maps)[args.runtime_map_key]
    forbidden = {
        "source": set(args.forbidden_source),
        "target": set(args.forbidden_target),
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = args.out_dir / "raw_candidate_bank.json"
    expected = {
        "accepted_concepts": len(accepted["concept_candidates"]),
        "accepted_relations": len(accepted["relation_candidates"]),
    }
    decision = None
    raw = None
    sampling_attempt = None
    last_summary = None
    for attempt in range(args.max_sampling_attempts):
        rng = np.random.default_rng(np.random.SeedSequence([args.seed, attempt]))
        raw = {
            "contract_version": payload["contract_version"],
            "schema_pair_id": payload["schema_pair_id"],
            "concept_candidates": random_concepts(
                rng, accepted["concept_candidates"], index, runtime_maps, forbidden
            ),
            "relation_candidates": random_relations(
                rng, accepted["relation_candidates"], index, dsl, runtime_maps, forbidden
            ),
            "abstentions": [],
        }
        raw_path.write_text(
            json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        current = VALIDATOR.validate_and_materialize(args.payload, raw_path)
        last_summary = current["summary"]
        if all(last_summary[key] == value for key, value in expected.items()):
            decision = current
            sampling_attempt = attempt
            break
    if decision is None or raw is None or sampling_attempt is None:
        raise RuntimeError(
            "Random bank failed capacity match after "
            f"{args.max_sampling_attempts} attempts: {last_summary} expected {expected}"
        )
    summary = decision["summary"]
    (args.out_dir / "decision_ledger.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    manifest = {
        "control": (
            "task_conditioned_runtime_capacity_matched_random_valid_bank"
            if runtime_maps is not None
            else "capacity_matched_random_valid_bank"
        ),
        "contract_version": payload["contract_version"],
        "schema_pair_id": payload["schema_pair_id"],
        "seed": args.seed,
        "sampling_attempt": sampling_attempt,
        "max_sampling_attempts": args.max_sampling_attempts,
        "runtime_map_key": args.runtime_map_key,
        "forbidden": {side: sorted(values) for side, values in forbidden.items()},
        "source_accepted_ledger": str(args.accepted_ledger),
        "source_accepted_ledger_sha256": hashlib.sha256(
            args.accepted_ledger.read_bytes()
        ).hexdigest(),
        "payload_sha256": hashlib.sha256(args.payload.read_bytes()).hexdigest(),
        "raw_candidate_bank_sha256": sha256_json(raw),
        "summary": summary,
    }
    (args.out_dir / "control_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
