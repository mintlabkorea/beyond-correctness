# Pre-registration: null-source mass ladder B, v1

Declared 2026-08-20 after the pre-frozen B trigger fired, and before either
new source-mass cell was fit.

## Trigger disclosure

`MCR_SOURCE_INFORMATIVENESS_LADDER_PREREGISTRATION_V1.md` required B if at
least four of six fixed strata crossed only in the final α interval. All six
strata crossed in `[0.75,1.00]`, so B is mandatory. The α=1, 2,048-source-row
endpoint is already observed and remains the failed/quarantined null-source
result. It is reused, not refit or reclassified.

## Frozen design

- Reuse the exact 60 primary cells: three fixed families x 20 realizations,
  K=32, the four free-R M/C arms, XGBoost and HistGB.
- Fix α=1: source labels are a no-fixed-point derangement preserving the exact
  label multiset within the selected source subset.
- Source mass is `{128,512,2048}`. Only 128 and 512 are new fits; 2048 is read
  from `experiments/crta_v3_mcr_null_source_v1`.
- Draw one deterministic, outcome-blind ordering of the 2,048 frozen source
  positions per family x realization. The first 128 positions are a subset of
  the first 512; all 2,048 positions recover the original source block.
- At each mass, sort selected positions back into frozen row order and draw the
  null runner's deterministic derangement at that subset size. Thus each mass
  exactly preserves its own source-label marginal. Label assignments need not
  be nested across masses; this is a mass intervention, not another α dose.
- Target support/query rows, lesions, features, fitting weights, model settings,
  and estimand remain unchanged.

Construction fails if source sets are not nested, a derangement has a fixed
point, a selected label multiset changes, the 2,048 permutation does not match
the frozen null-source hash, or the rebuilt cell audit differs.

## Estimand

For each realization, source mass, and backbone, use `Q=-nMSE` and

`I_MC = Q11-Q10-Q01+Q00`.

The six family x backbone strata remain fixed. Inference resamples the 20
independent realizations within each stratum (10,000 bootstrap replicates,
seed 20260820).

## Frozen adjudication

Two gates separate onset from amplification.

- **B1, low-mass conflict:** at 128 source rows, mean `I_MC<0` and its bootstrap
  CI95 upper bound is below zero in all six strata.
- **B2, mass amplification:** for every realization, regress its three I values
  on `log2(n_source)`. The mean slope must be negative and its bootstrap CI95
  upper bound below zero in all six strata.

Interpretation is fixed:

| B1 | B2 | interpretation |
|---|---|---|
| pass | pass | conflict is present by 128 rows and is amplified by source mass |
| pass | fail | conflict is present by 128 rows; mass amplification is unconfirmed |
| fail | pass | harm emerges with source mass; the 2,048:32 regime materially matters |
| fail | fail | the mass-versus-collision distinction remains unresolved |

Failure of B2 is not evidence of equivalence or flatness. Report all three
curves, `I(2048)-I(128)`, and construction audits regardless of verdict.

Runner: `scripts/run_crta_v3_mcr_null_source_mass_ladder_v1.py`.  
Adjudicator: `scripts/summarize_crta_v3_mcr_null_source_mass_ladder_v1.py`.
