#!/usr/bin/env python3
"""Summarize the review-triggered TransTab correspondence extension."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "experiments/crta_v3_mcr_transtab_c_v1"
FAMILIES = ("additive", "pairwise", "sparse")
SUPPORTS = (32, 512)
N_REALIZATIONS = 20
N_BOOT = 10_000
CONTRASTS = {
    "C_content_correct_vs_wrong": ("correct", "c_wrong"),
    "C_utility_correct_vs_reference": ("correct", "c_reference"),
    "C_wrong_vs_reference": ("c_wrong", "c_reference"),
}


def stable_seed(*parts: Any) -> int:
    digest = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
    return int.from_bytes(digest[:8], "little") % (2**32 - 1)


def summarize_values(values: np.ndarray, key: tuple[Any, ...]) -> tuple[dict[str, Any], np.ndarray]:
    rng = np.random.default_rng(stable_seed("mcr_transtab_c_summary_v1", *key))
    draws = values[rng.integers(0, len(values), size=(N_BOOT, len(values)))].mean(axis=1)
    low, high = np.quantile(draws, [0.025, 0.975])
    mean = float(np.mean(values))
    win = float(np.mean(values > 0))
    return ({
        "n": len(values),
        "mean": mean,
        "ci95": [float(low), float(high)],
        "win_fraction": win,
        "separated_descriptive": bool(mean > 0 and low > 0 and win >= 0.60),
        "values": values.tolist(),
    }, draws)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()
    cells: dict[tuple[str, int], dict[str, Any]] = {}
    provenance: set[tuple[Any, ...]] = set()
    missing: list[str] = []
    for family in FAMILIES:
        for realization in range(N_REALIZATIONS):
            path = args.input_root / family / f"r{realization:02d}" / "metrics.json"
            if not path.is_file():
                missing.append(str(path))
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("status") != "complete":
                raise RuntimeError(f"incomplete payload: {path}")
            if payload.get("family") != family or payload.get("realization") != realization:
                raise RuntimeError(f"path/payload identity mismatch: {path}")
            provenance.add(tuple(payload.get(key) for key in (
                "input_sha256", "parent_runner_sha256", "semantic_runner_sha256",
                "protocol_sha256", "runner_sha256", "transtab_tree_sha256",
            )))
            cells[(family, realization)] = payload
    if len(provenance) > 1:
        raise RuntimeError(f"mixed provenance tree: {len(provenance)} tuples")
    if missing and not args.allow_incomplete:
        raise RuntimeError(f"missing {len(missing)} of 60 cells; first: {missing[0]}")

    sections: dict[str, Any] = {}
    for support in SUPPORTS:
        support_section: dict[str, Any] = {}
        for contrast, (first, second) in CONTRASTS.items():
            family_stats: dict[str, Any] = {}
            family_draws: list[np.ndarray] = []
            for family in FAMILIES:
                values: list[float] = []
                for realization in range(N_REALIZATIONS):
                    payload = cells.get((family, realization))
                    if payload is None:
                        continue
                    result = payload["results"][str(support)]
                    # Q(first)-Q(second) = nmse(second)-nmse(first).
                    values.append(float(result[second]["nmse"]) - float(result[first]["nmse"]))
                if values:
                    stats, draws = summarize_values(
                        np.asarray(values, dtype=np.float64), (support, contrast, family)
                    )
                    family_stats[family] = stats
                    family_draws.append(draws)
            grid: dict[str, Any] = {"evaluable": len(family_stats) == len(FAMILIES)}
            if grid["evaluable"]:
                minimum = np.min(np.vstack(family_draws), axis=0)
                low, high = np.quantile(minimum, [0.025, 0.975])
                grid.update({
                    "min_family_mean": float(min(v["mean"] for v in family_stats.values())),
                    "min_stat_ci95": [float(low), float(high)],
                    "all_families_descriptively_separated": all(
                        value["separated_descriptive"] for value in family_stats.values()
                    ),
                })
            support_section[contrast] = {"families": family_stats, "grid": grid}
        sections[str(support)] = support_section

    summary = {
        "status": "complete" if not missing else "incomplete",
        "review_triggered_post_result_extension": True,
        "cells_complete": len(cells),
        "cells_expected": len(FAMILIES) * N_REALIZATIONS,
        "missing": missing,
        "bootstrap_draws": N_BOOT,
        "score": "Q=-MSE/Var(y_query); positive contrast favors first arm",
        "provenance_tuple": list(next(iter(provenance))) if provenance else [],
        "supports": sections,
    }
    args.input_root.mkdir(parents=True, exist_ok=True)
    (args.input_root / "SUMMARY_V1.json").write_text(
        json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# TransTab correspondence review extension", "",
        f"Status: {summary['status']} ({len(cells)}/60 realization cells).",
        "Positive values favor the first named arm; post-result learner-coverage extension.", "",
    ]
    for support, section in sections.items():
        lines.extend([f"## K={support}", ""])
        for contrast in CONTRASTS:
            lines.append(f"### {contrast}")
            for family, stats in section[contrast]["families"].items():
                lines.append(
                    f"- {family}: {stats['mean']:+.6f} "
                    f"[{stats['ci95'][0]:+.6f}, {stats['ci95'][1]:+.6f}], "
                    f"win={stats['win_fraction']:.3f}"
                )
            grid = section[contrast]["grid"]
            if grid.get("evaluable"):
                lines.append(
                    f"- min-statistic: min mean={grid['min_family_mean']:+.6f}, "
                    f"CI=[{grid['min_stat_ci95'][0]:+.6f}, {grid['min_stat_ci95'][1]:+.6f}]"
                )
            lines.append("")
    (args.input_root / "SUMMARY_V1.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": summary["status"], "cells": len(cells)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
