"""Adjudicate MCR-MD (mismatch dose) per its prereg.

U(d) = Q(decode) - Q(raw_d{d}), Q = -nMSE.  MD-P1: realization-level
Spearman of U(d) vs d (mean > 0 and CI95 above 0).  MD-P2: U(8)
separated (mean > 0, CI95 low > 0, win >= 0.60).  Verdicts at K=32 on
xgb and histgb; xgb K=512 confirmatory; rawsent curves descriptive.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "experiments/crta_v3_mcr_mismatch_dose_v1"

FAMILIES = ("additive", "pairwise", "sparse")
DOSES = (0, 2, 4, 6, 8)
VERDICT_CELLS = (("xgb", "32"), ("histgb", "32"))
CONFIRMATORY_CELLS = (("xgb", "512"),)
EXPECTED_REALIZATIONS = 20
BOOTSTRAP_REPS = 10000
BOOTSTRAP_SEED = 20260820
WIN_THRESHOLD = 0.60


def boot(values: np.ndarray, seed_key: str) -> dict:
    seed = int(hashlib.sha256(
        f"mcr_md|{BOOTSTRAP_SEED}|{seed_key}".encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    chosen = rng.integers(0, len(values), size=(BOOTSTRAP_REPS, len(values)))
    means = values[chosen].mean(axis=1)
    lower, upper = float(np.quantile(means, 0.025)), float(
        np.quantile(means, 0.975))
    return {"mean": float(np.mean(values)),
            "ci95": [lower, upper],
            "win": float(np.mean(values > 0)),
            "n": int(len(values))}


def utility_curve(record: dict, backbone: str, k: str, label: str
                  ) -> list[float]:
    arms = record["results"][k][backbone]
    q_decode = -float(arms["decode"]["nmse"])
    return [q_decode - (-float(arms[f"{label}_d{d}"]["nmse"]))
            for d in DOSES]


def analyze_cell(cells: dict[str, list[dict]], backbone: str, k: str) -> dict:
    out: dict[str, dict] = {}
    for family in FAMILIES:
        curves = np.asarray([utility_curve(r, backbone, k, "raw")
                             for r in cells[family]])
        rhos = np.asarray([
            float(spearmanr(DOSES, curve).statistic) for curve in curves])
        p1 = boot(rhos, f"P1|{family}|{backbone}|{k}")
        p1["pass"] = bool(p1["mean"] > 0 and p1["ci95"][0] > 0)
        u8 = curves[:, -1]
        p2 = boot(u8, f"P2|{family}|{backbone}|{k}")
        p2["separated"] = bool(p2["mean"] > 0 and p2["ci95"][0] > 0
                               and p2["win"] >= WIN_THRESHOLD)
        sent_curves = np.asarray([utility_curve(r, backbone, k, "rawsent")
                                  for r in cells[family]])
        out[family] = {
            "MD_P1_spearman": p1,
            "MD_P2_u8": p2,
            "mean_U_by_dose": [float(v) for v in curves.mean(axis=0)],
            "mean_U_sent_by_dose": [float(v)
                                    for v in sent_curves.mean(axis=0)],
        }
    out["all_P1_pass"] = all(out[f]["MD_P1_spearman"]["pass"]
                             for f in FAMILIES)
    out["all_P2_separated"] = all(out[f]["MD_P2_u8"]["separated"]
                                  for f in FAMILIES)
    return out


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

    sections = {}
    for backbone, k in VERDICT_CELLS + CONFIRMATORY_CELLS:
        sections[f"{backbone}_K{k}"] = analyze_cell(cells, backbone, k)

    if complete:
        verdicts = {
            "MD_P1_graded_utility": all(
                sections[f"{b}_K{k}"]["all_P1_pass"]
                for b, k in VERDICT_CELLS),
            "MD_P2_full_mismatch_utility": all(
                sections[f"{b}_K{k}"]["all_P2_separated"]
                for b, k in VERDICT_CELLS),
        }
        verdicts["grid_verdict"] = bool(
            verdicts["MD_P1_graded_utility"]
            and verdicts["MD_P2_full_mismatch_utility"])
    else:
        verdicts = {"status": "incomplete — verdicts withheld"}

    payload = {
        "n_cells": sum(len(v) for v in cells.values()),
        "doses": list(DOSES),
        "bootstrap": {"reps": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED},
        "sections": sections,
        "verdicts": verdicts,
    }
    out_path = args.root / "SUMMARY_V1.json"
    out_path.write_text(json.dumps(payload, indent=1, sort_keys=True))
    print(json.dumps({"written": str(out_path), "verdicts": verdicts},
                     indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
