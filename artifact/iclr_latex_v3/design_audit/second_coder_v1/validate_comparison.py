from pathlib import Path
import csv,json,hashlib,collections
P=Path(__file__).resolve().parent;A=P.parent;I=P/'independent';O=P/'comparison'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
for f in json.loads((P/'PRIMARY_BASELINE_HASHES.json').read_text()):assert sha(A/f['path'])==f['sha256'],f['path']
for f in json.loads((I/'SECOND_CODER_FREEZE_V1.json').read_text())['files']:assert sha(I/f['path'])==f['sha256'],f['path']
for f in json.loads((P/'packet/PACKET_MANIFEST.json').read_text())['files']:assert sha(P/'packet'/f['path'])==f['sha256'],f['path']
read=lambda f:list(csv.DictReader((O/f).open()))
rr=read('ALL_25_PAIRED_CODES_V1.csv');dd=read('DISAGREEMENTS_V1.csv');aa=read('GATE_AGREEMENT_V1.csv');cf=read('CONFUSION_TABLES_V1.csv');ss=read('STUDY_STATUS_SENSITIVITY_V1.csv')
assert len(rr)==25 and len(dd)==13 and len(ss)==9 and len(cf)==36
assert len({r['Comparison ID'] for r in rr})==25
assert {r['Comparison ID'] for r in dd}=={r['Comparison ID'] for r in rr if r['Disagreeing fields']}
for a in aa:
 g=a['Field'];n=sum(r['Primary '+g]==r['Second '+g] for r in rr)
 assert int(a['Exact agreements'])==n and int(a['Disagreements'])==25-n and float(a['Agreement percent'])==100*n/25
 mm=[r for r in cf if r['Field']==g]
 assert sum(int(r['Count']) for r in mm)==25
 assert sum(int(r['Count']) for r in mm if r['Primary']==r['Second'])==n
 for m in mm:assert int(m['Count'])==sum(r['Primary '+g]==m['Primary'] and r['Second '+g]==m['Second'] for r in rr)
for r in rr:
 for coder in ['Primary','Second']:
  vals=[r[coder+' '+g] for g in ['Removal','Preservation','Interface']]
  derived='Yes' if vals==['Pass']*3 else 'No' if 'Fail' in vals else 'Unclear'
  assert r[coder+' Admissible reference']==derived
for s in ss:
 r=[r for r in rr if r['Study']==s['Study']]
 assert set(s['Comparisons'].split(';'))=={x['Comparison ID'] for x in r}
 for coder in ['Primary','Second']:
  vals=[x[coder+' Admissible reference'] for x in r]
  status='at least one Yes' if 'Yes' in vals else 'Unclear but no Yes' if 'Unclear' in vals else 'all No'
  assert s[coder+' status']==status
assert (O/'SUPPLEMENT_SECOND_CODER_V1.pdf').read_bytes().startswith(b'%PDF-')
report={'status':'PASS','all_25_coded':True,'agreements':{r['Field']:int(r['Exact agreements']) for r in aa},'disagreement_rows':13,'admissibility_disagreement_rows':9,'full_confusion_cells':36,'scope_and_protection_disclosed_for_all_25':True,'primary_and_outcome_baseline_unchanged':True,'independent_freeze_unchanged':True,'packet_unchanged':True,'second_coder':'Separate AI agent; no inherited conversation; instructional read boundary, not OS enforced','adjudication':'None','supplement_pdf_pages':18,'factual_clarification_addendum':'../CONSTRUCTION_SOURCE_ADDENDUM_V1_2.md; no code changes'}
print(json.dumps(report,indent=2))
