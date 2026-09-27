#!/usr/bin/env python3
"""Build the main-paper figures from frozen experiment summaries."""

from __future__ import annotations

import glob
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
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np


PAPER_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PAPER_ROOT.parent
OUT_DIR = PAPER_ROOT / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BLUE = "#377eb8"
ORANGE = "#e68613"
GREEN = "#2a9d5b"
PURPLE = "#7b61a8"
GRAY = "#686868"
LIGHT_GRAY = "#ececec"
FAMILIES = ("additive", "pairwise", "sparse")
BACKBONES = ("xgb", "histgb")

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.size": 8,
        "axes.titlesize": 8.5,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 6.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


def load_json(relative_path: str) -> dict:
    with (REPO_ROOT / relative_path).open() as handle:
        return json.load(handle)


def save_figure(fig: plt.Figure, stem: str) -> None:
    fig.savefig(OUT_DIR / f"{stem}.pdf", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(
        OUT_DIR / f"{stem}.png",
        dpi=220,
        bbox_inches="tight",
        pad_inches=0.02,
    )
    plt.close(fig)


def rounded_box(ax, xy, width, height, text, facecolor, fontsize=7.5):
    patch = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        transform=ax.transAxes,
        linewidth=0.8,
        edgecolor="#444444",
        facecolor=facecolor,
    )
    ax.add_patch(patch)
    ax.text(
        xy[0] + width / 2,
        xy[1] + height / 2,
        text,
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=fontsize,
    )


def arrow(ax, start, end):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            transform=ax.transAxes,
            arrowstyle="-|>",
            mutation_scale=9,
            linewidth=0.9,
            color="#555555",
        )
    )


def make_overview() -> None:
    """Conceptual overview for the three-condition evaluation."""
    fig, ax = plt.subplots(figsize=(7.0, 2.35))
    ax.axis("off")

    ax.text(
        0.01,
        0.95,
        "Cross-schema transfer",
        transform=ax.transAxes,
        fontsize=9.0,
        fontweight="bold",
        color="#174a9c",
        va="top",
    )
    rounded_box(
        ax,
        (0.01, 0.61),
        0.18,
        0.23,
        "Source schema A\nSMQ040 · BP_SYS\ncodes 0/1 · mmHg",
        "#eef4fb",
        fontsize=6.4,
    )
    rounded_box(
        ax,
        (0.23, 0.61),
        0.18,
        0.23,
        "Target schema B\nSmoking · SBP\nlabels Yes/No · mmHg",
        "#eef4fb",
        fontsize=6.4,
    )
    arrow(ax, (0.19, 0.725), (0.23, 0.725))
    ax.text(
        0.21,
        0.77,
        "?",
        transform=ax.transAxes,
        ha="center",
        fontsize=12,
        fontweight="bold",
        color="#174a9c",
    )

    rounded_box(
        ax,
        (0.01, 0.28),
        0.12,
        0.18,
        "Measurement (M)\nvalue interpretation",
        "#f7f9fc",
        fontsize=5.2,
    )
    rounded_box(
        ax,
        (0.15, 0.28),
        0.12,
        0.18,
        "Correspondence (C)\nvariable alignment",
        "#f7f9fc",
        fontsize=4.9,
    )
    rounded_box(
        ax,
        (0.29, 0.28),
        0.12,
        0.18,
        "Relation (R)\nstructured relations",
        "#fff3e6",
        fontsize=5.2,
    )

    ax.text(
        0.455,
        0.95,
        "Three-condition evaluation",
        transform=ax.transAxes,
        fontsize=9.0,
        fontweight="bold",
        color="#216627",
        va="top",
    )
    condition_specs = (
        (0.455, "Supplied\n$K^{\\mathrm{S}}$", "#edf7f0", "#216627"),
        (0.635, "Matched-wrong\n$K^{\\mathrm{W}}$", "#fff3e6", "#c54b10"),
        (0.815, "Reference\n$K^{0}$", "#f2f2f2", "#555555"),
    )
    for x, label, facecolor, text_color in condition_specs:
        rounded_box(ax, (x, 0.67), 0.16, 0.17, label, facecolor, fontsize=7.2)
        ax.text(
            x + 0.08,
            0.64,
            "│",
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=7,
            color=text_color,
        )

    rounded_box(
        ax,
        (0.455, 0.48),
        0.52,
        0.11,
        "Same predictive learner · split · budget · seed",
        "#f7f7f7",
        fontsize=6.7,
    )
    rounded_box(
        ax,
        (0.455, 0.29),
        0.25,
        0.12,
        r"Content sensitivity" "\n" r"$Q(S)-Q(W)$",
        "#edf7f0",
        fontsize=6.5,
    )
    rounded_box(
        ax,
        (0.725, 0.29),
        0.25,
        0.12,
        r"Predictive utility" "\n" r"$Q(S)-Q(0)$",
        "#eef4fb",
        fontsize=6.5,
    )
    rounded_box(
        ax,
        (0.455, 0.07),
        0.52,
        0.13,
        "A supplied–matched-wrong gap may reflect benefit,\nmatched-wrong degradation, or both.",
        "#f6f2fb",
        fontsize=6.5,
    )

    save_figure(fig, "overview_v5")


def make_method_pipeline() -> None:
    """Methods proof diagram: freeze, match, evaluate, and decompose."""
    fig, ax = plt.subplots(figsize=(7.0, 4.15))
    ax.axis("off")

    ax.text(
        0.01,
        0.975,
        "1. Freeze semantic records",
        transform=ax.transAxes,
        fontsize=8.7,
        fontweight="bold",
        color="#174a9c",
        va="top",
    )
    rounded_box(
        ax,
        (0.02, 0.79),
        0.23,
        0.13,
        "Documentation\n$M/C$ supported records",
        "#eef4fb",
        fontsize=6.7,
    )
    rounded_box(
        ax,
        (0.28, 0.79),
        0.23,
        0.13,
        "Declared domain priors\n$R$ frozen registry",
        "#fff3e6",
        fontsize=6.7,
    )
    arrow(ax, (0.515, 0.855), (0.59, 0.855))
    rounded_box(
        ax,
        (0.60, 0.79),
        0.37,
        0.13,
        "Frozen $K^M,K^C,K^R$\nconstructed without target labels or performance",
        "#edf7f0",
        fontsize=6.0,
    )

    ax.text(
        0.01,
        0.735,
        "2. Build component-matched conditions",
        transform=ax.transAxes,
        fontsize=8.7,
        fontweight="bold",
        color="#174a9c",
        va="top",
    )
    rounded_box(
        ax,
        (0.02, 0.55),
        0.19,
        0.12,
        "Supplied\n$K^{\\mathrm{S}}$",
        "#edf7f0",
        fontsize=7.4,
    )
    rounded_box(
        ax,
        (0.235, 0.55),
        0.48,
        0.12,
        "Matched-wrong  $K^{\\mathrm{W}}$\nmatch intervention structure\nand predictive interface",
        "#fff3e6",
        fontsize=6.3,
    )
    rounded_box(
        ax,
        (0.74, 0.55),
        0.23,
        0.12,
        "Reference  $K^{0}$\nremove only the tested\ncomponent-specific intervention",
        "#f2f2f2",
        fontsize=5.7,
    )
    chip_specs = (
        (0.02, "M\nsame fields / decoder\n→ alter semantics", "#eef4fb"),
        (0.345, "C\nsame bindings / profile\n→ derange pairing", "#edf7f0"),
        (0.67, "R\nsame relation structure\n→ reverse / derange", "#fff3e6"),
    )
    for x, label, color in chip_specs:
        rounded_box(ax, (x, 0.375), 0.30, 0.115, label, color, fontsize=6.2)

    ax.text(
        0.01,
        0.335,
        "3. Fixed evaluation and exact decomposition",
        transform=ax.transAxes,
        fontsize=8.7,
        fontweight="bold",
        color="#174a9c",
        va="top",
    )
    rounded_box(
        ax,
        (0.02, 0.195),
        0.95,
        0.065,
        "Same source/target cells · preprocessing · learner · split · budget · seed · aggregation weights",
        "#f6f2fb",
        fontsize=6.1,
    )
    equation_specs = (
        (0.02, 0.29, r"$\Delta_{\rm content}=Q(S)-Q(W)$", "#edf7f0"),
        (0.35, 0.29, r"$\Delta_{\rm utility}=Q(S)-Q(0)$", "#eef4fb"),
        (0.68, 0.29, r"$\Delta_{\rm wrong}=Q(0)-Q(W)$", "#fff3e6"),
    )
    for x, width, label, color in equation_specs:
        rounded_box(ax, (x, 0.095), width, 0.075, label, color, fontsize=6.8)
    rounded_box(
        ax,
        (0.19, 0.012),
        0.62,
        0.06,
        r"$\Delta_{\rm content}=\Delta_{\rm utility}+\Delta_{\rm wrong}$"
        "  (exact within paired aggregates; descriptive decomposition)",
        "#f7f7f7",
        fontsize=6.2,
    )

    save_figure(fig, "method_v3")


def mean_survey_arms() -> tuple[list[str], dict[str, np.ndarray]]:
    root = REPO_ROOT / "experiments/crta_v3_survey_label_panel_v1"
    targets = (
        "diabetes_history",
        "hypertension_history",
        "current_smoking_status",
    )
    labels = ["Diabetes", "Hypertension", "Smoking"]
    arms = {"Raw": [], "Correct decoding": [], "Matched-wrong": []}
    arm_keys = {
        "Raw": "raw",
        "Correct decoding": "pipeline_table",
        "Matched-wrong": "placebo_table",
    }
    for target in targets:
        paths = sorted((root / target).glob("seed_*/metrics.json"))
        if len(paths) != 10:
            raise RuntimeError(f"Expected 10 frozen seeds for {target}, found {len(paths)}")
        values = {name: [] for name in arms}
        for path in paths:
            with path.open() as handle:
                metrics = json.load(handle)
            for name, arm in arm_keys.items():
                values[name].append(metrics["auroc"]["256"][arm])
        for name in arms:
            arms[name].append(float(np.mean(values[name])))
    return labels, {name: np.asarray(values) for name, values in arms.items()}


def horizontal_ci(ax, y, record, color, marker="o", filled=True):
    mean = record["mean_gain"] if "mean_gain" in record else record["mean"]
    low, high = record["ci95"]
    ax.errorbar(
        mean,
        y,
        xerr=np.array([[mean - low], [high - mean]]),
        fmt=marker,
        color=color,
        markerfacecolor=color if filled else "white",
        markeredgecolor="white" if filled else color,
        markeredgewidth=0.5,
        markersize=4.5,
        linewidth=1.0,
        capsize=2,
        zorder=3,
    )


def style_effect_axis(ax, labels, xlabel, xlim):
    ax.axvline(0, color="#555555", linewidth=0.8)
    ax.set_yticks(np.arange(len(labels)), labels)
    ax.set_ylim(len(labels) - 0.5, -0.5)
    ax.set_xlim(*xlim)
    ax.set_xlabel(xlabel)
    ax.grid(axis="x", color=LIGHT_GRAY, linewidth=0.6)


def mismatch_u8_by_family(
    relative_root: str, backbone: str, support: int
) -> list[np.ndarray]:
    """Load realization-level full-dose measurement utility by family."""
    base = REPO_ROOT / relative_root
    family_values = []
    for family in FAMILIES:
        values = []
        for path in sorted((base / family).glob("r*/metrics.json")):
            with path.open() as handle:
                record = json.load(handle)
            arms = record["results"][str(support)][backbone]
            values.append(
                float(arms["raw_d8"]["nmse"])
                - float(arms["decode"]["nmse"])
            )
        if len(values) != 20:
            raise RuntimeError(
                f"Expected 20 mismatch realizations for {backbone}, "
                f"K={support}, {family}; found {len(values)}"
            )
        family_values.append(np.asarray(values, dtype=float))
    return family_values


def measurement_arm_records(
    backbone: str, support: int, family: str
) -> list[dict]:
    """Load the 20 frozen absolute-nMSE arm records for one measurement stratum."""
    if support == 32 and backbone in BACKBONES:
        base = REPO_ROOT / "experiments/crta_v3_mcr_mismatch_dose_v1" / family
    elif support == 32 and backbone == "tabpfn":
        base = (
            REPO_ROOT
            / "experiments/crta_v3_mcr_mismatch_dose_tabpfn_v1"
            / family
        )
    elif support == 512 and backbone == "xgb":
        base = REPO_ROOT / "experiments/crta_v3_mcr_mismatch_dose_v1" / family
    elif support == 512 and backbone in ("histgb", "tabpfn"):
        base = (
            REPO_ROOT
            / "experiments/crta_v3_mcr_mismatch_dose_k512_extension_v1"
            / backbone
            / family
        )
    else:
        raise ValueError(f"Unsupported measurement stratum: {backbone}, K={support}")

    records = []
    for path in sorted(base.glob("r*/metrics.json")):
        with path.open() as handle:
            payload = json.load(handle)
        records.append(payload["results"][str(support)][backbone])
    if len(records) != 20:
        raise RuntimeError(
            f"Expected 20 measurement realizations for {backbone}, K={support}, "
            f"{family}; found {len(records)}"
        )
    return records


def summarize_arm_curves(
    supplied_curves: np.ndarray, reference_curves: np.ndarray
) -> dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """Return the mean and across-stratum range for two absolute arm curves."""
    supplied_curves = np.asarray(supplied_curves, dtype=float)
    reference_curves = np.asarray(reference_curves, dtype=float)
    if supplied_curves.shape != reference_curves.shape:
        raise RuntimeError("Supplied/reference change-curve shapes do not match")
    return {
        "supplied": (
            supplied_curves.mean(axis=0),
            supplied_curves.min(axis=0),
            supplied_curves.max(axis=0),
        ),
        "reference": (
            reference_curves.mean(axis=0),
            reference_curves.min(axis=0),
            reference_curves.max(axis=0),
        ),
    }


def make_mismatch_arm_mechanism_figure() -> None:
    """Show which absolute arm moves under the three controlled perturbations."""
    learners = ("xgb", "histgb", "tabpfn")
    doses = np.asarray([0, 2, 4, 6, 8], dtype=float)

    mismatch_supplied = []
    mismatch_reference = []
    for backbone in learners:
        for family in FAMILIES:
            at_32 = measurement_arm_records(backbone, 32, family)
            supplied_32 = float(
                np.mean([record["decode"]["nmse"] for record in at_32])
            )
            raw_32 = np.asarray(
                [
                    np.mean([record[f"raw_d{int(dose)}"]["nmse"] for record in at_32])
                    for dose in doses
                ],
                dtype=float,
            )
            mismatch_supplied.append(np.full_like(doses, supplied_32))
            mismatch_reference.append(raw_32)

    mismatch_summary = summarize_arm_curves(
        np.asarray(mismatch_supplied), np.asarray(mismatch_reference)
    )

    support_ladder = load_json(
        "experiments/crta_v3_mcr_mismatch_support_ladder_v1/SUMMARY_V1.json"
    )
    support_ks = tuple(int(value) for value in support_ladder["supports"])
    if not support_ladder["complete"] or support_ks != (32, 64, 128, 256, 512):
        raise RuntimeError("Mismatch support ladder is incomplete or has a wrong grid")
    support_supplied = []
    support_reference = []
    support_wrong = []
    for backbone in learners:
        for family in FAMILIES:
            section = support_ladder["sections"][backbone][family]["absolute_nmse"]
            support_supplied.append([
                section[str(support)]["intended"]["mean"]
                for support in support_ks
            ])
            support_reference.append([
                section[str(support)]["reference"]["mean"]
                for support in support_ks
            ])
            support_wrong.append([
                section[str(support)]["matched_wrong"]["mean"]
                for support in support_ks
            ])
    support_summary = summarize_arm_curves(
        np.asarray(support_supplied), np.asarray(support_reference)
    )
    support_wrong = np.asarray(support_wrong, dtype=float)
    support_summary["matched_wrong"] = (
        support_wrong.mean(axis=0),
        support_wrong.min(axis=0),
        support_wrong.max(axis=0),
    )
    if not (
        np.isclose(
            support_summary["supplied"][0][0],
            mismatch_summary["supplied"][0][-1], atol=1e-3,
        )
        and np.isclose(
            support_summary["reference"][0][0],
            mismatch_summary["reference"][0][-1], atol=1e-3,
        )
    ):
        raise RuntimeError("K=32 support-ladder endpoint does not reproduce panel (a)")

    ladder = load_json(
        "experiments/crta_v3_mcr_redundancy_ladder_v1/SUMMARY_V1.json"
    )
    if ladder["metric"] != (
        "nMSE = MSE/Var(y_query), lower is better; "
        "U = nmse(free) - nmse(op_true), positive = ops help"
    ):
        raise RuntimeError("Unexpected redundancy-ladder metric definition")
    removal_supplied = []
    removal_reference = []
    for support in ("32", "512"):
        for stratum, rungs in ladder["sections"][support]["rung_table"].items():
            if not stratum.endswith("|pairwise"):
                continue
            rung_keys = sorted(rungs, key=int)
            supplied = np.asarray(
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
            if not np.allclose(reference - supplied, utility, atol=1e-12):
                raise RuntimeError(
                    f"Redundancy-ladder arms do not close for K={support}, {stratum}"
                )
            removal_supplied.append(supplied)
            removal_reference.append(reference)
    removal_summary = summarize_arm_curves(
        np.asarray(removal_supplied), np.asarray(removal_reference)
    )

    panels = (
        {
            "x": doses,
            "summary": mismatch_summary,
            "title": "(a) Add schema mismatch",
            "xlabel": "Discrepant source features",
            "xticks": doses,
            "xticklabels": [str(int(value)) for value in doses],
        },
        {
            "x": np.arange(len(support_ks), dtype=float),
            "summary": support_summary,
            "title": "(b) Then add target examples",
            "xlabel": "Target support",
            "xticks": np.arange(len(support_ks), dtype=int),
            "xticklabels": ["$K=32$", "$64$", "$128$", "$256$", "$512$"],
        },
        {
            "x": np.arange(7, dtype=float),
            "summary": removal_summary,
            "title": "(c) Remove input columns",
            "xlabel": "Relation input columns removed",
            "xticks": np.arange(7, dtype=int),
            "xticklabels": [str(value) for value in range(7)],
        },
    )

    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.25), sharey=False)
    arm_styles = {
        "supplied": (BLUE, "s", "intended"),
        "reference": (ORANGE, "o", "reference"),
        "matched_wrong": (PURPLE, "^", "wrong"),
    }
    for panel_index, (ax, panel) in enumerate(zip(axes, panels)):
        panel_arms = (
            ("supplied", "reference", "matched_wrong")
            if panel_index == 1 else ("supplied", "reference")
        )
        for arm in panel_arms:
            color, marker, _ = arm_styles[arm]
            mean = panel["summary"][arm][0]
            ax.plot(
                panel["x"], mean, color=color, marker=marker, markersize=3.8,
                linewidth=1.45, zorder=3,
            )
        supplied_mean = panel["summary"]["supplied"][0]
        reference_mean = panel["summary"]["reference"][0]
        ax.fill_between(
            panel["x"], supplied_mean, reference_mean,
            color="#9db9cc", alpha=0.34, linewidth=0, zorder=2,
        )
        end_gap = float(reference_mean[-1] - supplied_mean[-1])
        x_end = float(panel["x"][-1])
        y_low = float(supplied_mean[-1])
        y_high = float(reference_mean[-1])
        ax.vlines(
            x_end, y_low, y_high, color="#4d6878", linewidth=0.75, zorder=4
        )
        if panel_index != 1:
            ax.text(
                x_end, (y_low + y_high) / 2, f"  +{end_gap:.2f}",
                ha="left", va="center", fontsize=6.5, fontweight="bold",
                color="#36515f", zorder=5,
            )
        ax.set_title(panel["title"], loc="left", pad=4)
        ax.set_xlabel(panel["xlabel"])
        ax.set_xticks(panel["xticks"], panel["xticklabels"])
        ax.grid(axis="y", color=LIGHT_GRAY, linewidth=0.6, zorder=0)

    axes[0].set_ylabel("Mean normalized error")
    for ax in axes:
        ax.set_ylim(0.66, 1.06)
    axes[0].set_xlim(-0.3, 9.45)
    axes[1].set_xlim(-0.15, 5.45)
    axes[2].set_xlim(-0.25, 7.05)
    axes[0].text(
        0.02, 0.97, r"worse $\uparrow$", transform=axes[0].transAxes,
        ha="left", va="top", fontsize=6.2, color=GRAY,
    )
    axes[0].text(
        0.02, 0.03, r"better $\downarrow$", transform=axes[0].transAxes,
        ha="left", va="bottom", fontsize=6.2, color=GRAY,
    )

    support_supplied_mean = support_summary["supplied"][0]
    support_reference_mean = support_summary["reference"][0]
    support_wrong_mean = support_summary["matched_wrong"][0]
    left_gap = float(support_reference_mean[0] - support_supplied_mean[0])
    axes[1].vlines(
        panels[1]["x"][0], support_supplied_mean[0], support_reference_mean[0],
        color="#4d6878", linewidth=0.75, zorder=4,
    )
    axes[1].text(
        panels[1]["x"][0],
        (support_supplied_mean[0] + support_reference_mean[0]) / 2,
        f"  +{left_gap:.2f}", ha="left", va="center", fontsize=6.2,
        color="#36515f", zorder=5,
    )
    right_x = float(panels[1]["x"][-1])
    right_benefit = float(support_reference_mean[-1] - support_supplied_mean[-1])
    right_damage = float(support_wrong_mean[-1] - support_reference_mean[-1])
    axes[1].text(
        right_x + 0.18,
        (support_supplied_mean[-1] + support_reference_mean[-1]) / 2,
        f"+{right_benefit:.2f} benefit",
        ha="left", va="center", fontsize=5.7, fontweight="bold",
        color="#36515f", zorder=5,
    )
    axes[1].vlines(
        right_x + 0.08, support_reference_mean[-1], support_wrong_mean[-1],
        color=PURPLE, linewidth=0.75, zorder=4,
    )
    axes[1].text(
        right_x + 0.18,
        (support_reference_mean[-1] + support_wrong_mean[-1]) / 2,
        f"+{right_damage:.2f} damage",
        ha="left", va="center", fontsize=5.7, fontweight="bold",
        color=PURPLE, zorder=5,
    )
    fig.legend(
        handles=[
            Line2D([0], [0], color=color, marker=marker, linewidth=1.45,
                   markersize=4.0, label=label)
            for color, marker, label in arm_styles.values()
        ],
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.015),
        ncol=3,
        columnspacing=1.4,
        handletextpad=0.45,
    )
    fig.text(
        0.995, 0.015,
        "Shading: intended--reference = benefit; in (b), "
        "reference--wrong distance = damage from wrong content",
        ha="right", va="bottom", fontsize=5.3, color=GRAY,
    )
    fig.subplots_adjust(bottom=0.25, top=0.82, left=0.080, right=0.985, wspace=0.31)
    save_figure(fig, "figure2_mismatch_resolution_arms")


def make_real_support_reference_figure() -> None:
    """Controlled, TabLLM, and examination target-support attenuation."""
    controlled = load_json(
        "experiments/crta_v3_mcr_mismatch_support_ladder_v1/SUMMARY_V1.json"
    )
    controlled_supports = tuple(map(int, controlled["supports"]))
    if not controlled["complete"] or controlled_supports != (32, 64, 128, 256, 512):
        raise RuntimeError("Unexpected or incomplete controlled support ladder")
    controlled_section = controlled["sections"]["xgb"]["pairwise"]
    controlled_rows = [controlled_section["contrasts"]["benefit"][str(k)]
                       for k in controlled_supports]
    controlled_means = np.asarray([row["mean"] for row in controlled_rows])
    controlled_ci = np.asarray([row["ci95"] for row in controlled_rows])
    absolute = controlled_section["absolute_nmse"]
    np.testing.assert_allclose(controlled_means, [
        absolute[str(k)]["reference"]["mean"] - absolute[str(k)]["intended"]["mean"]
        for k in controlled_supports], atol=1e-12)
    np.testing.assert_allclose(controlled_means[[0, -1]], [.259, .037], atol=.0005)
    tabllm = load_json(
        "experiments/tabllm_ranon_support_ladder_v1/SUMMARY_V1.json"
    )
    tabllm_supports = tuple(int(value) for value in tabllm["shots"])
    if tabllm_supports != (0, 4, 32, 512):
        raise RuntimeError("Unexpected TabLLM support grid")
    if tabllm["verdict"] != "SUPPORTED_WITHIN_FIXED_PANEL":
        raise RuntimeError("Unexpected TabLLM frozen verdict")

    exam = load_json(
        "experiments/crta_v3_exam_support_ladder_v1/SUMMARY_V1.json"
    )
    exam_supports = tuple(int(value) for value in exam["ladder"])
    if exam_supports != (64, 256, 1024):
        raise RuntimeError("Unexpected examination support grid")
    if exam["verdicts"]["scope"] != (
        "class A (six cardiometabolic endpoints) only, per protocol"
    ):
        raise RuntimeError("Unexpected examination support-ladder scope")

    tabllm_x = np.arange(len(tabllm_supports), dtype=float)
    tabllm_rows = [
        tabllm["macro"]["utility"][str(support)]
        for support in tabllm_supports
    ]
    tabllm_means = np.asarray([row["estimate"] for row in tabllm_rows])
    tabllm_lower = tabllm_means - np.asarray(
        [row["bootstrap_ci95"][0] for row in tabllm_rows]
    )
    tabllm_upper = np.asarray(
        [row["bootstrap_ci95"][1] for row in tabllm_rows]
    ) - tabllm_means
    if not np.all(np.diff(tabllm_means) <= 0):
        raise RuntimeError("TabLLM macro utility trajectory is not nonincreasing")
    tabllm_primary = tabllm["primary_decay_0_to_512"]
    positive_decays = sum(
        row["primary_decay_0_to_512"] > 0
        for row in tabllm["datasets"].values()
    )
    monotone_datasets = sum(
        np.all(
            np.diff([
                row["utility"][str(support)]
                for support in tabllm_supports
            ]) <= 0
        )
        for row in tabllm["datasets"].values()
    )
    if (positive_decays, monotone_datasets) != (7, 2):
        raise RuntimeError("Unexpected TabLLM dataset-level diagnostics")

    exam_x = np.arange(len(exam_supports), dtype=float)
    exam_trajectories = exam["absolute_nrmse_trajectories"]
    levels_by_scope = {
        scope: exam["levels"][scope]["utility_S_minus_R"]
        for scope in ("classA_primary", "all13")
    }
    decays_by_scope = {
        scope: exam["decays"][scope][
            "decay_utility_S_minus_R_64_minus_1024"
        ]
        for scope in ("classA_primary", "all13")
    }

    utility_series = {}
    for scope, levels in levels_by_scope.items():
        rows = [levels[str(support)] for support in exam_supports]
        means = np.asarray([row["mean"] for row in rows], dtype=float)
        lower = means - np.asarray([row["ci95"][0] for row in rows], dtype=float)
        upper = np.asarray([row["ci95"][1] for row in rows], dtype=float) - means
        utility_series[scope] = (means, lower, upper)

    for scope in ("classA_primary", "all13"):
        intended = np.asarray([
            exam_trajectories[scope]["S_shared_bridge"][str(support)]
            for support in exam_supports
        ])
        reference = np.asarray([
            exam_trajectories[scope]["R_domain_local"][str(support)]
            for support in exam_supports
        ])
        if not np.allclose(
            reference - intended, utility_series[scope][0], atol=1e-12
        ):
            raise RuntimeError(f"{scope} absolute arms do not close to utility")

    fig, (ax_controlled, ax_tabllm, ax_exam) = plt.subplots(
        1, 3, figsize=(7.4, 2.65)
    )

    def draw_series(ax, x, means, lower, upper, *, color=BLUE,
                    marker="o", linestyle="-", label=None):
        if np.any(lower < 0) or np.any(upper < 0):
            raise RuntimeError("Stored confidence interval does not contain its mean")
        ax.errorbar(x, means, yerr=np.vstack([lower, upper]), color=color,
                    marker=marker, linestyle=linestyle, markersize=3.7,
                    linewidth=1.45, elinewidth=.9, capsize=2.3,
                    markeredgecolor="white", markeredgewidth=.4,
                    label=label, zorder=3)

    controlled_x = np.arange(len(controlled_supports))
    draw_series(ax_controlled, controlled_x, controlled_means,
                controlled_means-controlled_ci[:, 0],
                controlled_ci[:, 1]-controlled_means)
    ax_controlled.set_title("(a) Controlled benchmark", loc="left", pad=7, fontsize=8.5)
    ax_controlled.text(.97, .97, "Pairwise XGB\nLargest measurement difference",
                       transform=ax_controlled.transAxes, ha="right", va="top",
                       fontsize=6.7, color=GRAY)
    ax_controlled.set_ylabel("Predictive utility\n(nMSE reduction)")
    ax_controlled.set_xticks(controlled_x, list(map(str, controlled_supports)))
    ax_controlled.set_xlabel(r"Labeled target rows $n_{\mathrm{target}}$", fontsize=7)
    ax_controlled.set_xlim(-.3, 4.3)
    ax_controlled.set_ylim(-.015, .35)
    ax_controlled.set_yticks([0, .1, .2, .3])

    draw_series(ax_tabllm, tabllm_x, tabllm_means, tabllm_lower, tabllm_upper)
    ax_tabllm.set_title("(b) TabLLM", loc="left", pad=7, fontsize=8.5)
    ax_tabllm.text(.97, .97, "Mean across 9 datasets\nName-masked reference",
                   transform=ax_tabllm.transAxes, ha="right", va="top",
                   fontsize=6.7, color=GRAY)
    ax_tabllm.set_ylabel("Predictive utility\n(AUROC gain)")
    ax_tabllm.set_xticks(tabllm_x, list(map(str, tabllm_supports)))
    ax_tabllm.set_xlabel(r"Labeled adaptation examples $n_{\mathrm{adapt}}$", fontsize=7)
    ax_tabllm.set_xlim(-.3, 3.3)
    ax_tabllm.set_ylim(-.020, .18)
    ax_tabllm.set_yticks([0, .05, .10, .15])

    specs = (
        ("classA_primary", BLUE, "o", "-", "6 targets (replication)", -.035),
        ("all13", GREEN, "D", "--", "13 targets (exploratory)", .035),
    )
    for scope, color, marker, style, label, offset in specs:
        means, lower, upper = utility_series[scope]
        draw_series(ax_exam, exam_x+offset, means, lower, upper,
                    color=color, marker=marker, linestyle=style, label=label)
    ax_exam.set_title("(c) Examination transfer", loc="left", pad=7, fontsize=8)
    ax_exam.set_ylabel("Predictive utility\n(SD-normalized RMSE reduction)")
    ax_exam.set_xticks(exam_x, list(map(str, exam_supports)))
    ax_exam.set_xlabel(r"Labeled target rows $n_{\mathrm{target}}$", fontsize=7)
    ax_exam.set_xlim(-.25, 2.25)
    ax_exam.set_ylim(-.006, .125)
    ax_exam.set_yticks([0, .04, .08, .12])
    ax_exam.legend(loc="upper right", frameon=False, fontsize=6,
                   handlelength=1.4, handletextpad=.4, borderaxespad=.15)

    for ax in (ax_controlled, ax_tabllm, ax_exam):
        ax.axhline(0, color=GRAY, linewidth=.65, zorder=1)
        ax.grid(axis="y", color=LIGHT_GRAY, linewidth=.6)
        ax.set_axisbelow(True)
        ax.tick_params(labelsize=7)
    fig.subplots_adjust(bottom=.23, top=.86, left=.075, right=.99, wspace=.55)
    save_figure(fig, "figure2_real_support_reference")


def make_mismatch_figure() -> None:
    mismatch = load_json(
        "experiments/crta_v3_mcr_mismatch_dose_v1/SUMMARY_V1.json"
    )
    mismatch_tabpfn = load_json(
        "experiments/crta_v3_mcr_mismatch_dose_tabpfn_v1/SUMMARY_V1.json"
    )
    mismatch_k512 = load_json(
        "experiments/crta_v3_mcr_mismatch_dose_k512_extension_v1/SUMMARY_V1.json"
    )
    doses = np.asarray(mismatch["doses"], dtype=float)
    series = (
        ("XGB", "tree", "xgb_K32", BLUE, "o", "-"),
        ("HistGB", "tree", "histgb_K32", ORANGE, "s", "-"),
        ("TabPFN", "tabpfn", None, GREEN, "D", "-"),
        ("XGB", "tree", "xgb_K512", BLUE, "o", "--"),
        ("HistGB", "extension", "histgb_K512", ORANGE, "s", "--"),
        ("TabPFN", "extension", "tabpfn_K512", GREEN, "D", "--"),
    )

    fig = plt.figure(figsize=(7.0, 2.05))
    grid = fig.add_gridspec(
        1, 2, width_ratios=(1.22, 1.0), wspace=0.34
    )
    ax_m = fig.add_subplot(grid[0, 0])
    ax_ladder = fig.add_subplot(grid[0, 1])

    for learner, source, key, color, marker, linestyle in series:
        if source == "tabpfn":
            family_curves = np.asarray(
                [mismatch_tabpfn["sections"][family]["mean_U_by_dose"]
                 for family in FAMILIES], dtype=float)
        elif source == "tree":
            family_curves = np.asarray(
                [mismatch["sections"][key][family]["mean_U_by_dose"]
                 for family in FAMILIES], dtype=float)
        else:
            family_curves = np.asarray(
                [mismatch_k512["sections"][key][family]["mean_U_by_dose"]
                 for family in FAMILIES], dtype=float)
        mean_curve = family_curves.mean(axis=0)
        ax_m.plot(
            doses,
            mean_curve,
            color=color,
            marker=marker,
            markersize=3.7,
            linewidth=1.25,
            linestyle=linestyle,
            zorder=2,
        )

    ax_m.axhline(0, color="#555555", linewidth=0.8)
    ax_m.set_xticks(doses.astype(int))
    ax_m.set_xlim(-0.25, 8.25)
    ax_m.set_ylim(-0.012, 0.30)
    ax_m.set_xlabel("Discrepant source features $d$")
    ax_m.set_ylabel(r"$U_M(d)$ ($\Delta Q$)")
    ax_m.grid(axis="y", color=LIGHT_GRAY, linewidth=0.6)
    ax_m.set_title("(a) Mismatch dose-response", loc="left", pad=4)
    ax_m.legend(
        handles=[
            Line2D([0], [0], color=BLUE, marker="o", linewidth=1.2,
                   label="XGB"),
            Line2D([0], [0], color=ORANGE, marker="s", linewidth=1.2,
                   label="HistGB"),
            Line2D([0], [0], color=GREEN, marker="D", linewidth=1.2,
                   label="TabPFN"),
            Line2D([0], [0], color=GRAY, linewidth=1.2, linestyle="-",
                   label="$K=32$"),
            Line2D([0], [0], color=GRAY, linewidth=1.2, linestyle="--",
                   label="$K=512$"),
        ],
        frameon=False,
        loc="upper left",
        ncol=2,
        columnspacing=0.65,
        handletextpad=0.38,
        borderaxespad=0.15,
        labelspacing=0.22,
        fontsize=5.7,
    )

    ladder = load_json(
        "experiments/crta_v3_mcr_redundancy_ladder_v1/SUMMARY_V1.json"
    )
    if ladder["metric"] != (
        "nMSE = MSE/Var(y_query), lower is better; "
        "U = nmse(free) - nmse(op_true), positive = ops help"
    ):
        raise RuntimeError("Unexpected redundancy-ladder metric definition")
    rungs = ladder["sections"]["32"]["rung_table"]["xgb|pairwise"]
    rung_keys = sorted(rungs, key=int)
    rung_x = np.asarray([int(key) for key in rung_keys], dtype=int)
    free_nmse = np.asarray(
        [rungs[key]["arm_mean_nmse"]["free"] for key in rung_keys],
        dtype=float,
    )
    supplied_nmse = np.asarray(
        [rungs[key]["arm_mean_nmse"]["op_true"] for key in rung_keys],
        dtype=float,
    )
    utility = np.asarray(
        [rungs[key]["U"]["mean"] for key in rung_keys], dtype=float
    )
    if not np.allclose(free_nmse - supplied_nmse, utility, atol=1e-12):
        raise RuntimeError("Ladder arm means do not subtract to utility")
    expected_endpoints = np.asarray([0.710, 0.983, 0.708, 0.741])
    plotted_endpoints = np.asarray(
        [free_nmse[0], free_nmse[-1], supplied_nmse[0], supplied_nmse[-1]]
    )
    if not np.allclose(plotted_endpoints, expected_endpoints, atol=5e-4):
        raise RuntimeError("Ladder endpoints do not match the reported values")

    ax_ladder.fill_between(
        rung_x,
        supplied_nmse,
        free_nmse,
        color="#8fb3c9",
        alpha=0.34,
        linewidth=0,
        label="shaded gap = benefit",
        zorder=1,
    )
    ax_ladder.plot(
        rung_x,
        free_nmse,
        color=ORANGE,
        marker="o",
        markersize=3.5,
        linewidth=1.35,
        label="reference (no computed value)",
        zorder=3,
    )
    ax_ladder.plot(
        rung_x,
        supplied_nmse,
        color=BLUE,
        marker="s",
        markersize=3.2,
        linewidth=1.35,
        label="supplied (computed value)",
        zorder=3,
    )
    for value, xy, offset, color in (
        (free_nmse[0], (rung_x[0], free_nmse[0]), (4, 6), ORANGE),
        (supplied_nmse[0], (rung_x[0], supplied_nmse[0]), (4, -10), BLUE),
        (free_nmse[-1], (rung_x[-1], free_nmse[-1]), (-3, 5), ORANGE),
        (supplied_nmse[-1], (rung_x[-1], supplied_nmse[-1]), (-3, -11), BLUE),
    ):
        ax_ladder.annotate(
            f"{value:.3f}",
            xy,
            xytext=offset,
            textcoords="offset points",
            ha="right" if xy[0] == rung_x[-1] else "left",
            fontsize=5.8,
            color=color,
        )
    ax_ladder.set_xticks(rung_x)
    ax_ladder.set_xlim(-0.25, 6.25)
    ax_ladder.set_ylim(0.68, 1.02)
    ax_ladder.set_yticks([0.7, 0.8, 0.9, 1.0])
    ax_ladder.set_xlabel("Input columns removed")
    ax_ladder.set_ylabel("Mean nMSE (lower is better)")
    ax_ladder.grid(axis="y", color=LIGHT_GRAY, linewidth=0.6, zorder=0)
    ax_ladder.set_title("(b) Removing input columns", loc="left", pad=4)
    ax_ladder.legend(
        frameon=False,
        loc="upper left",
        handlelength=1.4,
        handletextpad=0.35,
        borderaxespad=0.15,
        labelspacing=0.22,
        fontsize=5.2,
    )

    fig.subplots_adjust(bottom=0.25, top=0.90, left=0.070, right=0.995)
    save_figure(fig, "figure2_mismatch_resolution")


def bootstrap_mean_ci(values: np.ndarray, seed: int) -> tuple[float, list[float]]:
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(10_000, len(values)))
    means = values[indices].mean(axis=1)
    low, high = np.quantile(means, (0.025, 0.975))
    return float(values.mean()), [float(low), float(high)]


def internal_integrity_values(family: str, backbone: str, alpha: float) -> np.ndarray:
    paths = sorted(
        glob.glob(
            str(
                REPO_ROOT
                / f"experiments/crta_v3_mcr_source_informativeness_ladder_v1/"
                f"{family}/r*/metrics.json"
            )
        )
    )
    if len(paths) != 20:
        raise RuntimeError(f"Expected 20 integrity realizations for {family}")
    values = []
    alpha_key = f"{alpha:.2f}"
    for path in paths:
        with open(path) as handle:
            result = json.load(handle)["results"][alpha_key][backbone]
        nmse = {arm: result[arm]["nmse"] for arm in result}
        interaction = (
            -nmse["m1c1rf"]
            + nmse["m1c0rf"]
            + nmse["m0c1rf"]
            - nmse["m0c0rf"]
        )
        values.append(interaction)
    return np.asarray(values)


def integrity_record(
    family: str,
    backbone: str,
    alpha: float,
    factorial: dict,
    null_source: dict,
    ladder: dict,
) -> tuple[float, list[float]]:
    if alpha == 0:
        record = factorial["primary"][f"{backbone}_K32"]["P4_MC_interaction"][
            family
        ]
        return record["mean"], record["ci95"]
    if alpha == 1:
        record = null_source["results"][backbone][family]
        return record["mean"], record["ci95"]

    values = internal_integrity_values(family, backbone, alpha)
    seed = 20260820 + FAMILIES.index(family) * 10 + BACKBONES.index(backbone)
    mean, ci = bootstrap_mean_ci(values, seed)
    expected = ladder["strata"][family][backbone]["mean_I_MC_by_alpha"][f"{alpha:.2f}"]
    if not np.isclose(mean, expected, atol=1e-12):
        raise RuntimeError("Integrity-ladder reconstruction does not match frozen summary")
    return mean, ci


def make_source_integrity_appendix_figure() -> None:
    factorial = load_json(
        "experiments/crta_v3_mcr_factorial_semisynth_v1/SUMMARY_V1.json"
    )
    tabpfn = load_json(
        "experiments/crta_v3_mcr_factorial_tabpfn_v1/SUMMARY_V1.json"
    )
    null_source = load_json(
        "experiments/crta_v3_mcr_null_source_v1/SUMMARY_V1.json"
    )
    ladder = load_json(
        "experiments/crta_v3_mcr_source_informativeness_ladder_v1/SUMMARY_V1.json"
    )

    fig = plt.figure(figsize=(7.0, 4.25))
    grid = fig.add_gridspec(2, 1, height_ratios=(1.05, 1.2), hspace=0.62)
    ax_forest = fig.add_subplot(grid[0, 0])

    series = [
        ("XGB, K=32", BLUE, "o", True, "xgb_K32"),
        ("HistGB, K=32", ORANGE, "s", True, "histgb_K32"),
        ("TabPFN, K=32", GREEN, "D", True, "tabpfn"),
        ("XGB, K=512", BLUE, "o", False, "xgb_K512"),
        ("HistGB, K=512", ORANGE, "s", False, "histgb_K512"),
    ]
    base_y = {"additive": 2.0, "pairwise": 1.0, "sparse": 0.0}
    offsets = np.linspace(-0.27, 0.27, len(series))
    for series_index, (
        offset,
        (label, color, marker, filled, key),
    ) in enumerate(zip(offsets, series)):
        for family in FAMILIES:
            if key == "tabpfn":
                record = tabpfn["sections"]["T3_MC_interaction"][family]
            else:
                record = factorial["primary"][key]["P4_MC_interaction"][family]
            mean = record["mean"]
            low, high = record["ci95"]
            ax_forest.errorbar(
                mean,
                base_y[family] + offset,
                xerr=np.array([[mean - low], [high - mean]]),
                fmt=marker,
                color=color,
                markerfacecolor=color if filled else "white",
                markeredgecolor=color,
                markersize=4,
                linewidth=0.9,
                capsize=1.5,
                label=label.split(",")[0]
                if family == "additive" and series_index < 3
                else None,
            )
    ax_forest.axvline(0, color="#555555", linewidth=0.8)
    ax_forest.set_yticks([2, 1, 0], ["Additive", "Pairwise", "Sparse"])
    ax_forest.set_ylim(-0.48, 2.48)
    ax_forest.set_xlim(-0.02, 0.61)
    ax_forest.set_xlabel(r"$I_{MC}$")
    ax_forest.grid(axis="x", color=LIGHT_GRAY, linewidth=0.6)
    ax_forest.set_title(
        "(a) Non-additive interaction across all prespecified strata",
        loc="left",
        pad=5,
    )
    ax_forest.legend(
        frameon=False,
        ncol=3,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.30),
        handletextpad=0.35,
        columnspacing=0.9,
    )

    lower = grid[1, 0].subgridspec(1, 3, wspace=0.22)
    alphas = np.asarray([0.0, 0.25, 0.5, 0.75, 1.0])
    family_titles = ("(b) Additive", "Pairwise", "Sparse")
    for panel_index, (family, title) in enumerate(zip(FAMILIES, family_titles)):
        ax = fig.add_subplot(lower[0, panel_index])
        for backbone, color, marker, label in (
            ("xgb", BLUE, "o", "XGB"),
            ("histgb", ORANGE, "s", "HistGB"),
        ):
            records = [
                integrity_record(
                    family,
                    backbone,
                    alpha,
                    factorial,
                    null_source,
                    ladder,
                )
                for alpha in alphas
            ]
            means = np.asarray([record[0] for record in records])
            lows = np.asarray([record[1][0] for record in records])
            highs = np.asarray([record[1][1] for record in records])
            ax.errorbar(
                alphas,
                means,
                yerr=np.vstack((means - lows, highs - means)),
                color=color,
                marker=marker,
                markersize=3.5,
                linewidth=1.15,
                capsize=1.5,
                label=label,
            )
        ax.axhline(0, color="#555555", linewidth=0.8)
        ax.axvspan(0.75, 1.0, color="#f1f1f1", zorder=-2)
        ax.set_xlim(-0.03, 1.03)
        ax.set_ylim(-0.15, 0.56)
        ax.set_xticks(alphas)
        ax.set_title(title, pad=4)
        ax.set_xlabel(r"Source-label corruption $\alpha$")
        ax.grid(axis="y", color=LIGHT_GRAY, linewidth=0.6)
        if panel_index == 0:
            ax.set_ylabel(r"$I_{MC}(\alpha)$")
            ax.legend(frameon=False, loc="lower left")
        else:
            ax.tick_params(labelleft=False)

    fig.subplots_adjust(top=0.92, bottom=0.09)
    save_figure(fig, "figureA_mc_source_integrity")


def paired_relation_interface_record(
    family: str,
    backbone: str,
    support: str,
    arm: str,
    contrast_name: str,
    factorial_summary: dict,
) -> dict:
    paths = sorted(
        REPO_ROOT.glob(
            f"experiments/crta_v3_mcr_factorial_semisynth_v1/"
            f"primary/{family}/r*/metrics.json"
        )
    )
    if len(paths) != 20:
        raise RuntimeError(
            f"Expected 20 factorial cells for {family}, found {len(paths)}"
        )
    values = []
    for path in paths:
        with path.open() as handle:
            arms = json.load(handle)["results"][support][backbone]
        # Q = -nMSE, so Q(arm) - Q(free) = nMSE(free) - nMSE(arm).
        values.append(arms["m1c1rf"]["nmse"] - arms[arm]["nmse"])
    values = np.asarray(values, dtype=float)

    seed_key = f"{backbone}|{support}|{contrast_name}|{family}"
    seed = int(
        hashlib.sha256(
            f"mcr_summary_r2|20260820|{seed_key}".encode()
        ).hexdigest()[:8],
        16,
    )
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(10_000, len(values)))
    bootstrap_means = values[indices].mean(axis=1)
    record = {
        "mean": float(values.mean()),
        "ci95": [
            float(np.quantile(bootstrap_means, 0.025)),
            float(np.quantile(bootstrap_means, 0.975)),
        ],
    }

    frozen = factorial_summary["primary"][f"{backbone}_K{support}"][
        contrast_name
    ][family]
    if not (
        np.isclose(record["mean"], frozen["mean"], atol=1e-12)
        and np.allclose(record["ci95"], frozen["ci95"], atol=1e-12)
    ):
        raise RuntimeError(
            "Paired common-reference reconstruction does not match the "
            "frozen factorial summary"
        )
    return record


def make_examination_generalization_figure() -> None:
    """Five-row forest for the frozen-six to expanded-thirteen dissociation."""
    summary = load_json(
        "experiments/crta_v3_exam_reference_sensitivity_v2/SUMMARY_V1.json"
    )
    six = summary["contrasts"]["class_A_original_six"]
    thirteen = summary["contrasts"]["full_13_endpoints"]
    rows = (
        ("6 endpoints · content", six["content_S_minus_W"], BLUE, "o", True),
        ("6 endpoints · utility", six["utility_S_minus_R_domain_local"],
         ORANGE, "s", True),
        ("6 endpoints · reference $-$ wrong",
         six["coherence_R_domain_local_minus_W"], PURPLE, "D", True),
        ("13 endpoints · content", thirteen["content_S_minus_W"],
         BLUE, "o", True),
        ("13 endpoints · utility",
         thirteen["utility_S_minus_R_domain_local"], ORANGE, "s", False),
    )
    y_positions = np.asarray([0.0, 1.0, 2.0, 3.35, 4.35])
    fig, ax = plt.subplots(figsize=(5.2, 1.62))
    for y, (label, record, color, marker, filled) in zip(y_positions, rows):
        horizontal_ci(ax, y, record, color, marker=marker, filled=filled)
    ax.axvline(0, color="#555555", linewidth=0.8)
    ax.axhline(2.68, color="#b8b8b8", linewidth=0.8)
    ax.set_yticks(y_positions, [row[0] for row in rows])
    ax.set_ylim(4.85, -0.50)
    ax.set_xlim(-0.025, 0.135)
    ax.set_xticks([-0.02, 0.00, 0.04, 0.08, 0.12])
    ax.set_xlabel(r"Gain in normalized-RMSE (positive favors supplied)")
    ax.grid(axis="x", color=LIGHT_GRAY, linewidth=0.6)
    fig.subplots_adjust(bottom=0.28, top=0.97, left=0.39, right=0.985)
    save_figure(fig, "figure_examination_generalization")


def make_correspondence_appendix_figure() -> None:
    """Generate the canonical appendix-native correspondence forest."""
    from make_appendix_assets import plot_correspondence_interfaces

    plot_correspondence_interfaces()


def draw_transtab_decomposition(ax, transtab: dict) -> None:
    """Draw the full six-row TransTab four-arm decomposition on one axis."""
    rows = (
        ("Additive", "32", "additive", 0.0),
        ("Pairwise", "32", "pairwise", 1.0),
        ("Sparse", "32", "sparse", 2.0),
        ("Additive", "512", "additive", 3.65),
        ("Pairwise", "512", "pairwise", 4.65),
        ("Sparse", "512", "sparse", 5.65),
    )
    specs = (
        ("name_token_content_beyond_shared_identity", BLUE),
        ("shared_identity_bridge", ORANGE),
        ("false_bridge", PURPLE),
    )
    for _, support, family, y in rows:
        panel = transtab["results"][support]
        components = (
            panel["name_token_content_beyond_shared_identity"][family]["mean"],
            panel["shared_identity_bridge"][family]["mean"],
            -panel["false_bridge"][family]["mean"],
        )
        positive_left = 0.0
        negative_left = 0.0
        for value, (_, color) in zip(components, specs):
            if value >= 0:
                ax.barh(
                    y, value, left=positive_left, height=0.56,
                    color=color, edgecolor="white", linewidth=0.45, zorder=2,
                )
                positive_left += value
            else:
                ax.barh(
                    y, -value, left=negative_left + value, height=0.56,
                    color=color, edgecolor="white", linewidth=0.45, zorder=2,
                )
                negative_left += value
        total = float(sum(components))
        frozen_total = panel["conventional_content_gap"][family]["mean"]
        if not np.isclose(total, frozen_total, atol=1e-12):
            raise RuntimeError("TransTab plotted decomposition does not close")
        ax.plot(
            total, y, marker="D", markersize=4.4, color="#202020",
            markerfacecolor="white", markeredgewidth=0.8, zorder=4,
        )
    ax.axvline(0, color="#555555", linewidth=0.8, zorder=1)
    ax.axhline(2.83, color="#bbbbbb", linewidth=0.7)
    ax.set_yticks(
        [row[3] for row in rows],
        [f"$K={row[1]}$ · {row[0]}" for row in rows],
    )
    ax.set_ylim(6.20, -0.82)
    ax.set_xlim(-0.055, 0.61)
    ax.set_xticks([0.0, 0.2, 0.4, 0.6])
    ax.set_xlabel(r"Signed contribution to correct--wrong gap ($\Delta Q$)")
    ax.grid(axis="x", color=LIGHT_GRAY, linewidth=0.6, zorder=0)
    ax.legend(
        handles=[
            Line2D([0], [0], color=BLUE, marker="s", linewidth=0,
                   markersize=6.5, label="names beyond identifier"),
            Line2D([0], [0], color=ORANGE, marker="s", linewidth=0,
                   markersize=6.5, label="shared identifier"),
            Line2D([0], [0], color=PURPLE, marker="s", linewidth=0,
                   markersize=6.5, label="false bridge"),
            Line2D([0], [0], color="#202020", marker="D", linewidth=0,
                   markerfacecolor="white", markersize=4.2,
                   label="correct--wrong gap"),
        ],
        frameon=False,
        loc="lower center",
        bbox_to_anchor=(0.50, 1.01),
        ncol=4,
        columnspacing=0.9,
        handletextpad=0.25,
        fontsize=5.9,
    )


def make_transtab_bridge_figure() -> None:
    transtab = load_json(
        "experiments/crta_v3_mcr_transtab_bridge_decomposition_v1/SUMMARY_V1.json"
    )
    fig, ax = plt.subplots(figsize=(7.0, 1.80))
    draw_transtab_decomposition(ax, transtab)
    fig.subplots_adjust(bottom=0.22, top=0.82, left=0.145, right=0.985)
    save_figure(fig, "figure_transtab_bridge")


def make_composition_interface_figure() -> None:
    transtab = load_json(
        "experiments/crta_v3_mcr_transtab_bridge_decomposition_v1/SUMMARY_V1.json"
    )
    fig = plt.figure(figsize=(7.0, 4.20))
    grid = fig.add_gridspec(
        2,
        2,
        height_ratios=(0.72, 1.48),
        width_ratios=(1.0, 1.06),
        hspace=0.62,
        wspace=0.40,
    )
    ax_c_cont = fig.add_subplot(grid[0, 0])
    ax_c_survey = fig.add_subplot(grid[0, 1])
    ax_transtab = fig.add_subplot(grid[1, :])
    layer = load_json(
        "experiments/crta_v3_m1m2_layer_ladder_v1/SUMMARY_V1.json"
    )
    exam_reference = load_json(
        "experiments/crta_v3_exam_no_bridge_reference_v1/SUMMARY_V1.json"
    )["contrasts"]
    stage = load_json(
        "experiments/crta_v3_m1m2_stage_factorial_v1/SUMMARY_V1.json"
    )
    hist = load_json(
        "experiments/crta_v3_binding_backbone_generality_v1/SUMMARY_V1.json"
    )
    continuous_records = (
        exam_reference["content_S_minus_W"],
        exam_reference["utility_S_minus_R"],
        layer["R2_grouping_vs_placebo"],
    )
    continuous_labels = ["Binding content", "Bridge utility", "Aggregation content"]
    continuous_styles = ((BLUE, True), (BLUE, False), (ORANGE, True))
    for y, (record, (color, filled)) in enumerate(
            zip(continuous_records, continuous_styles)):
        horizontal_ci(ax_c_cont, y, record, color, "o", filled)
    style_effect_axis(
        ax_c_cont,
        continuous_labels,
        r"$\Delta$ normalized-RMSE",
        (-0.025, 0.135),
    )
    ax_c_cont.set_title(
        "(a) Exam correspondence · XGB", loc="left", pad=4, fontsize=8.0
    )

    survey_records = {
        "XGB": {
            "content": stage["S2_binding_content"],
            "utility": stage["desc_columns_at_stage"],
        },
        "HistGB": {
            "content": hist["sections"]["K256"]["S5_P1_binding_content"],
            "utility": hist["sections"]["K256"]["S5_P2_columns_on_stage"],
        },
    }
    learner_colors = {"XGB": BLUE, "HistGB": ORANGE}
    learner_markers = {"XGB": "o", "HistGB": "s"}
    survey_order = ("XGB", "HistGB")
    for row, learner in enumerate(survey_order):
        records = survey_records[learner]
        for offset, estimand, filled in (
            (-0.10, "content", True),
            (+0.10, "utility", False),
        ):
            horizontal_ci(
                ax_c_survey,
                row + offset,
                records[estimand],
                learner_colors[learner],
                marker=learner_markers[learner],
                filled=filled,
            )
    style_effect_axis(
        ax_c_survey,
        list(survey_order),
        r"$\Delta$ AUROC",
        (-0.025, 0.105),
    )
    ax_c_survey.set_ylim(1.42, -0.42)
    ax_c_survey.set_title(
        "(b) Survey correspondence · $K=256$",
        loc="left",
        pad=4,
        fontsize=8.0,
    )
    ax_c_survey.legend(
        handles=[
            Line2D([0], [0], color=GRAY, marker="o", linewidth=0,
                   markerfacecolor=GRAY, markeredgecolor="white",
                   label="content"),
            Line2D([0], [0], color=GRAY, marker="o", linewidth=0,
                   markerfacecolor="white", markeredgecolor=GRAY,
                   label="utility"),
        ],
        frameon=False,
        loc="center",
        bbox_to_anchor=(0.53, 0.50),
        ncol=2,
        columnspacing=0.45,
        handletextpad=0.25,
        fontsize=5.2,
    )

    transtab_rows = (
        ("Additive", "32", "additive", 0.0),
        ("Pairwise", "32", "pairwise", 1.0),
        ("Sparse", "32", "sparse", 2.0),
        ("Additive", "512", "additive", 3.65),
        ("Pairwise", "512", "pairwise", 4.65),
        ("Sparse", "512", "sparse", 5.65),
    )
    component_specs = (
        ("name_token_content_beyond_shared_identity", BLUE, "names beyond identifier"),
        ("shared_identity_bridge", ORANGE, "shared identifier"),
        ("false_bridge", PURPLE, "false bridge"),
    )
    for _, support, family, y in transtab_rows:
        panel = transtab["results"][support]
        components = (
            panel["name_token_content_beyond_shared_identity"][family]["mean"],
            panel["shared_identity_bridge"][family]["mean"],
            -panel["false_bridge"][family]["mean"],
        )
        positive_left = 0.0
        negative_left = 0.0
        for value, (_, color, _) in zip(components, component_specs):
            if value >= 0:
                ax_transtab.barh(
                    y, value, left=positive_left, height=0.56,
                    color=color, edgecolor="white", linewidth=0.45,
                    zorder=2,
                )
                positive_left += value
            else:
                ax_transtab.barh(
                    y, -value, left=negative_left + value, height=0.56,
                    color=color, edgecolor="white", linewidth=0.45,
                    zorder=2,
                )
                negative_left += value
        total = float(sum(components))
        frozen_total = panel["conventional_content_gap"][family]["mean"]
        if not np.isclose(total, frozen_total, atol=1e-12):
            raise RuntimeError("TransTab plotted decomposition does not close")
        ax_transtab.plot(
            total, y, marker="D", markersize=4.2, color="#202020",
            markerfacecolor="white", markeredgewidth=0.8, zorder=4,
        )
    ax_transtab.axvline(0, color="#555555", linewidth=0.8, zorder=1)
    ax_transtab.axhline(2.83, color="#bbbbbb", linewidth=0.7)
    ax_transtab.set_yticks(
        [row[3] for row in transtab_rows],
        [f"$K={row[1]}$ · {row[0]}" for row in transtab_rows],
    )
    ax_transtab.set_ylim(6.20, -0.82)
    ax_transtab.set_xlim(-0.055, 0.61)
    ax_transtab.set_xticks([0.0, 0.2, 0.4, 0.6])
    ax_transtab.set_xlabel(r"Signed contribution to correct--wrong gap ($\Delta Q$)")
    ax_transtab.grid(axis="x", color=LIGHT_GRAY, linewidth=0.6, zorder=0)
    ax_transtab.set_title(
        "(c) TransTab: what the conventional correspondence gap contains",
        loc="left",
        pad=4,
        fontsize=8.2,
    )
    ax_transtab.legend(
        handles=[
            Line2D([0], [0], color=BLUE, marker="s", linewidth=0,
                   markersize=6.5, label="names beyond identifier"),
            Line2D([0], [0], color=ORANGE, marker="s", linewidth=0,
                   markersize=6.5, label="shared identifier"),
            Line2D([0], [0], color=PURPLE, marker="s", linewidth=0,
                   markersize=6.5, label="false bridge"),
            Line2D([0], [0], color="#202020", marker="D", linewidth=0,
                   markerfacecolor="white", markersize=4.2,
                   label="correct--wrong gap"),
        ],
        frameon=False,
        loc="lower center",
        bbox_to_anchor=(0.50, -0.33),
        ncol=4,
        columnspacing=0.8,
        handletextpad=0.25,
        fontsize=5.7,
    )

    fig.subplots_adjust(bottom=0.17, top=0.96, left=0.105, right=0.985)
    save_figure(fig, "figure3_composition_interface")


def main() -> None:
    make_overview()
    make_method_pipeline()
    make_mismatch_figure()
    make_mismatch_arm_mechanism_figure()
    make_real_support_reference_figure()
    make_examination_generalization_figure()
    make_correspondence_appendix_figure()
    make_transtab_bridge_figure()


if __name__ == "__main__":
    main()
