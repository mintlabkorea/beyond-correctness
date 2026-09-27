#!/usr/bin/env python3
"""Adjudicator for S5 (binding backbone generality on HistGB).

Frozen rules: `iclr_latex_v3/BINDING_BACKBONE_GENERALITY_PREREGISTRATION
_V1.md`.  At K = 256: hierarchical bootstrap (targets then seeds, 10,000
reps, seed 20260820); separation = mean > 0 and CI95 excludes 0 and win
>= 0.60 and mean > 0 with the best target dropped.  Metric: AUROC gain
(higher is better).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "experiments/crta_v3_binding_backbone_generality_v1"

PRIMARY_K = "256"
ALL_K = ("64", "256", "1024")
BOOTSTRAP_REPS = 10000
BOOTSTRAP_SEED = 20260820
WIN_THRESHOLD = 0.60
CONTRASTS = {
    "S5_P1_binding_content": ("a11_stage_columns", "pl_columns_at_stage"),
    "S5_P2_columns_on_stage": ("a11_stage_columns", "a10_stage"),
    "desc_deranged_vs_base": ("pl_columns_at_stage", "a10_stage"),
}


def load_cells(root: Path) -> list[dict[str, Any]]:
    return [json.loads(p.read_text())
            for p in sorted(root.glob("*/seed_*/metrics.json"))]


def contrast_by_target(cells: list[dict[str, Any]], pair: tuple[str, str],
                       k: str) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for cell in cells:
        arms = cell["auroc"][k]
        out.setdefault(cell["target"], []).append(
            float(arms[pair[0]]) - float(arms[pair[1]]))
    return out


def hierarchical(by_target: dict[str, list[float]], seed_key: str
                 ) -> dict[str, Any]:
    targets = sorted(by_target)
    arrays = {t: np.asarray(by_target[t], dtype=float) for t in targets}
    flat = np.concatenate([arrays[t] for t in targets])
    seed = int(hashlib.sha256(
        f"s5|{BOOTSTRAP_SEED}|{seed_key}".encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    means = np.empty(BOOTSTRAP_REPS)
    for rep in range(BOOTSTRAP_REPS):
        chosen = rng.integers(0, len(targets), size=len(targets))
        parts = [arrays[targets[int(i)]][
            rng.integers(0, len(arrays[targets[int(i)]]),
                         size=len(arrays[targets[int(i)]]))]
            for i in chosen]
        means[rep] = float(np.mean(np.concatenate(parts)))
    target_means = {t: float(np.mean(arrays[t])) for t in targets}
    best = max(target_means, key=target_means.get)
    drop_best = float(np.mean(np.concatenate(
        [arrays[t] for t in targets if t != best]))) if len(targets) > 1 \
        else float(np.mean(flat))
    mean = float(np.mean(flat))
    lower, upper = (float(np.quantile(means, 0.025)),
                    float(np.quantile(means, 0.975)))
    win = float(np.mean(flat > 0))
    return {
        "mean": mean, "ci95": [lower, upper], "win": win, "n": int(len(flat)),
        "target_means": target_means, "drop_best_mean": drop_best,
        "separated": bool(mean > 0 and lower > 0 and win >= WIN_THRESHOLD
                          and drop_best > 0),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()

    cells = load_cells(args.root)
    counts: dict[str, int] = {}
    for cell in cells:
        counts[cell["target"]] = counts.get(cell["target"], 0) + 1
    complete = sorted(counts.values()) == [10, 10, 10]

    sections: dict[str, Any] = {}
    for k in ALL_K:
        sections[f"K{k}"] = {
            name: hierarchical(contrast_by_target(cells, pair, k),
                               f"{k}|{name}")
            for name, pair in CONTRASTS.items()
        }
    if complete:
        primary = sections[f"K{PRIMARY_K}"]
        verdicts = {
            "S5_P1": primary["S5_P1_binding_content"]["separated"],
            "S5_P2": primary["S5_P2_columns_on_stage"]["separated"],
        }
    else:
        verdicts = {"status": "incomplete — verdicts withheld",
                    "cells_per_target": counts}
    payload = {
        "n_cells": len(cells),
        "cells_per_target": counts,
        "primary_k": int(PRIMARY_K),
        "bootstrap": {"reps": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED},
        "verdicts": verdicts,
        "sections": sections,
    }
    out_path = args.root / "SUMMARY_V1.json"
    out_path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({"verdicts": verdicts, "n_cells": len(cells),
                      "written": str(out_path)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
