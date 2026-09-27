#!/usr/bin/env python3
"""Summarize the review-triggered CARTE M/C/R extension."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "experiments/crta_v3_mcr_carte_v1"
FAMILIES = ("additive", "pairwise", "sparse")
SUPPORTS = (32, 512)
N_REALIZATIONS = 20
N_BOOT = 10_000
CONTRASTS = {
    "M_content_correct_vs_wrong": ("correct", "m_wrong"),
    "M_utility_correct_vs_raw": ("correct", "m_raw"),
    "C_content_correct_vs_wrong": ("correct", "c_wrong"),
    "C_utility_correct_vs_reference": ("correct", "c_reference"),
    "R_content_correct_vs_wrong": ("correct", "r_wrong"),
    "R_utility_correct_vs_free": ("correct", "r_free"),
}


def stable_seed(*parts: Any) -> int:
    digest = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
    return int.from_bytes(digest[:8], "little") % (2**32 - 1)


def interval(values: np.ndarray, key: tuple[Any, ...]) -> dict[str, Any]:
    rng = np.random.default_rng(stable_seed("mcr_carte_summary_v1", *key))
    n = len(values)
    draws = values[rng.integers(0, n, size=(N_BOOT, n))].mean(axis=1)
    low, high = np.quantile(draws, [0.025, 0.975])
    mean = float(np.mean(values))
    win = float(np.mean(values > 0))
    return {
        "n": n,
        "mean": mean,
        "ci95": [float(low), float(high)],
        "win_fraction": win,
        "separated_descriptive": bool(mean > 0 and low > 0 and win >= 0.60),
        "values": values.tolist(),
        "bootstrap_means": draws,
    }


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
            provenance.add(
                tuple(
                    payload.get(key)
                    for key in (
                        "input_sha256",
                        "parent_runner_sha256",
                        "protocol_sha256",
                        "runner_sha256",
                        "pretrained_model_sha256",
                        "fasttext_model_sha256",
                    )
                )
            )
            cells[(family, realization)] = payload
    if len(provenance) > 1:
        raise RuntimeError(f"mixed provenance tree: {len(provenance)} tuples")
    if missing and not args.allow_incomplete:
        raise RuntimeError(f"missing {len(missing)} of 60 cells; first: {missing[0]}")

    sections: dict[str, Any] = {}
    for support in SUPPORTS:
        support_section: dict[str, Any] = {}
        for contrast, (correct_arm, comparator_arm) in CONTRASTS.items():
            family_stats: dict[str, Any] = {}
            bootstrap_by_family: list[np.ndarray] = []
            for family in FAMILIES:
                values: list[float] = []
                for realization in range(N_REALIZATIONS):
                    payload = cells.get((family, realization))
                    if payload is None:
                        continue
                    result = payload["results"][str(support)]
                    # Q(correct) - Q(other) = nmse(other) - nmse(correct).
                    values.append(
                        float(result[comparator_arm]["nmse"])
                        - float(result[correct_arm]["nmse"])
                    )
                if not values:
                    continue
                stats = interval(np.asarray(values, dtype=np.float64), (support, contrast, family))
                bootstrap_by_family.append(stats.pop("bootstrap_means"))
                family_stats[family] = stats
            grid: dict[str, Any] = {"evaluable": len(family_stats) == len(FAMILIES)}
            if grid["evaluable"]:
                minimum = np.min(np.vstack(bootstrap_by_family), axis=0)
                low, high = np.quantile(minimum, [0.025, 0.975])
                grid.update(
                    {
                        "min_family_mean": float(
                            min(stats["mean"] for stats in family_stats.values())
                        ),
                        "min_stat_ci95": [float(low), float(high)],
                        "all_families_descriptively_separated": all(
                            stats["separated_descriptive"]
                            for stats in family_stats.values()
                        ),
                    }
                )
            support_section[contrast] = {"families": family_stats, "grid": grid}
        # The decomposition requested by review: wrong versus reference.
        for component, wrong_key, utility_key, content_key in (
            ("M", "m_wrong", "M_utility_correct_vs_raw", "M_content_correct_vs_wrong"),
            ("C", "c_wrong", "C_utility_correct_vs_reference", "C_content_correct_vs_wrong"),
            ("R", "r_wrong", "R_utility_correct_vs_free", "R_content_correct_vs_wrong"),
        ):
            implied: dict[str, Any] = {}
            for family in FAMILIES:
                utility = support_section[utility_key]["families"].get(family)
                content = support_section[content_key]["families"].get(family)
                if utility is None or content is None:
                    continue
                # Q(wrong)-Q(reference) = utility-content, paired at cell level.
                values = np.asarray(utility["values"]) - np.asarray(content["values"])
                stats = interval(values, (support, component, wrong_key, "wrong_vs_reference"))
                stats.pop("bootstrap_means")
                implied[family] = stats
            support_section[f"{component}_wrong_vs_reference"] = {"families": implied}
        sections[str(support)] = support_section

    provenance_payload = list(next(iter(provenance))) if provenance else []
    summary = {
        "status": "complete" if not missing else "incomplete",
        "review_triggered_post_result_extension": True,
        "cells_complete": len(cells),
        "cells_expected": len(FAMILIES) * N_REALIZATIONS,
        "missing": missing,
        "bootstrap_draws": N_BOOT,
        "score": "Q=-MSE/Var(y_query); positive contrast favors first arm",
        "provenance_tuple": provenance_payload,
        "supports": sections,
    }
    args.input_root.mkdir(parents=True, exist_ok=True)
    (args.input_root / "SUMMARY_V1.json").write_text(
        json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )

    lines = [
        "# CARTE M/C/R review extension",
        "",
        f"Status: {summary['status']} ({len(cells)}/60 realization cells).",
        "Positive values favor correct knowledge; this is a post-result learner-coverage extension.",
        "",
    ]
    for support, support_section in sections.items():
        lines.extend([f"## K={support}", ""])
        for contrast in CONTRASTS:
            lines.append(f"### {contrast}")
            for family, stats in support_section[contrast]["families"].items():
                lines.append(
                    f"- {family}: {stats['mean']:+.6f} "
                    f"[{stats['ci95'][0]:+.6f}, {stats['ci95'][1]:+.6f}], "
                    f"win={stats['win_fraction']:.3f}"
                )
            grid = support_section[contrast]["grid"]
            if grid.get("evaluable"):
                lines.append(
                    f"- min-statistic: min mean={grid['min_family_mean']:+.6f}, "
                    f"CI=[{grid['min_stat_ci95'][0]:+.6f}, "
                    f"{grid['min_stat_ci95'][1]:+.6f}]"
                )
            lines.append("")
        lines.extend(["### Wrong versus reference", ""])
        for component in ("M", "C", "R"):
            for family, stats in support_section[
                f"{component}_wrong_vs_reference"
            ]["families"].items():
                lines.append(
                    f"- {component}/{family}: {stats['mean']:+.6f} "
                    f"[{stats['ci95'][0]:+.6f}, {stats['ci95'][1]:+.6f}]"
                )
        lines.append("")
    (args.input_root / "SUMMARY_V1.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": summary["status"], "cells": len(cells)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
