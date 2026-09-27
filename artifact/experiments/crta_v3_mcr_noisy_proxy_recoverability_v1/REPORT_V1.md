# Fixed-width noisy-proxy recoverability ladder

Status: **complete**

The proxy phase was completed and cryptographically sealed before the utility phase. All structural gates passed in all 40 cells.

| Family | Backbone | K | Mean within-realization Spearman | 95% CI | Supports graded relation? |
|---|---|---:|---:|---:|:---:|
| pairwise | xgb | 32 | +0.984 | [+0.971, +0.995] | yes |
| pairwise | xgb | 512 | +0.989 | [+0.982, +0.996] | yes |
| pairwise | histgb | 32 | +0.980 | [+0.964, +0.993] | yes |
| pairwise | histgb | 512 | +0.984 | [+0.977, +0.991] | yes |
| sparse | xgb | 32 | +0.989 | [+0.980, +0.996] | yes |
| sparse | xgb | 512 | +0.993 | [+0.986, +0.998] | yes |
| sparse | histgb | 32 | +0.995 | [+0.989, +1.000] | yes |
| sparse | histgb | 512 | +0.986 | [+0.979, +0.993] | yes |

Global all-eight-strata verdict: **pass**.

Scope: controlled pairwise/sparse relation-value setting only; this does not override the previously reported real-data non-replication.
