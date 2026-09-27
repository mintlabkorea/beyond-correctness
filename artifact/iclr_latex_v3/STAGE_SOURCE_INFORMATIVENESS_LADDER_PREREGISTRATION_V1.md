# Pre-registration: real-data M×C source-informativeness ladder, v1

Drafted 2026-08-24; to be freeze-committed before any cell is fit.

## Motivation and prior observation disclosure

The manuscript's source-integrity mechanism (I_MC falls monotonically as
source labels are permuted, crossing sign only at full corruption) is
established **only on the semi-synthetic MCR benchmark**; the paper
itself concedes that exploratory real-data proxies did not explain
endpoint-level interaction heterogeneity.  This experiment manipulates
source-label integrity directly in the real ten-endpoint
NHANES↔KNHANES stage factorial.

Known prior observations, disclosed: the frozen ten-endpoint expansion's
pooled corrected interaction is +.0312 (endpoint-clustered CI
[+.0051, +.0682]); the effect is concentrated (dropping diabetes more
than halves it; dropping diabetes and heart attack leaves the CI
crossing zero); arthritis and hypertension clusters are negative; the
cross-direction endpoint correlation is ≈.74; the MCR ladder declined
monotonically with all six Spearman coefficients in [−.96, −.90] and
crossed sign only between α=.75 and 1.  No cell of THIS ladder has been
fit.  The registered prediction is a monotone decline of the real-data
interaction with source-label corruption; a flat curve would say the
real interaction is not source-label-driven and will be reported as a
mechanism-transfer failure.

## Frozen design

- Base: the frozen bidirectional ten-endpoint stage factorial exactly —
  engine `run_crta_v3_m1m2_stage_factorial_v1.py`, registry
  `crta_v3_stage_endpoint_registry_v1.py`, both direction wrappers'
  patches replicated verbatim (BENCHMARK_ID, label-map swaps, and the
  `derived_rng` namespace rewrites to
  `stage_endpoint_expansion_{nh2kn,kn2nh}_v1`, so every placebo/lesion
  draw matches the frozen trees), seeds 50–59, K=256, XGBoost
  regression-ranked AUROC, SHA-pinned parquets.
- Arms restricted to the four interaction cells `a00_base`,
  `a01_columns`, `a10_stage`, `a11_stage_columns` (the frozen
  interaction contrast never reads the other five arms).
- **Source-label corruption.**  Per (direction, endpoint, seed), a full
  no-fixed-point derangement of the source block indices
  `[0:n_source]` is drawn by rejection sampling from
  `stable_seed("stage_source_ladder_v1", direction, endpoint, seed)`
  (the MCR null-source algorithm and seed formula).  Internal doses
  α ∈ {0.25, 0.50, 0.75} are built from the frozen MCR ladder's
  `permutation_cycles` + `partial_permutation` functions (imported from
  that runner file, unmodified) with the outcome-blind cycle order drawn
  from `stable_seed("stage_source_ladder_cycle_order_v1", direction,
  endpoint, seed)`; α = 1.00 is asserted byte-identical to the full
  derangement.  Moved-row counts must be within one of
  `round(α·n_source)`, maps bijective, moved sets nested across α.
- The permutation is applied to the **raw** training label vector's
  source prefix before any label mapping, identically in all three
  builder bundles (the engine's bundle-consistency guard therefore
  passes and every arm inherits the same corrupted pairing).  Target
  support rows, evaluation labels, all features, and all lesion draws
  are untouched.  The raw label multiset (sentinel codes included) is
  preserved by construction.
- α = 0 is read from the frozen expansion trees
  `experiments/crta_v3_stage_endpoint_expansion_{nh2kn,kn2nh}_v1`; it is
  not refit.  New cells: 2 directions × 10 endpoints × 10 seeds ×
  4 α × 4 arms = **3,200 fits**.
- Output: `experiments/crta_v3_stage_source_informativeness_ladder_v1/
  {direction}/alpha_{α}/{endpoint}/seed_{s}/metrics.json`, plus a
  permutation audit (per-cell permutation SHA-256, realized moved
  counts, fixed-point count at α=1) per direction × α.

## Adjudication (frozen)

For each (direction, endpoint, seed, α), the corrected interaction of
the frozen adjudicator:

    I*(α) = (f(a11) − f(a10)) − (f(a01) − f(a00)),  f(A) = max(A, 1−A).

Unit curves: per (direction, endpoint), the seed-mean I* at each
α ∈ {0, .25, .50, .75, 1}; α=0 from the frozen trees.  Endpoint
clusters: the two directions of an endpoint averaged (the frozen
post-hoc convention; 10 clusters).  Bootstrap: 10,000 reps, seed
20260820, resampling the 10 endpoint clusters, seed key
`stage_ladder|{quantity}`.

- **RS-P1 (graded decline):** per-unit Spearman ρ of the 5-point curve
  against α, averaged into endpoint clusters — cluster-bootstrap mean
  ρ < 0 and CI95 entirely below 0.
- **RS-P2 (endpoint decline):** D = Ī*(0) − Ī*(1) per endpoint cluster —
  mean > 0, CI95 low > 0, win ≥ 0.60.
- Verdict = RS-P1 ∧ RS-P2.  Descriptives: pooled corrected I*(α) curve
  with cluster-bootstrap CIs, per-direction curves, the raw
  (uncorrected) variant, and the drop-diabetes sensitivity of RS-P1/P2
  (declared sensitivity, not a gate, given the known concentration).

Interpretation map, declared now:

- RS-P1 ∧ RS-P2 → the real-data M×C interaction tracks source-label
  integrity: the controlled mechanism has a real-data fingerprint under
  direct manipulation; report alongside the α=1 residual (which bounds
  the non-label-mediated arm differences: feature harmonization and
  support-label mapping remain active at α=1 by design).
- RS-P2 passes, RS-P1 fails → the interaction is destroyed by full
  corruption but not gradedly; weak-form support only.
- Both fail (flat or rising curve) → the real interaction is not
  driven by source-label pairing; the mechanism does not transfer as
  measured, reported as a boundary of the controlled-benchmark claim.
- Direction disagreement in the descriptives is reported but does not
  gate (the estimand is the endpoint-cluster mean, as frozen).

## What this experiment cannot show

α=1 does not remove the M axis's feature-harmonization or
support-label-mapping differences, so I*(1) is not forced to zero by
construction; the estimand is the decline attributable to source-label
pairing, not a full decomposition of I*.  AUROC's boundedness and the
per-arm polarity correction f make the metric scale incommensurate with
the MCR ladder's nMSE-based I_MC; only signs and orderings are
compared, never magnitudes.

## Execution

Runner `scripts/run_crta_v3_stage_source_informativeness_ladder_v1.py`
(wraps the frozen engine per direction × α; resumable via the engine's
own cell cache), summarizer
`scripts/summarize_crta_v3_stage_source_informativeness_ladder_v1.py`
(recomputes every permutation from the frozen seeds and verifies the
audit SHA-256s and nestedness before adjudicating), self-test
`scripts/test_crta_v3_stage_source_ladder_synthetic_v1.py` (derangement
determinism/no-fixed-point, dose nesting and tolerance on a hand-built
permutation, idempotent builder wrapping, multiset preservation).
Committed with this document before launch.  Local CPU ≤ 16 threads
across shards, no GPU (contract), public-use NHANES/KNHANES parquets
(SHA-pinned; NHANES via the T71 mount), aggregate metrics only.
