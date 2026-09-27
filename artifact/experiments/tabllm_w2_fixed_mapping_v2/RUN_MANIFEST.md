# Active W2 fixed-mapping campaign

User's revised design supersedes the 24-way cross. Use exactly canonical
`ref_00` with R1 `feature_001...`, R2 `Field A...`, R3 `Variable A...`.
Nine datasets, supports 0/4/32/512, seeds 42/1024/0/1/32. Optional additional
zero-shot mappings are excluded. Reference cells: 540; shared intended: 180;
new R2/R3 cells: 360, of which 270 are adaptation fits.

The superseded v1 supervisor and its orphaned audit child were stopped on
2026-09-10 at 14:06:44 UTC. It generated zero new prediction files. Its
design, failed-audit correction and logs remain preserved.

The user explicitly approved copying/running code and design on anonymous
(61.107.200.104) within `external/tabllm_w2_lexical_v1`. V2 stays inside
that approved root:

- Code: `scripts/tabllm_w2_fixed_mapping/`.
- Output: `experiments/tabllm_w2_fixed_mapping_v2/`.
- Protocol: `iclr_latex_v3/TABLLM_W2_FIXED_MAPPING_FREEZE_V2.md`.
- Shared W4 margin: .02 AUROC, frozen before both versions.
- Supervisor PID at launch: 905625; consult STATUS.json for current state.
- Runtime: original `external/tabllm_3arm_v1/env/bin/python`.
- GPU: 2; other occupied GPUs are untouched, GPU 1 excluded.

Sequence: freeze -> all-input audit -> first-epoch timing only -> zero-shot
evidence -> paired primary analysis -> support 4/32/512 -> full analysis.
Audit failure or runtime errors stop the pipeline with an explicit status;
no scientific choices are changed automatically. Evidence cells use an atomic
lock and can resume after checking frozen hashes and cached prediction hashes.

Timing-only first epoch uses bank/R2/ref_00/seed42 at n_adapt=512 (128 steps),
with no evaluation. It never counts as evidence; all full fits reset the
initial IA3 state and seed. `timing_only/FIRST_EPOCH.json` records measurement.
Historical same-runner timing projects 27.1 hours for the 270 new adaptation
fits on one GPU, excluding zero-shot, audit, model loading and analysis.

Validation before new outcomes: six unit tests passed; a synthetic 720-cell
full-pipeline check passed including overlapping-row bootstrap, multiclass
AUROC, exact utility cancellation, endpoint interactions and output generation.
The outcome-blind previous-artifact preflight found all 1,485 candidate cells
match the current source tree, base execution code and package versions.
V2 additionally checks each reused cell's support prompts, test prompts,
memberships, IA3 checkpoint and probabilities' hash before accepting it.

Artifacts: FROZEN_DESIGN.json; AUDIT_SUMMARY.json; per-dataset audit/mapping
and memberships; per-cell evidence; primary_analysis and full_analysis with
CSV/JSON/Markdown summaries and paired bootstrap arrays; logs and STATUS.json.

Provenance: **reference lexical-realization robustness; design frozen before inspecting these outcomes**.

No manuscript result has been changed. Generic-reference robustness does not
itself prove that the prompts are in-distribution.

## Confirmed launch observations

All nine datasets passed the audit: 116,198 distinct dataset rows in four
conditions, zero truncation; maximum R1/R2/R3 input lengths 249/210/230.
Design SHA256: `5cdac31d67a015ebca58c1f61ac5f150b842e88eced1d18b254345199302899b`.
First bank/R2 512-support epoch completed in 33.7508 seconds (128 steps);
model loading took 62.012 seconds. Projected new training is 27.09 GPU-hours;
full elapsed estimate 28--32 hours, conditional on successful baseline reuse
and similar execution speed. Primary evidence started at 14:13:30 UTC
(23:13:30 KST) on 2026-09-10. Local five-minute backup watcher PID 645314 (execution session 63790).
The initial detached watcher PID 643449 did not persist and was replaced.
