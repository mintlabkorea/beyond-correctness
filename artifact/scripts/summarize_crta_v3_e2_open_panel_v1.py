#!/usr/bin/env python3
"""Adjudicate E2-P2/P3: per open model, A1 = AUROC(llm_table) −
AUROC(placebo_table) and A3 = AUROC(llm_table) − AUROC(pipeline_table) over
the 30 frozen three-endpoint cells at K=256, with `llm_table` from the
model's E2 tree and the other arms from the frozen survey-label panel.
Bootstrap 10,000 reps, seed 20260819 (the frozen panel's); separated =
mean > 0 ∧ CI95 low > 0 ∧ win ≥ .60.
Prereg: iclr_latex_v3/E2_QUESTIONNAIRE_VALUE_TABLE_OPEN_PANEL_PREREGISTRATION_V1.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "experiments/crta_v3_survey_label_panel_v1"
E2 = ROOT / "experiments/crta_v3_e2_open_panel_v1"
TARGETS = ("diabetes_history", "hypertension_history", "current_smoking_status")
SEEDS = tuple(range(50, 60))
K = "256"
REPS = 10000
SEED = 20260819
WIN = 0.60


def boot(values: np.ndarray, key: str) -> dict:
    seed = int(hashlib.sha256(f"e2_panel|{SEED}|{key}".encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    chosen = rng.integers(0, len(values), size=(REPS, len(values)))
    means = values[chosen].mean(axis=1)
    lo, hi = float(np.quantile(means, .025)), float(np.quantile(means, .975))
    mean = float(np.mean(values))
    win = float(np.mean(values > 0))
    return {"mean": mean, "ci95": [lo, hi], "win": win, "n": int(len(values)),
            "separated": bool(mean > 0 and lo > 0 and win >= WIN)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--e2-root", type=Path, default=E2)
    args = parser.parse_args()
    score = json.loads((args.e2_root / "E2_SCORE_V1.json").read_text())
    frozen = {}
    for t in TARGETS:
        for s in SEEDS:
            frozen[(t, s)] = json.loads((FROZEN / t / f"seed_{s}" / "metrics.json").read_text())["auroc"][K]
    models: dict[str, dict] = {}
    for run in sorted((args.e2_root / "label_panel").glob("*/")):
        name = run.name
        if (run / "NOT_MATERIALIZABLE.json").is_file():
            models[name] = {"materializable": False,
                            "error": json.loads((run / "NOT_MATERIALIZABLE.json").read_text())["error"]}
            continue
        cells = {}
        for t in TARGETS:
            for s in SEEDS:
                p = run / t / f"seed_{s}" / "metrics.json"
                if not p.is_file():
                    continue
                cells[(t, s)] = json.loads(p.read_text())["auroc"][K]["llm_table"]
        if len(cells) != len(TARGETS) * len(SEEDS):
            models[name] = {"materializable": True, "complete": False, "n_cells": len(cells)}
            continue
        a1 = np.asarray([cells[k] - frozen[k]["placebo_table"] for k in sorted(cells)])
        a3 = np.asarray([cells[k] - frozen[k]["pipeline_table"] for k in sorted(cells)])
        per_target = {t: {"llm_mean": float(np.mean([cells[(t, s)] for s in SEEDS])),
                          "a1_mean": float(np.mean([cells[(t, s)] - frozen[(t, s)]["placebo_table"] for s in SEEDS])),
                          "a3_mean": float(np.mean([cells[(t, s)] - frozen[(t, s)]["pipeline_table"] for s in SEEDS]))}
                      for t in TARGETS}
        models[name] = {"materializable": True, "complete": True,
                        "A1_llm_minus_placebo": boot(a1, f"A1|{name}"),
                        "A3_llm_minus_pipeline": boot(a3, f"A3|{name}"),
                        "per_target": per_target}
    n_sep = sum(1 for m in models.values() if m.get("complete") and m["A1_llm_minus_placebo"]["separated"])
    n_complete = sum(1 for m in models.values() if m.get("complete"))
    payload = {"E2_P1": score["E2_P1"], "models": models,
               "E2_P2": {"n_models_separated": n_sep, "n_models_complete": n_complete,
                         "pass": bool(n_sep >= 1)},
               "verdicts": {"E2_P1": score["E2_P1"]["pass"], "E2_P2": bool(n_sep >= 1)}}
    payload["verdicts"]["all"] = bool(payload["verdicts"]["E2_P1"] and payload["verdicts"]["E2_P2"])
    (args.e2_root / "SUMMARY_V1.json").write_text(json.dumps(payload, indent=1, sort_keys=True))
    print(json.dumps({"verdicts": payload["verdicts"], "E2_P2": payload["E2_P2"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
