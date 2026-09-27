# TabLLM generic-lexical zero-shot reference audit — frozen design, v1

Frozen 2026-09-07 (Asia/Seoul) before any generic-lexical prediction was
scored or inspected.  This is a review-triggered reference-family sensitivity
analysis of the already reported TabLLM zero-shot feature-name utility.  It is
not a replacement reference and it does not alter the completed anonymous-
identifier analyses.

## Pre-experiment interview

**Category:** experiment.  **Approval:** the user explicitly requested the
zero-shot-only experiment and authorized starting it on the free server GPU.

**Goal.** Test the objection that the stable-anonymous identifiers themselves
may be an unusual interface for the pretrained T0 model by comparing them with
stable, natural-language-shaped identifiers that carry no feature semantics.

**Outcome tree.** If the generic-lexical and stable-anonymous macro utilities
are close, the zero-shot feature-name result is stable across these two
reference families.  A material shift remains informative: reference
dependence extends beyond the assignment of anonymous identifiers to the
lexical family used for the reference.  A macro sign change means the
qualitative zero-shot utility conclusion depends on reference family.  All
nine dataset results are retained under every outcome.

**Load-bearing assumptions.** The new arm must change only field labels, must
preserve a stable one-to-one field identity within each dataset, and must not
introduce feature-specific meaning.  Exact template and split-membership gates
are checked before interpretation.  The words denoting ordinal identity are
generic identifiers, not claims about feature semantics.

**Decision and stopping rule.** Run one fixed generic-lexical reference at
zero shot on all nine datasets.  Do not add alternative prefixes, identifier
assignments, support levels, or datasets after observing the output.  A later
support experiment, if any, is a separately frozen post-result extension.

## Fixed reference

For feature line `i`, counting from one in the released List Template, replace
the original field label with the exact identifier `Feature <number-word>`.
The fixed sequence is:

`Feature one`, `Feature two`, `Feature three`, `Feature four`, `Feature five`,
`Feature six`, `Feature seven`, `Feature eight`, `Feature nine`, `Feature ten`,
`Feature eleven`, `Feature twelve`, `Feature thirteen`, `Feature fourteen`,
`Feature fifteen`, `Feature sixteen`, `Feature seventeen`, `Feature eighteen`,
`Feature nineteen`, and `Feature twenty`.

The frozen TabLLM panel has at most 20 fields, so this sequence covers every
dataset without fallback naming.  The mapping from feature line to identifier
is fixed and stable over every row of a dataset.  Original feature names are
removed rather than reassigned.

Only the label substring before `: ${...}` changes.  Feature-line order,
placeholders, substituted values, bullets, colons, whitespace, questions,
verbalizers, rows, split memberships, model, checkpoint, batch size, and
scoring code remain unchanged.

## Fixed execution contract

- Model: the same local `bigscience/T0` 11B snapshot and released
  `t011b_ia3_finish.pt` checkpoint as the compatibility reproduction.
- Code: the unchanged released-code-compatible zero-shot scorer used by the
  retrospective audit, loaded by a thin reference-template wrapper.
- Data: all nine datasets: `bank`, `blood`, `calhousing`, `car`, `creditg`,
  `diabetes`, `heart`, `income`, and `jungle`.
- Evaluation: score once the sorted union of the five released 20% test splits
  (`42`, `1024`, `0`, `1`, `32`) and reconstruct all five split AUROCs.
- Batch size: 16; maximum input length: 1024; bfloat16 model compute; normalized
  class likelihoods; no fit.
- Device: NVIDIA B200 GPU 3.  Device choice has no role in the estimand.
- Reuse: intended-name and stable-anonymous zero-shot predictions are reused,
  not rerun.
- New evidence: exactly 9 dataset--reference scoring groups.

The protobuf pure-Python compatibility implementation is required, matching
the completed TabLLM follow-up runs.  A two-dataset limited-example smoke is
stored outside the evidence root and is inadmissible.

## Pre-scoring and validation gates

For every dataset, the implementation must verify before interpretation:

1. the original template has between 1 and 20 nonempty List Template lines;
2. every original field label is replaced exactly once by the fixed identifier
   at the same line index;
3. line count, line order, placeholders, punctuation after the label, and
   substituted values are unchanged;
4. generic identifiers are unique and stable across all rows;
5. no original field label remains in a label position;
6. full-row count, scored-union count, per-seed test size, label, and test-row
   membership match both reused arms; and
7. model, checkpoint, source-tree, scoring, protocol, wrapper, and prediction
   hashes are complete and internally consistent.

Failure of any gate stops adjudication.  Completed evidence groups are cached
and resumable only when their frozen provenance validates.

## Estimands and frozen interpretation

For dataset `d`, let `S[d]`, `R_anon[d]`, and `R_lex[d]` be the five-split mean
AUROCs of the intended-name, stable-anonymous, and generic-lexical arms.

`u_anon[d] = S[d] - R_anon[d]`

`u_lex[d] = S[d] - R_lex[d]`

The primary reference-family shift is the unweighted nine-dataset macro
difference `Delta = macro(u_lex) - macro(u_anon)`.  Report both macro utilities,
`Delta`, all nine dataset utilities and shifts, and any dataset-level sign
changes.  A 10,000-draw paired dataset bootstrap with
`default_rng(20260907)` gives a descriptive percentile interval for `Delta`;
the purposively assembled nine-dataset panel is not treated as a random sample
of all tabular tasks.

The existing `.02 AUROC` smallest effect of interest is reused as a
materiality scale:

- **MACRO_STABLE_ACROSS_ANONYMOUS_AND_GENERIC_LEXICAL** iff both macro
  utilities are positive and `abs(Delta) < .02`;
- **MACRO_SIGN_DEPENDS_ON_REFERENCE_FAMILY** iff the two macro utilities do
  not have the same strictly positive sign; and
- otherwise **MATERIAL_MACRO_REFERENCE_FAMILY_SHIFT**.

The verdict characterizes these two fixed reference families on this fixed
zero-shot panel.  It does not establish lexical-reference invariance in
general, pretrained-input perplexity, or target-support attenuation.

## Required artifacts

- this protocol, wrapper, base-runner, source-tree, model, checkpoint, and
  package hashes;
- prepare-only template/note audit and separate smoke output;
- labels, normalized class probabilities, row IDs, prompt hashes, per-split
  metrics, and prediction hashes for all nine groups;
- validation against both reused arms;
- complete JSON/CSV/Markdown summary and artifact manifest.
