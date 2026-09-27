#!/usr/bin/env python3
"""Generate the main three-panel utility-drivers figure.

Panels show schema mismatch, target support, and constituent removal using
stored controlled-benchmark results.  No experiment is run by this script.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", ".runtime")
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

import make_main_figures as mf


PAPER_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PAPER_ROOT.parent
OUT_DIR = PAPER_ROOT / "figures"
STEM = "figure1_utility_drivers_reconstruction"
REDUNDANCY_SUMMARY = (
    REPO_ROOT
    / "experiments/crta_v3_mcr_redundancy_ladder_v1/SUMMARY_V1.json"
)
PDF_METADATA = {
    "Creator": "Matplotlib",
    "Producer": "Matplotlib PDF backend",
    "CreationDate": None,
    "ModDate": None,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def controlled_arm_summaries():
    """Reproduce panels (a) and (b) from the current canonical figure."""
    learners = ("xgb", "histgb", "tabpfn")
    doses = np.asarray([0, 2, 4, 6, 8], dtype=float)

    mismatch_intended = []
    mismatch_reference = []
    for backbone in learners:
        for family in mf.FAMILIES:
            records = mf.measurement_arm_records(backbone, 32, family)
            intended = float(np.mean([record["decode"]["nmse"] for record in records]))
            reference = np.asarray(
                [
                    np.mean([record[f"raw_d{int(dose)}"]["nmse"] for record in records])
                    for dose in doses
                ],
                dtype=float,
            )
            mismatch_intended.append(np.full_like(doses, intended))
            mismatch_reference.append(reference)
    mismatch = mf.summarize_arm_curves(
        np.asarray(mismatch_intended), np.asarray(mismatch_reference)
    )

    support = mf.load_json(
        "experiments/crta_v3_mcr_mismatch_support_ladder_v1/SUMMARY_V1.json"
    )
    support_ks = tuple(int(value) for value in support["supports"])
    if not support["complete"] or support_ks != (32, 64, 128, 256, 512):
        raise RuntimeError("mismatch support ladder is incomplete or has a wrong grid")
    intended_curves = []
    reference_curves = []
    wrong_curves = []
    for backbone in learners:
        for family in mf.FAMILIES:
            section = support["sections"][backbone][family]["absolute_nmse"]
            intended_curves.append(
                [section[str(k)]["intended"]["mean"] for k in support_ks]
            )
            reference_curves.append(
                [section[str(k)]["reference"]["mean"] for k in support_ks]
            )
            wrong_curves.append(
                [section[str(k)]["matched_wrong"]["mean"] for k in support_ks]
            )
    target_support = mf.summarize_arm_curves(
        np.asarray(intended_curves), np.asarray(reference_curves)
    )
    wrong = np.asarray(wrong_curves, dtype=float)
    target_support["matched_wrong"] = (
        wrong.mean(axis=0), wrong.min(axis=0), wrong.max(axis=0)
    )
    if not (
        np.isclose(target_support["supplied"][0][0], mismatch["supplied"][0][-1], atol=1e-3)
        and np.isclose(
            target_support["reference"][0][0], mismatch["reference"][0][-1], atol=1e-3
        )
    ):
        raise RuntimeError("K=32 support endpoint does not reproduce mismatch panel")
    return doses, mismatch, support_ks, target_support


def draw_arm_panel(ax, x, summary, title, xlabel, xticks, xticklabels, *, wrong=False):
    styles = {
        "supplied": (mf.BLUE, "s", "intended"),
        "reference": (mf.ORANGE, "o", "reference"),
        "matched_wrong": (mf.PURPLE, "^", "wrong"),
    }
    arms = ("supplied", "reference", "matched_wrong") if wrong else (
        "supplied", "reference"
    )
    for arm in arms:
        color, marker, _ = styles[arm]
        ax.plot(
            x, summary[arm][0], color=color, marker=marker, markersize=3.8,
            linewidth=1.45, zorder=3,
        )
    intended = summary["supplied"][0]
    reference = summary["reference"][0]
    ax.fill_between(
        x, intended, reference, color="#9db9cc", alpha=0.34, linewidth=0, zorder=2
    )
    ax.set_title(title, loc="left", pad=4)
    ax.set_xlabel(xlabel)
    ax.set_xticks(xticks, xticklabels)
    ax.set_ylim(0.66, 1.06)
    ax.grid(axis="y", color=mf.LIGHT_GRAY, linewidth=0.6, zorder=0)
    return styles


def draw_redundancy_panel(ax) -> dict:
    summary = json.loads(REDUNDANCY_SUMMARY.read_text(encoding="utf-8"))
    expected_metric = (
        "nMSE = MSE/Var(y_query), lower is better; "
        "U = nmse(free) - nmse(op_true), positive = ops help"
    )
    if summary.get("metric") != expected_metric:
        raise RuntimeError("unexpected redundancy-ladder metric definition")

    representative_key = "xgb|pairwise"
    rungs = summary["sections"]["32"]["rung_table"][representative_key]
    rung_keys = sorted(rungs, key=int)
    x = np.asarray([int(key) for key in rung_keys], dtype=int)
    intended = np.asarray(
        [rungs[key]["arm_mean_nmse"]["op_true"] for key in rung_keys],
        dtype=float,
    )
    reference = np.asarray(
        [rungs[key]["arm_mean_nmse"]["free"] for key in rung_keys],
        dtype=float,
    )
    utility = np.asarray(
        [rungs[key]["U"]["mean"] for key in rung_keys], dtype=float
    )
    if not np.array_equal(x, np.arange(7)):
        raise RuntimeError("expected constituent-removal rungs 0 through 6")
    if not np.allclose(reference - intended, utility, atol=1e-12):
        raise RuntimeError("redundancy-ladder arm means do not close to utility")
    expected_endpoints = np.asarray([0.708, 0.741, 0.710, 0.983])
    plotted_endpoints = np.asarray(
        [intended[0], intended[-1], reference[0], reference[-1]]
    )
    if not np.allclose(plotted_endpoints, expected_endpoints, atol=5e-4):
        raise RuntimeError("redundancy-ladder endpoints differ from reported values")
    if not np.allclose(utility[[0, -1]], [0.002, 0.242], atol=5e-4):
        raise RuntimeError("redundancy-ladder utility endpoints differ from reported values")

    ax.fill_between(
        x, intended, reference, color="#9db9cc", alpha=0.34,
        linewidth=0, zorder=2,
    )
    ax.plot(
        x, intended, color=mf.BLUE, marker="s", markersize=3.8,
        linewidth=1.45, zorder=3,
    )
    ax.plot(
        x, reference, color=mf.ORANGE, marker="o", markersize=3.8,
        linewidth=1.45, zorder=3,
    )
    ax.text(
        0.96, 0.94,
        rf"utility: ${utility[0]:.3f}\rightarrow{utility[-1]:.3f}$",
        transform=ax.transAxes, ha="right", va="top", fontsize=5.8,
        color=mf.GRAY,
    )
    ax.set_title(
        "(c) Removing redundant inputs\nweakens the reference", loc="left", pad=4
    )
    ax.set_xlabel("Input columns removed")
    ax.set_xticks(x)
    ax.set_xlim(-0.25, 6.25)
    ax.set_ylim(0.66, 1.06)
    ax.grid(axis="y", color=mf.LIGHT_GRAY, linewidth=0.6, zorder=0)
    return {
        "representative": "pairwise|xgb|K=32",
        "rungs": x.tolist(),
        "n_realizations": int(rungs[rung_keys[0]]["n_realizations"]),
        "intended_nmse": intended.tolist(),
        "reference_nmse": reference.tolist(),
        "utility": utility.tolist(),
    }


def main() -> int:
    doses, mismatch, support_ks, support = controlled_arm_summaries()
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.45))
    styles = draw_arm_panel(
        axes[0], doses, mismatch,
        "(a) Mismatch weakens reference", "Number of mismatched source features",
        doses, [str(int(value)) for value in doses],
    )
    support_x = np.arange(len(support_ks), dtype=float)
    draw_arm_panel(
        axes[1], support_x, support,
        "(b) Target support closes the gap", r"Labeled target rows $K$",
        support_x, ["32", "64", "128", "256", "512"], wrong=True,
    )
    axes[0].set_ylabel("Mean normalized error")
    axes[0].set_xlim(-0.3, 9.45)
    axes[1].set_xlim(-0.15, 5.45)
    redundancy_stats = draw_redundancy_panel(axes[2])
    axes[0].text(
        0.02, 0.97, r"worse $\uparrow$", transform=axes[0].transAxes,
        ha="left", va="top", fontsize=6.2, color=mf.GRAY,
    )
    axes[0].text(
        0.02, 0.03, r"better $\downarrow$", transform=axes[0].transAxes,
        ha="left", va="bottom", fontsize=6.2, color=mf.GRAY,
    )

    # Intended and reference apply to all panels; wrong appears only in (b).
    fig.legend(
        handles=[
            Line2D([0], [0], color=color, marker=marker, linewidth=1.45,
                   markersize=4.0, label=label)
            for color, marker, label in styles.values()
        ],
        frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.015), ncol=3,
        columnspacing=1.25, handletextpad=0.42,
    )
    fig.subplots_adjust(
        bottom=0.245, top=0.78, left=0.078, right=0.992, wspace=0.34
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf = OUT_DIR / f"{STEM}.pdf"
    png = OUT_DIR / f"{STEM}.png"
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.02, metadata=PDF_METADATA)
    fig.savefig(png, dpi=220, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)

    provenance = {
        "figure": STEM,
        "existing_assets_overwritten": True,
        "panel_c": redundancy_stats,
        "inputs": {
            "redundancy_summary": {
                "path": str(REDUNDANCY_SUMMARY),
                "sha256": sha256_file(REDUNDANCY_SUMMARY),
            },
        },
        "outputs": {
            "png": {"path": str(png), "sha256": sha256_file(png)},
            "pdf": {"path": str(pdf), "sha256": sha256_file(pdf)},
        },
    }
    provenance_path = OUT_DIR / f"{STEM}_provenance.json"
    provenance_path.write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(provenance, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
