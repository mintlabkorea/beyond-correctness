# Pre-registration: exhaustive N5 finite-lesion calibration, v1

Declared 2026-08-20 before any confirmatory N5-exhaustive fit. The original
MCR grid drew two exchangeable type-preserving correspondence lesions per
cell. N5 compared them and one family-level draw differed by about 0.1 nMSE.
The exact slot-swap diagnostic ruled out implementation asymmetry, but two
draws cannot estimate the finite-lesion variance.

## Frozen design

- Reuse byte-identical MCR primary cells: three mechanism families, 20
  realizations, K=32, correct M and R, real NHANES panels.
- The four ordinal and four continuous features are independently deranged.
  There are `D4 x D4 = 9 x 9 = 81` admissible lesions; enumerate all 81.
- Fit XGBoost and HistGB. The correct correspondence is fit once per cell;
  every lesion uses the same rows, outcomes, model seed, weights and R.
- Metric is Q = -nMSE. Independent units remain the 20 realizations within
  each fixed family. The two backbones are replications, not extra units.

## Frozen adjudication

P1 is `Q(correct) - mean_81 Q(lesion)`. Within each family x backbone,
realization bootstrap (10,000, deterministic seed), separation requires
mean > 0, CI95 > 0 and win >= .60. The global claim requires all three
families and both backbones.

For calibration, simulate 100,000 experiments that select two different
lesions per realization and average their signed difference. Report signed
.5/2.5/97.5/99.5 percentiles, absolute 95/99 percentiles, and the two-sided
tail probability of the original frozen N5 draw. The original equivalence
margin remains 0.05 nMSE; it is not changed after seeing this distribution.
Failure of that margin does not invalidate P2 correspondence; it means the
two-draw null was under-calibrated and must be described as such.

Runner: `scripts/run_crta_v3_mcr_n5_exhaustive_v1.py`.
Adjudicator: `scripts/summarize_crta_v3_mcr_n5_exhaustive_v1.py`.

