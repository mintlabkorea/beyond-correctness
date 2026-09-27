# A2. Raw versus folded M×C interaction

## Result

| Scope | Raw interaction | Folded interaction | Raw − folded |
|---|---:|---:|---:|
| Pooled, 20 endpoint-direction units | 0.0472 [0.0178, 0.0861] | 0.0312 [0.0082, 0.0582] | 0.0161 [0.0003, 0.0372] |
| NH→KN, 10 units | 0.0200 [-0.0054, 0.0558] | 0.0200 [-0.0054, 0.0558] | 0.0000 [-0.0022, 0.0022] |
| KN→NH, 10 units | 0.0744 [0.0308, 0.1415] | 0.0423 [0.0062, 0.0853] | 0.0321 [0.0012, 0.0709] |

Folding is applied cellwise as `max(AUROC, 1-AUROC)` before forming the factorial interaction. The raw and folded estimates and their difference use the same endpoint-direction and within-unit seed resamples. There are 10,000 hierarchical bootstrap draws.

The pooled interaction remains positive after folding. Folding reduces its level, with the reduction concentrated in KN→NH. This strengthens the claim that a positive interaction is not solely an orientation artifact, while qualifying its magnitude.

This is an interaction-level sensitivity. It does not rescue or reinterpret the previously failed raw attenuation-ladder criterion, which is a distinct estimand.

## Reproduction

```bash
python reanalysis_20260903/A2_raw_interaction/analyze_raw_vs_folded.py
```

Outputs: `raw_vs_folded_interaction.csv`, `per_endpoint_direction.csv`, and `summary.json`. Parent raw and folded point estimates reproduce to floating-point precision.

Primary sources: `experiments/crta_v3_stage_endpoint_expansion_nh2kn_v1/`, `experiments/crta_v3_stage_endpoint_expansion_kn2nh_v1/`, and `scripts/summarize_crta_v3_stage_factorial_endpoint_expansion_v1.py`.
