#!/usr/bin/env python3
"""Section 4.3 standalone figure: the evaluated reference library, not CIs.

Caption: Predictive-utility sign depends on the admissible reference in four
of nine TabLLM datasets. Points show utility for each of 24 frozen anonymous
identifier mappings at n_adapt=0; lines span their minimum and maximum, and
diamonds mark the name-masked reference (ref_00). Orange rows cross zero.
The separate macro row uses the 24 index-aligned global constructions, not the
dataset-wise product space. Ranges describe the evaluated library, not
confidence intervals or bounds over the full admissible reference space.
"""
import csv
import hashlib
import json
from pathlib import Path

import make_main_figures as mf
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter
import numpy as np


def main():
    source = mf.REPO_ROOT / "experiments/tabllm_reference_space_v1/summary_v1"
    summary_path = source / "SUMMARY_V1.json"
    csv_path = source / "reference_utilities.csv"
    summary = json.loads(summary_path.read_text())
    with csv_path.open() as handle:
        rows = list(csv.DictReader(handle))
    assert summary["reference_count"] == 24 and summary["dataset_count"] == 9
    order = ["calhousing", "creditg", "heart", "jungle",
             "bank", "blood", "car", "diabetes", "income"]
    names = ["California", "Credit-g", "Heart", "Jungle",
             "Bank", "Blood", "Car", "Diabetes", "Income"]
    # Keep every row and marker while using a compact, paper-width aspect ratio.
    fig, ax = plt.subplots(figsize=(7.0, 2.25))
    flip_color, stable_color = "#B85D27", "#55758A"
    series = []
    for key in order:
        record = summary["datasets"][key]
        data = sorted([r for r in rows if r["dataset"] == key], key=lambda r: r["reference_id"])
        values = np.asarray([float(r["utility"]) for r in data])
        assert len(values) == 24 and len({r["reference_id"] for r in data}) == 24
        np.testing.assert_allclose([values.min(), values.max(), values[0]],
            [record["minimum_utility"], record["maximum_utility"], record["canonical_utility"]], atol=1e-12)
        assert (values.min() < 0 < values.max()) == record["sign_change_across_references"]
        assert np.count_nonzero(values > 0) == record["positive_reference_count"]
        series.append((values, record["canonical_utility"], record["sign_change_across_references"]))
    assert sum(item[2] for item in series) == 4
    assert all(np.ptp(item[0]) > summary["sesoi"] for item in series)
    macro = summary["aligned_reference_index_macro_distribution"]
    macro_values = np.asarray([macro["values"][f"ref_{i:02d}"] for i in range(24)])
    np.testing.assert_allclose(np.mean([item[0] for item in series], axis=0), macro_values, atol=1e-12)
    assert macro_values.min() > 0
    series.append((macro_values, summary["canonical_macro_utility"], False))
    positions = [0.80 * index for index in range(9)] + [7.25]
    ax.axvline(0, color="#303A44", linewidth=1.0, zorder=1)
    for y, (values, canonical, flip) in zip(positions, series):
        color = flip_color if flip else stable_color
        if flip:
            ax.axhspan(y-.34, y+.34, color=flip_color, alpha=.055, linewidth=0)
        ax.hlines(y, values.min(), values.max(), color=color, linewidth=1.25, zorder=2)
        ax.vlines([values.min(), values.max()], y-.10, y+.10, color=color, linewidth=.8)
        # Small deterministic vertical offsets separate nearby markers; only x
        # carries a measured quantity. Every plotted point is an evaluated ref.
        ranks = np.argsort(np.argsort(values, kind="stable"), kind="stable")
        offsets = ((ranks % 3)-1)*.095
        ax.scatter(values, y+offsets, s=10, color=color, alpha=.7, linewidth=0, zorder=3)
        ax.scatter([canonical], [y], marker="D", s=19, facecolor="white",
                   edgecolor="#182B3A", linewidth=.95, zorder=4)
        ax.text(.363, y, f"{np.count_nonzero(values > 0)}/24", fontsize=7.5,
                va="center", ha="center", color=color)
    ax.axhline(6.825, color="#CBD1D6", linewidth=.65)
    ax.set_yticks(positions, names + ["Macro (global)"])
    for label in ax.get_yticklabels():
        label.set_color("#303A44")
    ax.set_ylim(7.82, -.48)
    ax.set_xlim(-.052, .385)
    ax.set_xticks([-.05, 0, .1, .2, .3])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: "0" if v == 0 else f"{v:+.2f}"))
    ax.set_xlabel("Predictive utility (AUROC gain over reference)", fontsize=8)
    ax.tick_params(axis="y", length=0, labelsize=8)
    ax.tick_params(axis="x", labelsize=7.5)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_bounds(-.05, .35)
    legend_handles = [
        Line2D([], [], marker="o", linestyle="None", markersize=3.5,
               markerfacecolor=stable_color, markeredgewidth=0,
               label="Evaluated reference"),
        Line2D([], [], marker="D", linestyle="None", markersize=4.0,
               markerfacecolor="white", markeredgecolor="#182B3A",
               markeredgewidth=.9, label="Name-masked reference"),
    ]
    legend = ax.legend(
        handles=legend_handles, loc="upper left", bbox_to_anchor=(.60, .995),
        frameon=True, facecolor="white", edgecolor="#9AA3AA",
        framealpha=.96, fontsize=7.0, handlelength=.9, handletextpad=.45,
        borderpad=.35, labelspacing=.3,
    )
    legend.get_frame().set_linewidth(.55)
    ax.text(.363, -.71, "Refs > 0", ha="center", va="center", fontsize=7)
    fig.subplots_adjust(left=.13, right=.985, top=.955, bottom=.21)
    stem = mf.OUT_DIR / "figure_reference_sensitivity"
    fig.savefig(stem.with_suffix(".pdf"), facecolor="white")
    fig.savefig(stem.with_suffix(".png"), facecolor="white", dpi=300)
    plt.close(fig)
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    provenance = {
        "sources": {str(p.relative_to(mf.REPO_ROOT)): digest(p) for p in [summary_path, csv_path]},
        "sign_change_datasets": [key for key, item in zip(order, series) if item[2]],
        "all_dataset_spans_exceed_sesoi": summary["sesoi"],
        "macro_definition": "24 index-aligned global constructions, not product space",
        "outputs": {str(stem.with_suffix('.'+ext)): digest(stem.with_suffix('.'+ext)) for ext in ('pdf', 'png')},
    }
    stem.with_name(stem.name+"_provenance.json").write_text(json.dumps(provenance, indent=2)+"\n")
    print("Sources:", summary_path, csv_path, sep="\n  ")
    print("Outputs:", stem.with_suffix(".pdf"), stem.with_suffix(".png"), sep="\n  ")
    print("Verified 216 dataset/reference utilities; 4/9 sign changes; 24/24 macro utilities positive.")


if __name__ == "__main__":
    main()
