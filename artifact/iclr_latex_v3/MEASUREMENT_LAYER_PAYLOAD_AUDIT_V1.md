# The measurement layer: what the corpus actually carries

> **CORRECTION (2026-08-19, same day).**  §3 and §4 of this document conclude
> that the corpus states no directions.  The measurement it reports (3 of 83
> spans carry a directional word) is correct; the inference is not.  The payload
> is the end of a chain that had already discarded the material: the KNHANES
> codebook holds 461 variables of which 311 are ordinal with explicit scales,
> and a pre-selection step reduced that to a 30KB document pack covering twelve
> laboratory and anthropometric slots, where measurement conflicts cannot occur
> by construction.  Read
> [`MEASUREMENT_LAYER_EXTRACTION_RESULTS_V1.md`](MEASUREMENT_LAYER_EXTRACTION_RESULTS_V1.md)
> instead for the corrected conclusion and the extraction results.

2026-08-19.  Outcome-blind audit, run before any extraction model was called and
requiring no model at all.  Artifacts:
`scripts/measure_crta_v3_measurement_layer_payload_v1.py`,
`experiments/crta_v3_measurement_layer_v1/PAYLOAD_MEASUREMENT_AUDIT_V1.json`.

## 0. Why this audit exists

The original design had three layers: **concept** (grouping), **relation**
(typed edges), and **measurement** (unit, dimension, direction, numeric scale).
The measurement layer was load-bearing by intent — unifying a concept means
nothing if the two schemas differ in unit or in sign.  Reviewing the executed
program, it looked as if the measurement layer had quietly disappeared.  It had
not: it is where the program's **only** placebo survivor lives.  But two of its
four parts were never given an arm, so before building an extraction experiment
the cheaper question is what there is to extract and whether it has work to do.

## 1. The measurement layer is already in the payload

`proposer_input.json` declares a full unit object on every column:

```json
"unit": {"symbol": "cm", "dimension": "length",
         "canonical_symbol": "m", "scale_to_canonical": 0.01,
         "offset_to_canonical": 0.0}
```

So unit, dimension, and the affine map to canonical units were built into the
contract from the start.  What is missing is downstream: the DSL has no `unit`
field (0 occurrences), and `same_dimension_groups` — which the DSL declares on
every operation (`difference` requires `[['lhs','rhs']]`, `safe_ratio` requires
`[]`) — **never appears in `compile_bank.py`**.  The measurement layer was
specified and then not enforced, because relation went zero-active and nothing
else consumed it.

## 2. Unit: declared on both sides, and with nothing to reconcile

All 12 shared slots carry a unit block on both sides.  Five disagree, and the
disagreements are not what a unit-harmonization layer exists for:

| slot | source | target | same dimension | same affine |
|---|---|---|---|---|
| `creatinine` | `mg/dL` | `mg/dl` | yes | yes |
| `glucose` | `mg/dL` | `mg/dl` | yes | yes |
| `total_cholesterol` | `mg/dL` | `mg/dl` | yes | yes |
| `triglycerides` | `mg/dL` | `mg/dl` | yes | yes |
| `age` | `years` / `time` | `unknown` / `unknown` | no | yes |

Four are **letter case**.  The fifth is an undeclared unit on the target side.
**Zero slots have a genuine semantic unit mismatch**: every pair shares its
dimension and its scale/offset to canonical.  NHANES and KNHANES simply measure
these twelve quantities the same way.

This is the same trap that has now caught three claims in a row.  Grouping could
not be shown to help because the correspondence was already there; correspondence
could not be shown to help in M3 because the names already give it away
(normalized match 0.917, see `M4_CONTROL_LADDER_PREREGISTRATION_V1.md` §4); and
unit harmonization cannot be shown to help here because the units already agree.
A layer can only demonstrate value where the pipeline has not already done its
job.  **The unit layer needs a schema pair whose units genuinely differ** — that
is a task-selection requirement, not a method fix.

## 3. Direction: the corpus does not state it

Across all 83 evidence spans (26,263 characters of span text), the count of
directional language is:

```
increase   2
associat   1
TOTAL      3        spans containing any directional word:  3 / 83
```

No span states that a higher value of one variable goes with a higher value of
another.  **A documentation-grounded marginal-direction claim is therefore not
extractable from this corpus** — not by a better prompt, not by a better model.
Three spans is the ceiling.

This matters because direction is exactly the part of the measurement layer that
**worked**.  `MONOTONE_ANCHOR_FIRST_PASS_V1.md` records the monotone sign
constraint as the only injection in this program to beat its capacity-matched
placebo (documented vs random −0.01369, 160/240, holding at every K; flipped vs
none +0.16531 with 0/240 — wrong signs never win a single cell).  Its own §4
already flagged that the sign table is "declared physiology, not yet EXTRACTED
from the payload spans."  This audit closes that question: it could not have
been.  The knowledge that made the constraint work came from the author's
physiology, and would have to come from a model's clinical prior — not from
these documents.

## 4. Consequence for the paper

The honest statement is sharper than the one it replaces, and it is symmetric
with the relation result:

> Of the measurement layer's four parts, **unit** and **dimension** are declared
> in the payload but have nothing to reconcile in this schema pair; **numeric
> scale** was tested as reference-interval calibration and rejected (permuted
> intervals beat correct ones at K≥128); and **direction** is the one construct
> that beat its placebo — but the corpus states no directions, so its knowledge
> is a prior, not a document.

This parallels the evidence-relaxation ladder's finding for relations exactly:
7 models × 5 rungs produced 0 composed relations and 0 cross-model agreement,
with abstentions dominated by `insufficient_evidence`, and **0 even at the R4
knowledge ceiling**.  Two independent layers of the original design fail for the
same reason, and it is not a modelling failure: *the documentation does not
contain the relational or directional material the method was designed to
transport.*

## 5. What is still open, and what it needs

The remaining question is not what the corpus contains but where the working
knowledge lives, and it needs a model:

- **`documented` arm** — payload supplied, every claim must cite a span and
  quote it.  Prediction, declared here: near-total abstention, since only 3 of
  83 spans carry any directional word.  Any sign returned with a citation whose
  quoted text carries no directional statement is a **provenance confabulation**
  and is reportable as such.
- **`knowledge_only` arm** (ceiling) — slot names only.  If this recovers the
  frozen 7-pair sign table, the working constraint is a model prior, and
  "document-driven" cannot cover it.

Prompts are frozen and hashed at
`experiments/crta_v3_measurement_layer_v1/prompts_v1/` (documented 69,199 chars,
sha256 `45639e14…`; knowledge_only 1,559 chars, sha256 `ac9efd1f…`); the scorer
is `scripts/score_crta_v3_direction_extraction_v1.py`, keyed to the frozen sign
table.  **Execution is blocked**: the Codex provider returned
`You've hit your usage limit` on both arms (resets 2026-08-20 12:29), and the
open-weight models live on the B200, whose GPUs need the user's permission.
The assistant must not act as the extraction model itself — it has already seen
the answer key and the utility results, so its output would be contaminated.
