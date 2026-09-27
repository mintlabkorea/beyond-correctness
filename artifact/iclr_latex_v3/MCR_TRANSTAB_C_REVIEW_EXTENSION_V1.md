# Review-triggered TransTab correspondence extension, v1

**Frozen before evidence execution:** 2026-08-25. This is a post-result,
review-triggered learner-coverage extension. It will be labelled as such
regardless of direction. Engineering smokes use separate output directories,
at most two epochs, and are inadmissible for analysis.

**Engineering-smoke disclosure:** additive realization 0 at K=32 was run for
two epochs in a separate `_smoke` result tree. All three arms completed and
raw regression predictions were finite. The smoke exposed that the source-tree
provenance function included import-generated `__pycache__` files; the function
was narrowed to the fixed Python, tokenizer, setup, and requirements files.
No model, data, arm, optimization, or reporting choice changed after the smoke.

## Question

Does the correct / matched-wrong / reference separation for schema
correspondence survive in a learner whose native input tokenizes column names
and accepts tables with different schemas?

This is deliberately a narrow three-arm experiment. It does not force
measurement or relation knowledge through interfaces for which TransTab was
not designed. The measurement decoder and relation-derived value columns are
held correct in all three arms; only the schema-semantic bridge changes.

## Frozen data and arms

The experiment reuses the exact 60 primary MCR cells (three outcome families
times 20 realizations), 2,048 source rows, target support/query rows, outcomes,
renderings, type-preserving derangements, and RNG namespaces from
`MCR_FACTORIAL_SEMISYNTHETIC_PREREGISTRATION_V1.md`. Support budgets are
K in {32, 512}; every target query set has 2,000 rows.

| Arm | Source names | Target names | Values |
|---|---|---|---|
| `correct` | shared documented concept names | the same documented names | correctly decoded |
| `c_wrong` | the same documented-name multiset, attached through the frozen type-preserving source derangement | documented names | correctly decoded |
| `c_reference` | frozen source-side anonymous hash names | distinct frozen target-side anonymous hash names | correctly decoded |

The correct and wrong arms therefore have identical name tokens and feature
counts. The reference removes the supplied cross-table semantic bridge rather
than replacing it with a favorable alternative. Correct relation-derived
columns are present in every arm and are named from the base names available
in that arm, so the reference does not recover canonical correspondence from
derived-column labels.

## Learner and fitting contract

- Code: official TransTab repository commit
  `fdb34cf38abda73ee6a741b802fe226cc89ba7b5`, whose package metadata is
  version 0.0.7. The regression head was added to the official repository in
  2025, after the original NeurIPS 2022 paper; this timing is disclosed.
- Model: `TransTabRegressor`, official defaults (hidden size 128, two
  transformer layers, eight heads, feed-forward size 256, ReLU, no dropout),
  initialized from scratch. The official project does not publish a generic
  regression checkpoint for this use.
- Training input: a list containing the source table and the target-support
  table, using TransTab's variable-column supervised training interface.
- Optimization: 50 fixed epochs, Adam, learning rate 1e-4, weight decay 0,
  batch size 64. There is no validation-based model selection. Holding epochs
  fixed uses every support label and keeps selection identical across arms.
- Labels: standardized by the source-training mean and standard deviation for
  optimization, then transformed back before scoring.
- Numeric missingness: domain-local training medians plus explicit missing
  indicators. Source state is fitted on source rows; target state is fitted on
  target support and applied unchanged to target query.
- Random state: realization index, paired across the three arms.
- Hardware: B200 GPUs 0, 1, and 2, one fixed outcome family per process. GPU 3
  remains unused under the user's allocation instruction.

Two narrow compatibility corrections are part of the frozen wrapper and are
recorded in every artifact. First, upstream `TrainDataset.__getitem__` uses
`index-1:index`, omitting a row; the wrapper uses `index:index+1`. Second,
upstream `predict()` treats every one-output model as binary and applies a
sigmoid; the wrapper reads raw `TransTabRegressor` outputs. The architecture,
MSE loss, tokenizer, optimizer, and training path otherwise remain upstream.

## Estimands and reporting

The score is the parent benchmark's `Q = -MSE / Var(y_query)`.

- content: `Q(correct) - Q(c_wrong)`;
- utility: `Q(correct) - Q(c_reference)`;
- wrong versus reference: `Q(c_wrong) - Q(c_reference) = utility - content`.

Inference is paired at the realization level within each of the three fixed
outcome-family strata (20 units, 10,000 bootstrap draws). Family estimates,
95% percentile intervals, and win fractions are always reported. A compact
minimum-family bootstrap statistic is descriptive only. No arm, support
budget, realization, hyperparameter, or reporting contrast changes after the
first full-grid evidence cell is opened.
