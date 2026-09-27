# Null-source mass ladder B: frozen adjudication

Date: 2026-08-20  
Pre-registration: `iclr_latex_v3/MCR_NULL_SOURCE_MASS_LADDER_PREREGISTRATION_V1.md`

## Verdict

Neither intersection gate passes, so the registered classification is
**mass-versus-collision unresolved**.

- B1 (negative I_MC at 128 rows in all six strata): failed. Sparse XGBoost
  and HistGB pass individually; additive and pairwise means are negative but
  their realization-bootstrap CIs include zero.
- B2 (negative log2-mass slope in all six strata): failed. No individual
  stratum has a slope CI wholly below zero.

Failure of B2 is not an equivalence result. It does, however, provide no
support for the simple claim that the α=1 interaction becomes increasingly
negative in proportion to corrupt source mass.

## Curves

| family | backbone | I_MC(128) | I_MC(512) | I_MC(2048) | slope CI95 |
|---|---|---:|---:|---:|---:|
| additive | XGBoost | -.084 | -.007 | -.043 | [-.014, +.034] |
| additive | HistGB | -.084 | -.002 | -.038 | [-.013, +.037] |
| pairwise | XGBoost | -.041 | -.086 | -.062 | [-.018, +.008] |
| pairwise | HistGB | -.042 | -.077 | -.066 | [-.020, +.008] |
| sparse | XGBoost | -.084 | -.093 | -.070 | [-.010, +.017] |
| sparse | HistGB | -.084 | -.084 | -.068 | [-.010, +.017] |

All six point estimates are already negative at 128 source rows (a 4:1
source-to-target-support ratio), but only sparse separates there:

- sparse XGBoost CI95 `[-.126,-.042]`;
- sparse HistGB CI95 `[-.124,-.043]`.

For additive and pairwise, the 128-row upper bounds are `+.013` to `+.024`.
Likewise, `I(2048)-I(128)` includes zero in all strata. The curves are
non-monotone and family-dependent rather than mass-proportional.

## Interpretation boundary

This directly weakens the objection that the original negative interaction is
only the mechanical consequence of placing 2,048 noise rows beside 32 target
rows: the negative point-estimate sign appears at 128 rows in every stratum and
there is no registered evidence that adding mass makes it more negative.
However, because B1 required all six CIs to exclude zero and only sparse does,
the stronger statement that low-mass aligned noise reliably causes harm across
families is not licensed.

Together with the α ladder, the supported claim is bounded: source-label
informativeness controls the sign of MxC near complete corruption, while the
size of the negative endpoint is not explained by a simple source-mass dose.
The detailed collision geometry remains family-dependent.

## Construction audit

- Complete grid: 60 cells, with new masses 128 and 512; frozen 2,048 endpoints
  reused without refitting.
- Source position sets were nested; every subset derangement had zero fixed
  points and preserved its exact label multiset.
- The 2,048 permutation hash matched the frozen null-source cell in every
  realization.
- One provenance tuple; maximum recorded deranged marginal feature-label
  correlation `0.217`.
