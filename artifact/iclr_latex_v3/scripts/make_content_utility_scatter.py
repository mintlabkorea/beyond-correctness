#!/usr/bin/env python3
"""Plot content sensitivity against predictive utility for the M/C/R panels.

The default view uses the reported metric units.  ``--normalize`` divides both
coordinates and their marginal confidence limits by the corresponding content
point estimate.  The normalized point therefore has x=1 and y=utility/content;
the y=x line denotes equality of the two contrasts.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", ".runtime")
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


PAPER_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PAPER_ROOT / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BLUE = "#377eb8"
ORANGE = "#e68613"
PURPLE = "#7b61a8"
GRAY = "#686868"
LIGHT_GRAY = "#ececec"

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.size": 8,
        "axes.labelsize": 8.5,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "legend.fontsize": 7.0,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


@dataclass(frozen=True)
class Panel:
    short: str
    label: str
    setting: str
    content: float
    content_ci: tuple[float, float]
    utility: float
    utility_ci: tuple[float, float]
    color: str
    marker: str


PANELS = (
    Panel(
        "M", "Measurement", "3-endpoint polarity",
        0.292, (0.145, 0.431), 0.384, (0.202, 0.553), BLUE, "o",
    ),
    Panel(
        "C", "Correspondence", "6-endpoint examination",
        0.070, (0.029, 0.121), 0.047, (0.017, 0.084), ORANGE, "s",
    ),
    Panel(
        "R", "Relation", "CAMELS-120",
        0.144, (0.127, 0.163), -0.0000, (-0.0011, 0.0012), PURPLE, "^",
    ),
)


def asymmetric_error(center: float, interval: tuple[float, float]) -> np.ndarray:
    low, high = interval
    if not low <= center <= high:
        raise ValueError(f"Point estimate {center} lies outside {interval}")
    return np.asarray([[center - low], [high - center]], dtype=float)


def save(fig: plt.Figure, stem: str) -> None:
    for suffix in ("png", "pdf"):
        fig.savefig(
            OUT_DIR / f"{stem}.{suffix}",
            dpi=320 if suffix == "png" else None,
            bbox_inches="tight",
            facecolor="white",
        )
    plt.close(fig)


def make_raw() -> None:
    """Raw-coordinate diagnostic; cross-panel distances are not comparable."""
    fig, ax = plt.subplots(figsize=(4.25, 3.25))
    for panel in PANELS:
        ax.errorbar(
            panel.content,
            panel.utility,
            xerr=asymmetric_error(panel.content, panel.content_ci),
            yerr=asymmetric_error(panel.utility, panel.utility_ci),
            fmt=panel.marker,
            color=panel.color,
            markerfacecolor=panel.color,
            markeredgecolor="white",
            markeredgewidth=0.7,
            markersize=7.0,
            elinewidth=1.15,
            capsize=3.0,
            label=f"{panel.short}: {panel.label}",
            zorder=3,
        )
    low, high = -0.025, 0.58
    ax.plot([low, high], [low, high], color=GRAY, linestyle="--", linewidth=0.9)
    ax.axhline(0, color="#999999", linewidth=0.65)
    ax.set_xlim(low, 0.46)
    ax.set_ylim(low, high)
    ax.set_xlabel("Content sensitivity (intended $-$ wrong)")
    ax.set_ylabel("Predictive utility (intended $-$ reference)")
    ax.grid(color=LIGHT_GRAY, linewidth=0.6, zorder=0)
    ax.legend(frameon=False, loc="upper left")
    fig.subplots_adjust(left=0.17, bottom=0.18, right=0.98, top=0.97)
    save(fig, "figure_content_utility_scatter_raw")


def make_normalized() -> None:
    """Unit-free view: divide both coordinates by each content estimate."""
    fig, ax = plt.subplots(figsize=(4.45, 3.35))

    for panel in PANELS:
        scale = panel.content
        x = panel.content / scale
        y = panel.utility / scale
        x_ci = tuple(value / scale for value in panel.content_ci)
        y_ci = tuple(value / scale for value in panel.utility_ci)
        ax.errorbar(
            x,
            y,
            xerr=asymmetric_error(x, x_ci),
            yerr=asymmetric_error(y, y_ci),
            fmt=panel.marker,
            color=panel.color,
            markerfacecolor=panel.color,
            markeredgecolor="white",
            markeredgewidth=0.7,
            markersize=7.4,
            elinewidth=1.2,
            capsize=3.2,
            label=f"{panel.short}: {panel.label}",
            zorder=4,
        )
        displayed_ratio = 0.0 if abs(y) < 0.005 else y
        ax.annotate(
            f"{panel.short}  {displayed_ratio:.2f}",
            xy=(x, y),
            xytext=(7, 0 if panel.short != "R" else 7),
            textcoords="offset points",
            ha="left",
            va="center" if panel.short != "R" else "bottom",
            fontsize=7.0,
            fontweight="bold",
            color=panel.color,
            zorder=5,
        )

    x_low, x_high = 0.35, 1.82
    y_low, y_high = -0.12, 2.00
    diagonal_low = max(x_low, y_low)
    diagonal_high = min(x_high, y_high)
    ax.plot(
        [diagonal_low, diagonal_high],
        [diagonal_low, diagonal_high],
        color=GRAY,
        linestyle="--",
        linewidth=0.95,
        zorder=1,
    )
    ax.text(
        1.50, 1.55, "equal contrasts\n(ratio = 1)",
        rotation=45, ha="center", va="bottom", fontsize=6.2, color=GRAY,
    )
    ax.axhline(0, color="#999999", linewidth=0.65, zorder=1)
    ax.set_xlim(x_low, x_high)
    ax.set_ylim(y_low, y_high)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Content sensitivity / content estimate")
    ax.set_ylabel("Predictive utility / content estimate")
    ax.grid(color=LIGHT_GRAY, linewidth=0.6, zorder=0)
    ax.legend(
        frameon=False,
        loc="lower center",
        bbox_to_anchor=(0.5, 1.015),
        ncol=3,
        columnspacing=1.0,
        handletextpad=0.35,
    )
    fig.text(
        0.985,
        0.018,
        "Error bars are the reported marginal 95% CIs rescaled by the same denominator.",
        ha="right",
        va="bottom",
        fontsize=5.4,
        color=GRAY,
    )
    fig.subplots_adjust(left=0.18, bottom=0.21, right=0.98, top=0.88)
    save(fig, "figure_content_utility_scatter_normalized")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--normalize",
        action="store_true",
        help="divide each point and its marginal CIs by its content estimate",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.normalize:
        make_normalized()
    else:
        make_raw()


if __name__ == "__main__":
    main()
