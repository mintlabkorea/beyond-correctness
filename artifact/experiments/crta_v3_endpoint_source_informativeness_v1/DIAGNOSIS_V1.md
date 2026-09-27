# Endpoint source-informativeness prediction: frozen adjudication

Date: 2026-08-20  
Pre-registration: `iclr_latex_v3/ENDPOINT_SOURCE_INFORMATIVENESS_PREREGISTRATION_V1.md`

## Verdict

The prospective primary prediction **failed**.

- Endpoint-cluster Spearman `rho(S_e, I_e*) = -0.0303`.
- Exact one-sided permutation `p = 0.5408` (`1,962,498 / 3,628,800`).
- Diabetes-excluded rho is `-0.4167`, also opposite to the registered sign.
- Directional sensitivity is heterogeneous: NHANES->KNHANES `rho=+0.3455`,
  KNHANES->NHANES `rho=-0.1394`.

The null-source sign reversal therefore does **not** make the successful
real-data prediction that endpoint-level source-only AUROC should order the
existing MxC interactions. Endpoint heterogeneity remains a limitation, and
no direction or endpoint subset is promoted as confirmation.

## Endpoint decomposition

| endpoint | source-only AUROC - 0.5 | corrected MxC interaction |
|---|---:|---:|
| angina | +0.2350 | +0.0089 |
| arthritis | +0.2808 | -0.0141 |
| asthma | +0.0426 | +0.0211 |
| cancer | +0.1914 | +0.0262 |
| current smoking | +0.2002 | +0.0114 |
| diabetes | +0.4381 | +0.1799 |
| heart attack | +0.2527 | +0.0440 |
| hypertension | +0.3375 | -0.0202 |
| kidney disease | +0.2529 | +0.0368 |
| stroke | +0.2914 | +0.0175 |

Diabetes is consistent with the prediction, but arthritis and hypertension
are counterexamples: each source-only model is informative while its corrected
interaction is negative. Removing diabetes makes the rank relation more
negative rather than merely less precise.

## Registered secondary diagnostic

The target-only marginal-source-utility proxy gives positive cross-seed rank
correlations:

- proxy seeds 50--54 vs interaction seeds 55--59: `rho=+0.4545`;
- proxy seeds 55--59 vs interaction seeds 50--54: `rho=+0.3333`;
- arithmetic mean: `+0.3939`.

This is descriptive only. The proxy contains `a11*`, as does `I*`, so the
part--whole coupling prevents it from serving as an independent confirmation.
The pattern suggests that source-only discriminative ability is too coarse:
compatibility with target support and the particular M/C lesions may matter,
but that interpretation is not established here.

## Execution audit

- Complete grid: 10 endpoints x 2 directions x 10 seeds = 200 cells.
- Two new fits per cell; one provenance tuple across all cells.
- Eight scarce-support cells had a single observed target-support class. They
  were retained and fit without redraw or exclusion, exactly as fixed by
  `ENDPOINT_SOURCE_INFORMATIVENESS_EXECUTION_ERRATUM_V1.md`.
- The earlier four-arm endpoint outcomes were disclosed as observed before
  this study.

The original null-source failure remains failed and quarantined. This result
does not alter the semi-synthetic sign reversal; it limits the attempted bridge
from that mechanism to real endpoint heterogeneity.
