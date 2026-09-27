# W3: paired evaluation-noise decomposition — v2 positive weights

Design recorded 2026-09-10 before computing the new bootstrap results.
This is a reviewer-triggered post-result analysis of the existing Figure 1,
not a new confirmatory experiment or a search for a replacement reference.

## Fixed inputs and estimand

Use all nine datasets, all 24 frozen reference mappings, the original intended
predictions, and the five original test splits (42, 1024, 0, 1, 32).
Reproduce every original split AUROC and all 216 Figure 1 utilities to 1e-12.
Validate prediction hashes, labels, row identities, and split membership hashes.
No model fitting, new inference, reference selection, or GPU use. CUDA is hidden;
in particular server GPU 3 is excluded. Existing unrelated jobs are untouched.

U_r is the mean of five split-specific intended-minus-reference AUROCs.
The reference library and nine datasets are fixed, not a random sample of
references or datasets. The five overlapping splits are not independent units.

## Paired resampling

5,000 class-stratified normalized exponential-weight bootstrap draws over unique rows
in the union of the five evaluation splits. Each class retains its union total weight. Within each class with n rows, draw
e_i independently from Exp(1), then set w_i = n e_i / sum(e). These are scaled
Dirichlet(1,...,1) weights, strictly positive with probability one.
Each draw gives a unique row ONE positive real weight, reused in every split
containing that row and in all 25 prediction arms. Recompute each split's exact
weighted AUROC (half credit for ties; macro one-versus-rest if multiclass), then
average the five split AUROCs. Use PCG64 with dataset seed derived from SHA256
of `tabllm-paired-reference-v2/<dataset>`. A zero-class draw fails explicitly;
do not silently drop/redraw it. Bootstrap batches are 50 draws.

This conditions on the released checkpoint, prediction scores, evaluation
membership patterns and union class counts. It estimates evaluation-row
uncertainty, not retraining randomness, population-of-datasets uncertainty,
or an independent-repeat interpretation of the five split seeds.

## Covariance-aware finite-library decomposition

Let R=24, P=I-11'/R, u be the original utility vector and C the bootstrap
covariance of the R-vector (bootstrap covariance uses B-1).

- Observed between-reference variance: V_obs = u' P u / R.
- Within-reference evaluation variance: V_within = tr(C)/R.
- Evaluation contribution to observed between-reference spread:
  V_noise = tr(P C)/R = tr(C)/R - 1' C 1/R^2.
- Method-of-moments corrected finite-library variance:
  V_ref_raw = V_obs - V_noise; report the signed value, and use max(0,V_ref_raw)
  only for the display SD and SD ratio sqrt(max(0,V_ref_raw)/V_within).
- Report V_noise/V_obs and common-shift variance 1'C1/R^2 as well.

Subtracting all of V_within would be incorrect: a common intended-score error
shifts every utility equally and cancels in the reference spread. This is a
bootstrap moment correction, not an exact variance-component identification;
finite-sample AUROC bias and bootstrap approximation remain limitations.
The corrected SD and variance fractions are point summaries, not significance
claims or estimates of a randomly sampled reference population variance.

## Inference and headline check

Report percentile 95% CIs for each utility, within-dataset simultaneous 95%
max-standardized-error bands across 24 utilities, and a stricter simultaneous
95% band across all 216 utilities. Bootstrap errors are centered at their
bootstrap means; standard errors are fixed bootstrap SDs. For the global band,
combine independent dataset bootstrap draws by index, with no dataset resampling.
A resolved sign crossing requires at least one band's lower endpoint >0 AND
another band's upper endpoint <0. Count all nine datasets without selection.
Also report bootstrap crossing frequencies as stability summaries, never as
posterior probabilities or evidence by themselves.

For heterogeneity, compare V_obs with the bootstrap distribution of the
across-reference variance of centered bootstrap errors (an approximate centered
bootstrap test of equal reference utilities). Report (1+exceedances)/(B+1),
and Bonferroni-adjusted p across nine datasets. Report Monte Carlo resolution.
This test concerns unequal reference utilities, separately from opposite signs.
No random-reference resampling, seed-as-independent inference, or new thresholds.

## Deliverables and checks

Standalone runner, deterministic synthetic checks against sklearn weighted
AUROC including ties/multiclass and shared-noise cancellation, input/code hashes,
all bootstrap utility draws, covariance matrices, 216-row interval CSV, nine-row
decomposition CSV, readable results and companion plot. Verify full-data point
reproduction before bootstrap execution. Preserve original Figure 1 inputs.

## Disclosed v1 failure and v2 amendment

The first full v1 run stopped when a multinomial resample omitted an OVR
class in a Car split. No draw was discarded or redrawn. The incomplete v1
outputs and log are retained and cannot substitute for this full v2 analysis.
Before inspecting numerical component or significance results, switch ALL
nine datasets to normalized positive exponential weights, preserving every
arm, estimand, split, draw count, reporting rule, and covariance correction.
The first v1 timing pilot was inadmissible and used Bank only.

Positive weights keep the empirical class support intact and do not manufacture
new rare-class observations. Inference with very few observed positives remains
limited. Weighted-bootstrap bands and centered tests use a frequentist
large-sample bootstrap calibration; they are not exact finite-sample guarantees
or Bayesian posterior claims. This is not an ordinary integer-resampling
bootstrap and must not be described as one.

Sources: Rubin (1981), [The Bayesian Bootstrap](https://people.eecs.berkeley.edu/~jordan/sail/readings/rubin.pdf);
Praestgaard and Wellner, [Exchangeably Weighted Bootstraps of the General Empirical Process](https://stat.uw.edu/research/tech-reports/exchangeably-weighted-bootstraps-general-empirical-process).

Validation additionally compares positive continuous weights against sklearn
and the first actual bootstrap draw in every dataset against an independent
sklearn recomputation across all 25 arms and five splits.
