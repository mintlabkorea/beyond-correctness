# Published semantic-knowledge design audit v1

**9 studies; 28 scoped comparison rows.** C06-01/02 are two estimands for one experiment; TARTE pairings share arms. Do not treat row count as independent evidence.

All codes concern design identifiability, not observed effects. See [CODEBOOK_V1.md](CODEBOOK_V1.md) for Pass/Fail/Unclear and Yes/No/Partial definitions.

The complete requested 14 fields plus row ID are in [DESIGN_AUDIT_V1.csv](DESIGN_AUDIT_V1.csv). This readable view gives gates first, followed by exact conditions, protected information, and evidence for every row.

| ID | Study | Wrong-like | Removal-like | Removal | Preservation | Interface | Admissible utility reference | Content sensitivity | Predictive utility |
|---|---|---|---|---|---|---|---|---|---|
| C01-01 | LIFT | Yes | No | Fail | Unclear | Unclear | No | Partial | No |
| C01-02 | LIFT | Yes | No | Fail | Unclear | Unclear | No | Partial | No |
| C01-03 | LIFT | No | Yes | Pass | Fail | Pass | No | No | No |
| C01-04 | LIFT | No | Yes | Pass | Fail | Pass | No | No | No |
| C03-01 | TabLLM | Yes | No | Fail | Pass | Pass | No | Yes | No |
| C03-02 | TabLLM | No | Yes | Pass | Fail | Pass | No | No | No |
| C03-03 | TabLLM | Yes | No | Fail | Fail | Pass | No | Partial | No |
| C04-01 | PLATO | No | Yes | Unclear | Unclear | Pass | Unclear | No | Partial |
| C04-02 | PLATO | No | Yes | Pass | Fail | Pass | No | No | No |
| C04-03 | PLATO | No | Yes | Fail | Unclear | Pass | No | No | No |
| C05-01 | CARTE | No | Yes | Pass | Fail | Unclear | No | No | No |
| C05-02 | CARTE | No | Yes | Unclear | Unclear | Unclear | Unclear | No | Partial |
| C05-03 | CARTE | No | Yes | Unclear | Fail | Unclear | No | No | No |
| C06-01 | FeatLLM | No | Yes | Pass | Fail | Unclear | No | No | No |
| C06-02 | FeatLLM | No | Yes | Pass | Pass | Unclear | Unclear | No | Partial |
| C06-03 | FeatLLM | No | Yes | Pass | Pass | Unclear | Unclear | No | Partial |
| C07-01 | TabuLa-8B | No | Yes | Pass | Pass | Pass | Yes | No | Yes |
| C08-01 | ConTextTab | No | Yes | Pass | Fail | Unclear | No | No | No |
| C08-02 | ConTextTab | No | Yes | Pass | Fail | Unclear | No | No | No |
| C08-03 | ConTextTab | No | Yes | Pass | Fail | Unclear | No | No | No |
| C08-04 | ConTextTab | No | Yes | Pass | Fail | Unclear | No | No | No |
| C08-05 | ConTextTab | No | Yes | Pass | Pass | Pass | Yes | No | Yes |
| C08-06 | ConTextTab | No | Yes | Pass | Unclear | Pass | Unclear | No | Partial |
| C09-01 | TabSTAR | No | Yes | Pass | Pass | Pass | Yes | No | Yes |
| C09-02 | TabSTAR | No | Yes | Pass | Pass | Pass | Yes | No | Yes |
| C10-01 | TARTE | No | Yes | Unclear | Unclear | Unclear | Unclear | No | Partial |
| C10-02 | TARTE | No | Yes | Pass | Fail | Unclear | No | No | No |
| C10-03 | TARTE | No | Yes | Pass | Fail | Unclear | No | No | No |

## C01-01 — LIFT

**Semantic component:** Feature-name/value association, prompt format I

**Intended condition:** Correct-Names I

**Comparator:** Shuffled-Names I

**Intervention type:** shuffle

**Protected information/setup:** Values and their multiplicities, target question, name inventory, prompt-I structure, training recipe

**Rationale:** The condition is a name shuffle, not absence of names. However, the published supplementary example repeats semester and does not present a clean bijection of the listed names. This may be a typographical error, but the paper alone does not resolve it. Do not certify cardinality or exact preservation from the caption alone; no execution failure is asserted.

**Evidence:** C01 official main §4.1, Table 9 (p.8); official supplement D.2.1 (printed pp.42–44)


## C01-02 — LIFT

**Semantic component:** Feature-name/value association, prompt format II

**Intended condition:** Correct-Names II

**Comparator:** Shuffled-Names II

**Intervention type:** shuffle; compound

**Protected information/setup:** Values and their multiplicities, target question, linguistic template, training recipe

**Rationale:** The supplement acknowledges incoherent sentences; incoherence alone is not interface invalidity. Its worked shuffled example also appears to repeat or omit values relative to the intended example. Exact value/routing preservation is unresolved, so this is only a partial content-sensitivity design, not an established clean permutation.

**Evidence:** C01 official main §4.1, Table 9 (p.8); official supplement D.2.1 (printed pp.42–44)


## C01-03 — LIFT

**Semantic component:** Feature-name semantics conditional on other prompt information, format I

**Intended condition:** Correct-Names I

**Comparator:** W/o Names I (Table 9 label)

**Intervention type:** removal; replacement; compound

**Protected information/setup:** Target description, value rendering, format-specific scaffolding, predictor and learning recipe

**Rationale:** The main table has two unnamed variants; the supplement illustrates a generic indexed prompt rather than literal absence of identifiers. The example also changes the named task question to generic y and textual categories to codes; format II additionally changes sentence scaffolding. Thus names are withdrawn, but feature-name-only utility is not isolated. The generic input remains valid language-model input; exact dataset-wise unnamed templates are not fully supplied.

**Evidence:** C01 official main §4.1, Table 9 (p.8); official supplement D.2.1 (printed pp.42–44)


## C01-04 — LIFT

**Semantic component:** Feature-name semantics conditional on other prompt information, format II

**Intended condition:** Correct-Names II

**Comparator:** W/o Names II (Table 9 label)

**Intervention type:** removal; replacement; compound

**Protected information/setup:** Target description, value rendering, format-specific scaffolding, predictor and learning recipe

**Rationale:** The main table has two unnamed variants; the supplement illustrates a generic indexed prompt rather than literal absence of identifiers. The example also changes the named task question to generic y and textual categories to codes; format II additionally changes sentence scaffolding. Thus names are withdrawn, but feature-name-only utility is not isolated. The generic input remains valid language-model input; exact dataset-wise unnamed templates are not fully supplied.

**Evidence:** C01 official main §4.1, Table 9 (p.8); official supplement D.2.1 (printed pp.42–44)


## C03-01 — TabLLM

**Semantic component:** Feature-name/value association

**Intended condition:** List Template

**Comparator:** List Permuted Names

**Intervention type:** shuffle

**Protected information/setup:** Field order, values, list scaffolding, task prompt, T0 and tuning protocol

**Rationale:** The paper specifies one name permutation shared across examples. Names remain semantic but are assigned to other fields; this preserves the list/value contract and supports intended–wrong content sensitivity. Derangement is not guaranteed, so the claim is sensitivity to the published permutation, not to every field being wrong.

**Evidence:** C03 official §3 (PDF pp.3–4), §5.1/Figure 2 (p.6), supplementary Tables 12–14 and §9


## C03-02 — TabLLM

**Semantic component:** Feature-name semantics conditional on List Template structure

**Intended condition:** List Template

**Comparator:** List Only Values

**Intervention type:** removal; compound

**Protected information/setup:** List field scaffolding and stable explicit field identifiers, ordered values, task prompt, learner

**Rationale:** The comparator removes names along with their field-label scaffolding rather than substituting neutral names in the same List Template. Ordered values may remain, but that does not preserve the claim-specific serialization contract. It is valid LM input. This coding is consistent with the existing manuscript; its format-preservation requirement is an auditor-defined estimand, not an original-author requirement.

**Evidence:** C03 official §3 (PDF pp.3–4), §5.1/Figure 2 (p.6), supplementary Tables 12–14 and §9


## C03-03 — TabLLM

**Semantic component:** Value meaning, including continuous-value information

**Intended condition:** List Template

**Comparator:** List Permuted Values

**Intervention type:** shuffle; corruption; compound

**Protected information/setup:** Continuous resolution, value/type representation, feature names and template, learner

**Rationale:** Per-column value mappings are shared across examples, but continuous values are first binned into ten uniform bins. The pooled contrast therefore changes resolution as well as meaning. A separately specified categorical-only bijection might admit a cleaner content contrast; this mixed published condition is Partial, and it is not an absence reference.

**Evidence:** C03 official §3 (PDF pp.3–4), §5.1/Figure 2 (p.6), supplementary Tables 12–14 and §9


## C04-01 — PLATO

**Semantic component:** Broader-domain KG information beyond feature nodes

**Intended condition:** Full KG

**Comparator:** Feature-only KG

**Intervention type:** removal

**Protected information/setup:** Feature nodes and observations, non-tested feature information, MLP weight-inference recipe

**Rationale:** The induced feature-node subgraph removes the broader nodes from message passing. The model also uses pretrained KG embeddings; the published ablation does not fully state whether these are rebuilt without broader-domain information. Their retained content and the non-tested embedding setup are unresolved. Subgraph deletion itself is not automatically a preservation violation. Feature nodes still provide the specified input/output interface.

**Evidence:** C04 Ruiz et al. official §3.1–3.2, §4.1; Table 3 (p.7), construction (p.9)


## C04-02 — PLATO

**Semantic component:** Auxiliary KG contribution with the KG-enabled predictive setup protected

**Intended condition:** Full KG

**Comparator:** No KG (standard MLP)

**Intervention type:** removal; compound

**Protected information/setup:** Tabular observations and KG-enabled weight-inference architecture/training setup

**Rationale:** The paper explicitly ablates to a standard MLP without KG access. Removal passes; preservation fails because the feature-weight generation mechanism changes. Both models still accept tabular predictors and predict the same target, so this architecture change is not itself an input/output interface failure. Only a broader architecture-plus-knowledge comparison is available.

**Evidence:** C04 Ruiz et al. official §3.1–3.2, §4.1; Table 3 (p.7), construction (p.9)


## C04-03 — PLATO

**Semantic component:** Complete supplied KG relational information

**Intended condition:** 100% KG edges

**Comparator:** 50% KG edges (random edge deletion)

**Intervention type:** removal

**Protected information/setup:** Feature observations, non-tested node features/embeddings, same learner

**Rationale:** This is a partial missing-edge robustness condition: half the edges remain, and deleting facts does not assert false facts. It is neither absence of the full tested KG use nor a matched-wrong graph. Whether embeddings are recomputed is unspecified. Graph sparsification is compatible with the message-passing interface as described.

**Evidence:** C04 official §4.1 (p.9), Table 4


## C05-01 — CARTE

**Semantic component:** Language-semantic feature initialization, conditional on encoder/predictor setup

**Intended condition:** CARTE

**Comparator:** Graph Construction with Minhash

**Intervention type:** replacement; compound

**Protected information/setup:** Encoder family/geometry, value and field information, graph predictor and training recipe

**Rationale:** MinHash replaces the semantic initialization channel by an n-gram string encoder. Removal is limited to that language-semantic channel, not all knowledge in pretrained CARTE. Encoder identity and representation geometry change, failing the protected setup. Dimensions, collision handling, and compatibility with the pretrained graph model are not specified sufficiently for an interface Pass.

**Evidence:** C05 official §3/architecture, Appendix C.3 and Figure 10 (p.21)


## C05-02 — CARTE

**Semantic component:** Column semantics carried by edge information

**Intended condition:** CARTE

**Comparator:** Exclude Edge Info.

**Intervention type:** removal; compound

**Protected information/setup:** Value-bearing node initializations and multiplicities, graph architecture/routing

**Rationale:** Numerical nodes are initialized using column-name embeddings as well as numerical values. The label Exclude Edge Info. does not specify whether that pathway is retained, nor whether edge vectors are neutralized or the edge-conditioned computation is changed. Thus complete removal and protected numeric routing are unresolved. Do not infer clean name removal from a plot label.

**Evidence:** C05 official §3/architecture, Appendix C.3 and Figure 10 (p.21)


## C05-03 — CARTE

**Semantic component:** Column semantics carried by edge information

**Intended condition:** CARTE

**Comparator:** Exclude Att. Layer & Edge Info.

**Intervention type:** removal; compound

**Protected information/setup:** Attention architecture, value-bearing node initializations, same graph predictor

**Rationale:** The condition expressly removes attention as well as edge information, so the protected model changes. Whether column information persists in numerical-node initialization remains unclear; post-removal routing/shape handling is also unspecified. This is not an admissible component-specific reference.

**Evidence:** C05 official §3/architecture, Appendix C.3 and Figure 10 (p.21)


## C06-01 — FeatLLM

**Semantic component:** Feature-definition prose, conditional on type/category metadata

**Intended condition:** FeatLLM

**Comparator:** -Description

**Intervention type:** removal; compound

**Protected information/setup:** Types, category inventory, task/examples, generation/parser instructions and learner policy

**Rationale:** The feature-description block includes value types and sometimes category inventories, not just explanatory prose. Omitting the block also withdraws protected schema information used to generate type-compatible rules. The ablated prompt and per-arm type/error handling are not documented sufficiently for interface validation. Changes in generated rules are mediators, not the reason for the Preservation failure.

**Evidence:** C06 official §3.1/Figure 2 (pp.3–4), §4.2/Table 4 (pp.7–8), Appendix A.2, K.2/Table 18


## C06-02 — FeatLLM

**Semantic component:** Entire supplied feature-description block (definitions, types, category information)

**Intended condition:** FeatLLM

**Comparator:** -Description

**Intervention type:** removal

**Protected information/setup:** Task description, demonstrations, model/generation/parser recipe, feature-count and tuning policy

**Rationale:** Scope alternative to C06-01, not another experiment. With all block contents declared tested, their removal is allowed; the reported single-component ablation retains the remaining recipe at design level. However, type-guided generation/parsing without that block is insufficiently documented. Rule changes do not automatically violate preservation. Utility remains conditional on interface clarification.

**Evidence:** C06 official §3.1/Figure 2 (pp.3–4), §4.2/Table 4 (pp.7–8), Appendix A.2, K.2/Table 18


## C06-03 — FeatLLM

**Semantic component:** Use of the Step-1 reasoning instruction during rule generation

**Intended condition:** FeatLLM (two-step generation)

**Comparator:** -Reasoning

**Intervention type:** removal

**Protected information/setup:** Task/feature metadata, demonstrations, rule budget, parser and downstream learner policy

**Rationale:** Step 1 is omitted; this removes an elicitation procedure, not all semantic knowledge in the LM or all feature descriptions. Under this narrow procedural scope, generated-rule changes are allowed mediators. Step 2 references Step 1, and the exact edited prompt/output contract is not given, so interface compatibility remains unresolved. Do not interpret this row as utility of supplied factual relation content.

**Evidence:** C06 official §3.1/Figure 2 (pp.3–4), §4.2/Table 4 (pp.7–8), Appendix A.2, K.2/Table 18


## C07-01 — TabuLa-8B

**Semantic component:** Joint feature-header and target-header semantic content

**Intended condition:** TABULA-8B with original UniPredict headers

**Comparator:** TABULA-8B with feature headers X1, X2, ... and target header Y

**Intervention type:** replacement

**Protected information/setup:** Table values, feature identity and positions, target values, serialization and model/evaluation policy

**Rationale:** F.2 explicitly changes headers only and evaluates the same model on the data. Stable indexed feature names and Y remain valid headers. This is a design-admissible reference for the joint header-content scope, not absence of all pretrained knowledge. A feature-name-only scope protecting the original target header would instead fail Preservation. Pass is not a runtime/token-budget audit or a claim of positive utility.

**Evidence:** C07 official §5.5; Appendix F.2 (p.26), Figure 12 (p.27)


## C08-01 — ConTextTab

**Semantic component:** LLM-based categorical/string feature semantics, conditional on encoder setup

**Intended condition:** base (feature and column name semantics)

**Comparator:** no feature semantics - Ordinal encoder

**Intervention type:** replacement; compound

**Protected information/setup:** Encoder family/representation, non-tested column metadata, numerical values, model/training policy

**Rationale:** Ordinal identifiers discard language-semantic similarity and change the encoder/representation family. Removal is only of the declared LLM feature-embedding channel. The nominal same-learner experiment does not demonstrate unchanged representation dimensionality, initialization or routing for each encoder. These are representation comparisons, not misinformation controls.

**Evidence:** C08 official §5.1 (p.8), Table 2 bottom block (p.9), Appendix A.4, Figures 9–10 (pp.27–28)


## C08-02 — ConTextTab

**Semantic component:** LLM-based categorical/string feature semantics, conditional on encoder setup

**Intended condition:** base (feature and column name semantics)

**Comparator:** no feature semantics - MinHash encoder

**Intervention type:** replacement; compound

**Protected information/setup:** Encoder family/representation, non-tested column metadata, numerical values, model/training policy

**Rationale:** Morphological hashing replaces the semantic embedding channel and changes its geometry/collision properties. Removal is only of the declared LLM feature-embedding channel. The nominal same-learner experiment does not demonstrate unchanged representation dimensionality, initialization or routing for each encoder. These are representation comparisons, not misinformation controls.

**Evidence:** C08 official §5.1 (p.8), Table 2 bottom block (p.9), Appendix A.4, Figures 9–10 (pp.27–28)


## C08-03 — ConTextTab

**Semantic component:** LLM-based categorical/string feature semantics, conditional on encoder setup

**Intended condition:** base (feature and column name semantics)

**Comparator:** no feature semantics - AutoGluon encoder

**Intervention type:** replacement; compound

**Protected information/setup:** Encoder family/representation, non-tested column metadata, numerical values, model/training policy

**Rationale:** A conventional feature-preprocessing pipeline replaces the semantic encoding pipeline. Removal is only of the declared LLM feature-embedding channel. The nominal same-learner experiment does not demonstrate unchanged representation dimensionality, initialization or routing for each encoder. These are representation comparisons, not misinformation controls.

**Evidence:** C08 official §5.1 (p.8), Table 2 bottom block (p.9), Appendix A.4, Figures 9–10 (pp.27–28)


## C08-04 — ConTextTab

**Semantic component:** LLM-based categorical/string feature semantics, conditional on encoder setup

**Intended condition:** base (feature and column name semantics)

**Comparator:** no feature semantics - Gap encoder

**Intervention type:** replacement; compound

**Protected information/setup:** Encoder family/representation, non-tested column metadata, numerical values, model/training policy

**Rationale:** Character-string decomposition replaces semantic embeddings with a different representational basis. Removal is only of the declared LLM feature-embedding channel. The nominal same-learner experiment does not demonstrate unchanged representation dimensionality, initialization or routing for each encoder. These are representation comparisons, not misinformation controls.

**Evidence:** C08 official §5.1 (p.8), Table 2 bottom block (p.9), Appendix A.4, Figures 9–10 (pp.27–28)


## C08-05 — ConTextTab

**Semantic component:** Supplied column-header semantic content

**Intended condition:** base (feature and column name semantics)

**Comparator:** column semantics - drop column names (col1, ..., colN)

**Intervention type:** replacement

**Protected information/setup:** Cell contents, stable field positions/identities, semantic cell encoder, header-input path and evaluation policy

**Rationale:** The text explicitly describes generic-name replacement, not deleting columns. It preserves a header at every field in the same semantic-encoding pathway; column-name meaning is the tested span. This supports reference-relative design identification without claiming numerical invariance or runtime validation.

**Evidence:** C08 official §5.1 (p.8), Table 2 bottom block (p.9), Appendix A.4, Figures 9–10 (pp.27–28)


## C08-06 — ConTextTab

**Semantic component:** Additional LLM-generated contextual column descriptions

**Intended condition:** column semantics - add description (<name>:<description>)

**Comparator:** base (original column names only)

**Intervention type:** removal

**Protected information/setup:** Original names, cell data, evaluation population, generation access policy, same model/encoder

**Rationale:** Both variants are published; the intended direction is the enriched condition for this incremental-description scope. Generated descriptions use five sampled rows. It is not specified sufficiently whether that generation access is restricted to the same allowed context, especially relative to evaluation rows/targets. Removing descriptions is clear and the text interface stays valid, but protected information access is unresolved. No generated description is assumed correct by default.

**Evidence:** C08 official §5.1 (p.8), Table 2 bottom block (p.9), Appendix A.4, Figures 9–10 (pp.27–28)


## C09-01 — TabSTAR

**Semantic component:** Explicit quantile information in numerical verbalization, conditional on bin ranges

**Intended condition:** TabSTAR (Name + Bin + quantile information)

**Comparator:** Name + Bin

**Intervention type:** removal

**Protected information/setup:** Bin/range words, field name, numerical input branch, encoder/fusion architecture, training policy

**Rationale:** Q3 removes quantile wording while preserving the thinner name-plus-bin variant; the unchanged architecture separately encodes standardized numerical inputs. This identifies the contribution of supplying quantile text, not whether quantiles are unrecoverable from numbers or bins. Reconstructibility does not itself fail Removal of an explicit use. The declared variant preserves the semantic-element interface.

**Evidence:** C09 official §4/A.1 (dual numerical/semantic paths), §6 Q3 (p.9), Table 4 (p.10), Appendix G.4/Tables 31–32 (pp.53–54)


## C09-02 — TabSTAR

**Semantic component:** Explicit numeric bin/quantile content in the verbalized branch

**Intended condition:** TabSTAR (Name + Bin + quantile information)

**Comparator:** Name (e.g. Age: Numeric)

**Intervention type:** removal; replacement

**Protected information/setup:** Separate standardized-numeric branch, field identity, encoder/fusion architecture and training policy

**Rationale:** The intervention concerns verbalization, not deleting numerical inputs from the model. The Name variant retains a generic numerical-type marker; the architecture continues to contain the numerical branch. Thus this is a reference for explicit verbalized numeric content under that branch, not for all numerical information or all feature semantics. Pass relies on the paper defining this as a verbalization-only variant.

**Evidence:** C09 official §4/A.1 (dual numerical/semantic paths), §6 Q3 (p.9), Table 4 (p.10), Appendix G.4/Tables 31–32 (pp.53–54)


## C10-01 — TARTE

**Semantic component:** Supplied column-name semantic content

**Intended condition:** TARTE | Enriched YAGO4.5

**Comparator:** TARTE | Remove column names | Enriched YAGO4.5

**Intervention type:** removal

**Protected information/setup:** Numerical/cell information, stable field identity, encoder/model, pretraining and Ridge policy

**Rationale:** The published figure establishes a column-information ablation but does not establish the exact operation (neutral names, zeroed embeddings, or dropping a branch). This matters because numerical routing can use column embeddings. The supplied preprint cannot close that published-version gap. No clean removal or preservation/interface Pass is inferred from the label.

**Evidence:** C10 published indexed Figure 6 (p.10)/§4.3; user tarte.pdf §4.3/Figure 6 is preacceptance corroboration only


## C10-02 — TARTE

**Semantic component:** FastText semantic initialization with the tabular transformer unpretrained

**Intended condition:** TARTE | Random weights (FastText initialization)

**Comparator:** TARTE | MinHash | Random weights

**Intervention type:** replacement; compound

**Protected information/setup:** String encoder family/geometry, numerical/cell routing, random-initialized transformer and Ridge policy

**Rationale:** Both arms are shown in the same published figure; this is the explicitly stated audit pairing of those arms, not an assertion of a reported paired significance test. It holds absence of table pretraining nominally common, but swaps FastText for MinHash and hence changes the protected encoder. Dimensional/numeric compatibility is not specified sufficiently in the published extract.

**Evidence:** C10 published indexed Figure 6 (p.10)/§4.3; user tarte.pdf §4.3/Figure 6 is preacceptance corroboration only


## C10-03 — TARTE

**Semantic component:** FastText semantic initialization conditional on table pretraining

**Intended condition:** TARTE | Enriched YAGO4.5

**Comparator:** TARTE | MinHash | Random weights

**Intervention type:** replacement; compound

**Protected information/setup:** Table pretraining status, encoder/model setup, numerical routing, Ridge policy

**Rationale:** This alternative figure-arm pairing changes both the string encoder and table-pretraining status. It must not be substituted for C10-02 as an isolated FastText contrast. The label Random weights refers to the table model; it does not mean the FastText arm lacks pretrained language knowledge. These two pairings share arms and are not independent evidence.

**Evidence:** C10 published indexed Figure 6 (p.10)/§4.3; user tarte.pdf §4.3/Figure 6 is preacceptance corroboration only

