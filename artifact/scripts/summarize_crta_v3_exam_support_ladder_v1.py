#!/usr/bin/env python3
"""Adjudicate the examination support ladder per its protocol.

Reuses the frozen summarizer's `analyze` and `interval_sensitivities` by
import so the inference conventions cannot drift.  The verdict is declared
on class A alone, uses interval logic rather than point-estimate ordering,
and requires the endpoint Student-t to agree with the bootstrap gate.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FROZEN_SUMMARIZER = ROOT / "scripts/summarize_crta_v3_exam_no_bridge_reference_v1.py"
DEFAULT_ROOT = ROOT / "experiments/crta_v3_exam_support_ladder_v1"
V2_ROOT = ROOT / "experiments/crta_v3_exam_reference_sensitivity_v2"
PROTOCOL = DEFAULT_ROOT / "PROTOCOL_V1.md"

LADDER = (64, 256, 1024)
PRIMARY_K = 256
K_LOW, K_HIGH = 64, 1024          # decay is low-support minus high-support
SESOI = 0.020                     # protocol: frozen before execution
PREDICTED_DECAY = (0.049, 0.096)  # protocol: calibrated from the m1m2 ladder
MDE80 = (0.066, 0.093)            # protocol: simulated before execution
CONTROLLED_RETENTION = (0.07, 0.14)
ARMS = ("S_shared_bridge", "W_deranged_bridge", "R_domain_local")
PANEL = {
    "A": ("glucose", "waist_cm", "triglycerides", "sbp", "dbp",
          "total_cholesterol"),
    "B": ("alt", "bun"),
    "C": ("creatinine", "hemoglobin", "hematocrit", "rbc", "wbc"),
}
ALL_TARGETS = tuple(t for g in ("A", "B", "C") for t in PANEL[g])
CLASS_OF = {t: g for g, ts in PANEL.items() for t in ts}
SCOPES = {
    "classA_primary": PANEL["A"],
    "all13": ALL_TARGETS,
    "classB": PANEL["B"],
    "classC": PANEL["C"],
}
CONTRASTS = {
    "content_S_minus_W": ("S_shared_bridge", "W_deranged_bridge"),
    "utility_S_minus_R": ("S_shared_bridge", "R_domain_local"),
    "reference_minus_wrong_R_minus_W": ("R_domain_local", "W_deranged_bridge"),
}
PRIMARY_DECAY = f"decay_utility_S_minus_R_{K_LOW}_minus_{K_HIGH}"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def with_intervals(record: dict, frozen, seed: int) -> dict:
    """Attach endpoint-level intervals, or record why they are undefined."""
    means = list(record["per_endpoint_mean"].values())
    if len(means) < 2:
        record["interval_sensitivities"] = {
            "status": "degenerate: fewer than two endpoint clusters"}
    elif float(np.std(means)) <= 0.0:
        record["interval_sensitivities"] = {
            "status": "degenerate: zero between-endpoint variance"}
    else:
        record["interval_sensitivities"] = frozen.interval_sensitivities(
            record["per_endpoint_mean"], seed)
    return record


def grouped(per_cell: dict, targets) -> dict:
    return {t: np.asarray(per_cell[t], dtype=float)
            for t in sorted(targets) if t in per_cell}


def retention_interval(low: dict, high: dict, frozen, seed: int) -> dict:
    """m(K_high)/m(K_low) under the frozen hierarchical resampling.

    Endpoints and then seeds are resampled once per draw and the SAME
    indices are used at both rungs, because the cells are paired.
    """
    endpoints = sorted(low)
    rng = np.random.default_rng(seed)
    draws, bad_denominator = np.empty(frozen.BOOTSTRAP_REPS), 0
    for index in range(frozen.BOOTSTRAP_REPS):
        chosen = rng.integers(0, len(endpoints), size=len(endpoints))
        lo_vals, hi_vals = [], []
        for endpoint_index in chosen:
            key = endpoints[int(endpoint_index)]
            picks = rng.integers(0, len(low[key]), size=len(low[key]))
            lo_vals.append(low[key][picks])
            hi_vals.append(high[key][picks])
        denominator = float(np.mean(np.concatenate(lo_vals)))
        if denominator <= 0.0:
            bad_denominator += 1
            draws[index] = np.nan
            continue
        draws[index] = float(np.mean(np.concatenate(hi_vals))) / denominator
    finite = draws[np.isfinite(draws)]
    point_low = float(np.mean(np.concatenate([low[e] for e in endpoints])))
    point_high = float(np.mean(np.concatenate([high[e] for e in endpoints])))
    unstable = bad_denominator > 0.01 * frozen.BOOTSTRAP_REPS
    return {
        "retention_point": (point_high / point_low
                            if point_low > 0 else None),
        "ci95": ([float(np.quantile(finite, 0.025)),
                  float(np.quantile(finite, 0.975))]
                 if finite.size else None),
        "draws_with_nonpositive_denominator": bad_denominator,
        "unstable": bool(unstable),
        "note": ("ratio of pooled means, paired resampling; the interval is "
                 "meaningless if the denominator can cross zero"),
        "controlled_law_retention_for_comparison": list(CONTROLLED_RETENTION),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=DEFAULT_ROOT)
    args = parser.parse_args()
    frozen = load("exam_frozen_summarizer", FROZEN_SUMMARIZER)

    cells = [json.loads(p.read_text(encoding="utf-8"))
             for p in sorted(args.root.glob("*/seed_*/metrics.json"))]
    expected_cells = len(ALL_TARGETS) * 10
    if len(cells) != expected_cells:
        raise RuntimeError(f"expected {expected_cells} cells, found {len(cells)}")

    # --- integrity 1: exactly 390 exact comparisons, no skips -------------
    expected_cmp = len(ALL_TARGETS) * 10 * len(ARMS)
    worst, exact, missing, deviations = 0.0, 0, [], []
    version_mismatch = []
    n_cmp = 0
    for cell in cells:
        path = V2_ROOT / cell["target"] / f"seed_{cell['seed']}/metrics.json"
        if not path.is_file():
            missing.append(str(path.relative_to(ROOT)))
            continue
        baseline = json.loads(path.read_text(encoding="utf-8"))
        if baseline.get("versions") != cell.get("versions"):
            version_mismatch.append(
                {"target": cell["target"], "seed": cell["seed"],
                 "baseline": baseline.get("versions"),
                 "observed": cell.get("versions")})
        for arm in ARMS:
            observed = cell["nrmse"][str(PRIMARY_K)][arm]
            published = baseline["nrmse"][arm]
            n_cmp += 1
            if observed == published:
                exact += 1
            else:
                delta = abs(observed - published)
                worst = max(worst, delta)
                deviations.append({"target": cell["target"],
                                   "seed": cell["seed"], "arm": arm,
                                   "abs_delta": delta})
    # Protocol: exact equality unless the recorded library versions differ,
    # in which case the check degrades to |delta| < 1e-12 and says so.
    degraded = bool(version_mismatch)
    if degraded:
        passed = bool(n_cmp == expected_cmp and not missing
                      and worst < 1e-12)
    else:
        passed = bool(n_cmp == expected_cmp and not missing
                      and exact == expected_cmp)
    integrity = {
        "k256_reproduces_published_v2": {
            "comparisons_required": expected_cmp,
            "comparisons_made": n_cmp,
            "exactly_equal": exact,
            "missing_baseline_files": missing,
            "worst_abs_delta_nrmse": worst,
            "deviations": deviations[:20],
            "criterion": ("float equality" if not degraded
                          else "DEGRADED to |delta| < 1e-12: library versions "
                               "differ from the v2 baseline"),
            "version_mismatch": version_mismatch[:5],
            "pass": passed},
        "pool_floor": {
            "floor": int(4 * max(LADDER)),
            "min_observed_pool": int(min(c["n_pool"] for c in cells)),
            "pass": bool(min(c["n_pool"] for c in cells) >= 4 * max(LADDER))},
        "support_rows_drawn": {
            str(k): sorted({c["support_rows_drawn"][str(k)] for c in cells})
            for k in LADDER},
    }

    def contrast_values(key: str) -> dict:
        """[contrast][K][endpoint] -> list of per-seed gains."""
        out = {name: {k: {} for k in LADDER} for name in CONTRASTS}
        for cell in cells:
            block = cell["nrmse"] if key == "nrmse" else \
                cell.get("nrmse_diagnostic", {}).get(key, {})
            if not block:
                continue
            for k in LADDER:
                if str(k) not in block:
                    continue
                scores = block[str(k)]
                for name, (left, right) in CONTRASTS.items():
                    gain = float(scores[right]) - float(scores[left])
                    out[name][k].setdefault(cell["target"], []).append(gain)
        return out

    values = contrast_values("nrmse")
    diag_values = contrast_values("diag_mcw")

    # --- absolute per-arm trajectories, mandatory by protocol -------------
    trajectories = {}
    for scope, targets in SCOPES.items():
        trajectories[scope] = {
            arm: {str(k): float(np.mean([c["nrmse"][str(k)][arm] for c in cells
                                         if c["target"] in targets]))
                  for k in LADDER}
            for arm in ARMS}

    index = 0
    levels: dict = {}
    for scope, targets in SCOPES.items():
        levels[scope] = {}
        for name in CONTRASTS:
            levels[scope][name] = {}
            for k in LADDER:
                record = with_intervals(
                    frozen.analyze(
                        grouped(values[name][k], targets),
                        np.random.default_rng(frozen.BOOTSTRAP_SEED + index)),
                    frozen, frozen.BOOTSTRAP_SEED + 10_000 + index)
                index += 1
                levels[scope][name][str(k)] = record

    def decay_block(source: dict, tag: str) -> dict:
        nonlocal index
        out = {scope: {} for scope in SCOPES}
        steps = [(name, K_LOW, K_HIGH) for name in CONTRASTS]
        steps += [("utility_S_minus_R", K_LOW, PRIMARY_K),
                  ("utility_S_minus_R", PRIMARY_K, K_HIGH)]
        for contrast, k_lo_support, k_hi_support in steps:
            label = (f"{tag}decay_{contrast}_"
                     f"{k_lo_support}_minus_{k_hi_support}")
            per_cell = {}
            for target in source[contrast][k_lo_support]:
                low = np.asarray(source[contrast][k_lo_support][target], float)
                high = np.asarray(source[contrast][k_hi_support][target], float)
                per_cell[target] = list(low - high)
            for scope, targets in SCOPES.items():
                groups = grouped(per_cell, targets)
                if not groups:
                    continue
                out[scope][label] = with_intervals(
                    frozen.analyze(
                        groups,
                        np.random.default_rng(frozen.BOOTSTRAP_SEED + index)),
                    frozen, frozen.BOOTSTRAP_SEED + 10_000 + index)
                index += 1
        # curvature: the only independent contrast the middle rung adds
        for scope, targets in SCOPES.items():
            per_cell = {}
            for target in source["utility_S_minus_R"][K_LOW]:
                a = np.asarray(source["utility_S_minus_R"][K_LOW][target], float)
                b = np.asarray(source["utility_S_minus_R"][PRIMARY_K][target], float)
                c = np.asarray(source["utility_S_minus_R"][K_HIGH][target], float)
                per_cell[target] = list(a - 2 * b + c)
            groups = grouped(per_cell, targets)
            if not groups:
                continue
            out[scope][f"{tag}curvature_utility_descriptive"] = with_intervals(
                frozen.analyze(
                    groups,
                    np.random.default_rng(frozen.BOOTSTRAP_SEED + index)),
                frozen, frozen.BOOTSTRAP_SEED + 10_000 + index)
            index += 1
        return out

    decays = decay_block(values, "")
    diagnostic_decays = (decay_block(diag_values, "diag_mcw_")
                         if diag_values["utility_S_minus_R"][K_LOW] else {})

    retention = retention_interval(
        grouped(values["utility_S_minus_R"][K_LOW], PANEL["A"]),
        grouped(values["utility_S_minus_R"][K_HIGH], PANEL["A"]),
        frozen, frozen.BOOTSTRAP_SEED + 50_000)

    # --- verdict: class A, interval logic --------------------------------
    primary = levels["classA_primary"]
    means = {k: primary["utility_S_minus_R"][str(k)]["mean"] for k in LADDER}
    record = decays["classA_primary"][PRIMARY_DECAY]
    boot_low, boot_high = record["ci95"]
    student = record.get("interval_sensitivities", {}).get(
        "student_t_cluster_mean", [None, None])
    student_low, student_high = student if student else (None, None)

    supported = bool(
        boot_low > 0.0
        and student_low is not None and student_low > 0.0
        and record["mean"] >= SESOI)
    contradicted = bool(
        boot_high < 0.0
        or (boot_low > -SESOI and boot_high < SESOI))

    if not integrity["k256_reproduces_published_v2"]["pass"]:
        verdict = "WITHHELD — the K=256 rung does not reproduce the published cells"
    elif supported:
        verdict = ("SUPPORTED (within the selected panel) — the correspondence "
                   "utility declines with the number of distinct labeled "
                   "target rows at fixed target-domain mass")
    elif contradicted:
        verdict = ("CONTRADICTED — no meaningful positive decay on this panel")
    else:
        verdict = "INCONCLUSIVE — pre-declared as a likely outcome of this design"

    verdicts = {
        "verdict": verdict,
        "claim_ceiling": ("No outcome licenses 'the controlled law extends to "
                          "real data': this varies distinct-row count at fixed "
                          "target-domain mass, the controlled benchmark varies "
                          "count and mass together, and class A is an "
                          "outcome-selected panel."),
        "scope": "class A (six cardiometabolic endpoints) only, per protocol",
        "primary_decay": {
            "name": PRIMARY_DECAY, "mean": record["mean"],
            "bootstrap_ci95": record["ci95"],
            "endpoint_student_t": [student_low, student_high],
            "win": record["win"],
            "drop_best_endpoint_mean": record["drop_best_endpoint_mean"],
            "bootstrap_gate": bool(record["separated"]),
            "sesoi": SESOI, "meets_sesoi": bool(record["mean"] >= SESOI)},
        "predicted_decay_interval": list(PREDICTED_DECAY),
        "decay_inside_predicted_interval": bool(
            PREDICTED_DECAY[0] <= record["mean"] <= PREDICTED_DECAY[1]),
        "mde80_frozen": list(MDE80),
        "retention_classA": retention,
        "classA_utility_mean_by_k": {str(k): means[k] for k in LADDER},
        "monotone_diagnostic_not_a_verdict_conjunct": bool(
            means[64] >= means[256] >= means[1024]),
        "coherence_descriptive_by_k": {
            str(k): bool(
                primary["reference_minus_wrong_R_minus_W"][str(k)]["separated"])
            for k in LADDER},
        "rule": ("SUPPORTED requires bootstrap CI lower > 0 AND endpoint "
                 "Student-t lower > 0 AND mean >= SESOI (.020). CONTRADICTED "
                 "requires CI upper < 0, or the whole CI inside (-SESOI, "
                 "+SESOI). Everything else is INCONCLUSIVE, including a noisy "
                 "non-monotone reversal. Monotonicity and reference coherence "
                 "are diagnostics, not gates. Class B, class C, and the pooled "
                 "13-endpoint ladder are non-verdict-bearing. Post-hoc "
                 "selection of a K pair, endpoint subset, or weighting regime "
                 "is inadmissible; hba1c must not be added in response."),
    }

    per_endpoint = {
        t: {"class": CLASS_OF[t],
            **{f"utility_k{k}": float(np.mean(values["utility_S_minus_R"][k][t]))
               for k in LADDER},
            "decay_64_minus_1024": float(np.mean(
                np.asarray(values["utility_S_minus_R"][K_LOW][t])
                - np.asarray(values["utility_S_minus_R"][K_HIGH][t])))}
        for t in sorted(values["utility_S_minus_R"][PRIMARY_K])}

    summary = {
        "analysis_status": "post-result labeled-target-support ladder",
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "what_is_varied": ("the number of distinct labeled target rows at "
                           "fixed target-domain mass (per-row weight "
                           "n_source/K), not the controlled benchmark's "
                           "count-and-mass manipulation"),
        "metric": "query_sd_normalized_rmse (lower is better); "
                  "gain = right arm minus left arm, positive favours the left",
        "decomposition_identity": "utility = content - reference_minus_wrong",
        "bootstrap": {"reps": frozen.BOOTSTRAP_REPS,
                      "seed_base": frozen.BOOTSTRAP_SEED,
                      "hierarchy": "endpoints then seeds"},
        "n_cells": len(cells), "ladder": list(LADDER),
        "hosts": sorted({c.get("host", "?") for c in cells}),
        "versions": sorted({json.dumps(c.get("versions", {}), sort_keys=True)
                            for c in cells}),
        "integrity": integrity,
        "absolute_nrmse_trajectories": trajectories,
        "levels": levels,
        "decays": decays,
        "diagnostic_min_child_weight_decays": diagnostic_decays,
        "per_endpoint_descriptive": per_endpoint,
        "verdicts": verdicts,
    }
    out = args.root / "SUMMARY_V1.json"
    out.write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps({"written": str(out),
                      "integrity": {k: v.get("pass", v)
                                    for k, v in integrity.items()},
                      "verdicts": verdicts}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
