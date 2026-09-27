# Pre-registration: strong schema-matching baselines, v1

Declared 2026-08-20 before executing the matcher suite. The previous
token-Jaccard comparator recovered 0/9 member bindings and is too weak to
locate the contribution relative to realistic metadata-rich alignment.

## Frozen task

Closed-set 9x9 bipartite matching of the stage-factorial member columns:
height, weight, waist, SBP, DBP, glucose, HbA1c, total cholesterol and
triglycerides. The closed set is deliberately optimistic: the matcher is
told that exactly one target member exists for every source member. Hungarian
assignment is used for every score matrix.

Inputs come from stored, pre-existing assets only. Gold
`canonical_var_name`, shared flags, benchmark role and hand-built gold pair
ids are excluded from scoring and used only for evaluation. Frozen methods:

1. raw-id character TF-IDF;
2. codebook word TF-IDF;
3. codebook character TF-IDF;
4. unit-gated robust distribution-profile distance (5/25/50/75/95th
   percentiles and IQR on each parquet);
5. fixed hybrid: .55 word metadata + .20 character metadata + .25 normalized
   unit/distribution score.

## Frozen adjudication

Primary output is exact mapping accuracy. A strong non-raw baseline passes
at >=8/9; perfect 9/9 is also reported. Because a perfect permutation is
byte-identical to the stage factorial's `a11_stage_columns` input, its
downstream value is exactly the already observed a11 arm rather than a new
stochastic fit. Imperfect methods receive no such equivalence claim; their
mapping is disclosed for a later dedicated downstream run.

This is an upper-bound-friendly baseline, not a claim that metadata are free:
if metadata-rich matching closes the binding gap, the paper must say the
method's advantage is in settings without those curated descriptions/units,
not universal superiority over schema matching.

Runner/adjudicator: `scripts/run_crta_v3_schema_matcher_baselines_v1.py`.

