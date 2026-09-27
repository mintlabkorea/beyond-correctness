# Pre-registration: null-source falsification of M×C, v1

Declared 2026-08-20 before executing any null-source fit. This experiment asks
whether the M×C adjudicator produces a nonzero interaction when the transferred
source labels contain no feature signal. It is a falsification check for the
paper's strongest interaction claim, not a new efficacy family.

## Frozen data and cell reuse

- Reuse the public NHANES panel, row splits, renderings, measurement tables,
  correspondence derangements, outcomes, and three fixed mechanism families
  from `MCR_FACTORIAL_SEMISYNTHETIC_PREREGISTRATION_V1.md`.
- Reuse all 60 salted primary cells: additive, pairwise, sparse × realizations
  0–19. Target support (`K=32`), target query, and their labels remain exactly
  as in the original cell.
- XGBoost and HistGB use the original frozen hyperparameters and CPU-only
  execution. Backbones share cells and are not independent replicates.

## Frozen null-source intervention

Within each family×realization, permute the 2,048 source labels with a
deterministic no-fixed-point permutation under namespace
`mcr_null_source_v1|family|realization`. The same permutation is reused for all
four M/C arms and both backbones. Source feature values, missingness,
measurement rendering, label multiset, and target data are unchanged.

The intervention destroys the row-wise source feature–label relation while
retaining the source label marginal. It does not assert exact zero empirical
correlation in a finite realization; the realized correlations are descriptive
audits only.

## Frozen arms and estimand

Relation input is absent in every arm. Execute only:

- `m1c1rf`: correct M, correct C;
- `m1c0rf`: correct M, deranged C;
- `m0c1rf`: wrong M, correct C;
- `m0c0rf`: wrong M, deranged C.

Primary metric is `Q = -MSE/Var(y_query)`. For every fixed family×backbone,

`I_MC^null = Q(m1c1rf) - Q(m1c0rf) - Q(m0c1rf) + Q(m0c0rf)`.

The independent unit is realization (`n=20` within each fixed family).

## Frozen inference and verdict

Use a paired realization bootstrap with 10,000 repetitions and seed 20260820.
No pooling across families or backbones. The equivalence margin is fixed at
`±0.05 Q`, the same numerical margin used for the MCR exchangeable-null checks
and less than 14% of the smallest original K=32 family-level M×C effect.

A family×backbone falsification check passes only if:

1. the 95% bootstrap interval contains zero; and
2. the entire 95% interval lies strictly inside `[-0.05,+0.05]`.

The grid passes only if all three families×both backbones pass
(intersection–union, 6/6). Mean, interval, sign fraction, and maximum absolute
source feature–shuffled-label correlation are reported regardless of verdict.

Interpretation is frozen:

- **6/6 pass:** the original positive M×C interaction does not reproduce when
  the transferred source labels are signal-free, arguing against an
  adjudicator-generated interaction at the registered margin.
- **Any failure:** the M×C headline is quarantined from a mechanism claim until
  the failed family/backbone is diagnosed. A wide interval is failure, not
  evidence for the null.

Runner:
`scripts/run_crta_v3_mcr_null_source_v1.py`.

Adjudicator:
`scripts/summarize_crta_v3_mcr_null_source_v1.py`.
