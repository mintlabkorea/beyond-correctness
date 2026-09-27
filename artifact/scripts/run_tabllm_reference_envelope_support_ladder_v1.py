#!/usr/bin/env python3
"""Run the frozen nonzero-shot ladder for ref_22 and ref_04.

This wrapper deliberately reuses the validated stable-anonymous ladder runner.
It substitutes only the frozen anonymous-identifier permutation and augments
the per-cell provenance after the base runner writes each artifact.
"""

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
BASE_RUNNER = ROOT / "scripts/run_tabllm_ranon_support_ladder_v1.py"
PROTOCOL = ROOT / "iclr_latex_v3/TABLLM_REFERENCE_ENVELOPE_SUPPORT_LADDER_FREEZE_V1.md"
REFERENCE_MANIFEST = (
    ROOT / "experiments/tabllm_reference_space_v1/REFERENCE_MANIFEST_V1.json"
)
REFERENCE_MANIFEST_SHA256 = (
    "7fe208e544a954ebd2c15e273473d604107a22e49230631101466ab97097d8da"
)
REFERENCE_IDS = ("ref_22", "ref_04")
SHOTS = (4, 32, 512)


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BASE = load_module("tabllm_reference_envelope_base_v1", BASE_RUNNER)


def sha256_file(path: Path) -> str:
    return BASE.sha256_file(path)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def template_parts(list_template: str) -> tuple[list[str], list[str]]:
    labels: list[str] = []
    tails: list[str] = []
    for line in list_template.splitlines():
        match = re.match(r"^- (.*?): (?=\$\{)(.*)$", line)
        if match is None:
            raise RuntimeError(f"unexpected List Template line: {line!r}")
        labels.append(match.group(1))
        tails.append(match.group(2))
    if not labels:
        raise RuntimeError("empty List Template")
    return labels, tails


def render_reference_template(
    list_template: str, permutation: tuple[int, ...]
) -> str:
    labels, tails = template_parts(list_template)
    if len(permutation) != len(labels) or set(permutation) != set(range(len(labels))):
        raise RuntimeError("invalid anonymous-identifier permutation")
    return "\n".join(
        f"- feature_{permutation[index] + 1:03d}: {tail}"
        for index, tail in enumerate(tails)
    )


def load_frozen_manifest() -> dict[str, Any]:
    observed = sha256_file(REFERENCE_MANIFEST)
    if observed != REFERENCE_MANIFEST_SHA256:
        raise RuntimeError(
            "reference manifest hash mismatch: "
            f"{observed} != {REFERENCE_MANIFEST_SHA256}"
        )
    return json.loads(REFERENCE_MANIFEST.read_text(encoding="utf-8"))


FROZEN_MANIFEST = load_frozen_manifest()


def build_notes(tabllm: Any, frame: Any, dataset: str, arm: str) -> list[str]:
    if arm not in REFERENCE_IDS:
        raise ValueError(arm)
    candidate = FROZEN_MANIFEST["datasets"][dataset]["candidates"][arm]
    permutation = tuple(
        int(value) for value in candidate["line_to_identifier_index_zero_based"]
    )
    list_template = getattr(tabllm, f"template_{dataset}_list")
    rendered = render_reference_template(list_template, permutation)
    if sha256_text(rendered) != candidate["template_sha256"]:
        raise RuntimeError(f"frozen template hash mismatch: {dataset}/{arm}")
    config = getattr(tabllm, f"template_config_{dataset}_list")
    generator = tabllm.NoteTemplate(rendered, **config)
    return [
        tabllm.NoteGenerator.clean_note(generator.substitute(row))
        for _, row in frame.iterrows()
    ]


def wrapper_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--datasets", nargs="+", choices=BASE.DATASETS, default=list(BASE.DATASETS))
    parser.add_argument("--arms", nargs="+", choices=REFERENCE_IDS, default=list(REFERENCE_IDS))
    parser.add_argument("--shots", nargs="+", type=int, choices=SHOTS, default=list(SHOTS))
    parser.add_argument("--seeds", nargs="+", type=int, choices=BASE.SEEDS, default=list(BASE.SEEDS))
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--num-shards", type=int, default=1)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--max-steps", type=int, default=0)
    parser.add_argument("--eval-limit", type=int, default=0)
    parser.add_argument("--prepare-only", action="store_true")
    args, _ = parser.parse_known_args()
    return args


def augment_metrics(args: argparse.Namespace) -> None:
    if args.prepare_only:
        return
    cells = [
        (dataset, shot, seed, arm)
        for dataset in args.datasets
        for shot in args.shots
        for seed in args.seeds
        for arm in args.arms
    ]
    assigned = [
        cell for index, cell in enumerate(cells)
        if index % args.num_shards == args.shard_index
    ]
    status = (
        "engineering_smoke_inadmissible"
        if args.max_steps or args.eval_limit
        else "frozen_reference_envelope_support_ladder_evidence"
    )
    for dataset, shot, seed, arm in assigned:
        path = args.out_root / arm / dataset / f"k{shot}" / f"seed{seed}" / "metrics.json"
        if not path.is_file():
            raise FileNotFoundError(path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        candidate = FROZEN_MANIFEST["datasets"][dataset]["candidates"][arm]
        payload.update({
            "analysis_status": status,
            "base_runner_sha256": sha256_file(BASE_RUNNER),
            "reference_manifest_sha256": REFERENCE_MANIFEST_SHA256,
            "reference_id": arm,
            "reference_selection_role": "center" if arm == "ref_22" else "upper",
            "reference_permutation": candidate["line_to_identifier_index_zero_based"],
            "reference_template_sha256": candidate["template_sha256"],
            "execution_device": args.device,
            "execution_num_shards": args.num_shards,
            "execution_shard_index": args.shard_index,
            "protobuf_python_implementation": os.environ.get(
                "PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"
            ),
        })
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(temporary, path)


def main() -> int:
    args = wrapper_args()
    if os.environ.get("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION") != "python":
        raise RuntimeError(
            "set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python for the frozen "
            "Transformers 4.30 tokenizer compatibility path"
        )
    BASE.PROTOCOL = PROTOCOL
    BASE.ARMS = REFERENCE_IDS
    BASE.SHOTS = SHOTS
    BASE.build_notes = build_notes
    # BASE.main hashes its module-global __file__.  Point it at this wrapper so
    # evidence cache validity tracks the actual executable contract.
    BASE.__file__ = __file__
    result = BASE.main()
    if result != 0:
        return int(result)
    augment_metrics(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
