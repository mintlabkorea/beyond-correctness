# Final artifact report

Release record: 2026-09-24. Scope: frozen-result verification and release integrity.

| Check | Result |
|---|---|
| Numerical and source-record verification | 1175 PASS / 0 FAIL / 0 MISSING |
| Table regeneration | 16/16 PASS |
| Figure regeneration | 9/9 PASS |
| Anonymity scan, including decoded code strings and separate audit | PASS |
| Secret scan | PASS |
| Manifest and checksum verification | PASS |
| Fresh-extraction verify / scan / validate | PASS |
| Human audit | 25 comparisons / 150 P1–P6 checks |
| Independent P1–P6 agreement | 105/150; independent utility support 15/18, kappa .693 |
| Final explicit content adjudication | 4/4 recorded; 3 Supported / 1 Unsupported |
| Candidate-name inventory | 1,315/1,315; matches all 50 frozen full-pool hashes |
| Full historical reconstruction | PARTIAL |

The table/figure reports are retained successful regenerations from unchanged frozen inputs. Numerical verification now includes 34 additional checks of final content-adjudication provenance and consistency. The new CSV and C01-B narrative record are dated finalization records: three initial agreements are carried forward, and the C01-B decision/rationale is author supplied. They are not backdated records or new independent-coding observations. See published_audit/README.md.

Remaining reconstruction limitations:

- L01: exact restricted clinical source/preparation chain remains incomplete.
- L02: complete historical execution environment locks are unavailable for all runs.
- L03: the historical NHANES builder revision/environment is not fully pinned.

See ARTIFACT_STATUS.md, MISSING_ARTIFACTS.md and reproducibility/ for evidence and scope. The stricter --require-full-completeness check correctly fails on L01–L03. Release checks are repeated after fresh extraction before publishing this ZIP; the detailed external report records the archive hash, size and commands without a circular in-archive hash.

This report summarizes validation of the submitted artifact.
It does not claim archive-only reproduction of all historical training runs.
