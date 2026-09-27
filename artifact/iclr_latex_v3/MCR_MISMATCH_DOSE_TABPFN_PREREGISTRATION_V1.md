# Pre-registration: MCR-MD-T — the mismatch-dose experiment on TabPFN

Drafted 2026-08-25; to be freeze-committed before any TabPFN dose cell is fit.

## Motivation and prior observation disclosure

MCR-MD established, on XGBoost and HistGB, that measurement utility
U(d) = Q(decode) − Q(raw at dose d) is zero by construction at d=0 and rises
monotonically with the number of discrepantly recorded source features
(grid verdict TRUE; ρ +.78–+.90 at K=32; U(8) ≈ +.26; +.03 at K=512).  That
result now carries a headline claim of the manuscript ("correct knowledge
helps in proportion to the consequential mismatch it resolves"), yet its
evidence is tree-only.  Unlike the relation-interface result, nothing about
mismatch resolution is intrinsically a tree mechanism, so a reviewer may ask
whether it is another boosted-tree property.  This extension runs the
identical dose construction on the in-context backbone.

Disclosed prior observations, not re-registered as evidence: the tree MD
verdict above; MCR-T (TabPFN reproduces the M/C content contrasts and the
interaction at α=0); the MCR-T ladder (TabPFN reproduces the integrity
trend).  Prospective claims cover only the TabPFN dose cells.

## Frozen design

- Cells: the identical frozen 60 primary cells (`mcr_v1c` namespace); rows,
  mechanism, outcome, renderings, support draws, and the true source table
  reused unchanged from the frozen MCR runner.  C is true routing, R is
  free in every arm; no constraint vectors exist for this backbone.
- **Mismatch dose: byte-identical to MCR-MD.**  The balanced outcome-blind
  dose order is drawn from the same namespace
  (`stable_seed("mcr_mismatch_dose_v1", "dose_order", family, realization,
  type)`), so each cell's dosed sets are the same features in the same
  order as the tree experiment; the runner asserts equality with the
  `dose_order` and `mismatch_entry_counts` recorded in the frozen MD cell.
  Dosed features are recorded in the cell's frozen source rendering;
  undosed features are canonical.
- Arms per cell (source block varies; target support/query frames are the
  frozen arm-invariant objects): `decode` (asserted bit-equal to the
  `m1c1rf` source block), `raw_d{2,4,6,8}` (sentinels neutralized to NaN;
  primary reference), `rawsent_d{2,4,6,8}` (sentinels live; descriptive).
  At d=0 both raw arms are bit-identical to `decode` (asserted) and copied,
  not refit.
- Backbone: TabPFNRegressor 7.0.0, `random_state` = realization, GPU
  (the MCR-T convention; the CPU-only contract binds the XGBoost benchmark
  cells only).  **K = 32 only** (MCR-T's budget).  9 fits per cell,
  **540 fits** total.
- Construction asserts per cell, inherited from MD: rendering rebuild
  identity, d=0 and d=8 bit-identities, nested dosed sets, nondecreasing
  mismatch-entry counts, decode-block equality with `m1c1rf`.

## Adjudication (frozen)

Q = −MSE/Var(y_query); families are fixed strata; per-family realization
bootstrap (20 units, 10,000 reps, seed 20260820, seed key
`mcr_md_t|{quantity}|{family}`); separated = mean > 0 ∧ CI95 low > 0 ∧
win ≥ 0.60.

- **MDT-P1 (graded utility):** per family, the realization-level Spearman
  correlation of U(d) against d over the five doses — mean ρ > 0 and CI95
  above 0.
- **MDT-P2 (anchor):** U(8) separated in every family.
- Verdict = MDT-P1 ∧ MDT-P2 in all three families.  The `rawsent` curve,
  the mean U(d) table, and the paired comparison against the tree MD
  curves on the same realizations are descriptive.

Interpretation, declared now: P1 ∧ P2 → the mismatch-dose result is
reproduced on an in-context predictor and the manuscript may state it for
"two boosted-tree implementations and one in-context tabular predictor"
(never "architecture-general").  Either failing → the claim stays
tree-scoped in the paper and the TabPFN curve is reported as the boundary.

## Execution

Runner `scripts/run_crta_v3_mcr_mismatch_dose_tabpfn_v1.py` (imports the
frozen MCR runner and the frozen MD runner for bit-identical construction;
per-cell `metrics.json`, resumable, provenance-gated, paired-construction
gate against the frozen MD cell).  Summarizer
`scripts/summarize_crta_v3_mcr_mismatch_dose_tabpfn_v1.py`.  Output
`experiments/crta_v3_mcr_mismatch_dose_tabpfn_v1/`.  Committed before
launch.  Executed on the B200 server (GPUs 0/1, whichever are free) in a
dedicated `coret_tabpfn` environment pinned to TabPFN 7.0.0 (the MCR-T
version) with numpy 2.2.6 / scikit-learn 1.7.2 (the `coret_pin` versions);
the benchmark parquet is SHA-identical to the local input and is passed via
`--input`.  Hardware differs from MCR-T (RTX 4090), so the decode arm is a
cross-hardware replay of `m1c1rf` and is compared to MCR-T descriptively
only; every verdict contrast (decode vs raw at each dose) is computed within
the same hardware and environment.
