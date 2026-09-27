# MCR-RL — the redundancy ladder: internal report

Status: complete, 40/40 family-by-realization cells (pairwise and sparse,
20 realizations each).  **Internal only — deliberately not in the
manuscript and not in any review-response file.**  Protocol frozen and
committed before execution: `PROTOCOL_V1.md` (commit `dc61ce762`).

## What was run

MCR-VR established two endpoints and nothing between them.  This fills in
the interior by removing a nested, frozen-random prefix of the true
pairs' constituent base columns and reading operation-column utility at
every rung.  `U(k) = nMSE(free) - nMSE(op_true)`; nMSE is
`MSE / Var(y_query)`, lower is better, so **positive U means the compiled
operation columns help**.

## Verdicts (K=32 primary; grid = 2 families x 2 backbones)

| verdict | result | grid |
|---|---|---|
| RL1 monotone rise | **pass** | 4/4 |
| RL2 endpoints reproduce VR | **pass** | 4/4 |
| RL3 interior is not a step | **pass** | 4/4 |
| graded_redundancy_budget | **true** | — |

Within-realization Spearman between `k` and `U(k)` is `+0.986` to `+0.990`
(CI low `+0.970` or higher), win 1.00 in every stratum; K=512 gives
`+0.977` to `+1.000`.  The rise is essentially deterministic per cell.

## The curve (K=32, both backbones agree to ~0.002)

| k removed | pairwise U(k) xgb | sparse U(k) xgb |
|---:|---:|---:|
| 0 | `+0.0021 [-0.0015,+0.0054]` | `+0.0000 [-0.0032,+0.0032]` |
| 1 | `+0.0362 [+0.0278,+0.0446]` | `+0.0678 [+0.0443,+0.0957]` |
| 2 | `+0.0724 [+0.0615,+0.0831]` | `+0.1435 [+0.1212,+0.1668]` |
| 3 | `+0.1233 [+0.1106,+0.1362]` | `+0.2084 [+0.1897,+0.2280]` |
| 4 | `+0.1676 [+0.1531,+0.1816]` | `+0.2466 [+0.2213,+0.2702]` (n=8) |
| 5 | `+0.2072 [+0.1907,+0.2235]` | — |
| 6 | `+0.2420 [+0.2267,+0.2571]` | — |

Only 8 of 20 sparse realizations have `|C| = 4`; that rung's `n` is
reported rather than pooled away.  Figure: `LADDER_U_CURVE_V1.png`.

## The arm decomposition is the substantive result

The contrast hides what produces it.  Arm means below are over exactly the
realizations that contribute to `U` at each rung, so they subtract to `U`
exactly (checked: max deviation `2.8e-16` over all 44 rung-strata).

| stratum, K=32 | supplied (`op_true`) | reference (`free`) |
|---|---|---|
| pairwise XGB, k=0 -> 6 | `.708 -> .741` (**+.033**) | `.710 -> .983` (**+.273**) |
| sparse XGB, k=0 -> 4 | `.731 -> .776` (**+.046**) | `.731 -> 1.023` (**+.292**) |
| pairwise HistGB | `.708 -> .742` | `.710 -> .983` |

The supplied arm barely moves; the reference collapses by roughly eight
times as much.  Utility rises from 0 to `+.24` while the supplied arm gets
slightly *worse* in absolute terms.  The entire effect is the reference
moving, so it is invisible in the supplied arm alone and cannot be
measured without a reference.  Figure:
`LADDER_ARM_DECOMPOSITION_V1.png`; paper version
`iclr_latex_v3/figures/appendix_figure_a8_redundancy_ladder.pdf`.

Read the other way: this does not show relation knowledge is intrinsically
valuable.  Usefulness here **is** non-redundancy.  What the ladder adds is
that the redundancy declines smoothly with how much of the constituent set
the frame retains, rather than switching on at the last column.

## Reference admissibility (verified, not assumed)

At every rung both arms must see the identical reduced frame and differ
only in whether the operation column is present, or the reference is not
admissible.  `scripts/verify_crta_v3_mcr_redundancy_ladder_frames_v1.py`
checks this on the actual fit and query matrices — shared block
bit-identical, `op_true` exactly `n_op` columns wider, `sig_true` equal to
`op_true` except in its constraint vector, removal sets nested and of the
declared size: **456/456 pass** across both families, all 20 realizations,
both support budgets, every rung.

The constraint channel on top of non-redundant values (`S` at the top
rung) is separated 4/4 at both budgets, `+0.0085..+0.0174`, reproducing
MCR-VR's V2.

## Endpoint identity — a declared check that failed, was diagnosed, and passed like-for-like

The protocol required the five endpoint arm means to agree with the
published VR tree within `0.005` nMSE.  **Against the published tree the
check failed**: worst deviation `0.0075`, 708/800 exact.

Every one of the 92 deviating comparisons is HistGB; **all 400 XGBoost
comparisons are bit-identical**.  The published VR tree was fit at
`threads=2` on `cloud-hq1Cey`; this ladder at `threads=1` locally, and
`run_crta_v3_mcr_factorial_semisynth_v1.py` documents in its own source
that parallel histogram accumulation perturbs these fits at the bit
level.  Re-fitting the unmodified frozen VR runner at `threads=1` on this
host (`experiments/_recheck_vr_threads1`, 40/40) removes the deviation
completely: **800/800 bit-identical, worst delta `0.0`.**

The declared tolerance was not relaxed.  Both comparisons are recorded in
`SUMMARY_V1.json` under `endpoint_identity_vs_vr`, and the verdict gate
uses the like-for-like one.  Consequence for the wider project: HistGB
cells in this codebase are reproducible only at a fixed thread count, and
cross-host HistGB comparisons at differing `--threads` can move an nMSE
by up to ~0.008.

## Scope — what this does and does not license

This is the **constructed semi-synthetic benchmark**, with M and C true in
every arm and a synthetic outcome.  It shows that in that world
operation-column utility is a graded function of the frame's residual
expressiveness rather than a step at full removal.  It **bounds** the
real-data utility nulls by locating them at the redundant end of a curve;
it does **not** diagnose them.  Two boosted-tree implementations only.
No claim here may be written as architecture-general, and none of it may
enter a frozen claim without its own preregistration.

Artifacts: `SUMMARY_V1.json`, `LADDER_U_CURVE_V1.png`, 40 per-cell
`metrics.json`, shard logs in
`logs/crta_v3_mcr_redundancy_ladder_v1/`.
