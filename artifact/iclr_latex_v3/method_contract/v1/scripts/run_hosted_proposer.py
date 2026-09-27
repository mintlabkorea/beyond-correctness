#!/usr/bin/env python3
"""Run one hosted CLI proposer while preserving the frozen CRTA prompt artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def load_artifact(path: Path) -> dict[str, Any]:
    artifact = json.loads(path.read_text(encoding="utf-8"))
    messages = artifact.get("messages", [])
    if [item.get("role") for item in messages] != ["system", "user"]:
        raise ValueError("Prompt artifact must contain exactly one system and one user message")
    return artifact


def strict_json(raw: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(raw.strip())
    except json.JSONDecodeError as exc:
        return None, str(exc)
    if not isinstance(value, dict):
        return None, "Top-level response is not a JSON object"
    return value, None


def executable_version(executable: str) -> str | None:
    """Return a one-line CLI version without failing a proposer run."""
    try:
        completed = subprocess.run(
            [executable, "--version"],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    value = (completed.stdout or completed.stderr or "").strip()
    return value.splitlines()[0] if value else None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=["codex", "claude", "gemini"], required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--prompt-artifact", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--reasoning-effort", default="high")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.out_dir.exists() and any(args.out_dir.iterdir()):
        print(f"Refusing to overwrite non-empty run directory: {args.out_dir}", file=sys.stderr)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)

    artifact = load_artifact(args.prompt_artifact)
    system = artifact["messages"][0]["content"]
    user = artifact["messages"][1]["content"]
    flattened = system + "\n\n" + user
    raw_path = args.out_dir / "raw_response.txt"

    if args.provider == "claude":
        executable = shutil.which("claude")
        command = [
            executable or "claude",
            "--print",
            "--model",
            args.model,
            "--effort",
            args.reasoning_effort,
            "--system-prompt",
            system,
            "--tools",
            "",
            "--disable-slash-commands",
            "--no-session-persistence",
            "--output-format",
            "text",
        ]
        stdin_text = user
        role_transport = "native_system_user"
    elif args.provider == "codex":
        executable = shutil.which("codex")
        command = [
            executable or "codex",
            "exec",
            "--ephemeral",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
            "--ignore-rules",
            "--model",
            args.model,
            "-c",
            f'model_reasoning_effort="{args.reasoning_effort}"',
            "--output-last-message",
            str(raw_path),
            "--color",
            "never",
            "-",
        ]
        stdin_text = flattened
        role_transport = "flattened_system_then_user"
    else:
        executable = shutil.which("gemini")
        command = [executable or "gemini", "--model", args.model, "--output-format", "text"]
        stdin_text = flattened
        role_transport = "flattened_system_then_user"

    if executable is None:
        print(f"Missing executable for provider: {args.provider}", file=sys.stderr)
        return 2

    transport_version = executable_version(executable)

    started = datetime.now(timezone.utc)
    try:
        completed = subprocess.run(
            command,
            input=stdin_text,
            text=True,
            capture_output=True,
            timeout=args.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        completed = subprocess.CompletedProcess(command, 124, exc.stdout or "", exc.stderr or "timeout")
    finished = datetime.now(timezone.utc)

    (args.out_dir / "transport_stdout.log").write_text(completed.stdout or "", encoding="utf-8")
    (args.out_dir / "transport_stderr.log").write_text(completed.stderr or "", encoding="utf-8")
    if args.provider != "codex":
        raw_path.write_text(completed.stdout or "", encoding="utf-8")
    raw = raw_path.read_text(encoding="utf-8") if raw_path.exists() else ""
    parsed, parse_error = strict_json(raw)
    if parsed is not None:
        (args.out_dir / "raw_candidate_bank.json").write_text(
            json.dumps(parsed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    manifest = {
        "contract_version": artifact["contract_version"],
        "schema_pair_id": artifact["schema_pair_id"],
        "provider": args.provider,
        "model": args.model,
        "transport": f"{args.provider}_cli",
        "transport_version": transport_version,
        "role_transport": role_transport,
        "role_transport_confounded": role_transport != "native_system_user",
        "tools_requested": "disabled",
        "external_retrieval_requested": "disabled",
        "reasoning_effort": args.reasoning_effort,
        "native_structured_output": False,
        "return_code": completed.returncode,
        "started_at_utc": started.isoformat(),
        "finished_at_utc": finished.isoformat(),
        "elapsed_seconds": round((finished - started).total_seconds(), 3),
        "prompt_hashes": artifact["hashes"],
        "transport_prompt_sha256": sha256_text(stdin_text),
        "raw_response_sha256": sha256_text(raw),
        "raw_response_chars": len(raw),
        "strict_json_parse": parsed is not None,
        "strict_json_error": parse_error,
        "command": [item for item in command if item not in {system}],
    }
    (args.out_dir / "generation_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: manifest[key] for key in ("provider", "model", "return_code", "strict_json_parse", "elapsed_seconds")}, sort_keys=True))
    return 0 if completed.returncode == 0 and parsed is not None else 3


if __name__ == "__main__":
    raise SystemExit(main())
