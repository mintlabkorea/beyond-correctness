#!/usr/bin/env python3
"""Fail-closed validator for written HRS authorization records."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WHITELIST = ROOT / "configs" / "HRS_AI_PROVIDER_RESPONSE_WHITELIST_V1.json"
EXPECTED_WHITELIST_SHA256 = (
    "54139cbfa9ec7cee809691bfc62a89203792955ca6c82119d78f40d2bf850995"
)

# Revision 1.1.0 extends the granted scope set to M5 and M6.  The M3 and M4
# frozen run contracts record the 1.0.0 hash
# cc49c7330667257296ec9fd7e0f55623a45218c67b86f7b1002d3cb43da83254, archived at
# configs/archive/HRS_AI_PROVIDER_RESPONSE_WHITELIST_V1.pre_m5m6_extension_cc49c733.json.
ACCEPTED_WHITELIST_VERSION = "hrs-ai-provider-response-review-1.1.0"


REQUIRED_TRUE = (
    "person_level_ai_use_authorized",
    "local_machine_learning_authorized",
    "checkpoint_generation_authorized",
)

# Never granted by the provider: the release question was withdrawn, not answered
# (M3_M6_AUTHORIZATION_PROTOCOL_CORRECTION_V2.md, correction 1).  Asserting it
# must fail closed rather than pass silently.
REQUIRED_FALSE = ("subject_manifest_generation_authorized",)

REQUIRED_EVIDENCE = (*REQUIRED_TRUE, "research_scope", "current_ai_policy_disposition")

# The provider issued an out-of-scope determination rather than an exception.
# Both dispositions are admissible; anything else fails closed.
ACCEPTED_POLICY_DISPOSITIONS = (
    "HRS_AI_LLM_USE_POLICY_2026-02-04_EXCEPTION",
    "HRS_AI_LLM_USE_POLICY_2026-02-04_OUT_OF_SCOPE_DETERMINATION",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _load_reviewed_entry(
    whitelist_path: Path,
    expected_whitelist_sha256: str,
    document_sha256: str,
    required_scope_id: str,
) -> tuple[dict[str, Any], str]:
    if not whitelist_path.is_file():
        raise PermissionError("HRS provider-response review whitelist is missing")
    whitelist_hash = sha256(whitelist_path)
    if whitelist_hash != expected_whitelist_sha256:
        raise PermissionError("HRS provider-response whitelist pin mismatch")
    whitelist = json.loads(whitelist_path.read_text(encoding="utf-8"))
    if whitelist.get("whitelist_version") != ACCEPTED_WHITELIST_VERSION:
        raise PermissionError("unsupported HRS provider-response whitelist version")
    entries = whitelist.get("approved_provider_responses")
    if not isinstance(entries, list):
        raise PermissionError("HRS provider-response whitelist is malformed")
    matches = [item for item in entries if item.get("document_sha256") == document_sha256]
    if len(matches) != 1:
        raise PermissionError(
            "written HRS document is not an independently reviewed approved provider response"
        )
    entry = matches[0]
    if entry.get("document_kind") != "provider_issued_response":
        raise PermissionError("approved HRS document must be a provider-issued response")
    if entry.get("provider") != "Health and Retirement Study":
        raise PermissionError("reviewed response provider must be Health and Retirement Study")
    if entry.get("review_status") != "approved":
        raise PermissionError("reviewed HRS provider response is not approved")
    if entry.get("policy_disposition") not in ACCEPTED_POLICY_DISPOSITIONS:
        raise PermissionError(
            "reviewed HRS response carries no admissible disposition of the current AI/LLM policy"
        )
    if entry.get("subject_manifest_public_release_prohibited") is not True:
        raise PermissionError(
            "reviewed HRS response must carry the subject-manifest non-release prohibition"
        )
    if not isinstance(entry.get("reviewed_by"), str) or not entry["reviewed_by"].strip():
        raise PermissionError("reviewed HRS provider response has no reviewer")
    if not isinstance(entry.get("reviewed_at"), str) or not entry["reviewed_at"].strip():
        raise PermissionError("reviewed HRS provider response has no review date")
    permissions = entry.get("authorized_permissions")
    if not isinstance(permissions, list) or any(key not in permissions for key in REQUIRED_TRUE):
        raise PermissionError("reviewed HRS response lacks one or more required permissions")
    scopes = entry.get("authorized_research_scope_ids")
    if not isinstance(scopes, list) or required_scope_id not in scopes:
        raise PermissionError(
            f"reviewed HRS provider response does not grant scope: {required_scope_id}"
        )
    evidence = entry.get("permission_evidence")
    if not isinstance(evidence, dict):
        raise PermissionError("reviewed HRS response has no permission evidence")
    for key in REQUIRED_EVIDENCE:
        item = evidence.get(key)
        if not isinstance(item, dict):
            raise PermissionError(f"reviewed HRS response lacks evidence for: {key}")
        if not isinstance(item.get("page"), int) or item["page"] < 1:
            raise PermissionError(f"invalid evidence page for: {key}")
        if not isinstance(item.get("paragraph_or_section"), str) or not item[
            "paragraph_or_section"
        ].strip():
            raise PermissionError(f"invalid evidence location for: {key}")
        excerpt_hash = item.get("excerpt_sha256")
        if not isinstance(excerpt_hash, str) or len(excerpt_hash) != 64:
            raise PermissionError(f"invalid evidence excerpt hash for: {key}")
    entry_id = entry.get("entry_id")
    if not isinstance(entry_id, str) or not entry_id.strip():
        raise PermissionError("reviewed HRS response has no entry ID")
    return entry, whitelist_hash


def validate(
    path: Path,
    required_scope_id: str,
) -> dict[str, Any]:
    if not path.is_file():
        raise PermissionError("written HRS authorization record is missing")
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("provider") != "Health and Retirement Study":
        raise PermissionError("authorization provider must be Health and Retirement Study")
    missing = [key for key in REQUIRED_TRUE if record.get(key) is not True]
    if missing:
        raise PermissionError(f"HRS authorization does not grant: {missing}")
    overreached = [key for key in REQUIRED_FALSE if record.get(key) is not False]
    if overreached:
        raise PermissionError(f"HRS authorization asserts ungranted permission: {overreached}")
    scopes = record.get("authorized_research_scope_ids")
    if not isinstance(scopes, list) or required_scope_id not in scopes:
        raise PermissionError(f"HRS authorization does not grant scope: {required_scope_id}")
    document_text = record.get("written_authorization_document")
    if not isinstance(document_text, str) or not document_text:
        raise PermissionError("written HRS authorization document path is missing")
    document = Path(document_text)
    if not document.is_file():
        raise PermissionError("written HRS authorization document is missing")
    expected = record.get("written_authorization_sha256")
    observed = sha256(document)
    if not isinstance(expected, str) or len(expected) != 64 or observed != expected:
        raise PermissionError("written HRS authorization document hash mismatch")
    reviewed, whitelist_hash = _load_reviewed_entry(
        DEFAULT_WHITELIST,
        EXPECTED_WHITELIST_SHA256,
        observed,
        required_scope_id,
    )
    if record.get("provider_response_whitelist_entry_id") != reviewed["entry_id"]:
        raise PermissionError("authorization record does not bind the reviewed whitelist entry")
    return {
        "status": "pass",
        "provider": record["provider"],
        "required_scope_id": required_scope_id,
        "written_authorization_sha256": observed,
        "provider_response_whitelist_entry_id": reviewed["entry_id"],
        "provider_response_whitelist_sha256": whitelist_hash,
        "provider_response_whitelist_path": str(DEFAULT_WHITELIST.resolve()),
        "record_path": str(path.resolve()),
        "record_sha256": sha256(path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hrs-ai-authorization", type=Path, required=True)
    parser.add_argument("--required-scope-id", required=True)
    args = parser.parse_args()
    result = validate(
        args.hrs_ai_authorization,
        args.required_scope_id,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
