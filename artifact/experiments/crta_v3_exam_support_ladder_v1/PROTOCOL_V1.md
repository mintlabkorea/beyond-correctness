# Examination correspondence utility across labeled target support — frozen design

Frozen before execution: 2026-09-01 (Asia/Seoul).  Post-result extension to
`iclr_latex_v3/EXAM_NO_BRIDGE_REFERENCE_FREEZE_V1.md` and to
`experiments/crta_v3_exam_reference_sensitivity_v2/PROTOCOL_V1.md`.  It does
not retroactively change either experiment's estimand, arms, learner, or
status.  `K=256` remains the primary support size of the published result.

This document was rewritten once, before any cell was fitted, after two
independent adversarial reviews of the first draft.  The pre-review draft is
kept at
`context/archive/2026-09-01-exam-support-ladder/PROTOCOL_V1_predraft_before_adversarial_review.md`
together with one of the reviews.  Every change the reviews forced is listed
in the final section.  No result existed when either draft was written.

## Question

The manuscript states a law supported **only** by the controlled benchmark:

> "the benefit of decoding grows with how much mismatch is left to resolve
> and **shrinks as labeled target support increases**" (`main.tex`,
> Conclusion).

Its two controlled instances: measurement-dose benefit falls from `~+.26 dQ`
at `K=32` to `+.022--+.037` at `K=512` (retention `~.10`), and the TransTab
shared-identifier benefit falls from `+.114--+.129` to `+.007--+.009`
(retention `~.07`).

The one real-data correspondence utility the manuscript reports,
`S_shared_bridge - R_domain_local = +.0473 [+.0171,+.0844]` on the six
cardiometabolic examination endpoints, was measured at **one** support size,
`K=256`.  That estimand has never been swept over `K`.

**This experiment sweeps it.**

## Disclosure of prior information and analysis order

**This prediction is not blind, and must not be presented as if it were.**

`scripts/run_crta_v3_m1m2_layer_ladder_v1.py:63` already defines
`SUPPORT_ROWS = (64, 256, 1024)`, and
`experiments/crta_v3_m1m2_layer_ladder_v1/` already holds **60 completed
cells** on the *same six class-A endpoints*, the *same seeds 50--59*, the
*same pinned weighting*, and the same learner family (only
`colsample_bytree` differs, `.8` there against `1.0` here).  Its arms are
column-presence arms, not the bridge arms, so the correspondence utility
itself is genuinely unmeasured across `K`.  But the decay behaviour of
closely related contrasts on these exact cells was already on disk before
this experiment was designed:

| contrast (existing ladder) | K=64 | K=256 | K=1024 | decay 64−1024 | retention |
|---|---:|---:|---:|---:|---:|
| `rung1_columns − loo_columns` | +.0879 | +.0500 | +.0306 | +.0573 | .35 |
| `rung1_columns − pl_columns` | +.1563 | +.0646 | +.0283 | +.1280 | .18 |

Consequences, accepted here rather than discovered later:

1. The direction of the prediction is **calibrated, not blind**.  The bare
   directional claim "utility shrinks as `K` grows" carries almost no
   information, because the project has already observed 3--5x decay of
   related contrasts on these cells.
2. What is therefore frozen instead is a **numeric prediction interval**.
   Anchoring on the bit-reproduced `m(256) = +.0473` and the per-4x
   retention ratio `r in [.41,.61]` implied by the ladder above:
   `m(64) in [.078,.115]`, `m(1024) in [.019,.029]`, and

   > **predicted primary decay `mu in [+.049,+.096]`, central `+.071`.**

   A result inside that interval is a **replication of an already-observed
   pattern in new arms**, not a discovery.  A result outside it is the
   informative outcome.
3. Post-result, no wording may claim this experiment independently
   established the direction.

## What is actually varied, stated precisely

Both conventions below are the project's existing ones, taken verbatim from
`scripts/run_crta_v3_m1m2_layer_ladder_v1.py`:

- **Draw.** `rng(seed * 131 + K).choice(n_pool, size=K, replace=False)`.
  Seeded with `K`, so the rungs are **independent draws, not nested**.
- **Weights.** Source rows weight `1`; each support row weight
  `n_source / K`.  The target block's **total** weight is `n_source` at
  every `K`.

So the quantity swept is **the number of distinct labeled target rows at
fixed target-domain mass** — a diversity/effective-sample-size channel.
Kish effective sample size of the fit frame rises from `~4K = 256` at `K=64`
to `~3,900--4,030` at `K=1024` despite constant total weight.

**This is not the controlled benchmark's comparative static.**  There
`weights = np.ones(...)`, so `K` moves count *and* mass together
(target:source mass `.016 -> .25`).  Here mass is pinned at `1.0` throughout.

The first draft of this protocol asserted that pinned weighting "can only
mute the predicted decay, never manufacture it."  **That assertion was
unjustified and is withdrawn.**  No such monotonicity result holds for
boosted trees; re-weighting can move histogram thresholds, split gains, and
row-subsampling behaviour in either direction.

**Therefore, declared now: no outcome of this experiment licenses the
sentence "the controlled law extends to real data."**  The strongest
permissible claim is

> a prospective support-sensitivity follow-up, within the previously
> positive six-endpoint panel, on the diversity channel at fixed
> target-domain mass.

The unit-weight ladder is **not** run, and the reason is recorded rather
than left implicit: unweighted, the target block would be `.1%--4.6%` of
total loss mass at these `n_source` (22,302--60,124), which is a
near-null manipulation by construction rather than a faithful transport of
the controlled regime.  The interpretable second channel — per-row weight
held at `n_source/1024` so that total target mass grows with `K` — is the
**named follow-up**, declared here so that appealing to it after a null is
not an escape.

## `K` grid, and why `1024` is the ceiling

`K in {64, 256, 1024}`.  `K=256` is re-run rather than copied, so the
ladder's middle rung is the published number itself.  The upper rung is
fixed by the project's **pre-existing** eligibility rule
(`crta_v3_exam_reference_sensitivity_v2/PROTOCOL_V1.md`, panel rule (b)):
the target pool must hold at least `4K` rows.  Observed pools are
`5,988--8,078`, so `4 x 1024 = 4,096` clears for all thirteen endpoints and
`4 x 2048 = 8,192` fails for every one.  `K=1024` is the largest admissible
rung, not a chosen one.  `64` is the base runner's existing bottom rung.

## Panel

The thirteen endpoints of the frozen expanded panel, in their frozen classes:

| class | endpoints | role here |
|---|---|---|
| A — target is a member slot | glucose, waist_cm, triglycerides, sbp, dbp, total_cholesterol | **primary** |
| B — target is neither | alt, bun | secondary, descriptive |
| C — target is a base slot | creatinine, hemoglobin, hematocrit, rbc, wbc | secondary, descriptive |

The verdict is declared on class A alone, because `+.0473` is a class-A
number.  Classes B and C and the pooled thirteen-endpoint ladder are run in
the same process and reported, but are **non-verdict-bearing by protocol**.

**Class A is itself an outcome-selected subset** — it is the group that
survived when the thirteen-endpoint expansion collapsed the level to
`+.0137`.  This experiment inherits that selection and cannot undo it.

**Projected, so that it is not later read as news:** using the
thirteen-endpoint variance components (`mean +.0137`, `tau .0503`,
`sigma .0313`), the pooled thirteen-endpoint decay is projected at
`+.018--+.027` with `SE .021--.030`, i.e. `t ~ .9`.  **The thirteen-endpoint
ladder is expected to fail its gate for any plausible decay ratio.**

Seeds 50--59.  **13 endpoints x 10 seeds x 3 support sizes = 390 primary
cells.**

## Arms

**Verdict-bearing (three, the frozen three):**

| arm | member encoding |
|---|---|
| `S_shared_bridge` | `[shared correct, all-missing pad]` |
| `W_deranged_bridge` | `[shared deranged, all-missing pad]` |
| `R_domain_local` | `[source-only, target-only]`, complementary missingness |

`R_domain_offset`, `R_target_local_only`, `S_unpadded`, `W_unpadded` are
excluded: the expanded panel established that both alternative references
give a larger utility and both fail the coherence check, so carrying them
would create three reference ladders and an opportunity to select one.
`S_unpadded`/`W_unpadded` were proved bit-identical to their padded forms.

**Diagnostic ladder, non-verdict-bearing, class A only.**  Both reviews
independently identified the same threat: at `K=64` each support row carries
weight `n_source/K` = **348 (glucose) to 939 (waist_cm)** against
`min_child_weight = 1`, so a *single* target row can found a leaf.  The
exposure is asymmetric — `R_domain_local`'s target-local column is observed
only on target rows, so target-pure leaves are constructible there, whereas
`S_shared_bridge`'s shared column places those same values among thousands
of weight-1 source rows that regularise the leaf.  A decay produced by
single-row leaf memorisation in the reference would look exactly like the
predicted decay.

The diagnostic re-runs the three arms across the same ladder with
`min_child_weight = 8 * n_source / K`, which forces at least eight distinct
target rows behind any target-only leaf at every rung and is otherwise
identical.  It changes **one** thing.  If the primary decay survives it, the
memorisation explanation is excluded; if the decay collapses under it, the
primary result is reported as learner-mechanical rather than semantic.
`subsample=1.0` is the **named second follow-up** and is not run here.

## Estimands

Per cell `(endpoint, seed, K)`, gains are reductions in query-SD-normalized
RMSE, positive favouring the left arm:

- `utility_S_minus_R` = `nrmse(R_domain_local) - nrmse(S_shared_bridge)`
- `content_S_minus_W` = `nrmse(W_deranged_bridge) - nrmse(S_shared_bridge)`
- `reference_minus_wrong_R_minus_W` = `nrmse(W_deranged_bridge) - nrmse(R_domain_local)`

Identity `utility = content - (reference_minus_wrong)` holds cell by cell,
so the **decomposition is mandatory**: a utility decay driven entirely by
movement of the reference is a different finding from one driven by the
supplied arm, and both must be visible.  **Absolute per-arm nRMSE
trajectories in `K` are reported for all three arms**, not only contrasts.

**Level contrasts:** all three, at each `K`.

**Decay contrasts,** paired within `(endpoint, seed)`:

- `decay_utility_64_minus_1024` — **PRIMARY.**  Chosen because it is the
  statistic the controlled benchmark itself reports (`K=512` minus `K=32`),
  so the two are comparable.
- `decay_utility_64_minus_256`, `decay_utility_256_minus_1024` — steps.
- `decay_content_64_minus_1024`, `decay_reference_minus_wrong_64_minus_1024`
  — the decomposition.  **No prediction is made for either.**
- `curvature_utility` = `u(64) - 2 u(256) + u(1024)` — the **only**
  independent contrast the middle rung contributes.  Descriptive shape
  statistic, no prediction.

  One review proposed a within-cell OLS slope on `log2 K` as a
  better-powered supporting statistic "because it uses the middle rung."
  The algebra was checked and that is false here: on an equally spaced
  three-point grid (`log2 K = 6, 8, 10`) the OLS slope weights are
  `(-1/4, 0, +1/4)`, so the middle rung has weight exactly zero and the
  slope equals `-(decay)/4` identically.  It carries no information beyond
  the primary and is therefore **not** reported as an independent statistic.
- `retention = m(1024) / m(64)` — the statistic comparable to the controlled
  law's own retention (`~.07--.14`).  Reported with a bootstrap interval.
  Retention is what separates "the law operates here" from "the level is
  merely positive at both rungs."

**Pairing does not cancel endpoint variance.**  The first draft claimed it
did; that claim was measured and is false.  On the existing ladder, the
seed-level residual correlation across `K=64` and `K=1024` is
`-.15 to +.13` (`~0`), so `Var(decay) = Var@64 + Var@1024`, and endpoint
effects are multiplicative rather than additive, so the coefficient of
variation is preserved (`1.96 -> 1.66`, `.85 -> .91`).  **The decay
statistic is approximately as well powered as the level statistic, not
better.**

## Power, frozen before execution

Class-A variance components at `K=256` (6 endpoints x 10 seeds): grand mean
`+.04735`, between-endpoint `tau = .0441`, within-endpoint `sigma = .0376`,
`ICC = .58`, `SE = .0186`, `t = 2.54` against `t_5 = 2.571`.  **58% of the
variance is between-endpoint**, so more seeds barely help (10 -> 20 seeds
shrinks `SE` by ~6%); only more endpoints would, and adding endpoints is
exactly what collapsed the level.

Simulated minimum detectable effect at 80% power on the primary decay, using
the observed endpoint profile and the gate as implemented:

> **MDE80 = +.066 to +.093 nRMSE units.**

Against the calibrated prediction (`mu in [+.049,+.096]`, central `+.071`):

> **power is roughly .50 at the pessimistic end and .85 at the central
> prediction.  An INCONCLUSIVE outcome is a likely result of this design,
> not a failure of execution, and is pre-declared as such.**

**SESOI.** A decay below `+.020` is declared here to be scientifically
uninteresting: against a level of `+.0473` it corresponds to retention
above `~.6`, whereas the controlled law's own retention is `~.07--.14`.

## Inference

The frozen procedure, by import rather than re-implementation
(`scripts/summarize_crta_v3_exam_no_bridge_reference_v1.py`): 10,000
hierarchical bootstrap draws over endpoints then paired seeds, seed
`20260828`.  Each named contrast draws from its own generator
`default_rng(20260828 + i)` at a fixed enumeration index `i` rather than
from one shared stream.  Recorded so it is not later read as a discrepancy:
the re-run `K=256` utility reproduces the published **point estimate**
exactly, but its interval differs in the fourth decimal because it is drawn
at a different index of a different stream.  `[+.0171,+.0844]` remains the
reported interval for that estimand.

**The six-cluster percentile bootstrap does not decide alone.**  The
strongest verdict word additionally requires the endpoint-level Student-$t$
interval to exclude zero.  The published `K=256` level passes the bootstrap
gate while its Student-$t$ crosses zero by `.0006`; binding a verdict to the
favourable interval alone while merely displaying the others would be
engineered.  Student-$t$, BCa, and studentized intervals are all reported.

**Stated limitation, not fixed here:** the six endpoints share subjects,
features, and splits, so they are not six i.i.d. clusters, and ten seeds do
not create sixty independent scientific units.  The frozen inference treats
them as clusters; that convention is retained for comparability with the
published number, and its weakness is inherited, not repaired.

## Verdict rule, declared now

Interval logic, not point-estimate ordering.  Let `D` be
`decay_utility_64_minus_1024` on class A.

- **SUPPORTED (within the selected panel).**  `D`'s bootstrap CI95 lower
  bound `> 0`, **and** its endpoint Student-$t$ lower bound `> 0`, **and**
  `mean(D) >= SESOI = .020`.
- **CONTRADICTED.**  `D`'s CI95 upper bound `< 0`, **or** the whole CI95
  lies inside `(-.020, +.020)` — an equivalence result ruling out a
  meaningful positive decay.
- **INCONCLUSIVE.**  Everything else.  A small non-monotone reversal is
  uncertainty, not falsification, and lands here.

Monotonicity of `m(64) >= m(256) >= m(1024)` is reported as a **diagnostic**
and is no longer a verdict conjunct: under a true null a monotone ordering
arises by chance about one time in six, so it is too weak to carry a claim.

**Reference coherence is reported, not gating.**  The first draft withheld
the verdict if `reference_minus_wrong` failed at a rung.  Because
`reference_minus_wrong = content - utility` algebraically, gating on it
conditions the primary on an outcome that shares its terms.  `R_domain_local`
is frozen by construction; its coherence at each rung is reported as a
descriptive property of the operating region.

**The word "vanishes" is dropped from the prediction.**  Failure to reject
`m(1024) = 0` would not establish vanishing.  Shrinkage is what is
predicted; the retention ratio is what is reported.

**Symmetry of scope.**  A CONTRADICTED or INCONCLUSIVE outcome is equally a
scope limit on *this real-data regime* — pinned target mass, six
outcome-selected endpoints, XGBoost, a complementary-missingness reference —
as on the controlled law.  Both readings are pre-declared; the
`min_child_weight` diagnostic is the pre-declared adjudicator between
"semantic" and "learner-mechanical" readings of a SUPPORTED outcome.

Post-hoc selection of a `K` pair, of an endpoint subset, or of a weighting
regime is inadmissible.  **`hba1c` must not be added in response to this
result**; the expanded-panel report already records why that move is
forbidden, and this protocol restates it so it cannot be forgotten.

## Integrity checks

1. **`K=256` reproduces the published cells exactly.**  All three frozen
   arms x thirteen endpoints x ten seeds = **exactly 390 comparisons
   required**; a missing baseline file is a failure, not a skip; comparison
   is float equality, not a tolerance.  The recorded library versions must
   also match those in the v2 cells.  If versions differ, the check degrades
   to `|delta| < 1e-12`, and that degradation is reported in the summary
   rather than hidden.  A failure withholds all verdicts.
2. **Pool floor.**  Every cell asserts `n_pool >= 4 * max(K) = 4,096`.
3. **No duplicated member values** per arm per rung, as frozen.

## Secondary, declared here so it cannot be presented later as a finding

The expanded panel already explains the thirteen-endpoint collapse
structurally: classes B and C are not cardiometabolic and every bridged
member slot is.  This run adds a support-side reading of the same collapse,
**descriptive only**: per-class decay, per-endpoint decay, and the
within-class-A association between an endpoint's `K=256` utility and its
decay.  No class-by-support interaction test is preregistered and none may
be reported as one.  Note in advance that under a multiplicative endpoint
model `decay_e ~ theta_e (f(64) - f(1024))`, so a correlation between level
and decay is expected by construction and is not evidence of a mechanism.

## What this does not address

- **Resolution.**  Six endpoint clusters.  No outcome here narrows the
  frozen `[-.0006,+.0952]` Student-$t$ interval on the `K=256` level.
- **Concentration.**  Glucose carries a third of the pooled `K=256` effect;
  the drop-best-endpoint statistic is part of the gate.
- **The mass channel** and **`subsample`**, both named follow-ups above.
- **Nesting.**  A nested `A64 ⊂ A256 ⊂ A1024` scheme preserving the frozen
  `K=256` draw is constructible, but measured `rho(64,1024) ~ 0` implies it
  would reduce the decay `SE` by only about 2--5%, and it would break
  comparability with the existing ladder used above for calibration.  Named
  as a follow-up; not run.

## Changes forced by adversarial review, listed

1. Disclosure of the existing `crta_v3_m1m2_layer_ladder_v1` `K` sweep;
   directional prediction replaced by a calibrated numeric interval.
2. The "pinned weighting can only mute" claim withdrawn as unjustified.
3. Headline claim narrowed: no outcome licenses "the controlled law extends
   to real data."
4. The false pairing-cancels-endpoint-variance claim removed and replaced by
   the measured variance structure.
5. Power, MDE, and SESOI frozen; INCONCLUSIVE pre-declared as likely.
6. Verdict rule changed from point-estimate ordering to interval logic with
   an equivalence branch; monotonicity demoted to diagnostic.
7. Endpoint Student-$t$ made binding alongside the bootstrap gate.
8. Coherence guard demoted from gating to descriptive.
9. `min_child_weight` diagnostic ladder added.
10. Per-arm absolute trajectories and the `U = C - (R-W)` decomposition made
    mandatory.
11. Integrity check tightened to exactly 390 exact comparisons plus a
    version assertion.
12. Thirteen-endpoint secondary pre-declared as projected to fail.

## Execution

Runner `scripts/run_crta_v3_exam_support_ladder_v1.py`, summarizer
`scripts/summarize_crta_v3_exam_support_ladder_v1.py`, figure
`scripts/plot_crta_v3_exam_support_ladder_v1.py`.  Committed with this
document before launch.  Executed on `anonymous` under conda env
`coret_pin`, CPU only with all CUDA hidden, user-authorized budget of
13 shards x 2 threads = 26 of 96 cores.  `threads=2` per process is fixed by
integrity check 1.  Public-use NHANES/KNHANES panels; aggregate metrics only.
