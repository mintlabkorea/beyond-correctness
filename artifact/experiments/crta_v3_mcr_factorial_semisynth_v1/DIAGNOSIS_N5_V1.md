# N5 quarantine diagnosis (2026-08-20)

The frozen rule fired: `N5_deranged_vs_deranged2` failed its
exchangeable-null criterion in the pairwise family (+0.105 nMSE
[+0.032, +0.184] xgb; +0.108 histgb), so all verdicts were quarantined
pending diagnosis.

## Diagnosis: statistical excursion, not a manufactured effect

1. **Slot-symmetry swap test (mechanical).** Rebuilding the two worst
   cells (r18, r03) with the permutation contents exchanged between the
   `deranged` and `deranged2` slots swaps the Q values **exactly**
   (`exact_swap=True` for both). The pipeline is bit-symmetric in the
   two slots; Q is a function of permutation content only.
2. **Family sign pattern.** A slot-asymmetry bug would push the same
   direction in every family (the code path is family-agnostic). The
   observed means are +0.105 (pairwise), −0.030 (additive), −0.027
   (sparse): pairwise-only, and both other families lean the other way.
3. **Magnitude of the excursion.** Per-realization diffs in pairwise
   have SD 0.17; the mean +0.105 over n = 20 is t ≈ 2.6 (p ≈ 0.02 for
   one test). Nine null tests were evaluated (3 nulls × 3 families);
   one excursion at this level is within expectation. The two backbones
   are near-perfectly correlated on identical draws, so backbone
   agreement adds no independent evidence here.

## Consequence for interpretation (recorded, not hidden)

- The C-axis derangement-draw contrast has a **noise floor of roughly
  0.1 nMSE in the pairwise family at n = 20**. Every C-axis effect
  claimed (P2: +0.30 to +0.51) exceeds that floor by 3–5×; the P2
  verdicts stand.
- The R-axis null (N4) is tight (±0.005 across families), so the small
  P3a/P3b margins (+0.007 to +0.13) are read against their own
  calibrated floor, which they clear.
- The adjudicator's null criterion (CI95 ∋ 0 ∧ |mean| < 0.05) has a
  measurable false-alarm rate on high-variance C contrasts at n = 20;
  any future use of this factorial at smaller effect sizes needs more
  realizations or matched-variance nulls.

Quarantine lifted on this basis; the `exchangeable_nulls_clean: false`
flag stays in `SUMMARY_V1.json` as the honest record.
