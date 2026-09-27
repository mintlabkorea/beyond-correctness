# Pre-registration: endpoint source informativeness predicts real M×C, v1

Declared 2026-08-20 before either new arm is fit.

## Prior observation disclosure

The ten endpoints and both directions were frozen outcome-blind in
`STAGE_ENDPOINT_EXPANSION_PREREGISTRATION_V1.md`, but their four-arm M×C
results have already been observed. In particular, endpoint-clustered corrected
interactions are heterogeneous: diabetes is strongly positive, while arthritis
and hypertension are negative. This study prospectively tests a new contrast
on those already-observed endpoints; it is not a held-out endpoint confirmation.

## Question

If correct measurement and correspondence make source content commensurable
with the target, does independently measured source informativeness predict the
sign and magnitude of the existing endpoint-level M×C interaction?

## Frozen panel and fits

- The same ten endpoints, NHANES→KNHANES and KNHANES→NHANES, seeds 50–59,
  K=256, query rows, documented label maps, base/member slots, and XGBoost
  hyperparameters as the frozen endpoint expansion.
- `source_only_correct`: the exact correct `a11_stage_columns` representation,
  trained on valid source rows only and evaluated on the unchanged target query.
- `target_only_correct`: the same correct target representation, trained on the
  same K=256 target-support rows only and evaluated on the same query.
- Neither new arm changes endpoint eligibility, splits, query labels, features,
  or existing interaction cells.
- A frozen target-support draw with only one observed class remains a valid
  target-only scarce-support cell. As in the parent stage runner, XGBRegressor
  is fit and its constant/rank-degenerate prediction is scored; the draw is not
  redrawn, excluded, or labelled not evaluable.

Expected completeness is 10 endpoints × 2 directions × 10 seeds = 200 cells,
with two new fits per cell. Endpoint, not seed or direction, is the primary
inferential unit.

## Primary predictor and outcome

For endpoint `e` and direction `d`, define source informativeness

`S_ed = mean_seed(AUROC(source_only_correct) - 0.5)`.

The documented correct label orientation is retained; AUROC is not folded with
`max(A,1-A)`, so anti-predictive transfer remains negative. Average the two
directions within endpoint to obtain `S_e`.

The outcome `I_e*` is the already-observed, arm-wise polarity-corrected

`(a11*-a10*) - (a01*-a00*)`,

averaged over seeds and then over the two directions within endpoint.
`source_only_correct` shares no fitted arm with this outcome.

## Frozen adjudication

Primary P1 uses Spearman correlation across the ten endpoint clusters.

- Directional prediction: `rho(S_e, I_e*) > 0`.
- One-sided exact permutation p-value over all `10!` permutations must be
  `< 0.05`.
- Diabetes-excluded Spearman rho must remain positive. This is a concentration
  guard, not a second p-value.

Report all endpoint pairs, direction-specific correlations, every
leave-one-endpoint-out rho, and the exact permutation denominator. Do not turn
a failed P1 into confirmation by selecting a direction or endpoint subset.

## Secondary target-only diagnostic

`U = a11* - target_only_correct*` directly measures marginal source utility but
shares `a11*` with `I*`; therefore it has a part–whole coupling and cannot be an
independent primary confirmation. Report only cross-seed diagnostics:

- proxy on seeds 50–54 versus interaction on 55–59;
- proxy on seeds 55–59 versus interaction on 50–54;
- the two Spearman correlations and their arithmetic mean.

These remain descriptive even if positive. Raw-AUROC analogues are reported as
sensitivity only.

## Interpretation lock

- P1 pass: the signal/noise-transmission interpretation makes a successful
  real-data endpoint-level prediction within this already-observed panel.
- P1 fail: endpoint heterogeneity remains a limitation; it does not invalidate
  the semi-synthetic sign reversal, and no alternative proxy may be promoted.
- The null-source verdict remains failed and quarantined either way.

Runner: `scripts/run_crta_v3_endpoint_source_informativeness_v1.py`.
Adjudicator: `scripts/summarize_crta_v3_endpoint_source_informativeness_v1.py`.
