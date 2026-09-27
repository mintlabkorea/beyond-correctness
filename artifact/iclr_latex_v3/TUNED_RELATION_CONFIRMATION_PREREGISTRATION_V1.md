# Pre-registration: tuned-free relation confirmation, v1

Declared 2026-08-27 before any cell from the new realization namespace is
fit. This is a review-triggered, confirmatory extension. It tests whether
correct directional knowledge adds predictive utility after the unconstrained
reference is tuned fairly, and whether any gain is specific to the correct
semantic restriction rather than generic function-class shrinkage.

## Independent cells and frozen panel

Reuse the controlled relation generator and frozen raw NHANES panel from the
main experiment, but use previously unexecuted realization IDs 100--139.
Run all three mechanism families (`additive`, `pairwise`, `sparse`) and target
supports K in {32, 512}. The original query construction is unchanged: 2,000
target rows are held out before support sampling. Query outcomes may not enter
model selection.

## Four interface-matched arms

Measurement and correspondence are correct in every arm.

- `correct`: the true monotonic restrictions.
- `free`: no monotonic restrictions. For pair-operation families, the true
  operation columns remain present, so only the restriction is removed.
- `flipped`: the same restricted columns with every true direction reversed.
- `random`: the same number of restrictions, unrelated to the true semantic
  directions. For additive cells, locations and signs are a matched random
  draw. For pair-operation cells, the true operation columns remain present
  and a random sign vector is drawn conditional on differing from both the
  correct and completely flipped vectors.

Thus `correct` versus `free` isolates executable direction at a common
interface; `correct` versus `random` tests semantic specificity without
changing restriction count.

## Frozen arm-wise tuning

Every arm receives the same nine one-factor XGBoost configurations used in
the registered capacity sensitivity:

`depth2`, `depth4`, `baseline`, `depth8`, `depth12`, `l2_0`, `l2_10`,
`trees100`, and `trees1000`.

Within each family x realization x K cell, independently split source rows
and target-support rows 75/25 with deterministic keys shared by every arm and
configuration. Fit on the two training partitions. The selection score is the
equal-weight average of source-validation NMSE and target-support-validation
NMSE, each normalized by its own validation variance. Select the lowest score
independently for each arm; deterministic grid order breaks exact ties. Then
refit the selected configuration on all source plus all K support rows and
evaluate the untouched query once. Training remains unweighted, matching the
primary controlled relation analysis.

## Estimands and inference

Quality is Q = -NMSE on the untouched query. At K=32, first average each
contrast over the three mechanism families within realization; the 40
realizations are the independent inferential units. The primary interval is a
two-sided 95% Student-t interval over these 40 means. BCa bootstrap intervals
(10,000 draws, seed 20260827) are sensitivity analyses.

Primary utility:

`Q(tuned correct) - Q(tuned free)`.

Co-primary semantic specificity:

`Q(tuned correct) - Q(tuned random)`.

Secondary wrong-direction harm:

`Q(tuned free) - Q(tuned flipped)`.

The confirmatory claim requires both primary Student-t intervals at K=32 to
exclude zero above. K=512 and family-specific results are prespecified
secondary heterogeneity analyses, not substitutes for the primary result.
Selected-configuration frequencies and every realization-level contrast are
reported regardless of outcome.

