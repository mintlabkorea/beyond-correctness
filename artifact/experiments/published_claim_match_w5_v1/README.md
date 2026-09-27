# W5 reported claims × control support

Completed files-only analysis of the existing nine-study / 25-comparison audit.
Manuscript source and the original audit/support judgments are unchanged.

Start with [the Korean review](REVIEW_KO_V1.md).

| File | Purpose |
|---|---|
| `COMPARISONS_CLAIM_MATCH_V1.csv` | Requested complete 25-row sheet: source quote/location, A/B claims, adjudicated claims, original support, automatic match |
| `CLAIM_SUPPORT_CROSSTABS_V1.csv` | All 3×3 claim/support cells on both axes |
| `STUDY_CLAIM_MATCH_V1.csv` | Study counts without treating shared comparisons as independent |
| `RESULTS_V1.md` | Computed summary and all 25 quoted comparisons |
| `CLAIM_AGREEMENT_V1.csv/.json` | Pre-adjudication raw agreement and unweighted Cohen kappa |
| `CLAIM_CONFUSION_V1.csv` | Claim confusion matrices; marginals also in JSON |
| `coder_a_raw.json`, `coder_b_raw.json` | Frozen independent AI submissions |
| `claims_adjudicated.json`, `adjudication_ledger.json` | Third-AI decisions and source justifications |
| `SUPPORT_AGREEMENT_HISTORICAL_V1.csv/.json` | Previously frozen two-AI support/gate reproducibility; derived content caveat |
| `UTILITY_SUPPORT_SENSITIVITY_V1.csv` | Same 11 explicit claims under primary versus secondary support |
| `SELECTION_AND_BOUNDARIES_V1.md` | Actual historical search/screening, source access, and masking limits |
| `CLAIM_CODEBOOK_V1.md`, `UNITS_V1.json` | Pre-extraction rules and unchanged coding units |
| `claim_packet/` | Numeric-masked, support-label-blind packet used by A/B |
| `adjudication_packet/` | Same packet plus frozen A/B sheets; no original support labels |
| `extraction_earlier.json`, `extraction_later.json` | Verbatim unmasked source windows and locations |
| `sources_reading/` | Reading-order text regenerated from existing official PDFs when needed |
| `*_FREEZE_V1.json`, `*_boundary.json` | Stage hashes/timestamps and agent read attestations |
| `VALIDATION_V1.json` | Quote, unit, kappa, match-rule, and immutability checks |

The labels describe a conservative retrospective audit, not a paper leaderboard.
Same-model AI coding does not supply independent human inter-rater reliability.
The original support judgments are scope-sensitive. TARTE's local text is an
unverified preacceptance mirror. The review explains why the content-mismatch
count should not be promoted directly to a claim of author overstatement.

## Recompute deterministic summaries

From `.`, with frozen raw submissions already present:

```bash
.venv-klosa-baselines/bin/python experiments/published_claim_match_w5_v1/analyze_w5.py self-test
.venv-klosa-baselines/bin/python experiments/published_claim_match_w5_v1/analyze_w5.py claims
.venv-klosa-baselines/bin/python experiments/published_claim_match_w5_v1/analyze_w5.py merge
.venv-klosa-baselines/bin/python experiments/published_claim_match_w5_v1/validate_w5.py
```

Recomputing agreement does not rerun subjective coding. Preserve frozen raw
submissions and use a new version if the codebook, packet, or adjudication changes.
No GPU or new model-training experiment is used.
