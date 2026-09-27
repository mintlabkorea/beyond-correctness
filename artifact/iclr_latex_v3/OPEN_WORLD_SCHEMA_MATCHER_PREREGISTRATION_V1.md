# Pre-registration: distractor-open schema matching curves, v1

Declared 2026-08-20 before executing the open-candidate matcher. The closed 9×9
suite recovered 9/9 under every strong baseline, so this experiment locates the
boundary as target-candidate distractors grow and metadata are ablated.

## Frozen task and scope

- Left/query side: the same nine NHANES member variables used in the stage
  factorial (height, weight, waist, SBP, DBP, glucose, HbA1c, total cholesterol,
  triglycerides).
- Target universe: all 1,315 unique columns in the frozen KNHANES L3 parquet.
  The nine gold target columns are guaranteed to be present but never enter a
  score. Every other target column is an eligible distractor.
- This is **distractor-open one-sided matching**: nine known source queries,
  exactly one known match per query, no abstention, and a target candidate pool
  up to the full schema. It is not full ontology discovery or unknown-cardinality
  open-world matching.
- Hungarian rectangular assignment selects nine distinct target columns.
  `canonical_var_name`, shared flags, benchmark role, gold pair IDs, outcome
  labels, and predictive performance never enter scoring.

## Frozen nested candidate curves

Total target candidate sizes are `9, 17, 33, 65, 129, 257, 513, 1315`.
For each of 50 deterministic draws, all nine gold columns are retained and the
1,306 distractors receive one random order under namespace
`open_world_schema_matcher_v1|draw`. Candidate pools are nested prefixes of
that order. The 1,315-column endpoint is identical across draws and is reported
once as well as in the repeated table.

## Frozen metadata-completeness regimes

The local metadata registry covers 23 NHANES and 23 KNHANES variables. Metadata
for all other target candidates remains missing; it is not inferred or filled.
All text similarities are fit jointly on the nine source texts and the full
1,315-column target universe before candidate subsetting.

1. **name_only** — character TF-IDF cosine on normalized raw identifiers,
   analyzer `char`, n-grams 2–5.
2. **name_plus_unit** — `0.80 × name + 0.20 × exact normalized unit match`;
   missing units score zero.
3. **name_unit_codebook** — `0.35 × name + 0.15 × unit + 0.25 × codebook-word
   TF-IDF + 0.25 × codebook-character TF-IDF`. Codebook text concatenates
   display name, family, subfamily, domain, unit, specimen/system,
   visit/module, and codebook text. Word n-grams are 1–2 and `char_wb` n-grams
   are 3–5. Missing documents score zero.

Every component lies in `[0,1]`; weights are fixed before execution. Richer
regimes are cumulative. Their advantage may partly reflect metadata coverage,
which is reported rather than hidden.

## Frozen outputs and adjudication

Primary output: exact gold accuracy out of nine at every
candidate-size×metadata regime. For subsampled sizes report mean, 2.5/97.5%
empirical draw quantiles, minimum/maximum, and all 50 draw accuracies. For the
full 1,315-column universe report the exact mapping and accuracy. No confidence
interval is interpreted as a population-sampling interval; draws measure
distractor-subset sensitivity only.

Diagnostic verdicts:

- `OWM_P1_closed_set_perfect`: every regime is 9/9 at size 9.
- `OWM_P2_distractors_break_triviality`: at least one regime is below 8/9 in
  the full 1,315-column universe.
- `OWM_P3_rich_metadata_rescues`: the full-universe cumulative codebook regime
  exceeds name-only by at least 2/9 and reaches at least 8/9.

Interpretation is outcome-independent:

- If P2 holds, the 9×9 result is a closed-candidate upper bound; the curve marks
  where correspondence recovery becomes nontrivial.
- If P2 fails, this schema pair remains easy even with all distractors, and the
  paper must not motivate the correspondence layer by recovery difficulty.
- If P3 holds, metadata availability moves the boundary on this pair; because
  only 23/1,315 target columns have curated metadata, this is not a universal
  estimate of metadata value.

Runner/adjudicator:
`scripts/run_crta_v3_open_world_schema_matcher_v1.py`.
