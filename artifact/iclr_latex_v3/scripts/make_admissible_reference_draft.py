#!/usr/bin/env python3
"""Standalone Section 3.2 concept figure; does not edit the manuscript."""
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", ".runtime")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = Path(__file__).resolve().parents[1] / "figures" / "drafts"
plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42,
                     "svg.fonttype": "none", "mathtext.fontset": "dejavusans"})
fig, ax = plt.subplots(figsize=(13.6, 4.9))
fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
ax.set(xlim=(0, 13.6), ylim=(0, 4.9))
ax.axis("off")
INK, MUTED, LINE = "#202C3A", "#526173", "#A9B5C1"
BLUE, GREEN, RED = "#345C84", "#256B57", "#A34E40"

def text(x, y, s, size=11, color=INK, weight="normal", ha="left", **kw):
    return ax.text(x, y, s, fontsize=size, color=color, weight=weight,
                   ha=ha, va="center", linespacing=1.45, **kw)

def box(x, y, w, h, fill="#F5F7FA", edge=LINE, lw=.9):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0.015,rounding_size=0.07",
                 facecolor=fill, edgecolor=edge, linewidth=lw))

def arrow(x1, y1, x2, y2, color=LINE, dashed=False):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                 mutation_scale=11, linewidth=1.15, color=color,
                 linestyle="--" if dashed else "-", shrinkA=2, shrinkB=2))

text(.22, 4.56, "Constructing an admissible reference", 17, weight="bold")
text(.22, 4.17, "Remove the tested use while preserving what the original claim requires.", 11.5, MUTED)

# Claim specification precedes candidate construction and all three checks.
for y, title, subtitle in [
    (3.23, "Evaluation claim", None),
    (2.38, "Specify the tested use", "Fix what must be preserved"),
    (1.53, "Construct candidate", "reference")]:
    box(.22, y, 2.15, .62)
    text(1.295, y + (.40 if subtitle else .31), title, 10.5, weight="bold", ha="center")
    if subtitle:
        text(1.295, y+.16, subtitle, 9.1, MUTED, ha="center")
arrow(1.295, 3.23, 1.295, 3.03)
arrow(1.295, 2.38, 1.295, 2.18)

# Shared enclosure makes these conjunctive checks, not alternative controls.
box(2.84, 1.52, 7.25, 2.33, fill="#FFFFFF", edge=BLUE, lw=1.1)
text(3.02, 3.59, "THREE REQUIRED CHECKS", 9.5, BLUE, "bold")
arrow(2.39, 1.84, 2.82, 1.84, BLUE)
checks = [
    (3.02, "1", "Removal", "Is the tested use\nactually removed?",
     "Remove this use of\nsemantic knowledge.", "Semantic use remains"),
    (5.40, "2", "Preservation", "Are protected information\nand setup preserved?",
     "Unchanged, or recoverable\nby a fixed deterministic map.", "Compound comparison"),
    (7.78, "3", "Interface validity", "Does it still work through\nthe same interface?",
     "No parsing, shape, routing,\ncardinality or missing-value failures.", "Invalid comparison"),
]
for x, n, title, question, detail, fail in checks:
    if n != "1":
        ax.plot([x-.13, x-.13], [1.72, 3.26], color="#DCE2E8", lw=.8)
    text(x, 3.15, n, 10, BLUE, "bold")
    text(x+.23, 3.15, title, 11.5, INK, "bold")
    text(x, 2.65, question, 10.2)
    text(x, 1.99, detail, 8.5, MUTED)
    arrow(x+1.03, 1.51, x+1.03, 1.17, RED, dashed=True)
    text(x+1.03, 1.00, "FAIL", 8.3, RED, "bold", ha="center")
    text(x+1.03, .75, fail, 9.3, RED, ha="center")

arrow(10.11, 2.88, 10.73, 2.88, GREEN)
text(10.42, 3.16, "All pass", 9, GREEN, "bold", ha="center")
box(10.76, 2.43, 2.60, .91, "#EDF5F1", GREEN, 1.2)
text(12.06, 3.00, "Admissible reference $R$", 11.5, GREEN, "bold", ha="center")
text(12.06, 2.68, "Fix the primary reference\nbefore seeing outcomes", 8.5, GREEN, ha="center")
arrow(12.06, 2.41, 12.06, 2.05, GREEN)
text(12.06, 1.86, "If several admissible\nreferences are evaluated", 9.4, weight="bold", ha="center")
text(12.06, 1.50, "$R_1,\\ R_2,\\ \\ldots$", 12, GREEN, ha="center")
text(12.06, 1.15, "Report reference sensitivity", 9.4, GREEN, "bold", ha="center")
text(12.06, .81, "Utility range over evaluated\nadmissible references only", 8.8, MUTED, ha="center")

ax.plot([.22, 13.36], [.43, .43], color="#DCE2E8", lw=.8)
text(.22, .20, "If no admissible reference exists:", 9.5, weight="bold")
text(3.52, .20, "predictive utility is not separately evaluable.", 9.5)

OUT.mkdir(parents=True, exist_ok=True)
stem = OUT / "admissible_reference_v1"
for ext in ("pdf", "svg", "png"):
    fig.savefig(stem.with_suffix("."+ext), dpi=220, facecolor="white")
print(stem)
