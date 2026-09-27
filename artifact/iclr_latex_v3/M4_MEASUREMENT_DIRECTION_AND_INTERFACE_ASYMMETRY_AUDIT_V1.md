# M4 measurement-direction audit, and what it turned up instead

Audited 2026-08-19 (evening session). Question posed by the measurement-layer
handoff (`context/short_term_handoff_20260819_measurement.md` §5): M4
(HRS→KLoSA) applies no measurement treatment — no recode/harmonize/rescale in
`scripts/crta_v3_m4_hrs2klosa_runtime_v1.py`, sidecar masks only sentinels
`[-9,-8,-7,-1]` — yet it carries the project's one separated positive
(**+0.052828 nRMSE**, lower-is-better metric, gain = Base − Auto-C, L2/llama4_scout).
If HRS and KLoSA code equivalent items in opposite directions, that positive
was obtained without measurement alignment and its interpretation changes.

**Compliance note.** Everything below was derived from code, configs, public
codebook documents, aggregate value-count histograms, and aggregate
performance summaries. No person-level value, row, identifier, or row-level
prediction was accessed (the `predictions.csv` files were never opened).

## 1. Direction verdict: concordant. No polarity inversion anywhere.

The accepted llama4_scout M4 bank
(`experiments/crta_v3_all_llm_all_task_utility_v1/primary_banks/llama4_scout/M4/decision_ledger.json`)
has two concepts:

| concept | HRS members (source) | KLoSA members (target) |
|---|---|---|
| `adl_difficulty` (c_001) | `adl5_difficulty_count`, `adl6_difficulty_count` | `wwc201`–`wwc205` |
| `mobility_difficulty` (c_002) | `mobility_difficulty_count` | `wwc209`, `wwc210` |

**HRS side** (RAND codebook windows,
`method_contract/v1/.../source_hrs_rand_full_selected_windows.txt`):
`RwADL5A` "Any Diff — sum of ADLs /0-5", `RwADL6A` /0-6, `RwMOBILA`
"Any Diff — sum of Mobility measures /0-5". Counts of tasks with difficulty;
**higher = worse**.

**KLoSA side** (`method_contract/v1/medical_documents/v1/native_sources/klosa/klosa_wave9_structured_codebook.xlsx`,
sheet `C.건강 상태`): every item C201–C217 is
"일상생활의 주변 도움 필요정도\_..." coded **1 = 도움 필요 없음, 3 = 부분적인
도움, 5 = 전적으로 도움 필요함**; **higher = worse**. Wave uniformity was
verified on the sidecar with aggregate code histograms only: all 7 member
columns contain exactly {1,3,5} in **all 9 waves** (e.g. `wwc201`:
1→67,289, 3→1,195, 5→788 of 69,272 rows).

So: same direction on both sides, same direction within every member set.
The scale difference (0–5/0–6 count vs {1,3,5} item codes) is absorbed by the
compiler's per-member robust standardization
(`method_contract/v1/compiler/compile_bank.py:29-41,106-108` — median/IQR with
std fallback, no sign logic), which is monotone, so no reverse-coding
machinery is needed *for this bank*. The absence of measurement treatment in
the M4 runtime is **not** a direction bug.

Two caveats worth keeping:

- **The proposer never saw the value coding.** The KLoSA registry rows carry no
  semantics ("target-side raw KLoSA schema field represented across waves by
  wWC201") and the materialized doc pack kept only variable name + Korean item
  label (`context_lines: 0`), dropping the 1/3/5 value labels. Direction
  concordance here is luck of the survey conventions, not something the
  pipeline checked or the model was given.
- **c_002 is semantically loose.** Its KLoSA members `wwc209`/`wwc210` are
  IADL items (집안일, 식사준비), not mobility; the runtime's own frozen
  component map puts KLoSA mobility at `wwc205/212/213`. Direction-concordant
  severity proxies, but not a mobility↔mobility correspondence.

## 2. The bigger finding: the positive sits where the target interface is switched off

Per-endpoint blocking was read from executed run artifacts
(`coret_private/crta_v3/m4_hrs2klosa_auto_c_v1/<endpoint>/support_01pct/seed_70/auto_c/llama4_scout/compiler_manifest.json`)
and per-endpoint gains from the L2 summary
(`m4_hrs2klosa_auto_c_v1__uncapped_summary/endpoint_gains.csv`). When a
concept has any member in the endpoint's forbidden set, the compiler zeroes
**all four of its channels on that side** (`compile_bank.py:120-127`),
including `observed_fraction`.

nRMSE gains (llama4_scout, L2), with concept status source→target:

| endpoint | gain | win | c_001 adl | c_002 mobility |
|---|---:|---:|---|---|
| `mobility_difficulty_count` | **+0.30521** | 1.00 | active→**BLOCKED** | blocked→blocked |
| `adl6_difficulty_count` | +0.05226 | 1.00 | blocked→blocked | active→active |
| `gross_function_limitation` | +0.04688 | 1.00 | active→**BLOCKED** | blocked→blocked |
| `adl5_difficulty_count` | +0.04446 | 0.93 | blocked→blocked | active→active |
| `iadl5_difficulty_count` | +0.02914 | 1.00 | active→active | active→**BLOCKED** |
| `grip_strength_max` | +0.00217 | 0.73 | active→active | active→active |
| `grip_strength_right` | −0.00099 | 0.17 | active→active | active→active |
| `grip_strength_left` | −0.00138 | 0.10 | active→active | active→active |
| `cesd_score` | −0.00230 | 0.30 | active→active | active→active |

The same structure holds at L0 (mobility +0.11178 top, grips/cesd ≈ 0).

Read off the table:

1. **74.1% of the positive mass (mobility + gross_function) sits on endpoints
   where every target-side concept channel is identically zero.** On those
   endpoints the Auto-C interface carries *no information at all* on KLoSA
   rows — whatever the +0.305 is, it is mechanically incapable of being
   cross-schema semantic transfer, and the §1 direction question is moot
   there.
2. On those endpoints the nonzero-on-source / zero-on-target channels are a
   near-perfect **domain indicator**: c_001's `observed_fraction` is ≈1 on
   every HRS row and exactly 0 on every KLoSA row. A tree model trained on the
   pooled set (source + 10×-weighted target support) can split on it once and
   fit the target support essentially separately — a mechanism that needs no
   semantics and no measurement alignment, and that fits the ladder shape
   already in `M4_CONTROL_LADDER_PREREGISTRATION_V1.md` §1 (Base degrades
   with more source, Auto-C flat).
3. Endpoints where the interface is genuinely live on both sides (3× grip,
   cesd) show ≈0 or negative gains. Binary endpoints echo this weakly
   (walk_block/chair positive, both-sides-active chronic/depression negative).
4. The residual ~20% (adl5/adl6, +0.044/+0.052) is the one place a real
   transfer claim could live: c_002 is active on both sides and
   direction-concordant (§1). Even there a softer separator exists — c_002 is
   single-member on source, so its `std`/`range` channels are identically 0 on
   HRS rows and variable on KLoSA rows.

## 3. Consequence for the frozen control ladder — read before launching

The pre-registered arms (`M3_M6_OUTCOME_BLIND_CONTROL_FREEZE_V1.json`, status
`frozen_metadata_only_no_control_banks_materialized`; verdict table in
`M4_CONTROL_LADDER_PREREGISTRATION_V1.md`) randomize concept membership
(`matched_random_concept`) or target binding (`wrong_auto_binding_concept`).
Randomized members will usually **miss the forbidden sets**, so those arms
lose the deterministic target-side zeroing — i.e. they lose the domain
indicator *along with* the semantics. Note the causal chain in the real bank:
the binding is semantically correct **⇒** its target members are exactly the
endpoint's own raw components **⇒** they are forbidden **⇒** the concept zeroes
on target **⇒** the indicator exists. A lesioned binding breaks the chain at
step 1, so under the domain-indicator mechanism the controls fail to
reproduce the gain and the frozen verdict table reads that as "specificity
emerges with source budget" — upgrading the semantic claim on the strength of
an artifact.

(The `wrong_auto_binding_concept` 0/3 standing quoted in the preregistration
§3 is from the **M1/M2 nh2kn** specificity follow-up
(`experiments/crta_v3_medical_concept_specificity_followup_v1/`), not from
M4. No M4 control arm has ever been executed.)

**Recommendation (decision is the licensed user's; nothing here was run):**
before launching the ladder, amend the freeze with one cheap discriminating
arm — `base` plus a single explicit `is_target` indicator column (or
equivalently, a control whose per-endpoint blocked/active pattern is forced to
match Auto-C's exactly). If base+indicator reproduces the
mobility/gross_function gains, the 74% share is explained without semantics;
if it does not, the domain-indicator reading is dead and the existing verdict
table stands. Freeze the amended rule *before* any control result is read,
per project policy.

## 4. What this does not overturn

- Direction concordance (§1) stands on public documentation and aggregate
  histograms; it makes the adl5/adl6 share *interpretable*, not artifactual.
- The reproducibility of the M4 numbers is untouched; this is about what the
  endpoints mean, exactly as in
  `ENDPOINT_CONCENTRATION_AND_LEAKAGE_BLOCK_AUDIT_V1.md` §6.
- Nothing here required or touched person-level data.
