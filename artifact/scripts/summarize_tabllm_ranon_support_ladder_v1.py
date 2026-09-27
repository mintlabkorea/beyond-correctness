#!/usr/bin/env python3
"""Validate and summarize the frozen TabLLM S-vs-R_anon support ladder."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "iclr_latex_v3/TABLLM_RANON_SUPPORT_LADDER_FREEZE_V1.md"
DATASETS = (
    "bank", "blood", "calhousing", "car", "creditg",
    "diabetes", "heart", "income", "jungle",
)
ARMS = ("list_template", "list_stable_anonymous")
SHOTS = (0, 4, 32, 512)
SEEDS = (42, 1024, 0, 1, 32)
REPS = 10_000
BOOTSTRAP_SEED = 20260903
T_DF8_975 = 2.306004135204166
SESOI = 0.02


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def read_predictions(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            rows.append(json.loads(line))
    return (
        np.asarray([int(row["row_id"]) for row in rows], dtype=np.int64),
        np.asarray([int(row["label"]) for row in rows], dtype=np.int64),
        np.asarray([row["class_probabilities"] for row in rows], dtype=np.float64),
    )


def auc(labels: np.ndarray, probabilities: np.ndarray) -> float:
    if probabilities.shape[1] == 2:
        return float(roc_auc_score(labels, probabilities[:, 1]))
    return float(roc_auc_score(
        labels, probabilities, multi_class="ovr", average="macro"
    ))


def percentile_interval(draws: np.ndarray) -> list[float]:
    return [float(value) for value in np.quantile(draws, [0.025, 0.975])]


def t_interval(values: np.ndarray) -> list[float]:
    mean = float(values.mean())
    half_width = T_DF8_975 * float(values.std(ddof=1)) / math.sqrt(len(values))
    return [mean - half_width, mean + half_width]


def dataset_bootstrap(values: np.ndarray, seed: int) -> tuple[np.ndarray, list[float]]:
    rng = np.random.default_rng(seed)
    selected = rng.integers(0, len(values), size=(REPS, len(values)))
    draws = values[selected].mean(axis=1)
    return draws, percentile_interval(draws)


def interval_record(values: np.ndarray, seed: int) -> dict[str, Any]:
    draws, boot = dataset_bootstrap(values, seed)
    return {
        "estimate": float(values.mean()),
        "dataset_values": [float(value) for value in values],
        "bootstrap_ci95": boot,
        "student_t_ci95_df8": t_interval(values),
        "bootstrap_draw_mean": float(draws.mean()),
    }


def validate_evidence_cell(
    root: Path, dataset: str, arm: str, shot: int, seed: int
) -> tuple[dict[str, Any], float, dict[str, str], float]:
    cell = root / arm / dataset / f"k{shot}" / f"seed{seed}"
    metrics_path = cell / "metrics.json"
    predictions_path = cell / "predictions.jsonl.gz"
    checkpoint_path = cell / "ia3_finish.pt"
    for path in (metrics_path, predictions_path, checkpoint_path):
        if not path.is_file():
            raise FileNotFoundError(f"missing evidence artifact: {path}")
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    expected = {
        "analysis_status": "frozen_ranon_support_ladder_evidence",
        "dataset": dataset,
        "arm": arm,
        "shot": shot,
        "seed": seed,
        "n_train": shot,
    }
    for key, value in expected.items():
        if metrics.get(key) != value:
            raise RuntimeError(f"{metrics_path}: {key}={metrics.get(key)!r}, expected {value!r}")
    planned = 30 * (shot // 4)
    training = metrics["training"]
    if training["planned_steps"] != planned or training["executed_steps"] != planned:
        raise RuntimeError(f"incomplete training steps in {metrics_path}")
    if metrics["predictions_sha256"] != sha256_file(predictions_path):
        raise RuntimeError(f"prediction hash mismatch in {metrics_path}")
    if metrics["trained_checkpoint_sha256"] != sha256_file(checkpoint_path):
        raise RuntimeError(f"checkpoint hash mismatch in {metrics_path}")

    row_ids, labels, probabilities = read_predictions(predictions_path)
    if len(row_ids) != metrics["n_test"] or len(set(row_ids.tolist())) != len(row_ids):
        raise RuntimeError(f"bad prediction membership in {predictions_path}")
    if not np.isfinite(probabilities).all():
        raise RuntimeError(f"nonfinite probabilities in {predictions_path}")
    if np.max(np.abs(probabilities.sum(axis=1) - 1.0)) > 1e-6:
        raise RuntimeError(f"probabilities do not sum to one in {predictions_path}")
    recomputed_auc = auc(labels, probabilities)
    recomputed_accuracy = float(accuracy_score(labels, np.argmax(probabilities, axis=1)))
    error = max(
        abs(recomputed_auc - float(metrics["metrics"]["auc"])),
        abs(recomputed_accuracy - float(metrics["metrics"]["accuracy"])),
    )
    if error > 1e-12:
        raise RuntimeError(f"metric recomputation mismatch {error} in {metrics_path}")
    hashes = {
        str(path.relative_to(root)): sha256_file(path)
        for path in (metrics_path, predictions_path, checkpoint_path)
    }
    return metrics, recomputed_auc, hashes, error


def verdict(
    primary: dict[str, Any], supervised: dict[str, Any], drop_car: float
) -> tuple[str, list[str]]:
    intervals = (primary["bootstrap_ci95"], primary["student_t_ci95_df8"])
    lower_positive = all(interval[0] > 0 for interval in intervals)
    upper_negative = all(interval[1] < 0 for interval in intervals)
    equivalent = all(
        interval[0] > -SESOI and interval[1] < SESOI for interval in intervals
    )
    same_sign = np.sign(supervised["estimate"]) == np.sign(primary["estimate"])
    supported_checks = {
        "both_primary_lower_bounds_gt_zero": lower_positive,
        "primary_mean_ge_sesoi": primary["estimate"] >= SESOI,
        "drop_car_primary_mean_gt_zero": drop_car > 0,
        "supervised_secondary_same_sign": bool(same_sign),
    }
    if all(supported_checks.values()):
        return "SUPPORTED_WITHIN_FIXED_PANEL", [
            key for key, passed in supported_checks.items() if passed
        ]
    if upper_negative:
        return "CONTRADICTED", ["both_primary_upper_bounds_lt_zero"]
    if equivalent:
        return "CONTRADICTED", ["both_primary_intervals_inside_equivalence_region"]
    return "INCONCLUSIVE", [
        key for key, passed in supported_checks.items() if not passed
    ]


def write_plot(summary: dict[str, Any], path: Path) -> None:
    x = np.arange(len(SHOTS))
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.6), constrained_layout=True)
    for arm, label, color in (
        (ARMS[0], "S: intended names", "#1769aa"),
        (ARMS[1], "R_anon: stable anonymous", "#c45100"),
    ):
        values = [summary["macro"]["arm_auc"][str(shot)][arm] for shot in SHOTS]
        axes[0].plot(x, values, marker="o", linewidth=2, label=label, color=color)
    axes[0].set_xticks(x, [str(shot) for shot in SHOTS])
    axes[0].set_xlabel("Target support k")
    axes[0].set_ylabel("Unweighted macro AUROC")
    axes[0].legend(frameon=False, fontsize=8)

    utility = summary["macro"]["utility"]
    estimates = [utility[str(shot)]["estimate"] for shot in SHOTS]
    intervals = [utility[str(shot)]["bootstrap_ci95"] for shot in SHOTS]
    errors = np.asarray([
        [estimate - interval[0], interval[1] - estimate]
        for estimate, interval in zip(estimates, intervals)
    ]).T
    axes[1].errorbar(
        x, estimates, yerr=errors, marker="o", linewidth=2,
        capsize=3, color="#4b2e83",
    )
    axes[1].axhline(0, color="black", linewidth=0.8)
    axes[1].set_xticks(x, [str(shot) for shot in SHOTS])
    axes[1].set_xlabel("Target support k")
    axes[1].set_ylabel("Feature-name utility (S − R_anon)")
    fig.savefig(path, dpi=220)
    plt.close(fig)


def format_ci(values: list[float]) -> str:
    return f"[{values[0]:+.4f}, {values[1]:+.4f}]"


def write_report(summary: dict[str, Any], path: Path) -> None:
    primary = summary["primary_decay_0_to_512"]
    supervised = summary["secondary_decay_4_to_512"]
    trajectory = " → ".join(
        f"{summary['macro']['utility'][str(shot)]['estimate']:+.4f}" for shot in SHOTS
    )
    text = f"""# TabLLM stable-anonymous support ladder — results v1

Frozen verdict: **{summary['verdict']}**.

The unweighted macro point trajectory for `S - R_anon` is {trajectory} at
`k = 0, 4, 32, 512`.  The primary decay is {primary['estimate']:+.4f}; its
dataset-cluster bootstrap 95% interval is {format_ci(primary['bootstrap_ci95'])}
and its Student-t interval is {format_ci(primary['student_t_ci95_df8'])}.
The predeclared supervised-only decay (`k=4` to `k=512`) is
{supervised['estimate']:+.4f}.  Dropping Car, the primary decay is
{summary['drop_car_primary_decay']:+.4f}.

This directly addresses the format confound in the published `List Only Values`
ladder: `R_anon` preserves List Template serialization and changes only stable
feature-name strings.  The claim is limited to TabLLM's externally fixed but
purposively assembled nine-dataset panel.  Macro monotonicity, if present, is a
descriptive point trajectory and not a dataset-wise or population-level law.

All 270 nonzero-shot cells passed artifact, pairing, step-count, probability,
checkpoint, and metric-recomputation validation before this report was written.
"""
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--zero-root", type=Path,
        default=ROOT / "experiments/tabllm_retrospective_audit_v1",
    )
    parser.add_argument("--out", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--plot", type=Path)
    args = parser.parse_args()
    out = args.out or args.root / "SUMMARY_V1.json"
    report = args.report or args.root / "RESULTS_V1.md"
    plot = args.plot or args.root / "tabllm_ranon_support_ladder_v1.png"

    values = np.zeros((len(DATASETS), len(SEEDS), len(SHOTS), len(ARMS)))
    input_hashes: dict[str, str] = {}
    common_fields: dict[str, Any] | None = None
    pairing: dict[tuple[str, int, int], dict[str, tuple[str, str, str]]] = {}
    max_recompute_error = 0.0

    for dataset_index, dataset in enumerate(DATASETS):
        for arm_index, arm in enumerate(ARMS):
            zero_metrics_path = args.zero_root / arm / dataset / "metrics.json"
            if not zero_metrics_path.is_file():
                raise FileNotFoundError(zero_metrics_path)
            zero = json.loads(zero_metrics_path.read_text(encoding="utf-8"))
            if zero.get("analysis_status") != "retrospective_published_style_reproduction":
                raise RuntimeError(f"inadmissible zero-shot source: {zero_metrics_path}")
            input_hashes[f"zero/{arm}/{dataset}/metrics.json"] = sha256_file(
                zero_metrics_path
            )
            for seed_index, seed in enumerate(SEEDS):
                values[dataset_index, seed_index, 0, arm_index] = float(
                    zero["metrics"][str(seed)]["auc"]
                )

            for shot_index, shot in enumerate(SHOTS[1:], start=1):
                for seed_index, seed in enumerate(SEEDS):
                    metrics, estimate, hashes, error = validate_evidence_cell(
                        args.root, dataset, arm, shot, seed
                    )
                    values[dataset_index, seed_index, shot_index, arm_index] = estimate
                    input_hashes.update(hashes)
                    max_recompute_error = max(max_recompute_error, error)
                    fields = {
                        key: metrics[key] for key in (
                            "protocol_sha256", "runner_sha256", "split_manifest_sha256",
                            "tabllm_commit", "tfew_execution_commit",
                            "raw_and_serialization_tree_sha256", "ia3_checkpoint_sha256",
                        )
                    }
                    if common_fields is None:
                        common_fields = fields
                    elif common_fields != fields:
                        raise RuntimeError("nonzero cells do not share one frozen contract")
                    key = (dataset, shot, seed)
                    pairing.setdefault(key, {})[arm] = (
                        metrics["train_membership_row_ids_sha256"],
                        metrics["test_row_ids_sha256"],
                        metrics["initial_trainable_state_sha256"],
                    )

    for key, arms in pairing.items():
        if set(arms) != set(ARMS) or arms[ARMS[0]] != arms[ARMS[1]]:
            raise RuntimeError(f"unpaired arm evidence for {key}: {arms}")
    if common_fields is None or common_fields["protocol_sha256"] != sha256_file(PROTOCOL):
        raise RuntimeError("evidence does not match the local frozen protocol")

    utility_seed = values[:, :, :, 0] - values[:, :, :, 1]
    dataset_utility = utility_seed.mean(axis=1)
    primary_values = dataset_utility[:, 0] - dataset_utility[:, 3]
    supervised_values = dataset_utility[:, 1] - dataset_utility[:, 3]
    primary = interval_record(primary_values, BOOTSTRAP_SEED)
    supervised = interval_record(supervised_values, BOOTSTRAP_SEED + 1)
    drop_car = float(np.delete(primary_values, DATASETS.index("car")).mean())
    frozen_verdict, verdict_diagnostics = verdict(primary, supervised, drop_car)

    utility_summary = {
        str(shot): interval_record(dataset_utility[:, index], BOOTSTRAP_SEED + 100 + index)
        for index, shot in enumerate(SHOTS)
    }
    macro_arm_auc = {
        str(shot): {
            arm: float(values[:, :, shot_index, arm_index].mean())
            for arm_index, arm in enumerate(ARMS)
        }
        for shot_index, shot in enumerate(SHOTS)
    }
    dataset_summaries = {
        dataset: {
            "arm_mean_auc": {
                str(shot): {
                    arm: float(values[d, :, k, a].mean())
                    for a, arm in enumerate(ARMS)
                }
                for k, shot in enumerate(SHOTS)
            },
            "utility": {
                str(shot): float(dataset_utility[d, k])
                for k, shot in enumerate(SHOTS)
            },
            "primary_decay_0_to_512": float(primary_values[d]),
            "secondary_decay_4_to_512": float(supervised_values[d]),
            "seed_utility": {
                str(shot): {
                    str(seed): float(utility_seed[d, s, k])
                    for s, seed in enumerate(SEEDS)
                }
                for k, shot in enumerate(SHOTS)
            },
        }
        for d, dataset in enumerate(DATASETS)
    }
    macro_points = np.asarray([
        utility_summary[str(shot)]["estimate"] for shot in SHOTS
    ])
    payload = {
        "analysis_status": "frozen_ranon_support_ladder_complete",
        "verdict": frozen_verdict,
        "verdict_diagnostics": verdict_diagnostics,
        "estimand": "mean_d mean_seed [AUROC(S)-AUROC(R_anon)]",
        "panel": list(DATASETS),
        "shots": list(SHOTS),
        "seeds": list(SEEDS),
        "macro": {
            "arm_auc": macro_arm_auc,
            "utility": utility_summary,
            "unweighted_macro_point_trajectory_nonincreasing": bool(
                np.all(np.diff(macro_points) <= 0)
            ),
            "retention_point": (
                float(macro_points[-1] / macro_points[0])
                if macro_points[0] != 0 else None
            ),
        },
        "primary_decay_0_to_512": primary,
        "secondary_decay_4_to_512": supervised,
        "descriptive_decay_0_to_32": interval_record(
            dataset_utility[:, 0] - dataset_utility[:, 2], BOOTSTRAP_SEED + 2
        ),
        "descriptive_decay_32_to_512": interval_record(
            dataset_utility[:, 2] - dataset_utility[:, 3], BOOTSTRAP_SEED + 3
        ),
        "drop_car_primary_decay": drop_car,
        "datasets": dataset_summaries,
        "validation": {
            "nonzero_cell_count": 270,
            "paired_cell_group_count": len(pairing),
            "maximum_metric_recompute_error": max_recompute_error,
            "all_nonzero_cells_complete": True,
            "all_pairing_hashes_match": True,
        },
        "inference": {
            "independent_unit": "dataset",
            "bootstrap_reps": REPS,
            "primary_bootstrap_seed": BOOTSTRAP_SEED,
            "student_t_df": 8,
            "sesoi": SESOI,
        },
        "provenance": {
            "protocol_sha256": sha256_file(PROTOCOL),
            "summarizer_sha256": sha256_file(Path(__file__)),
            "nonzero_common_contract": common_fields,
            "input_sha256": input_hashes,
        },
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    write_report(payload, report)
    write_plot(payload, plot)
    print(json.dumps({
        "verdict": frozen_verdict,
        "macro_utility": {shot: utility_summary[str(shot)]["estimate"] for shot in SHOTS},
        "primary": primary,
        "supervised": supervised,
        "drop_car": drop_car,
        "written": [str(out), str(report), str(plot)],
    }, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
