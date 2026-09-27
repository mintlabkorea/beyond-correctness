# Second-coder comparison and disagreements v1

A separate AI agent coded all 25 comparisons from the common rule, the factual sheet and source papers, with no inherited conversation. Primary scopes/codes and extracted outcomes were not supplied. The second scope sheet and codes were frozen before comparison. Primary v1 remains unchanged; no adjudication was performed.

This is second-AI-coder reproducibility/sensitivity, not independent human validation. The model, common rules and primary factual-construction sheet are shared. The read boundary was instructional within a shared filesystem, not technically enforced. Published PDFs contain outcomes; no literal outcome blindness is claimed. Gate agreement measures label agreement under independently declared scopes, not proof of identical estimands.

## Exact agreement

| Field | Agreement | Percent | Disagreements |
|---|---:|---:|---:|
| Removal | 24/25 | 96.0% | 1 |
| Preservation | 14/25 | 56.0% | 11 |
| Interface | 21/25 | 84.0% | 4 |
| Admissible reference | 16/25 | 64.0% | 9 |

Rows share papers and arms. No independence-based confidence intervals, significance tests or kappa-only reliability claims are used.

## Headline sensitivity

| Study | Primary | Second | Changed? |
|---|---|---|---|
| LIFT | all No | Unclear but no Yes | True |
| TabLLM | all No | at least one Yes | True |
| PLATO | Unclear but no Yes | Unclear but no Yes | False |
| CARTE | Unclear but no Yes | Unclear but no Yes | False |
| FeatLLM | Unclear but no Yes | all No | True |
| TabuLa-8B | at least one Yes | at least one Yes | False |
| ConTextTab | at least one Yes | at least one Yes | False |
| TabSTAR | at least one Yes | at least one Yes | False |
| TARTE | Unclear but no Yes | Unclear but no Yes | False |

```json
{
  "primary": {
    "comparison_counts": {
      "No": 16,
      "Unclear": 5,
      "Yes": 4
    },
    "study_counts": {
      "all No": 2,
      "Unclear but no Yes": 4,
      "at least one Yes": 3
    }
  },
  "second": {
    "comparison_counts": {
      "No": 9,
      "Unclear": 11,
      "Yes": 5
    },
    "study_counts": {
      "Unclear but no Yes": 4,
      "at least one Yes": 4,
      "all No": 1
    }
  },
  "changed_comparisons": [
    "C01-C",
    "C01-D",
    "C03-B",
    "C05-A",
    "C06-A",
    "C08-A",
    "C08-B",
    "C08-C",
    "C08-D"
  ],
  "changed_studies": [
    "LIFT",
    "TabLLM",
    "FeatLLM"
  ],
  "rows_with_any_gate_or_admissibility_disagreement": 13,
  "primary_preserved": true,
  "adjudication": "None; retain primary v1",
  "outcomes_used_in_comparison": false
}
```

## Complete paired coding: all 25 comparisons

Every pair includes independently declared scope and protection. Textual differences are disclosed without inventing a semantic-agreement percentage. Disagreement rationales below are each coder’s frozen explanations; they are not post-hoc adjudication.

### C01-A — LIFT

**Disagreeing labels:** None.

**Primary scope and protected set**

- Tested semantic use: Feature-name semantics/association within the specified prompt format
- Protected observations: Observed values, their multiplicity, target labels and examples
- Protected metadata: Target/task descriptions and category/value meanings
- Protected representation: Format-specific scaffolding and field identity, except the tested name span
- Protected predictive setup: Same LM family and training/inference policy
- Scope evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.

**Second scope and protected set**

- Tested semantic use: Feature-name meanings in the name/value associations of prompt format I.
- Protected observations: All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.
- Protected metadata: Feature identity/position, type and category-domain information, and target/task identity, except the explicitly tested semantic channel.
- Protected representation: A stable field/value association and distinct feature slots; numerical and missing-value information remain representable. Exact semantic token strings or semantic embedding coordinates are not protected. Retain the within-format presentation scaffold and output-label mapping outside removed names/context.
- Protected predictive setup: Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted.
- Scope evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.

| Gate | Primary | Second |
|---|---|---|
| Removal | Fail | Fail |
| Preservation | Unclear | Unclear |
| Interface | Unclear | Unclear |
| Admissible reference | No | No |

### C01-B — LIFT

**Disagreeing labels:** None.

**Primary scope and protected set**

- Tested semantic use: Feature-name semantics/association within the specified prompt format
- Protected observations: Observed values, their multiplicity, target labels and examples
- Protected metadata: Target/task descriptions and category/value meanings
- Protected representation: Format-specific scaffolding and field identity, except the tested name span
- Protected predictive setup: Same LM family and training/inference policy
- Scope evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.

**Second scope and protected set**

- Tested semantic use: Feature-name meanings in the name/value associations of prompt format II.
- Protected observations: All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.
- Protected metadata: Feature identity/position, type and category-domain information, and target/task identity, except the explicitly tested semantic channel.
- Protected representation: A stable field/value association and distinct feature slots; numerical and missing-value information remain representable. Exact semantic token strings or semantic embedding coordinates are not protected. Retain the within-format presentation scaffold and output-label mapping outside removed names/context.
- Protected predictive setup: Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted.
- Scope evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.

| Gate | Primary | Second |
|---|---|---|
| Removal | Fail | Fail |
| Preservation | Unclear | Unclear |
| Interface | Unclear | Unclear |
| Admissible reference | No | No |

### C01-C — LIFT

**Disagreeing labels:** Preservation, Admissible reference.

**Primary scope and protected set**

- Tested semantic use: Feature-name semantics/association within the specified prompt format
- Protected observations: Observed values, their multiplicity, target labels and examples
- Protected metadata: Target/task descriptions and category/value meanings
- Protected representation: Format-specific scaffolding and field identity, except the tested name span
- Protected predictive setup: Same LM family and training/inference policy
- Scope evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.

**Second scope and protected set**

- Tested semantic use: Named feature and task context in prompt format I, including informative target question; categorical observation identities remain protected even if recoded.
- Protected observations: All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.
- Protected metadata: Feature identity/position, type and category-domain information, and target/task identity, except the explicitly tested semantic channel.
- Protected representation: A stable field/value association and distinct feature slots; numerical and missing-value information remain representable. Exact semantic token strings or semantic embedding coordinates are not protected. Retain the within-format presentation scaffold and output-label mapping outside removed names/context.
- Protected predictive setup: Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted.
- Scope evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.

| Gate | Primary | Second |
|---|---|---|
| Removal | Pass | Pass |
| Preservation | Fail | Unclear |
| Interface | Unclear | Unclear |
| Admissible reference | No | Unclear |

**Preservation disagreement**

Primary: For the feature-name-only scope, the worked construction also substitutes a generic target question and recodes category words; the two prompt forms are not held constant. The published mapping for both unnamed variants is incomplete, so do not claim every dataset has the same additional changes. Evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.

Second: The lone unnamed example changes category words to numeric codes; a complete fixed coding map is not documented. Two table variants are not separately specified. Format-II correct example also omits class size, making preservation across the worked examples unresolved. Evidence: packet/sources/C01_main.pdf §4.1/Table 9 p.8; C01_supp.pdf D.2.1 printed pp.42–44 (PDF pp.20–22), five printed prompt examples.

**Admissible reference disagreement**

Primary: All Pass -> Yes; any Fail -> No; otherwise Unclear. Evidence: Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md

Second: Removal=Pass; Preservation=Unclear; Interface=Unclear; frozen rule therefore yields Unclear. Evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.

### C01-D — LIFT

**Disagreeing labels:** Preservation, Admissible reference.

**Primary scope and protected set**

- Tested semantic use: Feature-name semantics/association within the specified prompt format
- Protected observations: Observed values, their multiplicity, target labels and examples
- Protected metadata: Target/task descriptions and category/value meanings
- Protected representation: Format-specific scaffolding and field identity, except the tested name span
- Protected predictive setup: Same LM family and training/inference policy
- Scope evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.

**Second scope and protected set**

- Tested semantic use: Named feature and task context in prompt format II, including informative target question; categorical observation identities remain protected even if recoded.
- Protected observations: All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.
- Protected metadata: Feature identity/position, type and category-domain information, and target/task identity, except the explicitly tested semantic channel.
- Protected representation: A stable field/value association and distinct feature slots; numerical and missing-value information remain representable. Exact semantic token strings or semantic embedding coordinates are not protected. Retain the within-format presentation scaffold and output-label mapping outside removed names/context.
- Protected predictive setup: Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted.
- Scope evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.

| Gate | Primary | Second |
|---|---|---|
| Removal | Pass | Pass |
| Preservation | Fail | Unclear |
| Interface | Unclear | Unclear |
| Admissible reference | No | Unclear |

**Preservation disagreement**

Primary: For the feature-name-only scope, the worked construction also substitutes a generic target question and recodes category words; the two prompt forms are not held constant. The published mapping for both unnamed variants is incomplete, so do not claim every dataset has the same additional changes. Evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.

Second: The lone unnamed example changes category words to numeric codes; a complete fixed coding map is not documented. Two table variants are not separately specified. Format-II correct example also omits class size, making preservation across the worked examples unresolved. Evidence: packet/sources/C01_main.pdf §4.1/Table 9 p.8; C01_supp.pdf D.2.1 printed pp.42–44 (PDF pp.20–22), five printed prompt examples.

**Admissible reference disagreement**

Primary: All Pass -> Yes; any Fail -> No; otherwise Unclear. Evidence: Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md

Second: Removal=Pass; Preservation=Unclear; Interface=Unclear; frozen rule therefore yields Unclear. Evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.

### C03-A — TabLLM

**Disagreeing labels:** None.

**Primary scope and protected set**

- Tested semantic use: Feature-name semantics/association under List Template
- Protected observations: Ordered values, target labels and examples
- Protected metadata: Task/target prompt and non-tested value meanings
- Protected representation: List Template scaffolding and stable field identity
- Protected predictive setup: Same T0 and fine-tuning/evaluation policy
- Scope evidence: Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.

**Second scope and protected set**

- Tested semantic use: Column-name meanings as supplied in the list name/value associations.
- Protected observations: All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.
- Protected metadata: Feature identity/position, type and category-domain information, and target/task identity, except the explicitly tested semantic channel.
- Protected representation: Ordered feature-value slots, value boundaries and task prompt/verbalizer; field-name text may be absent when that is the tested channel. For value permutations, continuous precision is protected as observation information.
- Protected predictive setup: Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted.
- Scope evidence: Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.

| Gate | Primary | Second |
|---|---|---|
| Removal | Fail | Fail |
| Preservation | Pass | Pass |
| Interface | Pass | Pass |
| Admissible reference | No | No |

### C03-B — TabLLM

**Disagreeing labels:** Preservation, Admissible reference.

**Primary scope and protected set**

- Tested semantic use: Feature-name semantics/association under List Template
- Protected observations: Ordered values, target labels and examples
- Protected metadata: Task/target prompt and non-tested value meanings
- Protected representation: List Template scaffolding and stable field identity
- Protected predictive setup: Same T0 and fine-tuning/evaluation policy
- Scope evidence: Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.

**Second scope and protected set**

- Tested semantic use: Column-name text as semantic annotation of a fixed ordered value list.
- Protected observations: All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.
- Protected metadata: Feature identity/position, type and category-domain information, and target/task identity, except the explicitly tested semantic channel.
- Protected representation: Ordered feature-value slots, value boundaries and task prompt/verbalizer; field-name text may be absent when that is the tested channel. For value permutations, continuous precision is protected as observation information.
- Protected predictive setup: Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted.
- Scope evidence: Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.

| Gate | Primary | Second |
|---|---|---|
| Removal | Pass | Pass |
| Preservation | Fail | Pass |
| Interface | Pass | Pass |
| Admissible reference | No | Yes |

**Preservation disagreement**

Primary: The declared scope protects List Template field scaffolding. Values-only serialization removes that scaffolding along with names, so ordered raw values alone do not satisfy this protection. This is an auditor-declared format-conditional estimand. Evidence: Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.

Second: The defined operation retains the feature values in their fixed arbitrary order and the separate task prompt. Explicit name prefixes are the tested annotation channel, not an independently protected scaffold; ordered slots and boundaries suffice here. Evidence: packet/sources/C03_main.pdf §3.1–3.2 pp.3–4, serialization definitions; §5.1/Figure 2; Supplement §9 examples.

**Admissible reference disagreement**

Primary: All Pass -> Yes; any Fail -> No; otherwise Unclear. Evidence: Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md

Second: Removal=Pass; Preservation=Pass; Interface=Pass; frozen rule therefore yields Yes. Evidence: Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.

### C03-C — TabLLM

**Disagreeing labels:** None.

**Primary scope and protected set**

- Tested semantic use: Meaning assigned to values under the mixed categorical/continuous permutation
- Protected observations: Original continuous resolution, categorical identity structure, targets and examples
- Protected metadata: Feature names, task and target prompt
- Protected representation: List Template scaffolding and stable field identity
- Protected predictive setup: Same T0 and fine-tuning/evaluation policy
- Scope evidence: Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.

**Second scope and protected set**

- Tested semantic use: Semantic meanings of supplied feature-value tokens, including continuous-value magnitude.
- Protected observations: All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.
- Protected metadata: Feature identity/position, type and category-domain information, and target/task identity, except the explicitly tested semantic channel.
- Protected representation: Ordered feature-value slots, value boundaries and task prompt/verbalizer; field-name text may be absent when that is the tested channel. For value permutations, continuous precision is protected as observation information.
- Protected predictive setup: Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted.
- Scope evidence: Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.

| Gate | Primary | Second |
|---|---|---|
| Removal | Fail | Fail |
| Preservation | Fail | Fail |
| Interface | Pass | Pass |
| Admissible reference | No | No |

### C04-A — PLATO

**Disagreeing labels:** Preservation, Interface.

**Primary scope and protected set**

- Tested semantic use: Broader-domain KG information beyond feature nodes
- Protected observations: BRCA features, labels and evaluated examples
- Protected metadata: Feature-node information independent of the removed broader domain
- Protected representation: Feature-node input representation and weight-inference interface
- Protected predictive setup: Same PLATO family, capacity and training policy except tested graph input
- Scope evidence: Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.

**Second scope and protected set**

- Tested semantic use: Broader-domain KG information conveyed by non-feature nodes, including through pretrained embeddings and message passing. Feature-node information is protected.
- Protected observations: All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.
- Protected metadata: Feature identity/position, type and category-domain information, and target/task identity, except the explicitly tested semantic channel.
- Protected representation: Feature-node correspondence and the PLATO first-layer weight-inference scaffold, MLP downstream layers, observed-feature routing; changing KG neighborhoods is intrinsic to the intervention. Semantic embedding coordinates may change under the same recipe.
- Protected predictive setup: Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted.
- Scope evidence: Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.

| Gate | Primary | Second |
|---|---|---|
| Removal | Unclear | Unclear |
| Preservation | Unclear | Pass |
| Interface | Unclear | Pass |
| Admissible reference | Unclear | Unclear |

**Preservation disagreement**

Primary: Feature nodes remain, but retained versus recomputed embeddings and their non-tested information are unspecified. Removing the tested nodes itself is allowed; the unresolved embedding construction is the issue. Evidence: Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.

Second: Feature nodes and observations remain; neighborhood changes are intrinsic to withdrawing broader nodes. The described PLATO recipe retains the protected inference scaffold, and no extra change is established. Evidence: packet/sources/C04_main.pdf (Ruiz et al.), §§3.1–3.6 pp.4–6, Eq.(1) and Algorithm 1; §4.1 p.9, Tables 3–4.

**Interface disagreement**

Primary: The weight-inference pathway is described, but embedding provenance and retraining determine the representations and opportunities available to that pathway. The published ablation does not settle them. Evidence: Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.

Second: An induced feature subgraph retains feature-node correspondence and feeds the same graph-to-weight predictor. Graph-size change is compatible with that interface. Evidence: packet/sources/C04_main.pdf (Ruiz et al.), §§3.1–3.6 pp.4–6, Eq.(1) and Algorithm 1; §4.1 p.9, Tables 3–4.

### C04-B — PLATO

**Disagreeing labels:** Interface.

**Primary scope and protected set**

- Tested semantic use: Complete auxiliary KG use conditional on the KG-enabled predictive setup
- Protected observations: BRCA features, labels and evaluated examples
- Protected metadata: Non-tested feature information
- Protected representation: Feature-node input representation and weight-inference interface
- Protected predictive setup: Same PLATO family, capacity and training policy except tested graph input
- Scope evidence: Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.

**Second scope and protected set**

- Tested semantic use: Auxiliary KG information used for feature embeddings and first-layer weight inference.
- Protected observations: All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.
- Protected metadata: Feature identity/position, type and category-domain information, and target/task identity, except the explicitly tested semantic channel.
- Protected representation: Feature-node correspondence and the PLATO first-layer weight-inference scaffold, MLP downstream layers, observed-feature routing; changing KG neighborhoods is intrinsic to the intervention. Semantic embedding coordinates may change under the same recipe.
- Protected predictive setup: Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted.
- Scope evidence: Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.

| Gate | Primary | Second |
|---|---|---|
| Removal | Pass | Pass |
| Preservation | Fail | Fail |
| Interface | Unclear | Pass |
| Admissible reference | No | No |

**Interface disagreement**

Primary: Both accept tabular inputs and predict the same target, but their first-layer learning pathways and opportunities differ. The paper does not establish a matched opportunity/interaction contract for the declared component-specific comparison; architecture change alone is not labelled an interface failure. Evidence: Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.

Second: The replacement is an explicitly defined standard MLP with the same observed feature/target interface; architecture change does not itself create a routing or shape violation. Evidence: packet/sources/C04_main.pdf (Ruiz et al.), §§3.1–3.6 pp.4–6, Eq.(1) and Algorithm 1; §4.1 p.9, Tables 3–4.

### C04-C — PLATO

**Disagreeing labels:** Preservation, Interface.

**Primary scope and protected set**

- Tested semantic use: Complete supplied KG relational information (not just the deleted subset)
- Protected observations: BRCA features, labels and evaluated examples
- Protected metadata: Non-tested feature information
- Protected representation: Feature-node input representation and weight-inference interface
- Protected predictive setup: Same PLATO family, capacity and training policy except tested graph input
- Scope evidence: Official C04 §4.1 p.9, Table 4.

**Second scope and protected set**

- Tested semantic use: KG edge information as a whole, including its encoding in pretrained node embeddings and message passing; a 50% deletion is a partial intervention on this use.
- Protected observations: All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.
- Protected metadata: Feature identity/position, type and category-domain information, and target/task identity, except the explicitly tested semantic channel.
- Protected representation: Feature-node correspondence and the PLATO first-layer weight-inference scaffold, MLP downstream layers, observed-feature routing; changing KG neighborhoods is intrinsic to the intervention. Semantic embedding coordinates may change under the same recipe.
- Protected predictive setup: Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted.
- Scope evidence: Official C04 §4.1 p.9, Table 4.

| Gate | Primary | Second |
|---|---|---|
| Removal | Fail | Fail |
| Preservation | Unclear | Pass |
| Interface | Unclear | Pass |
| Admissible reference | No | No |

**Preservation disagreement**

Primary: The feature inputs and model family remain, but the embedding-retention/recomputation policy accompanying random deletion is not given. Evidence: Official C04 §4.1 p.9, Table 4.

Second: Edge deletion changes tested connectivity while preserving feature nodes and the common PLATO prediction scaffold. No evidenced extra alteration is specified. Evidence: packet/sources/C04_main.pdf (Ruiz et al.), §§3.1–3.6 pp.4–6, Eq.(1) and Algorithm 1; §4.1 p.9, Tables 3–4.

**Interface disagreement**

Primary: Sparse graph processing is intentional, not a demonstrated failure. However, residual embedding information and its training opportunity are not documented enough to certify substantive interface comparability. Evidence: Official C04 §4.1 p.9, Table 4.

Second: The model accepts a sparser KG with the same feature-node mapping; sparsity is the declared graph intervention, not evidence of an unintended missing-value or cardinality violation. Evidence: packet/sources/C04_main.pdf (Ruiz et al.), §§3.1–3.6 pp.4–6, Eq.(1) and Algorithm 1; §4.1 p.9, Tables 3–4.

### C05-A — CARTE

**Disagreeing labels:** Preservation, Admissible reference.

**Primary scope and protected set**

- Tested semantic use: Language-semantic string initialization, conditional on the remaining CARTE setup
- Protected observations: Cell values, field multiplicity and target labels
- Protected metadata: Non-tested names/value semantics
- Protected representation: Encoder family and non-tested value/graph representation
- Protected predictive setup: Graph predictor, capacity, pretraining/adaptation policy
- Scope evidence: Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.

**Second scope and protected set**

- Tested semantic use: External pretrained linguistic meaning in string feature initialization.
- Protected observations: All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.
- Protected metadata: Feature identity/position, type and category-domain information, and target/task identity, except the explicitly tested semantic channel.
- Protected representation: Graphlet feature slots, numeric-value and missing-value representation, central readout and attention scaffold; encoder coordinates may change but nonsemantic identity/routing must survive.
- Protected predictive setup: Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted.
- Scope evidence: Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.

| Gate | Primary | Second |
|---|---|---|
| Removal | Pass | Pass |
| Preservation | Fail | Unclear |
| Interface | Unclear | Unclear |
| Admissible reference | No | Unclear |

**Preservation disagreement**

Primary: The entire string encoder and its representational geometry change, outside the scope of semantic content under a protected encoder/predictor setup. Evidence: Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.

Second: Numeric initialization, nonsemantic string distinctions and encoder/training alignment after replacement are not documented sufficiently to establish protected information/scaffold preservation. Encoder replacement alone is not a failure. Evidence: packet/sources/C05_main.pdf §3.1/Figure 1 (numerical node initialization), §3 architecture; Appendix C.3/Figure 10 p.21.

**Admissible reference disagreement**

Primary: All Pass -> Yes; any Fail -> No; otherwise Unclear. Evidence: Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md

Second: Removal=Pass; Preservation=Unclear; Interface=Unclear; frozen rule therefore yields Unclear. Evidence: Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.

### C05-B — CARTE

**Disagreeing labels:** None.

**Primary scope and protected set**

- Tested semantic use: Column semantics carried by edge information, including any retained column-conditioned routes
- Protected observations: Cell values, field multiplicity and target labels
- Protected metadata: Non-tested names/value semantics
- Protected representation: Value-bearing node initialization and non-tested graph representation
- Protected predictive setup: Graph predictor, capacity, pretraining/adaptation policy
- Scope evidence: Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.

**Second scope and protected set**

- Tested semantic use: Column-name semantic information in CARTE, including edge encodings and any propagation through numerical-node initialization.
- Protected observations: All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.
- Protected metadata: Feature identity/position, type and category-domain information, and target/task identity, except the explicitly tested semantic channel.
- Protected representation: Graphlet feature slots, numeric-value and missing-value representation, central readout and attention scaffold; encoder coordinates may change but nonsemantic identity/routing must survive.
- Protected predictive setup: Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted.
- Scope evidence: Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.

| Gate | Primary | Second |
|---|---|---|
| Removal | Unclear | Unclear |
| Preservation | Unclear | Unclear |
| Interface | Unclear | Unclear |
| Admissible reference | Unclear | Unclear |

### C05-C — CARTE

**Disagreeing labels:** None.

**Primary scope and protected set**

- Tested semantic use: Column semantics carried by edge information, including any retained column-conditioned routes
- Protected observations: Cell values, field multiplicity and target labels
- Protected metadata: Non-tested names/value semantics
- Protected representation: Value-bearing node initialization and non-tested graph representation
- Protected predictive setup: Graph predictor, capacity, pretraining/adaptation policy
- Scope evidence: Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.

**Second scope and protected set**

- Tested semantic use: Column-name semantic information in CARTE, including edge encodings and any propagation through numerical-node initialization.
- Protected observations: All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.
- Protected metadata: Feature identity/position, type and category-domain information, and target/task identity, except the explicitly tested semantic channel.
- Protected representation: Graphlet feature slots, numeric-value and missing-value representation, central readout and attention scaffold; encoder coordinates may change but nonsemantic identity/routing must survive.
- Protected predictive setup: Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted.
- Scope evidence: Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.

| Gate | Primary | Second |
|---|---|---|
| Removal | Unclear | Unclear |
| Preservation | Fail | Fail |
| Interface | Unclear | Unclear |
| Admissible reference | No | No |

### C06-A — FeatLLM

**Disagreeing labels:** Preservation, Admissible reference.

**Primary scope and protected set**

- Tested semantic use: Entire supplied feature-description block, including types, definitions and category information
- Protected observations: Observed demonstrations, their labels and prediction inputs
- Protected metadata: Task description and metadata outside that block
- Protected representation: Same named examples, rule-count/format policy and binary-feature interface
- Protected predictive setup: Same generator/parser/model family, ensemble and tuning recipe; generated rules may change
- Scope evidence: Official C06 §3.1/Figure 2 pp.3–4, §4.2/Table 4 pp.7–8, Appendix A.2 and K.2/Table 18; supplied featllm.pdf corroborates prompt components.

**Second scope and protected set**

- Tested semantic use: Explanatory semantic definitions in the feature-description block used to generate rules.
- Protected observations: All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.
- Protected metadata: Feature identity, explicit value types, categorical domains/examples and task/answer-class definition; these structural facts are protected separately from explanatory meaning.
- Protected representation: Generate/parse/binary-feature interface and parser rules; newly generated rules and binary features are allowed consequences.
- Protected predictive setup: Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted.
- Scope evidence: Official C06 §3.1/Figure 2 pp.3–4, §4.2/Table 4 pp.7–8, Appendix A.2 and K.2/Table 18; supplied featllm.pdf corroborates prompt components.

| Gate | Primary | Second |
|---|---|---|
| Removal | Pass | Pass |
| Preservation | Pass | Fail |
| Interface | Unclear | Unclear |
| Admissible reference | Unclear | No |

**Preservation disagreement**

Primary: Under this package scope, its type/category contents are tested rather than protected. The paper describes a single-component omission with the remaining generation/parser/ensemble/tuning recipe common. Resulting rule and feature changes are mediators. A prose-only scope protecting type/category metadata would instead fail Preservation. Evidence: Official C06 §3.1/Figure 2 pp.3–4, §4.2/Table 4 pp.7–8, Appendix A.2 and K.2/Table 18; supplied featllm.pdf corroborates prompt components.

Second: The same block explicitly conveys types and possible categories, which are protected metadata in this scope. Those explicit facts are withdrawn together with definitions; examples alone do not document a lossless replacement for category/type information. Evidence: packet/sources/C06_main.pdf §3.1/Figure 2 pp.3–4, §4.2/Table 4 pp.7–8, Appendix A.2 and K.2/Table 18.

**Admissible reference disagreement**

Primary: All Pass -> Yes; any Fail -> No; otherwise Unclear. Evidence: Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md

Second: Removal=Pass; Preservation=Fail; Interface=Unclear; frozen rule therefore yields No. Evidence: Official C06 §3.1/Figure 2 pp.3–4, §4.2/Table 4 pp.7–8, Appendix A.2 and K.2/Table 18; supplied featllm.pdf corroborates prompt components.

### C07-A — TabuLa-8B

**Disagreeing labels:** None.

**Primary scope and protected set**

- Tested semantic use: Joint informative feature-and-target-header content
- Protected observations: Table values, target values and examples
- Protected metadata: Non-header metadata
- Protected representation: Stable field positions/identities and serialization, except tested header strings
- Protected predictive setup: Same TABULA-8B checkpoint and evaluation procedure
- Scope evidence: Official C07 §5.5, Appendix F.2 p.26/Figure 12 p.27; supplied tabula.pdf has different pagination.

**Second scope and protected set**

- Tested semantic use: Informative feature headers and informative target header jointly, as opposed to indexed headers.
- Protected observations: All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.
- Protected metadata: Feature identity/position, type and category-domain information, and target/task identity, except the explicitly tested semantic channel.
- Protected representation: A stable field/value association and distinct feature slots; numerical and missing-value information remain representable. Exact semantic token strings or semantic embedding coordinates are not protected.
- Protected predictive setup: Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted.
- Scope evidence: Official C07 §5.5, Appendix F.2 p.26/Figure 12 p.27; supplied tabula.pdf has different pagination.

| Gate | Primary | Second |
|---|---|---|
| Removal | Pass | Pass |
| Preservation | Pass | Pass |
| Interface | Pass | Pass |
| Admissible reference | Yes | Yes |

### C08-A — ConTextTab

**Disagreeing labels:** Preservation, Admissible reference.

**Primary scope and protected set**

- Tested semantic use: LLM-derived cell-feature semantic channel conditional on encoder setup
- Protected observations: Cells, target labels and evaluated rows
- Protected metadata: Column metadata not under test
- Protected representation: Encoder family/geometry, numerical branch and field identity
- Protected predictive setup: Same base-model family, capacity and training/adaptation/evaluation opportunity
- Scope evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

**Second scope and protected set**

- Tested semantic use: Pretrained linguistic meaning in categorical/string cell encodings; column-header semantic meaning remains protected.
- Protected observations: All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.
- Protected metadata: Feature identity/position, type and category-domain information, and target/task identity, except the explicitly tested semantic channel.
- Protected representation: Distinct cell/column identity, numeric/date/missingness paths and the column-plus-cell backbone interface. A compatible change of cell encoder is allowed; loss of observational distinctions is not.
- Protected predictive setup: Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted.
- Scope evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

| Gate | Primary | Second |
|---|---|---|
| Removal | Pass | Pass |
| Preservation | Fail | Unclear |
| Interface | Unclear | Unclear |
| Admissible reference | No | Unclear |

**Preservation disagreement**

Primary: The named encoder family/representation changes rather than only its semantic content. That violates the protected encoder/representation setup for this scoped claim. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

Second: The ordinal replacement is stated, but the per-arm handling of free text, unseen/missing categories, retained distinctions and fitting/pretraining alignment is materially underspecified. This is uncertainty, not an assumed failure from changing geometry. Evidence: packet/sources/C08_main.pdf §3.1 pp.3–4 (modality encoders and projection), §5.1 p.8, Table 2 semantic block p.9; Appendix A.4 pp.27–28.

**Admissible reference disagreement**

Primary: All Pass -> Yes; any Fail -> No; otherwise Unclear. Evidence: Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md

Second: Removal=Pass; Preservation=Unclear; Interface=Unclear; frozen rule therefore yields Unclear. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

### C08-B — ConTextTab

**Disagreeing labels:** Preservation, Admissible reference.

**Primary scope and protected set**

- Tested semantic use: LLM-derived cell-feature semantic channel conditional on encoder setup
- Protected observations: Cells, target labels and evaluated rows
- Protected metadata: Column metadata not under test
- Protected representation: Encoder family/geometry, numerical branch and field identity
- Protected predictive setup: Same base-model family, capacity and training/adaptation/evaluation opportunity
- Scope evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

**Second scope and protected set**

- Tested semantic use: Pretrained linguistic meaning in categorical/string cell encodings; column-header semantic meaning remains protected.
- Protected observations: All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.
- Protected metadata: Feature identity/position, type and category-domain information, and target/task identity, except the explicitly tested semantic channel.
- Protected representation: Distinct cell/column identity, numeric/date/missingness paths and the column-plus-cell backbone interface. A compatible change of cell encoder is allowed; loss of observational distinctions is not.
- Protected predictive setup: Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted.
- Scope evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

| Gate | Primary | Second |
|---|---|---|
| Removal | Pass | Pass |
| Preservation | Fail | Unclear |
| Interface | Unclear | Unclear |
| Admissible reference | No | Unclear |

**Preservation disagreement**

Primary: The named encoder family/representation changes rather than only its semantic content. That violates the protected encoder/representation setup for this scoped claim. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

Second: The MinHash replacement is stated, but the per-arm handling of free text, unseen/missing categories, retained distinctions and fitting/pretraining alignment is materially underspecified. This is uncertainty, not an assumed failure from changing geometry. Evidence: packet/sources/C08_main.pdf §3.1 pp.3–4 (modality encoders and projection), §5.1 p.8, Table 2 semantic block p.9; Appendix A.4 pp.27–28.

**Admissible reference disagreement**

Primary: All Pass -> Yes; any Fail -> No; otherwise Unclear. Evidence: Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md

Second: Removal=Pass; Preservation=Unclear; Interface=Unclear; frozen rule therefore yields Unclear. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

### C08-C — ConTextTab

**Disagreeing labels:** Removal, Preservation, Admissible reference.

**Primary scope and protected set**

- Tested semantic use: LLM-derived cell-feature semantic channel conditional on encoder setup
- Protected observations: Cells, target labels and evaluated rows
- Protected metadata: Column metadata not under test
- Protected representation: Encoder family/geometry, numerical branch and field identity
- Protected predictive setup: Same base-model family, capacity and training/adaptation/evaluation opportunity
- Scope evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

**Second scope and protected set**

- Tested semantic use: Pretrained linguistic meaning in categorical/string cell encodings; column-header semantic meaning remains protected.
- Protected observations: All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.
- Protected metadata: Feature identity/position, type and category-domain information, and target/task identity, except the explicitly tested semantic channel.
- Protected representation: Distinct cell/column identity, numeric/date/missingness paths and the column-plus-cell backbone interface. A compatible change of cell encoder is allowed; loss of observational distinctions is not.
- Protected predictive setup: Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted.
- Scope evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

| Gate | Primary | Second |
|---|---|---|
| Removal | Pass | Unclear |
| Preservation | Fail | Unclear |
| Interface | Unclear | Unclear |
| Admissible reference | No | Unclear |

**Removal disagreement**

Primary: §5.1 replaces the LLM-based categorical/string semantic-embedding channel by the named AutoGluon encoding. Removal is scoped to that channel; neither all column semantics nor all pretrained model knowledge is claimed absent. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

Second: The named AutoGluon feature encoder does not specify the configured string/text transformations, so complete removal of the pretrained linguistic pathway cannot be independently established. Evidence: packet/sources/C08_main.pdf §3.1 pp.3–4 (modality encoders and projection), §5.1 p.8, Table 2 semantic block p.9; Appendix A.4 pp.27–28.

**Preservation disagreement**

Primary: The named encoder family/representation changes rather than only its semantic content. That violates the protected encoder/representation setup for this scoped claim. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

Second: The AutoGluon replacement is stated, but the per-arm handling of free text, unseen/missing categories, retained distinctions and fitting/pretraining alignment is materially underspecified. This is uncertainty, not an assumed failure from changing geometry. Evidence: packet/sources/C08_main.pdf §3.1 pp.3–4 (modality encoders and projection), §5.1 p.8, Table 2 semantic block p.9; Appendix A.4 pp.27–28.

**Admissible reference disagreement**

Primary: All Pass -> Yes; any Fail -> No; otherwise Unclear. Evidence: Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md

Second: Removal=Unclear; Preservation=Unclear; Interface=Unclear; frozen rule therefore yields Unclear. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

### C08-D — ConTextTab

**Disagreeing labels:** Preservation, Admissible reference.

**Primary scope and protected set**

- Tested semantic use: LLM-derived cell-feature semantic channel conditional on encoder setup
- Protected observations: Cells, target labels and evaluated rows
- Protected metadata: Column metadata not under test
- Protected representation: Encoder family/geometry, numerical branch and field identity
- Protected predictive setup: Same base-model family, capacity and training/adaptation/evaluation opportunity
- Scope evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

**Second scope and protected set**

- Tested semantic use: Pretrained linguistic meaning in categorical/string cell encodings; column-header semantic meaning remains protected.
- Protected observations: All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.
- Protected metadata: Feature identity/position, type and category-domain information, and target/task identity, except the explicitly tested semantic channel.
- Protected representation: Distinct cell/column identity, numeric/date/missingness paths and the column-plus-cell backbone interface. A compatible change of cell encoder is allowed; loss of observational distinctions is not.
- Protected predictive setup: Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted.
- Scope evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

| Gate | Primary | Second |
|---|---|---|
| Removal | Pass | Pass |
| Preservation | Fail | Unclear |
| Interface | Unclear | Unclear |
| Admissible reference | No | Unclear |

**Preservation disagreement**

Primary: The named encoder family/representation changes rather than only its semantic content. That violates the protected encoder/representation setup for this scoped claim. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

Second: The Gap replacement is stated, but the per-arm handling of free text, unseen/missing categories, retained distinctions and fitting/pretraining alignment is materially underspecified. This is uncertainty, not an assumed failure from changing geometry. Evidence: packet/sources/C08_main.pdf §3.1 pp.3–4 (modality encoders and projection), §5.1 p.8, Table 2 semantic block p.9; Appendix A.4 pp.27–28.

**Admissible reference disagreement**

Primary: All Pass -> Yes; any Fail -> No; otherwise Unclear. Evidence: Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md

Second: Removal=Pass; Preservation=Unclear; Interface=Unclear; frozen rule therefore yields Unclear. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

### C08-E — ConTextTab

**Disagreeing labels:** None.

**Primary scope and protected set**

- Tested semantic use: Supplied column-name semantic content
- Protected observations: Cells, target labels and evaluated rows
- Protected metadata: Cell meanings, target context and other metadata
- Protected representation: Cell encoder and stable field slots; header pathway except tested name strings
- Protected predictive setup: Same base-model family, capacity and training/adaptation/evaluation opportunity
- Scope evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

**Second scope and protected set**

- Tested semantic use: Informative original column-header meanings; indexed header strings are a neutral replacement.
- Protected observations: All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.
- Protected metadata: Feature identity/position, type and category-domain information, and target/task identity, except the explicitly tested semantic channel.
- Protected representation: Distinct cell/column identity, numeric/date/missingness paths and the column-plus-cell backbone interface. A compatible change of cell encoder is allowed; loss of observational distinctions is not.
- Protected predictive setup: Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted.
- Scope evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

| Gate | Primary | Second |
|---|---|---|
| Removal | Pass | Pass |
| Preservation | Pass | Pass |
| Interface | Pass | Pass |
| Admissible reference | Yes | Yes |

### C08-F — ConTextTab

**Disagreeing labels:** Interface.

**Primary scope and protected set**

- Tested semantic use: Additional generated contextual column-description content
- Protected observations: Cells, target labels and evaluated rows
- Protected metadata: Original column names and target context
- Protected representation: Original field identity and column/cell-encoding pathways
- Protected predictive setup: Same model/evaluation procedure and permitted row/target access; generated-description content may differ
- Scope evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

**Second scope and protected set**

- Tested semantic use: Additional contextual descriptions appended to original column names, beyond the original name meaning.
- Protected observations: All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.
- Protected metadata: Feature identity/position, type and category-domain information, and target/task identity, except the explicitly tested semantic channel.
- Protected representation: Distinct cell/column identity, numeric/date/missingness paths and the column-plus-cell backbone interface. A compatible change of cell encoder is allowed; loss of observational distinctions is not.
- Protected predictive setup: Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted. Description generation may transform available training observations but must not acquire additional held-out or target information relative to the comparator.
- Scope evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

| Gate | Primary | Second |
|---|---|---|
| Removal | Pass | Pass |
| Preservation | Unclear | Unclear |
| Interface | Unclear | Pass |
| Admissible reference | Unclear | Unclear |

**Interface disagreement**

Primary: Both strings use the same encoder route, but the generator creates an additional route from sampled rows to the predictor. Without its access policy, representation availability and training/evaluation opportunity are not confirmed comparable. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

Second: Both original names and enriched name:description strings are compatible inputs to the same header encoder; provenance uncertainty belongs to Preservation. Evidence: packet/sources/C08_main.pdf §3.1 pp.3–4 (modality encoders and projection), §5.1 p.8, Table 2 semantic block p.9; Appendix A.4 pp.27–28.

### C09-A — TabSTAR

**Disagreeing labels:** None.

**Primary scope and protected set**

- Tested semantic use: Explicit quantile text conditional on name-plus-bin verbalization
- Protected observations: Numerical and other values, targets and examples
- Protected metadata: Field names, non-tested metadata and target context
- Protected representation: Separate numerical branch, fusion/interaction architecture and non-tested text; bin/range text is protected
- Protected predictive setup: Same encoder/model family and training/adaptation recipe; fitted weights may change
- Scope evidence: Official C09 §4/A.1, §6 Q3 p.9/Table 4 p.10, Appendix G.4/Tables 31–32 pp.53–54; supplied tabstar.pdf has different pagination.

**Second scope and protected set**

- Tested semantic use: Explicit quantile wording in numerical-feature verbalization.
- Protected observations: All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.
- Protected metadata: Feature identity/position, type and category-domain information, and target/task identity, except the explicitly tested semantic channel.
- Protected representation: Separate standardized numerical-input branch, feature name/slot and missing-value markers, text encoder and numerical/semantic fusion scaffold. Numerical facts remain allowed through the numeric branch.
- Protected predictive setup: Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted.
- Scope evidence: Official C09 §4/A.1, §6 Q3 p.9/Table 4 p.10, Appendix G.4/Tables 31–32 pp.53–54; supplied tabstar.pdf has different pagination.

| Gate | Primary | Second |
|---|---|---|
| Removal | Pass | Pass |
| Preservation | Pass | Pass |
| Interface | Pass | Pass |
| Admissible reference | Yes | Yes |

### C09-B — TabSTAR

**Disagreeing labels:** None.

**Primary scope and protected set**

- Tested semantic use: Explicit bin/quantile numeric content in verbalization conditional on the numerical branch
- Protected observations: Numerical and other values, targets and examples
- Protected metadata: Field names, non-tested metadata and target context
- Protected representation: Separate numerical branch, fusion/interaction architecture and non-tested text
- Protected predictive setup: Same encoder/model family and training/adaptation recipe; fitted weights may change
- Scope evidence: Official C09 §4/A.1, §6 Q3 p.9/Table 4 p.10, Appendix G.4/Tables 31–32 pp.53–54; supplied tabstar.pdf has different pagination.

**Second scope and protected set**

- Tested semantic use: Numeric bin/magnitude and quantile wording in the semantic verbalization branch only.
- Protected observations: All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.
- Protected metadata: Feature identity/position, type and category-domain information, and target/task identity, except the explicitly tested semantic channel.
- Protected representation: Separate standardized numerical-input branch, feature name/slot and missing-value markers, text encoder and numerical/semantic fusion scaffold. Numerical facts remain allowed through the numeric branch.
- Protected predictive setup: Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted.
- Scope evidence: Official C09 §4/A.1, §6 Q3 p.9/Table 4 p.10, Appendix G.4/Tables 31–32 pp.53–54; supplied tabstar.pdf has different pagination.

| Gate | Primary | Second |
|---|---|---|
| Removal | Pass | Pass |
| Preservation | Pass | Pass |
| Interface | Pass | Pass |
| Admissible reference | Yes | Yes |

### C10-A — TARTE

**Disagreeing labels:** None.

**Primary scope and protected set**

- Tested semantic use: Supplied column-name semantic content
- Protected observations: Cell/numerical values, target labels and examples
- Protected metadata: Non-tested metadata and field identities
- Protected representation: Numerical/cell-value routing, field identity and non-tested representations
- Protected predictive setup: Same table-pretraining status, model family and Ridge training policy
- Scope evidence: C10 official indexed published Figure 6 p.10/§4.3 from eligibility screening; supplied tarte.pdf is arXiv v2 corroboration, not the accepted PDF. Conditions known, implementation details not fully established from published source.

**Second scope and protected set**

- Tested semantic use: Column-name semantics across table-representation paths, including any numeric initialization use.
- Protected observations: All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.
- Protected metadata: Feature identity/position, type and category-domain information, and target/task identity, except the explicitly tested semantic channel.
- Protected representation: Feature slots, numeric/date/missingness handling and fixed representation-to-Ridge interface; compatible string-encoder replacement is allowed.
- Protected predictive setup: Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted. Table-model pretraining regime and downstream Ridge fitting recipe are protected independently of the tested channel.
- Scope evidence: C10 official indexed published Figure 6 p.10/§4.3 from eligibility screening; supplied tarte.pdf is arXiv v2 corroboration, not the accepted PDF. Conditions known, implementation details not fully established from published source.

| Gate | Primary | Second |
|---|---|---|
| Removal | Unclear | Unclear |
| Preservation | Unclear | Unclear |
| Interface | Unclear | Unclear |
| Admissible reference | Unclear | Unclear |

### C10-B — TARTE

**Disagreeing labels:** None.

**Primary scope and protected set**

- Tested semantic use: FastText semantic initialization conditional on table pretraining
- Protected observations: Cell/numerical values, target labels and examples
- Protected metadata: Non-tested metadata and field identities
- Protected representation: Non-tested cell initialization/encoder and downstream representation
- Protected predictive setup: Same table-pretraining status, model family and Ridge training policy
- Scope evidence: C10 official indexed published Figure 6 p.10/§4.3 from eligibility screening; supplied tarte.pdf is arXiv v2 corroboration, not the accepted PDF. Conditions known, implementation details not fully established from published source.

**Second scope and protected set**

- Tested semantic use: External linguistic meaning provided by the string encoder; table-level Enriched YAGO4.5 pretraining is protected as a distinct component.
- Protected observations: All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.
- Protected metadata: Feature identity/position, type and category-domain information, and target/task identity, except the explicitly tested semantic channel.
- Protected representation: Feature slots, numeric/date/missingness handling and fixed representation-to-Ridge interface; compatible string-encoder replacement is allowed.
- Protected predictive setup: Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted. Table-model pretraining regime and downstream Ridge fitting recipe are protected independently of the tested channel.
- Scope evidence: C10 official indexed published Figure 6 p.10/§4.3 from eligibility screening; supplied tarte.pdf is arXiv v2 corroboration, not the accepted PDF. Conditions known, implementation details not fully established from published source.

| Gate | Primary | Second |
|---|---|---|
| Removal | Pass | Pass |
| Preservation | Fail | Fail |
| Interface | Unclear | Unclear |
| Admissible reference | No | No |

## Preserved artifacts and limitations

Primary design codes remain the primary analysis. Secondary statuses are a sensitivity analysis with no outcome re-join. Suspected factual errors, if any, are listed in the independent coder’s review; disagreements alone do not authorize a correction. The original primary operational addendum was not supplied; the user-requested shared rule was CONTROL_CODING_RULE_V1. Operational interpretation differences as well as coder-declared protection can contribute to disagreement.

CSV files provide full 3×3 confusion tables, every paired code/rationale, disagreements and study status transitions. Source access limitations and incidental exposure are documented in ../independent/REVIEW_SECOND_V1.md.
