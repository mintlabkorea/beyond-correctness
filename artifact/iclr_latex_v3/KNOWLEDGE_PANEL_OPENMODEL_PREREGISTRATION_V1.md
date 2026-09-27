# Pre-registration: open-model knowledge panel (G1)

Declared 2026-08-20 ~03:50, **before any generation has run.** The
long-GPU program the paper still needs: tonight's surviving knowledge
forms come from mixed sources (one closed-model extractor for
measurement/adjacency, a hand-frozen sign table). G1 extracts **the full
narrowing stack from an 8-model open panel** with frozen prompts, so the
paper's generality table — extraction quality and downstream survival
across models — exists, and the "all knowledge LLM-extracted" pipeline
becomes assemblable per model.

## 1. What is generated

Four frozen prompts (hashes in
`experiments/crta_v3_knowledge_panel_v1/prompts/ARTIFACT_MANIFEST.json`):

| prompt | content | reference key |
|---|---|---|
| `meas_nhkn_v2` | 17-item NHANES/KNHANES measurement extraction, v2 reverse-coding convention | the 17-row audited key |
| `meas_klosa_v2` | 42-item KLoSA measurement extraction, v2 convention | wave-9 codebook (valid codes) |
| `sign_v1` | **NEW**: marginal direction {−1, 0, +1} for all 66 (feature, target) clinical pairs — the missing all-LLM piece of the constraint stack | the frozen 7-pair table (subset) |
| `adj_v1` | concept-pair adjacency + ancestor {−1, 0, +1}, 6 pairs | — (cross-model agreement only) |

Models (all cached on anonymous): Qwen3-32B, Qwen3-14B, Qwen3-8B,
gemma-3-27b-it, medgemma-27b-it, medgemma-4b-it, Olmo-3.1-32B-Instruct,
Llama-4-Scout-17B-16E. **Greedy decoding, one generation per (model,
prompt)** — determinism replaces within-model sampling; agreement is read
ACROSS models (the evidence-ladder logic: convergence = the document
constrains; divergence = each model's prior). Runner: byte-identical copy
of the frozen `run_frozen_prompt_hf_v1.py` with only the `--cuda-device`
choices widened to (1, 2, 3) (`scripts/remote/run_frozen_prompt_hf_v2_panel.py`).
Scout may not fit a single B200 (109B total parameters); it runs last in
its queue and an OOM is **recorded as a result**, not retried.

## 2. Frozen predictions

- **G1-P1 (documentation constrains)**: on fields with supplied codebook
  text, cross-model agreement is high (valid-code sets: majority of
  models exactly matching the key on ≥ 80% of documented items); on
  prior-only fields (KNHANES `ALL__educ`, KLoSA sentinels) models
  diverge.
- **G1-P2 (the v2 convention transfers)**: a majority of models flag the
  1=yes/2=no binaries (`DIQ010`, `BPQ020`, `SMQ040`) as reverse-coded
  under the operationalized definition — the convention fix is not a
  single-vendor artifact.
- **G1-P3 (sign knowledge is textbook-grade)**: for the 7 hand-frozen
  pairs, a majority of models return the same nonzero sign with **zero
  flipped signs** across the panel; flips on those 7 falsify the "the
  constraint content is standard knowledge" reading.
- Downstream utility per model table (label-panel arm, sign-content arm
  vs placebos) is Stage B, CPU, adjudicated under the existing frozen
  rules after the generations return; it is declared here but its cells
  run tomorrow.

## 3. Execution and etiquette

anonymous **GPUs 1, 2, 3 only** (the user's current allocation; GPU 0
untouched), all four idle at launch. Three serial queues:
GPU1 Qwen3-32B → Qwen3-8B; GPU2 gemma-3-27b → medgemma-27b →
medgemma-4b; GPU3 Olmo-3.1-32B → Qwen3-14B → Llama-4-Scout(last).
8 models × 4 prompts, one process per (model, prompt); outputs
(`raw_response.txt` + `generation_manifest.json`) under
`~/coret_knowledge_panel_v1_20260820/runs/` and **pulled back to local
immediately on completion** (server logs sync rule). A local watcher
polls, pulls, and inventories; parsing/scoring runs locally afterwards.
