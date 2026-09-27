# Pre-registration: form × lesion-severity, matched (F)

Declared 2026-08-20 ~10:00, **before any F cell has been executed.**
Replaces the "40× expression ratio" claim of
`FORM_CONTENT_DECONFOUND_PREREGISTRATION_V1.md`, which compared two
contrasts at **different lesion severities** and is therefore not a
form comparison:

| earlier contrast | lesion | severity |
|---|---|---|
| `sign_documented` vs `pl_sign_flip` (+0.183) | same pairs, **negated** signs | adversarial (actively wrong knowledge) |
| `val_documented` vs `val_random` (+0.004) | **different** pairs, no direction | neutral (uninformative knowledge) |

## 1. The mechanistic hypothesis this tests

A gradient-boosted tree is invariant to negating a single feature: a
split `f ≤ t` and a split `−f ≥ −t` induce the same partition. So the
adversarial (direction-reversed) lesion **does not exist** in the value
form for a tree — the value interface can carry *which variables pair*,
but cannot carry *which way the relation runs*. If so, the two forms
differ in the KIND of knowledge they can express, not merely the
magnitude, and the honest comparison is documented-vs-fully-randomized
within each form.

## 2. Design

Surface, cells, splits, backbone identical to PAM v1
(`M1M2_PAM_CONSTRAINT_RELATIONS_PREREGISTRATION_V1.md`): nh2kn, 6
targets, seeds 50–59, K ∈ {64, 256, 1024}, primary K = 256, XGBoost hist
d6 n300, pooled source + support weighting. Knowledge = the frozen
documented pair/sign table of `run_crta_v3_m1m2_monotone_anchor_v1.py`.
**All seven arms are fit fresh in the same process on the same cell**
(no cross-experiment copying):

| arm | form | what is lesioned |
|---|---|---|
| `free` | — | reference |
| `val_documented` | value | — (difference + product of documented pairs) |
| `val_random` | value | pairing (random pairs from the 9 member slots — strength-matched) |
| `val_documented_negated` | value | direction (difference features negated: b−a instead of a−b; product unchanged, it is symmetric) |
| `sign_documented` | constraint | — (monotone constraints on documented pairs) |
| `sign_random` | constraint | pairing **and** direction (random slots, random ±1, same count) |
| `sign_flipped` | constraint | direction only (same slots, negated signs) |

All draws from `sha256("form_lesion_v1|<arm>|<target>|<seed>")`.

## 3. Contrasts and frozen predictions

nRMSE, lower better; gain = lesion − documented (positive = documented
better). Hierarchical bootstrap (targets→seeds, 10k, seed 20260819),
K=256; separation rule as always.

| # | contrast | reads |
|---|---|---|
| **F-C3** | `val_documented_negated` − `val_documented` | direction expressibility in value form |
| **F-C1a** | `val_random` − `val_documented` | value-form content, neutral lesion |
| **F-C1b** | `sign_random` − `sign_documented` | constraint-form content, **matched** neutral lesion |
| **F-C2** | `sign_flipped` − `sign_documented` | constraint-form content, adversarial lesion |

- **F-P1**: |F-C3| < 0.001 nRMSE with its CI containing 0 — negating a
  value feature changes nothing; **direction is inexpressible in the
  value form for a tree.** (Falsified if the CI excludes 0.)
- **F-P2**: the per-cell paired difference F-C1b − F-C1a is > 0 with CI
  excluding 0 — at **matched lesion severity** the constraint form still
  expresses more content than the value form. **If this fails, the
  earlier 40× was entirely lesion severity** and proposition 1's form
  claim reduces to F-P1's expressibility statement alone (which would
  still stand, and is the stronger claim anyway).
- **F-P3**: F-C2 > F-C1b (adversarial lesion is worse than neutral) —
  expected, and quantifies how much of the +0.183 is "actively wrong"
  rather than "merely uninformative".

## 4. What replaces the 40× sentence, in each branch

- F-P1 pass ∧ F-P2 pass: "the constraint interface carries a kind of
  knowledge (direction) that the value interface provably cannot, and
  expresses the shared kind (pairing) more strongly."
- F-P1 pass ∧ F-P2 fail: "the two interfaces carry the same pairing
  content at the same strength; only the constraint interface can carry
  direction at all." (Cleanest possible outcome; no magnitude claim.)
- F-P1 fail: the mechanistic argument is wrong; report the empirical
  numbers with no interpretation and drop the form claim entirely.

## 5. Execution

Runner `scripts/run_crta_v3_form_lesion_matched_v1.py`, summarizer
`scripts/summarize_crta_v3_form_lesion_matched_v1.py`, committed before
launch; 60 cells × 7 arms × 3 K; 3 shards × 2 threads, CPU only.
