# Pre-registration: M×C source-informativeness ladder, v1

Drafted 2026-08-20 while the separate real-endpoint C extension was running;
to be freeze-committed before any internal α cell is fit.

## Prior observation disclosure

The two endpoints of this ladder have already been observed:

- α=0: the original signal-bearing MCR factorial, positive `I_MC`;
- α=1: the no-fixed-point source-label derangement, negative mean `I_MC` and
  failed 6/6 equivalence.

This extension does not re-register those endpoints as new evidence. It
prospectively tests only the three internal levels, the five-point monotone
trend, and the sign-crossing interval. The original null-source failure and
`DIAGNOSIS_V1.md` quarantine remain authoritative and cannot be rewritten as a
passed null.

## Frozen design

- Reuse the exact 60 original primary cells: three fixed families × 20
  realizations, K=32, XGBoost and HistGB, free-R M/C arms
  `m1c1rf`, `m1c0rf`, `m0c1rf`, `m0c0rf`.
- Internal source-label corruption levels are α ∈ `{0.25,0.50,0.75}`.
- α=0 and α=1 are read from the frozen original and null-source results; they
  are not refit.
- Target support/query rows and labels, source/target features and missingness,
  M/C lesions, learner settings, and unweighted fitting remain unchanged.

## Nested, marginal-preserving partial permutation

For each family×realization, reconstruct the exact α=1 derangement used in
`run_crta_v3_mcr_null_source_v1.py`. Decompose that permutation into cycles and
traverse a deterministic outcome-blind cycle order. At each internal α, activate
complete cycles and at most one cycle prefix so that the number of non-fixed
source assignments is within one row of `round(α×2048)`.

Every partial map must be a bijection, preserve the exact source-label
multiset, and have a corrupted-row set nested within the next dose. α=1 must be
byte-identical to the existing full derangement. Report realized moved-row
fractions and shuffled feature–label correlations for every cell. A cell fails
construction if the moved-count error exceeds one, the map is not bijective,
the label multiset changes, or nestedness fails.

## Estimand and adjudication

For each realization and α, `Q=-nMSE` and

`I_MC(α)=Q11-Q10-Q01+Q00`.

P1 is the realization-level Spearman correlation between α and `I_MC(α)` over
all five levels. For every fixed family×backbone stratum:

- mean Spearman rho must be negative;
- a 10,000-replicate realization bootstrap CI95 (seed 20260820) must lie below
  zero.

The primary verdict is the intersection of all six strata. Report the mean
five-point curve, all adjacent changes, and the first adjacent α interval whose
mean endpoints have opposite signs. The crossing interval is descriptive; no
continuous threshold is claimed from five grid points.

## Pre-frozen decision rule for the optional mass ladder B

Run B after this adjudication if either condition holds:

1. P1 fails in any stratum; or
2. at least four of six strata first cross from positive to negative only in
   the final `[0.75,1.00]` interval.

Otherwise B is deferred as nonessential. This rule is fixed before internal α
results are observed.

Runner: `scripts/run_crta_v3_mcr_source_informativeness_ladder_v1.py`.
Adjudicator: `scripts/summarize_crta_v3_mcr_source_informativeness_ladder_v1.py`.
