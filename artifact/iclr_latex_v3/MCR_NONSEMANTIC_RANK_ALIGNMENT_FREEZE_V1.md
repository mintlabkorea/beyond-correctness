# Frozen design: non-semantic rank alignment in the controlled mismatch ladder

Frozen 2026-09-03 (Asia/Seoul) before any rank-aligned outcome was fit or
inspected. This is a post-result confirmatory response to the alternative
explanation that the controlled measurement result reflects coordinate
alignment under pooled tree fitting rather than a uniquely semantic benefit.

## Prior observations and scope

The existing mismatch-dose experiment is known to give approximately
`+.26` predictive utility at full mismatch and `K=32` for both XGBoost and
HistGradientBoosting. Its primary raw arm already maps the true source
sentinels to missing values, so the headline effect is not attributable to
live sentinel codes. The same experiment varies increasing affine recodings,
ordinal recodings that may preserve or reverse polarity, and which features
are dosed. Post-result regressions on those counts are descriptive and will
not be interpreted as a causal decomposition.

The new analysis asks whether a generic, label-free distribution-alignment
operation can substitute for documented decoding. Rank alignment is not
called a new admissible reference: it adds a preprocessing intervention and
therefore changes the comparison. Instead, the experiment is a matched 2 x 2
design that applies the same preprocessing choice to both decoded and raw
frames.

## Reused cells and factorial arms

The analysis reuses the frozen 60 primary cells, row splits, mechanisms,
renderings, balanced nested feature-dose order, target supports, outcomes,
and learner recipes from `MCR_MISMATCH_DOSE_PREREGISTRATION_V1.md`. Doses are
`d in {0,2,4,6,8}`. The raw source frame is the sentinel-neutral `raw_d`
frame from that experiment; no live-sentinel arm is rerun.

For each dose, the four conceptual arms are

| | No rank alignment | Rank alignment |
|---|---|---|
| Documented decode | `decode_none` | `decode_rank` |
| Sentinel-neutral raw | `raw_none_d` | `raw_rank_d` |

The existing no-rank metrics are imported only after exact input, core-runner,
cell, and dose-order checks. The two rank-aligned arms are newly fit. At
`d=0`, decoded and raw frames are bit-identical before rank transformation and
must remain bit-identical afterward.

## Frozen rank transformation

Rank alignment is feature-wise and domain-specific. For a finite fitting
sample of size `n`, a value `x` is mapped to

`(number below x + 0.5 * number equal to x) / n`.

This is the empirical mid-distribution transform. Values below or above the
fitting range map to `0` or `1`; missing values remain missing. A feature with
no finite fitting observations remains missing. No labels, outcomes, feature
names, rendering tables, or cross-domain pair statistics enter the map.

Two target-map regimes are fixed:

1. `support_only` (primary, inductive): the source map is fitted on source
   training rows and the target map only on the `K` labeled-target support
   rows. Target query features are transformed by the frozen support map.
2. `support_query` (label-free transductive sensitivity): the source map is
   unchanged, while the target map is fitted on the union of target support
   and query features. Query labels are never used.

The decoded and raw arms in a regime receive the same target transformation;
their source maps are fitted separately to their own source frames. This is
necessary for a generic within-domain rank operation. Increasing affine
recodings and same-direction ordinal recodings are expected to become
invariant in rank space. Polarity reversals are not, so complete closure is
not required by construction.

## Learners, budgets, and fits

- Primary grid: XGBoost and HistGradientBoosting at `K=32`, all three outcome
  families and 20 realizations.
- Support sensitivity: XGBoost at `K=512`, matching the original registered
  mismatch-dose grid.
- Both rank-map regimes are run throughout. TabPFN is outside the required
  response because the objection concerns pooled axis-aligned tree fitting.
- Models, hyperparameters, weights, seeds, query rows, and normalized-MSE
  metric are inherited unchanged from the frozen controlled runner.

## Estimands and adjudication

Let `Q=-nMSE`. For each cell, dose, learner, support size, and rank-map regime:

- original semantic utility: `U_raw = Q(decode_none)-Q(raw_none)`;
- semantic utility conditional on generic alignment:
  `U_rank = Q(decode_rank)-Q(raw_rank)`;
- generic alignment gain on the raw arm:
  `A_rank = Q(raw_rank)-Q(raw_none)`;
- effect of rank preprocessing on the decoded arm:
  `D_rank = Q(decode_rank)-Q(decode_none)`;
- absorbed original gap: `C_rank = U_raw-U_rank = A_rank-D_rank`;
- alternative-baseline performance gap:
  `G = Q(decode_none)-Q(raw_rank)`.

`G` is not called semantic utility. It answers whether generic alignment
recovers the performance of untransformed documented decoding.

The primary test is at full dose, separately within each of the six
family-by-learner strata at `K=32`, using 10,000 realization-bootstrap draws.
Rank alignment is said to absorb a separated part of the original gap in a
stratum when the mean of `C_rank` is positive and its 95% interval is above
zero. Residual conditional utility is separated when the mean of `U_rank` is
positive, its interval is above zero, and at least 60% of realizations are
positive. No grid-level success label is required: every stratum and both
map regimes are reported.

Across doses, mean curves for all five contrasts are reported. The
realization-level Spearman correlation of `U_rank(d)` with dose is descriptive
because the feature mixture changes with dose. The XGBoost `K=512` results and
the transductive regime are sensitivities rather than replacements for the
primary `K=32` support-only comparison.

## Interpretation map

- `C_rank` separated and `U_rank` unresolved or near zero: much of the
  original controlled effect is substitutable by non-semantic coordinate
  alignment; the original measurement-utility claim must be narrowed.
- Both `C_rank` and `U_rank` separated: generic alignment absorbs part of the
  gap, while documented decoding retains incremental utility under the
  matched rank design.
- `C_rank` unresolved: the tested generic alignment does not demonstrably
  explain the original gap; this does not rule out other non-semantic
  alignment procedures.
- A material negative `D_rank` indicates that rank alignment also discards
  predictive distributional information; `A_rank` alone must then not be
  interpreted as the fraction of semantic utility explained.

These results concern this constructed panel and the specified empirical-rank
operation. They do not establish that documented decoding and generic
distribution alignment are equivalent interventions in real data.

## Required artifacts

Runner, construction self-test, summarizer, this frozen design and their
hashes; per-cell metrics for all 60 cells; complete-cell and provenance audit;
family/learner/dose summaries for both map regimes; and a compact result
report. Engineering smoke outputs, if any, are stored outside the evidence
root and are not used for inference.
