# Factual construction v1.1 — 25 comparisons / 9 studies

Supersedes v1 through CONSTRUCTION_CORRECTION_V1_1.md. No design codes or outcomes.

## C01-A — LIFT

**Semantic component:** Feature names associated with feature values; prompt format I

**Intended arm:** Correct-Names I

**Comparator arm:** Shuffled-Names I

**What changed:** Authors describe randomly shuffling feature names within the corresponding prompt design.

**What remained fixed:** Caption describes the same LIFT/GPT-3 tabular tasks and paired prompt-format family; exact name/value inventory in the supplementary example is not consistently shown.

**Other simultaneous changes:** D.2.1 example I repeats semester; example II changes the rendered value sequence and repeats summer. Authors explicitly note that format-II shuffled sentences may be incoherent. Whether the example inconsistencies reflect executed templates is not stated.

**Predictive interface:** 불명 — same LM text-input/output scheme is described, but the printed examples do not establish consistent field/value routing.

**Evidence:** Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.


## C01-B — LIFT

**Semantic component:** Feature names associated with feature values; prompt format II

**Intended arm:** Correct-Names II

**Comparator arm:** Shuffled-Names II

**What changed:** Authors describe randomly shuffling feature names within the corresponding prompt design.

**What remained fixed:** Caption describes the same LIFT/GPT-3 tabular tasks and paired prompt-format family; exact name/value inventory in the supplementary example is not consistently shown.

**Other simultaneous changes:** D.2.1 example I repeats semester; example II changes the rendered value sequence and repeats summer. Authors explicitly note that format-II shuffled sentences may be incoherent. Whether the example inconsistencies reflect executed templates is not stated.

**Predictive interface:** 불명 — same LM text-input/output scheme is described, but the printed examples do not establish consistent field/value routing.

**Evidence:** Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.


## C01-C — LIFT

**Semantic component:** Names and contextual information in prompts; prompt format I

**Intended arm:** Correct-Names I

**Comparator arm:** W/o Names I (Table 9)

**What changed:** Compare named prompts with unnamed/generic-index prompts; the table distinguishes two formats.

**What remained fixed:** Same reported learner and task family. Supplement gives one generic W/O Names example, not a full per-dataset expansion of both table variants.

**Other simultaneous changes:** Worked example replaces the named task question with generic y and category words with numerical codes; format II also differs from the generic sentence form. Exact correspondence to both unnamed table variants is not fully specified.

**Predictive interface:** 불명 — the same LM text-input/output framework is used, but the worked example also changes target/category representation and does not fully specify the mapping for both unnamed variants.

**Evidence:** Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.


## C01-D — LIFT

**Semantic component:** Names and contextual information in prompts; prompt format II

**Intended arm:** Correct-Names II

**Comparator arm:** W/o Names II (Table 9)

**What changed:** Compare named prompts with unnamed/generic-index prompts; the table distinguishes two formats.

**What remained fixed:** Same reported learner and task family. Supplement gives one generic W/O Names example, not a full per-dataset expansion of both table variants.

**Other simultaneous changes:** Worked example replaces the named task question with generic y and category words with numerical codes; format II also differs from the generic sentence form. Exact correspondence to both unnamed table variants is not fully specified.

**Predictive interface:** 불명 — the same LM text-input/output framework is used, but the worked example also changes target/category representation and does not fully specify the mapping for both unnamed variants.

**Evidence:** Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.


## C03-A — TabLLM

**Semantic component:** Column-name/value associations

**Intended arm:** List Template

**Comparator arm:** List Permuted Names

**What changed:** Apply a permutation to column names; the same permutation is used across examples.

**What remained fixed:** Defined as List Template with permuted names: values, column positions and list form are retained by that definition; shared T0/fine-tuning setup is described globally.

**Other simultaneous changes:** No additional intervention specified. The text does not require a derangement with no fixed points.

**Predictive interface:** 동일 — List Template text serialization and LM prediction interface.

**Evidence:** Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.


## C03-B — TabLLM

**Semantic component:** Column names in list serialization

**Intended arm:** List Template

**Comparator arm:** List Only Values

**What changed:** Serialize feature values only rather than column-name/value pairs.

**What remained fixed:** Value list and common task/learner recipe are described; the original list fixes an arbitrary column order.

**Other simultaneous changes:** Field-name text and associated name/value list scaffolding are omitted; this is not described as replacement by generic field-name tokens.

**Predictive interface:** 동일 — LM receives text and predicts the same target; serialization structure changes.

**Evidence:** Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.


## C03-C — TabLLM

**Semantic component:** Column-value meanings and representations

**Intended arm:** List Template

**Comparator arm:** List Permuted Values

**What changed:** Generate one value permutation per column and apply it across all examples.

**What remained fixed:** Column names and List Template family; mapping is explicitly shared across examples.

**Other simultaneous changes:** Continuous values are put into ten uniform bins before the value mapping.

**Predictive interface:** 동일 — same list-to-LM prediction scheme with altered value tokens.

**Evidence:** Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.


## C04-A — PLATO

**Semantic component:** Auxiliary feature nodes and broader-domain KG nodes

**Intended arm:** Full KG

**Comparator arm:** Feature-only KG

**What changed:** Use the induced subgraph on feature nodes instead of the full graph including broader-domain nodes.

**What remained fixed:** BRCA prediction task and PLATO family; feature nodes remain. Same recipe is described at study level.

**Other simultaneous changes:** Graph size/neighborhoods change. Recomputing versus retaining pretrained KG embeddings is not specified for this contrast.

**Predictive interface:** 동일 — feature nodes feed the PLATO weight-inference/prediction scheme; exact embedding construction is unspecified.

**Evidence:** Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.


## C04-B — PLATO

**Semantic component:** Auxiliary KG input

**Intended arm:** Full KG

**Comparator arm:** No KG

**What changed:** Remove access to the auxiliary KG.

**What remained fixed:** Same BRCA tabular prediction task and observed feature/target definition.

**Other simultaneous changes:** Paper explicitly states the no-KG configuration becomes a standard MLP, replacing KG-derived first-layer weight inference.

**Predictive interface:** 변경 — KG-to-weight construction is replaced by standard MLP fitting; external tabular input/target interface remains.

**Evidence:** Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.


## C04-C — PLATO

**Semantic component:** KG edges

**Intended arm:** 100% edges

**Comparator arm:** 50% edges

**What changed:** Randomly remove KG edges to retain the fraction reported in Table 4.

**What remained fixed:** BRCA task and PLATO model family.

**Other simultaneous changes:** Connectivity changes; handling/retraining of pretrained node embeddings is not specified in the ablation description.

**Predictive interface:** 동일 — graph message-passing predictor with a sparser graph; node-embedding details are unspecified.

**Evidence:** Official C04 §4.1 p.9, Table 4.


## C05-A — CARTE

**Semantic component:** String feature initialization

**Intended arm:** CARTE

**Comparator arm:** Graph Construction with Minhash

**What changed:** Replace feature initialization with skrub MinHash encoding based on string n-grams.

**What remained fixed:** Reported within the CARTE component study with the same train-size range; exact per-arm initialization/training alignment is not provided.

**Other simultaneous changes:** The feature encoder changes; resulting dimensions, numerical-feature handling, and compatibility adaptation are not specified in C.3.

**Predictive interface:** 변경 — string-to-vector encoder is replaced; downstream tensor compatibility details are 불명.

**Evidence:** Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.


## C05-B — CARTE

**Semantic component:** Column/edge information

**Intended arm:** CARTE

**Comparator arm:** Exclude Edge Info.

**What changed:** Figure label specifies exclusion of edge information.

**What remained fixed:** Same component-study family and training-size range; exact implementation of the exclusion is not supplied.

**Other simultaneous changes:** Main architecture also uses column embeddings in numerical-node initialization. The ablation text does not state whether that initialization is altered.

**Predictive interface:** 불명 — zeroing/remapping edge vectors versus deleting edge-conditioned computation is not described.

**Evidence:** Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.


## C05-C — CARTE

**Semantic component:** Edge information with attention component

**Intended arm:** CARTE

**Comparator arm:** Exclude Att. Layer & Edge Info.

**What changed:** Exclude both the attention layer and edge information, as named in the figure.

**What remained fixed:** Same component-study task family and train-size range.

**Other simultaneous changes:** Attention-layer removal accompanies edge-information exclusion; exact replacement computation is unspecified.

**Predictive interface:** 변경 — attention architecture is altered; resulting routing details are 불명.

**Evidence:** Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.


## C06-A — FeatLLM

**Semantic component:** Feature-description block in rule generation

**Intended arm:** FeatLLM

**Comparator arm:** -Description

**What changed:** Omit feature descriptions when generating rules.

**What remained fixed:** Authors present this as one component ablation; task/examples, parser, ensemble and tuning are described by the common recipe, not by a fully printed ablated prompt.

**Other simultaneous changes:** Descriptions include value types, optional definitions and category examples/inventories. Rules and their binary features are generated anew; exact ablated prompt and per-arm error handling are not specified.

**Predictive interface:** 불명 — common generate/parse/binary-feature pipeline is described, but type-compatible parsing after removal is not detailed.

**Evidence:** Official C06 §3.1/Figure 2 pp.3–4, §4.2/Table 4 pp.7–8, Appendix A.2 and K.2/Table 18; supplied featllm.pdf corroborates prompt components.


## C07-A — TabuLa-8B

**Semantic component:** Informative feature and target headers

**Intended arm:** TABULA-8B on UniPredict with original headers (descriptive label)

**Comparator arm:** TABULA-8B with feature headers X1, X2, ... and target header Y (descriptive label)

**What changed:** Replace original feature headers by indexed names and replace the target header by Y.

**What remained fixed:** F.2 explicitly says the data themselves are not altered; evaluation uses TABULA-8B on the modified tables.

**Other simultaneous changes:** Target-header replacement accompanies feature-header replacement; no extra intervention is specified.

**Predictive interface:** 동일 — replacement strings occupy header positions in the same tabular-LM evaluation scheme.

**Evidence:** Official C07 §5.5, Appendix F.2 p.26/Figure 12 p.27; supplied tabula.pdf has different pagination.


## C08-A — ConTextTab

**Semantic component:** Categorical/string feature encoding

**Intended arm:** base (feature and column name semantics)

**Comparator arm:** no feature semantics - Ordinal encoder

**What changed:** Replace categorical/string semantic feature encodings with Ordinal encoder.

**What remained fixed:** Semantic ablations are run on the CARTE benchmark; Table 2 identifies the one-dimensional-embedding base. Other settings follow the shared description; per-encoder adaptation details are not given.

**Other simultaneous changes:** Encoding algorithm/representation changes; exact dimension, initialization and adaptation details are not reported for each variant.

**Predictive interface:** 변경 — feature encoding path changes; precise downstream compatibility is 불명.

**Evidence:** Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.


## C08-B — ConTextTab

**Semantic component:** Categorical/string feature encoding

**Intended arm:** base (feature and column name semantics)

**Comparator arm:** no feature semantics - MinHash encoder

**What changed:** Replace categorical/string semantic feature encodings with MinHash encoder.

**What remained fixed:** Semantic ablations are run on the CARTE benchmark; Table 2 identifies the one-dimensional-embedding base. Other settings follow the shared description; per-encoder adaptation details are not given.

**Other simultaneous changes:** Encoding algorithm/representation changes; exact dimension, initialization and adaptation details are not reported for each variant.

**Predictive interface:** 변경 — feature encoding path changes; precise downstream compatibility is 불명.

**Evidence:** Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.


## C08-C — ConTextTab

**Semantic component:** Categorical/string feature encoding

**Intended arm:** base (feature and column name semantics)

**Comparator arm:** no feature semantics - AutoGluon encoder

**What changed:** Replace categorical/string semantic feature encodings with AutoGluon encoder.

**What remained fixed:** Semantic ablations are run on the CARTE benchmark; Table 2 identifies the one-dimensional-embedding base. Other settings follow the shared description; per-encoder adaptation details are not given.

**Other simultaneous changes:** Encoding algorithm/representation changes; exact dimension, initialization and adaptation details are not reported for each variant.

**Predictive interface:** 변경 — feature encoding path changes; precise downstream compatibility is 불명.

**Evidence:** Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.


## C08-D — ConTextTab

**Semantic component:** Categorical/string feature encoding

**Intended arm:** base (feature and column name semantics)

**Comparator arm:** no feature semantics - Gap encoder

**What changed:** Replace categorical/string semantic feature encodings with Gap encoder.

**What remained fixed:** Semantic ablations are run on the CARTE benchmark; Table 2 identifies the one-dimensional-embedding base. Other settings follow the shared description; per-encoder adaptation details are not given.

**Other simultaneous changes:** Encoding algorithm/representation changes; exact dimension, initialization and adaptation details are not reported for each variant.

**Predictive interface:** 변경 — feature encoding path changes; precise downstream compatibility is 불명.

**Evidence:** Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.


## C08-E — ConTextTab

**Semantic component:** Column-name encoding

**Intended arm:** base (feature and column name semantics)

**Comparator arm:** column semantics - drop column names

**What changed:** Replace names by col1, ..., colN, as stated in §5.1.

**What remained fixed:** Column slots remain named by indexed strings; same semantic-ablation benchmark and base-model description.

**Other simultaneous changes:** No additional intervention specified; this is name replacement, not removal of table columns.

**Predictive interface:** 동일 — names remain string inputs to the column-name encoding path.

**Evidence:** Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.


## C08-F — ConTextTab

**Semantic component:** Additional contextual column descriptions

**Intended arm:** column semantics - add description

**Comparator arm:** base (feature and column name semantics)

**What changed:** Enriched arm uses <name>:<description> in place of the original name; comparator uses the original name. Direction here treats enrichment as the intended use.

**What remained fixed:** Original name is retained as a prefix; same semantic-ablation benchmark/model family.

**Other simultaneous changes:** Descriptions are generated with gemma3-12b from five randomly sampled JSON-serialized rows. Which split/target information those rows expose is not specified in the quoted construction.

**Predictive interface:** 동일 — enriched strings occupy the name-encoding path; description-generation access policy is unspecified.

**Evidence:** Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.


## C09-A — TabSTAR

**Semantic component:** Quantile text in numerical verbalization

**Intended arm:** TabSTAR

**Comparator arm:** Name + Bin

**What changed:** Remove quantile information from the numerical verbalization.

**What remained fixed:** Name and bin information remain by variant definition. The general architecture has a separate numerical-input branch; Q3 describes a verbalization change and states no removal of that branch.

**Other simultaneous changes:** No additional intervention specified; per-variant checkpoint/training matching is not separately detailed.

**Predictive interface:** 동일 — numerical/semantic fusion architecture is described as common; semantic text content changes.

**Evidence:** Official C09 §4/A.1, §6 Q3 p.9/Table 4 p.10, Appendix G.4/Tables 31–32 pp.53–54; supplied tabstar.pdf has different pagination.


## C09-B — TabSTAR

**Semantic component:** Numerical information in verbalized features

**Intended arm:** TabSTAR

**Comparator arm:** Name

**What changed:** Remove numeric content from verbalization; illustrative entries retain a name and generic Numeric marker.

**What remained fixed:** Numerical-input branch remains in the common architecture; Q3 changes verbalization and does not state that numerical inputs are deleted.

**Other simultaneous changes:** Bin and quantile wording are both absent in this variant; missing-value examples remain separately illustrated.

**Predictive interface:** 동일 — common numeric/semantic architecture; this statement does not verify per-arm execution.

**Evidence:** Official C09 §4/A.1, §6 Q3 p.9/Table 4 p.10, Appendix G.4/Tables 31–32 pp.53–54; supplied tabstar.pdf has different pagination.


## C10-A — TARTE

**Semantic component:** Column-name information

**Intended arm:** TARTE | Enriched YAGO4.5

**Comparator arm:** TARTE | Remove column names | Enriched YAGO4.5

**What changed:** Figure names a variant without column-name information.

**What remained fixed:** Both labels specify Enriched YAGO4.5; caption uses Ridge on extracted representations. Exact checkpoint equality is not specified.

**Other simultaneous changes:** Not specified whether names are replaced, embeddings zeroed, or a pathway omitted; effects on numerical-value initialization are not described in the published extract.

**Predictive interface:** 불명 — exact name-removal and numerical-routing construction is not established.

**Evidence:** C10 official indexed published Figure 6 p.10/§4.3 from eligibility screening; supplied tarte.pdf is arXiv v2 corroboration, not the accepted PDF. Conditions known, implementation details not fully established from published source.


## C10-B — TARTE

**Semantic component:** String encoder and table pretraining

**Intended arm:** TARTE | Enriched YAGO4.5

**Comparator arm:** TARTE | MinHash | Random weights

**What changed:** Published figure includes a MinHash string-encoder variant with randomly initialized table-model weights.

**What remained fixed:** TARTE family and Ridge-on-embeddings evaluation are named; exact matching of random initialization and dimensions is unspecified.

**Other simultaneous changes:** Encoder and table-pretraining status both differ from the Enriched YAGO4.5 baseline. A FastText/Random weights arm is also plotted but is not turned into an additional auditor-created pair here.

**Predictive interface:** 변경 — string encoder changes; downstream tensor/numerical routing details are 불명.

**Evidence:** C10 official indexed published Figure 6 p.10/§4.3 from eligibility screening; supplied tarte.pdf is arXiv v2 corroboration, not the accepted PDF. Conditions known, implementation details not fully established from published source.

