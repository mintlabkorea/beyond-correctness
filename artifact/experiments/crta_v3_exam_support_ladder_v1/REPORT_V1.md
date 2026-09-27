# Examination correspondence utility across labeled target support — internal report

Status: complete, 130/130 cells (13 endpoints × seeds 50–59 × K ∈ {64, 256,
1024}, three frozen arms, plus a class-A `min_child_weight` diagnostic
ladder).  Protocol frozen and committed before execution: `PROTOCOL_V1.md`
(commit `73fa916a7`).  Executed on `anonymous` (`cloud-hq1Cey`) in an
isolated clone, conda env `coret_pin`, CPU only, 13 shards × 2 threads.
Not in the manuscript.

## Verdict

**SUPPORTED, within the selected panel.**  The correspondence utility
declines with the number of distinct labeled target rows at fixed
target-domain mass.

| class A, 6 endpoints | K=64 | K=256 | K=1024 |
|---|---:|---:|---:|
| utility `S − R_domain_local` | `+.0697 [+.0374,+.1025]` | `+.0473 [+.0175,+.0842]` | `+.0180 [+.0079,+.0280]` |

- Primary decay `utility@64 − utility@1024` = **`+.0518`**, bootstrap
  `[+.0279,+.0766]`, **endpoint Student-$t$ `[+.0217,+.0818]`**, win `.78`,
  drop-best-endpoint `+.0454`.  Both intervals exclude zero, and the mean
  clears the frozen SESOI of `.020`.
- Retention `m(1024)/m(64)` = **`.26 [.18,.35]`**.
- The result lands **inside** the prediction interval `[+.049,+.096]` that
  was frozen before execution.

**All six class-A endpoints decay positively**, including `dbp`, whose
`K=256` utility was `+.0006`.  The drop-best-endpoint mean `+.0454` against
a pooled `+.0518` shows this is not the glucose endpoint alone — unlike the
`K=256` level, where glucose carried a third of the effect.

## Execution incident and full recomputation

**Disclosed because it affects how the numbers were produced.** The launch
was issued three times: each `ssh` invocation appeared to fail because the
session never returned, but all three had in fact started. Thirty shard
processes ran concurrently against the **same** `--out-root` (sharding was by
`--targets` only, so duplicate shards for an endpoint targeted the same file
paths), at roughly 60 cores against a 26-core authorization. They were
stopped with the exact-script `pkill`, and the run was relaunched once.
**120 of the 130 files were written during that contaminated window**; only
10 came from the clean relaunch.

Parse-and-structure validation of the 130 files was not a sufficient answer,
because the summarizer reads the tree by `glob("*/seed_*/metrics.json")`
with no manifest and no per-shard isolation. The whole panel was therefore
**recomputed from scratch** into a separate output root by a single clean
launcher invocation (13 shards, no duplicates), and compared value by value:

| comparison | values | float-equal | mismatches |
|---|---:|---:|---:|
| primary ladder (130 cells × 3 rungs × 3 arms) | 1,170 | 1,170 | **0** |
| class-A `min_child_weight` diagnostic ladder | 540 | 540 | **0** |
| **total** | **1,710** | **1,710** | **0** |

Support-row draws, `n_source`/`n_pool`/`n_query`, and the member derangement
also match in all 130 cells. Re-running the summarizer on the clean tree
reproduces `levels`, `decays`, the diagnostic ladder, the absolute
trajectories, the per-endpoint table, and the `verdicts` block **identically**
— primary decay `0.0517533226` against `0.0517533226`.

Why no contamination was possible in the end: the configuration is
bit-reproducible on this host (independently demonstrated by the 390/390
match against the earlier v2 run), so duplicate processes computing the same
cell emit identical bytes; and `Path.write_text` truncates then writes
sequentially, so an interrupted write leaves an unterminated prefix that
would have failed the `json.loads` in the runner's own resume path and
crashed the relaunch. It did not. The recomputation confirms this
empirically rather than by argument.

Verification artifacts: `VERIFICATION_RERUN_SUMMARY_V1.json`, logs in
`logs/crta_v3_exam_support_ladder_v1/verification_rerun/`. The recomputed
cell tree remains on `anonymous` at
`~/coret_exam_ladder/experiments/_verify_crta_v3_exam_support_ladder_v1/`;
it is byte-identical to the committed tree and is not duplicated here.

## Integrity

- The `K=256` rung reproduces the published expanded-panel cells **exactly:
  390/390 float-equal, zero missing baselines**, under the strict criterion
  (not a tolerance).  Library versions matched, so no degradation clause
  fired.
- Pool floor `n_pool ≥ 4·1024 = 4,096` holds for all thirteen endpoints
  (minimum observed 5,988).

## What the decay actually is

This is the part that determines the reading, and it is visible only in the
absolute trajectories the protocol made mandatory.

| class A, mean nRMSE (lower better) | K=64 | K=256 | K=1024 | 64→1024 |
|---|---:|---:|---:|---:|
| `S_shared_bridge` (supplied) | .7385 | .7002 | .6761 | `−.0623` |
| `R_domain_local` (reference) | .8082 | .7476 | .6941 | `−.1141` |
| `W_deranged_bridge` (wrong) | .9238 | .7698 | .7043 | `−.2195` |

**Every arm improves as target support grows; they improve at very different
rates, and the gap closes.**  The supplied arm is not degrading — it improves
too, just least.  The utility falls because the reference catches up.  That
is exactly the mechanism the manuscript states for the controlled setting:
the target itself comes to supply what the bridge was supplying.

The decomposition `utility = content − (reference − wrong)` holds cell by
cell and both parts decay:

| decay 64−1024, class A | mean | bootstrap | win |
|---|---:|---|---:|
| utility `S − R` | `+.0518` | `[+.0279,+.0766]` | .78 |
| content `S − W` | `+.1571` | `[+.0654,+.2792]` | .97 |
| reference `R − W` | `+.1054` | `[+.0222,+.2156]` | .80 |

The correct−wrong gap decays about three times as fast as the utility.  Most
of what a naive gap would report as "the benefit shrinking" is the
matched-wrong arm recovering, not the benefit disappearing — which is the
manuscript's own thesis, now visible along a support axis.

## The pre-declared adjudicator comes down on the semantic side

Both adversarial reviews independently predicted the same artifact: at
`K=64` a support row carries weight `n_source/K` = 348 (glucose) to 939
(waist_cm) against `min_child_weight = 1`, so a single target row can found
a leaf, and the exposure is asymmetric — `R_domain_local`'s target-local
column contains only target rows, so target-pure leaves are constructible
there, while `S_shared_bridge`'s shared column places the same values among
thousands of weight-1 source rows.  A decay produced by single-row leaf
memorisation in the reference would be indistinguishable from the predicted
decay at the level of the contrast.

The frozen diagnostic re-ran the ladder with `min_child_weight =
8 · n_source / K`, forcing at least eight distinct target rows behind any
target-only leaf at every rung, changing nothing else:

| class A, decay 64−1024 | mean | bootstrap | win | gate |
|---|---:|---|---:|---|
| primary (`min_child_weight = 1`) | `+.0518` | `[+.0279,+.0766]` | .78 | pass |
| diagnostic (`= 8·n_source/K`) | **`+.0614`** | `[+.0324,+.1067]` | .95 | pass |

**The decay survives, and is if anything larger.**  Single-row leaf
memorisation is excluded as the explanation.

## Reference coherence across the ladder

Reported as a descriptive property, not a gate (see protocol).

| `R − W` | K=64 | K=256 | K=1024 |
|---|---:|---:|---:|
| mean | `+.1156` | `+.0222` | `+.0102` |
| CI95 | `[+.0241,+.2374]` | `[+.0019,+.0429]` | `[+.0017,+.0211]` |

`R_domain_local` clears the coherence check at every rung, so the ladder does
not rest on an incoherent reference at either end.  The margin does shrink
sharply with `K`; at supports beyond this ladder the check would likely stop
separating, which bounds how far this design could be pushed.

## Where the pre-declaration was wrong

The protocol projected the pooled thirteen-endpoint decay at `+.018--+.027`,
`t ~ .9`, and stated it was **expected to fail** its gate.  Observed:

> thirteen endpoints, decay `+.0307`, bootstrap `[+.0029,+.0563]`,
> Student-$t$ `[+.0032,+.0583]`, win `.63` — it **passes**.

The projection was too pessimistic.  Recording this because the protocol
pre-declared the opposite; it is non-verdict-bearing either way, but a
pre-declaration that missed must be reported as having missed.

Per class (descriptive, no interaction test was preregistered):

| class | decay 64−1024 | gate |
|---|---:|---|
| A (cardiometabolic) | `+.0518` | pass |
| B (alt, bun) | `−.0294` | fail |
| C (base-slot targets) | `+.0296` | fail |

The bonus question — why the utility vanished on thirteen endpoints — gains
a support-side reading that does **not** replace the structural one.  At
`K=64` the thirteen-endpoint utility is `+.0391 [+.0073,+.0689]` and clears
the gate; at `K=256` it is `+.0137` and fails; at `K=1024` it is `+.0084`
and fails.  The expansion's collapse is therefore partly a support effect
and not only an endpoint-family effect: the added endpoints are not merely
inert, they sit further along the same decay curve.  Under a multiplicative
endpoint model this correlation between level and decay is expected by
construction, so it is reported as description, not mechanism.

## What this does and does not license

**Settled.**  On these cells, columns, splits, seeds, and learner, the
correspondence utility declines steeply and monotonically in the number of
distinct labeled target rows; the decline is not an artifact of single-row
leaf memorisation; it consists of the reference catching up rather than the
supplied arm degrading; and it holds for every class-A endpoint rather than
resting on glucose.

**Not licensed, and declared before execution.**  No wording may claim that
"the controlled law extends to real data."  Three reasons, all frozen in the
protocol:

1. **A different comparative static.**  The frozen real-data convention pins
   the target block's total weight at `n_source` for every `K`, so this
   sweeps distinct-row count at fixed target-domain mass.  The controlled
   benchmark uses `weights = np.ones(...)`, moving count and mass together.
   The named follow-up is the mass channel (per-row weight held at
   `n_source/1024`), not run here.
2. **Retention is 2--4× the controlled law's.**  `.26 [.18,.35]` here
   against `~.07--.14` there.  The direction agrees; the magnitude does not.
3. **The panel is outcome-selected.**  Class A is the subset that survived
   when the thirteen-endpoint expansion collapsed the level.

**The prediction was calibrated, not blind.**
`experiments/crta_v3_m1m2_layer_ladder_v1` already held a completed
`K ∈ {64,256,1024}` sweep on these exact endpoints and seeds with different
arms, showing retention `.35` and `.18`.  That is why the protocol froze a
numeric prediction interval instead of a direction, and why a result inside
it (`+.0518` in `[+.049,+.096]`) is a **replication of an already-observed
pattern in new arms**, not an independent discovery of the direction.

**`hba1c` must not be added in response to this result**, per the
expanded-panel protocol and restated in this one.

## Named follow-ups, declared before execution

1. The mass channel: `K=64` at per-row weight `n_source/1024`.
2. `subsample = 1.0`, to remove tree-to-tree target-block jitter (CV 6.25%
   at `K=64` against 1.56% at `K=1024`).
3. Nested supports `A64 ⊂ A256 ⊂ A1024`; measured `ρ(64,1024) ≈ 0` implies
   this would reduce the decay SE by only about 2--5%.

Artifacts: `SUMMARY_V1.json`, `SUPPORT_LADDER_V1.png`, 130 per-cell
`metrics.json`, logs in `logs/crta_v3_exam_support_ladder_v1/`.
