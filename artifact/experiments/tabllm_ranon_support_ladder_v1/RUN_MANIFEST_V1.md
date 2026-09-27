# TabLLM stable-anonymous support ladder v1

This directory contains the compact adjudicated outputs for the frozen
format-matched TabLLM support ladder.  The design and verdict rule are fixed in
`iclr_latex_v3/TABLLM_RANON_SUPPORT_LADDER_FREEZE_V1.md`.

- Arms: List Template (`S`) and stable-anonymous List Template (`R_anon`)
- Supports: 0, 4, 32, and 512 labeled target examples
- Panel: all nine externally fixed TabLLM datasets
- Nonzero-shot evidence: 270 IA3 fits (2 arms x 3 supports x 5 seeds x 9 datasets)
- Frozen verdict: `SUPPORTED_WITHIN_FIXED_PANEL`
- Primary decay: +0.081279 AUROC
- Dataset-bootstrap 95% CI: [+0.024526, +0.147888]
- Student-t 95% CI: [+0.004398, +0.158161]
- Validation: 270/270 cells complete, 135/135 paired groups, maximum metric
  recomputation error 0

`SUMMARY_V1.json` is the figure and manuscript source of truth.  The full raw
predictions and IA3 checkpoints remain in the B200 evidence archive at
`external/tabllm_ranon_support_ladder_v1/evidence_v1` and are covered by
the per-file hashes recorded in the summary.
