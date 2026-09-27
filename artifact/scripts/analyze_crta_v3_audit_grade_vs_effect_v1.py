#!/usr/bin/env python3
"""N5: join the external-evidence audit (Table A7) to the unit-resolved
effect table (Table A3), and test whether audit grade predicts effect size.

The two tables are already in the paper but sit in parallel: A7 grades the
external evidence behind each declared relation, A3 reports the measured
per-endpoint content and utility effects, and no row of either references
the other.  This script builds the join and adjudicates it.

Nothing here is hand-transcribed.  Audit grades are PARSED from the frozen
appendix table; the endpoint -> relation map is DERIVED from the two
runners' frozen `DOCUMENTED_SIGNS` tables; effects are read from the same
SUMMARY JSONs that generate Table A3.  A drift in any of those three
sources makes this script fail rather than silently report stale numbers.

Status: POST-HOC on frozen data.  The grade ordering below is stated
before any correlation is computed, and because any such ordering is
arguable the script also reports the BEST and WORST Kendall tau attainable
over all orderings of the medical grades -- so the verdict does not depend
on the ordering chosen.

Metric note: both medical settings report `query_sd_normalized_rmse`, so
their magnitudes are comparable.  CAMELS reports log1p RMSE and is
therefore analysed separately, using the GC-REL per-relation ablation.
"""

from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
APPENDIX = ROOT / "iclr_latex_v3/appendix_results.tex"
AUDIT_LABEL = r"\label{tab:app_relation_evidence}"

NHKN_RUNNER = ROOT / "scripts/run_crta_v3_pam_constraint_relations_v1.py"
HRS_RUNNER = ROOT / "scripts/run_crta_v3_m3_sign_probe_v1.py"

SETTINGS = {
    "NHANES-KNHANES": {
        "summary": ROOT / "experiments/crta_v3_pam_constraint_relations_v1/SUMMARY_V1.json",
        "content": ("V_SIGN_CONTENT_flip_must_hurt", "per_target_mean"),
        "utility": ("declared_sign_vs_free_tax_expected", "per_target_mean"),
        "runner": NHKN_RUNNER,
    },
    "NHANES/KNHANES-HRS": {
        "summary": ROOT / "experiments/crta_v3_m3_sign_probe_v1/SUMMARY_V1.json",
        "content": ("GS_P1_identification_flipped", "per_endpoint_mean"),
        "utility": ("GS_P3_utility_vs_free", "per_endpoint_mean"),
        "runner": HRS_RUNNER,
    },
}

# Relation identity as the set of variable tokens the constraint links.
# Keys are the audit table's relation strings after TeX stripping.
RELATION_VARIABLES: dict[str, frozenset[str]] = {
    "Age -> SBP": frozenset({"age", "sbp"}),
    "SBP <-> DBP": frozenset({"sbp", "dbp"}),
    "Fasting glucose <-> HbA1c": frozenset({"glucose", "hba1c"}),
    "Total cholesterol <-> triglycerides": frozenset({"total_cholesterol",
                                                      "triglycerides"}),
    "Weight -> waist circumference": frozenset({"weight_kg", "waist_cm"}),
    "BUN <-> creatinine": frozenset({"bun", "creatinine"}),
    "Hemoglobin <-> hematocrit/RBC": frozenset({"hemoglobin", "hematocrit",
                                                "rbc"}),
}
CAMELS_RELATIONS = ("Precipitation -> discharge", "PET -> discharge")

# Ordinal strength of external evidence, weakest (1) to strongest (5), so a
# POSITIVE correlation with effect size means "audit grade predicts effect".
# Stated before any correlation is computed; the justification is the audit
# table's own limitation text, quoted in the emitted JSON.
GRADE_RANK: dict[str, int] = {
    "Mixed": 1,                   # counterevidence reported
    "Conditional": 2,             # holds only under stated conditions
    "Constructive, indirect": 3,  # definitional co-occurrence, not a population relation
    "Indirect": 4,                # evidence is on a proxy or related variable
    "Direct, qualified": 5,       # evidence is on the exact variables
}
ALIGNED_SIGN = ("positive tau = audit grade predicts effect size "
                "(stronger external evidence -> larger measured effect)")
PERMUTATION_SEED = 20260827


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def strip_tex(text: str) -> str:
    text = re.sub(r"\\citep\{[^}]*\}", "", text)
    text = (text.replace(r"\(\rightarrow\)", "->")
                .replace(r"\(\leftrightarrow\)", "<->")
                .replace(r"\(+\)", "+").replace(r"\(-\)", "-"))
    text = re.sub(r"\\[a-zA-Z]+", "", text)
    return " ".join(text.split())


def parse_audit_table(path: Path) -> list[dict]:
    """Parse (relation, prior, limitation, audit status) from the frozen table."""
    source = path.read_text(encoding="utf-8")
    start = source.index(AUDIT_LABEL)
    body = source[source.index(r"\midrule", start) + len(r"\midrule"):
                  source.index(r"\bottomrule", start)]
    rows = []
    for chunk in body.split(r"\\"):
        fields = [strip_tex(f) for f in chunk.split("&")]
        if len(fields) != 5 or not fields[0]:
            continue
        rows.append({"relation": fields[0], "prior": fields[1],
                     "limitation": fields[3], "audit_status": fields[4]})
    return rows


def endpoint_relations(runner: Path, module_name: str,
                       audit: dict[str, str]) -> dict[str, list[str]]:
    """Map each endpoint to the audit relations its constraints instantiate.

    Derived from the runner's frozen DOCUMENTED_SIGNS, so an endpoint whose
    declared parent is not covered by the audit raises instead of passing
    silently.
    """
    signs = _load(module_name, runner).DOCUMENTED_SIGNS
    out: dict[str, list[str]] = {}
    for endpoint, parents in signs.items():
        found = []
        for parent in parents:
            pair = {endpoint, parent}
            matches = [name for name, variables in RELATION_VARIABLES.items()
                       if pair <= variables]
            if not matches:
                raise SystemExit(
                    f"{runner.name}: constraint {endpoint}<-{parent} matches no "
                    "audited relation; the audit table and the runner disagree")
            found.extend(matches)
        out[endpoint] = sorted(set(found))
    return out


def kendall_tau_b(x: np.ndarray, y: np.ndarray) -> float:
    n = len(x)
    concordant = discordant = tie_x = tie_y = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx, dy = x[i] - x[j], y[i] - y[j]
            if dx == 0 and dy == 0:
                continue
            if dx == 0:
                tie_x += 1
            elif dy == 0:
                tie_y += 1
            elif (dx > 0) == (dy > 0):
                concordant += 1
            else:
                discordant += 1
        # loop body intentionally O(n^2): n <= 13 here
    denominator = np.sqrt((concordant + discordant + tie_x)
                          * (concordant + discordant + tie_y))
    return float((concordant - discordant) / denominator) if denominator else float("nan")


def exact_permutation_p(ranks: np.ndarray, values: np.ndarray) -> tuple[float, int]:
    """Two-sided exact p over all permutations of the grade ranks."""
    observed = abs(kendall_tau_b(ranks, values))
    perms = list(itertools.permutations(range(len(ranks))))
    extreme = sum(1 for p in perms
                  if abs(kendall_tau_b(ranks[list(p)], values)) >= observed - 1e-12)
    return extreme / len(perms), len(perms)


def ordering_envelope(grades: list[str], values: np.ndarray) -> dict:
    """Best and worst Kendall tau over EVERY ordering of the distinct grades.

    If even the best-case ordering is weak, no choice of grade scale rescues
    the hypothesis that audit grade predicts effect size.
    """
    distinct = sorted(set(grades))
    best, worst, best_order, worst_order = -2.0, 2.0, None, None
    for order in itertools.permutations(range(1, len(distinct) + 1)):
        mapping = dict(zip(distinct, order))
        tau = kendall_tau_b(np.array([mapping[g] for g in grades], float), values)
        if tau > best:
            best, best_order = tau, dict(mapping)
        if tau < worst:
            worst, worst_order = tau, dict(mapping)
    n_orderings = 1
    for k in range(2, len(distinct) + 1):
        n_orderings *= k
    return {"n_distinct_grades": len(distinct), "n_orderings_tried": n_orderings,
            "best_tau": best, "best_ordering": best_order,
            "worst_tau": worst, "worst_ordering": worst_order}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gc-rel-summary", type=Path, default=ROOT /
                        "experiments/crta_v3_camels_sign_relation_ablation_v1"
                        "/SUMMARY_GC_REL.json")
    parser.add_argument("--out", type=Path, default=ROOT /
                        "experiments/crta_v3_audit_grade_vs_effect_v1")
    args = parser.parse_args()

    audit_rows = parse_audit_table(APPENDIX)
    audit = {row["relation"]: row["audit_status"] for row in audit_rows}
    if not set(RELATION_VARIABLES) | set(CAMELS_RELATIONS) <= set(audit):
        raise SystemExit(
            "audit table drifted; unmatched: "
            f"{sorted((set(RELATION_VARIABLES) | set(CAMELS_RELATIONS)) - set(audit))}")
    for relation in RELATION_VARIABLES:
        if audit[relation] not in GRADE_RANK:
            raise SystemExit(f"unranked audit status {audit[relation]!r}")

    units: list[dict] = []
    for setting, config in SETTINGS.items():
        summary = json.loads(Path(config["summary"]).read_text(encoding="utf-8"))
        mapping = endpoint_relations(
            config["runner"], f"n5_signs_{setting.replace('/', '_')}", audit)
        content_block, content_key = config["content"]
        utility_block, utility_key = config["utility"]
        content = summary[content_block][content_key]
        utility = summary[utility_block][utility_key]
        for endpoint in sorted(content):
            relations = mapping[endpoint]
            grades = sorted({audit[r] for r in relations})
            units.append({
                "setting": setting, "endpoint": endpoint,
                "relations": relations, "audit_status": grades,
                "grade_rank": min(GRADE_RANK[g] for g in grades),
                "grade_ambiguous": len(grades) > 1,
                "content": float(content[endpoint]),
                "utility": float(utility[endpoint]),
            })

    ranks = np.array([u["grade_rank"] for u in units], float)
    grades_flat = [u["audit_status"][0] if len(u["audit_status"]) == 1
                   else "/".join(u["audit_status"]) for u in units]
    endpoint_level = {}
    for column in ("content", "utility"):
        values = np.array([u[column] for u in units], float)
        endpoint_level[column] = {
            "kendall_tau_b": kendall_tau_b(ranks, values),
            "ordering_envelope": ordering_envelope(grades_flat, values),
        }

    # Relation level: each relation contributes the mean effect of the
    # endpoints it constrains, which respects the shared-relation dependence
    # between e.g. hematocrit and rbc.
    relation_level = {}
    per_relation: dict[str, dict[str, list[float]]] = {}
    for unit in units:
        for relation in unit["relations"]:
            bucket = per_relation.setdefault(relation, {"content": [], "utility": [],
                                                        "endpoints": []})
            bucket["content"].append(unit["content"])
            bucket["utility"].append(unit["utility"])
            bucket["endpoints"].append(f"{unit['setting']}:{unit['endpoint']}")
    relation_names = sorted(per_relation)
    relation_ranks = np.array([GRADE_RANK[audit[r]] for r in relation_names], float)
    relation_grades = [audit[r] for r in relation_names]
    for column in ("content", "utility"):
        values = np.array([float(np.mean(per_relation[r][column]))
                           for r in relation_names])
        p_value, n_perm = exact_permutation_p(relation_ranks, values)
        envelope = ordering_envelope(relation_grades, values)
        best_ranks = np.array([envelope["best_ordering"][g]
                               for g in relation_grades], float)
        envelope["best_exact_permutation_p_two_sided"] = exact_permutation_p(
            best_ranks, values)[0]
        envelope["best_p_is_invalid_because_selected"] = True
        relation_level[column] = {
            "kendall_tau_b": kendall_tau_b(relation_ranks, values),
            "exact_permutation_p_two_sided": p_value,
            "n_permutations": n_perm,
            "ordering_envelope": envelope,
            "per_relation_mean": dict(zip(relation_names, values.tolist())),
        }

    camels = None
    if args.gc_rel_summary.is_file():
        gc = json.loads(args.gc_rel_summary.read_text(encoding="utf-8"))
        camels = {
            "note": "log1p RMSE; not comparable to the medical settings' "
                    "sd-normalized RMSE, so reported separately",
            "relations": {
                "Precipitation -> discharge": {
                    "audit_status": audit.get("Precipitation -> discharge"),
                    "single_flip_mean_gain": gc["single_flip"]["flip_precip_only"]
                                               ["log1p_rmse"]["mean_gain"],
                    "direction": gc["single_flip"]["flip_precip_only"]
                                   ["log1p_rmse"]["direction"],
                    "share_of_both_flip": gc["share_of_both_flip_effect_log1p_rmse"]
                                            ["flip_precip_only"]},
                "PET -> discharge": {
                    "audit_status": audit.get("PET -> discharge"),
                    "single_flip_mean_gain": gc["single_flip"]["flip_pet_only"]
                                               ["log1p_rmse"]["mean_gain"],
                    "direction": gc["single_flip"]["flip_pet_only"]
                                   ["log1p_rmse"]["direction"],
                    "share_of_both_flip": gc["share_of_both_flip_effect_log1p_rmse"]
                                            ["flip_pet_only"]},
            },
        }

    report = {
        "analysis": "N5_audit_grade_vs_effect_size",
        "status": "post-hoc on frozen data; grade ordering fixed before "
                  "computing, and reported against its full ordering envelope",
        "metric": "query_sd_normalized_rmse for both medical settings "
                  "(comparable); CAMELS log1p RMSE reported separately",
        "grade_rank_scale": GRADE_RANK,
        "sign_convention": ALIGNED_SIGN,
        "audit_table_rows": audit_rows,
        "units": units,
        "endpoint_level": endpoint_level,
        "relation_level": relation_level,
        "camels_per_relation": camels,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "SUMMARY_N5.json").write_text(
        json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items()
                      if k not in ("audit_table_rows",)},
                     indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
