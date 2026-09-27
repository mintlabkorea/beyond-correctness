"""Materialize hand-coded published-design judgments; contains no outcomes."""
from pathlib import Path
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parent
ROWS = []

def row(id, study, component, intended, comparator, intervention, wrong, removal_like,
        removal, preservation, interface, evidence, protected, rationale):
    gates = [removal, preservation, interface]
    admissible = 'No' if 'Fail' in gates else ('Yes' if gates == ['Pass'] * 3 else 'Unclear')
    content = ('Yes' if preservation == interface == 'Pass' else 'Partial') if wrong == 'Yes' else ('Partial' if wrong == 'Unclear' else 'No')
    utility = {'Yes': 'Yes', 'No': 'No', 'Unclear': 'Partial'}[admissible]
    ROWS.append(dict(ID=id, Study=study, **{
        'Semantic component': component, 'Intended condition': intended,
        'Comparator': comparator, 'Intervention type': intervention,
        'Wrong-like?': wrong, 'Removal-like?': removal_like, 'Removal': removal,
        'Preservation': preservation, 'Interface validity': interface,
        'Admissible reference for utility?': admissible,
        'Can identify content sensitivity?': content,
        'Can identify predictive utility?': utility, 'Evidence': evidence,
        'Protected information/setup': protected, 'Rationale': rationale}))

L='C01 official main §4.1, Table 9 (p.8); official supplement D.2.1 (printed pp.42–44)'
row('C01-01','LIFT','Feature-name/value association, prompt format I',
    'Correct-Names I','Shuffled-Names I','shuffle','Yes','No','Fail','Unclear','Unclear',L,
    'Values and their multiplicities, target question, name inventory, prompt-I structure, training recipe',
    'The condition is a name shuffle, not absence of names. However, the published supplementary example repeats semester and does not present a clean bijection of the listed names. This may be a typographical error, but the paper alone does not resolve it. Do not certify cardinality or exact preservation from the caption alone; no execution failure is asserted.')
row('C01-02','LIFT','Feature-name/value association, prompt format II',
    'Correct-Names II','Shuffled-Names II','shuffle; compound','Yes','No','Fail','Unclear','Unclear',L,
    'Values and their multiplicities, target question, linguistic template, training recipe',
    'The supplement acknowledges incoherent sentences; incoherence alone is not interface invalidity. Its worked shuffled example also appears to repeat or omit values relative to the intended example. Exact value/routing preservation is unresolved, so this is only a partial content-sensitivity design, not an established clean permutation.')
for k in ['I','II']:
    row('C01-03' if k=='I' else 'C01-04','LIFT','Feature-name semantics conditional on other prompt information, format '+k,
        'Correct-Names '+k,'W/o Names '+k+' (Table 9 label)','removal; replacement; compound',
        'No','Yes','Pass','Fail','Pass',L,
        'Target description, value rendering, format-specific scaffolding, predictor and learning recipe',
        'The main table has two unnamed variants; the supplement illustrates a generic indexed prompt rather than literal absence of identifiers. The example also changes the named task question to generic y and textual categories to codes; format II additionally changes sentence scaffolding. Thus names are withdrawn, but feature-name-only utility is not isolated. The generic input remains valid language-model input; exact dataset-wise unnamed templates are not fully supplied.')

T='C03 official §3 (PDF pp.3–4), §5.1/Figure 2 (p.6), supplementary Tables 12–14 and §9'
row('C03-01','TabLLM','Feature-name/value association',
    'List Template','List Permuted Names','shuffle','Yes','No','Fail','Pass','Pass',T,
    'Field order, values, list scaffolding, task prompt, T0 and tuning protocol',
    'The paper specifies one name permutation shared across examples. Names remain semantic but are assigned to other fields; this preserves the list/value contract and supports intended–wrong content sensitivity. Derangement is not guaranteed, so the claim is sensitivity to the published permutation, not to every field being wrong.')
row('C03-02','TabLLM','Feature-name semantics conditional on List Template structure',
    'List Template','List Only Values','removal; compound','No','Yes','Pass','Fail','Pass',T,
    'List field scaffolding and stable explicit field identifiers, ordered values, task prompt, learner',
    'The comparator removes names along with their field-label scaffolding rather than substituting neutral names in the same List Template. Ordered values may remain, but that does not preserve the claim-specific serialization contract. It is valid LM input. This coding is consistent with the existing manuscript; its format-preservation requirement is an auditor-defined estimand, not an original-author requirement.')
row('C03-03','TabLLM','Value meaning, including continuous-value information',
    'List Template','List Permuted Values','shuffle; corruption; compound','Yes','No','Fail','Fail','Pass',T,
    'Continuous resolution, value/type representation, feature names and template, learner',
    'Per-column value mappings are shared across examples, but continuous values are first binned into ten uniform bins. The pooled contrast therefore changes resolution as well as meaning. A separately specified categorical-only bijection might admit a cleaner content contrast; this mixed published condition is Partial, and it is not an absence reference.')

P='C04 Ruiz et al. official §3.1–3.2, §4.1; Table 3 (p.7), construction (p.9)'
row('C04-01','PLATO','Broader-domain KG information beyond feature nodes',
    'Full KG','Feature-only KG','removal','No','Yes','Unclear','Unclear','Pass',P,
    'Feature nodes and observations, non-tested feature information, MLP weight-inference recipe',
    'The induced feature-node subgraph removes the broader nodes from message passing. The model also uses pretrained KG embeddings; the published ablation does not fully state whether these are rebuilt without broader-domain information. Their retained content and the non-tested embedding setup are unresolved. Subgraph deletion itself is not automatically a preservation violation. Feature nodes still provide the specified input/output interface.')
row('C04-02','PLATO','Auxiliary KG contribution with the KG-enabled predictive setup protected',
    'Full KG','No KG (standard MLP)','removal; compound','No','Yes','Pass','Fail','Pass',P,
    'Tabular observations and KG-enabled weight-inference architecture/training setup',
    'The paper explicitly ablates to a standard MLP without KG access. Removal passes; preservation fails because the feature-weight generation mechanism changes. Both models still accept tabular predictors and predict the same target, so this architecture change is not itself an input/output interface failure. Only a broader architecture-plus-knowledge comparison is available.')
row('C04-03','PLATO','Complete supplied KG relational information',
    '100% KG edges','50% KG edges (random edge deletion)','removal','No','Yes','Fail','Unclear','Pass',
    'C04 official §4.1 (p.9), Table 4',
    'Feature observations, non-tested node features/embeddings, same learner',
    'This is a partial missing-edge robustness condition: half the edges remain, and deleting facts does not assert false facts. It is neither absence of the full tested KG use nor a matched-wrong graph. Whether embeddings are recomputed is unspecified. Graph sparsification is compatible with the message-passing interface as described.')

C='C05 official §3/architecture, Appendix C.3 and Figure 10 (p.21)'
row('C05-01','CARTE','Language-semantic feature initialization, conditional on encoder/predictor setup',
    'CARTE','Graph Construction with Minhash','replacement; compound','No','Yes','Pass','Fail','Unclear',C,
    'Encoder family/geometry, value and field information, graph predictor and training recipe',
    'MinHash replaces the semantic initialization channel by an n-gram string encoder. Removal is limited to that language-semantic channel, not all knowledge in pretrained CARTE. Encoder identity and representation geometry change, failing the protected setup. Dimensions, collision handling, and compatibility with the pretrained graph model are not specified sufficiently for an interface Pass.')
row('C05-02','CARTE','Column semantics carried by edge information',
    'CARTE','Exclude Edge Info.','removal; compound','No','Yes','Unclear','Unclear','Unclear',C,
    'Value-bearing node initializations and multiplicities, graph architecture/routing',
    'Numerical nodes are initialized using column-name embeddings as well as numerical values. The label Exclude Edge Info. does not specify whether that pathway is retained, nor whether edge vectors are neutralized or the edge-conditioned computation is changed. Thus complete removal and protected numeric routing are unresolved. Do not infer clean name removal from a plot label.')
row('C05-03','CARTE','Column semantics carried by edge information',
    'CARTE','Exclude Att. Layer & Edge Info.','removal; compound','No','Yes','Unclear','Fail','Unclear',C,
    'Attention architecture, value-bearing node initializations, same graph predictor',
    'The condition expressly removes attention as well as edge information, so the protected model changes. Whether column information persists in numerical-node initialization remains unclear; post-removal routing/shape handling is also unspecified. This is not an admissible component-specific reference.')

F='C06 official §3.1/Figure 2 (pp.3–4), §4.2/Table 4 (pp.7–8), Appendix A.2, K.2/Table 18'
row('C06-01','FeatLLM','Feature-definition prose, conditional on type/category metadata',
    'FeatLLM','-Description','removal; compound','No','Yes','Pass','Fail','Unclear',F,
    'Types, category inventory, task/examples, generation/parser instructions and learner policy',
    'The feature-description block includes value types and sometimes category inventories, not just explanatory prose. Omitting the block also withdraws protected schema information used to generate type-compatible rules. The ablated prompt and per-arm type/error handling are not documented sufficiently for interface validation. Changes in generated rules are mediators, not the reason for the Preservation failure.')
row('C06-02','FeatLLM','Entire supplied feature-description block (definitions, types, category information)',
    'FeatLLM','-Description','removal','No','Yes','Pass','Pass','Unclear',F,
    'Task description, demonstrations, model/generation/parser recipe, feature-count and tuning policy',
    'Scope alternative to C06-01, not another experiment. With all block contents declared tested, their removal is allowed; the reported single-component ablation retains the remaining recipe at design level. However, type-guided generation/parsing without that block is insufficiently documented. Rule changes do not automatically violate preservation. Utility remains conditional on interface clarification.')
row('C06-03','FeatLLM','Use of the Step-1 reasoning instruction during rule generation',
    'FeatLLM (two-step generation)','-Reasoning','removal','No','Yes','Pass','Pass','Unclear',F,
    'Task/feature metadata, demonstrations, rule budget, parser and downstream learner policy',
    'Step 1 is omitted; this removes an elicitation procedure, not all semantic knowledge in the LM or all feature descriptions. Under this narrow procedural scope, generated-rule changes are allowed mediators. Step 2 references Step 1, and the exact edited prompt/output contract is not given, so interface compatibility remains unresolved. Do not interpret this row as utility of supplied factual relation content.')

row('C07-01','TabuLa-8B','Joint feature-header and target-header semantic content',
    'TABULA-8B with original UniPredict headers',
    'TABULA-8B with feature headers X1, X2, ... and target header Y',
    'replacement','No','Yes','Pass','Pass','Pass',
    'C07 official §5.5; Appendix F.2 (p.26), Figure 12 (p.27)',
    'Table values, feature identity and positions, target values, serialization and model/evaluation policy',
    'F.2 explicitly changes headers only and evaluates the same model on the data. Stable indexed feature names and Y remain valid headers. This is a design-admissible reference for the joint header-content scope, not absence of all pretrained knowledge. A feature-name-only scope protecting the original target header would instead fail Preservation. Pass is not a runtime/token-budget audit or a claim of positive utility.')

X='C08 official §5.1 (p.8), Table 2 bottom block (p.9), Appendix A.4, Figures 9–10 (pp.27–28)'
for i,(label,detail) in enumerate([
    ('Ordinal encoder','Ordinal identifiers discard language-semantic similarity and change the encoder/representation family.'),
    ('MinHash encoder','Morphological hashing replaces the semantic embedding channel and changes its geometry/collision properties.'),
    ('AutoGluon encoder','A conventional feature-preprocessing pipeline replaces the semantic encoding pipeline.'),
    ('Gap encoder','Character-string decomposition replaces semantic embeddings with a different representational basis.')],1):
    row('C08-0'+str(i),'ConTextTab','LLM-based categorical/string feature semantics, conditional on encoder setup',
        'base (feature and column name semantics)', 'no feature semantics - '+label,
        'replacement; compound','No','Yes','Pass','Fail','Unclear',X,
        'Encoder family/representation, non-tested column metadata, numerical values, model/training policy',
        detail+' Removal is only of the declared LLM feature-embedding channel. The nominal same-learner experiment does not demonstrate unchanged representation dimensionality, initialization or routing for each encoder. These are representation comparisons, not misinformation controls.')
row('C08-05','ConTextTab','Supplied column-header semantic content',
    'base (feature and column name semantics)','column semantics - drop column names (col1, ..., colN)',
    'replacement','No','Yes','Pass','Pass','Pass',X,
    'Cell contents, stable field positions/identities, semantic cell encoder, header-input path and evaluation policy',
    'The text explicitly describes generic-name replacement, not deleting columns. It preserves a header at every field in the same semantic-encoding pathway; column-name meaning is the tested span. This supports reference-relative design identification without claiming numerical invariance or runtime validation.')
row('C08-06','ConTextTab','Additional LLM-generated contextual column descriptions',
    'column semantics - add description (<name>:<description>)',
    'base (original column names only)','removal','No','Yes','Pass','Unclear','Pass',X,
    'Original names, cell data, evaluation population, generation access policy, same model/encoder',
    'Both variants are published; the intended direction is the enriched condition for this incremental-description scope. Generated descriptions use five sampled rows. It is not specified sufficiently whether that generation access is restricted to the same allowed context, especially relative to evaluation rows/targets. Removing descriptions is clear and the text interface stays valid, but protected information access is unresolved. No generated description is assumed correct by default.')

S='C09 official §4/A.1 (dual numerical/semantic paths), §6 Q3 (p.9), Table 4 (p.10), Appendix G.4/Tables 31–32 (pp.53–54)'
row('C09-01','TabSTAR','Explicit quantile information in numerical verbalization, conditional on bin ranges',
    'TabSTAR (Name + Bin + quantile information)','Name + Bin','removal','No','Yes','Pass','Pass','Pass',S,
    'Bin/range words, field name, numerical input branch, encoder/fusion architecture, training policy',
    'Q3 removes quantile wording while preserving the thinner name-plus-bin variant; the unchanged architecture separately encodes standardized numerical inputs. This identifies the contribution of supplying quantile text, not whether quantiles are unrecoverable from numbers or bins. Reconstructibility does not itself fail Removal of an explicit use. The declared variant preserves the semantic-element interface.')
row('C09-02','TabSTAR','Explicit numeric bin/quantile content in the verbalized branch',
    'TabSTAR (Name + Bin + quantile information)','Name (e.g. Age: Numeric)',
    'removal; replacement','No','Yes','Pass','Pass','Pass',S,
    'Separate standardized-numeric branch, field identity, encoder/fusion architecture and training policy',
    'The intervention concerns verbalization, not deleting numerical inputs from the model. The Name variant retains a generic numerical-type marker; the architecture continues to contain the numerical branch. Thus this is a reference for explicit verbalized numeric content under that branch, not for all numerical information or all feature semantics. Pass relies on the paper defining this as a verbalization-only variant.')

R='C10 published indexed Figure 6 (p.10)/§4.3; user tarte.pdf §4.3/Figure 6 is preacceptance corroboration only'
row('C10-01','TARTE','Supplied column-name semantic content',
    'TARTE | Enriched YAGO4.5','TARTE | Remove column names | Enriched YAGO4.5',
    'removal','No','Yes','Unclear','Unclear','Unclear',R,
    'Numerical/cell information, stable field identity, encoder/model, pretraining and Ridge policy',
    'The published figure establishes a column-information ablation but does not establish the exact operation (neutral names, zeroed embeddings, or dropping a branch). This matters because numerical routing can use column embeddings. The supplied preprint cannot close that published-version gap. No clean removal or preservation/interface Pass is inferred from the label.')
row('C10-02','TARTE','FastText semantic initialization with the tabular transformer unpretrained',
    'TARTE | Random weights (FastText initialization)',
    'TARTE | MinHash | Random weights','replacement; compound',
    'No','Yes','Pass','Fail','Unclear',R,
    'String encoder family/geometry, numerical/cell routing, random-initialized transformer and Ridge policy',
    'Both arms are shown in the same published figure; this is the explicitly stated audit pairing of those arms, not an assertion of a reported paired significance test. It holds absence of table pretraining nominally common, but swaps FastText for MinHash and hence changes the protected encoder. Dimensional/numeric compatibility is not specified sufficiently in the published extract.')
row('C10-03','TARTE','FastText semantic initialization conditional on table pretraining',
    'TARTE | Enriched YAGO4.5','TARTE | MinHash | Random weights',
    'replacement; compound','No','Yes','Pass','Fail','Unclear',R,
    'Table pretraining status, encoder/model setup, numerical routing, Ridge policy',
    'This alternative figure-arm pairing changes both the string encoder and table-pretraining status. It must not be substituted for C10-02 as an isolated FastText contrast. The label Random weights refers to the table model; it does not mean the FastText arm lacks pretrained language knowledge. These two pairings share arms and are not independent evidence.')


def main():
    requested = list(ROWS[0])[:-2]
    with (ROOT/'DESIGN_AUDIT_V1.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=requested,extrasaction='ignore');w.writeheader();w.writerows(ROWS)
    (ROOT/'DESIGN_AUDIT_V1.json').write_text(json.dumps(ROWS,ensure_ascii=False,indent=2)+'\n')
    lines=['# Published semantic-knowledge design audit v1','',
           '**9 studies; '+str(len(ROWS))+' scoped comparison rows.** C06-01/02 are two estimands for one experiment; TARTE pairings share arms. Do not treat row count as independent evidence.',
           '', 'All codes concern design identifiability, not observed effects. See [CODEBOOK_V1.md](CODEBOOK_V1.md) for Pass/Fail/Unclear and Yes/No/Partial definitions.',
           '', 'The complete requested 14 fields plus row ID are in [DESIGN_AUDIT_V1.csv](DESIGN_AUDIT_V1.csv). This readable view gives gates first, followed by exact conditions, protected information, and evidence for every row.', '',
           '| ID | Study | Wrong-like | Removal-like | Removal | Preservation | Interface | Admissible utility reference | Content sensitivity | Predictive utility |',
           '|---|---|---|---|---|---|---|---|---|---|']
    for r in ROWS:
        keys=['ID','Study','Wrong-like?','Removal-like?','Removal','Preservation','Interface validity','Admissible reference for utility?','Can identify content sensitivity?','Can identify predictive utility?']
        lines.append('| '+' | '.join(r[k] for k in keys)+' |')
    for r in ROWS:
        lines += ['', '## '+r['ID']+' — '+r['Study'], '']
        for k in ['Semantic component','Intended condition','Comparator','Intervention type','Protected information/setup','Rationale','Evidence']:
            lines += ['**'+k+':** '+r[k], '']
    (ROOT/'DESIGN_AUDIT_V1.md').write_text('\n'.join(lines)+'\n')
    assert len({r['Study'] for r in ROWS}) == 9
    assert len({r['ID'] for r in ROWS}) == len(ROWS)
    for r in ROWS:
        for k in ['Removal','Preservation','Interface validity']:
            assert r[k] in ['Pass','Fail','Unclear']
        for k in ['Wrong-like?','Removal-like?','Admissible reference for utility?']:
            assert r[k] in ['Yes','No','Unclear']
        for k in ['Can identify content sensitivity?','Can identify predictive utility?']:
            assert r[k] in ['Yes','No','Partial']
        if r['Admissible reference for utility?']=='Yes':
            assert all(r[k]=='Pass' for k in ['Removal','Preservation','Interface validity'])
        assert r['Evidence'] and r['Rationale'] and r['Protected information/setup']
    print(f'{len(ROWS)} rows / 9 studies; field vocabulary and gate consistency validated.')

if __name__=='__main__': main()
