import json, hashlib
from pathlib import Path
root=Path('./iclr_latex_v3/design_audit/second_coder_v1')
rows=json.loads((root/'packet/CONTROL_CONSTRUCTION_V1_1.json').read_text())
# Deliberately contains scope declarations only; gate assignment is a later operation.
scopes=[]
for r in rows:
 i=r['Comparison ID']; study=r['Study']
 obs='All observed feature values and target labels, row/sample identities, feature cardinality and missingness; reversible fixed recoding is permitted.'
 meta='Feature identity/position, type and category-domain information, and target/task identity, except the explicitly tested semantic channel.'
 rep='A stable field/value association and distinct feature slots; numerical and missing-value information remain representable. Exact semantic token strings or semantic embedding coordinates are not protected.'
 setup='Same data/split/shot regime, learner and fitting recipe outside the tested channel; ordinary fitted-state changes caused by the intervention are permitted.'
 if study=='LIFT':
  use='Feature-name meanings in the name/value associations of prompt format '+('I' if i in ['C01-A','C01-C'] else 'II')+'.'
  if i in ['C01-C','C01-D']:use='Named feature and task context in prompt format '+('I' if i=='C01-C' else 'II')+', including informative target question; categorical observation identities remain protected even if recoded.'
  rep+=' Retain the within-format presentation scaffold and output-label mapping outside removed names/context.'
 if study=='TabLLM':
  use={'C03-A':'Column-name meanings as supplied in the list name/value associations.','C03-B':'Column-name text as semantic annotation of a fixed ordered value list.','C03-C':'Semantic meanings of supplied feature-value tokens, including continuous-value magnitude.'}[i]
  rep='Ordered feature-value slots, value boundaries and task prompt/verbalizer; field-name text may be absent when that is the tested channel. For value permutations, continuous precision is protected as observation information.'
 if study=='PLATO':
  use={'C04-A':'Broader-domain KG information conveyed by non-feature nodes, including through pretrained embeddings and message passing. Feature-node information is protected.','C04-B':'Auxiliary KG information used for feature embeddings and first-layer weight inference.','C04-C':'KG edge information as a whole, including its encoding in pretrained node embeddings and message passing; a 50% deletion is a partial intervention on this use.'}[i]
  rep='Feature-node correspondence and the PLATO first-layer weight-inference scaffold, MLP downstream layers, observed-feature routing; changing KG neighborhoods is intrinsic to the intervention. Semantic embedding coordinates may change under the same recipe.'
 if study=='CARTE':
  use='External pretrained linguistic meaning in string feature initialization.' if i=='C05-A' else 'Column-name semantic information in CARTE, including edge encodings and any propagation through numerical-node initialization.'
  rep='Graphlet feature slots, numeric-value and missing-value representation, central readout and attention scaffold; encoder coordinates may change but nonsemantic identity/routing must survive.'
 if study=='FeatLLM':
  use='Explanatory semantic definitions in the feature-description block used to generate rules.'
  meta='Feature identity, explicit value types, categorical domains/examples and task/answer-class definition; these structural facts are protected separately from explanatory meaning.'
  rep='Generate/parse/binary-feature interface and parser rules; newly generated rules and binary features are allowed consequences.'
 if study=='TabuLa-8B':use='Informative feature headers and informative target header jointly, as opposed to indexed headers.'
 if study=='ConTextTab':
  use='Pretrained linguistic meaning in categorical/string cell encodings; column-header semantic meaning remains protected.'
  rep='Distinct cell/column identity, numeric/date/missingness paths and the column-plus-cell backbone interface. A compatible change of cell encoder is allowed; loss of observational distinctions is not.'
  if i=='C08-E':use='Informative original column-header meanings; indexed header strings are a neutral replacement.'
  if i=='C08-F':
   use='Additional contextual descriptions appended to original column names, beyond the original name meaning.'
   setup+=' Description generation may transform available training observations but must not acquire additional held-out or target information relative to the comparator.'
 if study=='TabSTAR':
  use='Explicit quantile wording in numerical-feature verbalization.' if i=='C09-A' else 'Numeric bin/magnitude and quantile wording in the semantic verbalization branch only.'
  rep='Separate standardized numerical-input branch, feature name/slot and missing-value markers, text encoder and numerical/semantic fusion scaffold. Numerical facts remain allowed through the numeric branch.'
 if study=='TARTE':
  use='Column-name semantics across table-representation paths, including any numeric initialization use.' if i=='C10-A' else 'External linguistic meaning provided by the string encoder; table-level Enriched YAGO4.5 pretraining is protected as a distinct component.'
  rep='Feature slots, numeric/date/missingness handling and fixed representation-to-Ridge interface; compatible string-encoder replacement is allowed.'
  setup+=' Table-model pretraining regime and downstream Ridge fitting recipe are protected independently of the tested channel.'
 scopes.append({'Comparison ID':i,'Study':study,'Tested semantic use':use,'Protected observations':obs,'Protected metadata':meta,'Protected representation':rep,'Protected predictive setup':setup,'Scope evidence':r['Evidence']})
p=root/'independent/SCOPES_SECOND_V1.json';p.write_text(json.dumps(scopes,ensure_ascii=False,indent=2)+'\n')
h=hashlib.sha256(p.read_bytes()).hexdigest();(p.parent/'SCOPES_SECOND_V1.sha256').write_text(h+'  '+p.name+'\n')
print('Frozen scope rows:',len(scopes),'SHA256:',h)
