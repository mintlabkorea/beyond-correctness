# W3 paired reference decomposition

Original point ranges cross zero in 4/9 datasets. Resolved sign crossings: 1/9 with pointwise percentile intervals; 1/9 with simultaneous 24-reference bands; 1/9 with simultaneous 216-utility bands.

Reference heterogeneity survives Bonferroni adjustment over nine datasets in 9/9.

| Dataset | Observed SD | Corrected ref SD | Evaluation SE (RMS) | SD ratio | Spread noise % | Resolved crossing (24 / 216) | Heterogeneity adjusted p |
|---|---:|---:|---:|---:|---:|---|---:|
| bank | 0.03560 | 0.03555 | 0.00567 | 6.27 | 0.30 | False / False | 0.00180 |
| blood | 0.03867 | 0.03479 | 0.04571 | 0.76 | 19.07 | False / False | 0.02699 |
| calhousing | 0.03062 | 0.03051 | 0.00645 | 4.73 | 0.76 | False / False | 0.00180 |
| car | 0.02079 | 0.02017 | 0.01587 | 1.27 | 5.87 | False / False | 0.00180 |
| creditg | 0.02016 | 0.01853 | 0.02237 | 0.83 | 15.52 | False / False | 0.00180 |
| diabetes | 0.03511 | 0.03124 | 0.03193 | 0.98 | 20.83 | False / False | 0.00360 |
| heart | 0.04267 | 0.04216 | 0.01708 | 2.47 | 2.35 | False / False | 0.00180 |
| income | 0.01074 | 0.01070 | 0.00290 | 3.68 | 0.86 | False / False | 0.00180 |
| jungle | 0.02460 | 0.02453 | 0.00376 | 6.53 | 0.53 | True / True | 0.00180 |

SD ratio compares corrected finite-library reference SD with RMS within-reference utility SE. Spread noise % uses the covariance projected across references, not the full within-reference variance. All variance/ratio summaries are point estimates.

The simultaneous bands protect reference selection when asserting opposite utility signs. Unequal reference utilities and resolved opposite signs are different claims.

The 5,000 paired exponential-weight draws preserve overlapping-row and shared-intended-score dependence. Class-stratified positive-weight union resampling conditions on the released checkpoint and evaluation memberships. It does not assess training randomness. The centered-bootstrap heterogeneity p-values are approximate, with minimum Monte Carlo p = 1/5001. No reference or dataset was dropped. The v1 multinomial bootstrap stopped on an absent Car class; v2 uses normalized exponential weights for all nine datasets.

Protocol SHA256: `7cd86ff8d54808c73d598e5728891c116d267861923d9589741f689f5a99886b`. Runner SHA256: `536c615d3b2de2e1f0188aa6298826cac5065ad0f3ce587a0a4d7f2bfb676420`.

Methodological background: correlated AUROC estimates require covariance-aware comparison ([DeLong et al., 1988](https://pubmed.ncbi.nlm.nih.gov/3203132/)); this analysis uses exact paired resampling rather than fitting a random-effects reference population.

Elapsed analysis time: 43.0 seconds; GPU use: none.
