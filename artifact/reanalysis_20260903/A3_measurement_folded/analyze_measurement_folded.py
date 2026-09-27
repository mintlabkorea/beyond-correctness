#!/usr/bin/env python3
"""Raw and cellwise-folded AUROC sensitivity for measurement panels."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
FOCUSED = REPO / "experiments/crta_v3_survey_label_panel_v1"
EXT_ROOTS = {
    "nh2kn": REPO / "experiments/crta_v3_survey_label_panel_endpoint_expansion_nh2kn_v1",
    "kn2nh": REPO / "experiments/crta_v3_survey_label_panel_endpoint_expansion_kn2nh_v1",
}
REPS = 10_000


def f(x: float, folded: bool) -> float:
    x = float(x)
    return max(x, 1.0 - x) if folded else x


def focused_data(folded: bool) -> dict[str, np.ndarray]:
    out = {}
    for p in sorted(FOCUSED.glob("*/seed_*/metrics.json")):
        d = json.loads(p.read_text()); a = d["auroc"]["256"]
        out.setdefault(d["target"], []).append([
            f(a["pipeline_table"], folded) - f(a["placebo_table"], folded),
            f(a["pipeline_table"], folded) - f(a["raw"], folded),
        ])
    return {k: np.asarray(v, float) for k, v in out.items()}


def extension_data(folded: bool) -> dict[str, dict[str, np.ndarray]]:
    out = {}
    for direction, root in EXT_ROOTS.items():
        for p in sorted(root.glob("*/seed_*/metrics.json")):
            d = json.loads(p.read_text()); a = d["auroc"]["256"]
            vals = [
                f(a["pipeline_table"], folded) - f(a["placebo_table"], folded),
                f(a["pipeline_table"], folded) - f(a["raw"], folded),
            ]
            out.setdefault(d["target"], {}).setdefault(direction, []).append(vals)
    return {t: {d: np.asarray(v, float) for d, v in by_d.items()}
            for t, by_d in out.items()}


def endpoint_descriptives() -> tuple[list[dict], list[dict]]:
    arm_rows = []
    contrast_rows = []
    panels = [("focused_3_endpoint", "nh2kn", FOCUSED)] + [
        ("extension_10_endpoint_bidirectional", direction, root)
        for direction, root in EXT_ROOTS.items()
    ]
    for panel, direction, root in panels:
        grouped = {}
        for path in sorted(root.glob("*/seed_*/metrics.json")):
            d = json.loads(path.read_text()); grouped.setdefault(d["target"], []).append(d["auroc"]["256"])
        for endpoint, records in sorted(grouped.items()):
            for arm, role in (("pipeline_table", "intended"), ("raw", "reference"),
                              ("placebo_table", "wrong")):
                raw = np.asarray([a[arm] for a in records], float)
                raw = raw[np.isfinite(raw)]; folded = np.maximum(raw, 1.0 - raw)
                arm_rows.append({
                    "panel": panel, "direction": direction, "endpoint": endpoint,
                    "role": role, "arm": arm, "n_finite": len(raw),
                    "mean_raw_auroc": float(raw.mean()),
                    "mean_folded_auroc": float(folded.mean()),
                })
            for estimand, right in (("intended_minus_wrong_content", "placebo_table"),
                                    ("intended_minus_reference_utility", "raw")):
                for scale in ("raw", "folded_cellwise"):
                    values = []
                    for a in records:
                        left_value, right_value = float(a["pipeline_table"]), float(a[right])
                        if np.isfinite(left_value) and np.isfinite(right_value):
                            values.append(f(left_value, scale == "folded_cellwise") -
                                          f(right_value, scale == "folded_cellwise"))
                    contrast_rows.append({
                        "panel": panel, "direction": direction, "endpoint": endpoint,
                        "scale": scale, "estimand": estimand, "n_finite_pairs": len(values),
                        "mean_contrast": float(np.mean(values)),
                    })
    return arm_rows, contrast_rows


def boot_focused_one(data, j: int) -> tuple[float, np.ndarray, int]:
    """Exact parent hierarchy: each contrast resets RNG to the frozen seed."""
    names = sorted(data)
    values = {t: data[t][:, j][np.isfinite(data[t][:, j])] for t in names}
    flat = np.concatenate(list(values.values()))
    rng = np.random.default_rng(20260819)
    draws = np.empty(REPS)
    for b in range(REPS):
        parts = []
        for i in rng.integers(0, len(names), len(names)):
            x = values[names[int(i)]]
            parts.append(x[rng.integers(0, len(x), len(x))])
        draws[b] = np.concatenate(parts).mean()
    return float(flat.mean()), draws, len(flat)


def boot_extension_one(data, j: int, key: str) -> tuple[float, np.ndarray, int]:
    """Exact parent endpoint/direction/seed hierarchy, filtering finite pairs."""
    targets = sorted(data); directions = ("nh2kn", "kn2nh")
    values = {
        t: {d: data[t][d][:, j][np.isfinite(data[t][d][:, j])] for d in directions}
        for t in targets
    }
    seed = int(hashlib.sha256(f"label_panel_10|20260820|{key}".encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    draws = np.empty(REPS)
    for b in range(REPS):
        clusters = []
        for i in rng.integers(0, len(targets), len(targets)):
            t = targets[int(i)]
            dm = []
            for d in directions:
                x = values[t][d]
                dm.append(x[rng.integers(0, len(x), len(x))].mean())
            clusters.append(np.mean(dm))
        draws[b] = np.mean(clusters)
    point = float(np.mean([
        np.mean([values[t][d].mean() for d in directions]) for t in targets
    ]))
    n = sum(len(values[t][d]) for t in targets for d in directions)
    return point, draws, n


def main() -> int:
    rows = []
    point_checks = {}
    for panel in ("focused_3_endpoint", "extension_10_endpoint_bidirectional"):
        for folded in (False, True):
            data = focused_data(folded) if panel.startswith("focused") else extension_data(folded)
            scale = "folded_cellwise" if folded else "raw"
            for j, estimand in enumerate(("intended_minus_wrong_content", "intended_minus_reference_utility")):
                if panel.startswith("focused"):
                    point, draws, n = boot_focused_one(data, j)
                else:
                    raw_key = "pipeline_vs_placebo" if j == 0 else "raw_minus_pipeline"
                    key = raw_key if not folded else "folded_" + raw_key
                    point, draws, n = boot_extension_one(data, j, key)
                rows.append({
                    "panel": panel, "scale": scale, "estimand": estimand,
                    "estimate": point,
                    "ci95_low": float(np.quantile(draws, .025)),
                    "ci95_high": float(np.quantile(draws, .975)),
                    "n_seed_cells": n,
                })
                point_checks[(panel, scale, j)] = point

    parent3 = json.loads((FOCUSED / "SUMMARY_V1.json").read_text())
    parent10 = json.loads((REPO / "experiments/crta_v3_survey_label_panel_endpoint_expansion_v1/SUMMARY_V1.json").read_text())
    expected = [
        (point_checks[("focused_3_endpoint", "raw", 0)], parent3["A2_pipeline_vs_placebo"]["mean_gain"]),
        (point_checks[("focused_3_endpoint", "raw", 1)], -parent3["raw_vs_pipeline_descriptive"]["mean_gain"]),
        (point_checks[("extension_10_endpoint_bidirectional", "raw", 0)], parent10["P1_pipeline_vs_placebo"]["mean"]),
        (point_checks[("extension_10_endpoint_bidirectional", "raw", 1)], -parent10["raw_minus_pipeline_descriptive"]["mean"]),
    ]
    max_error = max(abs(a-b) for a,b in expected)
    if max_error > 1e-12:
        raise AssertionError(f"raw parent point mismatch: {max_error}")
    with (HERE / "measurement_folded_sensitivity.csv").open("w", newline="") as fobj:
        w = csv.DictWriter(fobj, list(rows[0])); w.writeheader(); w.writerows(rows)
    arm_rows, endpoint_contrast_rows = endpoint_descriptives()
    for name, output_rows in (("endpoint_arm_aurocs.csv", arm_rows),
                              ("endpoint_contrasts.csv", endpoint_contrast_rows)):
        with (HERE / name).open("w", newline="") as fobj:
            w = csv.DictWriter(fobj, list(output_rows[0])); w.writeheader(); w.writerows(output_rows)
    payload = {
        "status": "complete", "results": rows, "max_raw_parent_point_error": max_error,
        "folding": "Each arm AUROC A is transformed to max(A, 1-A) before contrasts.",
        "bootstrap": {
            "reps": REPS,
            "focused": "targets then seeds; base seed 20260819",
            "extension": "endpoint clusters, paired directions, then seeds; base seed 20260820",
        },
        "coverage_note": (
            "Extension content contrasts use finite intended/wrong pairs; the frozen exact "
            "coverage gate still fails at cancer_history/kn2nh (4/10). Utility contrasts are finite."
        ),
        "machine_readable_outputs": ["measurement_folded_sensitivity.csv",
                                     "endpoint_arm_aurocs.csv", "endpoint_contrasts.csv"],
        "sources": [str(FOCUSED.relative_to(REPO))] +
                   [str(x.relative_to(REPO)) for x in EXT_ROOTS.values()],
    }
    (HERE / "summary.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"written": [str(HERE / "measurement_folded_sensitivity.csv"),
                                  str(HERE / "endpoint_arm_aurocs.csv"),
                                  str(HERE / "endpoint_contrasts.csv"), str(HERE / "summary.json")],
                      "results": rows}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
