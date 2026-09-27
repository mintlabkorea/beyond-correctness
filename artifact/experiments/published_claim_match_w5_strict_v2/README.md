# W5: strict content claims × original control support

Files-only revision implementing the user's strict claim-strength definition:

> The authors interpret the comparison as showing dependence on the particular semantic content supplied, rather than merely showing that the semantic component matters or is used.

All nine studies, 25 comparisons, source windows, utility judgments and control-support judgments are retained. The original v1 analysis is archived unchanged. No manuscript changes or GPU jobs are part of this revision.

Start with [the Korean review](REVIEW_KO_V2.md) and [the 25-row sheet](COMPARISONS_STRICT_CLAIM_MATCH_V2.csv).

| File | Purpose |
|---|---|
| `STRICT_CONTENT_CODEBOOK_V2.md` | Definition and attribution rules frozen before new coding |
| `COMPARISONS_STRICT_CLAIM_MATCH_V2.csv/.json` | New strict content, unchanged utility/support, legacy weak claims, source evidence and raw A/B labels |
| `CONTENT_V1_TO_V2_TRANSITIONS.csv` | All 25 old-to-new content labels and match states |
| `CLAIM_SUPPORT_CROSSTABS_V2.csv` | Complete content and utility 3×3 cross-tabs |
| `STUDY_STRICT_CONTENT_V2.csv` | Study-level counts to expose concentration within studies |
| `SUMMARY_V2.json`, `RESULTS_V2.md` | Computed summary and comparison-level quotes/rationales |
| `CONTENT_AGREEMENT_V2.csv/.json`, `CONTENT_CONFUSION_V2.csv` | Raw, pre-adjudication agreement, marginals and Cohen's κ |
| `coder_a_raw.json`, `coder_b_raw.json` | Frozen fresh AI coding submissions |
| `content_adjudicated.json`, `adjudication_ledger.json` | Support-blind third-AI review of all 25 comparisons |
| `packet/`, `adjudication_packet/` | Fixed numerical-magnitude-masked reading packets |
| `*_FREEZE_V2.json`, `*_boundary.json` | Stage hashes, timestamps and read attestations |
| `VALIDATION_V2.json` | Quote, unit, agreement, deterministic classification and immutability checks |

The main `claim_text`, `claim_location`, `rationale`, `claim_scope`, `claim_linkage` and `coder_1/2` fields refer to the new strict-content coding. Utility evidence and scope remain in `legacy_claim_text`, `legacy_claim_location`, `legacy_rationale`, `legacy_claim_scope` and `legacy_claim_linkage`; the original utility coder columns are preserved. A strict `No` does not deny a weaker semantic-use claim and need not imply `descriptive_only=Yes`.

The unchanged [v1 selection/source record](../published_claim_match_w5_v1/SELECTION_AND_BOUNDARIES_V1.md) documents the original bounded candidate pool and TARTE source-version gap. The new coding uses fresh same-model AI contexts with instructional read boundaries, not technically isolated access or human inter-rater validation. The definition revision is retrospective; it is not preregistration.

Recompute deterministic summaries with the frozen submissions already present:

```bash
OPENBLAS_NUM_THREADS=1 .venv-klosa-baselines/bin/python experiments/published_claim_match_w5_strict_v2/analyze_strict_v2.py coders
OPENBLAS_NUM_THREADS=1 .venv-klosa-baselines/bin/python experiments/published_claim_match_w5_strict_v2/analyze_strict_v2.py finish
```

These commands validate stage hashes; they do not rerun subjective coding. Changing a frozen codebook, packet or submission requires a new version.
