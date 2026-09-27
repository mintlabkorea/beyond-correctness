#!/usr/bin/env python3
"""Summarize the coherent real M+C transfer pipeline against target only.

The supplied arm is the existing a11 measurement+correspondence pipeline from
the frozen ten-endpoint expansion.  This is a transfer-abstention contrast,
not utility of M or C individually.  Endpoint clusters are the inferential
units; seed and direction are averaged within endpoint.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "experiments/crta_v3_endpoint_source_informativeness_v1/SUMMARY_V1.json"
FREEZE = ROOT / "iclr_latex_v3/REAL_TRANSFER_AND_CONSTITUENT_AUDIT_FREEZE_V1.md"
OUT = ROOT / "experiments/crta_v3_real_transfer_abstention_v1/SUMMARY_V1.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def student_t_summary(values: list[float]) -> dict[str, object]:
    array = np.asarray(values, dtype=float)
    mean = float(np.mean(array))
    sem = float(stats.sem(array))
    critical = float(stats.t.ppf(0.975, df=len(array) - 1))
    return {
        "mean": mean,
        "ci95_student_t": [mean - critical * sem, mean + critical * sem],
        "n_endpoint_clusters": len(array),
        "endpoint_cluster_values": array.tolist(),
        "positive_endpoint_clusters": int(np.sum(array > 0)),
    }


def main() -> int:
    source = json.loads(INPUT.read_text(encoding="utf-8"))
    if not source.get("complete") or source.get("n_endpoint_clusters") != 10:
        raise RuntimeError("expected complete frozen ten-endpoint source panel")
    endpoint_values = {
        endpoint: float(row["target_utility_corrected"])
        for endpoint, row in source["endpoint_clusters"].items()
    }
    endpoint_values_raw = {
        endpoint: float(row["target_utility_raw"])
        for endpoint, row in source["endpoint_clusters"].items()
    }
    direction_values = {}
    for direction, endpoints in source["per_direction"].items():
        values = [float(row["target_utility_corrected"]) for row in endpoints.values()]
        values_raw = [float(row["target_utility_raw"]) for row in endpoints.values()]
        direction_values[direction] = {
            "mean_over_endpoints": float(np.mean(values)),
            "positive_endpoint_clusters": int(np.sum(np.asarray(values) > 0)),
            "raw_mean_over_endpoints": float(np.mean(values_raw)),
            "raw_positive_endpoint_clusters": int(
                np.sum(np.asarray(values_raw) > 0)
            ),
            "n_endpoint_clusters": len(values),
        }
    summary = student_t_summary(list(endpoint_values.values()))
    summary_raw = student_t_summary(list(endpoint_values_raw.values()))
    payload = {
        "analysis_status": (
            "review_triggered_transfer_abstention_summary_of_existing_"
            "prespecified_descriptive_cells"
        ),
        "estimand": (
            "correct documented measurement+correspondence source-transfer "
            "pipeline minus target-only with the same representation and "
            "target support"
        ),
        "interpretation": (
            "transfer-abstention comparison; not component-specific utility "
            "and not a pooled M+C+R estimand"
        ),
        "metrics": {
            "corrected": (
                "f(A)=max(A,1-A), applied separately to each arm before "
                "differencing; positive favors source transfer"
            ),
            "raw": "raw AUROC difference; positive favors source transfer",
        },
        "support_k": 256,
        "summary": summary,
        "summary_corrected": summary,
        "summary_raw": summary_raw,
        "per_endpoint": endpoint_values,
        "per_endpoint_corrected": endpoint_values,
        "per_endpoint_raw": endpoint_values_raw,
        "per_direction": direction_values,
        "provenance": {
            "input_summary_sha256": sha256_file(INPUT),
            "freeze_sha256": sha256_file(FREEZE),
            "summarizer_sha256": sha256_file(Path(__file__)),
        },
    }
    if not math.isfinite(float(summary["mean"])):
        raise RuntimeError("non-finite summary")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
