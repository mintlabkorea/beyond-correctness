# Pre-registration: positive control for the constraint-utility contrast (E1)

Declared 2026-08-20 ~14:00, **before any E1 cell has been executed.**

## 0. Why this is the most urgent open item

Proposition 2's second half is "enforcing the knowledge is profitable
nowhere". That is a **null**, and this program's own Proposition 1
corollary says a null is uninformative when the channel cannot carry the
thing being tested (F-P1: negating a value feature is a no-op, so a null
there is not evidence). A reviewer can turn that argument on us: *is the
utility contrast able to detect a utility at all?* Without a positive
control, every "no utility" result re-reads as "we cannot measure it",
and half the paper goes with it.

Partial evidence exists but does not transfer: the measurement layer
shows an enormous utility on labels (raw AUROC 0.13 vs correct table
+0.42). That is a different layer and a different interface; it does not
license the **constraint** channel's utility contrast.

## 1. E1a — minimum detectable effect (analysis, no new cells)

For each dataset where the utility contrast returned a null (nh↔kn PAM,
M3, CAMELS v2), take the real per-cell arm values and add a constant
improvement δ to the documented arm, then run the **frozen adjudicator
unchanged**. Report the smallest δ (grid 0 to 0.05 nRMSE, step 0.0005)
at which the verdict flips to *separated*. This is the contrast's
minimum detectable effect under the real noise and the real clustering.

Frozen reporting rule: the paper must state "our rule detects a true
utility of δ ≥ MDE; the observed effect was X ≪ MDE", turning the null
into a **bounded** statement instead of an absence.

## 2. E1b — synthetic positive control (execution)

Same benchmark, same cells, same arms, same adjudicator; **only the
target is replaced** by a synthetic outcome whose truth is monotone in
the constrained features by construction:

    y = Σ_j w_j · z_j + ε,  w_j > 0 for the documented features of that
    endpoint, z = the robust-standardized feature, ε ~ N(0, σ²)

with σ chosen per cell so the signal-to-noise ratio is 1.0 (declared
now; no tuning). Arms: `free`, `sign_documented` (the true signs),
`sign_flipped`. Support K ∈ {16, 32, 64, 256} — the scarce regimes where
a correct constraint must pay. Everything else — splits, weighting,
estimator, bootstrap, separation rule — is byte-identical to the real
experiment.

**Frozen predictions:**

- **E1b-P1 (the control must fire)**: `free` − `sign_documented`
  separates at K = 16 with CI excluding 0. If it does not, the utility
  contrast cannot register a utility that is true by construction, and
  **every "no utility" verdict in this program must be downgraded to
  "not measurable with this contrast"** — reported as such, prominently.
- **E1b-P2 (monotone in scarcity)**: the gain at K = 16 exceeds the gain
  at K = 256.
- **E1b-P3 (sanity)**: `flipped` − `documented` separates at every K,
  as on real data.

## 3. Interpretation, fixed in advance

E1b-P1 pass ∧ real-data null ⇒ the null is a real null, bounded below by
E1a's MDE: documented direction knowledge is correct but its enforcement
is worth less than MDE in every regime tested. E1b-P1 fail ⇒ the
program's utility claims are retracted to measurement statements about
the contrast, not about knowledge.

## 4. Execution

`scripts/compute_crta_v3_utility_mde_v1.py` (E1a) and
`scripts/run_crta_v3_synthetic_utility_control_v1.py` (E1b), committed
before launch; CPU only; 6 targets × seeds 50–59 × 4 K × 3 arms.
