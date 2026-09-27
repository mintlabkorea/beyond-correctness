# Conditional correspondence utility: exploratory analysis and HistGB confirmation

Frozen 2026-08-27.  The XGBoost ten-endpoint cells already existed and had been
inspected before this document.  Their `a11_stage_columns - a10_stage` contrast
is therefore an exploratory conditional analysis.  After observing that
exploratory contrast, this HistGradientBoosting protocol was frozen before any
new confirmation cell was executed.

## Estimand

At K=256 and with measurement supplied in both arms:

`conditional C utility = AUROC(a11_stage_columns) - AUROC(a10_stage)`.

This asks whether adding the correctly bound nine member columns helps beyond
the supplied measurement-stage base.  It is not the standalone C utility from
the earlier three-endpoint surface.  NHANES->KNHANES and KNHANES->NHANES use
the same ten fixed questionnaire endpoints, ten seeds (50--59), split/support
rows, label maps and endpoint-specific target evaluation as the executed XGB
endpoint expansion.

## Confirmation learner and arms

Use `HistGradientBoostingRegressor(max_iter=300, max_depth=6,
learning_rate=.05, min_samples_leaf=20, l2_regularization=1,
early_stopping=False, random_state=seed)`, source rows plus equal-total-weight
K=256 target support, and exactly three arms:

- `a11_stage_columns`: supplied measurement plus correct member binding;
- `a10_stage`: supplied measurement, no added member columns;
- `pl_columns_at_stage`: supplied measurement plus the exact XGB
  endpoint-expansion derangement for the same direction/endpoint/seed.

The third arm permits the content/harm decomposition but the primary
confirmation estimand is a11-a10.  No other support budget is part of the
confirmation family.

## Fixed analysis

First average the ten seeds within each direction x endpoint cell, then average
the two directions to form ten independent endpoint-cluster estimates.  Report
all ten estimates, their unweighted mean, 9/10-style sign count, leave-best-out
mean, a two-sided Student-t 95% interval over the ten endpoint clusters, and a
10,000-draw endpoint bootstrap (seed 20260827) as sensitivity.  Confirmation
means positive mean, t-interval lower bound above zero, at least 8/10 positive
endpoint clusters, and positive leave-best-out mean.  The result is reported
regardless of verdict.  XGB and HistGB are never pooled as independent units.

