# Relation wrong-condition construction audit (reviewer W5), v1

Compiled 2026-09-04. Purpose: answer the review point that reversal is a
maximally adversarial wrong condition for a monotone constraint, that the
Methods definition of a wrong relation condition is better instantiated by
random features with random directions at matched count, and that the real-data
rows lack the exchangeable-random control that the controlled benchmark declares.

## 1. Finding

Every real-data relation setting in Table 2 already carries a matched-count,
random-feature, random-sign wrong arm (`sign_random`), frozen before execution on
2026-08-20 (G-SIGN and F preregistrations) and 2026-08-25 (CAMELS-120 extension,
contrast X3). The manuscript reported only the reversal contrast. The gap was
therefore one of reporting for HRS and CAMELS-120, and one of draw count and
seed coverage for NH→KN, which the W5-R extension closes (section 3).

Sign conventions: all values are `error(second) − error(first)` on each
setting's native lower-is-better metric (nRMSE for clinical, log1p-RMSE for
CAMELS), so positive favours the first-named condition. Intervals are the
frozen hierarchical bootstraps of each row-source experiment (10,000 reps, seed
20260819; endpoints then cells for HRS, query basins for CAMELS-120, targets then
seeds for NH→KN). Computed by `scripts/compute_crta_v3_table2_random_wrong_v1.py`
from the frozen cells; output `experiments/crta_v3_relation_random_wrong_v1/TABLE2_RANDOM_WRONG_V1.json`.

## 2. Frozen row-source experiments (no new fits)

| Setting | Intended − reversal (W_rev) | Intended − matched random (W_rand) | Utility (intended − free) | Free − W_rand | W_rev − W_rand |
|---|---|---|---|---|---|
| NH/KN→HRS, 7 endpoints, 210 cells (`crta_v3_m3_sign_probe_v1`, GS-P2) | +.266 [+.175, +.367] | **+.041 [+.016, +.077]**, win .73, separated | +.002 [−.004, +.009] | +.039 [+.015, +.072] | +.225 [+.125, +.338] |
| CAMELS US→GB, 120 basins, 7,200 basin-cells (`crta_v3_camels_query_extension_v1/probe`, X3) | +.144 [+.127, +.163] | +.0015 [+.0003, +.0028], win .51, **not separated** (win < .60) | −.000 [−.001, +.001] | +.0015 [+.0008, +.0022] | +.143 [+.125, +.161] |
| NH→KN, 6 endpoints, 60 cells, seeds 50–59, one draw per cell (`crta_v3_form_lesion_matched_v1`, F-C1b; arms bit-identical to the PAM row source) | +.183 [+.081, +.298] | +.004 [−.005, +.015], win .57, not separated | −.002 [−.007, +.003] | +.006 [+.001, +.015] | +.180 [+.078, +.296] |

Random-arm construction in all three runners: `k` = number of documented
constrained features; `k` distinct features drawn uniformly from the full base
feature list, each with an independent sign in {−1, +1}; keyed per cell.
(HRS: `run_crta_v3_m3_sign_probe_v1.py:143-146`; CAMELS:
`run_crta_v3_camels_query_extension_probe_v1.py:181-185`; F:
`run_crta_v3_form_lesion_matched_v1.py:125-131`.)

Controlled benchmark counterpart (tree factorial
`crta_v3_mcr_factorial_semisynth_v1`, XGB, K=32, ΔQ): true vs exchangeable-random
relation set (`P3a`) additive +.126 [+.092, +.163], pairwise +.012, sparse
+.007; true vs reversed (`relation_vs_flipped`) additive +.304, pairwise +.013,
sparse +.010; random constraint harm vs free additive +.102, pairwise and sparse
not separated; utility (`P3b`) additive +.024, pairwise +.010, sparse +.007. The
appendix relation summary table reports the reversal-based contrast only.

## 3. W5-R extension (NH→KN, five draws per cell, both seed sets)

Prereg `RELATION_MATCHED_RANDOM_WRONG_PREREGISTRATION_V1.md` (commit 97bec85c2);
runner re-fits `free`, `sign_documented`, `pl_sign_flip` with a bit-level
replication gate against the frozen PAM cells and adds `sign_random_1..5`
drawn from the non-documented features. Results are appended below by the
summarizer output once the 120 cells complete.

### Results (run 2026-09-04 10:33–10:52, 120/120 cells, replication gate 120/120 with worst deviation 0.0)

| Seed set | Intended − reversal (RW2) | Intended − matched random, mean of 5 draws (RW1) | Utility, intended − free (RW3) | Free − random (RW4) | Reversal − random (RW5) |
|---|---|---|---|---|---|
| NH→KN seeds 50–59 (60 cells) | +0.183 [+0.081, +0.298] | -0.001 [-0.006, +0.003], win 0.47, not separated | -0.002 [-0.007, +0.003] | +0.001 [-0.000, +0.001] | +0.185 [+0.082, +0.299], separated |
| NH→KN seeds 60–69 (60 cells) | +0.186 [+0.084, +0.299] | -0.001 [-0.007, +0.004], win 0.55, not separated | -0.001 [-0.007, +0.003] | +0.001 [-0.000, +0.001] | +0.187 [+0.085, +0.299], separated |
| NH→KN pooled (120 cells, descriptive) | +0.185 [+0.082, +0.298] | -0.001 [-0.006, +0.004], win 0.51 | -0.002 [-0.007, +0.003] | +0.001 [+0.000, +0.001] | +0.186 [+0.083, +0.299] |

Per-draw RW1 means (v1): [-0.0018, -0.0002, -0.0014, -0.0023, -0.0011]; (rep1): [-0.0012, 0.001, -0.0015, -0.0008, -0.0007]; mean within-cell draw SD 0.0030 / 0.0038 nRMSE.

Frozen predictions: {"RW_P1_gate_and_reversal_separated": true, "RW_P2_random_content_not_separated": true, "RW_P3_reversal_beyond_random_separated": true} — all three hold in both seed sets.

Interpretation (prereg map, branch P1 ∧ P2 ∧ P3): the NH→KN intended–wrong gap is reversal-specific. Under the matched-random wrong construction, content sensitivity (−.001) and utility (−.002) are both unresolved and random constraints on non-documented features neither help nor hurt (free − random +.001). Table 2's clinical relation rows must therefore state content sensitivity as *directional* sensitivity against reversal, and report the matched-random contrast alongside: NH→KN ≈ 0, HRS +.041 (separated, and matched by a +.039 harm of random constraints relative to free), CAMELS-120 +.002 (below the frozen win-rate rule).

## 4. Consequence for the manuscript

- Methods (Table of conditions, relation row): name both wrong constructions.
- §4.2 and Table 2: add the matched-random line under each relation row (content sensitivity and reference − wrong).
- Appendix relation aggregate: add the wrong-construction table (both seed sets for NH→KN) and the controlled counterpart (true vs exchangeable-random +.126 vs true vs reversed +.304, additive XGB K=32).
- Conclusion: the size of the intended–wrong difference for relation knowledge depends on the wrong construction; the decomposition claim (most of the reversal gap is wrong-condition harm) survives under both constructions.

Artifacts: `experiments/crta_v3_relation_random_wrong_v1/{v1,rep1}/*/seed_*/metrics.json`, `SUMMARY_V1.json`, `TABLE2_RANDOM_WRONG_V1.json`; logs `logs/crta_v3_relation_random_wrong_v1/`; results commit follows the freeze commit 97bec85c2.
