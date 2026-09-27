# Pre-registration addendum: stage factorial, reverse direction (E3)

Declared 2026-08-20 ~15:20, **before any reverse-direction cell has been
executed.**

## 1. Why

`M1M2_STAGE_FACTORIAL_PREREGISTRATION_V1.md`'s primary contrast — the
interaction I1, "columns are worth more on the measurement-aligned stage
than off it" — was **directionally positive but unproven**: +0.05563,
CI [-0.0104, +0.1582], win 0.70, with per-target interactions of
diabetes +0.163, hypertension +0.013, smoking -0.010. The limitation is
**three independent units**, not seed noise, so more seeds cannot fix
it. The benchmark has no further survey endpoints in this direction.

The available power fix is the **other direction**: the identical
factorial on KNHANES→NHANES yields three more endpoint-direction units.

## 2. Design

Byte-identical to the frozen factorial except: benchmark
`std_cross_kn2nh_shared_anchorreset_fewshot_v1`; label maps and the
fixed evaluation label swapped to the NHANES side (documented
`1 = yes / 2 = no` binaries); llm/pipeline/placebo tables and every arm,
cell, seed, K and rule unchanged; placebo draws re-namespaced.

## 3. Frozen predictions and adjudication

- **E3-P1 (replication of the direction)**: the reverse-direction I1 has
  a positive mean.
- **E3-P2 (pooled adjudication, the reason for the run)**: with the six
  endpoint-direction units pooled, I1 separates under the unchanged rule
  (mean > 0, CI excludes 0, win ≥ 0.60, drop-best > 0). Pooling across
  directions is declared **here, before the data**, as the primary
  analysis for the interaction; the two directions are also reported
  separately.
- **E3-P3 (the artifact guard)**: I1-sens, computed on
  inversion-corrected AUROC, agrees in sign with I1 — as it did in the
  forward direction (+0.0556 vs +0.0556).

If E3-P2 fails, the interaction claim is retired for this program and
reported as "directionally positive in both directions, unproven at
n = 6 units". The known caveat carries over: the reverse direction's raw
arm is also inverted (E4: AUROC 0.407–0.449), and its placebo draws can
produce empty label maps — such arm-cells are reported and excluded,
with the exclusion count stated.

## 4. Execution

`scripts/run_crta_v3_stage_factorial_kn2nh_v1.py`, 3 shards x 2 threads,
CPU only; adjudicated by the frozen factorial summarizer plus a pooled
run over both roots.
