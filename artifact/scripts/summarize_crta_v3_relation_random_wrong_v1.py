#!/usr/bin/env python3
"""Frozen adjudication for W5-R (matched exchangeable-random wrong control).

Implements `iclr_latex_v3/RELATION_MATCHED_RANDOM_WRONG_PREREGISTRATION_V1.md`
section 3.  Reuses the frozen PAM summarizer's hierarchical bootstrap (targets
then seeds, 10,000 reps, seed 20260819) and separation rule at K = 256.  nRMSE
lower is better; every contrast is `nrmse(second) - nrmse(first)`, positive
favouring the first-named arm.  Seed sets v1 and rep1 are adjudicated
separately; the pooled estimate is descriptive.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PRIMARY_K = "256"
N_DRAWS = 5
SEED_SETS = ("v1", "rep1")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pam_summary = _load("crta_pam_v1_summary_frozen",
                    ROOT / "scripts/summarize_crta_v3_pam_constraint_relations_v1.py")
analyze = pam_summary.analyze
paired_gains = pam_summary.paired_gains


def random_arm_names(n_draws: int = N_DRAWS) -> list[str]:
    return [f"sign_random_{d}" for d in range(1, n_draws + 1)]


def load_cells(root: Path) -> tuple[dict[str, dict[int, dict]], list[dict]]:
    cells: dict[str, dict[int, dict]] = {}
    gates: list[dict] = []
    for path in sorted(root.glob("*/seed_*/metrics.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        values = dict(record["nrmse"][PRIMARY_K])
        names = random_arm_names(int(record.get("n_draws", N_DRAWS)))
        values["sign_random_mean"] = float(np.mean([values[n] for n in names]))
        values["sign_random_sd"] = float(np.std([values[n] for n in names], ddof=0))
        cells.setdefault(record["target"], {})[int(record["seed"])] = values
        gates.append({"target": record["target"], "seed": int(record["seed"]),
                      **record["replication_gate"]})
    return cells, gates


def summarize_seed_set(cells, gates, with_verdicts: bool) -> dict:
    n_cells = sum(len(v) for v in cells.values())
    gate_ok = bool(gates) and all(g["passed"] for g in gates)
    verdict = with_verdicts and gate_ok
    out = {
        "n_cells": n_cells,
        "targets_present": sorted(cells),
        "replication_gate_all_pass": gate_ok,
        "replication_gate_worst_abs_delta_nrmse": float(max(
            (g["worst_abs_delta_nrmse"] for g in gates), default=float("nan"))),
        "RW1_random_content": analyze(
            paired_gains(cells, "sign_documented", "sign_random_mean"), with_verdict=verdict),
        "RW2_reversal_content_gate": analyze(
            paired_gains(cells, "sign_documented", "pl_sign_flip"), with_verdict=verdict),
        "RW3_utility": analyze(
            paired_gains(cells, "sign_documented", "free"), with_verdict=False),
        "RW4_reference_minus_random_wrong": analyze(
            paired_gains(cells, "free", "sign_random_mean"), with_verdict=False),
        "RW5_reversal_beyond_random": analyze(
            paired_gains(cells, "sign_random_mean", "pl_sign_flip"), with_verdict=verdict),
        "desc_per_draw_RW1": {
            name: analyze(paired_gains(cells, "sign_documented", name), with_verdict=False)
            for name in random_arm_names()},
        "desc_per_draw_RW4": {
            name: analyze(paired_gains(cells, "free", name), with_verdict=False)
            for name in random_arm_names()},
        "desc_within_cell_draw_sd_mean": float(np.mean([
            by_seed[s]["sign_random_sd"] for by_seed in cells.values() for s in by_seed])),
    }
    if verdict:
        out["predictions"] = {
            "RW_P1_gate_and_reversal_separated": bool(
                gate_ok and out["RW2_reversal_content_gate"]["separated"]),
            "RW_P2_random_content_not_separated": bool(
                not out["RW1_random_content"]["separated"]),
            "RW_P3_reversal_beyond_random_separated": bool(
                out["RW5_reversal_beyond_random"]["separated"]),
        }
    return out


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <experiment_root>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    summary = {
        "experiment_root": str(root),
        "metric": "query_sd_normalized_rmse (lower is better); "
                  "gain = nrmse(second) - nrmse(first), positive favours first",
        "primary_k": int(PRIMARY_K), "n_draws": N_DRAWS,
        "bootstrap": {"reps": pam_summary.BOOTSTRAP_REPS,
                      "seed": pam_summary.BOOTSTRAP_SEED,
                      "hierarchy": "targets then seeds"},
        "seed_sets": {},
    }
    pooled_cells: dict[str, dict[int, dict]] = {}
    pooled_gates: list[dict] = []
    for seed_set in SEED_SETS:
        cells, gates = load_cells(root / seed_set)
        if not cells:
            summary["seed_sets"][seed_set] = {"n_cells": 0}
            continue
        summary["seed_sets"][seed_set] = summarize_seed_set(cells, gates, with_verdicts=True)
        for target, by_seed in cells.items():
            pooled_cells.setdefault(target, {}).update(by_seed)
        pooled_gates.extend(gates)
    if pooled_cells:
        summary["pooled_descriptive"] = summarize_seed_set(
            pooled_cells, pooled_gates, with_verdicts=False)
    complete = all(summary["seed_sets"].get(s, {}).get("n_cells", 0) == 60 for s in SEED_SETS)
    summary["complete_120_cells"] = bool(complete)
    if complete:
        preds = [summary["seed_sets"][s]["predictions"] for s in SEED_SETS]
        summary["verdicts"] = {
            key: bool(all(p[key] for p in preds)) for key in preds[0]}
    (root / "SUMMARY_V1.json").write_text(
        json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
