# Pre-registration: survey-label measurement panel (M1/M2), v1

Declared 2026-08-19 ~23:20, **before any cell has been executed.** Follows
the ladder result (`M1M2_LAYER_LADDER_PREREGISTRATION_V1.md` adjudication):
measurement separated from its placebo only on the survey-dependent thin
surface and was crowded out by clinical proxies. This panel puts the
measurement conflict where it cannot be crowded out: **on the training
labels themselves.**

## 1. Question

Cross-cohort transfer of survey endpoints requires the *label coding* to be
aligned (NHANES `DIQ010` 1=yes/2=no vs KNHANES `de1_dg` 0=no/1=yes is a
polarity inversion in the label). No feature treatment can compensate a
mis-mapped training label. Does a measurement table — the pipeline's, the
LLM's — earn its keep there, against a capacity-matched wrong table?

## 2. Design

- Benchmark `std_cross_nh2kn_shared_anchorreset_fewshot_v1`, feature set
  `shared_clinical_plus_survey_v1`, **default (pipeline-harmonized)
  features, identical in every arm** — only the training-label mapping
  varies. The builder drops the endpoint's own slot from X (asserted).
- Injected targets (raw codes, untouched by questionnaire rules):
  `diabetes_history` (DIQ010 / ALL__de1_dg), `hypertension_history`
  (BPQ020 / ALL__di1_dg), `current_smoking_status` (SMQ040 / ALL__bs3_1).
  `education_level` is excluded (known-wrong key row, non-binary), `sex`
  excluded (no conflict).
- Seeds 50–59, support K ∈ {64, 256, 1024}, **primary K = 256**. Backbone
  XGBRegressor hist d6 n300 on the mapped label values; **metric AUROC on
  target queries (higher is better)** — rank-based, so any monotone label
  scale is admissible per arm.
- **Evaluation label, fixed across arms**: the codebook-documented
  target-side map (`de1_dg`/`di1_dg` 1→1, 0→0; `bs3_1` 1,2→1, 3,4→0; all
  else masked and excluded from AUROC). This is the audit-verified KNHANES
  side, not the contested education row.
- Per arm, training rows (source and support) whose mapped label is NaN are
  dropped; weights: kept source rows 1, kept support rows
  n_source_kept / n_support_kept.

## 3. Arms (training-label maps)

| arm | map |
|---|---|
| `raw` | identity — the polarity inversion lives in the labels |
| `pipeline_table` | transcribed operative rules: DIQ010 {1→1, 2→0}, de1 {1→1, 0→0}, BPQ020 {1→1, 2→0}, di1 {1→1, 0→0}, SMQ040 {1,2→1, 3→0}, bs3_1 {1,2→1, 3,4→0}; else NaN |
| `llm_table` | `canon_v1` of the isolated session's documented extraction (majority of s1–s3), identical translation to the ladder's rung 3: valid codes min–max to [0,1], orient iff reverse-flag or higher_is_less, else NaN |
| `placebo_table` | capacity-matched to `llm_table`: per item, pool = LLM valid ∪ sentinel, mask \|sentinel\| random codes, assign the true canonical output multiset to survivors by uniform permutation (identity included); redrawn per (target, seed) |

## 4. Pre-declared directional prediction (the confirmatory content)

The LLM extraction flags 1=Yes/2=No binaries as reverse-coded
(`BPQ020`, `SMQ040`, `bs3_1` rev=true) but not `DIQ010` (rev=false,
majority). Mechanically, canon therefore **fixes the polarity for
hypertension and smoking and leaves diabetes inverted.** Prediction, frozen
now: per-target `llm_table − pipeline_table` AUROC has a 95% CI containing
0 for hypertension and smoking, and a CI **below 0 for diabetes**. Any
other pattern falsifies the mechanical-translation account.

## 5. Adjudication (frozen)

AUROC gain = arm − reference (**positive = arm better**; note the sign
flip vs the nRMSE experiments). Hierarchical bootstrap (targets then
seeds, 10,000 reps, seed 20260819) at K = 256 over 30 pairs; separation =
mean > 0 ∧ CI₉₅ excludes 0 ∧ win ≥ 0.60 ∧ mean > 0 with the best target
dropped (here: over the remaining 2).

| # | contrast | role |
|---|---|---|
| A1 | `llm_table` vs `placebo_table` | primary verdict |
| A2 | `pipeline_table` vs `placebo_table` | secondary verdict |
| A3 | `llm_table` vs `pipeline_table`, per target | the §4 prediction check |
| — | `raw` vs everything | descriptive only (no verdict words) |

Per-target decomposition is mandatory in every report.

## 6. Execution

Runner `scripts/run_crta_v3_survey_label_panel_v1.py`, summarizer
`scripts/summarize_crta_v3_survey_label_panel_v1.py`, both committed with
this document before launch. 30 cells, 1 build + 12 fits each; 3 shards ×
2 threads alongside the tail of ksup v2 (per the standing instruction to
run on the local CPU now). NHANES/KNHANES only; no GPU.
