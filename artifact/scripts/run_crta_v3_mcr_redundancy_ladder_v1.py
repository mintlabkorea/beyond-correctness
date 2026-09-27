"""MCR-RL: the redundancy ladder between MCR-VR's two endpoints.

Removes a nested, frozen-random prefix of the true pairs' constituent base
columns and reads operation-column utility at every rung, so that VR's
`full` (utility null) and `drop` (utility +0.24) become the k=0 and
k=|C| ends of one curve.  Pairwise and sparse families only.
Protocol: experiments/crta_v3_mcr_redundancy_ladder_v1/PROTOCOL_V1.md.
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
VR_RUNNER = ROOT / "scripts/run_crta_v3_mcr_value_redundancy_v1.py"
DEFAULT_OUT = ROOT / "experiments/crta_v3_mcr_redundancy_ladder_v1"
PROTOCOL = DEFAULT_OUT / "PROTOCOL_V1.md"

FAMILIES = ("pairwise", "sparse")
SUPPORT_KS = (32, 512)
BACKBONES = ("xgb", "histgb")
N_BASE = 8
LADDER_RNG_NS = "mcr_rl"
FROZEN_INPUT_SHA256 = "6af2215c72a65ecc306e5c4d3d9af5b61b16a073dd5aa4c0f33b178741245a25"


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


def ladder_permutation(family: str, realization: int,
                       constituents: list[int]) -> list[int]:
    """Frozen nested removal order; rung k removes the first k entries."""
    key = f"{LADDER_RNG_NS}|{family}|{realization}".encode()
    seed = int.from_bytes(hashlib.sha256(key).digest()[:8], "big")
    rng = np.random.default_rng(seed)
    order = list(np.asarray(constituents)[rng.permutation(len(constituents))])
    return [int(j) for j in order]


def build_rungs(vr, mcr, cell, family: str, realization: int, support_k: int
                ) -> tuple[list[dict], np.ndarray, np.ndarray, dict]:
    """Return per-rung arm specs reusing VR's frozen matrix construction."""
    x_free, y_fit, weights, q_free, c_free = mcr.arm_matrices(
        cell, "m1c1rf", support_k, weighted=False)
    x_op, y_op, _, q_op, c_zero = mcr.arm_matrices(
        cell, "r_op_only", support_k, weighted=False)
    x_sig, _, _, q_sig, c_true = mcr.arm_matrices(
        cell, "m1c1r1", support_k, weighted=False)
    if not np.all(weights == 1.0):
        raise AssertionError("pooling must be unweighted")
    if not (vr.frames_equal(x_op, x_sig) and vr.frames_equal(q_op, q_sig)):
        raise AssertionError("r_op_only / m1c1r1 matrices differ")
    if not (vr.frames_equal(x_op[:, :N_BASE], x_free)
            and vr.frames_equal(q_op[:, :N_BASE], q_free)):
        raise AssertionError("base block of the op matrix != free matrix")
    if not np.array_equal(y_fit, y_op):
        raise AssertionError("y_fit differs across arms")
    if any(c_free) or any(c_zero):
        raise AssertionError("free / op_only arms must carry no signs")
    n_op = x_op.shape[1] - N_BASE
    if n_op <= 0:
        raise AssertionError("no operation column")
    if any(c_true[j] != 0 for j in range(N_BASE)) or any(
            c_true[j] == 0 for j in range(N_BASE, N_BASE + n_op)):
        raise AssertionError("signs must sit exactly on the op columns")

    constituents = vr.constituents_of(cell)
    order = ladder_permutation(family, realization, constituents)
    pair_terms = [(int(a), int(b)) for a, b, _op, _s in
                  cell.relations["true"].pair_terms]
    op_cols = list(range(N_BASE, N_BASE + n_op))
    signs_true = tuple(c_true[j] for j in op_cols)

    rungs: list[dict] = []
    for k in range(len(constituents) + 1):
        removed = set(order[:k])
        keep_base = [j for j in range(N_BASE) if j not in removed]
        if not keep_base:
            raise AssertionError("no base column survives at this rung")
        cols = keep_base + op_cols
        zeros_keep = tuple([0] * len(keep_base))
        rungs.append({
            "k": k,
            "rho": k / len(constituents),
            "removed": sorted(removed),
            "n_pairs_broken": sum(
                1 for a, b in pair_terms if a in removed or b in removed),
            "keep_base": keep_base,
            "arms": {
                "free": (x_free[:, keep_base], q_free[:, keep_base],
                         zeros_keep),
                "op_true": (x_op[:, cols], q_op[:, cols],
                            zeros_keep + tuple([0] * n_op)),
                "sig_true": (x_op[:, cols], q_op[:, cols],
                             zeros_keep + signs_true),
            },
        })

    # Declared endpoint identity: k=0 is VR's `full_*`, k=|C| its `drop_*`.
    if rungs[0]["keep_base"] != list(range(N_BASE)):
        raise AssertionError("rung 0 is not the full frame")
    vr_keep = [j for j in range(N_BASE) if j not in set(constituents)]
    if rungs[-1]["keep_base"] != vr_keep:
        raise AssertionError("top rung does not reproduce VR's keep_base")

    info = {"constituents": constituents, "removal_order": order,
            "n_op": n_op, "signs_true": [int(s) for s in signs_true],
            "pair_terms": pair_terms,
            "vr_keep_base": vr_keep, "n_rungs": len(rungs)}
    return rungs, y_fit, weights, info


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=None)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--families", nargs="*", default=list(FAMILIES))
    parser.add_argument("--realizations", nargs="*", type=int, default=None)
    parser.add_argument("--threads", type=int, default=1)
    args = parser.parse_args()

    mcr = _load("mcr_core", MCR_RUNNER)
    vr = _load("mcr_vr", VR_RUNNER)
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
        "vr_runner_sha256": sha256_file(VR_RUNNER),
        "protocol_sha256": sha256_file(PROTOCOL),
        "rng_namespace": mcr.RNG_NS,
        "ladder_rng_namespace": LADDER_RNG_NS,
        "threads": args.threads,
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
                if any(existing.get(key) != provenance[key] for key in
                       ("runner_sha256", "mcr_runner_sha256",
                        "vr_runner_sha256", "input_sha256",
                        "protocol_sha256", "threads")):
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
                rungs, y_fit, weights, info = build_rungs(
                    vr, mcr, cell, family, realization, support_k)
                info_out = info
                results[str(support_k)] = {}
                for backbone in BACKBONES:
                    per_rung: dict = {}
                    for rung in rungs:
                        cell_out: dict = {}
                        for name, (x_fit, x_query, constraints) in \
                                rung["arms"].items():
                            prediction = mcr.fit_predict(
                                backbone, x_fit, y_fit, weights, x_query,
                                tuple(int(c) for c in constraints),
                                seed=realization, threads=args.threads)
                            mse = float(np.mean((y_query - prediction) ** 2))
                            cell_out[name] = {
                                "nmse": mse / query_var,
                                "n_features": int(x_fit.shape[1]),
                            }
                        per_rung[str(rung["k"])] = {
                            "rho": rung["rho"],
                            "removed": rung["removed"],
                            "n_pairs_broken": rung["n_pairs_broken"],
                            "arms": cell_out,
                        }
                    results[str(support_k)][backbone] = per_rung
            payload = {
                "mode": "redundancy_ladder",
                "family": family,
                "realization": realization,
                "arms": ["free", "op_true", "sig_true"],
                "supports": [str(k) for k in SUPPORT_KS],
                "backbones": list(BACKBONES),
                "query_var": query_var,
                **info_out,
                "results": results,
                "wall_seconds": round(time.time() - started, 2),
                **provenance,
            }
            out_dir.mkdir(parents=True, exist_ok=True)
            metrics_path.write_text(json.dumps(payload, indent=1,
                                               sort_keys=True))
            print(f"{family} r{realization:02d} done "
                  f"({payload['wall_seconds']}s, {info_out['n_rungs']} rungs)",
                  flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
