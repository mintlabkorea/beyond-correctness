# Pre-registration: MCR-MD — measurement utility as a function of mismatch dose

Drafted 2026-08-24; to be freeze-committed before any cell is fit.

## Motivation and prior observation disclosure

The manuscript's conclusion states that correct knowledge helps when it
"resolves a consequential mismatch", but no experiment manipulates the
mismatch itself.  The MCR factorial manipulates the *knowledge* (true vs
wrong tables) at a fixed, effectively total rendering mismatch, and MCR-D
doses the *corruption of the knowledge*; neither contains an *M-absent*
reference (a raw, undecoded source arm) — the M axis has correct and
matched-wrong levels only, so measurement **utility** (correct vs absent)
has never been measured in the constructed world, only measurement
**content** (correct vs wrong).  Known prior results, disclosed: P1
measurement content separates everywhere; MCR-D shows graded content
dose–response; the real-data ten-endpoint raw pooled AUROC was .556 and
the real M utility evidence rests on three polarity-reversed endpoints.

This experiment adds the missing reference arm and doses the **mismatch**:
the fraction of source features whose recorded form actually disagrees
with the canonical target frame.  The estimand is measurement utility as
a function of mismatch dose,

    U(d) = Q(decode) − Q(raw at dose d),  d ∈ {0, 2, 4, 6, 8} features.

At d=0 the source is recorded canonically and `raw` is bit-identical to
`decode` (asserted), so U(0)=0 by construction — the admissibility
boundary of Eq. (2) in the paper.  The registered prediction is that
U(d) increases with d; a flat or threshold-shaped curve is informative
and will be reported as such.

## Frozen design

- Cells: the identical frozen 60 primary cells (`mcr_v1c` namespace);
  rows, mechanism, outcome, renderings, support draws, and the true
  source table are reused unchanged from the frozen MCR runner's
  `build_cell`.  No lesion arms are used: C is true routing, R is free
  in every arm.
- **Mismatch dose.**  Per realization, an outcome-blind balanced order
  interleaves the 4 ordinal and 4 continuous features: draw one
  permutation of the ordinal features and one of the continuous
  features from `stable_seed("mcr_mismatch_dose_v1", "dose_order",
  family, realization, type)` and take o0,c0,o1,c1,o2,c2,o3,c3.  The
  dosed set at dose d is the first d entries (nested prefixes; each dose
  level has d/2 ordinal + d/2 continuous features).  Dosed features are
  recorded in the cell's frozen source rendering (codes with
  direction/base and live ordinal sentinels; affine-transformed values
  with ±99 sentinels).  Undosed features are recorded canonically:
  ordinal as the canonical bin means, continuous as z, missing as NaN —
  exactly the values the true decode would produce.
- Arms per cell (fit matrices differ only in the source block; target
  support/query frames are the frozen arm-invariant objects):
  - `decode` — the full true decode of the frozen rendering; identical
    for every dose (asserted bit-equal to the `m1c1rf` source block) and
    therefore fit once per cell × K × backbone.
  - `raw_d{2,4,6,8}` — dosed columns raw with the true sentinel codes
    neutralized to NaN; undosed columns canonical.  The primary
    reference: it isolates coding/unit mismatch from sentinel poison.
  - `rawsent_d{2,4,6,8}` — the same with sentinels left live
    (descriptive: the no-knowledge-at-all severity).
  - At d=0 both raw arms are bit-identical to `decode` (asserted); their
    records are copied with `identical_by_construction: true`, not
    refit.
- Backbones and budgets: XGBoost at K ∈ {32, 512} and
  HistGradientBoosting at K = 32, both with the frozen factorial
  configurations via the frozen runner's `fit_predict` with an all-zero
  constraint vector.  Unweighted pooling.  9 fits per cell × backbone-K
  = 27 per cell, **1,620 fits** total.
- Construction asserts per cell: the rebuilt source rendering
  reproduces `cell.source_rendered` bit-exactly; `rawsent_d8` equals
  `cell.source_rendered`; `raw_d8` equals it after sentinel→NaN;
  dosed sets are nested; the per-dose count of entries differing from
  the canonical frame is nondecreasing in d.

## Adjudication (frozen)

Q = −MSE/Var(y_query); families are fixed strata; per-family
realization bootstrap (20 units, 10,000 reps, seed 20260820, seed key
`mcr_md|{quantity}|{family}|{backbone}|{K}`); separated = mean > 0 ∧
CI95 low > 0 ∧ win ≥ 0.60.

- **MD-P1 (graded utility):** per family × backbone at K=32, the
  realization-level Spearman correlation of U(d) against d over the
  five doses — mean ρ > 0 and CI95 above 0.
- **MD-P2 (anchor):** U(8) separated in every family × backbone at
  K=32.  This is the constructed-world measurement-utility analog of
  P3b, at the factorial's native (total) mismatch.
- Grid verdict = MD-P1 ∧ MD-P2 in all three families × both backbones.
  XGBoost K=512 repeats both as confirmatory.  The `rawsent` curve, the
  mean U(d) tables, and per-dose mismatch composition are descriptive.

Interpretation map, declared now:

- P1 ∧ P2 → measurement utility is mismatch-dose-graded: correct
  knowledge helps in proportion to the consequential mismatch it
  resolves; this licenses the paper's condition (i) as a manipulated
  result, not an inference.
- P2 passes, P1 fails → utility exists at full mismatch but is not
  graded (threshold-shaped); condition (i) holds only in its weak form.
- P2 fails → decoding provides no detectable utility over raw transfer
  even at total mismatch in this benchmark; the real-data utility nulls
  can then NOT be attributed to small mismatch, and the paper's
  condition (i) loses its constructed-world support — reported as such.
- Backbone disagreement → scope to the backbone that shows it.

## What this experiment cannot show

It reads the utility of *correct* decoding against *absence*; it does
not revisit content (correct vs wrong), which MCR-D already dosed.  The
dose unit is "features rendered discrepantly", not a calibrated severity
scale; ordinal and continuous discrepancies are balanced per dose but
their severities are not equated.  Sentinel knowledge is granted to the
primary reference arm by design; `rawsent` bounds the no-knowledge case
descriptively.

## Execution

Runner `scripts/run_crta_v3_mcr_mismatch_dose_v1.py` (per-cell
`metrics.json`, cached/resumable, provenance-hashed), summarizer
`scripts/summarize_crta_v3_mcr_mismatch_dose_v1.py`, self-test
`scripts/test_crta_v3_mcr_mismatch_dose_synthetic_v1.py` (rendering
rebuild identity, d=0/d=8 bit-identities, nested balanced dose order,
decode-block equality with `m1c1rf`, monotone mismatch-entry counts).
Committed with this document before launch.  Local CPU ≤ 6 threads
total, no GPU (contract), public-use panel, aggregate metrics only.
