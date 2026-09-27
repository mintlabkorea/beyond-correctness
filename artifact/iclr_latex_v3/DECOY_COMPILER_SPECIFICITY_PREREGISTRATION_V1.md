# Pre-registration: compiler specificity under absent counterparts (decoy negative control), v1

Drafted 2026-08-25; to be freeze-committed before stage A is scored or
any stage-B cell is fit.

## Motivation and prior observation disclosure

The manuscript states that the compiler rejects what the documentation
does not support, and the controlled benchmark shows that wrong
correspondence is dose-monotonically harmful (MCR-D; MCR-MC surface).
Together these make the compiler's **precision under absent
counterparts** load-bearing, yet no experiment tests it: the open-world
matcher (`crta_v3_open_world_schema_matcher_v1`) uses target-side
distractors with a guaranteed gold for every query and no abstention
(name-only 2/9, name+unit 4/9, name+unit+codebook 9/9 at the full
1,315-column pool); the schema-matcher baselines are closed-set 9×9;
the MCR C lesions misroute among present columns.  Nothing feeds the
matcher a variable that has **no** counterpart, and nothing measures
what a forced false binding costs downstream in real data.  Those
prior verdicts are known and disclosed.

## Stage A — matcher abstention on orphaned queries (deterministic)

- Scoring: the frozen matcher's three regimes byte-for-byte
  (`run_crta_v3_open_world_schema_matcher_v1.py`: `norm_id`,
  `text_score`, `unit`, `document`, weights 0.80/0.20 and
  0.35/0.15/0.25/0.25), nine member queries, the 1,315-column KNHANES
  universe, the frozen metadata table.
- **Orphaning rule.**  For query q with gold g, remove from the pool
  every KNHANES column whose post-`ALL__` name starts with the gold's
  stem (trailing digits stripped: `he_sbp1` → `he_sbp`, removing
  he_sbp1/2/3…), so the construct — not just the exact column — is
  absent.  The runner asserts the gold itself is removed and records
  the removed set.
- Per query and regime: top-1 score and top-1/top-2 margin in the
  gold-present pool and in the orphan pool; per-query independent
  top-1 (no joint assignment — abstention is a per-query decision).
- **Abstention rules swept:** absolute threshold τ ∈ {0, .025, …, 1}
  and margin δ ∈ {0, .025, …, .5}.  **Registered operating point:** the
  largest τ (resp. δ) at which gold-present recall (gold is top-1 and
  passes the rule) is ≥ 8/9.  False-binding rate (FBR) = the number of
  the nine orphan queries still bound at that point.
- **DA-P1 (specificity achievable with metadata):** in the
  name+unit+codebook regime, FBR at the operating point ≤ 2/9 under at
  least one of the two rules.
- **DA-P2 (names cannot abstain):** in the name-only regime, FBR at the
  operating point ≥ 5/9 under both rules (or no operating point exists
  because recall ≥ 8/9 is unreachable, which counts as failure to
  abstain).
- **Forced false bindings** (no abstention, orphan pool, rich regime
  top-1) are frozen by stage A and are the ONLY input stage B consumes.

## Stage B — downstream damage of forced false bindings (real data)

- Base: the frozen NHANES→KNHANES ten-endpoint stage factorial
  (engine, registry, nh2kn wrapper patches, seeds 50–59, K=256,
  XGBoost) restricted to the `a11_stage_columns` arm.  The correct-arm
  reference is the frozen expansion tree's `a11_stage_columns` (same
  engine, seeds, splits) and is not refit.
- Decoy dose k ∈ {1, 3, 5, 9}: the first k member slots in a frozen
  outcome-blind order (`stable_seed("decoy_stage_b_order_v1")`
  permutation of the nine members; nested prefixes) have their
  KNHANES raw column in the benchmark manifest replaced by the
  stage-A forced false binding for that member (`slots[member].knhanes
  := decoy`), which rebinds both the K=256 support rows and the query
  rows exactly as a deployed false binding would.  The NHANES side,
  harmonization tables, labels, splits, and the remaining members are
  untouched.  Member slots carry no inline harmonization (verified).
- 10 endpoints × 10 seeds × 4 doses = 400 cells, one arm each.
  Executed on the remote server (identical builder tree, SHA-pinned
  parquets, pinned environment); RAM-capped shards.
- Estimand per (endpoint, seed, k): D(k) = AUROC(a11 correct) −
  AUROC(a11 with k decoy bindings).  Units = endpoints (seed means);
  endpoint bootstrap, 10,000 reps, seed 20260820, key
  `decoy_b|{quantity}`.
- **DB-P1 (graded damage):** per-endpoint Spearman(D, k) over
  k ∈ {0,1,3,5,9} (D(0)=0 by construction) — mean ρ > 0, CI95 low > 0.
- **DB-P2 (full-dose damage):** D(9) separated (mean > 0, CI low > 0,
  win ≥ .6 over endpoints).
- Descriptive: D(9) against the frozen derangement damage
  AUROC(a11) − AUROC(pl_columns_at_stage) (same cells) — whether
  matcher-chosen false bindings are more or less harmful than
  derangement among true members; per-member damage at k=1 is not
  identified (only the first member in the frozen order is dosed) and
  is not claimed.

Interpretation map, declared now:

- DA-P1 ∧ DA-P2 ∧ DB-P1 ∧ DB-P2 → the compiler's metadata-gated
  matcher can abstain on absent counterparts while name-only matching
  cannot, and forced false bindings are dose-monotonically harmful in
  real data; the precision claim is supported and its load is
  quantified.
- DA-P1 fails → even rich metadata does not let the frozen matcher
  abstain; the paper's "rejected rather than guessed" claim must be
  restricted to the validator's schema/provenance checks and must not
  be read as semantic precision.
- DB-P1/P2 fail (false bindings harmless) → forced false bindings land
  on near-duplicates or inert columns; precision is then not
  load-bearing for this pair, reported as such with the binding table.

## What this experiment cannot show

Stage A tests the deterministic matcher, not the LLM proposer (a
separate stage would be needed on GPU); the orphaning rule removes a
construct by name stem and could miss synonyms recorded under other
stems; stage B doses members in one frozen order, so per-member
damage is not identified.

## Execution

Stage A `scripts/run_crta_v3_decoy_matcher_v1.py` (local, seconds);
stage B `scripts/run_crta_v3_decoy_stage_b_v1.py` (server); summarizer
`scripts/summarize_crta_v3_decoy_compiler_specificity_v1.py`.
Committed with this document before stage A is run.
