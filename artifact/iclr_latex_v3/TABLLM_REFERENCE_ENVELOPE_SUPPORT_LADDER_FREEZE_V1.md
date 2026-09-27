# TabLLM global-reference envelope support ladder — frozen extension, v1

Frozen 2026-09-03 (Asia/Seoul) before fitting or inspecting any nonzero-shot
output for the two added references.  This is a post-result sensitivity
extension of the completed canonical stable-anonymous support ladder.  It does
not retroactively make the original analysis reference-robust or blind.

## Motivation and prior information

The completed canonical ladder measured an unweighted macro utility trajectory
of `+.0884 -> +.0727 -> +.0350 -> +.0071` for `k = 0,4,32,512`, hence a
positive canonical point decay from zero to 512 shots.  The separate zero-shot
reference-space audit then measured 24 aligned global stable-anonymous
references.  Their macro utilities ranged from `+.088369992896` to
`+.124038609868`.

The new question is deliberately narrow: does the sign of the zero-to-512
decay remain positive for a lower, central, and upper global reference selected
from that already-observed zero-shot range?  Selection is therefore informed
by zero-shot outcomes and must always be described as a post-result
sensitivity analysis, not an independent confirmation.

## Frozen reference selection

The candidate set and every permutation come unchanged from
`experiments/tabllm_reference_space_v1/REFERENCE_MANIFEST_V1.json` (SHA-256
`7fe208e544a954ebd2c15e273473d604107a22e49230631101466ab97097d8da`).
Selection uses the aligned global-reference macro utilities, not the
combinatorial per-dataset envelope:

- lower endpoint and existing canonical reference: `ref_00`, macro `+.088369992896`;
- center: `ref_22`, macro `+.106028061004`, the reference closest to the
  aligned-range midpoint `+.106204301382`;
- upper endpoint: `ref_04`, macro `+.124038609868`.

Ties, had they occurred, would have been broken by the smaller numeric
reference ID.  Only `ref_22` and `ref_04` receive new fits.  `ref_00` is reused
from the completed canonical ladder.

## Fixed panel and execution grid

- Datasets: `bank`, `blood`, `calhousing`, `car`, `creditg`, `diabetes`,
  `heart`, `income`, and `jungle`, with no exclusions.
- Supports: `k in {0,4,32,512}`.
- Seeds, in released order: `42, 1024, 0, 1, 32`.
- Zero-shot values are reused from the completed 24-reference audit.
- Intended-name `S` values at nonzero supports are reused from the completed
  canonical support ladder.
- New grid: 2 references x 3 nonzero supports x 5 seeds x 9 datasets =
  **270 IA3 fits**.

No dataset, seed, support, or selected reference may be dropped after output is
observed.  A failed cell is retried under the identical contract and attempts
are retained in logs.

## Serialization, pairing, model, and training contract

Each selected reference is exactly the frozen within-dataset bijection from
the reference manifest.  It preserves field order, placeholders, punctuation,
values, and the set and within-dataset stability of anonymous identifiers;
only the identifier-to-field assignment changes.  New reference cells must
match the reused intended-name cell on train membership (including replacement
multiplicity), test membership, question, verbalizers, split seed, and initial
IA3 state.

All other details are inherited unchanged from
`TABLLM_RANON_SUPPORT_LADDER_FREEZE_V1.md`: local `bigscience/T0` 11B,
released `t011b_ia3_finish.pt`, 192 trainable IA3 `lora_b` tensors, the
three-term T-Few loss, Adafactor at `.003`, linear decay with `.06` warmup,
gradient clipping at 1, batch size 4, 30 epochs, maximum length 1024, and the
same normalized-likelihood AUROC scorer.  The original frozen runner is loaded
as an implementation module; a new wrapper changes only the frozen reference
template and provenance fields.

Evidence cells may be distributed over free NVIDIA B200 GPUs 0, 1, and 2.
Each cell remains a single seeded process on one GPU, and the device and shard
are recorded.  Parallel scheduling does not alter sampling, optimization,
scoring, or the estimand.

## Pre-evidence gates

Evidence execution opens only after all of the following pass:

1. The local reference manifest has the frozen SHA-256 above, and every
   rendered template reproduces its per-dataset template hash.
2. Preparation reproduces the frozen split manifest and reports all
   train/test membership and note hashes for both selected references.
3. A two-step, limited-evaluation smoke cell has finite losses, gradients, and
   probabilities and writes the expected reference provenance.
4. A repeated identical smoke reproduces membership, prompt, and initial-state
   hashes; numerical output differences, if any, are recorded.
5. The intended-name cells selected for reuse pass their original artifact and
   metric validation and match new cells on pairing hashes.

Smoke outputs are stored separately and are inadmissible evidence.

### Pre-evidence tokenizer compatibility correction

The first smoke attempt stopped before model loading, fitting, evaluation, or
artifact creation because the frozen Transformers 4.30 tokenizer code is
incompatible with the host's newer compiled protobuf runtime.  Evidence and
all repeated smoke runs therefore set
`PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python`, the protobuf-supported
pure-Python parser compatibility path.  This affects tokenizer initialization,
not tokenization rules or model computation.  The wrapper now requires and
records this setting; no scientific output was observed before the correction.

## Estimands and adjudication

For reference `r`, dataset `d`, seed `s`, and support `k`, define

`u[r,d,s,k] = AUROC(S[d,s,k]) - AUROC(R_r[d,s,k])`.

Dataset utility is the mean over the five paired seeds, and macro utility is
the unweighted mean over the nine datasets.  The primary descriptive quantity
for each reference is

`D_r = macro_u_r(0) - macro_u_r(512)`.

The fixed sensitivity result is **SIGN_ROBUST_ACROSS_SELECTED_REFERENCES** iff
all three point estimates `D_ref_00`, `D_ref_22`, and `D_ref_04` are strictly
positive.  Otherwise it is **SIGN_NOT_ROBUST_ACROSS_SELECTED_REFERENCES**.
Report the minimum and maximum of the three decay magnitudes.  Also report,
without changing the sign criterion, 10,000 paired dataset-bootstrap
percentile intervals using one shared resampling matrix from
`default_rng(20260903)` and Student-t intervals with df=8 for every reference.
Whether all interval lower bounds exceed zero is a stronger descriptive check,
not a replacement verdict.

Secondary outputs are the macro utility trajectories at all four supports,
dataset-level decays, `k=4` to `k=512` decays, drop-Car decays, and the count of
positive dataset decays.  Macro monotonicity is descriptive only.

## Scope and reporting boundary

This analysis covers three prespecified points spanning the observed aligned
global-reference range; it is not an exhaustive 24-reference ladder and does
not establish robustness over arbitrary or combinatorial reference choices.
The selected center and upper references were chosen after zero-shot utilities
were known.  Results remain experiment artifacts until the user separately
authorizes incorporation into manuscript text, tables, or figures.

## Required artifacts

- frozen protocol, wrapper, base-runner, reference-manifest, split-manifest,
  repository, model, and checkpoint hashes;
- per-cell device, shard, membership, prompt, state, prediction, checkpoint,
  step-count, loss, and timing provenance;
- per-example labels and normalized class probabilities;
- validation of all 270 new cells and all reused inputs;
- compact JSON/CSV/Markdown summary and a complete artifact hash manifest.
