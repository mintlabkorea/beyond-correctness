#!/usr/bin/env python3
"""Adjudicator for the MCR factorial semi-synthetic benchmark, v1 (rev 2).

Frozen rules (`iclr_latex_v3/MCR_FACTORIAL_SEMISYNTHETIC_PREREGISTRATION_V1
.md` section 10): Q = -MSE/Var(y_query); families are fixed strata;
per family x backbone at K = 32, realization-level paired bootstrap
(10,000 reps, seed 20260820); separation within a family = mean > 0 and
CI95 excludes 0 and win rate >= 0.60; a grid verdict = separation in all
three families x both backbones.  Exchangeable-null pairs must keep 0
inside their CI in every family.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "experiments/crta_v3_mcr_factorial_semisynth_v1"

FAMILIES = ("additive", "pairwise", "sparse")
PRIMARY_K = "32"
SECONDARY_K = "512"
BACKBONES = ("xgb", "histgb")
BOOTSTRAP_REPS = 10000
BOOTSTRAP_SEED = 20260820
WIN_THRESHOLD = 0.60
EXPECTED_REALIZATIONS = 20

CellFn = Callable[[dict[str, float]], float]


def q(arms: dict[str, Any], name: str) -> float:
    return -float(arms[name]["nmse"])


def make_pair(a: str, b: str) -> CellFn:
    return lambda arms: q(arms, a) - q(arms, b)


def i_mcr_free(arms: dict[str, Any]) -> float:
    return (q(arms, "m1c1r1") - q(arms, "m1c1rf") - q(arms, "m1c0r1")
            - q(arms, "m0c1r1") + q(arms, "m1c0rf") + q(arms, "m0c1rf")
            + q(arms, "m0c0r1") - q(arms, "m0c0rf"))


def i_mcr_random(arms: dict[str, Any]) -> float:
    return (q(arms, "m1c1r1") - q(arms, "m1c1r0") - q(arms, "m1c0r1")
            - q(arms, "m0c1r1") + q(arms, "m1c0r0") + q(arms, "m0c1r0")
            + q(arms, "m0c0r1") - q(arms, "m0c0r0"))


def i_mc_free(arms: dict[str, Any]) -> float:
    return (q(arms, "m1c1rf") - q(arms, "m1c0rf") - q(arms, "m0c1rf")
            + q(arms, "m0c0rf"))


PRIMARY_CONTRASTS: dict[str, CellFn] = {
    "P1_measurement": make_pair("m1c1r1", "m0c1r1"),
    "P2_correspondence": make_pair("m1c1r1", "m1c0r1"),
    "P3a_relation_identification": make_pair("m1c1r1", "m1c1r0"),
    "P3b_relation_utility": make_pair("m1c1r1", "m1c1rf"),
    "P4_MC_interaction": i_mc_free,
    "S4_interaction_free": i_mcr_free,
}
# The composition claim rests on the conditional main effects plus the
# two-way M x C interaction; the three-way I is secondary and only
# interpretable off-floor (prereg section 10).
GRID_VERDICT_CONTRASTS = ("P1_measurement", "P2_correspondence",
                          "P3a_relation_identification",
                          "P4_MC_interaction")
OFF_FLOOR_GATES: dict[str, CellFn] = {
    "gate_m_alone_off_floor": make_pair("m1c0rf", "m0c0rf"),
    "gate_c_alone_off_floor": make_pair("m0c1rf", "m0c0rf"),
}
NULL_CONTRASTS: dict[str, CellFn] = {
    "N4_random_vs_random2": make_pair("m1c1r0", "r_random2"),
    "N5_deranged_vs_deranged2": make_pair("m1c0r1", "c_deranged2"),
    "N6_wrong_vs_wrong2": make_pair("m0c1r1", "m_wrong2"),
}
NULL_MARGIN = 0.05  # nMSE units; exchangeable pairs must also stay inside
DESCRIPTIVE_CONTRASTS: dict[str, CellFn] = {
    "relation_vs_flipped": make_pair("m1c1r1", "r_flipped"),
    "random_constraint_harm": make_pair("m1c1rf", "m1c1r0"),
    "transfer_anchor": make_pair("m1c1r1", "target_only"),
    "target_only_vs_all_wrong": make_pair("target_only", "m0c0r0"),
    "secondary_I_random": i_mcr_random,
    "P3b_ops_alone": make_pair("r_op_only", "m1c1rf"),          # B/C only
    "P3b_signs_given_ops": make_pair("m1c1r1", "r_op_only"),    # B/C only
}


def i_scale_variant(arms: dict[str, Any], transform: str) -> float:
    """Three-way I under alternative monotone scales (robustness only)."""
    def qv(name: str) -> float:
        nmse = float(arms[name]["nmse"])
        if transform == "log":
            return -float(np.log(nmse))
        if transform == "rmse":
            return -float(np.sqrt(nmse))
        raise ValueError(transform)
    return (qv("m1c1r1") - qv("m1c1rf") - qv("m1c0r1") - qv("m0c1r1")
            + qv("m1c0rf") + qv("m0c1rf") + qv("m0c0r1") - qv("m0c0rf"))
ARM_LIST = ("m1c1r1", "m1c1r0", "m1c0r1", "m0c1r1", "m1c0r0", "m0c1r0",
            "m0c0r1", "m0c0r0", "m1c1rf", "m1c0rf", "m0c1rf", "m0c0rf",
            "r_flipped", "r_random2", "c_deranged2", "m_wrong2",
            "target_only")


def load_cells(root: Path, mode: str) -> list[dict[str, Any]]:
    pattern = f"{mode}/*/r*/metrics.json" if mode == "primary" \
        else f"{mode}/r*/metrics.json"
    cells = [json.loads(path.read_text())
             for path in sorted(root.glob(pattern))]
    if mode == "primary":
        cells = [c for c in cells if c["family"] in FAMILIES]
    hashes = {(c.get("runner_sha256"), c.get("input_sha256"),
               c.get("prereg_sha256")) for c in cells}
    if len(hashes) > 1:
        raise RuntimeError(
            f"{mode}: cells carry {len(hashes)} different provenance "
            "triples; archive the mixed tree before summarizing.")
    return cells


def bootstrap_stats(values: np.ndarray, seed_key: str) -> dict[str, Any]:
    seed = int(hashlib.sha256(
        f"mcr_summary_r2|{BOOTSTRAP_SEED}|{seed_key}".encode()
    ).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    n = len(values)
    samples = values[rng.integers(0, n, size=(BOOTSTRAP_REPS, n))]
    means = samples.mean(axis=1)
    mean = float(values.mean())
    lower, upper = (float(np.quantile(means, 0.025)),
                    float(np.quantile(means, 0.975)))
    win = float(np.mean(values > 0))
    return {
        "mean": mean, "ci95": [lower, upper], "win": win, "n": int(n),
        "separated": bool(mean > 0 and lower > 0 and win >= WIN_THRESHOLD),
        "ci_contains_zero": bool(lower <= 0 <= upper),
    }


def per_family_values(cells: list[dict[str, Any]], fn: CellFn,
                      k: str, backbone: str) -> dict[str, np.ndarray]:
    out: dict[str, list[float]] = {}
    for cell in cells:
        arms = cell["results"][k][backbone]
        try:
            value = fn(arms)
        except KeyError as error:
            if cell["family"] == "additive":  # r_op_only is B/C-only
                continue
            raise RuntimeError(
                f"missing arm in {cell['mode']}/{cell['family']}"
                f"/r{cell['realization']}: {error}") from error
        out.setdefault(cell["family"], []).append(value)
    return {f: np.asarray(v, dtype=float) for f, v in out.items()}


def stratified(cells: list[dict[str, Any]], fn: CellFn, k: str,
               backbone: str, seed_key: str) -> dict[str, Any]:
    families = per_family_values(cells, fn, k, backbone)
    section = {
        family: bootstrap_stats(values, f"{seed_key}|{family}")
        for family, values in sorted(families.items())
    }
    section["all_families_separated"] = bool(
        all(section[f]["separated"] for f in families))
    section["equal_weight_family_mean"] = float(
        np.mean([section[f]["mean"] for f in families]))
    return section


def summarize_primary(cells: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for backbone in BACKBONES:
        for k in (PRIMARY_K, SECONDARY_K):
            section: dict[str, Any] = {}
            for name, fn in {**PRIMARY_CONTRASTS, **OFF_FLOOR_GATES,
                             **NULL_CONTRASTS,
                             **DESCRIPTIVE_CONTRASTS}.items():
                section[name] = stratified(cells, fn, k, backbone,
                                           f"{backbone}|{k}|{name}")
            section["S4_scale_robustness"] = {
                transform: {
                    family: float(np.mean(values))
                    for family, values in sorted(per_family_values(
                        cells,
                        lambda arms, t=transform: i_scale_variant(arms, t),
                        k, backbone).items())
                }
                for transform in ("log", "rmse")
            }
            section["arm_mean_nmse"] = {
                arm: float(np.mean([c["results"][k][backbone][arm]["nmse"]
                                    for c in cells]))
                for arm in ARM_LIST
            }
            out[f"{backbone}_K{k}"] = section
    return out


def summarize_sensitivity(cells: list[dict[str, Any]]) -> dict[str, Any]:
    """Direction agreement of the weighted scheme (xgb, K=32, core arms)."""
    def wq(cell: dict[str, Any], name: str) -> float:
        return -float(cell["sensitivity_weighted_xgb_k32"][name]["nmse"])

    weighted_pairs = {
        "P1_measurement": ("m1c1r1", "m0c1r1"),
        "P2_correspondence": ("m1c1r1", "m1c0r1"),
        "P3a_relation_identification": ("m1c1r1", "m1c1r0"),
    }
    out: dict[str, Any] = {}
    for name, (a, b) in weighted_pairs.items():
        by_family: dict[str, list[float]] = {}
        for cell in cells:
            if not cell.get("sensitivity_weighted_xgb_k32"):
                continue
            by_family.setdefault(cell["family"], []).append(
                wq(cell, a) - wq(cell, b))
        out[name] = {
            family: {"mean": float(np.mean(values)), "n": len(values)}
            for family, values in sorted(by_family.items())
        }
    return out


def summarize_nc(root: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    nc_m = load_cells(root, "nc_m")
    if nc_m:
        out["nc_m"] = {
            "n_cells": len(nc_m),
            "m_pair_bit_identity_all": bool(all(
                all(c["checks"].values()) for c in nc_m)),
            "delta_c": bootstrap_stats(np.asarray([
                q(c["results"][PRIMARY_K]["xgb"], "m1c1r1")
                - q(c["results"][PRIMARY_K]["xgb"], "m1c0r1")
                for c in nc_m]), "nc_m|dc"),
            "delta_r": bootstrap_stats(np.asarray([
                q(c["results"][PRIMARY_K]["xgb"], "m1c1r1")
                - q(c["results"][PRIMARY_K]["xgb"], "m1c1r0")
                for c in nc_m]), "nc_m|dr"),
        }
    nc_c = load_cells(root, "nc_c")
    if nc_c:
        out["nc_c"] = {
            "n_cells": len(nc_c),
            "name_match_all_one": bool(all(
                c["name_match_accuracy"] == 1.0 for c in nc_c)),
            "delta_c_sanity": bootstrap_stats(np.asarray([
                q(c["results"][PRIMARY_K]["xgb"], "m1c1r1")
                - q(c["results"][PRIMARY_K]["xgb"], "m1c0r1")
                for c in nc_c]), "nc_c|dc"),
        }
    nc_r = load_cells(root, "nc_r")
    if nc_r:
        out["nc_r"] = {
            "n_cells": len(nc_r),
            "true_equals_free_all": bool(all(
                all(c["checks"].values()) for c in nc_r)),
            "delta_m": bootstrap_stats(np.asarray([
                q(c["results"][PRIMARY_K]["xgb"], "m1c1r1")
                - q(c["results"][PRIMARY_K]["xgb"], "m0c1r1")
                for c in nc_r]), "nc_r|dm"),
            "delta_c": bootstrap_stats(np.asarray([
                q(c["results"][PRIMARY_K]["xgb"], "m1c1r1")
                - q(c["results"][PRIMARY_K]["xgb"], "m1c0r1")
                for c in nc_r]), "nc_r|dc"),
            "desc_free_vs_random": bootstrap_stats(np.asarray([
                q(c["results"][PRIMARY_K]["xgb"], "m1c1rf")
                - q(c["results"][PRIMARY_K]["xgb"], "m1c1r0")
                for c in nc_r]), "nc_r|fr"),
        }
    return out


def verdicts(primary: dict[str, Any], nc: dict[str, Any],
             primary_cells: list[dict[str, Any]]) -> dict[str, Any]:
    verdict: dict[str, Any] = {}
    for name in GRID_VERDICT_CONTRASTS + ("P3b_relation_utility",
                                          "S4_interaction_free"):
        verdict[name] = {
            backbone: primary[f"{backbone}_K{PRIMARY_K}"][name][
                "all_families_separated"]
            for backbone in BACKBONES
        }
        verdict[name]["grid"] = bool(all(
            verdict[name][b] for b in BACKBONES))
    verdict["composition_claim"] = bool(all(
        verdict[name]["grid"] for name in GRID_VERDICT_CONTRASTS))
    verdict["S4_off_floor_gate"] = bool(all(
        primary[f"{backbone}_K{PRIMARY_K}"][gate]["all_families_separated"]
        for backbone in BACKBONES for gate in OFF_FLOOR_GATES))
    nulls_ok = True
    for name in NULL_CONTRASTS:
        clean = True
        for backbone in BACKBONES:
            per_family = primary[f"{backbone}_K{PRIMARY_K}"][name]
            for family in FAMILIES:
                stats = per_family.get(family)
                clean &= bool(
                    stats is not None
                    and stats["ci_contains_zero"]
                    and abs(stats["mean"]) < NULL_MARGIN)
        verdict[name + "_clean"] = bool(clean)
        nulls_ok &= clean
    verdict["exchangeable_nulls_clean"] = bool(nulls_ok)
    primary_names_zero = all(
        c["name_match_accuracy"] == 0.0 for c in primary_cells)
    verdict["N1_nc_m"] = bool(
        nc.get("nc_m", {}).get("m_pair_bit_identity_all")
        and nc["nc_m"]["delta_c"]["separated"]
    ) if "nc_m" in nc else None
    verdict["N2_name_matcher"] = bool(
        nc.get("nc_c", {}).get("name_match_all_one") and primary_names_zero
    ) if "nc_c" in nc else None
    verdict["N3_nc_r"] = bool(
        nc.get("nc_r", {}).get("true_equals_free_all")
        and nc["nc_r"]["delta_m"]["separated"]
        and nc["nc_r"]["delta_c"]["separated"]
    ) if "nc_r" in nc else None
    return verdict


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()

    primary_cells = load_cells(args.root, "primary")
    counts = {f: sum(1 for c in primary_cells if c["family"] == f)
              for f in FAMILIES}
    nc_cells = {s: load_cells(args.root, s) for s in ("nc_m", "nc_c", "nc_r")}
    provenance = {
        (c.get("runner_sha256"), c.get("input_sha256"),
         c.get("prereg_sha256"))
        for group in ([primary_cells] + list(nc_cells.values()))
        for c in group
    }
    if len(provenance) > 1:
        raise RuntimeError(
            "provenance differs across modes; archive the mixed tree.")
    expected = set(range(EXPECTED_REALIZATIONS))
    primary = summarize_primary(primary_cells)
    nc = summarize_nc(args.root)
    complete = (
        all({c["realization"] for c in primary_cells
             if c["family"] == f} == expected for f in FAMILIES)
        and all({c["realization"] for c in nc_cells[s]} == expected
                for s in ("nc_m", "nc_c", "nc_r"))
    )
    if complete:
        verdict = verdicts(primary, nc, primary_cells)
    else:
        verdict = {
            "status": "incomplete — verdicts withheld",
            "cells_per_family": counts,
            "nc_cells": {s: nc.get(s, {}).get("n_cells", 0)
                         for s in ("nc_m", "nc_c", "nc_r")},
        }
    payload = {
        "n_primary_cells": len(primary_cells),
        "cells_per_family": counts,
        "primary_k": int(PRIMARY_K),
        "bootstrap": {"reps": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED,
                      "unit": "realization within fixed family strata"},
        "verdicts": verdict,
        "primary": primary,
        "sensitivity_weighted": summarize_sensitivity(primary_cells),
        "negative_controls": nc,
    }
    out_path = args.root / "SUMMARY_V1.json"
    out_path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({"verdicts": verdict,
                      "n_primary_cells": len(primary_cells),
                      "written": str(out_path)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
