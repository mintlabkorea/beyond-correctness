#!/usr/bin/env python3
"""MCR-N: the MCR factorial's value-expressible subset on a frozen MLP recipe.

Frozen design and verdicts: `iclr_latex_v3/MCR_MLP_PREREGISTRATION_V1.md`.

Imports the frozen MCR runner and rebuilds the identical cells (same
salted RNG namespace), so MCR-N is a further backbone paired per
realization with the executed tree and TabPFN grids.  Monotone-constraint
vectors returned by the shared arm builder are asserted unused on free
arms and discarded everywhere: the MLP receives value inputs only.  NaNs
are mean-imputed and exposed as binary indicator columns (frozen recipe;
the tree/TabPFN backbones route NaN natively).  Metric: nMSE (verdicts)
+ nRMSE (descriptive).
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
PREREG = ROOT / "iclr_latex_v3/MCR_MLP_PREREGISTRATION_V1.md"
DEFAULT_OUT = ROOT / "experiments/crta_v3_mcr_factorial_mlp_v1"

SUPPORT_KS = (32, 512)
FREE_ARMS = ("m1c1rf", "m1c0rf", "m0c1rf", "m0c0rf")
OP_ARMS = {"rop_true": "m1c1r1", "rop_random": "m1c1r0"}  # matrices only
HIDDEN = (32,)
ALPHA = 1e-2
LEARNING_RATE = 1e-3
MAX_ITER = 500


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


def fit_predict_mlp(x_fit: np.ndarray, y_fit: np.ndarray, x_query: np.ndarray,
                    seed: int, threads: int) -> np.ndarray:
    from sklearn.impute import SimpleImputer
    from sklearn.neural_network import MLPRegressor
    from sklearn.preprocessing import StandardScaler
    from threadpoolctl import threadpool_limits

    imputer = SimpleImputer(strategy="mean").fit(x_fit)
    fit_frame = np.hstack([imputer.transform(x_fit),
                           np.isnan(x_fit).astype(np.float64)])
    query_frame = np.hstack([imputer.transform(x_query),
                             np.isnan(x_query).astype(np.float64)])
    scaler = StandardScaler().fit(fit_frame)
    # A constant column has scale 0; StandardScaler maps it to 0, which is fine.
    fit_frame = scaler.transform(fit_frame)
    query_frame = scaler.transform(query_frame)
    y_mean, y_std = float(np.mean(y_fit)), float(np.std(y_fit))
    if y_std <= 0:
        raise RuntimeError("degenerate fit-label variance")
    model = MLPRegressor(
        hidden_layer_sizes=HIDDEN, activation="relu", solver="adam",
        alpha=ALPHA, learning_rate_init=LEARNING_RATE, max_iter=MAX_ITER,
        early_stopping=False, tol=1e-6, random_state=seed)
    with threadpool_limits(limits=max(threads, 1)):
        model.fit(fit_frame, (y_fit - y_mean) / y_std)
        prediction = model.predict(query_frame)
    return np.asarray(prediction, dtype=np.float64) * y_std + y_mean


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
                                  SUPPORT_KS)
            y_query = cell.y[cell.query_rows]
            query_var = float(np.var(y_query, ddof=0))
            results: dict[str, dict[str, dict[str, float]]] = {}
            for support_k in SUPPORT_KS:
                results[str(support_k)] = {}
                for arm_name, grid_arm in arm_map.items():
                    x_fit, y_fit, weights, x_query, constraints = \
                        mcr.arm_matrices(cell, grid_arm, support_k,
                                         weighted=False)
                    if not np.all(weights == 1.0):
                        raise AssertionError("MCR-N pooling must be unweighted.")
                    if arm_name.startswith("m") and any(constraints):
                        raise AssertionError("free arms must carry no signs")
                    # Constraint vectors are deliberately discarded: the MLP
                    # receives value inputs only (prereg: interface-aware).
                    prediction = fit_predict_mlp(
                        x_fit, y_fit, x_query, seed=realization,
                        threads=args.threads)
                    mse = float(np.mean((y_query - prediction) ** 2))
                    results[str(support_k)][arm_name] = {
                        "nmse": mse / query_var,
                        "nrmse": float(np.sqrt(mse / query_var)),
                        "n_features": int(x_fit.shape[1]),
                        "nan_fraction_fit": float(np.mean(np.isnan(x_fit))),
                    }
            payload = {
                "mode": "primary_mlp",
                "family": family,
                "realization": realization,
                "support_ks": list(SUPPORT_KS),
                "backbone": "sklearn_mlp_32_relu_adam",
                "recipe": {
                    "hidden_layer_sizes": list(HIDDEN),
                    "alpha": ALPHA,
                    "learning_rate_init": LEARNING_RATE,
                    "max_iter": MAX_ITER,
                    "imputation": "mean_plus_missing_indicators",
                    "scaling": "standard_x_and_y",
                },
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
