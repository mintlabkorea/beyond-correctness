#!/usr/bin/env python3
"""Full 5x5 M x C corruption surface on frozen MCR cells."""

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
DOSE_RUNNER = ROOT / "scripts/run_crta_v3_mcr_dose_response_v1.py"
PREREG = ROOT / "iclr_latex_v3/MCR_MC_SURFACE_PREREGISTRATION_V1.md"
DEFAULT_OUT = ROOT / "experiments/crta_v3_mcr_mc_surface_v1"
DOSES = (0, 2, 4, 6, 8)
SUPPORT_K = 32


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(8 * 1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--families", nargs="*", default=None)
    ap.add_argument("--realizations", nargs="*", type=int, default=None)
    ap.add_argument("--backbones", nargs="*", default=None)
    ap.add_argument("--threads", type=int, default=2)
    args = ap.parse_args()
    mcr = _load("mcr_surface_core", MCR_RUNNER)
    dose = _load("mcr_surface_dose", DOSE_RUNNER)
    families = args.families or list(mcr.FAMILIES)
    realizations = args.realizations if args.realizations is not None else list(range(20))
    backbones = args.backbones or list(mcr.BACKBONES)
    provenance = {
        "input_sha256": sha256_file(mcr.DEFAULT_INPUT),
        "runner_sha256": sha256_file(Path(__file__)),
        "mcr_runner_sha256": sha256_file(MCR_RUNNER),
        "dose_runner_sha256": sha256_file(DOSE_RUNNER),
        "prereg_sha256": sha256_file(PREREG), "rng_namespace": mcr.RNG_NS,
    }
    panel = mcr.load_panel(mcr.DEFAULT_INPUT)
    print(json.dumps({"rows_source": len(panel.source_index),
                      "rows_target": len(panel.target_index), **provenance}),
          flush=True)
    for family in families:
        for realization in realizations:
            out_dir = args.out_root / family / f"r{realization:02d}"
            path = out_dir / "metrics.json"
            if path.is_file():
                old = json.loads(path.read_text())
                if any(old.get(k) != provenance[k] for k in (
                        "input_sha256", "runner_sha256", "mcr_runner_sha256",
                        "dose_runner_sha256", "prereg_sha256")):
                    raise RuntimeError(f"provenance mismatch: {path}")
                continue
            started = time.time()
            cell = mcr.build_cell(panel, "primary", family, realization,
                                  (SUPPORT_K,))
            y_query = cell.y[cell.query_rows]
            query_var = float(np.var(y_query, ddof=0))
            truth = cell.relations["true"]
            source_true = cell.source_tables["true"]
            source_wrong = cell.source_tables["wrong"]
            rng = mcr.keyed_rng(mcr.RNG_NS, "dose_orders", family, realization)
            ordinal = sorted(cell.audit["ordinal_features"])
            continuous = sorted(set(range(8)) - set(ordinal))
            m_order = [int(x) for x in rng.permutation(8)]
            c_ord_order = [int(x) for x in rng.permutation(ordinal)]
            c_con_order = [int(x) for x in rng.permutation(continuous)]
            y_fit = np.concatenate([
                cell.y[cell.source_rows], cell.y[cell.supports[SUPPORT_K]]])
            weights = np.ones(len(y_fit))
            x_query, _ = mcr.compile_design(cell.target_decoded_query, truth)
            target_support = cell.target_decoded_support[SUPPORT_K]
            results = {b: {} for b in backbones}
            for md in DOSES:
                table = source_true if md == 0 else dose.partial_table(
                    mcr, source_true, source_wrong, set(m_order[:md]))
                decoded = mcr.decode(cell.source_rendered, table)
                for cd in DOSES:
                    source = decoded
                    if cd:
                        perm = dose.partial_rotation(c_ord_order, c_con_order, cd)
                        if int(np.sum(perm != np.arange(8))) != cd:
                            raise AssertionError("C dose contract violated")
                        source = source[:, perm]
                    x_fit, constraints = mcr.compile_design(
                        np.vstack([source, target_support]), truth)
                    for backbone in backbones:
                        pred = mcr.fit_predict(
                            backbone, x_fit, y_fit, weights, x_query,
                            constraints, seed=realization, threads=args.threads)
                        nmse = float(np.mean((y_query - pred) ** 2)) / query_var
                        results[backbone].setdefault(str(md), {})[str(cd)] = nmse
            payload = {
                "mode": "mc_surface", "family": family,
                "realization": realization, "support_k": SUPPORT_K,
                "metric": "nmse = MSE/Var(y_query)", "doses": list(DOSES),
                "backbones": backbones, "results": results,
                "m_order": m_order, "c_ordinal_order": c_ord_order,
                "c_continuous_order": c_con_order,
                "wall_seconds": round(time.time() - started, 1), **provenance,
            }
            out_dir.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
            print(json.dumps({"family": family, "realization": realization,
                              "wall_seconds": payload["wall_seconds"]}),
                  flush=True)
    print(json.dumps({"status": "complete"}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
