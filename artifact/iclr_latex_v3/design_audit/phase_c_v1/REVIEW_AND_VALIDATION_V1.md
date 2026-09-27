# Phase C review and validation record

Date: 2026-09-08 (session date). Final status: 25 scoped comparisons across
the unchanged nine studies; three evidence-backed gates and derived
identifiability fields frozen. Reported outcomes and empirical supported claims
remain unextracted.

## Corrections and actual chronology

The user's review recommended dropping the procedural C06-B comparison and
changing LIFT C01-C/D's factual interface to Unclear. Both were applied through
CONSTRUCTION_CORRECTION_V1_1.md, not silent edits. The previous factual record
had already been frozen, so the correction is honestly recorded as **after v1
freeze, before authoritative Phase C coding**. The old v1 remains intact.

The factual v1.1 freeze and Phase C operational addendum preceded the scope
sheet. CLAIM_SCOPES_V1 was hashed before build_codes.py and the gate artifacts
were created. These local records establish an artifact sequence, not an
independent preregistration. Earlier nonbinding interpretive drafts already
existed and were explicitly disclosed; this is not claimed as a first-ever
outcome-blind judgment.

## Interpretation review

- Each comparison has one declared scope and four protection fields before
  its codes. The descriptions specify an auditor's component-level question,
  not an assertion that original authors used the same estimand.
- C07-A tests **joint feature-and-target headers**. Under a feature-only scope,
  changing target Y would be an additional metadata change and Preservation
  would fail. That alternative is a scope caveat, not another comparison row.
- C06-A tests the **whole description block**, including types and categories.
  Its common generation recipe can preserve the remaining setup even though
  generated rules change. Interface remains unresolved without the edited
  prompt/type-handling details. A prose-only scope protecting type/category
  metadata would have a different Preservation verdict; do not report the
  package-scope result as isolated utility of prose.
- The LIFT example inconsistencies are retained as uncertainties, not silently
  corrected or asserted to be executed bugs. The unnamed comparator's gate
  rationale distinguishes documented accompanying changes from unknown
  dataset-wise variant implementation.
- Encoder/architecture changes do not automatically become Interface Fail.
  CARTE/ConTextTab replacements and PLATO's MLP switch have explicit
  Preservation reasoning and independent interface assessments. Many have
  insufficient published compatibility detail. No quota for Interface Fail
  was imposed; no such failure is established by this evidence set.
- Interface Pass for declared same-path text replacement is documentary:
  pathways, available representations, training opportunity and interactions
  are supported by the stated operation. It is not a reproduced execution or
  identical-token-count certificate. TabLLM values-only has a valid described
  LM contract while failing the narrower protected serialization requirement.
- TabSTAR tests explicit verbalization with the separate numeric path retained
  by the described architecture. It does not test removal of all numerical
  information or whether verbalized information is statistically recoverable.
- TARTE's published labels support the recorded contrasts, but not precise
  numerical routing or adaptation. The preprint cannot fill those gaps with
  an accepted-version Pass. The MinHash comparison also changes table-model
  pretraining; no alternative nonbaseline pairing replaces it.

## Machine-checkable checks

validate_codes.py checks:

1. Exactly 25 comparison IDs and nine studies; C06-B absent; no replacement
   studies or invented additional comparisons.
2. Exact linkage to frozen construction and scope strings.
3. Three gates per row, each containing an allowed enum, source locator and
   nonempty reason: 75 evidenced gate cells, no bare-verdict cells.
4. Four substantive interface dimensions per row, each with an observation
   and source evidence.
5. Derived admissibility and content/utility capability follow the frozen
   arithmetic rules and cannot contradict gate values.
6. CSV cells include verdict, locator and rationale; JSON/CSV/Markdown agree.
7. Phase A, original Phase B, factual v1.1, scope and source hash bindings
   remain valid. The final bundle contains scripts and human-readable notes.

The validator checks consistency and traceability, not scientific correctness
independently of the auditor. The documentary reasoning above was reviewed
against the construction record and relevant source text; this remains a
single-auditor assessment, not double coding or model reproduction.

**Reported outcomes were not extracted or used in assigning the design
codes.** Numbers/directions had been incidentally exposed during PDF reading;
literal blinding is not claimed. Identifiable=Yes means a possible estimand,
not a positive, significant, generalizable or practically useful effect.
Partial means conditional/unresolved identification. No outcomes file,
supported-claim synthesis, or manuscript edit was created in this phase.

## Authoritative artifacts

- CLAIM_SCOPES_V1.json / .csv: pre-code scope/protection snapshot.
- CLAIM_IDENTIFICATION_V1.md / .csv / .json: source-backed judgments.
- DESIGN_CODE_FREEZE_V1.json / .sha256: final immutable snapshot binding the
  corrected facts, rule/addendum, scopes, source references, scripts and codes.

Corrections after this freeze require a new version/addendum. The next stage
can extract reported outcomes against these fixed comparison IDs; it must
not revise the design judgments to match those outcomes.
