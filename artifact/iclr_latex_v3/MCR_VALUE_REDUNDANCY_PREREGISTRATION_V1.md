# Pre-registration: MCR-VR — redundancy vs. sign-equivariance behind the dead value channel

Drafted 2026-08-25; to be freeze-committed before any cell is fit.

## Motivation and prior observation disclosure

Section 4.3 of the manuscript explains the dead relation-value channel
(operation values over free: 0/4 separated; direction constraints on the
same columns: 4/4) by the sign-invariance of axis-aligned splits.  Two
later results make that explanation incomplete: MCR-N found the value
channel dead on a sign-sensitive MLP, and MCR-NM found that on a
certified monotone MLP the constraint channel yields only
direction-independent gains.  Two mechanisms can each produce a dead
value channel, and the current design cannot tell them apart:

- **Redundancy.** Every compiled operation column is a deterministic
  function of two base columns that are already in the frame; a learner
  that can reconstruct the operation from its constituents gains nothing
  from the column, whatever its sign.
- **Sign-equivariance.** For learners whose hypothesis class and fitting
  procedure are invariant to negating an input column (trees; MLPs up to
  a first-layer weight flip), the sign of a value column carries no
  information at all — only its magnitude/ordering does.

Known prior observations, disclosed: `P3b_ops_alone` unseparated and
`P3b_signs_given_ops` separated on both trees at K=32; MCR-N N4 and
MCR-T T4 value-content nulls; MCR-NM NM1/NM2 grid false.

This experiment removes the redundancy by **dropping the true pairs'
constituent base columns** from the frame, so that an operation column
is the only carrier of that information, and then reads magnitude and
sign separately.

## Frozen design

- Cells: the frozen 60-cell grid's pairwise and sparse families (the
  additive family has no operation columns), 20 realizations each,
  `mcr_v1c` namespace, matrices from the frozen runner's `arm_matrices`.
  M and C are true in every arm.
- Constituent set: the union of features appearing in the true relation
  set's `pair_terms` (6 of 8 features in pairwise; 3–4 in sparse).
  `keep_base` = the remaining base columns (asserted non-empty).
- Arms per cell × K × backbone (all matrices are column subsets of the
  frozen `m1c1rf` / `r_op_only` / `m1c1r1` / `r_flipped` / `m1c1r0`
  matrices; the runner asserts the shared matrices are bit-identical
  where the design requires it):
  - `full_free` — the frozen `m1c1rf` matrix (8 base), no constraints;
  - `full_op_true` — the frozen `r_op_only` matrix (8 base + true ops),
    no constraints (the original "values over free" arm);
  - `drop_free` — `keep_base` only;
  - `drop_op_true` — `keep_base` + true operation columns, no
    constraints;
  - `drop_op_true_negated` — the same with every operation column
    multiplied by −1 (fit and query), no constraints;
  - `drop_op_true_signed` — `drop_op_true` columns with the true
    monotone signs on the operation columns;
  - `drop_op_flip_signed` — the same with every sign negated;
  - `drop_op_random` — `keep_base` + the frozen random-topology
    operation columns, no constraints (descriptive: the true
    constituents are still dropped, so information is not matched).
- Backbones and budgets: XGBoost and HistGradientBoosting with the
  frozen factorial configurations, K ∈ {32 (primary), 512 (secondary)},
  unweighted pooling.  2 families × 20 × 2 K × 2 backbones × 8 arms =
  **1,280 fits**.  Executed on the remote server in a pinned environment
  matching the local versions (xgboost 3.1.3, scikit-learn 1.7.2,
  numpy 2.2.6, pandas 2.3.3); every cell records the package versions
  and the host.

## Adjudication (frozen)

Q = −MSE/Var(y_query); families are fixed strata; per-family
realization bootstrap (20 units, 10,000 reps, seed 20260820, seed key
`mcr_vr|{contrast}|{family}|{backbone}|{K}`); separated = mean > 0 ∧
CI95 low > 0 ∧ win ≥ 0.60; null = CI95 contains 0 ∧ |mean| < 0.05 nMSE
(the factorial's exchangeable-null margin).  Grid = both families × both
backbones at K=32; K=512 confirmatory.

- **V1 (magnitude when non-redundant):** Q(drop_op_true) − Q(drop_free).
- **V4 (sign-equivariance in value form):** Q(drop_op_true) −
  Q(drop_op_true_negated), adjudicated as a null.
- **V2 (direction on top, constraint form):** Q(drop_op_true_signed) −
  Q(drop_op_true).
- **V3 (constraint content when non-redundant):**
  Q(drop_op_true_signed) − Q(drop_op_flip_signed).
- Descriptives: Q(full_op_true) − Q(full_free) (the original
  values-over-free contrast, re-fit here), Q(full_free) − Q(drop_free)
  (the information removed), Q(drop_op_random) − Q(drop_free).

Interpretation map, declared now:

- V1 separated ∧ V4 null → the dead value channel is **redundancy plus
  sign-equivariance**: values carry magnitude when they are the only
  carrier, and never carry sign; §4.3 is rewritten from "trees cannot
  read values" to "values were redundant and sign is unreadable in
  value form".
- V1 not separated → operation values are inert even when they are the
  only carrier; the expressiveness reading of §4.3 stands as written.
- V4 not null (negation changes performance) → sign-equivariance fails
  for these tree fits (binning asymmetry or similar); report it and do
  not use the equivariance argument in the paper.
- V2 separated → direction adds beyond non-redundant magnitude; V2 not
  separated → the original constraint gain was largely "forcing the
  learner onto the operation column", not sign per se; either is
  reported with V3 as the content check.
- Backbone disagreement → scope to the backbone that shows it.

## Execution

Runner `scripts/run_crta_v3_mcr_value_redundancy_v1.py` (per-cell
`metrics.json`, resumable, provenance-hashed, `--input` override for
the panel path on the server), summarizer
`scripts/summarize_crta_v3_mcr_value_redundancy_v1.py`, self-test
`scripts/test_crta_v3_mcr_value_redundancy_synthetic_v1.py` (matrix
identities, constituent removal, negation, constraint alignment).
Committed with this document before launch.  Remote CPU, no GPU
(contract), public-use panel, aggregate metrics only.
