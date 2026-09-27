# Pre-registration: M1/M2 measurement-harmonization ablation (v1)

Declared 2026-08-19, **before any cell of this experiment has been executed.**
Metric: query-SD-normalized RMSE (**nRMSE, lower is better**). Verdicts are
frozen here; the summarizer implementing them is
`scripts/summarize_crta_v3_measurement_harmonization_ablation_v1.py`, written
together with this document and before any run.

## 1. Why the previous design was invalid, and what replaces it

`scripts/run_crta_v3_measurement_survey_v1.py` (never launched) transformed
target-cohort survey values *after* the benchmark build. That design assumed
the benchmark leaves survey values raw. It does not: the builder applies the
questionnaire harmonization table before any method sees a row —
`load_questionnaire_rule_index()` at
`nhanes_knhanes_concept/tasks/standard_benchmark/current/scripts/build_benchmark_table.py:317`
(the operative table is
`relation_sources/common/artifacts/questionnaire_seed_bundle_v1/executable_item_rules.csv`,
12 rows; the 17-row `questionnaire_value_harmonization_rules_v1.csv` is its
source document). So the old `sentinel_doc` arm was a no-op and `align_full`
re-transformed already-aligned values.

This experiment instead **ablates the harmonization inside the builder**. The
rule index is injected per arm at that single call site; everything else
(splits, support draws, model, metric) is shared across arms.

## 2. Task, cells, backbone

- Benchmark `std_cross_nh2kn_shared_anchorreset_fewshot_v1` (NHANES→KNHANES),
  feature set `shared_clinical_plus_survey_v1` (12 clinical slots + `sex`,
  `education_level`, `diabetes_history`), target set
  `objective_anchor_targets_v1_safe`.
- Targets: glucose, waist_cm, triglycerides, sbp, dbp, total_cholesterol.
- Seeds 50–59; support rows K ∈ {64, 256, 1024}; **primary cell K = 256**
  (matches the ksup program's adjudication choice).
- Backbone: XGBoost hist, d6, n300, lr 0.05 — identical config in every arm.
- Data: same SHA-256-pinned parquets as every other M1/M2 experiment
  (NHANES `345163df…`, KNHANES `34762e6e…`).

The three survey slots bind six harmonization rows: `RIAGENDR`/`ALL__sex`,
`DMDEDUC2`/`ALL__educ`, `DIQ010`/`ALL__de1_dg`. Raw-side conflicts on record:
`DIQ010` {1=yes,2=no} vs `de1_dg` {0=no,1=yes} polarity inversion; education
5-level vs 8-level scales; KNHANES sentinel 8/9 mass.

## 3. Arms

All arms are **tables**, expressed in one spec formalism
(`identity` = numeric passthrough; `map` = {input code → output value},
everything unlisted → NaN) and applied identically to *both* cohorts by the
builder. The spec interpreter replaces `recode_questionnaire_series`; the
per-arm index replaces `load_questionnaire_rule_index`.

| arm | table |
|---|---|
| `raw` | empty index — harmonization ablated, conflicts live (inline manifest harmonization verified absent for all 15 feature slots at startup) |
| `pipeline_table` | the six operative rows exactly as the benchmark applies them today (specs transcribed from `recode_questionnaire_series`) |
| `llm_table` | the table the isolated session produced (documented arm, canary-verified; `experiments/crta_v3_measurement_layer_v1/harmon_responses_v1/raw_documented_s{1,2,3}.txt`) under the frozen translation of §4 |
| `placebo_table` | capacity-matched wrong table, generated per (target, seed) by the frozen procedure of §5 |

`pipeline_table` is **not** treated as gold: its `KNHANES::ALL__educ` row is
known-wrong (`iclr_latex_v3/HARMONIZATION_KEY_AUDIT_V1.md` — declares 1..8 +
88/99 on data that contains 0 and 9 and no 8/88/99). The arm measures the
table the benchmark actually uses, as-is.

**Mandatory preflight (before any training cell):** with the interpreter
active and `pipeline_table` injected, the built bundle (X_train, X_test,
y_train, y_test) must be **exactly equal** to the unpatched default build for
one probe cell (glucose, seed 50), and the `raw` build must differ from it on
at least one survey column. Failing either aborts the experiment.

## 4. Frozen llm_table translation (mechanical, no human patching)

From the three documented-arm samples, per item take the **field-wise majority
across s1–s3** (2-of-3; if all three disagree, sample s1 — recorded in the
materialized artifact). Then per item:

- every code in `valid_codes` maps to itself;
- if `requires_reverse_coding` is true, map v → (min+max of valid_codes) − v
  instead (any response type — the convention-boundary disagreement is applied
  as stated, not adjudicated away);
- everything else (including all `missing_or_sentinel_codes`) → NaN.

No cross-cohort collapse and no polarity map is synthesized on the model's
behalf: the model's table contains none, and that capability difference is
exactly what the arm measures. (Known consequences, recorded before running:
`ALL__educ` valid=[1..4] masks real education codes 5–7; `DIQ010`
valid=[1,2,3] keeps borderline 3 and leaves the polarity inversion in place.)
The materialized table is written to the experiment root before training.

## 5. Frozen placebo generator

Capacity-matched to `pipeline_table`, drawn per (target, seed) with
`rng = default_rng(sha256("placebo_v1|{target}|{seed}|{cohort}|{item}"))`,
independently per item row:

- code pool P = the row's documented `valid_codes` ∪
  `missing_or_sentinel_codes` (from the executable CSV);
- draw |sentinel| codes from P without replacement → masked to NaN;
- assign the multiset of the pipeline row's output values to the surviving
  codes by a **uniform random permutation, identity included** (the placebo is
  a uniform draw from the same structural family; content, not surgery kind or
  amount, is the only difference);
- identity rows (sex) have an empty sentinel set: the permutation is over
  {1,2} and may swap the coding in one cohort but not the other.

## 6. Verdict rules (frozen)

Primary comparisons are **against `placebo_table`**, not against `raw`. Gain =
placebo_nRMSE − arm_nRMSE (positive = arm better). At K = 256 over the 60
(target × seed) pairs, hierarchical bootstrap (resample targets, then seeds;
10,000 reps, seed 20260819):

| # | comparison | separated iff |
|---|---|---|
| V1 | `pipeline_table` vs `placebo_table` | mean gain > 0, 95% CI excludes 0, win ≥ 0.60, and mean gain stays > 0 with the single best target dropped |
| V2 | `llm_table` vs `placebo_table` | same rule |
| V3 (secondary, descriptive) | `pipeline_table` vs `llm_table` | report mean, CI, win; no verdict word |

**Insensitivity gate, adjudicated first:** if |mean(`pipeline_table` −
`raw`)| < 0.001 nRMSE at K=256, the survey block does not move these
endpoints at all and the outcome is recorded as **"testbed insensitive —
not evaluable"**; V1/V2 are then reported as numbers but carry no
interpretation. This is declared now so a null cannot be re-read post-hoc as
"the table has no value".

Interpretation map, declared now: V1 yes & V2 yes → measurement content
matters and the model's sentinel/validity knowledge alone captures it. V1 yes
& V2 no → the value is in the hand-authored cross-cohort mapping, which the
model did not produce. V1 no → the pipeline's own table does not beat a
random member of its structural family on these endpoints; no measurement
claim of any kind survives on this testbed. `raw` is context, never the bar.

## 7. Execution constraints

- Runner: `scripts/run_crta_v3_measurement_harmonization_ablation_v1.py`
  (assistant-executable; no licensed-user attestation flag involved, CPU
  only, no HRS/KLoSA data touched — NHANES/KNHANES only).
- **Do not launch while the ksup v2 shards are running** (5 shards, ETA
  ~00:15); load is already 21/20 cores.
- Cells are cached (`metrics.json` present ⇒ skipped); safe to kill and
  resume. Logs under `logs/crta_v3_measurement_harmonization_ablation_v1/`.
