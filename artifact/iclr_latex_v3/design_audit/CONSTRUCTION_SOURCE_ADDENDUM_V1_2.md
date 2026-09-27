# Construction-source clarification addendum v1.2

Date: 2026-09-08. Written after primary design/outcome freezes and independent second-coder freeze. Parent factual sheet: `design_v1_1/CONTROL_CONSTRUCTION_V1_1.json`. This is a separate source clarification; no parent construction, scope, gate, outcome, or supported-claim file is overwritten. Primary design v1 remains authoritative and unchanged. No adjudication has been performed.

## LIFT: omitted detail in the factual sheet

The official supplement D.2.1 first defines the TAE example with class size 19 (printed p.42 / PDF p.20). Correct-Names I explicitly includes that class size. Correct-Names II's natural-language example (printed p.43 / PDF p.21) mentions course 3, summer semester, a native-English-speaking assistant, and instructor ID 23, but omits the class-size value. The existing factual sheet records inconsistencies in shuffled and unnamed examples without separately recording this omission in the correct format-II example.

The second coder identified the omission; the root reviewer verified the official layout text and rendered page. This supplements the example-level construction record. It does **not** establish that the executed experiments deleted a feature, nor that both formats used the same defective template. It reinforces the unresolved relationship between illustrative examples and executed templates. The primary LIFT gates already record example/mapping uncertainty; no gate change is made here, and the independent secondary codes remain exactly as frozen.

## TabSTAR: common recipe versus checkpoint identity

The official paper §6 opening (p.9) states a common variant experiment: pretraining over 256 datasets including 30 benchmark datasets, then evaluation on the remaining 20. The factual sheet's wording that per-variant checkpoint/training matching is not separately detailed must be read with this explicit common experimental recipe. Identical fitted checkpoints are not required by CONTROL_CODING_RULE_V1; ordinary fitted-state changes under a common recipe are allowed consequences.

This is a contextual clarification, not a demonstrated contradiction of the factual sheet or an error requiring primary recoding. Both coders' TabSTAR gates agree. The statement is recorded to avoid an overly strong inference from the absence of checkpoint-level detail.

## Excluded from factual correction

TabLLM scaffold protection, FeatLLM description-package scope, encoder-change protection and allocation of missing provenance to gates are interpretive disagreements. They are disclosed in `second_coder_v1/comparison/` and are not relabelled factual errors to permit post-outcome revisions.
