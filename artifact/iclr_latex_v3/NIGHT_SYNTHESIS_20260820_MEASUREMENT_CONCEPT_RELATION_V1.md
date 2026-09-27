# Synthesis, night of 2026-08-19→20: measurement / concept / relation

Written 2026-08-20 ~02:30 for a reader new to the program. Every
experiment below was pre-registered (design and verdict rules frozen and
committed before any cell ran) and judged against capacity-matched
placebos — wrong-content controls of the same size and form. Metrics:
nRMSE (normalized prediction error, lower is better) for continuous
endpoints; AUROC (ranking accuracy, higher is better, 0.5 = coin flip)
for binary ones. "Separated" = the frozen rule passed (positive mean,
bootstrap CI excluding zero, win rate ≥ 0.60, survives dropping the best
endpoint).

## 0. The question

Cross-country health-survey transfer (US NHANES ↔ Korean KNHANES; US
HRS → Korean KLoSA): does LLM-extracted knowledge help a model trained
on one survey predict on the other? Knowledge is split into three layers:

- **Measurement**: what each questionnaire code means — which codes are
  real answers, which mean "no answer", which direction the scale runs.
- **Concept**: which columns form one clinical concept, and which column
  in survey A corresponds to which in survey B.
- **Relation**: knowledge about how variables relate to each other.

## 1. The one prior positive is largely an artifact candidate (M4 audit)

The program's only separated transfer gain (HRS→KLoSA, +0.0528 nRMSE)
was audited: 74% of it sits on endpoints where the leakage-safety rules
zero out every knowledge feature on the target side — turning those
features into a de-facto "which cohort is this row from" flag. A direct
probe (base model + literally one such flag) is queued; if the flag alone
reproduces the gain, the headline number is an artifact of the interface
pattern, not knowledge. Coding directions themselves were verified
concordant between HRS and KLoSA, so this is not a measurement bug.

## 2. Measurement layer: value depends on WHERE the conflict sits

Four experiments on NHANES↔KNHANES:

1. **Harmonization ablation.** The benchmark normally repairs
   questionnaire codings before any model sees data. Turning that repair
   off and comparing tables: the benchmark's own hand-written table made
   transfer WORSE than raw codes (−0.0074) and failed its placebo —
   consistent with its independently-audited wrong education row. The
   LLM-extracted table beat its placebo (+0.0091, win 0.72) — the
   program's first placebo survivor of any kind.
2. **Layer ladder** (clinical endpoints, strong lab features present):
   here the measurement layer was placebo-equivalent — when powerful
   correlated lab columns carry the prediction, fixing survey codings
   moves nothing.
3. **Label panel** (survey endpoints, so the coding conflict sits on the
   training labels themselves): the correct table was decisive — +0.29
   AUROC over a wrong table, winning all 60 comparisons; with raw labels
   the transferred model predicts BACKWARDS (AUROC 0.40–0.44), because
   "1=yes/2=no" vs "0=no/1=yes" inverts the supervision and no feature
   can compensate.
4. **Extraction repair loop.** The LLM table's one failure was a
   convention, not knowledge: it did not flag 1=yes/2=no items as
   reverse-coded, costing 0.70 AUROC on the diabetes label. Freezing an
   operational definition of reverse-coding into the extraction prompt
   flipped that item in 3/3 fresh isolated samples, and the re-run panel
   confirmed: the LLM table now separates from its placebo (+0.358, win
   0.90) and sits within 0.034 of the hand-written table on diabetes — a
   20× repair. A fresh KLoSA extraction under the same prompt got 36/36
   valid-code sets right with unanimous directions.

**Measurement verdict:** inert where the pipeline already repaired the
codes; invisible where strong non-survey features dominate; **decisive
where the labels themselves are miscoded** — and LLM extraction reaches
parity with the hand-written table once the one ambiguous convention is
pinned in the prompt.

## 3. Concept layer: correspondence is real, aggregation is not

- **Which columns, correctly paired across surveys** (the bank's
  membership + binding): beats a same-size wrongly-paired control on two
  different task surfaces (+0.065 win 0.97 on clinical endpoints; +0.045
  win 1.00 on survey endpoints), and also beats the cheap "cohort flag"
  explanation. This is the concept layer's real content.
- **Grouping those columns into aggregate features** (per-concept
  mean/spread channels): indistinguishable from randomly grouped
  channels. Structure-as-added-features fails, again.
- The "measurement is the stage on which concepts act" multiplication
  claim (interaction test) pointed the right way (+0.056) but did not
  separate — three survey endpoints with very different conflict
  severities give no statistical power; recorded as unproven, not false.

## 4. Relation layer: as values dead, as prohibitions alive

- Relations as computed feature values (differences, ratios): failed
  their random-pair placebo for the third time, even with measurement
  aligned.
- Translating the partial-graph idea of Reuter et al. (arXiv 2602.14972:
  encode relational knowledge as {−1, 0, +1} matrices) into the model's
  **constraint** interface instead:
  - **Direction-of-effect constraints** (e.g. "HbA1c can only push the
    glucose prediction up"): flipping the documented directions is
    catastrophic (+0.183 separation, win 0.98) — the knowledge content
    is unambiguously real, though enforcing it on abundant data is a
    mild tax rather than a gain.
  - **Interaction prohibitions** (columns may only combine within their
    concept): beats no-constraints outright, and beats a wrongly
    partitioned control on 5/6 endpoints — missing the frozen
    separation rule by 0.00016; an independent fresh-seed replication is
    running now.
  - **Opening cross-concept channels** (the "groups also attend to each
    other where physiologically coupled" idea, with the coupling itself
    LLM-extracted and non-trivial): actively harmful (−0.0028, CI < 0).
    Freedom between groups is excess capacity here, not knowledge.

## 5. Final conclusions as of tonight

1. **Knowledge helps this transfer problem when it says what the model
   must NOT do, not when it hands the model more things.** Added
   features, added channels, added attention freedom lose to matched
   noise everywhere tried; restrictions (which columns pair with which,
   which effects run which way, which interactions are forbidden) are
   where content survives its placebo.
2. **Measurement alignment is a precondition, priced by location**: free
   where already paid, decisive on miscoded labels — and automatable by
   LLM extraction at hand-written parity once conventions are frozen.
3. **The headline cross-schema gain is under active suspicion** of being
   an interface artifact; the probe chain decides overnight.

Pending as of writing: the fresh-seed replication of the interaction
-prohibition result; the HRS→KLoSA artifact probes (queued behind a
long-running unrelated job); the knowledge-supervision run's own
verdicts (K=256).
