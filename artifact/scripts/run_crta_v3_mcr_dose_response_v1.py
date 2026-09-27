#!/usr/bin/env python3
"""MCR-D: per-layer corruption dose-response on the frozen MCR cells.

Frozen design and verdicts:
`iclr_latex_v3/MCR_DOSE_RESPONSE_PREREGISTRATION_V1.md`.

One axis dosed at a time, the other two correct; XGBoost, K = 32.
Every graded lesion is asserted against the frozen endpoints: dose 0
equals the correct objects, the maximal M dose equals the frozen wrong
table, C dose k misroutes exactly k columns, R dose j flips exactly j
signs.
"""

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
PREREG = ROOT / "iclr_latex_v3/MCR_DOSE_RESPONSE_PREREGISTRATION_V1.md"
DEFAULT_OUT = ROOT / "experiments/crta_v3_mcr_dose_response_v1"

SUPPORT_K = 32
M_DOSES = (0, 2, 4, 6, 8)
C_DOSES = (0, 2, 4, 6, 8)


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


def partial_table(mcr, true_table, wrong_table, corrupt: set[int]):
    """Per-feature merge: corrupted features decode with the wrong table."""
    return mcr.AlignmentTable(
        canonical=true_table.canonical,
        ordinal_map={j: (wrong_table.ordinal_map[j] if j in corrupt
                         else mapping)
                     for j, mapping in true_table.ordinal_map.items()},
        inv_scale={j: (wrong_table.inv_scale[j] if j in corrupt else v)
                   for j, v in true_table.inv_scale.items()},
        inv_offset={j: (wrong_table.inv_offset[j] if j in corrupt else v)
                    for j, v in true_table.inv_offset.items()},
        declared_sentinel={j: (wrong_table.declared_sentinel[j]
                               if j in corrupt else v)
                           for j, v in true_table.declared_sentinel.items()},
        entry_count=true_table.entry_count,
    )


# k misrouted columns, type-preserving; a rotated subset needs >= 2
# members, so k = 2 rotates two ordinals and no continuous feature.
C_ROTATION_COUNTS = {2: (2, 0), 4: (2, 2), 6: (3, 3), 8: (4, 4)}


def partial_rotation(ordinal_order: list[int], continuous_order: list[int],
                     k: int) -> np.ndarray:
    perm = np.arange(8)
    ord_count, con_count = C_ROTATION_COUNTS[k]
    for order, count in ((ordinal_order, ord_count),
                         (continuous_order, con_count)):
        chosen = order[:count]
        if len(chosen) >= 2:
            for i, feature in enumerate(chosen):
                perm[feature] = chosen[(i + 1) % len(chosen)]
    return perm


def flipped_subset(mcr, relations, flip_order: list[int], j: int):
    flip = set(flip_order[:j])
    feats = tuple((f, -s if i in flip else s)
                  for i, (f, s) in enumerate(relations.feat_signs))
    pairs = tuple((a, b, op, -s if i in flip else s)
                  for i, (a, b, op, s) in enumerate(relations.pair_terms))
    return mcr.RelationSet(feats, pairs)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--families", nargs="*", default=None)
    parser.add_argument("--realizations", nargs="*", type=int, default=None)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()

    mcr = _load("mcr_core", MCR_RUNNER)
    families = args.families or list(mcr.FAMILIES)
    realizations = (args.realizations if args.realizations is not None
                    else list(range(mcr.N_REALIZATIONS)))
    provenance = {
        "input_sha256": sha256_file(mcr.DEFAULT_INPUT),
        "runner_sha256": sha256_file(Path(__file__)),
        "mcr_runner_sha256": sha256_file(MCR_RUNNER),
        "prereg_sha256": sha256_file(PREREG),
        "rng_namespace": mcr.RNG_NS,
    }
    panel = mcr.load_panel(mcr.DEFAULT_INPUT)
    print(json.dumps({"rows_source": int(len(panel.source_index)),
                      "rows_target": int(len(panel.target_index)),
                      **provenance}), flush=True)

    for family in families:
        for realization in realizations:
            out_dir = args.out_root / family / f"r{realization:02d}"
            metrics_path = out_dir / "metrics.json"
            if metrics_path.is_file():
                existing = json.loads(metrics_path.read_text())
                if any(existing.get(k) != provenance[k] for k in
                       ("runner_sha256", "mcr_runner_sha256",
                        "input_sha256", "prereg_sha256")):
                    raise RuntimeError(
                        f"{metrics_path} does not match current provenance.")
                continue
            started = time.time()
            cell = mcr.build_cell(panel, "primary", family, realization,
                                  (SUPPORT_K,))
            y_query = cell.y[cell.query_rows]
            query_var = float(np.var(y_query, ddof=0))
            truth = cell.relations["true"]
            n_signs = len(truth.feat_signs) + len(truth.pair_terms)
            r_doses = tuple(range(n_signs + 1))

            rng = mcr.keyed_rng(mcr.RNG_NS, "dose_orders", family,
                                realization)
            ordinal = sorted(cell.audit["ordinal_features"])
            continuous = sorted(set(range(8)) - set(ordinal))
            m_order = [int(x) for x in rng.permutation(8)]
            c_ord_order = [int(x) for x in rng.permutation(ordinal)]
            c_con_order = [int(x) for x in rng.permutation(continuous)]
            r_order = [int(x) for x in rng.permutation(n_signs)]

            source_true = cell.source_tables["true"]
            source_wrong = cell.source_tables["wrong"]

            def fit_arm(source_table, c_perm, relations) -> float:
                source_decoded = mcr.decode(cell.source_rendered,
                                            source_table)
                if c_perm is not None:
                    source_decoded = source_decoded[:, c_perm]
                target_support = cell.target_decoded_support[SUPPORT_K]
                frame = np.vstack([source_decoded, target_support])
                x_fit, constraints = mcr.compile_design(frame, relations)
                x_query, _ = mcr.compile_design(cell.target_decoded_query,
                                                relations)
                y_fit = np.concatenate([
                    cell.y[cell.source_rows],
                    cell.y[cell.supports[SUPPORT_K]],
                ])
                prediction = mcr.fit_predict(
                    "xgb", x_fit, y_fit, np.ones(len(y_fit)), x_query,
                    constraints, seed=realization, threads=args.threads)
                return float(np.mean((y_query - prediction) ** 2)) / query_var

            results: dict[str, dict[str, float]] = {"m": {}, "c": {}, "r": {}}
            dose0 = fit_arm(source_true, None, truth)
            for k in M_DOSES:
                if k == 0:
                    results["m"]["0"] = dose0
                    continue
                corrupt = set(m_order[:k])
                table = partial_table(mcr, source_true, source_wrong, corrupt)
                if k == 8 and mcr.table_digest(table) != \
                        mcr.table_digest(source_wrong):
                    raise AssertionError("maximal M dose != frozen wrong table")
                results["m"][str(k)] = fit_arm(table, None, truth)
            for k in C_DOSES:
                if k == 0:
                    results["c"]["0"] = dose0
                    continue
                perm = partial_rotation(c_ord_order, c_con_order, k)
                if int(np.sum(perm != np.arange(8))) != k:
                    raise AssertionError(f"C dose {k} misroutes "
                                         f"{int(np.sum(perm != np.arange(8)))}")
                results["c"][str(k)] = fit_arm(source_true, perm, truth)
            for j in r_doses:
                if j == 0:
                    results["r"]["0"] = dose0
                    continue
                relations = flipped_subset(mcr, truth, r_order, j)
                n_flipped = sum(
                    1 for a, b in zip(
                        list(truth.feat_signs) + list(truth.pair_terms),
                        list(relations.feat_signs) + list(relations.pair_terms))
                    if a != b)
                if n_flipped != j:
                    raise AssertionError(f"R dose {j} flipped {n_flipped}")
                results["r"][str(j)] = fit_arm(source_true, None, relations)

            payload = {
                "mode": "dose_response",
                "family": family,
                "realization": realization,
                "support_k": SUPPORT_K,
                "backbone": "xgb",
                "metric": "nmse = MSE/Var(y_query)",
                "m_doses": list(M_DOSES),
                "c_doses": list(C_DOSES),
                "r_doses": list(r_doses),
                "results": results,
                "wall_seconds": round(time.time() - started, 1),
                **provenance,
            }
            out_dir.mkdir(parents=True, exist_ok=True)
            metrics_path.write_text(
                json.dumps(payload, indent=1, sort_keys=True) + "\n",
                encoding="utf-8")
            print(json.dumps({"family": family, "realization": realization,
                              "wall_seconds": payload["wall_seconds"]}),
                  flush=True)
    print(json.dumps({"status": "complete"}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
