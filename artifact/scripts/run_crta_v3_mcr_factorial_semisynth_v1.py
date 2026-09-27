#!/usr/bin/env python3
"""M x C x R full-factorial semi-synthetic benchmark, v1 (revision 2).

Frozen design and verdicts:
`iclr_latex_v3/MCR_FACTORIAL_SEMISYNTHETIC_PREREGISTRATION_V1.md`.

Real public-use NHANES rows, values, and missingness in the rendering;
outcomes computed from mask-independent completed latents with known
mechanisms.  Lesions act on the source side only -- the target frame is
identical in every arm.  Verdict metric = normalized MSE (lower is
better); nRMSE recorded for description.  No participant-level output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = Path(
    "data/foundation/artifacts/foundation_v2/"
    "raw_adapter_source_locks_v2_3_20260724/"
    "nhanes_common_panel_source_lock_v2/nhanes_common_panel_tokens_v2.parquet"
)
PREREG = ROOT / "iclr_latex_v3/MCR_FACTORIAL_SEMISYNTHETIC_PREREGISTRATION_V1.md"
DEFAULT_OUT = ROOT / "experiments/crta_v3_mcr_factorial_semisynth_v1"

# Salted namespace: the pre-freeze smoke observed realization 0 of every
# family under the unsalted "mcr_v1" keys, so the confirmatory grid draws
# from a fresh key space (prereg section 13).
RNG_NS = "mcr_v1c"

FEATURES = (
    "age", "total_cholesterol", "hba1c", "creatinine",
    "hemoglobin", "rbc", "wbc", "waist",
)
FEATURE_IDS = {name: f"NHANES:{name}" for name in FEATURES}
SOURCE_CYCLES = (
    "2001-2002", "2003-2004", "2005-2006", "2007-2008",
    "2009-2010", "2011-2012", "2013-2014",
)
TARGET_CYCLES = ("2015-2016", "2017-2018", "2023")
REQUIRED_COLUMNS = (
    "subject_id", "source_cycle", "source_variable_id", "value_numeric", "observed",
)

FAMILIES = ("additive", "pairwise", "sparse")
NC_SUITES = ("nc_m", "nc_c", "nc_r")
N_REALIZATIONS = 20
SOURCE_BUDGET = 2048
QUERY_SIZE = 2000
SUPPORTS = (32, 512)
NC_SUPPORT = 32
PRIMARY_K = 32
N_BINS = 5
ORDINAL_COUNT = 4
Z_CLIP = 5.0
LOG_SHIFT = 6.5  # inputs are clipped at +/-5, so x + 6.5 >= 1.5

# arm -> (m_level, c_level, r_level); target_only additionally drops source.
ARM_SPECS: dict[str, tuple[str, str, str]] = {
    "m1c1r1": ("true", "true", "true"),
    "m1c1r0": ("true", "true", "random"),
    "m1c0r1": ("true", "deranged", "true"),
    "m0c1r1": ("wrong", "true", "true"),
    "m1c0r0": ("true", "deranged", "random"),
    "m0c1r0": ("wrong", "true", "random"),
    "m0c0r1": ("wrong", "deranged", "true"),
    "m0c0r0": ("wrong", "deranged", "random"),
    "m1c1rf": ("true", "true", "free"),
    "m1c0rf": ("true", "deranged", "free"),
    "m0c1rf": ("wrong", "true", "free"),
    "m0c0rf": ("wrong", "deranged", "free"),
    "r_flipped": ("true", "true", "flipped"),
    "r_random2": ("true", "true", "random2"),
    "c_deranged2": ("true", "deranged2", "true"),
    "m_wrong2": ("wrong2", "true", "true"),
    "r_op_only": ("true", "true", "op_only"),
    "target_only": ("true", "true", "free"),
}
CORE_ARMS = ("m1c1r1", "m1c1r0", "m1c0r1", "m0c1r1",
             "m1c0r0", "m0c1r0", "m0c0r1", "m0c0r0")
WEIGHTED_SENSITIVITY_ARMS = CORE_ARMS
BACKBONES = ("xgb", "histgb")


# ---------------------------------------------------------------- utilities

def stable_seed(*parts: Any) -> int:
    digest = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
    return int.from_bytes(digest[:8], "little") % (2**32 - 1)


def keyed_rng(*parts: Any) -> np.random.Generator:
    return np.random.default_rng(stable_seed(*parts))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


# ------------------------------------------------------------------- panel

@dataclass(frozen=True)
class Panel:
    z: np.ndarray          # (n, 8) standardized values, 0.0 where unobserved
    mask: np.ndarray       # (n, 8) float 0/1
    source_index: np.ndarray
    target_index: np.ndarray


def load_panel(input_path: Path) -> Panel:
    tokens = pd.read_parquet(input_path, columns=list(REQUIRED_COLUMNS))
    reverse = {v: k for k, v in FEATURE_IDS.items()}
    tokens = tokens[tokens["source_variable_id"].isin(reverse)].copy()
    tokens["feature"] = tokens["source_variable_id"].map(reverse)
    tokens["source_cycle"] = tokens["source_cycle"].astype(str)
    allowed = set(SOURCE_CYCLES) | set(TARGET_CYCLES)
    tokens = tokens[tokens["source_cycle"].isin(allowed)].copy()
    if tokens.duplicated(["subject_id", "source_cycle", "feature"]).any():
        raise ValueError("Duplicate subject/cycle/feature keys in input.")

    values = tokens.pivot(
        index=["subject_id", "source_cycle"], columns="feature",
        values="value_numeric",
    )[list(FEATURES)].sort_index()
    observed = tokens.pivot(
        index=["subject_id", "source_cycle"], columns="feature",
        values="observed",
    )[list(FEATURES)].reindex(values.index).fillna(False).astype(bool)

    cycles = values.index.get_level_values("source_cycle").to_numpy(str)
    subjects = values.index.get_level_values("subject_id").to_numpy(str)
    source_index = np.flatnonzero(np.isin(cycles, SOURCE_CYCLES))
    target_index = np.flatnonzero(np.isin(cycles, TARGET_CYCLES))
    if set(subjects[source_index]) & set(subjects[target_index]):
        raise ValueError("Source and target cycles share subjects.")

    n = len(values)
    z = np.zeros((n, len(FEATURES)), dtype=np.float64)
    mask = np.zeros((n, len(FEATURES)), dtype=np.float64)
    for j, feature in enumerate(FEATURES):
        raw = values[feature].to_numpy(np.float64)
        obs = observed[feature].to_numpy(bool)
        fit = source_index[obs[source_index]]
        if len(fit) < 100:
            raise ValueError(f"Too few observed source values for {feature}.")
        mean = float(np.mean(raw[fit]))
        scale = float(np.std(raw[fit], ddof=0))
        if not np.isfinite(scale) or scale <= 0:
            raise ValueError(f"Degenerate source scale for {feature}.")
        z[obs, j] = np.clip((raw[obs] - mean) / scale, -Z_CLIP, Z_CLIP)
        mask[:, j] = obs.astype(np.float64)
    return Panel(z=z, mask=mask, source_index=source_index,
                 target_index=target_index)


def complete_latents(panel: Panel, key: tuple[Any, ...]) -> np.ndarray:
    """Fill missing entries from the feature's observed source marginal."""
    rng = keyed_rng(RNG_NS,"complete", *key)
    z = panel.z.copy()
    for j in range(len(FEATURES)):
        pool = panel.z[panel.source_index, j][
            panel.mask[panel.source_index, j] > 0]
        missing = np.flatnonzero(panel.mask[:, j] == 0)
        z[missing, j] = rng.choice(pool, size=len(missing), replace=True)
    return z


# ---------------------------------------------------- canonical quantization

@dataclass(frozen=True)
class CanonicalBins:
    """Source-partition quintile edges and bin means, shared by both sides."""
    ordinal_features: tuple[int, ...]
    edges: dict[int, np.ndarray]     # 4 interior edges
    centers: dict[int, np.ndarray]   # 5 per-bin means of observed source z


def canonical_bins(panel: Panel, ordinal_features: tuple[int, ...]
                   ) -> CanonicalBins:
    edges: dict[int, np.ndarray] = {}
    centers: dict[int, np.ndarray] = {}
    for j in ordinal_features:
        observed = panel.source_index[panel.mask[panel.source_index, j] > 0]
        zj = panel.z[observed, j]
        cut = np.quantile(zj, np.linspace(0, 1, N_BINS + 1)[1:-1])
        edges[j] = np.asarray(cut, dtype=np.float64)
        bins = np.digitize(zj, cut)
        centers[j] = np.array([
            float(np.mean(zj[bins == k])) if np.any(bins == k)
            else float(np.mean(zj))
            for k in range(N_BINS)
        ])
    return CanonicalBins(tuple(sorted(ordinal_features)), edges, centers)


def quantize(values: np.ndarray, bins: CanonicalBins) -> np.ndarray:
    """Replace ordinal features by their canonical bin value (z-tilde)."""
    out = values.copy()
    for j in bins.ordinal_features:
        codes = np.digitize(values[:, j], bins.edges[j])
        out[:, j] = bins.centers[j][codes]
    return out


# -------------------------------------------------------------- mechanisms

@dataclass(frozen=True)
class Mechanism:
    family: str
    feat_terms: tuple[tuple[int, int, float], ...]        # (feature, sign, w)
    pair_terms: tuple[tuple[int, int, str, int, float], ...]  # (a,b,op,sign,w)
    vshape_terms: tuple[tuple[int, float], ...]           # (feature, coef)


def draw_mechanism(family: str, realization: int) -> Mechanism:
    rng = keyed_rng(RNG_NS,"mechanism", family, realization)
    p = len(FEATURES)
    if family == "additive":
        feats = rng.choice(p, size=5, replace=False)
        terms = tuple(
            (int(j), int(rng.choice((-1, 1))), float(rng.uniform(0.5, 1.0)))
            for j in feats
        )
        return Mechanism(family, terms, (), ())
    if family == "pairwise":
        perm = rng.permutation(p)[:6]
        pairs = [(int(perm[0]), int(perm[1])), (int(perm[2]), int(perm[3])),
                 (int(perm[4]), int(perm[5]))]
        terms = tuple(
            (a, b, str(rng.choice(("diff", "log_ratio"))),
             int(rng.choice((-1, 1))), float(rng.uniform(0.5, 1.0)))
            for a, b in pairs
        )
        return Mechanism(family, (), terms, ())
    if family == "sparse":
        unordered = list(combinations(range(p), 2))
        picks = rng.choice(len(unordered), size=2, replace=False)
        terms = []
        for index in picks:
            a, b = unordered[int(index)]
            if rng.random() < 0.5:
                a, b = b, a
            terms.append((int(a), int(b), str(rng.choice(("diff", "log_ratio"))),
                          int(rng.choice((-1, 1))), float(rng.uniform(0.5, 1.0))))
        return Mechanism(family, (), tuple(terms), ())
    if family == "vshape":
        feats = rng.choice(p, size=5, replace=False)
        terms = tuple((int(j), float(rng.uniform(0.5, 1.0))) for j in feats)
        return Mechanism(family, (), (), terms)
    raise ValueError(f"Unknown family: {family}")


def op_values(op: str, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    if op == "diff":
        out = a - b
    elif op == "log_ratio":
        left, right = a + LOG_SHIFT, b + LOG_SHIFT
        with np.errstate(invalid="ignore", divide="ignore"):
            out = np.where((left > 0) & (right > 0),
                           np.log(left) - np.log(right), np.nan)
    else:
        raise ValueError(f"Unknown op: {op}")
    return np.where(np.isfinite(out), out, np.nan)


def make_outcome(panel: Panel, mechanism: Mechanism, bins: CanonicalBins,
                 family: str, realization: int) -> np.ndarray:
    """Outcome from completed latents (mask-independent), unit-SD terms."""
    latent = complete_latents(panel, (family, realization))
    latent = quantize(latent, bins)
    source = panel.source_index

    def standardized(term: np.ndarray) -> np.ndarray:
        center = float(np.mean(term[source]))
        scale = float(np.std(term[source], ddof=0))
        if not np.isfinite(scale) or scale <= 1e-8:
            raise ValueError("Degenerate mechanism term.")
        return (term - center) / scale

    signal = np.zeros(len(latent), dtype=np.float64)
    for j, sign, weight in mechanism.feat_terms:
        signal += weight * sign * standardized(latent[:, j])
    for a, b, op, sign, weight in mechanism.pair_terms:
        signal += weight * sign * standardized(op_values(op, latent[:, a],
                                                         latent[:, b]))
    for j, coef in mechanism.vshape_terms:
        median = float(np.median(latent[source, j]))
        signal += coef * standardized(np.abs(latent[:, j] - median))
    sigma = float(np.std(signal[source], ddof=0))
    if not np.isfinite(sigma) or sigma <= 1e-8:
        raise ValueError("Degenerate synthetic signal.")
    noise = keyed_rng(RNG_NS,"noise", family, realization
                      ).standard_normal(len(latent))
    return signal + sigma * noise


# --------------------------------------------------------------- rendering

@dataclass(frozen=True)
class SideRendering:
    canonical: bool
    ordinal_features: tuple[int, ...]
    direction: dict[int, int]        # ordinal: +1 keep, -1 reverse
    base: dict[int, int]             # ordinal: code base 0 or 1
    scale: dict[int, float]          # continuous
    offset: dict[int, float]         # continuous
    sentinel: dict[int, float]       # per feature
    names: tuple[str, ...]           # per feature (concept order)


def draw_side_rendering(ordinal_features: tuple[int, ...],
                        key: tuple[Any, ...], canonical: bool
                        ) -> SideRendering:
    rng = keyed_rng(RNG_NS,"render", *key)
    p = len(FEATURES)
    names = tuple(
        "v_" + hashlib.sha256(
            f"{RNG_NS}|name|{'|'.join(map(str, key))}|{j}".encode()
        ).hexdigest()[:8]
        for j in range(p)
    )
    if canonical:
        return SideRendering(True, (), {}, {}, {}, {}, {}, names)
    direction: dict[int, int] = {}
    base: dict[int, int] = {}
    scale: dict[int, float] = {}
    offset: dict[int, float] = {}
    sentinel: dict[int, float] = {}
    for j in range(p):
        if j in ordinal_features:
            direction[j] = int(rng.choice((1, -1)))
            base[j] = int(rng.choice((0, 1)))
            sentinel[j] = float(rng.choice((8.0, 9.0)))
        else:
            scale[j] = float(np.exp(rng.uniform(np.log(0.25), np.log(4.0))))
            offset[j] = float(rng.uniform(-2.0, 2.0))
            sentinel[j] = float(rng.choice((-99.0, 99.0)))
    return SideRendering(False, tuple(sorted(ordinal_features)), direction,
                         base, scale, offset, sentinel, names)


def render_side(panel: Panel, rows: np.ndarray, rendering: SideRendering,
                bins: CanonicalBins) -> np.ndarray:
    """Rendered matrix in concept order (column j = feature j as rendered)."""
    p = len(FEATURES)
    out = np.zeros((len(rows), p), dtype=np.float64)
    z, mask = panel.z[rows], panel.mask[rows]
    for j in range(p):
        observed = mask[:, j] > 0
        if rendering.canonical:
            out[observed, j] = z[observed, j]
            out[~observed, j] = np.nan
            continue
        if j in rendering.direction:
            code = np.digitize(z[observed, j], bins.edges[j]).astype(float)
            if rendering.direction[j] < 0:
                code = (N_BINS - 1) - code
            code += rendering.base[j]
            out[observed, j] = code
        else:
            out[observed, j] = (z[observed, j] * rendering.scale[j]
                                + rendering.offset[j])
        out[~observed, j] = rendering.sentinel[j]
    return out


# ------------------------------------------------------- alignment tables

@dataclass(frozen=True)
class AlignmentTable:
    """Per-side decode: rendered column -> canonical estimate (NaN = missing)."""
    canonical: bool
    ordinal_map: dict[int, dict[float, float]]  # feature -> code -> value/NaN
    inv_scale: dict[int, float]
    inv_offset: dict[int, float]
    declared_sentinel: dict[int, float]
    entry_count: int


def true_table(rendering: SideRendering, bins: CanonicalBins
               ) -> AlignmentTable:
    if rendering.canonical:
        return AlignmentTable(True, {}, {}, {}, {}, 0)
    ordinal_map: dict[int, dict[float, float]] = {}
    inv_scale: dict[int, float] = {}
    inv_offset: dict[int, float] = {}
    declared: dict[int, float] = {}
    entries = 0
    for j in range(len(FEATURES)):
        if j in rendering.direction:
            mapping: dict[float, float] = {}
            for raw_bin in range(N_BINS):
                code = float(
                    ((N_BINS - 1) - raw_bin if rendering.direction[j] < 0
                     else raw_bin) + rendering.base[j]
                )
                mapping[code] = float(bins.centers[j][raw_bin])
            mapping[rendering.sentinel[j]] = np.nan
            ordinal_map[j] = mapping
            entries += len(mapping)
        else:
            inv_scale[j] = rendering.scale[j]
            inv_offset[j] = rendering.offset[j]
            declared[j] = rendering.sentinel[j]
            entries += 2
    return AlignmentTable(False, ordinal_map, inv_scale, inv_offset,
                          declared, entries)


def wrong_table(rendering: SideRendering, bins: CanonicalBins,
                key: tuple[Any, ...]) -> AlignmentTable:
    """Matched-complexity wrong source-side table (prereg section 5)."""
    if rendering.canonical:
        return AlignmentTable(True, {}, {}, {}, {}, 0)
    rng = keyed_rng(RNG_NS,"wrong_table", *key)
    truth = true_table(rendering, bins)
    ordinal_map: dict[int, dict[float, float]] = {}
    for j, mapping in truth.ordinal_map.items():
        valid_codes = sorted(c for c, v in mapping.items() if np.isfinite(v))
        centers = [mapping[c] for c in valid_codes]
        reversed_true = {code: centers[len(valid_codes) - 1 - i]
                         for i, code in enumerate(valid_codes)}
        true_sentinel = rendering.sentinel[j]
        wrong_nan_code = float(rng.choice(valid_codes))
        value_keys = [c for c in valid_codes if c != wrong_nan_code]
        value_keys.append(true_sentinel)
        surviving = [c for c in valid_codes if c != wrong_nan_code]
        for _ in range(1000):
            perm = rng.permutation(N_BINS)
            wrong: dict[float, float] = {wrong_nan_code: np.nan}
            for slot, code in enumerate(value_keys):
                wrong[float(code)] = float(centers[int(perm[slot])])
            # Value-level rejection: a map that decodes every surviving
            # valid code correctly is truth-plus-moved-NaN, and one that
            # decodes them all reversed is the adversarial special case.
            if all(wrong[c] == mapping[c] for c in surviving):
                continue
            if all(wrong[c] == reversed_true[c] for c in surviving):
                continue
            break
        else:
            raise RuntimeError("No admissible wrong permutation found.")
        if len(wrong) != len(mapping):
            raise AssertionError("Wrong-table complexity mismatch (ordinal).")
        ordinal_map[j] = wrong
    continuous = sorted(truth.inv_scale)
    if continuous:
        for _ in range(1000):
            perm = rng.permutation(len(continuous))
            if not np.any(perm == np.arange(len(continuous))):
                break
        else:
            raise RuntimeError("No continuous derangement found.")
        donor = {continuous[i]: continuous[int(perm[i])]
                 for i in range(len(continuous))}
    else:
        donor = {}
    inv_scale = {j: truth.inv_scale[donor[j]] for j in continuous}
    inv_offset = {j: truth.inv_offset[donor[j]] for j in continuous}
    declared = {j: -truth.declared_sentinel[j] for j in continuous}
    real_entries = (sum(len(m) for m in ordinal_map.values())
                    + 2 * len(inv_scale))
    if real_entries != truth.entry_count:
        raise AssertionError("Wrong-table complexity mismatch.")
    return AlignmentTable(False, ordinal_map, inv_scale, inv_offset,
                          declared, real_entries)


def table_digest(table: AlignmentTable) -> str:
    payload = json.dumps(json_ready({
        "ordinal": {k: sorted(v.items()) for k, v in table.ordinal_map.items()},
        "scale": table.inv_scale, "offset": table.inv_offset,
        "sentinel": table.declared_sentinel,
    }), sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:12]


def decode(rendered: np.ndarray, table: AlignmentTable) -> np.ndarray:
    if table.canonical:
        return rendered.copy()
    out = np.full_like(rendered, np.nan)
    for j in range(rendered.shape[1]):
        column = rendered[:, j]
        if j in table.ordinal_map:
            for code, value in table.ordinal_map[j].items():
                out[column == code, j] = value
        else:
            keep = column != table.declared_sentinel[j]
            out[keep, j] = (
                (column[keep] - table.inv_offset[j]) / table.inv_scale[j]
            )
    return out


# ------------------------------------------------------ relation knowledge

@dataclass(frozen=True)
class RelationSet:
    feat_signs: tuple[tuple[int, int], ...]              # (feature, sign)
    pair_terms: tuple[tuple[int, int, str, int], ...]    # (a, b, op, sign)


def true_relations(mechanism: Mechanism) -> RelationSet:
    return RelationSet(
        tuple((j, s) for j, s, _ in mechanism.feat_terms),
        tuple((a, b, op, s) for a, b, op, s, _ in mechanism.pair_terms),
    )


def flipped_relations(relations: RelationSet) -> RelationSet:
    return RelationSet(
        tuple((j, -s) for j, s in relations.feat_signs),
        tuple((a, b, op, -s) for a, b, op, s in relations.pair_terms),
    )


def distinct_feature_count(pairs: tuple[tuple[int, int, str, int], ...]) -> int:
    return len({f for a, b, _, _ in pairs for f in (a, b)})


def random_relations(mechanism: Mechanism, family: str, realization: int,
                     draw: str) -> RelationSet:
    """Density- and topology-matched neutral random set.

    vshape (direction-free) uses family-A density (5 feature signs)."""
    rng = keyed_rng(RNG_NS,"random_relations", family, realization, draw)
    p = len(FEATURES)
    truth = true_relations(mechanism)
    if mechanism.family in ("additive", "vshape"):
        count = len(truth.feat_signs) if truth.feat_signs else 5
        true_map = dict(truth.feat_signs)
        for _ in range(1000):
            feats = rng.choice(p, size=count, replace=False)
            signs = rng.choice((-1, 1), size=count)
            candidate = tuple((int(j), int(s)) for j, s in zip(feats, signs))
            if dict(candidate) != true_map:
                return RelationSet(candidate, ())
        raise RuntimeError("No admissible random sign set found.")
    true_pairs = {frozenset((a, b)) for a, b, _, _ in truth.pair_terms}
    ops = [op for _, _, op, _ in truth.pair_terms]
    rng.shuffle(ops)
    target_distinct = distinct_feature_count(truth.pair_terms)
    for _ in range(10000):
        if mechanism.family == "pairwise":
            perm = rng.permutation(p)[:6]
            pairs = [(int(perm[0]), int(perm[1])), (int(perm[2]), int(perm[3])),
                     (int(perm[4]), int(perm[5]))]
        else:
            unordered = list(combinations(range(p), 2))
            picks = rng.choice(len(unordered), size=len(truth.pair_terms),
                               replace=False)
            pairs = []
            for index in picks:
                a, b = unordered[int(index)]
                if rng.random() < 0.5:
                    a, b = b, a
                pairs.append((int(a), int(b)))
        candidate = tuple(
            (a, b, ops[i], int(rng.choice((-1, 1))))
            for i, (a, b) in enumerate(pairs)
        )
        if any(frozenset((a, b)) in true_pairs for a, b, _, _ in candidate):
            continue
        if distinct_feature_count(candidate) != target_distinct:
            continue
        return RelationSet((), candidate)
    raise RuntimeError("No admissible random pair set found.")


def op_only_relations(relations: RelationSet) -> RelationSet:
    return RelationSet((), tuple(
        (a, b, op, 0) for a, b, op, _ in relations.pair_terms))


def compile_design(frame: np.ndarray, relations: RelationSet | None
                   ) -> tuple[np.ndarray, tuple[int, ...]]:
    """Append compiled op columns; return (matrix, monotone constraints)."""
    p = frame.shape[1]
    constraints = [0] * p
    columns = [frame]
    if relations is not None:
        for j, s in relations.feat_signs:
            constraints[j] = s
        for a, b, op, s in relations.pair_terms:
            columns.append(op_values(op, frame[:, a], frame[:, b])[:, None])
            constraints.append(s)
    matrix = np.hstack(columns) if len(columns) > 1 else frame
    return matrix, tuple(constraints)


# ------------------------------------------------------------ arm assembly

def type_preserving_derangement(ordinal_features: tuple[int, ...],
                                key: tuple[Any, ...],
                                forbidden: tuple[int, ...] | None = None
                                ) -> np.ndarray:
    """Derange within the ordinal group and within the continuous group."""
    rng = keyed_rng(RNG_NS,"derangement", *key)
    p = len(FEATURES)
    groups = [sorted(ordinal_features),
              sorted(set(range(p)) - set(ordinal_features))]
    for _ in range(1000):
        perm = np.arange(p)
        for group in groups:
            if len(group) < 2:
                raise ValueError("Type group too small to derange.")
            while True:
                shuffled = rng.permutation(group)
                if not np.any(shuffled == np.asarray(group)):
                    break
            for position, feature in zip(group, shuffled):
                perm[position] = feature
        if forbidden is not None and np.array_equal(perm, forbidden):
            continue
        return perm
    raise RuntimeError("No admissible derangement found.")


def name_match_accuracy(source: SideRendering, target: SideRendering) -> float:
    lookup = {name: j for j, name in enumerate(source.names)}
    hits = sum(1 for j, name in enumerate(target.names)
               if lookup.get(name) == j)
    return hits / len(FEATURES)


@dataclass(frozen=True)
class CellData:
    y: np.ndarray
    source_rows: np.ndarray
    query_rows: np.ndarray
    supports: dict[int, np.ndarray]
    source_rendered: np.ndarray
    target_decoded_support: dict[int, np.ndarray]   # true target decode
    target_decoded_query: np.ndarray
    source_tables: dict[str, AlignmentTable]        # true / wrong / wrong2
    c_perms: dict[str, np.ndarray]                  # deranged / deranged2
    relations: dict[str, RelationSet | None]
    name_accuracy: float
    audit: dict[str, Any]


def build_cell(panel: Panel, mode: str, family: str, realization: int,
               supports: tuple[int, ...]) -> CellData:
    mech_family = "vshape" if mode == "nc_r" else family
    ordinal = tuple(
        int(j) for j in keyed_rng(RNG_NS,"ordinal", mode, family, realization
                                  ).choice(len(FEATURES), size=ORDINAL_COUNT,
                                           replace=False)
    )
    bins = canonical_bins(panel, ordinal)
    mechanism = draw_mechanism(mech_family, realization)
    y = make_outcome(panel, mechanism, bins, mech_family, realization)

    rng = keyed_rng(RNG_NS,"rows", mode, family, realization)
    source_rows = np.sort(rng.choice(panel.source_index, size=SOURCE_BUDGET,
                                     replace=False))
    query_rows = np.sort(rng.choice(panel.target_index, size=QUERY_SIZE,
                                    replace=False))
    pool = np.setdiff1d(panel.target_index, query_rows)
    support_rows = {
        k: np.sort(keyed_rng(RNG_NS,"support", mode, family, realization, k
                             ).choice(pool, size=k, replace=False))
        for k in supports
    }

    canonical = mode == "nc_m"
    if mode == "nc_c":
        shared_key = (mode, family, realization, "shared")
        source_rendering = draw_side_rendering(ordinal, shared_key, canonical)
        target_rendering = draw_side_rendering(ordinal, shared_key, canonical)
    else:
        source_rendering = draw_side_rendering(
            ordinal, (mode, family, realization, "source"), canonical)
        target_rendering = draw_side_rendering(
            ordinal, (mode, family, realization, "target"), canonical)

    source_tables = {
        "true": true_table(source_rendering, bins),
        "wrong": wrong_table(source_rendering, bins,
                             (mode, family, realization, "w1")),
        "wrong2": wrong_table(source_rendering, bins,
                              (mode, family, realization, "w2")),
    }
    if not source_tables["true"].canonical and table_digest(
            source_tables["wrong"]) == table_digest(source_tables["wrong2"]):
        raise AssertionError("wrong and wrong2 tables coincide.")
    target_table = true_table(target_rendering, bins)

    perm1 = type_preserving_derangement(ordinal, (mode, family, realization, 1))
    perm2 = type_preserving_derangement(ordinal, (mode, family, realization, 2),
                                        forbidden=perm1)
    truth_relations = true_relations(mechanism)
    random1 = random_relations(mechanism, mech_family, realization, "r1")
    random2 = random_relations(mechanism, mech_family, realization, "r2")
    if truth_relations.pair_terms or truth_relations.feat_signs:
        if random1 == random2:
            raise AssertionError("random and random2 relation sets coincide.")
    relations: dict[str, RelationSet | None] = {
        "true": truth_relations,
        "flipped": flipped_relations(truth_relations),
        "random": random1,
        "random2": random2,
        "op_only": op_only_relations(truth_relations),
        "free": None,
    }
    return CellData(
        y=y,
        source_rows=source_rows,
        query_rows=query_rows,
        supports=support_rows,
        source_rendered=render_side(panel, source_rows, source_rendering, bins),
        target_decoded_support={
            k: decode(render_side(panel, rows, target_rendering, bins),
                      target_table)
            for k, rows in support_rows.items()
        },
        target_decoded_query=decode(
            render_side(panel, query_rows, target_rendering, bins),
            target_table),
        source_tables=source_tables,
        c_perms={"deranged": perm1, "deranged2": perm2},
        relations=relations,
        name_accuracy=name_match_accuracy(source_rendering, target_rendering),
        audit={
            "ordinal_features": list(ordinal),
            "c_deranged": perm1.tolist(),
            "c_deranged2": perm2.tolist(),
            "source_table_digests": {
                k: table_digest(v) for k, v in source_tables.items()},
        },
    )


def arm_matrices(cell: CellData, arm: str, support_k: int, weighted: bool
                 ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray,
                            tuple[int, ...]]:
    """Return (X_fit, y_fit, weights, X_query, constraints)."""
    m_level, c_level, r_level = ARM_SPECS[arm]
    relations = cell.relations[r_level]
    target_support = cell.target_decoded_support[support_k]
    target_query = cell.target_decoded_query

    if arm == "target_only":
        x_support, constraints = compile_design(target_support, relations)
        x_query, _ = compile_design(target_query, relations)
        y_fit = cell.y[cell.supports[support_k]]
        return x_support, y_fit, np.ones(len(y_fit)), x_query, constraints

    source_table = cell.source_tables[
        {"true": "true", "wrong": "wrong", "wrong2": "wrong2"}[m_level]]
    source_decoded = decode(cell.source_rendered, source_table)
    if c_level in ("deranged", "deranged2"):
        source_decoded = source_decoded[:, cell.c_perms[c_level]]
    x_fit_frame = np.vstack([source_decoded, target_support])
    x_fit, constraints = compile_design(x_fit_frame, relations)
    x_query, _ = compile_design(target_query, relations)
    y_fit = np.concatenate([
        cell.y[cell.source_rows], cell.y[cell.supports[support_k]],
    ])
    if weighted:
        weights = np.concatenate([
            np.ones(len(cell.source_rows)),
            np.full(support_k, len(cell.source_rows) / support_k),
        ])
    else:
        weights = np.ones(len(y_fit))
    return x_fit, y_fit, weights, x_query, constraints


# ------------------------------------------------------------------- fits

def fit_predict(backbone: str, x_fit: np.ndarray, y_fit: np.ndarray,
                weights: np.ndarray, x_query: np.ndarray,
                constraints: tuple[int, ...], seed: int, threads: int
                ) -> np.ndarray:
    active = any(constraints)
    if backbone == "xgb":
        from xgboost import XGBRegressor

        model = XGBRegressor(
            tree_method="hist", max_depth=6, n_estimators=300,
            learning_rate=0.05, min_child_weight=20, reg_lambda=1.0,
            n_jobs=threads, random_state=seed, verbosity=0,
            monotone_constraints=(tuple(constraints) if active else None),
        )
        model.fit(x_fit, y_fit, sample_weight=weights)
        return np.asarray(model.predict(x_query), dtype=np.float64)
    if backbone == "histgb":
        from sklearn.ensemble import HistGradientBoostingRegressor
        from threadpoolctl import threadpool_limits

        model = HistGradientBoostingRegressor(
            max_iter=300, max_depth=6, learning_rate=0.05,
            min_samples_leaf=20, l2_regularization=1.0,
            random_state=seed, early_stopping=False,
            monotonic_cst=(list(constraints) if active else None),
        )
        with threadpool_limits(limits=max(threads, 1)):
            model.fit(x_fit, y_fit, sample_weight=weights)
            return np.asarray(model.predict(x_query), dtype=np.float64)
    raise ValueError(f"Unknown backbone: {backbone}")


def primary_arm_list(family: str) -> tuple[str, ...]:
    arms = tuple(ARM_SPECS)
    if family == "additive":
        arms = tuple(a for a in arms if a != "r_op_only")
    return arms


def run_cell(panel: Panel, mode: str, family: str, realization: int,
             threads: int) -> dict[str, Any]:
    primary = mode == "primary"
    supports = SUPPORTS if primary else (NC_SUPPORT,)
    backbones = BACKBONES if primary else ("xgb",)
    if primary:
        arms = primary_arm_list(family)
    elif mode == "nc_r":
        arms = CORE_ARMS + ("m1c1rf",)
    else:
        arms = CORE_ARMS
    # NC assertions compare bit-level predictions; keep those fits at one
    # thread so parallel histogram accumulation cannot perturb them.
    fit_threads = threads if primary else 1

    cell = build_cell(panel, mode, family, realization, supports)
    if primary and cell.name_accuracy != 0.0:
        raise AssertionError("Primary rendering leaked matchable names.")
    if mode == "nc_c" and cell.name_accuracy != 1.0:
        raise AssertionError("NC-C rendering names failed to match.")

    y_query = cell.y[cell.query_rows]
    query_var = float(np.var(y_query, ddof=0))
    predictions: dict[tuple[int, str, str], np.ndarray] = {}
    results: dict[str, Any] = {}
    for support_k in supports:
        results[str(support_k)] = {}
        for backbone in backbones:
            results[str(support_k)][backbone] = {}
            for arm in arms:
                x_fit, y_fit, weights, x_query, constraints = arm_matrices(
                    cell, arm, support_k, weighted=False)
                prediction = fit_predict(
                    backbone, x_fit, y_fit, weights, x_query, constraints,
                    seed=realization, threads=fit_threads)
                predictions[(support_k, backbone, arm)] = prediction
                mse = float(np.mean((y_query - prediction) ** 2))
                results[str(support_k)][backbone][arm] = {
                    "nmse": mse / query_var,
                    "nrmse": float(np.sqrt(mse)) / float(np.sqrt(query_var)),
                }

    sensitivity: dict[str, Any] = {}
    if primary:
        for arm in WEIGHTED_SENSITIVITY_ARMS:
            x_fit, y_fit, weights, x_query, constraints = arm_matrices(
                cell, arm, PRIMARY_K, weighted=True)
            prediction = fit_predict("xgb", x_fit, y_fit, weights, x_query,
                                     constraints, seed=realization,
                                     threads=fit_threads)
            mse = float(np.mean((y_query - prediction) ** 2))
            sensitivity[arm] = {
                "nmse": mse / query_var,
                "nrmse": float(np.sqrt(mse)) / float(np.sqrt(query_var)),
            }

    checks: dict[str, bool] = {}
    if mode == "nc_m":
        for c in (1, 0):
            for r in (1, 0):
                pair = (f"m1c{c}r{r}", f"m0c{c}r{r}")
                equal = bool(np.array_equal(
                    predictions[(NC_SUPPORT, "xgb", pair[0])],
                    predictions[(NC_SUPPORT, "xgb", pair[1])],
                ))
                checks[f"m_pair_identical_c{c}r{r}"] = equal
                if not equal:
                    raise AssertionError(f"NC-M pair differs: {pair}")
    if mode == "nc_r":
        equal = bool(np.array_equal(
            predictions[(NC_SUPPORT, "xgb", "m1c1r1")],
            predictions[(NC_SUPPORT, "xgb", "m1c1rf")],
        ))
        checks["true_relation_equals_free"] = equal
        if not equal:
            raise AssertionError("NC-R: empty true relation set is not free.")

    mechanism = draw_mechanism("vshape" if mode == "nc_r" else family,
                               realization)
    return {
        "mode": mode,
        "family": family,
        "realization": realization,
        "metric": "nmse = MSE/Var(y_query) (verdicts); nrmse descriptive",
        "n_source": SOURCE_BUDGET,
        "n_query": QUERY_SIZE,
        "supports": list(supports),
        "backbones": list(backbones),
        "arms": list(arms),
        "mechanism": {
            "family": mechanism.family,
            "feat_terms": [list(t) for t in mechanism.feat_terms],
            "pair_terms": [list(t) for t in mechanism.pair_terms],
            "vshape_terms": [list(t) for t in mechanism.vshape_terms],
        },
        "audit": cell.audit,
        "name_match_accuracy": cell.name_accuracy,
        "checks": checks,
        "results": results,
        "sensitivity_weighted_xgb_k32": sensitivity,
    }


# -------------------------------------------------------------------- main

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--modes", nargs="*",
                        default=["primary", *NC_SUITES])
    parser.add_argument("--families", nargs="*", default=list(FAMILIES))
    parser.add_argument("--realizations", nargs="*", type=int,
                        default=list(range(N_REALIZATIONS)))
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()

    os.environ.setdefault("OMP_NUM_THREADS", str(args.threads))
    import sklearn
    import xgboost

    provenance = {
        "input_sha256": sha256_file(args.input),
        "runner_sha256": sha256_file(Path(__file__)),
        "prereg_sha256": sha256_file(PREREG),
        "versions": {
            "numpy": np.__version__, "pandas": pd.__version__,
            "sklearn": sklearn.__version__, "xgboost": xgboost.__version__,
        },
    }
    panel = load_panel(args.input)
    print(json.dumps({
        "rows_source": int(len(panel.source_index)),
        "rows_target": int(len(panel.target_index)),
        **provenance,
    }), flush=True)

    for mode in args.modes:
        families = args.families if mode == "primary" else ["pairwise"]
        for family in families:
            for realization in args.realizations:
                out_dir = (
                    args.out_root / mode / family / f"r{realization:02d}"
                    if mode == "primary"
                    else args.out_root / mode / f"r{realization:02d}"
                )
                metrics_path = out_dir / "metrics.json"
                if metrics_path.is_file():
                    existing = json.loads(metrics_path.read_text())
                    mismatch = (
                        any(existing.get(k) != provenance[k] for k in
                            ("runner_sha256", "input_sha256",
                             "prereg_sha256"))
                        or existing.get("mode") != mode
                        or existing.get("realization") != realization
                        or (mode == "primary"
                            and existing.get("family") != family)
                    )
                    if mismatch:
                        raise RuntimeError(
                            f"{metrics_path} does not match the current "
                            "runner/input/prereg or its own path; archive "
                            "that tree before resuming.")
                    continue
                started = time.time()
                payload = run_cell(panel, mode, family, realization,
                                   args.threads)
                payload["wall_seconds"] = round(time.time() - started, 1)
                payload.update(provenance)
                out_dir.mkdir(parents=True, exist_ok=True)
                metrics_path.write_text(
                    json.dumps(json_ready(payload), indent=1, sort_keys=True)
                    + "\n", encoding="utf-8")
                print(json.dumps({
                    "mode": mode, "family": family,
                    "realization": realization,
                    "wall_seconds": payload["wall_seconds"],
                }), flush=True)
    print(json.dumps({"status": "complete"}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
