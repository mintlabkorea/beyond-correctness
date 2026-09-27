# MxC source-informativeness ladder: frozen adjudication

Date: 2026-08-20  
Pre-registration: `iclr_latex_v3/MCR_SOURCE_INFORMATIVENESS_LADDER_PREREGISTRATION_V1.md`

## Verdict

The prospective internal-dose test **passes P1 in all six fixed strata**.
The negative α=1 endpoint is not a failed null rewritten as success; it is the
previously quarantined endpoint of a newly registered five-point mechanism
curve.

| family | backbone | mean realization Spearman | bootstrap CI95 | mean I_MC at α=0/.25/.50/.75/1 |
|---|---|---:|---:|---|
| additive | XGBoost | -0.960 | [-0.980, -0.940] | +.419 / +.337 / +.222 / +.061 / -.043 |
| additive | HistGB | -0.955 | [-0.990, -0.910] | +.420 / +.321 / +.220 / +.087 / -.038 |
| pairwise | XGBoost | -0.895 | [-0.965, -0.795] | +.370 / +.246 / +.179 / +.077 / -.062 |
| pairwise | HistGB | -0.910 | [-0.975, -0.820] | +.370 / +.257 / +.176 / +.071 / -.066 |
| sparse | XGBoost | -0.910 | [-0.970, -0.820] | +.400 / +.322 / +.163 / +.083 / -.070 |
| sparse | HistGB | -0.925 | [-0.985, -0.850] | +.404 / +.310 / +.168 / +.069 / -.068 |

Thus MxC is not a direction-free benefit of alignment. As the source-label
signal is progressively destroyed while its marginal label distribution is
held fixed, the interaction declines monotonically; near complete corruption,
alignment changes from beneficial to harmful. This supports the bounded claim
that M and C transmit upstream content, including error, rather than merely
adding an invariant architectural bonus.

## Crossing and conditional B decision

All six strata first cross from positive to negative only in `[0.75,1.00]`.
The pre-frozen decision rule therefore **triggers the source-mass ladder B**,
even though P1 itself passes. B must distinguish whether the α=1 negative
interaction grows with the amount of corrupt source data or is already present
once conflicting aligned content reaches the target region.

## Construction audit

- Complete internal grid: 3 families x 20 realizations = 60 cells.
- New doses: α=.25/.50/.75; α=0 and α=1 were read from frozen results.
- Every partial permutation was bijective, preserved the exact source-label
  multiset, and had nested corrupted-row sets.
- Maximum moved-count deviation from `round(α*2048)` was one row.
- One provenance tuple across all cells.

The maximum recorded marginal absolute feature--label correlation across the
partial doses is `0.350`; it is reported as an audit quantity, not used for
selection or adjudication.
