"""MCR-MD: measurement utility as a function of mismatch dose.

Adds the M-absent (raw source) reference the factorial lacks and doses
the number of source features recorded discrepantly from the canonical
frame.  C is true routing and R is free in every arm.
Prereg: iclr_latex_v3/MCR_MISMATCH_DOSE_PREREGISTRATION_V1.md.
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
PREREG = ROOT / "iclr_latex_v3/MCR_MISMATCH_DOSE_PREREGISTRATION_V1.md"
DEFAULT_OUT = ROOT / "experiments/crta_v3_mcr_mismatch_dose_v1"

MD_NS = "mcr_mismatch_dose_v1"
DOSES = (0, 2, 4, 6, 8)
SUPPORT_KS = (32, 512)
BACKBONE_KS = (("xgb", 32), ("xgb", 512), ("histgb", 32))
ZERO_CONSTRAINTS = tuple([0] * 8)


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


def dose_order(mcr, family: str, realization: int,
               ordinal: tuple[int, ...]) -> list[int]:
    """Outcome-blind balanced order: o0,c0,o1,c1,o2,c2,o3,c3 (nested)."""
    continuous = [j for j in range(8) if j not in set(ordinal)]
    rng_o = np.random.default_rng(
        mcr.stable_seed(MD_NS, "dose_order", family, realization, "ordinal"))
    rng_c = np.random.default_rng(
        mcr.stable_seed(MD_NS, "dose_order", family, realization,
                        "continuous"))
    ord_seq = [ordinal[i] for i in rng_o.permutation(len(ordinal))]
    cont_seq = [continuous[i] for i in rng_c.permutation(len(continuous))]
    order: list[int] = []
    for o, c in zip(ord_seq, cont_seq):
        order.extend((o, c))
    if sorted(order) != list(range(8)):
        raise AssertionError("dose order must cover all 8 features")
    return order


def hybrid_source(cell, rendering, canonical_source: np.ndarray,
                  order: list[int], dose: int,
                  sentinel_neutral: bool) -> np.ndarray:
    out = canonical_source.copy()
    for j in order[:dose]:
        column = cell.source_rendered[:, j].copy()
        if sentinel_neutral:
            column[column == rendering.sentinel[j]] = np.nan
        out[:, j] = column
    return out


def frames_equal(a: np.ndarray, b: np.ndarray) -> bool:
    return bool(np.array_equal(a, b, equal_nan=True))


def mismatch_entries(hybrid: np.ndarray, canonical: np.ndarray) -> int:
    same = (hybrid == canonical) | (np.isnan(hybrid) & np.isnan(canonical))
    return int(np.sum(~same))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--families", nargs="*", default=None)
    parser.add_argument("--realizations", nargs="*", type=int, default=None)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()

    mcr = _load("mcr_core", MCR_RUNNER)
    families = args.families or list(mcr.FAMILIES)
    realizations = (args.realizations if args.realizations is not None
                    else list(range(mcr.N_REALIZATIONS)))
    provenance = {
        "input_sha256": sha256_file(mcr.DEFAULT_INPUT),
        "runner_sha256": sha256_file(Path(__file__)),
        "mcr_runner_sha256": sha256_file(MCR_RUNNER),
        "prereg_sha256": sha256_file(PREREG),
        "rng_namespace": mcr.RNG_NS,
        "dose_namespace": MD_NS,
    }
    panel = mcr.load_panel(mcr.DEFAULT_INPUT)
    print(json.dumps(provenance), flush=True)

    for family in families:
        for realization in realizations:
            out_dir = args.out_root / family / f"r{realization:02d}"
            metrics_path = out_dir / "metrics.json"
            if metrics_path.is_file():
                existing = json.loads(metrics_path.read_text())
                if any(existing.get(k) != provenance[k] for k in
                       ("runner_sha256", "mcr_runner_sha256",
                        "input_sha256", "prereg_sha256")):
                    raise RuntimeError(
                        f"{metrics_path} does not match current provenance; "
                        "archive that tree before resuming.")
                continue
            started = time.time()
            cell = mcr.build_cell(panel, "primary", family, realization,
                                  SUPPORT_KS)
            ordinal = tuple(cell.audit["ordinal_features"])
            bins = mcr.canonical_bins(panel, ordinal)
            rendering = mcr.draw_side_rendering(
                ordinal, ("primary", family, realization, "source"), False)
            rebuilt = mcr.render_side(panel, cell.source_rows, rendering, bins)
            if not frames_equal(rebuilt, cell.source_rendered):
                raise AssertionError("source rendering rebuild mismatch")
            canonical_source = mcr.decode(cell.source_rendered,
                                          cell.source_tables["true"])
            order = dose_order(mcr, family, realization, ordinal)

            # construction asserts (prereg)
            if not frames_equal(hybrid_source(cell, rendering,
                                              canonical_source, order, 0,
                                              True), canonical_source):
                raise AssertionError("d=0 raw must equal decode")
            full_sent = hybrid_source(cell, rendering, canonical_source,
                                      order, 8, False)
            if not np.array_equal(full_sent, cell.source_rendered):
                raise AssertionError("d=8 rawsent must equal the rendering")
            neutral_full = cell.source_rendered.copy()
            for j in range(8):
                neutral_full[neutral_full[:, j] == rendering.sentinel[j],
                             j] = np.nan
            if not frames_equal(hybrid_source(cell, rendering,
                                              canonical_source, order, 8,
                                              True), neutral_full):
                raise AssertionError("d=8 raw must equal neutralized render")

            raw_frames = {d: hybrid_source(cell, rendering, canonical_source,
                                           order, d, True) for d in DOSES}
            sent_frames = {d: hybrid_source(cell, rendering, canonical_source,
                                            order, d, False) for d in DOSES}
            counts = [mismatch_entries(raw_frames[d], canonical_source)
                      for d in DOSES]
            if any(b < a for a, b in zip(counts, counts[1:])):
                raise AssertionError("mismatch entry counts must not decrease")

            y_query = cell.y[cell.query_rows]
            query_var = float(np.var(y_query, ddof=0))
            x_query = cell.target_decoded_query
            results: dict[str, dict[str, dict[str, dict[str, float]]]] = {}
            for backbone, support_k in BACKBONE_KS:
                k_key = str(support_k)
                results.setdefault(k_key, {})
                target_support = cell.target_decoded_support[support_k]
                y_fit = np.concatenate([
                    cell.y[cell.source_rows],
                    cell.y[cell.supports[support_k]]])
                weights = np.ones(len(y_fit))

                x_decode = np.vstack([canonical_source, target_support])
                ref = mcr.arm_matrices(cell, "m1c1rf", support_k,
                                       weighted=False)
                if not (frames_equal(x_decode, ref[0])
                        and np.array_equal(y_fit, ref[1])):
                    raise AssertionError("decode arm must equal m1c1rf")

                arm_records: dict[str, dict[str, float]] = {}

                def fit(matrix: np.ndarray) -> dict[str, float]:
                    prediction = mcr.fit_predict(
                        backbone, matrix, y_fit, weights, x_query,
                        ZERO_CONSTRAINTS, seed=realization,
                        threads=args.threads)
                    mse = float(np.mean((y_query - prediction) ** 2))
                    return {"nmse": mse / query_var,
                            "nrmse": float(np.sqrt(mse / query_var)),
                            "nan_fraction_fit":
                                float(np.mean(np.isnan(matrix)))}

                arm_records["decode"] = fit(x_decode)
                for label, frames in (("raw", raw_frames),
                                      ("rawsent", sent_frames)):
                    for d in DOSES:
                        name = f"{label}_d{d}"
                        if d == 0:
                            arm_records[name] = dict(
                                arm_records["decode"],
                                identical_by_construction=True)
                            continue
                        arm_records[name] = fit(
                            np.vstack([frames[d], target_support]))
                results[k_key][backbone] = arm_records

            composition = []
            for d in DOSES:
                dosed = order[:d]
                composition.append({
                    "dose": d,
                    "ordinal_reversed": sum(
                        1 for j in dosed if j in rendering.direction
                        and rendering.direction[j] < 0),
                    "ordinal_total": sum(
                        1 for j in dosed if j in rendering.direction),
                    "continuous_total": sum(
                        1 for j in dosed if j not in rendering.direction),
                })
            payload = {
                "mode": "mismatch_dose",
                "family": family,
                "realization": realization,
                "doses": list(DOSES),
                "dose_order": order,
                "mismatch_entry_counts": counts,
                "dose_composition": composition,
                "supports": sorted({str(k) for _, k in BACKBONE_KS}),
                "results": results,
                "wall_seconds": round(time.time() - started, 2),
                **provenance,
            }
            out_dir.mkdir(parents=True, exist_ok=True)
            metrics_path.write_text(json.dumps(payload, indent=1,
                                               sort_keys=True))
            print(f"{family} r{realization:02d} done "
                  f"({payload['wall_seconds']}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
