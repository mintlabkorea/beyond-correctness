#!/usr/bin/env python3
"""Paired comparison of TransTab v1 and its transformers-4.30 replication."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = ROOT / "experiments/crta_v3_mcr_transtab_c_v1"
DEFAULT_REPLICATION = ROOT / "experiments/crta_v3_mcr_transtab_c_tf430_v1"
FAMILIES = ("additive", "pairwise", "sparse")
SUPPORTS = (32, 512)
ARMS = ("correct", "c_wrong", "c_reference")
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


def load_tree(root: Path) -> dict[tuple[str, int], dict[str, Any]]:
    cells: dict[tuple[str, int], dict[str, Any]] = {}
    for family in FAMILIES:
        for realization in range(N_REALIZATIONS):
            path = root / family / f"r{realization:02d}" / "metrics.json"
            if not path.is_file():
                raise FileNotFoundError(path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("status") != "complete":
                raise RuntimeError(f"incomplete payload: {path}")
            if payload.get("family") != family or payload.get("realization") != realization:
                raise RuntimeError(f"path/payload identity mismatch: {path}")
            if payload.get("supports") != list(SUPPORTS) or payload.get("arms") != list(ARMS):
                raise RuntimeError(f"unexpected support/arm contract: {path}")
            cells[(family, realization)] = payload
    return cells


def paired_stats(values: np.ndarray, key: tuple[Any, ...]) -> dict[str, Any]:
    rng = np.random.default_rng(stable_seed("transtab_tf430_compare_v1", *key))
    draws = values[rng.integers(0, len(values), size=(N_BOOT, len(values)))].mean(axis=1)
    low, high = np.quantile(draws, [0.025, 0.975])
    return {
        "n": len(values),
        "mean": float(np.mean(values)),
        "ci95": [float(low), float(high)],
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "values": values.tolist(),
    }


def q(payload: dict[str, Any], support: int, arm: str) -> float:
    return -float(payload["results"][str(support)][arm]["nmse"])


def contrast(payload: dict[str, Any], support: int, first: str, second: str) -> float:
    return q(payload, support, first) - q(payload, support, second)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-root", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--replication-root", type=Path, default=DEFAULT_REPLICATION)
    parser.add_argument("--out-root", type=Path, default=None)
    args = parser.parse_args()
    out_root = args.replication_root if args.out_root is None else args.out_root
    baseline = load_tree(args.baseline_root)
    replication = load_tree(args.replication_root)

    construction_mismatches: list[str] = []
    baseline_versions: set[str] = set()
    replication_versions: set[str] = set()
    for key in sorted(baseline):
        old = baseline[key]
        new = replication[key]
        baseline_versions.add(str(old["versions"]["transformers"]))
        replication_versions.add(str(new["versions"]["transformers"]))
        if old.get("cell_audit") != new.get("cell_audit"):
            construction_mismatches.append(f"{key}:cell_audit")
        for support in SUPPORTS:
            for arm in ARMS:
                old_audit = old["results"][str(support)][arm]["audit"]
                new_audit = new["results"][str(support)][arm]["audit"]
                for field in (
                    "source_frame_sha256", "support_frame_sha256", "query_frame_sha256"
                ):
                    if old_audit.get(field) != new_audit.get(field):
                        construction_mismatches.append(
                            f"{key}:K{support}:{arm}:{field}"
                        )

    sections: dict[str, Any] = {}
    for support in SUPPORTS:
        support_section: dict[str, Any] = {"arms": {}, "contrasts": {}}
        for arm in ARMS:
            arm_section: dict[str, Any] = {}
            for family in FAMILIES:
                values = np.asarray([
                    q(replication[(family, realization)], support, arm)
                    - q(baseline[(family, realization)], support, arm)
                    for realization in range(N_REALIZATIONS)
                ])
                arm_section[family] = paired_stats(
                    values, (support, "arm", arm, family)
                )
            support_section["arms"][arm] = arm_section
        for name, (first, second) in CONTRASTS.items():
            contrast_section: dict[str, Any] = {}
            for family in FAMILIES:
                values = np.asarray([
                    contrast(replication[(family, realization)], support, first, second)
                    - contrast(baseline[(family, realization)], support, first, second)
                    for realization in range(N_REALIZATIONS)
                ])
                old_mean = float(np.mean([
                    contrast(baseline[(family, realization)], support, first, second)
                    for realization in range(N_REALIZATIONS)
                ]))
                new_mean = float(np.mean([
                    contrast(replication[(family, realization)], support, first, second)
                    for realization in range(N_REALIZATIONS)
                ]))
                stats = paired_stats(values, (support, "contrast", name, family))
                stats.update({
                    "baseline_mean": old_mean,
                    "replication_mean": new_mean,
                    "mean_sign_preserved": bool(np.sign(old_mean) == np.sign(new_mean)),
                })
                contrast_section[family] = stats
            support_section["contrasts"][name] = contrast_section
        sections[str(support)] = support_section

    report = {
        "status": "complete",
        "comparison_is_post_result_descriptive": True,
        "baseline_root": str(args.baseline_root),
        "replication_root": str(args.replication_root),
        "cells_each": len(baseline),
        "bootstrap_draws": N_BOOT,
        "baseline_transformers_versions": sorted(baseline_versions),
        "replication_transformers_versions": sorted(replication_versions),
        "construction_hashes_identical": not construction_mismatches,
        "construction_mismatches": construction_mismatches,
        "delta_definition": "replication minus baseline on Q or Q contrast",
        "no_posthoc_equivalence_margin": True,
        "supports": sections,
    }
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "ENV_CONFORMANCE_COMPARISON_V1.json").write_text(
        json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# TransTab transformers-4.30 environment comparison", "",
        f"Status: complete; {len(baseline)} paired realization cells per environment.",
        f"Versions: {sorted(baseline_versions)} -> {sorted(replication_versions)}.",
        f"Construction hashes identical: {not construction_mismatches}.",
        "Deltas are replication minus baseline; no post-hoc equivalence margin is used.", "",
    ]
    for support in SUPPORTS:
        lines.extend([f"## K={support}", "", "### Frozen contrast deltas", ""])
        for name in CONTRASTS:
            for family, stats in sections[str(support)]["contrasts"][name].items():
                lines.append(
                    f"- {name}/{family}: old={stats['baseline_mean']:+.6f}, "
                    f"new={stats['replication_mean']:+.6f}, "
                    f"delta={stats['mean']:+.6f} "
                    f"[{stats['ci95'][0]:+.6f}, {stats['ci95'][1]:+.6f}], "
                    f"sign_preserved={stats['mean_sign_preserved']}"
                )
        lines.extend(["", "### Arm Q deltas", ""])
        for arm in ARMS:
            for family, stats in sections[str(support)]["arms"][arm].items():
                lines.append(
                    f"- {arm}/{family}: {stats['mean']:+.6f} "
                    f"[{stats['ci95'][0]:+.6f}, {stats['ci95'][1]:+.6f}]"
                )
        lines.append("")
    (out_root / "ENV_CONFORMANCE_COMPARISON_V1.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": "complete",
        "cells": len(baseline),
        "construction_hashes_identical": not construction_mismatches,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
