#!/usr/bin/env python3
"""Adjudicate the decoy compiler-specificity experiment (stages A and B).

Stage A (from STAGE_A_MATCHER_V1.json): DA-P1 rich-regime FBR at the
registered operating point <= 2/9 under at least one rule; DA-P2
name-only FBR >= 5/9 under both rules or no operating point.
Stage B: D(k) = AUROC(a11 frozen correct) - AUROC(a11 with k decoy
bindings); endpoints are units (seed means); DB-P1 Spearman(D,k) with
D(0)=0, mean rho > 0 and CI low > 0; DB-P2 D(9) separated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/crta_v3_decoy_compiler_specificity_v1"
FROZEN = ROOT / "experiments/crta_v3_stage_endpoint_expansion_nh2kn_v1"
SEEDS = tuple(range(50, 60))
DOSES = (1, 3, 5, 9)
K = "256"
REPS = 10000
SEED = 20260820
WIN = 0.60


def boot(values: np.ndarray, key: str) -> dict:
    seed = int(hashlib.sha256(f"decoy_b|{SEED}|{key}".encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    chosen = rng.integers(0, len(values), size=(REPS, len(values)))
    means = values[chosen].mean(axis=1)
    return {"mean": float(np.mean(values)),
            "ci95": [float(np.quantile(means, .025)), float(np.quantile(means, .975))],
            "win": float(np.mean(values > 0)), "n": int(len(values))}


def stage_a_verdicts(a: dict) -> dict:
    rich = a["sweeps"]["name_unit_codebook"]
    name = a["sweeps"]["name_only"]

    def fbr(op):
        return None if op is None else op["false_bindings"]

    rich_fbrs = [fbr(rich["operating_threshold"]), fbr(rich["operating_margin"])]
    p1 = any(v is not None and v <= 2 for v in rich_fbrs)
    name_fbrs = [fbr(name["operating_threshold"]), fbr(name["operating_margin"])]
    p2 = all(v is None or v >= 5 for v in name_fbrs)
    return {"DA_P1_rich_specificity": {"fbr_threshold": rich_fbrs[0],
                                       "fbr_margin": rich_fbrs[1], "pass": bool(p1)},
            "DA_P2_names_cannot_abstain": {"fbr_threshold": name_fbrs[0],
                                           "fbr_margin": name_fbrs[1],
                                           "gold_accuracy": name["gold_present_accuracy"],
                                           "pass": bool(p2)},
            "forced_false_bindings": rich["forced_false_bindings"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=EXP)
    args = parser.parse_args()
    stage_a = json.loads((args.root / "STAGE_A_MATCHER_V1.json").read_text())
    payload: dict = {"stage_a": stage_a_verdicts(stage_a)}

    endpoints = sorted(p.name for p in FROZEN.iterdir() if p.is_dir())
    expected = len(endpoints) * len(SEEDS) * len(DOSES)
    found = sum(1 for k in DOSES for e in endpoints for s in SEEDS
                if (args.root / "stage_b" / f"k{k}" / e / f"seed_{s}" / "metrics.json").is_file())
    payload["stage_b_cells"] = {"found": found, "expected": expected}
    if found == expected:
        # Codex-identified guard (2026-08-25): every dose's binding audit must
        # equal the bindings recomputed from stage A + the frozen member order.
        import importlib.util, sys
        spec = importlib.util.spec_from_file_location(
            "decoy_b_for_summary", ROOT / "scripts/run_crta_v3_decoy_stage_b_v1.py")
        sb = importlib.util.module_from_spec(spec); sys.modules["decoy_b_for_summary"] = sb
        spec.loader.exec_module(sb)
        eng = sb.load("decoy_b_engine_probe_summary", sb.ENGINE)
        order = sb.member_order(tuple(eng.MEMBER_SLOTS))
        forced = stage_a["sweeps"][sb.REGIME]["forced_false_bindings"]
        stage_a_sha = hashlib.sha256((args.root / "STAGE_A_MATCHER_V1.json").read_bytes()).hexdigest()
        for k in DOSES:
            audit = json.loads((args.root / "stage_b" / f"k{k}" / "BINDING_AUDIT_V1.json").read_text())
            expected_b = {m: forced[m] for m in order[:k]}
            if audit["bindings"] != expected_b or audit["member_order"] != order:
                raise RuntimeError(f"binding audit mismatch at k{k}")
            if audit["stage_a_sha256"] != stage_a_sha:
                raise RuntimeError(f"stage-A hash mismatch at k{k}")
        payload["binding_audits_verified"] = True
        curves, derangement = {}, {}
        for e in endpoints:
            frozen = [json.loads((FROZEN / e / f"seed_{s}" / "metrics.json").read_text())["auroc"][K]
                      for s in SEEDS]
            correct = np.asarray([f["a11_stage_columns"] for f in frozen])
            derangement[e] = float(np.mean(correct - np.asarray([f["pl_columns_at_stage"] for f in frozen])))
            curve = [0.0]
            for k in DOSES:
                decoy = np.asarray([json.loads((args.root / "stage_b" / f"k{k}" / e / f"seed_{s}" /
                                                "metrics.json").read_text())["auroc"][K]["a11_stage_columns"]
                                    for s in SEEDS])
                if not np.all(np.isfinite(decoy)):
                    raise RuntimeError(f"non-finite AUROC at k{k}/{e}")
                curve.append(float(np.mean(correct - decoy)))
            curves[e] = curve
        xs = (0,) + DOSES
        rhos = np.asarray([spearmanr(xs, c).statistic for c in curves.values()])
        p1 = boot(rhos, "P1"); p1["pass"] = bool(p1["mean"] > 0 and p1["ci95"][0] > 0)
        d9 = np.asarray([c[-1] for c in curves.values()])
        p2 = boot(d9, "P2"); p2["pass"] = bool(p2["mean"] > 0 and p2["ci95"][0] > 0 and p2["win"] >= WIN)
        der = boot(np.asarray(list(derangement.values())), "derangement")
        payload["stage_b"] = {
            "DB_P1_graded_damage": p1, "DB_P2_full_dose_damage": p2,
            "mean_D_by_dose": {str(k): float(np.mean([c[i] for c in curves.values()]))
                               for i, k in enumerate(xs)},
            "per_endpoint_curves": curves,
            "derangement_damage_reference": der,
        }
        payload["verdicts"] = {
            "DA_P1": payload["stage_a"]["DA_P1_rich_specificity"]["pass"],
            "DA_P2": payload["stage_a"]["DA_P2_names_cannot_abstain"]["pass"],
            "DB_P1": p1["pass"], "DB_P2": p2["pass"],
        }
        payload["verdicts"]["all"] = all(payload["verdicts"].values())
    else:
        payload["verdicts"] = {"status": "stage B incomplete — verdicts withheld",
                               "DA_P1": payload["stage_a"]["DA_P1_rich_specificity"]["pass"],
                               "DA_P2": payload["stage_a"]["DA_P2_names_cannot_abstain"]["pass"]}
    (args.root / "SUMMARY_V1.json").write_text(json.dumps(payload, indent=1, sort_keys=True))
    print(json.dumps({"verdicts": payload["verdicts"],
                      "stage_b_cells": payload["stage_b_cells"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
