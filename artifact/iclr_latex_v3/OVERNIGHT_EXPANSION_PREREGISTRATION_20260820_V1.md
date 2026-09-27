# Pre-registration: overnight expansion, 2026-08-20 (~03:20)

Declared **before any cell of E1–E4 has been executed.** Four cheap
experiments that turn tonight's conclusions into paper figures. Shared
conventions: nRMSE lower-is-better (gain = reference − arm) / AUROC
higher-is-better (gain = arm − reference); hierarchical bootstrap
(targets then seeds, 10,000 reps, seed 20260819); separation rule as all
night (mean > 0, CI₉₅ excludes 0, win ≥ 0.60, drop-best > 0).

## E1 — Direction-constraint support sweep (the regularization curve)

The identification-utility split (sign content +0.183/+0.186 vs utility
−0.002 at abundant data) predicts standard regularizer behavior: **the
constraint should become a gain when support is scarce.** Arms `free`,
`sign_documented`, `pl_sign_flip` (PAM v1 runner unchanged, arms
restricted), K ∈ {16, 32, 64, 128, 256, 1024}, 6 targets × seeds 50–59,
pooled regime.

Frozen predictions:
- **E1-P1 (slope)**: gain(sign vs free) at K=16 > at K=1024, CI on the
  paired per-cell difference excluding 0.
- **E1-P2 (crossover)**: gain(sign vs free) > 0 with CI > 0 at K=16,
  and ≤ 0 or CI∋0 at K=1024. A crossover K makes the figure.
- **E1-P3 (content at every K)**: gain(sign vs flip) > 0 with CI > 0 at
  each of the 6 K values — wrong knowledge hurts everywhere.

## E2 — Label panel on TabPFN (backbone generality, local RTX 4090)

The label-panel result (correct table decisive, raw inverted) re-run
with TabPFN 7.0.0 in-context regression instead of XGBoost: same arms
(`raw` / `pipeline_table` / `llm_table` **v2** / `placebo_table`
capacity-matched to v2), same cells (3 targets × seeds 50–59,
K ∈ {64, 256, 1024}), same fixed documented eval label. Differences,
declared: no sample weights (TabPFN API), source subsampled to 8,192
rows per cell (deterministic rng
`tabpfn_subsample|{target}|{seed}`) for the context limit.

Frozen predictions: **E2-P1** raw diabetes AUROC < 0.5 (inversion is
backbone-independent); **E2-P2** llm(v2) vs placebo separated; **E2-P3**
pipeline vs placebo separated. Any failure localizes the night's
headline to the tree backbone and must be reported as scope.

## E3 — Label panel small-K extension (does label knowledge matter more when data is scarce?)

Panel v2 arms unchanged, new cells at K ∈ {16, 32} (separate root,
same seeds). Frozen prediction **E3-P1**: gain(llm_v2 vs placebo) at
K=16 ≥ at K=1024 (label alignment governs what is learned FROM THE
SOURCE, so scarcer support should raise, not lower, its value); the
five-point curve {16, 32, 64, 256, 1024} is the figure.

## E4 — Reverse direction (KNHANES → NHANES) label panel

Same design as the panel, direction reversed
(`std_cross_kn2nh_shared_anchorreset_fewshot_v1`); label maps and eval
side swapped accordingly (eval = documented NHANES-side binary).

Frozen predictions, including a directional **asymmetry**: **E4-P1** the
raw arm is much less damaged than in nh2kn — the KNHANES source labels
(0=no/1=yes) already agree with the eval convention, so only the small
support and live sentinels corrupt; raw diabetes AUROC > 0.5 here
(vs 0.398 in nh2kn). **E4-P2/P3** llm(v2) and pipeline each separate
from placebo. E4-P1 passing would show the measurement debt is
*directional*: it falls due on whichever side supplies the bulk of the
supervision — a sharper statement of "가치는 위치가 결정한다".

## Execution

E1: 3 shards × 2 threads (CPU). E3: 1 shard (CPU). E4: 3 shards
(CPU). E2: single process on the local RTX 4090 (the b200 GPUs 1–3 the
user allocated are reserved for tomorrow's heavier neural replications;
tonight's GPU need fits locally). All runners/wrappers committed with
this document; every experiment has a completion watcher that runs its
frozen summarizer. The M4 probe chain continues independently.
