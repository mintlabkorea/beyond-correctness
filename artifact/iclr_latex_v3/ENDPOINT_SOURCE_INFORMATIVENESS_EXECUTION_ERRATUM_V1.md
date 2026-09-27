# Execution erratum: single-class target-support cells, 2026-08-20

## Trigger

The first C execution stopped at NHANES→KNHANES kidney disease, seed 51,
because the newly written extension required two unique fit labels in each new
arm. No stored AUROC values were opened or summarized before this erratum.

## Defect

That check was stricter than the frozen parent stage runner. The parent requires
only nonempty finite source and support labels and permits XGBRegressor to fit a
single-class support draw. A target-only constant predictor is a real outcome of
the frozen scarce-support draw, not an invalid endpoint.

## Correction

- Require at least one finite fit label, matching the parent runner.
- Record the number of unique fit labels for each arm.
- Never redraw, drop, or reclassify a single-class support cell.
- Require matching runner/prereg/input provenance before resuming an existing
  cell. The partial pre-erratum output tree is archived and all cells are rerun
  under the corrected frozen runner.

The primary `source_only_correct` estimand and all adjudication rules are
unchanged. This is a pre-adjudication feasibility correction, not an
outcome-responsive analysis change.
