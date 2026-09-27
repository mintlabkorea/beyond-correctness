#!/usr/bin/env python3
"""Exhaustive finite-lesion calibration for the MCR N5 correspondence null.

For each frozen primary cell, enumerate all 9 x 9 = 81 admissible
type-preserving derangements of the four ordinal and four continuous
columns.  Fit the correct correspondence once and every derangement for
both frozen tree backbones at K=32.  Design and verdicts are frozen in
MCR_N5_EXHAUSTIVE_PREREGISTRATION_V1.md.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MCR_RUNNER = ROOT / "scripts/run_crta_v3_mcr_factorial_semisynth_v1.py"
PREREG = ROOT / "iclr_latex_v3/MCR_N5_EXHAUSTIVE_PREREGISTRATION_V1.md"
DEFAULT_OUT = ROOT / "experiments/crta_v3_mcr_n5_exhaustive_v1"
SUPPORT_K = 32


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def all_derangements(group: list[int]) -> list[tuple[int, ...]]:
    return [p for p in itertools.permutations(group)
            if all(a != b for a, b in zip(group, p))]


def admissible_permutations(ordinal: list[int]) -> list[np.ndarray]:
    continuous = sorted(set(range(8)) - set(ordinal))
    ord_perms = all_derangements(sorted(ordinal))
    con_perms = all_derangements(continuous)
    if len(ord_perms) != 9 or len(con_perms) != 9:
        raise AssertionError("D4 x D4 must contain exactly 81 lesions")
    out = []
    for po in ord_perms:
        for pc in con_perms:
            perm = np.arange(8)
            for position, donor in zip(sorted(ordinal), po):
                perm[position] = donor
            for position, donor in zip(continuous, pc):
                perm[position] = donor
            if np.any(perm == np.arange(8)):
                raise AssertionError("non-deranged correspondence emitted")
            out.append(perm)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--families", nargs="*", default=None)
    parser.add_argument("--realizations", nargs="*", type=int, default=None)
    parser.add_argument("--backbones", nargs="*", default=None)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()

    mcr = _load("mcr_n5_core", MCR_RUNNER)
    families = args.families or list(mcr.FAMILIES)
    realizations = (args.realizations if args.realizations is not None
                    else list(range(mcr.N_REALIZATIONS)))
    backbones = args.backbones or list(mcr.BACKBONES)
    provenance = {
        "input_sha256": sha256_file(mcr.DEFAULT_INPUT),
        "runner_sha256": sha256_file(Path(__file__)),
        "mcr_runner_sha256": sha256_file(MCR_RUNNER),
        "prereg_sha256": sha256_file(PREREG),
        "rng_namespace": mcr.RNG_NS,
    }
    panel = mcr.load_panel(mcr.DEFAULT_INPUT)
    print(json.dumps({"rows_source": len(panel.source_index),
                      "rows_target": len(panel.target_index),
                      **provenance}), flush=True)

    for family in families:
        for realization in realizations:
            out_dir = args.out_root / family / f"r{realization:02d}"
            path = out_dir / "metrics.json"
            if path.is_file():
                old = json.loads(path.read_text())
                if any(old.get(k) != provenance[k] for k in (
                        "input_sha256", "runner_sha256", "mcr_runner_sha256",
                        "prereg_sha256")):
                    raise RuntimeError(f"provenance mismatch: {path}")
                continue
            started = time.time()
            cell = mcr.build_cell(panel, "primary", family, realization,
                                  (SUPPORT_K,))
            ordinal = sorted(cell.audit["ordinal_features"])
            permutations = admissible_permutations(ordinal)
            y_query = cell.y[cell.query_rows]
            query_var = float(np.var(y_query, ddof=0))
            source_true = mcr.decode(cell.source_rendered,
                                     cell.source_tables["true"])
            target_support = cell.target_decoded_support[SUPPORT_K]
            relations = cell.relations["true"]
            y_fit = np.concatenate([
                cell.y[cell.source_rows], cell.y[cell.supports[SUPPORT_K]]])
            weights = np.ones(len(y_fit))
            x_query, _ = mcr.compile_design(cell.target_decoded_query,
                                            relations)

            def fit_nmse(backbone: str, perm: np.ndarray | None) -> float:
                source = source_true if perm is None else source_true[:, perm]
                x_fit, constraints = mcr.compile_design(
                    np.vstack([source, target_support]), relations)
                pred = mcr.fit_predict(
                    backbone, x_fit, y_fit, weights, x_query, constraints,
                    seed=realization, threads=args.threads)
                return float(np.mean((y_query - pred) ** 2)) / query_var

            results = {}
            for backbone in backbones:
                correct = fit_nmse(backbone, None)
                lesions = [fit_nmse(backbone, perm) for perm in permutations]
                results[backbone] = {
                    "correct_nmse": correct,
                    "deranged_nmse": lesions,
                }
            payload = {
                "mode": "n5_exhaustive", "family": family,
                "realization": realization, "support_k": SUPPORT_K,
                "metric": "nmse = MSE/Var(y_query)",
                "backbones": backbones,
                "ordinal_features": ordinal,
                "n_derangements": len(permutations),
                "permutations": [p.tolist() for p in permutations],
                "results": results,
                "wall_seconds": round(time.time() - started, 1),
                **provenance,
            }
            out_dir.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, indent=1, sort_keys=True)
                            + "\n", encoding="utf-8")
            print(json.dumps({"family": family,
                              "realization": realization,
                              "wall_seconds": payload["wall_seconds"]}),
                  flush=True)
    print(json.dumps({"status": "complete"}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
