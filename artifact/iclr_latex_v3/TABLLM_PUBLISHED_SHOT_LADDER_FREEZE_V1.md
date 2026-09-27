# TabLLM published shot-ladder retrospective — frozen design, v1

Frozen 2026-09-02 (Asia/Seoul), before any table cell beyond those disclosed
below was transcribed, and before any estimand of this experiment was
computed.  Retrospective decomposition of already-published numbers; no new
model is fit.

## Question

The manuscript states (Conclusion): the benefit of supplied semantic
knowledge "decreased as more labeled target examples became available", and
its one real-data support ladder (`crta_v3_exam_support_ladder_v1`) sits on
the six outcome-selected class-A examination endpoints.  The rule-fixed
thirteen-endpoint decay in that run (`+.0307 [+.0029,+.0563]`) removes the
selection concern but not the single-setting concern.

This experiment asks whether the same directional dependence appears in a
**third, independent real-data setting whose panel is fixed by a published
benchmark**: the nine public datasets of TabLLM (Hegselmann et al., 2023,
PMLR v206), whose appendix Tables 12--14 report every serialization arm at
shots `k ∈ {0,4,8,16,32,64,128,256,512}` (and `all`), mean test AUROC over
five seeds, macro one-versus-rest for Car.

The feature-name utility of this setting at `k=0` is the manuscript's own
Table `tab:gap_utility` row: reproduction utility `+.088 [+.032,+.157]`
against the format-matched anonymous reference; published-table utility
`+.0756` macro against `List Only Values`.  It has never been examined
across `k`.

## Disclosure of prior information and analysis order

**The direction is calibrated, not blind — trebly so.**

1. TabLLM's own text asserts it: "the performance equalized with more
   training examples" (values-only and permuted names); "permuting the
   column names only showed a difference for up to 16 training examples";
   "all serializations with less information came close to the best
   serialization for 256 ... training examples"; Figure 2 caption: "For many
   examples, the performance of different serializations converges."
2. The zero-shot column is fully observed: it is the repo's
   `tabllm_published_three_arm_v1` decomposition (macro S `.63`, W `.5233`,
   R_pub `.5544`).
3. During the 2026-09-02 feasibility check, two full few-shot rows were
   observed (Bank: `List Perm. Names` `0.64,0.55,0.62,0.63,0.63,0.68,0.82,
   0.86,0.88`; `List Only Values` `0.56,0.58,0.60,0.63,0.63,0.71,0.79,0.84,
   0.86`), plus one flagged page-image/HTML discrepancy on Bank
   `Text T0` — an arm not used here.  No other few-shot cell was read, and
   no utility, content, or harm value at any `k>0` was computed anywhere.

Consequently no outcome may be presented as an independent discovery of the
direction.  What this experiment adds that the original paper does not
contain: (a) the **utility-lens three-arm decomposition** — whether the
reference *catches up* while the intended arm barely moves, the manuscript's
mechanism claim; (b) a **retention statistic** comparable to the
examination ladder (`.26`) and the controlled law (`~.07--.14`); (c) formal
paired inference over the nine-dataset panel.

## Arms and their fixed published names

| arm | published row (Tables 12--14) |
|---|---|
| `S` intended | `TabLLM (T0 + List Template)` |
| `W` wrong | `TabLLM (T0 + List Perm. Names)` |
| `R_pub` reference | `TabLLM (T0 + List Only Values)` |

**R_pub is format-confounded, and this is inherited, not fixed here**: the
values-only serialization changes prompt structure as well as removing
names — the reason the manuscript built the format-matched anonymous
reference for zero-shot.  A format-matched anonymous ladder requires
few-shot IA3 training and is the **named follow-up** (assets verified on
`anonymous:~/tabllm_3arm_v1/`), declared now so that appealing to it after
an unwelcome outcome is not an escape.

**Excluded by rule, stated now:** the `all` column (starred out or
single-run for TabLLM arms); the healthcare-claims Table 15 (single seed,
different shot grid, no `List Only Values` arm); `List Perm. Values`,
`Text *` serializations, and the T0-3B row (not arms of the manuscript's
three-condition construction).  Shots `k ∈ {0,...,512}`: all nine columns
retained for trajectories.

## Data extraction, frozen procedure

Two independent sources, cross-checked cell by cell:

1. `pdftotext -layout` on the PMLR PDF
   (`https://proceedings.mlr.press/v206/hegselmann23a/hegselmann23a.pdf`);
2. the arXiv e-print LaTeX source (`arxiv.org/src/2210.10723`) table files.

**All 3 arms x 9 shots x 9 datasets = 243 mean cells are required from each
source, and every pair must match exactly (two-decimal string equality).
Any mismatch, or any missing cell, halts the experiment with a report; no
tolerance, no single-source fallback without a disclosed degradation.**
If one source is unreachable, the run degrades to single-source plus the
zero-shot anchor check, and the summary must say so.  Five-seed SD
subscripts are recorded from the LaTeX source if cleanly parseable,
descriptive only.

**Zero-shot anchor:** the extracted `k=0` column must equal the 27 values
in `scripts/summarize_tabllm_published_three_arm_v1.py::PUBLISHED` exactly.
A failure withholds all verdicts.

## Estimands

Per `(dataset, k)`, on mean test AUROC, positive favouring `S`:

- `utility(k) = S(k) - R_pub(k)`
- `content(k) = S(k) - W(k)`
- `harm(k) = R_pub(k) - W(k)`; identity `content = utility + harm` exact.

Macro = unweighted mean over the nine datasets (the paper's own panel
summary).  **Absolute macro trajectories of all three arms are mandatory**,
as is the per-`k` decomposition: a utility decay driven by the reference
rising is a different finding from one driven by `S` falling.

**Primary decay:** `D = utility(0) - utility(512)`, paired within dataset.
`k=0` is the manuscript's published operating point for this setting and
the full published range; `k=512` is the largest published shot count.

**Pre-declared secondary (no numeric prediction):**
`D_sup = utility(4) - utility(512)` — the supervised-regime-only decay,
excluding the qualitatively different zero-shot rung (no task-specific fit
at `k=0`; fine-tuning at `k=4` is known to be unstable).  The strongest
verdict wording additionally requires `sign(D_sup) = sign(D)`.

Descriptive: step decays `u(0)-u(16)`, `u(16)-u(512)`; per-dataset decays;
retention `utility(512)/utility(0)` with bootstrap interval; the full
nine-point utility trajectory.

## Calibrated numeric prediction, frozen

Anchoring on the observed `utility(0) = +.0756` (published R_pub macro) and
TabLLM's own equalization claims (differences gone by 8--256 shots):

> predicted `utility(512)` in `[-.02, +.02]`, hence
> **predicted primary decay `D` in `[+.056, +.096]`, central `+.076`;
> predicted retention `|u(512)/u(0)| <= ~.26`.**

A result inside the interval is a **re-reading of TabLLM's published
pattern through the utility lens**, not a discovery.  A result outside it
is the informative outcome.

## Inference

Nine datasets are the clusters; there are no per-seed values, so the
printed five-seed means are the cell values (disclosed limitation; the
printed SDs quantify but cannot recover seed pairing).  10,000 percentile
bootstrap draws over the nine dataset-level paired decays, seed `20260902`,
one independent `default_rng(20260902 + i)` per named contrast at a fixed
enumeration index `i`.  Student-t over the nine dataset decays reported
alongside; **both** intervals bind, mirroring the examination ladder's
dual gate.

**Rounding floor:** two-decimal printing injects at most `±.005` per cell,
i.e. an SE contribution of about `.0014` to the macro decay — an order of
magnitude below the SESOI; stated so it cannot be raised post hoc.

**SESOI = .02 AUROC**: against a level of `+.0756`, a decay below `.02`
leaves retention above `~.74` and is declared uninteresting now.

## Verdict rule, declared now

Let `D` be the primary decay, macro over nine datasets.

- **SUPPORTED (within the published panel).**  Bootstrap CI95 lower bound
  `> 0` **and** Student-t lower bound `> 0` **and** `mean(D) >= .02`
  **and** drop-Car `mean(D) > 0` (Car carries the largest zero-shot
  utility, `+.31`, and is pre-declared the concentration check — the
  endpoint-concentration lesson applied a priori).
- **CONTRADICTED.**  CI95 upper bound `< 0`, or the whole CI95 inside
  `(-.02, +.02)`.
- **INCONCLUSIVE.**  Everything else.

The strongest wording additionally requires `sign(D_sup) = sign(D)`; if it
disagrees, the verdict stands but must carry the sentence "the decay rests
on the zero-shot rung".

**Wording ceiling, frozen:** no outcome licenses "the controlled law
extends to real data", nor "a third setting independently establishes the
direction".  The ceiling is: *a third real-data setting with a
benchmark-fixed panel, a different learner family (an 11B LLM with IA3
few-shot tuning), and a different knowledge channel (feature names) shows
the same directional dependence of utility on labeled target examples,
measured against the published values-only reference, which is
format-confounded.*  Post-hoc selection of a shot pair, dataset subset, or
alternative reference arm is inadmissible.

## Integrity checks, restated as a list

1. Dual-source exact match on all 243 cells (or disclosed degradation).
2. Zero-shot anchor equality with the frozen `PUBLISHED` dict (27 values).
3. All 243 cells present; a missing cell is a failure, not a skip.
4. Identity `content - utility - harm = 0` exactly, every cell.

## Execution

`scripts/extract_tabllm_published_shot_tables_v1.py` (extraction +
cross-check, writes `EXTRACTED_TABLES_V1.json` with source hashes),
`scripts/summarize_tabllm_published_shot_ladder_v1.py` (estimands,
bootstrap, verdict, writes `SUMMARY_V1.json`),
`scripts/plot_tabllm_published_shot_ladder_v1.py` (trajectories + ladder
figure).  Output under `experiments/tabllm_published_shot_ladder_v1/`,
logs under `logs/tabllm_published_shot_ladder_v1/`.  Local CPU only; no
GPU; no licensed data.  Committed with this document before the extractor
is first run.
