# Pre-registration: S5 — backbone generality of the binding-content result

Declared 2026-08-20, **before any S5 cell has been executed.**

S1 established that the direction-constraint identification result is
not an XGBoost artifact. The correspondence axis has no such check: the
stage factorial's binding contrast (S2: `a11_stage_columns` vs
`pl_columns_at_stage`, +0.045 AUROC [0.022, 0.071]) and everything the
paper says about correspondence content on the survey surface comes
from one estimator. S5 refits the identical cells on sklearn
HistGradientBoosting.

## Design

The frozen stage-factorial cells (benchmark
`std_cross_nh2kn_shared_anchorreset_fewshot_v1`, targets
diabetes_history / hypertension_history / current_smoking_status, seeds
50–59, K ∈ {64, 256, 1024}, **primary K = 256**), L0 on (pipeline
table + pipeline label maps), three arms only:

| arm | features |
|---|---|
| `a10_stage` | base slots |
| `a11_stage_columns` | base + 9 member slots, correct target-side binding |
| `pl_columns_at_stage` | base + members with the **same frozen derangement draws** as the executed XGBoost run (identical RNG keys `stage_factorial_v1|pl_col|{target}|{seed}`), identical column exposure |

Estimator: HistGradientBoostingRegressor (max_iter 300, max_depth 6,
learning_rate 0.05, min_samples_leaf 20, l2_regularization 1.0, no
early stopping), the S1 matching; XGBoost's subsample/colsample 0.8
have no HistGB analog and are declared unmatched. Pooled weighted fit
exactly as the executed program (source weight 1, support weight
n_src/n_sup); under weights sklearn's count-based `min_samples_leaf`
and XGBoost's Hessian-mass `min_child_weight` are not equivalent, so S5
claims **direction agreement, never effect-size equality**. Metric:
AUROC against the fixed codebook-documented target-side binary,
evaluation identical to the stage factorial.

## Adjudication (frozen)

At K = 256, hierarchical bootstrap (targets then seeds, 10,000 reps,
seed 20260820), separation = mean > 0 ∧ CI95 excludes 0 ∧ win ≥ 0.60 ∧
mean > 0 with the best target dropped.

- **S5-P1**: `a11_stage_columns` − `pl_columns_at_stage` separates
  (binding content on a second backbone).
- **S5-P2**: `a11_stage_columns` − `a10_stage` separates (member
  columns are worth having on the stage).

S5-P1 ∧ S5-P2 ⇒ the correspondence-content claim is a property of the
task and the knowledge, not of one library. S5-P1 failing ⇒ the binding
result is estimator-specific and every correspondence claim on this
surface must be scoped to XGBoost. Descriptive: all three K, per-target
tables, XGBoost-vs-HistGB effect-size comparison.

## Execution

`scripts/run_crta_v3_binding_backbone_generality_v1.py` (per-cell
`metrics.json`, resumable),
`scripts/summarize_crta_v3_binding_backbone_generality_v1.py`.
Committed before launch. One L0-on build per cell (no ablated or wrong
builds needed), 30 cells, local CPU, no GPU.
