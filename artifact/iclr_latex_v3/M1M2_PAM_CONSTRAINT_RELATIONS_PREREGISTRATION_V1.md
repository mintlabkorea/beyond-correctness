# Pre-registration: PAM-form constraint relations (M1/M2), v1

Declared 2026-08-20 ~01:10, **before any cell has been executed.**
Motivated by Reuter et al., "Use What You Know: Causal Foundation Models
with Partial Graphs" (arXiv 2602.14972v2, read tonight): partial relational
knowledge as matrices over {−1, 0, +1} (known-absent / unknown /
known-present), covering adjacency and ancestral structure (PAM).

## 1. Translation to this program — and what is deliberately NOT retested

The paper injects the PAM through learnable attention biases in a
transformer CFM. **That mechanism class already died here**: the knowledge
-injection placebo program's C3 (relations as typed attention bias) lost
to C5 (random-pair bias). What has *survived* in this program is knowledge
as **constraint** — capacity removal — where the monotone-sign first pass
(`MONOTONE_ANCHOR_FIRST_PASS_V1.md`) produced the program's first
content-beats-matched-noise result in the support-only regime, while every
constraint taxed the pooled-transfer regime.

The PAM formalism maps natively onto the tree estimator's constraint
interface:

- **sign PAM** (feature → target): `monotone_constraints` ∈ {−1, 0, +1}
  per feature — 0 = unknown = unconstrained, exactly PAM's partiality.
- **adjacency PAM** (feature × feature): `interaction_constraints` —
  features may co-occur on a path only within declared groups. Grouping
  as capacity REMOVAL: the dual of the additive grouping channels that
  died (ladder R2), and the genuinely untested axis.

## 2. Design

Default (pipeline-harmonized) benchmark surface, 6 anchor targets
(glucose, waist_cm, triglycerides, sbp, dbp, total_cholesterol), seeds
50–59, K ∈ {64, 256, 1024}, **primary K = 256**, pooled source +
10×-analog support weighting as in every night runner (weights: source 1,
support n_source/K). Features: the ladder surface — 11 base slots + the
8 remaining bank-member slots. Backbone XGBRegressor hist d6 n300; arms
differ **only** in constraint parameters. Metric nRMSE (lower is better);
gain = reference − arm (positive = arm better).

Frozen knowledge inputs:

- Sign table: the frozen `DOCUMENTED_SIGNS` of
  `run_crta_v3_m1m2_monotone_anchor_v1.py` (7 pairs over 6 targets),
  zeros elsewhere.
- Adjacency: the gpt-5.6-sol bank's 4 concepts; interaction groups =
  [base ∪ concept_g members] per concept, so base features interact
  freely and member×member interactions are allowed only within a
  concept.

| arm | constraints |
|---|---|
| `free` | none |
| `adj_concept` | interaction groups per the true concept partition |
| `pl_adj` | same group sizes, wrong partition (≠ true; redrawn per target × seed) |
| `sign_documented` | monotone signs per the frozen table |
| `pl_sign_flip` | the same entries, every sign negated |
| `adj_sign` | both true constraints combined (descriptive "full PAM") |

## 3. Verdicts (frozen)

Hierarchical bootstrap (targets then seeds, 10,000 reps, seed 20260819),
K = 256, 60 pairs; separation = mean > 0 ∧ CI₉₅ > 0 ∧ win ≥ 0.60 ∧
drop-best > 0.

| # | contrast | reads |
|---|---|---|
| **V-ADJ (primary)** | `adj_concept` vs `pl_adj` | does the *true* adjacency beat a wrong one — the constraint-form retest of grouping |
| V-SIGN-CONTENT | `sign_documented` vs `pl_sign_flip` | wrong signs must hurt more — the content signature |
| declared expectation | `sign_documented` vs `free` | from the first pass, constraints likely **tax** this pooled regime; a negative marginal here is expected and is *not* evidence against sign content (that is V-SIGN-CONTENT's job) |
| desc | `adj_concept` − `free`; `adj_sign` arm; per-target everything | no verdict words |

Interpretation map, declared now: V-ADJ separated → the first surviving
structure-form knowledge effect, in constraint form; grouping's death was
a death of the *additive* form only. V-ADJ fails → the fourth structure
death; on tree models the PAM direction reduces to the already-known
sign-at-small-K result, and the relation axis is declared closed on this
surface pending a different estimator class.

## 4. Execution

Runner `scripts/run_crta_v3_pam_constraint_relations_v1.py`, summarizer
`scripts/summarize_crta_v3_pam_constraint_relations_v1.py`, committed
before launch; 60 cells × (1 build + 18 fits); 3 shards × 2 threads,
launched after the label-panel v2 shards exit. NHANES/KNHANES only.
