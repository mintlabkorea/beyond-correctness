# Examination reference sensitivity, expanded panel — frozen design

Frozen before execution: 2026-08-28 (Asia/Seoul).  Supersedes nothing: v1
(`experiments/crta_v3_exam_reference_sensitivity_v1`) stays intact, and the
original six-endpoint estimand of
`iclr_latex_v3/EXAM_NO_BRIDGE_REFERENCE_FREEZE_V1.md` remains primary.

## Why this exists, stated honestly

v1 answered one of three problems with the reported examination utility
`+.0473 [+.0171,+.0844]`:

1. **Reference construction.**  v1 showed the result is not an artifact of
   the reference's induced missingness (R2) or of the padding decision (R3,
   bit-identical).  But R2 turned out to be a *weaker* reference --- it loses
   to `R_domain_local` in 90% of cells and is indistinguishable from
   matched-wrong --- so it bounds nothing.  **Unresolved: is
   `R_domain_local` the strongest coherent no-bridge reference?**
2. **Cluster count.**  Endpoint-level SD is `.0456` over `n=6`, so the
   Student-$t$ half-width is `.0479` against a mean of `.0473`; the interval
   crosses zero by `.0006`.  Additional seeds cannot help, because the
   bootstrap hierarchy clusters on endpoints.
3. **Concentration.**  Glucose alone is `+.1277` while dbp is `+.0006`;
   drop-best-endpoint is `+.0313`, so a third of the pooled effect is one
   endpoint.

**Disclosure of analysis order.**  The arithmetic in (2) --- that seven
endpoints with the same dispersion would move the Student-$t$ off zero ---
was computed **before** this expansion was designed.  Expanding an endpoint
panel after such a calculation is exactly the pattern this project forbids
when done sequentially.  Two protections are therefore fixed here and are
not negotiable after results are seen: the panel is defined by a rule rather
than chosen, and the **entire** eligible panel is executed once.  There is
no second expansion round.  If the expanded panel fails, that is the
reported result.

## Endpoint panel (rule, not a choice)

Include every target `T` in the pre-existing benchmark target set
`objective_broader_validation_targets_v2` such that

- (a) `build_single_target_table` succeeds for `T`, and
- (b) the target-domain pool has at least `4K = 1,024` rows, `K=256` being
  the frozen support size.  The threshold is derived from the design, not
  from the observed pools.

The rule was applied by an outcome-blind probe that built each table and
recorded sample sizes only; **no model was fit and no performance number
was computed** before this document was frozen.  Result:

| class | targets | base slots | member slots | pool range |
|---|---|---|---|---|
| A: target is a member slot | glucose, waist_cm, triglycerides, sbp, dbp, total_cholesterol | 11 | 8 | 6,776--8,078 |
| B: target is neither | alt, bun | 11 | 9 | 6,791--6,797 |
| C: target is a base slot | creatinine, hemoglobin, hematocrit, rbc, wbc | 10 | 9 | 5,988--6,799 |
| excluded | pulse_rate | --- | --- | **285** (fails (b)) |

**13 endpoints x seeds 50--59 = 130 cells.**  Class A is exactly the frozen
six.  Classes B and C are structurally different --- the bridge spans nine
members instead of eight, and class C drops the target from the shared base
block --- and per-class means are reported so that heterogeneity is visible
rather than pooled away.  Class C requires one guard in the runner (skip the
target when building the shared base block); nothing else in the frozen
construction changes.

Switching the target-set override from `objective_anchor_targets_v1_safe` to
`objective_broader_validation_targets_v2` does not alter the per-target
tables: the outcome-blind probe reproduced the frozen `n_source`, `n_pool`,
and `n_query` exactly for the class-A endpoints.  The runner re-checks this
by requiring the class-A arms to reproduce v1 bit-identically.

## Arms (seven per cell)

Cells, splits, seeds, support, learner, and weights are those of the frozen
experiment.  Arms 1--4 and 6--7 are v1's, unchanged.

| arm | member encoding | role |
|---|---|---|
| `S_shared_bridge` | `[shared correct, pad]` | supplied |
| `W_deranged_bridge` | `[shared deranged, pad]` | matched-wrong |
| `R_domain_local` | `[source-only, target-only]` | frozen primary reference |
| `R_domain_offset` | `[disjoint-range single column, pad]` | R2, known weaker; kept for continuity |
| `R_target_local_only` | `[target-only, pad]`; source rows missing | **R4, candidate stronger reference** |
| `S_unpadded` / `W_unpadded` | one column | R3 padding replication |

`R_target_local_only` exists because `R_domain_local`'s source-local columns
are entirely missing at query time, so any split learned on them is capacity
spent on a column that cannot fire for a query row.  Dropping them leaves
the same information available at query time in a leaner frame.  It may
therefore be **stronger** than `R_domain_local`; that is the point of adding
it, and either outcome is informative.

## Reference selection and adjudication (frozen)

Gains are reductions in query-SD-normalized RMSE; inference is v1's
hierarchical bootstrap over endpoints then paired seeds, with the existing
descriptive gate (positive mean, CI95 lower bound above zero, win >= .60,
positive drop-best-endpoint mean).

- **Coherence bar.**  A candidate reference is admissible only if
  `reference - W_deranged_bridge` passes the gate.  A frame that performs no
  better than deranged content is not a reference.  `R_domain_offset` failed
  this bar in v1 and is expected to fail it again; it is reported, never
  selected.
- **Strongest-reference rule.**  Among admissible references, the primary
  robustness comparison uses the one with the **lowest pooled mean nRMSE**.
  The choice is made **once, globally**, never per cell and never per
  endpoint, and it is made on reference performance alone, which does not
  involve the supplied arm.
- **Primary claim.**  "The utility survives the strongest coherent no-bridge
  reference we could construct" is permitted only if
  `S_shared_bridge - (selected reference)` passes the gate on the full
  13-endpoint panel.
- Reported unconditionally, whatever the outcome: utility against **every**
  reference; the class-A-only (original six) restriction of every contrast;
  per-class and per-endpoint means; the coherence bar for every reference;
  the concentration diagnostic (pooled versus drop-best-endpoint).

## What is still not addressed

Concentration (problem 3) is *mitigated* by more endpoints, not solved.  If
the expanded panel remains dominated by one or two endpoints, that must be
stated, and no wording may imply otherwise.  `hba1c` remains excluded by its
documented KNHANES source-mapping/scale deferral; resolving that is a
separate data task and is not attempted here.

## Integrity checks

- The six class-A endpoints must reproduce v1's `S_shared_bridge`,
  `W_deranged_bridge`, `R_domain_local`, `R_domain_offset`, `S_unpadded`,
  and `W_unpadded` values **bit-identically**.  Any deviation is reported
  with its diagnosis, not absorbed.
- The offset construction re-asserts source/target range disjointness on fit
  and query and aborts on violation.

## Execution

Runner `scripts/run_crta_v3_exam_reference_sensitivity_v2.py`, summarizer
`scripts/summarize_crta_v3_exam_reference_sensitivity_v2.py`.  Committed with
this document before launch.  `anonymous`, conda env `coret_pin`, CPU only
with CUDA hidden, 6 shards x 2 threads within the authorized budget.
Public-use NHANES/KNHANES panels; aggregate metrics only.
