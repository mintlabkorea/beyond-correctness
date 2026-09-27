#!/usr/bin/env python3
"""Summarize the frozen TransTab shared-identity bridge decomposition."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "experiments/crta_v3_mcr_transtab_bridge_decomposition_v1"
PROTOCOL = ROOT / "iclr_latex_v3/MCR_TRANSTAB_BRIDGE_DECOMPOSITION_FREEZE_V1.md"
TABLE_OUT = ROOT / "iclr_latex_v3/generated/table_a12a_transtab_bridge.tex"
FAMILIES = ("additive", "pairwise", "sparse")
SUPPORTS = (32, 512)
N_REALIZATIONS = 20
N_BOOT = 10_000
CONTRASTS = {
    "name_token_content_beyond_shared_identity": ("correct", "shared_anonymous"),
    "shared_identity_bridge": ("shared_anonymous", "distinct_anonymous"),
    "false_bridge": ("c_wrong", "distinct_anonymous"),
    "conventional_content_gap": ("correct", "c_wrong"),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def stable_seed(*parts: Any) -> int:
    digest = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
    return int.from_bytes(digest[:8], "little") % (2**32 - 1)


def summarize(values: list[float], key: tuple[Any, ...]) -> dict[str, Any]:
    array = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(stable_seed("transtab_bridge_v1", *key))
    means = np.mean(array[rng.integers(0, len(array), size=(N_BOOT, len(array)))], axis=1)
    interval = np.quantile(means, [0.025, 0.975])
    return {
        "mean": float(np.mean(array)),
        "ci95": interval.tolist(),
        "win": float(np.mean(array > 0)),
        "n": len(values),
        "values": [float(value) for value in values],
    }


def compact(value: float) -> str:
    return f"{value:+.3f}".replace("+0.", "+.").replace("-0.", "-.")


def tex_record(record: dict[str, Any]) -> str:
    mean = compact(float(record["mean"]))
    lower, upper = (float(value) for value in record["ci95"])
    rendered = f"{mean} [{compact(lower)},{compact(upper)}]"
    if lower > 0 or upper < 0:
        return rf"\textbf{{{rendered}}}"
    return rendered


def render_table(results: dict[str, Any]) -> str:
    lines = [
        r"\begin{longtable}{ccP{0.105\linewidth}P{0.18\linewidth}P{0.18\linewidth}P{0.18\linewidth}P{0.18\linewidth}}",
        r"\caption{Post-result TransTab bridge decomposition under one four-arm runner. Name/token content is correct minus shared anonymous; shared bridge is shared minus distinct anonymous; false bridge is matched-wrong minus distinct anonymous, so a negative value denotes damage; conventional content is correct minus matched-wrong. Positive values favor the first named arm. Intervals resample the 20 realizations within each fixed family, and bold intervals exclude zero.}\label{tab:app-transtab-correspondence}\label{tab:app_transtab}\\",
        r"\toprule",
        r"$K$ & Family & Unit & Name/token content & Shared bridge & False bridge & Conventional content \\",
        r"\midrule\endfirsthead",
        r"\multicolumn{7}{c}{\tablename\ \thetable\ (continued)}\\",
        r"\toprule $K$ & Family & Unit & Name/token content & Shared bridge & False bridge & Conventional content \\",
        r"\midrule\endhead",
        r"\bottomrule\endfoot",
    ]
    contrast_order = (
        "name_token_content_beyond_shared_identity",
        "shared_identity_bridge",
        "false_bridge",
        "conventional_content_gap",
    )
    family_labels = {"additive": "Additive", "pairwise": "Pairwise", "sparse": "Sparse"}
    for support in SUPPORTS:
        for family in FAMILIES:
            cells = [
                tex_record(results[str(support)][contrast][family])
                for contrast in contrast_order
            ]
            lines.append(
                f"{support} & {family_labels[family]} & 20 realizations & "
                + " & ".join(cells)
                + r" \\"
            )
    lines.append(r"\end{longtable}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    cells: dict[tuple[str, int], dict[str, Any]] = {}
    protocol_hash = sha256_file(PROTOCOL)
    for family in FAMILIES:
        for realization in range(N_REALIZATIONS):
            path = args.root / family / f"r{realization:02d}" / "metrics.json"
            if not path.is_file():
                raise RuntimeError(f"missing {path}")
            cell = json.loads(path.read_text(encoding="utf-8"))
            if cell.get("protocol_sha256") != protocol_hash:
                raise RuntimeError(f"protocol mismatch: {path}")
            expected_arms = ["correct", "shared_anonymous", "distinct_anonymous", "c_wrong"]
            if cell.get("arms") != expected_arms:
                raise RuntimeError(f"arm mismatch: {path}")
            cells[(family, realization)] = cell

    results: dict[str, Any] = {}
    for support in SUPPORTS:
        results[str(support)] = {}
        for contrast, pair in CONTRASTS.items():
            results[str(support)][contrast] = {}
            for family in FAMILIES:
                values = []
                for realization in range(N_REALIZATIONS):
                    arms = cells[(family, realization)]["results"][str(support)]
                    # Q(first)-Q(second) = NMSE(second)-NMSE(first).
                    values.append(float(arms[pair[1]]["nmse"]) - float(arms[pair[0]]["nmse"]))
                results[str(support)][contrast][family] = summarize(
                    values, (support, contrast, family)
                )
        checks = {}
        for family in FAMILIES:
            content = results[str(support)]["conventional_content_gap"][family]["mean"]
            name = results[str(support)]["name_token_content_beyond_shared_identity"][family]["mean"]
            identity = results[str(support)]["shared_identity_bridge"][family]["mean"]
            false = results[str(support)]["false_bridge"][family]["mean"]
            # correct-wrong = (correct-shared)+(shared-distinct)-(wrong-distinct)
            checks[family] = {
                "content": content,
                "decomposed": name + identity - false,
                "absolute_residual": abs(content - (name + identity - false)),
            }
        results[str(support)]["decomposition_checks"] = checks

    payload = {
        "analysis_status": "post_result_review_triggered_mechanism_extension",
        "cells_complete": len(cells),
        "score": "Q=-MSE/Var(y_query); positive favors first arm",
        "bootstrap_reps": N_BOOT,
        "results": results,
        "provenance": {
            "protocol_sha256": protocol_hash,
            "summarizer_sha256": sha256_file(Path(__file__)),
            "runner_hashes": sorted(set(cell["runner_sha256"] for cell in cells.values())),
        },
    }
    out = args.root / "SUMMARY_V1.json"
    out.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    TABLE_OUT.parent.mkdir(parents=True, exist_ok=True)
    TABLE_OUT.write_text(render_table(results), encoding="utf-8")
    print(json.dumps({"status": "complete", "cells": len(cells),
                      "written": str(out), "table": str(TABLE_OUT)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
