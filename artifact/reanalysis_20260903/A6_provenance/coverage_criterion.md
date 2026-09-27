# Exact coverage criterion

The earliest retained contemporaneous rule is in `iclr_latex_v3/SURVEY_LABEL_PANEL_ENDPOINT_EXPANSION_PREREGISTRATION_V1.md`, committed as `12efa88d189bf562de2ddd14665b1c13722cde9f` at `2026-08-20T21:35:00+09:00`. The committed protocol has SHA-256 `98ce337f4668c03d0f1d8447c0e5519b77817885f9c90d372a7dff0a6828d418` and matches the current file byte-for-byte.

The rule at lines 51–54 is:

> Exactly 10 endpoints × 2 directions × 10 seeds = 200 cells. Each endpoint-direction unit must have at least 8/10 finite paired `pipeline_table`/`placebo_table` seeds. Otherwise the primary panel verdict is not evaluable.

Operationally,

`coverage(e,d) = sum_s I[finite(AUC_pipeline(e,d,s) - AUC_placebo(e,d,s))] >= 8`.

The adjudicator implements `MIN_COVERAGE = 8` at lines 15–22, computes finite paired gains and counts at lines 140–160, and includes `coverage_pass` in the decision at lines 161–168 of `scripts/summarize_crta_v3_survey_label_panel_endpoint_expansion_v1.py`.

The only failing unit is `cancer_history/kn2nh`, with 4/10 finite pairs. Other reduced-coverage units meet the boundary: `heart_attack_history/kn2nh` and `hypertension_history/kn2nh` each have 8/10. The complete grid has 200 stored cells and 187 finite intended/wrong pairs. Therefore the intended/wrong interval may be reported descriptively, but the prespecified primary verdict is not evaluable.

The earliest retained per-cell output begins about nine seconds after the commit according to local filesystem time. The output does not embed the protocol hash, and no push-time, scheduler, W&B, MLflow, cloud-version, CI, or other independent run timestamp was retained. Consequently the temporal classification is B (local timestamp only), not A.
