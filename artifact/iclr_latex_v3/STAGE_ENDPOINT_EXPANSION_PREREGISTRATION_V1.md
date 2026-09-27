# Pre-registration: bidirectional real-data M x C endpoint expansion, v1

Declared 2026-08-20 before any expansion cell is fit. The existing three
survey endpoints produced a raw pooled M x C interaction, but its
inversion-corrected CI crossed zero. The weakness is endpoint heterogeneity
and label-polarity artifact, not seed count.

## Eligibility lock and endpoint panel

Candidates were selected without predictive outcomes. Inclusion requires:
(1) a single raw item on each side, (2) explicit diagnosis/current-status
semantic agreement in the stored questionnaire assets, (3) both parquet
columns present, (4) documented valid and sentinel codes, and (5) two valid
outcome classes on each side. Aggregated families and wording proxies are
excluded. The resulting ten frozen pairs are:

| endpoint | NHANES | KNHANES |
|---|---|---|
| diabetes | DIQ010 | ALL__de1_dg |
| hypertension | BPQ020 | ALL__di1_dg |
| current smoking | SMQ040 | ALL__bs3_1 |
| kidney disease | KIQ022 | ALL__dn1_dg |
| stroke | MCQ160F | ALL__di3_dg |
| arthritis | MCQ160A | ALL__dm1_dg |
| asthma | MCQ010 | ALL__dj4_dg |
| cancer | MCQ220 | ALL__dc1_dg |
| heart attack | MCQ160E | ALL__di5_dg |
| angina | MCQ160D | ALL__di6_dg |

## Frozen design

Reuse the M1/M2 stage factorial's four interaction arms exactly, together
with its registered controls: seeds 50-59, primary K=256, XGBoost, same
split, weights and nine member columns. Run both NHANES->KNHANES and
KNHANES->NHANES. New binary items use source `{1->1,2->0,7/9->missing}`
and target `{1->1,0->0,8/9->missing}`. The already frozen diabetes and
smoking special cases are unchanged. Endpoint x direction (20 units), not
the 200 seed cells, is the inferential level.

## Frozen adjudication

For each arm A, artifact-robust AUROC is `A* = max(A,1-A)`. The primary
contrast is

`I* = (a11*-a10*) - (a01*-a00*)`.

P1: pooled corrected I* separates under hierarchical bootstrap of the 20
endpoint-direction units then seeds (10,000 reps, seed 20260820): mean>0,
CI95>0, seed-cell win>=.60, and positive after dropping the best unit.
P2: corrected mean is positive in each direction separately. P3: raw pooled
I separates under the same rule, reported as secondary. Raw success without
P1 is explicitly interpreted as polarity-assisted, not real-data layer
composition. Per-endpoint results and class/evaluable counts are reported.

Runners: `run_crta_v3_stage_factorial_endpoint_expansion_{nh2kn,kn2nh}_v1.py`.
Adjudicator: `summarize_crta_v3_stage_factorial_endpoint_expansion_v1.py`.

