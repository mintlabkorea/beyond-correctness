# TabLLM reference lexical-realization robustness

Date: 2026-09-10. Provenance category:
**reference lexical-realization robustness; design frozen before inspecting these outcomes**.
Known prior anonymous and Feature-number-word results are disclosed as prior
evidence. No new outcome selects labels, assignments, thresholds or exclusions.

## Sequential freeze

1. W4 margin/category contract: TABLLM_W4_AUROC_EQUIVALENCE_FREEZE_V1.md,
   delta=.02 AUROC, frozen first.
2. Exactly R1 `feature_{i:03d}`, R2 `Field {i:02d}`, R3 `Column {i:02d}`,
   with i = existing zero-based assigned index + 1. R1 preserves the actual
   historical spelling, rather than the illustrative Feature_01 in the request.
   Width, case, separator and generic noun together constitute realization.
   No unrelated nouns, shuffled names or pseudo-words enter the primary grid.
3. Reuse the exact 24 permutations per dataset from REFERENCE_MANIFEST_V1.json,
   SHA256 7fe208e544a954ebd2c15e273473d604107a22e49230631101466ab97097d8da.
4. Audit inputs with the actual tokenizer before any new model scoring.
5. Freeze family admissibility; never repair a family based on its performance.
6. Run all admissible cells; preserve every outcome and per-example probability.

## Matched execution

Datasets: bank, blood, calhousing, car, creditg, diabetes, heart, income,
jungle. Supports: 0,4,32,512. Seeds in original order: 42,1024,0,1,32.
Reference grid: 9*3*24*4*5=12,960 seed-level cells. Intended is shared over
assignments and families (180 cells), not counted as independent replication.
The existing R_anon support runner is the execution authority: released T0-11B
and IA3 initial checkpoint, 30 epochs, batch 4, original balanced sampling
with replacement, exact splits, question/choices, and evaluation batch 16.
Support means parameter adaptation, not concatenated in-context demonstrations.
No demonstrations are added. Train/test order and repeated support rows remain
unchanged. No reduced evaluation set or reduced epoch count is evidence.

Audit every distinct row used by any frozen support draw or evaluation split,
including intended inputs, for every assignment/family. Record full prompt
hash, untruncated token count, truncation flag and retained feature/value
count. Verify direct template substitution with only label positions changed.
Store explicit train and test memberships and feature-to-identifier mappings.
Use max_length=1024 and original special-token settings. A conservative
sufficient gate requires zero truncation in the intended and reference inputs;
if any input truncates, that family is inadmissible for the full panel and
is not scored. Do not change context length or drop rows. This gate is stricter
than merely preserving feature pairs when only a question tail would truncate.
All three families must pass to adjudicate the complete A/B/C comparison.

Hash-bind source/data tree, tokenizer files, T0 weight files, initial IA3,
split manifest, protocols, assignment manifest, audit and execution code.
Completed existing cells may be reused only when row IDs, prompt hashes,
probability dimensions, splits, initial checkpoint and execution settings
match. Otherwise rerun the identical declared cell; never substitute an
approximate reference. Keep any reused artifact unmodified with its provenance.

## Analysis, frozen before outcomes

U[d,n,a,s,f] = AUROC(intended[d,n,s]) - AUROC(reference[d,n,a,s,f]).
Average AUROCs over the five fixed seeds, then 24 fixed assignments, then
equally over the nine datasets. Never pool predictions across distinct fits
to compute one AUROC. Primary: n=0 macro U and paired U[R2]-U[R1],
U[R3]-U[R1]. The intended term cancels exactly in these differences.

Use 2,000 paired evaluation-row bootstrap replicates with seed 20260910.
Within each dataset resample its union of test rows, stratified by true class,
using multinomial multiplicities. A row receives the same multiplicity across
all seeds containing it, supports, assignments and families. Redraw an entire
dataset replicate if any test split loses a class. This handles overlapping
test splits without treating their repeated rows as independent subjects.
Assignments and adaptation draws are fixed; these intervals are conditional
on their realized fits. The nine-dataset primary macro is a fixed-panel mean,
not a population claim. Separately report a paired dataset-resampling macro
sensitivity interval; do not replace the primary interval with it.
For car, compute equally weighted one-vs-rest AUROCs of all four classes.

Apply the shared W4 categories to dataset and macro utility intervals.
Dataset classification: category change => reference-family sensitive;
same categories plus a paired difference CI entirely outside [-delta,delta]
=> magnitude-sensitive; same categories and both difference CIs within the
margin => reference-family robust; otherwise magnitude unresolved with
category agreement. This extra unresolved state prevents non-equivalence
from being misreported as proven sensitivity. Report all categories/counts.

Automatic macro interpretation, with precedence C then A then B:
- C: natural-generic macro category differs from R1. State that the macro
  utility conclusion depends on reference lexical realization; distinguish
  unresolved evidence from a demonstrated negative/near-zero result.
- A: all three macro categories positive, both paired lexical-effect CIs
  within the margin, and at least 7/9 datasets have the same category.
  State that indexed syntax alone does not explain this tested macro result.
- B: all macro categories remain positive but A fails. State macro positivity
  persists; report dataset sensitivity and/or unresolved lexical equivalence.
- Otherwise: unresolved; do not force an unsupported A/B/C claim.
- Any missing or inadmissible required family: not evaluable for this test.

Secondary: each family's U(0),U(4),U(32),U(512), all adjacent contrasts,
U(0)-U(512), strict pointwise monotonicity, and paired family-by-support
interactions [U_f(0)-U_f(n)]-[U_R1(0)-U_R1(n)], n=4,32,512. Use the same
row replicates across supports. Report endpoint attenuation and monotonicity
separately; endpoint decay alone does not prove every intermediate step.
All intervals are pointwise; no simultaneous dataset-wide significance claim.

Passing token/content gates establishes structural comparability only. Field
and Column remain generic identifiers: even a favorable result does not prove
in-distribution prompts, absence of all lexical effects, or criterion (ii)
for every possible removal reference. Do not claim this directly measures OOD.

## Outputs and scheduling

Store audit JSONL.gz and hashes; FROZEN_DESIGN.json; AUDIT_SUMMARY.json;
per-cell probabilities, labels, row IDs, support, seed, family, assignment,
prompt audit metadata, adaptation membership, model/source/checkpoint hashes;
paired dataset and macro CSV/JSON summaries; bootstrap arrays; A/B/C verdict;
family/support interactions and a provenance table with the exact phrase above.
Primary zero-shot completes before secondary adaptation. An atomic task queue
supports resumable workers. Use only currently free authorized GPUs, excluding
GPU 1 in this campaign. Runtime cannot change the scientific grid. No shared
upstream script or historical evidence tree is modified.

Timing-only engineering run: after the full input audit, run exactly the first
epoch (128 optimizer steps) of bank/R2/ref_00/seed42/n_adapt512 on a free GPU.
Do not score test outcomes. Store timing outside evidence; reset checkpoint
and seed for all subsequent evidence fits. This is authorized solely for the
user's runtime estimate and cannot enter analysis or change the frozen design.

## Pre-outcome engineering erratum, 2026-09-10

The first audit stopped on an intended bank input, before tokenization or
scoring: the audit regex required a space after every colon, while the released
clean_note removes that space for an empty value. All 16 field labels were
actually present; the old regex counted 15. The corrected audit replaces only
the label plus colon and preserves every following byte, including the empty
value's original whitespace. A regression test checks both equality and
detection of a changed blank. Templates, values, tokenizer, labels, mappings,
admissibility thresholds, training and analysis are unchanged. The initial
design hash 1d875071c4e17475899c255159e51b2e012bf65f18006b22172de3ac59b9b011,
code and failed logs are archived in engineering_history/attempt1. Re-freeze
the corrected audit before any new performance outcome; this is an audit-code
correction, not a failed family's lexical repair.
