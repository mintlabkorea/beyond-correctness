#!/usr/bin/env python3
"""Adjudicate one v3 lesion ladder (dose 0 = the v2 source-only α=0 tree).

P1: cluster-mean per-unit Spearman(I*, dose) < 0 with CI95 below 0.
P2: I*(0) − I*(1) > 0, CI low > 0, win ≥ .6.  Audits are recomputed from
the frozen seeds (column permutations / render parameters / pool
permutation) and nesting is checked across doses where applicable.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
V3 = ROOT / "scripts/run_crta_v3_stage_ladder_v3_lesions_v1.py"
DEFAULT_ROOT = ROOT / "experiments/crta_v3_stage_ladder_v3_lesions_v1"
V2_ROOT = ROOT / "experiments/crta_v3_stage_source_ladder_v2_source_only_v1"
DIRECTIONS = ("nh2kn", "kn2nh")
DOSES_NEW = (0.25, 0.50, 0.75, 1.00)
DOSES_FULL = (0.0, 0.25, 0.50, 0.75, 1.00)
SEEDS = tuple(range(50, 60))
K = "256"
REPS = 10000
SEED = 20260820
WIN = 0.60


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m


v3 = _load("stage_ladder_v3_for_summary", V3)
v1 = _load("stage_ladder_v1_for_v3_summary", v3.V1)
ladder = v1.load("mcr_source_ladder_frozen_v3s", v1.MCR_LADDER)


def interaction(arms, corrected=True):
    f = (lambda x: max(float(x), 1.0 - float(x))) if corrected else float
    return ((f(arms["a11_stage_columns"]) - f(arms["a10_stage"]))
            - (f(arms["a01_columns"]) - f(arms["a00_base"])))


def boot(values, key):
    seed = int(hashlib.sha256(f"stage_ladder_v3|{SEED}|{key}".encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    chosen = rng.integers(0, len(values), size=(REPS, len(values)))
    means = values[chosen].mean(axis=1)
    return {"mean": float(np.mean(values)), "ci95": [float(np.quantile(means, .025)), float(np.quantile(means, .975))],
            "win_positive": float(np.mean(values > 0)), "n": int(len(values))}


def verify(root: Path, lesion: str, endpoints) -> dict:
    checked, nested_ok = 0, True
    for d in DIRECTIONS:
        audits = {dose: json.loads((root / lesion / d / f"dose_{dose:.2f}" / "LESION_AUDIT_V1.json").read_text())
                  for dose in DOSES_NEW}
        for e in endpoints:
            for s in SEEDS:
                prev_moved: dict[str, set] = {}
                for dose in DOSES_NEW:
                    entry = audits[dose]["cells"].get(f"{e}|seed_{s}")
                    if entry is None:
                        raise RuntimeError(f"audit entry missing {lesion} {d} {dose} {e} s{s}")
                    prov = v3.LesionProvider(ladder, v1.stable_seed, lesion, d, dose)
                    n_src, n_pool = int(entry["n_source"]), int(entry["n_pool"])
                    if lesion == "source_feature_colperm":
                        cols = sorted(entry["column_perm_sha256"])
                        perms = prov.colperms(e, s, cols, n_src)
                        for c in cols:
                            if v3.sha_arr(perms[c].astype("<i8")) != entry["column_perm_sha256"][c]:
                                raise RuntimeError(f"colperm sha mismatch {d} {dose} {e} s{s} {c}")
                            moved = set(np.where(perms[c] != np.arange(n_src))[0].tolist())
                            if not prev_moved.get(c, set()).issubset(moved):
                                nested_ok = False
                            prev_moved[c] = moved
                    elif lesion == "source_feature_render":
                        # The audited slot_order is already the keyed permutation of the
                        # builder's column order; verify the slot set, the dose size, and
                        # every dosed slot's parameters (keyed per slot, order-free).
                        audited = entry["slot_order"]
                        if sorted(audited) != sorted(set(audited)) or e in audited:
                            raise RuntimeError(f"slot order malformed {d} {dose} {e} s{s}")
                        k = int(np.ceil(dose * len(audited)))
                        if set(entry["params"]) != set(audited[:k]):  # audit JSON is key-sorted
                            raise RuntimeError(f"dosed slots != prefix {d} {dose} {e} s{s}")
                        _, params = prov.render_plan(e, s, audited)  # params keyed per slot
                        for slot, pv in entry["params"].items():
                            rng = np.random.default_rng(prov.ss(v3.NS["source_feature_render"][1], d, e, s, slot))
                            if pv["kind"] == "code_permutation":
                                if pv["perm_seed"] != int(rng.integers(0, 2**31 - 1)):
                                    raise RuntimeError(f"render param mismatch {d} {dose} {e} s{s} {slot}")
                            else:
                                sc = float(np.exp(rng.uniform(np.log(0.25), np.log(4.0)))); of = float(rng.uniform(-2.0, 2.0))
                                if abs(pv["scale"] - sc) > 1e-12 or abs(pv["offset_sd"] - of) > 1e-12:
                                    raise RuntimeError(f"render param mismatch {d} {dose} {e} s{s} {slot}")
                        cur = set(entry["params"])
                        if not prev_moved.get("slots", set()).issubset(cur):
                            nested_ok = False
                        prev_moved["slots"] = cur
                    else:
                        perm = prov.pool_perm(e, s, n_pool)
                        if v3.sha_arr(perm.astype("<i8")) != entry["pool_perm_sha256"]:
                            raise RuntimeError(f"pool perm sha mismatch {d} {dose} {e} s{s}")
                        moved = set(np.where(perm != np.arange(n_pool))[0].tolist())
                        if not prev_moved.get("pool", set()).issubset(moved):
                            nested_ok = False
                        prev_moved["pool"] = moved
                    checked += 1
    if not nested_ok:
        raise RuntimeError("doses not nested")
    return {"cells_verified": checked, "nested": True}


def curves(root, lesion, endpoints, corrected):
    out = {}
    for d in DIRECTIONS:
        for e in endpoints:
            curve = []
            for dose in DOSES_FULL:
                vals = []
                for s in SEEDS:
                    if dose == 0.0:
                        p = V2_ROOT / d / "alpha_0.00" / e / f"seed_{s}" / "metrics.json"
                    else:
                        p = root / lesion / d / f"dose_{dose:.2f}" / e / f"seed_{s}" / "metrics.json"
                    rec = json.loads(p.read_text())
                    if rec.get("m_axis") != "source_only_fork_v1":
                        raise RuntimeError(f"not a source-only cell: {p}")
                    v = interaction(rec["auroc"][K], corrected)
                    if not np.isfinite(v):
                        raise RuntimeError(f"non-finite I* {p}")
                    vals.append(v)
                curve.append(float(np.mean(vals)))
            out[(d, e)] = curve
    return out


def adjudicate(cv, endpoints, tag):
    rho = {u: float(spearmanr(DOSES_FULL, c).statistic) for u, c in cv.items()}
    dec = {u: c[0] - c[-1] for u, c in cv.items()}
    cl = lambda per: np.asarray([np.mean([per[(d, e)] for d in DIRECTIONS]) for e in endpoints])
    p1 = boot(cl(rho), f"P1|{tag}"); p1["pass"] = bool(p1["mean"] < 0 and p1["ci95"][1] < 0)
    p2 = boot(cl(dec), f"P2|{tag}"); p2["pass"] = bool(p2["mean"] > 0 and p2["ci95"][0] > 0 and p2["win_positive"] >= WIN)
    pooled = {f"{a:.2f}": boot(cl({u: c[i] for u, c in cv.items()}), f"pooled|{tag}|{a:.2f}") for i, a in enumerate(DOSES_FULL)}
    return {"P1_spearman": p1, "P2_decline": p2, "pooled_I_by_dose": pooled,
            "per_direction_mean_curve": {d: [float(np.mean([cv[(d, e)][i] for e in endpoints])) for i in range(5)] for d in DIRECTIONS},
            "endpoint_cluster_rho": {e: float(r) for e, r in zip(endpoints, cl(rho))}}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lesion", required=True, choices=v3.LESIONS)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = ap.parse_args()
    reg = _load("stage_registry_v3s", ROOT / "scripts/crta_v3_stage_endpoint_registry_v1.py")
    endpoints = sorted(reg.ENDPOINTS)
    expected = len(DIRECTIONS) * len(endpoints) * len(SEEDS) * len(DOSES_NEW)
    found = sum(1 for d in DIRECTIONS for a in DOSES_NEW for e in endpoints for s in SEEDS
                if (args.root / args.lesion / d / f"dose_{a:.2f}" / e / f"seed_{s}" / "metrics.json").is_file())
    payload = {"lesion": args.lesion, "expected_cells": expected, "found_cells": found, "doses": list(DOSES_FULL)}
    if found == expected:
        payload["audit_check"] = verify(args.root, args.lesion, endpoints)
        cor = curves(args.root, args.lesion, endpoints, True)
        payload["corrected"] = adjudicate(cor, endpoints, f"{args.lesion}|corrected")
        payload["raw_descriptive"] = adjudicate(curves(args.root, args.lesion, endpoints, False), endpoints, f"{args.lesion}|raw")
        no_diab = [e for e in endpoints if e != "diabetes_history"]
        payload["drop_diabetes_sensitivity"] = adjudicate({u: c for u, c in cor.items() if u[1] != "diabetes_history"}, no_diab, f"{args.lesion}|nodiab")
        payload["verdicts"] = {"P1": payload["corrected"]["P1_spearman"]["pass"], "P2": payload["corrected"]["P2_decline"]["pass"]}
        payload["verdicts"]["ladder"] = bool(payload["verdicts"]["P1"] and payload["verdicts"]["P2"])
    else:
        payload["verdicts"] = {"status": "incomplete — verdicts withheld"}
    out = args.root / args.lesion / "SUMMARY_V1.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=1, sort_keys=True))
    print(json.dumps({"lesion": args.lesion, "verdicts": payload["verdicts"], "cells": f"{found}/{expected}"}, indent=1))


if __name__ == "__main__":
    raise SystemExit(main())
