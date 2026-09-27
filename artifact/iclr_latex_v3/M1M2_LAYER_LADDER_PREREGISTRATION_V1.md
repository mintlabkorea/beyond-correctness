# Pre-registration: M1/M2 layer ladder (column set → grouping → measurement), v1

Declared 2026-08-19 (late evening), **before any cell of this experiment has
been executed.** Metric: query-SD-normalized RMSE (**nRMSE, lower is
better**). The summarizer implementing every rule below is
`scripts/summarize_crta_v3_m1m2_layer_ladder_v1.py`, written and committed
together with this document.

## 0. What changed from the first draft, and why

The first draft was a cumulative base → +measurement → +concept → +relation
ladder. Three corrections, all adopted:

1. **The relation rung has nothing to run.** The current medical program
   banks carry empty relation sets (17/17), and the evidence-relaxation
   ladder (`experiments/crta_v3_evidence_ladder_v1/LADDER_REPORT.md`) shows
   **0 composed and 0 cross-schema relations at every rung R0–R4**, including
   the no-documentation ceiling; cross-model agreement on any relation is 0.
   The one legacy nh2kn relation (gpt-5.6-sol v1: `sbp − dbp`, single,
   intra-schema arithmetic) cannot support a rung. **Relation is declared
   not evaluable on these corpora** — a boundary statement, not an arm.
2. **A ladder without placebos is the exact shape that misreads artifacts as
   layers.** This program's history is that added structure loses to
   capacity-matched noise, and the M4 audit
   (`M4_MEASUREMENT_DIRECTION_AND_INTERFACE_ASYMMETRY_AUDIT_V1.md`) showed
   ~74% of the one separated positive is explained by a blocking-induced
   domain indicator. Every rung therefore gets a capacity-matched placebo,
   and a standing `base + is_target` arm carries the cheapest explanation.
3. **Measurement is likely a no-op on harmonized testbeds**, so the
   already-frozen M1/M2 harmonization ablation
   (`M1M2_MEASUREMENT_HARMONIZATION_ABLATION_PREREGISTRATION_V1.md`) runs
   **first** and its insensitivity gate governs rung 3's interpretability
   here.

## 1. Task and surface

NHANES→KNHANES (`std_cross_nh2kn_shared_anchorreset_fewshot_v1`), on the
**harmonization-ablated** slot surface: the builder's questionnaire rule
index is emptied (same injection point as the ablation experiment), so
survey values are raw and their conflicts are live. Targets: glucose,
waist_cm, triglycerides, sbp, dbp, total_cholesterol. Seeds 50–59; support
K ∈ {64, 256, 1024}; **primary K = 256**. Backbone: XGBoost hist d6 n300
lr 0.05, identical in every arm. Parquets SHA-256-pinned (NHANES
`345163df…`, KNHANES `34762e6e…`).

**Bank** (concept layer): the LLM-proposed nh2kn bank
`iclr_latex_v3/method_contract/v1/runs/proposer_bank_v2/models/gpt-5.6-sol/medical_nhanes_knhanes_full_documents_v2_attempt_02/decision_ledger.json`
(sha256 `cd1e230e…`, asserted at runtime). Its 4 concepts bind 9 raw columns
per side; all 9 bindings coincide with the manifest's slot pairing, so on
this surface the member columns are the slots:

| concept | member slots |
|---|---|
| body_measurements | height_cm, weight_kg, waist_cm |
| first_reading_blood_pressure | sbp, dbp |
| diabetes_test_measurements | glucose, hba1c |
| blood_lipid_measurements | total_cholesterol, triglycerides |

**Base slots** (never bank members): age, creatinine, rbc, wbc, hemoglobin,
hematocrit, sex, education_level, diabetes_history, hypertension_history,
current_smoking_status (11; the five survey slots enter **raw** except in
measurement arms). For endpoint e, the slot e is excluded from features and
from its concept's members **on both sides symmetrically** — no
source-active/target-blocked asymmetry can arise by construction, which is
why the M4-form interface-pattern-matched control is **n/a here** (it
remains required for M4-form tasks; that execution belongs to the licensed
user's control ladder, see
`M4_CONTROL_LADDER_PREREGISTRATION_V1.md`).

## 2. Layers, mechanically

- **column_set**: the 8 remaining member slots added as individual raw
  features.
- **grouping**: 4 channels per concept (mean / std / range /
  observed_fraction over robust-standardized members, clip ±10 — the exact
  channel math of `method_contract/v1/compiler/compile_bank.py`).
  Standardization parameters are fit per side: source params on source
  training rows, **target params on the K support rows only** (the M4
  convention), applied to support and query alike.
- **measurement**: the LLM-extracted table (documented arm, isolated
  session, field-wise majority of samples s1–s3) applied at the builder for
  the 10 survey items (5 slots × 2 cohorts), as the canonicalization
  `canon_v1`: codes outside `valid_codes` → NaN; orient v → (min+max)−v iff
  `requires_reverse_coding` or `ordinal_direction == higher_is_less`; then
  min–max rescale the valid range to [0,1]. Magnitude, direction, and
  dimension are thus explicit; no cross-cohort mapping is synthesized on the
  model's behalf (the model produced none — that capability boundary is part
  of what is measured).

## 3. Arms (10 fits per cell × K; one cell = target × seed)

| arm | composition |
|---|---|
| `rung0_base` | 11 base slots, raw |
| `rung1_columns` | rung0 + column_set |
| `rung2_grouping` | rung1 + grouping channels (true grouping) |
| `rung3_measurement` | rung2 with `canon_v1` applied to the survey slots |
| `pl_columns` | rung1 with the **target-side** member values permuted across member slots (derangement) — right capacity, wrong binding |
| `pl_grouping` | rung1 + channels from a random partition of the same members with the same size profile (≠ true partition) — right columns, wrong grouping |
| `pl_measurement` | rung3 with a capacity-matched wrong table: per item, pool = LLM valid ∪ sentinel; mask \|sentinel\| random codes; assign the true canonical output multiset to the survivors by uniform permutation (identity included) |
| `is_target` | rung0 + one 0/1 target-cohort indicator column — the standing cheapest explanation |
| `loo_columns` | rung3 minus raw member columns (grouping + measurement only) |
| `loo_grouping` | rung3 minus grouping channels |

`loo_measurement` ≡ `rung2_grouping` by construction and is reported as an
alias, not refit. All random draws derive from
`sha256("ladder_v1|<layer>|<target>|<seed>[|<item>]")`; redraw per (target,
seed).

## 4. Adjudication (frozen)

Hierarchical bootstrap (targets, then seeds; 10,000 reps, seed 20260819) at
K = 256 over the 60 pairs; gain = reference nRMSE − arm nRMSE. Separation =
mean > 0 ∧ CI₉₅ excludes 0 ∧ win ≥ 0.60 ∧ mean > 0 with the best target
dropped.

| # | contrast | reference |
|---|---|---|
| R1 | `rung1_columns` | `pl_columns` |
| R2 | `rung2_grouping` | `pl_grouping` |
| R3 | `rung3_measurement` | `pl_measurement` |
| D1–D3 | `rung{1,2,3}` | `is_target` — a rung "explains more than domain indication" only if separated here too |
| descriptive | marginals rung_k − rung_{k−1}; LOO vs rung3; is_target − rung0 | no verdict words |

**Gate coupling:** the M1/M2 harmonization ablation runs first. If its
insensitivity gate fires (|pipeline−raw| < 0.001 nRMSE at K=256), rung 3 and
R3 are reported as numbers with the fixed label **"measurement not
measurable on this testbed"** and carry no interpretation; a rung-3 claim
then requires a different task.

Every contrast is reported **per endpoint** alongside the member-drop
status for that endpoint (which concept lost which member, symmetric by
construction). No headline number without its per-endpoint decomposition.

Interpretation map, declared now: a rung that fails its R-contrast is
noise-equivalent at that capacity. A rung that passes R but fails D is
explained by domain indication. Only R ∧ D survives as a layer effect.
If `is_target` alone separates from `rung0`, the pooled-training mechanism
is confirmed present on this task family and every prior M1/M2 gain must be
re-read against it.

## 5. Execution

- Runner `scripts/run_crta_v3_m1m2_layer_ladder_v1.py`
  (assistant-executable, CPU-only, NHANES/KNHANES only; cells cached,
  kill/resume safe).
- Chain: `scripts/run_crta_v3_measurement_chain_orchestrator_v1.sh` waits
  for the ksup v2 shards to exit (~01:20), then (1) runs the harmonization
  ablation (3 shards × 4 threads) and its summarizer, then (2) runs this
  ladder (6 shards × 3 threads) and its summarizer. Nothing launches while
  ksup holds the machine.
- GPUs are not used anywhere in this chain. (Standing note for other work:
  on anonymous use GPUs 0, 2, 3 only; GPU 1 stays free.)
