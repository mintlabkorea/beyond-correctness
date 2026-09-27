# Pre-registration: form–content deconfound batch (A1–A3) + analysis specs (B1–B4)

Declared 2026-08-20 ~04:50, **before any new cell has been executed.**
Addresses the paper-plan review: proposition 1 (narrowing survives,
widening dies) currently compares different knowledge across forms; these
runs put the SAME knowledge into both forms. Conventions as all night
(nRMSE lower-better, gain = reference − arm; hierarchical bootstrap
targets→seeds, 10k reps, seed 20260819; separation rule unchanged).

## A1 — Same knowledge, two forms (the deconfound; highest value)

Knowledge K = the frozen documented pair list of
`run_crta_v3_m1m2_monotone_anchor_v1.py` (5 undirected pairs with signs:
age–sbp, dbp–sbp, hba1c–glucose, chol–tg, weight–waist).

- **Narrowing form** (exists, reused from PAM v1 cells — identical
  splits): per target t, monotone constraints on the pairs containing t
  (`sign_documented`), lesion `pl_sign_flip`, reference `free`.
- **Widening form** (new, 2 fits/cell): per target t, for every
  documented pair whose BOTH members are features of t (t itself in no
  pair member), append difference and product features
  (`val_documented`); capacity placebo `val_random` = the same number of
  random pairs × same ops, redrawn per (target, seed), ≠ the documented
  set.

Frozen predictions: **A1-P1** `val_documented` vs `val_random` does NOT
separate (widening of the same knowledge is placebo-equivalent);
**A1-P2** `sign_documented` vs `pl_sign_flip` separates (known, on these
same cells). A1-P1 ∧ A1-P2 = same knowledge, same pairs, same cells,
opposite fates — proposition 1 becomes an experiment, not an anthology.
If A1-P1 separates instead, proposition 1's form claim is weakened and
must be reported as content-dependent.

## A2 — Correspondence utility vs the name-matching baseline

The binding placebo (deranged pairs) measures identification; the schema
-matching community's baseline is **string similarity with no
documents**. Frozen matcher: lowercase alphanumeric token sets of the
raw column names, token-Jaccard ≥ 0.5, greedy 1:1, applied to the 9
member variables' raw NHANES↔KNHANES names. The audited name-overlap
for this pair is 0.000, so the frozen expectation **A2-P1** is that the
matcher returns an (near-)empty mapping; the name-baseline arm then
degenerates to the base arm, and the documented mapping's value over the
baseline is the already-measured column margin (+0.215 with the proxy
caveat; binding content +0.065). A2 is executed as a materialization
script + verification note; if the matcher unexpectedly recovers ≥ 5/9
members, a real name-baseline arm must be run instead (declared branch).

## A3 — Direction constraint × support, BOTH regimes (the figure)

E1 falsified the within-pooled-regime crossover; the crossover
hypothesis moves across regimes. One experiment, the frozen anchor
script unchanged except SUPPORT_ROWS widened to
{16, 32, 64, 128, 256, 1024} (fresh root, seeds 10–19, arms
none/documented/flipped/random, backbones **xgb_support** (fit on K
rows only — genuine scarcity) and **xgb_transfer** (pooled)).

Frozen predictions: **A3-P1** in xgb_support, documented − none gain is
positive at small K and shrinks/vanishes by K=1024; **A3-P2** in
xgb_transfer, documented − none ≤ 0 at every K (E1's finding, replicated
under the anchor program's own weighting); **A3-P3** documented beats
flipped in both regimes at every K. The two-panel figure is the boundary
statement: "documented direction knowledge pays exactly when data is
genuinely scarce."

## B — Analysis specifications (no new cells)

- **B1**: per-endpoint decomposition + drop-best for the direction
  -constraint content result (+0.183/+0.186) — extracted from the
  existing PAM v1/rep1 summaries into the verification doc; the program's
  recorded weakness (single-endpoint headlines) gets its defense on the
  second-largest number.
- **B2**: label panel +0.29 — per-endpoint CIs and explicit effective-n
  statement (3 endpoints; hierarchical bootstrap already clusters at
  target level).
- **B3**: verification note that the binding lesion is proxy-exposure
  -matched **by construction** (the feature SET is identical across
  arms; only target-side content permutes), plus per-endpoint gains.
- **B4**: the identification × utility 2×2 (measurement-on-labels /
  direction-constraint / M4-stabilization / additive-forms) as a table —
  proposition 2 as structure; no empty cell.

Outputs land in `VERIFICATION_NOTES_20260820_V1.md`.

## Addendum A1′ (declared 2026-08-20 ~05:25, after A1's adjudication and before any A1′ cell)

A1-P1 was **falsified**: `val_documented` beat `val_random` (+0.00465
[+0.0013, +0.0085], win 0.70, 6/6 targets) — the same knowledge
separates in widening form too, though its content expression is ~40×
smaller than the constraint form's (+0.183) on identical cells. Before
interpreting that as pairing content, one confound must be removed,
identified post-hoc and tested pre-registered: the documented pairs live
among the strongest clinical variables, while the placebo pool included
weak survey/base columns — the separation may be **variable-strength
selection, not pairing knowledge**.

**A1′**: identical runner with `--pair-pool members` — the placebo pairs
are drawn only among the 9 member slots (strength-matched), fresh root.
Frozen predictions: **A1′-P1** if `val_documented` vs the
strength-matched placebo still separates, the pairing content is real in
widening form and proposition 1 must be weakened to "form modulates
content expression by an order of magnitude" (40× on these cells);
if it does NOT separate, A1's falsification was the strength confound
and proposition 1's original form stands with the strength-matched
placebo as its evidence. Either way the constraint-form 40× asymmetry
(A1-P2 on the same cells) is unaffected.
