#!/usr/bin/env python3
"""Paired raw-versus-folded M x C interaction reanalysis."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOTS = {
    "nh2kn": REPO / "experiments/crta_v3_stage_endpoint_expansion_nh2kn_v1",
    "kn2nh": REPO / "experiments/crta_v3_stage_endpoint_expansion_kn2nh_v1",
}
PARENT = REPO / "experiments/crta_v3_stage_endpoint_expansion_SUMMARY_V1.json"
REPS = 10_000
SEED = 20260820


def interaction(a: dict, folded: bool) -> float:
    f = (lambda x: max(float(x), 1.0 - float(x))) if folded else float
    return ((f(a["a11_stage_columns"]) - f(a["a10_stage"]))
            - (f(a["a01_columns"]) - f(a["a00_base"])))


def load() -> dict[tuple[str, str], np.ndarray]:
    out = {}
    for direction, root in ROOTS.items():
        for path in sorted(root.glob("*/seed_*/metrics.json")):
            d = json.loads(path.read_text())
            vals = (interaction(d["auroc"]["256"], False),
                    interaction(d["auroc"]["256"], True))
            out.setdefault((direction, d["target"]), []).append(vals)
    arrays = {k: np.asarray(v, float) for k, v in out.items()}
    if len(arrays) != 20 or any(x.shape != (10, 2) for x in arrays.values()):
        raise RuntimeError("expected 20 endpoint-direction units x 10 seeds")
    return arrays


def stable_rng(scope: str) -> np.random.Generator:
    key = f"raw_folded_joint|{SEED}|{scope}"
    return np.random.default_rng(int(hashlib.sha256(key.encode()).hexdigest()[:8], 16))


def summarize(units: dict, scope: str) -> list[dict]:
    names = sorted(units)
    observed = np.concatenate([units[u] for u in names])
    rng = stable_rng(scope)
    draws = np.empty((REPS, 3))
    for b in range(REPS):
        selected = rng.integers(0, len(names), size=len(names))
        parts = []
        for i in selected:
            x = units[names[int(i)]]
            parts.append(x[rng.integers(0, len(x), size=len(x))])
        z = np.concatenate(parts)
        draws[b, :2] = z.mean(axis=0)
        draws[b, 2] = draws[b, 0] - draws[b, 1]
    point = np.r_[observed.mean(axis=0), observed[:, 0].mean() - observed[:, 1].mean()]
    labels = ("raw_interaction", "folded_interaction", "raw_minus_folded")
    return [{
        "scope": scope, "estimand": labels[j], "estimate": float(point[j]),
        "ci95_low": float(np.quantile(draws[:, j], .025)),
        "ci95_high": float(np.quantile(draws[:, j], .975)),
        "n_endpoint_direction_units": len(names), "n_seed_cells": len(observed),
    } for j in range(3)]


def main() -> int:
    units = load()
    rows = []
    rows += summarize(units, "pooled")
    for direction in ROOTS:
        rows += summarize({k: v for k, v in units.items() if k[0] == direction}, direction)
    parent = json.loads(PARENT.read_text())["results"]
    assertions = {
        "pooled_raw": (rows[0]["estimate"], parent["pooled_raw"]["mean"]),
        "pooled_folded": (rows[1]["estimate"], parent["pooled_corrected"]["mean"]),
        "nh2kn_raw": (rows[3]["estimate"], parent["forward_raw"]["mean"]),
        "nh2kn_folded": (rows[4]["estimate"], parent["forward_corrected"]["mean"]),
        "kn2nh_raw": (rows[6]["estimate"], parent["reverse_raw"]["mean"]),
        "kn2nh_folded": (rows[7]["estimate"], parent["reverse_corrected"]["mean"]),
    }
    max_error = max(abs(a - b) for a, b in assertions.values())
    if max_error > 1e-12:
        raise AssertionError(f"parent point mismatch: {max_error}")
    with (HERE / "raw_vs_folded_interaction.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
    per_unit = []
    for (direction, endpoint), values in sorted(units.items()):
        per_unit.append({
            "direction": direction, "endpoint": endpoint,
            "raw_mean": float(values[:, 0].mean()),
            "folded_mean": float(values[:, 1].mean()),
            "raw_minus_folded": float((values[:, 0] - values[:, 1]).mean()),
            "n_seeds": len(values),
        })
    with (HERE / "per_endpoint_direction.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, list(per_unit[0])); w.writeheader(); w.writerows(per_unit)
    payload = {
        "status": "complete", "results": rows,
        "bootstrap": {"reps": REPS, "base_seed": SEED,
                      "unit": "endpoint-direction, then seeds within unit",
                      "pairing": "raw, folded, and their difference use identical resamples"},
        "interpretive_boundary": (
            "This estimates interaction level. It does not overturn the previously failed "
            "raw attenuation-ladder criterion, which is a different estimand."
        ),
        "max_parent_point_error": max_error,
        "sources": [str(x.relative_to(REPO)) for x in ROOTS.values()] +
                   [str(PARENT.relative_to(REPO)),
                    "scripts/summarize_crta_v3_stage_factorial_endpoint_expansion_v1.py"],
    }
    (HERE / "summary.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"written": [str(HERE / "raw_vs_folded_interaction.csv"),
                                  str(HERE / "summary.json")],
                      "pooled": rows[:3]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
