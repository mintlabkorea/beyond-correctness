"""Construction tests for the non-semantic rank-alignment audit."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


rank = _load(
    "rank_audit",
    ROOT / "scripts/run_crta_v3_mcr_nonsemantic_rank_alignment_v1.py",
)
mcr = _load(
    "rank_mcr_core", ROOT / "scripts/run_crta_v3_mcr_factorial_semisynth_v1.py"
)
md = _load(
    "rank_md_core", ROOT / "scripts/run_crta_v3_mcr_mismatch_dose_v1.py"
)


def unit_checks() -> None:
    reference = np.asarray([[1.0], [2.0], [2.0], [4.0], [np.nan]])
    values = np.asarray([[0.0], [1.0], [2.0], [3.0], [4.0], [5.0], [np.nan]])
    got = rank.empirical_mid_transform(reference, values)[:, 0]
    expected = np.asarray([0.0, 0.125, 0.5, 0.75, 0.875, 1.0, np.nan])
    assert np.allclose(got, expected, equal_nan=True), (got, expected)

    frame = np.asarray([
        [1.0, 5.0], [2.0, 3.0], [4.0, np.nan], [8.0, 1.0]
    ])
    positive_affine = frame * np.asarray([3.0, 7.0]) + np.asarray([11.0, -4.0])
    base_rank = rank.empirical_mid_transform(frame, frame)
    affine_rank = rank.empirical_mid_transform(positive_affine, positive_affine)
    assert np.allclose(base_rank, affine_rank, equal_nan=True)

    reverse = frame.copy()
    reverse[:, 0] *= -1
    reverse_rank = rank.empirical_mid_transform(reverse, reverse)
    finite = np.isfinite(base_rank[:, 0])
    assert np.allclose(
        reverse_rank[finite, 0], 1.0 - base_rank[finite, 0]
    )


def cell_checks() -> None:
    panel = mcr.load_panel(mcr.DEFAULT_INPUT)
    for family in mcr.FAMILIES:
        cell = mcr.build_cell(panel, "primary", family, 0, (32, 512))
        ordinal = tuple(cell.audit["ordinal_features"])
        bins = mcr.canonical_bins(panel, ordinal)
        rendering = mcr.draw_side_rendering(
            ordinal, ("primary", family, 0, "source"), False
        )
        canonical = mcr.decode(cell.source_rendered, cell.source_tables["true"])
        order = md.dose_order(mcr, family, 0, ordinal)
        raw_zero = md.hybrid_source(
            cell, rendering, canonical, order, 0, sentinel_neutral=True
        )
        assert rank.frames_equal(raw_zero, canonical)
        for support_k in (32, 512):
            support = cell.target_decoded_support[support_k]
            query = cell.target_decoded_query
            for regime in rank.MAP_REGIMES:
                decoded = rank.rank_frames(canonical, support, query, regime)
                raw = rank.rank_frames(raw_zero, support, query, regime)
                assert all(
                    rank.frames_equal(first, second)
                    for first, second in zip(decoded, raw)
                )
                for original, transformed in zip(
                    (canonical, support, query), decoded
                ):
                    rank.assert_rank_frame(original, transformed)
        print(f"{family}: construction checks passed")


def main() -> int:
    unit_checks()
    cell_checks()
    print("all non-semantic rank-alignment construction tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
