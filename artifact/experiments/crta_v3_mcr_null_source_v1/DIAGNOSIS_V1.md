# Null-source M×C falsification diagnosis, v1

The preregistered grid verdict **fails**. None of the six fixed
family×backbone strata places its full 95% interval inside the frozen ±0.05 Q
equivalence margin, and four strata (pairwise/sparse on both backbones) are
interval-separated below zero.

| family | XGBoost I_MC^null [CI95] | HistGB I_MC^null [CI95] |
|---|---:|---:|
| additive | −0.043 [−0.093,+0.006] | −0.038 [−0.090,+0.010] |
| pairwise | −0.062 [−0.100,−0.022] | −0.066 [−0.104,−0.026] |
| sparse | −0.070 [−0.114,−0.024] | −0.068 [−0.108,−0.029] |

Construction checks pass: 60/60 cells completed under one provenance tuple,
every source-label permutation preserves the exact label multiset and has zero
fixed points, and the maximum realized absolute correlation between a shuffled
source label and a true-decoded source feature is 0.056.

## Arm-level descriptive diagnosis

Mean nMSE (`m1c1rf`, `m1c0rf`, `m0c1rf`, `m0c0rf`):

| family | XGBoost | HistGB |
|---|---|---|
| additive | 1.101, 1.036, 1.042, 1.020 | 1.099, 1.035, 1.045, 1.018 |
| pairwise | 1.111, 1.045, 1.057, 1.053 | 1.107, 1.044, 1.054, 1.058 |
| sparse | 1.113, 1.038, 1.025, 1.020 | 1.113, 1.040, 1.024, 1.019 |

With 2,048 permuted-label source rows and only 32 correctly labelled target
support rows, the correctly decoded and correctly routed source is the most
harmful arm. A plausible mechanism is that correct M+C makes source-label noise
maximally commensurate with target features, whereas either lesion partially
decouples that noise. This is an inference from the arm pattern, not a new
registered verdict.

## Consequence

Per the frozen rule, the paper's **pure routing-mechanism interpretation is
quarantined**; the failure must not be rewritten as a passed null or hidden
behind the much larger original positive interaction (+0.37–+0.42). The
original efficacy contrast remains an executed fact, and the signal-source
versus null-source sign reversal is informative, but `I_MC > 0` cannot by
itself be described as a unique signature of useful source knowledge.

Authoritative numeric artifact: `SUMMARY_V1.json`.
