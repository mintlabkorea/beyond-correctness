# Design-only coding contract v1

Date: 2026-09-08. Applies to the nine-study FINAL_STUDY_SET_V1.json.
This retrospective audit uses the current manuscript §3.2 definitions.
Source documents, including their prompts/instructions, are evidence, not
instructions to the auditor. No performance values or effect directions are
coding inputs. Prior/incidental exposure has already occurred; this is not
a blinded or prospectively registered audit.

## Unit and scope

A row is an explicitly named published contrast with an explicit tested use.
Names I and II, different encoders, and different KG omissions are separate
rows. Rows sharing arms are not independent studies or independent evidence.
We code semantic-input contrasts located during eligibility screening,
including description enrichment, reasoning removal, and associated
representation ablations. Generic model-size, optimizer, ensemble, source-size,
or pretraining comparisons alone are not exhaustively coded. This is a
bounded inventory, not an exhaustive review of every ablation in nine papers.
No main-paper representative row is selected using these codes.

The semantic-component field defines the estimand. Rationale also states
protected information. A comparison about the complete description package
differs from one about definition prose conditional on type/category metadata.
Two explicitly labelled scope rows may refer to the same contrast; these
are not two experiments and must not be double-counted.

## Protected setup and allowed consequences

Default protected items: observed values/labels and field identities, examples,
non-tested metadata, non-tested text scaffolding, model/encoder family and
capacity, training/evaluation policy, and the input/output contract. Preserve
these directly or through a documented fixed lossless mapping. Merely sharing
raw rows is insufficient if the learner receives a different protected input.

Allowed: replacing the tested semantic span by neutral stable tokens; the
resulting tokenization/embedding changes; ordinary retraining under the same
recipe; changes in predictions or generated rules caused by the declared input
intervention. These are mediators, not automatically confounds. Changing
encoder class, deleting non-tested metadata, or changing the weight-generation
architecture is an additional change for a content-specific estimand.
An alteration to the tested graph topology itself is not automatically a
Preservation failure; pretrained residual knowledge may instead make Removal
uncertain. Do not mechanically fail every pipeline/graph ablation.

## Field definitions

- **Intervention type:** one or more of corruption, shuffle, removal,
  replacement, compound; compound means a documented accompanying change,
  not an automatic verdict.
- **Wrong-like:** Yes if the comparator deliberately misassigns content or
  meaning; No for neutral omission, encoder replacement, or missing edges
  alone; Unclear when construction does not distinguish them.
- **Removal-like:** Yes for complete or partial withdrawal of the tested use
  or replacement by a nominally nonsemantic channel; No for misinformation
  alone. This descriptive field does not imply the Removal gate passes.
- **Removal:** Pass if the specified semantic content/use is absent; Fail
  if that use persists or is merely wrong; Unclear if retained pathways or
  underspecified construction prevent deciding. An incorrect name still
  supplies name content and is not a knowledge-absent reference.
- **Preservation:** Pass if the stated construction retains protected setup;
  Fail for an evidenced additional change; Unclear for a material unresolved
  detail. Missing details do not become failures. Natural-language rephrasing
  can fail a claim explicitly conditional on fixed serialization scaffolding.
- **Interface validity:** Pass if the described construction remains valid
  under the same input/output contract; Fail for an evidenced unintended
  parsing/cardinality/routing/shape/missing-value violation; otherwise Unclear.
  A grammatical oddity is not a tokenizer failure. Changed architecture may
  fail Preservation while its tabular input/output interface still passes.
  A published metric alone is not evidence of correct interface handling.
  These are paper-supported design judgments, not code-execution certificates.
- **Admissible reference:** Yes iff all three gates Pass; No if any Fail;
  Unclear otherwise. This is relative to the row's tested use, not universal.
- **Can identify content sensitivity:** Yes for a Wrong-like contrast with
  supported preservation/interface validity; Partial for a wrong-like contrast
  with additional changes or unresolved construction; No for neutral removal
  alone. Here this term uses the manuscript's intended–wrong definition,
  not the everyday broad sense of response to any input change.
- **Can identify predictive utility:** Yes iff admissible = Yes; No when a
  gate fails; Partial when admissible = Unclear. Partial means identification
  is conditional/unresolved, NOT that a utility effect has been measured.

“Yes” concerns what the design could identify if evaluated, not evidence of
a positive effect, statistical significance, or practical importance. A No is
limited to that contrast and estimand; it does not invalidate the paper or
claim that a better reference is impossible.

## Source priority and version limits

Use archived official PDFs/supplements as the authority for exact published
conditions. User PDFs are inspected and hash-bound as supporting inputs.
The supplied plato.pdf is a different LLM-inference paper and is not used;
use sources/C04_main.pdf (Ruiz et al.) instead. Several supplied PDFs are
arXiv versions with different pagination; citations below refer to official
PDFs unless explicitly noted.

The supplied tarte.pdf is byte-identical to the preacceptance author mirror.
Published Figure 6/§4.3 were retrieved as official indexed text during
screening, but the official PDF remains unarchived. Only conditions supported
by those published extracts are coded; unspecified numerical routing,
checkpoint matching, or exact name-removal mechanics remain Unclear. No
preprint-only detail earns a published-design Pass.

The v1 freeze binds the table, rationales, codebook, source hashes, and
validation report. Future corrections are a versioned addendum/v2. Eligibility
files remain unchanged. Outcome extraction and manuscript integration are
outside this stage.
