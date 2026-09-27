#!/usr/bin/env python3
"""Summarize the post-result HistGB/TabPFN K=512 mismatch-dose extension."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "experiments/crta_v3_mcr_mismatch_dose_k512_extension_v1"
MD_ROOT = ROOT / "experiments/crta_v3_mcr_mismatch_dose_v1"
MDT_ROOT = ROOT / "experiments/crta_v3_mcr_mismatch_dose_tabpfn_v1"

FAMILIES = ("additive", "pairwise", "sparse")
BACKBONES = ("histgb", "tabpfn")
DOSES = (0, 2, 4, 6, 8)
K = "512"
EXPECTED_REALIZATIONS = 20
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 20260825
WIN_THRESHOLD = 0.60


def boot(values: np.ndarray, key: str) -> dict:
    seed = int(hashlib.sha256(
        f"mcr_md_k512_ext|{BOOTSTRAP_SEED}|{key}".encode()
    ).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    chosen = rng.integers(0, len(values),
                          size=(BOOTSTRAP_REPS, len(values)))
    means = values[chosen].mean(axis=1)
    return {
        "mean": float(np.mean(values)),
        "ci95": [float(np.quantile(means, 0.025)),
                 float(np.quantile(means, 0.975))],
        "win": float(np.mean(values > 0)),
        "n": int(len(values)),
    }


def utility_curve(record: dict, backbone: str, k: str,
                  label: str = "raw") -> np.ndarray:
    arms = record["results"][k][backbone]
    q_decode = -float(arms["decode"]["nmse"])
    return np.asarray([
        q_decode - (-float(arms[f"{label}_d{dose}"]["nmse"]))
        for dose in DOSES
    ])


def load_cells(root: Path, nested_backbone: str | None = None
               ) -> dict[str, dict[int, dict]]:
    base = root / nested_backbone if nested_backbone else root
    cells = {family: {} for family in FAMILIES}
    for family in FAMILIES:
        for path in sorted((base / family).glob("r*/metrics.json")):
            record = json.loads(path.read_text())
            cells[family][int(record["realization"])] = record
    return cells


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()

    extension = {b: load_cells(args.root, b) for b in BACKBONES}
    tree = load_cells(MD_ROOT)
    tabpfn_k32 = load_cells(MDT_ROOT)
    sections = {}
    complete = True
    for backbone in BACKBONES:
        for family in FAMILIES:
            if sorted(extension[backbone][family]) != list(
                    range(EXPECTED_REALIZATIONS)):
                complete = False

    for backbone in BACKBONES:
        section = {}
        for family in FAMILIES:
            realizations = sorted(extension[backbone][family])
            if not realizations:
                continue
            records = [extension[backbone][family][r] for r in realizations]
            for record in records:
                gate = record["paired_construction_gate"]
                if not all(gate.values()):
                    raise RuntimeError("paired construction gate failed")
            curves = np.asarray([
                utility_curve(record, backbone, K) for record in records
            ])
            sent_curves = np.asarray([
                utility_curve(record, backbone, K, "rawsent")
                for record in records
            ])
            rhos = np.asarray([
                float(spearmanr(DOSES, curve).statistic)
                for curve in curves
            ])
            p1 = boot(rhos, f"rho|{backbone}|{family}")
            p1["descriptive_pass"] = bool(
                p1["mean"] > 0 and p1["ci95"][0] > 0)
            p2 = boot(curves[:, -1], f"u8|{backbone}|{family}")
            p2["descriptive_pass"] = bool(
                p2["mean"] > 0 and p2["ci95"][0] > 0 and
                p2["win"] >= WIN_THRESHOLD)

            if backbone == "histgb":
                k32_curves = np.asarray([
                    utility_curve(tree[family][r], "histgb", "32")
                    for r in realizations
                ])
            else:
                k32_curves = np.asarray([
                    utility_curve(tabpfn_k32[family][r], "tabpfn", "32")
                    for r in realizations
                ])
            xgb_k512 = np.asarray([
                utility_curve(tree[family][r], "xgb", "512")
                for r in realizations
            ])
            section[family] = {
                "rho_dose_utility": p1,
                "u8": p2,
                "mean_U_by_dose": [float(v) for v in curves.mean(axis=0)],
                "mean_U_sent_by_dose": [float(v)
                                        for v in sent_curves.mean(axis=0)],
                "paired_U8_K512_minus_K32": boot(
                    curves[:, -1] - k32_curves[:, -1],
                    f"budget|{backbone}|{family}"),
                "paired_U8_minus_XGB_K512": boot(
                    curves[:, -1] - xgb_k512[:, -1],
                    f"xgb|{backbone}|{family}"),
            }
        sections[f"{backbone}_K512"] = section

    criteria = {}
    if complete:
        for backbone in BACKBONES:
            rows = sections[f"{backbone}_K512"].values()
            criteria[backbone] = {
                "graded_utility_all_families": all(
                    row["rho_dose_utility"]["descriptive_pass"]
                    for row in rows),
                "full_dose_utility_all_families": all(
                    row["u8"]["descriptive_pass"] for row in rows),
            }
    payload = {
        "design_status": "post_result_descriptive_extension",
        "n_cells": sum(len(family) for backbone in extension.values()
                       for family in backbone.values()),
        "support_k": int(K),
        "doses": list(DOSES),
        "bootstrap": {"reps": BOOTSTRAP_REPS,
                      "seed": BOOTSTRAP_SEED},
        "complete": complete,
        "sections": sections,
        "descriptive_consistency_criteria": criteria,
    }
    out_path = args.root / "SUMMARY_V1.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"written": str(out_path), "complete": complete,
                      "criteria": criteria}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
