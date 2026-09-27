# MCR mismatch support ladder V1

Status: post-result descriptive extension requested after inspection of the
two-endpoint target-support comparison.

## Fixed design

- Support sizes: `K = {32, 64, 128, 256, 512}`.
- Outcome families: additive, pairwise, and sparse.
- Realizations: the existing 20 frozen MCR realizations per family.
- Learners: XGBoost, HistGradientBoosting, and TabPFN with the same frozen
  configurations used by the mismatch-dose experiments.
- Mismatch state: full measurement mismatch (`d=8`) with sentinels neutralized
  to missing, exactly as in the primary MCR mismatch-dose reference.
- Arms:
  - `intended`: documented decoding, true correspondence, free relation;
  - `reference`: full-mismatch source values, true correspondence, free relation;
  - `matched_wrong`: wrong measurement decoding, true correspondence, free relation.
- Metric: normalized MSE on the unchanged frozen query set. Lower values denote
  better prediction; plotted benefits are `nMSE(reference)-nMSE(intended)`.
- Target supports use the MCR runner's existing outcome-blind deterministic
  support draw for each `K`. Existing `K=32` and `K=512` cells therefore retain
  their original row selections; intermediate supports are additional draws,
  not interpolated values.

## Interpretation

This is a descriptive support-response extension, not a new confirmatory
family. Curves report all five measured support levels. No monotonicity verdict
is assigned in advance, and no intermediate point may be omitted after fitting.

## Integrity checks

- Reconstruct the frozen source rendering and full-mismatch frame.
- Require the dose order and mismatch-entry count to match the original frozen
  mismatch-dose cell.
- Require the intended arm to equal the parent runner's `m1c1rf` matrices and
  the matched-wrong arm to equal `m0c1rf`.
- Record all three arms for every family, realization, learner, and support.

