#!/usr/bin/env python3
"""MCR-T: the MCR factorial's value-expressible subset on TabPFN.

Frozen design and verdicts: `iclr_latex_v3/MCR_TABPFN_PREREGISTRATION_V1.md`.

Imports the frozen MCR runner and rebuilds the identical cells (same
salted RNG namespace), so MCR-T is a third backbone paired per
realization with the executed tree grid.  Monotone-constraint vectors
returned by the shared arm builder are asserted unused: TabPFN receives
value inputs only.  Metric: nMSE (verdicts) + nRMSE (descriptive).
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
PREREG = ROOT / "iclr_latex_v3/MCR_TABPFN_PREREGISTRATION_V1.md"
DEFAULT_OUT = ROOT / "experiments/crta_v3_mcr_factorial_tabpfn_v1"

SUPPORT_K = 32
FREE_ARMS = ("m1c1rf", "m1c0rf", "m0c1rf", "m0c0rf")
OP_ARMS = {"rop_true": "m1c1r1", "rop_random": "m1c1r0"}  # matrices only


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--families", nargs="*", default=None)
    parser.add_argument("--realizations", nargs="*", type=int, default=None)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    mcr = _load("mcr_core", MCR_RUNNER)
    from tabpfn import TabPFNRegressor

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
        arm_map = dict({a: a for a in FREE_ARMS},
                       **({} if family == "additive" else OP_ARMS))
        for realization in realizations:
            out_dir = args.out_root / family / f"r{realization:02d}"
            metrics_path = out_dir / "metrics.json"
            if metrics_path.is_file():
                existing = json.loads(metrics_path.read_text())
                if any(existing.get(k) != provenance[k] for k in
                       ("runner_sha256", "mcr_runner_sha256",
                        "input_sha256", "prereg_sha256")):
                    raise RuntimeError(
                        f"{metrics_path} does not match current provenance; "
                        "archive that tree before resuming.")
                continue
            started = time.time()
            cell = mcr.build_cell(panel, "primary", family, realization,
                                  (SUPPORT_K,))
            y_query = cell.y[cell.query_rows]
            query_var = float(np.var(y_query, ddof=0))
            results: dict[str, dict[str, float]] = {}
            for arm_name, grid_arm in arm_map.items():
                x_fit, y_fit, weights, x_query, constraints = \
                    mcr.arm_matrices(cell, grid_arm, SUPPORT_K,
                                     weighted=False)
                if not np.all(weights == 1.0):
                    raise AssertionError("MCR-T pooling must be unweighted.")
                if arm_name.startswith("m") and any(constraints):
                    raise AssertionError("free arms must carry no signs")
                # Constraint vectors are deliberately discarded: TabPFN
                # receives value inputs only (prereg: interface-aware).
                model = TabPFNRegressor(device=args.device,
                                        random_state=realization)
                model.fit(x_fit, y_fit)
                prediction = np.asarray(model.predict(x_query),
                                        dtype=np.float64)
                mse = float(np.mean((y_query - prediction) ** 2))
                results[arm_name] = {
                    "nmse": mse / query_var,
                    "nrmse": float(np.sqrt(mse / query_var)),
                    "n_features": int(x_fit.shape[1]),
                }
            payload = {
                "mode": "primary_tabpfn",
                "family": family,
                "realization": realization,
                "support_k": SUPPORT_K,
                "backbone": "tabpfn_7_regressor",
                "device": args.device,
                "metric": "nmse = MSE/Var(y_query) (verdicts)",
                "arms": sorted(arm_map),
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
