# Internal protocol: MCR-RL — the redundancy ladder

Declared 2026-08-28, **before any ladder cell is fit**.  Internal only:
this experiment is deliberately excluded from the manuscript and from all
review-response files.  Nothing here may be folded into a frozen claim.

## Question

MCR-VR (`experiments/crta_v3_mcr_value_redundancy_v1`) established two
endpoints and nothing between them: with the true pairs' constituent base
columns present, the compiled operation columns are worth
`+0.0000..+0.0021` nMSE (null, 4/4 grids, both K); with every constituent
removed, the identical columns are worth `+0.232..+0.242` (separated,
win 1.00, 4/4, both K).

This experiment fills in the interior.  It asks whether operation-column
utility is a **graded function of how much of the constituent information
the frame still carries**, or a step that only appears once the last
constituent is gone.

## Ladder

For each `(family, realization)` cell, let `C` be the constituent set
(`constituents_of`: the union of features in the true relation set's
`pair_terms`; |C| = 6 for pairwise, 3 or 4 for sparse).  A permutation
`pi` of `C` is drawn once per cell from a frozen RNG keyed
`mcr_rl|{family}|{realization}` (seed = first 8 bytes of the key's
SHA-256).  Rung `k in {0, 1, ..., |C|}` removes `pi[:k]` from the frame.
The ladder is **nested by construction**: rung `k`'s removed set is a
subset of rung `k+1`'s, so each rung strictly removes more information
than the last.  Both `k` and `rho = k/|C|` are recorded, along with
`n_pairs_broken` (true pair terms with at least one leg removed), which
is the mechanistically ordered x-axis.

`keep_base(k)` = the base columns not removed; asserted non-empty at
every rung.  Operation columns are never removed.

## Arms (3 per rung, per K, per backbone)

All matrices are column subsets of the frozen `m1c1rf` / `r_op_only` /
`m1c1r1` matrices returned by the frozen factorial runner; M and C are
true in every arm; pooling is unweighted.

| arm | columns | constraints |
|---|---|---|
| `free` | `keep_base(k)` | none |
| `op_true` | `keep_base(k)` + true operation columns | none |
| `sig_true` | same columns as `op_true` | true monotone signs on the operation columns |

## Endpoint identity (integrity check, declared now)

By construction rung `k=0` reproduces MCR-VR's `full_free` / `full_op_true`
and rung `k=|C|` reproduces its `drop_free` / `drop_op_true` /
`drop_op_true_signed`.  The runner asserts the **column sets** are
identical at both endpoints.  Numerically the ladder is fit at
`threads=1` on a different host from the VR run (which used `threads=2`
on `cloud-hq1Cey`), and the frozen factorial runner documents that
parallel histogram accumulation can perturb fits at the bit level, so
agreement is adjudicated as a closeness check, not a bit-identity
claim: the five endpoint arm means must agree with the published VR
arm means to within `0.005` nMSE.  A larger deviation invalidates the
run and is reported as such.

## Adjudication (frozen)

`Q = -nMSE` (nMSE = MSE / Var(y_query); positive gain = lower error).
Primary support `K=32`; `K=512` secondary.  Backbones XGBoost and
HistGradientBoosting with the frozen factorial configurations.
Families (pairwise, sparse) are fixed strata; the independent unit is
the realization (20 per family).  Bootstrap: 10,000 reps, seed
20260828, key `mcr_rl|{contrast}|{family}|{backbone}|{K}`.
Separated = mean > 0 AND CI95 low > 0 AND win >= 0.60.
Null = CI95 contains 0 AND |mean| < 0.05 nMSE (the factorial's
exchangeable-null margin).

- **U(k) = Q(op_true, k) - Q(free, k)** — the ladder itself, reported
  with a CI at every rung.
- **RL1 (monotone rise).**  Within each realization, Spearman rho between
  `k` and `U(k)` across all rungs; the verdict is on the mean rho over
  the 20 realizations.  Passes a grid cell if rho-bar > 0 with CI95
  excluding zero.  Grid = 2 families x 2 backbones at K=32.
- **RL2 (endpoints reproduce VR).**  `U(0)` adjudicated as a null and
  `U(|C|)` adjudicated as separated, in every grid cell.
- **RL3 (interior is not a step).**  At the middle rung
  `k* = round(|C|/2)`, `U(k*)` adjudicated as separated.  This is the
  claim that utility appears **before** the last constituent is gone.
- Descriptive, no verdict word: `S(k) = Q(sig_true, k) - Q(op_true, k)`
  (the constraint channel along the same ladder); `U` against
  `n_pairs_broken`; per-family rung tables.

Interpretation map, declared now:

- RL1 and RL3 pass -> operation-value utility is graded in the frame's
  residual expressiveness; the VR endpoints are two points on a curve and
  the real-data utility nulls sit at the curve's redundant end.  This
  remains a **constructed-benchmark** statement: it bounds the real-data
  nulls, it does not diagnose them.
- RL1 passes, RL3 fails -> the rise is real but concentrated at the last
  rung; report it as a threshold, never as a dose.
- RL1 fails -> utility is a step at full removal; the "redundancy budget"
  reading is not supported and must not be written anywhere.
- Family or backbone disagreement -> scope to the stratum that shows it.

## Execution

Runner `scripts/run_crta_v3_mcr_redundancy_ladder_v1.py`, summarizer
`scripts/summarize_crta_v3_mcr_redundancy_ladder_v1.py`, self-test
`scripts/test_crta_v3_mcr_redundancy_ladder_synthetic_v1.py`.  Committed
with this document before launch.  Local CPU only, 8 workers x 1 thread
of 20 cores, no GPU (contract), public-use NHANES panel, aggregate
metrics only.
