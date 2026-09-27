# Frozen protocol: fixed-width noisy-proxy recoverability ladder

Declared 2026-09-07 before any result from this experiment was fit or read.
This is a post-result diagnostic motivated by reviewer criticism; it does not
retroactively select an existing reference or replace the frozen primary
comparison.

## Question and scope

The existing MCR redundancy ladder lowers recoverability by deleting true
constituent columns.  That intervention also changes frame width and the set of
available variable identities.  This experiment asks the narrower controlled
question: when width, identities, missingness, rows, learner, and the
intended/reference contrast are fixed, does relation-value utility rise
continuously as the same constituent channels become less informative?

The conclusion is restricted to the constructed pairwise and sparse MCR
families.  It must be reported together with the existing real-data
reconstruction falsification, which did not establish a family-general
monotone relationship.

## Frozen design

- Frozen input: the MCR public-use panel with SHA-256
  `6af2215c72a65ecc306e5c4d3d9af5b61b16a073dd5aa4c0f33b178741245a25`.
- Families: `pairwise`, `sparse`; 20 frozen realizations per family.
- Supports: `K={32,512}`.
- Backbones: frozen MCR XGBoost and HistGradientBoosting configurations.
- Noise doses in source-IQR units:
  `sigma={0,0.125,0.25,0.5,1,2,4}`.
- Pooling remains unweighted.  Target-query labels are not used by the proxy
  phase.

For each `(family, realization, feature)` one standard-normal draw is generated
for every panel row from the SHA-256-keyed namespace
`mcr_noisy_proxy_v1|family|realization|feature`.  The same draw is reused at
every dose, in both arms, and wherever the same row occurs at either support
size.  For each constituent feature, noise is

`sigma * source_IQR(feature) * epsilon(row, feature)`.

The scale is estimated only from the frozen source rows.  A nonpositive IQR
falls back to source SD, then to 1.  Noise is added only at finite entries, so
the missingness mask is unchanged.  Nonconstituent columns are bit-identical to
the frozen decoded base frame.  Constituent columns remain present under their
original identities at every dose.

## Arms and intervention contract

At every dose the editable region is only the designated relation-value
channel:

| Arm | Base frame | Relation-value channel |
|---|---|---|
| `reference` | all eight base columns, with the frozen noisy proxies | absent |
| `intended` | the identical noisy-proxy base frame | exact clean compiled operation column(s) |

No monotone constraint is supplied in either arm.  The exact relation values
are compiled from the clean decoded constituents before proxy corruption.

The three gates are checked structurally at every cell:

1. **Removal:** `reference` contains no compiled relation-value channel.
2. **Preservation:** both arms share the exact noisy base block; all eight base
   identities, row order, split, missingness mask, learner configuration, and
   nonconstituent values are preserved.
3. **Interface:** matrices have the expected finite/NaN pattern and dimensions,
   and both are accepted by the unchanged learner without shape failure.

## Recoverability diagnostic and phase separation

For each exact reference frame, each clean operation column is reconstructed
separately using the same backbone and frozen hyperparameters.  The
reconstructor is fit on source plus target-support rows and scored on held-out
target-query rows.  Operation-level query R-squared values are averaged without
clipping.  The proxy phase receives no task outcome in a model fit and writes
all reconstruction results first.  Their hashes are sealed in
`PROXY_SEAL_V1.json`.  The utility phase refuses to run unless this complete
40-cell seal validates.

Utility is

`U(sigma) = nMSE(reference, sigma) - nMSE(intended, sigma)`,

so positive values mean the supplied clean relation channel helps.

## Frozen analysis

The independent unit is the realization.  Results are stratified by family,
backbone, and support size (eight strata).  Bootstrap resampling uses 10,000
realization-cluster replicates and the keyed seed namespace
`mcr_noisy_proxy_bootstrap_v1`.

Primary diagnostic:

1. Within every realization, compute Spearman correlation between
   `1 - reconstruction_R2` and `U` across the seven doses.
2. For each of the eight strata, report the mean realization-level correlation
   and its realization bootstrap 95% interval.
3. A stratum supports graded recoverability only when the mean is positive and
   the interval excludes zero.  The global controlled claim requires all eight
   strata to satisfy this rule.

Integrity/supporting diagnostics, not candidate-selection rules:

- mean reconstruction R-squared at every dose, including whether the mean at
  `sigma=0` exceeds 0.95;
- mean utility and realization-bootstrap interval at every dose;
- absolute reference and intended nMSE changes relative to `sigma=0`;
- within-realization Spearman correlations of dose with reconstruction
  R-squared and with utility;
- all three structural gates and proxy-seal validation.

If both intended and reference performance deteriorate substantially, the
mechanism is described as shared input degradation rather than as evidence
that low recoverability alone is sufficient.  No result from this experiment
may be generalized beyond the controlled relation-value setting without an
independent real-data replication.

