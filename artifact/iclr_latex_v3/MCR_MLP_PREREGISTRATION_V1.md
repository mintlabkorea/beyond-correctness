# Pre-registration: MCR-N — the MCR factorial's value-expressible subset on an MLP

Drafted 2026-08-24; to be freeze-committed before any contrast arm is fit.

## Motivation and prior observation disclosure

The manuscript's relation-interface finding (operation values 0/4, direction
constraints 4/4) rests on axis-aligned trees, whose split families are
sign-invariant; MCR-T additionally found the value channel dead on TabPFN
(T4 false). Both prior results are known. An MLP is sign-sensitive: a signed
operation value changes its function class, so the value channel *could*
carry relation content here. This extension asks whether the value-channel
deadness and the M×C composition extend to a small fully-connected network.
Either N4 outcome is informative and will be reported: separation scopes the
channel claim to trees/in-context backbones; failure extends the boundary to
a third architecture family (one frozen recipe; not a claim about all
neural learners).

**Pilot disclosure.** Twelve recipe-tuning fits were run before this freeze,
all on the reference arm `m1c1rf` of a single cell (pairwise r00, K=32).
No contrast arm was fit during tuning and no contrast was computed. The
tuning trajectory: mean-imputation alone left the recipe below the intercept
baseline (nMSE 1.03); adding missing-indicator columns and shrinking the
network recovered 0.73–0.75. The recipe below is frozen from that pilot.

## Frozen design

- Cells: the identical frozen 60 primary cells (`mcr_v1c` namespace), arms
  built by the frozen MCR runner's `arm_matrices`; monotone-constraint
  vectors are discarded and asserted absent on free arms.
- Support budgets: **K=32 (primary) and K=512 (secondary)**, both from the
  grid's frozen per-K support draws.
- Arms per cell and K: free grid `m1c1rf`, `m1c0rf`, `m0c1rf`, `m0c0rf`
  (all families); value-form op content `rop_true` (= `m1c1r1` matrix) vs
  `rop_random` (= `m1c1r0` matrix), pairwise and sparse families only
  (additive relation knowledge is sign-only and value-inexpressible).
- Backbone (frozen recipe, applied identically to every arm):
  `SimpleImputer(strategy="mean")` fit on the arm's fit matrix, concatenated
  with binary missing-indicator columns for the same matrix;
  `StandardScaler` on the concatenation; target standardized by fit-set
  mean/SD and predictions destandardized;
  `MLPRegressor(hidden_layer_sizes=(32,), activation="relu", solver="adam",
  alpha=1e-2, learning_rate_init=1e-3, max_iter=500, early_stopping=False,
  tol=1e-6, random_state=realization)`. Unweighted pooling as executed.
  The NaN interface necessarily differs from the tree/TabPFN backbones
  (native NaN routing there, imputation+indicators here); it is part of the
  backbone, held fixed across arms, so within-backbone contrasts are valid.

3 families × 20 realizations × 2 K × (4 | 6) arms = **640 fits**.

## Evaluability gate (declared before any contrast)

For each family×K stratum, the mean `m1c1rf` nMSE must be below 1.0 (the
learner must beat the query-mean predictor on the reference arm). A stratum
failing this gate has its verdicts declared **non-evaluable** — reported as
a learner-capacity failure, not as evidence about knowledge content.

## Adjudication (frozen)

Q = −MSE/Var(y_query); fixed family strata; per-family realization
bootstrap (20 units, 10,000 reps, seed 20260820); separation = mean > 0
∧ CI95 excludes 0 ∧ win ≥ 0.60. Primary verdicts at K=32; the same
contrasts at K=512 are confirmatory replications reported per stratum:

- **N1**: Q(m1c1rf) − Q(m0c1rf) separates in all 3 families (M content).
- **N2**: Q(m1c1rf) − Q(m1c0rf) separates in all 3 families (C content).
- **N3**: I_MC = Q(m1c1rf) − Q(m1c0rf) − Q(m0c1rf) + Q(m0c0rf) separates
  in all 3 families (M×C composition).
- **N4**: Q(rop_true) − Q(rop_random) separates in pairwise and sparse
  (value-form relation content on a sign-sensitive learner).

Descriptive, not gated: Q(rop_true) − Q(m1c1rf) (operation values over
free), per-family arm means, and comparison against the tree and TabPFN
backbones on the same paired cells.

## Execution

Runner: `scripts/run_crta_v3_mcr_factorial_mlp_v1.py` (imports the frozen
MCR runner for bit-identical cell construction; per-cell metrics.json,
resumable, provenance-gated). Summarizer:
`scripts/summarize_crta_v3_mcr_factorial_mlp_v1.py`.
Output: `experiments/crta_v3_mcr_factorial_mlp_v1/`. Committed before
launch. CPU only.
