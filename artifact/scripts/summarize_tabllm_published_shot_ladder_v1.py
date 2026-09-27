#!/usr/bin/env python3
"""Adjudicate the TabLLM published shot-ladder retrospective, v1.

Frozen design: iclr_latex_v3/TABLLM_PUBLISHED_SHOT_LADDER_FREEZE_V1.md.
Inputs are the dual-source-verified printed means (EXTRACTED_TABLES_V1.json).
Estimand identities are computed in integer cents so the identity check
content = utility + harm is exact, then converted to AUROC units.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/tabllm_published_shot_ladder_v1"
EXTRACTED = EXP / "EXTRACTED_TABLES_V1.json"
OUT = EXP / "SUMMARY_V1.json"

SHOTS = (0, 4, 8, 16, 32, 64, 128, 256, 512)
BOOT_SEED = 20260902
BOOT_REPS = 10_000
SESOI = 0.02
PREDICTION = {"primary_decay": [0.056, 0.096], "central": 0.076}
DROP_DATASET = "car"  # pre-declared concentration check


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def student_t_ci(values: np.ndarray) -> List[float]:
    # t_{n-1,.975}; n=9 fixed by the panel -> t_8 = 2.306.
    n = len(values)
    assert n == 9
    t975 = 2.306
    se = values.std(ddof=1) / np.sqrt(n)
    return [float(values.mean() - t975 * se), float(values.mean() + t975 * se)]


def boot_mean_ci(values: np.ndarray, stream_index: int) -> List[float]:
    rng = np.random.default_rng(BOOT_SEED + stream_index)
    draws = values[rng.integers(0, len(values), size=(BOOT_REPS, len(values)))]
    means = draws.mean(axis=1)
    return [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]


def boot_ratio_ci(num: np.ndarray, den: np.ndarray, stream_index: int) -> List[float]:
    rng = np.random.default_rng(BOOT_SEED + stream_index)
    idx = rng.integers(0, len(num), size=(BOOT_REPS, len(num)))
    ratios = num[idx].mean(axis=1) / den[idx].mean(axis=1)
    return [float(np.percentile(ratios, 2.5)), float(np.percentile(ratios, 97.5))]


def main() -> int:
    data = json.loads(EXTRACTED.read_text())
    assert data["cross_source_mismatches"] == 0
    assert data["zero_shot_anchor"].startswith("PASS")
    table = data["table"]
    datasets = sorted(table)
    assert len(datasets) == 9

    # cents[dataset][arm][k]
    cents = {
        ds: {arm: {int(k): cell["mean_cents"] for k, cell in arms.items()}
             for arm, arms in table[ds].items()}
        for ds in datasets
    }

    identity_violations = 0
    est: Dict[str, Dict[int, Dict[str, float]]] = {}
    for ds in datasets:
        est[ds] = {}
        for k in SHOTS:
            s, w, r = (cents[ds]["S"][k], cents[ds]["W"][k], cents[ds]["R_pub"][k])
            utility_c, content_c, harm_c = s - r, s - w, r - w
            if content_c != utility_c + harm_c:
                identity_violations += 1
            est[ds][k] = {
                "utility": utility_c / 100.0,
                "content": content_c / 100.0,
                "harm": harm_c / 100.0,
            }

    def panel(stat: str, k: int, subset=None) -> np.ndarray:
        keys = subset if subset is not None else datasets
        return np.array([est[ds][k][stat] for ds in keys])

    # Macro absolute trajectories (mandatory).
    trajectories = {
        arm: {str(k): float(np.mean([cents[ds][arm][k] for ds in datasets]) / 100.0)
              for k in SHOTS}
        for arm in ("S", "W", "R_pub")
    }

    # Named statistics with fixed bootstrap stream indices.
    stream = 0
    stats: Dict[str, dict] = {}

    def add_paired(name: str, values: np.ndarray, extra: dict | None = None):
        nonlocal stream
        entry = {
            "mean": float(values.mean()),
            "bootstrap_ci95": boot_mean_ci(values, stream),
            "student_t_ci95": student_t_ci(values),
            "per_dataset": {ds: float(v) for ds, v in zip(datasets, values)},
            "win": float((values > 0).mean()),
            "stream_index": stream,
        }
        if extra:
            entry.update(extra)
        stats[name] = entry
        stream += 1

    u0, u512 = panel("utility", 0), panel("utility", 512)
    u4, u16 = panel("utility", 4), panel("utility", 16)
    drop = [ds for ds in datasets if ds != DROP_DATASET]

    add_paired("primary_decay_utility_0_minus_512", u0 - u512, {
        "drop_car_mean": float((panel("utility", 0, drop)
                                - panel("utility", 512, drop)).mean()),
    })
    add_paired("secondary_decay_utility_4_minus_512", u4 - u512)
    add_paired("step_decay_utility_0_minus_16", u0 - u16)
    add_paired("step_decay_utility_16_minus_512", u16 - u512)
    add_paired("decay_content_0_minus_512",
               panel("content", 0) - panel("content", 512))
    add_paired("decay_harm_0_minus_512", panel("harm", 0) - panel("harm", 512))

    stats["retention_utility_512_over_0"] = {
        "point": float(u512.mean() / u0.mean()),
        "bootstrap_ci95": boot_ratio_ci(u512, u0, stream),
        "stream_index": stream,
    }
    stream += 1

    levels = {}
    for k in SHOTS:
        values = panel("utility", k)
        levels[str(k)] = {
            "mean": float(values.mean()),
            "bootstrap_ci95": boot_mean_ci(values, stream),
            "student_t_ci95": student_t_ci(values),
            "stream_index": stream,
        }
        stream += 1

    # Frozen verdict rule.
    primary = stats["primary_decay_utility_0_minus_512"]
    lo_b, hi_b = primary["bootstrap_ci95"]
    lo_t = primary["student_t_ci95"][0]
    supported = (lo_b > 0 and lo_t > 0 and primary["mean"] >= SESOI
                 and primary["drop_car_mean"] > 0)
    contradicted = (hi_b < 0) or (-SESOI < lo_b and hi_b < SESOI)
    verdict = ("SUPPORTED" if supported
               else "CONTRADICTED" if contradicted else "INCONCLUSIVE")
    sign_agrees = (np.sign(stats["secondary_decay_utility_4_minus_512"]["mean"])
                   == np.sign(primary["mean"]))

    payload = {
        "analysis_status": "frozen_retrospective_adjudicated",
        "protocol": "iclr_latex_v3/TABLLM_PUBLISHED_SHOT_LADDER_FREEZE_V1.md",
        "metric": "published mean test AUROC (5 seeds; macro one-vs-rest for Car); "
                  "positive favors S = List Template",
        "extracted_sha256": sha256_file(EXTRACTED),
        "identity_violations": identity_violations,
        "frozen_prediction": PREDICTION,
        "prediction_hit": bool(PREDICTION["primary_decay"][0]
                               <= primary["mean"]
                               <= PREDICTION["primary_decay"][1]),
        "verdict": verdict,
        "verdict_conjuncts": {
            "bootstrap_low_gt_0": lo_b > 0,
            "student_t_low_gt_0": lo_t > 0,
            "mean_ge_sesoi": primary["mean"] >= SESOI,
            "drop_car_gt_0": primary["drop_car_mean"] > 0,
        },
        "secondary_sign_agrees": bool(sign_agrees),
        "utility_levels_macro": levels,
        "contrasts": stats,
        "absolute_macro_trajectories": trajectories,
        "bootstrap": {"reps": BOOT_REPS, "seed": BOOT_SEED,
                      "scheme": "percentile over 9 dataset clusters, "
                                "one substream per named statistic"},
        "sesoi": SESOI,
    }
    OUT.write_text(json.dumps(payload, indent=1, sort_keys=True))
    print(f"verdict={verdict}  primary={primary['mean']:+.4f} "
          f"boot[{lo_b:+.4f},{hi_b:+.4f}] t_low={lo_t:+.4f} "
          f"drop_car={primary['drop_car_mean']:+.4f} "
          f"prediction_hit={payload['prediction_hit']}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
