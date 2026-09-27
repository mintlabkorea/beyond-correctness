#!/usr/bin/env python3
"""Conventional cluster-level resolution calculation for real-data utility.

The independent unit is an endpoint or basin.  Seed-level paired contrasts
are averaged within unit, and the minimum detectable positive mean is the
effect giving 80% power for a two-sided one-sample t test at alpha=.05 when
the observed between-unit standard deviation is treated as the planning SD.
This is a descriptive post-hoc resolution calculation, not an equivalence
test and not a claim that the observed SD is a population constant.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
from scipy.optimize import brentq
from scipy.stats import nct, t


PAPER = Path(__file__).resolve().parents[1]
ROOT = PAPER.parent
ALPHA = 0.05
TARGET_POWER = 0.80


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def exact_t_mde(values: list[float]) -> tuple[float, float]:
    array = np.asarray(values, dtype=float)
    n_units = len(array)
    sd = float(array.std(ddof=1))
    critical = float(t.ppf(1.0 - ALPHA / 2.0, n_units - 1))

    def power(effect: float) -> float:
        noncentrality = effect * np.sqrt(n_units) / sd
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            return float(
                nct.cdf(-critical, n_units - 1, noncentrality)
                + nct.sf(critical, n_units - 1, noncentrality)
            )

    upper = sd
    while power(upper) < TARGET_POWER:
        upper *= 2.0
    mde = float(brentq(lambda effect: power(effect) - TARGET_POWER,
                       0.0, upper))
    return mde, sd


def relation_panels() -> list[dict]:
    pam = load_json(
        ROOT / "experiments/crta_v3_pam_constraint_relations_v1/SUMMARY_V1.json"
    )["declared_sign_vs_free_tax_expected"]["per_target_mean"]
    hrs = load_json(
        ROOT / "experiments/crta_v3_m3_sign_probe_v1/SUMMARY_V1.json"
    )["GS_P3_utility_vs_free"]["per_endpoint_mean"]
    camels_12 = load_json(
        ROOT / "experiments/crta_v3_camels_sign_probe_v2/SUMMARY_V2.json"
    )["GCv2_P2_utility"]["log1p_rmse"]["per_basin_mean"]

    extended: dict[str, list[float]] = {}
    probe = ROOT / "experiments/crta_v3_camels_query_extension_v1/probe"
    for path in sorted(probe.glob("support_*/seed_*/metrics.json")):
        record = load_json(path)
        arms = record["arms"]
        for basin, free in arms["free"]["per_basin"].items():
            supplied = arms["sign_documented"]["per_basin"][basin]
            extended.setdefault(basin, []).append(
                float(free["log1p_rmse"])
                - float(supplied["log1p_rmse"])
            )

    return [
        {"setting": "Relation: NHANES--KNHANES", "metric": "norm.-RMSE",
         "values": list(pam.values())},
        {"setting": "Relation: NHANES/KNHANES--HRS", "metric": "norm.-RMSE",
         "values": list(hrs.values())},
        {"setting": "Relation: CAMELS-12", "metric": "log-RMSE",
         "values": list(camels_12.values())},
        {"setting": "Relation: CAMELS-120", "metric": "log-RMSE",
         "values": [float(np.mean(values))
                    for values in extended.values()]},
    ]


def correspondence_panel(root: Path, learner: str) -> dict:
    groups: dict[str, list[float]] = {}
    for path in sorted(root.glob("*/seed_*/metrics.json")):
        record = load_json(path)
        arms = record["auroc"]["256"]
        groups.setdefault(record["target"], []).append(
            float(arms["a11_stage_columns"])
            - float(arms["a10_stage"])
        )
    return {
        "setting": f"Correspondence: survey {learner}",
        "metric": "AUROC",
        "values": [float(np.mean(values)) for values in groups.values()],
    }


def format_effect(value: float) -> str:
    return f"{value:+.4f}".replace("+0.", "+.").replace("-0.", "-.")


def main() -> int:
    panels = relation_panels()
    panels.extend([
        correspondence_panel(
            ROOT / "experiments/crta_v3_m1m2_stage_factorial_v1", "XGB"),
        correspondence_panel(
            ROOT / "experiments/crta_v3_binding_backbone_generality_v1",
            "HistGB"),
    ])

    records = []
    for panel in panels:
        values = panel.pop("values")
        mde, sd = exact_t_mde(values)
        records.append({
            **panel,
            "n_units": len(values),
            "observed_mean": float(np.mean(values)),
            "between_unit_sd": sd,
            "mde_80": mde,
        })

    payload = {
        "analysis_status": "post-hoc conventional resolution diagnostic",
        "test": "two-sided one-sample noncentral-t power",
        "alpha": ALPHA,
        "target_power": TARGET_POWER,
        "unit": "seed-averaged endpoint or basin",
        "planning_sd": "observed between-unit standard deviation",
        "panels": records,
    }
    output_json = PAPER / "generated/real_utility_resolution.json"
    output_json.write_text(json.dumps(payload, indent=2) + "\n",
                           encoding="utf-8")

    lines = [
        r"\begin{table}[H]",
        r"\caption{Conventional cluster-level resolution diagnostic for real-data utility. MDE$_{80}$ is the minimum positive mean giving 80\% power for a two-sided one-sample $t$ test at $\alpha=.05$, treating the observed standard deviation of seed-averaged independent-unit effects as the planning standard deviation. Metrics are native and are not compared across rows. This post-hoc calculation is not an equivalence test or a bound on the observed effect.}",
        r"\label{tab:app-real-utility-resolution}",
        r"\centering\scriptsize",
        r"\setlength{\tabcolsep}{3pt}",
        r"\begin{tabular}{P{0.40\linewidth}P{0.15\linewidth}rrr}",
        r"\toprule",
        r"Setting & Metric & Units & Observed & MDE$_{80}$ \\",
        r"\midrule",
    ]
    for row in records:
        lines.append(
            f"{row['setting']} & {row['metric']} & {row['n_units']} & "
            f"{format_effect(row['observed_mean'])} & "
            f"{row['mde_80']:.4f} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    output_tex = PAPER / "generated/table_real_utility_resolution.tex"
    output_tex.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
