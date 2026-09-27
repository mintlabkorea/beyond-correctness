# TabLLM stable-anonymous target-support ladder — frozen design, v1

Frozen 2026-09-02 (Asia/Seoul) before any nonzero-shot model is fit or any
nonzero-shot output is inspected.  This is a compatibility-port follow-up to
the published-table `R_pub` ladder, not a revision of that frozen estimand.

## Pre-experiment decision

The approved goal is to test whether **feature-name predictive utility**
decreases with labeled target support in TabLLM while holding serialization
format fixed.  The experiment is deliberately two-arm:

- `S = list_template`: the released List Template with intended feature names;
- `R_anon = list_stable_anonymous`: the identical List Template with only the
  feature names replaced by deterministic within-dataset identifiers
  `feature_001`, `feature_002`, ... .

`W = list_permuted_names` is not part of this experiment.  It is unnecessary
for the primary utility estimand and will not be added after the result.  The
earlier published-table ladder remains the three-arm decomposition artifact.

## Prior information, fully disclosed

This direction is highly calibrated rather than blind.

1. TabLLM states that the serialization differences converge with more shots.
2. The completed published-table ladder found the unweighted macro
   `S-R_pub` point trajectory `+.0756 -> +.0100` and primary decay `+.0656`,
   but its frozen paired inference was `INCONCLUSIVE`.
3. The released-code zero-shot compatibility reproduction already measured
   macro `S-R_anon = +.088` with interval `[+.032,+.157]`.
4. `R_anon` can change both the dataset-level point decays and their dispersion;
   unchanged cluster count does not predetermine this experiment's verdict.

Thus a favorable result is a clean-reference external replication of a known
direction, not an independent discovery.

## Fixed panel, supports, and seeds

- Datasets: `bank`, `blood`, `calhousing`, `car`, `creditg`, `diabetes`,
  `heart`, `income`, `jungle` — all nine, with no exclusions.
- Support ladder: `k in {0,4,32,512}`.  These are respectively zero-shot,
  the smallest published supervised rung, T-Few's standard operating rung,
  and the largest published rung.
- Split/training seeds, in released order: `42, 1024, 0, 1, 32`.
- `k=0` is the already-frozen four-arm compatibility reproduction; no new fit.
- Nonzero grid: 2 arms x 3 supports x 5 seeds x 9 datasets = **270 IA3 fits**.

No shot, seed, or dataset may be dropped after outputs are observed.  A failed
cell is retried under the identical frozen contract and every attempt is logged.

## Serialization and pairing contract

Both arms use the same raw rows, row order, split membership, balanced
few-shot membership (including replacement multiplicities), question,
verbalizers, punctuation, value formatting, field order, and stable field
identity.  `R_anon` changes only the visible feature-name strings.

The test set is the released custom-reader 20% split.  Few-shot examples are
sampled from the remaining 80% exactly as the released TabLLM reader does:
balanced by class with replacement, followed by the released seeded shuffle.
Membership digests must be identical across arms for every
`(dataset,k,seed)`.

## Model and training contract

- Released executable model: local `bigscience/T0` 11B snapshot, not T0pp.
- Initialization: released `t011b_ia3_finish.pt` IA3 checkpoint.
- Only parameters matching `.*lora_b.*` are trainable.
- T-Few objective: language-model loss + multiple-choice loss + unlikely loss;
  answer-length normalization exponent 1.
- IA3/T-Few settings: Adafactor, learning rate `.003`, linear decay with `.06`
  warmup, gradient clipping at 1, batch size 4, no accumulation, 30 epochs,
  maximum input length 1024, bfloat16 compute.
- Evaluation: normalized verbalizer-sequence likelihood; binary AUROC uses
  class-1 probability and Car uses macro one-vs-rest AUROC.

The B200 host requires a modern PyTorch/CUDA stack and cannot execute the
historical PyTorch-Lightning 1.5 trainer.  A standalone PyTorch port may replace
only orchestration: sampling, tokenization, objective terms, optimizer,
scheduler, step count, checkpoint initialization, scoring, and metrics remain
fixed above.  This is a documented compatibility port, not a reconstruction of
the historical 2022 environment.

## Port-admissibility gate

All engineering outputs live under a separate `_smoke` root and are
inadmissible.  Evidence execution opens only if all checks pass:

1. Static calculation audit confirms the three loss terms, Adafactor settings,
   scheduler, clipping, and exact step counts against released T-Few code.
2. Prepared split and few-shot membership are identical across arms; test-row
   membership matches the frozen zero-shot split manifest.
3. A two-step `k=32` smoke has finite loss/gradients/probabilities, changes only
   the 192 IA3 `lora_b` tensors, and restores the initial checkpoint exactly
   before the next cell.
4. Repeated identical smoke runs reproduce membership, prompt, initial-state,
   and output hashes; any numerical nondeterminism is quantified rather than
   silently accepted.
5. Zero-shot scoring with the port reproduces the frozen compatibility
   reproduction within `1e-7` AUROC in every dataset/arm/seed cell.  Failure
   stops evidence execution and triggers a documented port correction, never a
   tolerance change after inspecting nonzero-shot results.

### Pre-evidence compatibility correction (2026-09-02)

Freeze commit `6c6fc7fed` passed the static audit, preparation audit, and two
bitwise-identical two-step smoke runs.  Its first zero-shot conformance cells
then failed the unchanged gate before evidence execution: Bank/List Template,
seed 42 differed by about `1.37e-3` AUROC and Bank/stable-anonymous, seed 42 by
about `1.82e-4`.  The failed port held the entire model in FP32 and used bf16
autocast, whereas the already-frozen compatibility scorer held T0 and IA3
weights in bf16.  The conformance shards were stopped after these two cells;
no admissible nonzero-shot fit or result had been produced or inspected.

The corrected port loads the frozen T0 base in bf16, retains only the 192 IA3
trainable tensors as FP32 master parameters for Adafactor, and uses bf16
autocast for training.  Evaluation uses a temporary bf16 copy of the IA3
tensors and then restores their exact FP32 state before checkpointing or the
next cell.  This preserves the released FP32 IA3 update semantics while making
the scorer identical to the frozen compatibility run.  All static, repeated
smoke, and 90-cell zero-shot gates are rerun; the `1e-7` tolerance and every
scientific design choice remain unchanged.

The first implementation of this correction exposed one further scoring-only
difference: it retained a bf16 autocast context during evaluation, while the
frozen compatibility scorer executed its all-bf16 model directly.  The second
conformance attempt was stopped after four cells, again before any admissible
fit.  The final port removes autocast from evaluation only; training retains
the frozen bf16-autocast/FP32-IA3-master contract.  The complete gate sequence
is rerun under a new runner/protocol hash, with the tolerance unchanged.

## Estimands

For dataset `d`, seed `s`, and support `k`, positive favors intended names:

`u[d,s,k] = AUROC(S[d,s,k]) - AUROC(R_anon[d,s,k])`.

Dataset level is the mean over the five paired seeds.  The panel macro is the
unweighted mean over all nine datasets.

- Primary: `D = macro_u(0) - macro_u(512)`.
- Predeclared supervised secondary: `D_sup = macro_u(4) - macro_u(512)`.
- Descriptive: the four utility levels, `u(0)-u(32)`, `u(32)-u(512)`, all
  dataset and seed values, arm trajectories, and point retention
  `macro_u(512)/macro_u(0)`.

No finite retention interval will be reported: the earlier ratio bootstrap was
nonregular when resampled denominators crossed zero.  Numerator and denominator
intervals are reported separately.

## Inference and frozen verdict

The independent unit for the primary gate is the dataset.  Report:

- 10,000 percentile bootstrap draws over the nine paired dataset decays using
  `default_rng(20260903)`; and
- Student-t interval over those nine decays with df=8.

Both intervals bind.  `SESOI = .02 AUROC`.  Car is again the predeclared
concentration check.

- **SUPPORTED (within this fixed panel):** both lower bounds `>0`, mean
  `D>=.02`, drop-Car mean `D>0`, and `sign(D_sup)=sign(D)`.
- **CONTRADICTED:** both upper bounds `<0`, or both complete intervals lie
  inside `(-.02,+.02)`.
- **INCONCLUSIVE:** everything else.

Macro monotonicity is descriptive only and must be called the “unweighted
macro point trajectory.”  It is not a dataset-level monotonicity claim.

## Outcome interpretation

- SUPPORTED: clean feature-name predictive utility decreases with target
  support within TabLLM's externally fixed nine-dataset panel.
- INCONCLUSIVE: the clean-reference direction is unresolved across datasets,
  regardless of the point trajectory.
- CONTRADICTED: the proposed support decay does not hold under the frozen clean
  reference at the declared SESOI.

The panel was externally fixed relative to this analysis but purposively
assembled by TabLLM for meaningful textual names.  No verdict licenses a random
task-population claim, a universal law, or an independent discovery.  Raw AUROC
headroom remains a disclosed scale limitation.

## Required artifacts

- frozen protocol and runner hashes;
- environment/model/checkpoint/repository hashes;
- split, training-membership, prompt, and initial-state hashes;
- per-example labels and normalized class probabilities;
- per-cell metrics, losses, steps, and wall time;
- trained IA3-only checkpoint per evidence cell;
- complete 270-cell manifest, summary, report, and plot.
