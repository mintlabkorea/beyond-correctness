#!/usr/bin/env python3
"""Figures for GC-REL (N6) and the audit-grade join (N5).

Left: the CAMELS identification effect decomposed by relation.
Right: audit evidence strength against measured content effect, one point
per endpoint, so the null is visible rather than only tabulated.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
GC_REL = ROOT / "experiments/crta_v3_camels_sign_relation_ablation_v1/SUMMARY_GC_REL.json"
N5 = ROOT / "experiments/crta_v3_audit_grade_vs_effect_v1/SUMMARY_N5.json"
OUT = ROOT / "experiments/crta_v3_audit_grade_vs_effect_v1"
GRADE_ORDER = ["Mixed", "Conditional", "Constructive, indirect", "Indirect",
               "Direct, qualified"]


def panel_gc_rel(ax) -> None:
    gc = json.loads(GC_REL.read_text(encoding="utf-8"))
    rows = [
        ("$B-D$  both flipped\n(v2 published)",
         gc["both_flip_reference"]["log1p_rmse"], "#444444"),
        ("$P-D$  precip flipped\n| PET documented",
         gc["single_flip"]["flip_precip_only"]["log1p_rmse"], "#1b6ca8"),
        ("$B-E$  precip flipped\n| PET also flipped",
         gc["opposite_conditional_effects"]
           ["precip_given_flipped_pet_B_minus_E"]["log1p_rmse"], "#5599c7"),
        ("$E-D$  PET flipped\n| precip documented",
         gc["single_flip"]["flip_pet_only"]["log1p_rmse"], "#c1440e"),
        ("$B-P$  PET flipped\n| precip also flipped",
         gc["opposite_conditional_effects"]
           ["pet_given_flipped_precip_B_minus_P"]["log1p_rmse"], "#e08b6a"),
        ("$\\varphi_{precip}$  Shapley",
         gc["shapley_effects"]["flip_precip_only"]["log1p_rmse"], "#0b3c5d"),
        ("$\\varphi_{PET}$  Shapley",
         gc["shapley_effects"]["flip_pet_only"]["log1p_rmse"], "#8c2d04"),
    ]
    for i, (label, block, color) in enumerate(rows):
        mean, (low, high) = block["mean_gain"], block["ci95"]
        ax.errorbar(mean, i, xerr=[[mean - low], [high - mean]], fmt="o",
                    color=color, capsize=4, markersize=7, linewidth=2)
        ax.annotate(f"{mean:+.4f}", (mean, i), textcoords="offset points",
                    xytext=(0, 11), ha="center", fontsize=8, color=color)
    ax.axvline(0, color="grey", linewidth=1, linestyle="--")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("log1p RMSE penalty from flipping the relation\n"
                  "(higher = the declared direction was load-bearing)", fontsize=9)
    share = gc["shapley_share_of_both_flip_log1p_rmse"]
    ax.set_title("N6  CAMELS identification, decomposed by relation\n"
                 "60 cells, basin-clustered 95% CI;  Shapley shares: "
                 f"precipitation {share['flip_precip_only']:.1%}, "
                 f"PET {share['flip_pet_only']:.1%}", fontsize=10)
    ax.grid(axis="x", alpha=0.3)


def panel_n5(ax) -> None:
    report = json.loads(N5.read_text(encoding="utf-8"))
    markers = {"NHANES-KNHANES": "o", "NHANES/KNHANES-HRS": "s"}
    colors = {"NHANES-KNHANES": "#1b6ca8", "NHANES/KNHANES-HRS": "#7b3294"}
    rng = np.random.default_rng(0)
    for unit in report["units"]:
        x = unit["grade_rank"] + rng.uniform(-0.13, 0.13)
        ax.scatter(x, unit["content"], marker=markers[unit["setting"]],
                   color=colors[unit["setting"]], s=55, zorder=3,
                   label=unit["setting"])
        ax.annotate(unit["endpoint"], (x, unit["content"]),
                    textcoords="offset points", xytext=(6, -3), fontsize=7.5,
                    color="#333333")
    tau = report["relation_level"]["content"]["kendall_tau_b"]
    p = report["relation_level"]["content"]["exact_permutation_p_two_sided"]
    envelope = report["relation_level"]["content"]["ordering_envelope"]
    ax.set_xticks(range(1, 6))
    ax.set_xticklabels([g.replace(", ", ",\n") for g in GRADE_ORDER],
                       fontsize=7.5)
    ax.set_xlabel("External evidence audit grade  (weaker -> stronger)", fontsize=9)
    ax.set_ylabel("Content effect (sd-normalized RMSE)", fontsize=9)
    ax.set_title("N5  Audit grade vs measured content effect\n"
                 f"relation-level Kendall tau = {tau:+.3f}, exact p = {p:.3f};  "
                 f"best of all {envelope['n_orderings_tried']} grade orderings = "
                 f"{envelope['best_tau']:+.3f}", fontsize=10)
    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    ax.legend(unique.values(), unique.keys(), fontsize=8, loc="upper left")
    ax.grid(alpha=0.3)
    ax.set_xlim(0.4, 5.9)


def main() -> int:
    fig, axes = plt.subplots(1, 2, figsize=(15.5, 6.4))
    panel_gc_rel(axes[0])
    panel_n5(axes[1])
    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "n5_n6_audit_grade_vs_effect.png"
    fig.savefig(path, dpi=170, bbox_inches="tight")
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
