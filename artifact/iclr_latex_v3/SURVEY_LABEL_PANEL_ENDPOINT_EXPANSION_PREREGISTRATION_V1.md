# Pre-registration: ten-endpoint survey-label panel expansion, v1

Declared 2026-08-20 before any of the seven added endpoint label-panel cells
was fit.

## Prior observation disclosure

The ten endpoint pairs were selected outcome-blind and frozen in
`STAGE_ENDPOINT_EXPANSION_PREREGISTRATION_V1.md`. Their MxC interaction results
have since been observed. In addition, the original three label-panel outcomes
(diabetes, hypertension, current smoking) are already observed, including the
NHANES->KNHANES pipeline-versus-placebo mean `+0.2915` and reverse-direction raw
AUROCs around `.41--.44`. Therefore this is a prospectively frozen extension to
seven endpoints, not a fully held-out ten-endpoint discovery.

## Question

Does the label-measurement result survive when the effective endpoint count is
raised from three to the complete outcome-blind ten-item panel? Specifically,
does the operative documented table beat a capacity-matched wrong table, and
does raw-code transfer remain rank-reversing?

## Frozen design

- Reuse the exact label-panel feature surface, splits, weights, XGBoost
  hyperparameters, raw endpoint injection, and four arm names:
  `raw`, `pipeline_table`, `llm_table`, `placebo_table`.
- Run the ten frozen endpoints in both directions, seeds 50--59, at the original
  primary support `K=256`. The non-primary K values are not repeated.
- `pipeline_table` and fixed query evaluation maps are exactly those in the
  frozen ten-endpoint registry. Every added diagnosis item is binary:
  NHANES `{1->1,2->0,7/9->missing}` and KNHANES
  `{1->1,0->0,8/9->missing}`.
- `placebo_table` uses the original generator unchanged: pool documented valid
  and sentinel codes, mask the documented sentinel capacity, and uniformly
  permute the true output multiset over survivors. The original RNG namespace
  is retained so the first three endpoints must reproduce their frozen K=256
  cells exactly.
- The inherited `llm_table` name has mixed provenance. For the original three
  endpoints it is the frozen isolated-LLM majority extraction. No such LLM
  extraction exists for the added seven, so their slot is filled by the frozen
  codebook-canonical binary table and tagged
  `codebook_registry_not_llm`. No pooled ten-endpoint LLM claim is allowed.

The endpoint's own slot remains excluded from features. A placebo fit may be
non-evaluable when its wrong table maps away all training labels; this remains
`NaN` as in the original runner and is never imputed.

## Construction gates

1. Exactly 10 endpoints x 2 directions x 10 seeds = 200 cells.
2. Each endpoint-direction unit has at least 8/10 finite paired
   `pipeline_table`/`placebo_table` seeds. If not, the primary panel verdict is
   not evaluable.
3. All original-three K=256 arm values reproduce the corresponding frozen
   direction-specific run exactly, including matching `NaN` locations.
4. On each added endpoint, `llm_table` and `pipeline_table` are numerically
   identical; this is a provenance/construction audit, not evidence for LLMs.

## Primary estimand and inference

For endpoint `e`, direction `d`, and finite seed `s`, define

`G_eds = AUROC(pipeline_table) - AUROC(placebo_table)`.

Average seeds within direction and the two paired directions within endpoint.
The primary inferential unit is the endpoint cluster (`n=10`). A 10,000-rep
hierarchical bootstrap (seed 20260820) resamples endpoints and then finite seeds
within each selected endpoint-direction; directions remain paired.

P1 separates if all construction gates pass and:

- pooled endpoint-cluster mean `G>0` with CI95 lower bound above zero;
- at least 6/10 endpoint-cluster means are positive;
- the mean remains positive after dropping the best endpoint;
- the diabetes-excluded mean remains positive.

Report both direction means, all endpoint means, finite coverage, and a ladder
dropping the best one and best two endpoints.

## Raw-code reversal

R1 uses the absolute raw-arm AUROC, averaged with the same endpoint clustering
and bootstrap. It passes if pooled mean AUROC is below `.5`, the CI95 upper
bound is below `.5`, each direction mean is below `.5`, at least 6/10 endpoint
means are below `.5`, and the diabetes-excluded mean is below `.5`.

`raw-pipeline_table` differences, pipeline absolute AUROC, the mixed-provenance
`llm_table`, and support/evaluation counts are descriptive. A failed P1 or R1
cannot be repaired by selecting a direction or endpoint subset.

Runner: `scripts/run_crta_v3_survey_label_panel_endpoint_expansion_v1.py`.  
Adjudicator: `scripts/summarize_crta_v3_survey_label_panel_endpoint_expansion_v1.py`.
