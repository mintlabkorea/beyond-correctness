## Pre-registration: schema-pair generalization of the direction result (G-SIGN)

Declared 2026-08-20 ~10:30, **before any G-SIGN cell has been executed.**
Addresses the review point that every surviving positive lives on one
schema pair (NHANES↔KNHANES). The most-replicated claim — documented
direction knowledge is identifiable (right ≫ wrong) while its
enforcement is not profitable — is re-tested on a **different schema
pair, different cohorts, different source construction**.

## 1. Scope, and what is deliberately not attempted

| task | assistant-runnable? | tested here | why |
|---|---|---|---|
| M1/M2 nh↔kn | yes | (already done) | origin of the claim |
| **M3 nhkn→hrs** | **yes** (launcher carries no licensed-user attestation) | **G-SIGN-M3** | endpoints are the same clinical variables, so the frozen sign table transfers verbatim |
| M4 hrs→klosa | yes | later, needs its own extracted sign table (disability scales) | endpoint panel differs |
| M5 hrs→elsa | **no** (attested) | — | also frozen not-evaluable |
| M6 hrs→charls | **no** (launcher AND summarizer attested) | — | licensed-user package only |

The **label-measurement** claim is NOT re-tested on M3/M4: M3's
endpoints are laboratory values with no questionnaire coding conflict,
and M4's target labels are sentinel-masked with concordant direction
(2026-08-19 audit §1). Its scope limit — "measurement pays where a
coding conflict actually sits on the supervision" — is a property of
those testbeds, and is reported as such rather than re-tested where the
conflict does not exist.

## 2. G-SIGN-M3 design

Frozen M3 runtime imported unmodified (loaders, keyed splits, Base
features, 192-wide zero interface, frozen estimator, metrics); cells are
therefore identical to the published M3 runs: uncapped source, seeds
40–49, support fractions 0.01/0.05/0.10. Endpoints: the 10 M3 endpoints
for which the frozen nh/kn table supplies a documented direction whose
partner survives that endpoint's Base (dropped automatically otherwise).

Arms: `free`; `sign_documented` (monotone constraints on the documented
features); `sign_flipped` (same features, negated — adversarial lesion);
`sign_random` (same count, random features and signs — neutral lesion).
Constraints on the all-zero interface block are 0.

## 3. Frozen predictions

Metric nRMSE (lower better), gain = lesion − documented; hierarchical
bootstrap over endpoints then (fraction, seed) cells, 10k reps, seed
20260819; separation rule as always.

- **GS-P1 (identification replicates)**: `sign_flipped` − `sign_documented`
  separates, with **zero endpoints showing a negative mean**.
- **GS-P2 (neutral lesion also separates, weaker)**: `sign_random` −
  `sign_documented` > 0, and less than GS-P1's effect.
- **GS-P3 (utility does not appear)**: `free` − `sign_documented` does
  **not** separate — enforcement is not profitable on this pair either.

GS-P1 ∧ GS-P3 replicates the identification–utility split on a second
schema pair and removes "one testbed" as a blanket objection to the
program's most-replicated result. A GS-P1 failure would confine the
direction result to nh↔kn and must be reported as such.

## 4. Execution

`scripts/run_crta_v3_m3_sign_probe_v1.py` (aggregate outputs only; CPU;
CUDA hidden), summarizer `summarize_crta_v3_m3_sign_probe_v1.py`, both
committed before launch. 10 endpoints × 3 fractions × 10 seeds × 4 arms.

## 5. G-SIGN-CAMELS (added 2026-08-20 ~12:10, before any CAMELS cell)

ELSA and CHARLS are unavailable to an assistant, so the third pair is
taken **outside medicine entirely**: CAMELS US → GB (hydrology, 64 US
source basins → 12 GB support-pool / 12 GB query basins, frozen
basin-level split). Source and target schemas share almost no names
(US Daymet `prcp/tmax/srad/swe` vs GB `precipitation_cehgear`,
`pet_chess`, `temperature_haduk`), so this is a genuine cross-schema
pair in a domain where the direction knowledge is a **physical law**
rather than a clinical convention.

**Documented signs = the water balance** Q = P − ET − ΔS: precipitation
family **+1**, potential-evapotranspiration family **−1**, and their
trailing means inherit the parent sign (positive-weighted averages).
Everything else — temperature, radiation, snow water equivalent, day
length, seasonality channels — is left at 0 because its sign is
regime-dependent (snowmelt basins invert temperature). 29 of 132 base
features are constrained.

Arms and lesions as in G-SIGN-M3 (`free`, `sign_documented`,
`sign_flipped`, `sign_random` at matched count). Cells: support ∈
{1, 3, 5} basins × seeds 20–29. **Primary metric declared now:
`log1p_rmse` (lower better)**, the frozen runner's first metric and the
analogue of nRMSE used throughout; `mean_basin_nse` (higher better) is
reported alongside as the hydrology-convention secondary. Gains =
lesion − documented.

Frozen predictions:

- **GC-P1 (identification)**: `sign_flipped` − `sign_documented`
  separates, no support level negative.
- **GC-P2 (utility, the cross-domain question)**: `free` −
  `sign_documented` > 0 with CI excluding 0 — **utility is expected
  HERE**, unlike medicine, because the constraint encodes a conservation
  law on load-bearing inputs and the target support is tiny (1–5
  basins). A failure returns the identification–utility split to being
  domain-general.
- **GC-P3 (content beyond capacity)**: `sign_random` −
  `sign_documented` > 0 with CI excluding 0. The smoke cell showed
  random constraints also beating `free`, so **any GC-P2 gain must be
  read against GC-P3**: if GC-P2 passes while GC-P3 fails, the benefit
  is monotone-regularization capacity, not the physics.

## 6. Addendum GC-v2 (declared 2026-08-20 ~12:55, after v1 was read, before any v2 cell)

v1's verdicts stand as recorded. Two acknowledged weaknesses are fixed
in a **separate root**, and the reason each is fixed is stated before
running:

1. **Wrong clustering unit.** v1 bootstrapped over the three support
   levels — a design factor, not an independent population unit. The
   natural unit is the **query basin** (12 of them, shared across arms
   and already the unit of the runner's own NSE). v2 stores per-basin
   log1p RMSE and NSE and clusters over basins.
2. **Underpowered for GC-P3.** v1's content-vs-random contrast was
   separated on the primary metric but reversed on the NSE secondary.
   v2 doubles the seeds (20–39, 60 cells) so the conflict is decided
   rather than reported as ambiguous.

Frozen predictions for v2, all on basin-clustered bootstrap:

- **GCv2-P1**: identification (`flipped` − `documented`) separates, with
  **no query basin negative** — the stricter basin-level version of
  GC-P1.
- **GCv2-P2**: utility (`free` − `documented`) does **not** separate,
  replicating v1's falsification of my own prediction at higher power.
- **GCv2-P3 (the reason for v2)**: content (`random` − `documented`)
  separates **on both metrics** (log1p RMSE primary and NSE secondary),
  or the contrast is declared **metric-dependent and not carryable**.
  This is a two-sided rule: passing on primary alone is NOT a pass.

No other arm, cell, or rule changes; v1 remains the record of the
lower-powered first look.

## 7. Addendum GC-LLM (declared 2026-08-20 ~13:20, after the extraction was scored, before any GC-LLM cell)

The CAMELS direction table was the only knowledge input in this program
still authored by hand. An isolated 3-sample extraction (prompt and key
frozen beforehand, `crta_v3_camels_sign_extraction_v1`) returned:
precipitation family **+1 unanimously**, PET family **0 in 2 of 3**
(one sample gave the key's −1), every regime-dependent driver
**0 unanimously**; **0 sign flips, 0 over-commitments**. The extracted
majority table is therefore a strict, conservative subset of the water
balance.

GC-LLM re-runs the v2 probe with `--sign-source llm_majority`
(precipitation +1 only; PET unconstrained), basin-clustered, seeds
20–39, same arms and rules.

- **GC-LLM-P1**: identification (`flipped` − `documented`) still
  separates with no basin negative. Passing removes the last
  hand-authored knowledge input from the program: the CAMELS result then
  rests on an LLM-extracted table exactly like the medical ones.
- **GC-LLM-P2**: the effect is **smaller** than the hand-key version,
  because the LLM table constrains roughly half as many features. A
  larger effect would mean the PET constraints were hurting and must be
  reported as such.

## 9. Addendum GC-REL: per-relation ablation (declared 2026-08-27 15:40, before any GC-REL cell)

**Why.** The CAMELS knowledge input declares exactly two relations:
precipitation → discharge (+) and PET → discharge (−). The external
evidence audit (Table `tab:app_relation_evidence`) grades the first
"Indirect; scale mismatch" and the second "Weak/mixed; scale
mismatch" — the lowest grade any relation in the program receives; the
annual PET–discharge relation is weak and not uniformly negative, and
it is transferred to a daily constraint. Every CAMELS arm to date flips
**both** relations at once, so the +0.184 identification effect is an
undecomposed sum. The audit therefore currently sits parallel to the
experiment and informs nothing in it. GC-REL flips one relation at a
time so the audit grade and the measured effect can be put on the same
axis.

**Design.** The v2 runner, root, data, split, estimator, seeds (20–39),
support levels (1, 3, 5) and basin-clustered bootstrap are reused
unmodified. Only the arm set changes; all four arms are fit in the same
process on the same fold:

| arm | precipitation family | PET family |
|---|---|---|
| `sign_documented` (reference) | +1 | −1 |
| `flip_precip_only` | −1 | −1 |
| `flip_pet_only` | +1 | +1 |
| `sign_flipped` (v2 replication) | −1 | +1 |

**Frozen predictions.**

- **GC-REL-P0 (pipeline identity)**: `sign_flipped` − `sign_documented`
  reproduces v2's +0.18422 log1p-RMSE mean gain to within 1e-6, and the
  reproduced `sign_documented` per-basin values match v2's stored values
  exactly. Failure of P0 invalidates any P1/P2 reading.
- **GC-REL-P1 (precipitation carries identification)**: `flip_precip_only`
  − `sign_documented` separates by the GCv2 rule (mean > 0, CI excluding
  0, win rate ≥ 0.60, drop-best-basin > 0) and accounts for the
  **majority** of the both-flip effect (mean gain ≥ 0.5 × 0.18422).
- **GC-REL-P2 (PET is the weak half)**: `flip_pet_only` −
  `sign_documented` does **not** separate by that rule. The audit-derived
  reading is directional and stated in advance in three exhaustive cases:
  (a) mean ≈ 0 — the declared PET direction is inert, the constraint is
  neither right nor wrong at daily resolution; (b) mean < 0 with CI
  excluding 0 — **flipping PET improves prediction**, i.e. the declared
  − is the wrong sign for a daily constraint and the audit's lowest grade
  identified a genuinely wrong relation; (c) mean > 0 and separated — P2
  fails, PET carries real identification signal despite the weak
  external evidence.
- **Additivity is reported, not predicted.** (precip-only + pet-only)
  − both-flip is descriptive; monotone constraints interact through the
  tree fit and no additivity is claimed in advance.

**What this decides.** If P1 and P2 both hold, the honest statement
becomes: the CAMELS identification effect is carried by the one relation
the audit grades higher, and the relation the audit grades lowest
contributes nothing (or is actively wrong). That connects the evidence
audit to an experimental outcome for the first time. If P2 fails, the
audit grade does not predict per-relation contribution, which is itself
the reportable result and is the same null that N5 tests across all
relations.

### GC-REL erratum (2026-08-27 16:05, after the 60 cells were read, before any
### GC-REL text entered the paper)

Adversarial review of the runner raised one objection that the frozen
section 9 wording does not survive, and it is recorded here rather than
edited away. Writing `D, P, E, B` for the documented, precipitation-flipped,
PET-flipped and both-flipped losses, section 9's "share" is
`(P − D) / (B − D)`. That is a **simple effect** divided by a joint
effect: each single-flip contrast holds the other relation at its
documented direction, `(P − D) + (E − D) ≠ B − D` in general, and a
relation could be inert given documented precipitation yet load-bearing
given flipped precipitation. So the P1 phrase "accounts for the majority"
and the P2 phrase "contributes nothing" were not identified as written.

Two additions repair this, both computed from arms that already exist —
no cell was re-run:

1. **The opposite conditional for each relation.** `B − P` is PET's
   effect *given precipitation is already flipped*; `B − E` is
   precipitation's given PET is flipped.
2. **Shapley effects**, which average each relation's two conditionals and
   therefore sum exactly to the joint effect:
   `φ_P = ½[(P − D) + (B − E)]`, `φ_E = ½[(E − D) + (B − P)]`,
   `φ_P + φ_E = B − D`.

`GC_REL_P1_pass_shapley` and `GC_REL_P2_pet_inert_in_both_contexts` are
added to the summary and are the figures the paper should quote. The
original simple-effect shares are retained in the JSON for continuity with
the frozen wording, flagged as not identified. P1 and P2 pass under both
readings, so no verdict changes; the objection was to the warrant, not the
result.

Two further review findings are recorded without changing the run.
(a) v2's `hierarchical_ci` resamples cells within each drawn basin even
though cells are crossed with basins, not nested in them. GC-REL keeps
that estimator so it stays cell-for-cell comparable with v2, and adds a
basin-means-only bootstrap as `robustness_basin_mean_bootstrap`; every
GC-REL interval is unchanged to three significant figures under it.
(b) XGBoost does not guarantee bitwise invariance to thread count, so
GC-REL-P0's "exactly" is an empirical check, not a guaranteed one. It was
verified over all 2880 per-basin comparisons at max |Δ| = 0.0 despite a
different `n_jobs` than v2; regardless, the four GC-REL arms share one
process and thread count, so the paired contrasts are internally valid
even had P0 drifted.
