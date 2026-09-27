# Pre-registration: MCR-NM — the constraint channel on a certified partially-monotone MLP

Drafted 2026-08-24; to be freeze-committed before any contrast arm is fit.

## Motivation and prior observation disclosure

The manuscript's relation-interface finding rests entirely on axis-aligned
trees: operation values were unseparated in 0/4 family--predictor
comparisons while explicit monotone direction constraints on the same
compiled columns separated in 4/4 (`m1c1r1` vs `r_op_only`,
`experiments/crta_v3_mcr_interface_decomposition_v1/SUMMARY_V1.json`).
MCR-N found the value channel dead on a sign-sensitive MLP as well
(N4 unseparated at both K), and MCR-T found it dead on TabPFN.  All prior
results are known and disclosed.  What has never been tested is the
**constraint channel on any non-tree learner**: neither TabPFN nor the
MCR-N MLP can accept a direction constraint, so "directional knowledge
requires an executable interface" is currently a claim about trees plus
an untested generalization.  This experiment gives one neural learner an
executable direction interface — a certified partially-monotone MLP — and
asks whether enforcing the true signs helps, whether it beats enforcing
the flipped signs, or whether the channel is inert or harmful here.
Every outcome is informative and will be reported: separation extends the
executable-interface finding to one neural recipe; failure scopes it to
trees; mono_true ≈ mono_flip with both above free reads as
constraint-as-regularization, not direction utility.

## Pilot disclosure

Seventeen recipe-tuning fits were run before this freeze, all on the
**free (unconstrained) arm** of a single cell (pairwise r00, K=32,
`m1c1r1` matrix): one sklearn MCR-N-recipe reference (nMSE 0.750) and a
16-point torch grid over hidden ∈ {16,32} × lr ∈ {1e-2,3e-3} ×
epochs ∈ {300,800} × weight_decay ∈ {1e-2,1e-3}, all with the constraint
channel off.  No constrained arm was fit and no contrast was computed.
Best: hidden 16, lr 3e-3, epochs 300, wd 1e-2 → nMSE 0.742.  Log:
`logs/crta_v3_mcr_monotone_mlp_v1/pilot_free_arm_v1.log`.

A second, synthetic-only iteration tuned the mono-path
reparameterization: on a hand-built monotone truth (no benchmark data),
softplus over torch-default init failed to train (nMSE 1.90 vs free
0.005) and softplus(-4,0.5) init starved through the ~0.02 sigmoid
gradient (0.70); among {softplus init −2, softplus init −1, abs, exp
init −2, exp init −3} the frozen choice softplus with N(−2, 0.5²) init
reached 0.043 with the flipped arm correctly degrading to 0.98.  No
benchmark cell was involved in this iteration.  The recipe below is
frozen from these two pilots.

## Frozen design

- Cells: the identical frozen 60 primary cells (`mcr_v1c` namespace),
  matrices and constraint vectors from the frozen MCR runner's
  `arm_matrices(cell, "m1c1r1", K, weighted=False)`.  All three families
  are eligible: in additive the ±1 signs sit on 5 of the 8 base concept
  columns; in pairwise/sparse they sit only on the appended true
  operation columns.  The runner asserts the expected sign topology per
  family and that weights are all 1.0 (unweighted pooling).
- Support budgets: **K=32 (primary) and K=512 (secondary)**, from the
  grid's frozen per-K support draws.
- Arms per cell and K (identical feature matrix in all three — the arm
  changes only the sign fold and the non-negativity reparameterization):
  - `free` — constraint channel off (raw weights on the P/v paths);
  - `mono_true` — channel on with the true signs;
  - `mono_flip` — channel on with every sign negated.
- Backbone (frozen recipe, applied identically to every arm):
  preprocessing exactly as MCR-N (`SimpleImputer(mean)` fit on the arm's
  fit matrix + binary missing-indicator columns + `StandardScaler` on the
  concatenation; target standardized by fit-set mean/SD and predictions
  destandardized).  Torch network (float64, CPU only,
  `CUDA_VISIBLE_DEVICES=""`):

  ```
  x_u = unconstrained columns (all indicator columns are unconstrained)
  x_c~ = sign-folded constrained value columns (x_j * s_j; s from the arm)
  free block : out_f = w2^T ReLU(W1 x_u + b1)
  mono block : out_m = v^T ReLU(U x_u + P x_c~ + bm)
  yhat = out_f + out_m + b0
  ```

  In `mono_*` arms, `P` and `v` are reparameterized through softplus
  (elementwise, hence non-negative) with their pre-activation weights
  initialized N(−2, 0.5²) (softplus ≈ 0.13, matching the default weight
  scale), which certifies d yhat / d x_j has sign s_j for every
  constrained column; in `free` they are raw torch-default weights and
  the architecture is otherwise unchanged.
  StandardScaler preserves per-column monotone direction (positive
  scale), so certification transfers to the pre-scaled column.
  Hidden width 16 in both blocks, AdamW(lr=3e-3, weight_decay=1e-2),
  300 full-batch epochs, MSE loss, `torch.manual_seed(realization)`,
  `torch.set_num_threads(threads)`.  The NaN interface (imputation +
  indicators) necessarily differs from the tree backbones' native NaN
  routing; it is part of the backbone, held fixed across arms, so
  within-backbone contrasts are valid.
- Certification audit: after every `mono_*` fit the runner evaluates the
  network at 64 fixed query points and at +1e-3 perturbations of each
  constrained (sign-folded) input and hard-fails if any directional
  finite difference is below −1e-8.

3 families × 20 realizations × 2 K × 3 arms = **360 fits**.

## Evaluability gate (declared before any contrast)

For each family×K stratum, the mean `free` nMSE must be below 1.0.  A
stratum failing the gate has its verdicts declared **non-evaluable** —
a learner-capacity failure, not evidence about the constraint channel.

## Adjudication (frozen)

Q = −MSE/Var(y_query); families are fixed strata; per-family
realization bootstrap (20 units, 10,000 reps, seed 20260820, seed key
`mcr_nm|{contrast}|{family}|{K}`); separated = mean > 0 ∧ CI95 low > 0 ∧
win ≥ 0.60.  Verdicts at K=32; K=512 is confirmatory.

- **NM1 (constraint utility):** Q(mono_true) − Q(free) — the analog of
  the tree grid's `P3b_signs_given_ops`.
- **NM2 (direction content):** Q(mono_true) − Q(mono_flip).
- Descriptive: Q(mono_flip) − Q(free) (the flipped channel's own
  utility, expected ≤ 0 if direction matters), per-arm nMSE tables.

Interpretation map, declared now:

- NM1 and NM2 both separated in all three families → the
  executable-direction finding extends beyond trees to this neural
  recipe; claim one-architecture generalization, not "all neural
  learners".
- NM1 separated, NM2 not → the gain is
  constraint-as-regularization, not direction content; report it as
  such and do not claim direction utility.
- NM1 not separated (or negative) with the gate passed → the constraint
  channel does not transfer to this recipe; the manuscript's
  executable-interface claim stays scoped to trees, stated explicitly.
- Gate failed in any stratum → that stratum is non-evaluable; no
  channel claim from it in either direction.

## Execution

Runner `scripts/run_crta_v3_mcr_monotone_mlp_v1.py` (per-cell
`metrics.json`, cached/resumable, provenance-hashed), summarizer
`scripts/summarize_crta_v3_mcr_monotone_mlp_v1.py`, self-test
`scripts/test_crta_v3_mcr_monotone_mlp_synthetic_v1.py` (certified
monotonicity on synthetic data, trainability of the softplus channel on
a known monotone function, sign-fold correctness, free/mono
architecture equality up to reparameterization).  Committed with this
document before launch.  Local CPU ≤ 6 threads total, no GPU
(contract), public-use panel, aggregate metrics only.

## Post-execution addendum (2026-08-25, after the frozen run; Codex-identified)

An adversarial code review (Codex, `logs/codex/review_new_runners_20260825_terra.log`)
found that the `free` arm receives the **true sign fold** on its constrained
inputs: its weights are unconstrained (function class unchanged), but the
fold is not optimization-neutral under fixed init, ReLU gates, weight decay
and 300 epochs, so `free` is not a clean channel-off baseline for NM1.
Fix: a fourth arm `free_unfolded` (all-ones fold, channel off) is added and
the whole grid is re-fit into a separate tree
`experiments/crta_v3_mcr_monotone_mlp_v1_addendum` (the frozen tree is
untouched).  Addendum contrasts: NM1b = Q(mono_true) − Q(free_unfolded)
(the corrected NM1), and fold_effect = Q(free) − Q(free_unfolded)
(descriptive).  NM1b is adjudicated with the frozen NM1 rule; the
addendum's `free`/`mono_*` numbers must reproduce the frozen tree
(same code path and seeds) and are checked for that.
