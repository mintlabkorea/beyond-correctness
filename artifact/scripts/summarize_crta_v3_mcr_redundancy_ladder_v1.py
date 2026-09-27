"""Adjudicate MCR-RL per its protocol (Q = -nMSE, per-family realization
bootstrap; grid = both families x both backbones at K=32).

U(k)  = Q(op_true, k) - Q(free, k)      the ladder
S(k)  = Q(sig_true, k) - Q(op_true, k)  constraint channel (descriptive)

RL1 monotone rise   : mean within-realization Spearman(k, U(k)) > 0, CI excl 0
RL2 endpoints       : U(0) null AND U(|C|) separated
RL3 interior        : U(k*) separated at k* = round(|C|/2)
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "experiments/crta_v3_mcr_redundancy_ladder_v1"
VR_ROOT = ROOT / "experiments/crta_v3_mcr_value_redundancy_v1"
# Like-for-like re-fit of the same frozen VR runner at threads=1 on this
# host.  The published VR tree was fit at threads=2 on cloud-hq1Cey, and
# the frozen factorial runner documents that parallel histogram
# accumulation perturbs HistGB fits at the bit level; both comparisons are
# reported and the verdict gate uses the like-for-like one.
VR_LIKE_ROOT = ROOT / "experiments/_recheck_vr_threads1"
FAMILIES = ("pairwise", "sparse")
BACKBONES = ("xgb", "histgb")
SUPPORT_KS = ("32", "512")
PRIMARY_K = "32"
EXPECTED_REALIZATIONS = 20
BOOTSTRAP_REPS = 10000
BOOTSTRAP_SEED = 20260828
WIN_THRESHOLD = 0.60
NULL_MARGIN = 0.05
ENDPOINT_TOLERANCE = 0.005
FROZEN_INPUT_SHA256 = "6af2215c72a65ecc306e5c4d3d9af5b61b16a073dd5aa4c0f33b178741245a25"

VR_ENDPOINT_MAP = (("first", "free", "full_free"),
                   ("first", "op_true", "full_op_true"),
                   ("last", "free", "drop_free"),
                   ("last", "op_true", "drop_op_true"),
                   ("last", "sig_true", "drop_op_true_signed"))


def boot(values: np.ndarray, key: str) -> dict:
    seed = int(hashlib.sha256(
        f"mcr_rl|{BOOTSTRAP_SEED}|{key}".encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    chosen = rng.integers(0, len(values), size=(BOOTSTRAP_REPS, len(values)))
    means = values[chosen].mean(axis=1)
    lower, upper = float(np.quantile(means, 0.025)), float(
        np.quantile(means, 0.975))
    mean = float(np.mean(values))
    win = float(np.mean(values > 0))
    return {"mean": mean, "ci95": [lower, upper], "win": win,
            "n": int(len(values)),
            "separated": bool(mean > 0 and lower > 0 and win >= WIN_THRESHOLD),
            "null": bool(lower <= 0 <= upper and abs(mean) < NULL_MARGIN)}


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    """Rank correlation; x is a strict ladder index so ties only occur in y."""
    def rank(v: np.ndarray) -> np.ndarray:
        order = np.argsort(v, kind="mergesort")
        ranks = np.empty(len(v), dtype=float)
        ranks[order] = np.arange(len(v), dtype=float)
        _, inverse, counts = np.unique(v, return_inverse=True,
                                       return_counts=True)
        sums = np.zeros(len(counts))
        np.add.at(sums, inverse, ranks)
        return (sums / counts)[inverse]
    rx, ry = rank(x), rank(y)
    sx, sy = rx.std(), ry.std()
    if sx == 0 or sy == 0:
        return 0.0
    return float(np.mean((rx - rx.mean()) * (ry - ry.mean())) / (sx * sy))


def u_curve(record: dict, k: str, backbone: str) -> tuple[np.ndarray, np.ndarray,
                                                          np.ndarray]:
    rungs = record["results"][k][backbone]
    ks = np.asarray(sorted(int(r) for r in rungs), dtype=float)
    u = np.asarray([rungs[str(int(i))]["arms"]["free"]["nmse"]
                    - rungs[str(int(i))]["arms"]["op_true"]["nmse"] for i in ks])
    s = np.asarray([rungs[str(int(i))]["arms"]["op_true"]["nmse"]
                    - rungs[str(int(i))]["arms"]["sig_true"]["nmse"] for i in ks])
    return ks, u, s


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()

    cells = {f: [] for f in FAMILIES}
    provenance = set()
    for family in FAMILIES:
        for path in sorted((args.root / family).glob("r*/metrics.json")):
            record = json.loads(path.read_text())
            cells[family].append(record)
            provenance.add((record["runner_sha256"], record["mcr_runner_sha256"],
                            record["vr_runner_sha256"], record["input_sha256"],
                            record["protocol_sha256"]))
    if len(provenance) > 1:
        raise RuntimeError("mixed provenance across cells")
    if provenance and next(iter(provenance))[3] != FROZEN_INPUT_SHA256:
        raise RuntimeError("cells were not fit on the frozen MCR panel")
    complete = all(sorted(r["realization"] for r in cells[f]) ==
                   list(range(EXPECTED_REALIZATIONS)) for f in FAMILIES)

    # --- declared endpoint identity against the frozen VR tree ------------
    def endpoint_check(vr_root: Path) -> dict:
        per_backbone = {bb: {"n": 0, "exact": 0, "worst": 0.0}
                        for bb in BACKBONES}
        for family in FAMILIES:
            for record in cells[family]:
                vr_path = (vr_root / family
                           / f"r{record['realization']:02d}/metrics.json")
                if not vr_path.is_file():
                    continue
                vr = json.loads(vr_path.read_text())
                last = str(record["n_rungs"] - 1)
                for where, arm, vr_arm in VR_ENDPOINT_MAP:
                    rung = "0" if where == "first" else last
                    for k in SUPPORT_KS:
                        for bb in BACKBONES:
                            a = record["results"][k][bb][rung]["arms"][arm]["nmse"]
                            b = vr["results"][k][bb][vr_arm]["nmse"]
                            delta = abs(a - b)
                            slot = per_backbone[bb]
                            slot["n"] += 1
                            slot["exact"] += int(delta < 1e-12)
                            slot["worst"] = max(slot["worst"], delta)
        n_checked = sum(v["n"] for v in per_backbone.values())
        worst = max((v["worst"] for v in per_backbone.values()), default=0.0)
        return {
            "n_comparisons": n_checked,
            "worst_abs_delta_nmse": worst,
            "tolerance": ENDPOINT_TOLERANCE,
            "pass": bool(n_checked > 0 and worst <= ENDPOINT_TOLERANCE),
            "bit_identical": bool(n_checked > 0 and worst < 1e-12),
            "per_backbone": per_backbone,
        }

    published = endpoint_check(VR_ROOT)
    like_for_like = (endpoint_check(VR_LIKE_ROOT)
                     if VR_LIKE_ROOT.is_dir() else None)
    endpoint_identity = {
        "gate": "like_for_like",
        "vs_vr_published_threads2_cloud": published,
        "vs_vr_refit_threads1_same_host": like_for_like,
        "deviation_diagnosis": (
            "Every deviation against the published VR tree is HistGB; all "
            "XGBoost comparisons are bit-identical. The published tree was "
            "fit at threads=2 on cloud-hq1Cey and this ladder at threads=1 "
            "on the local host; run_crta_v3_mcr_factorial_semisynth_v1.py "
            "documents that parallel histogram accumulation perturbs these "
            "fits at the bit level. Re-fitting the unmodified frozen VR "
            "runner at threads=1 on this host removes the deviation "
            "entirely. The declared tolerance was NOT relaxed; both "
            "comparisons are reported and the verdict gate uses the "
            "like-for-like one."),
        "pass": bool(like_for_like and like_for_like["pass"]),
    }

    sections: dict = {}
    for k in SUPPORT_KS:
        sections[k] = {"RL1_monotone_rise": {}, "RL2_endpoint_zero": {},
                       "RL2_endpoint_full": {}, "RL3_interior_middle": {},
                       "desc_constraint_channel_top": {}, "rung_table": {}}
        for backbone in BACKBONES:
            for family in FAMILIES:
                recs = cells[family]
                if not recs:
                    continue
                tag = f"{backbone}|{family}"
                rhos, u0, ulast, umid, slast = [], [], [], [], []
                per_k: dict = {}
                for record in recs:
                    ks, u, s = u_curve(record, k, backbone)
                    rhos.append(spearman(ks, u))
                    u0.append(u[0])
                    ulast.append(u[-1])
                    n_const = len(record["constituents"])
                    kstar = int(np.floor(n_const / 2 + 0.5))
                    umid.append(u[list(ks).index(float(kstar))])
                    slast.append(s[-1])
                    for idx, kk in enumerate(ks):
                        per_k.setdefault(str(int(kk)), {"u": [], "s": [],
                                                        "broken": []})
                        per_k[str(int(kk))]["u"].append(float(u[idx]))
                        per_k[str(int(kk))]["s"].append(float(s[idx]))
                        per_k[str(int(kk))]["broken"].append(
                            record["results"][k][backbone][str(int(kk))]
                            ["n_pairs_broken"])
                sections[k]["RL1_monotone_rise"][tag] = boot(
                    np.asarray(rhos), f"RL1|{family}|{backbone}|{k}")
                sections[k]["RL2_endpoint_zero"][tag] = boot(
                    np.asarray(u0), f"RL2z|{family}|{backbone}|{k}")
                sections[k]["RL2_endpoint_full"][tag] = boot(
                    np.asarray(ulast), f"RL2f|{family}|{backbone}|{k}")
                sections[k]["RL3_interior_middle"][tag] = boot(
                    np.asarray(umid), f"RL3|{family}|{backbone}|{k}")
                sections[k]["desc_constraint_channel_top"][tag] = boot(
                    np.asarray(slast), f"Stop|{family}|{backbone}|{k}")
                # Arm-level means over exactly the realizations that
                # contribute to U at this rung, so that
                # mean(free) - mean(op_true) == U(k) exactly.
                arm_mean: dict = {}
                for record in recs:
                    rungs = record["results"][k][backbone]
                    for kk, rung in rungs.items():
                        slot = arm_mean.setdefault(
                            kk, {a: [] for a in ("free", "op_true", "sig_true")})
                        for arm in slot:
                            slot[arm].append(rung["arms"][arm]["nmse"])
                sections[k]["rung_table"][tag] = {
                    kk: {"n_realizations": len(v["u"]),
                         "mean_pairs_broken": float(np.mean(v["broken"])),
                         "arm_mean_nmse": {
                             arm: float(np.mean(arm_mean[kk][arm]))
                             for arm in ("free", "op_true", "sig_true")},
                         "n_features": {
                             arm: sorted({r["results"][k][backbone][kk]["arms"]
                                          [arm]["n_features"] for r in recs
                                          if kk in r["results"][k][backbone]})
                             for arm in ("free", "op_true", "sig_true")},
                         "U": boot(np.asarray(v["u"]),
                                   f"Uk{kk}|{family}|{backbone}|{k}"),
                         "S": boot(np.asarray(v["s"]),
                                   f"Sk{kk}|{family}|{backbone}|{k}")}
                    for kk, v in sorted(per_k.items(), key=lambda kv: int(kv[0]))}
        sections[k]["RL1_monotone_rise"]["grid_pass"] = all(
            sections[k]["RL1_monotone_rise"][f"{bb}|{ff}"]["separated"]
            for bb in BACKBONES for ff in FAMILIES)
        sections[k]["RL2_endpoint_zero"]["grid_pass"] = all(
            sections[k]["RL2_endpoint_zero"][f"{bb}|{ff}"]["null"]
            for bb in BACKBONES for ff in FAMILIES)
        sections[k]["RL2_endpoint_full"]["grid_pass"] = all(
            sections[k]["RL2_endpoint_full"][f"{bb}|{ff}"]["separated"]
            for bb in BACKBONES for ff in FAMILIES)
        sections[k]["RL3_interior_middle"]["grid_pass"] = all(
            sections[k]["RL3_interior_middle"][f"{bb}|{ff}"]["separated"]
            for bb in BACKBONES for ff in FAMILIES)

    if complete and endpoint_identity["pass"]:
        primary = sections[PRIMARY_K]
        verdicts = {
            "RL1_monotone_rise": bool(primary["RL1_monotone_rise"]["grid_pass"]),
            "RL2_endpoints_reproduce_vr": bool(
                primary["RL2_endpoint_zero"]["grid_pass"]
                and primary["RL2_endpoint_full"]["grid_pass"]),
            "RL3_interior_not_a_step": bool(
                primary["RL3_interior_middle"]["grid_pass"]),
        }
        verdicts["graded_redundancy_budget"] = bool(
            verdicts["RL1_monotone_rise"] and verdicts["RL3_interior_not_a_step"])
    elif not endpoint_identity["pass"]:
        verdicts = {"status": "endpoint identity failed — verdicts withheld"}
    else:
        verdicts = {"status": "incomplete — verdicts withheld"}

    payload = {
        "n_cells": sum(len(v) for v in cells.values()),
        "primary_support_k": PRIMARY_K,
        "metric": "nMSE = MSE/Var(y_query), lower is better; "
                  "U = nmse(free) - nmse(op_true), positive = ops help",
        "bootstrap": {"reps": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED,
                      "win_threshold": WIN_THRESHOLD,
                      "null_margin": NULL_MARGIN},
        "endpoint_identity_vs_vr": endpoint_identity,
        "versions": sorted({json.dumps(r.get("versions", {}), sort_keys=True)
                            for f in FAMILIES for r in cells[f]}),
        "hosts": sorted({r.get("host", "?") for f in FAMILIES for r in cells[f]}),
        "n_constituents": {f: sorted({len(r["constituents"]) for r in cells[f]})
                           for f in FAMILIES if cells[f]},
        "sections": sections,
        "verdicts": verdicts,
    }
    out_path = args.root / "SUMMARY_V1.json"
    out_path.write_text(json.dumps(payload, indent=1, sort_keys=True))
    print(json.dumps({"written": str(out_path),
                      "endpoint_identity": endpoint_identity,
                      "verdicts": verdicts}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
