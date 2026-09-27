#!/usr/bin/env python3
"""Build appendix figures and LaTeX tables from frozen experiment artifacts.

The script reads stored summaries and, for the reconstruction scatter, the
stored realization-by-rung proxy rows.  It does not refit models or recompute
inferential units.  Generated files live under ``figures/`` and ``generated/``.
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", ".runtime")
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np


PAPER_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PAPER_ROOT.parent
FIG_DIR = PAPER_ROOT / "figures"
GEN_DIR = PAPER_ROOT / "generated"
FIG_DIR.mkdir(parents=True, exist_ok=True)
GEN_DIR.mkdir(parents=True, exist_ok=True)

BLUE = "#377eb8"
ORANGE = "#e68613"
GREEN = "#2a9d5b"
PURPLE = "#7b61a8"
GRAY = "#686868"
LIGHT_GRAY = "#ececec"
RED = "#c44e52"
FAMILIES = ("additive", "pairwise", "sparse")
FAMILY_LABEL = {"additive": "Additive", "pairwise": "Pairwise", "sparse": "Sparse"}

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.size": 8,
        "axes.titlesize": 8.5,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 6.7,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


def load(relative_path: str) -> dict:
    return json.loads((REPO_ROOT / relative_path).read_text())


def save(fig: plt.Figure, stem: str) -> None:
    fig.savefig(FIG_DIR / f"{stem}.pdf", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(FIG_DIR / f"{stem}.png", dpi=220, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def effect(value: float, digits: int = 3) -> str:
    if value is None or not math.isfinite(float(value)):
        return "---"
    text = f"{float(value):+.{digits}f}"
    return text.replace("+0.", "+.").replace("-0.", "-.")


def unsigned(value: float, digits: int = 3) -> str:
    if value is None or not math.isfinite(float(value)):
        return "---"
    text = f"{float(value):.{digits}f}"
    return text.replace("0.", ".", 1) if 0 <= float(value) < 1 else text


def record_text(record: dict, digits: int = 3, bold_if_separated: bool = True) -> str:
    mean = record.get("mean_gain", record.get("mean"))
    low, high = record["ci95"]
    text = f"{effect(mean, digits)} [{effect(low, digits)}, {effect(high, digits)}]"
    if bold_if_separated and record.get("separated", False):
        return rf"\textbf{{{text}}}"
    return text


def tex_name(name: str) -> str:
    aliases = {
        "current_smoking_status": "Smoking",
        "diabetes_history": "Diabetes",
        "hypertension_history": "Hypertension",
        "heart_attack_history": "Heart attack",
        "kidney_disease_history": "Kidney disease",
        "total_cholesterol": "Total cholesterol",
        "waist_cm": "Waist circumference",
        "hba1c": "HbA1c",
        "dbp": "DBP",
        "sbp": "SBP",
        "bun": "BUN",
        "rbc": "RBC",
    }
    if name in aliases:
        return aliases[name]
    return name.replace("_history", "").replace("_", " ").title()


def write_tex(name: str, lines: list[str]) -> None:
    (GEN_DIR / name).write_text("\n".join(lines).rstrip() + "\n")


def table_row(text: str) -> str:
    """Append a LaTeX tabular row terminator without escape ambiguity."""
    return text + r" \\"


def plot_a1_polarity() -> None:
    data = load("experiments/crta_v3_survey_label_panel_v1/SUMMARY_V1.json")
    targets = ["diabetes_history", "hypertension_history", "current_smoking_status"]
    labels = [tex_name(x) for x in targets]
    raw = np.asarray([data["raw_absolute_auroc_per_target"][x] for x in targets])
    correct = raw - np.asarray(
        [data["raw_vs_pipeline_descriptive"]["per_target_mean"][x] for x in targets]
    )
    wrong = correct - np.asarray(
        [data["A2_pipeline_vs_placebo"]["per_target_mean"][x] for x in targets]
    )

    fig, ax = plt.subplots(figsize=(7.0, 2.15))
    x = np.arange(len(labels))
    width = 0.23
    for offset, values, color, label in (
        (-width, raw, GRAY, "Reference (raw / undecoded)"),
        (0.0, correct, BLUE, "Intended decoding"),
        (width, wrong, ORANGE, "Wrong decoding"),
    ):
        bars = ax.bar(x + offset, values, width, color=color, label=label, zorder=3)
        for bar, value in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value + 0.017,
                f"{value:.2f}",
                ha="center",
                va="bottom",
                fontsize=6.4,
            )
    ax.axhline(0.5, color="#555555", linewidth=0.8, linestyle="--", label="Chance")
    ax.set_ylim(0.30, 1.02)
    ax.set_ylabel("Query AUROC")
    ax.set_xticks(x, labels)
    ax.grid(axis="y", color=LIGHT_GRAY, linewidth=0.6, zorder=0)
    ax.legend(
        frameon=False,
        ncol=4,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.08),
        columnspacing=1.5,
    )
    save(fig, "appendix_figure_a1_polarity")


def plot_a2_mismatch_grid() -> None:
    data = load("experiments/crta_v3_mcr_mismatch_dose_v1/SUMMARY_V1.json")
    tabpfn = load("experiments/crta_v3_mcr_mismatch_dose_tabpfn_v1/SUMMARY_V1.json")
    extension = load(
        "experiments/crta_v3_mcr_mismatch_dose_k512_extension_v1/SUMMARY_V1.json"
    )
    doses = np.asarray(data["doses"], dtype=float)
    panels = (
        ("tree", "xgb_K32", r"XGB, $n_{\mathrm{target}}=32$"),
        ("tree", "histgb_K32", r"HistGB, $n_{\mathrm{target}}=32$"),
        ("tabpfn", None, r"TabPFN, $n_{\mathrm{target}}=32$"),
        ("tree", "xgb_K512", r"XGB, $n_{\mathrm{target}}=512$"),
        ("extension", "histgb_K512", r"HistGB, $n_{\mathrm{target}}=512$"),
        ("extension", "tabpfn_K512", r"TabPFN, $n_{\mathrm{target}}=512$"),
    )
    family_style = {
        "additive": (BLUE, "o"),
        "pairwise": (ORANGE, "s"),
        "sparse": (GREEN, "^"),
    }
    fig, axes_grid = plt.subplots(2, 3, figsize=(7.0, 4.0), sharex=True)
    axes = axes_grid.ravel()
    for ax, (source, section, title) in zip(axes, panels):
        for family in FAMILIES:
            color, marker = family_style[family]
            if source == "tabpfn":
                values = tabpfn["sections"][family]["mean_U_by_dose"]
            elif source == "extension":
                values = extension["sections"][section][family]["mean_U_by_dose"]
            else:
                values = data["sections"][section][family]["mean_U_by_dose"]
            ax.plot(
                doses,
                values,
                color=color,
                marker=marker,
                linewidth=1.25,
                markersize=4,
                label=FAMILY_LABEL[family],
            )
        ax.axhline(0, color="#555555", linewidth=0.8)
        ax.set_xticks(doses.astype(int))
        ax.set_xlim(-0.25, 8.25)
        ax.grid(axis="y", color=LIGHT_GRAY, linewidth=0.6)
        ax.set_title(title)
        ax.set_xlabel("Mismatch dose $d$")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.text(
        0.012,
        0.50,
        r"Predictive utility ($\Delta Q$)",
        rotation=90,
        va="center",
        ha="center",
    )
    fig.legend(
        handles,
        labels,
        frameon=False,
        loc="upper right",
        bbox_to_anchor=(0.985, 1.015),
        ncol=3,
        columnspacing=1.0,
    )
    fig.suptitle(
        "Family-resolved predictive utility across schema mismatch",
        x=0.07,
        ha="left",
        y=1.02,
    )
    fig.tight_layout(w_pad=0.75, rect=(0.035, 0, 1, 0.96))
    save(fig, "appendix_figure_a2_mismatch_grid")


def plot_mismatch_support_ladder() -> None:
    """Full 5-point provenance for the support ladder in main Figure 1(b)."""
    data = load(
        "experiments/crta_v3_mcr_mismatch_support_ladder_v1/SUMMARY_V1.json"
    )
    supports = tuple(int(value) for value in data["supports"])
    if not data["complete"] or supports != (32, 64, 128, 256, 512):
        raise RuntimeError("The mismatch support ladder is incomplete")

    learners = (("xgb", "XGB"), ("histgb", "HistGB"), ("tabpfn", "TabPFN"))
    arms = (
        ("intended", BLUE, "o", "Intended"),
        ("reference", ORANGE, "s", "Reference"),
        ("matched_wrong", PURPLE, "^", "Wrong"),
    )
    x = np.arange(len(supports), dtype=float)
    fig, axes = plt.subplots(3, 3, figsize=(7.0, 5.25), sharex=True, sharey=True)
    for row, family in enumerate(FAMILIES):
        for col, (learner, learner_label) in enumerate(learners):
            ax = axes[row, col]
            section = data["sections"][learner][family]["absolute_nmse"]
            contrasts = data["sections"][learner][family]["contrasts"]
            for support in supports:
                key = str(support)
                intended = section[key]["intended"]["mean"]
                reference = section[key]["reference"]["mean"]
                wrong = section[key]["matched_wrong"]["mean"]
                if not (
                    np.isclose(reference - intended, contrasts["benefit"][key]["mean"], atol=1e-12)
                    and np.isclose(wrong - intended, contrasts["content"][key]["mean"], atol=1e-12)
                    and np.isclose(wrong - reference, contrasts["damage"][key]["mean"], atol=1e-12)
                ):
                    raise RuntimeError(
                        f"Support-ladder arms do not close for {learner}, {family}, K={support}"
                    )
            for arm, color, marker, label in arms:
                records = [section[str(k)][arm] for k in supports]
                means = np.asarray([record["mean"] for record in records])
                lows = np.asarray([record["ci95"][0] for record in records])
                highs = np.asarray([record["ci95"][1] for record in records])
                ax.fill_between(x, lows, highs, color=color, alpha=0.08, linewidth=0)
                ax.plot(
                    x,
                    means,
                    color=color,
                    marker=marker,
                    linewidth=1.15,
                    markersize=3.2,
                    label=label,
                )
            ax.grid(axis="y", color=LIGHT_GRAY, linewidth=0.55)
            ax.set_ylim(0.62, 1.16)
            if row == 0:
                ax.set_title(learner_label)
            if col == 0:
                ax.set_ylabel(f"{FAMILY_LABEL[family]}\nMean normalized MSE")
            if row == 2:
                ax.set_xticks(x, supports)
                ax.set_xlabel("Labeled target rows $K$")
            else:
                ax.tick_params(labelbottom=False)
    handles = [
        Line2D([0], [0], color=color, marker=marker, linewidth=1.2, label=label)
        for _, color, marker, label in arms
    ]
    fig.legend(
        handles=handles,
        frameon=False,
        ncol=3,
        loc="upper center",
        bbox_to_anchor=(0.56, 0.995),
        columnspacing=1.6,
    )
    fig.suptitle("Absolute conditions across labeled target rows", x=0.06, ha="left", y=1.035)
    fig.tight_layout(rect=(0, 0, 1, 0.91), h_pad=0.55, w_pad=0.55)
    save(fig, "appendix_figure_mismatch_support_ladder")


def _plot_forest_record(
    ax: plt.Axes,
    y: float,
    record: dict,
    color: str,
    marker: str,
) -> None:
    mean = float(record.get("mean", record.get("mean_gain")))
    low, high = (float(value) for value in record["ci95"])
    ax.errorbar(
        mean,
        y,
        xerr=np.asarray([[mean - low], [high - mean]]),
        fmt=marker,
        color=color,
        markerfacecolor=color,
        markeredgecolor="white",
        markeredgewidth=0.45,
        markersize=5,
        linewidth=1.05,
        capsize=1.8,
        zorder=3,
    )


def plot_correspondence_interfaces() -> None:
    """Native-scale forest plot with one stable sensitivity/utility grammar."""
    exam_reference = load(
        "experiments/crta_v3_exam_no_bridge_reference_v1/SUMMARY_V1.json"
    )["contrasts"]
    layer = load("experiments/crta_v3_m1m2_layer_ladder_v1/SUMMARY_V1.json")
    stage = load("experiments/crta_v3_m1m2_stage_factorial_v1/SUMMARY_V1.json")
    hist = load("experiments/crta_v3_binding_backbone_generality_v1/SUMMARY_V1.json")

    fig, (ax_exam, ax_survey) = plt.subplots(
        1, 2, figsize=(7.0, 2.35), gridspec_kw={"width_ratios": (0.92, 1.18)}
    )
    exam_rows = (
        ("Binding — content sensitivity", exam_reference["content_S_minus_W"]),
        ("Aggregation — content sensitivity", layer["R2_grouping_vs_placebo"]),
    )
    for y, (_, record) in enumerate(exam_rows):
        _plot_forest_record(ax_exam, y, record, BLUE, "o")
    ax_exam.set_yticks(range(len(exam_rows)), [row[0] for row in exam_rows])
    ax_exam.set_ylim(1.55, -0.55)
    ax_exam.set_xlim(-0.025, 0.135)
    ax_exam.set_xlabel("Gain in normalized-RMSE")
    ax_exam.set_title("(a) Examination", loc="left")

    survey_rows = (
        ("XGB — content sensitivity", stage["S2_binding_content"], BLUE, "o"),
        ("XGB — predictive utility", stage["desc_columns_at_stage"], ORANGE, "s"),
        (
            "HistGB — content sensitivity",
            hist["sections"]["K256"]["S5_P1_binding_content"],
            BLUE,
            "o",
        ),
        (
            "HistGB — predictive utility",
            hist["sections"]["K256"]["S5_P2_columns_on_stage"],
            ORANGE,
            "s",
        ),
    )
    for y, (_, record, color, marker) in enumerate(survey_rows):
        _plot_forest_record(ax_survey, y, record, color, marker)
    ax_survey.axhline(1.5, color="#c4c4c4", linewidth=0.7)
    ax_survey.set_yticks(range(len(survey_rows)), [row[0] for row in survey_rows])
    ax_survey.set_ylim(3.55, -0.55)
    ax_survey.set_xlim(-0.03, 0.105)
    ax_survey.set_xlabel("AUROC gain")
    ax_survey.set_title("(b) Survey, $K=256$", loc="left")

    for ax in (ax_exam, ax_survey):
        ax.axvline(0, color="#555555", linewidth=0.8)
        ax.grid(axis="x", color=LIGHT_GRAY, linewidth=0.6)
    fig.legend(
        handles=[
            Line2D([0], [0], color=BLUE, marker="o", linewidth=0, label="Content sensitivity"),
            Line2D([0], [0], color=ORANGE, marker="s", linewidth=0, label="Predictive utility"),
        ],
        frameon=False,
        ncol=2,
        loc="upper center",
        bbox_to_anchor=(0.58, 1.01),
        columnspacing=1.4,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.91), w_pad=1.3)
    save(fig, "appendix_figure_correspondence_interfaces")


def plot_a3_mc_surface() -> None:
    data = load("experiments/crta_v3_mcr_mc_surface_v1/SUMMARY_V1.json")
    all_arrays = []
    for backbone in ("xgb", "histgb"):
        for family in FAMILIES:
            surface = data["results"][backbone][family]["mean_nmse_surface"]
            all_arrays.append(
                np.asarray([[surface[str(m)][str(c)] for c in (0, 2, 4, 6, 8)] for m in (0, 2, 4, 6, 8)])
            )
    vmin = min(float(x.min()) for x in all_arrays)
    vmax = max(float(x.max()) for x in all_arrays)
    fig, axes = plt.subplots(2, 3, figsize=(7.0, 4.15), sharex=True, sharey=True)
    image = None
    idx = 0
    for row, backbone in enumerate(("xgb", "histgb")):
        for col, family in enumerate(FAMILIES):
            ax = axes[row, col]
            values = all_arrays[idx]
            idx += 1
            image = ax.imshow(values, cmap="YlOrRd", vmin=vmin, vmax=vmax, origin="lower")
            for i in range(5):
                for j in range(5):
                    color = "white" if values[i, j] > vmin + 0.62 * (vmax - vmin) else "#333333"
                    ax.text(j, i, f"{values[i, j]:.2f}", ha="center", va="center", fontsize=6.2, color=color)
            backbone_label = "XGB" if backbone == "xgb" else "HistGB"
            ax.set_title(f"{backbone_label} · {FAMILY_LABEL[family]}")
            ax.set_xticks(range(5), [0, 2, 4, 6, 8])
            ax.set_yticks(range(5), [0, 2, 4, 6, 8])
            if row == 1:
                ax.set_xlabel("Correspondence corruption dose")
            if col == 0:
                ax.set_ylabel("Variable-recording corruption dose")
    cbar = fig.colorbar(image, ax=axes.ravel().tolist(), fraction=0.022, pad=0.025)
    cbar.set_label("Mean normalized MSE (lower is better)")
    fig.suptitle(r"Joint $5\times 5$ variable-recording--correspondence corruption surfaces", y=0.995)
    fig.subplots_adjust(left=0.08, right=0.91, bottom=0.09, top=0.92, wspace=0.20, hspace=0.26)
    save(fig, "appendix_figure_a3_mc_surface")


def plot_a4_controlled_ladder() -> None:
    data = load("experiments/crta_v3_mcr_source_informativeness_ladder_v1/SUMMARY_V1.json")
    alphas = np.asarray([0, 0.25, 0.5, 0.75, 1.0])
    colors = {"additive": BLUE, "pairwise": ORANGE, "sparse": GREEN}
    fig, ax = plt.subplots(figsize=(7.0, 2.55))
    for family in FAMILIES:
        for backbone, linestyle, marker in (("xgb", "-", "o"), ("histgb", "--", "s")):
            row = data["strata"][family][backbone]
            values = [row["mean_I_MC_by_alpha"][f"{a:.2f}"] for a in alphas]
            ax.plot(
                alphas,
                values,
                color=colors[family],
                linestyle=linestyle,
                marker=marker,
                markersize=3.7,
                linewidth=1.15,
                label=f"{FAMILY_LABEL[family]} · {backbone.upper()}",
            )
    ax.axhline(0, color="#555555", linewidth=0.8)
    ax.set_xticks(alphas)
    ax.set_xlim(-0.02, 1.02)
    ax.set_xlabel(r"Corrupted source-label fraction $\alpha$")
    ax.set_ylabel(r"Interaction $I_{MC}(\alpha)$ ($\Delta Q$)")
    ax.grid(axis="y", color=LIGHT_GRAY, linewidth=0.6)
    ax.legend(frameon=False, ncol=3, loc="upper right")
    ax.set_title("Controlled source-label-informativeness ladder", loc="left")
    save(fig, "appendix_figure_a4_controlled_label_ladder")


def pooled_curve(payload: dict, key: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows = payload["corrected"][key]
    ordered = [rows[f"{a:.2f}"] for a in (0, 0.25, 0.5, 0.75, 1.0)]
    mean = np.asarray([x["mean"] for x in ordered])
    low = np.asarray([x["ci95"][0] for x in ordered])
    high = np.asarray([x["ci95"][1] for x in ordered])
    return mean, low, high


def plot_a5_real_ladder() -> None:
    v1 = load("experiments/crta_v3_stage_source_informativeness_ladder_v1/SUMMARY_V1.json")
    v2 = load("experiments/crta_v3_stage_source_ladder_v2_source_only_v1/SUMMARY_V1.json")
    alphas = np.asarray([0, 0.25, 0.5, 0.75, 1.0])
    fig, ax = plt.subplots(figsize=(7.0, 2.55))
    for payload, color, marker, label in (
        (v1, PURPLE, "o", "Original variable-recording setting"),
        (v2, BLUE, "s", "Source-only variable-recording setting"),
    ):
        mean, low, high = pooled_curve(payload, "pooled_I_by_alpha")
        ax.fill_between(alphas, low, high, color=color, alpha=0.13, linewidth=0)
        ax.plot(alphas, mean, color=color, marker=marker, linewidth=1.3, markersize=4, label=label)
    ax.axhline(0, color="#555555", linewidth=0.8)
    ax.set_xticks(alphas)
    ax.set_xlim(-0.02, 1.02)
    ax.set_xlabel(r"Corrupted source-label fraction $\alpha$")
    ax.set_ylabel(r"Endpoint-clustered $I^*_{MC}(\alpha)$")
    ax.grid(axis="y", color=LIGHT_GRAY, linewidth=0.6)
    ax.legend(frameon=False, loc="upper left")
    ax.set_title("Real-data ladder audit: neither variable-recording definition attenuates", loc="left")
    save(fig, "appendix_figure_a5_real_label_ladder")


def plot_a6_real_lesion_panel() -> None:
    """Render the three sequential real-data lesions from frozen summaries."""
    base = "experiments/crta_v3_stage_ladder_v3_lesions_v1"
    reference = load(
        "experiments/crta_v3_stage_source_ladder_v2_source_only_v1/SUMMARY_V1.json"
    )
    ref_mean, _, _ = pooled_curve(reference, "pooled_I_by_alpha")
    specs = (
        ("source_feature_render", "Source rendering\n— flat"),
        ("source_feature_colperm", "Source-column permutation\n— flat"),
        ("support_label", "Labeled-target-label corruption\n— attenuation"),
    )
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.28), sharex=True, sharey=True)
    for ax, (subdir, title) in zip(axes, specs):
        data = load(f"{base}/{subdir}/SUMMARY_V1.json")
        doses = np.asarray(data["doses"], dtype=float)
        rows = data["corrected"]["pooled_I_by_dose"]
        ordered = [rows[f"{x:.2f}"] for x in doses]
        mean = np.asarray([x["mean"] for x in ordered])
        low = np.asarray([x["ci95"][0] for x in ordered])
        high = np.asarray([x["ci95"][1] for x in ordered])
        ax.fill_between(doses, low, high, color=BLUE, alpha=0.16, linewidth=0)
        ax.plot(doses, mean, color=BLUE, marker="o", linewidth=1.35, markersize=3.3, label="Pooled")
        ax.plot(
            doses,
            data["corrected"]["per_direction_mean_curve"]["kn2nh"],
            color=ORANGE,
            linestyle="--",
            marker="s",
            linewidth=1.0,
            markersize=2.8,
            label="KN$\to$NH",
        )
        ax.plot(
            doses,
            data["corrected"]["per_direction_mean_curve"]["nh2kn"],
            color=GREEN,
            linestyle="--",
            marker="s",
            linewidth=1.0,
            markersize=2.8,
            label="NH$\to$KN",
        )
        ax.plot(
            doses,
            ref_mean,
            color=GRAY,
            linestyle=":",
            linewidth=1.0,
            label="Earlier source-label curve",
        )
        ax.axhline(0, color="#555555", linewidth=0.7)
        ax.set_xticks(doses)
        ax.set_xlim(-0.03, 1.03)
        ax.set_ylim(-0.006, 0.078)
        ax.set_xlabel("Corruption dose")
        ax.grid(axis="y", color=LIGHT_GRAY, linewidth=0.55)
        ax.set_title(title, loc="left", fontsize=7.1, linespacing=1.05)
    axes[0].set_ylabel(r"Polarity-invariant $I^*_{MC}$")
    axes[0].legend(frameon=False, fontsize=5.4, loc="lower left", handlelength=1.8)
    fig.subplots_adjust(wspace=0.12)
    save(fig, "appendix_figure_a6_real_lesions")


def plot_a7_decoy_damage() -> None:
    data = load("experiments/crta_v3_decoy_compiler_specificity_v1/SUMMARY_V1.json")
    doses = np.asarray([0, 1, 3, 5, 9])
    fig, ax = plt.subplots(figsize=(7.0, 2.55))
    for curve in data["stage_b"]["per_endpoint_curves"].values():
        ax.plot(doses, curve, color=GRAY, alpha=0.28, linewidth=0.65)
    mean = np.asarray([data["stage_b"]["mean_D_by_dose"][str(x)] for x in doses])
    ax.plot(doses, mean, color=RED, marker="o", linewidth=1.5, markersize=4.5, label="Endpoint mean")
    reference = data["stage_b"]["derangement_damage_reference"]["mean"]
    ax.axhline(
        reference,
        color=PURPLE,
        linestyle="--",
        linewidth=1.0,
        label="Altered condition: full derangement",
    )
    ax.axhline(0, color="#555555", linewidth=0.8)
    ax.set_xticks(doses)
    ax.set_xlabel("Number of forced orphan bindings $k$")
    ax.set_ylabel("AUROC loss")
    ax.grid(axis="y", color=LIGHT_GRAY, linewidth=0.6)
    ax.legend(frameon=False, loc="upper left")
    ax.set_title(
        "Performance loss from forced plausible-neighbour bindings",
        loc="left",
    )
    save(fig, "appendix_figure_a7_decoy_damage")


def plot_redundancy_ladder() -> None:
    """Absolute-condition decomposition for both budgets and tree models."""
    data = load("experiments/crta_v3_mcr_redundancy_ladder_v1/SUMMARY_V1.json")
    families = ("pairwise", "sparse")
    supports = ("32", "512")
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 3.65), sharey=True)
    for row, family in enumerate(families):
        for col, support in enumerate(supports):
            ax = axes[row, col]
            curves = {}
            for learner in ("xgb", "histgb"):
                table = data["sections"][support]["rung_table"][f"{learner}|{family}"]
                keys = sorted(table, key=int)
                xs = np.asarray([int(key) for key in keys])
                curves[learner] = {
                    "x": xs,
                    "intended": np.asarray(
                        [table[key]["arm_mean_nmse"]["op_true"] for key in keys]
                    ),
                    "reference": np.asarray(
                        [table[key]["arm_mean_nmse"]["free"] for key in keys]
                    ),
                }
                utility = np.asarray([table[key]["U"]["mean"] for key in keys])
                if not np.allclose(
                    curves[learner]["reference"] - curves[learner]["intended"],
                    utility,
                    atol=1e-12,
                ):
                    raise RuntimeError(
                        f"Removal-ladder arms do not close for {learner}, {family}, K={support}"
                    )
            x = curves["xgb"]["x"]
            intended_mean = np.mean(
                [curves[learner]["intended"] for learner in ("xgb", "histgb")],
                axis=0,
            )
            reference_mean = np.mean(
                [curves[learner]["reference"] for learner in ("xgb", "histgb")],
                axis=0,
            )
            ax.fill_between(
                x,
                intended_mean,
                reference_mean,
                color="#9ab8ce",
                alpha=0.28,
                linewidth=0,
                label="Predictive utility",
            )
            for learner, linestyle in (("xgb", "-"), ("histgb", "--")):
                ax.plot(
                    x,
                    curves[learner]["intended"],
                    color=BLUE,
                    linestyle=linestyle,
                    marker="o",
                    linewidth=1.35,
                    markersize=3.2,
                )
                ax.plot(
                    x,
                    curves[learner]["reference"],
                    color=ORANGE,
                    linestyle=linestyle,
                    marker="s",
                    linewidth=1.35,
                    markersize=3.2,
                )
            if row == 0:
                ax.set_title(r"$n_{\mathrm{target}}=" + support + "$")
            if col == 0:
                ax.set_ylabel(f"{FAMILY_LABEL[family]}\nMean normalized MSE")
            if row == 1:
                ax.set_xlabel("Input columns removed")
            ax.set_xticks(x)
            ax.set_ylim(0.66, 1.08)
            ax.grid(axis="y", color=LIGHT_GRAY, linewidth=0.55)
    fig.legend(
        handles=[
            Line2D([0], [0], color=BLUE, marker="o", label="Intended"),
            Line2D([0], [0], color=ORANGE, marker="s", label="Reference"),
            Line2D([0], [0], color=GRAY, linestyle="-", label="XGB"),
            Line2D([0], [0], color=GRAY, linestyle="--", label="HistGB"),
            Line2D([0], [0], color="#9ab8ce", linewidth=5, alpha=0.55, label="Predictive utility"),
        ],
        frameon=False,
        ncol=5,
        loc="upper center",
        bbox_to_anchor=(0.56, 1.01),
        columnspacing=1.0,
        handlelength=2.0,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.93), h_pad=0.8, w_pad=0.7)
    save(fig, "appendix_figure_a8_redundancy_ladder")


def plot_controlled_real_mechanism() -> None:
    """Pair the controlled attenuation result with its real-data audit."""
    controlled = load(
        "experiments/crta_v3_mcr_source_informativeness_ladder_v1/SUMMARY_V1.json"
    )
    real_original = load(
        "experiments/crta_v3_stage_source_informativeness_ladder_v1/SUMMARY_V1.json"
    )
    real_source_only = load(
        "experiments/crta_v3_stage_source_ladder_v2_source_only_v1/SUMMARY_V1.json"
    )
    alphas = np.asarray([0, 0.25, 0.5, 0.75, 1.0])
    fig, (ax_controlled, ax_real) = plt.subplots(
        1, 2, figsize=(7.0, 2.65), gridspec_kw={"width_ratios": (1.08, 0.92)}
    )
    colors = {"additive": BLUE, "pairwise": ORANGE, "sparse": GREEN}
    for family in FAMILIES:
        for learner, linestyle, marker in (("xgb", "-", "o"), ("histgb", "--", "s")):
            row = controlled["strata"][family][learner]
            values = [row["mean_I_MC_by_alpha"][f"{alpha:.2f}"] for alpha in alphas]
            ax_controlled.plot(
                alphas,
                values,
                color=colors[family],
                linestyle=linestyle,
                marker=marker,
                markersize=3.2,
                linewidth=1.05,
                label=f"{FAMILY_LABEL[family]} · {learner.upper()}",
            )
    ax_controlled.set_title("(a) Controlled source-label ladder", loc="left")
    ax_controlled.set_ylabel(r"Interaction $I_{MC}(\alpha)$ ($\Delta Q$)")
    ax_controlled.legend(
        frameon=False,
        ncol=2,
        fontsize=5.7,
        loc="upper right",
        columnspacing=0.7,
        handletextpad=0.3,
    )

    for payload, color, marker, label in (
        (real_original, PURPLE, "o", "Original measurement definition"),
        (real_source_only, BLUE, "s", "Source-only measurement definition"),
    ):
        mean, low, high = pooled_curve(payload, "pooled_I_by_alpha")
        ax_real.fill_between(alphas, low, high, color=color, alpha=0.13, linewidth=0)
        ax_real.plot(
            alphas,
            mean,
            color=color,
            marker=marker,
            linewidth=1.3,
            markersize=3.7,
            label=label,
        )
    ax_real.set_title("(b) Real-data initial probes", loc="left")
    ax_real.set_ylabel(r"Endpoint-clustered $I^*_{MC}(\alpha)$")
    ax_real.legend(frameon=False, fontsize=5.8, loc="upper left")
    for ax in (ax_controlled, ax_real):
        ax.axhline(0, color="#555555", linewidth=0.8)
        ax.set_xticks(alphas)
        ax.set_xlim(-0.02, 1.02)
        ax.set_xlabel(r"Corrupted source-label fraction $\alpha$")
        ax.grid(axis="y", color=LIGHT_GRAY, linewidth=0.55)
    fig.tight_layout(w_pad=1.1)
    save(fig, "appendix_figure_controlled_real_mechanism")


def table_a1_measurement() -> None:
    focused = load("experiments/crta_v3_survey_label_panel_v1/SUMMARY_V1.json")
    expanded = load("experiments/crta_v3_survey_label_panel_endpoint_expansion_v1/SUMMARY_V1.json")
    focused_utility = {
        "mean": -focused["raw_vs_pipeline_descriptive"]["mean_gain"],
        "ci95": [
            -focused["raw_vs_pipeline_descriptive"]["ci95"][1],
            -focused["raw_vs_pipeline_descriptive"]["ci95"][0],
        ],
        "separated": True,
    }
    expanded_utility = {
        "mean": -expanded["raw_minus_pipeline_descriptive"]["mean"],
        "ci95": [
            -expanded["raw_minus_pipeline_descriptive"]["ci95"][1],
            -expanded["raw_minus_pipeline_descriptive"]["ci95"][0],
        ],
        "separated": True,
    }
    raw10 = expanded["R1_raw_absolute_reversal"]
    write_tex(
        "table_a1_measurement.tex",
        [
            r"\begin{table}[H]",
            r"\caption{Full measurement-panel summary at $K=256$. Positive contrasts favor documented decoding. The ten-endpoint supplied--matched-wrong contrast is descriptive because the prespecified coverage gate failed, despite its interval excluding zero.}",
            r"\label{tab:app-measurement-full}",
            r"\label{tab:app_measurement}",
            r"\centering\scriptsize",
            r"\setlength{\tabcolsep}{3.5pt}",
            r"\begin{tabular}{P{0.15\linewidth}P{0.16\linewidth}P{0.22\linewidth}P{0.22\linewidth}P{0.10\linewidth}}",
            r"\toprule",
            r"Panel & Unit & Content: supplied $-$ matched-wrong & Utility: supplied $-$ reference & Raw reference AUROC \\",
            r"\midrule",
            table_row(f"Focused polarity & 3 endpoints & {record_text(focused['A2_pipeline_vs_placebo'])} & {record_text(focused_utility)} & {unsigned(np.mean(list(focused['raw_absolute_auroc_per_target'].values())),3)}"),
            table_row(f"Endpoint extension & 10 endpoint clusters & {record_text(expanded['P1_pipeline_vs_placebo'], bold_if_separated=False)} & {record_text(expanded_utility)} & {unsigned(raw10['mean'],3)} [{unsigned(raw10['ci95'][0],3)}, {unsigned(raw10['ci95'][1],3)}]"),
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
        ],
    )


def table_a2_mismatch() -> None:
    data = load("experiments/crta_v3_mcr_mismatch_dose_v1/SUMMARY_V1.json")
    lines = [
        r"\begin{table}[t]",
        r"\caption{Mismatch-dose statistics. $\rho$ is the realization-level Spearman coefficient between dose and $U_M(d)$; $U_M(8)$ is the full-mismatch utility. Intervals are realization-bootstrap intervals within each fixed family. HistGB and TabPFN at $K=512$ are post-result budget-completion extensions and are left unbolded; boldface is reserved for the originally registered full-dose strata.}",
        r"\label{tab:app-measurement-dose-stats}",
        r"\label{tab:app_mismatch_stats}",
        r"\centering\scriptsize",
        r"\setlength{\tabcolsep}{5pt}",
        r"\begin{tabular}{lllll}",
        r"\toprule",
        r"Learner & $K$ & Family & Mean $\rho$ [95\% CI] & $U_M(8)$ [95\% CI] \\",
        r"\midrule",
    ]
    for key, learner, budget in (("xgb_K32", "XGB", 32), ("histgb_K32", "HistGB", 32), ("xgb_K512", "XGB", 512)):
        for family in FAMILIES:
            row = data["sections"][key][family]
            rho = row["MD_P1_spearman"]
            u8 = row["MD_P2_u8"]
            lines.append(
                f"{learner} & {budget} & {FAMILY_LABEL[family]} & {effect(rho['mean'],2)} [{effect(rho['ci95'][0],2)}, {effect(rho['ci95'][1],2)}] & {record_text(u8)} \\\n+"
            )
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    write_tex("table_a2_mismatch.tex", lines)


def table_a2_mismatch_fixed() -> None:
    data = load("experiments/crta_v3_mcr_mismatch_dose_v1/SUMMARY_V1.json")
    tabpfn = load("experiments/crta_v3_mcr_mismatch_dose_tabpfn_v1/SUMMARY_V1.json")
    extension = load(
        "experiments/crta_v3_mcr_mismatch_dose_k512_extension_v1/SUMMARY_V1.json"
    )
    lines = [
        r"\begin{table}[H]",
        r"\caption{Mismatch-dose statistics. $\rho$ is the realization-level Spearman coefficient between dose and $U_M(d)$; $U_M(8)$ is the full-mismatch utility. Intervals are realization-bootstrap intervals within each fixed family. HistGB and TabPFN at $K=512$ are post-result budget-completion extensions and are left unbolded; boldface is reserved for the originally registered full-dose strata.}",
        r"\label{tab:app-measurement-dose-stats}",
        r"\label{tab:app_mismatch_stats}",
        r"\centering\scriptsize",
        r"\setlength{\tabcolsep}{5pt}",
        r"\begin{tabular}{lllll}",
        r"\toprule",
        r"Learner & $K$ & Family & Mean $\rho$ [95\% CI] & $U_M(8)$ [95\% CI] \\",
        r"\midrule",
    ]
    sections = (
        ("xgb_K32", "XGB", 32),
        ("histgb_K32", "HistGB", 32),
    )
    for key, learner, budget in sections:
        for family in FAMILIES:
            row = data["sections"][key][family]
            rho = row["MD_P1_spearman"]
            u8 = row["MD_P2_u8"]
            lines.append(table_row(
                f"{learner} & {budget} & {FAMILY_LABEL[family]} & "
                f"{effect(rho['mean'], 2)} [{effect(rho['ci95'][0], 2)}, "
                f"{effect(rho['ci95'][1], 2)}] & {record_text(u8)}"
            ))
    for family in FAMILIES:
        row = tabpfn["sections"][family]
        rho = row["MDT_P1_spearman"]
        u8 = row["MDT_P2_u8"]
        lines.append(table_row(
            f"TabPFN & 32 & {FAMILY_LABEL[family]} & "
            f"{effect(rho['mean'], 2)} [{effect(rho['ci95'][0], 2)}, "
            f"{effect(rho['ci95'][1], 2)}] & {record_text(u8)}"
        ))
    lines.append(r"\addlinespace[1pt]")
    for family in FAMILIES:
        row = data["sections"]["xgb_K512"][family]
        rho = row["MD_P1_spearman"]
        u8 = row["MD_P2_u8"]
        lines.append(table_row(
            f"XGB & 512 & {FAMILY_LABEL[family]} & "
            f"{effect(rho['mean'], 2)} [{effect(rho['ci95'][0], 2)}, "
            f"{effect(rho['ci95'][1], 2)}] & {record_text(u8)}"
        ))
    for key, learner in (("histgb_K512", "HistGB"),
                         ("tabpfn_K512", "TabPFN")):
        for family in FAMILIES:
            row = extension["sections"][key][family]
            rho = row["rho_dose_utility"]
            u8 = row["u8"]
            lines.append(table_row(
                f"{learner} & 512 & {FAMILY_LABEL[family]} & "
                f"{effect(rho['mean'], 2)} [{effect(rho['ci95'][0], 2)}, "
                f"{effect(rho['ci95'][1], 2)}] & {record_text(u8)}"
            ))
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    write_tex("table_a2_mismatch.tex", lines)


def table_a3_real_units() -> None:
    measurement = load("experiments/crta_v3_survey_label_panel_v1/SUMMARY_V1.json")
    exam = load("experiments/crta_v3_m1m2_layer_ladder_v1/SUMMARY_V1.json")
    survey_xgb = load("experiments/crta_v3_m1m2_stage_factorial_v1/SUMMARY_V1.json")
    survey_hist = load("experiments/crta_v3_binding_backbone_generality_v1/SUMMARY_V1.json")["sections"]["K256"]
    nhkn = load("experiments/crta_v3_pam_constraint_relations_v1/SUMMARY_V1.json")
    hrs = load("experiments/crta_v3_m3_sign_probe_v1/SUMMARY_V1.json")
    camels = load("experiments/crta_v3_camels_sign_probe_v2/SUMMARY_V2.json")
    rows: list[tuple[str, str, str, float | None, float | None]] = []
    for target in measurement["targets_present"]:
        rows.append(
            (
                "$M$",
                "NHANES--KNHANES labels",
                tex_name(target),
                measurement["A2_pipeline_vs_placebo"]["per_target_mean"][target],
                -measurement["raw_vs_pipeline_descriptive"]["per_target_mean"][target],
            )
        )
    for target, value in exam["R1_columns_vs_placebo"]["per_target_mean"].items():
        rows.append(("$C$", "Exam binding · original XGB", tex_name(target), value, None))
    for target in survey_xgb["targets_present"]:
        rows.append(
            (
                "$C$",
                "Survey binding · XGB",
                tex_name(target),
                survey_xgb["S2_binding_content"]["per_target_mean"][target],
                survey_xgb["desc_columns_at_stage"]["per_target_mean"][target],
            )
        )
    for target in survey_hist["S5_P1_binding_content"]["target_means"]:
        rows.append(
            (
                "$C$",
                "Survey binding · HistGB",
                tex_name(target),
                survey_hist["S5_P1_binding_content"]["target_means"][target],
                survey_hist["S5_P2_columns_on_stage"]["target_means"][target],
            )
        )
    for target in nhkn["targets_present"]:
        rows.append(
            (
                "$R$",
                "NHANES--KNHANES",
                tex_name(target),
                nhkn["V_SIGN_CONTENT_flip_must_hurt"]["per_target_mean"][target],
                nhkn["declared_sign_vs_free_tax_expected"]["per_target_mean"][target],
            )
        )
    for target in hrs["endpoints"]:
        rows.append(
            (
                "$R$",
                "NHANES/KNHANES--HRS",
                tex_name(target),
                hrs["GS_P1_identification_flipped"]["per_endpoint_mean"][target],
                hrs["GS_P3_utility_vs_free"]["per_endpoint_mean"][target],
            )
        )
    cam_content = camels["GCv2_P1_identification"]["log1p_rmse"]["per_basin_mean"]
    cam_utility = camels["GCv2_P2_utility"]["log1p_rmse"]["per_basin_mean"]
    for basin in sorted(cam_content, key=int):
        rows.append(("$R$", "CAMELS-US--GB", f"Basin {basin}", cam_content[basin], cam_utility[basin]))

    lines = [
        r"\begin{longtable}{P{0.045\linewidth}P{0.27\linewidth}P{0.23\linewidth}rr}",
        r"\caption{Unit-resolved real-data attribution. Entries are seed-averaged unit effects in each setting's native metric. Positive values favor the supplied condition. Unit rows are descriptive; inferential intervals are computed on the aggregate independent units and reported in Table~\ref{tab:app-relation-full} and the main paper.}\label{tab:app-unit-attribution}\label{tab:app_real_units}\\",
        r"\toprule",
        r"Role & Setting / interface & Endpoint or basin & Content & Utility \\",
        r"\midrule",
        r"\endfirsthead",
        r"\multicolumn{5}{c}{\tablename\ \thetable\ (continued)}\\",
        r"\toprule Role & Setting / interface & Endpoint or basin & Content & Utility \\",
        r"\midrule",
        r"\endhead",
        r"\bottomrule",
        r"\endfoot",
    ]
    previous = None
    for role, setting, unit, content, utility in rows:
        if previous is not None and (role, setting) != previous:
            lines.append(r"\addlinespace[1pt]")
        lines.append(table_row(f"{role} & {setting} & {unit} & {effect(content,3)} & {effect(utility,3) if utility is not None else 'n/e'}"))
        previous = (role, setting)
    lines.extend([
        r"\end{longtable}",
        r"\noindent{\footnotesize\emph{Note.} Utility is not evaluable (n/e) for the original examination arm because removing binding also removes its member columns. The post-result width-matched domain-local reference is reported separately in Table~\ref{tab:app-exam-no-bridge}.}",
    ])
    write_tex("table_a3_real_units.tex", lines)


def table_a4_factorial() -> None:
    tree = load("experiments/crta_v3_mcr_factorial_semisynth_v1/SUMMARY_V1.json")
    tabpfn = load("experiments/crta_v3_mcr_factorial_tabpfn_v1/SUMMARY_V1.json")
    mlp = load("experiments/crta_v3_mcr_factorial_mlp_v1/SUMMARY_V1.json")
    rows = []
    for section, learner, budget in (
        ("xgb_K32", "XGB", 32),
        ("xgb_K512", "XGB", 512),
        ("histgb_K32", "HistGB", 32),
        ("histgb_K512", "HistGB", 512),
    ):
        for family in FAMILIES:
            block = tree["primary"][section]
            rows.append((learner, budget, family, block["P1_measurement"][family], block["P2_correspondence"][family], block["P4_MC_interaction"][family]))
    for family in FAMILIES:
        rows.append(("TabPFN", 32, family, tabpfn["sections"]["T1_measurement"][family], tabpfn["sections"]["T2_correspondence"][family], tabpfn["sections"]["T3_MC_interaction"][family]))
    for budget in ("32", "512"):
        for family in FAMILIES:
            block = mlp["sections"][budget]
            rows.append(("MLP", int(budget), family, block["N1_measurement"][family], block["N2_correspondence"][family], block["N3_MC_interaction"][family]))
    lines = [
        r"\begin{longtable}{lllP{0.23\linewidth}P{0.23\linewidth}P{0.23\linewidth}}",
        r"\caption{Full controlled factorial results. All three effects use $Q=-\mathrm{MSE}/\mathrm{Var}(y^{\mathrm{qry}})$; intervals resample the 20 realizations within each fixed family. The MLP is a frozen-before-execution extension and is not included in the main figure.}\label{tab:app-controlled-factorial}\label{tab:app_factorial}\\",
        r"\toprule",
        r"Learner & $K$ & Family & Measurement & Correspondence & $I_{MC}$ \\",
        r"\midrule\endfirsthead",
        r"\multicolumn{6}{c}{\tablename\ \thetable\ (continued)}\\",
        r"\toprule Learner & $K$ & Family & Measurement & Correspondence & $I_{MC}$ \\",
        r"\midrule\endhead",
        r"\bottomrule\endfoot",
    ]
    previous = None
    for learner, budget, family, m, c, inter in rows:
        if previous is not None and (learner, budget) != previous:
            lines.append(r"\addlinespace[1pt]")
        lines.append(table_row(f"{learner} & {budget} & {FAMILY_LABEL[family]} & {record_text(m)} & {record_text(c)} & {record_text(inter)}"))
        previous = (learner, budget)
    lines.append(r"\end{longtable}")
    write_tex("table_a4_factorial.tex", lines)


def table_a5_value_channel() -> None:
    data = load("experiments/crta_v3_mcr_value_redundancy_v1/SUMMARY_V1.json")
    lines = [
        r"\begin{table}[t]",
        r"\caption{Value-channel mechanism contrasts after the true-pair constituent columns are removed. The reduced free arm retains only the remaining base columns; the unconstrained value arm adds the true operation columns. Magnitude becomes nonredundant, whereas negating an operation value remains nearly invariant. All effects are on the controlled $\Delta Q$ scale.}",
        r"\label{tab:app-relation-value-interface}",
        r"\label{tab:app_value_channel}",
        r"\centering\tiny",
        r"\setlength{\tabcolsep}{2.5pt}",
        r"\resizebox{\linewidth}{!}{%",
        r"\begin{tabular}{lllP{0.19\linewidth}P{0.19\linewidth}P{0.19\linewidth}P{0.19\linewidth}P{0.19\linewidth}}",
        r"\toprule Learner & $K$ & Family & Operation magnitude utility & Correct constraint vs. unconstrained values & Correct vs. flipped constraint & Flipped constraint vs. reduced free & Value-sign sensitivity \\",
        r"\midrule",
    ]
    for budget in ("32", "512"):
        block = data["sections"][budget]
        for learner in ("xgb", "histgb"):
            for family in ("pairwise", "sparse"):
                key = f"{learner}|{family}"
                lines.append(table_row(
                    f"{learner.upper()} & {budget} & {FAMILY_LABEL[family]} & {record_text(block['V1_magnitude_nonredundant'][key])} & {record_text(block['V2_direction_on_top'][key])} & {record_text(block['V3_constraint_content'][key])} & {record_text(block['desc_flipped_over_free'][key], bold_if_separated=False)} & {record_text(block['V4_value_sign_equivariance'][key], bold_if_separated=False)}"))
        if budget == "32":
            lines.append(r"\addlinespace[1pt]")
    lines += [r"\bottomrule\end{tabular}}", r"\end{table}"]
    write_tex("table_a5_value_channel.tex", lines)


def table_a6_monotone() -> None:
    data = load("experiments/crta_v3_mcr_monotone_mlp_v1/SUMMARY_V1.json")
    lines = [
        r"\begin{table}[t]",
        r"\caption{Partially monotone MLP probe. ``True utility'' compares correct constraints with the free model; ``direction content'' compares correct with flipped directions; the last column shows flipped constraints against free. The prespecified directional-utility verdict fails because correct direction does not dominate across families.}",
        r"\label{tab:app-relation-monotone-mlp}",
        r"\label{tab:app_monotone_mlp}",
        r"\centering\scriptsize",
        r"\setlength{\tabcolsep}{4pt}",
        r"\begin{tabular}{llP{0.23\linewidth}P{0.23\linewidth}P{0.23\linewidth}}",
        r"\toprule $K$ & Family & True utility & Direction content & Flipped vs. free \\",
        r"\midrule",
    ]
    for budget in ("32", "512"):
        block = data["sections"][budget]
        for family in FAMILIES:
            lines.append(table_row(
                f"{budget} & {FAMILY_LABEL[family]} & {record_text(block['NM1_constraint_utility'][family])} & {record_text(block['NM2_direction_content'][family])} & {record_text(block['flip_over_free'][family])}"))
        if budget == "32":
            lines.append(r"\addlinespace[1pt]")
    lines += [r"\bottomrule\end{tabular}", r"\end{table}"]
    write_tex("table_a6_monotone.tex", lines)


def table_a7_decoy_matcher() -> None:
    audit = load("experiments/crta_v3_decoy_compiler_specificity_v1/STAGE_A_MATCHER_V1.json")
    labels = {"name_only": "Name", "name_plus_unit": "Name + unit", "name_unit_codebook": "Name + unit + codebook"}
    lines = [
        r"\begin{table}[t]",
        r"\caption{Open-world decoy matcher over 1,315 target candidates. Gold top-1 accuracy is measured with the true construct present. ``Recall at zero false bindings'' is the largest recall retained by a single score threshold while binding none of the nine construct-level orphans. The last column reports the frozen operating summary.}",
        r"\label{tab:app-correspondence-decoy-matcher}",
        r"\label{tab:app_decoy_matcher}",
        r"\centering\scriptsize",
        r"\setlength{\tabcolsep}{5pt}",
        r"\begin{tabular}{P{0.25\linewidth}cccP{0.30\linewidth}}",
        r"\toprule Matcher evidence & Gold top-1 & Recall at zero FBR & Orphans & Frozen operating summary \\",
        r"\midrule",
    ]
    for key in ("name_only", "name_plus_unit", "name_unit_codebook"):
        sweep = audit["sweeps"][key]
        best_zero = max((row["recall"] for row in sweep["threshold_curve"] if row["false_bindings"] == 0), default=0)
        if key == "name_unit_codebook":
            summary = "threshold: 8/9 recall, 0 FBR; margin: 9/9 recall, 5 FBR"
        else:
            summary = "no operating point meeting the 8/9 recall target"
        lines.append(table_row(f"{labels[key]} & {sweep['gold_present_accuracy']}/9 & {best_zero}/9 & 9 & {summary}"))
    lines += [r"\bottomrule\end{tabular}", r"\end{table}"]
    write_tex("table_a7_decoy_matcher.tex", lines)


def table_a8_llm_panel() -> None:
    data = load("experiments/crta_v3_e2_open_panel_v1/SUMMARY_V1.json")
    pretty = {
        "qwen3_8b": "Qwen3-8B",
        "qwen3_14b": "Qwen3-14B",
        "qwen3_32b": "Qwen3-32B",
        "gemma_3_27b_it": "Gemma-3-27B-IT",
        "medgemma_4b_it": "MedGemma-4B-IT",
        "medgemma_27b_it": "MedGemma-27B-IT",
        "olmo_3_1_32b_instruct": "OLMo-3.1-32B-Instruct",
    }
    order = ["qwen3_8b", "qwen3_14b", "qwen3_32b", "gemma_3_27b_it", "medgemma_4b_it", "medgemma_27b_it", "olmo_3_1_32b_instruct"]
    lines = [
        r"\begin{table}[t]",
        r"\caption{Open-weight measurement-extraction panel. A materializable output can be converted into the frozen three-endpoint table; finite pooled contrasts additionally require evaluable mapped labels. Only Qwen3-8B separates from the matched-wrong condition.}",
        r"\label{tab:app-extraction-model-panel}",
        r"\label{tab:app_llm_panel}",
        r"\centering\scriptsize",
        r"\setlength{\tabcolsep}{4pt}",
        r"\begin{tabular}{P{0.23\linewidth}ccP{0.235\linewidth}P{0.235\linewidth}}",
        r"\toprule Model & Materializable & Complete & LLM $-$ matched-wrong & LLM $-$ documented pipeline \\",
        r"\midrule",
    ]
    for key in order:
        row = data["models"][key]
        material = "yes" if row.get("materializable", False) else "no"
        complete = "yes" if row.get("complete", False) else "no"
        if (
            "A1_llm_minus_placebo" in row
            and math.isfinite(float(row["A1_llm_minus_placebo"].get("mean", float("nan"))))
        ):
            a1 = record_text(row["A1_llm_minus_placebo"])
            a3 = record_text(row["A3_llm_minus_pipeline"], bold_if_separated=False)
        else:
            a1 = "not evaluable"
            a3 = "not evaluable"
        lines.append(table_row(f"{pretty[key]} & {material} & {complete} & {a1} & {a3}"))
    lines += [
        r"\bottomrule\end{tabular}",
        r"\vspace{2pt}\parbox{0.96\linewidth}{\footnotesize \emph{Note.} ``Complete'' means that all 30 endpoint--seed cell files exist. MedGemma-4B-IT is nevertheless not evaluable: its materialized table assigns source valid-code sets that do not overlap the observed codes for smoking and hypertension, leaving no finite mapped source labels for those endpoints.}",
        r"\end{table}",
    ]
    write_tex("table_a8_llm_panel.tex", lines)


def table_a9_loo() -> None:
    data = load("experiments/crta_v3_stage_endpoint_expansion_loo_v1/SUMMARY_V1.json")
    lines = [
        r"\begin{table}[H]",
        r"\caption{Leave-one-endpoint-out robustness for the ten-endpoint real-data interaction. Each row recomputes the endpoint-cluster bootstrap after omitting the named endpoint.}",
        r"\label{tab:app-composition-loo}",
        r"\label{tab:app_loo}",
        r"\centering\scriptsize",
        r"\setlength{\tabcolsep}{6pt}",
        r"\begin{tabular}{P{0.32\linewidth}P{0.30\linewidth}cc}",
        r"\toprule Omitted endpoint & Mean $I^*_{MC}$ [95\% CI] & Win rate & CI above zero \\",
        r"\midrule",
    ]
    all_row = data["all_endpoints"]
    lines.append(table_row(f"None (all 10) & {record_text(all_row, bold_if_separated=False)} & {unsigned(all_row['win'],2)} & yes"))
    for endpoint, row in data["leave_one_out"].items():
        lines.append(table_row(f"{tex_name(endpoint)} & {record_text(row, bold_if_separated=False)} & {unsigned(row['win'],2)} & {'yes' if row['ci_excludes_zero'] and row['ci95'][0] > 0 else 'no'}"))
    lines += [r"\bottomrule\end{tabular}", r"\end{table}"]
    write_tex("table_a9_loo.tex", lines)


def table_a10_relation() -> None:
    nhkn = load("experiments/crta_v3_pam_constraint_relations_v1/SUMMARY_V1.json")
    nhkn_rep = load("experiments/crta_v3_pam_constraint_relations_v1_rep1/SUMMARY_V1.json")
    hrs = load("experiments/crta_v3_m3_sign_probe_v1/SUMMARY_V1.json")
    cam = load("experiments/crta_v3_camels_sign_probe_v2/SUMMARY_V2.json")
    cam_llm = load("experiments/crta_v3_camels_sign_probe_llm_v1/SUMMARY_V2.json")
    cam_ext = load("experiments/crta_v3_camels_query_extension_v1/SUMMARY_V1.json")
    tree = load("experiments/crta_v3_mcr_factorial_semisynth_v1/SUMMARY_V1.json")
    rows = [
        ("Real", "NHANES--KNHANES", "XGB", 256, "6 endpoints", nhkn["V_SIGN_CONTENT_flip_must_hurt"], None, nhkn["declared_sign_vs_free_tax_expected"], None),
        ("Real", "NHANES--KNHANES replication", "XGB", 256, "6 endpoints", nhkn_rep["V_SIGN_CONTENT_flip_must_hurt"], None, nhkn_rep["declared_sign_vs_free_tax_expected"], None),
        ("Real", r"NHANES/\newline KNHANES--HRS", "XGB", "var.", "7 endpoints", hrs["GS_P1_identification_flipped"], None, hrs["GS_P3_utility_vs_free"], None),
        ("Real", "CAMELS keyed", "XGB", "var.", "12 basins", cam["GCv2_P1_identification"]["log1p_rmse"], None, cam["GCv2_P2_utility"]["log1p_rmse"], None),
        ("Real", "CAMELS extracted", "XGB", "var.", "12 basins", cam_llm["GCv2_P1_identification"]["log1p_rmse"], None, cam_llm["GCv2_P2_utility"]["log1p_rmse"], None),
        ("Real", "CAMELS extension", "XGB", "var.", "120 basins", cam_ext["sections"]["X1_content_documented_vs_flipped"]["extended"], None, cam_ext["sections"]["X2_utility_documented_vs_free"]["extended"], None),
    ]
    for section, learner, budget in (("xgb_K32", "XGB", 32), ("xgb_K512", "XGB", 512), ("histgb_K32", "HistGB", 32), ("histgb_K512", "HistGB", 512)):
        block = tree["primary"][section]
        for family in FAMILIES:
            op = block["P3b_ops_alone"].get(family)
            incremental = block["P3b_signs_given_ops"].get(family)
            rows.append(("Controlled", FAMILY_LABEL[family], learner, budget, "20 realizations", block["relation_vs_flipped"][family], op, block["P3b_relation_utility"][family], incremental))
    lines = [
        r"\begin{longtable}{P{0.07\linewidth}P{0.12\linewidth}P{0.06\linewidth}P{0.04\linewidth}P{0.08\linewidth}P{0.14\linewidth}P{0.14\linewidth}P{0.14\linewidth}P{0.14\linewidth}}",
        r"\caption{Full relation summary. In real data, content compares declared with reversed directions; in the controlled benchmark, it compares correct with matched-wrong relations. Operation-value utility and executable utility use the same free reference. Increment versus value is the paired descriptive contrast $Q_R^{\mathrm{exec}}-Q_R^{\mathrm{value}}$; it and operation-value utility are not evaluated for the additive family because that family has no nontrivial operation-value arm. Real-data settings use their native metrics, so magnitudes are not comparable to controlled $\Delta Q$.}\label{tab:app-relation-full}\label{tab:app_relation_full}\\",
        r"\toprule Scope & Setting / family & Learner & $K$ & Unit & Content & Value utility & Executable utility & Increment vs. value \\",
        r"\midrule\endfirsthead",
        r"\multicolumn{9}{c}{\tablename\ \thetable\ (continued)}\\",
        r"\toprule Scope & Setting / family & Learner & $K$ & Unit & Content & Value utility & Executable utility & Increment vs. value \\",
        r"\midrule\endhead",
        r"\bottomrule\endfoot",
    ]
    previous = None
    for scope, setting, learner, budget, unit, content, value, executable, incremental in rows:
        if previous is not None and scope != previous:
            lines.append(r"\addlinespace[2pt]")
        lines.append(table_row(f"{scope} & {setting} & {learner} & {budget} & {unit} & {record_text(content)} & {record_text(value) if value is not None else '---'} & {record_text(executable)} & {record_text(incremental) if incremental is not None else '---'}"))
        previous = scope
    lines.append(r"\end{longtable}")
    write_tex("table_a10_relation.tex", lines)


def table_correspondence_interfaces() -> None:
    """Summarize correspondence content and utility by predictive interface."""
    exam = load("experiments/crta_v3_m1m2_layer_ladder_v1/SUMMARY_V1.json")
    survey_xgb = load(
        "experiments/crta_v3_m1m2_stage_factorial_v1/SUMMARY_V1.json"
    )
    survey_hist = load(
        "experiments/crta_v3_binding_backbone_generality_v1/SUMMARY_V1.json"
    )["sections"]["K256"]
    rows = (
        (
            "Examination columns / explicit binding",
            "Content sensitivity",
            "correct binding $-$ deranged binding",
            exam["R1_columns_vs_placebo"],
        ),
        (
            "Examination columns / canonical aggregation",
            "Content sensitivity",
            "declared grouping $-$ matched random partition",
            exam["R2_grouping_vs_placebo"],
        ),
        (
            "Survey columns / XGB binding",
            "Content sensitivity",
            "correct binding $-$ deranged binding",
            survey_xgb["S2_binding_content"],
        ),
        (
            "Survey columns / XGB binding",
            "Utility",
            "correct binding $-$ no added bound columns",
            survey_xgb["desc_columns_at_stage"],
        ),
        (
            "Survey columns / HistGB binding",
            "Content sensitivity",
            "correct binding $-$ deranged binding",
            survey_hist["S5_P1_binding_content"],
        ),
        (
            "Survey columns / HistGB binding",
            "Utility",
            "correct binding $-$ no added bound columns",
            survey_hist["S5_P2_columns_on_stage"],
        ),
    )
    lines = [
        r"\begin{table}[H]",
        r"\caption{Correspondence contrasts by interface. Content sensitivity compares supplied binding or grouping with a capacity-matched wrong assignment; utility compares supplied correspondence with the component-specific no-correspondence reference. Positive values favor the supplied arm. Examination rows use query-SD-normalized RMSE gains; survey rows use AUROC gains, so their magnitudes are not compared.}",
        r"\label{tab:app-correspondence-interfaces}",
        r"\centering\scriptsize",
        r"\setlength{\tabcolsep}{3pt}",
        r"\begin{tabular}{P{0.27\linewidth}P{0.15\linewidth}P{0.31\linewidth}P{0.21\linewidth}}",
        r"\toprule Interface & Estimand & Contrast & Mean [95\% CI] \\",
        r"\midrule",
    ]
    for interface, estimand, contrast, record in rows:
        lines.append(table_row(
            f"{interface} & {estimand} & {contrast} & {record_text(record)}"
        ))
    lines += [r"\bottomrule\end{tabular}", r"\end{table}"]
    write_tex("table_correspondence_interfaces.tex", lines)


def table_exam_no_bridge_reference() -> None:
    data = load("experiments/crta_v3_exam_no_bridge_reference_v1/SUMMARY_V1.json")
    contrasts = data["contrasts"]
    rows = (
        ("Content", "supplied shared bridge $-$ deranged shared bridge",
         contrasts["content_S_minus_W"]),
        ("Utility", "supplied shared bridge $-$ domain-local reference",
         contrasts["utility_S_minus_R"]),
        ("Reference--wrong", "domain-local reference $-$ deranged shared bridge",
         contrasts["reference_minus_wrong_R_minus_W"]),
    )
    lines = [
        r"\begin{table}[H]",
        r"\caption{Width-matched examination correspondence audit at $K=256$. Every arm allocates two columns per non-endpoint member and preserves one materialized member-value location per row before native missingness. Positive endpoints count the six seed-averaged endpoint effects. Intervals hierarchically resample endpoints and paired seeds.}",
        r"\label{tab:app-exam-no-bridge}",
        r"\centering\scriptsize",
        r"\setlength{\tabcolsep}{2pt}",
        r"\begin{tabular}{P{0.15\linewidth}P{0.43\linewidth}P{0.20\linewidth}P{0.13\linewidth}}",
        r"\toprule Estimand & Contrast & Mean [95\% CI] & Positive endpoints \\",
        r"\midrule",
    ]
    for estimand, contrast, record in rows:
        positive = sum(value > 0.0 for value in record["per_endpoint_mean"].values())
        lines.append(table_row(
            f"{estimand} & {contrast} & {record_text(record)} & {positive}/6"
        ))
    lines += [r"\bottomrule\end{tabular}", r"\end{table}"]
    write_tex("table_exam_no_bridge_reference.tex", lines)


def table_relation_audit_effect() -> None:
    """Render the literature-audit/effect join."""
    data = load("experiments/crta_v3_audit_grade_vs_effect_v1/SUMMARY_N5.json")
    content = data["relation_level"]["content"]
    utility = data["relation_level"]["utility"]
    envelope = content["ordering_envelope"]

    def unit(setting: str, endpoint: str) -> dict:
        matches = [
            row for row in data["units"]
            if row["setting"] == setting and row["endpoint"] == endpoint
        ]
        if len(matches) != 1:
            raise RuntimeError(
                f"N5 expected one unit for {setting}:{endpoint}, got {len(matches)}"
            )
        return matches[0]

    examples = (
        unit("NHANES/KNHANES-HRS", "hematocrit"),
        unit("NHANES/KNHANES-HRS", "bun"),
        unit("NHANES-KNHANES", "dbp"),
        unit("NHANES/KNHANES-HRS", "dbp"),
    )
    lines = [
        r"\begin{table}[H]",
        r"\caption{Post-hoc literature-audit qualification versus predictive effect. Grades are parsed from Table~\ref{tab:app-relation-evidence}; relation mappings come from the frozen declared-direction definitions; effects come from the summaries that generate the unit-level relation table. The selected examples are descriptive, not additional tests.}",
        r"\label{tab:app-relation-audit-effect}",
        r"\centering\scriptsize",
        r"\setlength{\tabcolsep}{4pt}",
        r"\begin{tabular}{P{0.36\linewidth}P{0.23\linewidth}P{0.29\linewidth}}",
        r"\toprule Diagnostic & $\tau_b$ & Exact two-sided $p$ \\",
        r"\midrule",
        table_row(
            f"Medical relation-level content & {effect(content['kendall_tau_b'],3)} & {unsigned(content['exact_permutation_p_two_sided'],3)}"
        ),
        table_row(
            f"Medical relation-level utility & {effect(utility['kendall_tau_b'],3)} & {unsigned(utility['exact_permutation_p_two_sided'],3)}"
        ),
        table_row(
            f"Maximum content alignment over all {envelope['n_orderings_tried']} grade orderings & {effect(envelope['best_tau'],3)} & {unsigned(envelope['best_exact_permutation_p_two_sided'],3)} (selected; not confirmatory)"
        ),
        r"\bottomrule\end{tabular}",
        r"\vspace{4pt}",
        r"\begin{tabular}{P{0.31\linewidth}P{0.25\linewidth}P{0.18\linewidth}P{0.16\linewidth}}",
        r"\toprule Setting / endpoint & Audit category & Content & Utility \\",
        r"\midrule",
    ]
    for row in examples:
        setting = row["setting"].replace("NHANES/KNHANES-HRS", "NHANES/KNHANES--HRS").replace("NHANES-KNHANES", "NHANES--KNHANES")
        grade = "/".join(row["audit_status"])
        lines.append(table_row(
            f"{setting} / {tex_name(row['endpoint'])} & {grade} & {effect(row['content'],3)} & {effect(row['utility'],3)}"
        ))
    lines += [r"\bottomrule\end{tabular}", r"\end{table}"]
    write_tex("table_relation_audit_effect.tex", lines)


def table_camels_per_relation() -> None:
    """Render the committed CAMELS per-relation summary."""
    data = load(
        "experiments/crta_v3_camels_sign_relation_ablation_v1/SUMMARY_GC_REL.json"
    )
    metric = "log1p_rmse"
    rows = (
        ("Both flipped $-$ documented ($B-D$)", data["both_flip_reference"][metric]),
        ("Precipitation flipped, PET documented ($P-D$)", data["single_flip"]["flip_precip_only"][metric]),
        ("PET flipped, precipitation documented ($E-D$)", data["single_flip"]["flip_pet_only"][metric]),
        ("PET conditional when precipitation is flipped ($B-P$)", data["opposite_conditional_effects"]["pet_given_flipped_precip_B_minus_P"][metric]),
        ("Shapley precipitation contribution", data["shapley_effects"]["flip_precip_only"][metric]),
        ("Shapley PET contribution", data["shapley_effects"]["flip_pet_only"][metric]),
    )

    def n6_text(record: dict) -> str:
        mean = effect(record["mean_gain"], 5)
        low, high = record["ci95"]
        text = f"{mean} [{effect(low,4)}, {effect(high,4)}]"
        return rf"\textbf{{{text}}}" if record["separated"] else text

    lines = [
        r"\begin{table}[H]",
        r"\caption{Frozen-before-execution CAMELS per-relation ablation. The four observed arms are documented ($D$), precipitation-only flipped ($P$), PET-only flipped ($E$), and both flipped ($B$). The metric is log1p RMSE and gain is arm minus documented, so positive values mean that changing the declared direction worsened prediction. Intervals cluster by query basin.}",
        r"\label{tab:app-camels-per-relation}",
        r"\centering\scriptsize",
        r"\setlength{\tabcolsep}{4pt}",
        r"\begin{tabular}{P{0.57\linewidth}P{0.29\linewidth}c}",
        r"\toprule Contrast & Mean [95\% CI] & Separated \\",
        r"\midrule",
    ]
    for name, record in rows:
        lines.append(table_row(
            f"{name} & {n6_text(record)} & {'yes' if record['separated'] else 'no'}"
        ))
    lines += [r"\bottomrule\end{tabular}", r"\end{table}"]
    write_tex("table_camels_per_relation.tex", lines)


def table_a11_registry() -> None:
    rows = [
        ("Measurement polarity panel", "Confirmatory", "Pass", "3-endpoint content and utility separate", r"Table~\ref{tab:app-measurement-full}"),
        ("Ten-endpoint measurement extension", "Frozen-before-execution extension", "Qualified", "descriptive gain; matched-wrong coverage gate fails", r"Table~\ref{tab:app-measurement-full}"),
        ("Measurement mismatch dose and support ladder", "Frozen-before-execution + post-result budget completion / descriptive support extension", "Pass", "original 12 strata pass; six added K=512 strata pass the same consistency checks; the five-point support ladder documents all absolute arms", r"Figures~\ref{fig:app-measurement-dose} and~\ref{fig:app-mismatch-support-ladder}; Table~\ref{tab:app-measurement-dose-stats}"),
        ("Correspondence interfaces", "Confirmatory + frozen-before-execution extensions", "Qualified", "binding content separates; tree utility and canonical aggregation do not", r"Table~\ref{tab:app-correspondence-interfaces}"),
        ("Four-arm correspondence, XGB", "Exploratory existing-cell analysis", "Mixed", r"all four arms reported: measurement-off simple effect unresolved; measurement-supplied simple effect positive", r"Section~\ref{sec:app-correspondence-resolution}"),
        ("Conditional correspondence, HistGB", "Post-result frozen confirmation", "Fail rule", "8/10 positive but endpoint Student-$t$ interval crosses zero; no positive or no-effect claim", r"Section~\ref{sec:app-correspondence-resolution}"),
        ("Examination domain-local reference", "Post-result reference extension", "Qualified pass", "utility separates under primary, BCa, and studentized intervals; endpoint Student-$t$ narrowly crosses zero", r"Table~\ref{tab:app-exam-no-bridge}"),
        ("Real utility resolution", "Post-hoc power diagnostic", "Descriptive", "cluster-level MDE separates resolution-limited clinical panels from the CAMELS-120 boundary", r"Table~\ref{tab:app-real-utility-resolution}"),
        ("Real-data relation direction contrasts", "Confirmatory + frozen-before-execution extensions", "Qualified", "content separates in all three primary settings; utility remains unresolved", r"Table~\ref{tab:app-relation-full}"),
        ("Controlled relation interfaces", "Frozen-before-execution confirmatory benchmark", "Pass", "executable-direction utility separates across the tree family--budget grid; operation-value utility does not", r"Table~\ref{tab:app-relation-full}"),
        ("Controlled relation capacity", "Additional frozen sensitivity", "Fail stability", "no family--budget stratum is stable across every frozen one-factor alternative", r"Section~\ref{sec:app-relation-value-interface}"),
        ("Constituent-absence registry search", "Post-result outcome-blind audit", "Zero eligible", "constituent removal remains a controlled mechanism probe only", r"Section~\ref{sec:app-relation-value-interface}"),
        ("Joint M/C surface", "Frozen-before-execution extension", "Pass", "moderate rectangle separates in all 6 tree strata", r"Figure~\ref{fig:app-mc-surface}"),
        ("Controlled source-label ladder", "Frozen-before-execution extension", "Pass", "all six curves decline; crossing in final interval", r"Figure~\ref{fig:app-controlled-integrity-ladder}"),
        ("Null-source falsification", "Frozen-before-execution extension", "Fail", "negative interactions separate in pairwise/sparse; no universal routing-mechanism claim", r"Table~\ref{tab:app-target-only-wrong-transfer}"),
        ("Real source-label ladder", "Frozen-before-execution extension", "Fail", "flat/rising; controlled mechanism does not transfer", r"Figure~\ref{fig:app-real-source-ladders}"),
        ("Real source-only measurement ladder", "Frozen-before-execution extension", "Fail", "flat/rising under the source-only measurement axis", r"Figure~\ref{fig:app-real-source-ladders}"),
        ("Source-feature rendering lesion", "Frozen-before-execution extension", "Fail", "flat; neither attenuation criterion passes", r"Figure~\ref{fig:app-real-lesions}"),
        ("Source-feature column permutation", "Frozen-before-execution extension", "Fail", "flat; neither attenuation criterion passes", r"Figure~\ref{fig:app-real-lesions}"),
        ("Support-label lesion", "Frozen-before-execution extension", "Pass", "only tested real-data lesion passing both attenuation criteria", r"Figure~\ref{fig:app-real-lesions}"),
        ("Value redundancy/equivariance", "Frozen-before-execution extension", "Pass", "magnitude nonredundant; sign-equivariance criterion passes", r"Table~\ref{tab:app-relation-value-interface}"),
        ("Partially monotone MLP", "Frozen-before-execution extension", "Fail", "directional-utility grid does not pass", r"Table~\ref{tab:app-relation-monotone-mlp}"),
        ("CAMELS per-relation ablation", "Frozen-before-execution extension", "Qualified", "precipitation carries essentially the joint effect; PET contrast is not separated", r"Table~\ref{tab:app-camels-per-relation}"),
        ("Audit qualification versus effect", "Post-hoc robustness", "Qualified", "medical audit categories do not align with content or utility", r"Table~\ref{tab:app-relation-audit-effect}"),
        ("Open-world decoy compiler", "Frozen-before-execution extension", "Qualified", "high-recall abstention; operating tradeoff reported exactly", r"Table~\ref{tab:app-correspondence-decoy-matcher}; Figure~\ref{fig:app-correspondence-decoy-damage}"),
        ("Seven-model extraction panel", "Frozen-before-execution extension", "Qualified", "one model separates; six fail or are incomplete", r"Table~\ref{tab:app-extraction-model-panel}"),
        ("Ten-endpoint LOO", "Post-hoc robustness", "Pass", "all ten leave-one-out intervals remain above zero", r"Table~\ref{tab:app-composition-loo}"),
        ("CAMELS 120-basin extension", "Frozen-before-execution extension", "Pass", "content replicates; utility has a narrow scale-specific interval", r"Table~\ref{tab:app-relation-full}"),
        ("Real supplied transfer vs target-only", "Additional transfer-abstention summary", "Pass anchor", "supplied $M+C$ transfer beats target-only; not component utility", r"Section~\ref{sec:app-controlled-boundaries}"),
        ("TransTab correspondence", "Post-result mechanism extension", "Qualified", "four-arm bridge decomposition scopes name/token content, shared identity, and false-bridge effects", r"Table~\ref{tab:app-transtab-correspondence}"),
        ("CARTE M/C/R", "Post-result learner-coverage extension", "Qualified", "K=512 correspondence content; utility, measurement, relation remain scoped", r"Table~\ref{tab:app-carte-mcr}"),
        ("Higher-order M/C/R interaction", "Frozen-before-execution extension", "Fail gate", "no third stacking-layer claim", r"Section~\ref{sec:app-negative-results}"),
        ("Second HRS factorial pair", "Optional/not run", "Not run", "licensed-data scope would require new authorization", r"Section~\ref{sec:app-negative-results}"),
        ("Document-compiled Auto-C campaign", "Predates component draft", "Separate", "not pooled with M/C/R and not semantic-specificity evidence", r"Section~\ref{sec:app-autoc}"),
        ("Published TabLLM printed-number audit", "Retrospective external reanalysis", "Qualified", "aggregate conclusion survives; dataset benefit--harm decomposition is heterogeneous", r"Section~\ref{sec:app-tabllm-reproduction}"),
        ("TabLLM released-code reproduction", "Post-hoc compatibility reproduction", "Qualified", "stable-reference macro harm is unresolved; dataset-level heterogeneity remains", r"Section~\ref{sec:app-tabllm-reproduction}"),
    ]
    lines = [
        r"\begin{longtable}{P{0.23\linewidth}P{0.16\linewidth}P{0.10\linewidth}P{0.31\linewidth}P{0.13\linewidth}}",
        r"\caption{Audit and failure registry. ``Fail'' denotes failure of the stated prespecified criterion, not a failed computation. Optional tests without completed summaries are explicitly marked not run and are not interpreted as results.}\label{tab:app_registry}\label{tab:app-analysis-registry}\\",
        r"\toprule Test & Analysis status & Verdict & Consequence & Location \\",
        r"\midrule\endfirsthead",
        r"\multicolumn{5}{c}{\tablename\ \thetable\ (continued)}\\",
        r"\toprule Test & Analysis status & Verdict & Consequence & Location \\",
        r"\midrule\endhead",
        r"\bottomrule\endfoot",
    ]
    for test, status, verdict, consequence, location in rows:
        lines.append(table_row(f"{test} & {status} & {verdict} & {consequence} & {location}"))
    lines.append(r"\end{longtable}")
    write_tex("table_a11_registry.tex", lines)


def table_factorial_c_simple_effects() -> None:
    data = load("experiments/crta_v3_conditional_c_exploratory_v1/SUMMARY_V1.json")
    panel = data["factorial_four_arm_transparency"]
    rows = panel["endpoint_rows"]
    lines = [
        r"\begin{table}[H]",
        r"\caption{Complete XGB four-arm transparency for the pre-existing ten-endpoint survey factorial at $K=256$. The upper panel reports endpoint means of the raw arm AUROCs after averaging seeds within direction and then directions. The lower panel reports the two correspondence simple effects on raw AUROC and on the prespecified polarity-invariant score $f(A)=\max(A,1-A)$, applied per cell before differencing. These are point estimates; the text reports the endpoint-cluster Student-$t$ intervals.}",
        r"\label{tab:app-factorial-c-simple-effects}",
        r"\centering\scriptsize",
        r"\setlength{\tabcolsep}{4pt}",
        r"\begin{tabular}{P{0.27\linewidth}rrrr}",
        r"\toprule Endpoint & $A_{00}$ & $A_{01}$ & $A_{10}$ & $A_{11}$ \\",
        r"\midrule",
    ]
    for endpoint, row in rows.items():
        arms = row["arm_means_raw_auroc"]
        lines.append(table_row(
            f"{tex_name(endpoint)} & {arms['a00_base']:.3f} & "
            f"{arms['a01_columns']:.3f} & {arms['a10_stage']:.3f} & "
            f"{arms['a11_stage_columns']:.3f}"
        ))
    lines += [
        r"\bottomrule\end{tabular}",
        r"\vspace{4pt}",
        r"\begin{tabular}{P{0.27\linewidth}rrrr}",
        r"\toprule Endpoint & raw $A_{01}-A_{00}$ & raw $A_{11}-A_{10}$ & $f(A_{01})-f(A_{00})$ & $f(A_{11})-f(A_{10})$ \\",
        r"\midrule",
    ]
    for endpoint, row in rows.items():
        lines.append(table_row(
            f"{tex_name(endpoint)} & {effect(row['a01_minus_a00'], 3)} & "
            f"{effect(row['a11_minus_a10'], 3)} & "
            f"{effect(row['folded_a01_minus_a00'], 3)} & "
            f"{effect(row['folded_a11_minus_a10'], 3)}"
        ))
    lines += [r"\bottomrule\end{tabular}", r"\end{table}"]
    write_tex("table_factorial_c_simple_effects.tex", lines)


def plot_reconstructibility_proxy() -> None:
    """Plot the stored realization-by-rung controlled proxy observations."""
    csv_path = (
        REPO_ROOT
        / "experiments/crta_v3_reconstruction_utility_proxy_v1/CELL_RUNG_PROXY_V1.csv"
    )
    summary = load(
        "experiments/crta_v3_reconstruction_utility_proxy_v1/SUMMARY_V1.json"
    )
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 912 or summary.get("n_rows") != 912:
        raise RuntimeError("The controlled reconstruction proxy must contain 912 rows")

    families = (("pairwise", "Pairwise"), ("sparse", "Sparse"))
    columns = (
        ("xgb", 32, "XGB, $K=32$"),
        ("histgb", 32, "HistGB, $K=32$"),
        ("xgb", 512, "XGB, $K=512$"),
        ("histgb", 512, "HistGB, $K=512$"),
    )
    fig, axes = plt.subplots(2, 4, figsize=(7.0, 3.15), sharex=True, sharey=True)
    for row_index, (family, family_label) in enumerate(families):
        for column_index, (backbone, support, title) in enumerate(columns):
            ax = axes[row_index, column_index]
            selected = [
                row
                for row in rows
                if row["family"] == family
                and row["backbone"] == backbone
                and int(row["support"]) == support
            ]
            key = f"{family}|{backbone}|K={support}"
            record = summary["strata"][key]
            if len(selected) != record["n_observations"]:
                raise RuntimeError(f"Proxy row-count mismatch for {key}")
            x = np.asarray([float(row["reconstruction_r2"]) for row in selected])
            y = np.asarray([float(row["utility"]) for row in selected])
            fit = record["model_utility_on_reconstruction_r2"]
            fitted = np.polyfit(x, y, 1)
            if not np.allclose(
                fitted, [fit["slope"], fit["intercept"]], rtol=0, atol=1e-10
            ):
                raise RuntimeError(f"Stored proxy fit does not reproduce for {key}")
            ax.scatter(
                x,
                y,
                s=8,
                color=BLUE,
                alpha=0.24,
                linewidths=0,
                rasterized=True,
                zorder=2,
            )
            x_line = np.asarray([min(-0.10, float(x.min())), 1.02])
            ax.plot(
                x_line,
                fit["intercept"] + fit["slope"] * x_line,
                color="#1f4e79",
                linewidth=1.25,
                zorder=3,
            )
            ax.text(
                0.05,
                0.93,
                f"$r={fit['pearson_r']:.3f}$\n"
                f"LORO $R^2={record['loro_new_realization_prediction_from_reconstruction']['r2']:.3f}$",
                transform=ax.transAxes,
                ha="left",
                va="top",
                fontsize=6.25,
                color="#29495c",
            )
            ax.axhline(0, color="#777777", linewidth=0.55, zorder=1)
            ax.grid(color=LIGHT_GRAY, linewidth=0.45, zorder=0)
            ax.set_xlim(-0.12, 1.05)
            ax.set_ylim(-0.035, 0.325)
            if row_index == 0:
                ax.set_title(title)
            if column_index == 0:
                ax.set_ylabel(f"{family_label}\nPredictive utility")
            if row_index == 1:
                ax.set_xlabel("Reconstruction $R^2$")
    fig.tight_layout(h_pad=0.65, w_pad=0.55)
    save(fig, "appendix_figure_reconstructibility_proxy")


def plot_tabllm_support_by_dataset() -> None:
    """Plot the exact stored per-dataset stable-anonymous support trajectories."""
    data = load("experiments/tabllm_ranon_support_ladder_v1/SUMMARY_V1.json")
    supports = tuple(int(value) for value in data["shots"])
    if supports != (0, 4, 32, 512) or len(data["datasets"]) != 9:
        raise RuntimeError("The TabLLM support panel must have nine datasets and four rungs")
    names = {
        "bank": "Bank",
        "blood": "Blood",
        "calhousing": "California",
        "car": "Car",
        "creditg": "Credit-g",
        "diabetes": "Diabetes",
        "heart": "Heart",
        "income": "Income",
        "jungle": "Jungle",
    }
    x = np.arange(len(supports), dtype=float)
    fig, axes = plt.subplots(3, 3, figsize=(7.0, 4.25), sharex=True, sharey=True)
    for ax, dataset in zip(axes.ravel(), data["panel"]):
        values = np.asarray(
            [float(data["datasets"][dataset]["utility"][str(k)]) for k in supports]
        )
        ax.plot(x, values, color=BLUE, marker="o", linewidth=1.25, markersize=3.4)
        ax.axhline(0, color="#777777", linewidth=0.6)
        ax.grid(axis="y", color=LIGHT_GRAY, linewidth=0.5)
        ax.set_title(names[dataset])
        ax.set_ylim(-0.085, 0.325)
        ax.set_xticks(x, supports)
    for ax in axes[-1, :]:
        ax.set_xlabel("Target support $k$")
    for ax in axes[:, 0]:
        ax.set_ylabel(r"Utility $S-R_{\mathrm{anon}}$")
    fig.tight_layout(h_pad=0.65, w_pad=0.75)
    save(fig, "appendix_figure_tabllm_support_by_dataset")


def main() -> None:
    figure_main()
    table_a1_measurement()
    table_a2_mismatch_fixed()
    table_a3_real_units()
    table_a4_factorial()
    table_a5_value_channel()
    table_a6_monotone()
    table_a7_decoy_matcher()
    table_a8_llm_panel()
    table_a9_loo()
    table_a10_relation()
    table_correspondence_interfaces()
    table_exam_no_bridge_reference()
    table_relation_audit_effect()
    table_camels_per_relation()
    table_a11_registry()
    table_factorial_c_simple_effects()
    print(f"Wrote appendix assets to {FIG_DIR} and {GEN_DIR}")


def figure_main() -> None:
    plot_a1_polarity()
    plot_a2_mismatch_grid()
    plot_mismatch_support_ladder()
    plot_correspondence_interfaces()
    plot_a7_decoy_damage()
    plot_redundancy_ladder()
    plot_a3_mc_surface()
    plot_controlled_real_mechanism()
    plot_a6_real_lesion_panel()
    plot_reconstructibility_proxy()
    plot_tabllm_support_by_dataset()
    print(f"Wrote appendix figures to {FIG_DIR}")


if __name__ == "__main__":
    if "--figures-only" in sys.argv:
        figure_main()
    else:
        main()
