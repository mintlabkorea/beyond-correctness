# Beyond Correctness: anonymous reproducibility artifact

Frozen aggregate results, analysis/experiment code, semantic records, the 24-reference library, human coding and manuscript sources/PDFs accompany main_new.tex and appendix_new.tex.

**Frozen-result verification: PASS.** All mapped quantitative checks pass, including the supplied human records and the corrected within-dose aggregation. Restricted-data reconstruction and complete historical environment recovery remain **PARTIAL**, as itemized in MISSING_ARTIFACTS.md; this is not an archive-only reproduction of every training run.

The fastest check needs only Python 3, without data downloads, GPU, API calls or credentials:

```sh
make verify
make scan
make validate
```

1. **Level 1 — frozen-output verification:** verify numeric outputs and human coding against the paper, inspect stored intervals, and optionally regenerate figures/tables. This works from the archive alone. Confidence intervals are compared with frozen records; person-level bootstraps are not independently refit.
2. **Level 2 — public/controlled reproduction:** make reproduce-public checks required public inputs and prints runner commands. Obtain the matching NHANES components and public model/dataset assets described in DATA_ACCESS.md. No automatic training starts.
3. **Level 3 — full reproduction:** make reproduce-full checks authorized HRS/KNHANES inputs. Reviewer-specific access, original source products/preparation and model assets are external dependencies. Missing historical product/version/preparation records are disclosed; do not silently replace them with newer products.

make validate checks Level 1 scientific evidence, release integrity, anonymity and explicit disclosure of remaining reconstruction limitations. It does not certify complete historical training reproduction. Add --require-full-completeness to the validator to reject the remaining PARTIAL records; see QUICKSTART.md.

## Layout and paper map

The Appendix artifact-map directories are reviewer indexes; frozen files retain their experiments/, scripts/ and iclr_latex_v3/ paths. code/ indexes executable roles. No symlinks are used. The manuscript reflects the documented reporting corrections in REVISION_REPORT.md; frozen experimental results, settings and human judgments were not changed.

| Paper item | Input/output map | Generator |
|---|---|---|
| Main Table 1 (`tab:knowledge_conditions`) |  |  |
| Main Figure 1 (`fig:reference_construction`) | iclr_latex_v3/figures/reference_build.pdf | FROZEN_ILLUSTRATION |
| Main Table 2 (`tab:experimental_settings`) | configs/manuscript_settings.json |  |
| Main Table 3 (`tab:gap_utility`) | experiments/tabllm_retrospective_audit_v1/SUMMARY_V1.json; experiments/crta_v3_relation_random_wrong_v1/TABLE2_RANDOM_WRONG_V1.json; experiments/crta_v3_mcr_factorial_semisynth_v1/SUMMARY_V1.json | reproducibility/verify_reported_results.py |
| Main Figure 2 (`fig:ref_sensitivity`) | experiments/tabllm_reference_space_v1/summary_v1/SUMMARY_V1.json; experiments/tabllm_reference_space_v1/summary_v1/reference_utilities.csv | iclr_latex_v3/scripts/make_reference_sensitivity_figure.py |
| Main Figure 3 (`fig:real_support_reference`) | experiments/crta_v3_mcr_mismatch_support_ladder_v1/SUMMARY_V1.json; experiments/tabllm_ranon_support_ladder_v1/SUMMARY_V1.json; experiments/crta_v3_exam_support_ladder_v1/SUMMARY_V1.json | iclr_latex_v3/scripts/make_main_figures.py:make_real_support_reference_figure |
| Main Table 4 (`tab:published_audit`) | published_audit/comparison_level_final.csv; published_audit/content_sensitivity_final_adjudication.csv | reproducibility/verify_human_audit.py |
| Appendix Table A1 (`tab:app-common-settings`) | configs/manuscript_settings.json |  |
| Appendix Table A2 (`tab:app-analysis-registry`) | provenance/I-T01_complete_analysis_ledger.tex |  |
| Appendix Table A3 (`tab:app-measurement-endpoints`) |  |  |
| Appendix Table A4 (`tab:app-reference-portability`) |  |  |
| Appendix Table A5 (`tab:app-relation-evidence`) |  |  |
| Appendix Table A6 (`tab:app-tabllm-reproduction`) | experiments/tabllm_retrospective_audit_v1/SUMMARY_V1.json | scripts/summarize_tabllm_retrospective_audit_v1.py |
| Appendix Table A7 (`tab:app-measurement-full`) | experiments/crta_v3_survey_label_panel_v1/SUMMARY_V1.json; experiments/crta_v3_survey_label_panel_endpoint_expansion_v1/SUMMARY_V1.json; iclr_latex_v3/generated/table2_reference_vs_wrong_v1.json | iclr_latex_v3/scripts/make_appendix_assets.py |
| Appendix Table A8 (`tab:app-exam-no-bridge`) | experiments/crta_v3_exam_no_bridge_reference_v1/SUMMARY_V1.json | scripts/summarize_crta_v3_exam_no_bridge_reference_v1.py |
| Appendix Figure A1 (`fig:app-correspondence-decoy-damage`) | experiments/crta_v3_decoy_compiler_specificity_v1/SUMMARY_V1.json | iclr_latex_v3/scripts/make_appendix_assets.py:plot_a7_decoy_damage |
| Appendix Table A9 (`tab:app-relation-altered-construction`) | experiments/crta_v3_relation_random_wrong_v1/TABLE2_RANDOM_WRONG_V1.json | scripts/summarize_crta_v3_relation_random_wrong_v1.py |
| Appendix Table A10 (`tab:app-tabllm-reference-envelope`) | experiments/tabllm_reference_space_v1/summary_v1/SUMMARY_V1.json | scripts/summarize_tabllm_reference_space_v1.py |
| Appendix Figure A2 (`fig:app-tabllm-reference-noise`) | experiments/tabllm_paired_reference_decomposition_v2/SUMMARY_V1.json; experiments/tabllm_paired_reference_decomposition_v2/utility_intervals.csv | scripts/plot_tabllm_paired_reference_v1.py |
| Appendix Figure A3 (`fig:app-measurement-dose`) | experiments/crta_v3_mcr_mismatch_dose_v1/SUMMARY_V1.json; experiments/crta_v3_mcr_mismatch_dose_tabpfn_v1/SUMMARY_V1.json; experiments/crta_v3_mcr_mismatch_dose_k512_extension_v1/SUMMARY_V1.json | iclr_latex_v3/scripts/make_appendix_assets.py:plot_a2_mismatch_grid |
| Appendix Table A11 (`tab:app-measurement-dose-stats`) | experiments/crta_v3_mcr_mismatch_dose_v1/SUMMARY_V1.json; experiments/crta_v3_mcr_mismatch_dose_tabpfn_v1/SUMMARY_V1.json; experiments/crta_v3_mcr_mismatch_dose_k512_extension_v1/SUMMARY_V1.json | scripts/summarize_crta_v3_mcr_mismatch_dose_v1.py |
| Appendix Figure A4 (`fig:app-redundancy-ladder`) | experiments/crta_v3_mcr_redundancy_ladder_v1/SUMMARY_V1.json | iclr_latex_v3/scripts/make_appendix_assets.py:plot_redundancy_ladder |
| Appendix Table A12 (`tab:app-tabllm-support-ladder`) | experiments/tabllm_ranon_support_ladder_v1/SUMMARY_V1.json | scripts/summarize_tabllm_ranon_support_ladder_v1.py |
| Appendix Figure A5 (`fig:app-tabllm-support-by-dataset`) | experiments/tabllm_ranon_support_ladder_v1/SUMMARY_V1.json | iclr_latex_v3/scripts/make_appendix_assets.py:plot_tabllm_support_by_dataset |
| Appendix Table A13 (`tab:app-exam-support-ladder`) | experiments/crta_v3_exam_support_ladder_v1/SUMMARY_V1.json | scripts/summarize_crta_v3_exam_support_ladder_v1.py |
| Appendix Table A14 (`tab:app-measurement-rank-alignment`) | experiments/crta_v3_mcr_nonsemantic_rank_alignment_v1/SUMMARY_V1.json; experiments/crta_v3_mcr_nonsemantic_rank_alignment_v1/POLARITY_DOSE_V1.json | scripts/summarize_crta_v3_mcr_nonsemantic_rank_alignment_v1.py |
| Appendix Table A15 (`tab:app-relation-capacity`) | experiments/crta_v3_relation_capacity_sensitivity_v1/SUMMARY_V1.json | scripts/summarize_crta_v3_relation_capacity_sensitivity_v1.py |
| Appendix Table A16 (`tab:app-model-coverage-compact`) | experiments/crta_v3_mcr_transtab_bridge_decomposition_v1/SUMMARY_V1.json; experiments/crta_v3_mcr_carte_v1/SUMMARY_V1.json | reproducibility/verify_reported_results.py |
| Appendix Table A17 (`tab:app-unit-attribution-summary`) | experiments/crta_v3_m1m2_stage_factorial_v1/SUMMARY_V1.json; experiments/crta_v3_binding_backbone_generality_v1/SUMMARY_V1.json; experiments/crta_v3_pam_constraint_relations_v1/SUMMARY_V1.json; experiments/crta_v3_m3_sign_probe_v1/SUMMARY_V1.json; experiments/crta_v3_camels_sign_probe_v2/SUMMARY_V2.json | iclr_latex_v3/scripts/make_appendix_assets.py:table_a3_real_units |
| Appendix Figure A6 (`fig:app-interaction-controlled-real`) | experiments/crta_v3_mcr_source_informativeness_ladder_v1/SUMMARY_V1.json; experiments/crta_v3_stage_source_informativeness_ladder_v1/SUMMARY_V1.json; experiments/crta_v3_stage_source_ladder_v2_source_only_v1/SUMMARY_V1.json | iclr_latex_v3/scripts/make_appendix_assets.py:plot_controlled_real_mechanism |
| Appendix Table A18 (`tab:app-audit-screening`) | iclr_latex_v3/design_audit/ELIGIBILITY_SCREEN_V1.csv; published_audit/revision_screening_record.csv | reproducibility/verify_human_audit.py |
| Appendix Table A19 (`tab:app-published-audit-agreement`) | published_audit/claim_coding_coder_a.csv; published_audit/claim_coding_coder_b.csv; published_audit/agreement_summary.csv | reproducibility/verify_human_audit.py |
| Appendix Table A20 (`tab:app-published-audit`) | published_audit/comparison_level_final.csv; published_audit/p1_p6_evidence_150.csv | reproducibility/verify_human_audit.py |
| Appendix Table A21 (`tab:app-published-claim-provenance`) | published_audit/source_evidence.csv | reproducibility/verify_human_audit.py |
| Appendix Table A22 (`tab:app-software-environment`) | reproducibility/environments/version_audit.csv |  |
| Appendix Table A23 (`tab:app-artifact-map`) | ARTIFACT_STATUS.md |  |

## Integrity and readable manuscript

SHA256SUMS covers every file except itself. ARTIFACT_MANIFEST.csv excludes itself and SHA256SUMS to avoid circular hashes; its hash is in SHA256SUMS. source_copy_ledger.csv distinguishes original and sanitized hashes. A digest of an omitted input is external provenance, not a bundled input.

Compiled copies are generated/manuscript/main_new.pdf and appendix_new.pdf. make paper uses temporary legacy include aliases and requires pdflatex, bibtex and Ghostscript. make figures and make tables use frozen numeric inputs. make aggregate-audits recomputes thread comparisons and within-dose coefficients from existing aggregates; these new projections are not represented as historical output files.

No personnel file, restricted row data, row predictions, model weight, credential, git history or full third-party paper is included. No new training or model generation was performed. See the one-page FINAL_ARTIFACT_REPORT.md, DATA_ACCESS.md, ARTIFACT_STATUS.md, REVISION_REPORT.md and reproducibility/validation_scope.md for exact scope and limitations.
