# Outcome extraction rule v1

Date: 2026-09-08. Freeze before outcome extraction in this phase.
Parent: phase_c_v1/DESIGN_CODE_FREEZE_V1.json, unchanged 9 studies / 25 comparisons.

Extract all reported outcomes directly associated with each frozen semantic
comparison at the granularity reported by the paper; do not choose datasets,
budgets, model variants or metrics based on effect direction. Use published
main tables, supplements, figures and associated prose. This is documentary
extraction, not a meta-analysis or a replication of any model.

## Source and inventory

First inventory the main/supplement outcome locations for every fixed ID.
Use the same official source versions as the design audit. Record a linked
published row even when exact matching to a frozen arm is ambiguous, with
match_status=ambiguous and no promotion to a comparison-level claim. Do not
silently map generic unnamed prompt variants onto both format-specific arms.
Do not use our later experiments or a preprint-only numerical result as a
published outcome. TARTE's published-source access limitation remains visible.

## Long-format extraction

Fields include outcome ID, Comparison ID, dataset/task, budget/regime, model,
metric and orientation, intended/comparator labels and printed values,
reported uncertainty, direction, reported significance, evidence location,
source type, match status, duplicate-of and extraction notes.

- Extract every tabulated row/column belonging to a frozen pair, including
  all datasets, budgets, models and metrics. Record aggregate rows separately
  from per-dataset rows; do not average incompatible metrics or repeat them as
  independent evidence. Repeated main/supplement presentations can be logged
  as duplicate/aggregate presentations instead of double-counted observations.
- Preserve printed precision and uncertainty notation. Separate arm-wise SD,
  SE or CI from uncertainty for a paired contrast. Never infer significance
  from non-overlap, error bars, decimal rounding or numerical direction.
- If a table reports change relative to a common baseline, retain that change
  and its stated convention; derive an absolute value only if the baseline,
  scale and arithmetic are unambiguous, labelling the derivation.
- For figure-only outcomes, record the complete displayed panel/budget range
  as figure-reported; exact value unavailable. Do not digitize points, infer
  hidden per-dataset numbers, or interpolate. An explicit printed number in a
  caption/prose may be extracted at exactly its stated scope. Source prose
  may support a qualitative direction; distinguish it from numeric ordering.
- For figures with many cells, inventory each relevant panel/comparator and
  its full regime rather than inventing point-level outcomes. Visible printed
  numerical cells may be transcribed after inspection; no pixel estimation.
- Unavailable or ambiguous extraction is a retained row, not an exclusion.
  A missing exact value does not become zero. Source unavailable, arm matching
  uncertain, and figure-only exact values absent are distinct statuses.

## Direction and supported claims

Numeric direction uses the metric's orientation and printed point values:
intended higher/lower predictive performance or equal at printed precision.
Equality does not establish equivalence or a practically negligible effect.
Qualitative directions are explicitly attributed to the authors and scoped
to the cited prose. Do not generalize qualitative prose to every curve point.
Use not_reported when no pair-specific significance is supplied. Preserve
explicit pairwise p-values or author statements without inventing new tests.

Only after extraction, join by fixed Comparison ID to the frozen codes.
Utility Yes + favorable direction permits a descriptive positive utility
statement for the declared scope; statistical support is a separate field.
Utility No forbids component-specific utility language regardless of outcome;
Utility Partial remains conditional/unresolved. Apply the same rule to
content sensitivity. No reported outcome changes design codes. An actual
source error requires a separate preserved addendum, not silent correction.

## Deterministic synthesis

Keep outcomes separated by comparison and by numeric/qualitative evidence.
For each comparison report counts of favorable, adverse, equal-at-precision,
and direction-unavailable records, excluding duplicates, aggregate repeats
and ambiguous arm matches. Counts describe rows, not independent experiments.
Use all favorable / all adverse / mixed (both signs) / equal at printed
precision / favorable-or-equal / adverse-or-equal / direction unavailable.
Do not call mixed findings “mostly positive” to hide adverse results; report
the counts. Do not infer near-zero from rounded equality or nonsignificance.
Unknown directions remain explicit and prevent an unqualified all-regimes claim.

Study-level summary retains every comparison and its scope; it does not select
the strongest comparator or pool numerical effects across datasets/budgets.
Identify studies with at least one admissible reference separately from
studies with only unresolved or non-admissible references. No causal census
or independent-experiment interpretation of the 25-row audit is permitted.

## Boundaries and freeze

Reported outcomes were not extracted or used in assigning the design codes.
Outcomes are deliberately extracted only now; prior incidental exposure was
disclosed. Preserve all Phase A/B/C hashes. Hash this rule before extracting,
then freeze extraction and supported-claim artifacts with source locations,
coverage checks and remaining limitations. Manuscript integration is a later
step; flag the TabLLM values-only/reference terminology issue in the handoff.
