# TabLLM published shot-ladder retrospective — report, v1

Status: complete, adjudicated under the frozen design
(`iclr_latex_v3/TABLLM_PUBLISHED_SHOT_LADDER_FREEZE_V1.md`, committed
`fb1cd5da7` before extraction).  Metric: published mean test AUROC (5
seeds; macro one-vs-rest for Car); positive favours `S = List Template`.
No new model fit; local CPU only.

## Verdict: **INCONCLUSIVE** (frozen dual gate)

Primary decay `D = utility(0) − utility(512)`, paired over the nine
published datasets:

> `+.0656`, bootstrap CI95 `[−.0067, +.1400]`, Student-t `[−.0240, +.1551]`,
> win 8/9, drop-Car `+.0363`.

Conjuncts: mean ≥ SESOI (.02) PASS; drop-Car > 0 PASS; bootstrap lower
bound > 0 **FAIL**; Student-t lower bound > 0 **FAIL**.  The interval
failure is dispersion, not direction: the sole negative dataset is
Credit-g (`−.15`) — the manuscript's own published zero-utility example,
whose values-only reference is anomalously high at `k=0` (.66) — and Car
(`+.30`) stretches the other tail.  Nine clusters cannot absorb that
spread.

**The frozen numeric prediction was hit**: `+.0656 ∈ [+.056, +.096]`
(central `+.076`).  Per the freeze, this is a re-reading of TabLLM's
published pattern through the utility lens, not a discovery, and no
outcome upgrades the wording.

## Pre-declared descriptives (all from the frozen enumeration)

**The macro utility declines monotonically across all nine rungs**, and
its level interval excludes zero at every rung:

| k | 0 | 4 | 8 | 16 | 32 | 64 | 128 | 256 | 512 |
|---|---|---|---|---|---|---|---|---|---|
| utility | +.0756 | +.0644 | +.0611 | +.0444 | +.0400 | +.0356 | +.0233 | +.0156 | +.0100 |
| CI95 low | +.0056 | +.0178 | +.0167 | +.0111 | +.0100 | +.0133 | +.0044 | +.0089 | +.0056 |

- Secondary `D_sup = utility(4) − utility(512)` (supervised regime only):
  `+.0544 [+.0056, +.1044]`, win 7/9 — **sign agrees with the primary**,
  and its bootstrap interval excludes zero (its role is the sign
  conjunct only; it carries no verdict).
- Retention `utility(512)/utility(0) = .132 [.043, .769]` — the point
  estimate sits inside the controlled law's `~.07–.14` band, below the
  examination ladder's `.26`; the interval is wide.
- **The reference catches up**: R_pub rises `+.277` (`.554 → .831`)
  against S's `+.211` (`.630 → .841`); W nearly equalizes with S at 512
  (`.840` vs `.841`).  Content decays `+.1056 [+.0278, +.1967]`.  This is
  the manuscript's mechanism sentence, visible in a third setting.
- Identity `content = utility + harm` holds exactly in all 81 cells
  (integer-cent arithmetic), 0 violations.

## Integrity

- 243/243 mean cells exact-match between the arXiv LaTeX source and
  `pdftotext -layout` of the PMLR PDF (hashes in
  `EXTRACTED_TABLES_V1.json`).
- Zero-shot anchor: 27/27 float-equal to the frozen `PUBLISHED` dict of
  `tabllm_published_three_arm_v1`.
- For the record: one cell quoted in the freeze's disclosure (from the
  feasibility agent's page-image read) was an OCR misread — Bank
  `List Only Values` at k=32 is `.67`, not `.63`.  Both real sources
  agree on `.67`; the disclosure quoted observed material, not ground
  truth, and no estimand had been computed from it.

## What this licenses (frozen ceiling)

At most: *in a third real-data setting with a benchmark-fixed panel, a
different learner family (11B LLM, IA3 few-shot tuning) and a different
knowledge channel (feature names), the point pattern of utility declining
as labeled target examples grow reproduces — monotone across nine
published support sizes, positive at every size — but the paired
nine-cluster decay interval includes zero, so the setting adds a
consistent trajectory, not an independently significant decay.*  It must
not be written as "the controlled law extends", nor as an independent
establishment of the direction (TabLLM's own text pre-declares
equalization), and the reference is the format-confounded published
values-only arm.

## Named follow-ups (frozen)

1. Format-matched anonymous reference (`R_anon`) few-shot ladder via IA3
   training on `anonymous` — fixes the reference confound; does **not**
   fix the nine-cluster dispersion limit (Credit-g/Car spread survives
   seed-level pairing).
2. No shot-pair, dataset-subset, or reference re-selection is admissible.

Artifacts: `EXTRACTED_TABLES_V1.json`, `SUMMARY_V1.json`,
`SHOT_LADDER_V1.{png,pdf}`, `sources/`, logs in
`logs/tabllm_published_shot_ladder_v1/`.
