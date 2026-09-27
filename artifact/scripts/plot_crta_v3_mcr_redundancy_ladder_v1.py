"""Plot the MCR-RL redundancy ladder: U(k) with realization-bootstrap CIs."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/crta_v3_mcr_redundancy_ladder_v1"
FAMILIES = ("pairwise", "sparse")
BACKBONES = ("xgb", "histgb")
VR = {"full": (0.0000, 0.0021), "drop": (0.232, 0.242)}


def main() -> int:
    summary = json.loads((EXP / "SUMMARY_V1.json").read_text())
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), sharey="row")
    for row, k in enumerate(("32", "512")):
        for col, family in enumerate(FAMILIES):
            ax = axes[row][col]
            for backbone, colour in zip(BACKBONES, ("#2a6fb0", "#c1541c")):
                table = summary["sections"][k]["rung_table"][f"{backbone}|{family}"]
                ks = sorted(table, key=int)
                xs = [int(x) for x in ks]
                mu = [table[x]["U"]["mean"] for x in ks]
                lo = [table[x]["U"]["ci95"][0] for x in ks]
                hi = [table[x]["U"]["ci95"][1] for x in ks]
                ns = [table[x]["n_realizations"] for x in ks]
                ax.plot(xs, mu, "o-", color=colour, label=backbone, lw=1.8, ms=5)
                ax.fill_between(xs, lo, hi, color=colour, alpha=0.18, lw=0)
                for x, m, n in zip(xs, mu, ns):
                    if n < max(ns):
                        ax.annotate(f"n={n}", (x, m), fontsize=7,
                                    xytext=(0, -12), textcoords="offset points",
                                    ha="center", color=colour)
            ax.axhline(0, color="0.4", lw=0.8, ls=":")
            ax.axhspan(VR["drop"][0], VR["drop"][1], color="0.75", alpha=0.35,
                       lw=0, zorder=0)
            ax.set_title(f"{family}, K={k}", fontsize=11)
            ax.set_xlabel("k = constituent base columns removed")
            if col == 0:
                ax.set_ylabel("U(k) = nMSE(free) − nMSE(op_true)\n(positive = "
                              "operation columns help)", fontsize=9)
            ax.grid(alpha=0.25, lw=0.6)
            ax.legend(fontsize=8, loc="upper left")
    fig.suptitle("MCR-RL: operation-column utility vs. how much constituent "
                 "information the frame still carries\n"
                 "grey band = MCR-VR's frozen drop-frame result "
                 "(+0.232..+0.242 nMSE); k=0 is VR's full-frame null",
                 fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    out = EXP / "LADDER_U_CURVE_V1.png"
    fig.savefig(out, dpi=150)
    print(out)
    return 0


def plot_arm_decomposition() -> Path:
    """The primary figure: absolute arm nMSE, with the gap between them = U(k).

    Drawn because the utility rise is produced by the reference degrading,
    not by the supplied arm improving -- which is invisible in a U(k) plot.
    """
    summary = json.loads((EXP / "SUMMARY_V1.json").read_text())
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for row, k in enumerate(("32", "512")):
        for col, family in enumerate(FAMILIES):
            ax = axes[row][col]
            table = summary["sections"][k]["rung_table"][f"xgb|{family}"]
            ks = sorted(table, key=int)
            xs = [int(x) for x in ks]
            free = [table[x]["arm_mean_nmse"]["free"] for x in ks]
            supp = [table[x]["arm_mean_nmse"]["op_true"] for x in ks]
            ht = summary["sections"][k]["rung_table"][f"histgb|{family}"]
            ax.fill_between(xs, supp, free, color="#7aa6c2", alpha=0.30, lw=0,
                            label="U(k) = the gap")
            ax.plot(xs, free, "o-", color="#b02a2a", lw=2, ms=6,
                    label="reference (free): no operation column")
            ax.plot(xs, supp, "o-", color="#1f6f3f", lw=2, ms=6,
                    label="supplied (op_true): + operation columns")
            ax.plot(xs, [ht[x]["arm_mean_nmse"]["free"] for x in ks], "--",
                    color="#b02a2a", lw=1, alpha=0.65)
            ax.plot(xs, [ht[x]["arm_mean_nmse"]["op_true"] for x in ks], "--",
                    color="#1f6f3f", lw=1, alpha=0.65)
            ax.annotate(f"+{free[-1] - free[0]:.3f}", (xs[-1], free[-1]),
                        xytext=(-4, 8), textcoords="offset points",
                        ha="right", color="#b02a2a", fontsize=9,
                        fontweight="bold")
            ax.annotate(f"+{supp[-1] - supp[0]:.3f}", (xs[-1], supp[-1]),
                        xytext=(-4, -16), textcoords="offset points",
                        ha="right", color="#1f6f3f", fontsize=9,
                        fontweight="bold")
            ax.set_title(f"{family}, K={k}   (solid XGB, dashed HistGB)",
                         fontsize=10)
            ax.set_xlabel("k = constituent base columns removed")
            ax.set_ylabel("mean nMSE (lower is better)", fontsize=9)
            ax.grid(alpha=0.25, lw=0.6)
            if row == 0 and col == 0:
                ax.legend(fontsize=8, loc="upper left")
    fig.suptitle("MCR-RL arm decomposition: utility rises because the "
                 "REFERENCE degrades, not because the supplied arm improves\n"
                 "at every rung both arms see the identical reduced frame; "
                 "they differ only in whether the operation column is present",
                 fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    out = EXP / "LADDER_ARM_DECOMPOSITION_V1.png"
    fig.savefig(out, dpi=150)
    print(out)
    return out


def plot_paper_figure() -> Path:
    """Generate the canonical 2x2 appendix arm decomposition."""
    import sys

    paper_scripts = ROOT / "iclr_latex_v3/scripts"
    if str(paper_scripts) not in sys.path:
        sys.path.insert(0, str(paper_scripts))
    from make_appendix_assets import plot_redundancy_ladder

    plot_redundancy_ladder()
    out = ROOT / "iclr_latex_v3/figures/appendix_figure_a8_redundancy_ladder.pdf"
    print(out)
    return out


if __name__ == "__main__":
    main()
    plot_arm_decomposition()
    plot_paper_figure()
