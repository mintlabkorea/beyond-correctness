# A5. MLP absolute nMSE audit

## Result

The intended `m1c1rf` cell is not degraded for MLP. Across the six family×K strata, MLP intended nMSE is 0.023–0.030 lower than the matched XGB/HistGB value, and each paired CI excludes zero. Representative means are:

| Family | K | XGB intended | HistGB intended | MLP intended |
|---|---:|---:|---:|---:|
| Additive | 32 | 0.721 | 0.719 | 0.695 |
| Pairwise | 32 | 0.710 | 0.710 | 0.681 |
| Sparse | 32 | 0.731 | 0.730 | 0.707 |
| Additive | 512 | 0.712 | 0.711 | 0.682 |
| Pairwise | 512 | 0.703 | 0.703 | 0.673 |
| Sparse | 512 | 0.721 | 0.720 | 0.691 |

The larger MLP contrasts arise mostly because its incomplete/wrong M×C cells are worse, not because its intended cell fails. At K=32, for example, MLP `m0c1rf` is 1.500–1.595 versus 1.012–1.068 for trees, while MLP `m1c0rf` is 1.359–1.377 versus 1.165–1.253. Correspondingly, MLP measurement contrasts are 0.792–0.915 versus 0.281–0.359 for trees.

All learner×family×K measurement, correspondence, and M×C interaction means are positive with 95% CIs above zero in this reaggregation. Exact arm distributions, contrast intervals, and paired MLP-minus-tree comparisons are in the CSV files.

Recommended description: **cross-model replication**, qualified as qualitative rather than equal-effect-size replication. “Learner-coverage stress test” is not the best primary label because the intended MLP cell is comparable to, and slightly better than, the tree intended cells. The magnitude of the decomposition is nevertheless learner-dependent because MLP is substantially more damaged in the missing/wrong control cells.

## Reproduction

```bash
python reanalysis_20260903/A5_mlp_absolute/analyze_mlp_absolute.py
```

Outputs: `mlp_absolute_nmse.csv`, `contrasts.csv`, `learner_comparisons.csv`, and `summary.json`. The MLP parent arm means reproduce exactly, and tree M×C interaction means reproduce to floating-point precision.

Primary sources: `experiments/crta_v3_mcr_factorial_semisynth_v1/primary/`, `experiments/crta_v3_mcr_factorial_mlp_v1/`, and `scripts/summarize_crta_v3_mcr_factorial_mlp_v1.py`.
