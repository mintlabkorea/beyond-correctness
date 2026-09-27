"""Post-freeze comparison only. Never edits primary or independent coding files."""
from pathlib import Path
import csv,json,hashlib,collections
P=Path(__file__).resolve().parent;A=P.parent;I=P/'independent';O=P/'comparison';O.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert (I/'SECOND_CODER_FREEZE_V1.json').exists(),'Second coding must be frozen before comparison'
for f in json.loads((P/'PRIMARY_BASELINE_HASHES.json').read_text()):assert sha(A/f['path'])==f['sha256'],f['path']
for f in json.loads((P/'packet/PACKET_MANIFEST.json').read_text())['files']:assert sha(P/'packet'/f['path'])==f['sha256'],f['path']
primary=json.loads((A/'phase_c_v1/CLAIM_IDENTIFICATION_V1.json').read_text());second=json.loads((I/'CODES_SECOND_V1.json').read_text())
if isinstance(second,dict):second=second.get('comparisons',second.get('rows',second.get('codes')))
C={r['Comparison ID']:r for r in primary};D={r['Comparison ID']:r for r in second}
assert len(C)==len(D)==25 and set(C)==set(D)
G=['Removal','Preservation','Interface','Admissible reference']
S=['Tested semantic use','Protected observations','Protected metadata','Protected representation','Protected predictive setup']
def val(r,g):return r[g]['value']
def adm(r):
    a=[val(r,g) for g in G[:3]]
    return 'Yes' if all(v=='Pass' for v in a) else 'No' if 'Fail' in a else 'Unclear'
def csvwrite(name,rows):
    with (O/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
for cid in C:
    assert C[cid]['Study']==D[cid]['Study']
    for r in [C[cid],D[cid]]:
        assert adm(r)==val(r,'Admissible reference')
        for g in G[:3]:
            assert val(r,g) in ['Pass','Fail','Unclear']
            assert r[g]['evidence'] and r[g]['rationale']
        for s in S:assert r[s]
agreement=[];confusion=[]
for g in G:
    n=sum(val(C[c],g)==val(D[c],g) for c in C)
    cats=['Yes','No','Unclear'] if g=='Admissible reference' else ['Pass','Fail','Unclear']
    agreement.append({'Field':g,'Exact agreements':n,'Total':25,'Agreement percent':f'{100*n/25:.1f}','Disagreements':25-n,'Primary counts':json.dumps(dict(collections.Counter(val(r,g) for r in C.values()))),'Second counts':json.dumps(dict(collections.Counter(val(r,g) for r in D.values())))})
    for a in cats:
        for b in cats:confusion.append({'Field':g,'Primary':a,'Second':b,'Count':sum(val(C[c],g)==a and val(D[c],g)==b for c in C)})
csvwrite('GATE_AGREEMENT_V1.csv',agreement);csvwrite('CONFUSION_TABLES_V1.csv',confusion)
paired=[];disagreements=[]
for cid,c in C.items():
    d=D[cid];r={'Comparison ID':cid,'Study':c['Study'],'Disagreeing fields':'; '.join(g for g in G if val(c,g)!=val(d,g))}
    for s in S:
        r['Primary '+s]=c[s];r['Second '+s]=d[s]
    for g in G:
        r['Primary '+g]=val(c,g);r['Second '+g]=val(d,g)
        r['Primary '+g+' evidence']=c[g].get('evidence',c['Scope evidence'])
        r['Second '+g+' evidence']=d[g].get('evidence',d['Scope evidence'])
        r['Primary '+g+' rationale']=c[g]['rationale'];r['Second '+g+' rationale']=d[g]['rationale']
    paired.append(r)
    if r['Disagreeing fields']:disagreements.append(r)
csvwrite('ALL_25_PAIRED_CODES_V1.csv',paired)
with (O/'DISAGREEMENTS_V1.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(paired[0]));w.writeheader();w.writerows(disagreements)
# Study hierarchy includes unresolved references even where other comparisons are No.
def status(rows):
    vs=[val(r,'Admissible reference') for r in rows]
    return 'at least one Yes' if 'Yes' in vs else 'Unclear but no Yes' if 'Unclear' in vs else 'all No'
studies=[]
for study in dict.fromkeys(c['Study'] for c in primary):
    cc=[c for c in primary if c['Study']==study];dd=[D[c['Comparison ID']] for c in cc]
    r={'Study':study,'Comparisons':';'.join(c['Comparison ID'] for c in cc),'Primary status':status(cc),'Second status':status(dd)}
    r['Status changed']=str(r['Primary status']!=r['Second status'])
    for label,rr in [('Primary',cc),('Second',dd)]:
        for v in ['Yes','No','Unclear']:r[label+' '+v+' comparisons']=';'.join(c['Comparison ID'] for c in rr if val(c,'Admissible reference')==v)
    studies.append(r)
csvwrite('STUDY_STATUS_SENSITIVITY_V1.csv',studies)
headline={'primary':{'comparison_counts':dict(collections.Counter(val(r,'Admissible reference') for r in primary)),'study_counts':dict(collections.Counter(r['Primary status'] for r in studies))},'second':{'comparison_counts':dict(collections.Counter(val(r,'Admissible reference') for r in second)),'study_counts':dict(collections.Counter(r['Second status'] for r in studies))},'changed_comparisons':[c for c in C if val(C[c],'Admissible reference')!=val(D[c],'Admissible reference')],'changed_studies':[r['Study'] for r in studies if r['Status changed']=='True'],'rows_with_any_gate_or_admissibility_disagreement':len(disagreements),'primary_preserved':True,'adjudication':'None; retain primary v1','outcomes_used_in_comparison':False}
(O/'HEADLINE_SENSITIVITY_V1.json').write_text(json.dumps(headline,ensure_ascii=False,indent=2)+'\n')
# Full disclosure, including scope/protected set even for label-agreement rows.
lines=['# Second-coder comparison and disagreements v1','',
'A separate AI agent coded all 25 comparisons from the common rule, the factual sheet and source papers, with no inherited conversation. Primary scopes/codes and extracted outcomes were not supplied. The second scope sheet and codes were frozen before comparison. Primary v1 remains unchanged; no adjudication was performed.','',
'This is second-AI-coder reproducibility/sensitivity, not independent human validation. The model, common rules and primary factual-construction sheet are shared. The read boundary was instructional within a shared filesystem, not technically enforced. Published PDFs contain outcomes; no literal outcome blindness is claimed. Gate agreement measures label agreement under independently declared scopes, not proof of identical estimands.','',
'## Exact agreement','', '| Field | Agreement | Percent | Disagreements |','|---|---:|---:|---:|']
for r in agreement:lines.append(f"| {r['Field']} | {r['Exact agreements']}/25 | {r['Agreement percent']}% | {r['Disagreements']} |")
lines+=['','Rows share papers and arms. No independence-based confidence intervals, significance tests or kappa-only reliability claims are used.','', '## Headline sensitivity','', '| Study | Primary | Second | Changed? |','|---|---|---|---|']
for r in studies:lines.append(f"| {r['Study']} | {r['Primary status']} | {r['Second status']} | {r['Status changed']} |")
lines+=['', '```json',json.dumps(headline,ensure_ascii=False,indent=2),'```','',
'## Complete paired coding: all 25 comparisons','',
'Every pair includes independently declared scope and protection. Textual differences are disclosed without inventing a semantic-agreement percentage. Disagreement rationales below are each coder’s frozen explanations; they are not post-hoc adjudication.']
for cid,c in C.items():
    d=D[cid];gs=[g for g in G if val(c,g)!=val(d,g)]
    lines+=['',f"### {cid} — {c['Study']}",'', '**Disagreeing labels:** '+(', '.join(gs) if gs else 'None')+'.','']
    for label,r in [('Primary',c),('Second',d)]:
        lines+=['**'+label+' scope and protected set**','']
        for s in S:lines.append('- '+s+': '+r[s])
        lines+=['- Scope evidence: '+r['Scope evidence'],'']
    lines+=['| Gate | Primary | Second |','|---|---|---|']
    for g in G:lines.append(f'| {g} | {val(c,g)} | {val(d,g)} |')
    for g in gs:
        lines+=['',f'**{g} disagreement**','',f"Primary: {c[g]['rationale']} Evidence: {c[g].get('evidence',c['Scope evidence'])}",'',f"Second: {d[g]['rationale']} Evidence: {d[g].get('evidence',d['Scope evidence'])}"]
lines+=['','## Preserved artifacts and limitations','',
'Primary design codes remain the primary analysis. Secondary statuses are a sensitivity analysis with no outcome re-join. Suspected factual errors, if any, are listed in the independent coder’s review; disagreements alone do not authorize a correction. The original primary operational addendum was not supplied; the user-requested shared rule was CONTROL_CODING_RULE_V1. Operational interpretation differences as well as coder-declared protection can contribute to disagreement.','',
'CSV files provide full 3×3 confusion tables, every paired code/rationale, disagreements and study status transitions. Source access limitations and incidental exposure are documented in ../independent/REVIEW_SECOND_V1.md.']
(O/'SECOND_CODER_REPORT_V1.md').write_text('\n'.join(lines)+'\n')
# Standalone supplement-ready TeX contains all paired scopes and all disagreements.
def tex(s):
    s=str(s);mp={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
    s=''.join(mp.get(c,c) for c in s)
    for a,b in [('–','--'),('—','---'),('→',r'$\rightarrow$'),('≥',r'$\geq$'),('≤',r'$\leq$'),('×',r'$\times$'),('κ',r'$\kappa$'),('…','...'),('−','-'),('∼',r'$\sim$')]:s=s.replace(a,b)
    return s
x=[r'\documentclass[10pt]{article}',r'\usepackage[T1]{fontenc}',r'\usepackage[utf8]{inputenc}',r'\usepackage[margin=0.8in]{geometry}',r'\usepackage{booktabs,longtable}',r'\usepackage[hidelinks]{hyperref}',r'\usepackage{microtype}',r'\setlength{\emergencystretch}{3em}',r'\begin{document}',r'\section*{Second AI coder: agreement and scope sensitivity}',tex(lines[2]),r'\par\medskip',tex(lines[4]),r'\subsection*{Exact agreement}',r'\begin{tabular}{lrrr}\toprule Field & Agreement & Percent & Disagreements \\ \midrule']
for r in agreement:x.append(f"{tex(r['Field'])} & {r['Exact agreements']}/25 & {r['Agreement percent']}\\% & {r['Disagreements']}"+r' \\')
x+=[r'\bottomrule\end{tabular}',r'\subsection*{Study-level status sensitivity}',r'\begin{longtable}{p{.14\linewidth}p{.3\linewidth}p{.3\linewidth}l}\toprule Study & Primary & Second & Changed \\ \midrule\endhead']
for r in studies:x.append(' & '.join(tex(r[k]) for k in ['Study','Primary status','Second status','Status changed'])+r' \\')
x+=[r'\bottomrule\end{longtable}',tex('Admissibility (Yes / No / Unclear): primary 4 / 16 / 5; second 5 / 9 / 11. Studies with at least one admissible reference: primary 3/9; second 4/9. Counts are descriptive, not independent experiments. No adjudication. Preservation agrees on only 14/25 comparisons; the precise primary No prevalence is not coder-invariant. TabLLM values-only changes from No to Yes because the second scope protects ordered slots but not the removed name-prefix scaffolding. Full scope declarations and every disagreement follow.'),r'\subsection*{All comparisons and disagreements}']
for cid,c in C.items():
    d=D[cid];x+=[r'\subsubsection*{'+tex(cid+' / '+c['Study'])+'}']
    for label,r in [('Primary',c),('Second',d)]:
        x+=[r'\paragraph{'+label+' scope and protection.}']
        for s in S:x+=[r'\textbf{'+tex(s)+':} '+tex(r[s])+r'\par']
        x+=[tex('Scope evidence: '+r['Scope evidence'])+r'\par']
    x+=[r'\begin{tabular}{lll}\toprule Gate & Primary & Second \\ \midrule']
    for g in G:x.append(tex(g)+' & '+val(c,g)+' & '+val(d,g)+r' \\')
    x+=[r'\bottomrule\end{tabular}']
    for g in G:
        if val(c,g)==val(d,g):continue
        x+=[r'\paragraph{'+tex(g+' disagreement.')+'}']
        for label,r in [('Primary',c),('Second',d)]:x+=[r'\textbf{'+label+':} '+tex(r[g]['rationale']+' Evidence: '+r[g].get('evidence',r['Scope evidence']))+r'\par']
x+=[r'\end{document}'];(O/'SUPPLEMENT_SECOND_CODER_V1.tex').write_text('\n'.join(x)+'\n')
print(json.dumps({'agreement':agreement,'headline':headline},ensure_ascii=False,indent=2))
