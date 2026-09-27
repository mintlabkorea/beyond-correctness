#!/usr/bin/env python3
"""MCR-T ladder: TabPFN on the source-informativeness doses of the frozen MCR cells.

Frozen design and verdicts:
`iclr_latex_v3/MCR_TABPFN_SOURCE_INFORMATIVENESS_LADDER_PREREGISTRATION_V1.md`.

Rebuilds the identical frozen cells (same salted RNG namespace as the MCR
grid) and applies source-label interventions byte-identical to the executed
tree ladder: every internal-alpha partial permutation must reproduce the
`permutation_sha256` recorded in the tree-ladder cell, and alpha=1 must
reproduce the null-source derangement hash.  alpha=0 is read from the frozen
MCR-T results and never refit.  Monotone-constraint vectors are asserted
unused: TabPFN receives value inputs only.  Metric: nMSE (verdicts) + nRMSE
(descriptive).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE_RUNNER = ROOT / "scripts/run_crta_v3_mcr_factorial_semisynth_v1.py"
NULL_RUNNER = ROOT / "scripts/run_crta_v3_mcr_null_source_v1.py"
PREREG = (ROOT / "iclr_latex_v3/"
          "MCR_TABPFN_SOURCE_INFORMATIVENESS_LADDER_PREREGISTRATION_V1.md")
ORIGINAL_ROOT = ROOT / "experiments/crta_v3_mcr_factorial_semisynth_v1"
NULL_ROOT = ROOT / "experiments/crta_v3_mcr_null_source_v1"
TREE_LADDER_ROOT = ROOT / "experiments/crta_v3_mcr_source_informativeness_ladder_v1"
TABPFN_ALPHA0_ROOT = ROOT / "experiments/crta_v3_mcr_factorial_tabpfn_v1"
DEFAULT_OUT = ROOT / "experiments/crta_v3_mcr_tabpfn_source_informativeness_ladder_v1"
DEFAULT_INPUT = Path(
    "data/foundation/artifacts/foundation_v2/"
    "raw_adapter_source_locks_v2_3_20260724/"
    "nhanes_common_panel_source_lock_v2/nhanes_common_panel_tokens_v2.parquet")
FAMILIES = ("additive", "pairwise", "sparse")
ARMS = ("m1c1rf", "m1c0rf", "m0c1rf", "m0c0rf")
INTERNAL_ALPHAS = (0.25, 0.50, 0.75)
ALPHAS = (0.25, 0.50, 0.75, 1.00)
K = 32
N_REALIZATIONS = 20
# Same cycle-order namespace as the tree ladder: doses must be byte-identical.
CYCLE_NS = "mcr_source_informativeness_ladder_cycle_order_v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def permutation_cycles(perm: np.ndarray) -> list[list[int]]:
    """Return nontrivial cycles for the destination->source permutation."""
    perm = np.asarray(perm, dtype=np.int64)
    n = len(perm)
    if not np.array_equal(np.sort(perm), np.arange(n)):
        raise ValueError("not a permutation")
    seen = np.zeros(n, dtype=bool)
    cycles = []
    for start in range(n):
        if seen[start]:
            continue
        cycle = []
        current = start
        while not seen[current]:
            seen[current] = True
            cycle.append(int(current))
            current = int(perm[current])
        if current != start:
            raise ValueError("cycle did not close at its start")
        if len(cycle) > 1:
            cycles.append(cycle)
    return cycles


def partial_permutation(full_perm: np.ndarray, target_moved: int,
                        cycle_order: np.ndarray) -> np.ndarray:
    """Build a bijective prefix path to full_perm within one moved row."""
    full_perm = np.asarray(full_perm, dtype=np.int64)
    cycles = permutation_cycles(full_perm)
    if sorted(cycle_order.tolist()) != list(range(len(cycles))):
        raise ValueError("invalid cycle order")
    result = np.arange(len(full_perm), dtype=np.int64)
    remaining = int(target_moved)
    for cycle_index in cycle_order:
        if remaining <= 0:
            break
        cycle = cycles[int(cycle_index)]
        if remaining >= len(cycle):
            active = cycle
        elif remaining == 1:
            active = cycle[:2]
        else:
            active = cycle[:remaining]
        for i, destination in enumerate(active):
            result[destination] = active[(i + 1) % len(active)]
        remaining -= len(active)
        if len(active) < len(cycle):
            break
    moved = int(np.sum(result != np.arange(len(result))))
    if abs(moved - target_moved) > 1:
        raise AssertionError(f"moved {moved}, target {target_moved}")
    if not np.array_equal(np.sort(result), np.arange(len(result))):
        raise AssertionError("partial map is not bijective")
    return result


def max_abs_corr(x: np.ndarray, y: np.ndarray) -> float:
    values = []
    for column in x.T:
        if np.std(column) == 0 or np.std(y) == 0:
            continue
        values.append(abs(float(np.corrcoef(column, y)[0, 1])))
    return max(values, default=0.0)


def load_cell(root: Path, family: str, realization: int,
              primary: bool) -> tuple[Path, dict[str, Any]]:
    prefix = root / "primary" if primary else root
    path = prefix / family / f"r{realization:02d}" / "metrics.json"
    if not path.is_file():
        raise RuntimeError(f"missing frozen cell: {path}")
    return path, json.loads(path.read_text())


def perm_sha256(perm: np.ndarray) -> str:
    return hashlib.sha256(perm.astype("<i8", copy=False).tobytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--families", nargs="*", default=list(FAMILIES))
    parser.add_argument("--realizations", nargs="*", type=int,
                        default=list(range(N_REALIZATIONS)))
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if not set(args.families).issubset(FAMILIES):
        raise RuntimeError(f"invalid families: {args.families}")
    if any(r < 0 or r >= N_REALIZATIONS for r in args.realizations):
        raise RuntimeError(f"invalid realizations: {args.realizations}")

    base = load("mcr_tabpfn_info_ladder_base", BASE_RUNNER)
    null = load("mcr_tabpfn_info_ladder_null", NULL_RUNNER)
    from tabpfn import TabPFNRegressor

    panel = base.load_panel(args.input)
    provenance = {
        "runner_sha256": sha256_file(Path(__file__)),
        "base_runner_sha256": sha256_file(BASE_RUNNER),
        "null_runner_sha256": sha256_file(NULL_RUNNER),
        "prereg_sha256": sha256_file(PREREG),
        "input_sha256": sha256_file(args.input),
    }
    expected_cells = len(args.families) * len(args.realizations)
    for family in args.families:
        for realization in args.realizations:
            load_cell(ORIGINAL_ROOT, family, realization, primary=True)
            load_cell(NULL_ROOT, family, realization, primary=False)
            load_cell(TREE_LADDER_ROOT, family, realization, primary=False)
            load_cell(TABPFN_ALPHA0_ROOT, family, realization, primary=False)
    if args.validate_only:
        print(json.dumps({
            "expected_cells": expected_cells,
            "alphas": list(ALPHAS),
            "provenance": provenance,
        }, indent=1, sort_keys=True))
        return 0

    for family in args.families:
        for realization in args.realizations:
            out = args.out_root / family / f"r{realization:02d}" / "metrics.json"
            if out.is_file():
                existing = json.loads(out.read_text())
                if any(existing.get(key) != provenance[key] for key in provenance):
                    raise RuntimeError(
                        f"{out} does not match current provenance; "
                        "archive that tree before resuming.")
                continue
            started = time.time()
            original_path, original = load_cell(
                ORIGINAL_ROOT, family, realization, primary=True)
            null_path, null_cell = load_cell(
                NULL_ROOT, family, realization, primary=False)
            tree_path, tree_cell = load_cell(
                TREE_LADDER_ROOT, family, realization, primary=False)
            alpha0_path, _ = load_cell(
                TABPFN_ALPHA0_ROOT, family, realization, primary=False)

            cell = base.build_cell(panel, "primary", family, realization, (K,))
            if base.json_ready(cell.audit) != original["audit"]:
                raise RuntimeError("rebuilt cell audit differs from original")
            source_y = np.asarray(cell.y[cell.source_rows], dtype=np.float64)
            full_perm = null.derangement(base, family, realization, len(source_y))
            full_hash = perm_sha256(full_perm)
            expected_hash = null_cell["source_label_intervention"]["permutation_sha256"]
            if full_hash != expected_hash:
                raise RuntimeError("reconstructed full derangement hash mismatch")
            if tree_cell["full_derangement_sha256"] != full_hash:
                raise RuntimeError("tree-ladder cell disagrees on derangement hash")

            cycles = permutation_cycles(full_perm)
            order_rng = np.random.default_rng(base.stable_seed(
                CYCLE_NS, family, realization))
            cycle_order = order_rng.permutation(len(cycles))
            permutations: dict[str, np.ndarray] = {}
            for alpha in INTERNAL_ALPHAS:
                key = f"{alpha:.2f}"
                perm = partial_permutation(
                    full_perm, int(round(alpha * len(source_y))), cycle_order)
                if perm_sha256(perm) != tree_cell["construction"][key][
                        "permutation_sha256"]:
                    raise RuntimeError(
                        f"alpha={key} permutation differs from the tree ladder")
                permutations[key] = perm
            permutations["1.00"] = full_perm
            keys = [f"{alpha:.2f}" for alpha in ALPHAS]
            moved_sets = {
                key: set(np.flatnonzero(
                    permutations[key] != np.arange(len(source_y))).tolist())
                for key in keys
            }
            if not all(moved_sets[a].issubset(moved_sets[b])
                       for a, b in zip(keys, keys[1:])):
                raise AssertionError("corrupted row sets are not nested")

            reference = base.arm_matrices(cell, "m1c1rf", K, weighted=False)
            reference_x = reference[0][:len(source_y), :len(base.FEATURES)]
            y_query = np.asarray(cell.y[cell.query_rows], dtype=np.float64)
            query_var = float(np.var(y_query, ddof=0))
            if query_var <= 0:
                raise RuntimeError("non-positive query variance")

            construction = {}
            results: dict[str, dict[str, dict[str, float]]] = {}
            for alpha in ALPHAS:
                alpha_key = f"{alpha:.2f}"
                perm = permutations[alpha_key]
                partial_y = source_y[perm]
                if not np.array_equal(np.sort(source_y), np.sort(partial_y)):
                    raise AssertionError("permutation changed label multiset")
                moved = int(np.sum(perm != np.arange(len(perm))))
                construction[alpha_key] = {
                    "target_moved_rows": int(round(alpha * len(source_y))),
                    "realized_moved_rows": moved,
                    "realized_alpha": moved / len(source_y),
                    "permutation_bijective": True,
                    "label_multiset_identical": True,
                    "matches_tree_ladder": alpha_key != "1.00",
                    "matches_null_derangement": alpha_key == "1.00",
                    "max_abs_source_feature_label_corr": max_abs_corr(
                        reference_x, partial_y),
                    "permutation_sha256": perm_sha256(perm),
                }
                results[alpha_key] = {}
                for arm in ARMS:
                    x_fit, y_fit, weights, x_query, constraints = base.arm_matrices(
                        cell, arm, K, weighted=False)
                    if not np.all(weights == 1.0):
                        raise AssertionError("ladder pooling must be unweighted")
                    if any(constraints):
                        raise AssertionError("free arms must carry no signs")
                    if not np.array_equal(y_fit[:len(source_y)], source_y):
                        raise AssertionError("unexpected original source labels")
                    # Constraint vectors are deliberately discarded: TabPFN
                    # receives value inputs only (prereg: interface-aware).
                    dose_y_fit = y_fit.copy()
                    dose_y_fit[:len(source_y)] = partial_y
                    model = TabPFNRegressor(device=args.device,
                                            random_state=realization)
                    model.fit(x_fit, dose_y_fit)
                    prediction = np.asarray(model.predict(x_query),
                                            dtype=np.float64)
                    mse = float(np.mean((y_query - prediction) ** 2))
                    results[alpha_key][arm] = {
                        "nmse": mse / query_var,
                        "nrmse": float(np.sqrt(mse / query_var)),
                        "n_features": int(x_fit.shape[1]),
                    }

            payload = {
                "experiment": "mcr_tabpfn_source_informativeness_ladder_v1",
                "family": family,
                "realization": realization,
                "support_k": K,
                "backbone": "tabpfn_7_regressor",
                "device": args.device,
                "metric": "nmse = MSE/Var(y_query) (verdicts)",
                "alphas": [f"{alpha:.2f}" for alpha in ALPHAS],
                "arms": list(ARMS),
                "n_source": len(source_y),
                "n_query": len(y_query),
                "full_derangement_sha256": full_hash,
                "cycle_count": len(cycles),
                "nested_corrupted_sets": True,
                "construction": construction,
                "results": results,
                "original_metrics_sha256": sha256_file(original_path),
                "null_metrics_sha256": sha256_file(null_path),
                "tree_ladder_metrics_sha256": sha256_file(tree_path),
                "tabpfn_alpha0_metrics_sha256": sha256_file(alpha0_path),
                "wall_seconds": round(time.time() - started, 1),
                **provenance,
            }
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n",
                           encoding="utf-8")
            print(json.dumps({
                "family": family, "realization": realization,
                "wall_seconds": payload["wall_seconds"], "done": True,
            }), flush=True)

    print(json.dumps({"status": "complete",
                      "expected_cells": expected_cells}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
