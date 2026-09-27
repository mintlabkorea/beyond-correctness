# A4. Incremental LORO R² of reconstruction

## Result

The point estimate `LORO R²(reconstruction) - LORO R²(removed fraction)` is positive in all eight controlled strata, but every paired realization-bootstrap CI includes zero.

| Family | Learner | K | Reconstruction R² | Fraction R² | Delta R² [95% CI] |
|---|---|---:|---:|---:|---:|
| Pairwise | HistGB | 32 | 0.899 | 0.889 | 0.010 [-0.029, 0.042] |
| Pairwise | XGB | 32 | 0.897 | 0.886 | 0.010 [-0.026, 0.040] |
| Pairwise | HistGB | 512 | 0.903 | 0.886 | 0.017 [-0.010, 0.041] |
| Pairwise | XGB | 512 | 0.905 | 0.885 | 0.019 [-0.006, 0.042] |
| Sparse | HistGB | 32 | 0.812 | 0.775 | 0.036 [-0.054, 0.132] |
| Sparse | XGB | 32 | 0.809 | 0.773 | 0.036 [-0.053, 0.130] |
| Sparse | HistGB | 512 | 0.820 | 0.758 | 0.061 [-0.043, 0.171] |
| Sparse | XGB | 512 | 0.825 | 0.765 | 0.060 [-0.036, 0.164] |

The paired bootstrap resamples 20 realization blocks and recomputes both R² values from the same fixed leave-one-realization-out predictions. `bootstrap_deltas.csv` retains all 80,000 draws.

The conditional analysis is more stable. In `utility ~ reconstruction_R² + categorical(removed_fraction)`, all eight reconstruction slopes are negative and all cluster-bootstrap CIs exclude zero:

| Family | Learner | K | Conditional slope [95% CI] |
|---|---|---:|---:|
| Pairwise | HistGB | 32 | -0.176 [-0.314, -0.060] |
| Pairwise | XGB | 32 | -0.177 [-0.311, -0.067] |
| Pairwise | HistGB | 512 | -0.215 [-0.330, -0.103] |
| Pairwise | XGB | 512 | -0.221 [-0.329, -0.119] |
| Sparse | HistGB | 32 | -0.173 [-0.281, -0.069] |
| Sparse | XGB | 32 | -0.173 [-0.283, -0.067] |
| Sparse | HistGB | 512 | -0.199 [-0.312, -0.086] |
| Sparse | XGB | 512 | -0.199 [-0.308, -0.089] |

Delta R² is positive in every stratum, ranges from 0.0096 to 0.0612, and has no interval excluding zero. Conclusion: reconstruction has conditional signal beyond the rung category, but the stronger statement that its LORO R² is statistically higher than fraction-only R² is not established by the paired uncertainty analysis. The result remains limited to computed relation values in this controlled benchmark; it is not a general predictor of semantic utility.

## Reproduction

```bash
python reanalysis_20260903/A4_reconstruction_incremental/analyze_incremental_loro.py
```

Outputs: `reconstruction_incremental_r2.csv`, `bootstrap_deltas.csv`, `conditional_slope_bootstrap.csv`, and `summary.json`. Stored parent LORO R² values reproduce with maximum error below `2e-16`.
