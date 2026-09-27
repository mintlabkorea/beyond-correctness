#!/usr/bin/env python3
"""Summarize the frozen controlled relation capacity sensitivity."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "experiments/crta_v3_relation_capacity_sensitivity_v1"
PROTOCOL = ROOT / "iclr_latex_v3/RELATION_CAPACITY_SENSITIVITY_FREEZE_V1.md"
CONFIG_IDS = (
    "depth2", "depth4", "baseline", "depth8", "depth12",
    "l2_0", "l2_10", "trees100", "trees1000",
)
FAMILIES = ("additive", "pairwise", "sparse")
SUPPORTS = (32, 512)
N_BOOT = 10_000
BOOT_SEED = 20260827


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def bootstrap(values: list[float], key: str) -> dict[str, Any]:
    array = np.asarray(values, dtype=np.float64)
    seed = int(hashlib.sha256(f"{BOOT_SEED}|{key}".encode()).hexdigest()[:16], 16)
    rng = np.random.default_rng(seed)
    means = np.mean(array[rng.integers(0, len(array), size=(N_BOOT, len(array)))], axis=1)
    interval = np.quantile(means, [0.025, 0.975])
    return {
        "mean": float(np.mean(array)),
        "ci95": interval.tolist(),
        "win": float(np.mean(array > 0)),
        "n": len(values),
        "values": [float(value) for value in values],
        "positive_and_interval_excludes_zero": bool(np.mean(array) > 0 and interval[0] > 0),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    paths = sorted(args.root.glob("*/r*/metrics.json"))
    if len(paths) != 60:
        raise RuntimeError(f"expected 60 cells, found {len(paths)}")
    cells = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    protocol_hash = sha256_file(PROTOCOL)
    if any(cell.get("protocol_sha256") != protocol_hash for cell in cells):
        raise RuntimeError("protocol hash mismatch")
    if any(cell.get("config_ids") != list(CONFIG_IDS) for cell in cells):
        raise RuntimeError("configuration set/order mismatch")

    results: dict[str, Any] = {}
    stability: dict[str, Any] = {}
    for family in FAMILIES:
        family_cells = [cell for cell in cells if cell["family"] == family]
        if len(family_cells) != 20:
            raise RuntimeError(f"incomplete family {family}")
        results[family] = {}
        stability[family] = {}
        for support in SUPPORTS:
            support_key = str(support)
            results[family][support_key] = {}
            stability[family][support_key] = {}
            contrasts = {
                "total_utility": ("m1c1r1", "m1c1rf"),
            }
            if family != "additive":
                contrasts["incremental_direction"] = ("m1c1r1", "r_op_only")
            for contrast, pair in contrasts.items():
                by_config: dict[str, Any] = {}
                for config_id in CONFIG_IDS:
                    values = []
                    for cell in family_cells:
                        arms = cell["results"][support_key][config_id]
                        values.append(float(arms[pair[0]]["q"]) - float(arms[pair[1]]["q"]))
                    by_config[config_id] = bootstrap(
                        values, f"{family}|{support}|{contrast}|{config_id}"
                    )
                results[family][support_key][contrast] = by_config
                baseline = float(by_config["baseline"]["mean"])
                means = {key: float(value["mean"]) for key, value in by_config.items()}
                ratios = {
                    key: (value / baseline if baseline != 0 else None)
                    for key, value in means.items()
                }
                all_positive = all(value > 0 for value in means.values())
                within_band = bool(
                    baseline > 0
                    and all(ratio is not None and 0.25 <= ratio <= 4.0
                            for ratio in ratios.values())
                )
                stability[family][support_key][contrast] = {
                    "baseline_mean": baseline,
                    "configuration_means": means,
                    "ratios_to_baseline": ratios,
                    "positive_configurations": int(sum(value > 0 for value in means.values())),
                    "all_means_positive": all_positive,
                    "all_ratios_within_quarter_to_fourfold": within_band,
                    "stability_rule_passed": bool(all_positive and within_band),
                    "min_mean": min(means.values()),
                    "max_mean": max(means.values()),
                }

    payload = {
        "analysis_status": "review_triggered_post_result_capacity_sensitivity",
        "score": "Q=-MSE/Var(y_query); positive favors first arm",
        "cells_complete": len(cells),
        "config_ids": list(CONFIG_IDS),
        "bootstrap": {"reps": N_BOOT, "root_seed": BOOT_SEED,
                      "unit": "realization within fixed family"},
        "results": results,
        "stability": stability,
        "provenance": {
            "protocol_sha256": protocol_hash,
            "summarizer_sha256": sha256_file(Path(__file__)),
            "runner_hashes": sorted(set(cell["runner_sha256"] for cell in cells)),
            "parent_runner_hashes": sorted(set(cell["parent_runner_sha256"] for cell in cells)),
        },
    }
    out = args.root / "SUMMARY_V1.json"
    out.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "cells_complete": len(cells),
        "stability_pass_count": sum(
            entry["stability_rule_passed"]
            for family in stability.values()
            for support in family.values()
            for entry in support.values()
        ),
        "stability_cell_count": sum(
            1 for family in stability.values() for support in family.values()
            for _ in support.values()
        ),
        "written": str(out),
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
