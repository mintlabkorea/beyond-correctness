"""MCR-VR: redundancy vs sign-equivariance behind the dead value channel.

Drops the true pairs' constituent base columns so an operation column is
the only carrier of its information, then reads magnitude (values),
sign in value form (negation), and sign in constraint form (monotone
constraints) separately.  Pairwise and sparse families only.
Prereg: iclr_latex_v3/MCR_VALUE_REDUNDANCY_PREREGISTRATION_V1.md.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MCR_RUNNER = ROOT / "scripts/run_crta_v3_mcr_factorial_semisynth_v1.py"
PREREG = ROOT / "iclr_latex_v3/MCR_VALUE_REDUNDANCY_PREREGISTRATION_V1.md"
DEFAULT_OUT = ROOT / "experiments/crta_v3_mcr_value_redundancy_v1"

FAMILIES = ("pairwise", "sparse")
SUPPORT_KS = (32, 512)
BACKBONES = ("xgb", "histgb")
N_BASE = 8
FROZEN_INPUT_SHA256 = "6af2215c72a65ecc306e5c4d3d9af5b61b16a073dd5aa4c0f33b178741245a25"  # Codex-identified guard (2026-08-25)


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


def frames_equal(a: np.ndarray, b: np.ndarray) -> bool:
    return bool(np.array_equal(a, b, equal_nan=True))


def constituents_of(cell) -> list[int]:
    rel = cell.relations["true"]
    feats: set[int] = set()
    for a, b, _op, _s in rel.pair_terms:
        feats.add(int(a))
        feats.add(int(b))
    return sorted(feats)


def build_arms(mcr, cell, support_k: int) -> tuple[dict, np.ndarray, np.ndarray, dict]:
    """Return arms {name: (x_fit, x_query, constraints)}, y_fit, weights, info."""
    x_free, y_fit, weights, q_free, c_free = mcr.arm_matrices(
        cell, "m1c1rf", support_k, weighted=False)
    x_op, y_op, _, q_op, c_zero = mcr.arm_matrices(
        cell, "r_op_only", support_k, weighted=False)
    x_sig, _, _, q_sig, c_true = mcr.arm_matrices(
        cell, "m1c1r1", support_k, weighted=False)
    x_flp, _, _, q_flp, c_flip = mcr.arm_matrices(
        cell, "r_flipped", support_k, weighted=False)
    x_rnd, _, _, q_rnd, _c_rnd = mcr.arm_matrices(
        cell, "m1c1r0", support_k, weighted=False)
    if not np.all(weights == 1.0):
        raise AssertionError("pooling must be unweighted")
    if not (frames_equal(x_op, x_sig) and frames_equal(x_op, x_flp)
            and frames_equal(q_op, q_sig) and frames_equal(q_op, q_flp)):
        raise AssertionError("r_op_only / m1c1r1 / r_flipped matrices differ")
    if not (frames_equal(x_op[:, :N_BASE], x_free)
            and frames_equal(q_op[:, :N_BASE], q_free)):
        raise AssertionError("base block of the op matrix != free matrix")
    if not np.array_equal(y_fit, y_op):
        raise AssertionError("y_fit differs across arms")
    if any(c_free) or any(c_zero):
        raise AssertionError("free / op_only arms must carry no signs")
    if tuple(c_flip) != tuple(-s for s in c_true):
        raise AssertionError("flipped signs must be the exact negation")
    n_op = x_op.shape[1] - N_BASE
    if n_op <= 0 or x_rnd.shape[1] != x_op.shape[1]:
        raise AssertionError("operation column count mismatch")
    if any(c_true[j] != 0 for j in range(N_BASE)) or any(
            c_true[j] == 0 for j in range(N_BASE, N_BASE + n_op)):
        raise AssertionError("signs must sit exactly on the op columns")

    constituents = constituents_of(cell)
    keep_base = [j for j in range(N_BASE) if j not in set(constituents)]
    if not keep_base:
        raise AssertionError("no base column survives constituent removal")
    op_cols = list(range(N_BASE, N_BASE + n_op))
    cols = keep_base + op_cols
    zeros_keep = tuple([0] * len(keep_base))
    signs_true = tuple(c_true[j] for j in op_cols)
    signs_flip = tuple(-s for s in signs_true)

    def negate_ops(matrix: np.ndarray) -> np.ndarray:
        out = matrix.copy()
        out[:, len(keep_base):] *= -1.0
        return out

    arms = {
        "full_free": (x_free, q_free, tuple([0] * N_BASE)),
        "full_op_true": (x_op, q_op, tuple([0] * x_op.shape[1])),
        "drop_free": (x_free[:, keep_base], q_free[:, keep_base], zeros_keep),
        "drop_op_true": (x_op[:, cols], q_op[:, cols],
                         zeros_keep + tuple([0] * n_op)),
        "drop_op_true_negated": (negate_ops(x_op[:, cols]),
                                 negate_ops(q_op[:, cols]),
                                 zeros_keep + tuple([0] * n_op)),
        "drop_op_true_signed": (x_op[:, cols], q_op[:, cols],
                                zeros_keep + signs_true),
        "drop_op_flip_signed": (x_op[:, cols], q_op[:, cols],
                                zeros_keep + signs_flip),
        "drop_op_random": (x_rnd[:, cols], q_rnd[:, cols],
                           zeros_keep + tuple([0] * n_op)),
    }
    info = {"constituents": constituents, "keep_base": keep_base,
            "n_op": n_op, "signs_true": [int(s) for s in signs_true]}
    return arms, y_fit, weights, info


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=None)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--families", nargs="*", default=list(FAMILIES))
    parser.add_argument("--realizations", nargs="*", type=int, default=None)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()

    mcr = _load("mcr_core", MCR_RUNNER)
    input_path = args.input or mcr.DEFAULT_INPUT
    realizations = (args.realizations if args.realizations is not None
                    else list(range(mcr.N_REALIZATIONS)))
    import sklearn
    import xgboost
    input_sha = sha256_file(input_path)
    if input_sha != FROZEN_INPUT_SHA256:
        raise SystemExit("input panel is not the frozen MCR panel")
    provenance = {
        "input_sha256": input_sha,
        "runner_sha256": sha256_file(Path(__file__)),
        "mcr_runner_sha256": sha256_file(MCR_RUNNER),
        "prereg_sha256": sha256_file(PREREG),
        "rng_namespace": mcr.RNG_NS,
        "versions": {"xgboost": xgboost.__version__,
                     "sklearn": sklearn.__version__,
                     "numpy": np.__version__,
                     "python": platform.python_version()},
        "host": platform.node(),
    }
    panel = mcr.load_panel(input_path)
    print(json.dumps(provenance), flush=True)

    for family in args.families:
        if family not in FAMILIES:
            raise SystemExit(f"{family}: only pairwise/sparse have op columns")
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
            results: dict = {}
            info_out: dict = {}
            for support_k in SUPPORT_KS:
                arms, y_fit, weights, info = build_arms(mcr, cell, support_k)
                info_out = info
                results[str(support_k)] = {}
                for backbone in BACKBONES:
                    results[str(support_k)][backbone] = {}
                    for name, (x_fit, x_query, constraints) in arms.items():
                        prediction = mcr.fit_predict(
                            backbone, x_fit, y_fit, weights, x_query,
                            tuple(int(c) for c in constraints),
                            seed=realization, threads=args.threads)
                        mse = float(np.mean((y_query - prediction) ** 2))
                        results[str(support_k)][backbone][name] = {
                            "nmse": mse / query_var,
                            "nrmse": float(np.sqrt(mse / query_var)),
                            "n_features": int(x_fit.shape[1]),
                        }
            payload = {
                "mode": "value_redundancy",
                "family": family,
                "realization": realization,
                "arms": list(arms),
                "supports": [str(k) for k in SUPPORT_KS],
                "backbones": list(BACKBONES),
                **info_out,
                "results": results,
                "wall_seconds": round(time.time() - started, 2),
                **provenance,
            }
            out_dir.mkdir(parents=True, exist_ok=True)
            metrics_path.write_text(json.dumps(payload, indent=1,
                                               sort_keys=True))
            print(f"{family} r{realization:02d} done "
                  f"({payload['wall_seconds']}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
