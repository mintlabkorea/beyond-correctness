#!/usr/bin/env python3
"""Run the frozen generic-lexical zero-shot TabLLM reference audit."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_RUNNER = ROOT / "scripts/run_tabllm_retrospective_audit_v1.py"
PROTOCOL = ROOT / "iclr_latex_v3/TABLLM_GENERIC_LEXICAL_ZERO_SHOT_FREEZE_V1.md"
ARM = "list_generic_lexical"
NUMBER_WORDS = (
    "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen", "twenty",
)


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BASE = load_module("tabllm_generic_lexical_base_v1", BASE_RUNNER)


def sha256_file(path: Path) -> str:
    return BASE.sha256_file(path)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def template_parts(template: str) -> tuple[list[str], list[str]]:
    labels: list[str] = []
    tails: list[str] = []
    for line in template.splitlines():
        match = re.match(r"^- (.*?): (?=\$\{)(.*)$", line)
        if match is None:
            raise RuntimeError(f"unexpected List Template line: {line!r}")
        labels.append(match.group(1))
        tails.append(match.group(2))
    if not labels or len(labels) > len(NUMBER_WORDS):
        raise RuntimeError(f"unsupported feature-line count: {len(labels)}")
    return labels, tails


def generic_lexical_template(list_template: str) -> str:
    original_labels, tails = template_parts(list_template)
    identifiers = [f"Feature {NUMBER_WORDS[index]}" for index in range(len(tails))]
    if len(set(identifiers)) != len(identifiers):
        raise RuntimeError("generic identifiers are not unique")
    if set(original_labels) & set(identifiers):
        raise RuntimeError("an original label collides with a generic identifier")
    rendered = "\n".join(
        f"- {identifier}: {tail}"
        for identifier, tail in zip(identifiers, tails)
    )
    rendered_labels, rendered_tails = template_parts(rendered)
    if rendered_labels != identifiers or rendered_tails != tails:
        raise RuntimeError("generic lexical template changed non-label content")
    return rendered


def build_notes(tabllm: Any, frame: Any, dataset: str, arm: str) -> list[str]:
    if arm != ARM:
        raise ValueError(arm)
    template = getattr(tabllm, f"template_{dataset}_list")
    config = getattr(tabllm, f"template_config_{dataset}_list")
    generator = tabllm.NoteTemplate(generic_lexical_template(template), **config)
    return [
        tabllm.NoteGenerator.clean_note(generator.substitute(row))
        for _, row in frame.iterrows()
    ]


def wrapper_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument(
        "--datasets", nargs="+", choices=BASE.DATASETS, default=list(BASE.DATASETS)
    )
    parser.add_argument("--arms", nargs="+", choices=(ARM,), default=[ARM])
    parser.add_argument("--device", default="cuda:3")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--smoke-examples", type=int, default=0)
    parser.add_argument("--prepare-only", action="store_true")
    args, _ = parser.parse_known_args()
    return args


def validate_frozen_args(args: argparse.Namespace) -> None:
    if args.arms != [ARM]:
        raise ValueError(f"the frozen arm is exactly {ARM}")
    if len(args.datasets) != len(set(args.datasets)):
        raise ValueError("datasets must be unique")
    if not args.smoke_examples and not args.prepare_only:
        if tuple(args.datasets) != BASE.DATASETS:
            raise ValueError("the frozen evidence run requires all nine datasets")
        if args.device != "cuda:3":
            raise ValueError("the frozen evidence device is cuda:3")
        if args.batch_size != 16:
            raise ValueError("the frozen evidence batch size is 16")
    if os.environ.get("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION") != "python":
        raise RuntimeError(
            "PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python is required"
        )


def augment_metrics(args: argparse.Namespace) -> None:
    if args.prepare_only:
        return
    status = (
        "engineering_smoke_inadmissible"
        if args.smoke_examples
        else "frozen_generic_lexical_zero_shot_evidence"
    )
    for dataset in args.datasets:
        path = args.out_root / ARM / dataset / "metrics.json"
        if not path.is_file():
            raise FileNotFoundError(path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        list_template = getattr(
            load_tabllm_for_template(args), f"template_{dataset}_list"
        )
        original_labels, tails = template_parts(list_template)
        rendered = generic_lexical_template(list_template)
        identifiers, rendered_tails = template_parts(rendered)
        if rendered_tails != tails:
            raise RuntimeError(f"non-label template mutation: {dataset}")
        payload.update({
            "analysis_status": status,
            "runner_sha256": sha256_file(Path(__file__)),
            "base_runner_sha256": sha256_file(BASE_RUNNER),
            "reference_family": "generic_lexical",
            "reference_identifier_rule": "Feature <English number word>",
            "reference_identifiers": identifiers,
            "original_feature_count": len(original_labels),
            "original_label_sha256": sha256_text("\n".join(original_labels)),
            "placeholder_and_tail_sha256": sha256_text("\n".join(tails)),
            "reference_template_sha256": sha256_text(rendered),
            "template_audit": {
                "line_count_preserved": True,
                "line_order_preserved": True,
                "placeholder_and_tail_preserved": True,
                "identifiers_unique": True,
                "original_labels_removed": True,
                "identity_stable_over_rows": True,
            },
            "protobuf_python_implementation": os.environ.get(
                "PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"
            ),
        })
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(temporary, path)


_TABLLM_MODULE: Any | None = None


def load_tabllm_for_template(args: argparse.Namespace) -> Any:
    global _TABLLM_MODULE
    if _TABLLM_MODULE is None:
        tabllm_root = None
        for index, value in enumerate(sys.argv):
            if value == "--tabllm-root" and index + 1 < len(sys.argv):
                tabllm_root = Path(sys.argv[index + 1])
                break
        if tabllm_root is None:
            raise ValueError("--tabllm-root is required")
        _TABLLM_MODULE = load_module(
            "tabllm_generic_lexical_template_data_v1",
            tabllm_root / "create_external_datasets.py",
        )
    return _TABLLM_MODULE


def main() -> int:
    args = wrapper_args()
    validate_frozen_args(args)
    BASE.PROTOCOL = PROTOCOL
    BASE.ARMS = (ARM,)
    BASE.build_notes = build_notes
    result = BASE.main()
    if result != 0:
        return int(result)
    augment_metrics(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
