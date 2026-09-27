"""Matched 2x2 non-semantic rank-alignment audit for MCR mismatch dose.

The new arms apply a feature-wise, domain-specific empirical mid-distribution
transform to both documented-decoded and sentinel-neutral raw frames. Existing
no-rank metrics are imported after exact provenance and construction checks.

Frozen design:
iclr_latex_v3/MCR_NONSEMANTIC_RANK_ALIGNMENT_FREEZE_V1.md
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
MD_PREREG = ROOT / "iclr_latex_v3/MCR_MISMATCH_DOSE_PREREGISTRATION_V1.md"
PREREG = (
    ROOT / "iclr_latex_v3/MCR_NONSEMANTIC_RANK_ALIGNMENT_FREEZE_V1.md"
)
MD_ROOT = ROOT / "experiments/crta_v3_mcr_mismatch_dose_v1"
DEFAULT_OUT = ROOT / "experiments/crta_v3_mcr_nonsemantic_rank_alignment_v1"

MAP_REGIMES = ("support_only", "support_query")
DOSES = (0, 2, 4, 6, 8)
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


def empirical_mid_transform(reference: np.ndarray,
                            values: np.ndarray) -> np.ndarray:
    """Map columns through the reference empirical mid-distribution.

    A finite x maps to (count(ref < x) + .5 count(ref == x)) / n.
    Missing values remain missing; an empty reference column maps to missing.
    """
    if reference.ndim != 2 or values.ndim != 2:
        raise ValueError("rank inputs must be two-dimensional")
    if reference.shape[1] != values.shape[1]:
        raise ValueError("reference and values must have the same columns")
    out = np.full(values.shape, np.nan, dtype=np.float64)
    for column in range(reference.shape[1]):
        fit = np.asarray(reference[:, column], dtype=np.float64)
        fit = np.sort(fit[np.isfinite(fit)])
        value = np.asarray(values[:, column], dtype=np.float64)
        finite = np.isfinite(value)
        if not len(fit) or not np.any(finite):
            continue
        left = np.searchsorted(fit, value[finite], side="left")
        right = np.searchsorted(fit, value[finite], side="right")
        out[finite, column] = (left + right) / (2.0 * len(fit))
    return out


def rank_frames(source: np.ndarray, target_support: np.ndarray,
                target_query: np.ndarray, regime: str
                ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    source_rank = empirical_mid_transform(source, source)
    if regime == "support_only":
        target_reference = target_support
    elif regime == "support_query":
        target_reference = np.vstack([target_support, target_query])
    else:
        raise ValueError(f"unknown rank-map regime: {regime}")
    support_rank = empirical_mid_transform(target_reference, target_support)
    query_rank = empirical_mid_transform(target_reference, target_query)
    return source_rank, support_rank, query_rank


def frames_equal(first: np.ndarray, second: np.ndarray) -> bool:
    return bool(np.array_equal(first, second, equal_nan=True))


def assert_rank_frame(original: np.ndarray, transformed: np.ndarray) -> None:
    if original.shape != transformed.shape:
        raise AssertionError("rank transform changed frame shape")
    if not np.array_equal(np.isnan(original), np.isnan(transformed)):
        raise AssertionError("rank transform changed missingness")
    finite = transformed[np.isfinite(transformed)]
    if len(finite) and (float(finite.min()) < 0 or float(finite.max()) > 1):
        raise AssertionError("rank transform left the unit interval")


def compact_no_rank(original: dict, backbone: str, support_k: int) -> dict:
    arms = original["results"][str(support_k)][backbone]
    names = ("decode",) + tuple(f"raw_d{dose}" for dose in DOSES)
    return {name: dict(arms[name]) for name in names}


def validate_original(original: dict, metrics_path: Path, mcr, md,
                      family: str, realization: int,
                      provenance: dict) -> None:
    expected = {
        "mode": "mismatch_dose",
        "family": family,
        "realization": realization,
        "input_sha256": provenance["input_sha256"],
        "mcr_runner_sha256": provenance["mcr_runner_sha256"],
        "runner_sha256": provenance["md_runner_sha256"],
        "prereg_sha256": provenance["md_prereg_sha256"],
    }
    for key, value in expected.items():
        if original.get(key) != value:
            raise RuntimeError(
                f"{metrics_path}: original {key}={original.get(key)!r}, "
                f"expected {value!r}"
            )
    if tuple(original.get("doses", ())) != DOSES:
        raise RuntimeError(f"{metrics_path}: wrong original dose grid")


def fit_record(mcr, backbone: str, source: np.ndarray,
               target_support: np.ndarray, target_query: np.ndarray,
               y_fit: np.ndarray, y_query: np.ndarray, query_var: float,
               realization: int, threads: int) -> dict:
    x_fit = np.vstack([source, target_support])
    prediction = mcr.fit_predict(
        backbone, x_fit, y_fit, np.ones(len(y_fit)), target_query,
        ZERO_CONSTRAINTS, seed=realization, threads=threads,
    )
    mse = float(np.mean((y_query - prediction) ** 2))
    return {
        "nmse": mse / query_var,
        "nrmse": float(np.sqrt(mse / query_var)),
        "nan_fraction_fit": float(np.mean(np.isnan(x_fit))),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--families", nargs="*", default=None)
    parser.add_argument("--realizations", nargs="*", type=int, default=None)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()

    mcr = _load("mcr_rank_core", MCR_RUNNER)
    md = _load("mcr_rank_md", MD_RUNNER)
    families = args.families or list(mcr.FAMILIES)
    realizations = (
        args.realizations if args.realizations is not None
        else list(range(mcr.N_REALIZATIONS))
    )
    provenance = {
        "input_sha256": sha256_file(mcr.DEFAULT_INPUT),
        "runner_sha256": sha256_file(Path(__file__)),
        "mcr_runner_sha256": sha256_file(MCR_RUNNER),
        "md_runner_sha256": sha256_file(MD_RUNNER),
        "md_prereg_sha256": sha256_file(MD_PREREG),
        "prereg_sha256": sha256_file(PREREG),
    }
    panel = mcr.load_panel(mcr.DEFAULT_INPUT)
    print(json.dumps(provenance, sort_keys=True), flush=True)

    for family in families:
        for realization in realizations:
            out_dir = args.out_root / family / f"r{realization:02d}"
            metrics_path = out_dir / "metrics.json"
            if metrics_path.is_file():
                existing = json.loads(metrics_path.read_text())
                for key, value in provenance.items():
                    if existing.get(key) != value:
                        raise RuntimeError(
                            f"{metrics_path} has stale {key}; archive before resuming"
                        )
                continue

            started = time.time()
            original_path = MD_ROOT / family / f"r{realization:02d}" / "metrics.json"
            if not original_path.is_file():
                raise FileNotFoundError(original_path)
            original = json.loads(original_path.read_text())
            validate_original(
                original, original_path, mcr, md, family, realization, provenance
            )

            cell = mcr.build_cell(panel, "primary", family, realization, (32, 512))
            ordinal = tuple(cell.audit["ordinal_features"])
            bins = mcr.canonical_bins(panel, ordinal)
            rendering = mcr.draw_side_rendering(
                ordinal, ("primary", family, realization, "source"), False
            )
            rebuilt = mcr.render_side(panel, cell.source_rows, rendering, bins)
            if not frames_equal(rebuilt, cell.source_rendered):
                raise AssertionError("source rendering rebuild mismatch")
            canonical_source = mcr.decode(
                cell.source_rendered, cell.source_tables["true"]
            )
            order = md.dose_order(mcr, family, realization, ordinal)
            if order != original["dose_order"]:
                raise AssertionError("dose order differs from original experiment")
            raw_frames = {
                dose: md.hybrid_source(
                    cell, rendering, canonical_source, order, dose, True
                )
                for dose in DOSES
            }
            if not frames_equal(raw_frames[0], canonical_source):
                raise AssertionError("dose-zero raw frame differs from decode")

            y_query = cell.y[cell.query_rows]
            query_var = float(np.var(y_query, ddof=0))
            results: dict[str, dict] = {}
            construction: dict[str, dict] = {}

            for backbone, support_k in BACKBONE_KS:
                k_key = str(support_k)
                results.setdefault(k_key, {})
                construction.setdefault(k_key, {})
                target_support = cell.target_decoded_support[support_k]
                target_query = cell.target_decoded_query
                y_fit = np.concatenate([
                    cell.y[cell.source_rows],
                    cell.y[cell.supports[support_k]],
                ])
                backbone_results = {
                    "no_rank": compact_no_rank(original, backbone, support_k)
                }
                backbone_checks: dict[str, dict] = {}

                for regime in MAP_REGIMES:
                    decode_source_rank, support_rank, query_rank = rank_frames(
                        canonical_source, target_support, target_query, regime
                    )
                    assert_rank_frame(canonical_source, decode_source_rank)
                    assert_rank_frame(target_support, support_rank)
                    assert_rank_frame(target_query, query_rank)
                    rank_records = {
                        "decode_rank": fit_record(
                            mcr, backbone, decode_source_rank, support_rank,
                            query_rank, y_fit, y_query, query_var, realization,
                            args.threads,
                        )
                    }
                    raw_zero_rank, raw_support_rank, raw_query_rank = rank_frames(
                        raw_frames[0], target_support, target_query, regime
                    )
                    if not (
                        frames_equal(raw_zero_rank, decode_source_rank)
                        and frames_equal(raw_support_rank, support_rank)
                        and frames_equal(raw_query_rank, query_rank)
                    ):
                        raise AssertionError(
                            "dose-zero decoded/raw rank frames are not identical"
                        )
                    rank_records["raw_rank_d0"] = dict(
                        rank_records["decode_rank"], identical_by_construction=True
                    )
                    for dose in DOSES[1:]:
                        raw_source_rank, raw_support_rank, raw_query_rank = rank_frames(
                            raw_frames[dose], target_support, target_query, regime
                        )
                        assert_rank_frame(raw_frames[dose], raw_source_rank)
                        if not (
                            frames_equal(raw_support_rank, support_rank)
                            and frames_equal(raw_query_rank, query_rank)
                        ):
                            raise AssertionError(
                                "target rank map differs across decoded/raw arms"
                            )
                        rank_records[f"raw_rank_d{dose}"] = fit_record(
                            mcr, backbone, raw_source_rank, support_rank,
                            query_rank, y_fit, y_query, query_var, realization,
                            args.threads,
                        )
                    backbone_results[regime] = rank_records
                    backbone_checks[regime] = {
                        "dose_zero_identical": True,
                        "source_missingness_preserved": True,
                        "target_missingness_preserved": True,
                        "target_map_shared_across_arms": True,
                    }
                results[k_key][backbone] = backbone_results
                construction[k_key][backbone] = backbone_checks

            payload = {
                "mode": "nonsemantic_rank_alignment",
                "family": family,
                "realization": realization,
                "doses": list(DOSES),
                "dose_order": order,
                "map_regimes": list(MAP_REGIMES),
                "rank_definition": (
                    "(count(reference < x) + 0.5*count(reference == x)) / n"
                ),
                "results": results,
                "construction_checks": construction,
                "original_metrics_path": str(original_path.relative_to(ROOT)),
                "original_metrics_sha256": sha256_file(original_path),
                "wall_seconds": round(time.time() - started, 2),
                **provenance,
            }
            out_dir.mkdir(parents=True, exist_ok=True)
            metrics_path.write_text(json.dumps(payload, indent=1, sort_keys=True))
            print(
                f"{family} r{realization:02d} done "
                f"({payload['wall_seconds']}s)", flush=True
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
