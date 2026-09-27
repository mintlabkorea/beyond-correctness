# Frozen protocol: real-data computed-value reconstruction falsification

Frozen before any outcome-bearing fit or inspection of any existing computed-value
utility result. This is a post-review extension and is not part of the manuscript.

## Question and asymmetric scope

The test asks whether an outcome-free reconstruction score measured before fitting
the outcome reference predicts when a supplied **computed relation value** can add
predictive utility. It does not apply the score to directional-constraint utility.

Track A is a falsification check plus a semi-synthetic real-data noise ladder.
Track B contains no numerical surrogate: for fixed covariates `X`, replacing `Y`
by `-Y` leaves every `X`-only score unchanged while reversing the correct monotone
direction and potentially the utility sign. Therefore an `X`-only outcome-free
proxy cannot identify directional-constraint utility. A binding diagnostic based
on an unconstrained outcome fit is outside the proxy class because it requires the
reference fit first.

## Frozen channels and cells

1. NHANES -> KNHANES: clean supplied value `SBP - DBP`; targets glucose,
   waist circumference, triglycerides, and total cholesterol; seeds 50--54;
   exactly 256 target-support rows. SBP and DBP targets are excluded because the
   computed value would contain the outcome. Metric: query-SD-normalized RMSE.
2. CAMELS-US -> CAMELS-GB: clean supplied value `PET mean / precipitation mean`;
   the frozen 12 query basins plus the 108 hash-continuation query basins;
   five frozen target-support basins; seeds 20--24. Metric: log1p-RMSE.
3. HRS has no eligible computed-value relation and is not run.

No pre-existing computed-value utility file is read. All utility is fitted anew
after the proxy predictions are sealed.

## Frozen perturbation and models

Noise standard deviations are `[0, 0.125, 0.25, 0.5, 1, 2, 4]` in the
fit-side IQR of each constituent. A single deterministic standard-normal draw is
scaled at every rung so perturbations are nested. Missingness is unchanged. For
CAMELS static attributes, one draw per basin is repeated across its dates. The
CAMELS base already contains `aridity`, a direct precomputed duplicate of the
PET/precipitation relation; the perturbation therefore covers the full redundant
closure `pet_mean`, `p_mean`, and `aridity`. Otherwise the proposed ladder would
leave an exact unperturbed copy in the reference frame and would not manipulate
reconstructibility.

At every rung, reference and intended arms receive the identical noisy base frame
and identical width. The intended arm additionally receives the clean, side-fitted
robust-standardized relation value and its availability flag; the reference gets
two zero columns. The supplied value is never recomputed from noisy constituents.

The proxy fits the clean standardized relation value from the noisy base using
source plus target support and evaluates held-out target query. It uses no outcome
magnitudes and no reference/utility result. Downstream XGBoost parameters match the
corresponding existing real-data runner. CAMELS reconstruction R2 is computed after
averaging predictions within basin, so the 120 static values are equally weighted.

## Frozen order and predictions

Execution is mechanically separated:

1. hash and freeze this protocol, runner, dependencies, and input data;
2. run proxy fits only;
3. write reconstruction results and the following predictions, then seal their
   file hash;
4. permit outcome utility fits only if all frozen hashes and the proxy seal match;
5. report every result.

At noise zero, if a setting's mean reconstruction R2 is at least 0.95, the frozen
prediction is that the absolute mean utility is no larger than its borrowed
planning-resolution band: 0.0095 normalized-RMSE for NHANES--KNHANES and 0.0015
log-RMSE for CAMELS-120. These are falsification bands, not equivalence margins.
If the R2 gate is not met, the endpoint check is declared uninformative rather than
retrofitted.

For the ladder, utility is predicted to increase as unreconstructibility
`1 - R2` increases. The primary within-setting statistic is the mean cell-wise
Spearman correlation across the seven rungs, with a percentile 95% cluster
bootstrap interval over cells (10,000 resamples, seed 20260903). The prespecified
criterion is a lower interval bound above zero. Raw slopes and utilities are never
pooled across the two outcome scales, and the controlled-benchmark slope is not
transferred.

## Interpretation limits

The zero-noise endpoint can falsify but cannot confirm the proxy with only two
relation families. The ladder uses real covariates and outcomes but semi-synthetic
constituent corruption. Noise can weaken both relation reconstruction and the raw
predictor path; this limits causal/mechanistic interpretation but does not alter
the prospective prediction being tested. Regardless of success or failure, no
paper source is edited by this run.
