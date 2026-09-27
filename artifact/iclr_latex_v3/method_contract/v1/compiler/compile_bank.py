#!/usr/bin/env python3
"""Compile an accepted CRTA bank into a fixed-width downstream matrix.

The compiler is deliberately independent of a tabular backbone.  It consumes
one schema-local dataframe and a support/reference mask, fits every statistic
on that mask only, and emits the fixed interface described by ``DSL.md``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


CONCEPT_CHANNELS = ("mean", "std", "range", "observed_fraction")
RELATION_CHANNELS = ("value", "availability")


@dataclass(frozen=True)
class CompiledBank:
    values: np.ndarray
    feature_names: tuple[str, ...]
    metadata: dict[str, Any]


def _robust_fit(values: np.ndarray, fit_mask: np.ndarray) -> tuple[float, float]:
    support = np.asarray(values, dtype=np.float64)[fit_mask]
    support = support[np.isfinite(support)]
    if not len(support):
        return 0.0, 1.0
    center = float(np.median(support))
    q25, q75 = np.quantile(support, [0.25, 0.75])
    scale = float(q75 - q25)
    if not np.isfinite(scale) or scale <= 1.0e-8:
        scale = float(np.std(support))
    if not np.isfinite(scale) or scale <= 1.0e-8:
        scale = 1.0
    return center, scale


def _table(payload: Mapping[str, Any], side: str) -> Mapping[str, Any]:
    matches = [table for table in payload["tables"] if table["table_id"] == side]
    if len(matches) != 1:
        raise ValueError(f"Expected one payload table for side={side}; found {len(matches)}")
    return matches[0]


def _column_index(payload: Mapping[str, Any], side: str) -> dict[str, Mapping[str, Any]]:
    return {column["column_id"]: column for column in _table(payload, side)["columns"]}


def _runtime_name(column_id: str, column_map: Mapping[str, str | None]) -> str | None:
    return column_map[column_id] if column_id in column_map else column_id


def _column_values(
    frame: pd.DataFrame,
    column_id: str,
    column_map: Mapping[str, str | None],
    column_meta: Mapping[str, Mapping[str, Any]],
    *,
    canonicalize: bool = True,
) -> np.ndarray:
    runtime_name = _runtime_name(column_id, column_map)
    if runtime_name is None or runtime_name not in frame.columns:
        return np.full(len(frame), np.nan, dtype=np.float64)
    if not canonicalize:
        return frame[runtime_name].to_numpy(copy=True)
    values = pd.to_numeric(frame[runtime_name], errors="coerce").to_numpy(np.float64)
    unit = column_meta[column_id].get("unit")
    if unit:
        values = values * float(unit["scale_to_canonical"]) + float(
            unit["offset_to_canonical"]
        )
    return values


def _compile_concepts(
    frame: pd.DataFrame,
    fit_mask: np.ndarray,
    candidates: Sequence[Mapping[str, Any]],
    side: str,
    column_map: Mapping[str, str | None],
    column_meta: Mapping[str, Mapping[str, Any]],
    forbidden_column_ids: set[str],
) -> tuple[dict[str, dict[str, np.ndarray]], list[dict[str, Any]]]:
    compiled: dict[str, dict[str, np.ndarray]] = {}
    records: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_id = candidate["candidate_id"]
        member_ids = [member["column_id"] for member in candidate["members"][side]]
        blocked = sorted(set(member_ids) & forbidden_column_ids)
        member_values: list[np.ndarray] = []
        fit_stats: list[dict[str, Any]] = []
        if not blocked:
            for member_id in member_ids:
                raw = _column_values(
                    frame, member_id, column_map, column_meta, canonicalize=True
                )
                center, scale = _robust_fit(raw, fit_mask)
                standardized = np.full(len(frame), np.nan, dtype=np.float64)
                observed = np.isfinite(raw)
                standardized[observed] = np.clip(
                    (raw[observed] - center) / scale, -10.0, 10.0
                )
                member_values.append(standardized)
                fit_stats.append(
                    {
                        "column_id": member_id,
                        "runtime_column": _runtime_name(member_id, column_map),
                        "center": center,
                        "scale": scale,
                        "runtime_observed_fraction": float(observed.mean()),
                    }
                )

        if blocked or not member_values:
            channels = {
                "mean": np.zeros(len(frame), dtype=np.float32),
                "std": np.zeros(len(frame), dtype=np.float32),
                "range": np.zeros(len(frame), dtype=np.float32),
                "observed_fraction": np.zeros(len(frame), dtype=np.float32),
            }
            runtime_missing_fraction = 1.0
        else:
            matrix = np.column_stack(member_values)
            observed = np.isfinite(matrix)
            counts = observed.sum(axis=1)
            safe = np.where(observed, matrix, 0.0)
            mean = np.divide(
                safe.sum(axis=1), counts, out=np.zeros(len(frame)), where=counts > 0
            )
            centered = np.where(observed, matrix - mean[:, None], 0.0)
            std = np.sqrt(
                np.divide(
                    np.square(centered).sum(axis=1),
                    counts,
                    out=np.zeros(len(frame)),
                    where=counts > 0,
                )
            )
            row_min = np.min(np.where(observed, matrix, np.inf), axis=1)
            row_max = np.max(np.where(observed, matrix, -np.inf), axis=1)
            value_range = np.where(counts > 0, row_max - row_min, 0.0)
            channels = {
                "mean": mean.astype(np.float32),
                "std": std.astype(np.float32),
                "range": value_range.astype(np.float32),
                "observed_fraction": (counts / len(member_ids)).astype(np.float32),
            }
            runtime_missing_fraction = float(np.mean(counts == 0))
        compiled[candidate_id] = channels
        records.append(
            {
                "candidate_id": candidate_id,
                "canonical_name": candidate["canonical_name"],
                "member_ids": member_ids,
                "blocked_forbidden_columns": blocked,
                "runtime_missing_fraction": runtime_missing_fraction,
                "member_fit": fit_stats,
            }
        )
    return compiled, records


def _resolve_endpoint(
    endpoint: Mapping[str, Any],
    frame: pd.DataFrame,
    column_map: Mapping[str, str | None],
    column_meta: Mapping[str, Mapping[str, Any]],
    concepts: Mapping[str, Mapping[str, np.ndarray]],
    *,
    canonicalize: bool = True,
) -> np.ndarray:
    if endpoint["kind"] == "column":
        return _column_values(
            frame, endpoint["id"], column_map, column_meta, canonicalize=canonicalize
        )
    return np.asarray(concepts[endpoint["id"]][endpoint["channel"]])


def _relation_forbidden(
    arguments: Mapping[str, Mapping[str, Any]],
    concept_candidates: Mapping[str, Mapping[str, Any]],
    side: str,
    forbidden_column_ids: set[str],
) -> list[str]:
    blocked: set[str] = set()
    for endpoint in arguments.values():
        if endpoint["kind"] == "column" and endpoint["id"] in forbidden_column_ids:
            blocked.add(endpoint["id"])
        elif endpoint["kind"] == "concept":
            concept = concept_candidates[endpoint["id"]]
            blocked.update(
                member["column_id"]
                for member in concept["members"][side]
                if member["column_id"] in forbidden_column_ids
            )
    return sorted(blocked)


def _temporal_operation(
    name: str,
    arguments: Mapping[str, np.ndarray],
    parameters: Mapping[str, Any],
) -> np.ndarray:
    value = np.asarray(arguments["value"], dtype=np.float64)
    group = np.asarray(arguments["group"])
    order = np.asarray(arguments["order"], dtype=np.float64)
    output = np.full(len(value), np.nan, dtype=np.float64)
    grouped = pd.Series(np.arange(len(value))).groupby(pd.Series(group), sort=False)
    for positions in grouped:
        indices = positions[1].to_numpy(dtype=np.int64)
        indices = indices[np.argsort(order[indices], kind="stable")]
        if name == "lag_difference":
            lag = int(parameters["lag"])
            for offset in range(lag, len(indices)):
                current, past = indices[offset], indices[offset - lag]
                if np.isfinite(value[current]) and np.isfinite(value[past]):
                    output[current] = value[current] - value[past]
        else:
            window = int(parameters["window"])
            for offset in range(window - 1, len(indices)):
                selected = indices[offset - window + 1 : offset + 1]
                x = order[selected]
                y = value[selected]
                if np.isfinite(x).all() and np.isfinite(y).all() and np.ptp(x) > 0:
                    x_centered = x - x.mean()
                    output[indices[offset]] = float(
                        np.dot(x_centered, y - y.mean()) / np.dot(x_centered, x_centered)
                    )
    return output


def _apply_operation(
    name: str,
    arguments: Mapping[str, np.ndarray],
    parameters: Mapping[str, Any],
) -> np.ndarray:
    eps = 1.0e-12
    if name in {"lag_difference", "trailing_slope"}:
        return _temporal_operation(name, arguments, parameters)
    a = {key: np.asarray(value, dtype=np.float64) for key, value in arguments.items()}
    if name == "difference":
        return a["lhs"] - a["rhs"]
    if name == "absolute_difference":
        return np.abs(a["lhs"] - a["rhs"])
    if name == "safe_ratio":
        denominator = a["denominator"]
        return np.divide(
            a["numerator"],
            denominator,
            out=np.full(len(denominator), np.nan),
            where=np.isfinite(denominator) & (np.abs(denominator) > eps),
        )
    if name == "normalized_difference":
        denominator = np.abs(a["lhs"]) + np.abs(a["rhs"])
        return np.divide(
            a["lhs"] - a["rhs"],
            denominator,
            out=np.full(len(denominator), np.nan),
            where=np.isfinite(denominator) & (denominator > eps),
        )
    if name == "product":
        return a["lhs"] * a["rhs"]
    if name == "sum2":
        return a["lhs"] + a["rhs"]
    if name == "ratio_of_differences":
        numerator = a["lhs_a"] - a["lhs_b"]
        denominator = a["rhs_a"] - a["rhs_b"]
        return np.divide(
            numerator,
            denominator,
            out=np.full(len(denominator), np.nan),
            where=np.isfinite(denominator) & (np.abs(denominator) > eps),
        )
    raise ValueError(f"Unsupported accepted operation at runtime: {name}")


def _compile_relations(
    frame: pd.DataFrame,
    fit_mask: np.ndarray,
    candidates: Sequence[Mapping[str, Any]],
    concept_candidates: Mapping[str, Mapping[str, Any]],
    concepts: Mapping[str, Mapping[str, np.ndarray]],
    side: str,
    column_map: Mapping[str, str | None],
    column_meta: Mapping[str, Mapping[str, Any]],
    dsl: Mapping[str, Any],
    forbidden_column_ids: set[str],
) -> tuple[dict[str, dict[str, np.ndarray]], list[dict[str, Any]]]:
    compiled: dict[str, dict[str, np.ndarray]] = {}
    records: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_id = candidate["candidate_id"]
        binding = candidate["bindings"][side]
        endpoint_specs = binding["arguments"]
        blocked = _relation_forbidden(
            endpoint_specs, concept_candidates, side, forbidden_column_ids
        )
        operation = candidate["operation"]
        operation_spec = dsl["operations"][operation["name"]]
        if blocked:
            raw = np.full(len(frame), np.nan, dtype=np.float64)
        else:
            arguments: dict[str, np.ndarray] = {}
            for argument_name, endpoint in endpoint_specs.items():
                role = operation_spec["argument_roles"][argument_name]
                arguments[argument_name] = _resolve_endpoint(
                    endpoint,
                    frame,
                    column_map,
                    column_meta,
                    concepts,
                    canonicalize=role == "value",
                )
            raw = _apply_operation(operation["name"], arguments, operation["parameters"])
        observed = np.isfinite(raw)
        center, scale = _robust_fit(raw, fit_mask)
        value = np.zeros(len(frame), dtype=np.float32)
        value[observed] = np.clip((raw[observed] - center) / scale, -10.0, 10.0)
        availability = observed.astype(np.float32)
        compiled[candidate_id] = {"value": value, "availability": availability}
        records.append(
            {
                "candidate_id": candidate_id,
                "canonical_name": candidate["canonical_name"],
                "operation": operation,
                "blocked_forbidden_columns": blocked,
                "center": center,
                "scale": scale,
                "runtime_missing_fraction": float(1.0 - observed.mean()),
            }
        )
    return compiled, records


def compile_bank(
    frame: pd.DataFrame,
    fit_mask: np.ndarray,
    accepted_bank: Mapping[str, Any],
    payload: Mapping[str, Any],
    dsl: Mapping[str, Any],
    *,
    side: str,
    arm: str = "full",
    column_map: Mapping[str, str | None] | None = None,
    forbidden_column_ids: Sequence[str] = (),
) -> CompiledBank:
    """Compile one side of an accepted bank to the contract's fixed width.

    ``arm`` controls which block is exposed, but every relation may still use
    concept endpoints internally.  Slots not exposed or not occupied by an
    accepted candidate remain constant zero; therefore every arm has exactly
    ``4 * max_concepts + 2 * max_relations`` columns.
    """
    if arm not in {"base", "concept", "relation", "full"}:
        raise ValueError(f"Unknown compiler arm: {arm}")
    fit_mask = np.asarray(fit_mask, dtype=bool)
    if fit_mask.shape != (len(frame),) or not fit_mask.any():
        raise ValueError("fit_mask must align with frame and contain at least one row")
    column_map = dict(column_map or {})
    forbidden = set(forbidden_column_ids)
    column_meta = _column_index(payload, side)
    concept_candidates = list(accepted_bank.get("concept_candidates", []))
    relation_candidates = list(accepted_bank.get("relation_candidates", []))
    concept_index = {item["candidate_id"]: item for item in concept_candidates}
    concepts, concept_records = _compile_concepts(
        frame,
        fit_mask,
        concept_candidates,
        side,
        column_map,
        column_meta,
        forbidden,
    )
    relations, relation_records = _compile_relations(
        frame,
        fit_mask,
        relation_candidates,
        concept_index,
        concepts,
        side,
        column_map,
        column_meta,
        dsl,
        forbidden,
    )

    max_concepts = int(payload["candidate_budgets"]["max_concepts"])
    max_relations = int(payload["candidate_budgets"]["max_relations"])
    width = max_concepts * len(CONCEPT_CHANNELS) + max_relations * len(RELATION_CHANNELS)
    values = np.zeros((len(frame), width), dtype=np.float32)
    names: list[str] = []
    offset = 0
    for slot in range(max_concepts):
        candidate = concept_candidates[slot] if slot < len(concept_candidates) else None
        for channel in CONCEPT_CHANNELS:
            if candidate is None:
                names.append(f"concept_pad_{slot + 1:03d}::{channel}")
            else:
                candidate_id = candidate["candidate_id"]
                names.append(f"concept::{candidate_id}::{channel}")
                if arm in {"concept", "full"}:
                    values[:, offset] = concepts[candidate_id][channel]
            offset += 1
    for slot in range(max_relations):
        candidate = relation_candidates[slot] if slot < len(relation_candidates) else None
        for channel in RELATION_CHANNELS:
            if candidate is None:
                names.append(f"relation_pad_{slot + 1:03d}::{channel}")
            else:
                candidate_id = candidate["candidate_id"]
                names.append(f"relation::{candidate_id}::{channel}")
                if arm in {"relation", "full"}:
                    values[:, offset] = relations[candidate_id][channel]
            offset += 1
    assert offset == width
    metadata = {
        "compiler_version": "crta-compiler-1.0.0",
        "contract_version": payload["contract_version"],
        "schema_pair_id": payload["schema_pair_id"],
        "side": side,
        "arm": arm,
        "fit_row_count": int(fit_mask.sum()),
        "row_count": len(frame),
        "fixed_width": width,
        "max_concepts": max_concepts,
        "max_relations": max_relations,
        "accepted_concept_count": len(concept_candidates),
        "accepted_relation_count": len(relation_candidates),
        "forbidden_column_ids": sorted(forbidden),
        "concepts": concept_records,
        "relations": relation_records,
    }
    return CompiledBank(values=values, feature_names=tuple(names), metadata=metadata)
