# Artifact inventory

## Scope and immutability check

This reanalysis used retained scored predictions, metrics, rung tables, summaries, protocols, logs, and git metadata. It did not fit a new predictive model and did not edit the manuscript.

| Manuscript file | SHA-256 before analysis | SHA-256 after analysis | Status |
|---|---|---|---|
| `iclr_latex_v3/main.tex` | `643a263aabeab9dada80fccd1e3398d2457411e4766134aaa803a3a8a52e00ad` | same | untouched |
| `iclr_latex_v3/appendix.tex` | `d54f5fbedde4acf4a10a6318952284662f04bbf87c840d9d62decee27de52dc0` | same | untouched |

The two files already had user worktree modifications before this task; those changes were preserved.

## Inputs located

| Workstream | Original artifacts | Count / granularity | Parent statistical implementation |
|---|---|---:|---|
| A1 | `experiments/tabllm_retrospective_audit_v1/{list_template,list_permuted_names,list_only_values,list_stable_anonymous}/{dataset}/` | 4 arms × 9 datasets; 36 metric files and 36 paired prediction files | `scripts/summarize_tabllm_retrospective_audit_v1.py` |
| A1 | `experiments/tabllm_retrospective_split_manifest_v1.json` | 9 datasets × 5 fixed splits | same |
| A2 | `experiments/crta_v3_stage_endpoint_expansion_{nh2kn,kn2nh}_v1/*/seed_*/metrics.json` | 10 endpoints × 2 directions × 10 seeds = 200 | `scripts/summarize_crta_v3_stage_factorial_endpoint_expansion_v1.py` |
| A3 focused | `experiments/crta_v3_survey_label_panel_v1/*/seed_*/metrics.json` | 3 endpoints × 10 seeds = 30; pooled and endpoint arm outputs | `scripts/summarize_crta_v3_survey_label_panel_v1.py` |
| A3 extension | `experiments/crta_v3_survey_label_panel_endpoint_expansion_{nh2kn,kn2nh}_v1/*/seed_*/metrics.json` | 10 endpoints × 2 directions × 10 seeds = 200 | `scripts/summarize_crta_v3_survey_label_panel_endpoint_expansion_v1.py` |
| A4 | `experiments/crta_v3_reconstruction_utility_proxy_v1/CELL_RUNG_PROXY_V1.csv` | 912 realization-rung rows; 8 family×learner×K strata | `scripts/analyze_crta_v3_reconstruction_utility_proxy_v1.py` |
| A4 parent | `experiments/crta_v3_reconstruction_utility_proxy_v1/SUMMARY_V1.json` | stored LORO and regression summaries | same |
| A5 trees | `experiments/crta_v3_mcr_factorial_semisynth_v1/primary/*/r*/metrics.json` | 3 families × 20 realizations; both XGB and HistGB, K=32/512 | `scripts/summarize_crta_v3_mcr_factorial_semisynth_v1.py` |
| A5 MLP | `experiments/crta_v3_mcr_factorial_mlp_v1/*/r*/metrics.json` | 3 families × 20 realizations, K=32/512 | `scripts/summarize_crta_v3_mcr_factorial_mlp_v1.py` |
| A6 | measurement extension protocol, adjudicator, parent summary, git history, local logs and mtimes | 200-cell gate audit plus 8 provenance rows | `reanalysis_20260903/A6_provenance/audit_provenance.py` |

## Key manifest identifiers

| Manifest / protocol | SHA-256 |
|---|---|
| TabLLM retrospective freeze | `84ed4f92d8ff4e198bf036dd3378e7b9008cf501374115a4893d1e11abf780c0` |
| Stage endpoint expansion | `72f4ca51e319fd08b117ffd17f20bf619142b7b46515b9434f9872c964d5188f` |
| Focused survey-label panel | `35656164509b0ddc87158a1c03f6cfbd1ee992dab06e3f638a2e0d3a390b8efb` |
| Ten-endpoint survey-label extension | `98ce337f4668c03d0f1d8447c0e5519b77817885f9c90d372a7dff0a6828d418` |
| MCR redundancy ladder | `45d65f712bd1d6ee403a556b08ccdee31230b99a9322041bf34e8f56cb3af34a` |
| MCR tree factorial, run revision | `c4fb8a7ab8f02ba39ad30a3e6eca486c20a92093561cca9f10f96c885fbeb1f5` |
| MCR MLP factorial | `25387913d4fbc53d15360e7f54381e692e8756612833ab1a1971d96fcbb2fec4` |

Per-file hashes for all A1 scored predictions and metrics are in `A1_tabllm_reference/tabllm_reference_sensitivity_macro.json`. A6 commit IDs, local run-time evidence, and classifications are in `A6_provenance/provenance_timestamps.csv`.

## Missing artifact that blocks one requested analysis

The retained support ladder contains `Ranon` but no matching within-run `Rpub` predictions at the same support rungs. The two-reference support-ladder sensitivity cannot be computed without new fitting. It was not run.

## New outputs

Each A1–A6 directory contains its analysis script, machine-readable outputs, and a README. A4 additionally retains all 80,000 paired LORO-difference draws and all 80,000 conditional-slope draws.
