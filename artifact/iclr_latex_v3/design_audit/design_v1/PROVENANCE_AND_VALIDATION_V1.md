# Phase B steps 5–6: provenance and validation

Session date: 2026-09-08 (Asia/Seoul).

## Authoritative sequence and status

1. Phase A files were retained byte-for-byte; their existing checksum bundle
   passes. The eligible set remains nine studies; TransTab remains excluded
   for absence of a located published semantic intervention, not control quality.
2. After the user's sequence clarification, the earlier generated gate table,
   source-aware codebook and generator were moved to unfrozen_draft_archive/.
   They were never frozen and are not authoritative. They contain premature
   interpretation and cannot silently supply later final judgments.
3. CONTROL_CODING_RULE_V1.md was written with definitions only, then hashed
   before the authoritative factual-construction generator/sheets were created.
4. CONTROL_CONSTRUCTION_V1 records construction only: 26 rows, nine studies,
   ten requested fields. No later design-code table has been frozen.
5. This factual snapshot is hash-bound for the next stage. Local hashes record
   file integrity; they are not an external preregistration or blinding proof.

## Supplied-file identity and authoritative evidence

| Study | Supplied file | Source used for published-condition authority |
|---|---|---|
| LIFT | figures/LIFT.pdf, combined 54-page version | sources/C01_main.pdf + C01_supp.pdf; distinguish printed and PDF page numbers |
| TabLLM | figures/tabllm.pdf | sources/C03_main.pdf; supplied paper corroborates definitions |
| PLATO (Ruiz et al.) | figures/plato.pdf is **a different paper**, *Plato: Plan to Efficiently Decode for Large Language Model Inference*, Jin et al., arXiv:2402.12280v2 | sources/C04_main.pdf, *High dimensional, tabular deep learning with an auxiliary knowledge graph*, Ruiz et al., NeurIPS 2023 |
| CARTE | figures/carte.pdf | sources/C05_main.pdf, official PMLR copy |
| FeatLLM | figures/featllm.pdf | sources/C06_main.pdf, official PMLR copy |
| TabuLa-8B | figures/tabula.pdf, 44-page supplied version | sources/C07_main.pdf, 51-page proceedings version |
| ConTextTab | figures/contextab.pdf, 29-page supplied version | sources/C08_main.pdf, 36-page proceedings version |
| TabSTAR | figures/tabstar.pdf, 47-page supplied version | sources/C09_main.pdf, 54-page proceedings version (pagination checked from local text) |
| TARTE | figures/tarte.pdf, arXiv:2505.14415v2, preacceptance | Official indexed published Figure 6/§4.3 evidence recorded in ELIGIBILITY_SCREEN_V1.md; supplied preprint only corroborates, does not replace accepted-version evidence |

The supplied TARTE file is byte-identical to sources/C10_author_mirror.pdf.
It does not resolve the previous official-PDF archival caveat. Published
condition labels can be recorded; exact implementation not established by the
published extract is marked unspecified. The incorrect PLATO attachment is
retained unchanged and hash-recorded, but none of its technical contents is
used in the selected study's construction record.

Supplied PDFs and official archives have separate hashes/roles in
CONSTRUCTION_SOURCE_MANIFEST_V1.json. All evidence citations in the sheet refer
to the official pagination unless explicitly labelled otherwise. Different
PDF hashes or page counts are not treated as proof of substantive disagreement.

## Inventory boundaries

- Four LIFT format-specific pairs; three TabLLM serialization pairs; three
  PLATO KG pairs; three CARTE component pairs; two FeatLLM generation pairs;
  one joint-header TabuLa-8B pair; six ConTextTab semantic pairs; two TabSTAR
  verbalization pairs; two TARTE figure-baseline pairs.
- One comparator arm per row. One experiment is not duplicated merely to
  protect a different semantic scope. All nine selected studies are represented.
- Combined-component comparisons are retained. Their eventual admissibility
  has not been decided by the factual sheet.
- The inventory is the located semantic-input comparisons plus associated
  combined-component variants, not every possible experiment in each paper.
  Examples outside this inventory include generic tuning/pretraining-size
  studies, CARTE's attention-only/initial-edge-layer-only variants, and TARTE
  source/sampling/datetime variants. Those are not exclusions of studies and
  must not be used to claim all ablations in these papers were exhaustively coded.
- ConTextTab enrichment is displayed with the enriched condition as intended;
  both arm identities remain explicit. TARTE's MinHash condition is contrasted
  against the published Enriched YAGO4.5 baseline; its different pretraining
  status is recorded. No matched-random-weights comparison is invented here.

## Verification and limitations

- Original Phase A checksums and coding-rule checksum pass.
- Comparison IDs are unique, ordered by study, and drawn from the fixed set.
- All ten required construction fields are populated; CSV/JSON/Markdown
  records agree. Validation also checks the official-source page counts.
- No wrong-like/removal-like/admissibility/gate/supported-claim fields are
  present. No result values, directions, or significance claims are extracted.
- Source observations include ambiguity rather than silently repairing it:
  inconsistent LIFT examples, unspecified CARTE edge removal, unspecified
  FeatLLM edited prompts, contextual-description sampling access, and TARTE
  published-version implementation gaps.
- A shared recipe is explicitly labelled as such; it is not proof of exact
  checkpoint, seed, split or implementation equality. Interface 동일/변경/불명
  describes the named construction boundary, not validity or measured success.
- This is a single-auditor documentary record, not independent double coding
  or an execution-based reproduction.
- Earlier PDF reading and current surrounding text exposed some outcomes.
  They were not extracted into this record or used to choose its construction
  entries. Do not claim literal outcome blindness. At the later code stage,
  use the wording specified in CONTROL_CODING_RULE_V1.md about outcomes not
  being extracted or used to assign design codes.

Next: assign design codes from this construction sheet under the frozen rule,
with explicit claim scope and reasoned uncertainty. That step, outcome
extraction, and manuscript integration have not been performed in this
authoritative sequence.
