#!/usr/bin/env python3
"""Paired TabLLM reference-construction sensitivity from retained predictions."""

from __future__ import annotations

import csv
import gzip
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
INPUT = REPO / "experiments/tabllm_retrospective_audit_v1"
MANIFEST = REPO / "experiments/tabllm_retrospective_split_manifest_v1.json"
PARENT_SUMMARY = INPUT / "SUMMARY_V1.json"
PARENT_SCRIPT = REPO / "scripts/summarize_tabllm_retrospective_audit_v1.py"
REPS = 10_000
SEED = 20260903


def load_parent():
    spec = importlib.util.spec_from_file_location("tabllm_parent", PARENT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while block := f.read(8 * 1024 * 1024):
            h.update(block)
    return h.hexdigest()


def ci(x: np.ndarray) -> list[float]:
    return [float(v) for v in np.quantile(x, [0.025, 0.975])]


def effects(arms: np.ndarray) -> np.ndarray:
    supplied, rpub, ranon = arms.T
    upub = supplied - rpub
    uanon = supplied - ranon
    return np.column_stack([upub, uanon, uanon - upub])


def main() -> int:
    parent = load_parent()
    manifest = json.loads(MANIFEST.read_text())
    frozen = json.loads(PARENT_SUMMARY.read_text())
    rng = np.random.default_rng(SEED)
    wanted = ("list_template", "list_only_values", "list_stable_anonymous")
    rows = []
    dataset_points = []
    dataset_covariances = []
    artifact_hashes = {}
    max_point_error = 0.0

    for dataset in parent.DATASETS:
        loaded = {}
        metrics = {}
        for arm in wanted:
            cell = INPUT / arm / dataset
            pred = cell / "predictions.jsonl.gz"
            metric = cell / "metrics.json"
            if not pred.is_file() or not metric.is_file():
                raise FileNotFoundError(f"missing retained artifact: {cell}")
            loaded[arm] = parent.load_predictions(pred)
            metrics[arm] = json.loads(metric.read_text())
            artifact_hashes[str(pred.relative_to(REPO))] = sha256(pred)
            artifact_hashes[str(metric.relative_to(REPO))] = sha256(metric)

        ids, labels, _ = loaded[wanted[0]]
        for arm in wanted[1:]:
            if not np.array_equal(ids, loaded[arm][0]) or not np.array_equal(labels, loaded[arm][1]):
                raise RuntimeError(f"unpaired example rows for {dataset}/{arm}")
        lookup = {int(row_id): i for i, row_id in enumerate(ids)}
        influence = np.zeros((len(ids), len(wanted)))
        seed_estimates = np.zeros((len(parent.SEEDS), len(wanted)))
        for si, seed in enumerate(parent.SEEDS):
            positions = np.asarray([
                lookup[int(row_id)]
                for row_id in manifest["datasets"][dataset]["test_row_ids"][str(seed)]
            ])
            for ai, arm in enumerate(wanted):
                estimate, inf = parent.macro_auc_and_influence(
                    labels[positions], loaded[arm][2][positions]
                )
                seed_estimates[si, ai] = estimate
                influence[positions, ai] += inf / len(parent.SEEDS)
                reported = float(metrics[arm]["metrics"][str(seed)]["auc"])
                if abs(estimate - reported) > 1e-10:
                    raise AssertionError(f"AUROC recomputation mismatch: {dataset}/{arm}/{seed}")

        point = seed_estimates.mean(axis=0)
        covariance = parent.psd_covariance(influence.T @ influence)
        draws = rng.multivariate_normal(point, covariance, size=REPS)
        ep = effects(point[None, :])[0]
        ed = effects(draws)
        frozen_arms = frozen["datasets"][dataset]["arm_mean_auc"]
        for ai, arm in enumerate(wanted):
            max_point_error = max(max_point_error, abs(point[ai] - frozen_arms[arm]))
        all_points = np.r_[point, ep]
        all_draws = np.column_stack([draws, ed])
        for j, name in enumerate((
            "AUC_S", "AUC_Rpub", "AUC_Ranon", "U_pub", "U_anon",
            "Delta_ref_U_anon_minus_U_pub",
        )):
            rows.append({
                "scope": "dataset", "dataset": dataset, "estimand": name,
                "estimate": float(all_points[j]), "ci95_low": ci(all_draws[:, j])[0],
                "ci95_high": ci(all_draws[:, j])[1], "n_examples": len(ids),
                "n_fixed_splits": len(parent.SEEDS),
            })
        dataset_points.append(point)
        dataset_covariances.append(covariance)

    points = np.asarray(dataset_points)
    macro_point = points.mean(axis=0)
    selected = rng.integers(0, len(points), size=(REPS, len(points)))
    macro_draws = np.zeros((REPS, len(wanted)))
    for position in range(len(points)):
        chosen = selected[:, position]
        for di in range(len(points)):
            mask = chosen == di
            if mask.any():
                macro_draws[mask] += rng.multivariate_normal(
                    points[di], dataset_covariances[di], size=int(mask.sum())
                )
    macro_draws /= len(points)
    mep = effects(macro_point[None, :])[0]
    med = effects(macro_draws)
    macro_all_points = np.r_[macro_point, mep]
    macro_all_draws = np.column_stack([macro_draws, med])
    for j, name in enumerate((
        "AUC_S", "AUC_Rpub", "AUC_Ranon", "U_pub", "U_anon",
        "Delta_ref_U_anon_minus_U_pub",
    )):
        rows.append({
            "scope": "macro_dataset_bootstrap", "dataset": "ALL_9", "estimand": name,
            "estimate": float(macro_all_points[j]), "ci95_low": ci(macro_all_draws[:, j])[0],
            "ci95_high": ci(macro_all_draws[:, j])[1], "n_examples": "",
            "n_fixed_splits": len(parent.SEEDS),
        })

    if max_point_error > 1e-12:
        raise AssertionError(f"parent point-estimate mismatch: {max_point_error}")
    fields = list(rows[0])
    with (HERE / "tabllm_reference_sensitivity.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fields)
        writer.writeheader(); writer.writerows(rows)
    payload = {
        "status": "complete_for_retained_four_arm_grid",
        "bootstrap": {
            "reps": REPS, "seed": SEED,
            "within_dataset": "paired shared-example AUROC influence Gaussian multiplier",
            "macro": "datasets resampled, then within-dataset multivariate influence draws",
        },
        "estimands": {
            "U_pub": "AUC(list_template)-AUC(list_only_values)",
            "U_anon": "AUC(list_template)-AUC(list_stable_anonymous)",
            "Delta_ref_U_anon_minus_U_pub": "U_anon-U_pub = AUC(Rpub)-AUC(Ranon)",
        },
        "max_parent_arm_point_error": max_point_error,
        "results": rows,
        "support_ladder_status": (
            "not estimable without refitting: retained support ladder contains Ranon but no "
            "within-run Rpub predictions at matching support rungs"
        ),
        "sources": {
            "parent_script": str(PARENT_SCRIPT.relative_to(REPO)),
            "parent_summary": str(PARENT_SUMMARY.relative_to(REPO)),
            "split_manifest": str(MANIFEST.relative_to(REPO)),
            "split_manifest_sha256": sha256(MANIFEST),
            "artifact_sha256": artifact_hashes,
        },
    }
    (HERE / "tabllm_reference_sensitivity_macro.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({"written": [str(HERE / "tabllm_reference_sensitivity.csv"),
                                  str(HERE / "tabllm_reference_sensitivity_macro.json")],
                      "macro": rows[-3:]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
