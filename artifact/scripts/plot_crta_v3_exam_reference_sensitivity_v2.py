"""Per-endpoint examination utility on the expanded 13-endpoint panel."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/crta_v3_exam_reference_sensitivity_v2"
COLOUR = {"A": "#2a6fb0", "B": "#c1541c", "C": "#6b6b6b"}
LABEL = {"A": "class A: cardiometabolic anchor (original six)",
         "B": "class B: alt, bun", "C": "class C: base-slot targets"}


def main() -> int:
    s = json.loads((EXP / "SUMMARY_V1.json").read_text())
    cls = {t: c for c, v in s["per_class"].items() for t in v["targets"]}
    pe = s["contrasts"]["full_13_endpoints"][
        "utility_S_minus_R_domain_local"]["per_endpoint_mean"]
    order = sorted(pe, key=lambda k: -pe[k])

    fig, (ax, ax2) = plt.subplots(
        1, 2, figsize=(13, 4.6), gridspec_kw={"width_ratios": [2.1, 1]})

    ax.bar(range(len(order)), [pe[t] for t in order],
           color=[COLOUR[cls[t]] for t in order])
    full = s["contrasts"]["full_13_endpoints"]["utility_S_minus_R_domain_local"]
    six = s["contrasts"]["class_A_original_six"]["utility_S_minus_R_domain_local"]
    ax.axhline(six["mean"], color="#2a6fb0", ls="--", lw=1.4,
               label=f"original six pooled {six['mean']:+.4f} (separates)")
    ax.axhline(full["mean"], color="#111111", ls="-", lw=1.4,
               label=f"13-endpoint pooled {full['mean']:+.4f} (unresolved)")
    ax.axhspan(full["ci95"][0], full["ci95"][1], color="0.5", alpha=0.16, lw=0)
    ax.axhline(0, color="0.2", lw=0.9)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels(order, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("utility vs $R_{domain\\_local}$\n(nRMSE reduction, higher better)",
                  fontsize=9)
    ax.set_title("Utility is confined to the cardiometabolic anchor endpoints\n"
                 "grey band = 13-endpoint 95% CI, which contains zero",
                 fontsize=10)
    handles = [plt.Rectangle((0, 0), 1, 1, color=COLOUR[c]) for c in "ABC"]
    ax.legend(handles + ax.get_legend_handles_labels()[0],
              [LABEL[c] for c in "ABC"] + ax.get_legend_handles_labels()[1],
              fontsize=7.5, loc="upper right")
    ax.grid(axis="y", alpha=0.25, lw=0.6)

    names = ["content\n$S-W$", "utility\n$S-R_{local}$"]
    for i, panel in enumerate(("class_A_original_six", "full_13_endpoints")):
        keys = ["content_S_minus_W", "utility_S_minus_R_domain_local"]
        vals = [s["contrasts"][panel][k] for k in keys]
        x = np.arange(2) + (i - 0.5) * 0.36
        colour = "#2a6fb0" if i == 0 else "#111111"
        ax2.bar(x, [v["mean"] for v in vals], 0.34, color=colour,
                label="original six" if i == 0 else "13 endpoints",
                yerr=[[v["mean"] - v["ci95"][0] for v in vals],
                      [v["ci95"][1] - v["mean"] for v in vals]],
                capsize=5, error_kw={"lw": 1.1})
    ax2.axhline(0, color="0.2", lw=0.9)
    ax2.set_xticks(range(2))
    ax2.set_xticklabels(names, fontsize=9)
    ax2.set_title("Content sensitivity generalizes;\npredictive utility does not",
                  fontsize=10)
    ax2.legend(fontsize=8)
    ax2.grid(axis="y", alpha=0.25, lw=0.6)

    fig.tight_layout()
    out = EXP / "EXPANDED_PANEL_V1.png"
    fig.savefig(out, dpi=150)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
