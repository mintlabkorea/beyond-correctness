# Pre-registration: M×C×R full-factorial semi-synthetic benchmark, v1

Declared 2026-08-20, **before any evidence cell has been executed.**
Revision 2: the first draft was adversarially reviewed (Codex design
review, 22 findings; an independent second reviewer on the code) before
freezing; every design change they forced is listed in §13. **Smoke
disclosure**: realization 0 of every family and construction suite was
executed and its contrasts observed under both the draft and the
revised runner (outputs in
`experiments/crta_v3_mcr_factorial_semisynth_v1_smoke*/`, not
evidence). The confirmatory grid therefore draws from a **salted RNG
namespace** (`mcr_v1c`), so no observed mechanism, rendering, lesion,
or row draw recurs in the evidence run.

This is the composition experiment the paper lacks (`PAPER_PLAN` §1-5):
the three axes — **M** (source-side scale alignment), **C**
(correspondence), **R** (relation/operation knowledge) — manipulated
independently on a semi-synthetic benchmark with known ground truth,
matched lesions, exchangeable-null calibration arms, construction
checks, and two tree backbones.

**Scope of the claim, declared now.** Knowledge is declared at the
canonical/concept level and must be routed onto rendered columns by the
layers below it; the factorial therefore tests a **routing gate**, not
an emergent synergy: correct knowledge is expected to be worth more when
the layers beneath it are correct because that is what routing means.
P1/P2 read content-versus-matched-misinformation (the same contrast
class as the program's real-data placebos), not knowledge-versus-none.
The R axis alone has a true "absent" level (free), so R carries both an
identification verdict and a utility verdict, kept separate — the
program's identification≠utility split must be allowed to reproduce
here, not be assumed away.

## 1. Data basis

Public-use NHANES covariate panel (`nhanes_common_panel_tokens_v2
.parquet`, SHA-256 pinned at run time), the same eight locked features
and cycle split as `nhanes_semisynthetic_attribution_v1`: age,
total_cholesterol, hba1c, creatinine, hemoglobin, rbc, wbc, waist;
source cycles 2001–2014, target cycles 2015–2023, disjoint subjects.
Real rows, values, and missingness masks are preserved in the
**rendering**; the outcome is computed from mask-independent latents
(§3). z_j = source-fitted standardization of the real values (clip ±5).

## 2. Realizations (the independent unit)

A realization = one draw of (rendering parameters, lesion draws,
mechanism, latent completion, rows, noise), keyed by hash-rng on
(family, index). 20 per family. One lesion draw of each kind per
realization, reused across every cell, K, and backbone. Realizations
are DGP draws conditional on the fixed NHANES panel; this licenses no
NHANES-population claim and is stated as such.

Per realization: source rows = 2,048 (capped on purpose — an uncapped
source lets the model relearn everything and starves every knowledge
contrast); query = 2,000 target rows; support = K ∈ {32, 512} from the
remaining target pool, **primary K = 32**.

## 3. Latents and outcome families

**Latent completion.** For every missing entry, a latent value is drawn
from that feature's observed source distribution (keyed rng). Outcomes
are computed from the completed latents, so **missingness carries zero
information about y**; the rendering still shows the model the real
mask (sentinel/NaN). This removes the availability-artifact channel the
attribution benchmark documented.

**Decodable truth.** Ordinal features (§4) enter the outcome through
their canonical bin value z̃_j (bin mean under the canonical edges), so
the correct decode recovers the signal variables **exactly** on both
sides; continuous features enter as z_j. Every mechanism term is
standardized to unit SD on source rows before its coefficient is
applied, so difference and ratio terms contribute at matched scale.

Families (regression only; ε ~ N(0, σ), σ = SD(signal on source rows),
SNR 1):

- **A — monotone additive**: 5 of 8 features, signs ±1, weights
  U(0.5, 1). True R = the 5 (feature, sign) pairs.
- **B — pairwise operations**: 3 **disjoint** pairs over 6 features,
  op ∈ {difference, log_ratio} with log_ratio(a,b) = log(a + 6.5) −
  log(b + 6.5) (inputs are clipped at ±5, so arguments ≥ 1.5; both
  sides carry real gradient, unlike a raw ratio whose numerator
  explains ~98% of its variance on this panel). True R = the 3
  (pair, op, sign) triples.
- **C — sparse pairwise**: 2 pairs from all 28 (may share a feature),
  rest nuisance. True R = the 2 triples.

## 4. Schema rendering

Per realization: ordinal subset = 4 of 8 features (shared — the
construct is shared; the coding is not). **Canonical quintile edges and
bin means are computed once on the source partition** and used by both
sides (no transductive target quantiles; identical canonical values
land in identical bins on both sides). Per side: ordinal direction
(reversed w.p. 1/2), code base (0/1), sentinel ∈ {8, 9}; continuous:
affine scale ~ exp(U(ln .25, ln 4)), offset ~ U(−2, 2), sentinel ∈
{−99, 99}; anonymized hash column names (a string matcher recovers
0/8; checked). Missing → sentinel code.

## 5. Factors

The **target frame is identical in every arm**: target columns decoded
with the true target-side table. Lesions act on the source side only,
so M/C contrasts read source–target alignment content, never a change
of the query representation or its NaN topology.

| factor | correct | lesion (matched) |
|---|---|---|
| **M** | true source-side table: ordinal code→canonical-bin map (undoing direction/base), sentinel→NaN, affine inverse | same-entry-count wrong source table: ordinal map composed with a random non-identity, non-reversal permutation of the 5 bin values, the NaN slot moved to a random valid code (the true sentinel decodes to a live value); continuous: affine inverse taken from a different continuous feature (derangement), declared sentinel negated |
| **C** | true source→concept routing | **type-preserving** derangement (deranged within the 4 ordinal and within the 4 continuous features; no fixed point), same columns exposed — routing only, no ordinal↔continuous type artifact |
| **R** | true relation set: monotone constraints at concept positions (family A) or compiled op columns + constraints (B/C) | **random**: same density, same op multiset, family-matched topology (B: disjoint; C: shares-a-feature matched), no true pair, drawn once per realization; **free**: no relation input (the true absent level) |

The composed source mapping (M table used × C routing) is written to
the cell record for audit. Two declared asymmetries: the family-A
random sign set forbids only the exact true assignment (an expected
~1.6 of 5 entries coincide with truth by chance, attenuating P3a
there), while B/C forbid any true pair; and all lesions are
**catastrophic** (every ordinal map scrambled, every slot deranged), so
P1/P2 read whether content at full severity is recoverable — the graded
dose–response version is a declared follow-up, not this experiment.
A deranged source can still transfer through the panel's own feature
correlations; that attenuates P2 conservatively and is expected.

## 6. Arms (17 per cell; 18 in B/C)

- Core 2×2×2 with R0 = **random**: `m1c1r1 … m0c0r0` (8).
- Free-baseline R grid: `m1c1rf`, `m1c0rf`, `m0c1rf`, `m0c0rf` (4).
- Diagnostics at M=C=1: `r_flipped` (signs negated), `r_op_only`
  (B/C only: true op columns, no constraints).
- **Exchangeable nulls** (adjudicator calibration): `r_random2` (a
  second independent random relation set), `c_deranged2` (a second
  derangement), `m_wrong2` (a second wrong source table).
- `target_only`: support rows only, free. The target frame is
  arm-invariant, so this is a single well-defined anchor.

Pooling is **unweighted**: source rows and support rows all carry
weight 1 (a weighted scheme makes XGBoost's Hessian-mass
`min_child_weight` and sklearn's count-based `min_samples_leaf`
inequivalent at small K; unweighted pooling restores the matched
meaning). The program's 1:1 weighted scheme runs as a registered
sensitivity (§9).

## 7. Backbones (both required)

- XGBRegressor: hist, depth 6, 300 trees, lr 0.05, min_child_weight
  20, reg_lambda 1.0, monotone_constraints, random_state =
  realization.
- HistGradientBoostingRegressor: max_iter 300, depth 6, lr 0.05,
  min_samples_leaf 20, l2_regularization 1.0, no early stopping,
  monotonic_cst, random_state = realization.

Under unweighted pooling the two leaf thresholds are equivalent in
expectation; this is what "matched" means here.

## 8. Construction checks and name-matcher claim

These are **plumbing assertions, not statistical negative controls**
(first-draft labelling corrected):

- **NC-M** (no-conflict rendering, family B): both M tables are empty
  by construction; the runner asserts every M-paired arm bit-identical.
  Registered, non-trivial: ΔC stays separated (ΔR is reported
  descriptively — family B's R axis may be genuinely inert for trees
  that can reconstruct pairwise structure from aligned columns, and a
  quarantine rule must not fire on a design property).
- **NC-C** (shared schema): exact-name matcher recovers 8/8 there and
  0/8 in every primary realization (N2). Derangement harm persisting is
  sanity, not a null.
- **NC-R** (direction-free outcome y = Σ c_j |z̃_j − median| + ε): true
  relation set is empty; the runner asserts `m1c1r1` ≡ `m1c1rf`
  bit-identically. Registered, non-trivial: ΔM and ΔC stay separated.

The **statistical** null calibration lives in the primary grid: N4
(`m1c1r0` vs `r_random2`), N5 (`m1c0r1` vs `c_deranged2`), N6
(`m0c1r1` vs `m_wrong2`) — exchangeable pairs whose contrast must
center on zero: CI95 contains 0 **and** |mean| < 0.05 nMSE, in every
family, on both backbones (a wide CI alone is absence of evidence, not
a null). A failed exchangeable pair means the adjudicator manufactures
effects and quarantines everything.

## 9. Scale

Primary: 3 × 20 × 2K × (17|18 arms) × 2 backbones ≈ **4,200 fits**,
plus weighted-sensitivity refits of the 8 core arms at K=32, XGBoost
only (+480). Construction suites: 3 × 20 × ≤9 arms (+~520). CPU only.

## 10. Metric and adjudication (frozen)

Fits are scored as normalized MSE, **Q = −MSE/Var(y_query)** (nRMSE is
recorded for description only — a concave transform of MSE manufactures
third-order differences, so the interaction verdict must live on the
MSE scale).

**Families are fixed strata, never resampled** (three hand-picked
mechanism classes are not a cluster sample). Per family × backbone at
K = 32: realization-level paired bootstrap (20 units, 10,000 reps, seed
20260820). Separation within a family = mean > 0 ∧ CI95 excludes 0 ∧
win ≥ 0.60. A **grid verdict** = separation in **all three families ×
both backbones** (intersection-union; no pooling across families, no
drop-best rule).

| # | contrast (per family, per backbone) | reads |
|---|---|---|
| **P1** | Q(m1c1r1) − Q(m0c1r1) | M content vs matched misinformation |
| **P2** | Q(m1c1r1) − Q(m1c0r1) | C content vs matched misinformation |
| **P3a** | Q(m1c1r1) − Q(m1c1r0) | R content identification (vs random) |
| **P3b** | Q(m1c1r1) − Q(m1c1rf) | R utility (vs absent) — separate claim, never implied by P3a |
| **P4-MC** | Q(m1c1rf) − Q(m1c0rf) − Q(m0c1rf) + Q(m0c0rf) | the measurement×correspondence interaction the paper's §1-5 needs, with no R input at all |
| **S4** (secondary) | I_MCR on the **free-baseline** grid: Q111 − Q110 − Q101 − Q011 + Q100 + Q010 + Q001 − Q000, with the R0 corners = the `rf` arms | three-way routing-gate composition — see the gates below |
| sec | I_MCR on the core (random-R0) grid; everything at K = 512; per-family effect tables; weighted-sensitivity direction agreement; for B/C the P3b decomposition Q(r_op_only) − Q(m1c1rf) (ops alone) and Q(m1c1r1) − Q(r_op_only) (signs given ops) | descriptive |

**S4 guards** (a three-way interaction on a bounded loss scale is fragile
and must not carry the claim): (i) **off-floor gate** — S4 is
interpretable only if Q(m1c0rf) − Q(m0c0rf) and Q(m0c1rf) − Q(m0c0rf)
both separate in every family × backbone (if single lesions saturate at
the all-wrong floor, I algebraically collapses to P3b and reads
nothing); (ii) **scale robustness** — the sign of I recomputed under
−log(MSE) and −RMSE is reported per family, and a sign that flips
across scales is reported as a removable interaction, never as
composition evidence. **The composition claim = P1 ∧ P2 ∧ P3a ∧ P4-MC
grid verdicts.** S4 never gates the claim in either direction.

**Completeness gate**: verdicts are emitted only from the full grid (20
realizations × 3 families × both backbones, and 20 cells per
construction suite); a partial tree yields descriptives labelled
incomplete, never a verdict. The summarizer refuses trees whose cells
were written by more than one runner version.

Interpretation map, declared now:

- P1 ∧ P2 ∧ P3a ∧ P4-MC (grid verdicts) ∧ N-checks clean → each
  layer's content is recoverable when the layers beneath it are
  correct, and measurement and correspondence compose through the
  routing gate; the real-data composition null (§1-5) is then
  power-limited, not machinery-limited.
- P3b fails while P3a holds → the identification≠utility split
  reproduces in the constructed world even with exact knowledge and
  real mismatch; report it as the program's strongest internal
  replication, and read S4 through it (an S4 effect may then hinge on
  misinformation-avoidance rather than knowledge gain — say so).
- S4 separates with its gates clean → the R axis additionally stacks;
  claim three-layer composition. S4 fails or its gates fail →
  composition is a two-layer (M×C) fact and the R axis does not stack;
  claim only M×C.
- Any of P1/P2/P3a fails in any family → that layer's lesion is
  undetectable there even with exact knowledge; weaken the
  corresponding real-data claim to match.
- Any exchangeable null (N4–N6) separates → adjudicator artifact;
  quarantine everything until diagnosed.
- Backbone disagreement on any verdict → scope that claim to the
  backbone that shows it; no cross-backbone pooling.

## 11. Execution

Runner `scripts/run_crta_v3_mcr_factorial_semisynth_v1.py` (per-cell
`metrics.json`, cached/resumable), summarizer
`scripts/summarize_crta_v3_mcr_factorial_semisynth_v1.py`, self-test
`scripts/test_crta_v3_mcr_factorial_synthetic_v1.py` (round-trip
decode, wrong-table complexity matching, type-preserving derangement,
topology-matched placebos, NC bit-identities, sign routing,
learnability floor). Committed with this document before launch. Local
CPU ≤ 8 threads, no GPU (contract), public-use panel, aggregate
metrics only.

## 12. What this experiment cannot show

It cannot show that real documentation carries this content (that is
the real-data program), cannot separate routing-tax from knowledge gain
without the deferred oracle-R arm (declared: if S4 separates, a
follow-up compiles R directly against the physically rendered columns
at every M×C corner to price the routing tax), and cannot support
NHANES-population claims.

## 13. Revision log (all pre-execution)

Draft 1 archived at
`context/archive/MCR_FACTORIAL_SEMISYNTH_PREREG_V1_draft1_20260820.md`.
Changes forced by adversarial review, accepted before freezing: verdict
metric moved from nRMSE to normalized MSE (Jensen bias in third
differences); M lesion restricted to the source side (the draft
corrupted the query representation and its NaN topology); outcome
detached from the missingness mask via latent completion (availability
confound); ordinal truth redefined as canonical bin values with
source-partition edges (exact-knowledge property; transductive
quantiles removed); raw safe_ratio replaced by log_ratio with unit-SD
term standardization (numerator dominance measured at ~98%); C lesion
made type-preserving; R placebos topology-matched; free-baseline R
grid added and P4 moved onto it (misinformation-vs-absence separation);
P3 split into identification and utility; exchangeable-null arms N4–N6
added; family resampling replaced by fixed strata with
intersection-union verdicts and the drop-best rule removed; pooling
made unweighted with the weighted scheme demoted to sensitivity
(min_child_weight vs min_samples_leaf mismatch under weights);
"negative controls" relabelled construction checks; P4 reworded from
super-additivity to routing-gate composition; target_only anchor
well-defined by the arm-invariant target frame. Rejected from review:
resampling families as clusters was replaced rather than patched;
oracle-R arms deferred (declared in §12) rather than silently added.
After the real-panel smoke (not evidence): N1's ΔR requirement demoted
to descriptive — the smoke showed family B's R axis can be inert for
trees, which is a finding, not a plumbing defect, and must not trigger
quarantine.

Second (code-level) adversarial pass, all pre-freeze: RNG namespace
salted to `mcr_v1c` because smoke observed the r00 draws; wrong-table
generator now rejects value-level truth-plus-moved-NaN and effective
reversal (the index-level rejection admitted a truth-preserving map
with p ≈ 0.7% per feature); wrong-table entry count computed from
contents (the previous assert compared a copy to itself); the resumable
cache refuses cells written by a different runner hash and the
summarizer refuses mixed-hash trees; library versions recorded in
provenance; HistGB fits wrapped in threadpool limits; the composition
claim moved from the three-way I to P1∧P2∧P3a∧P4-MC with the three-way
demoted to S4 behind an off-floor gate and a scale-robustness report
(lesion saturation makes the free-referenced three-way collapse
algebraically to P3b, and its sign is not invariant to monotone
rescalings of the loss); exchangeable nulls given an explicit
equivalence margin (|mean| < 0.05 nMSE) on both backbones; verdicts
withheld on incomplete grids; r_op_only wired into the registered
P3b decomposition for B/C.

## 14. Post-execution addendum (2026-08-20, after the grid ran)

A third adversarial pass finished after execution. Nothing below
changes a rule or a verdict; the executed tree was re-audited and
passes the strengthened gates (one provenance triple across all modes,
realization sets exactly {0..19}, `r_op_only` present in every B/C
cell).

- **Wording correction (§3).** "Missingness carries zero information
  about y" was too strong. What the construction guarantees is
  y ⊥ mask **given the completed latents**: the direct channel of the
  attribution benchmark (masked terms contributing exactly 0) is
  removed, and no arm-specific mask asymmetry exists. Marginally,
  corr(y, mask_j) reaches 0.27 on the real panel because missingness
  covaries with the covariates themselves (the panel is not MCAR);
  this realistic structure is shared identically by every arm.
- **Audit wording (§5).** The cell record stores the C permutations
  and per-table digests; the composed mapping is derivable from them,
  not materialized as one object.
- **Naming.** The construction suites are emitted under the JSON key
  `negative_controls` for house-style compatibility; §8's relabelling
  to "construction checks" is the interpretive statement.
- **S4 scale robustness.** The "−RMSE" variant is query-SD-normalized
  RMSE (the program's nRMSE convention), not raw RMSE.
- **Hardening applied after the run** (verified not to bite it): the
  resume cache now also checks input/prereg hashes and the cell's own
  path identity; the summarizer refuses cross-mode provenance mixtures,
  requires realization-set completeness rather than counts, and treats
  a missing arm outside family A as an error rather than skipping it.
