# Pre-registration: MCR-T — the MCR factorial on TabPFN (interface-aware subset)

Declared 2026-08-20, **before any MCR-T cell has been executed.**

The MCR factorial's composition verdicts (P1, P2, P4-MC) hold on two
tree implementations. MCR-T asks whether they hold on an in-context
architecture. Per the program's interface principle, TabPFN is tested
**only on value-expressible knowledge**: it has no constraint API, so
the R-as-constraint axis is out of scope by design, not by omission
(forcing it would be the exact channel-expressiveness error the paper
indicts). Family A's relation knowledge is sign-only and therefore
also out of scope on this backbone.

## Design

The **identical frozen cells** as the executed MCR grid: same panel,
same salted RNG namespace (`mcr_v1c`), same realizations, lesion draws,
mechanisms, rows — MCR-T is a third backbone on the same cells, paired
per realization with the tree results. K = 32 only (the grid's primary).
Unweighted pooling as executed. Backbone: TabPFNRegressor 7.0.0,
`random_state` = realization, local GPU (the E2 convention; the
CPU-only contract binds the XGBoost benchmark cells, and TabPFN cells
carry their own backbone tag).

Arms per cell (built by the frozen MCR runner's own `arm_matrices`;
monotone-constraint vectors are discarded — asserted unused):

- Free grid (all families): `m1c1rf`, `m1c0rf`, `m0c1rf`, `m0c0rf`.
- Value-form op content (B/C only): `rop_true` (= the grid's `m1c1r1`
  design matrix: true compiled op columns, no constraints) vs
  `rop_random` (= `m1c1r0`'s matrix: topology-matched random op
  columns). Capacity-matched by construction.

3 families × 20 realizations × (4 | 6) arms = **320 fits**.

## Adjudication (frozen)

Q = −MSE/Var(y_query); fixed family strata; per-family realization
bootstrap (20 units, 10,000 reps, seed 20260820); separation = mean > 0
∧ CI95 excludes 0 ∧ win ≥ 0.60. Verdicts:

- **T1**: Q(m1c1rf) − Q(m0c1rf) separates in all 3 families (M content).
- **T2**: Q(m1c1rf) − Q(m1c0rf) separates in all 3 families (C content).
- **T3**: I_MC = Q(m1c1rf) − Q(m1c0rf) − Q(m0c1rf) + Q(m0c0rf)
  separates in all 3 families (M×C composition).
- **T4** (B/C only): Q(rop_true) − Q(rop_lesion...) — precisely:
  Q(rop_true) − Q(rop_random) separates in both pairwise families
  (value-form relation content on an in-context model).

Interpretation, declared now: T1 ∧ T2 ∧ T3 → the M×C composition is
architecture-general (trees and in-context). T4 separating would show
the op-value channel carries relation content for TabPFN — reported
either way against the tree grid's constraint-channel result; T4
failing does not weaken T1–T3. Any Tx failing → that claim is scoped
to tree backbones. Descriptive: per-family tables, effect-size
comparison against the tree backbones on the same paired cells.

## Execution

`scripts/run_crta_v3_mcr_factorial_tabpfn_v1.py` (imports the frozen
MCR runner for bit-identical cell construction; per-cell metrics.json,
resumable, provenance-gated),
`scripts/summarize_crta_v3_mcr_factorial_tabpfn_v1.py`. Committed
before launch. Local GPU 0, ~320 fits. Disclosure: one wall-time smoke
cell (pairwise r00, 3.8 s) ran into a separate tree before this commit;
its metric contents were not read.
