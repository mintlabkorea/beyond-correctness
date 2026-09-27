# Supported published claims: study summary v1

Frozen design codes are unchanged. Reported outcomes were not extracted or used in assigning the design codes. This phase joins the codes to published outcomes; it is not outcome-blind review or meta-analysis.

Counts below describe extracted records, not independent experiments. Figure panels are one record per displayed regime. Numeric aggregates, pairwise summaries, author prose, ambiguous matches, N/A cells and duplicates remain distinct.

| Study | Published utility-reference status | What is observed and identifiable |
|---|---|---|
| LIFT | No for all comparisons | C01-A/B: mixed directions across both LM variants and tasks; content identification remains Partial. C01-C/D: each has 3 favorable and 1 adverse matched classification outcomes, but utility is No. Supplementary shared-unnamed outcomes are retained as ambiguous and cannot establish format-specific claims. |
| TabLLM | No for all comparisons | C03-A identifies content sensitivity, with both favorable and adverse point estimates (including healthcare). C03-B values-only is non-admissible: its gains cannot be labelled feature-name utility. C03-C has favorable/equal recorded estimates but only Partial content identification and No utility identification. Missing full-data/healthcare cells remain visible. |
| PLATO | Unclear only (no Yes) | All three frozen BRCA comparisons favor the full KG by PearsonR point estimates. C04-A utility remains Partial; C04-B/C utility is No. SD does not supply a pairwise significance test. |
| CARTE | Unclear only (no Yes) | C05-A/B/C: both regression and classification panels retained; exact values unavailable. Authors describe losses from component ablation, but isolated utility is No/Partial/No respectively. Broad caption wording does not establish a statistical test at every train size. |
| FeatLLM | Unclear only (no Yes) | C06-A: 42 favorable and 23 adverse per-dataset/shot estimates; aggregate -Description changes favor intended at all five shots. Utility remains Partial for the full description block; no feature-name-only conclusion. |
| TabuLa-8B | at least one Yes | C07-A is admissible for JOINT feature-and-target-header content. Both subset panels are retained without digitization. Authors report a 3–5 percentage-point gain in the 16-shot subset and effectively identical performance at 32 shots. This supports regime-dependent qualitative utility, not a uniform benefit or feature-only effect. |
| ConTextTab | at least one Yes | C08-A/B/C/D aggregate ranks, accuracy/R2 deltas and win ratios favor semantic encoding, but utility is No. C08-E is admissible: removal loses 1.2 accuracy and 2.1 R2 percentage points; base wins 0.92 vs 0.08, with Wilcoxon p printed 0.00 (rounded). C08-F remains Partial: better rank and 0.57 win ratio, but accuracy/R2 changes round to 0.0 and p=0.40. |
| TabSTAR | at least one Yes | Both comparisons are admissible for their narrower verbalization scopes. C09-A (quantile text conditional on name+bin): 9 favorable / 10 adverse / 1 equal. C09-B (bin/quantile content conditional on numerical branch): 14 favorable / 3 adverse / 3 equal. Aggregate normalized scores favor full in both tasks; per-dataset utility is mixed, not uniformly positive. |
| TARTE | Unclear only (no Yes) | C10-A/B: published Figure 6 compares Ridge embeddings over sizes 32–1024. Exact ranks/directions cannot be recovered from accessible official text; no numeric direction assigned. Utility remains Partial/No. The preacceptance mirror is not a published numeric source. |

## Every frozen comparison

| ID | Content / utility identifiable | Primary direction counts | Separate aggregate counts | Retained ambiguous rows |
|---|---|---|---|---|
| C01-A | Partial / No | mixed: {"favorable": 7, "adverse": 7, "equal_at_printed_precision": 3} | {} | 0 |
| C01-B | Partial / No | mixed: {"adverse": 7, "favorable": 10} | {} | 0 |
| C01-C | No / No | mixed: {"adverse": 1, "favorable": 3} | {} | 14 |
| C01-D | No / No | mixed: {"adverse": 1, "favorable": 3} | {} | 14 |
| C03-A | Yes / No | mixed; unavailable directions also retained: {"adverse": 16, "favorable": 77, "unavailable": 10, "equal_at_printed_precision": 11} | {} | 0 |
| C03-B | No / No | mixed; unavailable directions also retained: {"favorable": 67, "adverse": 10, "unavailable": 6, "equal_at_printed_precision": 7} | {} | 0 |
| C03-C | Partial / No | favorable-or-equal; unavailable directions also retained: {"favorable": 78, "unavailable": 6, "equal_at_printed_precision": 6} | {} | 0 |
| C04-A | No / Partial | all favorable: {"favorable": 1} | {} | 0 |
| C04-B | No / No | all favorable: {"favorable": 1} | {} | 0 |
| C04-C | No / No | all favorable: {"favorable": 1} | {} | 0 |
| C05-A | No / No | direction unavailable: {"unavailable": 2} | {} | 0 |
| C05-B | No / Partial | direction unavailable: {"unavailable": 2} | {} | 0 |
| C05-C | No / No | direction unavailable: {"unavailable": 2} | {} | 0 |
| C06-A | No / Partial | mixed: {"favorable": 42, "adverse": 23} | {} | 0 |
| C07-A | No / Yes | direction unavailable: {"unavailable": 2} | {} | 0 |
| C08-A | No / No | direction unavailable: {} | {"favorable": 4} | 0 |
| C08-B | No / No | direction unavailable: {} | {"favorable": 4} | 0 |
| C08-C | No / No | direction unavailable: {} | {"favorable": 4} | 0 |
| C08-D | No / No | direction unavailable: {} | {"favorable": 4} | 0 |
| C08-E | No / Yes | direction unavailable: {} | {"favorable": 4} | 0 |
| C08-F | No / Partial | direction unavailable: {} | {"favorable": 2, "equal_at_printed_precision": 2} | 0 |
| C09-A | No / Yes | mixed: {"adverse": 10, "favorable": 9, "equal_at_printed_precision": 1} | {} | 1 |
| C09-B | No / Yes | mixed: {"equal_at_printed_precision": 3, "adverse": 3, "favorable": 14} | {} | 1 |
| C10-A | No / Partial | direction unavailable: {"unavailable": 1} | {} | 0 |
| C10-B | No / No | direction unavailable: {"unavailable": 1} | {} | 0 |

## Scope and handoff

At least one admissible published utility reference occurs in 3/9 studies (TabuLa-8B, ConTextTab, TabSTAR). Four studies have unresolved references but no Yes, and two have only No. The 4/25 admissible comparisons are descriptive, correlated comparison counts, not four independent experiments. Outcomes do not alter these design-level counts.

**TabLLM manuscript correction for the later integration phase:** published List Template vs List Permuted Names is the clean intended–wrong comparison. Published List Only Values fails Preservation and is not the utility reference. Our subsequently constructed stable-anonymous reference belongs to the separate quantitative deep dive and is not among the published outcomes here. No manuscript files were edited in this phase.

**Extraction limitations:** LIFT Table 35 does not label its metric explicitly; RAE identification is contextual (Table 20 and the regression protocol), and lower-is-better ordering is retained with that note. Shared unnamed supplementary arms are ambiguous. TabSTAR Figure 8 uses different labels from its tabulated variants and is retained as an ambiguous aggregate presentation. TARTE official indexed text is available but the published PDF download remains restricted; exact rank/significance cannot be supplied. None of these limitations changes the frozen design codes.

Artifacts: [raw long-format outcomes](REPORTED_OUTCOMES_V1.csv), [row-level supported claims](SUPPORTED_CLAIMS_V1.csv), [comparison summaries](COMPARISON_SUMMARY_V1.csv), [study summaries](STUDY_SUMMARY_V1.csv), [source inventory](SOURCE_COVERAGE_V1.md).
