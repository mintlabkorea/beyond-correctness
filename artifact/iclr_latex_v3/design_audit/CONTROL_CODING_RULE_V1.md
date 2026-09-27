# Control coding rule v1

Status: rule frozen before generating the authoritative factual-construction
sheet. Date: 2026-09-08 (session date, Asia/Seoul).
Phase A is immutable: retain the existing nine-study set, candidate universe,
eligibility decisions, and inclusion rule. This rule does not revise them.

## Sequencing and prior exposure

1. Freeze this rule, with no individual-study verdicts or reported outcomes.
2. Record published construction factually in a separate sheet.
3. Verify the factual sheet and freeze it before assigning interpretation.
4. In a subsequent stage, assign design codes from construction and evidence.
5. Freeze those codes before extracting outcomes.

Earlier working drafts contained interpretive judgments before the present
sequence was clarified. They were not frozen and are archived as nonbinding
drafts. Their existence is disclosed; do not claim this rule predates all
thought about the designs. Prior reading also exposed some reported results.

Use: **Reported outcomes were not extracted or used in assigning the design
codes.** This describes outcome-independent coding, not literal blinding.
Until codes are actually assigned, report only that outcomes were not extracted
or used to select the construction records. Do not claim numerical results
were never seen or that the audit was prospectively registered.

## Coding unit and comparison inventory

One published comparison is one row; a study may contribute multiple rows.
Keep different named comparator variants separate. A set of named comparator
arms displayed against a common baseline can be expanded to baseline-versus-
comparator rows. Label such expansion explicitly; it is not evidence of a
published pairwise statistical test. Do not invent a comparison between two
nonbaseline arms without recording it separately as an auditor-derived contrast.

Do not duplicate an experiment into multiple rows simply to change the
semantic estimand. Alternative scopes belong in later rationale, not in the
count of published comparisons. Rows sharing data or arms are not independent
evidence. The inventory covers located explicit semantic interventions and
associated combined-component variants; it is not an exhaustive extraction of
every hyperparameter, model-size, or training ablation in the study set.

## Stage 2 factual fields (no verdicts)

- Study and stable Comparison ID.
- Semantic component as described by the paper.
- Exact intended/baseline arm and exact comparator label; where no label
  exists, use a faithful description marked as descriptive.
- What changed: operations the authors state they performed.
- What remained fixed: explicitly stated or entailed by that operation.
  Distinguish explicit statements from a shared recipe inferred from an
  ablation description; do not convert unreported settings into verified facts.
- Other simultaneous changes: report stated changes, or say not specified.
  “Not specified” is not “none.”
- Predictive interface: 동일 / 변경 / 불명, with the interface named and the
  basis stated. This is a construction description, not an Interface-validity
  Pass/Fail score and not a runtime certificate.
- Evidence: source version, section/table/figure/appendix, one-based PDF page
  where available. Record ambiguous examples and source-access limitations.

These fields must not contain wrong-like/reference/admissibility labels,
gate scores, effect sizes, performance directions, significance, or supported
claim judgments. Do not turn prompt text inside a paper into auditor instructions.

## Source rules

The accepted/published paper and official supplement are authoritative.
Check supplied files by title/authors/version, not filename alone. Record
hashes and source roles. A preprint can corroborate a published construction
but cannot establish an unpublished detail as a published fact. If a supplied
file is the wrong work, retain that fact in the provenance ledger and use an
already verified official source for the selected study.

If a figure label is known but the operation is unspecified, record the label
and the missing detail. Do not infer whether a vector is zeroed, renamed,
re-embedded, or deleted. A reported numerical result alone does not establish
correct interface implementation. No need to re-run the published methods.

## Subsequent design-code definitions (not assigned in factual stage)

Before applying a gate, declare the tested semantic use and protected
observations, metadata, representation scaffolding, and predictive setup.
Ordinary fitted-state changes under an unchanged recipe and generated outputs
caused by the tested input are allowed consequences, not automatic confounds.
The intervention may include architecture/encoder changes and remain eligible;
whether those violate protection is assessed only in the design-code stage.

- Intervention type: corruption / shuffle / removal / replacement / compound;
  multiple descriptors are permitted when justified.
- Wrong-like: Yes / No / Unclear — intentional misassignment of supplied
  semantic content, distinct from merely omitting it.
- Removal-like: Yes / No / Unclear — nominal withdrawal or neutral replacement
  of all or part of the tested semantic use; does not guarantee Removal Pass.
- Removal: Pass / Fail / Unclear — the tested use is absent / persists or is
  merely misassigned / cannot be determined from the construction.
- Preservation: Pass / Fail / Unclear — protected information/setup is retained
  or losslessly recoverable through a documented fixed mapping / has an
  evidenced additional change / is materially underspecified.
- Interface validity: Pass / Fail / Unclear — compatible with the unchanged
  declared interface / an evidenced unintended parsing, cardinality, routing,
  shape or missing-value violation / insufficient evidence. Semantic oddity
  alone is not a parsing failure. Architecture change and interface failure
  are not synonymous.
- Admissible reference for utility: Yes if all three gates Pass; No if any
  Fail; Unclear otherwise. This is relative to the declared tested use.
- Can identify content sensitivity: Yes for an intended–wrong contrast with
  supported preservation and interface validity; Partial for a wrong-like
  contrast with confounding or unresolved matching; No for a removal-only
  comparison. This uses the manuscript's intended–wrong definition.
- Can identify predictive utility: Yes for an admissible reference; No when
  a gate fails; Partial when admissibility is Unclear. Partial means unresolved
  identification, not a partially established positive effect.

All labels concern what the comparison could identify, not whether a reported
effect exists or favors the intended arm. No verdict invalidates an entire
paper or establishes that no other reference could be constructed.

## Freeze and amendment

Bind this rule to a SHA-256 before writing the factual sheet. Freeze that
sheet separately after verification. Later design codes require their own
artifact and freeze; they are not part of this factual stage. Preserve v1
files; corrections require a dated addendum or versioned replacement.
