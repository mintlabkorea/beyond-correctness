#!/usr/bin/env python3
"""Audit the measurement coverage gate and retained pre-execution provenance."""

from __future__ import annotations

import csv
import glob
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def iso(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, timezone.utc).astimezone().isoformat()


def estimated_start(patterns: list[str]) -> tuple[str, str, int]:
    candidates = []
    for pattern in patterns:
        for name in glob.glob(str(REPO / pattern)):
            path = Path(name)
            if not path.is_file():
                continue
            elapsed = 0.0
            if path.name == "metrics.json":
                try:
                    elapsed = float(json.loads(path.read_text()).get("wall_seconds", 0.0))
                except (ValueError, TypeError, json.JSONDecodeError):
                    elapsed = 0.0
            candidates.append((path.stat().st_mtime - elapsed, path, elapsed))
    if not candidates:
        return "", "no matching retained artifact", 0
    timestamp, path, elapsed = min(candidates, key=lambda x: x[0])
    note = (f"estimated from local mtime({path.relative_to(REPO)})"
            + (f" - wall_seconds({elapsed:g})" if elapsed else ""))
    return iso(timestamp), note, len(candidates)


def git_record(commit: str, path: str, expected_hash: str) -> dict:
    meta = subprocess.run(
        ["git", "show", "-s", "--format=%H%x09%cI%x09%s", commit],
        cwd=REPO, check=True, text=True, capture_output=True,
    ).stdout.strip().split("\t", 2)
    content = subprocess.run(
        ["git", "show", f"{commit}:{path}"], cwd=REPO,
        check=True, capture_output=True,
    ).stdout
    actual = sha256_bytes(content)
    if actual != expected_hash:
        raise AssertionError(f"git content hash mismatch for {commit}:{path}: {actual}")
    branches = subprocess.run(
        ["git", "branch", "-a", "--contains", commit], cwd=REPO,
        check=True, text=True, capture_output=True,
    ).stdout.strip().replace("\n", "; ")
    return {"commit": meta[0], "commit_time": meta[1], "subject": meta[2],
            "containing_refs": branches}


def audit_coverage() -> dict:
    roots = {
        "nh2kn": REPO / "experiments/crta_v3_survey_label_panel_endpoint_expansion_nh2kn_v1",
        "kn2nh": REPO / "experiments/crta_v3_survey_label_panel_endpoint_expansion_kn2nh_v1",
    }
    coverage = {}
    cell_count = 0
    for direction, root in roots.items():
        for path in sorted(root.glob("*/seed_*/metrics.json")):
            d = json.loads(path.read_text()); cell_count += 1
            arms = d["auroc"]["256"]
            finite = all(
                isinstance(arms[name], (int, float)) and arms[name] == arms[name]
                for name in ("pipeline_table", "placebo_table")
            )
            coverage.setdefault(d["target"], {}).setdefault(direction, 0)
            coverage[d["target"]][direction] += int(finite)
    if cell_count != 200:
        raise AssertionError(f"expected 200 cells, found {cell_count}")
    failed = [{"endpoint": target, "direction": direction, "finite_pairs": n}
              for target, by_direction in sorted(coverage.items())
              for direction, n in sorted(by_direction.items()) if n < 8]
    parent = json.loads((REPO / "experiments/crta_v3_survey_label_panel_endpoint_expansion_v1/SUMMARY_V1.json").read_text())
    if coverage != parent["construction"]["coverage_by_endpoint_direction"]:
        raise AssertionError("coverage recomputation does not match frozen summary")
    return {
        "exact_grid_rule": "exactly 10 endpoints x 2 directions x 10 seeds = 200 cells",
        "exact_coverage_rule": (
            "For every endpoint-direction unit, count finite paired pipeline_table/placebo_table "
            "K=256 seeds; require count >= 8 of 10. If any unit fails, the primary panel "
            "verdict is not evaluable."
        ),
        "formula": "coverage(e,d)=sum_s I[finite(AUC_pipeline(e,d,s)-AUC_placebo(e,d,s))] >= 8",
        "cell_count": cell_count, "coverage_by_endpoint_direction": coverage,
        "failed_units": failed, "coverage_gate_pass": not failed,
        "protocol_path": "iclr_latex_v3/SURVEY_LABEL_PANEL_ENDPOINT_EXPANSION_PREREGISTRATION_V1.md",
        "protocol_lines": "49-54 (gate), 62-69 (estimand/inference), 71-76 (P1)",
        "adjudicator_path": "scripts/summarize_crta_v3_survey_label_panel_endpoint_expansion_v1.py",
        "adjudicator_lines": "15-22 (constants), 140-160 (finite count/gate), 161-168 (decision)",
    }


def main() -> int:
    definitions = [
        {
            "analysis": "A1 TabLLM four-arm retrospective audit",
            "manifest_path": "iclr_latex_v3/TABLLM_RETROSPECTIVE_AUDIT_FREEZE_V1.md",
            "manifest_sha256": "84ed4f92d8ff4e198bf036dd3378e7b9008cf501374115a4893d1e11abf780c0",
            "commit": "", "patterns": ["experiments/tabllm_retrospective_audit_v1/*/*/metrics.json"],
            "hash_link": "metrics.json protocol_sha256 matches; protocol file is currently untracked",
            "classification": "C",
            "reason": "hash-linked at execution, but no independent external timestamp retained",
        },
        {
            "analysis": "A2 10-endpoint stage-factorial interaction",
            "manifest_path": "iclr_latex_v3/STAGE_ENDPOINT_EXPANSION_PREREGISTRATION_V1.md",
            "manifest_sha256": "72f4ca51e319fd08b117ffd17f20bf619142b7b46515b9434f9872c964d5188f",
            "commit": "2436f0a017e99c63fa14c725800acd39439b80f8", "patterns": [
                "experiments/crta_v3_stage_endpoint_expansion_nh2kn_v1/*/seed_*/metrics.json",
                "experiments/crta_v3_stage_endpoint_expansion_kn2nh_v1/*/seed_*/metrics.json"],
            "hash_link": "no manifest hash embedded in per-cell metrics",
            "classification": "B",
            "reason": "committed plan exists, but pre-run ordering depends on local output mtimes; push time unavailable",
        },
        {
            "analysis": "A3 focused 3-endpoint measurement panel",
            "manifest_path": "iclr_latex_v3/M1M2_SURVEY_LABEL_MEASUREMENT_PANEL_PREREGISTRATION_V1.md",
            "manifest_sha256": "35656164509b0ddc87158a1c03f6cfbd1ee992dab06e3f638a2e0d3a390b8efb",
            "commit": "2bfa08396fb4923ac4ee0a1cf64d2b7460f78220", "patterns": [
                "experiments/crta_v3_survey_label_panel_v1/*/seed_*/metrics.json"],
            "hash_link": "no manifest hash embedded in per-cell metrics; local runner logs retained",
            "classification": "B",
            "reason": "committed plan exists, but pre-run ordering depends on local logs/mtimes; push time unavailable",
        },
        {
            "analysis": "A3/A6 10-endpoint bidirectional measurement extension",
            "manifest_path": "iclr_latex_v3/SURVEY_LABEL_PANEL_ENDPOINT_EXPANSION_PREREGISTRATION_V1.md",
            "manifest_sha256": "98ce337f4668c03d0f1d8447c0e5519b77817885f9c90d372a7dff0a6828d418",
            "commit": "12efa88d189bf562de2ddd14665b1c13722cde9f", "patterns": [
                "experiments/crta_v3_survey_label_panel_endpoint_expansion_nh2kn_v1/*/seed_*/metrics.json",
                "experiments/crta_v3_survey_label_panel_endpoint_expansion_kn2nh_v1/*/seed_*/metrics.json"],
            "hash_link": "wrapper can print prereg hash, but per-cell metrics do not embed it",
            "classification": "B",
            "reason": "commit is retained, but run ordering rests on local mtimes and no push/scheduler timestamp was found",
        },
        {
            "analysis": "A4 reconstruction proxy (post-result exploratory analysis)",
            "manifest_path": "scripts/analyze_crta_v3_reconstruction_utility_proxy_v1.py",
            "manifest_sha256": "", "commit": "", "patterns": [
                "experiments/crta_v3_reconstruction_utility_proxy_v1/SUMMARY_V1.json"],
            "hash_link": "summary embeds analysis_runner_sha256; no pre-execution decision manifest",
            "classification": "C",
            "reason": "script version is hash-linked, but timing is local and the analysis is explicitly post-result/exploratory",
        },
        {
            "analysis": "A4 underlying MCR redundancy ladder",
            "manifest_path": "experiments/crta_v3_mcr_redundancy_ladder_v1/PROTOCOL_V1.md",
            "manifest_sha256": "45d65f712bd1d6ee403a556b08ccdee31230b99a9322041bf34e8f56cb3af34a",
            "commit": "dc61ce762f8eca5af036c72056929b3a764d918f", "patterns": [
                "experiments/crta_v3_mcr_redundancy_ladder_v1/*/r*/metrics.json"],
            "hash_link": "per-cell metrics and local shard logs embed exact protocol_sha256",
            "classification": "C",
            "reason": "strong hash linkage, but no independently timestamped run-start record was found",
        },
        {
            "analysis": "A5 tree controlled factorial",
            "manifest_path": "iclr_latex_v3/MCR_FACTORIAL_SEMISYNTHETIC_PREREGISTRATION_V1.md@run-revision",
            "manifest_sha256": "c4fb8a7ab8f02ba39ad30a3e6eca486c20a92093561cca9f10f96c885fbeb1f5",
            "commit": "0013dbbda121622bf1ee4e5a18294d5d27682c24", "patterns": [
                "experiments/crta_v3_mcr_factorial_semisynth_v1/primary/*/r*/metrics.json"],
            "hash_link": "per-cell metrics embed prereg_sha256 for the historical run revision",
            "classification": "C",
            "reason": "hash-linked and committed, but run start is supported only by local artifact time",
        },
        {
            "analysis": "A5 MLP controlled factorial",
            "manifest_path": "iclr_latex_v3/MCR_MLP_PREREGISTRATION_V1.md",
            "manifest_sha256": "25387913d4fbc53d15360e7f54381e692e8756612833ab1a1971d96fcbb2fec4",
            "commit": "6dae2cc33a76fcb29649d9fda1c6e76fb0343004", "patterns": [
                "experiments/crta_v3_mcr_factorial_mlp_v1/*/r*/metrics.json"],
            "hash_link": "per-cell metrics and local logs embed exact prereg_sha256",
            "classification": "C",
            "reason": "hash-linked and committed, but no independent scheduler/push/run timestamp was found",
        },
    ]

    rows = []
    for item in definitions:
        manifest_path = item["manifest_path"].split("@", 1)[0]
        path = REPO / manifest_path
        if item["manifest_sha256"] and item["commit"]:
            git = git_record(item["commit"], manifest_path, item["manifest_sha256"])
        else:
            git = {"commit": "", "commit_time": "", "subject": "", "containing_refs": ""}
        if not item["manifest_sha256"] and path.is_file():
            item["manifest_sha256"] = sha256(path)
        start, start_basis, n = estimated_start(item["patterns"])
        rows.append({
            "analysis": item["analysis"], "manifest_or_code": item["manifest_path"],
            "manifest_sha256": item["manifest_sha256"], "git_commit": git["commit"],
            "git_commit_time": git["commit_time"], "run_start_or_first_output": start,
            "run_time_basis": start_basis, "n_run_artifacts": n,
            "available_timestamp_evidence": (
                f"commit refs={git['containing_refs'] or 'none'}; {item['hash_link']}; "
                "run timing from local filesystem/log metadata only"
            ),
            "classification": item["classification"], "classification_reason": item["reason"],
        })

    coverage = audit_coverage()
    (HERE / "coverage.json").write_text(json.dumps(coverage, indent=2, sort_keys=True) + "\n")
    with (HERE / "provenance_timestamps.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
    (HERE / "provenance_timestamps.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(json.dumps({"coverage_gate_pass": coverage["coverage_gate_pass"],
                      "failed_units": coverage["failed_units"],
                      "classification_counts": {x: sum(r["classification"] == x for r in rows)
                                                for x in "ABCD"}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
