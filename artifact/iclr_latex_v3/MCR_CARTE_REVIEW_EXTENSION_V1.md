# Review-triggered extension: CARTE on the M/C/R attribution design, v1

**Frozen before execution:** 2026-08-25.  This is a review-triggered,
post-result learner-coverage extension.  It is not part of the original MCR
confirmation and will be labelled as such regardless of direction.

**Engineering-smoke disclosure:** before the full grid was opened, pairwise
realization 0 at K=32 was run for two epochs (rather than the evidence
contract's 200-epoch maximum) to verify the CARTE 0.0.26 API, graph shapes,
and CUDA path.  The smoke tree is stored separately with a `-smoke` suffix and
is inadmissible for analysis.  It caused no design or hyperparameter change;
the only subsequent code edit suppressed repeated upstream deprecation
warnings in logs.

## Question and scope

The paper cites schema-semantic learners but its controlled M/C/R benchmark
currently contains tree learners, TabPFN, and an MLP.  This extension asks
whether the paper's correct / matched-wrong / reference decomposition remains
meaningful in a learner whose native interface embeds column names and learns
jointly across tables.  It uses the official `carte-ai==0.0.26`
`CARTEMultitableRegressor`, the shipped `kg_pretrained.pt`, and fastText
`cc.en.300.bin` embeddings.

The extension reuses the exact 60 frozen primary MCR realizations, source rows,
target support/query rows, outcomes, renderings, lesions, and RNG namespace
from `MCR_FACTORIAL_SEMISYNTHETIC_PREREGISTRATION_V1.md`.  Its parent runner
SHA-256 is pinned by the extension runner.  No participant-level artifact is
written.

## Arms

There are seven arms per realization and support budget.  `correct` is shared
by all three rows; the other six change exactly one component while keeping
the remaining components correct.

| Component | correct | matched-wrong | reference |
|---|---|---|---|
| Measurement M | true source decoder | frozen matched-complexity wrong decoder | rendered source values left undecoded; true sentinels are neutralized to missing |
| Correspondence C | shared documented concept names | the same semantic-name multiset with source values routed through the frozen type-preserving derangement | distinct frozen source/target native hash names, i.e. no supplied semantic bridge |
| Relation R | true relation-derived columns | frozen density-, operation-, and topology-matched random relations | no relation-derived columns |

The target values are correctly decoded in every arm.  Correct and wrong C
use the same eight semantic column names; only their source assignment differs.
The C reference retains the original per-side anonymous names.  Relation names
are rendered from the names available in that arm, so the C-reference arm does
not leak a canonical correspondence through derived-column labels.

CARTE has no monotonic-constraint API.  R is therefore evaluated through its
natural value-plus-text interface, not through the executable constraint
interface used by the tree learners.  In pairwise and sparse families, derived
columns contain the declared difference or log-ratio and their names state the
arguments and direction.  In the additive family, the matched relation channel
duplicates the selected feature value under a directional relation name.  The
correct and wrong arms have identical channel counts; the free arm has none.
This extension may establish a CARTE-specific content or utility result for
that interface, but it cannot generalize the tree constraint result.

## Learner and fitting contract

- Predictor: official `carte-ai==0.0.26` multitable regression with one model,
  shipped pretrained weights loaded and frozen.
- Source: the frozen 2,048 MCR source rows; target support: K in {32, 512};
  query: the frozen 2,000 target rows.
- Hyperparameters: learning rate 0.001, batch size 64, maximum 200 epochs,
  validation fraction 0.2, early-stopping patience 20, target fraction 0.125.
- Numeric missingness: domain-local training medians plus explicit missing
  indicator columns.  The state is fitted on source rows for the source table
  and on target support rows for the target table, then applied unchanged to
  query rows.
- Random state: realization index, held fixed across arms.  CARTE uses GPU
  scatter operations that are not bit-deterministic; the paired 20-realization
  distribution, not repeated selection of favorable runs, is the unit of
  analysis.
- Hardware: B200 GPUs 0, 1, and 2, one outcome family per GPU.  GPU 3 is kept
  free by the user's execution instruction for this extension.

## Estimands and reporting

The score is the parent benchmark's
`Q = -MSE / Var(y_query)`.  For each component L,

- content: `Q(correct) - Q(L_wrong)`;
- utility: `Q(correct) - Q(L_reference)`;
- implied wrong-versus-reference:
  `Q(L_wrong) - Q(L_reference) = utility - content`.

Inference is realization-level within each fixed outcome family (20 units,
10,000 paired bootstrap draws).  Per-family estimates, 95% percentile
intervals, and win fractions are always reported.  For a compact across-family
screen, the summarizer also reports the bootstrap distribution of the minimum
family mean (a min-statistic over the three fixed strata).  The inherited
descriptive separation rule is mean > 0, lower interval > 0, and win >= 0.60;
it is not promoted to a new confirmatory claim because this extension was
triggered by review after the primary results were known.

No hyperparameter, arm definition, realization, or support budget will be
changed after the first evidence cell is opened.  Runtime failures are reported
and resumed under the same runner hash; mixed-hash result trees are rejected.
