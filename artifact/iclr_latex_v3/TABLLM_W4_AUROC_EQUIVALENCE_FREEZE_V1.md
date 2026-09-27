# W4 / W2 shared AUROC decision contract

Frozen 2026-09-10, before generating or inspecting the new matched R2/R3
lexical-family outcomes. Historical TabLLM outcomes are already known; this
is a review-triggered extension, not retrospective preregistration.

The shared practical-equivalence margin is **delta = 0.02 AUROC**. This reuses
the pre-existing TabLLM SESOI in TABLLM_RANON_SUPPORT_LADDER_FREEZE_V1.md and
TABLLM_PUBLISHED_SHOT_LADDER_FREEZE_V1.md. It is an operational study-scale
threshold, not a clinically validated or universally negligible difference.
The earlier lexical audit's point-estimate materiality verdict is unchanged.

Use a paired two-sided 95% interval [L,H]. The mutually exclusive categories
are: positive if L > delta; negative if H < -delta; near-zero if
L >= -delta and H <= delta; unresolved otherwise. A CI merely excluding zero
is also reported, but does not override these practical categories.
For lexical-family effects, equivalence requires the entire interval inside
[-delta,delta]; failure to establish equivalence does not establish a large
effect. Apply this same rule to endpoint attenuation interactions.

This contract freezes W4's TabLLM margin and categories only; it does not
claim to complete other, unspecified W4 analyses or retrofit old verdicts.
