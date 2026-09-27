# Finalization revision — 2026-09-23

This revision incorporates supplied human source records and explicitly authorized reporting corrections. No experiment was rerun, frozen metric changed, human judgment invented, endpoint removed, seed changed, or interval refitted.

See ARTIFACT_ISSUES.md for I01–I13 dispositions, published_audit/source_provenance.csv for human source hashes and roles, and reproducibility/manuscript_changes.diff for the exact manuscript changes. D.2's original .165–.329 is unchanged: the earlier verifier compared a different averaging axis. The recovered historical table confirms the correct estimand.

The four numerical corrections apply strict nearest three-decimal rounding to frozen source values. The .738 correction also updates duplicate appendix prose. The 2,000 bootstrap exception and failed 4/10 measurement coverage are reporting qualifications; frozen estimates and intervals are retained. XTab/CM2 revision decisions and the schema-only candidate export are dated finalization records, not invented historic artifacts.

The missing Kim et al. (2025) entry was not located in a retained local bibliography. Metadata was obtained from the publisher's [Nature Communications article](https://www.nature.com/articles/s41467-025-58624-6), DOI 10.1038/s41467-025-58624-6. This supplies the missing key without changing the cited scientific claim.

The validation interface now separates Level 1 evidence/integrity from full historical reconstruction. make verify still fails on any missing numerical/coding evidence or mismatch. make validate checks the numerical verifier, hygiene, manifests, mapped inputs and exact disclosure of the three residual PARTIAL promises. --require-full-completeness additionally fails on any PARTIAL/MISSING promise. This distinction is visible in README, ARTIFACT_STATUS and validation JSON; no full reconstruction PASS is asserted.

Security scanning now covers nested XLSX XML and author/comment metadata. The email scan first checks for an at-sign, avoiding quadratic regex work on long hash-only lines. No file-size skip or evidence exception was added. Hashes are cached within one validation invocation; the checksum and manifest checks still cover all payload files.

## Subsequent anonymity and wording correction

The obsolete review verifier was excluded because its source contained reconstructible private-identity search patterns. Four unused KLoSA scripts were also removed from the release. Original repository sources remain private and unchanged. No source excerpt or diff of the excluded detector is distributed. Generated indexes, source-copy ledger, manifest and checksums were regenerated.

The main source and compiled PDF correct the Introduction spelling of prediction and use check Setup consistently with the three named criteria in Section 3.2. No effect estimate, confidence interval, coding decision or experiment setting changes.

An independent local audit searches both raw text and statically reconstructed Python strings, plus workbook XML and extracted PDF text. Private search patterns are never shipped. The original scanner PASS was insufficient; this additional audit and a regression against the excluded source are reported separately. Bibliographic names in third-party author fields are retained.

## Content adjudication completion — 2026-09-24

content_sensitivity_final_adjudication.csv now records C01-A, C01-B, C03-A and C03-C. The three agreeing original decisions are carried forward. C01-B retains the original disagreement and records the final Supported decision and source-recheck rationale supplied by the author during finalization. C01-B_adjudication_record.md provides the narrative record. Both records carry their actual creation date; they do not claim a retained contemporaneous record or independently establish joint participation by both coders.

Final content fields now derive from this record, not a manuscript transcription. Initial sheets and the original final utility/P1–P6 workbook are unchanged, as are initial reliability statistics and the paper's 3 Supported / 1 Unsupported count. Verification checks the new record's ID coverage, raw initial labels, evidence, final labels, provenance and links to reviewer projections.

The in-archive FINAL_ARTIFACT_REPORT.md is a compact validation summary. The detailed external report still records archive size/hash and commands. Existing clinical provenance evidence remains PARTIAL; no acquisition date was inferred. Existing requirements and conda declarations were reviewed, but no complete lock tied to every historical reported run was established. No current pip freeze or replacement historical environment was produced.
