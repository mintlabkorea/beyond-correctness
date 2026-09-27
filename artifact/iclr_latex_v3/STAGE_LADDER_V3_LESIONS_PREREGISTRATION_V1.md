# Pre-registration: real-data M×C ladders v3 — which source/support information sustains the interaction?

Drafted 2026-08-25; to be freeze-committed before any cell is fit.

## Why — prior observation disclosure

Two real-data ladders have now failed the source-integrity prediction:
v1 (frozen M axis) and v2 (source-only M axis) both left the corrected
M×C interaction flat through α=.75 and rising at α=1 (+.031→+.057;
+.041→+.059) when the SOURCE LABELS were nested-permuted.  With support
labels held correct (v2), the measurement content that remained at α=1 was
the harmonization of source features, and the interaction persisted.  The
open question is therefore what information sustains it.  Three lesions,
run in the order below with a declared stopping rule, ask that question.
All prior numbers are known and are not re-adjudicated.

A note on construction: permuting the source feature ROWS jointly while
leaving labels in place yields exactly the same set of (x, y) pairs as
permuting the labels, so it is the v2 ladder in disguise and is NOT run.
The feature lesions below act on values (A2) or on each column
independently (A1).

## Common frozen design

- Engine: the source-only fork `run_crta_v3_m1m2_stage_factorial_source_only_v1.py`
  exactly as in v2 (support labels documented-mapped and target features
  harmonized in every arm; M-off = raw source features + identity source
  labels).  Registry, seeds 50–59, K=256, XGBoost, four interaction arms,
  `derived_rng` namespaces, SHA-pinned parquets: unchanged.
- Dose 0 for every ladder = the v2 α=0 cells
  (`crta_v3_stage_source_ladder_v2_source_only_v1/{dir}/alpha_0.00`),
  read and never refit.  New doses {.25, .50, .75, 1.00}; per ladder
  2 directions × 10 endpoints × 10 seeds × 4 doses × 4 arms = 3,200 fits.
- Nested constructions reuse the frozen cycle-prefix machinery
  (`run_crta_v3_mcr_source_informativeness_ladder_v1.py`), with
  lesion-specific seed namespaces so each ladder's draws are independent
  of v1/v2 and of each other.  Every cell carries the lesion tag and the
  audit records the per-cell permutation/parameter hashes; the summarizer
  recomputes and verifies them and checks nesting across doses.
- Estimand and adjudication are those of v1/v2: corrected
  I*(dose) = (f(a11) − f(a10)) − (f(a01) − f(a00)), f(A) = max(A, 1−A);
  seed means; endpoint clusters (two directions averaged); bootstrap
  10,000 reps, seed 20260820, key prefix `stage_ladder_v3|{lesion}`.
  **P1:** cluster-mean per-unit Spearman(I*, dose) < 0 with CI95 below 0.
  **P2:** I*(0) − I*(1) > 0, CI low > 0, win ≥ .6.  Ladder verdict = P1 ∧ P2.

## Lesion A2 — source-feature rendering corruption (`source_feature_render`)

Source (x, y) pairing intact; the CODING of a nested fraction β of the
source feature slots is made discrepant with the target frame (the
real-data analog of MCR-MD, applied on top of each arm's own
harmonization state):
- slot order: outcome-blind permutation of the feature slots present in
  the cell (`ALL_SLOTS` minus the endpoint), keyed
  `stable_seed("stage_ladder_v3_render_order", direction, endpoint, seed)`;
  the first ⌈β·n_slots⌉ slots are corrupted (nested prefixes);
- continuous slots (base clinical and member slots): affine distortion of
  the source prefix only, x′ = m + s·(x − m) + o·sd, with
  s = exp(U(ln .25, ln 4)) and o = U(−2, 2) drawn per (direction,
  endpoint, seed, slot), m and sd the source column's mean/SD; NaN kept;
- survey slots (`sex`, `education_level`, `diabetes_history`,
  `hypertension_history`, `current_smoking_status`, minus the endpoint):
  a keyed random non-identity permutation of the column's observed
  (non-NaN) value set applied to the source prefix; applied to whichever
  values the bundle carries (raw codes in M-off, harmonized values in
  M-on), so the lesion is defined per bundle but keyed identically.
- Target/support features, all labels: untouched.
Prediction: if source-feature alignment sustains the interaction,
I*(β) declines.

## Lesion A1 — source-feature column-wise permutation (`source_feature_colperm`)

Each source feature column's prefix [0:n_source] is nested-permuted with
its OWN derangement (key `stable_seed("stage_ladder_v3_colperm",
direction, endpoint, seed, column)`; cycle order key
`…_colperm_cycle_order`), destroying the feature–label pairing and the
inter-feature structure while preserving every marginal.  Labels and
target side untouched.  Prediction: if anything beyond the source
marginals sustains the interaction, I*(β) declines; if not, the
interaction is a property of marginal commensurability.

## Lesion B — support-label corruption (`support_label`)

Source block untouched; the raw training labels of the target POOL
suffix [n_source:n_train] are nested-permuted (key
`stable_seed("stage_ladder_v3_support", direction, endpoint, seed)`),
so the K=256 support rows drawn from that pool carry labels of other
pool rows in proportion γ; evaluation labels untouched.  Prediction: if
target-side supervision sustains the interaction, I*(γ) declines.

## Sequential rule (declared)

1. Run A2 and A1 (both cheap).  If A2 declines (P1 ∧ P2), the mechanism
   story is "source-feature alignment, not source-label informativeness";
   A1 is reported as the marginal-only bound.  Stop.
2. If A2 does not decline, run B.  If B declines: "target-side
   supervision combined with correspondence".  Stop.
3. If none declines, report that source-side integrity (labels, feature
   values, feature structure) and support-side supervision each fail to
   explain the interaction; a 3×3 joint (A2 × B) factorial is then
   considered separately, not run under this document.

Interpretation map is exhausted by the three rows of the table above
plus: dose-0 I* must remain separated (it is, +.041 [+.024,+.059]); a
ladder whose dose-1 I* is not separated from zero but whose Spearman CI
straddles zero is reported as "destroyed but not graded".

## Execution

Runner `scripts/run_crta_v3_stage_ladder_v3_lesions_v1.py`
(`--lesion {source_feature_render,source_feature_colperm,support_label}`),
summarizer `scripts/summarize_crta_v3_stage_ladder_v3_lesions_v1.py`,
self-test `scripts/test_crta_v3_stage_ladder_v3_synthetic_v1.py`
(identity at dose 0; only the intended block/columns change; nesting;
per-column independence; survey permutation non-identity; pool-only
label movement).  One-cell preflight per lesion is recorded below before
commit.  Remote CPU, pinned environment, RAM-capped shards; no GPU.

## Preflight (one cell each, nh2kn / diabetes_history / seed 50, dose 1.00; recorded before commit)

v2 α=0 reference arms (a00, a01, a10, a11) = (.7096, .5756, .8862, .9583), I* = +.206.
- A2 render: (.7276, .8047, .8088, .8877), I* = +.002; all 19 feature slots corrupted at dose 1.
- A1 colperm: (.8092, .8468, .7042, .7568), I* = +.015; 19 independent column derangements, 68,561 rows moved each.
- B support: (.4877, .3484, .8850, .9606), I* = −.064; 15,492 pool labels moved.
All audits written; fork tag present.  No other cell was fit before this commit.
