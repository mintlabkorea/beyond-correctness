# W8 eligibility screening — 10 candidates, 9 included, 1 excluded

Date: 2026-09-08 (session date, Asia/Seoul).
Rule: unchanged [INCLUSION_RULE_FREEZE_V1.md](INCLUSION_RULE_FREEZE_V1.md).
Candidate universe: unchanged [CANDIDATES_V1.md](CANDIDATES_V1.md).
Screening decisions follow C01→C10. This is eligibility screening only;
control admissibility and supported claims have not been coded.

## Decision

**Include 9: LIFT, TabLLM, PLATO, CARTE, FeatLLM, TabuLa-8B,
ConTextTab, TabSTAR, TARTE. Exclude TransTab (E4).**

The requested 6–8 was the anticipated yield. The frozen rule explicitly
retains all eligible candidates and permits encoder/pipeline changes alongside
semantic changes. CARTE and TARTE both report eligible semantic interventions;
dropping either solely to reach eight would contradict that rule. No paper
was replaced, no discovery expansion was run, and no eligibility rule changed.
This nine-study set is the final set under v1, not a claim that an eight-study
set was obtained. Any later compact presentation must disclose the full nine.

## Criterion-level ledger

P = published; T = predictive tabular task; S = explicit semantic use;
A = published semantic intervention; L = traceable design. A pass only
establishes eligibility, not preservation, interface validity, or utility.

| ID | Study | P | T | S | A | L | Decision | Semantic intervention and evidence location |
|---|---|---|---|---|---|---|---|---|
| C01 | LIFT | yes | yes | yes | yes | yes | INCLUDE | Correct/Shuffled/W/o Names prompt variants; §4.1 pp.7–8, Table 9 p.8; official supplement D.2.1 printed pp.42–44 |
| C02 | TransTab | yes | yes | yes | no located | — | EXCLUDE E4 | Main §3.1–3.5 and official appendix A–D, Tables 8–12, Figures 4–6 inspected; no intervention on the semantic encoding/content itself located |
| C03 | TabLLM | yes | yes | yes | yes | yes | INCLUDE | List Template, List Only Values, List Permuted Names/Values; §3 PDF p.4, §5.1/Figure 2 p.6; supplement Table 12 p.19 |
| C04 | PLATO | yes | yes | yes | yes | yes | INCLUDE | Full KG / feature-only KG / No KG; Table 3 p.7, §4 p.9; edge deletion also reported in Table 4 |
| C05 | CARTE | yes | yes | yes | yes | yes | INCLUDE | Feature initialization replaced by MinHash; edge-information exclusions also reported; Appendix C.3/Figure 10 p.21 |
| C06 | FeatLLM | yes | yes | yes | yes | yes | INCLUDE | Feature-description omission during rule generation; §4.2 p.7, Table 4 p.8, Appendix K.2/Table 18 p.26 onward |
| C07 | TabuLa-8B | yes | yes | yes | yes | yes | INCLUDE | Original headers replaced with X1, X2, … and target with Y; §5.5 p.10, Appendix F.2 p.26/Figure 12 p.27 |
| C08 | ConTextTab | yes | yes | yes | yes | yes | INCLUDE | Column names replaced with col1,…,colN; separately semantic cell encoders replaced; §5.1 p.8, Table 2 p.9, Appendix A.4; Figures 9–10 pp.27/28 |
| C09 | TabSTAR | yes | yes | yes | yes | yes | INCLUDE | Numerical verbalization variants Name / Name + Bin / full; §6 Q3 p.9, Table 4 p.10; Appendix G.4, Tables 31–32 pp.53–54 |
| C10 | TARTE | yes | yes | yes | yes | yes | INCLUDE; source-access caveat | Remove column names and MinHash variants; published Figure 6 p.10 and §4.3; official indexed PDF evidence, cross-checked against author preprint (not a publication substitute) |

Page numbers are one-based PDF pages unless explicitly marked printed pages.
Inclusion needs at least one qualifying comparison. This ledger does not claim
to enumerate all comparisons that later deserve coding.

## Evidence and boundary cases

### C01 — LIFT: include

[Official main PDF](https://proceedings.neurips.cc/paper_files/paper/2022/file/4ce7fe1d2730f53cb3857032952cd1b8-Paper-Conference.pdf),
[official supplement](https://proceedings.neurips.cc/paper_files/paper/2022/file/4ce7fe1d2730f53cb3857032952cd1b8-Supplemental-Conference.pdf).
Table 9 reports tabular classification under named, shuffled-name, and
unnamed prompt variants. D.2.1 describes their construction and additional
evaluations. This is a single-table prediction comparison using a pretrained
LM, not itself a source–target schema-matching experiment. Importantly,
W/o Names should not yet be described as literally deleting all name tokens:
the supplementary example uses generic indexed features and a generic target.
Exact prompt changes belong to the next coding stage.

### C02 — TransTab: exclude E4

[Official main PDF](https://proceedings.neurips.cc/paper_files/paper/2022/file/1377f76686d56439a2bd7a91859972f5-Paper-Conference.pdf),
[official supplement ZIP](https://proceedings.neurips.cc/paper_files/paper/2022/file/1377f76686d56439a2bd7a91859972f5-Supplemental-Conference.zip).
The ZIP contains appendix.pdf (printed pp.15–19) and code.txt. The paper uses
column descriptions and original categorical descriptions, satisfying S.
Experiments compare supervised learning, incremental features, transfer,
zero-shot learning, and pretraining; supplementary analyses vary partition
number and actual column overlap. Figure 6 changes which measured columns
occur in training/test, not whether their semantic identities/descriptions are
correctly supplied, omitted, or re-encoded. These are task/input-availability
and learning-regime changes, not an explicit semantic-information ablation.
No qualifying comparison was located across those experimental sections and
the complete five-page official appendix. This is a scoped absence finding,
not proof that no later code or paper version contains such an experiment.
Our post-result TransTab regression experiments are outside this study's
published evidence and cannot rescue eligibility.

### C03 — TabLLM: include

[Official PDF](https://proceedings.mlr.press/v206/hegselmann23a/hegselmann23a.pdf).
§3 defines omission of names, a shared permutation of names across examples,
and a separate value permutation. Figure 2 and the supplementary tables
report predictive comparisons. Scope: within-dataset few-shot classification
with pretrained language knowledge. The original published comparisons are
the eligibility evidence; our subsequently constructed references are not.
At coding time, distinguish name permutation from value permutation.

### C04 — PLATO: include

[Official PDF](https://proceedings.neurips.cc/paper_files/paper/2023/file/53dd219b6b11abc8ce523921c18c7a3e-Paper-Conference.pdf).
§4 explicitly compares the full auxiliary KG, the induced subgraph on feature
nodes, and no KG on BRCA; Table 3 reports the comparison. The no-KG condition
becomes an MLP. That accompanying model change does not exclude the study
under criterion 4. Table 4 additionally reports randomly removed KG edges.
Scope: tabular prediction augmented with domain knowledge, without requiring
cross-schema transfer. No admissibility judgment is made here.

### C05 — CARTE: include

[Official PMLR PDF](https://raw.githubusercontent.com/mlresearch/v235/main/assets/kim24d/kim24d.pdf).
Appendix C.3 explicitly replaces feature initialization with skrub's MinHash
encoder. Figure 10 reports predictive learning curves alongside edge and
attention component exclusions. This changes semantic representation and
meets criterion 4 even though other representation properties may change.
The qualifying ablation is a downstream prediction component study; the
paper also evaluates transfer across tables. This is original published
evidence, separate from our later M/C/R CARTE extension. Consequently CARTE
cannot be discarded as lacking semantic ablation.

### C06 — FeatLLM: include

[Official PMLR PDF](https://raw.githubusercontent.com/mlresearch/v235/main/assets/han24f/han24f.pdf).
§4.2 defines omission of feature descriptions in the generation process;
Table 4 reports the ablation and Table 18 gives dataset-level entries.
This suffices independently of the separate reasoning-instruction ablation.
Scope: within-dataset few-shot classification through generated features.
Descriptions are altered upstream of the fitted predictor; detailed changes
to prompts, generated rules, and tuning remain for control coding.

### C07 — TabuLa-8B: include

[Official PDF](https://proceedings.neurips.cc/paper_files/paper/2024/file/4fd5cfd2e31bebbccfa5ffa354c04bdc-Paper-Conference.pdf).
Appendix F.2 defines replacement of original feature headers by X1, X2, …
**and replacement of the target header by Y** on the UniPredict benchmark.
Figure 12 reports the predictive comparison. Scope: pretrained cross-table
LM transfer evaluated on target tables. Do not later summarize this as an
isolated feature-name intervention without considering the target-name change.
Gardner et al. now has a published-design entry; this does not retroactively
explain why it was not previously quantitatively reproduced.

### C08 — ConTextTab: include

[Official PDF](https://proceedings.neurips.cc/paper_files/paper/2025/file/d807e7678ba3afd3a904f4af52819e77-Paper-Conference.pdf).
§5.1 contains two distinct eligible families: replacing semantic feature
encodings and replacing names with generic col-index names. It also reports
enrichment of names with generated descriptions. Table 2's bottom block
reports semantic experiments; Appendix A.4 and Figures 9–10 expand them.
Scope: pretrained tabular ICL, with these interventions on the CARTE benchmark.
The future audit must not collapse this paper to encoder replacement only;
it contains an explicit header-content intervention as well.

### C09 — TabSTAR: include

[Official PDF](https://proceedings.neurips.cc/paper_files/paper/2025/file/faf6e23e198314c7728eaa6ac44ae079-Paper-Conference.pdf).
§6 Q3 and Table 4 compare full numerical verbalization to variants removing
quantile information or numerical information from the verbalized feature.
Appendix G.4 illustrates the representations in Table 31 and reports results
in Table 32. Scope: classification and regression after foundation-model
pretraining. The Name variant's example retains a generic Numeric marker;
do not equate removing verbalized numeric content with removing the separate
numeric input path without further inspection. Verbalization is explicitly
within the frozen semantic scope, so this study remains eligible.

### C10 — TARTE: include, with transparent access provenance

[Official published PDF identifier](https://openreview.net/pdf?id=QV4P8Csw17),
[indexed version-specific official PDF](https://openreview.net/pdf/7dfbc481b152839b35e7f200b528bd880a6826e2.pdf),
[author preprint v2](https://arxiv.org/abs/2505.14415v2).
The web search tool returned the official PDF's publication banner (TMLR,
08/2025), Figure 6 caption/conditions, and accompanying §4.3 text. The figure
reports a ridge predictor on embeddings with column information removed;
it separately reports FastText replacement by MinHash. Both establish a
published semantic intervention; exact construction is a later coding issue.
The retrieved author preprint contains matching Figure 6 conditions, but is
dated before acceptance and is retained only as corroboration. It is **not**
labelled as the accepted PDF or asserted byte-identical to it.

Direct official downloads returned HTTP 403/browser challenge; the official
full PDF has not been archived locally. Eligibility rests on the explicitly
retrieved published-source excerpt, not on the preprint alone. Thus this is
not “ablation absent” and is not excluded. For subsequent exhaustive control
coding, obtain the published PDF or retain unclear codes where the published
excerpt is insufficient. Do not treat author-preprint details as automatically
part of the publication. Scope: knowledge-pretrained representations for
tabular classification/regression; the paper also studies domain transfer.

## Source provenance, exposure, and stage boundary

- Official main PDFs for C01–C09 and the separate C01/C02 supplements were
  downloaded; C07's official supplement ZIP was also saved. Other reviewed
  papers' appendices are embedded in their main PDFs.
- URLs and download hashes are in sources/DOWNLOAD_MANIFEST_V1.json; the
  final SOURCE_MANIFEST_V1.json also inventories extracted appendix files and
  derived text. C10's mirror has an explicitly different provenance role.
- TARTE official evidence was obtained with the queries `"TARTE" "ablation"
  "MinHash"` and `"TARTE" "Remove column names" "pre-trained"`. These were
  within-candidate eligibility searches, not searches for new studies or
  favorable effects. Official extracts were returned even though direct
  open/download failed. No anti-bot or access control was bypassed.
- Full PDF text and table captions unavoidably exposed performance numbers
  and directions. They were not extracted as study outcomes or used in the
  inclusion rule. Do not call this a blinded review or claim all numerical
  results were hidden.
- Final count: 10 screened, 9 included, 1 excluded, 0 eligibility-unresolved;
  one included study has a published-PDF archival/access caveat.
- Next stage: control construction coding. No wrong/reference/compound
  verdict, Removal/Preservation/Interface score, supported claim, or outcome
  synthesis is assigned by this screening record. Manuscript files untouched.
