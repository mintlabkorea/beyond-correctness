# Design lock: K=512 completion of the MCR mismatch-dose panel

Drafted 2026-08-25 after the MCR-MD and MCR-MD-T results were observed.
This is a post-result, descriptive extension; it does not enlarge either
experiment's original confirmatory scope.

## Motivation and prior-result disclosure

The frozen tree experiment evaluated XGB at K=32 and K=512 but HistGB only at
K=32.  The frozen TabPFN extension evaluated K=32 only.  The main figure now
uses model identity as color and support budget as line style, so the two
missing K=512 curves are required for a balanced visual comparison.

Known before this lock: at K=32, full-dose utility U(8) is about +.26 on both
trees and +.18--+.25 on TabPFN; XGB K=512 is about +.03--+.04.  The TabPFN K=32
graded and full-dose criteria pass in all three families.  These observations
are not re-registered as prospective evidence.

## Locked extension

- Cells: the identical 60 primary MCR realizations (three fixed outcome
  families by 20 realizations).  Source/query rows, outcome, renderings, and
  the K=512 support draw come from the frozen MCR runner.
- Dose construction: byte-identical to MCR-MD.  Each cell must match the
  frozen tree cell's `dose_order` and `mismatch_entry_counts`; the d=0 and d=8
  identities and decode=`m1c1rf` equality are asserted.
- New learner-budget strata only: HistGradientBoosting at K=512 and
  TabPFNRegressor 7.0.0 at K=512.  C is true and R is free throughout.
- Arms: decode plus raw and raw-with-live-sentinel doses 2/4/6/8; d=0 is copied
  from decode.  Nine fits per cell, 540 fits per learner.
- Primary plotted quantity: U(d)=Q(decode)-Q(raw_d), Q=-nMSE.  Thin curves are
  fixed-family means; the bold curve is their equal-weight mean.

## Descriptive adjudication

For continuity, report the same two family-resolved diagnostics as MCR-MD-T:
the realization-level Spearman correlation between dose and U(d), and U(8),
with 10,000-replicate realization bootstraps.  Also report paired K=512-minus-
K=32 U(8) within learner and paired learner-minus-XGB U(8) at K=512.  Applying
the earlier thresholds is a descriptive consistency check, not a new
confirmatory verdict.

The manuscript may use these curves to describe support-budget attenuation.
It must retain the bounded learner wording and must not call the result
architecture-general.

## Execution contract

Runner: `scripts/run_crta_v3_mcr_mismatch_dose_k512_extension_v1.py`.
Summarizer: `scripts/summarize_crta_v3_mcr_mismatch_dose_k512_extension_v1.py`.
Output: `experiments/crta_v3_mcr_mismatch_dose_k512_extension_v1/`.
HistGB uses the pinned NumPy/scikit-learn environment and CPU implementation.
TabPFN uses the same B200 `coret_tabpfn` environment as MCR-MD-T.  Code and this
lock are freeze-committed before any final extension cell is fitted.
