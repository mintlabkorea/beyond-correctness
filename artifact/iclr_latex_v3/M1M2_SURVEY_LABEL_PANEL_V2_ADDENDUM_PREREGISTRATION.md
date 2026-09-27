# Pre-registration addendum: survey-label panel v2 (extraction-v2 table)

Declared 2026-08-20 ~00:45, after the v2 re-extraction's DIQ010 flip was
confirmed (3/3 samples, as predicted in the frozen prompt manifest
`harmon_prompts_v2/PROMPT_MANIFEST.json`) and **before any v2 panel cell
has been executed.**

## 1. What changes vs the v1 panel

Identical design, cells, metric, and adjudication to
`M1M2_SURVEY_LABEL_MEASUREMENT_PANEL_PREREGISTRATION_V1.md`, with exactly
one substitution: `llm_table` is translated from the **v2 documented
responses** (`harmon_responses_v2/raw_documented_v2_s{1,2,3}.txt`,
majority of 3; same canon translation), and `placebo_table` is re-derived
capacity-matched to that v2 table. `raw` and `pipeline_table` are
recomputed in the new root for internal consistency.

Known v2 translation consequences, recorded before running: DIQ010 canon
becomes {1→1.0, 2→0.5, 3→0.0} (yes-high, polarity concordant with de1;
"no" sits at 0.5 vs the target's 0.0, and borderline lands at 0.0 — a
scale offset and a mild misorder, but no inversion). BPQ020/SMQ040
unchanged-correct. KLoSA-style sentinel divergence does not apply here.

## 2. Frozen predictions

- **P-A1′**: `llm_table(v2)` vs `placebo_table`: **separated** (the v1
  panel's A1 failed only through the diabetes inversion).
- **P-A3′**: per-target `llm − pipeline`: diabetes mean within ±0.10
  AUROC (an order-of-magnitude repair of v1's −0.704); hypertension CI
  containing 0 or degenerate-equal; smoking CI above 0 (the graded-map
  advantage, replicating v1's favorable mismatch).

## 3. Execution

Thin wrapper `scripts/run_crta_v3_survey_label_panel_v2.py` (imports the
v1 runner module, overrides the response directory/sample names and the
placebo rng namespace to `label_panel_v2`), same summarizer, out-root
`experiments/crta_v3_survey_label_panel_v2/`. 30 cells, 3 shards × 2
threads. Committed before launch.
