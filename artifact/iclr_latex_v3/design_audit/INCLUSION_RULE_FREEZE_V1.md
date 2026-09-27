# W8 published semantic-knowledge design audit — inclusion freeze v1

Status: FROZEN before external candidate lookup in this work session.
Session date: 2026-09-08 (Asia/Seoul, supplied environment).
Filesystem clock at freeze: 2026-09-07T15:35:05Z; retain this literal clock
reading rather than treating the timestamp as an external registration.
Scope authorized now: freeze rules, then create an 8–10-study candidate list.
Full-text eligibility screening, final study selection, control coding,
outcome extraction, and manuscript integration are subsequent stages.

## Purpose and unit

Assess which claims published semantic-knowledge comparisons can identify
under the current manuscript's removal, preservation, and interface-validity
criteria. This is a bounded, retrospectively assembled design audit, not an
exhaustive systematic review, a method leaderboard, or a replication study.
Study is the eligibility unit; each distinct semantic intervention and
published comparison will be a separate coding unit in later stages.

## Frozen inclusion rule

Include a study if ALL of the following are supported by its published paper
or associated official supplement:

1. **Published:** a peer-reviewed full conference or journal paper, published
   or officially accepted by 2026-09-08. An official acceptance record suffices
   if proceedings are pending. Preprint-only, workshop-only, proposals, and
   unpublished code extensions are outside the primary sample. Use the
   accepted/published version; do not import later arXiv-only ablations.
2. **Predictive tabular task:** at least one classification or regression task
   predicts a target from tabular records/features. Both single-table and
   cross-table studies are eligible; record that scope separately. A table
   serialization or a table-derived graph does not itself disqualify a study.
3. **Explicit semantic input/use:** the method uses feature/column names or
   descriptions, semantic verbalization (including values/labels), dataset
   documentation or context, codebooks, external rules, an auxiliary knowledge
   graph, or schema/cross-table identity in constructing or learning the
   predictor. Purely statistical pretraining or arbitrary column indices alone
   do not establish this criterion.
4. **Published semantic intervention:** at least one reported predictive
   comparison deliberately removes, corrupts, replaces, or otherwise changes
   that semantic input/use relative to a specified intended condition.
   Architecture/encoder/pipeline changes may accompany it: such comparisons
   remain eligible, since their admissibility is a later coding question.
5. **Traceable design:** the paper/supplement identifies the semantic component,
   compared conditions, and a section/table/figure sufficient to locate the
   comparison. Incomplete preservation details are coded as unclear later,
   not used to exclude an otherwise identifiable ablation.

No requirement that the intended arm wins, that an effect is significant,
that a control is admissible, that all three arms exist, that the authors use
our vocabulary, or that code/checkpoints are available. No requirement for a
particular learner, support budget, or schema-transfer setting.

## Exclusions and unresolved cases (for later screening)

- E1: publication criterion fails.
- E2: no predictive tabular task (e.g. schema matching, table QA/retrieval only).
- E3: no explicit semantic input/use.
- E4: no semantic intervention; only SOTA/model comparisons or generic tuning.
- E5: synthesis is the primary task and there is no separate predictive
  comparison intervening on semantic information.
- E6: duplicate version of the same study (merge under the publication).
- U1: full text/supplement or official status unavailable; unresolved, not
  evidence that an ablation is absent.

Do not exclude a compound intervention because it will not identify
component-specific utility. Apply the same rules to TabLLM, TransTab, CARTE,
Gardner et al., and newly found studies. Our own post-result experiments do
not establish an original study's eligibility.

## Candidate discovery and stopping rule

1. Start with predictive semantic methods named in current main.tex Related
   Work and its LIFT/TabLLM control paragraph. Consult references_seed.bib for
   identity; a bibliography-only citation is not automatically an RW seed.
2. Add recent (2025–cutoff) predictive semantic tabular methods found through
   official proceedings/OpenReview/publisher records. The user-supplied
   ConTextTab and TabSTAR leads are disclosed discovery inputs.
3. Search identity/publication and semantic-method relevance first. Use
   queries for `ConTextTab`, `TabSTAR`, and `semantic tabular foundation model
   2025 2026`; retain query/source notes. Do not search for favorable outcomes
   or control failures. Stop at 8–10 distinct plausible candidates; if more
   equally relevant additions are available, prefer newer official publication
   date, then title alphabetically, without consulting control verdicts.
4. The candidate list is not the eligible sample. In the NEXT stage screen
   every listed study in ID order, recording inclusion/exclusion/uncertainty
   with source locations. Retain all eligible studies from that list; 6–8 is
   a planning expectation, not a quota. If too few qualify, register a dated
   search expansion before seeking replacements. Do not replace exclusions
   silently or drop eligible studies to obtain a desired mixture of verdicts.

## Prior exposure and sequencing

The user's pasted brief already contains candidate names, asserted ablation
details, qualitative results, and anticipated control classifications. The
project also already analyzed TabLLM and ran TransTab/CARTE extensions. Thus
neither initial discovery nor this freeze is fully outcome-blind or a
prospective preregistration. Those assertions are leads, not verified coding.

From this freeze onward, performance direction/magnitude and anticipated
classification must not determine eligibility. Record incidental exposure
from search snippets/abstracts; do not claim results were never seen.

Later sequence: full-text eligibility -> freeze eligible set -> code control
construction with evidence -> freeze design codes -> extract reported outcomes
-> write supported claims. Keep outcomes out of the candidate/design sheets.
Wrong/reference/compound labels, Removal/Preservation/Interface verdicts, and
supported-claim judgments remain unassigned at the current stage. Preserve all
three manuscript criteria; do not preemptively demote interface validity.

## Change policy

Preserve this v1 file. Any changed eligibility/search rule requires a dated
v2/addendum describing the reason and affected studies. A local SHA-256
sidecar binds v1 before external candidate lookup; it is an integrity record,
not proof of independent registration or blinding.
