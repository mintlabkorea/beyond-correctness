"""MCR-NM: constraint channel on a certified partially-monotone MLP.

Fits the frozen MCR factorial's `m1c1r1` matrices (all three families)
with a two-block torch MLP under three arms: `free` (channel off),
`mono_true` (softplus-certified signs), `mono_flip` (negated signs).
Prereg: iclr_latex_v3/MCR_MONOTONE_MLP_PREREGISTRATION_V1.md.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("NVIDIA_VISIBLE_DEVICES", "none")

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
MCR_RUNNER = ROOT / "scripts/run_crta_v3_mcr_factorial_semisynth_v1.py"
PREREG = ROOT / "iclr_latex_v3/MCR_MONOTONE_MLP_PREREGISTRATION_V1.md"
DEFAULT_OUT = ROOT / "experiments/crta_v3_mcr_monotone_mlp_v1"

SUPPORT_KS = (32, 512)
GRID_ARM = "m1c1r1"
ARMS = ("free", "mono_true", "mono_flip", "free_unfolded")
# free_unfolded: Codex-identified addendum (2026-08-25) — `free` still
# receives the true sign fold on its inputs; this arm uses an all-ones
# fold so the channel-off baseline carries no directional knowledge.
HIDDEN = 16
LEARNING_RATE = 3e-3
WEIGHT_DECAY = 1e-2
EPOCHS = 300
MONO_INIT_MEAN = -2.0
MONO_INIT_STD = 0.5
CERT_POINTS = 64
CERT_DELTA = 1e-3
CERT_TOL = -1e-8
# expected sign topology per family: (matrix width, n nonzero, on op cols only)
SIGN_TOPOLOGY = {"additive": (8, 5, False),
                 "pairwise": (11, 3, True),
                 "sparse": (10, 2, True)}


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


class TwoBlockNet(torch.nn.Module):
    """Identical wiring in every arm; `mono_mode` only reparameterizes
    the constrained paths (P, v) through softplus."""

    def __init__(self, n_u: int, n_c: int, hidden: int, mono_mode: str):
        super().__init__()
        if mono_mode not in ("off", "on"):
            raise ValueError(mono_mode)
        self.mono_mode = mono_mode
        self.free = torch.nn.Linear(n_u, hidden)
        self.free_out = torch.nn.Linear(hidden, 1)
        self.mono_u = torch.nn.Linear(n_u, hidden)
        self.mono_c = torch.nn.Linear(n_c, hidden, bias=False)
        self.mono_out = torch.nn.Linear(hidden, 1, bias=False)
        self.bias = torch.nn.Parameter(torch.zeros(1))
        if mono_mode == "on":
            # softplus(default init) ~ 0.69 makes the mono block dominate
            # at initialization and it fails to train; softplus(-4) ~ 0.02
            # starves the channel through the ~0.02 sigmoid gradient.
            # softplus(-2) ~ 0.13 matches the default |weight| scale.
            with torch.no_grad():
                self.mono_c.weight.normal_(MONO_INIT_MEAN, MONO_INIT_STD)
                self.mono_out.weight.normal_(MONO_INIT_MEAN, MONO_INIT_STD)

    def _pos(self, weight: torch.Tensor) -> torch.Tensor:
        if self.mono_mode == "on":
            return torch.nn.functional.softplus(weight)
        return weight

    def forward(self, x_u: torch.Tensor, x_c: torch.Tensor) -> torch.Tensor:
        out_f = self.free_out(torch.relu(self.free(x_u)))
        pre_m = self.mono_u(x_u) + torch.nn.functional.linear(
            x_c, self._pos(self.mono_c.weight))
        out_m = torch.nn.functional.linear(
            torch.relu(pre_m), self._pos(self.mono_out.weight))
        return (out_f + out_m + self.bias).squeeze(-1)


def preprocess(x_fit: np.ndarray, x_query: np.ndarray, y_fit: np.ndarray):
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler

    imputer = SimpleImputer(strategy="mean").fit(x_fit)
    fit_frame = np.hstack([imputer.transform(x_fit),
                           np.isnan(x_fit).astype(np.float64)])
    query_frame = np.hstack([imputer.transform(x_query),
                             np.isnan(x_query).astype(np.float64)])
    scaler = StandardScaler().fit(fit_frame)
    fit_frame = scaler.transform(fit_frame)
    query_frame = scaler.transform(query_frame)
    y_mean, y_std = float(np.mean(y_fit)), float(np.std(y_fit))
    if y_std <= 0:
        raise RuntimeError("degenerate fit-label variance")
    return fit_frame, query_frame, (y_fit - y_mean) / y_std, y_mean, y_std


def split_columns(frame: np.ndarray, cons_idx: list[int], signs: np.ndarray):
    """Fold signs into constrained columns; everything else (incl. all
    indicator columns) is unconstrained."""
    cons = set(cons_idx)
    u_idx = [j for j in range(frame.shape[1]) if j not in cons]
    x_u = frame[:, u_idx]
    x_c = frame[:, cons_idx] * signs[None, :]
    return x_u, x_c


def certify(model: TwoBlockNet, q_u: torch.Tensor, q_c: torch.Tensor) -> float:
    """Min directional finite difference over CERT_POINTS query points and
    all folded constrained inputs.  Certified architecture => >= ~0."""
    with torch.no_grad():
        base = model(q_u[:CERT_POINTS], q_c[:CERT_POINTS])
        worst = float("inf")
        for j in range(q_c.shape[1]):
            bumped = q_c[:CERT_POINTS].clone()
            bumped[:, j] += CERT_DELTA
            diff = model(q_u[:CERT_POINTS], bumped) - base
            worst = min(worst, float(diff.min()))
    return worst


def fit_predict_arm(x_fit: np.ndarray, y_fit: np.ndarray, x_query: np.ndarray,
                    cons_idx: list[int], base_signs: np.ndarray, arm: str,
                    seed: int, threads: int) -> tuple[np.ndarray, float | None]:
    fit_frame, query_frame, y_norm, y_mean, y_std = preprocess(
        x_fit, x_query, y_fit)
    if arm == "mono_flip":
        signs = -base_signs
    elif arm == "free_unfolded":
        signs = np.ones_like(base_signs)
    else:
        signs = base_signs
    mono_mode = "off" if arm in ("free", "free_unfolded") else "on"
    xf_u, xf_c = split_columns(fit_frame, cons_idx, signs)
    xq_u, xq_c = split_columns(query_frame, cons_idx, signs)
    torch.set_num_threads(max(threads, 1))
    torch.manual_seed(seed)
    to_t = lambda a: torch.tensor(a, dtype=torch.float64)  # noqa: E731
    t_u, t_c, t_y = to_t(xf_u), to_t(xf_c), to_t(y_norm)
    q_u, q_c = to_t(xq_u), to_t(xq_c)
    model = TwoBlockNet(xf_u.shape[1], xf_c.shape[1], HIDDEN,
                        mono_mode).double()
    opt = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE,
                            weight_decay=WEIGHT_DECAY)
    for _ in range(EPOCHS):
        opt.zero_grad()
        loss = torch.mean((model(t_u, t_c) - t_y) ** 2)
        loss.backward()
        opt.step()
    cert_min = None
    if mono_mode == "on":
        cert_min = certify(model, q_u, q_c)
        if cert_min < CERT_TOL:
            raise AssertionError(
                f"monotone certification violated: {cert_min}")
    with torch.no_grad():
        pred = model(q_u, q_c).numpy()
    return np.asarray(pred, dtype=np.float64) * y_std + y_mean, cert_min


def check_topology(family: str, x_fit: np.ndarray,
                   constraints: tuple[int, ...]) -> tuple[list[int], np.ndarray]:
    width, n_nonzero, op_only = SIGN_TOPOLOGY[family]
    if x_fit.shape[1] != width:
        raise AssertionError(
            f"{family}: matrix width {x_fit.shape[1]} != {width}")
    cons_idx = [j for j, s in enumerate(constraints) if s != 0]
    if len(cons_idx) != n_nonzero:
        raise AssertionError(
            f"{family}: {len(cons_idx)} nonzero signs, expected {n_nonzero}")
    if op_only and any(j < 8 for j in cons_idx):
        raise AssertionError(f"{family}: sign on a base column")
    signs = np.asarray([constraints[j] for j in cons_idx], dtype=np.float64)
    return cons_idx, signs


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
                x_fit, y_fit, weights, x_query, constraints = \
                    mcr.arm_matrices(cell, GRID_ARM, support_k,
                                     weighted=False)
                if not np.all(weights == 1.0):
                    raise AssertionError("MCR-NM pooling must be unweighted.")
                cons_idx, signs = check_topology(family, x_fit, constraints)
                results[str(support_k)] = {}
                for arm in ARMS:
                    prediction, cert_min = fit_predict_arm(
                        x_fit, y_fit, x_query, cons_idx, signs, arm,
                        seed=realization, threads=args.threads)
                    mse = float(np.mean((y_query - prediction) ** 2))
                    record = {
                        "nmse": mse / query_var,
                        "nrmse": float(np.sqrt(mse / query_var)),
                        "n_features": int(x_fit.shape[1]),
                        "nan_fraction_fit": float(np.mean(np.isnan(x_fit))),
                    }
                    if cert_min is not None:
                        record["mono_cert_min"] = cert_min
                    results[str(support_k)][arm] = record
            payload = {
                "mode": "primary_monotone_mlp",
                "family": family,
                "realization": realization,
                "grid_arm": GRID_ARM,
                "arms": ARMS,
                "supports": [str(k) for k in SUPPORT_KS],
                "constrained_columns": cons_idx,
                "signs": [int(s) for s in signs],
                "recipe": {"hidden": HIDDEN, "lr": LEARNING_RATE,
                           "weight_decay": WEIGHT_DECAY, "epochs": EPOCHS},
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
