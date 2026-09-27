# Selection history and information boundaries

This W5 extension adds reported-claim coding to the **existing 9 studies and
25 comparisons**. It conducts no new candidate search, adds no paper, and
changes no comparison unit or original support label.

## Recovered historical selection, not a reconstructed systematic review

The archived inclusion rule defines a bounded retrospective audit. Discovery
started from seven semantic predictive methods already named in the manuscript's
Related Work/control discussion. Three recent published leads were added:
ConTextTab and TabSTAR were explicitly user supplied, and TARTE was located
through the recorded recent-method query. The predeclared discovery cap was
8–10 plausible candidates; discovery stopped at ten, not after obtaining a
desired mix of control judgments.

The recorded query strings include `ConTextTab NeurIPS 2025`,
`TabSTAR 2025 publication`, and `semantic tabular foundation model 2025 2026`.
Publication/identity checks used NeurIPS proceedings, PMLR, and OpenReview/TMLR.
The complete Q1–Q5 query groups and source-access notes remain in the original
`iclr_latex_v3/design_audit/CANDIDATES_V1.md`. Do not invent query result counts,
database-wide screening denominators, or coverage beyond this bounded queue.

Eligibility required a peer-reviewed full paper published/accepted by the
recorded 2026-09-08 cutoff, a predictive tabular task, explicit semantic input,
a published manipulation/removal/replacement of that semantic use, and a
traceable comparison. Compound interventions remained eligible; inability to
isolate a claim was a later coding judgment, not an exclusion rule. Neither
positive effects nor acceptable controls were required.

| Stage | Count | What the record establishes |
|---|---:|---|
| Fixed candidate queue | 10 | Seven manuscript leads plus three recent leads |
| Full-text eligibility screening | 10 | All candidates screened in fixed ID order |
| Included studies | 9 | All eligible candidates retained |
| Excluded studies | 1 | TransTab, C02: no explicit semantic-information intervention located in the published paper/official appendix |
| Eligibility unresolved | 0 | As recorded; this does not resolve every source/version or control-design detail |
| Located comparison units | 25 | Original IDs C01-A through C10-B as listed in UNITS_V1.json |

The nine retained studies are LIFT, TabLLM, PLATO, CARTE, FeatLLM, TabuLa-8B,
ConTextTab, TabSTAR, and TARTE. TransTab's exclusion means the required
intervention was not located under the archived search; it is not proof that
no version or subsequent code ever contains one. It was not replaced.

Primary records: `INCLUSION_RULE_FREEZE_V1.md`, `CANDIDATES_V1.md`,
`ELIGIBILITY_SCREEN_V1.csv/.md`, `FINAL_STUDY_SET_V1.json`, and the fixed
`design_v1_1/CONTROL_CONSTRUCTION_V1_1.json`, all under the original design audit.
The current extension binds their relevant inputs by SHA-256.

## What was and was not blinded

The original selection documentation discloses prior exposure to candidate
names, qualitative results, anticipated control classifications, and existing
project experiments. Search snippets/abstracts also exposed outcomes. The
primary design codes were frozen before **formal outcome extraction**; this
does not establish literal blindness or a prospective paper-selection process.

For this W5 addition, the codebook and 25 unit IDs were frozen first, followed
by exact source-window extraction and a hashed masked packet. All numeric
tokens in source-window prose were replaced by `[NUM]`; numeric outcome tables
and plots were omitted. Comparison IDs, source locations, and design labels
retain identifying numbers. Qualitative interpretation, including benefit
language, must remain visible because it is the object of claim coding.

Two new AI coders received only that packet in separate fresh contexts. A
third fresh AI context adjudicates claims using the same masked packet and the
frozen A/B sheets before original support labels are merged. The coordinator
and source extractors had access to unmasked sources and project context.
Instructional read boundaries were used in a shared filesystem; they were not
technical access controls. Raw-coder boundary attestations and hashes are
retained. No claim of independent human double coding is made.

## TARTE source limitation

The existing local mirror explicitly identifies arXiv:2505.14415v2 (June 30,
2025; manuscript date July 1, 2025). The original eligibility record used an
official indexed TMLR excerpt; it did not archive the accepted PDF. A retry of
the same original [OpenReview PDF](https://openreview.net/pdf?id=QV4P8Csw17)
during W5 returned a browser-verification challenge. No new study search was
performed. The local mirror is evidence of its own wording, not proof of
word-for-word equivalence to the accepted publication. Preserve C10-A/B and
their uncertainty; do not promote a preacceptance quotation to a verified
published claim or code unavailable evidence as an absent claim.

## Optional manuscript-method wording — proposal only

> We extended a fixed, bounded retrospective audit of 25 published comparisons
> from nine studies by extracting the claims explicitly linked to each
> comparison. The original ten-candidate queue combined seven methods already
> discussed in the manuscript with three recent-method leads, using recorded
> proceedings/publisher queries; screening retained all nine eligible studies
> and excluded one study for which no qualifying intervention was located.
> This was not an exhaustive systematic review. Two separate AI coders coded
> semantic-content dependence and predictive-benefit claims independently from
> a common packet with numeric results and prior control-support labels masked.
> We report pre-adjudication agreement and unweighted Cohen's kappa as AI
> coding reproducibility, then cross-tabulate adjudicated claims against the
> unchanged design-support codes. Source-version uncertainty and indeterminate
> support are retained rather than counted as confirmed mismatches.

This text has not been inserted into the manuscript.
