# Pre-registration: matched exchangeable-random wrong control for real-data relation knowledge (W5-R)

Declared 2026-09-04 (Asia/Seoul), **before any cell of this extension has been
executed.** Post-review extension; no manuscript source is edited by this run.

## 1. Reviewer objection and what already exists

The review (W5) states that reversal is a maximally adversarial wrong condition
for a monotone constraint, that the Methods definition of a wrong relation
condition ("matched incorrect relation content while preserving how the relation
enters the learner") is better instantiated by random features with random
directions at matched count, and that the real-data rows lack the
exchangeable-random control that the controlled benchmark declares (appendix,
"reversal and exchangeable-random relations are treated as separate controls").

Disclosure of everything already run, read before this declaration:

| Setting (Table 2 row) | Experiment | Wrong = reversal (content) | Wrong = matched random | Reference (utility) |
|---|---|---|---|---|
| NH→KN, 6 endpoints, K=256, seeds 50–59 | `crta_v3_pam_constraint_relations_v1` (row source) and `crta_v3_form_lesion_matched_v1` (F; same cells, arms bit-identical, 360/360 values, max abs diff 0) | +.1834 [+.0806, +.2975], win .98 | **F-C1b** `sign_random − sign_documented` = +.0038 [−.0046, +.0145], win .57, not separated; **one draw per cell** | −.0020 [−.0071, +.0028] |
| NH→KN replication, seeds 60–69 | `crta_v3_pam_constraint_relations_v1_rep1` | +.1862 [+.0841, +.2990] | **none** | −.0012 [−.0066, +.0031] |
| NH/KN→HRS, 7 endpoints | `crta_v3_m3_sign_probe_v1` (row source; G-SIGN prereg 2026-08-20) | +.2660 [+.1745, +.3675] | **GS-P2** +.0409 [+.0162, +.0769], win .73, separated; one draw per cell (210 cells) | +.0023 [−.0044, +.0093] |
| CAMELS US→GB, 120 basins | `crta_v3_camels_query_extension_v1` (row source; prereg 2026-08-25) | +.1443 [+.1265, +.1628] | **X3** +.0015 [+.0003, +.0028], win .51, not separated (win < .60); one draw per cell, 7,200 basin-cells | −.0000 [−.0011, +.0012] |

All values are gains on each setting's native lower-is-better error (nRMSE for
clinical, log1p-RMSE for CAMELS), oriented so that positive favours the intended
documented directions. The matched-random arm in every existing runner draws the
same number of constrained features as the documented table, uniformly from the
full base feature set, each with an independent random sign, keyed per cell.

Consequently the objection is a **reporting gap for HRS and CAMELS-120** (the arm
is inside the row-source experiments) and a **single-draw, single-seed-set gap
for NH→KN** (one random draw per cell on seeds 50–59 only, in a companion
experiment). This extension closes the NH→KN gap; it does not rerun HRS or
CAMELS.

## 2. Frozen design

- Cells: the frozen PAM cells, unchanged — 6 endpoints (`glucose`, `waist_cm`,
  `triglycerides`, `sbp`, `dbp`, `total_cholesterol`), seed set **v1** =
  seeds 50–59 and seed set **rep1** = seeds 60–69, K ∈ {64, 256, 1024} with
  **primary K = 256**, benchmark `std_cross_nh2kn_shared_anchorreset_fewshot_v1`,
  feature set `pam_constraint_all_v1` (11 base + 9 member slots minus the
  target), pooled source + support weighting (source 1, support n_source/K),
  XGBRegressor hist d6 n300 lr .05 subsample .8 colsample .8 lambda 1,
  `random_state = seed`, `n_jobs = 2`. Bundle construction and support draws are
  taken verbatim from the frozen PAM runner, which is imported unmodified.
- Arms per cell × K (8 fits): `free`, `sign_documented`, `pl_sign_flip`
  (re-fit), and `sign_random_1` … `sign_random_5` (**D = 5 draws**).
- Random arm: `k` = number of documented features present for the endpoint
  (1 or 2). Draw `k` distinct slots uniformly from the endpoint's feature list
  **excluding the documented features** (so no draw contains a correct or a
  reversed documented relation; this matches the controlled benchmark's
  exclusion of true pairs) and an independent sign in {−1, +1} for each; all
  other entries 0. A draw equal to an earlier draw of the same cell is
  rejected. RNG key
  `relation_random_wrong_v1|sign_random|{target}|{seed}|{draw}` through the
  frozen PAM `derived_rng`. D = 5 rather than 1 because with k ∈ {1, 2} a single
  draw per cell makes the arm a near-lottery; the per-cell mean over draws is
  the primary random-arm value and the five per-draw contrasts are descriptive.
- Replication gate: for every cell and K, the re-fit `free`, `sign_documented`
  and `pl_sign_flip` nRMSE must equal the frozen PAM values (v1 or rep1 root)
  within 1e-9. The gate is recorded per cell; the summarizer refuses to declare
  any verdict unless all 120 cells pass. Contrasts always use the in-process
  fits.
- Environment: conda `arpa` (xgboost 3.1.3, numpy 2.2.6, pandas 2.3.3,
  scikit-learn 1.7.2), the environment in which PAM and F were run; local CPU,
  3 shards × 2 threads, no GPU. Parquet SHA-256 pins as in the PAM runner.

## 3. Estimands and adjudication (frozen)

nRMSE at K = 256; gain = second-named minus first-named error, so positive
favours the first-named arm. Hierarchical bootstrap, targets then seeds, 10,000
reps, seed 20260819 (the PAM summarizer's `hierarchical_ci`); separated = mean >
0 ∧ CI95 low > 0 ∧ win ≥ .60 ∧ drop-best-target mean > 0. Seed sets v1 and rep1
are adjudicated **separately** (60 cells each); the pooled 120-cell estimate is
descriptive.

- **RW1 (matched-random content):** documented vs mean-over-draws random,
  `nrmse(sign_random_mean) − nrmse(sign_documented)`.
- **RW2 (reversal content, gate):** `nrmse(pl_sign_flip) − nrmse(sign_documented)`;
  must reproduce the PAM V-SIGN-CONTENT value exactly.
- **RW3 (utility, descriptive):** `nrmse(free) − nrmse(sign_documented)`.
- **RW4 (reference − matched-random wrong, descriptive):**
  `nrmse(sign_random_mean) − nrmse(free)`; this is the Table 2
  "Reference − wrong" column under the matched-random construction.
- **RW5 (reversal beyond random):** `nrmse(pl_sign_flip) − nrmse(sign_random_mean)`.
- Descriptive: per-draw RW1 and RW4; per-draw dispersion within cell.

Frozen predictions:

- **RW-P1:** replication gate passes in 120/120 cells and RW2 is separated in
  both seed sets.
- **RW-P2:** RW1 is **not** separated in either seed set (prior: F-C1b on v1,
  one draw). A separated RW1 in both seed sets falsifies this and is reported as
  matched-random content sensitivity in NH→KN.
- **RW-P3:** RW5 is separated in both seed sets.

Interpretation map:

- P1 ∧ P2 ∧ P3: the NH→KN intended–wrong gap is reversal-specific; under the
  matched-random wrong construction content sensitivity and utility are both
  unresolved, so Table 2's "large content sensitivity, near-zero utility"
  contrast must be stated as "large **directional** sensitivity (vs reversal),
  small generic content sensitivity (vs matched random), near-zero utility".
- P2 fails in both seed sets: documented directions beat matched-random
  directions in NH→KN as they do in HRS; report the magnitude alongside HRS and
  CAMELS-120.
- P2 splits across seed sets: report as unreplicated.
- P1 fails: environment or construction drift; the extension is reported with
  the deviation and no verdict.

## 4. What this extension cannot show

It does not create a capacity-matched control beyond matched count: a random
constraint removes capacity on different, possibly irrelevant, features. It does
not rerun HRS or CAMELS-120, whose single-draw random arms are reported from the
frozen row-source experiments. It does not change any relation table.

## 5. Execution

Runner `scripts/run_crta_v3_relation_random_wrong_v1.py`, self-test
`scripts/test_crta_v3_relation_random_wrong_synthetic_v1.py`, summarizer
`scripts/summarize_crta_v3_relation_random_wrong_v1.py`, launcher
`scripts/launch_crta_v3_relation_random_wrong_v1.sh`; evidence root
`experiments/crta_v3_relation_random_wrong_v1/{v1,rep1}/`; logs
`logs/crta_v3_relation_random_wrong_v1/`. Committed with this document before
launch. Engineering smoke outputs, if any, live outside the evidence root and are
not used for inference.
