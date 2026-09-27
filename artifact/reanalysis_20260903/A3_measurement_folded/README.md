# A3. Measurement-panel orientation sensitivity

## Result

AUROC is folded cellwise as `max(A, 1-A)` before computing each contrast.

| Panel | Scale | Intended − wrong | Intended − reference |
|---|---|---:|---:|
| Focused 3 endpoints | Raw | 0.2915 [0.1448, 0.4314] | 0.3845 [0.2025, 0.5530] |
| Focused 3 endpoints | Folded | 0.1630 [0.0728, 0.2495] | 0.2757 [0.0900, 0.3846] |
| 10 endpoints × 2 directions | Raw | 0.2494 [0.1824, 0.3087] | 0.1973 [0.1102, 0.2939] |
| 10 endpoints × 2 directions | Folded | 0.1335 [0.0944, 0.1703] | 0.1560 [0.0893, 0.2249] |

The focused panel resamples endpoints and then seeds (`n=3`, 30 cells). The extension resamples endpoint clusters, keeps both directions paired, and resamples finite seeds within direction (`n=10`; 187 finite intended/wrong pairs and 200 intended/reference pairs). Each interval uses 10,000 draws and the parent hierarchy.

Both contrasts remain positive with CIs above zero after folding. In the focused panel, folding reduces the content estimate by 44.1% and utility by 28.3%. In the extension, the reductions are 46.5% and 21.0%. Orientation correction therefore reduces magnitude but does not remove separation.

The focused three-endpoint result remains useful as focused evidence and a mechanism illustration, but `n=3` is too narrow to carry a generality claim alone; the 10-endpoint extension is the broader sensitivity. The 10-endpoint intended/wrong result remains descriptive because its prespecified construction gate fails: `cancer_history/kn2nh` has only 4/10 finite pairs, below the required 8/10. Folding cannot repair that gate.

## Reproduction

```bash
python reanalysis_20260903/A3_measurement_folded/analyze_measurement_folded.py
```

Outputs: `measurement_folded_sensitivity.csv`, `endpoint_arm_aurocs.csv`, `endpoint_contrasts.csv`, and `summary.json`. The endpoint file reports raw and folded intended/reference/wrong AUROC means and finite counts. Raw pooled point estimates reproduce the two parent summaries to floating-point precision.

Primary sources: `experiments/crta_v3_survey_label_panel_v1/`, the two `crta_v3_survey_label_panel_endpoint_expansion_*_v1/` roots, and their parent summarizers.
