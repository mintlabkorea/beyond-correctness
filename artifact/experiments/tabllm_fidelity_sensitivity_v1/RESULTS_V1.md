# W11 reproduction-fidelity sensitivity

Descriptive reanalysis of existing zero-shot results; no new predictions or inferential intervals. Manuscript unchanged.

Filter: include a dataset only when all three reproduced published-condition means (S, W, R_pub) differ from their printed published means by at most .015 AUROC. R_anon and utility never enter the filter. Means retain stored precision; published inputs are the original two-decimal printed values.

Included: car, diabetes, income, jungle. Excluded: bank, blood, calhousing, creditg, heart.

| Panel | Datasets | Macro content | Macro utility vs R_anon | Global 24-reference macro range | Span | Sign-sensitive datasets |
|---|---:|---:|---:|---|---:|---|
| full_panel | 9 | +0.112447 | +0.088370 | [+0.088370, +0.124039] | 0.035669 | 4/9 (calhousing, creditg, heart, jungle) |
| fidelity_015 | 4 | +0.216482 | +0.140687 | [+0.119741, +0.175161] | 0.055420 | 1/4 (jungle) |

## Dataset inclusion audit

| Dataset | S error | W error | R_pub error | D_j | Included |
|---|---:|---:|---:|---:|---|
| bank | 0.009695 | 0.001434 | 0.027082 | 0.027082 | False |
| blood | 0.006295 | 0.008148 | 0.034699 | 0.034699 | False |
| calhousing | 0.007616 | 0.021275 | 0.007689 | 0.021275 | False |
| car | 0.001760 | 0.010535 | 0.010245 | 0.010535 | True |
| creditg | 0.002311 | 0.021702 | 0.007492 | 0.021702 | False |
| diabetes | 0.006633 | 0.000799 | 0.002135 | 0.006633 | True |
| heart | 0.022057 | 0.017983 | 0.000910 | 0.022057 | False |
| income | 0.010433 | 0.011116 | 0.004187 | 0.011116 | True |
| jungle | 0.008273 | 0.008678 | 0.005886 | 0.008678 | True |

Subset membership was saved and hashed before the outcome calculations. The .015 threshold is inherited from the manuscript; no alternative cutoffs were tried. Global range uses index-aligned ref_00–ref_23 across the included datasets, not dataset-specific envelope extrema. Sign sensitivity requires both a negative and positive utility among the evaluated references. Counts and ranges are descriptive; no independence claim, uncertainty interval or equivalence inference is made.

Prior full-panel results were known. This is a user-specified post-result sensitivity analysis with outcome-independent filtering, not prospective preregistration. Changes under restriction also change dataset composition and cannot uniquely establish the causal contribution of reproduction error.

## Interpretation

The all-three-arms restriction retains Car, Diabetes, Income and Jungle (4/9 datasets). Canonical macro utility remains positive, increasing from +.088370 to +.140687; macro content sensitivity changes from +.112447 to +.216482. These magnitudes are not unchanged under the restriction.

Reference dependence persists: the subset's 24 global macro utilities range from +.119741 to +.175161 (span .055420), versus +.088370 to +.124039 (span .035669) on the full panel. Dataset-level sign sensitivity decreases from 4/9 to 1/4, with Jungle remaining sign-sensitive. All evaluated global macro utilities on the subset are positive, which is distinct from all dataset utilities being positive. The subset global minimum is ref_16 and maximum ref_20; the canonical ref_00 is not its minimum.

A defensible descriptive statement is: **Positive aggregate utility and variation across the evaluated references persist under the fidelity restriction, while dataset-level sign sensitivity is less frequent and the aggregate magnitudes change.** This has the positive-utility/reduced-sign-frequency pattern of the proposed Case B, but does not justify claiming unchanged magnitude or assigning reproduction error as the cause of the shift. The filter also changes dataset composition. Preserve the original 4/9 full-panel result and report 1/4 as a separate fidelity sensitivity.

Name alignment: `calhousing` in reproduced/reference artifacts maps to `california` in the published summary; `creditg` maps to `credit-g`. Published values are cross-checked against the reproduction summary's embedded printed values. The comparison is between five-split mean AUROCs, not single split values, condition-selected averages or anonymous-reference performance.
