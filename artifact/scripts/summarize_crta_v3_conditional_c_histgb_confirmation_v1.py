#!/usr/bin/env python3
"""Summarize the frozen two-direction HistGB conditional-C confirmation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

import analyze_crta_v3_conditional_c_exploratory_v1 as stats


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOTS = {
    "nh2kn": ROOT / "experiments/crta_v3_conditional_c_histgb_nh2kn_v1",
    "kn2nh": ROOT / "experiments/crta_v3_conditional_c_histgb_kn2nh_v1",
}
DEFAULT_OUT = ROOT / "experiments/crta_v3_conditional_c_histgb_v1/SUMMARY_V1.json"
PROTOCOL = ROOT / "iclr_latex_v3/CONDITIONAL_C_HISTGB_CONFIRMATION_FREEZE_V1.md"
PAIRS = {
    "conditional_utility": ("a11_stage_columns", "a10_stage"),
    "content": ("a11_stage_columns", "pl_columns_at_stage"),
    "matched_wrong_harm": ("a10_stage", "pl_columns_at_stage"),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load(root: Path, pair: tuple[str, str]) -> dict[str, list[float]]:
    result: dict[str, list[float]] = {}
    for path in sorted(root.glob("*/seed_*/metrics.json")):
        cell = json.loads(path.read_text(encoding="utf-8"))
        provenance = cell.get("confirmation_provenance", {})
        if (
            provenance.get("protocol_sha256") != sha256_file(PROTOCOL)
            or provenance.get("xgb_derangement_exact_match") is not True
        ):
            raise RuntimeError(f"missing or conflicting provenance: {path}")
        arms = cell["auroc"]["256"]
        result.setdefault(str(cell["target"]), []).append(
            float(arms[pair[0]]) - float(arms[pair[1]])
        )
    counts = {key: len(value) for key, value in result.items()}
    if len(result) != 10 or set(counts.values()) != {10}:
        raise RuntimeError(f"incomplete panel at {root}: {counts}")
    return result


def summarize(directions: dict[str, dict[str, list[float]]]) -> dict[str, Any]:
    endpoints, estimates, audit = stats.endpoint_estimates(directions)
    best = int(np.argmax(estimates))
    return {
        "mean": float(np.mean(estimates)),
        "median": float(np.median(estimates)),
        "positive_endpoint_clusters": int(np.sum(estimates > 0)),
        "best_endpoint": endpoints[best],
        "drop_best_mean": float(np.mean(np.delete(estimates, best))),
        "endpoint_estimates": audit,
        "intervals": stats.bootstrap_intervals(estimates),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nh2kn-root", type=Path, default=DEFAULT_ROOTS["nh2kn"])
    parser.add_argument("--kn2nh-root", type=Path, default=DEFAULT_ROOTS["kn2nh"])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    roots = {"nh2kn": args.nh2kn_root, "kn2nh": args.kn2nh_root}
    results = {
        name: summarize({
            direction: load(root, pair) for direction, root in roots.items()
        })
        for name, pair in PAIRS.items()
    }
    utility = results["conditional_utility"]
    t_low = utility["intervals"]["student_t_ci95"][0]
    verdict = bool(
        utility["mean"] > 0
        and t_low > 0
        and utility["positive_endpoint_clusters"] >= 8
        and utility["drop_best_mean"] > 0
    )
    payload = {
        "analysis_status": "review_triggered_confirmation_frozen_after_exploratory_xgb",
        "estimand": "conditional correspondence utility given supplied measurement",
        "learner": "sklearn HistGradientBoostingRegressor",
        "support_k": 256,
        "confirmation_rule": "mean>0; endpoint t-CI low>0; >=8/10 endpoints positive; drop-best mean>0",
        "confirmation_passed": verdict,
        "results": results,
        "provenance": {
            "protocol_sha256": sha256_file(PROTOCOL),
            "summarizer_sha256": sha256_file(Path(__file__)),
            "roots": {key: str(value) for key, value in roots.items()},
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({
        "confirmation_passed": verdict,
        "conditional_utility_mean": utility["mean"],
        "conditional_utility_t_ci95": utility["intervals"]["student_t_ci95"],
        "positive_endpoint_clusters": utility["positive_endpoint_clusters"],
        "drop_best_mean": utility["drop_best_mean"],
        "written": str(args.out),
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
