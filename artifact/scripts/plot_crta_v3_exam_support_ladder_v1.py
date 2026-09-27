"""Plot the examination correspondence utility against labeled target support.

Four panels, in the order the protocol requires them to be read: the class-A
utility ladder, the absolute per-arm trajectories that show whether a decay
is the supplied arm falling or the reference rising, the decay statistics
with the U = C - (R-W) decomposition and the min_child_weight diagnostic,
and the per-endpoint ladders.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/crta_v3_exam_support_ladder_v1"
LADDER = (64, 256, 1024)
CLASS_A = ("glucose", "triglycerides", "waist_cm", "sbp",
           "total_cholesterol", "dbp")
ARM_STYLE = {"S_shared_bridge": ("#2a6fb0", "supplied $S$ (shared bridge)"),
             "R_domain_local": ("#1c6b3c", "reference $R_{domain\\_local}$"),
             "W_deranged_bridge": ("#a02020", "matched-wrong $W$")}


def main() -> int:
    summary = json.loads((EXP / "SUMMARY_V1.json").read_text())
    levels, decays = summary["levels"], summary["decays"]
    verdict = summary["verdicts"]
    diag = summary.get("diagnostic_min_child_weight_decays", {})
    x = np.arange(len(LADDER))
    fig, axes = plt.subplots(1, 4, figsize=(21, 4.7))

    # --- 1: the class-A ladder -------------------------------------------
    ax = axes[0]
    for scope, colour, label in (
            ("classA_primary", "#2a6fb0", "class A (primary, 6 endpoints)"),
            ("all13", "#8a8a8a", "all 13 endpoints (non-verdict-bearing)")):
        rows = [levels[scope]["utility_S_minus_R"][str(k)] for k in LADDER]
        means = [r["mean"] for r in rows]
        lo = [r["mean"] - r["ci95"][0] for r in rows]
        hi = [r["ci95"][1] - r["mean"] for r in rows]
        ax.errorbar(x, means, yerr=[lo, hi], color=colour, marker="o",
                    capsize=5, lw=1.8, label=label)
    ax.axhline(0, color="0.3", lw=0.9)
    ax.set_xticks(x); ax.set_xticklabels([f"K={k}" for k in LADDER])
    ax.set_xlabel("distinct labeled target rows (target mass pinned)", fontsize=8)
    ax.set_ylabel("utility $S-R$ (nRMSE reduction, higher better)", fontsize=9)
    retention = verdict["retention_classA"].get("retention_point")
    ax.set_title("Utility across support\n"
                 f"retention m(1024)/m(64) = "
                 f"{retention:.2f}" if retention else "Utility across support",
                 fontsize=10)
    ax.legend(fontsize=7); ax.grid(axis="y", alpha=0.25, lw=0.6)

    # --- 2: absolute per-arm trajectories --------------------------------
    ax = axes[1]
    traj = summary["absolute_nrmse_trajectories"]["classA_primary"]
    for arm, (colour, label) in ARM_STYLE.items():
        ax.plot(x, [traj[arm][str(k)] for k in LADDER], marker="o",
                color=colour, lw=1.8, label=label)
    ax.set_xticks(x); ax.set_xticklabels([f"K={k}" for k in LADDER])
    ax.set_xlabel("distinct labeled target rows", fontsize=8)
    ax.set_ylabel("absolute nRMSE (lower is better)", fontsize=9)
    ax.set_title("Is a decay the supplied arm falling\nor the reference rising?",
                 fontsize=10)
    ax.legend(fontsize=7); ax.grid(axis="y", alpha=0.25, lw=0.6)

    # --- 3: decay statistics, decomposition, diagnostic -------------------
    ax = axes[2]
    keys = [("decay_utility_S_minus_R_64_minus_1024", "utility\n(PRIMARY)", False),
            ("decay_content_S_minus_W_64_minus_1024", "content\n$S-W$", True),
            ("decay_reference_minus_wrong_R_minus_W_64_minus_1024",
             "reference\n$R-W$", True)]
    rows, labels, colours = [], [], []
    for key, label, descriptive in keys:
        r = decays["classA_primary"][key]
        rows.append(r); labels.append(label)
        colours.append("#8a8a8a" if descriptive
                       else ("#1c6b3c" if r["separated"] else "#a02020"))
    dk = "diag_mcw_decay_utility_S_minus_R_64_minus_1024"
    if diag.get("classA_primary", {}).get(dk):
        r = diag["classA_primary"][dk]
        rows.append(r); labels.append("utility\nmin_child_weight\ndiagnostic")
        colours.append("#c1541c")
    means = [r["mean"] for r in rows]
    lo = [r["mean"] - r["ci95"][0] for r in rows]
    hi = [r["ci95"][1] - r["mean"] for r in rows]
    ax.bar(labels, means, 0.55, color=colours, yerr=[lo, hi], capsize=6,
           error_kw={"lw": 1.2})
    ax.axhline(0, color="0.3", lw=0.9)
    ax.axhline(verdict["primary_decay"]["sesoi"], color="#666", lw=1.0,
               ls=":", label="SESOI (.020)")
    band = verdict["predicted_decay_interval"]
    ax.axhspan(band[0], band[1], color="#2a6fb0", alpha=0.10,
               label="calibrated prediction")
    ax.set_ylabel("decay, K=64 minus K=1024", fontsize=9)
    ax.set_title(verdict["verdict"][:52] + "…", fontsize=9)
    ax.legend(fontsize=7); ax.tick_params(labelsize=7)
    ax.grid(axis="y", alpha=0.25, lw=0.6)

    # --- 4: per-endpoint ladders -----------------------------------------
    ax = axes[3]
    per = summary["per_endpoint_descriptive"]
    cmap = plt.get_cmap("tab10")
    for i, endpoint in enumerate(CLASS_A):
        row = per[endpoint]
        ax.plot(x, [row[f"utility_k{k}"] for k in LADDER], marker="o", ms=4,
                lw=1.4, color=cmap(i), label=endpoint)
    ax.axhline(0, color="0.3", lw=0.9)
    ax.set_xticks(x); ax.set_xticklabels([f"K={k}" for k in LADDER])
    ax.set_xlabel("distinct labeled target rows", fontsize=8)
    ax.set_ylabel("per-endpoint utility", fontsize=9)
    ax.set_title("Per endpoint, class A (descriptive)", fontsize=10)
    ax.legend(fontsize=7, ncol=2); ax.grid(axis="y", alpha=0.25, lw=0.6)

    fig.tight_layout()
    out = EXP / "SUPPORT_LADDER_V1.png"
    fig.savefig(out, dpi=150)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
