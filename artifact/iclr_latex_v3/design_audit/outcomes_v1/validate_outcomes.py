from pathlib import Path
from decimal import Decimal
import csv,json,hashlib,collections,re
P=Path(__file__).resolve().parent;A=P.parent
read=lambda f:list(csv.DictReader((P/f).open()))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
codes=json.loads((A/'phase_c_v1/CLAIM_IDENTIFICATION_V1.json').read_text()); C={c['Comparison ID']:c for c in codes}
# All authoritative parent files and original PDFs are unchanged.
for f in json.loads((A/'phase_c_v1/DESIGN_CODE_FREEZE_V1.json').read_text())['files']:
    assert sha(A/f['path'])==f['sha256'],f['path']
for f in json.loads((A/'design_v1/CONSTRUCTION_SOURCE_MANIFEST_V1.json').read_text())['files']:
    assert sha(Path(f['path']))==f['sha256'],f['path']
assert sha(A/'OUTCOME_EXTRACTION_RULE_V1.md')==(A/'OUTCOME_EXTRACTION_RULE_V1.sha256').read_text().split()[0]
R=read('REPORTED_OUTCOMES_V1.csv');J=read('SUPPORTED_CLAIMS_V1.csv');S=read('COMPARISON_SUMMARY_V1.csv');T=read('STUDY_SUMMARY_V1.csv')
assert len(R)==len(J)==559 and len(S)==25 and len(T)==9
assert {r['Comparison ID'] for r in R}==set(C)
assert len({r['Outcome ID'] for r in R})==len(R)
expected={'LIFT':72,'TabLLM':297,'PLATO':4,'CARTE':9,'FeatLLM':71,'TabuLa-8B':4,'ConTextTab':54,'TabSTAR':46,'TARTE':2}
assert dict(collections.Counter(r['Study'] for r in R))==expected
assert json.loads((P/'REPORTED_OUTCOMES_V1.json').read_text())==R
for r,j in zip(R,J):
    c=C[r['Comparison ID']]
    assert r['Outcome ID']==j['Outcome ID']
    assert r['Study']==c['Study'] and r['Intended arm']==c['Intended arm'] and r['Comparator arm']==c['Comparator arm']
    for k in ['Admissible reference','Content sensitivity identifiable','Predictive utility identifiable']:assert j[k]==c[k]['value']
    for k in ['Dataset-task','Budget-regime','Metric','Evidence','Reported significance','Uncertainty type']: assert r[k],(r['Outcome ID'],k)
    if r['Intended value'] and r['Comparator value']:
        d=(Decimal(r['Intended value'])-Decimal(r['Comparator value']))*(1 if r['Orientation']=='higher' else -1)
        assert r['Direction']==('favorable' if d>0 else 'adverse' if d<0 else 'equal_at_printed_precision')
    if r['Source type'] in ['figure','missing_table_cell','not_applicable']:assert r['Direction']=='unavailable'
    if r['Source type']=='figure': assert not r['Intended value'] and not r['Comparator value']
    if j['Supported utility claim'].startswith('Positive predictive utility'):
        assert j['Predictive utility identifiable']=='Yes' and r['Match status']=='matched' and r['Direction'] in ['favorable','author_reported_favorable']
    if r['Contrast uncertainty']:assert not r['Intended uncertainty'] and not r['Comparator uncertainty']
# Granularity: no selective dataset/shot extraction; missing cells survive.
rr=[r for r in R if r['Comparison ID']=='C06-A' and r['Summary stratum']=='primary']
assert len({r['Dataset-task'] for r in rr})==13
for data in {r['Dataset-task'] for r in rr}:assert {r['Budget-regime'] for r in rr if r['Dataset-task']==data}=={'4','8','16','32','64'}
for cid in ['C03-A','C03-B','C03-C']:
    rr=[r for r in R if r['Comparison ID']==cid and re.search('Table 1[234];',r['Evidence'])]
    assert len(rr)==90 and len({r['Dataset-task'] for r in rr})==9
    assert sum(r['Source type']=='missing_table_cell' for r in rr)==6
for cid in ['C09-A','C09-B']:
    rr=[r for r in R if r['Comparison ID']==cid and r['Summary stratum']=='primary']
    assert len(rr)==20 and sum(r['Dataset-task'].startswith('C') for r in rr)==8
# Verify all numeric pairs in manual LIFT Table 9 / 34 transcription occur on their own source row.
for f,table in [('C01_main','Table 9'),('C01_supp','Table 34')]:
    text=(A/'sources'/f'{f}.txt').read_text()
    for r in R:
        if r['Study']!='LIFT' or table not in r['Evidence'] or r['Source type']!='table':continue
        data=r['Dataset-task'];label=data.replace('CMC (23)','CMC (23)').replace('Vehicle (54)','Vehicle (54)')
        candidates=[re.sub(r'\s+','',l) for l in text.splitlines() if label in l]
        a=r['Intended value']+'±'+r['Intended uncertainty'];b=r['Comparator value']+'±'+r['Comparator uncertainty']
        assert any(a in l and b in l for l in candidates),(r['Outcome ID'],a,b)
# Known polarity and precision checks (catch swapped intended/reference and missing SD parsing).
def find(cid,data,budget):return next(r for r in R if r['Comparison ID']==cid and r['Dataset-task']==data and r['Budget-regime']==budget)
r=find('C03-A','Bank','0');assert (r['Intended value'],r['Comparator value'],r['Intended uncertainty'],r['Direction'])==('0.60','0.64','0.01','adverse')
r=find('C03-A','Surgical Procedure (Surgery)','16384');assert r['Comparator value']=='' and r['Intended value']=='0.79'
r=find('C09-A','R27','Q3: up to 10K examples; Appendix G.4');assert (r['Intended value'],r['Comparator value'],r['Direction'])==('81.3','82.0','adverse')
assert sum(r['Match status']=='ambiguous' for r in R)==30
assert sum(r['Source type']=='not_applicable' for r in R)==24
# All comparison outcomes accounted for by summaries; summaries retain complete study lists.
for s in S:
    rr=[r for r in R if r['Comparison ID']==s['Comparison ID']]
    assert s['All outcome IDs'].split(';')==[r['Outcome ID'] for r in rr]
    assert int(s['Total extracted rows'])==len(rr)
for t in T:assert t['All comparisons'].split(';')==[c['Comparison ID'] for c in codes if c['Study']==t['Study']]
report={'status':'PASS','studies':len(T),'comparisons':len(S),'outcome_records':len(R),'joined_claim_records':len(J),'by_study':expected,'by_source_type':dict(collections.Counter(r['Source type'] for r in R)),'by_summary_stratum':dict(collections.Counter(r['Summary stratum'] for r in R)),'ambiguous_records':30,'parent_freezes_unchanged':True,'source_pdf_hashes_unchanged':True,'review':'Single-auditor source review plus automated integrity, coverage and polarity checks; no independent double coding.'}
print(json.dumps(report,indent=2))
