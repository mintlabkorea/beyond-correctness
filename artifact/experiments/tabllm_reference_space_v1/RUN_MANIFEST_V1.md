# TabLLM admissible-reference space audit v1

This directory contains the frozen candidate manifest and compact adjudicated
outputs for the zero-shot multiple-reference audit.

- Frozen design: `iclr_latex_v3/TABLLM_ADMISSIBLE_REFERENCE_SPACE_FREEZE_V1.md`
- References: 24 unique stable-anonymous identifier bijections per dataset
- Panel: all nine fixed TabLLM datasets and five released test-split seeds
- Evidence groups: 216/216 complete
- Frozen verdict: `MAGNITUDE_SENSITIVE_SIGN_ROBUST`
- Canonical macro utility: `+.08837` AUROC
- Aligned 24-reference macro range: `[+.08837,+.12404]`
- Combinatorial fixed-panel envelope: `[+.04857,+.16183]`
- Primary envelope span: `+.11326`, dataset-bootstrap 95% interval
  `[+.08968,+.13550]`
- Independent-uniform product-space SD: `.01013`; central 95% interval
  `[+.08575,+.12546]`
- Canonical product-space percentile: `.04394`
- Dataset-level sign changes: 4/9; every dataset's utility span exceeds `.02`

All 216 metric files and 216 prediction files passed protocol, runner,
manifest, permutation, template, split-membership, and file-hash checks. The
nine canonical groups reproduce the frozen `R_anon` AUROCs with maximum error
zero. Compact results are under `summary_v1/`. The 155 MB raw evidence archive
remains on the B200 server at
`external/tabllm_reference_space_v1/evidence_v1` and is covered by
`summary_v1/ARTIFACT_MANIFEST_V1.json`.

