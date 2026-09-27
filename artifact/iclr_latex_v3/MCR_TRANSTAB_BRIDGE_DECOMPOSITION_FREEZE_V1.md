# TransTab correspondence bridge decomposition, v1

Frozen 2026-08-27 before execution.  This is a post-result mechanism extension
to the completed TransTab three-arm grid; it is not a pretrained-language
semantics identification experiment.

Reuse the exact model, training recipe, 60 MCR cells, K in {32,512}, seeds and
correct/wrong arms from `MCR_TRANSTAB_C_REVIEW_EXTENSION_V1.md`.  Add two
anonymous arms:

- `shared_anonymous`: deterministic anonymous identifiers are shared for the
  corresponding source/target columns;
- `distinct_anonymous`: deterministic domain-local identifiers use disjoint
  source and target namespaces while retaining within-domain column identity.

Serialization, values, feature order, missingness processing and identifier
length pattern are held fixed as closely as the tokenizer permits.  The
completed `correct` and `c_wrong` arms are refit under this runner rather than
mixed across runner versions.

Frozen contrasts in Q=-MSE/Var(y_query):

1. correct - shared_anonymous: name/token-content contribution beyond shared
   identity;
2. shared_anonymous - distinct_anonymous: shared identity-bridge contribution;
3. c_wrong - distinct_anonymous: false cross-domain bridge effect;
4. correct - c_wrong: conventional content gap and exact decomposition check.

Prior prediction: if the observed gain primarily comes from shared identity
rather than name content, shared anonymous identifiers should retain most of
correct-arm utility.  Nonzero correct-minus-shared may arise from tokenization,
token sharing, surface statistics or optimization and is not automatically
attributed to lexical semantics.  Report all family x K means, paired
realization intervals and win fractions; no contrast is promoted based on its
direction.

