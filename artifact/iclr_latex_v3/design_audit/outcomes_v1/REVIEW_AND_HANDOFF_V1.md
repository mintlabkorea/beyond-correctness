# Outcome extraction and supported-claim review v1

Completed: 2026-09-08. Single-auditor documentary extraction and review, not independent double extraction. This is a completed extraction of the inventoried published comparisons with explicit unavailable/ambiguous records, not a claim of complete numerical access to every source.

## Sequence and integrity

1. `../OUTCOME_EXTRACTION_RULE_V1.md` and its SHA-256 sidecar were written before extraction in this phase.
2. Source locations were inventoried by frozen arm construction.
3. Published tables, supplementary tables, figure panels and associated prose were extracted; outcomes were written before the claim join.
4. The outcome rows were joined by Comparison ID to the immutable Phase C codes. Supported claims and deterministic comparison/study summaries were then generated.
5. Parent hashes, source hashes, coverage, missing cells, polarity, uncertainty fields and claim eligibility were checked before this freeze.

No design code or study selection changed. The earlier design manifest's `outcome_extraction=NOT_STARTED` remains an accurate historical freeze statement; this new manifest records the subsequent completed phase instead of overwriting it.

## Coverage

9 studies / 25 frozen comparisons / 559 long-format records and 559 corresponding supported-claim records. These include 483 table records, 6 printed figure-matrix records, 22 missing table cells, 15 figure-panel records, 9 author-prose records and 24 benchmark-level N/A records. This is not 559 independent numerical experiments.

Every frozen comparison appears in the comparison and study summaries. All public TabLLM datasets and displayed budgets, all three healthcare tasks, all 65 FeatLLM dataset/shot cells, all 20 TabSTAR datasets, both CARTE task panels, both TabuLa subsets and all ConTextTab semantic metrics are retained. Supplemental LIFT model/task results are retained even where unnamed arms cannot be matched to the frozen formats. Additional PLATO 70%/90% edge arms, unrelated model ablations and our own stable-anonymous experiments do not belong to the frozen 25 pairs.

Matched primary rows comprise 422 numerical records and 32 records with unavailable directions. Another 26 primary numerical records have ambiguous format matching and are excluded from comparison-level direction counts. Aggregate metrics, pairwise summaries, aggregate repeats, duplicate presentations, qualitative reports and N/A rows remain separate. Study summaries retain each comparison; there is no strongest-comparator selection.

## Source review and checks

- Parsed tables were checked for full dataset/budget coverage and correct arm column assignments. Manual LIFT classification pairs were additionally checked against their source rows.
- Rendered PDF inspection confirmed LIFT Table 35's shared unnamed arm and unlabelled regression metric; TabLLM Table 15's blank Surgery/16384 cell; CARTE Figure 10's two panels; TabuLa Figure 12's two subsets and shaded bands; ConTextTab Figures 9–10's matrix axis directions and printed p-values.
- ConTextTab R2 uses the paper's soft clipping for negative scores. Its table contains changes relative to base, not absolute variant scores. Both directed win-ratio cells are preserved; ties can prevent their sum from being one. Printed p=0.00 is rounding, never literal zero.
- FeatLLM Table 4 gives SE of changes; Table 18 gives per-arm SD. Contrast uncertainty has a separate field and is not assigned to a comparator arm.
- TabSTAR's point estimates are rounded after bold selection; bold type and overlapping/non-overlapping 95% CIs are not converted into tests.
- `validate_outcomes.py` verifies 9/25/559 coverage, unchanged parent/source hashes, exact joins, missing data, granularity, numeric polarity, uncertainty separation and that positive utility statements only occur when the frozen utility code is Yes and arm matching is resolved. `../phase_c_v1/validate_codes.py` also passes.
- No new statistical test, average effect, pixel digitization or outcome-dependent design recoding was performed.

## Retained limitations

- LIFT: Tables 34–35 contain a shared unnamed condition rather than distinct format-I/II conditions. Those linked rows remain ambiguous. Table 35 does not explicitly label its regression metric; RAE is a contextual identification from Table 20/protocol, disclosed in every row. Its lower-is-better interpretation is also consistent with the printed bold minima. The caption's broad non-significance wording is not a pair-specific test for each frozen shuffled comparator.
- TabSTAR: Figure 8 uses Numerical-Full/Range/None labels; its correspondence to the tabulated labels is not silently assumed. The ambiguous figure presentation is an aggregate repeat and does not change the unambiguous Table 32 extraction.
- TARTE: official published TMLR indexed text confirms Figure 6 and the frozen arms, but official PDF download is restricted. The two figure records retain exact-rank and significance unavailability. Neither the supplied preacceptance tarte.pdf nor the author mirror supplies published numeric values for this extraction. Indexed source checked: https://openreview.net/pdf/7dfbc481b152839b35e7f200b528bd880a6826e2.pdf .

## Next phase: manuscript integration

No manuscript files were edited here. Use `STUDY_SUMMARY_V1.md` as the reviewable nine-study compression and retain the full comparison-level rationale/outcomes in the supplement. The study-level design count is 3/9 with at least one admissible utility reference; 4/25 is only a descriptive comparison count.

Published TabLLM List Only Values is non-admissible under Preservation. Its published omission gap must not be labelled predictive utility. Published List Permuted Names supports the content-sensitivity comparison; our subsequently constructed stable-anonymous reference must be introduced separately in the quantitative deep dive. This terminology correction is a necessary item for the manuscript integration phase.
