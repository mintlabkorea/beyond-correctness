#!/usr/bin/env python3
"""Authorized runtime core for the frozen M3 NHKN -> HRS Auto-C matrix.

Production callers must use ``run_crta_v3_m3_nhkn2hrs_auto_c_v1.py``.  That
standard-library-only launcher validates HRS authorization before importing
this module.  Direct imports are reserved for row-free synthetic tests.
"""

from __future__ import annotations

import hashlib
import hmac
import importlib.util
import json
import math
import os
import secrets
import stat
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from xgboost import XGBRegressor


ROOT = Path(__file__).resolve().parents[1]
AUTH_VALIDATOR = ROOT / "scripts" / "validate_hrs_ai_authorization.py"
EXPECTED_AUTH_VALIDATOR_SHA256 = (
    "d38d383a6ddf6a3e104db491a9e5cb0f04f74fa9594831c24a66742ecb754dee"
)
PRIVATE_ROOT = Path("data/private/crta_v3")
PRIVATE_TASK_LEAF = "m3_nhkn2hrs_auto_c_v1"
PRIVATE_TASK_ROOT = PRIVATE_ROOT / PRIVATE_TASK_LEAF
TASK_ID = "M3"
BENCHMARK_ID = "std_cross_nhkn2hrs_shared_anchorreset_fewshot_v1"
SCOPE_ID = "crta_v3_m3_nhkn2hrs_auto_c_utility_v1"
SCHEMA_PAIR_ID = "nhkn_combined_to_hrs_medical_registry_v1"
EXPECTED_SOURCE_SHA256 = (
    "47aff36cda708aaf31d698747365a88141775f5abb9a530cf7eb7ee3ba9121d7"
)
EXPECTED_HRS_SHA256 = (
    "3fb239b9aa3642e94b2be7be66de02bd86b233839f66fef95c7fe627ed2ffe5d"
)
EXPECTED_PAYLOAD_SHA256 = (
    "407356a04653af709a3c0bed1d3409017a85e41c43fa02d4be3c59598fecfa20"
)
EXPECTED_PAYLOAD_CANONICAL_SHA256 = (
    "f67018ba7a2dbd2514d1d1fea74795a8879c363062471b0ea50cc454ef045d0b"
)
EXPECTED_DSL_SHA256 = (
    "ffeb22b6502d431ec276d44c558d42fbc5bc5ffb5b079c52986bc248facbc28b"
)
EXPECTED_DSL_CANONICAL_SHA256 = (
    "e64459681e81fb3c9d9ba7b4ed2640d1d29353c98d91ad7a33e62d276a9c6f2b"
)
EXPECTED_RUNTIME_MAP_SHA256 = (
    "bf2563b8cb7aad1af3b59047bace4319e2377dd539f5ef491debb63a84a8e8ca"
)
EXPECTED_COMPILER_SHA256 = (
    "3ed08577091b91b81cd51cabfb13d2f947a5c4293c2b8265f235cdd1c2b6aefb"
)
EXPECTED_SOURCE_TRAIN_ROWS = 240_014
EXPECTED_HRS_ROWS = 45_234
SOURCE_CAP = 4_096
# Rungs of the source-budget ladder; None is uncapped.  Governed by
# iclr_latex_v3/SOURCE_BUDGET_LADDER_PROTOCOL_V1.md.  SOURCE_CAP stays the
# default so an unflagged invocation reproduces the executed L0 run exactly.
SOURCE_CAP_LADDER: tuple[int | None, ...] = (4_096, 16_384, None)
_SOURCE_CAP_BOUND = False


def source_cap_tag(source_cap: "int | None") -> str:
    return "uncapped" if source_cap is None else f"cap{source_cap}"


# Near-definitional proxy exclusion, added 2026-08-18 to bring M3 under the
# same rule M4/M5 already declare.  Governed by
# iclr_latex_v3/ENDPOINT_CONCENTRATION_AND_LEAKAGE_BLOCK_AUDIT_V1.md.  Three
# policies exist so the two halves of the M4 criterion can be told apart:
#   none           the executed pre-fix configuration: the endpoint's own
#                  schema column is the whole forbidden set.
#   compiler       LEAKAGE_BLOCKS added to the compiler forbidden set only.
#   compiler_base  the M4/M5 criterion in full -- blocked endpoints are also
#                  dropped from the Base feature set for that endpoint.
# Each policy other than `none` writes to its own private leaf, so a pre-fix
# tree can never be overwritten by a post-fix run.
LEAKAGE_BLOCK_POLICIES: tuple[str, ...] = ("none", "compiler", "compiler_base")
LEAKAGE_BLOCK_POLICY_TAG: dict[str, str] = {
    "none": "",
    "compiler": "block",
    "compiler_base": "blockbase",
}
LEAKAGE_BLOCK_POLICY = "none"
_LEAKAGE_BLOCK_POLICY_BOUND = False


def leakage_block_tag(policy: str) -> str:
    if policy not in LEAKAGE_BLOCK_POLICY_TAG:
        raise ValueError(f"M3 leakage-block policy is not declared: {policy}")
    return LEAKAGE_BLOCK_POLICY_TAG[policy]


def private_result_root(
    source_cap: "int | None", policy: "str | None" = None
) -> Path:
    """The frozen private leaf for one rung and policy; pre-fix L0 keeps its path."""
    if source_cap not in SOURCE_CAP_LADDER:
        raise ValueError(f"M3 source cap is not a declared ladder rung: {source_cap}")
    policy = LEAKAGE_BLOCK_POLICY if policy is None else policy
    tag = leakage_block_tag(policy)
    if source_cap == SOURCE_CAP:
        leaf = PRIVATE_TASK_LEAF
    else:
        leaf = f"{PRIVATE_TASK_LEAF}__{source_cap_tag(source_cap)}"
    return PRIVATE_ROOT / (leaf if not tag else f"{leaf}__{tag}")


def bind_leakage_block_policy(policy: str) -> str:
    """Bind the forbidden-set policy once; it selects the private leaf suffix."""
    global LEAKAGE_BLOCK_POLICY, _LEAKAGE_BLOCK_POLICY_BOUND
    if policy not in LEAKAGE_BLOCK_POLICIES:
        raise ValueError(f"M3 leakage-block policy is not declared: {policy}")
    if _LEAKAGE_BLOCK_POLICY_BOUND and LEAKAGE_BLOCK_POLICY != policy:
        raise RuntimeError(
            f"M3 leakage-block policy is already bound to {LEAKAGE_BLOCK_POLICY}"
        )
    if _SOURCE_CAP_BOUND and LEAKAGE_BLOCK_POLICY != policy:
        raise RuntimeError("M3 leakage-block policy must be bound before the rung")
    LEAKAGE_BLOCK_POLICY = policy
    _LEAKAGE_BLOCK_POLICY_BOUND = True
    return policy


def bind_source_cap(source_cap: "int | None") -> Path:
    """Bind this process to one rung, once; rebinding to another leaf is refused."""
    global PRIVATE_TASK_ROOT, _SOURCE_CAP_BOUND
    root = private_result_root(source_cap)
    if _SOURCE_CAP_BOUND and PRIVATE_TASK_ROOT != root:
        raise RuntimeError(
            f"M3 source-budget rung is already bound to {PRIVATE_TASK_ROOT.name}"
        )
    PRIVATE_TASK_ROOT = root
    _SOURCE_CAP_BOUND = True
    return root
INTERFACE_WIDTH = 192
TARGET_WEIGHT = 10.0
ENDPOINTS = (
    "glucose",
    "hba1c",
    "creatinine",
    "bun",
    "hemoglobin",
    "hematocrit",
    "rbc",
    "wbc",
    "total_cholesterol",
    "sbp",
    "dbp",
)
SUPPORT_FRACTIONS = (0.01, 0.05, 0.10)
SEEDS = tuple(range(40, 50))

TARGET_COLUMN = {target: f"target__{target}" for target in ENDPOINTS}
SOURCE_SCHEMA_COLUMN = {target: f"nhkn__{target}" for target in ENDPOINTS}
TARGET_SCHEMA_COLUMN = {target: f"hrs__{target}" for target in ENDPOINTS}

# Deterministic definitions and near-definitional proxies are excluded from
# both Base and compiler inputs for the endpoint at hand.  This is the same
# criterion the M4 and M5 runtimes carry; the dict shape mirrors
# scripts/crta_v3_m4_hrs2klosa_runtime_v1.py:133.
#
# Three families qualify under that criterion for this endpoint panel:
#   CBC red-cell trio -- haemoglobin is the protein carried by red cells,
#     haematocrit is the red-cell volume fraction, and all three are reported
#     off one automated count.  wbc is a separate cell line and is not blocked.
#   blood pressure    -- systolic and diastolic are two readings of one
#     measurement taken together in every protocol here.
#   glucose metabolism -- HbA1c is the glycated fraction, i.e. a three-month
#     average of the same analyte.
# bun/creatinine are correlated renal markers but are distinct analytes, not
# definitions of one another, so they are deliberately not blocked.
LEAKAGE_BLOCKS: dict[str, set[str]] = {
    "hemoglobin": {"hematocrit", "rbc"},
    "hematocrit": {"hemoglobin", "rbc"},
    "rbc": {"hemoglobin", "hematocrit"},
    "sbp": {"dbp"},
    "dbp": {"sbp"},
    "glucose": {"hba1c"},
    "hba1c": {"glucose"},
}
assert set(LEAKAGE_BLOCKS) <= set(ENDPOINTS)
assert all(set(v) <= set(ENDPOINTS) for v in LEAKAGE_BLOCKS.values())
assert all(
    key in LEAKAGE_BLOCKS[other]
    for key, others in LEAKAGE_BLOCKS.items()
    for other in others
), "LEAKAGE_BLOCKS must be symmetric"


def blocked_endpoints(endpoint: str) -> set[str]:
    """Endpoints whose columns are forbidden alongside `endpoint`'s own."""
    if LEAKAGE_BLOCK_POLICY == "none":
        return set()
    return set(LEAKAGE_BLOCKS.get(endpoint, set()))


def forbidden_source_ids(endpoint: str) -> list[str]:
    return sorted(
        {SOURCE_SCHEMA_COLUMN[item] for item in {endpoint, *blocked_endpoints(endpoint)}}
    )


def forbidden_target_ids(endpoint: str) -> list[str]:
    return sorted(
        {TARGET_SCHEMA_COLUMN[item] for item in {endpoint, *blocked_endpoints(endpoint)}}
    )


def base_features(endpoint: str) -> tuple[str, ...]:
    """Base slots for one endpoint, minus blocked proxies under compiler_base."""
    features = BASE_FEATURES[endpoint]
    if LEAKAGE_BLOCK_POLICY != "compiler_base":
        return features
    dropped = {f"slot__{item}" for item in blocked_endpoints(endpoint)}
    kept = tuple(name for name in features if name not in dropped)
    if not kept:
        raise ValueError(f"M3 Base is empty for endpoint after blocking: {endpoint}")
    if "slot__age" not in kept:
        raise ValueError("M3 Base lacks the required age context after blocking")
    return kept

# This is the pre-existing locked HRS bridge target-feature policy.  It is
# embedded so an unbound external policy file cannot change the M3 learner.
BASE_FEATURES = {
    "bun": (
        "slot__age", "slot__sex", "slot__sbp", "slot__dbp", "slot__glucose",
        "slot__hba1c", "slot__creatinine", "slot__hemoglobin",
    ),
    "creatinine": (
        "slot__age", "slot__sex", "slot__sbp", "slot__dbp", "slot__glucose",
        "slot__hba1c", "slot__hemoglobin",
    ),
    "dbp": (
        "slot__age", "slot__sex", "slot__sbp", "slot__glucose",
        "slot__creatinine", "slot__hemoglobin",
    ),
    "glucose": (
        "slot__age", "slot__sex", "slot__sbp", "slot__dbp", "slot__hba1c",
        "slot__creatinine", "slot__hemoglobin",
    ),
    "hba1c": (
        "slot__age", "slot__sex", "slot__sbp", "slot__dbp", "slot__glucose",
        "slot__creatinine", "slot__hemoglobin",
    ),
    "hematocrit": (
        "slot__age", "slot__sex", "slot__sbp", "slot__dbp", "slot__glucose",
        "slot__hba1c", "slot__creatinine", "slot__hemoglobin",
    ),
    "hemoglobin": (
        "slot__age", "slot__sex", "slot__sbp", "slot__dbp", "slot__glucose",
        "slot__hba1c", "slot__creatinine",
    ),
    "rbc": (
        "slot__age", "slot__sex", "slot__sbp", "slot__dbp", "slot__glucose",
        "slot__hba1c", "slot__creatinine", "slot__hemoglobin",
    ),
    "sbp": (
        "slot__age", "slot__sex", "slot__dbp", "slot__glucose",
        "slot__creatinine", "slot__hemoglobin",
    ),
    "total_cholesterol": (
        "slot__age", "slot__sex", "slot__sbp", "slot__dbp", "slot__glucose",
        "slot__hba1c", "slot__creatinine", "slot__hemoglobin",
    ),
    "wbc": (
        "slot__age", "slot__sex", "slot__sbp", "slot__dbp", "slot__glucose",
        "slot__hba1c", "slot__creatinine", "slot__hemoglobin",
    ),
}

NHANES_SINGLE = {
    "slot__age": "nhanes__ridageyr",
    "slot__sex": "nhanes__riagendr",
    "slot__glucose": "nhanes__glucose",
    "slot__hba1c": "nhanes__lbxgh",
    "slot__creatinine": "nhanes__lbxscr",
    "slot__hemoglobin": "nhanes__lbxhgb",
    "slot__hematocrit": "nhanes__lbxhct",
    "slot__rbc": "nhanes__lbxrbcsi",
    "slot__wbc": "nhanes__lbxwbcsi",
    "slot__total_cholesterol": "nhanes__total_cholesterol",
    "target__glucose": "nhanes__glucose",
    "target__hba1c": "nhanes__lbxgh",
    "target__creatinine": "nhanes__lbxscr",
    "target__bun": "nhanes__lbxsbu",
    "target__hemoglobin": "nhanes__lbxhgb",
    "target__hematocrit": "nhanes__lbxhct",
    "target__rbc": "nhanes__lbxrbcsi",
    "target__wbc": "nhanes__lbxwbcsi",
    "target__total_cholesterol": "nhanes__total_cholesterol",
}
NHANES_MEAN = {
    "slot__sbp": tuple(f"nhanes__bpxsy{i}" for i in range(1, 5)),
    "slot__dbp": tuple(f"nhanes__bpxdi{i}" for i in range(1, 5)),
    "target__sbp": tuple(f"nhanes__bpxsy{i}" for i in range(1, 5)),
    "target__dbp": tuple(f"nhanes__bpxdi{i}" for i in range(1, 5)),
}
KNHANES_SINGLE = {
    "slot__age": "knhanes__age",
    "slot__sex": "knhanes__sex",
    "slot__glucose": "knhanes__he_glu",
    "slot__hba1c": "knhanes__he_hba1c",
    "slot__creatinine": "knhanes__he_crea",
    "slot__hemoglobin": "knhanes__he_hb",
    "slot__rbc": "knhanes__he_rbc",
    "slot__wbc": "knhanes__he_wbc",
    "slot__total_cholesterol": "knhanes__he_chol",
    "target__glucose": "knhanes__he_glu",
    "target__hba1c": "knhanes__he_hba1c",
    "target__creatinine": "knhanes__he_crea",
    "target__bun": "knhanes__he_bun",
    "target__hemoglobin": "knhanes__he_hb",
    "target__rbc": "knhanes__he_rbc",
    "target__wbc": "knhanes__he_wbc",
    "target__total_cholesterol": "knhanes__he_chol",
}
KNHANES_MEAN = {
    "slot__sbp": ("knhanes__he_sbp1", "knhanes__he_sbp2"),
    "slot__dbp": ("knhanes__he_dbp1", "knhanes__he_dbp2"),
    "target__sbp": ("knhanes__he_sbp1", "knhanes__he_sbp2"),
    "target__dbp": ("knhanes__he_dbp1", "knhanes__he_dbp2"),
}


@dataclass(frozen=True)
class EstimatorSpec:
    n_estimators: int = 300
    max_depth: int = 5
    learning_rate: float = 0.05
    min_child_weight: float = 5.0
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    reg_lambda: float = 1.0


FROZEN_ESTIMATOR = EstimatorSpec()


@dataclass(frozen=True)
class ModelBank:
    model_id: str
    bank_status: str
    accepted_concepts: int
    ledger_path: Path
    ledger_sha256: str
    accepted_bank: Mapping[str, Any]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require_sha256(path: Path, expected: str, label: str) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"{label} is missing: {path}")
    observed = sha256_file(path)
    if observed != expected:
        raise ValueError(
            f"{label} SHA-256 mismatch: expected={expected} observed={observed} path={path}"
        )
    return observed


def array_sha256(values: np.ndarray) -> str:
    array = np.asarray(values)
    digest = hashlib.sha256()
    digest.update(json.dumps(list(array.shape), separators=(",", ":")).encode("ascii"))
    if np.issubdtype(array.dtype, np.number):
        numeric = np.asarray(array, dtype="<f8")
        finite = np.isfinite(numeric)
        canonical = np.where(finite, numeric, 0.0).astype("<f8", copy=False)
        digest.update(finite.astype(np.uint8).tobytes(order="C"))
        digest.update(canonical.tobytes(order="C"))
    else:
        for item in array.reshape(-1):
            encoded = str(item).encode("utf-8")
            digest.update(len(encoded).to_bytes(8, "little"))
            digest.update(encoded)
    return digest.hexdigest()


def membership_sha256(keys: Iterable[str], privacy_key: bytes) -> str:
    digest = hmac.new(privacy_key, digestmod=hashlib.sha256)
    for key in keys:
        encoded = str(key).encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "little"))
        digest.update(encoded)
    return digest.hexdigest()


def row_token(key: str, privacy_key: bytes) -> str:
    return hmac.new(
        privacy_key,
        f"crta-m3-row-token-v1|{key}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def stable_order(keys: Sequence[str], namespace: str) -> np.ndarray:
    if len(set(keys)) != len(keys):
        raise ValueError(f"duplicate row identities in deterministic split: {namespace}")
    decorated = [
        (
            hashlib.sha256(f"{namespace}|{key}".encode("utf-8")).digest(),
            index,
        )
        for index, key in enumerate(keys)
    ]
    decorated.sort()
    return np.asarray([index for _, index in decorated], dtype=np.int64)


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        temp_path = Path(handle.name)
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(temp_path, path)
    path.chmod(0o600)


def atomic_write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        temp_path = Path(handle.name)
        frame.to_csv(handle, index=False, lineterminator="\n", float_format="%.17g")
    os.replace(temp_path, path)
    path.chmod(0o600)


def _lexical_absolute(path: Path) -> Path:
    """Normalize ``.``/``..`` without following a possibly hostile symlink."""

    return Path(os.path.abspath(os.fspath(path.expanduser())))


def _require_private_directory(path: Path, label: str) -> None:
    if path.is_symlink():
        raise PermissionError(f"{label} may not be a symlink")
    if not path.is_dir():
        raise NotADirectoryError(f"{label} is not a directory: {path}")
    if stat.S_IMODE(path.lstat().st_mode) != 0o700:
        raise PermissionError(f"{label} mode must be exactly 0700")


def require_private_output_root(path: Path) -> Path:
    """Require the exact task leaf on the owner-only POSIX private store."""

    candidate = _lexical_absolute(path)
    expected = _lexical_absolute(PRIVATE_TASK_ROOT)
    if candidate != expected:
        raise PermissionError(
            "M3 row-derived outputs must use the frozen task-specific private leaf"
        )
    _require_private_directory(PRIVATE_ROOT.parent, "M3 private storage parent")
    _require_private_directory(PRIVATE_ROOT, "M3 private storage root")
    if candidate.is_symlink():
        raise PermissionError("M3 private output root may not be a symlink")
    if candidate.exists():
        _require_private_directory(candidate, "M3 private output root")
    else:
        candidate.mkdir(mode=0o700)
        _require_private_directory(candidate, "M3 private output root")
    return candidate


def load_or_create_private_key(path: Path, private_root: Path) -> bytes:
    candidate = _lexical_absolute(path)
    expected = _lexical_absolute(private_root / "private_row_token_key.bin")
    if candidate != expected:
        raise PermissionError("M3 private row-token key path differs from frozen location")
    _require_private_directory(private_root, "M3 private output root")
    if candidate.is_symlink():
        raise PermissionError("M3 private row-token key may not be a symlink")
    if candidate.exists():
        mode = candidate.lstat().st_mode
        if not stat.S_ISREG(mode):
            raise PermissionError("M3 private row-token key is not a regular file")
        if stat.S_IMODE(mode) != 0o600:
            raise PermissionError("M3 private row-token key mode must be exactly 0600")
        key = candidate.read_bytes()
    else:
        key = secrets.token_bytes(32)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(candidate, flags, 0o600)
        try:
            written = os.write(descriptor, key)
            if written != len(key):
                raise OSError("short write while creating M3 private row-token key")
        finally:
            os.close(descriptor)
    if len(key) != 32:
        raise RuntimeError("M3 private row-token key must be exactly 32 bytes")
    return key


def _relative_ledger(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"M3 primary ledger must be repository-relative: {path_text}")
    resolved = (ROOT / path).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as error:
        raise ValueError(f"M3 primary ledger escapes repository: {path_text}") from error
    return resolved


def validate_frozen_configuration(args: Any) -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any], list[ModelBank], dict[str, str]
]:
    payload_hash = require_sha256(args.payload, EXPECTED_PAYLOAD_SHA256, "M3 payload")
    dsl_hash = require_sha256(args.dsl, EXPECTED_DSL_SHA256, "M3 DSL")
    runtime_map_hash = require_sha256(
        args.runtime_map, EXPECTED_RUNTIME_MAP_SHA256, "M3 runtime schema map"
    )
    payload = load_json(args.payload)
    dsl = load_json(args.dsl)
    runtime_map = load_json(args.runtime_map)
    if canonical_json_sha256(payload) != EXPECTED_PAYLOAD_CANONICAL_SHA256:
        raise ValueError("M3 payload canonical JSON hash mismatch")
    if canonical_json_sha256(dsl) != EXPECTED_DSL_CANONICAL_SHA256:
        raise ValueError("M3 DSL canonical JSON hash mismatch")
    if payload.get("schema_pair_id") != SCHEMA_PAIR_ID:
        raise ValueError("M3 payload schema-pair mismatch")
    if runtime_map.get("schema_pair_id") != SCHEMA_PAIR_ID:
        raise ValueError("M3 runtime-map schema-pair mismatch")
    for side in ("source", "target"):
        if not isinstance(runtime_map.get(side), dict):
            raise ValueError(f"M3 runtime map lacks {side} mapping")

    plan = load_json(args.bank_plan)
    audit = load_json(args.bank_audit)
    task_manifest = load_json(args.task_manifest)
    overlay = load_json(args.eligibility_overlay)
    artifact_hashes = {
        "bank_plan_sha256": sha256_file(args.bank_plan),
        "bank_audit_sha256": sha256_file(args.bank_audit),
        "task_manifest_sha256": sha256_file(args.task_manifest),
        "eligibility_overlay_sha256": sha256_file(args.eligibility_overlay),
        "payload_sha256": payload_hash,
        "payload_canonical_sha256": canonical_json_sha256(payload),
        "dsl_sha256": dsl_hash,
        "dsl_canonical_sha256": canonical_json_sha256(dsl),
        "runtime_map_sha256": runtime_map_hash,
        "compiler_sha256": require_sha256(
            args.compiler, EXPECTED_COMPILER_SHA256, "M3 fixed-width compiler"
        ),
    }
    if plan.get("selection_policy") != "primary_only":
        raise ValueError("M3 efficacy requires a primary_only bank plan")
    if plan.get("plan_version") != "crta-v3-m3-m6-bank-staging-1.1.0":
        raise ValueError("unsupported M3/M6 bank-plan version")
    for field, actual in (
        ("audit_sha256", artifact_hashes["bank_audit_sha256"]),
        ("manifest_sha256", artifact_hashes["task_manifest_sha256"]),
        ("eligibility_overlay_sha256", artifact_hashes["eligibility_overlay_sha256"]),
    ):
        if plan.get(field) != actual:
            raise ValueError(f"M3 bank-plan binding mismatch: {field}")
    if audit.get("selection_policy") != "primary_only":
        raise ValueError("M3 bank audit is not primary_only")
    if audit.get("primary_efficacy_eligible") is not True:
        raise ValueError("M3 bank audit does not mark primary efficacy eligible")
    if audit.get("manifest_sha256") != artifact_hashes["task_manifest_sha256"]:
        raise ValueError("M3 bank audit/task-manifest hash mismatch")
    binding = overlay.get("binding", {})
    if overlay.get("status") != "active_fail_closed":
        raise ValueError("M3 eligibility overlay is not active_fail_closed")
    if binding.get("primary_audit_sha256") != artifact_hashes["bank_audit_sha256"]:
        raise ValueError("M3 eligibility overlay/audit hash mismatch")
    if binding.get("task_manifest_sha256") != artifact_hashes["task_manifest_sha256"]:
        raise ValueError("M3 eligibility overlay/task-manifest hash mismatch")

    tasks = {item["id"]: item for item in task_manifest.get("tasks", [])}
    task = tasks.get(TASK_ID)
    if not isinstance(task, dict):
        raise ValueError("frozen all-task manifest has no M3 task")
    if task.get("payload_id") != "medical_nhkn_hrs_registry_documents_v1":
        raise ValueError("frozen M3 payload ID mismatch")
    if task.get("payload_sha256") != EXPECTED_PAYLOAD_SHA256:
        raise ValueError("frozen M3 task-manifest payload hash mismatch")

    audit_rows = {
        (row.get("task_id"), row.get("model_id")): row
        for row in audit.get("results", [])
    }
    plan_rows = [row for row in plan.get("stageable_rows", []) if row.get("task_id") == TASK_ID]
    if not plan_rows:
        raise ValueError("primary eligible bank plan has no M3 rows")
    if len({row.get("model_id") for row in plan_rows}) != len(plan_rows):
        raise ValueError("duplicate M3 model in primary eligible bank plan")

    banks: list[ModelBank] = []
    for row in plan_rows:
        model_id = row.get("model_id")
        status = row.get("effective_bank_status")
        if status not in {"usable_nonempty", "valid_empty"}:
            raise ValueError(f"non-stageable M3 bank entered plan: {model_id}/{status}")
        if row.get("audit_bank_status") != status:
            raise ValueError(f"unexpected M3 eligibility override: {model_id}")
        if row.get("selected_attempt") != "primary":
            raise ValueError(f"recovery M3 bank cannot enter primary efficacy: {model_id}")
        if row.get("local_verified") is not True:
            raise ValueError(f"unverified local M3 bank: {model_id}")
        audit_row = audit_rows.get((TASK_ID, model_id))
        if not isinstance(audit_row, dict):
            raise ValueError(f"M3 plan row absent from primary audit: {model_id}")
        for key in (
            "bank_status", "decision_ledger_sha256", "selected_attempt",
            "accepted_concepts",
        ):
            plan_key = "audit_bank_status" if key == "bank_status" else key
            if row.get(plan_key) != audit_row.get(key):
                raise ValueError(f"M3 plan/audit mismatch for {model_id}: {key}")
        if audit_row.get("recovery_used") is True:
            raise ValueError(f"recovery-used M3 audit row cannot enter primary efficacy: {model_id}")
        if audit_row.get("primary_proposer_ablation_eligible") is not True:
            raise ValueError(f"M3 bank lacks primary proposer eligibility: {model_id}")
        ledger_path = _relative_ledger(str(row.get("local_ledger")))
        expected_ledger_hash = str(row.get("decision_ledger_sha256"))
        ledger_hash = require_sha256(
            ledger_path, expected_ledger_hash, f"M3 {model_id} decision ledger"
        )
        if row.get("local_sha256") != ledger_hash:
            raise ValueError(f"M3 local ledger plan hash mismatch: {model_id}")
        ledger = load_json(ledger_path)
        if ledger.get("schema_pair_id") != SCHEMA_PAIR_ID:
            raise ValueError(f"M3 ledger schema-pair mismatch: {model_id}")
        ledger_hashes = ledger.get("artifact_hashes", {})
        if ledger_hashes.get("proposer_input_sha256") != EXPECTED_PAYLOAD_CANONICAL_SHA256:
            raise ValueError(f"M3 ledger payload binding mismatch: {model_id}")
        if ledger_hashes.get("dsl_sha256") != EXPECTED_DSL_CANONICAL_SHA256:
            raise ValueError(f"M3 ledger DSL binding mismatch: {model_id}")
        accepted_bank = ledger.get("accepted_bank")
        if not isinstance(accepted_bank, dict):
            raise ValueError(f"M3 ledger accepted bank missing: {model_id}")
        concept_count = len(accepted_bank.get("concept_candidates", []))
        if concept_count != int(row.get("accepted_concepts")):
            raise ValueError(f"M3 accepted-concept count mismatch: {model_id}")
        if status == "valid_empty" and concept_count != 0:
            raise ValueError(f"M3 valid-empty bank is nonempty: {model_id}")
        if status == "usable_nonempty" and concept_count <= 0:
            raise ValueError(f"M3 usable bank is empty: {model_id}")
        banks.append(
            ModelBank(
                model_id=str(model_id),
                bank_status=str(status),
                accepted_concepts=concept_count,
                ledger_path=ledger_path,
                ledger_sha256=ledger_hash,
                accepted_bank=accepted_bank,
            )
        )
    return payload, dsl, runtime_map, banks, artifact_hashes


def verify_frozen_dataset_hashes(source_path: Path, target_path: Path) -> dict[str, str]:
    """Hash both exact objects before any parquet footer or row read."""
    return {
        "source_data_sha256": require_sha256(
            source_path, EXPECTED_SOURCE_SHA256, "M3 canonical NHANES+KNHANES source"
        ),
        "target_data_sha256": require_sha256(
            target_path, EXPECTED_HRS_SHA256, "M3 HRS medical snapshot"
        ),
    }


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(np.nan, index=frame.index, dtype=np.float64)
    return pd.to_numeric(frame[column], errors="coerce")


def _mean_existing(frame: pd.DataFrame, columns: Sequence[str]) -> pd.Series:
    existing = [column for column in columns if column in frame.columns]
    if not existing:
        return pd.Series(np.nan, index=frame.index, dtype=np.float64)
    return frame[existing].apply(pd.to_numeric, errors="coerce").mean(axis=1, skipna=True)


def _source_parquet_columns(path: Path) -> list[str]:
    available = set(pq.ParquetFile(path).schema.names)
    required = {"cohort", "split"}
    identity = [column for column in ("source_subject_id", "row_id") if column in available]
    if not identity:
        raise ValueError("M3 source object lacks source_subject_id and row_id")
    for mapping in (NHANES_SINGLE, KNHANES_SINGLE):
        required.update(mapping.values())
    for groups in (NHANES_MEAN, KNHANES_MEAN):
        for columns in groups.values():
            if not set(columns) & available:
                raise ValueError(f"M3 source object lacks all repeated measures: {columns}")
    missing = sorted(required - available)
    if missing:
        raise ValueError(f"M3 source object lacks frozen columns: {missing}")
    optional_measures = {
        column
        for groups in (NHANES_MEAN, KNHANES_MEAN)
        for columns in groups.values()
        for column in columns
        if column in available
    }
    return sorted(required | optional_measures | set(identity))


def _project_source_side(
    frame: pd.DataFrame,
    cohort_label: str,
    single: Mapping[str, str],
    means: Mapping[str, Sequence[str]],
) -> pd.DataFrame:
    out = pd.DataFrame(index=frame.index)
    subject_column = "source_subject_id" if "source_subject_id" in frame else "row_id"
    out["subject_id"] = frame[subject_column].astype(str)
    out["cohort"] = cohort_label.lower()
    out["source_row_position"] = frame["_source_row_position"].astype(np.int64)
    for output_column, input_column in single.items():
        out[output_column] = _numeric(frame, input_column)
    for output_column, input_columns in means.items():
        out[output_column] = _mean_existing(frame, input_columns)
    return out


def load_source_adapter(path: Path) -> pd.DataFrame:
    columns = _source_parquet_columns(path)
    raw = pd.read_parquet(path, columns=columns).reset_index(drop=True)
    raw["_source_row_position"] = np.arange(len(raw), dtype=np.int64)
    raw = raw[raw["split"].astype(str).eq("train")].copy()
    cohort = raw["cohort"].astype(str).str.upper()
    unknown = sorted(set(cohort) - {"NHANES", "KNHANES"})
    if unknown:
        raise ValueError(f"M3 source train rows contain unknown cohorts: {unknown}")
    nhanes = _project_source_side(
        raw.loc[cohort.eq("NHANES")], "NHANES", NHANES_SINGLE, NHANES_MEAN
    )
    knhanes = _project_source_side(
        raw.loc[cohort.eq("KNHANES")], "KNHANES", KNHANES_SINGLE, KNHANES_MEAN
    )
    for column in nhanes.columns:
        if column not in knhanes.columns:
            knhanes[column] = np.nan
    for column in knhanes.columns:
        if column not in nhanes.columns:
            nhanes[column] = np.nan
    source = pd.concat([nhanes, knhanes[nhanes.columns]], ignore_index=True)
    if len(source) != EXPECTED_SOURCE_TRAIN_ROWS:
        raise ValueError(
            f"M3 source train row-count mismatch: {len(source)} != {EXPECTED_SOURCE_TRAIN_ROWS}"
        )
    source["source_row_key"] = (
        source["cohort"].astype(str)
        + "|"
        + source["subject_id"].astype(str)
        + "|"
        + source["source_row_position"].astype(str)
    )
    if source["source_row_key"].duplicated().any():
        raise ValueError("M3 source row identities are not unique")
    return source.reset_index(drop=True)


def load_target_snapshot(
    path: Path, runtime_target_columns: Iterable[str | None] = ()
) -> pd.DataFrame:
    available = set(pq.ParquetFile(path).schema.names)
    required = {
        "subject_id", "cohort", "split", *set().union(*map(set, BASE_FEATURES.values())),
        *TARGET_COLUMN.values(),
    }
    required.update(
        column for column in runtime_target_columns if isinstance(column, str) and column
    )
    missing = sorted(required - available)
    if missing:
        raise ValueError(f"M3 HRS snapshot lacks frozen columns: {missing}")
    target = pd.read_parquet(path, columns=sorted(required)).reset_index(drop=True)
    if len(target) != EXPECTED_HRS_ROWS:
        raise ValueError(f"M3 HRS row-count mismatch: {len(target)} != {EXPECTED_HRS_ROWS}")
    if not target["cohort"].astype(str).str.lower().eq("hrs").all():
        raise ValueError("M3 target snapshot contains a non-HRS cohort row")
    if target["subject_id"].isna().any() or target["subject_id"].astype(str).duplicated().any():
        raise ValueError("M3 HRS subject identities are missing or duplicated")
    target["target_row_position"] = np.arange(len(target), dtype=np.int64)
    target["target_row_key"] = (
        target["subject_id"].astype(str)
        + "|"
        + target["target_row_position"].astype(str)
    )
    return target


def select_source_cap(
    source: pd.DataFrame, endpoint: str, seed: int, cap: "int | None" = SOURCE_CAP
) -> pd.DataFrame:
    target_column = TARGET_COLUMN[endpoint]
    y = pd.to_numeric(source[target_column], errors="coerce").to_numpy(np.float64)
    eligible = source.loc[np.isfinite(y)].copy()
    if cap is None or len(eligible) < cap:
        # Truncate rather than reject; see SOURCE_BUDGET_LADDER_PROTOCOL_V1.md 2.1.
        cap = len(eligible)
    if cap < 1:
        raise ValueError(f"M3 source has no observed rows for endpoint={endpoint}")
    order = stable_order(
        eligible["source_row_key"].astype(str).tolist(),
        f"crta-m3-source-cap-v1|{endpoint}|seed={seed}",
    )
    return eligible.iloc[order[:cap]].reset_index(drop=True)


def make_target_split(
    target: pd.DataFrame, endpoint: str, seed: int, support_fraction: float
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    target_column = TARGET_COLUMN[endpoint]
    y = pd.to_numeric(target[target_column], errors="coerce").to_numpy(np.float64)
    observed = target.loc[np.isfinite(y)].copy().reset_index(drop=True)
    if len(observed) < 2:
        raise ValueError(f"M3 endpoint has fewer than two observed HRS rows: {endpoint}")
    order = stable_order(
        observed["target_row_key"].astype(str).tolist(),
        f"crta-m3-target-support-v1|{endpoint}|seed={seed}",
    )
    n_support = max(1, int(math.floor(support_fraction * len(observed))))
    n_support = min(n_support, len(observed) - 1)
    support_positions = order[:n_support]
    support_mask = np.zeros(len(observed), dtype=bool)
    support_mask[support_positions] = True
    query_mask = ~support_mask
    if support_mask.sum() == 0 or query_mask.sum() == 0 or np.any(support_mask & query_mask):
        raise ValueError("M3 target support/query split is invalid")
    return observed, support_mask, query_mask


def numeric_matrix(frame: pd.DataFrame, columns: Sequence[str]) -> np.ndarray:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"M3 base feature columns missing: {missing}")
    values = frame[list(columns)].apply(pd.to_numeric, errors="coerce").to_numpy(np.float32)
    values[~np.isfinite(values)] = np.nan
    return values


def fit_predict_cpu(
    x_train: np.ndarray,
    y_train: np.ndarray,
    sample_weight: np.ndarray,
    x_query: np.ndarray,
    seed: int,
    n_jobs: int,
    estimator_spec: EstimatorSpec = FROZEN_ESTIMATOR,
) -> np.ndarray:
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        raise RuntimeError("M3 XGBoost requires CUDA_VISIBLE_DEVICES='' before import/execution")
    if n_jobs <= 0:
        raise ValueError("M3 n_jobs must be positive")
    if x_train.ndim != 2 or x_query.ndim != 2 or x_train.shape[1] != x_query.shape[1]:
        raise ValueError("M3 train/query design matrices are not aligned")
    if not np.isfinite(y_train).all() or not np.isfinite(sample_weight).all():
        raise ValueError("M3 training outcomes/weights contain nonfinite values")
    model = XGBRegressor(
        objective="reg:squarederror",
        n_estimators=estimator_spec.n_estimators,
        max_depth=estimator_spec.max_depth,
        learning_rate=estimator_spec.learning_rate,
        min_child_weight=estimator_spec.min_child_weight,
        subsample=estimator_spec.subsample,
        colsample_bytree=estimator_spec.colsample_bytree,
        reg_lambda=estimator_spec.reg_lambda,
        random_state=seed,
        n_jobs=n_jobs,
        tree_method="hist",
        verbosity=0,
    )
    model.fit(x_train, y_train, sample_weight=sample_weight)
    prediction = np.asarray(model.predict(x_query), dtype=np.float64)
    if prediction.shape != (len(x_query),) or not np.isfinite(prediction).all():
        raise ValueError("M3 XGBoost produced missing or nonfinite predictions")
    return prediction


def regression_metrics(y_true: np.ndarray, prediction: np.ndarray) -> dict[str, float]:
    y = np.asarray(y_true, dtype=np.float64)
    pred = np.asarray(prediction, dtype=np.float64)
    if y.shape != pred.shape or y.ndim != 1 or not np.isfinite(y).all() or not np.isfinite(pred).all():
        raise ValueError("M3 metric inputs are missing, nonfinite, or misaligned")
    residual = y - pred
    variance_sum = float(np.square(y - y.mean()).sum())
    query_sd = float(np.std(y, ddof=0))
    if variance_sum <= 0.0 or not np.isfinite(query_sd) or query_sd <= 0.0:
        raise ValueError("M3 query outcome has zero/nonfinite variance")
    rmse = float(np.sqrt(np.mean(np.square(residual))))
    result = {
        "rmse": rmse,
        "mae": float(np.mean(np.abs(residual))),
        "r2": float(1.0 - np.square(residual).sum() / variance_sum),
        "query_sd": query_sd,
        "query_sd_normalized_rmse": float(rmse / query_sd),
    }
    if not all(np.isfinite(value) for value in result.values()):
        raise ValueError("M3 metrics contain nonfinite values")
    return result


def _load_compiler(path: Path):
    spec = importlib.util.spec_from_file_location("crta_v3_m3_compile_bank", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import M3 compiler: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def revalidate_authorization(authorization: Mapping[str, Any]) -> dict[str, Any]:
    """Re-open the pinned authorization record before any participant object."""

    require_sha256(
        AUTH_VALIDATOR,
        EXPECTED_AUTH_VALIDATOR_SHA256,
        "M3 HRS authorization validator",
    )
    record_path = authorization.get("record_path")
    if not isinstance(record_path, str) or not record_path:
        raise PermissionError("M3 authorization capability lacks its pinned record path")
    spec = importlib.util.spec_from_file_location(
        "crta_v3_m3_runtime_auth_revalidation", AUTH_VALIDATOR
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import the pinned HRS authorization validator")
    validator = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = validator
    spec.loader.exec_module(validator)
    verified = validator.validate(Path(record_path), SCOPE_ID)
    compared = (
        "status",
        "required_scope_id",
        "written_authorization_sha256",
        "provider_response_whitelist_entry_id",
        "provider_response_whitelist_sha256",
        "provider_response_whitelist_path",
        "record_path",
        "record_sha256",
    )
    if any(authorization.get(key) != verified.get(key) for key in compared):
        raise PermissionError("M3 authorization capability differs from pinned revalidation")
    return verified


def _prediction_frame(
    query: pd.DataFrame,
    y_true: np.ndarray,
    prediction: np.ndarray,
    privacy_key: bytes,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "query_row_position": query["target_row_position"].to_numpy(np.int64),
            "query_row_token_hmac_sha256": [
                row_token(key, privacy_key)
                for key in query["target_row_key"].astype(str)
            ],
            "y_true": np.asarray(y_true, dtype=np.float64),
            "y_pred": np.asarray(prediction, dtype=np.float64),
        }
    )


def _split_manifest(
    source: pd.DataFrame,
    target_observed: pd.DataFrame,
    support_mask: np.ndarray,
    query_mask: np.ndarray,
    endpoint: str,
    support_fraction: float,
    seed: int,
    features: Sequence[str],
    input_hashes: Mapping[str, str],
    privacy_key: bytes,
) -> dict[str, Any]:
    source_x = numeric_matrix(source, features)
    target_x = numeric_matrix(target_observed, features)
    source_y = pd.to_numeric(source[TARGET_COLUMN[endpoint]], errors="coerce").to_numpy(np.float64)
    target_y = pd.to_numeric(
        target_observed[TARGET_COLUMN[endpoint]], errors="coerce"
    ).to_numpy(np.float64)
    return {
        "split_manifest_version": "crta-v3-m3-split-manifest-1.0.0",
        "benchmark_id": BENCHMARK_ID,
        "task_id": TASK_ID,
        "endpoint": endpoint,
        "support_fraction": support_fraction,
        "seed": seed,
        "nested_support_policy": "stable_hash_prefix_within_endpoint_seed",
        "source_cap": len(source),
        "target_observed_rows": len(target_observed),
        "target_support_rows": int(support_mask.sum()),
        "target_query_rows": int(query_mask.sum()),
        "base_features": list(features),
        "source_row_membership_sha256": membership_sha256(
            source["source_row_key"].astype(str), privacy_key
        ),
        "target_support_row_membership_sha256": membership_sha256(
            target_observed.loc[support_mask, "target_row_key"].astype(str),
            privacy_key,
        ),
        "target_query_row_membership_sha256": membership_sha256(
            target_observed.loc[query_mask, "target_row_key"].astype(str),
            privacy_key,
        ),
        "source_x_sha256": array_sha256(source_x),
        "source_y_sha256": array_sha256(source_y),
        "target_support_x_sha256": array_sha256(target_x[support_mask]),
        "target_support_y_sha256": array_sha256(target_y[support_mask]),
        "target_query_x_sha256": array_sha256(target_x[query_mask]),
        "target_query_y_sha256": array_sha256(target_y[query_mask]),
        "input_hashes": dict(input_hashes),
        "raw_subject_ids_written": False,
    }


def _write_trained_arm(
    arm_dir: Path,
    query: pd.DataFrame,
    y_query: np.ndarray,
    prediction: np.ndarray,
    compiler_manifest: Mapping[str, Any],
    split_manifest_path: Path,
    arm: str,
    model_id: str | None,
    bank: ModelBank | None,
    estimator_spec: EstimatorSpec,
    n_jobs: int,
    privacy_key: bytes,
) -> dict[str, Any]:
    predictions_path = arm_dir / "predictions.csv"
    compiler_path = arm_dir / "compiler_manifest.json"
    atomic_write_csv(
        predictions_path,
        _prediction_frame(query, y_query, prediction, privacy_key),
    )
    atomic_write_json(compiler_path, dict(compiler_manifest))
    manifest = {
        "arm_manifest_version": "crta-v3-m3-trained-arm-1.0.0",
        "arm": arm,
        "model_id": model_id,
        "training_executed": True,
        "relation_used": False,
        "metrics": regression_metrics(y_query, prediction),
        "estimator": {
            "name": "XGBRegressor",
            **asdict(estimator_spec),
            "tree_method": "hist",
            "n_jobs": n_jobs,
            "device_policy": "CPU-only; CUDA hidden before XGBoost import",
        },
        "bank_status": bank.bank_status if bank else None,
        "bank_sha256": bank.ledger_sha256 if bank else None,
        "accepted_concepts": bank.accepted_concepts if bank else 0,
        "split_manifest_sha256": sha256_file(split_manifest_path),
        "prediction_values_sha256": array_sha256(prediction),
        "artifacts": {
            "predictions.csv": sha256_file(predictions_path),
            "compiler_manifest.json": sha256_file(compiler_path),
        },
    }
    manifest_path = arm_dir / "hash_manifest.json"
    atomic_write_json(manifest_path, manifest)
    manifest["artifacts"]["hash_manifest.json"] = sha256_file(manifest_path)
    return manifest


def _write_identity_arm(
    arm_dir: Path,
    bank: ModelBank,
    base_manifest: Mapping[str, Any],
    base_predictions_path: Path,
    split_manifest_path: Path,
) -> dict[str, Any]:
    if bank.bank_status != "valid_empty" or bank.accepted_concepts != 0:
        raise ValueError(f"identity arm requires a valid-empty bank: {bank.model_id}")
    identity = {
        "identity_manifest_version": "crta-v3-m3-valid-empty-identity-1.0.0",
        "arm": "auto_concept",
        "model_id": bank.model_id,
        "bank_status": "valid_empty",
        "bank_sha256": bank.ledger_sha256,
        "accepted_concepts": 0,
        "training_executed": False,
        "predictions_materialized": False,
        "identity_rule": "Auto-C = shared Base; gain = 0",
        "paired_base_predictions_sha256": sha256_file(base_predictions_path),
        "paired_base_prediction_values_sha256": base_manifest[
            "prediction_values_sha256"
        ],
        "split_manifest_sha256": sha256_file(split_manifest_path),
        "relation_used": False,
    }
    path = arm_dir / "identity_manifest.json"
    atomic_write_json(path, identity)
    identity["artifacts"] = {"identity_manifest.json": sha256_file(path)}
    return identity


def execute_cell(
    *,
    source_all: pd.DataFrame,
    target_all: pd.DataFrame,
    endpoint: str,
    support_fraction: float,
    seed: int,
    banks: Sequence[ModelBank],
    payload: Mapping[str, Any],
    dsl: Mapping[str, Any],
    runtime_map: Mapping[str, Any],
    compiler: Any,
    cell_dir: Path,
    input_hashes: Mapping[str, str],
    n_jobs: int,
    privacy_key: bytes,
    private_root: Path,
    source_cap: "int | None",
    estimator_spec: EstimatorSpec = FROZEN_ESTIMATOR,
) -> dict[str, Any]:
    started = time.perf_counter()
    source = select_source_cap(source_all, endpoint, seed, source_cap)
    target, support_mask, query_mask = make_target_split(
        target_all, endpoint, seed, support_fraction
    )
    features = base_features(endpoint)
    source_base = numeric_matrix(source, features)
    target_base = numeric_matrix(target, features)
    source_y = pd.to_numeric(source[TARGET_COLUMN[endpoint]], errors="coerce").to_numpy(np.float64)
    target_y = pd.to_numeric(target[TARGET_COLUMN[endpoint]], errors="coerce").to_numpy(np.float64)
    if not np.isfinite(source_y).all() or not np.isfinite(target_y).all():
        raise ValueError("M3 selected endpoint outcomes contain nonfinite values")
    source_zero = np.zeros((len(source), INTERFACE_WIDTH), dtype=np.float32)
    target_zero = np.zeros((len(target), INTERFACE_WIDTH), dtype=np.float32)
    base_train = np.vstack(
        [
            np.column_stack([source_base, source_zero]),
            np.column_stack([target_base[support_mask], target_zero[support_mask]]),
        ]
    )
    base_train_y = np.concatenate([source_y, target_y[support_mask]])
    weights = np.concatenate(
        [
            np.ones(len(source), dtype=np.float64),
            np.full(int(support_mask.sum()), TARGET_WEIGHT, dtype=np.float64),
        ]
    )
    query = target.loc[query_mask].reset_index(drop=True)
    query_y = target_y[query_mask]
    query_base = np.column_stack([target_base[query_mask], target_zero[query_mask]])

    _validate_private_cell_location(
        cell_dir,
        private_root,
        endpoint,
        support_fraction,
        seed,
        create_parents=True,
        cell_must_exist=False,
    )
    with tempfile.TemporaryDirectory(
        dir=cell_dir.parent, prefix=f".{cell_dir.name}.building."
    ) as temp_text:
        build_dir = Path(temp_text)
        split_path = build_dir / "split_manifest.json"
        split_manifest = _split_manifest(
            source,
            target,
            support_mask,
            query_mask,
            endpoint,
            support_fraction,
            seed,
            features,
            input_hashes,
            privacy_key,
        )
        atomic_write_json(split_path, split_manifest)

        base_prediction = fit_predict_cpu(
            base_train,
            base_train_y,
            weights,
            query_base,
            seed,
            n_jobs,
            estimator_spec,
        )
        base_dir = build_dir / "base"
        base_manifest = _write_trained_arm(
            base_dir,
            query,
            query_y,
            base_prediction,
            {
                "compiler_version": "crta-v3-m3-zero-adapter-1.0.0",
                "source": {"arm": "base", "fixed_width": INTERFACE_WIDTH},
                "target": {"arm": "base", "fixed_width": INTERFACE_WIDTH},
                "all_zero_adapter": True,
                "relation_used": False,
            },
            split_path,
            "base",
            None,
            None,
            estimator_spec,
            n_jobs,
            privacy_key,
        )
        base_predictions_path = base_dir / "predictions.csv"

        model_records: list[dict[str, Any]] = []
        for bank in banks:
            arm_dir = build_dir / "auto_c" / bank.model_id
            if bank.bank_status == "valid_empty":
                identity = _write_identity_arm(
                    arm_dir, bank, base_manifest, base_predictions_path, split_path
                )
                model_records.append(
                    {
                        "model_id": bank.model_id,
                        "bank_status": bank.bank_status,
                        "execution": "declared_identity_no_training",
                        "gain_query_sd_normalized_rmse": 0.0,
                        "artifacts": identity["artifacts"],
                    }
                )
                continue

            source_fit = np.ones(len(source), dtype=bool)
            target_compiler_fit = support_mask.copy()
            source_compiled = compiler.compile_bank(
                source,
                source_fit,
                bank.accepted_bank,
                payload,
                dsl,
                side="source",
                arm="concept",
                column_map=runtime_map["source"],
                forbidden_column_ids=forbidden_source_ids(endpoint),
            )
            target_compiled = compiler.compile_bank(
                target,
                target_compiler_fit,
                bank.accepted_bank,
                payload,
                dsl,
                side="target",
                arm="concept",
                column_map=runtime_map["target"],
                forbidden_column_ids=forbidden_target_ids(endpoint),
            )
            for side, compiled, expected_rows in (
                ("source", source_compiled, len(source)),
                ("target", target_compiled, len(target)),
            ):
                if compiled.values.shape != (expected_rows, INTERFACE_WIDTH):
                    raise ValueError(
                        f"M3 {side} concept compiler width mismatch for {bank.model_id}"
                    )
                if not np.isfinite(compiled.values).all():
                    raise ValueError(
                        f"M3 {side} concept compiler emitted nonfinite values for {bank.model_id}"
                    )
                if np.count_nonzero(compiled.values[:, 96:]) != 0:
                    raise ValueError(
                        f"M3 relation coordinates are nonzero in concept-only arm: {bank.model_id}"
                    )
            auto_train = np.vstack(
                [
                    np.column_stack([source_base, source_compiled.values]),
                    np.column_stack(
                        [target_base[support_mask], target_compiled.values[support_mask]]
                    ),
                ]
            )
            auto_query = np.column_stack(
                [target_base[query_mask], target_compiled.values[query_mask]]
            )
            prediction = fit_predict_cpu(
                auto_train,
                base_train_y,
                weights,
                auto_query,
                seed,
                n_jobs,
                estimator_spec,
            )
            manifest = _write_trained_arm(
                arm_dir,
                query,
                query_y,
                prediction,
                {
                    "compiler_version": "crta-compiler-1.0.0",
                    "source": source_compiled.metadata,
                    "target": target_compiled.metadata,
                    "interface_feature_names": list(source_compiled.feature_names),
                    "forbidden_source_column_id": SOURCE_SCHEMA_COLUMN[endpoint],
                    "forbidden_target_column_id": TARGET_SCHEMA_COLUMN[endpoint],
                    "leakage_block_policy": LEAKAGE_BLOCK_POLICY,
                    "forbidden_source_column_ids": forbidden_source_ids(endpoint),
                    "forbidden_target_column_ids": forbidden_target_ids(endpoint),
                    "relation_used": False,
                },
                split_path,
                "auto_concept",
                bank.model_id,
                bank,
                estimator_spec,
                n_jobs,
                privacy_key,
            )
            if manifest["split_manifest_sha256"] != base_manifest["split_manifest_sha256"]:
                raise ValueError(f"M3 Base/Auto-C split mismatch: {bank.model_id}")
            gain = (
                base_manifest["metrics"]["query_sd_normalized_rmse"]
                - manifest["metrics"]["query_sd_normalized_rmse"]
            )
            model_records.append(
                {
                    "model_id": bank.model_id,
                    "bank_status": bank.bank_status,
                    "execution": "trained_auto_concept",
                    "gain_query_sd_normalized_rmse": float(gain),
                    "artifacts": manifest["artifacts"],
                }
            )

        artifacts: dict[str, str] = {}
        for path in sorted(build_dir.rglob("*")):
            if path.is_file() and path.name != "COMPLETE.json":
                artifacts[str(path.relative_to(build_dir))] = sha256_file(path)
        complete = {
            "cell_manifest_version": "crta-v3-m3-cell-complete-1.0.0",
            "status": "complete",
            "task_id": TASK_ID,
            "benchmark_id": BENCHMARK_ID,
            "endpoint": endpoint,
            "support_fraction": support_fraction,
            "seed": seed,
            "source_cap": source_cap,
            "interface_width": INTERFACE_WIDTH,
            "target_weight": TARGET_WEIGHT,
            "n_jobs": n_jobs,
            "base_training_count": 1,
            "usable_auto_c_training_count": sum(
                bank.bank_status == "usable_nonempty" for bank in banks
            ),
            "valid_empty_training_count": 0,
            "valid_empty_identity_count": sum(
                bank.bank_status == "valid_empty" for bank in banks
            ),
            "relation_used": False,
            "physical_gpu_1_used": False,
            "model_records": model_records,
            "input_hashes": dict(input_hashes),
            "artifact_sha256": artifacts,
            "runtime_seconds": float(time.perf_counter() - started),
        }
        atomic_write_json(build_dir / "COMPLETE.json", complete)
        _seal_private_cell_tree(build_dir)
        os.replace(build_dir, cell_dir)
        cell_dir.chmod(0o700)
        _validate_private_cell_tree(cell_dir)
    return complete


def _support_tag(fraction: float) -> str:
    return f"support_{int(round(100 * fraction)):02d}pct"


def _cell_dir(out_root: Path, endpoint: str, fraction: float, seed: int) -> Path:
    return out_root / endpoint / _support_tag(fraction) / f"seed_{seed}"


def _validate_private_cell_location(
    cell_dir: Path,
    private_root: Path,
    endpoint: str,
    fraction: float,
    seed: int,
    *,
    create_parents: bool,
    cell_must_exist: bool | None,
) -> bool:
    """Validate every path component before any private cell read or write."""

    root = _lexical_absolute(private_root)
    candidate = _lexical_absolute(cell_dir)
    expected = _lexical_absolute(_cell_dir(root, endpoint, fraction, seed))
    if candidate != expected:
        raise PermissionError("M3 cell path differs from its frozen private location")
    _require_private_directory(root, "M3 private result root")

    current = root
    for component in (endpoint, _support_tag(fraction)):
        current = current / component
        if current.is_symlink():
            raise PermissionError(f"M3 private directory may not be a symlink: {current}")
        if current.exists():
            _require_private_directory(current, "M3 private cell parent")
        elif create_parents:
            current.mkdir(mode=0o700)
            _require_private_directory(current, "M3 private cell parent")
        else:
            raise FileNotFoundError(f"M3 private cell parent is missing: {current}")

    if candidate.is_symlink():
        raise PermissionError("M3 private cell may not be a symlink")
    exists = candidate.exists()
    if exists:
        _require_private_directory(candidate, "M3 private cell")
    if cell_must_exist is True and not exists:
        raise FileNotFoundError(f"M3 private cell is missing: {candidate}")
    if cell_must_exist is False and exists:
        raise FileExistsError(f"M3 cell exists and will not be overwritten: {candidate}")
    return exists


def _validate_private_cell_tree(cell_dir: Path) -> None:
    """Reject nested symlinks, special files, and non-owner-only modes."""

    for current_text, directory_names, file_names in os.walk(
        cell_dir, topdown=True, followlinks=False
    ):
        current = Path(current_text)
        _require_private_directory(current, "M3 private cell directory")
        for name in directory_names:
            child = current / name
            if child.is_symlink():
                raise PermissionError(f"M3 private cell contains a symlink: {child}")
        for name in file_names:
            child = current / name
            if child.is_symlink():
                raise PermissionError(f"M3 private artifact may not be a symlink: {child}")
            mode = child.lstat().st_mode
            if not stat.S_ISREG(mode):
                raise PermissionError(f"M3 private artifact is not regular: {child}")
            if stat.S_IMODE(mode) != 0o600:
                raise PermissionError(f"M3 private artifact mode is not 0600: {child}")


def _seal_private_cell_tree(cell_dir: Path) -> None:
    """Apply owner-only modes to a newly built, symlink-free cell tree."""

    for current_text, directory_names, file_names in os.walk(
        cell_dir, topdown=True, followlinks=False
    ):
        current = Path(current_text)
        if current.is_symlink() or not current.is_dir():
            raise PermissionError(f"M3 build tree contains an unsafe directory: {current}")
        current.chmod(0o700)
        for name in directory_names:
            child = current / name
            if child.is_symlink():
                raise PermissionError(f"M3 build tree contains a symlink: {child}")
        for name in file_names:
            child = current / name
            mode = child.lstat().st_mode
            if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
                raise PermissionError(f"M3 build tree contains an unsafe artifact: {child}")
            child.chmod(0o600)


def _verify_complete_cell(
    cell_dir: Path,
    endpoint: str,
    fraction: float,
    seed: int,
    input_hashes: Mapping[str, str],
    banks: Sequence[ModelBank],
    n_jobs: int,
    private_root: Path,
    source_cap: "int | None",
    estimator_spec: EstimatorSpec = FROZEN_ESTIMATOR,
) -> dict[str, Any]:
    _validate_private_cell_location(
        cell_dir,
        private_root,
        endpoint,
        fraction,
        seed,
        create_parents=False,
        cell_must_exist=True,
    )
    _validate_private_cell_tree(cell_dir)
    complete_path = cell_dir / "COMPLETE.json"
    if not complete_path.is_file():
        raise RuntimeError(f"M3 cell is partial, not hash-complete: {cell_dir}")
    complete = load_json(complete_path)
    expected = {
        "cell_manifest_version": "crta-v3-m3-cell-complete-1.0.0",
        "status": "complete",
        "task_id": TASK_ID,
        "benchmark_id": BENCHMARK_ID,
        "endpoint": endpoint,
        "support_fraction": fraction,
        "seed": seed,
        "source_cap": source_cap,
        "interface_width": INTERFACE_WIDTH,
        "target_weight": TARGET_WEIGHT,
        "n_jobs": n_jobs,
        "relation_used": False,
        "physical_gpu_1_used": False,
    }
    for key, value in expected.items():
        if complete.get(key) != value:
            raise ValueError(f"M3 completed-cell identity mismatch for {key}: {cell_dir}")
    if complete.get("input_hashes") != dict(input_hashes):
        raise ValueError(f"M3 completed-cell input hashes mismatch: {cell_dir}")
    expected_counts = {
        "base_training_count": 1,
        "usable_auto_c_training_count": sum(
            bank.bank_status == "usable_nonempty" for bank in banks
        ),
        "valid_empty_training_count": 0,
        "valid_empty_identity_count": sum(
            bank.bank_status == "valid_empty" for bank in banks
        ),
    }
    for key, value in expected_counts.items():
        if complete.get(key) != value:
            raise ValueError(f"M3 completed-cell count mismatch for {key}: {cell_dir}")
    expected_models = [(bank.model_id, bank.bank_status) for bank in banks]
    observed_models = [
        (row.get("model_id"), row.get("bank_status"))
        for row in complete.get("model_records", [])
    ]
    if observed_models != expected_models:
        raise ValueError(f"M3 completed-cell model panel mismatch: {cell_dir}")
    expected_artifacts = {
        "split_manifest.json",
        "base/predictions.csv",
        "base/compiler_manifest.json",
        "base/hash_manifest.json",
    }
    for bank in banks:
        prefix = f"auto_c/{bank.model_id}"
        if bank.bank_status == "usable_nonempty":
            expected_artifacts.update(
                {
                    f"{prefix}/predictions.csv",
                    f"{prefix}/compiler_manifest.json",
                    f"{prefix}/hash_manifest.json",
                }
            )
        else:
            expected_artifacts.add(f"{prefix}/identity_manifest.json")
    actual_artifacts = {
        str(path.relative_to(cell_dir))
        for path in cell_dir.rglob("*")
        if path.is_file() and path.name != "COMPLETE.json"
    }
    if actual_artifacts != expected_artifacts:
        raise ValueError(f"M3 completed-cell artifact set mismatch: {cell_dir}")
    artifacts = complete.get("artifact_sha256")
    if not isinstance(artifacts, dict) or set(artifacts) != expected_artifacts:
        raise ValueError(f"M3 completed-cell artifact manifest missing: {cell_dir}")
    for relative, expected_hash in artifacts.items():
        path = cell_dir / relative
        if not path.is_file() or sha256_file(path) != expected_hash:
            raise ValueError(f"M3 completed-cell artifact hash mismatch: {path}")

    split_path = cell_dir / "split_manifest.json"
    split = load_json(split_path)
    split_expected = {
        "split_manifest_version": "crta-v3-m3-split-manifest-1.0.0",
        "benchmark_id": BENCHMARK_ID,
        "task_id": TASK_ID,
        "endpoint": endpoint,
        "support_fraction": fraction,
        "seed": seed,
        "source_cap": source_cap,
        "nested_support_policy": "stable_hash_prefix_within_endpoint_seed",
        "input_hashes": dict(input_hashes),
        "raw_subject_ids_written": False,
    }
    for key, value in split_expected.items():
        if split.get(key) != value:
            raise ValueError(f"M3 split manifest mismatch for {key}: {cell_dir}")
    observed_rows = split.get("target_observed_rows")
    support_rows = split.get("target_support_rows")
    query_rows = split.get("target_query_rows")
    if not all(isinstance(value, int) and value > 0 for value in (observed_rows, support_rows, query_rows)):
        raise ValueError(f"M3 split manifest has invalid row counts: {cell_dir}")
    if support_rows + query_rows != observed_rows:
        raise ValueError(f"M3 split manifest row counts do not partition target: {cell_dir}")

    def validate_trained_arm(
        arm_root: Path,
        arm: str,
        model_id: str | None,
        bank: ModelBank | None,
    ) -> tuple[dict[str, Any], tuple[tuple[int, ...], tuple[str, ...], str]]:
        prediction_path = arm_root / "predictions.csv"
        compiler_path = arm_root / "compiler_manifest.json"
        manifest_path = arm_root / "hash_manifest.json"
        manifest = load_json(manifest_path)
        prediction_frame = pd.read_csv(prediction_path, float_precision="round_trip")
        if list(prediction_frame.columns) != [
            "query_row_position",
            "query_row_token_hmac_sha256",
            "y_true",
            "y_pred",
        ]:
            raise ValueError(f"M3 prediction schema mismatch: {prediction_path}")
        if len(prediction_frame) != query_rows:
            raise ValueError(f"M3 prediction row count mismatch: {prediction_path}")
        if not bool(
            prediction_frame["query_row_token_hmac_sha256"]
            .astype(str)
            .str.fullmatch(r"[0-9a-f]{64}")
            .all()
        ):
            raise ValueError(f"M3 prediction row tokens are malformed: {prediction_path}")
        positions = pd.to_numeric(
            prediction_frame["query_row_position"], errors="coerce"
        ).to_numpy(np.float64)
        if (
            not np.isfinite(positions).all()
            or not np.equal(positions, np.floor(positions)).all()
            or len(np.unique(positions)) != len(positions)
        ):
            raise ValueError(f"M3 prediction row positions are invalid: {prediction_path}")
        tokens = tuple(prediction_frame["query_row_token_hmac_sha256"].astype(str))
        if len(set(tokens)) != len(tokens):
            raise ValueError(f"M3 prediction row tokens are duplicated: {prediction_path}")
        y_true = pd.to_numeric(prediction_frame["y_true"], errors="coerce").to_numpy(np.float64)
        prediction = pd.to_numeric(prediction_frame["y_pred"], errors="coerce").to_numpy(np.float64)
        recomputed = regression_metrics(y_true, prediction)
        y_true_hash = array_sha256(y_true)
        if y_true_hash != split.get("target_query_y_sha256"):
            raise ValueError(f"M3 prediction y_true differs from frozen query: {arm_root}")
        manifest_expected = {
            "arm_manifest_version": "crta-v3-m3-trained-arm-1.0.0",
            "arm": arm,
            "model_id": model_id,
            "training_executed": True,
            "relation_used": False,
            "bank_status": bank.bank_status if bank else None,
            "bank_sha256": bank.ledger_sha256 if bank else None,
            "accepted_concepts": bank.accepted_concepts if bank else 0,
            "split_manifest_sha256": sha256_file(split_path),
            "prediction_values_sha256": array_sha256(prediction),
        }
        for key, value in manifest_expected.items():
            if manifest.get(key) != value:
                raise ValueError(f"M3 trained-arm manifest mismatch for {key}: {arm_root}")
        if manifest.get("metrics") != recomputed:
            raise ValueError(f"M3 trained-arm metrics do not match predictions: {arm_root}")
        estimator = manifest.get("estimator", {})
        expected_estimator = {
            "name": "XGBRegressor",
            **asdict(estimator_spec),
            "tree_method": "hist",
            "n_jobs": n_jobs,
            "device_policy": "CPU-only; CUDA hidden before XGBoost import",
        }
        if estimator != expected_estimator:
            raise ValueError(f"M3 trained-arm estimator mismatch: {arm_root}")
        if manifest.get("artifacts") != {
            "predictions.csv": sha256_file(prediction_path),
            "compiler_manifest.json": sha256_file(compiler_path),
        }:
            raise ValueError(f"M3 trained-arm inner artifact mismatch: {arm_root}")
        compiler_manifest = load_json(compiler_path)
        if compiler_manifest.get("relation_used") is not False:
            raise ValueError(f"M3 trained arm unexpectedly uses relations: {arm_root}")
        pairing = (
            tuple(positions.astype(np.int64)),
            tokens,
            y_true_hash,
        )
        return manifest, pairing

    base_manifest, base_pairing = validate_trained_arm(
        cell_dir / "base", "base", None, None
    )
    base_prediction_hash = sha256_file(cell_dir / "base/predictions.csv")
    validated_records: list[dict[str, Any]] = []
    for bank in banks:
        arm_root = cell_dir / "auto_c" / bank.model_id
        if bank.bank_status == "usable_nonempty":
            manifest, auto_pairing = validate_trained_arm(
                arm_root, "auto_concept", bank.model_id, bank
            )
            if auto_pairing != base_pairing:
                raise ValueError(
                    f"M3 Base/Auto-C paired query rows differ: {bank.model_id}"
                )
            gain = (
                base_manifest["metrics"]["query_sd_normalized_rmse"]
                - manifest["metrics"]["query_sd_normalized_rmse"]
            )
            validated_records.append(
                {
                    "model_id": bank.model_id,
                    "bank_status": bank.bank_status,
                    "execution": "trained_auto_concept",
                    "gain_query_sd_normalized_rmse": float(gain),
                    "artifacts": {
                        "predictions.csv": sha256_file(arm_root / "predictions.csv"),
                        "compiler_manifest.json": sha256_file(arm_root / "compiler_manifest.json"),
                        "hash_manifest.json": sha256_file(arm_root / "hash_manifest.json"),
                    },
                }
            )
        else:
            identity_path = arm_root / "identity_manifest.json"
            identity = load_json(identity_path)
            expected_identity = {
                "identity_manifest_version": "crta-v3-m3-valid-empty-identity-1.0.0",
                "arm": "auto_concept",
                "model_id": bank.model_id,
                "bank_status": "valid_empty",
                "bank_sha256": bank.ledger_sha256,
                "accepted_concepts": 0,
                "training_executed": False,
                "predictions_materialized": False,
                "identity_rule": "Auto-C = shared Base; gain = 0",
                "paired_base_predictions_sha256": base_prediction_hash,
                "paired_base_prediction_values_sha256": base_manifest["prediction_values_sha256"],
                "split_manifest_sha256": sha256_file(split_path),
                "relation_used": False,
            }
            if identity != expected_identity:
                raise ValueError(f"M3 valid-empty identity mismatch: {arm_root}")
            validated_records.append(
                {
                    "model_id": bank.model_id,
                    "bank_status": bank.bank_status,
                    "execution": "declared_identity_no_training",
                    "gain_query_sd_normalized_rmse": 0.0,
                    "artifacts": {
                        "identity_manifest.json": sha256_file(identity_path)
                    },
                }
            )
    if complete.get("model_records") != validated_records:
        raise ValueError(f"M3 completed-cell model records are not derivable: {cell_dir}")
    return complete


def run(args: Any, authorization: Mapping[str, Any]) -> int:
    authorization = revalidate_authorization(authorization)
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        raise RuntimeError("M3 runtime is not CPU-only")
    if args.n_jobs <= 0:
        raise ValueError("--n-jobs must be positive")
    if args.shard_count <= 0 or not 0 <= args.shard_index < args.shard_count:
        raise ValueError("--shard-index must be in [0, --shard-count)")

    os.umask(0o077)
    args.out_root = require_private_output_root(args.out_root)
    privacy_key = load_or_create_private_key(
        args.out_root / "private_row_token_key.bin", args.out_root
    )

    payload, dsl, runtime_map, banks, contract_hashes = validate_frozen_configuration(args)

    # Authorization has passed.  Hash both participant-level objects before
    # reading a parquet footer or any row from either object.
    dataset_hashes = verify_frozen_dataset_hashes(args.source_parquet, args.hrs_snapshot)
    input_hashes = {
        **dataset_hashes,
        **contract_hashes,
        "model_panel_sha256": canonical_json_sha256(
            [
                {
                    "model_id": bank.model_id,
                    "status": bank.bank_status,
                    "bank_sha256": bank.ledger_sha256,
                }
                for bank in banks
            ]
        ),
        "authorization_record_sha256": str(authorization["record_sha256"]),
        "authorization_document_sha256": str(
            authorization["written_authorization_sha256"]
        ),
        "authorization_whitelist_sha256": str(
            authorization["provider_response_whitelist_sha256"]
        ),
        "authorization_validator_sha256": sha256_file(AUTH_VALIDATOR),
        "launcher_sha256": sha256_file(
            ROOT / "scripts/run_crta_v3_m3_nhkn2hrs_auto_c_v1.py"
        ),
        "runtime_sha256": sha256_file(Path(__file__).resolve()),
        "private_row_token_key_sha256": hashlib.sha256(privacy_key).hexdigest(),
    }
    source = load_source_adapter(args.source_parquet)
    target = load_target_snapshot(args.hrs_snapshot, runtime_map["target"].values())
    for side, frame in (("source", source), ("target", target)):
        required_runtime = {
            column
            for column in runtime_map[side].values()
            if isinstance(column, str) and column
        }
        missing_runtime = sorted(required_runtime - set(frame.columns))
        if missing_runtime:
            raise ValueError(
                f"M3 {side} adapter lacks frozen runtime-map columns: {missing_runtime}"
            )
    compiler = _load_compiler(args.compiler)

    _require_private_directory(args.out_root, "M3 private output root")
    frozen_run = {
        "run_contract_version": "crta-v3-m3-nhkn2hrs-auto-c-1.0.0",
        "task_id": TASK_ID,
        "benchmark_id": BENCHMARK_ID,
        "endpoints": list(ENDPOINTS),
        "support_fractions": list(SUPPORT_FRACTIONS),
        "seeds": list(SEEDS),
        "source_cap": args.source_cap,
        "interface_width": INTERFACE_WIDTH,
        "target_weight": TARGET_WEIGHT,
        "estimator": asdict(FROZEN_ESTIMATOR),
        "n_jobs": args.n_jobs,
        "base_policy": "one shared Base fit per endpoint/support/seed cell",
        "leakage_block_policy": LEAKAGE_BLOCK_POLICY,
        "leakage_blocks": {
            key: sorted(value) for key, value in sorted(LEAKAGE_BLOCKS.items())
        },
        "base_features": {
            endpoint: list(base_features(endpoint)) for endpoint in ENDPOINTS
        },
        "forbidden_source_column_ids": {
            endpoint: forbidden_source_ids(endpoint) for endpoint in ENDPOINTS
        },
        "forbidden_target_column_ids": {
            endpoint: forbidden_target_ids(endpoint) for endpoint in ENDPOINTS
        },
        "valid_empty_policy": "identity outside training",
        "relation_used": False,
        "gpu_policy": "CPU-only; all CUDA devices hidden; physical GPU 1 prohibited",
        "input_hashes": input_hashes,
        "model_panel": [
            {
                "model_id": bank.model_id,
                "bank_status": bank.bank_status,
                "accepted_concepts": bank.accepted_concepts,
                "bank_sha256": bank.ledger_sha256,
            }
            for bank in banks
        ],
    }
    config_path = args.out_root / "FROZEN_RUN_CONTRACT.json"
    if config_path.is_symlink():
        raise PermissionError("M3 frozen run contract may not be a symlink")
    if config_path.exists():
        mode = config_path.lstat().st_mode
        if not stat.S_ISREG(mode) or stat.S_IMODE(mode) != 0o600:
            raise PermissionError("M3 frozen run contract must be a regular 0600 file")
        if load_json(config_path) != frozen_run:
            raise ValueError("existing M3 frozen run contract differs from requested run")
    else:
        unexpected = {
            path.name
            for path in args.out_root.iterdir()
            if path.name != "private_row_token_key.bin"
        }
        if unexpected:
            raise FileExistsError(
                "M3 private result root is nonempty without a frozen run contract"
            )
        atomic_write_json(config_path, frozen_run)

    cells = [
        (endpoint, fraction, seed)
        for endpoint in ENDPOINTS
        for fraction in SUPPORT_FRACTIONS
        for seed in SEEDS
    ]
    selected = [
        cell
        for index, cell in enumerate(cells)
        if index % args.shard_count == args.shard_index
    ]
    completed_rows: list[dict[str, Any]] = []
    for position, (endpoint, fraction, seed) in enumerate(selected, start=1):
        cell_dir = _cell_dir(args.out_root, endpoint, fraction, seed)
        if cell_dir.exists():
            if not args.skip_complete:
                raise FileExistsError(
                    f"M3 cell exists; use --skip-complete only for hash-verified resume: {cell_dir}"
                )
            complete = _verify_complete_cell(
                cell_dir,
                endpoint,
                fraction,
                seed,
                input_hashes,
                banks,
                args.n_jobs,
                args.out_root,
                args.source_cap,
            )
            execution = "skipped_hash_verified_complete"
        else:
            complete = execute_cell(
                source_all=source,
                target_all=target,
                endpoint=endpoint,
                support_fraction=fraction,
                seed=seed,
                banks=banks,
                payload=payload,
                dsl=dsl,
                runtime_map=runtime_map,
                compiler=compiler,
                cell_dir=cell_dir,
                input_hashes=input_hashes,
                n_jobs=args.n_jobs,
                privacy_key=privacy_key,
                private_root=args.out_root,
                source_cap=args.source_cap,
            )
            execution = "executed"
        complete_path = cell_dir / "COMPLETE.json"
        completed_rows.append(
            {
                "endpoint": endpoint,
                "support_fraction": fraction,
                "seed": seed,
                "execution": execution,
                "cell_complete_sha256": sha256_file(complete_path),
                "base_training_count": complete["base_training_count"],
                "usable_auto_c_training_count": complete[
                    "usable_auto_c_training_count"
                ],
                "valid_empty_identity_count": complete[
                    "valid_empty_identity_count"
                ],
            }
        )
        print(
            json.dumps(
                {
                    "position": position,
                    "selected_cells": len(selected),
                    "endpoint": endpoint,
                    "support_fraction": fraction,
                    "seed": seed,
                    "execution": execution,
                },
                sort_keys=True,
            ),
            flush=True,
        )

    shard_manifest = {
        "shard_manifest_version": "crta-v3-m3-shard-1.0.0",
        "status": "complete",
        "task_id": TASK_ID,
        "shard_index": args.shard_index,
        "shard_count": args.shard_count,
        "selected_cell_count": len(selected),
        "completed_cell_count": len(completed_rows),
        "physical_gpu_1_used": False,
        "input_hashes": input_hashes,
        "cells": completed_rows,
    }
    shard_path = args.out_root / (
        f"SHARD_{args.shard_index:03d}_OF_{args.shard_count:03d}.json"
    )
    atomic_write_json(shard_path, shard_manifest)
    print(
        json.dumps(
            {
                "status": "complete",
                "task_id": TASK_ID,
                "shard_index": args.shard_index,
                "shard_count": args.shard_count,
                "completed_cells": len(completed_rows),
                "physical_gpu_1_used": False,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 0
