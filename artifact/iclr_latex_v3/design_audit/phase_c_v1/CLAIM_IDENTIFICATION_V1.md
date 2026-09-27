# Claim-identification coding v1

9 fixed studies; 25 comparisons. All judgments are relative to the scope fixed before coding. No reported outcomes or empirical supported claims are included.

**Reported outcomes were not extracted or used in assigning the design codes.** Prior exposure and the earlier nonbinding draft are disclosed; this is not a blinded audit.

Each gate cell below includes its source location and reason. Evidence refers to archived official PDFs unless a published-indexed-source caveat is explicitly stated. See SOURCE_LINKS_V1.md for clickable source files.

Pass is a documentary design judgment; Unclear is not Fail. Changed encoder/architecture is not automatically Interface Fail. Derived identifiability is a capability of the design, not an observed benefit.

## C01-A — LIFT

**Tested semantic use:** Feature-name semantics/association within the specified prompt format

**Protected observations:** Observed values, their multiplicity, target labels and examples

**Protected metadata:** Target/task descriptions and category/value meanings

**Protected representation:** Format-specific scaffolding and field identity, except the tested name span

**Protected predictive setup:** Same LM family and training/inference policy

**Intended arm:** Correct-Names I

**Comparator arm:** Shuffled-Names I

**Intervention type:** shuffle

| Axis | Evidence-backed judgment |
|---|---|
| Wrong-like | Yes — Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.: Comparator intentionally misassigns semantic content. |
| Removal-like | No — Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.: Misassigned semantic content remains supplied rather than being withdrawn. |
| Removal | Fail — Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.: Shuffled names still supply semantic names. This is content misassignment, not absence of the tested name channel. |
| Preservation | Unclear — Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.: The caption describes a shuffle, but supplementary examples do not consistently preserve the name/value inventory. Their relation to the executed format-I templates is not resolved; do not silently repair a possible publication typo. |
| Interface | Unclear — Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.: Same LM family does not settle field/value routing. Printed example inconsistencies prevent confirming representation availability and interaction matching. Incoherence alone is not an interface failure, and no actual runtime failure is inferred. |
| Admissible reference | No — Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md: All Pass -> Yes; any Fail -> No; otherwise Unclear. |
| Content sensitivity identifiable | Partial — This row’s wrong-like construction, Preservation and Interface evidence: Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast. |
| Predictive utility identifiable | No — This row’s evidenced admissibility determination: Partial denotes unresolved identification, not a partially positive result. |

**Substantive interface checks:**

- Model pathway: Same LM text pathway is described. Evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.
- Representation availability: Name/value multiplicities in the worked examples are inconsistent. Evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.
- Training opportunity: Same learner/training family is reported; per-template implementation is not provided. Evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.
- Predictive interaction: Whether only association changed is unresolved. Evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.

## C01-B — LIFT

**Tested semantic use:** Feature-name semantics/association within the specified prompt format

**Protected observations:** Observed values, their multiplicity, target labels and examples

**Protected metadata:** Target/task descriptions and category/value meanings

**Protected representation:** Format-specific scaffolding and field identity, except the tested name span

**Protected predictive setup:** Same LM family and training/inference policy

**Intended arm:** Correct-Names II

**Comparator arm:** Shuffled-Names II

**Intervention type:** shuffle

| Axis | Evidence-backed judgment |
|---|---|
| Wrong-like | Yes — Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.: Comparator intentionally misassigns semantic content. |
| Removal-like | No — Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.: Misassigned semantic content remains supplied rather than being withdrawn. |
| Removal | Fail — Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.: Shuffled names still supply semantic names. This is content misassignment, not absence of the tested name channel. |
| Preservation | Unclear — Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.: The caption describes a shuffle, but supplementary examples do not consistently preserve the name/value inventory. Their relation to the executed format-II templates is not resolved; do not silently repair a possible publication typo. |
| Interface | Unclear — Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.: Same LM family does not settle field/value routing. Printed example inconsistencies prevent confirming representation availability and interaction matching. Incoherence alone is not an interface failure, and no actual runtime failure is inferred. |
| Admissible reference | No — Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md: All Pass -> Yes; any Fail -> No; otherwise Unclear. |
| Content sensitivity identifiable | Partial — This row’s wrong-like construction, Preservation and Interface evidence: Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast. |
| Predictive utility identifiable | No — This row’s evidenced admissibility determination: Partial denotes unresolved identification, not a partially positive result. |

**Substantive interface checks:**

- Model pathway: Same LM text pathway is described. Evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.
- Representation availability: Name/value multiplicities in the worked examples are inconsistent. Evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.
- Training opportunity: Same learner/training family is reported; per-template implementation is not provided. Evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.
- Predictive interaction: Whether only association changed is unresolved. Evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.

## C01-C — LIFT

**Tested semantic use:** Feature-name semantics/association within the specified prompt format

**Protected observations:** Observed values, their multiplicity, target labels and examples

**Protected metadata:** Target/task descriptions and category/value meanings

**Protected representation:** Format-specific scaffolding and field identity, except the tested name span

**Protected predictive setup:** Same LM family and training/inference policy

**Intended arm:** Correct-Names I

**Comparator arm:** W/o Names I (Table 9)

**Intervention type:** removal; replacement; compound

| Axis | Evidence-backed judgment |
|---|---|
| Wrong-like | No — Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.: Comparator withdraws/replaces an information channel without asserting a wrong correspondence. |
| Removal-like | Yes — Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.: Comparator nominally withdraws all or part of the declared channel; this does not establish complete removal. |
| Removal | Pass — Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.: The unnamed conditions remove informative feature names; a generic indexed identifier does not restore their semantic content. |
| Preservation | Fail — Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.: For the feature-name-only scope, the worked construction also substitutes a generic target question and recodes category words; the two prompt forms are not held constant. The published mapping for both unnamed variants is incomplete, so do not claim every dataset has the same additional changes. |
| Interface | Unclear — Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.: Corrected factual v1.1 records a common LM framework but unresolved target/category representation and variant mapping. Shared text I/O does not establish comparable access to protected representations or interactions. |
| Admissible reference | No — Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md: All Pass -> Yes; any Fail -> No; otherwise Unclear. |
| Content sensitivity identifiable | No — This row’s wrong-like construction, Preservation and Interface evidence: Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast. |
| Predictive utility identifiable | No — This row’s evidenced admissibility determination: Partial denotes unresolved identification, not a partially positive result. |

**Substantive interface checks:**

- Model pathway: Same LM text framework. Evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.
- Representation availability: Target/category rendering changes in the example; complete maps for both variants absent. Evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.
- Training opportunity: Common fitting recipe is described, but effective prompt opportunities are incompletely specified. Evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.
- Predictive interaction: Scaffolding and target/value interactions can change beyond name semantics. Evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.

## C01-D — LIFT

**Tested semantic use:** Feature-name semantics/association within the specified prompt format

**Protected observations:** Observed values, their multiplicity, target labels and examples

**Protected metadata:** Target/task descriptions and category/value meanings

**Protected representation:** Format-specific scaffolding and field identity, except the tested name span

**Protected predictive setup:** Same LM family and training/inference policy

**Intended arm:** Correct-Names II

**Comparator arm:** W/o Names II (Table 9)

**Intervention type:** removal; replacement; compound

| Axis | Evidence-backed judgment |
|---|---|
| Wrong-like | No — Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.: Comparator withdraws/replaces an information channel without asserting a wrong correspondence. |
| Removal-like | Yes — Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.: Comparator nominally withdraws all or part of the declared channel; this does not establish complete removal. |
| Removal | Pass — Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.: The unnamed conditions remove informative feature names; a generic indexed identifier does not restore their semantic content. |
| Preservation | Fail — Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.: For the feature-name-only scope, the worked construction also substitutes a generic target question and recodes category words; the two prompt forms are not held constant. The published mapping for both unnamed variants is incomplete, so do not claim every dataset has the same additional changes. |
| Interface | Unclear — Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.: Corrected factual v1.1 records a common LM framework but unresolved target/category representation and variant mapping. Shared text I/O does not establish comparable access to protected representations or interactions. |
| Admissible reference | No — Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md: All Pass -> Yes; any Fail -> No; otherwise Unclear. |
| Content sensitivity identifiable | No — This row’s wrong-like construction, Preservation and Interface evidence: Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast. |
| Predictive utility identifiable | No — This row’s evidenced admissibility determination: Partial denotes unresolved identification, not a partially positive result. |

**Substantive interface checks:**

- Model pathway: Same LM text framework. Evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.
- Representation availability: Target/category rendering changes in the example; complete maps for both variants absent. Evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.
- Training opportunity: Common fitting recipe is described, but effective prompt opportunities are incompletely specified. Evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.
- Predictive interaction: Scaffolding and target/value interactions can change beyond name semantics. Evidence: Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.

## C03-A — TabLLM

**Tested semantic use:** Feature-name semantics/association under List Template

**Protected observations:** Ordered values, target labels and examples

**Protected metadata:** Task/target prompt and non-tested value meanings

**Protected representation:** List Template scaffolding and stable field identity

**Protected predictive setup:** Same T0 and fine-tuning/evaluation policy

**Intended arm:** List Template

**Comparator arm:** List Permuted Names

**Intervention type:** shuffle

| Axis | Evidence-backed judgment |
|---|---|
| Wrong-like | Yes — Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.: Comparator intentionally misassigns semantic content. |
| Removal-like | No — Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.: Misassigned semantic content remains supplied rather than being withdrawn. |
| Removal | Fail — Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.: A fixed permutation continues to present meaningful column names; it does not withdraw the name-use channel. |
| Preservation | Pass — Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.: The definition changes names by a shared permutation while retaining the List Template and values. The scope is the published permutation, not a claim that all fields are deranged. |
| Interface | Pass — Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.: The same list slots, values, task prompt and T0 prediction/training scheme remain available. No new representation adapter or pathway is required; documentary comparability follows from the specified permutation. |
| Admissible reference | No — Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md: All Pass -> Yes; any Fail -> No; otherwise Unclear. |
| Content sensitivity identifiable | Yes — This row’s wrong-like construction, Preservation and Interface evidence: Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast. |
| Predictive utility identifiable | No — This row’s evidenced admissibility determination: Partial denotes unresolved identification, not a partially positive result. |

**Substantive interface checks:**

- Model pathway: Same list-to-T0 pathway. Evidence: Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.
- Representation availability: Values and list slots remain; name assignment changes. Evidence: Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.
- Training opportunity: Shared T0/tuning/evaluation procedure. Evidence: Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.
- Predictive interaction: Same name/value interaction form, with changed content. Evidence: Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.

## C03-B — TabLLM

**Tested semantic use:** Feature-name semantics/association under List Template

**Protected observations:** Ordered values, target labels and examples

**Protected metadata:** Task/target prompt and non-tested value meanings

**Protected representation:** List Template scaffolding and stable field identity

**Protected predictive setup:** Same T0 and fine-tuning/evaluation policy

**Intended arm:** List Template

**Comparator arm:** List Only Values

**Intervention type:** removal; compound

| Axis | Evidence-backed judgment |
|---|---|
| Wrong-like | No — Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.: Comparator withdraws/replaces an information channel without asserting a wrong correspondence. |
| Removal-like | Yes — Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.: Comparator nominally withdraws all or part of the declared channel; this does not establish complete removal. |
| Removal | Pass — Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.: List Only Values omits column names rather than retaining wrong semantic names. |
| Preservation | Fail — Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.: The declared scope protects List Template field scaffolding. Values-only serialization removes that scaffolding along with names, so ordered raw values alone do not satisfy this protection. This is an auditor-declared format-conditional estimand. |
| Interface | Pass — Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.: Both conditions explicitly serialize values to the same LM with the same target procedure. Altered text scaffolding is a documented Preservation issue, not evidence of an unavailable model path or an unintended parse/shape failure. This Pass is limited to the described end-to-end LM contract. |
| Admissible reference | No — Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md: All Pass -> Yes; any Fail -> No; otherwise Unclear. |
| Content sensitivity identifiable | No — This row’s wrong-like construction, Preservation and Interface evidence: Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast. |
| Predictive utility identifiable | No — This row’s evidenced admissibility determination: Partial denotes unresolved identification, not a partially positive result. |

**Substantive interface checks:**

- Model pathway: Same text-to-T0 predictor. Evidence: Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.
- Representation availability: Ordered values remain; explicit field scaffolding is removed. Evidence: Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.
- Training opportunity: Shared LM/tuning opportunity, no alternate learner specified. Evidence: Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.
- Predictive interaction: The same LM can process both strings; extra scaffold changes are recorded under Preservation. Evidence: Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.

## C03-C — TabLLM

**Tested semantic use:** Meaning assigned to values under the mixed categorical/continuous permutation

**Protected observations:** Original continuous resolution, categorical identity structure, targets and examples

**Protected metadata:** Feature names, task and target prompt

**Protected representation:** List Template scaffolding and stable field identity

**Protected predictive setup:** Same T0 and fine-tuning/evaluation policy

**Intended arm:** List Template

**Comparator arm:** List Permuted Values

**Intervention type:** shuffle; corruption; compound

| Axis | Evidence-backed judgment |
|---|---|
| Wrong-like | Yes — Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.: Comparator intentionally misassigns semantic content. |
| Removal-like | No — Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.: Misassigned semantic content remains supplied rather than being withdrawn. |
| Removal | Fail — Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.: Values are assigned changed meanings; the value-content channel remains in use. |
| Preservation | Fail — Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.: The continuous-value variant first introduces ten uniform bins, changing protected numerical resolution as well as the value mapping. A categorical-only invertible subcontrast is not substituted for the frozen mixed comparison. |
| Interface | Pass — Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.: Binned/permuted tokens remain within the defined list serialization and the same T0/task framework. The known resolution change is an information-preservation failure, not evidence that this described predictive interface is invalid. |
| Admissible reference | No — Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md: All Pass -> Yes; any Fail -> No; otherwise Unclear. |
| Content sensitivity identifiable | Partial — This row’s wrong-like construction, Preservation and Interface evidence: Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast. |
| Predictive utility identifiable | No — This row’s evidenced admissibility determination: Partial denotes unresolved identification, not a partially positive result. |

**Substantive interface checks:**

- Model pathway: Same list-to-LM path. Evidence: Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.
- Representation availability: Continuous resolution is reduced; value tokens remain. Evidence: Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.
- Training opportunity: Same reported task/tuning recipe. Evidence: Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.
- Predictive interaction: Same predictive processing; input-resolution change is explicit. Evidence: Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.

## C04-A — PLATO

**Tested semantic use:** Broader-domain KG information beyond feature nodes

**Protected observations:** BRCA features, labels and evaluated examples

**Protected metadata:** Feature-node information independent of the removed broader domain

**Protected representation:** Feature-node input representation and weight-inference interface

**Protected predictive setup:** Same PLATO family, capacity and training policy except tested graph input

**Intended arm:** Full KG

**Comparator arm:** Feature-only KG

**Intervention type:** removal

| Axis | Evidence-backed judgment |
|---|---|
| Wrong-like | No — Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.: Comparator withdraws/replaces an information channel without asserting a wrong correspondence. |
| Removal-like | Yes — Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.: Comparator nominally withdraws all or part of the declared channel; this does not establish complete removal. |
| Removal | Unclear — Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.: Broader-domain nodes leave the induced graph, but PLATO also uses pretrained KG embeddings. The ablation does not establish whether broader-domain information persists in those embeddings. |
| Preservation | Unclear — Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.: Feature nodes remain, but retained versus recomputed embeddings and their non-tested information are unspecified. Removing the tested nodes itself is allowed; the unresolved embedding construction is the issue. |
| Interface | Unclear — Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.: The weight-inference pathway is described, but embedding provenance and retraining determine the representations and opportunities available to that pathway. The published ablation does not settle them. |
| Admissible reference | Unclear — Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md: All Pass -> Yes; any Fail -> No; otherwise Unclear. |
| Content sensitivity identifiable | No — This row’s wrong-like construction, Preservation and Interface evidence: Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast. |
| Predictive utility identifiable | Partial — This row’s evidenced admissibility determination: Partial denotes unresolved identification, not a partially positive result. |

**Substantive interface checks:**

- Model pathway: PLATO weight-inference family retained. Evidence: Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.
- Representation availability: Broader nodes removed; feature-embedding provenance unresolved. Evidence: Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.
- Training opportunity: Recomputation/retraining of KG embeddings not specified for this contrast. Evidence: Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.
- Predictive interaction: Neighborhoods intentionally change; availability of broader pretrained content is unclear. Evidence: Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.

## C04-B — PLATO

**Tested semantic use:** Complete auxiliary KG use conditional on the KG-enabled predictive setup

**Protected observations:** BRCA features, labels and evaluated examples

**Protected metadata:** Non-tested feature information

**Protected representation:** Feature-node input representation and weight-inference interface

**Protected predictive setup:** Same PLATO family, capacity and training policy except tested graph input

**Intended arm:** Full KG

**Comparator arm:** No KG

**Intervention type:** removal; compound

| Axis | Evidence-backed judgment |
|---|---|
| Wrong-like | No — Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.: Comparator withdraws/replaces an information channel without asserting a wrong correspondence. |
| Removal-like | Yes — Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.: Comparator nominally withdraws all or part of the declared channel; this does not establish complete removal. |
| Removal | Pass — Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.: The paper explicitly states that No KG has no auxiliary KG access and becomes a standard MLP. |
| Preservation | Fail — Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.: Standard-MLP fitting replaces the protected KG-enabled first-layer weight-generation mechanism. Removing semantic input therefore accompanies a predictive-setup change. |
| Interface | Unclear — Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.: Both accept tabular inputs and predict the same target, but their first-layer learning pathways and opportunities differ. The paper does not establish a matched opportunity/interaction contract for the declared component-specific comparison; architecture change alone is not labelled an interface failure. |
| Admissible reference | No — Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md: All Pass -> Yes; any Fail -> No; otherwise Unclear. |
| Content sensitivity identifiable | No — This row’s wrong-like construction, Preservation and Interface evidence: Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast. |
| Predictive utility identifiable | No — This row’s evidenced admissibility determination: Partial denotes unresolved identification, not a partially positive result. |

**Substantive interface checks:**

- Model pathway: KG-to-weight inference becomes direct MLP fitting. Evidence: Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.
- Representation availability: Raw tabular observations remain; KG-derived feature-weight representation is absent. Evidence: Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.
- Training opportunity: First-layer fitting mechanism changes; matched capacity/opportunity not established. Evidence: Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.
- Predictive interaction: Interactions can differ with the model change; comparability is unresolved. Evidence: Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.

## C04-C — PLATO

**Tested semantic use:** Complete supplied KG relational information (not just the deleted subset)

**Protected observations:** BRCA features, labels and evaluated examples

**Protected metadata:** Non-tested feature information

**Protected representation:** Feature-node input representation and weight-inference interface

**Protected predictive setup:** Same PLATO family, capacity and training policy except tested graph input

**Intended arm:** 100% edges

**Comparator arm:** 50% edges

**Intervention type:** removal

| Axis | Evidence-backed judgment |
|---|---|
| Wrong-like | No — Official C04 §4.1 p.9, Table 4.: Comparator withdraws/replaces an information channel without asserting a wrong correspondence. |
| Removal-like | Yes — Official C04 §4.1 p.9, Table 4.: Comparator nominally withdraws all or part of the declared channel; this does not establish complete removal. |
| Removal | Fail — Official C04 §4.1 p.9, Table 4.: The tested scope is all supplied KG relational information; the comparator retains half the edges. Missing edges alone do not form a false-fact control. |
| Preservation | Unclear — Official C04 §4.1 p.9, Table 4.: The feature inputs and model family remain, but the embedding-retention/recomputation policy accompanying random deletion is not given. |
| Interface | Unclear — Official C04 §4.1 p.9, Table 4.: Sparse graph processing is intentional, not a demonstrated failure. However, residual embedding information and its training opportunity are not documented enough to certify substantive interface comparability. |
| Admissible reference | No — Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md: All Pass -> Yes; any Fail -> No; otherwise Unclear. |
| Content sensitivity identifiable | No — This row’s wrong-like construction, Preservation and Interface evidence: Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast. |
| Predictive utility identifiable | No — This row’s evidenced admissibility determination: Partial denotes unresolved identification, not a partially positive result. |

**Substantive interface checks:**

- Model pathway: Same graph-prediction family with fewer edges. Evidence: Official C04 §4.1 p.9, Table 4.
- Representation availability: Half the edges remain; embedding information is uncertain. Evidence: Official C04 §4.1 p.9, Table 4.
- Training opportunity: Embedding refresh/retraining after deletion unspecified. Evidence: Official C04 §4.1 p.9, Table 4.
- Predictive interaction: Graph neighborhoods change intentionally; interaction with retained embeddings unresolved. Evidence: Official C04 §4.1 p.9, Table 4.

## C05-A — CARTE

**Tested semantic use:** Language-semantic string initialization, conditional on the remaining CARTE setup

**Protected observations:** Cell values, field multiplicity and target labels

**Protected metadata:** Non-tested names/value semantics

**Protected representation:** Encoder family and non-tested value/graph representation

**Protected predictive setup:** Graph predictor, capacity, pretraining/adaptation policy

**Intended arm:** CARTE

**Comparator arm:** Graph Construction with Minhash

**Intervention type:** replacement; compound

| Axis | Evidence-backed judgment |
|---|---|
| Wrong-like | No — Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.: Comparator withdraws/replaces an information channel without asserting a wrong correspondence. |
| Removal-like | Yes — Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.: Comparator nominally withdraws all or part of the declared channel; this does not establish complete removal. |
| Removal | Pass — Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.: MinHash substitutes for the declared language-semantic initialization channel. This Pass does not mean all knowledge in CARTE pretraining is erased. |
| Preservation | Fail — Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.: The entire string encoder and its representational geometry change, outside the scope of semantic content under a protected encoder/predictor setup. |
| Interface | Unclear — Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.: C.3 does not specify encoder dimensions, numerical routing, initialization adaptation or matched pretraining compatibility. Intentional replacement is not evidence of a shape/routing failure; the details required to assess comparability are missing. |
| Admissible reference | No — Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md: All Pass -> Yes; any Fail -> No; otherwise Unclear. |
| Content sensitivity identifiable | No — This row’s wrong-like construction, Preservation and Interface evidence: Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast. |
| Predictive utility identifiable | No — This row’s evidenced admissibility determination: Partial denotes unresolved identification, not a partially positive result. |

**Substantive interface checks:**

- Model pathway: String initialization replaced before the graph predictor. Evidence: Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.
- Representation availability: MinHash representation substituted; numerical/edge handling not fully specified. Evidence: Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.
- Training opportunity: Checkpoint/init/adaptation matching across encoders not supplied. Evidence: Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.
- Predictive interaction: Input geometry changes; downstream compatibility cannot be certified. Evidence: Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.

## C05-B — CARTE

**Tested semantic use:** Column semantics carried by edge information, including any retained column-conditioned routes

**Protected observations:** Cell values, field multiplicity and target labels

**Protected metadata:** Non-tested names/value semantics

**Protected representation:** Value-bearing node initialization and non-tested graph representation

**Protected predictive setup:** Graph predictor, capacity, pretraining/adaptation policy

**Intended arm:** CARTE

**Comparator arm:** Exclude Edge Info.

**Intervention type:** removal

| Axis | Evidence-backed judgment |
|---|---|
| Wrong-like | No — Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.: Comparator withdraws/replaces an information channel without asserting a wrong correspondence. |
| Removal-like | Yes — Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.: Comparator nominally withdraws all or part of the declared channel; this does not establish complete removal. |
| Removal | Unclear — Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.: The Exclude Edge Info. label does not establish removal from numerical-node initialization, which also uses column embeddings in the main architecture. |
| Preservation | Unclear — Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.: Zeroing/replacing edge information versus deleting its computation is not specified; protected value-bearing node information may be affected differently. |
| Interface | Unclear — Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.: The label does not define the resulting edge/node routes, representation availability or training adaptation. The existence of a published curve is not a validity check. |
| Admissible reference | Unclear — Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md: All Pass -> Yes; any Fail -> No; otherwise Unclear. |
| Content sensitivity identifiable | No — This row’s wrong-like construction, Preservation and Interface evidence: Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast. |
| Predictive utility identifiable | Partial — This row’s evidenced admissibility determination: Partial denotes unresolved identification, not a partially positive result. |

**Substantive interface checks:**

- Model pathway: Edge-removal operation not specified beyond label. Evidence: Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.
- Representation availability: Potential column-conditioned numerical-node route unresolved. Evidence: Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.
- Training opportunity: Pretraining/adaptation after the change not detailed. Evidence: Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.
- Predictive interaction: Neutralized vectors versus removed edge computation offer different interactions. Evidence: Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.

## C05-C — CARTE

**Tested semantic use:** Column semantics carried by edge information, including any retained column-conditioned routes

**Protected observations:** Cell values, field multiplicity and target labels

**Protected metadata:** Non-tested names/value semantics

**Protected representation:** Value-bearing node initialization and non-tested graph representation

**Protected predictive setup:** Graph predictor, capacity, pretraining/adaptation policy

**Intended arm:** CARTE

**Comparator arm:** Exclude Att. Layer & Edge Info.

**Intervention type:** removal; compound

| Axis | Evidence-backed judgment |
|---|---|
| Wrong-like | No — Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.: Comparator withdraws/replaces an information channel without asserting a wrong correspondence. |
| Removal-like | Yes — Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.: Comparator nominally withdraws all or part of the declared channel; this does not establish complete removal. |
| Removal | Unclear — Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.: Edge information is nominally removed, but the retained numerical-node path is not described well enough to exclude residual column semantics. |
| Preservation | Fail — Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.: The named condition also removes an attention layer, changing the protected predictive architecture. |
| Interface | Unclear — Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.: Attention removal is documented, but the replacement computation and value/edge routing are not. This establishes a model change, not an unintended interface failure; meaningful comparability remains underspecified. |
| Admissible reference | No — Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md: All Pass -> Yes; any Fail -> No; otherwise Unclear. |
| Content sensitivity identifiable | No — This row’s wrong-like construction, Preservation and Interface evidence: Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast. |
| Predictive utility identifiable | No — This row’s evidenced admissibility determination: Partial denotes unresolved identification, not a partially positive result. |

**Substantive interface checks:**

- Model pathway: Attention layer and edge channel removed; replacement computation unclear. Evidence: Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.
- Representation availability: Numerical-node/edge representation retention unspecified. Evidence: Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.
- Training opportunity: Matched adaptation opportunity not established. Evidence: Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.
- Predictive interaction: Attention-mediated interactions change; replacement interactions not described. Evidence: Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.

## C06-A — FeatLLM

**Tested semantic use:** Entire supplied feature-description block, including types, definitions and category information

**Protected observations:** Observed demonstrations, their labels and prediction inputs

**Protected metadata:** Task description and metadata outside that block

**Protected representation:** Same named examples, rule-count/format policy and binary-feature interface

**Protected predictive setup:** Same generator/parser/model family, ensemble and tuning recipe; generated rules may change

**Intended arm:** FeatLLM

**Comparator arm:** -Description

**Intervention type:** removal

| Axis | Evidence-backed judgment |
|---|---|
| Wrong-like | No — Official C06 §3.1/Figure 2 pp.3–4, §4.2/Table 4 pp.7–8, Appendix A.2 and K.2/Table 18; supplied featllm.pdf corroborates prompt components.: Comparator withdraws/replaces an information channel without asserting a wrong correspondence. |
| Removal-like | Yes — Official C06 §3.1/Figure 2 pp.3–4, §4.2/Table 4 pp.7–8, Appendix A.2 and K.2/Table 18; supplied featllm.pdf corroborates prompt components.: Comparator nominally withdraws all or part of the declared channel; this does not establish complete removal. |
| Removal | Pass — Official C06 §3.1/Figure 2 pp.3–4, §4.2/Table 4 pp.7–8, Appendix A.2 and K.2/Table 18; supplied featllm.pdf corroborates prompt components.: The tested scope is the entire supplied feature-description block: definitions, types and category information. -Description removes that block, not the LM’s latent knowledge. |
| Preservation | Pass — Official C06 §3.1/Figure 2 pp.3–4, §4.2/Table 4 pp.7–8, Appendix A.2 and K.2/Table 18; supplied featllm.pdf corroborates prompt components.: Under this package scope, its type/category contents are tested rather than protected. The paper describes a single-component omission with the remaining generation/parser/ensemble/tuning recipe common. Resulting rule and feature changes are mediators. A prose-only scope protecting type/category metadata would instead fail Preservation. |
| Interface | Unclear — Official C06 §3.1/Figure 2 pp.3–4, §4.2/Table 4 pp.7–8, Appendix A.2 and K.2/Table 18; supplied featllm.pdf corroborates prompt components.: The full prompt uses types to generate parseable rules; the exact ablated prompt and its type/error handling are not given. Comparable parser access, usable feature availability and training opportunity are therefore not established merely by sharing the pipeline name. |
| Admissible reference | Unclear — Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md: All Pass -> Yes; any Fail -> No; otherwise Unclear. |
| Content sensitivity identifiable | No — This row’s wrong-like construction, Preservation and Interface evidence: Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast. |
| Predictive utility identifiable | Partial — This row’s evidenced admissibility determination: Partial denotes unresolved identification, not a partially positive result. |

**Substantive interface checks:**

- Model pathway: Generate/parse/binary-feature pipeline named in both arms. Evidence: Official C06 §3.1/Figure 2 pp.3–4, §4.2/Table 4 pp.7–8, Appendix A.2 and K.2/Table 18; supplied featllm.pdf corroborates prompt components.
- Representation availability: Type/category block removed; feature availability after parsing not documented per arm. Evidence: Official C06 §3.1/Figure 2 pp.3–4, §4.2/Table 4 pp.7–8, Appendix A.2 and K.2/Table 18; supplied featllm.pdf corroborates prompt components.
- Training opportunity: Same nominal recipe; effective opportunity after generation/parse errors unspecified. Evidence: Official C06 §3.1/Figure 2 pp.3–4, §4.2/Table 4 pp.7–8, Appendix A.2 and K.2/Table 18; supplied featllm.pdf corroborates prompt components.
- Predictive interaction: Generated rules may legitimately change; comparability of valid rule interactions remains uncertain. Evidence: Official C06 §3.1/Figure 2 pp.3–4, §4.2/Table 4 pp.7–8, Appendix A.2 and K.2/Table 18; supplied featllm.pdf corroborates prompt components.

## C07-A — TabuLa-8B

**Tested semantic use:** Joint informative feature-and-target-header content

**Protected observations:** Table values, target values and examples

**Protected metadata:** Non-header metadata

**Protected representation:** Stable field positions/identities and serialization, except tested header strings

**Protected predictive setup:** Same TABULA-8B checkpoint and evaluation procedure

**Intended arm:** TABULA-8B on UniPredict with original headers (descriptive label)

**Comparator arm:** TABULA-8B with feature headers X1, X2, ... and target header Y (descriptive label)

**Intervention type:** replacement

| Axis | Evidence-backed judgment |
|---|---|
| Wrong-like | No — Official C07 §5.5, Appendix F.2 p.26/Figure 12 p.27; supplied tabula.pdf has different pagination.: Comparator withdraws/replaces an information channel without asserting a wrong correspondence. |
| Removal-like | Yes — Official C07 §5.5, Appendix F.2 p.26/Figure 12 p.27; supplied tabula.pdf has different pagination.: Comparator nominally withdraws all or part of the declared channel; this does not establish complete removal. |
| Removal | Pass — Official C07 §5.5, Appendix F.2 p.26/Figure 12 p.27; supplied tabula.pdf has different pagination.: F.2 replaces informative feature headers by indexed names and the target header by Y, withdrawing the joint header-content use declared in the scope. |
| Preservation | Pass — Official C07 §5.5, Appendix F.2 p.26/Figure 12 p.27; supplied tabula.pdf has different pagination.: F.2 explicitly leaves data unchanged and evaluates TABULA-8B with replaced headers. Both header classes are tested; target-header semantics are not silently treated as protected in this joint scope. |
| Interface | Pass — Official C07 §5.5, Appendix F.2 p.26/Figure 12 p.27; supplied tabula.pdf has different pagination.: Replacement strings occupy the same table-header pathway with the same model and evaluation procedure. Values and field identities remain available; the construction states no different training or predictive mechanism. This is a documentary comparison, not a rerun. |
| Admissible reference | Yes — Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md: All Pass -> Yes; any Fail -> No; otherwise Unclear. |
| Content sensitivity identifiable | No — This row’s wrong-like construction, Preservation and Interface evidence: Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast. |
| Predictive utility identifiable | Yes — This row’s evidenced admissibility determination: Partial denotes unresolved identification, not a partially positive result. |

**Substantive interface checks:**

- Model pathway: Same tabular-LM header/value pathway. Evidence: Official C07 §5.5, Appendix F.2 p.26/Figure 12 p.27; supplied tabula.pdf has different pagination.
- Representation availability: Values and stable header positions retained. Evidence: Official C07 §5.5, Appendix F.2 p.26/Figure 12 p.27; supplied tabula.pdf has different pagination.
- Training opportunity: Same TABULA-8B evaluation opportunity. Evidence: Official C07 §5.5, Appendix F.2 p.26/Figure 12 p.27; supplied tabula.pdf has different pagination.
- Predictive interaction: Same model interactions with neutralized header content. Evidence: Official C07 §5.5, Appendix F.2 p.26/Figure 12 p.27; supplied tabula.pdf has different pagination.

## C08-A — ConTextTab

**Tested semantic use:** LLM-derived cell-feature semantic channel conditional on encoder setup

**Protected observations:** Cells, target labels and evaluated rows

**Protected metadata:** Column metadata not under test

**Protected representation:** Encoder family/geometry, numerical branch and field identity

**Protected predictive setup:** Same base-model family, capacity and training/adaptation/evaluation opportunity

**Intended arm:** base (feature and column name semantics)

**Comparator arm:** no feature semantics - Ordinal encoder

**Intervention type:** replacement; compound

| Axis | Evidence-backed judgment |
|---|---|
| Wrong-like | No — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: Comparator withdraws/replaces an information channel without asserting a wrong correspondence. |
| Removal-like | Yes — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: Comparator nominally withdraws all or part of the declared channel; this does not establish complete removal. |
| Removal | Pass — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: §5.1 replaces the LLM-based categorical/string semantic-embedding channel by the named ordinal encoding. Removal is scoped to that channel; neither all column semantics nor all pretrained model knowledge is claimed absent. |
| Preservation | Fail — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: The named encoder family/representation changes rather than only its semantic content. That violates the protected encoder/representation setup for this scoped claim. |
| Interface | Unclear — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: The paper describes an intentional ordinal replacement but does not fully specify per-encoder dimensions, normalization, initialization or training adaptation. No demonstrated unintended violation warrants Fail; pathway and opportunity compatibility remain unresolved. |
| Admissible reference | No — Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md: All Pass -> Yes; any Fail -> No; otherwise Unclear. |
| Content sensitivity identifiable | No — This row’s wrong-like construction, Preservation and Interface evidence: Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast. |
| Predictive utility identifiable | No — This row’s evidenced admissibility determination: Partial denotes unresolved identification, not a partially positive result. |

**Substantive interface checks:**

- Model pathway: Cell-feature encoder replaced; base learner remains the named family. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.
- Representation availability: Different representation supplied; dimensional/normalization compatibility unspecified. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.
- Training opportunity: Per-encoder initialization and adaptation details not established. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.
- Predictive interaction: The learner receives a different feature basis; matched predictive interactions not documented. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

## C08-B — ConTextTab

**Tested semantic use:** LLM-derived cell-feature semantic channel conditional on encoder setup

**Protected observations:** Cells, target labels and evaluated rows

**Protected metadata:** Column metadata not under test

**Protected representation:** Encoder family/geometry, numerical branch and field identity

**Protected predictive setup:** Same base-model family, capacity and training/adaptation/evaluation opportunity

**Intended arm:** base (feature and column name semantics)

**Comparator arm:** no feature semantics - MinHash encoder

**Intervention type:** replacement; compound

| Axis | Evidence-backed judgment |
|---|---|
| Wrong-like | No — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: Comparator withdraws/replaces an information channel without asserting a wrong correspondence. |
| Removal-like | Yes — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: Comparator nominally withdraws all or part of the declared channel; this does not establish complete removal. |
| Removal | Pass — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: §5.1 replaces the LLM-based categorical/string semantic-embedding channel by the named MinHash encoding. Removal is scoped to that channel; neither all column semantics nor all pretrained model knowledge is claimed absent. |
| Preservation | Fail — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: The named encoder family/representation changes rather than only its semantic content. That violates the protected encoder/representation setup for this scoped claim. |
| Interface | Unclear — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: The paper describes an intentional MinHash replacement but does not fully specify per-encoder dimensions, normalization, initialization or training adaptation. No demonstrated unintended violation warrants Fail; pathway and opportunity compatibility remain unresolved. |
| Admissible reference | No — Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md: All Pass -> Yes; any Fail -> No; otherwise Unclear. |
| Content sensitivity identifiable | No — This row’s wrong-like construction, Preservation and Interface evidence: Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast. |
| Predictive utility identifiable | No — This row’s evidenced admissibility determination: Partial denotes unresolved identification, not a partially positive result. |

**Substantive interface checks:**

- Model pathway: Cell-feature encoder replaced; base learner remains the named family. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.
- Representation availability: Different representation supplied; dimensional/normalization compatibility unspecified. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.
- Training opportunity: Per-encoder initialization and adaptation details not established. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.
- Predictive interaction: The learner receives a different feature basis; matched predictive interactions not documented. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

## C08-C — ConTextTab

**Tested semantic use:** LLM-derived cell-feature semantic channel conditional on encoder setup

**Protected observations:** Cells, target labels and evaluated rows

**Protected metadata:** Column metadata not under test

**Protected representation:** Encoder family/geometry, numerical branch and field identity

**Protected predictive setup:** Same base-model family, capacity and training/adaptation/evaluation opportunity

**Intended arm:** base (feature and column name semantics)

**Comparator arm:** no feature semantics - AutoGluon encoder

**Intervention type:** replacement; compound

| Axis | Evidence-backed judgment |
|---|---|
| Wrong-like | No — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: Comparator withdraws/replaces an information channel without asserting a wrong correspondence. |
| Removal-like | Yes — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: Comparator nominally withdraws all or part of the declared channel; this does not establish complete removal. |
| Removal | Pass — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: §5.1 replaces the LLM-based categorical/string semantic-embedding channel by the named AutoGluon encoding. Removal is scoped to that channel; neither all column semantics nor all pretrained model knowledge is claimed absent. |
| Preservation | Fail — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: The named encoder family/representation changes rather than only its semantic content. That violates the protected encoder/representation setup for this scoped claim. |
| Interface | Unclear — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: The paper describes an intentional AutoGluon replacement but does not fully specify per-encoder dimensions, normalization, initialization or training adaptation. No demonstrated unintended violation warrants Fail; pathway and opportunity compatibility remain unresolved. |
| Admissible reference | No — Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md: All Pass -> Yes; any Fail -> No; otherwise Unclear. |
| Content sensitivity identifiable | No — This row’s wrong-like construction, Preservation and Interface evidence: Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast. |
| Predictive utility identifiable | No — This row’s evidenced admissibility determination: Partial denotes unresolved identification, not a partially positive result. |

**Substantive interface checks:**

- Model pathway: Cell-feature encoder replaced; base learner remains the named family. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.
- Representation availability: Different representation supplied; dimensional/normalization compatibility unspecified. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.
- Training opportunity: Per-encoder initialization and adaptation details not established. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.
- Predictive interaction: The learner receives a different feature basis; matched predictive interactions not documented. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

## C08-D — ConTextTab

**Tested semantic use:** LLM-derived cell-feature semantic channel conditional on encoder setup

**Protected observations:** Cells, target labels and evaluated rows

**Protected metadata:** Column metadata not under test

**Protected representation:** Encoder family/geometry, numerical branch and field identity

**Protected predictive setup:** Same base-model family, capacity and training/adaptation/evaluation opportunity

**Intended arm:** base (feature and column name semantics)

**Comparator arm:** no feature semantics - Gap encoder

**Intervention type:** replacement; compound

| Axis | Evidence-backed judgment |
|---|---|
| Wrong-like | No — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: Comparator withdraws/replaces an information channel without asserting a wrong correspondence. |
| Removal-like | Yes — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: Comparator nominally withdraws all or part of the declared channel; this does not establish complete removal. |
| Removal | Pass — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: §5.1 replaces the LLM-based categorical/string semantic-embedding channel by the named Gap encoding. Removal is scoped to that channel; neither all column semantics nor all pretrained model knowledge is claimed absent. |
| Preservation | Fail — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: The named encoder family/representation changes rather than only its semantic content. That violates the protected encoder/representation setup for this scoped claim. |
| Interface | Unclear — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: The paper describes an intentional Gap replacement but does not fully specify per-encoder dimensions, normalization, initialization or training adaptation. No demonstrated unintended violation warrants Fail; pathway and opportunity compatibility remain unresolved. |
| Admissible reference | No — Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md: All Pass -> Yes; any Fail -> No; otherwise Unclear. |
| Content sensitivity identifiable | No — This row’s wrong-like construction, Preservation and Interface evidence: Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast. |
| Predictive utility identifiable | No — This row’s evidenced admissibility determination: Partial denotes unresolved identification, not a partially positive result. |

**Substantive interface checks:**

- Model pathway: Cell-feature encoder replaced; base learner remains the named family. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.
- Representation availability: Different representation supplied; dimensional/normalization compatibility unspecified. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.
- Training opportunity: Per-encoder initialization and adaptation details not established. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.
- Predictive interaction: The learner receives a different feature basis; matched predictive interactions not documented. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

## C08-E — ConTextTab

**Tested semantic use:** Supplied column-name semantic content

**Protected observations:** Cells, target labels and evaluated rows

**Protected metadata:** Cell meanings, target context and other metadata

**Protected representation:** Cell encoder and stable field slots; header pathway except tested name strings

**Protected predictive setup:** Same base-model family, capacity and training/adaptation/evaluation opportunity

**Intended arm:** base (feature and column name semantics)

**Comparator arm:** column semantics - drop column names

**Intervention type:** replacement

| Axis | Evidence-backed judgment |
|---|---|
| Wrong-like | No — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: Comparator withdraws/replaces an information channel without asserting a wrong correspondence. |
| Removal-like | Yes — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: Comparator nominally withdraws all or part of the declared channel; this does not establish complete removal. |
| Removal | Pass — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: §5.1 explicitly replaces column names with col1,...,colN, removing supplied name content without deleting columns. |
| Preservation | Pass — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: The defined change retains cell encodings, field slots and the shared semantic-ablation base model while replacing only header strings. This protects values and non-tested pathways at the documentary level. |
| Interface | Pass — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: Generic strings are processed by the same header encoder alongside the same cell pathway. No alternate encoder, learner or adaptation regime is introduced by the stated name-only construction. |
| Admissible reference | Yes — Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md: All Pass -> Yes; any Fail -> No; otherwise Unclear. |
| Content sensitivity identifiable | No — This row’s wrong-like construction, Preservation and Interface evidence: Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast. |
| Predictive utility identifiable | Yes — This row’s evidenced admissibility determination: Partial denotes unresolved identification, not a partially positive result. |

**Substantive interface checks:**

- Model pathway: Same column-name and cell-encoding routes. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.
- Representation availability: Indexed headers retain slots; cell values remain. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.
- Training opportunity: Common base-model semantic-ablation procedure. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.
- Predictive interaction: Same header/cell interaction form with different header content. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

## C08-F — ConTextTab

**Tested semantic use:** Additional generated contextual column-description content

**Protected observations:** Cells, target labels and evaluated rows

**Protected metadata:** Original column names and target context

**Protected representation:** Original field identity and column/cell-encoding pathways

**Protected predictive setup:** Same model/evaluation procedure and permitted row/target access; generated-description content may differ

**Intended arm:** column semantics - add description

**Comparator arm:** base (feature and column name semantics)

**Intervention type:** removal

| Axis | Evidence-backed judgment |
|---|---|
| Wrong-like | No — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: Comparator withdraws/replaces an information channel without asserting a wrong correspondence. |
| Removal-like | Yes — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: Comparator nominally withdraws all or part of the declared channel; this does not establish complete removal. |
| Removal | Pass — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: Original names alone omit the additional generated descriptions present in the enriched intended arm. |
| Preservation | Unclear — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: The descriptions use five sampled rows; §5.1 does not establish the permitted split/target access for that generation. The declared protection includes equal allowed information access, so this unresolved point matters. |
| Interface | Unclear — Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.: Both strings use the same encoder route, but the generator creates an additional route from sampled rows to the predictor. Without its access policy, representation availability and training/evaluation opportunity are not confirmed comparable. |
| Admissible reference | Unclear — Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md: All Pass -> Yes; any Fail -> No; otherwise Unclear. |
| Content sensitivity identifiable | No — This row’s wrong-like construction, Preservation and Interface evidence: Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast. |
| Predictive utility identifiable | Partial — This row’s evidenced admissibility determination: Partial denotes unresolved identification, not a partially positive result. |

**Substantive interface checks:**

- Model pathway: Same name encoder, plus description generation for intended arm. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.
- Representation availability: Generated text may carry information from sampled rows; source split unclear. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.
- Training opportunity: Permitted row/target access for generation unspecified. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.
- Predictive interaction: Additional contextual interactions are intended; allowable information feeding them is unclear. Evidence: Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.

## C09-A — TabSTAR

**Tested semantic use:** Explicit quantile text conditional on name-plus-bin verbalization

**Protected observations:** Numerical and other values, targets and examples

**Protected metadata:** Field names, non-tested metadata and target context

**Protected representation:** Separate numerical branch, fusion/interaction architecture and non-tested text; bin/range text is protected

**Protected predictive setup:** Same encoder/model family and training/adaptation recipe; fitted weights may change

**Intended arm:** TabSTAR

**Comparator arm:** Name + Bin

**Intervention type:** removal

| Axis | Evidence-backed judgment |
|---|---|
| Wrong-like | No — Official C09 §4/A.1, §6 Q3 p.9/Table 4 p.10, Appendix G.4/Tables 31–32 pp.53–54; supplied tabstar.pdf has different pagination.: Comparator withdraws/replaces an information channel without asserting a wrong correspondence. |
| Removal-like | Yes — Official C09 §4/A.1, §6 Q3 p.9/Table 4 p.10, Appendix G.4/Tables 31–32 pp.53–54; supplied tabstar.pdf has different pagination.: Comparator nominally withdraws all or part of the declared channel; this does not establish complete removal. |
| Removal | Pass — Official C09 §4/A.1, §6 Q3 p.9/Table 4 p.10, Appendix G.4/Tables 31–32 pp.53–54; supplied tabstar.pdf has different pagination.: Q3 defines a variant omitting quantile wording from verbalization. The scope is explicit textual supply, not absence of numerical information from the separate numerical branch or inability to reconstruct it. |
| Preservation | Pass — Official C09 §4/A.1, §6 Q3 p.9/Table 4 p.10, Appendix G.4/Tables 31–32 pp.53–54; supplied tabstar.pdf has different pagination.: The variant changes verbalization within the documented dual-path architecture; numerical observations, field identity and the separate numeric branch remain in the described recipe. No different architecture is specified. This is not an assertion of byte-identical fitted weights. |
| Interface | Pass — Official C09 §4/A.1, §6 Q3 p.9/Table 4 p.10, Appendix G.4/Tables 31–32 pp.53–54; supplied tabstar.pdf has different pagination.: Both arms keep the numerical/semantic fusion and prediction architecture, with a valid text element in the thinner variant. The shared training recipe allows the same pathways and opportunities while the declared wording changes. |
| Admissible reference | Yes — Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md: All Pass -> Yes; any Fail -> No; otherwise Unclear. |
| Content sensitivity identifiable | No — This row’s wrong-like construction, Preservation and Interface evidence: Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast. |
| Predictive utility identifiable | Yes — This row’s evidenced admissibility determination: Partial denotes unresolved identification, not a partially positive result. |

**Substantive interface checks:**

- Model pathway: Dual numerical/semantic paths and fusion retained by the verbalization-only design. Evidence: Official C09 §4/A.1, §6 Q3 p.9/Table 4 p.10, Appendix G.4/Tables 31–32 pp.53–54; supplied tabstar.pdf has different pagination.
- Representation availability: Numerical branch and non-tested text remain; tested wording omitted. Evidence: Official C09 §4/A.1, §6 Q3 p.9/Table 4 p.10, Appendix G.4/Tables 31–32 pp.53–54; supplied tabstar.pdf has different pagination.
- Training opportunity: Common model and training recipe as described; no per-arm rerun claimed. Evidence: Official C09 §4/A.1, §6 Q3 p.9/Table 4 p.10, Appendix G.4/Tables 31–32 pp.53–54; supplied tabstar.pdf has different pagination.
- Predictive interaction: Fusion/interaction mechanism retained; explicit semantic input differs. Evidence: Official C09 §4/A.1, §6 Q3 p.9/Table 4 p.10, Appendix G.4/Tables 31–32 pp.53–54; supplied tabstar.pdf has different pagination.

## C09-B — TabSTAR

**Tested semantic use:** Explicit bin/quantile numeric content in verbalization conditional on the numerical branch

**Protected observations:** Numerical and other values, targets and examples

**Protected metadata:** Field names, non-tested metadata and target context

**Protected representation:** Separate numerical branch, fusion/interaction architecture and non-tested text

**Protected predictive setup:** Same encoder/model family and training/adaptation recipe; fitted weights may change

**Intended arm:** TabSTAR

**Comparator arm:** Name

**Intervention type:** removal; replacement

| Axis | Evidence-backed judgment |
|---|---|
| Wrong-like | No — Official C09 §4/A.1, §6 Q3 p.9/Table 4 p.10, Appendix G.4/Tables 31–32 pp.53–54; supplied tabstar.pdf has different pagination.: Comparator withdraws/replaces an information channel without asserting a wrong correspondence. |
| Removal-like | Yes — Official C09 §4/A.1, §6 Q3 p.9/Table 4 p.10, Appendix G.4/Tables 31–32 pp.53–54; supplied tabstar.pdf has different pagination.: Comparator nominally withdraws all or part of the declared channel; this does not establish complete removal. |
| Removal | Pass — Official C09 §4/A.1, §6 Q3 p.9/Table 4 p.10, Appendix G.4/Tables 31–32 pp.53–54; supplied tabstar.pdf has different pagination.: Q3 defines a variant omitting bin/quantile numeric wording from verbalization. The scope is explicit textual supply, not absence of numerical information from the separate numerical branch or inability to reconstruct it. |
| Preservation | Pass — Official C09 §4/A.1, §6 Q3 p.9/Table 4 p.10, Appendix G.4/Tables 31–32 pp.53–54; supplied tabstar.pdf has different pagination.: The variant changes verbalization within the documented dual-path architecture; numerical observations, field identity and the separate numeric branch remain in the described recipe. No different architecture is specified. This is not an assertion of byte-identical fitted weights. |
| Interface | Pass — Official C09 §4/A.1, §6 Q3 p.9/Table 4 p.10, Appendix G.4/Tables 31–32 pp.53–54; supplied tabstar.pdf has different pagination.: Both arms keep the numerical/semantic fusion and prediction architecture, with a valid text element in the thinner variant. The shared training recipe allows the same pathways and opportunities while the declared wording changes. |
| Admissible reference | Yes — Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md: All Pass -> Yes; any Fail -> No; otherwise Unclear. |
| Content sensitivity identifiable | No — This row’s wrong-like construction, Preservation and Interface evidence: Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast. |
| Predictive utility identifiable | Yes — This row’s evidenced admissibility determination: Partial denotes unresolved identification, not a partially positive result. |

**Substantive interface checks:**

- Model pathway: Dual numerical/semantic paths and fusion retained by the verbalization-only design. Evidence: Official C09 §4/A.1, §6 Q3 p.9/Table 4 p.10, Appendix G.4/Tables 31–32 pp.53–54; supplied tabstar.pdf has different pagination.
- Representation availability: Numerical branch and non-tested text remain; tested wording omitted. Evidence: Official C09 §4/A.1, §6 Q3 p.9/Table 4 p.10, Appendix G.4/Tables 31–32 pp.53–54; supplied tabstar.pdf has different pagination.
- Training opportunity: Common model and training recipe as described; no per-arm rerun claimed. Evidence: Official C09 §4/A.1, §6 Q3 p.9/Table 4 p.10, Appendix G.4/Tables 31–32 pp.53–54; supplied tabstar.pdf has different pagination.
- Predictive interaction: Fusion/interaction mechanism retained; explicit semantic input differs. Evidence: Official C09 §4/A.1, §6 Q3 p.9/Table 4 p.10, Appendix G.4/Tables 31–32 pp.53–54; supplied tabstar.pdf has different pagination.

## C10-A — TARTE

**Tested semantic use:** Supplied column-name semantic content

**Protected observations:** Cell/numerical values, target labels and examples

**Protected metadata:** Non-tested metadata and field identities

**Protected representation:** Numerical/cell-value routing, field identity and non-tested representations

**Protected predictive setup:** Same table-pretraining status, model family and Ridge training policy

**Intended arm:** TARTE | Enriched YAGO4.5

**Comparator arm:** TARTE | Remove column names | Enriched YAGO4.5

**Intervention type:** removal

| Axis | Evidence-backed judgment |
|---|---|
| Wrong-like | No — C10 official indexed published Figure 6 p.10/§4.3 from eligibility screening; supplied tarte.pdf is arXiv v2 corroboration, not the accepted PDF. Conditions known, implementation details not fully established from published source.: Comparator withdraws/replaces an information channel without asserting a wrong correspondence. |
| Removal-like | Yes — C10 official indexed published Figure 6 p.10/§4.3 from eligibility screening; supplied tarte.pdf is arXiv v2 corroboration, not the accepted PDF. Conditions known, implementation details not fully established from published source.: Comparator nominally withdraws all or part of the declared channel; this does not establish complete removal. |
| Removal | Unclear — C10 official indexed published Figure 6 p.10/§4.3 from eligibility screening; supplied tarte.pdf is arXiv v2 corroboration, not the accepted PDF. Conditions known, implementation details not fully established from published source.: The published Figure 6 label establishes nominal column-information removal but not whether names, embeddings or a branch are removed. Residual column-conditioned numerical initialization is unresolved. |
| Preservation | Unclear — C10 official indexed published Figure 6 p.10/§4.3 from eligibility screening; supplied tarte.pdf is arXiv v2 corroboration, not the accepted PDF. Conditions known, implementation details not fully established from published source.: The labels share Enriched YAGO4.5, but exact checkpoint matching and preservation of value-bearing numerical routes are not established by the published extract. |
| Interface | Unclear — C10 official indexed published Figure 6 p.10/§4.3 from eligibility screening; supplied tarte.pdf is arXiv v2 corroboration, not the accepted PDF. Conditions known, implementation details not fully established from published source.: The exact operation and downstream value routing cannot be certified from the figure label. The supplied preacceptance PDF is not accepted-version evidence for filling those gaps. |
| Admissible reference | Unclear — Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md: All Pass -> Yes; any Fail -> No; otherwise Unclear. |
| Content sensitivity identifiable | No — This row’s wrong-like construction, Preservation and Interface evidence: Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast. |
| Predictive utility identifiable | Partial — This row’s evidenced admissibility determination: Partial denotes unresolved identification, not a partially positive result. |

**Substantive interface checks:**

- Model pathway: Exact name-removal pathway unspecified in published evidence. Evidence: C10 official indexed published Figure 6 p.10/§4.3 from eligibility screening; supplied tarte.pdf is arXiv v2 corroboration, not the accepted PDF. Conditions known, implementation details not fully established from published source.
- Representation availability: Numerical/cell representation retention unresolved. Evidence: C10 official indexed published Figure 6 p.10/§4.3 from eligibility screening; supplied tarte.pdf is arXiv v2 corroboration, not the accepted PDF. Conditions known, implementation details not fully established from published source.
- Training opportunity: Common pretraining label, not proof of checkpoint/adaptation equality. Evidence: C10 official indexed published Figure 6 p.10/§4.3 from eligibility screening; supplied tarte.pdf is arXiv v2 corroboration, not the accepted PDF. Conditions known, implementation details not fully established from published source.
- Predictive interaction: Column/value interactions after removal unspecified. Evidence: C10 official indexed published Figure 6 p.10/§4.3 from eligibility screening; supplied tarte.pdf is arXiv v2 corroboration, not the accepted PDF. Conditions known, implementation details not fully established from published source.

## C10-B — TARTE

**Tested semantic use:** FastText semantic initialization conditional on table pretraining

**Protected observations:** Cell/numerical values, target labels and examples

**Protected metadata:** Non-tested metadata and field identities

**Protected representation:** Non-tested cell initialization/encoder and downstream representation

**Protected predictive setup:** Same table-pretraining status, model family and Ridge training policy

**Intended arm:** TARTE | Enriched YAGO4.5

**Comparator arm:** TARTE | MinHash | Random weights

**Intervention type:** replacement; compound

| Axis | Evidence-backed judgment |
|---|---|
| Wrong-like | No — C10 official indexed published Figure 6 p.10/§4.3 from eligibility screening; supplied tarte.pdf is arXiv v2 corroboration, not the accepted PDF. Conditions known, implementation details not fully established from published source.: Comparator withdraws/replaces an information channel without asserting a wrong correspondence. |
| Removal-like | Yes — C10 official indexed published Figure 6 p.10/§4.3 from eligibility screening; supplied tarte.pdf is arXiv v2 corroboration, not the accepted PDF. Conditions known, implementation details not fully established from published source.: Comparator nominally withdraws all or part of the declared channel; this does not establish complete removal. |
| Removal | Pass — C10 official indexed published Figure 6 p.10/§4.3 from eligibility screening; supplied tarte.pdf is arXiv v2 corroboration, not the accepted PDF. Conditions known, implementation details not fully established from published source.: The published caption specifies replacing FastText with MinHash; the declared FastText initialization use is absent in that comparator. |
| Preservation | Fail — C10 official indexed published Figure 6 p.10/§4.3 from eligibility screening; supplied tarte.pdf is arXiv v2 corroboration, not the accepted PDF. Conditions known, implementation details not fully established from published source.: The figure-baseline comparison also changes table-model pretraining from Enriched YAGO4.5 to Random weights, as well as encoder family. Both are protected for FastText-content attribution. A nonbaseline matched-random-weights pair is not substituted. |
| Interface | Unclear — C10 official indexed published Figure 6 p.10/§4.3 from eligibility screening; supplied tarte.pdf is arXiv v2 corroboration, not the accepted PDF. Conditions known, implementation details not fully established from published source.: Different pretraining opportunities are documented, and the vector/numerical adaptation is unspecified. Those differences rule out a Preservation Pass but do not by themselves demonstrate a broken interface; compatible routes/interactions are not established. |
| Admissible reference | No — Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md: All Pass -> Yes; any Fail -> No; otherwise Unclear. |
| Content sensitivity identifiable | No — This row’s wrong-like construction, Preservation and Interface evidence: Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast. |
| Predictive utility identifiable | No — This row’s evidenced admissibility determination: Partial denotes unresolved identification, not a partially positive result. |

**Substantive interface checks:**

- Model pathway: String encoder changes. Evidence: C10 official indexed published Figure 6 p.10/§4.3 from eligibility screening; supplied tarte.pdf is arXiv v2 corroboration, not the accepted PDF. Conditions known, implementation details not fully established from published source.
- Representation availability: MinHash representation and numerical adaptation unspecified. Evidence: C10 official indexed published Figure 6 p.10/§4.3 from eligibility screening; supplied tarte.pdf is arXiv v2 corroboration, not the accepted PDF. Conditions known, implementation details not fully established from published source.
- Training opportunity: Pretrained baseline versus random-weight table model is an explicit opportunity difference. Evidence: C10 official indexed published Figure 6 p.10/§4.3 from eligibility screening; supplied tarte.pdf is arXiv v2 corroboration, not the accepted PDF. Conditions known, implementation details not fully established from published source.
- Predictive interaction: Comparable downstream representation interactions not established. Evidence: C10 official indexed published Figure 6 p.10/§4.3 from eligibility screening; supplied tarte.pdf is arXiv v2 corroboration, not the accepted PDF. Conditions known, implementation details not fully established from published source.
