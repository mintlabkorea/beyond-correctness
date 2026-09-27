# Claim-matched audit: computed results

Fixed 25 comparisons / nine studies. Original support codes are unchanged. Mismatch means an explicit author claim paired with support=None under the frozen framework; it is not a paper-quality score or proof the substantive scientific claim is false.

| Axis | Explicit claims | Matched | Mismatch | Support indeterminate | Not claimed | Claim unclear |
|---|---:|---:|---:|---:|---:|---:|
| content | 18 | 1 | 14 | 3 | 3 | 4 |
| utility | 11 | 2 | 6 | 3 | 10 | 4 |

## Pre-adjudication reported-claim agreement

| Axis | Exact agreement | Cohen kappa |
|---|---:|---:|
| claim_content | 23/25 (92.0%) | 0.7983870967741936 |
| claim_utility | 23/25 (92.0%) | 0.8663101604278074 |
| descriptive_only | 25/25 (100.0%) | undefined |

## content: reported claim × original control support

| Claim | Supported | None | Unclear |
|---|---:|---:|---:|
| Yes | 1 | 14 | 3 |
| No | 0 | 3 | 0 |
| Unclear | 0 | 4 | 0 |

## utility: reported claim × original control support

| Claim | Supported | None | Unclear |
|---|---:|---:|---:|
| Yes | 2 | 6 | 3 |
| No | 2 | 8 | 0 |
| Unclear | 0 | 2 | 2 |

## Reliability limits

Claim coding uses two fresh same-model AI contexts and one common masked packet. This is AI reproducibility, not human inter-rater reliability. Numeric magnitudes and original support labels were withheld; qualitative result language was necessarily visible. Source extraction was not blinded. The read boundary was instructional. Kappa is unweighted with label marginals retained; no comparison-independence confidence intervals are reported. See [Cohen (1960)](https://doi.org/10.1177/001316446002000104) for the nominal-agreement coefficient.

Historical support reliability reuses previously frozen primary/second AI gates, with differing declared scopes. The historical second coder did not supply a standalone content-support label: that column is deterministically derived from its Preservation/Interface gates and the shared original Wrong-like intervention classification. Do not present its kappa as a new independently coded content rating. TARTE remains a preacceptance-mirror source limitation, not a source-verified published-claim determination.

## Every comparison and its evidence

### C01-A — LIFT

Correct-Names I vs Shuffled-Names I

> Second, we observe that correctly incorporating feature names helps boost the performances of LIFT for datasets except for CMC.

C01-A-W3: PDF p. 8, source lines 454–462 (iclr_latex_v3/design_audit/sources/C01_main.txt)

Claim content / utility: Yes / Yes. Original support: Unclear / None. Match: Indeterminate / Mismatch.

The shared correct/shuffled/unnamed comparison interpretation attributes prediction changes to correct feature/value association and explicitly says correct names boost performance. The benefit is qualified to datasets other than CMC, and this row retains its original prompt format and comparator.

### C01-B — LIFT

Correct-Names II vs Shuffled-Names II

> Second, we observe that correctly incorporating feature names helps boost the performances of LIFT for datasets except for CMC.

C01-B-W3: PDF p. 8, source lines 454–462 (iclr_latex_v3/design_audit/sources/C01_main.txt)

Claim content / utility: Yes / Yes. Original support: Unclear / None. Match: Indeterminate / Mismatch.

The shared correct/shuffled/unnamed comparison interpretation attributes prediction changes to correct feature/value association and explicitly says correct names boost performance. The benefit is qualified to datasets other than CMC, and this row retains its original prompt format and comparator.

### C01-C — LIFT

Correct-Names I vs W/o Names I (Table 9)

> Second, we observe that correctly incorporating feature names helps boost the performances of LIFT for datasets except for CMC.

C01-C-W3: PDF p. 8, source lines 454–462 (iclr_latex_v3/design_audit/sources/C01_main.txt)

Claim content / utility: Yes / Yes. Original support: None / None. Match: Mismatch / Mismatch.

The shared correct/shuffled/unnamed comparison interpretation attributes prediction changes to correct feature/value association and explicitly says correct names boost performance. The benefit is qualified to datasets other than CMC, and this row retains its original prompt format and comparator.

### C01-D — LIFT

Correct-Names II vs W/o Names II (Table 9)

> Second, we observe that correctly incorporating feature names helps boost the performances of LIFT for datasets except for CMC.

C01-D-W3: PDF p. 8, source lines 454–462 (iclr_latex_v3/design_audit/sources/C01_main.txt)

Claim content / utility: Yes / Yes. Original support: None / None. Match: Mismatch / Mismatch.

The shared correct/shuffled/unnamed comparison interpretation attributes prediction changes to correct feature/value association and explicitly says correct names boost performance. The benefit is qualified to datasets other than CMC, and this row retains its original prompt format and comparator.

### C03-A — TabLLM

List Template vs List Permuted Names

> This indicates that if enough training examples are available, the serialization approach does not matter, but that TabLLM relies on information from the feature names in the zero-shot and few-shot regime, and also relies on the association of the names with the correct values.

C03-A-W4: PDF p. 6, source lines 542–557 (experiments/published_claim_match_w5_v1/sources_reading/C03_raw.txt)

Claim content / utility: Yes / No. Original support: Supported / None. Match: Matched / Not claimed.

The interpretation explicitly asserts reliance on the relevant names, name/value associations, or values in zero/few-shot prediction, with equalization at larger training sizes. The complete window does not separately interpret this intervention as semantic knowledge benefiting prediction; observed poorer performance and reliance are not by themselves a utility claim.

### C03-B — TabLLM

List Template vs List Only Values

> This indicates that if enough training examples are available, the serialization approach does not matter, but that TabLLM relies on information from the feature names in the zero-shot and few-shot regime, and also relies on the association of the names with the correct values.

C03-B-W4: PDF p. 6, source lines 542–557 (experiments/published_claim_match_w5_v1/sources_reading/C03_raw.txt)

Claim content / utility: Yes / No. Original support: None / None. Match: Mismatch / Not claimed.

The interpretation explicitly asserts reliance on the relevant names, name/value associations, or values in zero/few-shot prediction, with equalization at larger training sizes. The complete window does not separately interpret this intervention as semantic knowledge benefiting prediction; observed poorer performance and reliance are not by themselves a utility claim.

### C03-C — TabLLM

List Template vs List Permuted Values

> The discrepancy for zero and very few shots was even stronger for List Permuted Values, which suggests that TabLLM relies more on the correct values than feature names. Again, the performance equalized for more examples showing the ability of TabLLM to learn new associations if enough training data is available.

C03-C-W4: PDF p. 6, source lines 542–557 (experiments/published_claim_match_w5_v1/sources_reading/C03_raw.txt)

Claim content / utility: Yes / No. Original support: Unclear / None. Match: Indeterminate / Not claimed.

The interpretation explicitly asserts reliance on the relevant names, name/value associations, or values in zero/few-shot prediction, with equalization at larger training sizes. The complete window does not separately interpret this intervention as semantic knowledge benefiting prediction; observed poorer performance and reliance are not by themselves a utility claim.

### C04-A — PLATO

Full KG vs Feature-only KG

> We find that both the feature nodes and the broader knowledge nodes are important for PLATO’s performance.

C04-A-W3: PDF p. 9, source lines 509–513 (experiments/published_claim_match_w5_v1/sources_reading/C04_raw.txt)

Claim content / utility: Yes / Yes. Original support: None / Unclear. Match: Mismatch / Indeterminate.

The exact full-KG versus feature-only comparison is explicitly interpreted as improved performance, within a group said to rely on feature and broader-domain information. Both semantic use and predictive utility are claimed on BRCA.

### C04-B — PLATO

Full KG vs No KG

> We find that both the feature nodes and the broader knowledge nodes are important for PLATO’s performance.

C04-B-W3: PDF p. 9, source lines 509–513 (experiments/published_claim_match_w5_v1/sources_reading/C04_raw.txt)

Claim content / utility: Yes / Yes. Original support: None / None. Match: Mismatch / Mismatch.

The Table 3 group explicitly interprets both feature and broader domain information as relied upon and important for predictive performance. This applies to the fixed KG-node comparison on BRCA without borrowing the separate edge-removal result.

### C04-C — PLATO

100% edges vs 50% edges

> We conduct an ablation study to assess PLATO’s robustness to missing edges in the KG.

C04-C-W2: PDF p. 9, source lines 514–520 (experiments/published_claim_match_w5_v1/sources_reading/C04_raw.txt); C04-C-W3: PDF p. 2, source lines 99–105 (experiments/published_claim_match_w5_v1/sources_reading/C04_raw.txt)

Claim content / utility: No / No. Original support: None / None. Match: Not claimed / Not claimed.

The edge comparison is interpreted as robustness to missing information, not as reliance on edge semantic content or a benefit from more knowledge. This is a substantive robustness interpretation rather than purely descriptive reporting; claims about other nodes and architectural embeddings cannot supply either positive axis for this comparison.

### C05-A — CARTE

CARTE vs Graph Construction with Minhash

> The figure shows that each are crucial for gaining the performance of CARTE.

C05-A-W2: PDF p. 21, source lines 1358–1368 (iclr_latex_v3/design_audit/sources/C05_main.txt)

Claim content / utility: Yes / Yes. Original support: None / None. Match: Mismatch / Mismatch.

The named Minhash interpretation links semantic-similarity encoding to effective use of external information, and the group expressly describes the components as crucial for performance. Preserve the emphasis on limited information in the table; the separate attention/context rationale is not needed for this row.

### C05-B — CARTE

CARTE vs Exclude Edge Info.

> In particular, it is interesting to observe the significant decrease with the exclusion of edge information and the attention layer. Since both are essential for leveraging context within a given table, it implies that capturing context is pivotal for attaining the strong performances in predictions.

C05-B-W2: PDF p. 21, source lines 1358–1368 (iclr_latex_v3/design_audit/sources/C05_main.txt)

Claim content / utility: Unclear / Unclear. Original support: None / Unclear. Match: Indeterminate / Indeterminate.

The comparison group expressly claims use and predictive value of table context, but does not distinguish semantic content of edge information from structural or statistical context. Both semantic axes therefore remain ambiguous; the explicit semantic-similarity claim for Minhash cannot transfer to this intervention.

### C05-C — CARTE

CARTE vs Exclude Att. Layer & Edge Info.

> In particular, it is interesting to observe the significant decrease with the exclusion of edge information and the attention layer. Since both are essential for leveraging context within a given table, it implies that capturing context is pivotal for attaining the strong performances in predictions.

C05-C-W2: PDF p. 21, source lines 1358–1368 (iclr_latex_v3/design_audit/sources/C05_main.txt)

Claim content / utility: Unclear / Unclear. Original support: None / None. Match: Indeterminate / Indeterminate.

The comparison group expressly claims use and predictive value of table context, but does not distinguish semantic content of edge information from structural or statistical context. Both semantic axes therefore remain ambiguous; the explicit semantic-similarity claim for Minhash cannot transfer to this intervention.

### C06-A — FeatLLM

FeatLLM vs -Description

> On the other hand, the effect of feature descriptions and reasoning instructions are high when the number of shot is small. This suggests that the efficient utilization of the prior knowledge of LLM becomes crucial for performance improvements.

C06-A-W2: PDF p. 8, source lines 684–696 (experiments/published_claim_match_w5_v1/sources_reading/C06_raw.txt)

Claim content / utility: Yes / Yes. Original support: None / Unclear. Match: Mismatch / Indeterminate.

The description/reasoning group explicitly interprets its effect as utilization of LLM prior knowledge crucial for performance improvement. The claim includes the audited description removal and is strongest when the number of shots is small, without importing tuning or ensemble claims.

### C07-A — TabuLa-8B

TABULA-8B on UniPredict with original headers (descriptive label) vs TABULA-8B with feature headers X1, X2, ... and target header Y (descriptive label)

> We believe that this drop in performance is commensurate to the loss in information when column headers are eliminated.

C07-A-W2: PDF p. 9, source lines 540–546 (iclr_latex_v3/design_audit/sources/C07_main.txt); C07-A-W5: PDF p. 26, source lines 1655–1666 (iclr_latex_v3/design_audit/sources/C07_main.txt)

Claim content / utility: Yes / Yes. Original support: None / Supported. Match: Mismatch / Matched.

The explicitly linked header ablation describes utilization of column-name semantic information and an explicit performance benefit for small shot counts. It also states declining utility as shots increase and robust prediction without rich headers; these qualifications do not erase the conditional positive claims.

### C08-A — ConTextTab

base (feature and column name semantics) vs no feature semantics - Ordinal encoder

> As expected, we observe a significant drop in performance when discarding semantics completely or when using the conventional string encoders from the skrub library. Hence, ConTextTab successfully leverages the semantic content of features.

C08-A-W2: PDF p. 8, source lines 471–479 (iclr_latex_v3/design_audit/sources/C08_main.txt)

Claim content / utility: Yes / No. Original support: None / None. Match: Mismatch / Not claimed.

The feature-encoder group, which names the audited alternative, explicitly concludes that the model leverages feature semantic content on CARTE. Its performance-drop report is interpreted as semantic use, without a separate explicit interpretation of semantic knowledge as a predictive benefit, so the utility axis is No under the conservative rule.

### C08-B — ConTextTab

base (feature and column name semantics) vs no feature semantics - MinHash encoder

> As expected, we observe a significant drop in performance when discarding semantics completely or when using the conventional string encoders from the skrub library. Hence, ConTextTab successfully leverages the semantic content of features.

C08-B-W2: PDF p. 8, source lines 471–479 (iclr_latex_v3/design_audit/sources/C08_main.txt)

Claim content / utility: Yes / No. Original support: None / None. Match: Mismatch / Not claimed.

The feature-encoder group, which names the audited alternative, explicitly concludes that the model leverages feature semantic content on CARTE. Its performance-drop report is interpreted as semantic use, without a separate explicit interpretation of semantic knowledge as a predictive benefit, so the utility axis is No under the conservative rule.

### C08-C — ConTextTab

base (feature and column name semantics) vs no feature semantics - AutoGluon encoder

> As expected, we observe a significant drop in performance when discarding semantics completely or when using the conventional string encoders from the skrub library. Hence, ConTextTab successfully leverages the semantic content of features.

C08-C-W2: PDF p. 8, source lines 471–479 (iclr_latex_v3/design_audit/sources/C08_main.txt)

Claim content / utility: Yes / No. Original support: None / None. Match: Mismatch / Not claimed.

The feature-encoder group, which names the audited alternative, explicitly concludes that the model leverages feature semantic content on CARTE. Its performance-drop report is interpreted as semantic use, without a separate explicit interpretation of semantic knowledge as a predictive benefit, so the utility axis is No under the conservative rule.

### C08-D — ConTextTab

base (feature and column name semantics) vs no feature semantics - Gap encoder

> As expected, we observe a significant drop in performance when discarding semantics completely or when using the conventional string encoders from the skrub library. Hence, ConTextTab successfully leverages the semantic content of features.

C08-D-W2: PDF p. 8, source lines 471–479 (iclr_latex_v3/design_audit/sources/C08_main.txt)

Claim content / utility: Yes / No. Original support: None / None. Match: Mismatch / Not claimed.

The feature-encoder group, which names the audited alternative, explicitly concludes that the model leverages feature semantic content on CARTE. Its performance-drop report is interpreted as semantic use, without a separate explicit interpretation of semantic knowledge as a predictive benefit, so the utility axis is No under the conservative rule.

### C08-E — ConTextTab

base (feature and column name semantics) vs column semantics - drop column names

> Dropping column name semantics indeed results in a performance loss of about [NUM]% in accuracy and [NUM]% in R[NUM] score.

C08-E-W3: PDF p. 8, source lines 480–489 (iclr_latex_v3/design_audit/sources/C08_main.txt); C08-E-W4: PDF p. 8, source lines 490–491 (iclr_latex_v3/design_audit/sources/C08_main.txt)

Claim content / utility: Yes / No. Original support: None / Supported. Match: Mismatch / Not claimed.

The shared closing interpretation explicitly asserts leveraging column-name semantics, covering the removal comparison on CARTE. The local removal statement reports a performance loss but does not separately interpret it as knowledge benefit; the explicit boost statement addresses enrichment, a different comparison.

### C08-F — ConTextTab

column semantics - add description vs base (feature and column name semantics)

> Further enriching column header semantics slightly boosts performance, resulting in a slightly better rank, however with a win rate of [NUM]% at a p-value of [NUM] this is not statistically significant.

C08-F-W3: PDF p. 8, source lines 480–489 (iclr_latex_v3/design_audit/sources/C08_main.txt); C08-F-W4: PDF p. 8, source lines 490–491 (iclr_latex_v3/design_audit/sources/C08_main.txt)

Claim content / utility: Yes / Yes. Original support: None / Unclear. Match: Mismatch / Indeterminate.

The closing semantic interpretation encompasses both column-name interventions, including contextual descriptions, and explicitly claims semantic use. Enrichment is expressly said to boost performance slightly on CARTE, with the stated lack of statistical significance preserved.

### C09-A — TabSTAR

TabSTAR vs Name + Bin

> The addition of the quantile information on top of the bin seems to have limited impact, although marginally winning on the average performance.

C09-A-W4: PDF p. 52, source lines 3103–3107 (iclr_latex_v3/design_audit/sources/C09_main.txt)

Claim content / utility: No / No. Original support: None / Supported. Match: Not claimed / Not claimed.

For quantile addition specifically, the authors interpret the impact as limited and report a marginal average win, without asserting use of quantile semantic content or interpreting semantic knowledge as providing benefit. The substantive limited-impact interpretation prevents descriptive-only coding, and broader numerical-information benefits concern comparisons to Name rather than this incremental quantile intervention.

### C09-B — TabSTAR

TabSTAR vs Name

> our findings reveal that incorporating numerical information significantly enhances performance, highlighting the importance of balancing numerical precision with a representation format that aligns with the language model’s parametric knowledge.

C09-B-W1: PDF p. 9, source lines 542–553 (iclr_latex_v3/design_audit/sources/C09_main.txt); C09-B-W4: PDF p. 52, source lines 3103–3107 (iclr_latex_v3/design_audit/sources/C09_main.txt)

Claim content / utility: No / Yes. Original support: None / Supported. Match: Not claimed / Matched.

The numerical-information group explicitly interprets semantically verbalized numerical information as improving prediction relative to names alone, while retaining dataset-specific limited gains and failures. Describing information injection and benefit does not independently assert reliance on or use of its semantic content, so content is No.

### C10-A — TARTE

TARTE | Enriched YAGO4.5 vs TARTE | Remove column names | Enriched YAGO4.5

> In addition, without datetime detection or column information, properly pre-trained weights still provide competitive representations. This suggests that TARTE can perform well even on tables without meaningful column names.

C10-A-W5: PDF p. 10, source lines 622–629 (iclr_latex_v3/design_audit/sources/C10_author_mirror.txt)

Claim content / utility: Unclear / Unclear. Original support: None / Unclear. Match: Indeterminate / Indeterminate.

The available arXiv v2 text gives a robustness interpretation for missing column names, not a positive use or benefit claim for that information. Equivalence to the accepted published version is unverified, so neither axis can be coded as absent for the published unit; broader pretraining claims do not transfer to header removal.

### C10-B — TARTE

TARTE | Enriched YAGO4.5 vs TARTE | MinHash | Random weights

> First, comparing MinHash to TARTE reveals the importance of FastText.

C10-B-W3: PDF p. 9, source lines 590–593 (iclr_latex_v3/design_audit/sources/C10_author_mirror.txt); C10-B-W6: PDF p. 12, source lines 748–758 (iclr_latex_v3/design_audit/sources/C10_author_mirror.txt)

Claim content / utility: Unclear / Unclear. Original support: None / None. Match: Indeterminate / Indeterminate.

The available arXiv v2 comparison describes semantic similarity in representations and the value of knowledge pretraining for tabular learning, making positive claims plausible in that version. Because equivalence to the accepted published source is unverified, both published-unit axes remain Unclear rather than treating that version as definitive evidence.

