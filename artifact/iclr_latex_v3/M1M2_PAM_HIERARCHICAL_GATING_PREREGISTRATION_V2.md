# Pre-registration: PAM hierarchical gating (M1/M2), v2

Declared 2026-08-20 ~01:40, **before the concept-adjacency extraction has
been read and before any v2 cell has been executed.** Extends the PAM v1
constraint experiment with the missing second level: v1's `adj_concept`
implements within-group interaction only; this v2 adds the **between-group
channel** — cross-concept member interactions opened selectively, per an
extracted concept-pair adjacency. The between-group "relation" IS the
adjacency: knowledge of which concept pairs are physiologically coupled.

## 1. Knowledge input

Concept-pair adjacency over the 4 bank concepts (6 unordered pairs),
{−1, 0, +1} with a selectivity instruction, extracted by 3 isolated
sessions (`crta_v3_concept_adjacency_extraction_v1/`, prompt sha
`5200b43d…`, same isolation protocol as every extraction tonight);
majority 2-of-3 per pair, else s1. An ancestor matrix (both directions)
is extracted alongside and **recorded only** — no arm uses it in v2.

**Degeneracy gate, declared now:** if the majority adjacency marks all 6
pairs coupled (h_gated ≡ members-free) or none (h_gated ≡ within-only),
the experiment is **not run** and the outcome is recorded as "concept
graph degenerate on this panel" — a real finding about the metabolic
panel, not a failure.

## 2. Arms and reuse

Identical surface, cells, splits, backbone, and metric to PAM v1
(`M1M2_PAM_CONSTRAINT_RELATIONS_PREREGISTRATION_V1.md`). Two new fits per
cell; the rest are **reused from v1's cached cells** (identical seeds and
support draws):

| arm | interaction groups | source |
|---|---|---|
| `free` | none | v1 |
| `adj_concept` (within-only) | [base ∪ gᵢ] per concept | v1 |
| `pl_adj` | wrong partition | v1 |
| `h_gated` | [base ∪ gᵢ] per concept **+ [base ∪ gᵢ ∪ gⱼ] per extracted coupled pair** | new |
| `h_gated_pl` | within groups + the same **number** of opened pairs, drawn ≠ the true set (per target × seed) | new |

## 3. Verdicts (frozen; bootstrap and separation rule as v1)

| # | contrast | reads |
|---|---|---|
| **V-BETWEEN-CONTENT** | `h_gated` vs `h_gated_pl` | does WHICH pairs are open matter |
| **V-BETWEEN-VALUE** | `h_gated` vs `adj_concept` | does opening the right between-channels beat within-only — the "between-group relations contribute" claim |
| desc | `h_gated` vs `free`; per-target everything | no verdict words |

Interpretation, declared now: both separate → the two-level structure
(within + selectively-between) is the first surviving hierarchical
knowledge effect. V-BETWEEN-VALUE separates but CONTENT does not → any
extra freedom between groups helps, the specific pairs are irrelevant —
capacity, not knowledge. Neither → the between-channel adds nothing on
this panel; within-only stands or falls with v1's V-ADJ.

## 4. Execution

Runner `scripts/run_crta_v3_pam_hierarchical_v2.py` (computes the two new
arms; copies the reused arms from `--v1-root` cells), summarizer
`scripts/summarize_crta_v3_pam_hierarchical_v2.py`. Gated launcher: waits
for PAM v1's 60/60 and ≥2 parseable adjacency samples, applies the
degeneracy gate, then 3 shards × 2 threads.
