"""Hand-adjudicated documentary gates; no reported outcomes are loaded."""
from pathlib import Path
import csv
import json

P=Path(__file__).resolve().parent
A=P.parent
C={r['Comparison ID']:r for r in json.loads((A/'design_v1_1/CONTROL_CONSTRUCTION_V1_1.json').read_text())}
S={r['Comparison ID']:r for r in json.loads((P/'CLAIM_SCOPES_V1.json').read_text())}
codes={}

def code(id,typ,wrong,removal_like,rg,rr,pg,pr,ig,ir,checks):
    # Every enum travels with its own locator and explanation.
    ev=C[id]['Evidence']
    codes[id]={'Intervention type':typ,
               'Wrong-like':{'value':wrong,'evidence':ev,'rationale':('Comparator intentionally misassigns semantic content.' if wrong=='Yes' else 'Comparator withdraws/replaces an information channel without asserting a wrong correspondence.')},
               'Removal-like':{'value':removal_like,'evidence':ev,'rationale':('Comparator nominally withdraws all or part of the declared channel; this does not establish complete removal.' if removal_like=='Yes' else 'Misassigned semantic content remains supplied rather than being withdrawn.')},
               'Removal':{'value':rg,'evidence':ev,'rationale':rr},
               'Preservation':{'value':pg,'evidence':ev,'rationale':pr},
               'Interface':{'value':ig,'evidence':ev,'rationale':ir},
               'Interface dimensions':dict(zip(['Model pathway','Representation availability','Training opportunity','Predictive interaction'],checks))}
    for k,v in codes[id]['Interface dimensions'].items():
        codes[id]['Interface dimensions'][k]={'observation':v,'evidence':ev}

for id,fmt in [('C01-A','I'),('C01-B','II')]:
    code(id,'shuffle','Yes','No','Fail',
         'Shuffled names still supply semantic names. This is content misassignment, not absence of the tested name channel.',
         'Unclear','The caption describes a shuffle, but supplementary examples do not consistently preserve the name/value inventory. Their relation to the executed format-'+fmt+' templates is not resolved; do not silently repair a possible publication typo.',
         'Unclear','Same LM family does not settle field/value routing. Printed example inconsistencies prevent confirming representation availability and interaction matching. Incoherence alone is not an interface failure, and no actual runtime failure is inferred.',
         ['Same LM text pathway is described.','Name/value multiplicities in the worked examples are inconsistent.','Same learner/training family is reported; per-template implementation is not provided.','Whether only association changed is unresolved.'])
for id in ['C01-C','C01-D']:
    code(id,'removal; replacement; compound','No','Yes','Pass',
         'The unnamed conditions remove informative feature names; a generic indexed identifier does not restore their semantic content.',
         'Fail','For the feature-name-only scope, the worked construction also substitutes a generic target question and recodes category words; the two prompt forms are not held constant. The published mapping for both unnamed variants is incomplete, so do not claim every dataset has the same additional changes.',
         'Unclear','Corrected factual v1.1 records a common LM framework but unresolved target/category representation and variant mapping. Shared text I/O does not establish comparable access to protected representations or interactions.',
         ['Same LM text framework.','Target/category rendering changes in the example; complete maps for both variants absent.','Common fitting recipe is described, but effective prompt opportunities are incompletely specified.','Scaffolding and target/value interactions can change beyond name semantics.'])

code('C03-A','shuffle','Yes','No','Fail',
     'A fixed permutation continues to present meaningful column names; it does not withdraw the name-use channel.',
     'Pass','The definition changes names by a shared permutation while retaining the List Template and values. The scope is the published permutation, not a claim that all fields are deranged.',
     'Pass','The same list slots, values, task prompt and T0 prediction/training scheme remain available. No new representation adapter or pathway is required; documentary comparability follows from the specified permutation.',
     ['Same list-to-T0 pathway.','Values and list slots remain; name assignment changes.','Shared T0/tuning/evaluation procedure.','Same name/value interaction form, with changed content.'])
code('C03-B','removal; compound','No','Yes','Pass',
     'List Only Values omits column names rather than retaining wrong semantic names.',
     'Fail','The declared scope protects List Template field scaffolding. Values-only serialization removes that scaffolding along with names, so ordered raw values alone do not satisfy this protection. This is an auditor-declared format-conditional estimand.',
     'Pass','Both conditions explicitly serialize values to the same LM with the same target procedure. Altered text scaffolding is a documented Preservation issue, not evidence of an unavailable model path or an unintended parse/shape failure. This Pass is limited to the described end-to-end LM contract.',
     ['Same text-to-T0 predictor.','Ordered values remain; explicit field scaffolding is removed.','Shared LM/tuning opportunity, no alternate learner specified.','The same LM can process both strings; extra scaffold changes are recorded under Preservation.'])
code('C03-C','shuffle; corruption; compound','Yes','No','Fail',
     'Values are assigned changed meanings; the value-content channel remains in use.',
     'Fail','The continuous-value variant first introduces ten uniform bins, changing protected numerical resolution as well as the value mapping. A categorical-only invertible subcontrast is not substituted for the frozen mixed comparison.',
     'Pass','Binned/permuted tokens remain within the defined list serialization and the same T0/task framework. The known resolution change is an information-preservation failure, not evidence that this described predictive interface is invalid.',
     ['Same list-to-LM path.','Continuous resolution is reduced; value tokens remain.','Same reported task/tuning recipe.','Same predictive processing; input-resolution change is explicit.'])

code('C04-A','removal','No','Yes','Unclear',
     'Broader-domain nodes leave the induced graph, but PLATO also uses pretrained KG embeddings. The ablation does not establish whether broader-domain information persists in those embeddings.',
     'Unclear','Feature nodes remain, but retained versus recomputed embeddings and their non-tested information are unspecified. Removing the tested nodes itself is allowed; the unresolved embedding construction is the issue.',
     'Unclear','The weight-inference pathway is described, but embedding provenance and retraining determine the representations and opportunities available to that pathway. The published ablation does not settle them.',
     ['PLATO weight-inference family retained.','Broader nodes removed; feature-embedding provenance unresolved.','Recomputation/retraining of KG embeddings not specified for this contrast.','Neighborhoods intentionally change; availability of broader pretrained content is unclear.'])
code('C04-B','removal; compound','No','Yes','Pass',
     'The paper explicitly states that No KG has no auxiliary KG access and becomes a standard MLP.',
     'Fail','Standard-MLP fitting replaces the protected KG-enabled first-layer weight-generation mechanism. Removing semantic input therefore accompanies a predictive-setup change.',
     'Unclear','Both accept tabular inputs and predict the same target, but their first-layer learning pathways and opportunities differ. The paper does not establish a matched opportunity/interaction contract for the declared component-specific comparison; architecture change alone is not labelled an interface failure.',
     ['KG-to-weight inference becomes direct MLP fitting.','Raw tabular observations remain; KG-derived feature-weight representation is absent.','First-layer fitting mechanism changes; matched capacity/opportunity not established.','Interactions can differ with the model change; comparability is unresolved.'])
code('C04-C','removal','No','Yes','Fail',
     'The tested scope is all supplied KG relational information; the comparator retains half the edges. Missing edges alone do not form a false-fact control.',
     'Unclear','The feature inputs and model family remain, but the embedding-retention/recomputation policy accompanying random deletion is not given.',
     'Unclear','Sparse graph processing is intentional, not a demonstrated failure. However, residual embedding information and its training opportunity are not documented enough to certify substantive interface comparability.',
     ['Same graph-prediction family with fewer edges.','Half the edges remain; embedding information is uncertain.','Embedding refresh/retraining after deletion unspecified.','Graph neighborhoods change intentionally; interaction with retained embeddings unresolved.'])

code('C05-A','replacement; compound','No','Yes','Pass',
     'MinHash substitutes for the declared language-semantic initialization channel. This Pass does not mean all knowledge in CARTE pretraining is erased.',
     'Fail','The entire string encoder and its representational geometry change, outside the scope of semantic content under a protected encoder/predictor setup.',
     'Unclear','C.3 does not specify encoder dimensions, numerical routing, initialization adaptation or matched pretraining compatibility. Intentional replacement is not evidence of a shape/routing failure; the details required to assess comparability are missing.',
     ['String initialization replaced before the graph predictor.','MinHash representation substituted; numerical/edge handling not fully specified.','Checkpoint/init/adaptation matching across encoders not supplied.','Input geometry changes; downstream compatibility cannot be certified.'])
code('C05-B','removal','No','Yes','Unclear',
     'The Exclude Edge Info. label does not establish removal from numerical-node initialization, which also uses column embeddings in the main architecture.',
     'Unclear','Zeroing/replacing edge information versus deleting its computation is not specified; protected value-bearing node information may be affected differently.',
     'Unclear','The label does not define the resulting edge/node routes, representation availability or training adaptation. The existence of a published curve is not a validity check.',
     ['Edge-removal operation not specified beyond label.','Potential column-conditioned numerical-node route unresolved.','Pretraining/adaptation after the change not detailed.','Neutralized vectors versus removed edge computation offer different interactions.'])
code('C05-C','removal; compound','No','Yes','Unclear',
     'Edge information is nominally removed, but the retained numerical-node path is not described well enough to exclude residual column semantics.',
     'Fail','The named condition also removes an attention layer, changing the protected predictive architecture.',
     'Unclear','Attention removal is documented, but the replacement computation and value/edge routing are not. This establishes a model change, not an unintended interface failure; meaningful comparability remains underspecified.',
     ['Attention layer and edge channel removed; replacement computation unclear.','Numerical-node/edge representation retention unspecified.','Matched adaptation opportunity not established.','Attention-mediated interactions change; replacement interactions not described.'])

code('C06-A','removal','No','Yes','Pass',
     'The tested scope is the entire supplied feature-description block: definitions, types and category information. -Description removes that block, not the LM’s latent knowledge.',
     'Pass','Under this package scope, its type/category contents are tested rather than protected. The paper describes a single-component omission with the remaining generation/parser/ensemble/tuning recipe common. Resulting rule and feature changes are mediators. A prose-only scope protecting type/category metadata would instead fail Preservation.',
     'Unclear','The full prompt uses types to generate parseable rules; the exact ablated prompt and its type/error handling are not given. Comparable parser access, usable feature availability and training opportunity are therefore not established merely by sharing the pipeline name.',
     ['Generate/parse/binary-feature pipeline named in both arms.','Type/category block removed; feature availability after parsing not documented per arm.','Same nominal recipe; effective opportunity after generation/parse errors unspecified.','Generated rules may legitimately change; comparability of valid rule interactions remains uncertain.'])

code('C07-A','replacement','No','Yes','Pass',
     'F.2 replaces informative feature headers by indexed names and the target header by Y, withdrawing the joint header-content use declared in the scope.',
     'Pass','F.2 explicitly leaves data unchanged and evaluates TABULA-8B with replaced headers. Both header classes are tested; target-header semantics are not silently treated as protected in this joint scope.',
     'Pass','Replacement strings occupy the same table-header pathway with the same model and evaluation procedure. Values and field identities remain available; the construction states no different training or predictive mechanism. This is a documentary comparison, not a rerun.',
     ['Same tabular-LM header/value pathway.','Values and stable header positions retained.','Same TABULA-8B evaluation opportunity.','Same model interactions with neutralized header content.'])

for id,encoder in [('C08-A','ordinal'),('C08-B','MinHash'),('C08-C','AutoGluon'),('C08-D','Gap')]:
    code(id,'replacement; compound','No','Yes','Pass',
         '§5.1 replaces the LLM-based categorical/string semantic-embedding channel by the named '+encoder+' encoding. Removal is scoped to that channel; neither all column semantics nor all pretrained model knowledge is claimed absent.',
         'Fail','The named encoder family/representation changes rather than only its semantic content. That violates the protected encoder/representation setup for this scoped claim.',
         'Unclear','The paper describes an intentional '+encoder+' replacement but does not fully specify per-encoder dimensions, normalization, initialization or training adaptation. No demonstrated unintended violation warrants Fail; pathway and opportunity compatibility remain unresolved.',
         ['Cell-feature encoder replaced; base learner remains the named family.','Different representation supplied; dimensional/normalization compatibility unspecified.','Per-encoder initialization and adaptation details not established.','The learner receives a different feature basis; matched predictive interactions not documented.'])
code('C08-E','replacement','No','Yes','Pass',
     '§5.1 explicitly replaces column names with col1,...,colN, removing supplied name content without deleting columns.',
     'Pass','The defined change retains cell encodings, field slots and the shared semantic-ablation base model while replacing only header strings. This protects values and non-tested pathways at the documentary level.',
     'Pass','Generic strings are processed by the same header encoder alongside the same cell pathway. No alternate encoder, learner or adaptation regime is introduced by the stated name-only construction.',
     ['Same column-name and cell-encoding routes.','Indexed headers retain slots; cell values remain.','Common base-model semantic-ablation procedure.','Same header/cell interaction form with different header content.'])
code('C08-F','removal','No','Yes','Pass',
     'Original names alone omit the additional generated descriptions present in the enriched intended arm.',
     'Unclear','The descriptions use five sampled rows; §5.1 does not establish the permitted split/target access for that generation. The declared protection includes equal allowed information access, so this unresolved point matters.',
     'Unclear','Both strings use the same encoder route, but the generator creates an additional route from sampled rows to the predictor. Without its access policy, representation availability and training/evaluation opportunity are not confirmed comparable.',
     ['Same name encoder, plus description generation for intended arm.','Generated text may carry information from sampled rows; source split unclear.','Permitted row/target access for generation unspecified.','Additional contextual interactions are intended; allowable information feeding them is unclear.'])

for id,part in [('C09-A','quantile wording'),('C09-B','bin/quantile numeric wording')]:
    code(id,'removal' if id=='C09-A' else 'removal; replacement','No','Yes','Pass',
         'Q3 defines a variant omitting '+part+' from verbalization. The scope is explicit textual supply, not absence of numerical information from the separate numerical branch or inability to reconstruct it.',
         'Pass','The variant changes verbalization within the documented dual-path architecture; numerical observations, field identity and the separate numeric branch remain in the described recipe. No different architecture is specified. This is not an assertion of byte-identical fitted weights.',
         'Pass','Both arms keep the numerical/semantic fusion and prediction architecture, with a valid text element in the thinner variant. The shared training recipe allows the same pathways and opportunities while the declared wording changes.',
         ['Dual numerical/semantic paths and fusion retained by the verbalization-only design.','Numerical branch and non-tested text remain; tested wording omitted.','Common model and training recipe as described; no per-arm rerun claimed.','Fusion/interaction mechanism retained; explicit semantic input differs.'])

code('C10-A','removal','No','Yes','Unclear',
     'The published Figure 6 label establishes nominal column-information removal but not whether names, embeddings or a branch are removed. Residual column-conditioned numerical initialization is unresolved.',
     'Unclear','The labels share Enriched YAGO4.5, but exact checkpoint matching and preservation of value-bearing numerical routes are not established by the published extract.',
     'Unclear','The exact operation and downstream value routing cannot be certified from the figure label. The supplied preacceptance PDF is not accepted-version evidence for filling those gaps.',
     ['Exact name-removal pathway unspecified in published evidence.','Numerical/cell representation retention unresolved.','Common pretraining label, not proof of checkpoint/adaptation equality.','Column/value interactions after removal unspecified.'])
code('C10-B','replacement; compound','No','Yes','Pass',
     'The published caption specifies replacing FastText with MinHash; the declared FastText initialization use is absent in that comparator.',
     'Fail','The figure-baseline comparison also changes table-model pretraining from Enriched YAGO4.5 to Random weights, as well as encoder family. Both are protected for FastText-content attribution. A nonbaseline matched-random-weights pair is not substituted.',
     'Unclear','Different pretraining opportunities are documented, and the vector/numerical adaptation is unspecified. Those differences rule out a Preservation Pass but do not by themselves demonstrate a broken interface; compatible routes/interactions are not established.',
     ['String encoder changes.','MinHash representation and numerical adaptation unspecified.','Pretrained baseline versus random-weight table model is an explicit opportunity difference.','Comparable downstream representation interactions not established.'])

def main():
    assert set(codes)==set(C)==set(S) and len(codes)==25
    out=[]
    for id in C:
        r={**S[id],'Intended arm':C[id]['Intended arm'],'Comparator arm':C[id]['Comparator arm'],**codes[id]}
        g=[r[k]['value'] for k in ['Removal','Preservation','Interface']]
        adm='No' if 'Fail' in g else 'Yes' if all(v=='Pass' for v in g) else 'Unclear'
        cs=('Yes' if g[1:]==['Pass','Pass'] else 'Partial') if r['Wrong-like']['value']=='Yes' else 'No'
        r['Admissible reference']={'value':adm,'evidence':'Derived from this row’s three evidenced gates under CONTROL_CODING_RULE_V1.md','rationale':'All Pass -> Yes; any Fail -> No; otherwise Unclear.'}
        r['Content sensitivity identifiable']={'value':cs,'evidence':'This row’s wrong-like construction, Preservation and Interface evidence','rationale':'Uses the manuscript intended–wrong definition; removal-only comparison is not that contrast.'}
        r['Predictive utility identifiable']={'value':{'Yes':'Yes','No':'No','Unclear':'Partial'}[adm],'evidence':'This row’s evidenced admissibility determination','rationale':'Partial denotes unresolved identification, not a partially positive result.'}
        out.append(r)
    (P/'CLAIM_IDENTIFICATION_V1.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    def cell(x):
        return x['value']+' — '+x['evidence']+': '+x['rationale']
    flat=[]
    for r in out:
        f={k:r[k] for k in ['Comparison ID','Study','Tested semantic use','Protected observations','Protected metadata','Protected representation','Protected predictive setup','Intended arm','Comparator arm','Intervention type']}
        for k in ['Wrong-like','Removal-like','Removal','Preservation','Interface','Admissible reference','Content sensitivity identifiable','Predictive utility identifiable']: f[k]=cell(r[k])
        f['Interface dimensions']='; '.join(k+': '+v['observation']+' ['+v['evidence']+']' for k,v in r['Interface dimensions'].items())
        flat.append(f)
    with (P/'CLAIM_IDENTIFICATION_V1.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
    lines=['# Claim-identification coding v1','',
           '9 fixed studies; 25 comparisons. All judgments are relative to the scope fixed before coding. No reported outcomes or empirical supported claims are included.',
           '', '**Reported outcomes were not extracted or used in assigning the design codes.** Prior exposure and the earlier nonbinding draft are disclosed; this is not a blinded audit.',
           '', 'Each gate cell below includes its source location and reason. Evidence refers to archived official PDFs unless a published-indexed-source caveat is explicitly stated. See SOURCE_LINKS_V1.md for clickable source files.',
           '', 'Pass is a documentary design judgment; Unclear is not Fail. Changed encoder/architecture is not automatically Interface Fail. Derived identifiability is a capability of the design, not an observed benefit.']
    for r in out:
        lines+=['','## '+r['Comparison ID']+' — '+r['Study'],'']
        for k in ['Tested semantic use','Protected observations','Protected metadata','Protected representation','Protected predictive setup','Intended arm','Comparator arm','Intervention type']:
            lines+=['**'+k+':** '+r[k],'']
        lines+=['| Axis | Evidence-backed judgment |','|---|---|']
        for k in ['Wrong-like','Removal-like','Removal','Preservation','Interface','Admissible reference','Content sensitivity identifiable','Predictive utility identifiable']:
            lines+=['| '+k+' | '+cell(r[k]).replace('|',' / ')+' |']
        lines+=['','**Substantive interface checks:**','']
        for k,v in r['Interface dimensions'].items(): lines+=['- '+k+': '+v['observation']+' Evidence: '+v['evidence']]
    (P/'CLAIM_IDENTIFICATION_V1.md').write_text('\n'.join(lines)+'\n')
    print('25 comparisons coded with 75 individually evidenced gate cells.')

if __name__=='__main__':main()
