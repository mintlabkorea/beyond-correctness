# Examination no-bridge reference — frozen design

Frozen before execution: 2026-08-28 (Asia/Seoul).

## Question

Can examination correspondence utility be evaluated against a coherent
domain-local reference that preserves the member values, representation width,
source transfer, target support, and learner recipe while removing shared
cross-domain member identity?

## Cells

- The six existing NHANES→KNHANES examination endpoints.
- Seeds 50–59 and target support K=256.
- The same source, target-support, and query splits as the M1/M2 layer ladder.
- XGBoost with 300 trees, depth 6, learning rate .05, row subsampling .8,
  `colsample_bytree=1.0`, and the existing source/support weights.

## Three arms

Every non-endpoint member has two allocated columns. All arms therefore have
the same width and exactly one observed member value per row and construct.

1. `S_shared_bridge`: source and target values occupy the first column of each
   construct; the second is missing. This supplies shared cross-domain identity.
2. `W_deranged_bridge`: the same representation, but target-side member values
   are assigned by the existing fixed-point-free derangement. This is the
   interface-matched wrong-content arm.
3. `R_domain_local`: source values occupy the first member column and target
   values occupy the second, with complementary missingness. It preserves
   within-domain member values but removes every shared cross-domain member
   column.

Base features remain shared and unchanged. Feature subsampling is disabled so
the inert padding column in S/W cannot change the probability that an
informative feature is offered to a tree.

## Estimands and reporting

All completed cells and all three paired contrasts will be retained:

- content: `S_shared_bridge − W_deranged_bridge`;
- utility: `S_shared_bridge − R_domain_local`;
- reference–wrong: `R_domain_local − W_deranged_bridge`.

Gains are oriented as reductions in query-SD-normalized RMSE. Inference uses
10,000 hierarchical bootstrap draws over endpoints and then paired seeds. The
existing descriptive gate (positive mean, lower interval above zero, ≥60%
positive paired cells, and positive drop-best-endpoint mean) is reported but
does not suppress any contrast.

This is a post-result reference-construction extension. It does not retroactively
change the original examination estimand, learner configuration, or status.

## Post-execution wording clarification

The phrase “exactly one observed member value per row and construct” above
refers to one materialized value location before native missingness. Rows whose
original value is missing remain missing; no arm imputes or duplicates them.
This clarification does not change the frozen matrices or estimands.
