#!/usr/bin/env python3
"""Summarize the five-level MCR measurement-mismatch support ladder."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "experiments/crta_v3_mcr_mismatch_support_ladder_v1"
SUPPORTS = (32, 64, 128, 256, 512)
BACKBONES = ("xgb", "histgb", "tabpfn")
FAMILIES = ("additive", "pairwise", "sparse")
ARMS = ("intended", "reference", "matched_wrong")
N_REALIZATIONS = 20
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 20260901


def bootstrap(values: np.ndarray, key: str) -> dict:
    seed = int(hashlib.sha256(
        f"mcr_mismatch_support|{BOOTSTRAP_SEED}|{key}".encode()
    ).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(BOOTSTRAP_REPS, len(values)))
    means = values[indices].mean(axis=1)
    return {
        "mean": float(values.mean()),
        "ci95": [float(np.quantile(means, 0.025)),
                 float(np.quantile(means, 0.975))],
        "n": int(len(values)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    sections = {}
    complete = True
    for backbone in BACKBONES:
        sections[backbone] = {}
        for family in FAMILIES:
            records = []
            for path in sorted((args.root / backbone / family).glob("r*/metrics.json")):
                records.append(json.loads(path.read_text()))
            if len(records) != N_REALIZATIONS:
                complete = False
                continue
            if sorted(record["realization"] for record in records) != list(
                    range(N_REALIZATIONS)):
                raise RuntimeError(f"Realization grid mismatch: {backbone}/{family}")
            if not all(all(record["paired_construction_gate"].values())
                       for record in records):
                raise RuntimeError(f"Construction gate failed: {backbone}/{family}")

            arm_stats = {}
            contrast_stats = {"benefit": {}, "content": {}, "damage": {}}
            benefit_matrix = []
            content_matrix = []
            for support in SUPPORTS:
                values = {
                    arm: np.asarray([
                        record["results"][str(support)][arm]["nmse"]
                        for record in records
                    ], dtype=float)
                    for arm in ARMS
                }
                arm_stats[str(support)] = {
                    arm: bootstrap(values[arm], f"arm|{backbone}|{family}|{support}|{arm}")
                    for arm in ARMS
                }
                benefit = values["reference"] - values["intended"]
                content = values["matched_wrong"] - values["intended"]
                damage = values["matched_wrong"] - values["reference"]
                benefit_matrix.append(benefit)
                content_matrix.append(content)
                for name, array in (
                    ("benefit", benefit), ("content", content), ("damage", damage)
                ):
                    contrast_stats[name][str(support)] = bootstrap(
                        array, f"{name}|{backbone}|{family}|{support}"
                    )
            benefit_matrix = np.asarray(benefit_matrix).T
            content_matrix = np.asarray(content_matrix).T
            log_support = np.log2(np.asarray(SUPPORTS, dtype=float))
            benefit_rho = np.asarray([
                spearmanr(log_support, row).statistic for row in benefit_matrix
            ], dtype=float)
            content_rho = np.asarray([
                spearmanr(log_support, row).statistic for row in content_matrix
            ], dtype=float)
            sections[backbone][family] = {
                "absolute_nmse": arm_stats,
                "contrasts": contrast_stats,
                "support_spearman": {
                    "benefit": bootstrap(
                        benefit_rho, f"rho_benefit|{backbone}|{family}"
                    ),
                    "content": bootstrap(
                        content_rho, f"rho_content|{backbone}|{family}"
                    ),
                },
            }

    payload = {
        "design_status": "post_result_descriptive_extension",
        "complete": complete,
        "supports": list(SUPPORTS),
        "backbones": list(BACKBONES),
        "families": list(FAMILIES),
        "arms": list(ARMS),
        "n_realizations_per_stratum": N_REALIZATIONS,
        "bootstrap": {"reps": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED},
        "sections": sections,
    }
    out_path = args.root / "SUMMARY_V1.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"written": str(out_path), "complete": complete}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

