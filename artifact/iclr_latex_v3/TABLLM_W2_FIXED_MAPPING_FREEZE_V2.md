# W2: fixed primary mapping, varied lexical realization

Frozen 2026-09-10 before any new lexical-family predictions. This supersedes
the user-rejected 24-assignment full cross. That campaign stopped during input
audit with zero prediction files; its design and failed-audit history remain
archived. This is review-triggered work with prior TabLLM outcomes known.

Provenance: **reference lexical-realization robustness; design frozen before inspecting these outcomes**.

## 1. Shared W4 margin first

Keep TABLLM_W4_AUROC_EQUIVALENCE_FREEZE_V1.md unchanged: delta=.02 AUROC,
reusing the existing TabLLM SESOI. Practical categories from a paired 95% CI
[L,H]: positive if L>.02; negative if H<-.02; near-zero if the complete CI
lies in [-.02,.02]; unresolved otherwise. A CI excluding zero is separately
reported, not equated with practical positivity. Historical verdicts are not
retroactively overwritten. Equivalence requires CI containment, not merely a
small point difference or a nonsignificant test.

## 2. Freeze strings and primary mapping

Use exactly the manuscript's original canonical mapping, `ref_00`, from
REFERENCE_MANIFEST_V1.json (SHA256
7fe208e544a954ebd2c15e273473d604107a22e49230631101466ab97097d8da).
The historical canonical builder assigns line i to index i. Verify `ref_00`
has precisely that permutation for every dataset; never create/select a new
mapping based on outcomes. Keep all other 23 historical assignments unchanged
as separate evidence; do not cross them with new lexical families.

- R1: actual existing spelling `feature_001`, `feature_002`, ...
- R2: `Field A`, `Field B`, ...
- R3: `Variable A`, `Variable B`, ...

For assigned zero-based index j, R1 uses `feature_{j+1:03d}`, and R2/R3 use
the capital Latin letter with code point 65+j. Maximum feature count must be
<=26. Case, generic word, separator and numeral-to-letter encoding together
constitute the lexical-realization intervention. Feature identity remains
stable across every support and test row. Use no unrelated-domain nouns,
pseudo-words or character shuffles. The optional two extra zero-shot mappings
are not part of this budget or execution.

## 3. Outcome-blind audit before model scoring

Datasets: bank, blood, calhousing, car, creditg, diabetes, heart, income,
jungle. Supports: 0,4,32,512; original seeds: 42,1024,0,1,32.
Audit all distinct rows in the union of every frozen support draw and test
split for intended and all three references. Verify exact feature order,
values, missing-value representation, non-label punctuation/whitespace,
question, placeholders and direct serializer output. Preserve original
`iterrows()` numeric coercion. Shared support/test memberships are stored
explicitly, including repeated support rows sampled with replacement.

Store every prompt SHA256, full token count, truncation flag and retained
feature/value count; summarize mean/min/max token count and truncation count.
Use the actual released-model tokenizer, original special tokens and context
limit 1024. Different token counts are allowed; any truncation in intended
or a family makes that family inadmissible for the full panel. This conservative
gate guarantees no extra feature/value removal. Do not change context length,
drop rows or repair labels after observing outcomes. Complete all three-family
audits before freezing admissibility and starting any performance calculation.

The earlier audit-regex bug is already corrected: empty-value lines can end
in a colon without a following blank. Match only label plus colon, preserving
every following byte. Regression tests cover both missing values and detection
of whitespace changes. No original input was changed by this correction.

## 4. Exact existing execution

Reuse the original support runner's released T0-11B and initial IA3 checkpoint,
30 epochs, batch 4, Adafactor/schedule/loss, balanced support selection,
seed order, split membership, question/choices, and batch-16 AUROC scorer.
Supports are parameter adaptation, not added in-context demonstrations.
No model, tokenizer, source tree or historical result is edited. Hash-bind
all code, protocols, split/data/source files, tokenizer/model files and IA3.

Grid: 9*3*1*4*5=540 reference cells, plus 180 shared intended cells.
New R2/R3: 9*2*1*4*5=360 cells, including **270 adaptation fits** and
90 zero-shot cells. Reuse compatible R1/intended artifacts only after validating
code/source/environment, initial checkpoint, memberships, prompts and
prediction hashes; otherwise rerun the exact fixed cell and disclose it.
The first 512-support bank/R2/ref_00/seed42 epoch (128 optimizer steps) may run
after the audit in a timing-only directory, without test scoring. It is not
evidence and must reset checkpoint/seed before every full fit. Record measured
epoch seconds and runtime projections as requested by the user.

## 5. Primary zero-shot analysis

U[d,n,s,f] = AUROC(I[d,n,s]) - AUROC(R[d,n,s,f]). Average AUROCs across the
five fixed seeds, then equally across the nine datasets. Never pool predictions
from different adapted models into one AUROC or count repeated seeds as
independent datasets. For car use equal-weight four-class one-vs-rest AUROC.
Primary contrasts are each family's n=0 macro utility and paired
U[R2]-U[R1], U[R3]-U[R1]. The intended term cancels in these paired effects.

Use 2,000 paired evaluation-row bootstrap replicates with RNG seed
20260910+dataset_index in the listed dataset order. For each dataset, sample
its union of test rows with replacement, separately within each true class.
Apply the same row multiplicity to all seeds containing that row, all families,
and all supports. Redraw a complete dataset replicate if any split loses a
class. Thus overlapping test splits do not create independent copies of a row.
Percentile 95% intervals condition on the fixed mapping and five fitted draws;
the macro is the fixed nine-dataset panel, not a population of all datasets.
Separately report paired 10,000-replicate dataset-resampling macro sensitivity
(RNG 20260910). Do not replace primary intervals by that sensitivity interval.

Apply the shared W4 categories to all nine dataset utilities. Report exactly
how many have identical categories in R1/R2/R3. If categories differ, label
reference-family sensitive. If categories agree and both paired effect CIs
are within delta, label reference-family robust; if at least one effect CI is
entirely outside the margin, label magnitude-sensitive; otherwise report
category agreement with magnitude unresolved. No raw-sign-flip criterion.

Primary A/B/C rules: C if either natural-family macro category differs from
R1; A if all three macro categories are positive, both effect CIs satisfy
equivalence, and >=7/9 dataset categories agree; B if all macro categories
are positive but A fails; unresolved otherwise. Always distinguish imprecision
from demonstrated absence or reversal. These rules cannot establish robustness
to mappings that this new experiment did not vary.

## 6. Secondary support attenuation and final interpretation

Report all four macro and dataset utilities, each adjacent support contrast,
endpoint attenuation U(0)-U(512), strict pointwise monotonicity, and
[U_f(0)-U_f(n)]-[U_R1(0)-U_R1(n)] for n=4,32,512 using the same row bootstrap.
Endpoint attenuation alone is not evidence of every intermediate inequality.
Intervals are pointwise; no simultaneous dataset-wide significance claim.

Final C if primary C, if an endpoint attenuation category differs from R1,
or if an endpoint family interaction CI lies wholly outside [-delta,delta].
Final A requires primary A, positive endpoint attenuation categories for all
three families, and equivalent endpoint interactions for both new families.
Final B requires all macro utility and endpoint attenuation categories positive
but fails A without triggering C. Otherwise final unresolved. Report both the
primary verdict and final verdict. Missing/inadmissible families => not evaluable.

Bound wording to these three realizations and this fixed primary mapping.
Even A does not directly demonstrate in-distribution prompts or rule out every
OOD mechanism. C narrows the TabLLM utility/attenuation claim rather than being
hidden. No manuscript claim is updated before validation.

## 7. Deliverables and scheduling

Store frozen design and audit manifests, mappings, train/test memberships,
every example's class probabilities/label/prompt hash/token count/truncation,
checkpoint and source provenance, paired bootstrap arrays, dataset/macro tables,
all support/family interactions, automatic verdict and provenance CSV bearing
the exact phrase above. Run input audit first, timing-only calibration next,
then zero-shot evidence/analysis, then nonzero support evidence/full analysis.
Use currently free GPU 2; GPU 1 and other users' occupied devices are excluded.
With historical per-dataset timing, new adaptation is approximately 27.1 hours
on one GPU; audit, zero-shot, analysis and overhead are additional. Timing may
change the estimate, never the grid or scientific rules.
