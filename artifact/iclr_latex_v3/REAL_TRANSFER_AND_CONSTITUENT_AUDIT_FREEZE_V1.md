# Real transfer-abstention and constituent-availability audits, v1

Frozen 2026-08-27 before outcome-guided case search or new target-only fits.

## Transfer-abstention comparisons

For each existing real-data experiment, first identify a coherent supplied
transfer pipeline whose source rows, target support/query split, learner,
features and preprocessing can be exactly re-run without inventing a pooled
M+C+R object.  Fit a target-only arm using the same learner and target-support
rows and no source rows.  Report

`Q(supplied transfer pipeline) - Q(target only)`

for every eligible pipeline, endpoint and seed.  These are labelled
transfer-abstention comparisons, not component-specific utility estimands.
Pipeline eligibility and any reason for non-eligibility are recorded before
performance is computed.  Auto-C is not used as a surrogate for the paper's
M/C/R objects.

## Outcome-blind constituent-absence search

Search the complete variable/construct registry using only documentation and
availability metadata.  An eligible case must satisfy all four rules:

1. the source cohort contains the documented constituents;
2. the target cohort does not expose those constituents to the learner;
3. a derived construct or operation is explicitly documented for both domains
   or has a fixed cross-domain definition;
4. no target label, prediction or performance statistic is consulted during
   eligibility screening.

Report all eligible cases, including zero.  If zero are found, the manuscript
states that constituent removal is a controlled mechanism probe only.  If one
or more are found, every eligible case is run and reported; no favorable case
is selected.

