"""Adjudicate MCR-NM (certified partially-monotone MLP) per its prereg.

Contrasts (Q = -nMSE, per-family realization bootstrap):
  NM1_constraint_utility  = Q(mono_true) - Q(free)
  NM2_direction_content   = Q(mono_true) - Q(mono_flip)
  flip_over_free (descr.) = Q(mono_flip) - Q(free)
Verdicts at K=32 gated on the free-arm evaluability rule (mean nMSE < 1).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "experiments/crta_v3_mcr_monotone_mlp_v1"

FAMILIES = ("additive", "pairwise", "sparse")
SUPPORT_KS = ("32", "512")
PRIMARY_K = "32"
EXPECTED_REALIZATIONS = 20
BOOTSTRAP_REPS = 10000
BOOTSTRAP_SEED = 20260820
WIN_THRESHOLD = 0.60

CONTRASTS = {
    "NM1_constraint_utility": ("mono_true", "free"),
    "NM2_direction_content": ("mono_true", "mono_flip"),
    "flip_over_free": ("mono_flip", "free"),
    "NM1b_constraint_utility_vs_unfolded": ("mono_true", "free_unfolded"),
    "fold_effect_free_minus_unfolded": ("free", "free_unfolded"),
}
VERDICT_CONTRASTS = ("NM1_constraint_utility", "NM2_direction_content")


def q(arms: dict, name: str) -> float:
    return -float(arms[name]["nmse"])


def bootstrap_stats(values: np.ndarray, seed_key: str) -> dict:
    seed = int(hashlib.sha256(
        f"mcr_nm|{BOOTSTRAP_SEED}|{seed_key}".encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    chosen = rng.integers(0, len(values), size=(BOOTSTRAP_REPS, len(values)))
    means = values[chosen].mean(axis=1)
    lower, upper = float(np.quantile(means, 0.025)), float(
        np.quantile(means, 0.975))
    mean = float(np.mean(values))
    win = float(np.mean(values > 0))
    return {
        "mean": mean,
        "ci95": [lower, upper],
        "win": win,
        "n": int(len(values)),
        "separated": bool(mean > 0 and lower > 0 and win >= WIN_THRESHOLD),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()

    cells: dict[str, list[dict]] = {family: [] for family in FAMILIES}
    provenance = set()
    for family in FAMILIES:
        for path in sorted((args.root / family).glob("r*/metrics.json")):
            record = json.loads(path.read_text())
            cells[family].append(record)
            provenance.add((record["runner_sha256"],
                            record["mcr_runner_sha256"],
                            record["input_sha256"],
                            record["prereg_sha256"]))
    if len(provenance) > 1:
        raise RuntimeError("mixed provenance across cells")

    complete = all(
        sorted(r["realization"] for r in cells[f]) ==
        list(range(EXPECTED_REALIZATIONS)) for f in FAMILIES)

    sections: dict[str, dict] = {}
    gates: dict[str, dict] = {}
    for k in SUPPORT_KS:
        sections[k] = {}
        gates[k] = {}
        for family in FAMILIES:
            free_nmse = [r["results"][k]["free"]["nmse"]
                         for r in cells[family]]
            mean_free = float(np.mean(free_nmse)) if free_nmse else float("nan")
            gates[k][family] = {"mean_free_nmse": mean_free,
                                "beats_intercept": bool(mean_free < 1.0)}
        for name, (a, b) in CONTRASTS.items():
            if any(b not in r["results"][k] or a not in r["results"][k]
                   for f in FAMILIES for r in cells[f]):
                continue  # arm absent in this tree (original run lacks free_unfolded)
            sections[k][name] = {}
            for family in FAMILIES:
                values = np.asarray([
                    q(r["results"][k], a) - q(r["results"][k], b)
                    for r in cells[family]])
                stats = bootstrap_stats(values, f"{name}|{family}|{k}")
                stats["evaluable"] = gates[k][family]["beats_intercept"]
                sections[k][name][family] = stats
            sections[k][name]["all_families_separated"] = all(
                sections[k][name][f]["separated"] for f in FAMILIES)
            sections[k][name]["all_families_evaluable"] = all(
                sections[k][name][f]["evaluable"] for f in FAMILIES)

    if complete:
        verdicts = {}
        for name in VERDICT_CONTRASTS:
            block = sections[PRIMARY_K][name]
            if not block["all_families_evaluable"]:
                verdicts[name] = "non-evaluable"
            else:
                verdicts[name] = bool(block["all_families_separated"])
    else:
        verdicts = {"status": "incomplete — verdicts withheld"}

    payload = {
        "n_cells": sum(len(v) for v in cells.values()),
        "primary_support_k": PRIMARY_K,
        "bootstrap": {"reps": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED},
        "evaluability_gate": gates,
        "sections": sections,
        "verdicts": verdicts,
        "arm_mean_nmse": {
            k: {family: {arm: float(np.mean([
                r["results"][k][arm]["nmse"] for r in cells[family]]))
                for arm in cells[family][0]["arms"]}
                for family in FAMILIES if cells[family]}
            for k in SUPPORT_KS},
    }
    out_path = args.root / "SUMMARY_V1.json"
    out_path.write_text(json.dumps(payload, indent=1, sort_keys=True))
    print(json.dumps({"written": str(out_path),
                      "verdicts": verdicts}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
