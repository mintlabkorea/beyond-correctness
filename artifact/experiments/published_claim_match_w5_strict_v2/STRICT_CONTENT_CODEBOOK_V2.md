# W5 v2: strict semantic-content claim coding

Frozen before new coding, 2026-09-11. User-directed definition correction.
Keep all 25 original comparisons, nine studies, and the exact v1 source windows.
Do not recode utility, original control support, or descriptive_only. Preserve v1.
No manuscript edits. This is a retrospective revision, not preregistration.

## Target claim (user's definition)

**The authors interpret the comparison as showing dependence on the particular
semantic content supplied, rather than merely showing that the semantic
component matters or is used.**

The question is what the authors claim, not whether their control supports it.
Do not inspect or infer the original support labels. A poorly controlled
comparison can still carry an explicit strong claim and must then be coded Yes.
Do not mechanically set No for removals or Yes for shuffles: read the attributed
interpretation. This separation prevents tautologically agreeing claim/support.

## Yes / No / Unclear

Yes requires an explicit interpretation about the PARTICULAR supplied meaning,
semantic assignment, correspondence, association, direction, or correct versus
altered semantic content. Examples of claim strength (not paper-specific labels):
"predictions depend on which meaning is assigned to a feature"; "the effect
depends on correct feature/value association"; "changing the supplied semantic
assignment changes prediction". The authors need not use our technical term or
claim that every experimental confound was controlled. Preserve qualifications.

No means the complete window does not assert that stronger claim. Statements
that semantics are used/exploited/leveraged, a component matters, information is
important, or removing/adding a component changes performance are insufficient
on their own. An explicit weak use/dependence claim is now No on this STRICT
axis, not automatically Unclear. Benefit language alone also does not imply the
stronger content claim. Numerical differences or the intervention label alone
are not an author interpretation.

Unclear means the wording genuinely leaves strict versus weak strength
ambiguous, the particular comparison's linkage is unresolved, or source/version
coverage prevents deciding the original publication's claim. Do not fabricate
strict content claims from incomplete or preacceptance sources. TARTE's local
arXiv-v2/accepted-version gap is unchanged. It cannot establish a verified
published claim and must be disclosed.

## Attribution and unchanged claim window

Use only the supplied packet: caption, introducing paragraph, following
interpretation, subsection conclusion, and already-extracted explicitly linked
summary passages. Do not add studies, comparisons, sources or passages.
Claims belong to the original unit and semantic scope. Do not transfer a
specific content interpretation for one intervention to adjacent different
interventions merely because they share a paragraph. A genuinely explicit
group-level conclusion may apply to multiple units: identify the words that
link the group and record explicit_group. If linkage is genuinely ambiguous,
use Unclear rather than inventing a connection or declaring the claim absent.

General whole-model claims, structural/context utilization, encoder quality,
or broad domain-information benefits do not become strict semantic-content
dependence without an explicit interpretation about the supplied content.

## Independent coding output

Two NEW separate fresh AI contexts read only this codebook and the common masked
packet. They do not see old claim labels, utility/support labels, old counts,
each other's judgments or the manuscript. Numeric performance magnitudes remain
masked; qualitative claims remain visible. Read boundaries are instructional,
not technical filesystem isolation. Same-model AI contexts are not human raters.

Each coder outputs 25 rows: comparison_id, study, claim_content (Yes/No/Unclear),
claim_text (short exact masked-packet excerpt), claim_location (window ID and
page/line span), linkage (explicit_comparison/explicit_group/ambiguous/none),
rationale, coder_id. For Yes, rationale must state the PARTICULAR-content
interpretation and its link to this unit. For No, distinguish merely weak-use,
benefit-only, descriptive, or other-scope language as applicable. Cite the words,
not the expected adequacy of the control. Quotes may normalize whitespace and
line-wrap hyphenation but not wording; join multiple extracts with ` | `.

Freeze raw submissions before computing unweighted Cohen kappa, raw agreement,
confusion matrix and marginals. Undefined kappa remains undefined. Do not use
independence-based confidence intervals for these clustered comparisons.
A third fresh AI adjudicator, still blind to support and old labels, resolves
differences and reviews agreements. Freeze adjudication before merging.

## Deterministic post-adjudication merge

Only claim_content is replaced. Existing supports_content and claim_utility /
supports_utility remain unchanged. Yes + Supported -> Matched;
Yes + None -> Mismatch; Yes + Unclear -> Indeterminate;
No + any support -> Not claimed; Unclear + any support -> Indeterminate.
Report Yes-claim denominator, all 25 states, claim-vs-support cross-tab, and a
v1-to-v2 transition ledger. Do not interpret No here as absence of a weaker
use/dependence claim. Preserve the old weaker labels under an explicit legacy
column, not as a second new coding outcome. Preserve utility evidence separately
from the new strict-content quotes. Report any remaining attribution uncertainty;
do not force a target number of strict claims or mismatches.
