# Distractor-open schema matcher diagnosis, v1

The full 1,315-column target universe creates a sharp metadata boundary:

| metadata regime | 9-candidate point | 1,315-candidate exact accuracy |
|---|---:|---:|
| name only | 4/9 | 2/9 |
| name + unit | 5/9 | 4/9 |
| name + unit + codebook | 9/9 | 9/9 |

Frozen verdicts: `OWM_P1_closed_set_perfect=false`,
`OWM_P2_distractors_break_triviality=true`, and
`OWM_P3_rich_metadata_rescues=true`.

## Why P1 does not contradict the earlier closed 9×9 result

The earlier runner fit its TF-IDF vocabulary and IDF weights on only the 18
closed-set identifiers/documents and recovered 9/9. This preregistration instead
fit every text scorer once on the nine source variables plus all 1,315 target
candidates, then held that score matrix fixed while candidate subsets changed.
Consequently, even the size-9 assignment point uses full-universe IDF weights;
it is not a re-execution of the earlier 18-document scorer. Weak raw-identifier
fragments are sensitive to that corpus definition. P1 therefore fails under its
frozen wording and is not retroactively repaired.

## What the experiment does establish

- Under full-schema competition, raw identifier fragments alone recover 2/9;
  adding known units recovers 4/9.
- Adding the frozen codebook fields recovers all 9/9 even against 1,306
  distractors. The rich regime is 9/9 at every registered pool size and draw.
- Thus closed-set recovery difficulty is not the paper's universal motivation.
  On this pair, correspondence is nontrivial when only names or names+units are
  available, but remains easy when the curated codebook is available.

## Boundary

Only 23 of 1,315 KNHANES candidates have rows in the curated metadata registry,
including all nine gold targets. Missing candidate metadata was left empty as
registered. The rich regime's success therefore mixes semantic informativeness
with highly uneven metadata coverage and is an upper-bound-friendly result, not
a general estimate of codebook matching accuracy.

The task also assumes nine known source queries, one gold match each, and no
abstention. It is distractor-open one-sided matching, not unknown-cardinality
ontology discovery.

Authoritative numeric artifact: `SUMMARY_V1.json`.
