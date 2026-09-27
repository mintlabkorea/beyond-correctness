"""Adjudicate MCR-VR per its prereg (Q = -nMSE, per-family realization
bootstrap; grid = both families x both backbones at K=32).

V1 magnitude when non-redundant: Q(drop_op_true) - Q(drop_free)   [separated]
V4 sign-equivariance (value form): Q(drop_op_true) - Q(drop_op_true_negated) [null]
V2 direction on top (constraints): Q(drop_op_true_signed) - Q(drop_op_true) [separated]
V3 constraint content: Q(drop_op_true_signed) - Q(drop_op_flip_signed) [separated]
descriptive flipped constraint over free:
    Q(drop_op_flip_signed) - Q(drop_free)
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "experiments/crta_v3_mcr_value_redundancy_v1"
FAMILIES = ("pairwise", "sparse")
BACKBONES = ("xgb", "histgb")
SUPPORT_KS = ("32", "512")
PRIMARY_K = "32"
EXPECTED_REALIZATIONS = 20
BOOTSTRAP_REPS = 10000
BOOTSTRAP_SEED = 20260820
WIN_THRESHOLD = 0.60
NULL_MARGIN = 0.05
FROZEN_INPUT_SHA256 = "6af2215c72a65ecc306e5c4d3d9af5b61b16a073dd5aa4c0f33b178741245a25"

CONTRASTS = {
    "V1_magnitude_nonredundant": ("drop_op_true", "drop_free", "separated"),
    "V4_value_sign_equivariance": ("drop_op_true", "drop_op_true_negated", "null"),
    "V2_direction_on_top": ("drop_op_true_signed", "drop_op_true", "separated"),
    "V3_constraint_content": ("drop_op_true_signed", "drop_op_flip_signed", "separated"),
    "desc_flipped_over_free": ("drop_op_flip_signed", "drop_free", "descriptive"),
    "desc_full_ops_over_free": ("full_op_true", "full_free", "descriptive"),
    "desc_information_removed": ("full_free", "drop_free", "descriptive"),
    "desc_random_ops_over_drop_free": ("drop_op_random", "drop_free", "descriptive"),
}
VERDICT_CONTRASTS = ("V1_magnitude_nonredundant", "V4_value_sign_equivariance",
                     "V2_direction_on_top", "V3_constraint_content")


def boot(values: np.ndarray, key: str) -> dict:
    seed = int(hashlib.sha256(
        f"mcr_vr|{BOOTSTRAP_SEED}|{key}".encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    chosen = rng.integers(0, len(values), size=(BOOTSTRAP_REPS, len(values)))
    means = values[chosen].mean(axis=1)
    lower, upper = float(np.quantile(means, 0.025)), float(
        np.quantile(means, 0.975))
    mean = float(np.mean(values))
    win = float(np.mean(values > 0))
    return {"mean": mean, "ci95": [lower, upper], "win": win,
            "n": int(len(values)),
            "separated": bool(mean > 0 and lower > 0 and win >= WIN_THRESHOLD),
            "null": bool(lower <= 0 <= upper and abs(mean) < NULL_MARGIN)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()

    cells = {f: [] for f in FAMILIES}
    provenance = set()
    for family in FAMILIES:
        for path in sorted((args.root / family).glob("r*/metrics.json")):
            record = json.loads(path.read_text())
            cells[family].append(record)
            provenance.add((record["runner_sha256"], record["mcr_runner_sha256"],
                            record["input_sha256"], record["prereg_sha256"]))
    if len(provenance) > 1:
        raise RuntimeError("mixed provenance across cells")
    if provenance and next(iter(provenance))[2] != FROZEN_INPUT_SHA256:
        raise RuntimeError("cells were not fit on the frozen MCR panel")
    complete = all(sorted(r["realization"] for r in cells[f]) ==
                   list(range(EXPECTED_REALIZATIONS)) for f in FAMILIES)

    sections: dict = {}
    for k in SUPPORT_KS:
        sections[k] = {}
        for name, (a, b, kind) in CONTRASTS.items():
            sections[k][name] = {"kind": kind}
            for backbone in BACKBONES:
                for family in FAMILIES:
                    values = np.asarray([
                        -r["results"][k][backbone][a]["nmse"]
                        + r["results"][k][backbone][b]["nmse"]
                        for r in cells[family]])
                    sections[k][name][f"{backbone}|{family}"] = boot(
                        values, f"{name}|{family}|{backbone}|{k}")
            criterion = "null" if kind == "null" else "separated"
            sections[k][name]["grid_pass"] = all(
                sections[k][name][f"{bb}|{ff}"][criterion]
                for bb in BACKBONES for ff in FAMILIES) if kind != "descriptive" else None

    if complete:
        verdicts = {name: bool(sections[PRIMARY_K][name]["grid_pass"])
                    for name in VERDICT_CONTRASTS}
        verdicts["redundancy_plus_equivariance"] = bool(
            verdicts["V1_magnitude_nonredundant"]
            and verdicts["V4_value_sign_equivariance"])
    else:
        verdicts = {"status": "incomplete — verdicts withheld"}

    versions = sorted({json.dumps(r.get("versions", {}), sort_keys=True)
                       for f in FAMILIES for r in cells[f]})
    hosts = sorted({r.get("host", "?") for f in FAMILIES for r in cells[f]})
    payload = {
        "n_cells": sum(len(v) for v in cells.values()),
        "primary_support_k": PRIMARY_K,
        "bootstrap": {"reps": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED},
        "versions": versions, "hosts": hosts,
        "sections": sections,
        "verdicts": verdicts,
        "arm_mean_nmse": {
            k: {bb: {ff: {arm: float(np.mean([r["results"][k][bb][arm]["nmse"]
                                               for r in cells[ff]]))
                          for arm in cells[ff][0]["arms"]}
                     for ff in FAMILIES if cells[ff]}
                for bb in BACKBONES}
            for k in SUPPORT_KS},
    }
    out_path = args.root / "SUMMARY_V1.json"
    out_path.write_text(json.dumps(payload, indent=1, sort_keys=True))
    print(json.dumps({"written": str(out_path), "verdicts": verdicts}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
