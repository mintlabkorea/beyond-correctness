# Controlled relation capacity and regularization sensitivity, v1

Frozen 2026-08-27 before execution.  This post-result sensitivity asks whether
the sign and scale of relation utility are stable over reasonable XGBoost
capacities.  It does not tune a learner or choose a configuration by effect
size.

## Frozen cells and arms

Reuse the exact 60 primary cells, outcome mechanisms, support/query rows and
RNG namespace from the MCR factorial benchmark.  Evaluate K in {32, 512} and
all additive, pairwise and sparse families.  For each cell/configuration fit:

- `m1c1rf`: correct M/C with the free reference;
- `r_op_only`: correct M/C and true operation values without constraints
  (pairwise/sparse only);
- `m1c1r1`: the same supplied content with executable true directions.

Report total utility `Q(m1c1r1)-Q(m1c1rf)` in all families and the incremental
direction contribution `Q(m1c1r1)-Q(r_op_only)` where defined.

## Frozen one-factor-at-a-time configurations

The baseline is 300 trees, depth 6, L2=1, learning rate .05,
min_child_weight=20 and otherwise the factorial XGBoost contract.  Nine unique
configurations are reported:

- depth axis: 2, 4, 6, 8, 12 at trees=300 and L2=1;
- L2 axis: 0, 1, 10 at trees=300 and depth=6;
- tree axis: 100, 300, 1000 at depth=6 and L2=1.

Shared baseline duplicates are fit once.  There is no full factorial, early
stopping or model selection.

## Reporting and adjudication

Q is `-MSE/Var(y_query)`.  Within each family x K x configuration, report the
paired 20-realization mean, percentile bootstrap interval (10,000 draws, seed
key rooted at 20260827), and win fraction.  The main sensitivity summary is the
range and sign count across all nine configurations, separately for total and
incremental utility.  Stability means all configuration means are positive
and no mean exceeds four times or falls below one quarter of the frozen
baseline magnitude within its family/K cell.  This descriptive fourfold band
is a scale-stability rule, not an equivalence margin.  All cells are reported
even if the stability rule fails.

