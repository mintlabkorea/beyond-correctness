#!/usr/bin/env python3
"""MCR-MD-T: the mismatch-dose experiment on TabPFN.

Frozen design and verdicts:
`iclr_latex_v3/MCR_MISMATCH_DOSE_TABPFN_PREREGISTRATION_V1.md`.

Imports the frozen MCR runner (cells) and the frozen MD runner (dose
order, hybrid source construction) so that every dosed frame is
byte-identical to the tree experiment's; asserts the recorded
`dose_order` and `mismatch_entry_counts` of the frozen MD cell.  TabPFN
receives value inputs only (no constraint vector exists).  K=32 only.
Metric: nMSE (verdicts) + nRMSE (descriptive).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MCR_RUNNER = ROOT / "scripts/run_crta_v3_mcr_factorial_semisynth_v1.py"
MD_RUNNER = ROOT / "scripts/run_crta_v3_mcr_mismatch_dose_v1.py"
PREREG = ROOT / "iclr_latex_v3/MCR_MISMATCH_DOSE_TABPFN_PREREGISTRATION_V1.md"
MD_ROOT = ROOT / "experiments/crta_v3_mcr_mismatch_dose_v1"
DEFAULT_OUT = ROOT / "experiments/crta_v3_mcr_mismatch_dose_tabpfn_v1"

SUPPORT_K = 32
DOSES = (0, 2, 4, 6, 8)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--families", nargs="*", default=None)
    parser.add_argument("--realizations", nargs="*", type=int, default=None)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--input", type=Path, default=None,
                        help="benchmark parquet; defaults to the frozen local path")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    mcr = _load("mcr_core", MCR_RUNNER)
    md = _load("mcr_md_core", MD_RUNNER)
    if tuple(md.DOSES) != DOSES:
        raise RuntimeError("dose grid differs from the frozen MD runner")
    input_path = args.input or mcr.DEFAULT_INPUT
    families = args.families or list(mcr.FAMILIES)
    realizations = (args.realizations if args.realizations is not None
                    else list(range(mcr.N_REALIZATIONS)))
    provenance = {
        "input_sha256": sha256_file(input_path),
        "runner_sha256": sha256_file(Path(__file__)),
        "mcr_runner_sha256": sha256_file(MCR_RUNNER),
        "md_runner_sha256": sha256_file(MD_RUNNER),
        "prereg_sha256": sha256_file(PREREG),
        "rng_namespace": mcr.RNG_NS,
        "dose_namespace": md.MD_NS,
    }
    for family in families:
        for realization in realizations:
            frozen = MD_ROOT / family / f"r{realization:02d}" / "metrics.json"
            if not frozen.is_file():
                raise RuntimeError(f"missing frozen MD cell: {frozen}")
    if args.validate_only:
        print(json.dumps({"expected_cells": len(families) * len(realizations),
                          "fits_per_cell": 9, **provenance},
                         indent=1, sort_keys=True))
        return 0

    from tabpfn import TabPFNRegressor
    panel = mcr.load_panel(input_path)
    print(json.dumps(provenance), flush=True)

    for family in families:
        for realization in realizations:
            out_dir = args.out_root / family / f"r{realization:02d}"
            metrics_path = out_dir / "metrics.json"
            if metrics_path.is_file():
                existing = json.loads(metrics_path.read_text())
                if any(existing.get(k) != provenance[k] for k in
                       ("runner_sha256", "mcr_runner_sha256",
                        "md_runner_sha256", "input_sha256",
                        "prereg_sha256")):
                    raise RuntimeError(
                        f"{metrics_path} does not match current provenance; "
                        "archive that tree before resuming.")
                continue
            started = time.time()
            frozen_path = MD_ROOT / family / f"r{realization:02d}" / "metrics.json"
            frozen_cell = json.loads(frozen_path.read_text())

            cell = mcr.build_cell(panel, "primary", family, realization,
                                  (SUPPORT_K,))
            ordinal = tuple(cell.audit["ordinal_features"])
            bins = mcr.canonical_bins(panel, ordinal)
            rendering = mcr.draw_side_rendering(
                ordinal, ("primary", family, realization, "source"), False)
            rebuilt = mcr.render_side(panel, cell.source_rows, rendering, bins)
            if not md.frames_equal(rebuilt, cell.source_rendered):
                raise AssertionError("source rendering rebuild mismatch")
            canonical_source = mcr.decode(cell.source_rendered,
                                          cell.source_tables["true"])
            order = md.dose_order(mcr, family, realization, ordinal)
            if list(order) != list(frozen_cell["dose_order"]):
                raise AssertionError("dose order differs from the frozen MD cell")

            # construction asserts (inherited from MD)
            if not md.frames_equal(md.hybrid_source(
                    cell, rendering, canonical_source, order, 0, True),
                    canonical_source):
                raise AssertionError("d=0 raw must equal decode")
            full_sent = md.hybrid_source(cell, rendering, canonical_source,
                                         order, 8, False)
            if not np.array_equal(full_sent, cell.source_rendered):
                raise AssertionError("d=8 rawsent must equal the rendering")
            neutral_full = cell.source_rendered.copy()
            for j in range(8):
                neutral_full[neutral_full[:, j] == rendering.sentinel[j],
                             j] = np.nan
            if not md.frames_equal(md.hybrid_source(
                    cell, rendering, canonical_source, order, 8, True),
                    neutral_full):
                raise AssertionError("d=8 raw must equal neutralized render")

            raw_frames = {d: md.hybrid_source(cell, rendering, canonical_source,
                                              order, d, True) for d in DOSES}
            sent_frames = {d: md.hybrid_source(cell, rendering,
                                               canonical_source, order, d,
                                               False) for d in DOSES}
            counts = [md.mismatch_entries(raw_frames[d], canonical_source)
                      for d in DOSES]
            if any(b < a for a, b in zip(counts, counts[1:])):
                raise AssertionError("mismatch entry counts must not decrease")
            if counts != list(frozen_cell["mismatch_entry_counts"]):
                raise AssertionError(
                    "mismatch entry counts differ from the frozen MD cell")

            y_query = cell.y[cell.query_rows]
            query_var = float(np.var(y_query, ddof=0))
            x_query = cell.target_decoded_query
            target_support = cell.target_decoded_support[SUPPORT_K]
            y_fit = np.concatenate([
                cell.y[cell.source_rows], cell.y[cell.supports[SUPPORT_K]]])

            x_decode = np.vstack([canonical_source, target_support])
            ref = mcr.arm_matrices(cell, "m1c1rf", SUPPORT_K, weighted=False)
            if not (md.frames_equal(x_decode, ref[0])
                    and np.array_equal(y_fit, ref[1])):
                raise AssertionError("decode arm must equal m1c1rf")

            def fit(matrix: np.ndarray) -> dict[str, float]:
                model = TabPFNRegressor(device=args.device,
                                        random_state=realization)
                model.fit(matrix, y_fit)
                prediction = np.asarray(model.predict(x_query),
                                        dtype=np.float64)
                mse = float(np.mean((y_query - prediction) ** 2))
                return {"nmse": mse / query_var,
                        "nrmse": float(np.sqrt(mse / query_var)),
                        "nan_fraction_fit": float(np.mean(np.isnan(matrix)))}

            arm_records: dict[str, dict[str, float]] = {"decode": fit(x_decode)}
            for label, frames in (("raw", raw_frames), ("rawsent", sent_frames)):
                for d in DOSES:
                    name = f"{label}_d{d}"
                    if d == 0:
                        arm_records[name] = dict(arm_records["decode"],
                                                 identical_by_construction=True)
                        continue
                    arm_records[name] = fit(np.vstack([frames[d], target_support]))

            payload = {
                "mode": "mismatch_dose_tabpfn",
                "family": family,
                "realization": realization,
                "support_k": SUPPORT_K,
                "backbone": "tabpfn_7_regressor",
                "device": args.device,
                "doses": list(DOSES),
                "dose_order": order,
                "mismatch_entry_counts": counts,
                "dose_composition": frozen_cell["dose_composition"],
                "paired_construction_gate": {"dose_order": True,
                                             "mismatch_entry_counts": True},
                "frozen_md_cell_sha256": sha256_file(frozen_path),
                "results": {str(SUPPORT_K): {"tabpfn": arm_records}},
                "wall_seconds": round(time.time() - started, 1),
                **provenance,
            }
            out_dir.mkdir(parents=True, exist_ok=True)
            metrics_path.write_text(json.dumps(payload, indent=1, sort_keys=True)
                                    + "\n", encoding="utf-8")
            print(json.dumps({"family": family, "realization": realization,
                              "wall_seconds": payload["wall_seconds"],
                              "done": True}), flush=True)
    print(json.dumps({"status": "complete"}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
