# Source-budget ladder protocol v1

Status: specified, not yet executed
Specified: 2026-08-17
Governs: M1, M2, M3, M4, M5, M6
Related: [`M3_NHKN2HRS_AUTO_C_PROTOCOL_V1.md`](M3_NHKN2HRS_AUTO_C_PROTOCOL_V1.md),
[`PAPER_BLUEPRINT.md`](PAPER_BLUEPRINT.md) §7

## Honest status of this protocol

**This is a disclosed post-hoc sensitivity analysis, not a confirmatory result.**
The 4,096-row rung has already been executed and read on all four medical tasks. A ladder specified
now is outcome-blind with respect to the *new* rungs only. It is not outcome-blind with respect to
the rung that motivated it.

Two commitments make it admissible anyway, and both are binding:

1. **Every rung is reported**, including rungs that stay null and rungs that are adverse. The
   sensitivity table is published whole or not at all.
2. **The primary rung is chosen here, before execution, by a rule that does not mention any gain.**
   That rule is in §4. Selecting the primary rung after seeing which one looks best is the
   favourable-cell selection that `long_term.md` forbids for the v4, v5, v6, and v7 lines, and it is
   equally forbidden here.

## 1. What prompted it

M1/M2 show interval-separated positive Auto-C utility. M3--M6 do not: M3 crosses zero, M4 is
separated positive on regression only, M5 is not evaluable, and M6 is separated **adverse** on two
strata. The obvious question is whether the medical nulls are a property of the medical transfer
problem or an artifact of how M3--M6 were configured.

One earlier candidate explanation --- that M1/M2 carried relations and M3--M6 did not --- was
**retracted on 2026-08-17**. `compile_bank` exposes relation coordinates only under
`arm in {"relation","full"}`; both regimes run `arm="concept"`, verified at
`compile_bank.py:407-418` and `run_crta_v3_medical_small_screen.py:343`. Relation coordinates are
constant zero in both. That explanation is dead and must not be revived.

Two differences survive.

### 1.1 Source budget, a protocol knob

| | M1/M2 | M3--M6 |
|---|---|---|
| source rows fitted | 22,302--60,124, uncapped, endpoint-observed | 4,096 (`SOURCE_CAP`) |
| target weight | 10.0 | 10.0 |
| estimator | XGB 300/5/0.05/5.0/0.8/0.8/1.0 | **identical** |

This was pre-declared. `M3_NHKN2HRS_AUTO_C_PROTOCOL_V1.md:34` states the cap "is part of M3 and is
not interpreted as the full-source M1/M2 regime." Its stated basis is that it matches "the already
materialized HRS bridge infrastructure" --- an engineering convenience, not a scientific rationale.
**Its effect has never been measured.**

Measured consequence. With `TARGET_WEIGHT = 10.0`, the source's share of effective training weight
is `n_source / (n_source + 10 * n_target_support)`:

| Support | M1 (dbp, 47,957 source) | M4 (grip_strength_max, 4,096 source) |
|---|---:|---:|
| 1 % | 87.1 % (vs 707 support rows) | 46.5 % (vs 471 support rows) |
| 5 % | 57.6 % (vs 3,537) | 13.9 % (vs 2,545) |
| 10 % | 40.4 % (vs 7,073) | 7.4 % (vs 5,139) |

In M3--M6 the source is a **minority of the training signal at every support and nearly absent at 10
percent.** If Auto-C's benefit is carried by making source rows usable for target prediction, M3--M6
is configured so that it cannot express that benefit. This is a plausible mechanism. **It is not a
demonstrated one, and this protocol exists to test it, not to assume it.**

### 1.2 Bank size, an outcome of the proposer

| Task | Accepted concept slots occupied |
|---|---|
| M1, M2 | 4 (Codex and Qwen3-32B alike) |
| M3 | 2 (Codex), 1 (Qwen3-32B) |
| M4 | 2 (Llama4 Scout) |
| M6 | 1 (Gemma3-27B), 1 (Qwen3-32B) |

Read from the executed cells' `interface_feature_names`. M3--M6 fill 1--2 of 24 concept slots
against M1/M2's 4, so 4--8 of 192 interface columns are nonzero rather than 16.

**This is not a knob and this protocol does not touch it.** Bank size is what the proposer produced
under a frozen contract; forcing it upward would mean re-running proposers until the medical banks
grew, which is proposer selection on downstream outcome. It is recorded here so that a null at the
top rung is not misattributed to the source budget alone.

## 2. The ladder

Three rungs, applied to all six medical tasks:

| Rung | `SOURCE_CAP` | Status |
|---|---|---|
| **L0** | 4,096 | M3--M6 already executed; **M1/M2 must be run down to it** |
| **L1** | 16,384 | new |
| **L2** | uncapped, all endpoint-observed source rows | M1/M2 already executed; **M3--M6 must be run up to it** |

L0 and L2 each already exist on one half of the matrix. Running the missing half of each makes the
matrix square, which is the point: at present no rung is observed on all six tasks, so no
cross-task statement about the source budget is supportable at all.

L1 exists to distinguish a threshold from a dose-response. A gain that appears only at L2 is a
different finding from a gain that rises monotonically across L0 -> L1 -> L2, and two rungs cannot
tell them apart.

The rungs are **nested**: the row subset kept at L0 is a subset of L1's, which is a subset of L2's.
Selection is a keyed order over row position, truncated at the cap, so a smaller rung can only remove
rows. This removes sampling noise from the rung comparison --- a difference between rungs is a
difference in budget, not in which rows happened to be drawn. Verified by test.

### 2.1 Cap semantics change, declared

`select_source_cap` currently raises when `len(eligible) < cap`. Under this protocol it becomes
`min(cap, len(eligible))`, and the realized count is recorded per cell as `source_rows_fitted`.

Rationale: L2 has no fixed integer, and at L1 some endpoints may have fewer than 16,384 observed
source rows. The alternative --- dropping any endpoint that cannot fill the cap --- would make the
endpoint panel depend on the source budget, so a rung comparison would silently compare different
endpoint sets.

This does not affect L0. Every M3--M6 endpoint had at least 4,096 observed source rows, which is why
the existing runs completed. The realized counts at L1 and L2 are reported.

### 2.2 Everything else is frozen

Unchanged across all rungs: estimator spec, `TARGET_WEIGHT = 10.0`, support fractions, seeds,
endpoint panels, leakage blocks, split keys, bank contents, compiler arm, bootstrap protocol
(50,000 draws, seed 20260814), and the missingness and AUROC-feasibility gates. The source budget is
the **only** thing that moves.

Consequences that must be honoured:

- The M5 missingness exclusion still fires at every rung. `qwen3_8b/c_003` binds ELSA
  nurse-visit-only columns at missing fraction 0.696 against the frozen 0.5, which is a target-side
  property and cannot be changed by the source budget. **M5 is expected to remain not evaluable at
  every rung.** If a larger source budget were used as a reason to relax that threshold, the
  exclusion would become outcome-influenced.
- M6 `hrs__depression` stays out of the binary panel at every rung. Its infeasibility is a
  target-side single-class query draw, 30 of 30.

## 3. Cost

Measured from the executed runs: M4 480 cells in 14.4 min, M5 390 in 24.7 min, M6 390 in 22.7 min,
all six-way sharded --- roughly 1 hour for M3--M6 at L0. Training cost scales about linearly in
`n_source + n_target_support`, so L2 on HRS (45,234 rows) is roughly 6--10x L0 depending on support.

Order-of-magnitude estimate: **L1 and L2 across M3--M6 is single-digit hours**, and the M1/M2 L0 rung
is cheaper than the runs already done. This is affordable in one night on `anonymous` (96 cores).
The estimate is deliberately loose; it will be replaced by measurement after the first shard.

## 4. Primary rung, declared now

> **The primary rung is L2, uncapped.**

The reason contains no reference to any gain, measured or expected:

- It makes the six medical tasks one regime, which is what the blueprint's §7 "반드시 고정할 항목"
  requires of a primary comparison matrix and what the current matrix does not satisfy.
- It is the regime M1/M2 already ran, so choosing it changes four tasks rather than two.
- It is the only rung definable without an arbitrary integer.

L0 and L1 are reported as sensitivity. If L2 is null on M3--M6, **the null stands and is a stronger
result than today's**, because it will have ruled out the source-budget explanation rather than left
it open. That outcome is not a failure of this protocol; it is the protocol working.

## 5. Interaction with the frozen control package

Editing the four utility runtimes moves their SHA-256, which is pinned in every completed cell and in
`M3_M6_OUTCOME_BLIND_CONTROL_FREEZE_V1.json`'s `forbidden_derivation_inputs`. So this change forces:

1. Full recomputation of M3--M6 at each rung.
2. A further re-seal of the control freeze's `utility_runtime` pins.

Because recomputation is forced anyway, the deferred defect batch in `short_term.md` is folded into
the same edit rather than spending a separate re-run on each: the M5 runtime pairing digest, the
absent M5 launcher runtime pin, the M5 summarizer's self-comparing `require_file_hash`, the M6
synthetic suite, and the M6 control runtime's missing not-evaluable path.

**The controls are executed only at the primary rung L2**, after the ladder completes. They are RQ3
of the blueprint and M1/M2 already carry them
(`--arms base auto_concept matched_random_concept wrong_auto_binding_concept target_only`); M3--M6
have run only `base` and `auto_concept`, so the medical half currently supports no specificity claim
at all. Running them at a rung that is not primary would waste the 790 random banks and 1,620
target-only cells.

The control freeze's outcome-blind property is unaffected: the source budget is a training-set size,
not a bank-selection rule, and it cannot change which control banks are sampled.

## 5a. Disclosed smoke observation

One M1 cell was run at both rungs to verify the plumbing before committing compute. Its numbers were
read, so they are disclosed here rather than left in a terminal.

`nh2kn`, `dbp`, support 0.01, seed 15, Qwen3-32B bank, arms `base` and `auto_concept`:

| Rung | source rows | Base RMSE | Auto-C RMSE | gain |
|---|---:|---:|---:|---:|
| L2 uncapped | 47,957 | 8.419236 | 7.827629 | `+0.591607` |
| L0 cap 4,096 | 4,096 | 8.078666 | 7.817406 | `+0.261260` |

**This is one cell. It is not evidence and no claim rests on it.** It is recorded because the
direction is what the ladder was built to test and a reader is entitled to know it was seen.

Provenance: this protocol was committed as `509a18af` at 2026-08-17 17:15:53, and the smoke cell ran
afterwards. The primary rung was fixed before any rung comparison was observed.

**Superseded by §5b.** The smoke cell suggested that Base *improves* when source rows are removed,
which would have meant the uncapped source is mildly harmful and Auto-C partly rescues that harm.
The full 1,080-cell run does **not** support that reading: Base moves in opposite directions in
different units. The single-cell inference was wrong, which is why it was labelled as not evidence.

## 5b. L0 executed: M1/M2 at the M3--M6 source budget

1,080 cells, three units, `status: pass` on all three, 0 errors, 0 missing, 0 duplicate.
Arms `base` and `auto_concept`; seeds and everything else identical to the executed uncapped runs.

| Unit | Rung | nRMSE gain | 95% CI | Win |
|---|---|---:|---|---:|
| M1 NH->KN, Codex | L2 uncapped | `+0.008244` | `[+0.002477,+0.017721]` | 0.900 |
| M1 NH->KN, Codex | **L0 cap 4,096** | `+0.002676` | `[-0.000911,+0.008673]` | **0.528** |
| M1 NH->KN, Qwen3-32B | L2 uncapped | `+0.008133` | `[+0.002473,+0.017661]` | 0.911 |
| M1 NH->KN, Qwen3-32B | **L0 cap 4,096** | `+0.001923` | `[-0.000204,+0.005308]` | **0.578** |
| M2 KN->NH, Codex | L2 uncapped | `+0.005192` | `[+0.001183,+0.010685]` | 0.822 |
| M2 KN->NH, Codex | **L0 cap 4,096** | `+0.002327` | `[+0.000291,+0.005533]` | 0.656 |

**Two of the three interval-separated positive results stop separating at the M3--M6 source budget,
and the third loses half its gain.** Win rates fall from 0.900/0.911/0.822 to 0.528/0.578/0.656.
This is the "M1/M2 gains collapse at L0" row of §6, written before execution as "the single most
informative cell in the ladder."

Per-arm decomposition, mean nRMSE over the same 180 pairs:

| Unit | Base L2 | Base L0 | Auto-C L2 | Auto-C L0 |
|---|---:|---:|---:|---:|
| M2 KN->NH, Codex | 0.691287 | 0.695933 | 0.686095 | 0.693606 |
| M1 NH->KN, Qwen3-32B | 0.678069 | 0.676766 | 0.669936 | 0.674843 |

Base moves in **opposite directions** in the two units --- worse by 0.0046 in M2, better by 0.0013 in
M1 --- so "the source harms Base" is not supported. Auto-C degrades in **both**, by 0.0075 and
0.0049. The consistent effect is on Auto-C, not on Base.

That is the mechanism §1.1 proposed, in its specific form: the concept interface is the channel
through which source rows reach the target prediction, so starving the source damages the arm that
uses the channel and leaves the arm that does not roughly where it was.

### What this does and does not license

- It **removes the main alternative explanation** for the M3--M6 medical nulls. Those tasks ran at
  exactly the budget that erases the effect in M1/M2.
- It **does not predict** that M3--M6 will separate at L2. The medical targets differ in cohort,
  endpoint panel, and bank size (1--2 accepted concepts against M1/M2's 4, §1.2). A null at L2 stays
  entirely possible and would then be a much better supported null.
- It does not change the primary rung, which was fixed at L2 before any of this was observed.

## 5c. Medical rungs executed: M4 responds, M3 does not

Both tasks ran all three rungs under the identical protocol. They disagree, and the disagreement is
the result.

**M4 HRS -> KLoSA, Llama4 Scout, nRMSE.** Monotone in the source budget, separated at every rung:

| Rung | source rows | gain | 95% CI | win |
|---|---:|---:|---|---:|
| L0 | 4,096 | `+0.020524` | `[+0.003545,+0.051802]` | 0.707 |
| L1 | 16,384 | `+0.037304` | `[+0.006123,+0.092814]` | 0.700 |
| L2 | 26,536--45,234 | `+0.052828` | `[+0.009156,+0.126937]` | 0.693 |

Binary AUROC does **not** respond: `-0.001787`, `-0.002507`, `-0.003245`, crossing zero at every
rung with win 0.529 / 0.505 / 0.476. A twelvefold source increase moves the regression gain 2.6x and
leaves the binary contrast where it was.

**M3 NHANES+KNHANES -> HRS, nRMSE.** Flat:

| Rung | source rows | Codex GPT-5.6-Sol | Qwen3-32B |
|---|---:|---|---|
| L0 | 4,096 | `+0.018587` `[-0.010238,+0.057453]` w0.758 | `-0.000348` w0.500 |
| L1 | 16,384 | `+0.019049` `[-0.002658,+0.054285]` w0.715 | `-0.004824` w0.491 |
| L2 | 58,737--126,500 | `+0.016580` `[-0.010613,+0.052341]` w0.748 | `-0.004558` w0.524 |

Codex moves by 0.0025 across a **14x to 31x** increase in fitted source rows and crosses zero at
every rung. Qwen3-32B is flat and slightly negative throughout.

The M3 L2 rung is the sharpest single fact in the ladder: at 58,737--126,500 source rows it fits
**more source than M1/M2 ever did** (22,302--60,124), under the same estimator, the same target
weight, and the same supports --- and still does not separate.

### Reading

This is §6's third row, "gains are flat across rungs", for M3 and §6's first row, "dose-response",
for M4. Both were written before execution.

- The source budget is **not** a general explanation for the medical nulls. It explains M4 and
  explains nothing in M3.
- Whatever separates M4 from M3 is therefore a property of the task pair, the target cohort, or the
  bank --- not of how much source was fitted. M3's usable banks hold 2 and 1 concept slots against
  M4's 2, so bank size alone does not obviously separate them either.
- The paper's claim stays **task-dependent utility**, and the ladder now supports that claim with a
  mechanism test rather than an assertion: the same knob moves one medical task and not another.

## 6. What would falsify the mechanism

Stated before execution so it cannot be reinterpreted afterwards.

| Observation | Reading |
|---|---|
| M3--M6 gains rise monotonically L0 -> L1 -> L2 and separate from zero at L2 | Dose-response consistent with the source budget being the binding constraint |
| M3--M6 gains rise but still cross zero at L2 | Source budget contributes; something else also binds --- bank size is the next candidate |
| M3--M6 gains are flat across rungs | **Source budget is not the explanation.** The medical nulls are a property of the task. Report as such |
| M1/M2 gains collapse at L0 | Symmetric confirmation from the other direction, and the single most informative cell in the ladder |
| M6 remains interval-separated adverse at L2 | Adverse transfer is real and survives the fix; it belongs in the paper as a boundary |

The M1/M2 L0 rung is worth emphasising: it is the cheapest run in the whole ladder and the only one
that tests the mechanism by *removing* source rows from a task that currently works. If M1/M2 stays
positive at 4,096, the source-budget explanation is in serious trouble regardless of what M3--M6 do.
