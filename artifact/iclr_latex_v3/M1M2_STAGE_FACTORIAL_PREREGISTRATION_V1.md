# Pre-registration: M1/M2 measurement-stage factorial, v1

Declared 2026-08-19 ~23:50, **before any cell has been executed.** The
centerpiece test of the measurement-stage thesis
(`MEASUREMENT_STAGE_PROGRAM_DIRECTION_V1.md`): the claim is an
**interaction** — structure (concept binding, numeric relations) performs
on the measurement-aligned stage and cannot off it — not a sum of layers.

## 1. Task and surface

Survey-endpoint transfer (the one surface where the stage is live on both
labels and features): benchmark `std_cross_nh2kn_shared_anchorreset_fewshot_v1`,
injected targets `diabetes_history`, `hypertension_history`,
`current_smoking_status` (raw codes; the builder drops the endpoint's own
slot). Seeds 50–59, K ∈ {64, 256, 1024}, **primary K = 256**. Backbone
XGBRegressor hist d6 n300 on mapped label values; **metric AUROC against
the fixed codebook-documented target-side binary (higher is better)**,
eval identical across arms, as in the label panel.

Feature blocks:

- **base slots** (11): age, creatinine, rbc, wbc, hemoglobin, hematocrit +
  the survey slots (sex, education_level + the two non-target survey
  slots).
- **L1 member columns** (9): the gpt-5.6-sol nh2kn bank's bound slots
  (height, weight, waist, sbp, dbp, glucose, hba1c, chol, tg) — clinical,
  untouched by measurement tables, so the interaction reads cleanly as
  *supervision × information*.
- **L2 numeric relations** (12): within-concept ordered pairs (6 pairs:
  body 3, bp 1, diabetes-labs 1, lipids 1) × {difference, safe ratio},
  compiled deterministically — no LLM proposal (17/17 banks
  relation-empty).

## 2. Stage (L0) operationalization

- **L0 on** = the operative pipeline table: builder-level feature
  harmonization (default rule index) + pipeline label maps (DIQ010
  {1→1,2→0}; de1/di1 {1→1,0→0}; BPQ020 {1→1,2→0}; SMQ040 {1,2→1,3→0};
  bs3_1 {1,2→1,3,4→0}; else NaN → row dropped).
- **L0 off** = harmonization-ablated build (empty rule index) + identity
  labels — the raw-coding reality, polarity inversions live.
- The stage uses the **correct** table deliberately: extraction *quality*
  was already measured (label panel A1/A3); the factorial tests the
  *stage*. An llm-table stage variant is deferred to the extraction-v2
  rerun.

## 3. Arms (9 fits per cell × K)

| arm | L0 | features |
|---|---|---|
| `a00_base` | off | base |
| `a10_stage` | on | base |
| `a01_columns` | off | base + members |
| `a11_stage_columns` | on | base + members |
| `a11r_stage_columns_relations` | on | base + members + relations |
| `pl_stage_at_columns` | **wrong table** (capacity-matched permutation of the pipeline table, features and labels coherently wrong; per target × seed) | base + members |
| `pl_columns_at_stage` | on | base + members with target-side values derangement-permuted |
| `pl_relations_at_stage` | on | base + members + 12 random-pair relations (same op mix, pairs drawn from all non-endpoint slots; per target × seed) |
| `is_target` | on | base + one 0/1 target indicator |

## 4. Adjudication (frozen)

AUROC gain = arm − reference (positive = arm better). Hierarchical
bootstrap (targets then seeds, 10,000 reps, seed 20260819), K = 256, 30
pairs. Separation = mean > 0 ∧ CI₉₅ excludes 0 ∧ win ≥ 0.60 ∧ mean > 0
with best target dropped.

| # | contrast | reads |
|---|---|---|
| **I1 (primary)** | [a11 − a10] − [a01 − a00], CI must exclude 0 above | the stage thesis: columns are worth more on the stage than off it |
| I1-sens | same, computed on inversion-corrected AUROC max(A, 1−A) for every arm | guards the known artifact: off-stage labels are polarity-inverted, so off-stage column gains can be *negative* in raw AUROC; if I1 holds only without correction, the inversion artifact is doing the work and the claim must say so |
| S1 | a11 vs `pl_stage_at_columns` | stage content (right table vs wrong, actors present) |
| S2 | a11 vs `pl_columns_at_stage` | binding content on the stage |
| S3 | a11r vs `pl_relations_at_stage` | relation content on the stage — the axis that previously died against random pairs; it must win here or L2 stays dead |
| D | a11 vs `is_target` | cheapest-explanation control |
| desc | a11r − a11; a10 − a00; per-target everything | no verdict words |

Interpretation map, declared now: I1 ∧ I1-sens ∧ S1 ∧ S2 → the stage
thesis stands with binding as the actor. S3 additionally → numeric
relations join it. I1 without I1-sens → the "stage" reduces to label
polarity repair; report as that. S2 fails → the ladder's R1 does not
survive on this surface and the binding claim is surface-limited.

## 5. Execution

Runner `scripts/run_crta_v3_m1m2_stage_factorial_v1.py`, summarizer
`scripts/summarize_crta_v3_m1m2_stage_factorial_v1.py`, committed with
this document before launch. 30 cells × (3 builds + 27 fits); 3 shards ×
2 threads, launched immediately (standing instruction: local CPU now,
ksup untouched). NHANES/KNHANES only; no GPU.
