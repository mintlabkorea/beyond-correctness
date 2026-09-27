# Direction: the measurement-stage program (v1 draft)

Drafted 2026-08-19 late night. **This is a direction document, not a
pre-registration** — each experiment it names gets its own freeze before
any cell runs. It records the thesis, the evidence for and against it as
of tonight, and the execution plan with its gates.

## 1. Thesis

**Measurement-level alignment is the stage on which concept/relation
transfer performs.** Concretely:

- **L0 measurement** (the stage): per-item value canonicalization —
  valid codes, sentinels, direction/orientation, scale — applied to
  features *and* to label/endpoint construction, derived from codebook
  extraction (isolated LLM sessions, mechanical frozen translation).
- **L1 concept** (actor): LLM candidate banks, as today. Its value is
  **membership + cross-schema binding** (ladder R1), not grouping
  aggregation (ladder R2 dead).
- **L2 relation** (actor): **not LLM-proposed**. 17/17 current medical
  banks are relation-empty and the evidence ladder shows 0 composed / 0
  cross-schema relations at every rung including the no-doc ceiling.
  Relations become a deterministic numeric library over L0-canonicalized
  members (within-concept pairwise difference/ratio, unit-aware),
  compiled, not proposed.

The claim's testable form is an **interaction, not a sum**: structure
gains (L1, L2) should be larger on the L0-aligned stage than off it —
(L1 gain | L0 on) − (L1 gain | L0 off) > 0 — judged against placebos on
every axis.

## 2. Evidence as of tonight

For the thesis:

- Label panel (2026-08-19): with codings in conflict on the *labels*, the
  correct table is decisive (+0.292 AUROC vs capacity-matched placebo,
  win 1.00) and raw transfer is polarity-inverted (AUROC < 0.5). No other
  layer can compensate a mis-mapped label.
- Ablation V2: the LLM table beats its placebo (+0.009 nRMSE) where
  survey features carry signal — the first placebo survivor in the
  program.
- The early hand-crafted M1/M2 positive that survived correspondence
  perturbation (8/8) was the bundle carrying **numeric relation
  coordinates** — prior support for L2-as-numeric.
- Ladder R1: correct column binding beats a binding lesion broadly
  (+0.065, 6/6 endpoints) — the L1 ingredient that is real.

Against / boundary conditions (must be carried, not argued away):

- Where the pipeline pre-pays L0 (harmonized benchmarks), L0 is inert —
  the stage must be *live* for the claim to be testable.
- On proxy-rich feature surfaces L0 is placebo-equivalent (ladder R3):
  the stage matters where measurement-bearing variables are load-bearing.
- Numeric relations **failed their placebo before** on M1/M2
  (relation-values vs random pairs: coin flip). L2 must beat random-pair
  placebos on the canonicalized stage, or the axis dies again.
- M4's positive is under an unresolved mechanism doubt (74%
  blocking-asymmetry share; is_target probe running tonight). Every
  M4-form claim waits on that verdict and carries the
  interface-pattern-matched control requirement.
- The extraction's reverse-coding convention cost 0.70 AUROC on one label
  (diabetes). Fixable at the prompt level (define the convention), but
  the fix is a *new extraction experiment* with its own freeze; the
  current tables stand as-is until then.

## 3. Per-task shape (M1–M6)

| task | role | L0 source | executor |
|---|---|---|---|
| M1/M2 nh↔kn | full 2×2(×2) factorial: {L0 off/on} × {L1 off/on} (+ L2 arm); interaction contrast is primary — **frozen and executed 2026-08-20 as `M1M2_STAGE_FACTORIAL_PREREGISTRATION_V1.md`** | 17-item extraction (exists; optional prompt-fix rerun) | assistant |
| M3 nhkn→hrs | control task only — name overlap 0.917, correspondence claims impossible; pre-declare L0 likely inert on its lab-dominated surface | n/a mostly | assistant |
| M4 hrs→klosa | **mechanism probes first** (is_target v1, pattern v2 — both frozen 2026-08-19/20). **Refinement, established 2026-08-20 00:10: L0 has no room on M4 as built** — the sidecar already masks sentinels, directions are concordant (audit §1), and the compiler's per-member robust standardization absorbs any affine recoding, which the canon map of a {1,3,5} item is. An L0 arm there is a predictable no-op and is dropped; the KLoSA v2 extraction (isolated `claude -p` sessions, **no GPU involved** — the b200 note applies only to open-model work) instead serves validation and future non-prepaid surfaces | KLoSA codebook extraction v2 (**done 2026-08-20**, reverse-coding convention operationalized) | assistant (M4 launcher is unattested) |
| M5 hrs→elsa | stays **not evaluable** (frozen; zero trained arms) — reported as boundary, not resurrected | — | — |
| M6 hrs→charls | **Refinement, 2026-08-20 00:15: the CHARLS target side is 7 columns from the Harmonized CHARLS D product** — the measurement debt is pre-paid by that product, so M6 is not a measurement stage either; its open questions are concept-binding ones and belong to the licensed-user control program. CHARLS extraction skipped as low-value | — | **licensed user only** (launcher + summarizer attested) |

## 4. Placebo suite (every axis, every task)

- L0: capacity-matched wrong table (ablation/label-panel generators).
- L1: binding lesion (wrong_auto_binding class) **and**, on M4-form,
  the blocking-pattern-matched control from the audit §3.
- L2: random-pair relations at matched count and operation mix.
- Standing: base + is_target.

## 5. Order of operations

1. Tonight: M4 is_target probe verdict (gated on ksup, running).
2. ksup v2 H1–H5 at K=256.
3. Review both; decide whether M4 keeps headline status.
4. Freeze the M1/M2 factorial prereg (first, cheapest, everything local).
5. KLoSA/CHARLS codebook extraction runs on anonymous (0,2,3; canary
   protocol; frozen mechanical translation with the reverse-coding
   convention defined in-prompt this time).
6. M4 factorial under the control requirements; M6 handed to the
   licensed user as a frozen package.

Nothing in this document launches anything; each numbered step that runs
code gets its own pre-registration first.
