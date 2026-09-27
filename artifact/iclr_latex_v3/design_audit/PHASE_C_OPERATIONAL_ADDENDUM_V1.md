# Phase C operational addendum v1

Date: 2026-09-08. Supplements, without rewriting,
CONTROL_CODING_RULE_V1.md. Implements the user's Phase C clarification and
review attachment. The nine-study set is unchanged. The factual basis is the
corrected and frozen 25-comparison construction v1.1.

## Scope before verdict

For each comparison first record: tested semantic use, protected observations,
protected metadata, protected representation, and protected predictive setup.
The scope sheet is hash-bound before the authoritative gate file is created.
These are auditor-declared estimands reconstructed from published contrasts,
not claims that the original authors prespecified our requirements. Alternative
scopes can be discussed but do not create additional comparison rows.

Ordinary changes in embeddings, fitted weights or generated features caused
by an intervention under a fixed recipe are mediators. They do not themselves
violate preservation. In contrast, a different encoder family, unrelated
architecture/training change or removal of protected metadata requires its own
evidential assessment. The scope cannot be retrospectively adjusted to make a
reference pass after seeing results.

## Three gates, independently justified

Removal: whether the declared supplied semantic use is absent, not whether
the underlying facts become unrecoverable from every other input. Wrong
content still supplies that channel; partial removal of a whole KG is not
complete absence. Distinguish removing explicit input from erasing pretrained
knowledge. Retained pathways without sufficient documentation imply Unclear.

Preservation: evaluate the protected information and setup relative to the
scope. A target-header change is an additional change for a feature-header-only
scope, but a tested change for joint feature-and-target-header semantics.
Do not hide that choice or infer information equality from similar raw inputs.

Interface: assess meaningful comparability, not merely accepted token counts
or identical model names. Inspect (i) model pathways, (ii) availability and
routing of protected representations, (iii) training/adaptation opportunity,
and (iv) predictive interactions accessible in each arm. Also check the
original rule's parsing/cardinality/shape/missing-value requirements.

**An intentional encoder or architecture replacement is not automatically an
Interface failure.** Fail requires evidence of a mismatch that makes the
specified comparison invalid at its interface (e.g. an incompatible input,
unintended missing pathway, or demonstrated unequal opportunity that defeats
the declared contract). If the construction simply leaves substantive
compatibility unresolved, use Unclear, even if Preservation independently
fails. Report architecture changes under Preservation where appropriate;
do not double-count them as an unsupported execution failure.

Pass may rest on an explicit same-model, same-recipe construction with only
the declared input span altered; it is a documentary design judgment, not a
runtime guarantee. Unreported random seeds or absence of reproduced runs alone
do not force Unclear. Material ambiguity in routing, pretraining/adaptation,
information availability or inconsistent examples does. A published metric
alone cannot establish interface validity. No required proportion of Pass,
Fail or Unclear is imposed.

## Evidence and derived fields

Each of the three gate cells contains **Pass / Fail / Unclear — source
location: reason**. No bare-verdict cells. Store the enum, source locator and
rationale separately in machine-readable form as well. Each row additionally
records the four substantive interface checks and their sources.

Preserve the multi-axis fields: intervention type, wrong-like, removal-like,
and the three gates. Admissible reference is derived: all Pass -> Yes; any
Fail -> No; otherwise Unclear. Identify utility as Yes/No/Partial by that rule.
Identify content sensitivity using the original intended–wrong definition:
Yes for a supported matched wrong contrast, Partial for a wrong contrast with
confounding/uncertainty, No for removal-only contrasts. These derived labels
are design capability, not an observed benefit or supported empirical claim.

No mutually exclusive global Wrong/Reference/Compound classification is
required. No favorable/unfavorable/null outcome is recorded. Use the statement:
**Reported outcomes were not extracted or used in assigning the design codes.**
Prior exposure and the earlier nonbinding draft are disclosed. This addendum
and the new coding are retrospective, outcome-independent judgments, not
independent double coding or literal blindness. Do not copy the archived
unfrozen draft as authoritative evidence.
