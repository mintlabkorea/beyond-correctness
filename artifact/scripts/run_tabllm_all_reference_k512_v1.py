#!/usr/bin/env python3
"""Run the frozen K=512 extension for the remaining 21 global references."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PRIOR_WRAPPER = ROOT / "scripts/run_tabllm_reference_envelope_support_ladder_v1.py"
PROTOCOL = ROOT / "iclr_latex_v3/TABLLM_ALL_REFERENCE_K512_FREEZE_V1.md"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PRIOR = load_module("tabllm_prior_reference_wrapper_v1", PRIOR_WRAPPER)
BASE = PRIOR.BASE
FROZEN_MANIFEST = PRIOR.FROZEN_MANIFEST
ALL_REFERENCES = tuple(f"ref_{index:02d}" for index in range(24))
REUSED_REFERENCES = ("ref_00", "ref_22", "ref_04")
REFERENCE_IDS = tuple(
    reference for reference in ALL_REFERENCES if reference not in REUSED_REFERENCES
)
SHOTS = (512,)


def build_notes(tabllm: Any, frame: Any, dataset: str, arm: str) -> list[str]:
    if arm not in REFERENCE_IDS:
        raise ValueError(arm)
    candidate = FROZEN_MANIFEST["datasets"][dataset]["candidates"][arm]
    permutation = tuple(
        int(value) for value in candidate["line_to_identifier_index_zero_based"]
    )
    list_template = getattr(tabllm, f"template_{dataset}_list")
    rendered = PRIOR.render_reference_template(list_template, permutation)
    if PRIOR.sha256_text(rendered) != candidate["template_sha256"]:
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
    parser.add_argument(
        "--datasets", nargs="+", choices=BASE.DATASETS, default=list(BASE.DATASETS)
    )
    parser.add_argument(
        "--arms", nargs="+", choices=REFERENCE_IDS, default=list(REFERENCE_IDS)
    )
    parser.add_argument("--shots", nargs="+", type=int, choices=SHOTS, default=[512])
    parser.add_argument(
        "--seeds", nargs="+", type=int, choices=BASE.SEEDS, default=list(BASE.SEEDS)
    )
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
        else "frozen_all_reference_k512_evidence"
    )
    for dataset, shot, seed, arm in assigned:
        path = args.out_root / arm / dataset / f"k{shot}" / f"seed{seed}" / "metrics.json"
        if not path.is_file():
            raise FileNotFoundError(path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        candidate = FROZEN_MANIFEST["datasets"][dataset]["candidates"][arm]
        payload.update({
            "analysis_status": status,
            "base_runner_sha256": PRIOR.sha256_file(PRIOR.BASE_RUNNER),
            "prior_wrapper_sha256": PRIOR.sha256_file(PRIOR_WRAPPER),
            "reference_manifest_sha256": PRIOR.REFERENCE_MANIFEST_SHA256,
            "reference_id": arm,
            "reference_selection_role": "exhaustive_remaining_21",
            "reference_permutation": candidate[
                "line_to_identifier_index_zero_based"
            ],
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
    if set(args.arms) != set(REFERENCE_IDS) and not (
        args.max_steps or args.eval_limit or args.prepare_only
    ):
        # Sharding is controlled by BASE.  Evidence runs keep the exhaustive
        # reference list so the modulo assignment remains fixed.
        raise RuntimeError("evidence execution requires all 21 frozen references")
    BASE.PROTOCOL = PROTOCOL
    BASE.ARMS = REFERENCE_IDS
    BASE.SHOTS = SHOTS
    BASE.build_notes = build_notes
    BASE.__file__ = __file__
    result = BASE.main()
    if result != 0:
        return int(result)
    augment_metrics(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
