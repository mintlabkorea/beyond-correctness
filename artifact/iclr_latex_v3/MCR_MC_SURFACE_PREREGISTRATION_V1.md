# Pre-registration: two-dimensional M x C corruption surface, v1

Declared 2026-08-20 before any joint-surface fit. The corner factorial proves
an M x C interaction, but a four-corner contrast alone cannot distinguish a
smooth complementarity mechanism from an extreme-dose floor or saturation.

## Frozen design

- Reuse the 60 frozen MCR primary cells, K=32 and true R.
- Cross M dose `{0,2,4,6,8}` corrupted measurement-table features with C
  dose `{0,2,4,6,8}` misrouted columns: a complete 5x5 surface.
- Reuse byte-identical nested corruption orders and partial lesions from
  MCR-D (`dose_orders` namespace); no new ordering is selected.
- Run XGBoost and HistGB. Metric Q = -nMSE; realizations are independent,
  families are fixed strata, backbones are replications.

For doses `a<b` and `c<d`, define the rectangle cross-difference

`I[a,b;c,d] = Q(a,c)-Q(b,c)-Q(a,d)+Q(b,d)`.

Positive I means the value of keeping one layer correct is larger when the
other layer is also correct.

## Frozen adjudication

Primary P1 is the moderate rectangle `I[0,4;0,4]`. Per family x backbone,
10,000-realization bootstrap; separation requires mean > 0, CI95 > 0 and
win >= .60. The architecture-general surface claim requires all three
families and both backbones.

Secondary, fixed diagnostics are: mean of the 3x3 adjacent rectangles whose
upper doses are <=6; mean of all 16 adjacent rectangles; one-axis Spearman
degradation at the other axis's dose 0; and
`I[0,4;0,4]-I[4,8;4,8]`. The last quantity diagnoses extreme-dose
saturation and is not a rescue test. If P1 fails while only the corner is
positive, the paper must scope the interaction as an endpoint/corner result.

Runner: `scripts/run_crta_v3_mcr_mc_surface_v1.py`.
Adjudicator: `scripts/summarize_crta_v3_mcr_mc_surface_v1.py`.

