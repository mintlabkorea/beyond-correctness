# Expanded-panel examination reference sensitivity — internal report

Status: complete, 130/130 cells (13 endpoints × seeds 50–59, K=256).
Protocol frozen before execution: `PROTOCOL_V1.md` (commit `4a45e19...`,
see git log).  `anonymous`, env `coret_pin`, CPU only, 6 shards × 2 threads.
Not in the manuscript.

## Integrity

The six class-A endpoints reproduce v1 **bit-identically across all six
shared arms: 360/360, worst |Δ| = 0.0**.  Switching the target-set override
did not perturb any frozen cell.

## Headline: the expansion did not rescue the interval, it bounded the claim

| panel | utility vs `R_domain_local` | gate |
|---|---|---|
| original six (class A) | `+.0473 [+.0170,+.0843]`, win .90 | pass |
| **all 13 endpoints** | **`+.0137 [-.0132,+.0424]`, win .61** | **fails** |

Endpoint Student-$t$ on 13 endpoints is `[-.0173,+.0446]`.  Adding seven
endpoints did not narrow the interval around a stable effect; it moved the
point estimate to roughly a quarter of its former size.

## Why: the effect is confined to the cardiometabolic anchor family

| class | endpoints | utility | content |
|---|---|---:|---:|
| A — cardiometabolic anchor | glucose, waist_cm, triglycerides, sbp, dbp, total_cholesterol | `+.0473` | `+.0696` |
| B — alt, bun | 2 | `-.0139` | `+.0773` |
| C — base-slot targets | creatinine, hemoglobin, hematocrit, rbc, wbc | `-.0156` | `+.0336` |

Per endpoint the ordering is glucose `+.1277`, triglycerides `+.0676`,
waist_cm `+.0455`, wbc `+.0277`, sbp `+.0233`, total_cholesterol `+.0194`,
bun `+.0124`, dbp `+.0006`, hemoglobin `-.0037`, hematocrit `-.0068`,
rbc `-.0097`, alt `-.0403`, creatinine `-.0858`.

This is mechanistically coherent rather than noise.  Every bridged member
slot is a cardiometabolic examination measure (height, weight, waist, sbp,
dbp, glucose, hba1c, total cholesterol, triglycerides).  For a
cardiometabolic target those members carry most of the signal, so asserting
their cross-domain identity correctly matters.  For a renal, hepatic, or
haematology target the same members are weakly relevant, and asserting a
bridge over them buys nothing and can cost.  The per-class means are
descriptive; no formal class-by-utility interaction test was preregistered
or run.

## The thesis result: content generalizes, utility does not

| contrast, 13 endpoints | mean | 95% CI | gate |
|---|---:|---|---|
| content `S − W` | `+.0569` | `[+.0248,+.0928]` | **pass** |
| utility `S − R_domain_local` | `+.0137` | `[-.0132,+.0424]` | fails |

On the same 130 cells, supplying wrong content clearly hurts while supplying
correct content does not beat a coherent reference.  That is precisely the
separation the manuscript argues for, now shown on 13 real endpoints rather
than six.  It is a stronger demonstration of the paper's claim than the
`+.047` was, and it costs the `+.047` its generality.

## The coherence bar did the work it was declared for

| reference | mean nRMSE | coherence vs wrong | utility (13 endpoints) |
|---|---:|---|---|
| `R_domain_local` | **.7174** | `+.0432 [+.0090,+.0889]` pass | `+.0137` unresolved |
| `R_domain_offset` | .7384 | `+.0222 [-.0033,+.0578]` fail | `+.0348 [+.0100,+.0680]` |
| `R_target_local_only` | .7419 | `+.0187 [-.0071,+.0502]` fail | `+.0382 [+.0129,+.0706]` |

Both alternative references produce a utility that **passes** the gate on 13
endpoints.  Both are inadmissible, because neither beats matched-wrong.
Without the coherence bar fixed in advance, this run could have been
reported as `+.0382 [+.0129,+.0706]` by choosing the reference afterwards.
It must not be.

Problem 1 from the v1 report is therefore answered: across three
constructions, `R_domain_local` has the lowest mean nRMSE **and** is the only
coherent one.  It is the strongest reference tested and stays primary.

## Where expansion can and cannot go next

Out-of-scope expansion pushes the estimate toward zero, so more haematology
or renal endpoints will not help.  In-scope expansion has exactly two
candidates and both are blocked:

- `hba1c` — in the cardiometabolic anchor set, excluded by the documented
  KNHANES source-mapping/scale deferral.  Resolving that is a real,
  outcome-blind data task.
- `pulse_rate` — target pool is 285 rows against 5,988–8,078 elsewhere, so it
  fails the frozen `4K = 1,024` floor regardless of the mapping issue.

**Stated so it cannot be forgotten:** `hba1c` would take the in-scope panel
to seven endpoints, which is the count this project already calculated would
move the Student-$t$ off zero.  Pursuing it *for that reason* is not
admissible.  It is admissible only as an endpoint that the anchor rule
already includes and that was excluded for a recorded data reason, run once
and reported whatever it shows.  Seven clusters is still a weak panel.

## What this means for the manuscript

The examination utility should not be presented as a general real-data
positive.  It is a six-endpoint, purposively selected, cardiometabolic-only
effect that does not survive an endpoint-family expansion drawn from the
project's own broader validation set.  Any wording must carry that scope.

Artifacts: `SUMMARY_V1.json`, `EXPANDED_PANEL_V1.png`, 130 per-cell
`metrics.json`, logs in `logs/crta_v3_exam_reference_sensitivity_v2/`.
