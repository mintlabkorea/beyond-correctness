#!/usr/bin/env python3
"""Post-result five-level target-support ladder for MCR measurement mismatch."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MCR_RUNNER = ROOT / "scripts/run_crta_v3_mcr_factorial_semisynth_v1.py"
MD_RUNNER = ROOT / "scripts/run_crta_v3_mcr_mismatch_dose_v1.py"
DESIGN_LOCK = ROOT / "iclr_latex_v3/MCR_MISMATCH_SUPPORT_LADDER_V1.md"
MD_ROOT = ROOT / "experiments/crta_v3_mcr_mismatch_dose_v1"
DEFAULT_OUT = ROOT / "experiments/crta_v3_mcr_mismatch_support_ladder_v1"

SUPPORT_KS = (32, 64, 128, 256, 512)
DOSE = 8
ZERO_CONSTRAINTS = tuple([0] * 8)
BACKBONES = ("xgb", "histgb", "tabpfn")
ARMS = ("intended", "reference", "matched_wrong")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def array_sha256(values: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(values).tobytes()).hexdigest()


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--backbones", nargs="+", choices=BACKBONES,
                        default=list(BACKBONES))
    parser.add_argument("--families", nargs="*", default=None)
    parser.add_argument("--realizations", nargs="*", type=int, default=None)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--input", type=Path, default=None)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    mcr = _load("mcr_support_ladder_core", MCR_RUNNER)
    md = _load("mcr_support_ladder_md", MD_RUNNER)
    if DOSE not in tuple(md.DOSES):
        raise RuntimeError("Full mismatch dose is absent from the frozen runner")
    input_path = args.input or mcr.DEFAULT_INPUT
    families = args.families or list(mcr.FAMILIES)
    realizations = (args.realizations if args.realizations is not None
                    else list(range(mcr.N_REALIZATIONS)))
    if any(family not in mcr.FAMILIES for family in families):
        raise ValueError(f"Families must be drawn from {mcr.FAMILIES}")
    if any(value < 0 or value >= mcr.N_REALIZATIONS for value in realizations):
        raise ValueError("Realization index is outside the frozen grid")

    provenance = {
        "input_sha256": sha256_file(input_path),
        "runner_sha256": sha256_file(Path(__file__)),
        "mcr_runner_sha256": sha256_file(MCR_RUNNER),
        "md_runner_sha256": sha256_file(MD_RUNNER),
        "design_lock_sha256": sha256_file(DESIGN_LOCK),
        "rng_namespace": mcr.RNG_NS,
        "dose_namespace": md.MD_NS,
    }
    for family in families:
        for realization in realizations:
            frozen_path = MD_ROOT / family / f"r{realization:02d}" / "metrics.json"
            if not frozen_path.is_file():
                raise RuntimeError(f"Missing frozen mismatch cell: {frozen_path}")
    if args.validate_only:
        print(json.dumps({
            "backbones": args.backbones,
            "families": families,
            "realizations": realizations,
            "supports": list(SUPPORT_KS),
            "arms": list(ARMS),
            "expected_output_cells": (
                len(args.backbones) * len(families) * len(realizations)
            ),
            "fits_per_output_cell": len(SUPPORT_KS) * len(ARMS),
            **provenance,
        }, indent=1, sort_keys=True))
        return 0

    TabPFNRegressor = None
    if "tabpfn" in args.backbones:
        from tabpfn import TabPFNRegressor as _TabPFNRegressor
        TabPFNRegressor = _TabPFNRegressor

    panel = mcr.load_panel(input_path)
    print(json.dumps(provenance, sort_keys=True), flush=True)
    for backbone in args.backbones:
        for family in families:
            for realization in realizations:
                out_dir = args.out_root / backbone / family / f"r{realization:02d}"
                metrics_path = out_dir / "metrics.json"
                if metrics_path.is_file():
                    existing = json.loads(metrics_path.read_text())
                    keys = (
                        "runner_sha256", "mcr_runner_sha256", "md_runner_sha256",
                        "input_sha256", "design_lock_sha256",
                    )
                    if any(existing.get(key) != provenance[key] for key in keys):
                        raise RuntimeError(
                            f"{metrics_path} has stale provenance; archive the tree "
                            "before resuming"
                        )
                    continue

                started = time.time()
                frozen_path = MD_ROOT / family / f"r{realization:02d}" / "metrics.json"
                frozen = json.loads(frozen_path.read_text())
                cell = mcr.build_cell(
                    panel, "primary", family, realization, SUPPORT_KS
                )
                ordinal = tuple(cell.audit["ordinal_features"])
                bins = mcr.canonical_bins(panel, ordinal)
                rendering = mcr.draw_side_rendering(
                    ordinal, ("primary", family, realization, "source"), False
                )
                rebuilt = mcr.render_side(panel, cell.source_rows, rendering, bins)
                if not md.frames_equal(rebuilt, cell.source_rendered):
                    raise AssertionError("Source rendering rebuild mismatch")
                canonical_source = mcr.decode(
                    cell.source_rendered, cell.source_tables["true"]
                )
                order = md.dose_order(mcr, family, realization, ordinal)
                if list(order) != list(frozen["dose_order"]):
                    raise AssertionError("Dose order differs from frozen mismatch cell")
                reference_source = md.hybrid_source(
                    cell, rendering, canonical_source, order, DOSE, True
                )
                mismatch_count = md.mismatch_entries(
                    reference_source, canonical_source
                )
                if mismatch_count != int(frozen["mismatch_entry_counts"][-1]):
                    raise AssertionError(
                        "Full-dose mismatch count differs from frozen mismatch cell"
                    )

                y_query = cell.y[cell.query_rows]
                query_var = float(np.var(y_query, ddof=0))
                x_query = cell.target_decoded_query
                results = {}
                support_audit = {}
                for support_k in SUPPORT_KS:
                    target_support = cell.target_decoded_support[support_k]
                    y_fit = np.concatenate([
                        cell.y[cell.source_rows],
                        cell.y[cell.supports[support_k]],
                    ])
                    weights = np.ones(len(y_fit))
                    intended = mcr.arm_matrices(
                        cell, "m1c1rf", support_k, weighted=False
                    )
                    matched_wrong = mcr.arm_matrices(
                        cell, "m0c1rf", support_k, weighted=False
                    )
                    expected_intended = np.vstack([
                        canonical_source, target_support
                    ])
                    if not (
                        md.frames_equal(intended[0], expected_intended)
                        and np.array_equal(intended[1], y_fit)
                        and md.frames_equal(intended[3], x_query)
                    ):
                        raise AssertionError("Intended arm differs from m1c1rf")
                    if not (
                        np.array_equal(matched_wrong[1], y_fit)
                        and md.frames_equal(matched_wrong[3], x_query)
                    ):
                        raise AssertionError(
                            "Matched-wrong arm differs from m0c1rf"
                        )
                    reference = np.vstack([reference_source, target_support])
                    matrices = {
                        "intended": intended[0],
                        "reference": reference,
                        "matched_wrong": matched_wrong[0],
                    }

                    def fit(matrix: np.ndarray) -> dict[str, float]:
                        if backbone in ("xgb", "histgb"):
                            prediction = mcr.fit_predict(
                                backbone, matrix, y_fit, weights, x_query,
                                ZERO_CONSTRAINTS, seed=realization,
                                threads=args.threads,
                            )
                        else:
                            model = TabPFNRegressor(
                                device=args.device, random_state=realization
                            )
                            model.fit(matrix, y_fit)
                            prediction = np.asarray(
                                model.predict(x_query), dtype=np.float64
                            )
                        mse = float(np.mean((y_query - prediction) ** 2))
                        return {
                            "nmse": mse / query_var,
                            "nrmse": float(np.sqrt(mse / query_var)),
                            "nan_fraction_fit": float(np.mean(np.isnan(matrix))),
                        }

                    results[str(support_k)] = {
                        arm: fit(matrix) for arm, matrix in matrices.items()
                    }
                    support_audit[str(support_k)] = {
                        "n_rows": int(len(cell.supports[support_k])),
                        "row_index_sha256": array_sha256(cell.supports[support_k]),
                    }

                payload = {
                    "mode": "mismatch_support_ladder",
                    "design_status": "post_result_descriptive_extension",
                    "backbone": backbone,
                    "family": family,
                    "realization": realization,
                    "supports": list(SUPPORT_KS),
                    "arms": list(ARMS),
                    "full_mismatch_dose": DOSE,
                    "device": args.device if backbone == "tabpfn" else "cpu",
                    "dose_order": order,
                    "mismatch_entry_count": mismatch_count,
                    "support_audit": support_audit,
                    "paired_construction_gate": {
                        "dose_order": True,
                        "mismatch_entry_count": True,
                        "intended_equals_m1c1rf": True,
                        "matched_wrong_equals_m0c1rf": True,
                    },
                    "frozen_md_cell_sha256": sha256_file(frozen_path),
                    "results": results,
                    "wall_seconds": round(time.time() - started, 2),
                    **provenance,
                }
                out_dir.mkdir(parents=True, exist_ok=True)
                metrics_path.write_text(
                    json.dumps(payload, indent=1, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                print(json.dumps({
                    "backbone": backbone,
                    "family": family,
                    "realization": realization,
                    "wall_seconds": payload["wall_seconds"],
                    "done": True,
                }), flush=True)
    print(json.dumps({"status": "complete"}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
