#!/usr/bin/env python3
"""Adjudicate MCR-MD-T (mismatch dose on TabPFN) per its prereg.

U(d) = Q(decode) - Q(raw_d{d}), Q = -nMSE, K=32, single backbone.
MDT-P1: realization-level Spearman of U(d) vs d (mean > 0, CI95 above 0)
per family.  MDT-P2: U(8) separated (mean > 0, CI95 low > 0, win >= 0.60)
per family.  Verdict = both in all three families.  rawsent curves and
the paired comparison against the frozen tree MD curves are descriptive.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "experiments/crta_v3_mcr_mismatch_dose_tabpfn_v1"
MD_ROOT = ROOT / "experiments/crta_v3_mcr_mismatch_dose_v1"

FAMILIES = ("additive", "pairwise", "sparse")
DOSES = (0, 2, 4, 6, 8)
K = "32"
BACKBONE = "tabpfn"
EXPECTED_REALIZATIONS = 20
BOOTSTRAP_REPS = 10000
BOOTSTRAP_SEED = 20260820
WIN_THRESHOLD = 0.60


def boot(values: np.ndarray, seed_key: str) -> dict:
    seed = int(hashlib.sha256(
        f"mcr_md_t|{BOOTSTRAP_SEED}|{seed_key}".encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    chosen = rng.integers(0, len(values), size=(BOOTSTRAP_REPS, len(values)))
    means = values[chosen].mean(axis=1)
    return {"mean": float(np.mean(values)),
            "ci95": [float(np.quantile(means, 0.025)),
                     float(np.quantile(means, 0.975))],
            "win": float(np.mean(values > 0)),
            "n": int(len(values))}


def utility_curve(record: dict, backbone: str, k: str, label: str
                  ) -> list[float]:
    arms = record["results"][k][backbone]
    q_decode = -float(arms["decode"]["nmse"])
    return [q_decode - (-float(arms[f"{label}_d{d}"]["nmse"]))
            for d in DOSES]


def load_cells(root: Path) -> dict[str, dict[int, dict]]:
    cells: dict[str, dict[int, dict]] = {f: {} for f in FAMILIES}
    for family in FAMILIES:
        for path in sorted((root / family).glob("r*/metrics.json")):
            record = json.loads(path.read_text())
            cells[family][int(record["realization"])] = record
    return cells


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()

    cells = load_cells(args.root)
    tree_cells = load_cells(MD_ROOT)
    provenance = {(r["runner_sha256"], r["mcr_runner_sha256"],
                   r["md_runner_sha256"], r["input_sha256"],
                   r["prereg_sha256"])
                  for fam in cells.values() for r in fam.values()}
    if len(provenance) > 1:
        raise RuntimeError("mixed provenance across cells")
    for fam in cells.values():
        for r in fam.values():
            gate = r["paired_construction_gate"]
            if not (gate["dose_order"] and gate["mismatch_entry_counts"]):
                raise RuntimeError("paired construction gate failed")
    complete = all(sorted(cells[f]) == list(range(EXPECTED_REALIZATIONS))
                   for f in FAMILIES)

    sections = {}
    p1_all, p2_all = [], []
    for family in FAMILIES:
        realizations = sorted(cells[family])
        curves = np.asarray([utility_curve(cells[family][r], BACKBONE, K, "raw")
                             for r in realizations])
        rhos = np.asarray([float(spearmanr(DOSES, c).statistic) for c in curves])
        p1 = boot(rhos, f"P1|{family}")
        p1["pass"] = bool(p1["mean"] > 0 and p1["ci95"][0] > 0)
        p2 = boot(curves[:, -1], f"P2|{family}")
        p2["separated"] = bool(p2["mean"] > 0 and p2["ci95"][0] > 0
                               and p2["win"] >= WIN_THRESHOLD)
        sent = np.asarray([utility_curve(cells[family][r], BACKBONE, K, "rawsent")
                           for r in realizations])
        paired = {}
        for tree_backbone in ("xgb", "histgb"):
            tree_curves = np.asarray([
                utility_curve(tree_cells[family][r], tree_backbone, K, "raw")
                for r in realizations if r in tree_cells[family]])
            if len(tree_curves) == len(curves):
                diff = curves[:, -1] - tree_curves[:, -1]
                paired[tree_backbone] = {
                    "tree_mean_U_by_dose": [float(v) for v in tree_curves.mean(axis=0)],
                    "U8_tabpfn_minus_tree": boot(diff, f"paired|{family}|{tree_backbone}"),
                }
        sections[family] = {
            "MDT_P1_spearman": p1,
            "MDT_P2_u8": p2,
            "mean_U_by_dose": [float(v) for v in curves.mean(axis=0)],
            "mean_U_sent_by_dose": [float(v) for v in sent.mean(axis=0)],
            "paired_vs_tree": paired,
        }
        p1_all.append(p1["pass"]); p2_all.append(p2["separated"])

    verdicts = ({"MDT_P1_graded_utility": bool(all(p1_all)),
                 "MDT_P2_full_mismatch_utility": bool(all(p2_all)),
                 "verdict": bool(all(p1_all) and all(p2_all))}
                if complete else {"status": "incomplete — verdicts withheld"})
    payload = {
        "n_cells": sum(len(v) for v in cells.values()),
        "backbone": "tabpfn_7_regressor",
        "support_k": int(K),
        "doses": list(DOSES),
        "bootstrap": {"reps": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED},
        "sections": sections,
        "verdicts": verdicts,
    }
    out_path = args.root / "SUMMARY_V1.json"
    out_path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"written": str(out_path), "verdicts": verdicts}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
