from pathlib import Path
import csv
import json

P=Path(__file__).resolve().parent
A=P.parent
codes=json.loads((P/'CLAIM_IDENTIFICATION_V1.json').read_text())
facts={r['Comparison ID']:r for r in json.loads((A/'design_v1_1/CONTROL_CONSTRUCTION_V1_1.json').read_text())}
scopes={r['Comparison ID']:r for r in json.loads((P/'CLAIM_SCOPES_V1.json').read_text())}
assert len(codes)==len(facts)==len(scopes)==25
assert len({r['Study'] for r in codes})==9
assert {r['Comparison ID'] for r in codes}==set(facts)==set(scopes)
assert 'C06-B' not in facts
with (P/'CLAIM_IDENTIFICATION_V1.csv').open() as f:
    flat=list(csv.DictReader(f))
md=(P/'CLAIM_IDENTIFICATION_V1.md').read_text()
assert len(flat)==25
count=0
for r,f in zip(codes,flat):
    id=r['Comparison ID']
    assert id==f['Comparison ID']
    for k,v in scopes[id].items(): assert r[k]==v
    for k in ['Intended arm','Comparator arm']: assert r[k]==facts[id][k]
    for k in ['Removal','Preservation','Interface']:
        x=r[k]
        assert x['value'] in ['Pass','Fail','Unclear']
        assert x['evidence']==facts[id]['Evidence'] and len(x['rationale'])>30
        c=x['value']+' — '+x['evidence']+': '+x['rationale']
        assert f[k]==c and c.replace('|',' / ') in md
        count+=1
    for k in ['Wrong-like','Removal-like']:
        assert r[k]['value'] in ['Yes','No','Unclear'] and r[k]['evidence'] and r[k]['rationale']
    assert set(r['Interface dimensions'])=={'Model pathway','Representation availability','Training opportunity','Predictive interaction'}
    for x in r['Interface dimensions'].values(): assert x['observation'] and x['evidence']==facts[id]['Evidence']
    vals=[r[k]['value'] for k in ['Removal','Preservation','Interface']]
    expected='No' if 'Fail' in vals else 'Yes' if vals==['Pass']*3 else 'Unclear'
    assert r['Admissible reference']['value']==expected
    assert r['Predictive utility identifiable']['value']=={'Yes':'Yes','No':'No','Unclear':'Partial'}[expected]
    content=('Yes' if vals[1:]==['Pass','Pass'] else 'Partial') if r['Wrong-like']['value']=='Yes' else 'No'
    assert r['Content sensitivity identifiable']['value']==content
    assert '## '+id+' — '+r['Study'] in md
assert count==75
print('PASS: 25 comparisons / 9 studies; 75 evidence-backed gates; 100 sourced interface checks; scope, CSV/JSON/Markdown and derivation consistency.')
