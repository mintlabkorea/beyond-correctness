# Non-semantic rank-alignment audit — results v1

Primary support-only full-dose strata with a separated absorbed gap: **2/6**.
Primary strata retaining separated utility conditional on rank alignment: **6/6**.

## Primary support-only results at K=32 and d=8

| Learner | Family | U_raw | U_rank | C_rank | A_rank | D_rank | G |
|---|---|---:|---:|---:|---:|---:|---:|
| XGB | additive | +0.2589 [+0.2259, +0.2915] | +0.2749 [+0.1977, +0.3567] | -0.0161 [-0.0983, +0.0625] | -0.0590 [-0.1400, +0.0173] | -0.0429 [-0.0592, -0.0300] | +0.3178 [+0.2386, +0.3997] |
| XGB | pairwise | +0.2594 [+0.2087, +0.3127] | +0.1687 [+0.1024, +0.2419] | +0.0907 [+0.0173, +0.1618] | +0.0370 [-0.0365, +0.1090] | -0.0537 [-0.0674, -0.0411] | +0.2224 [+0.1590, +0.2931] |
| XGB | sparse | +0.2596 [+0.2050, +0.3187] | +0.2412 [+0.1340, +0.3599] | +0.0184 [-0.0827, +0.1096] | -0.0151 [-0.1129, +0.0740] | -0.0336 [-0.0443, -0.0233] | +0.2747 [+0.1669, +0.3921] |
| HISTGB | additive | +0.2574 [+0.2252, +0.2911] | +0.2780 [+0.1969, +0.3628] | -0.0207 [-0.1062, +0.0585] | -0.0643 [-0.1476, +0.0119] | -0.0436 [-0.0604, -0.0298] | +0.3217 [+0.2418, +0.4070] |
| HISTGB | pairwise | +0.2643 [+0.2110, +0.3201] | +0.1666 [+0.1027, +0.2397] | +0.0977 [+0.0166, +0.1764] | +0.0446 [-0.0337, +0.1241] | -0.0531 [-0.0691, -0.0375] | +0.2197 [+0.1551, +0.2907] |
| HISTGB | sparse | +0.2628 [+0.2074, +0.3212] | +0.2405 [+0.1330, +0.3560] | +0.0223 [-0.0749, +0.1130] | -0.0164 [-0.1123, +0.0691] | -0.0387 [-0.0505, -0.0268] | +0.2792 [+0.1742, +0.3948] |

`G` is an alternative-baseline performance gap, not semantic utility.
Family-resolved dose curves, transductive sensitivity, and XGBoost K=512 results are retained in `SUMMARY_V1.json` and the CSV files.
