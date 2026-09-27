# Pre-registration: E2 — NHANES questionnaire value tables acquired; open-model measurement extraction and three-endpoint replication, v1

Drafted 2026-08-25; to be freeze-committed before any open-model
generation on the v3 prompt.

## Motivation and prior observation disclosure

The manuscript's automated-pipeline claim is supported in the main text
only for the relation component in hydrology.  Clinical measurement
extraction has been attempted at length and is known to fail on the
NHANES side for a documented reason: the NHANES questionnaire codebook
value text (DIQ010, BPQ020, SMQ040) was never available to the frozen
pipeline — the governed CDC snapshot of 2026-08-05 excluded questionnaire
components — so every open model in the 8-model panel returned
`valid_codes: []` for those items and 0/7 reverse-coding flags in all
four prompt variants; the closed-model v2 session flagged them only on a
`basis: prior`.  The KNHANES side extracted at .33–.89 valid-code rates.
All of this is known.

On 2026-08-25, with the user's authorization, the three official CDC
pages (DIQ_J, BPQ_J, SMQ_J; 2017-2018) were acquired **through the
governed resolver** (`fetch_nhanes_cdc_documents_v1.py`; host allowlist
wwwn.cdc.gov; admission satisfied by the locally present XPT files;
SHA-256 ledger; snapshot
`outputs/nhanes_cdc_official_snapshot_questionnaire_20260825_v1`, 3/3
verified, 0 failures) and their value-table TEXT extracted with the
frozen extractor (`extract_nhanes_value_tables_v1.py`; 99 variables).
This experiment asks whether open-weight models, given the same frozen
prompt with the NHANES value text now present, (i) produce the reverse
coding the documentation determines and (ii) produce a measurement table
that replicates the three-endpoint label-polarity result when consumed
by the frozen label-panel interface.

## Frozen design

- **Prompt v3** = the frozen v2 prompt (sha `d0ec7ec0…`) with the four
  NHANES questionnaire items' `codebook value text: (none available)`
  lines (DIQ010, BPQ020, SMQ020, SMQ040) replaced by the extracted CDC
  value-table text; nothing else changes (diff recorded;
  `experiments/crta_v3_measurement_layer_v1/harmon_prompts_v3/`).  The
  system prompt is the knowledge panel's.  Artifact
  `artifact_meas_nhkn_v3.json` carries `schema_pair_id` and hashes.
- **Models**: the single-GPU members of the frozen open panel at their
  locked revisions — Qwen3-32B, Qwen3-8B, gemma-3-27b-it,
  medgemma-27b-it, medgemma-4b-it, Olmo-3.1-32B-Instruct, and Qwen3-14B
  if its cached snapshot is present.  Llama-4-Scout is excluded (needs
  two GPUs; recorded as not run).  Greedy decoding, one generation each,
  `run_frozen_prompt_hf_v2_panel.py` unchanged, on anonymous GPUs 1 and
  2 only (the runner accepts devices 1–3; GPU 3 is excluded by user
  instruction; GPU 0 is not selectable by the frozen runner).
- **Scoring** (per model, frozen scorer semantics): valid-code exact
  match against the key for the six label items; `requires_reverse_coding`
  (or `ordinal_direction == higher_is_less`) for NHANES DIQ010, BPQ020,
  SMQ040; `basis` field counts.
- **Downstream**: for every model whose response parses and yields
  non-empty `valid_codes` for all six label items, its table is
  materialized by the frozen label-panel canon (single sample; the
  2-of-3 majority degenerates to that sample) and the three-endpoint
  survey-label panel is refit for the `llm_table` arm only
  (NHANES→KNHANES, seeds 50–59, K=256, XGBoost), with `raw`,
  `pipeline_table` and `placebo_table` read from the frozen
  `experiments/crta_v3_survey_label_panel_v1` cells (same seeds, K,
  builder, parquets).  Executed on the server CPU (identical builder
  tree and parquets; pinned environment).

## Adjudication (frozen)

- **E2-P1 (documentation determines reverse coding):** at least one
  model flags reverse coding for all three of DIQ010/BPQ020/SMQ040 with
  `basis: documentation`; the count of models doing so is reported
  against the prior 0/7.
- **E2-P2 (replication):** for each materializable model, A1 =
  AUROC(llm_table) − AUROC(placebo_table) over the 30 paired cells —
  mean > 0, CI95 low > 0 (10,000 reps, seed 20260819 as the frozen
  panel), win ≥ .60.  Verdict = at least one open model separates; the
  number that separate is reported.
- **E2-P3 (descriptive):** A3 = AUROC(llm_table) − AUROC(pipeline_table)
  per model; the diabetes-endpoint value in particular, against the
  closed-model v1 penalty of −.704.
- Models that fail to parse or leave any label item's `valid_codes`
  empty are reported as such, not dropped silently.

Interpretation map, declared now:

- E2-P1 ∧ E2-P2 → the measurement component is automatable from the
  same codebook pages for at least one open model; the main-text scope
  can say so (with the model count).
- E2-P1 passes, E2-P2 fails → reverse coding is recovered but the
  materialized table does not replicate; report which item broke it.
- E2-P1 fails with the value text present → the earlier failure was not
  (only) document absence; the automation claim is scoped to the
  relation component and the KNHANES measurement side.

## Execution

Prompt/artifact builder
`scripts/build_crta_v3_measurement_extraction_prompt_v3_questionnaire_v1.py`;
panel runs via the frozen `scripts/remote/run_frozen_prompt_hf_v2_panel.py`
queued per GPU; scoring and downstream scripts named in the addendum
below.  Committed with this document before any generation.

## Frozen artifact hashes (recorded before commit)

v3 prompt sha256 `b7ade1e1f2fc2cfa78d0f5c3bf51a86262638f2278365253360f7cde841f120a`
(5,865 chars; substituted items DIQ010, BPQ020, SMQ020, SMQ040); value
tables sha256 `542c1b30d92e61cca95e9f8bd55b7c2959ab80cab370a29671c3ce7820d0760f`.
Qwen3-14B cached snapshot `40c069824f4251a91eefaf281ebe4c544efd3e18` is present and included.
GPU queues wait until the assigned GPU reports < 2 GB used before starting.

## Addendum — downstream scripts (written before any generation completed)

Scorer `scripts/score_crta_v3_e2_open_panel_v1.py` (E2-P1); per-model
`llm_table` arm runner `scripts/run_crta_v3_e2_label_panel_llm_arm_v1.py`
(frozen panel runner with `LLM_RESPONSE_DIR`/`LLM_SAMPLES`/`ARMS`
overridden; non-materializable tables recorded, not dropped); adjudicator
`scripts/summarize_crta_v3_e2_open_panel_v1.py` (E2-P2/P3 against the
frozen `crta_v3_survey_label_panel_v1` cells).  GPU queue
`scripts/remote/e2_gpu_queue_v1.sh` (GPU 1: Qwen3-32B, Qwen3-8B,
medgemma-4b, Qwen3-14B; GPU 2: gemma-3-27b, medgemma-27b, Olmo-3.1-32B;
starts only when the GPU reports < 2 GB used).

## Addendum 2 — declared format repair (2026-08-25, after the first three responses)

Qwen3-32B's response parsed under strict JSON but carried a JSON `null`
inside one `missing_or_sentinel_codes` list, which the frozen canon's
`float()` rejects.  This is a format defect, not a content one; following
the project's "format is recoverable, content is not" rule, the E2 wrapper
now drops `null` entries from code lists before the frozen canon runs and
records the count in `E2_PROVENANCE_V1.json`.  Empty `valid_codes` remain
non-materializable.  Olmo-3.1-32B omitted `KNHANES::ALL__di1_dg` entirely
and stays non-materializable (content).  Applied to all models uniformly;
gemma-3-27b and medgemma-27b are unaffected (no nulls) and are not refit.
