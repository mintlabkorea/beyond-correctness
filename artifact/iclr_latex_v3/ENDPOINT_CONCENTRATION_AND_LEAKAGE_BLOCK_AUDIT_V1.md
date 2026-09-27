# Endpoint concentration and leakage-block asymmetry audit v1

Found: 2026-08-18, while answering "can the results move depending on which endpoint you predict?"
Status: **verified from executed artifacts**; the remediation is NOT yet run.
Severity: **highest open issue in the project.** It affects every positive Auto-C number.

## 0. One-paragraph summary

Every task's headline Auto-C gain is dominated by a single endpoint, and in the two
task families that never implemented a near-definitional-proxy block (M1/M2 and M3),
that endpoint is the one whose closest clinical partner sits inside the concept bank.
M4/M5 do implement such a block. The tasks were therefore not run under a common
exclusion rule, and the cross-task comparison in its current form is not sound.

## 1. Endpoint concentration (leave-one-out)

Regression, nRMSE, primary usable bank per task, uncapped rung unless noted.

| task / model | headline | top endpoint | top gain | share | drop top | change |
|---|---:|---|---:|---:|---:|---:|
| M3 L2 / codex_gpt56sol | +0.016580 | `hemoglobin` | +0.17209 | 94.4% | +0.001029 | **-94%** |
| M4 L2 / llama4_scout | +0.052828 | `hrs__mobility_difficulty_count` | +0.30521 | 64.2% | +0.021279 | **-60%** |
| M4 L0 / llama4_scout | +0.020524 | same | +0.11178 | -- | +0.009116 | -56% |
| M6 L2 / gemma3_27b_it | +0.006925 | `hrs__cesd_score` | +0.03827 | 69.1% | +0.002447 | **-65%** |

M3 is not "flat because nothing happens".  It is `hemoglobin +0.17209` against
`wbc -0.05243` and nine near-zero endpoints.

### M4's ladder is regression-only

The binary (AUROC) arm is negative and gets worse as the source budget grows:

    L0 -0.001787   L1 -0.002507   L2 -0.003245

Any sentence of the form "the gain grows with source budget" must say "regression".

## 2. Leakage-block asymmetry

`scripts/crta_v3_m4_hrs2klosa_runtime_v1.py` and the M5 runtime both carry a
`LEAKAGE_BLOCKS` dict, with this stated criterion in the code:

> Deterministic definitions and near-definitional proxies are excluded from both
> Base and compiler inputs for the endpoint at hand.

| task | proxy blocking | forbidden set per endpoint |
|---|---|---|
| M1 / M2 | **none in code, but see below** | `[target_raw_id(...)]` -- one column |
| M3 | **none** | `[SOURCE_SCHEMA_COLUMN[endpoint]]` -- one column |
| M4 | yes | `{endpoint} | LEAKAGE_BLOCKS[endpoint]` |
| M5 | yes | same |
| M6 | yes | same as M4/M5 -- **verified 2026-08-18** |

M6 was the one unread row.  Its `LEAKAGE_BLOCKS`
(`scripts/crta_v3_m6_hrs2charls_runtime_v1.py:196`) carries the same criterion
comment and is **content-identical** to M4's and M5's -- 13 blocked endpoints,
the same sets -- and is applied to both Base (`_base_suffixes_from_schemas`) and
the compiler forbidden set, through the same `_forbidden_source_ids` /
`_forbidden_target_ids` helpers.  So the asymmetry was never M4/M5 against
M3/M6; it was **M4/M5/M6 against M1/M2 and M3**, and after the M3 re-run only
M1/M2 sits outside the rule.  Remediation item 3 is closed.

The compiler itself is correct: `_compile_concepts` zeroes a concept's whole
channel set if any member is forbidden (`iclr_latex_v3/method_contract/v1/compiler/compile_bank.py:95`).
The defect is the forbidden set handed to it, not the compiler.

## 3. What that produced

### M3: hemoglobin predicted from red blood cell count

codex_gpt56sol M3 accepted bank:

    c_001 blood_pressure_measurements  source: nhkn__sbp, nhkn__dbp
    c_002 blood_cell_counts            source: nhkn__rbc, nhkn__wbc

Base features actually used for `hemoglobin` (read from `split_manifest.json`):

    slot__age slot__sex slot__sbp slot__dbp slot__glucose slot__hba1c slot__creatinine

`rbc` and `wbc` are **not in the base slot set for any endpoint**.  So:

    Base    age,sex,sbp,dbp,glucose,hba1c,creatinine  -> nRMSE 0.88282
    Auto-C  + concept channels over {rbc, wbc}        -> nRMSE 0.71073   gain +0.17209

Hemoglobin is the protein carried by red blood cells and is co-reported with RBC
in the same CBC panel; hematocrit (+0.02214, the second largest) is the red-cell
volume fraction.  The two positive endpoints are the two most collinear with the
concept's members.  This is 94.4% of M3's headline.

Both readings must be stated:
- **for**: this is the designed mechanism -- the proposer read documentation and
  found an alignable column outside the hand-built base slot interface.
- **against**: M4/M5 declare that near-definitional proxies are excluded and M3
  does not, so the tasks did not run under one rule.

### M1/M2: every target is a bank member

Targets: `glucose waist_cm triglycerides sbp dbp total_cholesterol`.
codex full-document v2 accepted bank (`.../gpt-5.6-sol/medical_nhanes_knhanes_full_documents_v2_attempt_02`):

    c_001 body_measurements          BMXHT, BMXWAIST, BMXWT
    c_002 first_reading_blood_pressure BPXSY1, BPXDI1
    c_003 diabetes_test_measurements LBXGLU, LBXGH
    c_004 blood_lipid_measurements   LBXTC, LBXSTR

All six targets are literally members.  Single-column blocking removes only the
target's own raw column and leaves its closest partner inside the concept:

    glucose           -> LBXGH  (HbA1c: 3-month glycated glucose average)
    total_cholesterol -> LBXSTR (triglycerides; Friedewald-related)
    triglycerides     -> LBXTC
    sbp               -> BPXDI1
    dbp               -> BPXSY1
    waist_cm          -> BMXHT + BMXWT

This is the leading hypothesis for why M1/M2 showed `+0.211053
[+0.072313,+0.379431]` win 0.900 while M3/M4/M6 show near-zero.  **It is a
hypothesis, not yet a measurement.**  See section 5 for the check that settles it.

> **2026-08-18, measured: this hypothesis is false.**  See
> `iclr_latex_v3/M1_M2_BASE_PROXY_PRECHECK_V1.md`.  It fails twice over.
> (1) M1/M2 Base already carries every listed partner -- `slot__hba1c` is in
> Base when predicting glucose, `slot__dbp` when predicting sbp, and so on -- so
> Auto-C injects nothing Base lacks.  (2) In every M1/M2 bank each target shares
> a concept with its partner, so blocking the target's own column already zeroes
> that concept: 180 executed manifests x 2 sides, 0 leaks, 360 zeroed.
> Paragraph left in place as the record of what was believed.

## 4. Two facts that are correct and should not be re-litigated

- `rbc` and `wbc` gains are byte-identical across codex_gpt56sol and qwen3_32b in
  M3 (`0.0019010193281439787`, `-0.05243242197891302`).  This is **not a bug**:
  the compiler emits a fixed-width interface, qwen's single blood-pressure concept
  and codex's blood-pressure-plus-zeroed-blood-cell-counts land on identical
  matrices, so XGBoost returns identical predictions.  It does mean the proposer
  comparison measures nothing on those endpoints.
- M5's exclusion is endpoint-independent: **13/13 endpoints, identical missing
  fraction 0.696236** on `c_003` (blood pressure) target side vs the 0.50 frozen
  threshold.  Changing the endpoint cannot rescue M5; only a different bank could,
  and choosing one after the fact is selection on outcome.

## 5. Remediation, in order

1. **Add `LEAKAGE_BLOCKS` to M3** mirroring the M4/M5 criterion, and re-run all
   three rungs.  Minimum blocks: CBC family (`hemoglobin` <-> `hematocrit` <-> `rbc`),
   blood pressure (`sbp` <-> `dbp`), glucose metabolism (`glucose` <-> `hba1c`).
   M3 launchers carry no attestation flag, so an assistant may run this.
2. **Decide and apply the same rule for M1/M2**, then re-run.  This is the check
   that settles section 3's hypothesis.  Before re-running, read the M1/M2 base
   feature list the way section 3 did for M3: if Base already carries HbA1c when
   predicting glucose, the Auto-C advantage is representational; if it does not,
   Auto-C is injecting the single strongest predictor.
3. **Verify M6's forbidden set** -- not yet read.
4. Report pre-fix and post-fix numbers **both**.  The fix was written after the
   results were seen; that must be disclosed.  It is a consistency repair of an
   already-declared criterion, not outcome selection, and saying so plainly is the
   defence.
5. Put the per-endpoint decomposition in the paper body.  A reviewer finds this in
   five minutes; it is far better volunteered than extracted.

## 6. What this does not overturn

The reproducibility results stand: L0 re-runs matched pre-edit numbers exactly,
2-arm and 5-arm runs agreed to 17 digits, bootstrap CIs were identical.  The
issue is what the endpoints mean, not whether the pipeline computes them stably.

## 7. The remembered "+0.211" is raw RMSE, not the primary estimand

`experiments/crta_v3_medical_carte_confirmatory_v1_summary/RESULTS.md` reports the
same M1/M2 contrast on four metrics:

| metric | Auto-C vs Base | 95% CI | win |
|---|---:|---|---:|
| **nrmse** | **+0.008244** | [0.002477, 0.017721] | 0.900 |
| rmse | +0.211053 | [0.072762, 0.378903] | 0.900 |
| mae | **-0.015757** | [-0.321306, 0.198493] | 0.767 |
| r2 | +0.012003 | [0.003455, 0.025332] | 0.900 |

The number carried around as the project's strong early result, `+0.211053`, is
**unnormalized RMSE pooled across endpoints in different units** (mg/dL, cm).  On
the declared primary estimand -- query-SD-normalized RMSE -- the same contrast is
**+0.008244**, which sits between M6 (+0.006925) and M3 (+0.016580) and *below*
M4 (+0.052828).  On MAE the mean gain is negative and the interval crosses zero.

So part of "where did the early gain go" is that it was never that large on the
scale the paper actually reports.  The rest is section 3's proxy hypothesis.

## 8. Source budgets are not matched across architectures

Same file, footnote: "CARTE uses 8,192 deterministic source rows, while the
primary XGBoost CRTA run uses all source rows."  Every
`descriptive_cross_architecture` contrast therefore compares methods with
different information, which is why they are labelled descriptive.  CARTE's own
multitable transfer is *negative* against its target-only floor
(nrmse -0.206368 [-0.438220, -0.029633]).
