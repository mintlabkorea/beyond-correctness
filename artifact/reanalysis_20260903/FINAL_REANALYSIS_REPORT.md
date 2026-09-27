# Final reanalysis report

## 1. Executive summary

All feasible analyses were completed from existing artifacts without new predictive-model fitting. `main.tex` and `appendix.tex` were not edited; their SHA-256 hashes are unchanged.

The high-level conclusions are:

1. TabLLM macro utility is positive under both control constructions, and their macro difference is not separated from zero. Dataset-level reference sensitivity is substantial and heterogeneous.
2. The 10-endpoint M×C interaction remains positive after cellwise AUROC folding, although folding significantly reduces the pooled level, mainly in KN→NH.
3. Measurement intended/wrong and intended/reference contrasts remain positive after folding in both the focused and expanded panels. The expanded intended/wrong result remains descriptive because the pre-existing 8/10 coverage gate fails.
4. Reconstruction has higher point-estimate LORO R² than removed fraction in all eight strata, but none of the paired delta-R² CIs excludes zero. The conditional reconstruction slope remains negative with CI below zero in all eight strata.
5. MLP intended-cell absolute nMSE is slightly better, not worse, than matched tree performance. The larger MLP decomposition effects are driven by worse missing/wrong control cells. The defensible label is qualitative cross-model replication, not equal-effect-size replication.
6. No retained provenance item supplies an independently verifiable external pre-execution timestamp. The strongest evidence is either local ordering (B) or exact hash linkage without an independent run timestamp (C).

## 2. A1 TabLLM reference/control sensitivity

| Estimand | Estimate [95% CI] | Inference unit | Source | Provenance | Claim effect |
|---|---:|---|---|---|---|
| `U_pub = S - Rpub` | 0.0800 [0.0047, 0.1539] | 9-dataset bootstrap over paired example-level influence draws | four-arm prediction artifacts | C | supports positive macro utility under published control |
| `U_anon = S - Ranon` | 0.0884 [0.0323, 0.1540] | same | same | C | supports positive macro utility under stable-anonymous control |
| `U_anon - U_pub` | 0.0084 [-0.0469, 0.0600] | same paired bootstrap | same | C | qualifies rather than weakens: no macro control-choice difference detected |

The dataset-level `Delta_ref = U_anon-U_pub` CI is positive for bank, calhousing, creditg, and diabetes; negative for heart and jungle; and unresolved for blood, car, and income. Control construction therefore matters locally even though its macro average is unresolved. This numerical analysis does not declare the two controls equally admissible; `Ranon` remains the format-matched design reference in the existing rationale.

Full results and per-artifact hashes: `A1_tabllm_reference/tabllm_reference_sensitivity.csv` and `tabllm_reference_sensitivity_macro.json`.

## 3. A2 raw versus folded interaction

| Scope | Raw | Folded | Raw − folded | Inference unit | Provenance | Claim effect |
|---|---:|---:|---:|---|---|---|
| Pooled | 0.0472 [0.0178, 0.0861] | 0.0312 [0.0082, 0.0582] | 0.0161 [0.0003, 0.0372] | 20 endpoint-direction units, seeds within unit | B | strengthens orientation robustness; qualifies magnitude |
| NH→KN | 0.0200 [-0.0054, 0.0558] | 0.0200 [-0.0054, 0.0558] | 0.0000 [-0.0022, 0.0022] | 10 endpoint units | B | unresolved within direction |
| KN→NH | 0.0744 [0.0308, 0.1415] | 0.0423 [0.0062, 0.0853] | 0.0321 [0.0012, 0.0709] | 10 endpoint units | B | positive after folding, but materially attenuated |

Raw and folded values use identical bootstrap resamples. This result concerns interaction level only. It does not change the failed raw attenuation-ladder result.

## 4. A3 measurement orientation sensitivity

| Panel | Scale | Intended − wrong | Intended − reference | Inference unit | Provenance | Claim effect |
|---|---|---:|---:|---|---|---|
| Focused 3 endpoint | Raw | 0.2915 [0.1448, 0.4314] | 0.3845 [0.2025, 0.5530] | endpoints then seeds, 30 cells | B | parent result reproduced |
| Focused 3 endpoint | Folded | 0.1630 [0.0728, 0.2495] | 0.2757 [0.0900, 0.3846] | same hierarchy | B | strengthens orientation robustness |
| 10 endpoint bidirectional | Raw | 0.2494 [0.1824, 0.3087] | 0.1973 [0.1102, 0.2939] | 10 endpoint clusters, directions paired, finite seeds | B | intended/wrong remains descriptive |
| 10 endpoint bidirectional | Folded | 0.1335 [0.0944, 0.1703] | 0.1560 [0.0893, 0.2249] | same hierarchy | B | strengthens orientation robustness but cannot repair coverage |

The expanded intended/wrong contrast uses 187 finite pairs; utility uses all 200. `cancer_history/kn2nh` has 4/10 finite intended/wrong pairs and fails the exact 8/10 construction gate. Therefore an interval above zero does not create an eligible primary verdict.

## 5. A4 reconstruction incremental R²

| Family | Learner/K | Delta LORO R² [95% CI] | Conditional reconstruction slope [95% CI] |
|---|---|---:|---:|
| Pairwise | HistGB/32 | 0.0096 [-0.0285, 0.0415] | -0.1761 [-0.3137, -0.0595] |
| Pairwise | XGB/32 | 0.0103 [-0.0259, 0.0401] | -0.1770 [-0.3114, -0.0668] |
| Pairwise | HistGB/512 | 0.0171 [-0.0101, 0.0407] | -0.2151 [-0.3298, -0.1026] |
| Pairwise | XGB/512 | 0.0195 [-0.0061, 0.0419] | -0.2214 [-0.3290, -0.1193] |
| Sparse | HistGB/32 | 0.0364 [-0.0544, 0.1318] | -0.1728 [-0.2813, -0.0688] |
| Sparse | XGB/32 | 0.0356 [-0.0534, 0.1305] | -0.1728 [-0.2826, -0.0674] |
| Sparse | HistGB/512 | 0.0612 [-0.0432, 0.1711] | -0.1988 [-0.3118, -0.0855] |
| Sparse | XGB/512 | 0.0601 [-0.0360, 0.1637] | -0.1990 [-0.3082, -0.0894] |

Inference unit is the realization cluster (`n=20` in each stratum; 10,000 draws). Provenance category is C. The pointwise ordering strengthens the descriptive comparison, but the paired delta CIs weaken any inferential claim of superior new-realization prediction. The conditional regression supports an incremental within-benchmark association after treating removed fraction as categorical.

This result is limited to supplied computed relation values in the controlled benchmark. It does not establish a general outcome-free predictor of semantic utility.

## 6. A5 MLP absolute performance

MLP intended `m1c1rf` nMSE is lower than both tree values in all family×K strata. The paired differences are:

| Family/K | MLP − XGB [95% CI] | MLP − HistGB [95% CI] |
|---|---:|---:|
| Additive/32 | -0.0261 [-0.0336, -0.0192] | -0.0237 [-0.0312, -0.0168] |
| Pairwise/32 | -0.0299 [-0.0350, -0.0245] | -0.0290 [-0.0340, -0.0238] |
| Sparse/32 | -0.0238 [-0.0298, -0.0171] | -0.0233 [-0.0301, -0.0160] |
| Additive/512 | -0.0292 [-0.0374, -0.0216] | -0.0290 [-0.0376, -0.0210] |
| Pairwise/512 | -0.0295 [-0.0359, -0.0229] | -0.0304 [-0.0363, -0.0247] |
| Sparse/512 | -0.0304 [-0.0359, -0.0249] | -0.0293 [-0.0346, -0.0239] |

Inference uses 20 paired realizations within each fixed stratum; provenance category is C. At K=32, MLP intended nMSE is 0.681–0.707 versus 0.710–0.731 for trees. Its `m0c1rf` is much worse, 1.500–1.595 versus 1.012–1.068, which inflates measurement contrasts to 0.792–0.915 versus 0.281–0.359. Thus the intended predictor is not a coverage failure, but the decomposition magnitude is learner-dependent.

Claim effect: supports qualitative cross-model replication of positive measurement, correspondence, and interaction contrasts. It does not support equal-strength effect-size replication.

## 7. A6 provenance audit

The exact coverage rule is present at lines 51–54 of the committed extension protocol and implemented by `MIN_COVERAGE=8` plus the finite-pair count in the adjudicator. The sole failing unit is `cancer_history/kn2nh = 4/10`.

| Analysis group | Evidence | Class |
|---|---|---|
| A1 TabLLM | exact protocol hash embedded in metrics; protocol currently untracked; local timing only | C |
| A2 stage expansion | committed protocol, but no embedded manifest hash and run ordering relies on local mtime | B |
| A3 focused panel | committed protocol and local logs; no embedded manifest hash | B |
| A3 10-endpoint extension | committed protocol; local mtime establishes ordering; no retained push/scheduler time | B |
| A4 proxy | analysis script hash embedded; explicitly post-result; no pre-execution decision manifest | C |
| A4 source ladder | exact protocol hash embedded in metrics/logs; no independent run timestamp | C |
| A5 trees | historical preregistration hash embedded in metrics; local run time only | C |
| A5 MLP | exact preregistration hash embedded in metrics/logs; local run time only | C |

No item is category A. A present-day public deposit would improve reproducibility but would not retrospectively establish preregistration.

## 8. Manuscript implications

No manuscript change was made. If these results are later considered for incorporation, the evidence supports the following boundaries:

- TabLLM: report macro robustness to two control constructions and dataset heterogeneity; do not call both controls equally admissible merely because the macro difference includes zero.
- M×C: folding preserves a positive pooled interaction but reduces it; keep the failed raw attenuation ladder separate.
- Measurement: folding strengthens orientation robustness, but the 10-endpoint intended/wrong analysis stays descriptive under the exact coverage gate.
- Reconstruction: retain the negative conditional slopes; describe the higher LORO R² as pointwise, because paired delta intervals all include zero.
- MLP: “qualitative cross-model replication” is accurate; “equal-strength replication” is not.
- Provenance: use “hash-keyed local manifests” where supported and continue stating that no external public registration/timestamp existed.

## 9. Analysis requiring new fitting

One requested extension could not be completed: a support-ladder comparison between `Rpub` and `Ranon`. Matching `Rpub` predictions were not retained at the `Ranon` support rungs. Following the task constraint, no refit was started.

All other requested workstreams were completed by reaggregation of existing artifacts. Reproduction commands and exact machine-readable outputs are documented in each workstream README.
