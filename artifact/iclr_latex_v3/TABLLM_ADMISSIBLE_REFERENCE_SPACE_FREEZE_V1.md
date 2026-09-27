# TabLLM admissible-reference space audit — frozen design, v1

Frozen 2026-09-03 (Asia/Seoul) before any new reference prediction is scored
or inspected. This is a sensitivity analysis of the already reported zero-shot
TabLLM feature-name utility, not a replacement reference and not a new choice
among references.

## Pre-experiment interview

**Category:** experiment. **Approval:** after the design was proposed, the user
selected the free B200 GPU 1 and said to run it there.

**Goal.** In one fixed setting, construct multiple admissible references and
measure how much the realized predictive utility varies across that reference
space.

**Outcome tree.** A narrow, same-sign envelope is evidence that the reported
utility is robust to the remaining arbitrary identifier assignment. A material
envelope with preserved sign shows magnitude sensitivity. A sign-crossing
envelope shows that admissibility alone does not determine the qualitative
utility conclusion. Every outcome is reportable; no reference is selected from
the audit for use as a revised primary control.

**Load-bearing assumption.** Every candidate must remove feature-name semantics
while preserving all other serialized information and the predictive
interface. This is checked before scoring by exact template audits and by
requiring the canonical candidate to reproduce the previously frozen
stable-anonymous result exactly.

## Fixed setting

- Model and checkpoint: the same released-code T0 11B model and released IA3
  checkpoint used in the compatibility reproduction.
- Data: all nine fixed TabLLM datasets (`bank`, `blood`, `calhousing`, `car`,
  `creditg`, `diabetes`, `heart`, `income`, and `jungle`).
- Evaluation: zero-shot scoring of the same sorted union of the five released
  test splits, followed by reconstruction of the five split AUROCs.
- Intended condition: the already frozen List Template predictions with the
  original feature names. These predictions are reused, not rerun.
- Reference conditions: 24 stable-anonymous List Templates defined below.
- Device: B200 GPU 1 only. GPU choice has no role in the estimand.

Zero-shot is chosen because it isolates reference construction without adding
fine-tuning randomness or requiring new IA3 fits. The nine-dataset panel is the
same externally fixed but purposively assembled panel used in the manuscript.

## Admissible reference space

For a dataset with `p` feature lines, every candidate uses exactly the identifier
set

`feature_001, feature_002, ..., feature_p`.

The candidate changes only the bijection from the original feature lines to
this fixed anonymous identifier set. Feature-line order, placeholders, values,
punctuation, whitespace, question, verbalizers, rows, split membership, model,
checkpoint, batch size, and scoring code remain unchanged. A bijection is
stable over all rows of a dataset, preserving within-dataset variable identity.
Because no original feature name is retained or reassigned, these are
no-semantic-content references rather than wrong-name conditions.

There are 24 candidates, `ref_00` through `ref_23`. `ref_00` is the identity
line-to-identifier mapping and is exactly the manuscript's current
`R_anon`. For each dataset, the remaining candidates are the first 23 unique
non-identity permutations produced as follows:

1. Initialize NumPy `default_rng` (PCG64) with the unsigned little-endian
   integer represented by the first eight bytes of
   `SHA256("tabllm-reference-space-v1/" + dataset)`.
2. Draw `rng.permutation(p)` repeatedly.
3. Retain a draw only if it differs from every previously retained
   permutation, starting with the identity permutation.
4. Stop after 24 unique permutations have been retained.

Blood has four features and therefore exactly `4! = 24` possible bijections;
the audit exhausts its complete tightly matched space. The other datasets use
the fixed 24-candidate subset generated above. No permutation or candidate
count may be changed after predictions are inspected.

`List Only Values` is excluded because it changes serialization. Permuted real
feature names are excluded because they supply wrong semantic content. Generic
prefix changes such as `column_001` are excluded from the primary space because
they change the lexical token set rather than only its arbitrary assignment.

## Pre-scoring admissibility gates

For every dataset and candidate, the runner must verify:

1. exactly 24 unique permutations and templates;
2. `ref_00` equals the prior stable-anonymous template byte for byte;
3. the identifier set is identical across candidates;
4. line count, line order, placeholder sequence, punctuation after each field
   label, and substituted values are unchanged;
5. no original feature label remains in an anonymous label position;
6. the five test memberships and their sorted union equal the frozen split
   construction; and
7. the generated reference manifest matches the committed manifest byte for
   byte before evidence scoring begins.

A two-candidate, two-dataset engineering smoke is stored outside the evidence
root and is inadmissible. In the evidence run, all nine `ref_00` groups are
scored first and must reproduce every frozen stable-anonymous split AUROC and
test-membership hash within `1e-12`. Failure stops the run before `ref_01`.

## Estimands

Let

`u[d,r] = mean_seed AUROC(S[d]) - mean_seed AUROC(R[d,r])`,

where the five released split seeds are averaged within dataset. The intended
term is shared across references.

Primary characterization of the evaluated reference library:

- dataset envelope: `min_r u[d,r]`, `max_r u[d,r]`, and their span;
- combinatorial macro lower endpoint:
  `L = mean_d min_r u[d,r]`;
- combinatorial macro upper endpoint:
  `H = mean_d max_r u[d,r]`;
- reference-space span: `H-L = mean_d (max_r u[d,r]-min_r u[d,r])`.

The combinatorial envelope permits any independently fixed candidate from the
24-member library for each dataset. Its endpoints are planned sensitivity
summaries, not outcome-dependent proposals for a new reference.

Secondary summaries are the canonical `ref_00` macro utility; mean, SD, IQR,
minimum, and maximum across the 24 index-aligned macro configurations; and the
analytic SD under independent uniform selection from the 24 candidates within
each dataset. A 1,000,000-draw product-space Monte Carlo approximation uses
`default_rng(20260903)` for the 2.5th, 10th, 50th, 90th, and 97.5th percentiles
and the percentile position of the canonical utility. A 10,000-draw dataset
bootstrap using `default_rng(20260904)` reports percentile intervals for `L`,
`H`, and `H-L`. Dataset-level envelopes and sign changes are always reported.

## Frozen interpretation

The existing smallest effect of interest, `.02 AUROC`, is reused only as an
interpretive scale.

- **STABLE_WITHIN_TIGHT_SPACE:** `L > 0` and `H-L < .02`.
- **MAGNITUDE_SENSITIVE_SIGN_ROBUST:** `L > 0` and `H-L >= .02`.
- **SIGN_SENSITIVE:** `L <= 0 <= H`.
- Otherwise report the observed direction and envelope without forcing one of
  the above labels.

These labels describe the fixed panel and the tightly matched anonymous-
identifier space only. They do not establish invariance over all conceivable
admissible references, generic identifier vocabularies, models, or task
populations. Sampling uncertainty over test examples remains separate from
reference-choice variation and is not collapsed into a single interval.

## Required artifacts

- frozen protocol, runner, summarizer, and reference-manifest hashes;
- complete feature-line-to-identifier permutation manifest;
- pre-scoring admissibility audit;
- smoke outputs in a separate root;
- per-example labels, normalized class probabilities, prompt hashes, and
  per-split metrics for all `24 x 9 = 216` reference groups;
- exact canonical reproduction audit;
- complete-cell and hash manifest;
- dataset and macro reference-space summaries and a result report.

