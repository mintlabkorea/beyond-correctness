# Pre-registration: MCR-T source-informativeness ladder, v1

Drafted 2026-08-24; to be freeze-committed before any TabPFN dose cell is fit.

## Motivation and prior observation disclosure

This is a **post-freeze extension** prompted by a paper-review scope gap: the
manuscript's mechanistic contribution currently risks reading as if the
source-integrity trend held on all three backbones, while the executed
informativeness ladder covered XGBoost and HistGB only. This extension asks
whether the trend also holds on the in-context backbone, so the claim can be
either widened or scoped with evidence rather than wording.

The following are already observed and are **not** re-registered as evidence:

- the tree-backbone ladder verdict (P1 passed 6/6 strata; monotone decline;
  every stratum first crossed sign in `[0.75, 1.00]`);
- MCR-T at α=0 (positive `I_MC` on all three families, T1–T3 passed);
- the tree α=1 null-source failure and its quarantine, which remain
  authoritative.

Prospective claims cover only the TabPFN cells at α ∈ `{0.25, 0.50, 0.75,
1.00}` and the TabPFN five-point trend built from them. Because the tree
trajectory is known, this is confirmatory for architecture-generality only;
it cannot strengthen the tree result itself.

## Frozen design

- Cells: the identical frozen 60 primary cells (three fixed families × 20
  realizations, salted RNG namespace `mcr_v1c`), K = 32, free-R M/C arms
  `m1c1rf`, `m1c0rf`, `m0c1rf`, `m0c0rf` — the MCR-T value-expressible
  subset. Monotone-constraint vectors are discarded and asserted absent, as
  in MCR-T.
- Backbone: TabPFNRegressor 7.0.0, `random_state` = realization, local GPU 0
  (the MCR-T convention; the CPU-only contract binds the XGBoost benchmark
  cells only).
- Doses: α ∈ `{0.25, 0.50, 0.75}` **and α = 1.00**. Unlike the tree ladder,
  α=1 must be newly fit here because the null-source run was tree-only. α=0
  is read from the frozen MCR-T results and is not refit.
- Source-label interventions are **byte-identical to the tree ladder**: for
  each family×realization, reconstruct the exact α=1 derangement of
  `run_crta_v3_mcr_null_source_v1.py` (hash-checked against the recorded
  null-source permutation), decompose into cycles, and traverse the same
  deterministic cycle order (namespace
  `mcr_source_informativeness_ladder_cycle_order_v1`). Each internal-α
  partial permutation must reproduce the `permutation_sha256` recorded in
  the executed tree-ladder cell, so TabPFN and the trees see identical
  corrupted labels row for row.
- Construction gates per cell (inherited from the tree ladder): bijection,
  exact label-multiset preservation, moved-count within one row of
  `round(α×n_source)`, corrupted-row sets nested across doses, and audit
  equality between the rebuilt cell and the frozen original.

## Estimand and adjudication (frozen)

`Q = −nMSE = −MSE/Var(y_query)`; `I_MC(α) = Q11 − Q10 − Q01 + Q00` per
realization and dose, with α=0 taken from frozen MCR-T.

**P1-T**: the realization-level Spearman correlation between α and `I_MC(α)`
over all five levels. For each of the three family strata (single backbone):

- mean Spearman rho must be negative;
- a 10,000-replicate realization bootstrap CI95 (seed 20260820) must lie
  below zero.

The primary verdict is the intersection of all three strata. Descriptive,
not gated: the mean five-point curve, adjacent changes, the first adjacent
sign-crossing interval, and the paired comparison against the tree strata on
the same realizations. No continuous threshold is claimed from five grid
points.

Interpretation, declared now: P1-T passing → the source-integrity dependence
of the M×C interaction is architecture-general across the three backbones,
and the manuscript sentence may be widened accordingly. P1-T failing in any
stratum → the integrity claim stays scoped to tree backbones in the paper,
and the TabPFN divergence is reported as a finding, not suppressed.

## Execution

Runner: `scripts/run_crta_v3_mcr_tabpfn_source_informativeness_ladder_v1.py`
(imports the frozen MCR runner for bit-identical cell construction and the
null-source runner for the derangement; per-cell metrics.json, resumable,
provenance-gated). Summarizer:
`scripts/summarize_crta_v3_mcr_tabpfn_source_informativeness_ladder_v1.py`.
Output: `experiments/crta_v3_mcr_tabpfn_source_informativeness_ladder_v1/`.
Committed before launch. 3 families × 20 realizations × 4 doses × 4 arms =
960 TabPFN fits, local GPU 0.
