# The direction knowledge is a model prior, and the corpus that would have
# carried it was discarded before the model ever ran

2026-08-19.  Supersedes the conclusion of
[`MEASUREMENT_LAYER_PAYLOAD_AUDIT_V1.md`](MEASUREMENT_LAYER_PAYLOAD_AUDIT_V1.md)
§3–§4, which over-claimed from a truncated corpus.  Artifacts:
`experiments/crta_v3_measurement_layer_v1/`,
`logs/crta_v3_measurement_layer_v1/`.

## 1. Correction first: "the corpus states no directions" was wrong

That audit measured the **proposer payload**, and reported that 3 of 83 evidence
spans contain any directional word.  That number is correct and the inference
from it was not.  The payload is the last link in a chain that had already
discarded almost everything:

```
KNHANES 2020-2024 official codebook   46,409 bytes | 461 variables
                                      460 (99.8%) carry value labels
                                      311 (67.5%) are ordinal, 2+ numbered options
                                      259 (56.2%) carry unit or scale notation
        |
        |  <-- pre-selection, before any model: "selected_pages"
        v
materialized document pack            10 .txt files, 30,259 chars total
                                      KNHANES side: 2 files, 9,506 chars
        |
        |  <-- payload builder, retains 87%
        v
proposer_input.json                   83 spans, 26,181 chars, 12 slots
                                      KNHANES side: 3,795 chars
```

The bottleneck is the pre-selection, not the payload builder and not the model.
And the material that was dropped is exactly the measurement layer:

```
D_1_1   주관적 건강인지    1.매우 좋음 2.좋음 3.보통 4.나쁨 5.매우 나쁨 9.모름
LQ_4EQL EuroQoL 통증/불편  1.없음, 2.다소 있음, 3.매우 심함, 8.비해당, 9.모름
LQ_1HT  HINT-8 계단오르기  1.전혀 없음, 2.약간 있음, 3.많이 있음, 4.오를 수 없음, 8.비해당, 9.모름
```

Each states a scale, an ordinal direction, and sentinel codes.  A cohort that
codes self-rated health 1=excellent…5=poor and one that codes it the other way
round differ in a way no amount of column matching detects and that inverts any
transferred effect — precisely the failure the measurement layer was designed to
prevent.

The reason the audit found an empty corpus is that the task was built on
`shared_clinical_v1`: twelve laboratory and anthropometric slots measured in
mg/dL, cm, kg and mmHg by both cohorts.  **Measurement conflicts cannot occur
there.**  The feature set was chosen for clean comparability, and that choice
removed the layer's subject matter before any experiment could test it.
`feature_sets.yaml` already defines `shared_clinical_plus_survey_v1` and
`anchor_core_plus_survey_v1`; the benchmark did not use them.

So the layer was never falsified.  It was never given its material.

## 2. What the extraction experiment does show

Six independent single-turn calls, three per arm, through an isolated session
(`scripts/run_crta_v3_direction_extraction_isolated_v1.sh`).  Prompts frozen and
hashed beforehand; scored mechanically against the 7-pair sign table that
`run_crta_v3_m1m2_monotone_anchor_v1.py` froze before its own run and that beat
its capacity-matched placebo.

| arm | directions returned | abstentions | key recall | sign errors | fabricated spans |
|---|---:|---:|---:|---:|---:|
| `documented` s1 | 0 | 132 | 0/7 | 0 | 0 |
| `documented` s2 | 0 | 50 | 0/7 | 0 | 0 |
| `documented` s3 | 0 | 66 | 0/7 | 0 | 0 |
| `knowledge_only` s1 | 58 | 74 | **7/7** | 0 | n/a |
| `knowledge_only` s2 | 36 | 55 | **7/7** | 0 | n/a |
| `knowledge_only` s3 | 66 | 33 | **7/7** | 0 | n/a |

Three findings, in decreasing strength:

1. **The sign table is a model prior.**  With no documentation, the model
   returns all seven pairs with the correct sign, in all three samples, with
   zero sign errors.  The knowledge that made this program's only
   placebo-surviving constraint work is available from a language model without
   any corpus at all.
2. **The model does not fake provenance.**  Required to cite and quote a span,
   it returned **zero** directions and abstained on 50–132 pairs, three times
   out of three.  Not one fabricated span id, not one quote that does not exist.
   This is a clean negative on the confabulation hypothesis and a useful
   companion to the proposer-retry finding ("format is recoverable, content is
   not"): when the contract demands grounding and the corpus is silent, this
   model abstains rather than inventing.
3. Over-claims are large and unadjudicated (29–59 pairs beyond the key).  They
   are counted, not scored — there is no key for them — but any future use of
   model-supplied signs must control the over-claim rate, since a prior that
   asserts 66 directions to get 7 right is not free.

## 3. Provenance of the isolated session

The orchestrating assistant had already seen the sign table, the utility results
and the payload audit, so it could not serve as the extraction model.  A fresh
session was used, and its isolation was verified **objectively** rather than by
self-report: a canary file was placed in the working directory and the session
was asked to output its contents, returning `NO_FILE_ACCESS`.  This matters —
asked in prose whether it could read files, the same configuration once answered
"Yes", a hallucinated capability claim.  Self-report is not a control; the canary
is.  Working directory was outside the repository so no project instructions or
memory loaded, and every file, shell, search, web and agent-spawning tool was
denied, `Workflow` included.

Limits, stated plainly: one provider, three samples.  This measures
within-provider consistency, not the cross-model agreement the evidence ladder
used, and the provider is the same family as the orchestrating assistant.  Codex
was rate-limited until 2026-08-20 12:29 and the open-weight models sit on a
shared server at load average 211.  Replication across providers is required
before this table is quoted as a general claim about language models.

## 4. Consequence

The measurement layer now splits cleanly into a tested part and an untested one.

- **Direction, tested**: works as a constraint (the only placebo survivor), and
  its knowledge is a model prior, not a document.  A method that wants it must
  say so — "documentation-grounded" cannot cover it.
- **Unit and dimension, untested**: declared on every payload column, but the
  twelve clinical slots agree on all of them, so there is nothing to reconcile.
- **Numeric scale, tested and rejected**: reference-interval calibration lost to
  data statistics even at 32 rows, and permuted intervals beat correct ones at
  K≥128.

The open question is worth one experiment, and it is not the one that was
planned.  It is: **on a feature set that includes survey items, where 311 of 461
codebook variables carry explicit ordinal scales and sentinel codes, does
documented measurement information beat a capacity-matched placebo?**  M4
(HRS→KLoSA) is the natural setting — it is entirely questionnaire-based, its
name overlap is 0.023, and it carries the project's one separated positive.  If
the layer has value anywhere in this project, it is there.
