"""Summarize the frozen non-semantic rank-alignment 2x2 audit."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "experiments/crta_v3_mcr_nonsemantic_rank_alignment_v1"

FAMILIES = ("additive", "pairwise", "sparse")
DOSES = (0, 2, 4, 6, 8)
MAP_REGIMES = ("support_only", "support_query")
BACKBONE_KS = (("xgb", 32), ("xgb", 512), ("histgb", 32))
PRIMARY_CELLS = (("xgb", 32), ("histgb", 32))
CONTRASTS = ("U_raw", "U_rank", "A_rank", "D_rank", "C_rank", "G")
EXPECTED_REALIZATIONS = 20
BOOTSTRAP_REPS = 10000
BOOTSTRAP_SEED = 20260903
WIN_THRESHOLD = 0.60


def boot(values: np.ndarray, seed_key: str) -> dict:
    seed = int(hashlib.sha256(
        f"mcr_rank|{BOOTSTRAP_SEED}|{seed_key}".encode()
    ).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    chosen = rng.integers(0, len(values), size=(BOOTSTRAP_REPS, len(values)))
    means = values[chosen].mean(axis=1)
    return {
        "mean": float(values.mean()),
        "ci95": [
            float(np.quantile(means, 0.025)),
            float(np.quantile(means, 0.975)),
        ],
        "win": float(np.mean(values > 0)),
        "n": int(len(values)),
    }


def q(record: dict) -> float:
    return -float(record["nmse"])


def contrast_curve(record: dict, backbone: str, support_k: int,
                   regime: str) -> dict[str, np.ndarray]:
    result = record["results"][str(support_k)][backbone]
    no_rank = result["no_rank"]
    ranked = result[regime]
    decode_none = q(no_rank["decode"])
    decode_rank = q(ranked["decode_rank"])
    values = {name: [] for name in CONTRASTS}
    for dose in DOSES:
        raw_none = q(no_rank[f"raw_d{dose}"])
        raw_rank = q(ranked[f"raw_rank_d{dose}"])
        u_raw = decode_none - raw_none
        u_rank = decode_rank - raw_rank
        a_rank = raw_rank - raw_none
        d_rank = decode_rank - decode_none
        values["U_raw"].append(u_raw)
        values["U_rank"].append(u_rank)
        values["A_rank"].append(a_rank)
        values["D_rank"].append(d_rank)
        values["C_rank"].append(u_raw - u_rank)
        values["G"].append(decode_none - raw_rank)
        if not np.isclose(u_raw - u_rank, a_rank - d_rank, atol=1e-12):
            raise AssertionError("2x2 closure identity failed")
    return {name: np.asarray(curve, dtype=np.float64)
            for name, curve in values.items()}


def summarize_curves(curves: dict[str, np.ndarray], seed_prefix: str) -> dict:
    out = {}
    for contrast, matrix in curves.items():
        out[contrast] = {
            "by_dose": [
                boot(matrix[:, index], f"{seed_prefix}|{contrast}|d{dose}")
                for index, dose in enumerate(DOSES)
            ]
        }
    rhos = []
    constant_count = 0
    for curve in curves["U_rank"]:
        if np.allclose(curve, curve[0], atol=1e-15, rtol=0):
            # A constant response has no dose ordering. SciPy leaves this
            # undefined; use zero for this descriptive dose-response score.
            rhos.append(0.0)
            constant_count += 1
        else:
            rhos.append(float(spearmanr(DOSES, curve).statistic))
    rhos = np.asarray(rhos, dtype=np.float64)
    out["U_rank"]["spearman_vs_dose"] = boot(
        rhos, f"{seed_prefix}|U_rank|spearman"
    )
    out["U_rank"]["spearman_constant_curve_count"] = constant_count
    full_absorbed = out["C_rank"]["by_dose"][-1]
    full_residual = out["U_rank"]["by_dose"][-1]
    out["full_dose_adjudication"] = {
        "absorbed_separated": bool(
            full_absorbed["mean"] > 0 and full_absorbed["ci95"][0] > 0
        ),
        "residual_utility_separated": bool(
            full_residual["mean"] > 0
            and full_residual["ci95"][0] > 0
            and full_residual["win"] >= WIN_THRESHOLD
        ),
    }
    return out


def fmt(value: float) -> str:
    return f"{value:+.4f}"


def stat_text(stat: dict) -> str:
    return (
        f"{fmt(stat['mean'])} "
        f"[{fmt(stat['ci95'][0])}, {fmt(stat['ci95'][1])}]"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()

    cells: dict[str, list[dict]] = {family: [] for family in FAMILIES}
    provenance = set()
    for family in FAMILIES:
        for path in sorted((args.root / family).glob("r*/metrics.json")):
            record = json.loads(path.read_text())
            if record.get("family") != family:
                raise RuntimeError(f"{path}: family mismatch")
            if tuple(record.get("doses", ())) != DOSES:
                raise RuntimeError(f"{path}: dose mismatch")
            if tuple(record.get("map_regimes", ())) != MAP_REGIMES:
                raise RuntimeError(f"{path}: map-regime mismatch")
            if not all(
                check["dose_zero_identical"]
                and check["source_missingness_preserved"]
                and check["target_missingness_preserved"]
                and check["target_map_shared_across_arms"]
                for support in record["construction_checks"].values()
                for backbone_checks in support.values()
                for check in backbone_checks.values()
            ):
                raise RuntimeError(f"{path}: failed construction check")
            cells[family].append(record)
            provenance.add((
                record["runner_sha256"], record["mcr_runner_sha256"],
                record["md_runner_sha256"], record["md_prereg_sha256"],
                record["input_sha256"], record["prereg_sha256"],
            ))
    if len(provenance) != 1:
        raise RuntimeError("missing or mixed provenance across rank-audit cells")
    complete = all(
        sorted(record["realization"] for record in cells[family])
        == list(range(EXPECTED_REALIZATIONS))
        for family in FAMILIES
    )
    if not complete:
        raise RuntimeError("rank-alignment evidence grid is incomplete")

    sections: dict[str, dict] = {}
    cell_rows = []
    full_rows = []
    for backbone, support_k in BACKBONE_KS:
        section_key = f"{backbone}_K{support_k}"
        sections[section_key] = {}
        for regime in MAP_REGIMES:
            regime_section = {}
            family_matrices = []
            for family in FAMILIES:
                curves_by_cell = [
                    contrast_curve(record, backbone, support_k, regime)
                    for record in cells[family]
                ]
                matrices = {
                    contrast: np.stack([
                        curve[contrast] for curve in curves_by_cell
                    ])
                    for contrast in CONTRASTS
                }
                family_matrices.append(matrices)
                summary = summarize_curves(
                    matrices, f"{section_key}|{regime}|{family}"
                )
                regime_section[family] = summary
                for record, curve in zip(cells[family], curves_by_cell):
                    for index, dose in enumerate(DOSES):
                        cell_rows.append({
                            "family": family,
                            "realization": record["realization"],
                            "backbone": backbone,
                            "support": support_k,
                            "map_regime": regime,
                            "dose": dose,
                            **{
                                contrast: float(curve[contrast][index])
                                for contrast in CONTRASTS
                            },
                        })
                full_rows.append({
                    "backbone": backbone,
                    "support": support_k,
                    "map_regime": regime,
                    "family": family,
                    **{
                        f"{contrast}_mean":
                            summary[contrast]["by_dose"][-1]["mean"]
                        for contrast in CONTRASTS
                    },
                    **{
                        f"{contrast}_ci_low":
                            summary[contrast]["by_dose"][-1]["ci95"][0]
                        for contrast in CONTRASTS
                    },
                    **{
                        f"{contrast}_ci_high":
                            summary[contrast]["by_dose"][-1]["ci95"][1]
                        for contrast in CONTRASTS
                    },
                    **summary["full_dose_adjudication"],
                })

            # Equal-family mean within realization, used only as a compact
            # cross-family summary; family-resolved results remain primary.
            pooled = {
                contrast: np.stack([
                    family[contrast] for family in family_matrices
                ]).mean(axis=0)
                for contrast in CONTRASTS
            }
            regime_section["equal_family_mean"] = summarize_curves(
                pooled, f"{section_key}|{regime}|equal_family_mean"
            )
            sections[section_key][regime] = regime_section

    primary = []
    for backbone, support_k in PRIMARY_CELLS:
        for family in FAMILIES:
            summary = sections[f"{backbone}_K{support_k}"]["support_only"][family]
            primary.append({
                "backbone": backbone,
                "support": support_k,
                "family": family,
                **summary["full_dose_adjudication"],
            })

    payload = {
        "analysis_status": "complete",
        "n_cells": sum(len(value) for value in cells.values()),
        "doses": list(DOSES),
        "map_regimes": list(MAP_REGIMES),
        "bootstrap": {
            "reps": BOOTSTRAP_REPS,
            "seed": BOOTSTRAP_SEED,
            "unit": "realization within family/learner/support/regime",
        },
        "contrasts": {
            "U_raw": "Q(decode_none)-Q(raw_none)",
            "U_rank": "Q(decode_rank)-Q(raw_rank)",
            "A_rank": "Q(raw_rank)-Q(raw_none)",
            "D_rank": "Q(decode_rank)-Q(decode_none)",
            "C_rank": "U_raw-U_rank=A_rank-D_rank",
            "G": "Q(decode_none)-Q(raw_rank); alternative-baseline gap",
        },
        "primary_support_only_full_dose": primary,
        "primary_counts": {
            "strata": len(primary),
            "absorbed_separated": sum(
                row["absorbed_separated"] for row in primary
            ),
            "residual_utility_separated": sum(
                row["residual_utility_separated"] for row in primary
            ),
        },
        "sections": sections,
        "validation": {
            "complete_cells": complete,
            "single_provenance_tuple": True,
            "all_construction_checks_pass": True,
            "all_2x2_closure_checks_pass": True,
            "provenance": list(next(iter(provenance))),
        },
    }
    summary_path = args.root / "SUMMARY_V1.json"
    summary_path.write_text(json.dumps(
        payload, indent=1, sort_keys=True, allow_nan=False
    ))

    with (args.root / "CELL_CONTRASTS_V1.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(cell_rows[0]))
        writer.writeheader()
        writer.writerows(cell_rows)
    with (args.root / "FULL_DOSE_V1.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(full_rows[0]))
        writer.writeheader()
        writer.writerows(full_rows)

    report = [
        "# Non-semantic rank-alignment audit — results v1",
        "",
        (
            "Primary support-only full-dose strata with a separated absorbed "
            f"gap: **{payload['primary_counts']['absorbed_separated']}/6**."
        ),
        (
            "Primary strata retaining separated utility conditional on rank "
            f"alignment: **{payload['primary_counts']['residual_utility_separated']}/6**."
        ),
        "",
        "## Primary support-only results at K=32 and d=8",
        "",
        "| Learner | Family | U_raw | U_rank | C_rank | A_rank | D_rank | G |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for backbone, support_k in PRIMARY_CELLS:
        section = sections[f"{backbone}_K{support_k}"]["support_only"]
        for family in FAMILIES:
            row = section[family]
            report.append(
                "| " + " | ".join([
                    backbone.upper(), family,
                    stat_text(row["U_raw"]["by_dose"][-1]),
                    stat_text(row["U_rank"]["by_dose"][-1]),
                    stat_text(row["C_rank"]["by_dose"][-1]),
                    stat_text(row["A_rank"]["by_dose"][-1]),
                    stat_text(row["D_rank"]["by_dose"][-1]),
                    stat_text(row["G"]["by_dose"][-1]),
                ]) + " |"
            )
    report.extend([
        "",
        "`G` is an alternative-baseline performance gap, not semantic utility.",
        "Family-resolved dose curves, transductive sensitivity, and XGBoost "
        "K=512 results are retained in `SUMMARY_V1.json` and the CSV files.",
        "",
    ])
    (args.root / "RESULTS_V1.md").write_text(
        "\n".join(report), encoding="utf-8"
    )
    print(json.dumps({
        "written": str(summary_path),
        "primary_counts": payload["primary_counts"],
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
