# Pre-registration: real-data source-informativeness ladder v2 — SOURCE-ONLY measurement axis

Drafted 2026-08-25; to be freeze-committed before any cell beyond the
declared preflight is fit.

## Why v2 exists — prior observation disclosure

The v1 ladder (`STAGE_SOURCE_INFORMATIVENESS_LADDER_PREREGISTRATION_V1.md`)
reversed its prediction: the corrected pooled interaction I* was flat
through α=.75 and rose at α=1 (+.031 → +.057; RS-P1 ρ +.38 [+.09,+.66];
RS-P2 −.026 [−.045,−.009]).  Both directions and the drop-diabetes
sensitivity agreed.  That result is known and is NOT re-adjudicated here.

Its design limitation is the reason for v2: in the frozen stage
factorial the M axis is not source-only.  `a00`/`a01` (M-off) use the
harmonization-ablated build on **both** cohorts and identity labels on
**both** source and support rows, whereas `a10`/`a11` (M-on) harmonize
both cohorts and document-map both label vectors.  At α=1 the source
labels carry no pairing information, so whatever interaction remains
must come from the support side (256 upweighted rows whose labels are
mapped only in M-on) and from target-feature harmonization — the M
axis's *target-side* content, not source alignment.  v1 therefore
cannot isolate source pairing, which is what the controlled mechanism
claim is about.

v2 restricts the measurement axis to the source side:

| arm | source features | source labels | target/support features | support labels |
|---|---|---|---|---|
| M-on (`a10`,`a11`) | harmonized | documented map | harmonized | documented map |
| M-off (`a00`,`a01`) | **raw** | **identity** | harmonized | documented map |

C is unchanged (base vs base+members).  The registered prediction is
the v1 prediction, now for the quantity it was meant for: I*(α)
declines with source-label corruption.  If I*(α) is again flat or
rising, the real interaction is not source-mediated even when the M
axis is confined to the source, and the mechanism claim is
benchmark-scoped with no remaining design excuse.

## Frozen design

- Engine: `scripts/run_crta_v3_m1m2_stage_factorial_source_only_v1.py`,
  a fork of the frozen engine with three audited changes (documented in
  its header): a `off_source` build mode whose questionnaire rule index
  keeps only the target cohort's rows (runner asserts the filter is
  neither empty nor complete); the `wrong` bundle is not built (its
  arms are never fit); `a00`/`a01` label maps are `{source: identity,
  target: documented}`.  Everything else — registry, seeds 50–59, K=256,
  XGBoost configuration, support draws, `derived_rng` namespaces,
  parquet pins — is byte-identical to the frozen expansion.
- Corruption: the v1 construction and **the v1 seed namespaces**
  (`stage_source_ladder_v1`, `stage_source_ladder_cycle_order_v1`) are
  reused, so every (direction, endpoint, seed, α) cell corrupts exactly
  the same source rows as v1; α = 0 is a moved-count-0 identity map
  through the same code path.  α ∈ {0, .25, .50, .75, 1.00}, all refit
  (α=0 has new semantics and is not read from the frozen trees).
- 2 directions × 10 endpoints × 10 seeds × 5 α × 4 arms = **4,000 fits**,
  on the remote server (identical builder tree and SHA-pinned parquets;
  pinned environment), RAM-capped shards.  Every cell carries the fork
  tag `m_axis = source_only_fork_v1` and the target cohort; the
  summarizer rejects cells without it.

## Construction preflight (declared, run before the freeze)

One probe cell (nh2kn, diabetes_history, seed 50, α=0): the fork's
`a10_stage` and `a11_stage_columns` AUROCs must be **bit-identical** to
the frozen expansion cell (M-on is unchanged by construction), and
`a00_base`/`a01_columns` must differ (support labels now mapped).  The
observed values are recorded in the section below before commit; a
failed preflight blocks the launch.

## Adjudication (frozen; identical rules to v1)

I*(α) = (f(a11) − f(a10)) − (f(a01) − f(a00)), f(A) = max(A, 1−A), per
(direction, endpoint, seed); seed means; endpoint clusters (two
directions averaged); bootstrap 10,000 reps, seed 20260820, key prefix
`stage_ladder_v2`.

- **RS-P1:** cluster-bootstrap mean per-unit Spearman(I*, α) < 0 with
  CI95 entirely below 0.
- **RS-P2:** D = I*(0) − I*(1): mean > 0, CI low > 0, win ≥ .6.
- Verdict = RS-P1 ∧ RS-P2.  Descriptives: pooled curve with CIs, per
  direction, raw variant, drop-diabetes sensitivity, and the v1 curve
  side by side (same corrupted rows, different M axis).

Interpretation map, declared now:

- Both pass → with the M axis confined to the source, the real
  interaction tracks source-label integrity; v1's rise is attributable
  to the support-side content of the frozen M axis; the paper reports
  both ladders and scopes the mechanism to source alignment.
- RS-P2 passes, RS-P1 fails → decline only at full corruption.
- Both fail again → the real interaction is not source-mediated under
  either M-axis definition; the controlled mechanism is
  benchmark-scoped, stated without qualification.
- α=0 I* not separated from zero under the new semantics → the
  real-data interaction itself depended on the support-side M content;
  report that as the primary finding and the ladder as descriptive.

## Execution

Runner `scripts/run_crta_v3_stage_source_ladder_v2_source_only_v1.py`
(reuses the v1 permutation/wrap machinery pointed at the fork),
summarizer `scripts/summarize_crta_v3_stage_source_ladder_v2_source_only_v1.py`
(audit + nestedness verification for every α including 0).  Committed
with this document after the preflight numbers are appended.

## Preflight result (recorded before the freeze commit)

nh2kn / diabetes_history / seed 50 / α=0, local run: `a10_stage`
0.886212 and `a11_stage_columns` 0.958259 are **bit-identical** to the
frozen expansion cell; `a00_base` 0.709608 (frozen 0.718995) and
`a01_columns` 0.575607 (frozen 0.653801) differ as required; the α=0
map moved 0 rows (target 0); fork tag and target cohort recorded.
Preflight passed; no other cell was fit before this commit.
