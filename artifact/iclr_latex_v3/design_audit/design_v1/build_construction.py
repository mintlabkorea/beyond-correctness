"""Factual transcription only; does not assign design gates or read outcomes."""
from pathlib import Path
import csv
import json

P=Path(__file__).resolve().parent
rows=[]
def add(id,study,component,intended,comparator,changed,fixed,other,interface,evidence):
    rows.append(dict(zip(['Study','Comparison ID','Semantic component','Intended arm','Comparator arm',
                         'What changed','What remained fixed','Other simultaneous changes','Predictive interface','Evidence'],
                        [study,id,component,intended,comparator,changed,fixed,other,interface,evidence])))

L='Official C01 main §4.1/Table 9, PDF p.8; official supplement D.2.1, printed pp.42–44 (PDF pp.20–22); supplied LIFT.pdf also contains these examples.'
for suffix,fmt in [('A','I'),('B','II')]:
    add('C01-'+suffix,'LIFT','Feature names associated with feature values; prompt format '+fmt,
        'Correct-Names '+fmt,'Shuffled-Names '+fmt,
        'Authors describe randomly shuffling feature names within the corresponding prompt design.',
        'Caption describes the same LIFT/GPT-3 tabular tasks and paired prompt-format family; exact name/value inventory in the supplementary example is not consistently shown.',
        'D.2.1 example I repeats semester; example II changes the rendered value sequence and repeats summer. Authors explicitly note that format-II shuffled sentences may be incoherent. Whether the example inconsistencies reflect executed templates is not stated.',
        '불명 — same LM text-input/output scheme is described, but the printed examples do not establish consistent field/value routing.',L)
for suffix,fmt in [('C','I'),('D','II')]:
    add('C01-'+suffix,'LIFT','Names and contextual information in prompts; prompt format '+fmt,
        'Correct-Names '+fmt,'W/o Names '+fmt+' (Table 9)',
        'Compare named prompts with unnamed/generic-index prompts; the table distinguishes two formats.',
        'Same reported learner and task family. Supplement gives one generic W/O Names example, not a full per-dataset expansion of both table variants.',
        'Worked example replaces the named task question with generic y and category words with numerical codes; format II also differs from the generic sentence form. Exact correspondence to both unnamed table variants is not fully specified.',
        '동일 — text is still passed to the LM and a target response parsed; prompt content/wording changes. This does not certify all example-level mappings.',L)

T='Official C03 §3, PDF pp.3–4; §5.1/Figure 2, p.6; supplement Tables 12–14 and §9; supplied tabllm.pdf corroborates definitions.'
add('C03-A','TabLLM','Column-name/value associations','List Template','List Permuted Names',
    'Apply a permutation to column names; the same permutation is used across examples.',
    'Defined as List Template with permuted names: values, column positions and list form are retained by that definition; shared T0/fine-tuning setup is described globally.',
    'No additional intervention specified. The text does not require a derangement with no fixed points.',
    '동일 — List Template text serialization and LM prediction interface.',T)
add('C03-B','TabLLM','Column names in list serialization','List Template','List Only Values',
    'Serialize feature values only rather than column-name/value pairs.',
    'Value list and common task/learner recipe are described; the original list fixes an arbitrary column order.',
    'Field-name text and associated name/value list scaffolding are omitted; this is not described as replacement by generic field-name tokens.',
    '동일 — LM receives text and predicts the same target; serialization structure changes.',T)
add('C03-C','TabLLM','Column-value meanings and representations','List Template','List Permuted Values',
    'Generate one value permutation per column and apply it across all examples.',
    'Column names and List Template family; mapping is explicitly shared across examples.',
    'Continuous values are put into ten uniform bins before the value mapping.',
    '동일 — same list-to-LM prediction scheme with altered value tokens.',T)

K='Official C04 (Ruiz et al., not supplied plato.pdf): §3.1–3.2, Table 3 p.7, §4.1 p.9.'
add('C04-A','PLATO','Auxiliary feature nodes and broader-domain KG nodes','Full KG','Feature-only KG',
    'Use the induced subgraph on feature nodes instead of the full graph including broader-domain nodes.',
    'BRCA prediction task and PLATO family; feature nodes remain. Same recipe is described at study level.',
    'Graph size/neighborhoods change. Recomputing versus retaining pretrained KG embeddings is not specified for this contrast.',
    '동일 — feature nodes feed the PLATO weight-inference/prediction scheme; exact embedding construction is unspecified.',K)
add('C04-B','PLATO','Auxiliary KG input','Full KG','No KG',
    'Remove access to the auxiliary KG.',
    'Same BRCA tabular prediction task and observed feature/target definition.',
    'Paper explicitly states the no-KG configuration becomes a standard MLP, replacing KG-derived first-layer weight inference.',
    '변경 — KG-to-weight construction is replaced by standard MLP fitting; external tabular input/target interface remains.',K)
add('C04-C','PLATO','KG edges','100% edges','50% edges',
    'Randomly remove KG edges to retain the fraction reported in Table 4.',
    'BRCA task and PLATO model family.',
    'Connectivity changes; handling/retraining of pretrained node embeddings is not specified in the ablation description.',
    '동일 — graph message-passing predictor with a sparser graph; node-embedding details are unspecified.',
    'Official C04 §4.1 p.9, Table 4.')

C='Official C05 §3 and Appendix C.3/Figure 10, PDF p.21; supplied carte.pdf corroborates component labels. Figure arms expanded against CARTE baseline; no separate pairwise test is implied.'
add('C05-A','CARTE','String feature initialization','CARTE','Graph Construction with Minhash',
    'Replace feature initialization with skrub MinHash encoding based on string n-grams.',
    'Reported within the CARTE component study with the same train-size range; exact per-arm initialization/training alignment is not provided.',
    'The feature encoder changes; resulting dimensions, numerical-feature handling, and compatibility adaptation are not specified in C.3.',
    '변경 — string-to-vector encoder is replaced; downstream tensor compatibility details are 불명.',C)
add('C05-B','CARTE','Column/edge information','CARTE','Exclude Edge Info.',
    'Figure label specifies exclusion of edge information.',
    'Same component-study family and training-size range; exact implementation of the exclusion is not supplied.',
    'Main architecture also uses column embeddings in numerical-node initialization. The ablation text does not state whether that initialization is altered.',
    '불명 — zeroing/remapping edge vectors versus deleting edge-conditioned computation is not described.',C)
add('C05-C','CARTE','Edge information with attention component','CARTE','Exclude Att. Layer & Edge Info.',
    'Exclude both the attention layer and edge information, as named in the figure.',
    'Same component-study task family and train-size range.',
    'Attention-layer removal accompanies edge-information exclusion; exact replacement computation is unspecified.',
    '변경 — attention architecture is altered; resulting routing details are 불명.',C)

F='Official C06 §3.1/Figure 2 pp.3–4, §4.2/Table 4 pp.7–8, Appendix A.2 and K.2/Table 18; supplied featllm.pdf corroborates prompt components.'
add('C06-A','FeatLLM','Feature-description block in rule generation','FeatLLM','-Description',
    'Omit feature descriptions when generating rules.',
    'Authors present this as one component ablation; task/examples, parser, ensemble and tuning are described by the common recipe, not by a fully printed ablated prompt.',
    'Descriptions include value types, optional definitions and category examples/inventories. Rules and their binary features are generated anew; exact ablated prompt and per-arm error handling are not specified.',
    '불명 — common generate/parse/binary-feature pipeline is described, but type-compatible parsing after removal is not detailed.',F)
add('C06-B','FeatLLM','Step-1 reasoning instruction for rule generation','FeatLLM','-Reasoning',
    'Omit Step 1 of the reasoning instruction when generating rules.',
    'Other components use the common recipe according to the single-component ablation description.',
    'Step 2 in the full prompt refers to Step 1; the edited wording of that reference and the output format are not printed. Generated rules/features can change.',
    '불명 — same named pipeline, but exact edited generation/response contract is not given.',F)

add('C07-A','TabuLa-8B','Informative feature and target headers',
    'TABULA-8B on UniPredict with original headers (descriptive label)',
    'TABULA-8B with feature headers X1, X2, ... and target header Y (descriptive label)',
    'Replace original feature headers by indexed names and replace the target header by Y.',
    'F.2 explicitly says the data themselves are not altered; evaluation uses TABULA-8B on the modified tables.',
    'Target-header replacement accompanies feature-header replacement; no extra intervention is specified.',
    '동일 — replacement strings occupy header positions in the same tabular-LM evaluation scheme.',
    'Official C07 §5.5, Appendix F.2 p.26/Figure 12 p.27; supplied tabula.pdf has different pagination.')

X='Official C08 §5.1 p.8, Table 2 bottom semantic block p.9, Appendix A.4/Figures 9–10 pp.27–28; supplied contextab.pdf has different pagination.'
for suffix,encoder in [('A','Ordinal encoder'),('B','MinHash encoder'),('C','AutoGluon encoder'),('D','Gap encoder')]:
    add('C08-'+suffix,'ConTextTab','Categorical/string feature encoding',
        'base (feature and column name semantics)','no feature semantics - '+encoder,
        'Replace categorical/string semantic feature encodings with '+encoder+'.',
        'Semantic ablations are run on the CARTE benchmark; Table 2 identifies the one-dimensional-embedding base. Other settings follow the shared description; per-encoder adaptation details are not given.',
        'Encoding algorithm/representation changes; exact dimension, initialization and adaptation details are not reported for each variant.',
        '변경 — feature encoding path changes; precise downstream compatibility is 불명.',X)
add('C08-E','ConTextTab','Column-name encoding','base (feature and column name semantics)',
    'column semantics - drop column names',
    'Replace names by col1, ..., colN, as stated in §5.1.',
    'Column slots remain named by indexed strings; same semantic-ablation benchmark and base-model description.',
    'No additional intervention specified; this is name replacement, not removal of table columns.',
    '동일 — names remain string inputs to the column-name encoding path.',X)
add('C08-F','ConTextTab','Additional contextual column descriptions',
    'column semantics - add description','base (feature and column name semantics)',
    'Enriched arm uses <name>:<description> in place of the original name; comparator uses the original name. Direction here treats enrichment as the intended use.',
    'Original name is retained as a prefix; same semantic-ablation benchmark/model family.',
    'Descriptions are generated with gemma3-12b from five randomly sampled JSON-serialized rows. Which split/target information those rows expose is not specified in the quoted construction.',
    '동일 — enriched strings occupy the name-encoding path; description-generation access policy is unspecified.',X)

S='Official C09 §4/A.1, §6 Q3 p.9/Table 4 p.10, Appendix G.4/Tables 31–32 pp.53–54; supplied tabstar.pdf has different pagination.'
add('C09-A','TabSTAR','Quantile text in numerical verbalization','TabSTAR','Name + Bin',
    'Remove quantile information from the numerical verbalization.',
    'Name and bin information remain by variant definition. The general architecture has a separate numerical-input branch; Q3 describes a verbalization change and states no removal of that branch.',
    'No additional intervention specified; per-variant checkpoint/training matching is not separately detailed.',
    '동일 — numerical/semantic fusion architecture is described as common; semantic text content changes.',S)
add('C09-B','TabSTAR','Numerical information in verbalized features','TabSTAR','Name',
    'Remove numeric content from verbalization; illustrative entries retain a name and generic Numeric marker.',
    'Numerical-input branch remains in the common architecture; Q3 changes verbalization and does not state that numerical inputs are deleted.',
    'Bin and quantile wording are both absent in this variant; missing-value examples remain separately illustrated.',
    '동일 — common numeric/semantic architecture; this statement does not verify per-arm execution.',S)

R='C10 official indexed published Figure 6 p.10/§4.3 from eligibility screening; supplied tarte.pdf is arXiv v2 corroboration, not the accepted PDF. Conditions known, implementation details not fully established from published source.'
add('C10-A','TARTE','Column-name information','TARTE | Enriched YAGO4.5',
    'TARTE | Remove column names | Enriched YAGO4.5',
    'Figure names a variant without column-name information.',
    'Both labels specify Enriched YAGO4.5; caption uses Ridge on extracted representations. Exact checkpoint equality is not specified.',
    'Not specified whether names are replaced, embeddings zeroed, or a pathway omitted; effects on numerical-value initialization are not described in the published extract.',
    '불명 — exact name-removal and numerical-routing construction is not established.',R)
add('C10-B','TARTE','String encoder and table pretraining',
    'TARTE | Enriched YAGO4.5','TARTE | MinHash | Random weights',
    'Published figure includes a MinHash string-encoder variant with randomly initialized table-model weights.',
    'TARTE family and Ridge-on-embeddings evaluation are named; exact matching of random initialization and dimensions is unspecified.',
    'Encoder and table-pretraining status both differ from the Enriched YAGO4.5 baseline. A FastText/Random weights arm is also plotted but is not turned into an additional auditor-created pair here.',
    '변경 — string encoder changes; downstream tensor/numerical routing details are 불명.',R)

def main():
    assert len(rows)==26 and len({r['Study'] for r in rows})==9
    assert len({r['Comparison ID'] for r in rows})==len(rows)
    with (P/'CONTROL_CONSTRUCTION_V1.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (P/'CONTROL_CONSTRUCTION_V1.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    lines=['# Published control construction — factual record v1','',
           '9 fixed studies; 26 comparison rows. No wrong/reference/admissibility/gate/outcome codes are assigned here.',
           '', 'Source/version details and scope limitations: [PROVENANCE_AND_VALIDATION_V1.md](PROVENANCE_AND_VALIDATION_V1.md).',
           '', 'The CSV contains all ten requested fields. Rows sharing a baseline are not independent evidence.',
           '', '| Comparison ID | Study | Intended arm | Comparator arm |', '|---|---|---|---|']
    for r in rows:
        lines.append('| '+' | '.join(r[k].replace('|',' / ') for k in ['Comparison ID','Study','Intended arm','Comparator arm'])+' |')
    for r in rows:
        lines += ['', '## '+r['Comparison ID']+' — '+r['Study'],'']
        for k,v in r.items():
            if k not in ['Study','Comparison ID']: lines += ['**'+k+':** '+v,'']
    (P/'CONTROL_CONSTRUCTION_V1.md').write_text('\n'.join(lines)+'\n')
    print('26 factual comparisons / 9 studies; no design-verdict fields.')

if __name__=='__main__':main()
