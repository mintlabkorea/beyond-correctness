# Relation-content controls: at >=693 target rows, content does not matter

Run 2026-08-18.  Adapter mechanism study on the shrunken-Base M1/M2 setting of
`M1_M2_CONCEPT_SCOPE_LADDER_V1.md`; same 180 cells (6 targets x 3 support
fractions x 10 seeds, direction `nh2kn`), same hash-checked parquets.

Metric: query-SD-normalized RMSE (**nRMSE, lower is better**).  A contrast is a
difference in nRMSE, so **negative means the first arm is better**.

## 1. Design

Three relation arms with **identical count** (the 7 relations the qwen3-32b
proposer actually accepted, minus any touching the endpoint -> 6 per target),
differing only in content:

    +rel        the accepted bank verbatim, documented direction
                (bp difference; BMI; waist/height; TC/TG; HbA1c/glucose;
                 Hgb/weight; creatinine/weight)
    +flip       same pairs, same operations, arguments reversed
    +randpair   pairs drawn uniformly from all slot pairs, per-seed redraw;
                the unstructured stand-in for a learned interaction

An earlier draft of this experiment synthesized "documented" relations from
group order and accidentally produced height/weight instead of BMI; its flip
outperforming it exposed the bug.  Only the bank-verbatim version is valid.

## 2. Result (180/180 cells)

| contrast | mean ΔnRMSE | first better in |
|---|---:|---:|
| `L_singleton+rel` vs `+randpair` | +0.00109 | 90/180 |
| `L_fine+rel` vs `+randpair` | +0.00476 | 92/180 |
| `L_single+rel` vs `+randpair` | +0.04614 | **43/180** (random wins) |
| `L_singleton+rel` vs `+flip` | -0.00012 | 89/180 |
| `L_singleton+rel` vs `L_singleton` | -0.00521 | 101/180 |

**In this regime the reviewer objection stands.**  Documented relations do not
beat capacity-matched random pairs (coin flip), documented direction is worthless
against its own reversal, and once member identity is preserved by singleton
concepts, relations of any content add almost nothing.  The earlier finding that
"+rel closes the grouping gap" was recovery of information the pooling had
destroyed -- and anything of matched capacity recovers it equally.

## 3. Why this is the expected answer in this regime, not a dead end

XGBoost with 22,302 source rows and >=693 target support rows can approximate
ratios and differences on its own.  The experiment measured the value of
knowledge under conditions where knowledge is not needed.  The regimes where a
documented prior can in principle matter, none of which this experiment covers:

1. **Data-scarce targets** -- CARTE's transfer protocol uses 32-256 target rows;
   our smallest rung is 693.  Untested.
2. **No column correspondence** -- M4's 2:5 / 1:2 arity, where no pairwise
   surface exists for attention or random pairs.  Already established elsewhere.
3. **Structural injection** -- knowledge as attention structure rather than as
   precomputed feature columns.  Untested.

These are the subject of the small-n prior-value experiment (Phase B) and the
injection comparison (Phase C).  If documented still fails to beat random at 32
rows across backbones, the methodology claim must be restated around regime 2
only.
