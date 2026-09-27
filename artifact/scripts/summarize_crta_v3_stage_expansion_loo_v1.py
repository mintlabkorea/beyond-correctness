#!/usr/bin/env python3
"""Leave-one-endpoint-out sensitivity of the frozen ten-endpoint
bidirectional stage-factorial interaction (no new fits).

For each dropped endpoint, the pooled corrected interaction
I* = (f(a11)-f(a10)) - (f(a01)-f(a00)), f(A)=max(A,1-A), is re-estimated
over the remaining 9 endpoint clusters (each cluster = mean over its two
directions and ten seeds) with the frozen post-hoc endpoint-clustered
bootstrap convention (10,000 reps, seed 20260820).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ROOTS = {"nh2kn": ROOT / "experiments/crta_v3_stage_endpoint_expansion_nh2kn_v1",
         "kn2nh": ROOT / "experiments/crta_v3_stage_endpoint_expansion_kn2nh_v1"}
SEEDS = tuple(range(50, 60))
K = "256"
REPS = 10000
SEED = 20260820


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m


def interaction(arms, corrected=True):
    f = (lambda x: max(float(x), 1.0 - float(x))) if corrected else float
    return ((f(arms["a11_stage_columns"]) - f(arms["a10_stage"]))
            - (f(arms["a01_columns"]) - f(arms["a00_base"])))


def boot(values, key):
    seed = int(hashlib.sha256(f"stage_loo|{SEED}|{key}".encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    chosen = rng.integers(0, len(values), size=(REPS, len(values)))
    means = values[chosen].mean(axis=1)
    return {"mean": float(np.mean(values)),
            "ci95": [float(np.quantile(means, .025)), float(np.quantile(means, .975))],
            "win": float(np.mean(values > 0)), "n": int(len(values))}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path,
                    default=ROOT / "experiments/crta_v3_stage_endpoint_expansion_loo_v1")
    args = ap.parse_args()
    reg = _load("reg", ROOT / "scripts/crta_v3_stage_endpoint_registry_v1.py")
    endpoints = sorted(reg.ENDPOINTS)
    cluster = {}
    for e in endpoints:
        vals = []
        for d, root in ROOTS.items():
            unit = [interaction(json.loads((root / e / f"seed_{s}" / "metrics.json").read_text())["auroc"][K])
                    for s in SEEDS]
            vals.append(float(np.mean(unit)))
        cluster[e] = float(np.mean(vals))
    full = boot(np.asarray([cluster[e] for e in endpoints]), "all")
    loo = {}
    for drop in endpoints:
        keep = [cluster[e] for e in endpoints if e != drop]
        loo[drop] = boot(np.asarray(keep), f"drop|{drop}")
        loo[drop]["ci_excludes_zero"] = bool(loo[drop]["ci95"][0] > 0)
    payload = {"endpoint_cluster_means": cluster, "all_endpoints": full,
               "leave_one_out": loo,
               "n_loo_ci_above_zero": int(sum(v["ci_excludes_zero"] for v in loo.values())),
               "bootstrap": {"reps": REPS, "seed": SEED,
                             "unit": "endpoint cluster (two directions x ten seeds averaged)"}}
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "SUMMARY_V1.json").write_text(json.dumps(payload, indent=1, sort_keys=True))
    print(f"all: {full['mean']:+.4f} [{full['ci95'][0]:+.4f},{full['ci95'][1]:+.4f}] win {full['win']:.2f}")
    for e in sorted(loo, key=lambda k: loo[k]["mean"]):
        v = loo[e]
        print(f"drop {e:24s}: {v['mean']:+.4f} [{v['ci95'][0]:+.4f},{v['ci95'][1]:+.4f}] "
              f"{'CI>0' if v['ci_excludes_zero'] else 'CI crosses 0'}")
    print(f"LOO variants with CI above zero: {payload['n_loo_ci_above_zero']}/10")


if __name__ == "__main__":
    raise SystemExit(main())
