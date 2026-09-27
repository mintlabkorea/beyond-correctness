# TabLLM exhaustive global-reference K=512 extension — frozen design, v1

Frozen 2026-09-04 (Asia/Seoul) before fitting or inspecting any K=512
prediction for the 21 newly added references.  This is a post-result
sensitivity extension.  It does not retroactively make the earlier analyses
blind or confirmatory, and it is not incorporated into the manuscript unless
the user separately authorizes that step.

## Prior information and question

The zero-shot audit already evaluates all 24 frozen aligned global anonymous
reference constructions.  A subsequent lower/center/upper sensitivity ran
`ref_00`, `ref_22`, and `ref_04` through the full support ladder.  Their
observed macro utilities at K=512 are `+.0071`, `+.0058`, and `+.0098`, and
their zero-to-512 decays are `+.0813`, `+.1002`, and `+.1142`; all three
decays and their dataset-bootstrap and Student-t intervals are positive.

The new question is exhaustive over the already-frozen global library: does
the sign of the zero-to-512 decay remain positive for every one of the 24
global constructions?  Only the missing K=512 cells are newly fit.

## Fixed reference set and execution grid

- Global reference library: `ref_00` through `ref_23`, unchanged from
  `experiments/tabllm_reference_space_v1/REFERENCE_MANIFEST_V1.json`
  (SHA-256
  `7fe208e544a954ebd2c15e273473d604107a22e49230631101466ab97097d8da`).
- Reused completed K=512 references: `ref_00`, `ref_22`, and `ref_04`.
- Newly executed references: all remaining 21 IDs, with no selection or
  exclusion after outcomes are observed.
- Datasets: `bank`, `blood`, `calhousing`, `car`, `creditg`, `diabetes`,
  `heart`, `income`, and `jungle`.
- Seeds in released order: `42`, `1024`, `0`, `1`, and `32`.
- Support: K=512 only.
- New grid: 21 references x 9 datasets x 5 seeds = **945 IA3 fits**.

No reference, dataset, or seed may be dropped.  A failed cell is retried under
the identical contract, while completed cells remain resumable and are
validated before summarization.

## Frozen training and pairing contract

The serialization, data splits, balanced 512-example sampling, local
`bigscience/T0` 11B model, released IA3 initialization, optimizer, three-term
T-Few loss, 30 epochs (3,840 steps), scoring rule, and artifact schema are
identical to the completed three-reference extension.  The new wrapper changes
only the frozen anonymous-identifier permutation and provenance status.

Every reference cell must match the reused intended-name cell for its dataset
and seed on train membership (including replacement multiplicity), test
membership and labels, question, verbalizers, split seed, and initial IA3
state.  Each stored probability vector, AUROC, accuracy, prediction hash,
checkpoint hash, and executed step count is revalidated before analysis.

The initially frozen schedule used two NVIDIA B200 devices, GPU 0 and GPU 1,
with deterministic modulo shards.  Parallel scheduling does not change cell
membership, seed, training, or scoring.  The runner is cached and resumable;
node-level interruptions are disclosed and retried without altering the grid.

### Pre-execution scheduling amendment

On 2026-09-04, after this design was written but before any new K=512 fit was
launched or inspected, the user authorized GPU 2 once it becomes available,
approximately 90 minutes after launch.  The fixed grid is therefore assigned
to three deterministic modulo shards of 315 cells each.  Shards 0 and 1 start
immediately on GPU 0 and GPU 1; shard 2 starts on GPU 2 only after the delay
and an automated free-memory check.  This resource-only amendment does not
change references, datasets, seeds, estimands, model initialization, training,
scoring, or adjudication.  Completed per-cell checkpoints, predictions, and
metrics are incrementally copied off the compute server because the server is
scheduled for maintenance five days after launch.

## Estimands and fixed adjudication

For reference `r`, dataset `d`, seed `s`, define

`u[r,d,s,512] = AUROC(S[d,s,512]) - AUROC(R_r[d,s,512])`.

Dataset utility averages the five paired seeds.  Zero-shot dataset utilities
are reused from the completed 24-reference audit.  For each reference,

`D_r = macro_u_r(0) - macro_u_r(512)`.

The primary verdict is
**SIGN_ROBUST_ACROSS_ALL_24_GLOBAL_REFERENCES** iff all 24 point estimates
`D_r` are strictly positive.  Otherwise it is
**SIGN_NOT_ROBUST_ACROSS_ALL_24_GLOBAL_REFERENCES**.

Using one shared 10,000-draw dataset-bootstrap matrix from
`default_rng(20260904)`, report for every reference its percentile interval
and the distribution of the minimum decay across all 24 references in each
draw.  A positive lower bound for this simultaneous minimum-decay envelope is
a stronger sensitivity result, not a replacement for the fixed point-sign
criterion.  Also report Student-t intervals with df=8, the K=512 utility
range, the zero-shot utility range, the correlation between reference-level
zero-shot and K=512 utilities, drop-Car decays, and positive dataset-decay
counts.

## Scope

The analysis is exhaustive for the frozen 24-member *global construction*
library.  It does not cover arbitrary anonymous serializations or the
combinatorial product space that independently chooses a different reference
for each dataset.  Reference-level constancy at K=512 is evaluated rather
than assumed.  All reference selection and zero-shot outcomes were already
known, so this remains a post-result sensitivity analysis.

## Required artifacts

- This protocol, the new wrapper and summarizer, base runners, reference and
  split manifests, repository/model/checkpoint hashes.
- All 945 new per-cell metrics, predictions, checkpoints, device/shard fields,
  membership and prompt hashes, initial/final state hashes, step counts,
  losses, and timings.
- Validation of the 945 new cells and all reused K=512 cells.
- Complete per-reference endpoint/decay CSV, JSON summary, Markdown report,
  run manifest, and artifact hash manifest.
