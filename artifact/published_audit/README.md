# Human published-ablation audit

The current release includes the user-supplied human coding records for all 25 comparisons and all 150 P1–P6 checks. Coder A/B are neutral aliases. The author-supplied finalization adjudication is distinguished from original independent observations; no historical date or inter-rater observation was invented.

| Stage | Canonical source | Use |
|---|---|---|
| Independent initial claim/control pass | claim_coding_coder_a.csv; claim_coding_coder_b.csv | Seven initial agreements and Cohen kappa in Appendix Table A19 |
| Independent frozen-rule P1–P6 pass | p1_p6_coder_a.csv; p1_p6_coder_b.csv | 105/150 agreement; derive 15/18 utility-support agreement, kappa .693 |
| Final P1–P6/support consensus | sources/final_consensus.xlsx, Final_P1-P6 / Operationalized support | Authoritative final checks and utility support |
| Check-level evidence | p1_p6_evidence_150.csv | Both independent labels, source passages, rationale and resolution stage |
| Initial claim excerpts | source_evidence.csv | 100 comparison/coder/claim-type records, with original locations |
| Final content adjudication | content_sensitivity_final_adjudication.csv; C01-B_adjudication_record.md | Four explicit claims; dated finalization record, with initial agreement versus resolved disagreement distinguished |
| Final reviewer projection | comparison_level_final.csv; p1_p6_final.csv; claim_coding.csv | Joined final display and explicitly named source for each domain |
| Recomputed agreement | agreement_summary.csv | Initial and independent frozen-rule stages remain separate |
| Adjudication history | adjudication_history/stage1_45_disagreements.xlsx through stage4_final_9.xlsx | 45, 18, 12 and 9 remaining-check stages; unique sheets retained |
| Revision screening | revision_screening_record.csv | XTab and CM2 exclusions; created during finalization from author-verified decisions, not backdated |

The master workbook's **Operationalized support** column is final (among 18 explicit utility claims: 1 Supported, 11 Unsupported, 6 Indeterminate). **Current paper support**, Support_Comparison and change columns refer to an older paper version; the 4/10/4 counts are historical, not the current result.

The original final workbook covers P1–P6 and utility support. Final content support for all four explicit claims is now recorded separately in content_sensitivity_final_adjudication.csv, created on 2026-09-24. C01-A and C03-A are Supported and C03-C is Unsupported by agreement in both original independent sheets; their agreed labels and construction rationale are carried forward. C01-B is Supported by the finalization decision and rationale supplied by the author in C01-B_adjudication_record.md. Its original Unclear/Supported disagreement is retained, and the absence of a contemporaneous standalone record is explicit. The record date is not a backdated adjudication date; the packaging record does not independently establish a joint meeting of both coders.

comparison_level_final.csv and claim_coding.csv now take these four final labels from the standalone adjudication CSV, not from the manuscript. Their content-claim flags come from the agreeing initial coding sheets. The printed main/appendix counts are checked against the adjudication records. Initial human sheets, the original workbook and all independent agreement statistics are unchanged. No new independent coding observation is asserted.

The earlier Coder A CSV in sources/coder_a_preliminary_checks.csv and Coder B combined sheet are auxiliary historical passes. They are not substituted for the canonical frozen-rule files that reproduce 105/150. All 300 independent check labels agree exactly with the final workbook's two initial-label columns. Final consensus agreement is never reported as independent reliability.

source_provenance.csv maps original file hashes, distributed locations and roles. Metadata sanitization changes XLSX bytes; release hashes identify distributed bytes. Workbook author/comment metadata and nested ZIP metadata are anonymous; personnel files are neither read nor distributed. Exact duplicate history sheets and blank/duplicate versions were omitted. The original final workbook's scientific sheets and values are retained.

Historical AI-assisted W5 coding remains clearly labelled at its original experiments/published_claim_match_w5_v1/ and related paths; it is not evidence for the human agreement. historical_comparison_level.csv and manuscript_display_transcription.csv retain their explicit historical/display-only roles. No full third-party papers are bundled.

Run make verify from the archive root. The standard-library verifier checks initial agreements, frozen-rule agreement, final check derivations, all 150 evidence rows and the manuscript display. It does not require Excel or openpyxl.
