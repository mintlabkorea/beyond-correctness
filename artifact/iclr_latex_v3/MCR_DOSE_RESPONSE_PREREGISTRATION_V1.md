# Pre-registration: MCR-D — per-layer corruption dose–response

Declared 2026-08-20, **before any MCR-D cell has been executed.** The
follow-up the MCR prereg declared in §5: the factorial's lesions are
catastrophic, so its P1/P2 verdicts read content at full severity; this
experiment grades each lesion and asks whether damage is monotone in
dose, which a single correct-vs-wrong contrast cannot show.

## Design

The identical frozen MCR cells (same salted namespace, same
realizations, mechanisms, rows; the graded lesions are new draws keyed
per realization). One axis is dosed at a time with the other two axes
correct. XGBoost only, K = 32 only, 3 families × 20 realizations.

- **M-dose**: k ∈ {0, 2, 4, 6, 8} source features decoded with the
  wrong table (per-feature merge of the frozen true and wrong tables;
  the corrupted set is the first k of a per-realization random feature
  order — nested, so higher dose strictly contains lower).
- **C-dose**: k ∈ {0, 2, 4, 6, 8} misrouted source columns,
  type-preserving: cyclic rotation of the first k/2 features of a
  per-realization ordinal order and the first k/2 of a continuous order
  (a rotated subset has no fixed point; k = 2 rotates 2 ordinals only).
- **R-dose**: j of the true relation signs flipped (nested flip order),
  j ∈ {0..5} (family A), {0..3} (B), {0..2} (C), applied through the
  constraint channel as in the grid.

Dose 0 is the shared `m1c1r1` fit. Runner asserts per cell: dose-0
tables/permutations/relations equal the frozen correct objects; the
maximal M dose equals the frozen wrong table; C dose k misroutes
exactly k columns; R dose j flips exactly j signs.

## Adjudication (frozen)

Metric nMSE. Per axis × family: the per-realization Spearman ρ between
dose and nMSE (5 points for M/C; 6/4/3 for R), then a realization-level
bootstrap (20 units, 10,000 reps, seed 20260820) of the mean ρ.
**MCR-D-P1 (per axis)**: mean ρ > 0 ∧ CI95 excludes 0 ∧ win ≥ 0.60 in
all three families. Descriptive: the mean nMSE dose curves (the
mechanism figure), per-family and pooled.

Interpretation, declared now: P1 for an axis → that layer's damage is
graded and monotone — the factorial's contrast reads content, not a
cliff artifact. Non-monotonicity is reported where it occurs with its
dose location; it would bound where "partially right knowledge" stops
helping. R-axis non-monotonicity in B/C is plausible (few discrete
signs) and its failure would not touch the M/C claims.

## Execution

`scripts/run_crta_v3_mcr_dose_response_v1.py` (imports the frozen MCR
runner; per-cell metrics.json, provenance-gated, resumable),
`scripts/summarize_crta_v3_mcr_dose_response_v1.py`. Committed before
launch; no smoke (all machinery is the grid's, exercised and
adversarially reviewed; in-runner asserts are fail-closed). ~720 fits,
local CPU.
