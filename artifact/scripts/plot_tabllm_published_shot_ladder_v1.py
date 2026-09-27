#!/usr/bin/env python3
"""Figure for the TabLLM published shot-ladder retrospective, v1."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/tabllm_published_shot_ladder_v1"
SUMMARY = json.loads((EXP / "SUMMARY_V1.json").read_text())
EXTRACTED = json.loads((EXP / "EXTRACTED_TABLES_V1.json").read_text())

SHOTS = [0, 4, 8, 16, 32, 64, 128, 256, 512]
X = np.arange(len(SHOTS))

fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.0))

ax = axes[0]
colors = {"S": "#1a7f37", "R_pub": "#555555", "W": "#b3261e"}
labels = {"S": "intended (List Template)",
          "R_pub": "reference (List Only Values)",
          "W": "wrong (List Perm. Names)"}
for arm in ("S", "R_pub", "W"):
    y = [SUMMARY["absolute_macro_trajectories"][arm][str(k)] for k in SHOTS]
    ax.plot(X, y, marker="o", ms=4, color=colors[arm], label=labels[arm])
ax.set_xticks(X, [str(k) for k in SHOTS])
ax.set_xlabel("labeled examples (shots)")
ax.set_ylabel("macro test AUROC (9 datasets)")
ax.set_title("(a) absolute performance")
ax.legend(frameon=False, fontsize=8)
ax.grid(alpha=0.25)

ax = axes[1]
per_ds = {}
for ds, arms in EXTRACTED["table"].items():
    per_ds[ds] = [(arms["S"][str(k)]["mean_cents"]
                   - arms["R_pub"][str(k)]["mean_cents"]) / 100.0 for k in SHOTS]
for ds, y in sorted(per_ds.items()):
    ax.plot(X, y, color="#9ecae1", lw=0.8, zorder=1)
levels = SUMMARY["utility_levels_macro"]
mean = [levels[str(k)]["mean"] for k in SHOTS]
lo = [levels[str(k)]["bootstrap_ci95"][0] for k in SHOTS]
hi = [levels[str(k)]["bootstrap_ci95"][1] for k in SHOTS]
ax.fill_between(X, lo, hi, color="#2166ac", alpha=0.18, zorder=2)
ax.plot(X, mean, marker="o", ms=5, color="#2166ac", zorder=3,
        label="macro utility (bootstrap CI95)")
ax.axhline(0.0, color="black", lw=0.8)
primary = SUMMARY["contrasts"]["primary_decay_utility_0_minus_512"]
ax.annotate(
    f"decay 0→512: {primary['mean']:+.3f}\n"
    f"[{primary['bootstrap_ci95'][0]:+.3f}, {primary['bootstrap_ci95'][1]:+.3f}]",
    xy=(0.55, 0.82), xycoords="axes fraction", fontsize=9)
ax.set_xticks(X, [str(k) for k in SHOTS])
ax.set_xlabel("labeled examples (shots)")
ax.set_ylabel("utility  S − R_pub  (AUROC)")
ax.set_title("(b) feature-name utility vs. labeled examples")
ax.legend(frameon=False, fontsize=8, loc="lower left")
ax.grid(alpha=0.25)

fig.suptitle("TabLLM published shot ladder (Tables 12–14, retrospective)",
             fontsize=11)
fig.tight_layout(rect=(0, 0, 1, 0.95))
for suffix in ("png", "pdf"):
    fig.savefig(EXP / f"SHOT_LADDER_V1.{suffix}", dpi=200)
print("wrote", EXP / "SHOT_LADDER_V1.png")
