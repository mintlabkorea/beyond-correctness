#!/usr/bin/env python3
"""Absolute nMSE audit for XGB, HistGB, and MLP M x C cells."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
TREE_ROOT = REPO / "experiments/crta_v3_mcr_factorial_semisynth_v1/primary"
MLP_ROOT = REPO / "experiments/crta_v3_mcr_factorial_mlp_v1"
FAMILIES = ("additive", "pairwise", "sparse")
LEARNERS = ("xgb", "histgb", "mlp")
KS = ("32", "512")
ARMS = ("m0c0rf", "m0c1rf", "m1c0rf", "m1c1rf")
REPS = 10_000
SEED = 20260820


def stable_rng(key: str) -> np.random.Generator:
    h = hashlib.sha256(f"absolute_nmse|{SEED}|{key}".encode()).hexdigest()
    return np.random.default_rng(int(h[:8], 16))


def load() -> dict[tuple[str, str, str], list[dict]]:
    out = {}
    for family in FAMILIES:
        for p in sorted((TREE_ROOT / family).glob("r*/metrics.json")):
            d = json.loads(p.read_text())
            for k in KS:
                for learner in ("xgb", "histgb"):
                    out.setdefault((learner, family, k), []).append({
                        "realization": int(d["realization"]),
                        **{arm: float(d["results"][k][learner][arm]["nmse"]) for arm in ARMS},
                    })
        for p in sorted((MLP_ROOT / family).glob("r*/metrics.json")):
            d = json.loads(p.read_text())
            for k in KS:
                out.setdefault(("mlp", family, k), []).append({
                    "realization": int(d["realization"]),
                    **{arm: float(d["results"][k][arm]["nmse"]) for arm in ARMS},
                })
    if len(out) != 18 or any(len(v) != 20 for v in out.values()):
        raise RuntimeError("expected 18 learner-family-K strata x 20 realizations")
    return out


def contrasts(row: dict) -> dict[str, float]:
    return {
        "measurement": row["m0c1rf"] - row["m1c1rf"],
        "correspondence": row["m1c0rf"] - row["m1c1rf"],
        "MC_interaction": -row["m1c1rf"] + row["m1c0rf"] + row["m0c1rf"] - row["m0c0rf"],
    }


def main() -> int:
    cells = load()
    absolute_rows = []
    contrast_rows = []
    comparison_rows = []
    for key, records in sorted(cells.items()):
        learner, family, k = key
        for arm in ARMS:
            x = np.asarray([r[arm] for r in records])
            absolute_rows.append({
                "learner": learner, "family": family, "K": int(k), "arm": arm,
                "n": len(x), "mean_nmse": float(x.mean()), "sd_nmse": float(x.std(ddof=1)),
                "min_nmse": float(x.min()), "max_nmse": float(x.max()),
            })
        c = [contrasts(r) for r in records]
        for name in c[0]:
            x = np.asarray([r[name] for r in c])
            rng = stable_rng(f"{learner}|{family}|{k}|{name}")
            draws = x[rng.integers(0, len(x), size=(REPS, len(x)))].mean(axis=1)
            contrast_rows.append({
                "learner": learner, "family": family, "K": int(k), "contrast": name,
                "n": len(x), "mean": float(x.mean()),
                "ci95_low": float(np.quantile(draws, .025)),
                "ci95_high": float(np.quantile(draws, .975)),
                "win_rate": float(np.mean(x > 0)),
            })

    for family in FAMILIES:
        for k in KS:
            mlp = {r["realization"]: r for r in cells[("mlp", family, k)]}
            for tree_name in ("xgb", "histgb"):
                tree = {r["realization"]: r for r in cells[(tree_name, family, k)]}
                for quantity in (*ARMS, "measurement", "correspondence", "MC_interaction"):
                    values = []
                    for realization in sorted(mlp):
                        m = mlp[realization] if quantity in ARMS else contrasts(mlp[realization])
                        t = tree[realization] if quantity in ARMS else contrasts(tree[realization])
                        values.append(m[quantity] - t[quantity])
                    x = np.asarray(values)
                    rng = stable_rng(f"compare|{tree_name}|{family}|{k}|{quantity}")
                    draws = x[rng.integers(0, len(x), size=(REPS, len(x)))].mean(axis=1)
                    comparison_rows.append({
                        "comparison": f"mlp_minus_{tree_name}", "family": family,
                        "K": int(k), "quantity": quantity, "n_paired_realizations": len(x),
                        "mean_difference": float(x.mean()),
                        "ci95_low": float(np.quantile(draws, .025)),
                        "ci95_high": float(np.quantile(draws, .975)),
                    })

    outputs = (("mlp_absolute_nmse.csv", absolute_rows), ("contrasts.csv", contrast_rows),
               ("learner_comparisons.csv", comparison_rows))
    for name, rows in outputs:
        with (HERE / name).open("w", newline="") as f:
            w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)

    mlp_summary = json.loads((MLP_ROOT / "SUMMARY_V1.json").read_text())
    tree_summary = json.loads(
        (REPO / "experiments/crta_v3_mcr_factorial_semisynth_v1/SUMMARY_V1.json").read_text()
    )
    max_error = 0.0
    max_tree_contrast_error = 0.0
    for row in absolute_rows:
        if row["learner"] == "mlp":
            expected = mlp_summary["arm_mean_nmse"][str(row["K"])][row["family"]][row["arm"]]
            max_error = max(max_error, abs(row["mean_nmse"] - expected))
    parent_names = {"MC_interaction": "P4_MC_interaction"}
    for row in contrast_rows:
        if row["learner"] in ("xgb", "histgb") and row["contrast"] in parent_names:
            expected = tree_summary["primary"][f"{row['learner']}_K{row['K']}"][
                parent_names[row["contrast"]]
            ][row["family"]]["mean"]
            max_tree_contrast_error = max(
                max_tree_contrast_error, abs(row["mean"] - expected)
            )
    if max_error > 1e-12:
        raise AssertionError(f"MLP parent mean mismatch: {max_error}")
    if max_tree_contrast_error > 1e-12:
        raise AssertionError(f"tree parent contrast mismatch: {max_tree_contrast_error}")
    payload = {
        "status": "complete", "bootstrap": {"reps": REPS, "seed": SEED,
                                                "unit": "paired realization within stratum"},
        "max_mlp_parent_arm_mean_error": max_error,
        "max_tree_parent_contrast_error": max_tree_contrast_error,
        "machine_readable_outputs": [name for name, _ in outputs],
        "interpretive_question": (
            "Assess whether MLP intended-cell nMSE is comparable to tree learners while "
            "reference/wrong cells and derived effects differ, distinguishing replication "
            "from learner-coverage stress testing."
        ),
        "sources": [str(TREE_ROOT.relative_to(REPO)), str(MLP_ROOT.relative_to(REPO)),
                    "scripts/summarize_crta_v3_mcr_factorial_mlp_v1.py"],
    }
    (HERE / "summary.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"written": [name for name, _ in outputs] + ["summary.json"],
                      "max_mlp_parent_error": max_error,
                      "max_tree_parent_error": max_tree_contrast_error}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
