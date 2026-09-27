#!/usr/bin/env python3
"""Two-panel Results figure using frozen pairwise-XGB, K=32 results.

Reuse the manuscript plotting style, measurement loader, and reconstruction
figure's input/hash helpers. Original reconstruction assets are never written.
Plot absolute intended/reference mean nMSE, with utility shown only as the gap.
Error bars are omitted because dose-wise intervals are not consistently available.
"""
import json
from pathlib import Path
import shutil

import make_figure1_utility_drivers_reconstruction as original
import make_main_figures as mf
import matplotlib.pyplot as plt
import numpy as np


def main():
    mismatch_path = mf.REPO_ROOT / "experiments/crta_v3_mcr_mismatch_dose_v1/SUMMARY_V1.json"
    mismatch = json.loads(mismatch_path.read_text())
    removal = json.loads(original.REDUNDANCY_SUMMARY.read_text())
    section = mismatch["sections"]["xgb_K32"]["pairwise"]
    doses = np.asarray(mismatch["doses"])
    mean_m = np.asarray(section["mean_U_by_dose"])
    records = mf.measurement_arm_records("xgb", 32, "pairwise")
    paired = np.asarray([[r[f"raw_d{d}"]["nmse"] - r["decode"]["nmse"]
                          for d in doses] for r in records])
    np.testing.assert_allclose(paired.mean(axis=0), mean_m, atol=1e-12)
    np.testing.assert_array_equal(paired[:, 0], 0)
    rungs = removal["sections"]["32"]["rung_table"]["xgb|pairwise"]
    steps = np.asarray(sorted(map(int, rungs)))
    np.testing.assert_array_equal(steps, np.arange(7))
    mean_r = np.asarray([rungs[str(k)]["U"]["mean"] for k in steps])
    arm_difference = [rungs[str(k)]["arm_mean_nmse"]["free"] -
                      rungs[str(k)]["arm_mean_nmse"]["op_true"] for k in steps]
    np.testing.assert_allclose(arm_difference, mean_r, atol=1e-12)
    np.testing.assert_allclose([mean_m[-1], mean_r[0], mean_r[-1]],
                               [.259, .002, .242], atol=.0005)
    intended_m = np.full(len(doses), np.mean([r["decode"]["nmse"] for r in records]))
    reference_m = np.asarray([np.mean([r[f"raw_d{d}"]["nmse"] for r in records])
                              for d in doses])
    intended_r = np.asarray([rungs[str(k)]["arm_mean_nmse"]["op_true"] for k in steps])
    reference_r = np.asarray([rungs[str(k)]["arm_mean_nmse"]["free"] for k in steps])
    np.testing.assert_allclose(reference_m-intended_m, mean_m, atol=1e-12)
    np.testing.assert_allclose(reference_r-intended_r, mean_r, atol=1e-12)

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.65))
    panels = [
        (doses, intended_m, reference_m, "(a) Schema mismatch", "Mismatched source features",
         "utility: 0 → +.259"),
        (steps, intended_r, reference_r, "(b) Constituent removal", "Constituent inputs removed",
         "utility: +.002 → +.242"),
    ]
    for ax, (x, intended, reference, title, xlabel, annotation) in zip(axes, panels):
        ax.fill_between(x, intended, reference, color="#9db9cc", alpha=.23,
                        linewidth=0, zorder=1)
        ax.plot(x, intended, color=mf.BLUE, marker="s", linestyle="-",
                markersize=3.8, linewidth=1.5, zorder=3, label="Intended")
        ax.plot(x, reference, color=mf.ORANGE, marker="o", linestyle="--",
                markersize=3.8, linewidth=1.5, zorder=4, label="Reference")
        ax.text(.035, .94, annotation, transform=ax.transAxes,
                ha="left", va="top", fontsize=8, color=mf.GRAY)
        ax.set_title(title, loc="left", fontsize=9, pad=7)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Mean normalized error\n(lower is better)")
        ax.set_xticks(x)
        ax.set_xlim(x[0]-.3, x[-1]+.4)
        ax.set_ylim(.66, 1.045)
        ax.set_yticks([.7, .8, .9, 1.0])
        ax.grid(axis="y", color=mf.LIGHT_GRAY, linewidth=.6)
        ax.set_axisbelow(True)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(.52, 1.01),
               ncol=2, frameon=False, fontsize=8, handlelength=2.1)
    fig.subplots_adjust(left=.10, right=.98, bottom=.21, top=.77, wspace=.36)

    stem = mf.OUT_DIR / "figure1_utility_drivers"
    # An older file already occupies the requested PNG name. Preserve it once
    # before replacing that name; repeated builds leave this archive untouched.
    manifest_path = stem.with_name(stem.name + "_provenance.json")
    if not manifest_path.exists():
        for extension in ("png", "pdf"):
            dest = stem.with_suffix("." + extension)
            backup = stem.with_name(stem.name + "_before_two_panel").with_suffix("." + extension)
            if dest.exists() and not backup.exists():
                shutil.copy2(dest, backup)
    for extension in ("pdf", "png"):
        kwargs = {"metadata": original.PDF_METADATA} if extension == "pdf" else {"dpi": 300}
        fig.savefig(stem.with_suffix("." + extension), facecolor="white", **kwargs)
    plt.close(fig)

    sources = [mismatch_path, original.REDUNDANCY_SUMMARY,
               Path(__file__).resolve(), Path(original.__file__).resolve(), Path(mf.__file__).resolve()]
    sources += sorted((mismatch_path.parent / "pairwise").glob("r*/metrics.json"))
    provenance = {
        "scope": "pairwise XGB, K=32; 20 realizations per panel",
        "metric": "Mean normalized error (nMSE), lower is better; shaded utility = reference nMSE - intended nMSE",
        "intervals": "Omitted consistently across both panels; no new intervals computed.",
        "panels": {
            "a": {"name": "Schema mismatch", "x": doses.tolist(), "intended_nmse": intended_m.tolist(), "reference_nmse": reference_m.tolist(), "utility": mean_m.tolist()},
            "b": {"name": "Constituent removal", "x": steps.tolist(), "intended_nmse": intended_r.tolist(), "reference_nmse": reference_r.tolist(), "utility": mean_r.tolist()},
        },
        "inputs": {str(p.relative_to(mf.REPO_ROOT)): original.sha256_file(p) for p in sources},
        "outputs": {str(stem.with_suffix('.'+ext).relative_to(mf.REPO_ROOT)):
                    original.sha256_file(stem.with_suffix('.'+ext)) for ext in ("pdf", "png")},
    }
    manifest_path.write_text(json.dumps(provenance, indent=2) + "\n")
    print("Sources:", mismatch_path, original.REDUNDANCY_SUMMARY, sep="\n  ")
    print("Reused: make_main_figures.py style/measurement loader; reconstruction figure helpers")
    print("Written:", stem.with_suffix(".pdf"), stem.with_suffix(".png"), manifest_path, sep="\n  ")


if __name__ == "__main__":
    main()
