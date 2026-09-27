# Factual construction correction v1.1

Date: 2026-09-08 (session date). Authorized by the user's attached review and
Phase C request. Applies after the existing v1 factual freeze and before the
authoritative Phase C judgments. This is not a correction made before v1 was
frozen; the earlier v1 and its hashes remain intact.

1. Remove comparison C06-B (-Reasoning) from the authoritative comparison
   inventory. The procedural instruction is not itself supplied data/domain
   semantic information under the fixed inclusion scope. C06-A (-Description)
   retains FeatLLM in the study set. This changes 26 to 25 comparisons, not the
   nine-study set, and does not depend on outcomes or control quality.
2. Change C01-C and C01-D factual Predictive interface from 동일 to 불명:
   the same LM text-input/output framework is used, but the worked example
   changes target/category representation and does not fully specify the
   mappings for both unnamed variants.
3. All other construction fields and comparison IDs remain byte-for-byte
   equal as JSON string values. IDs are not renumbered.

Authoritative successor: design_v1_1/CONTROL_CONSTRUCTION_V1_1.{json,csv,md}
and CONTROL_CONSTRUCTION_FREEZE_V1_1.json. No Phase A file or original coding
rule is edited. Construction changes after v1.1 require a further addendum.

For Phase C, a factual “changed interface” never automatically becomes
Interface Fail. The current user request's substantive comparability checks
are operationalized in PHASE_C_OPERATIONAL_ADDENDUM_V1.md before codes are
assigned. Eligibility, code assignment, and reported outcomes remain separate.
