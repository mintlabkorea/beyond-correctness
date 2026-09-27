# W5 reported-claim codebook — frozen before extraction/coding

Date: 2026-09-10. Reviewer-triggered retrospective addition, not prospective
registration. Preserve the existing 9 studies and 25 comparison IDs exactly.
Do not modify manuscript files, the existing audit, or its support codes.

## Unit and attribution

One original published comparison is one unit. Code claims actually attributed
to that comparison's semantic intervention. Never inherit general model-level
marketing claims, an architectural benefit, or a different comparison's claim.
Use the fixed intended/comparator labels and semantic component in UNITS_V1.json.
If a paragraph explicitly interprets a named table/figure comparison group, it
may apply to that group, but only where it addresses the unit's semantic scope.
Record linkage as explicit_comparison, explicit_group, ambiguous, or none.
A positive result alone does not supply an author interpretation.

## Fixed claim window

For each comparison inspect (1) table/figure caption, (2) paragraph introducing
the result, (3) immediately following interpretive paragraph, (4) relevant
subsection conclusion. Include abstract/introduction/conclusion text ONLY if it
explicitly links the particular ablation. Record every window component,
including absent/no separate paragraph, with source file, PDF page and text
line ranges. If a result table has no claim, do not invent one. Shared windows
are permitted and remain attributable to the original comparison IDs.
Source access/version uncertainty must be recorded and cannot become a No.

## Two independent axes: Yes / No / Unclear

claim_content = Yes only for an explicit claim that the model uses, relies on,
depends on, exploits, utilizes or is sensitive to semantic CONTENT, including
an interpretation of shuffled semantics affecting prediction. Do not infer
this claim merely from a generic performance change or from benefit language.

claim_utility = Yes only for an explicit interpretation that semantic knowledge
itself improves, helps, benefits, provides gains, or contributes to predictive
performance. "Removing it hurts" counts only when interpreted as knowledge
benefit. "Important/effective for performance" counts; generic "important"
without predictive-benefit linkage does not. Conditional benefit claims (for
some budgets/datasets) count Yes, with the condition preserved in rationale.
Explicit findings of no benefit are not positive utility claims: record No and
the negative interpretation, with descriptive_only=No.

Unclear: wording such as "feature names matter", "semantic information is
important", or "the role of textual information" does not distinguish use
from benefit; use Unclear on the ambiguous axis rather than manufacturing Yes.
Use Unclear if the comparison linkage or source coverage is insufficient to
decide that axis. The axes can both be Yes, both be No, or independently unclear.

No: no claim on that axis in the COMPLETE available window. Numeric results
alone, hypotheses/questions without an asserted answer, and condition labels
are not claims. descriptive_only=Yes only when both axes are No and the window
contains reporting without a substantive semantic interpretation; otherwise No.

## Evidence and output

For each unit output comparison_id, study, claim_content, claim_utility,
descriptive_only, claim_text (brief exact excerpt from the masked packet),
claim_location, linkage, claim_scope, rationale (1–2 sentences), coder_id.
No paraphrase inside quote fields. Use [NUM] where numeric masking is present;
never reconstruct numeric outcomes. No extra-textual evidence. For No use a
representative reporting passage plus the complete window inventory. For
Unclear preserve the ambiguous words and explain the ambiguity.

## Independent Phase B

Coders A and B are separate fresh AI-agent contexts with no conversation
history. They receive only this rule, fixed unit labels, and one common
source-text claim packet. Performance numeric magnitudes and original support
labels/rationales are withheld. Qualitative benefit language is retained because
it is the object being coded. Do not access original audit files, outcome
tables, full PDFs, each other's outputs, or sibling files outside the packet.
The read boundary is instructional within a shared workspace, not an enforced
filesystem sandbox. The coordinating extractor has prior design/result exposure;
do not call source selection or the whole audit outcome-blind. Record this limit.
No coder may consult the other or edit a frozen submission. Freeze raw A/B
files before agreement and adjudication; no feedback loop to improve agreement.

## Reliability, adjudication, and merge (frozen decision rules)

Report pre-adjudication exact agreement and unweighted Cohen's kappa on each
three-level claim axis, and separately descriptive_only. Include confusion
matrices and label marginals; undefined kappa remains undefined. Comparisons
share studies/arms; no independence-based CI or significance test for kappa.
This measures same-model AI coding reproducibility, not independent human
inter-rater reliability. An independent adjudicator sees packet + frozen A/B
claims only, with old support codes still withheld; disagreements receive an
explicit source-based decision, and Unclear is allowed. Also review agreed
claims for scope/attribution errors and log any such correction separately.

Only after adjudication freeze, join the existing support codes by original ID.
Existing Yes -> Supported; No -> None; Partial/Unclear -> Unclear. Apply to each
axis: Yes+Supported=Matched, Yes+None=Mismatch, Yes+Unclear=Indeterminate;
No+anything=Not claimed; Unclear+anything=Indeterminate (ambiguous-claim flag).
Report Yes-claim denominators separately from all 25. Never count absent or
ambiguous claims as definitive mismatches. Cross-tabulate all 3x3 claim/support
cells and the derived four states; provide comparison and study counts without
treating them as independent evidence. Do not call support=None a paper defect.

Optional support reliability uses the two ALREADY FROZEN independent primary/
secondary design codings, without rewriting either. Compute raw agreement and
kappa for content and utility support, show scope differences and a sensitivity
merge using secondary codes. Label this historical two-AI reproducibility;
it does not constitute new blinded support coding or independent human validation.

## Selection and deliverables

Use existing candidate/search/screening records only. No new studies,
comparisons, or candidate search. Recover the actual bounded retrospective
discovery history (including prior exposure and source-version caveats), not a
fabricated systematic search or PRISMA denominator. Produce a 25-row merged CSV,
frozen raw coder sheets, quotes/locations, agreement/kappa, adjudication ledger,
cross-tabs, historical support sensitivity, and review report. Files only;
do not edit main.tex, appendix.tex, figures or manuscript tables.
