"""Adjudicate the v2 (SOURCE-ONLY M axis) real-data source-informativeness ladder.

Same estimands and rules as v1, but alpha=0 is read from this tree (refit under
the source-only semantics) and every alpha, including 0, is audit-verified.
Also reports v1 (frozen-M-axis) curves side by side, descriptively.

Verifies every permutation audit by recomputing the frozen construction,
then evaluates:
  RS-P1: endpoint-cluster bootstrap of per-unit Spearman(I*(α), α):
         mean < 0 and CI95 entirely below 0.
  RS-P2: endpoint-cluster D = I*(0) - I*(1): mean > 0, CI low > 0,
         win >= 0.60.
Descriptives: pooled corrected curve, per-direction curves, raw variant,
drop-diabetes sensitivity.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "experiments/crta_v3_stage_source_ladder_v2_source_only_v1"
V1_ROOT = ROOT / "experiments/crta_v3_stage_source_informativeness_ladder_v1"
FROZEN_ROOTS = {
    "nh2kn": ROOT / "experiments/crta_v3_stage_endpoint_expansion_nh2kn_v1",
    "kn2nh": ROOT / "experiments/crta_v3_stage_endpoint_expansion_kn2nh_v1",
}
DIRECTIONS = ("nh2kn", "kn2nh")
ALPHAS_NEW = (0.00, 0.25, 0.50, 0.75, 1.00)
ALPHAS_FULL = (0.0, 0.25, 0.50, 0.75, 1.00)
SEEDS = tuple(range(50, 60))
K = "256"
ARMS = ("a00_base", "a01_columns", "a10_stage", "a11_stage_columns")
BOOTSTRAP_REPS = 10000
BOOTSTRAP_SEED = 20260820
WIN_THRESHOLD = 0.60


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


rsl = _load("stage_source_ladder_for_summary_v2",
            ROOT / "scripts/run_crta_v3_stage_source_informativeness_ladder_v1.py")
ladder = _load("mcr_ladder_for_summary", rsl.MCR_LADDER)


def interaction(arms: dict, corrected: bool) -> float:
    f = (lambda x: max(float(x), 1.0 - float(x))) if corrected else float
    return ((f(arms["a11_stage_columns"]) - f(arms["a10_stage"]))
            - (f(arms["a01_columns"]) - f(arms["a00_base"])))


def boot(values: np.ndarray, key: str) -> dict:
    seed = int(hashlib.sha256(
        f"stage_ladder_v2|{BOOTSTRAP_SEED}|{key}".encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    chosen = rng.integers(0, len(values), size=(BOOTSTRAP_REPS, len(values)))
    means = values[chosen].mean(axis=1)
    return {"mean": float(np.mean(values)),
            "ci95": [float(np.quantile(means, 0.025)),
                     float(np.quantile(means, 0.975))],
            "win_positive": float(np.mean(values > 0)),
            "n": int(len(values))}


def verify_audits(root: Path, endpoints: list[str]) -> dict:
    """Recompute every permutation from the frozen seeds; verify audited
    cells byte-for-byte, flag cells with no audit entry (fit before a shard
    was killed; see exp_log 2026-08-25), and assert moved-set nesting across
    alpha (Codex-identified additions, 2026-08-25)."""
    missing: list[str] = []
    for direction in DIRECTIONS:
        audits = {alpha: json.loads((root / direction / f"alpha_{alpha:.2f}" /
                                     "PERMUTATION_AUDIT_V1.json").read_text())
                  for alpha in ALPHAS_NEW}
        for endpoint in endpoints:
            for seed in SEEDS:
                prev_moved: set[int] = set()
                for alpha in ALPHAS_NEW:
                    adir = root / direction / f"alpha_{alpha:.2f}"
                    cell = json.loads((adir / endpoint / f"seed_{seed}" /
                                       "metrics.json").read_text())
                    n = int(cell["n_source"])
                    provider = rsl.PermProvider(ladder, direction, alpha)
                    perm = provider.get(endpoint, seed, n)
                    sha = hashlib.sha256(perm.astype("<i8").tobytes()).hexdigest()
                    moved = set(np.where(perm != np.arange(n))[0].tolist())
                    if not prev_moved.issubset(moved):
                        raise RuntimeError(
                            f"moved sets not nested {direction} {endpoint} s{seed} at {alpha}")
                    prev_moved = moved
                    entry = audits[alpha]["cells"].get(f"{endpoint}|seed_{seed}")
                    if entry is None:
                        missing.append(f"{direction}|{alpha:.2f}|{endpoint}|{seed}")
                        continue
                    if entry["n_source"] != n or sha != entry["permutation_sha256"]:
                        raise RuntimeError(
                            f"audit mismatch {direction} {alpha} {endpoint} s{seed}")
    return {"nestedness_verified": True, "cells_without_audit_entry": missing,
            "n_without_audit_entry": len(missing)}


def unit_curves(root: Path, endpoints: list[str], corrected: bool
                ) -> dict[tuple[str, str], list[float]]:
    curves: dict[tuple[str, str], list[float]] = {}
    for direction in DIRECTIONS:
        for endpoint in endpoints:
            curve = []
            for alpha in ALPHAS_FULL:
                values = []
                for seed in SEEDS:
                    path = (root / direction / f"alpha_{alpha:.2f}" /
                            endpoint / f"seed_{seed}" / "metrics.json")
                    record = json.loads(path.read_text())
                    if record.get("m_axis") != "source_only_fork_v1":
                        raise RuntimeError(f"cell without source-only tag: {path}")
                    arms = record["auroc"][K]
                    value = interaction(arms, corrected)
                    if not np.isfinite(value):
                        raise RuntimeError(f"non-finite I* at {path}")
                    values.append(value)
                if len(values) != len(SEEDS):
                    raise RuntimeError("missing seeds")
                curve.append(float(np.mean(values)))
            curves[(direction, endpoint)] = curve
    return curves


def cluster_means(per_unit: dict[tuple[str, str], float],
                  endpoints: list[str]) -> np.ndarray:
    return np.asarray([
        np.mean([per_unit[(d, e)] for d in DIRECTIONS]) for e in endpoints])


def adjudicate(curves: dict[tuple[str, str], list[float]],
               endpoints: list[str], tag: str) -> dict:
    rho_unit = {unit: float(spearmanr(ALPHAS_FULL, curve).statistic)
                for unit, curve in curves.items()}
    decline_unit = {unit: curve[0] - curve[-1]
                    for unit, curve in curves.items()}
    rho_clusters = cluster_means(rho_unit, endpoints)
    dec_clusters = cluster_means(decline_unit, endpoints)
    p1 = boot(rho_clusters, f"P1|{tag}")
    p1["pass"] = bool(p1["mean"] < 0 and p1["ci95"][1] < 0)
    p2 = boot(dec_clusters, f"P2|{tag}")
    p2["pass"] = bool(p2["mean"] > 0 and p2["ci95"][0] > 0
                      and p2["win_positive"] >= WIN_THRESHOLD)
    pooled = {}
    for i, alpha in enumerate(ALPHAS_FULL):
        clusters = cluster_means({u: c[i] for u, c in curves.items()},
                                 endpoints)
        pooled[f"{alpha:.2f}"] = boot(clusters, f"pooled|{tag}|{alpha:.2f}")
    return {
        "RS_P1_spearman": p1,
        "RS_P2_decline": p2,
        "pooled_I_by_alpha": pooled,
        "per_unit_rho": {f"{d}|{e}": rho_unit[(d, e)]
                         for d, e in sorted(rho_unit)},
        "per_direction_mean_curve": {
            d: [float(np.mean([curves[(d, e)][i] for e in endpoints]))
                for i in range(len(ALPHAS_FULL))]
            for d in DIRECTIONS},
        "endpoint_cluster_rho": {e: float(r)
                                 for e, r in zip(endpoints, rho_clusters)},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()

    registry = _load("stage_registry_for_summary",
                     ROOT / "scripts/crta_v3_stage_endpoint_registry_v1.py")
    endpoints = sorted(registry.ENDPOINTS)

    expected = (len(DIRECTIONS) * len(endpoints) * len(SEEDS)
                * len(ALPHAS_NEW))
    found = sum(
        1 for d in DIRECTIONS for a in ALPHAS_NEW for e in endpoints
        for s in SEEDS
        if (args.root / d / f"alpha_{a:.2f}" / e / f"seed_{s}" /
            "metrics.json").is_file())
    complete = found == expected

    payload: dict = {
        "expected_cells": expected,
        "found_cells": found,
        "alphas": list(ALPHAS_FULL),
        "bootstrap": {"reps": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED,
                      "unit": "endpoint cluster (two directions averaged)"},
    }
    if complete:
        payload["permutation_audit_check"] = verify_audits(args.root, endpoints)
        payload["permutation_audits_verified"] = True
        refit = args.root / "REFIT_VERIFICATION_V1.json"
        if refit.is_file():
            payload["refit_verification"] = json.loads(refit.read_text())
        corrected = unit_curves(args.root, endpoints, corrected=True)
        raw = unit_curves(args.root, endpoints, corrected=False)
        payload["corrected"] = adjudicate(corrected, endpoints, "corrected")
        payload["raw_descriptive"] = adjudicate(raw, endpoints, "raw")
        no_diab = [e for e in endpoints if e != "diabetes_history"]
        payload["drop_diabetes_sensitivity"] = adjudicate(
            {u: c for u, c in corrected.items() if u[1] != "diabetes_history"},
            no_diab, "corrected_no_diabetes")
        v1_summary = V1_ROOT / "SUMMARY_V1.json"
        if v1_summary.is_file():
            v1 = json.loads(v1_summary.read_text())["corrected"]
            payload["v1_frozen_m_axis_reference"] = {
                "pooled_I_by_alpha": {a: v1["pooled_I_by_alpha"][a]["mean"]
                                      for a in v1["pooled_I_by_alpha"]},
                "RS_P1_rho_mean": v1["RS_P1_spearman"]["mean"],
                "RS_P2_decline_mean": v1["RS_P2_decline"]["mean"]}
        payload["verdicts"] = {
            "RS_P1": payload["corrected"]["RS_P1_spearman"]["pass"],
            "RS_P2": payload["corrected"]["RS_P2_decline"]["pass"],
        }
        payload["verdicts"]["ladder_verdict"] = bool(
            payload["verdicts"]["RS_P1"] and payload["verdicts"]["RS_P2"])
    else:
        payload["verdicts"] = {"status": "incomplete — verdicts withheld"}

    out_path = args.root / "SUMMARY_V1.json"
    out_path.write_text(json.dumps(payload, indent=1, sort_keys=True))
    print(json.dumps({"written": str(out_path),
                      "verdicts": payload["verdicts"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
