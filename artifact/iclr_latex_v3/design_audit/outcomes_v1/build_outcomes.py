"""Documentary extraction. Reads pinned published text and frozen design codes only.
No network, no model runs, no edits to parent freezes. Values remain at printed precision.
"""
from pathlib import Path
from decimal import Decimal
import csv,json,re,collections
P=Path(__file__).resolve().parent; A=P.parent; S=A/'sources'
codes=json.loads((A/'phase_c_v1/CLAIM_IDENTIFICATION_V1.json').read_text())
C={x['Comparison ID']:x for x in codes}; rows=[]
def read(f): return (S/(f+'.txt')).read_text()
def add(cid,data,budget,metric,iv='',cv='',*,iu='',cu='',ut='not_reported',orient='higher',source='',model='',kind='table',match='matched',stratum='primary',notes='',contrast='',convention='',contrast_uncertainty='',sig='not_reported',direction='',duplicate=''):
    if not direction:
        if iv and cv and orient in ('higher','lower'):
            d=(Decimal(iv)-Decimal(cv))*(1 if orient=='higher' else -1)
            direction='favorable' if d>0 else 'adverse' if d<0 else 'equal_at_printed_precision'
        elif contrast and convention in ('comparator_minus_intended','intended_minus_comparator'):
            d=Decimal(contrast)*(1 if convention=='intended_minus_comparator' else -1)*(1 if orient=='higher' else -1)
            direction='favorable' if d>0 else 'adverse' if d<0 else 'equal_at_printed_precision'
        else: direction='unavailable'
    r={'Outcome ID':f'O{len(rows)+1:04d}','Comparison ID':cid,'Study':C[cid]['Study'],'Dataset-task':data,'Budget-regime':str(budget),'Model':model,'Metric':metric,'Orientation':orient,'Intended arm':C[cid]['Intended arm'],'Comparator arm':C[cid]['Comparator arm'],'Intended value':iv,'Comparator value':cv,'Intended uncertainty':iu,'Comparator uncertainty':cu,'Uncertainty type':ut,'Reported contrast':contrast,'Contrast convention':convention,'Contrast uncertainty':contrast_uncertainty,'Direction':direction,'Reported significance':sig,'Evidence':source,'Source type':kind,'Match status':match,'Summary stratum':stratum,'Duplicate of':duplicate,'Notes':notes}
    rows.append(r); return r['Outcome ID']
def pair(cid,data,budget,metric,a,b,**kw):
    av,*au=a.replace(' ','').split('±'); bv,*bu=b.replace(' ','').split('±')
    return add(cid,data,budget,metric,av,bv,iu=au[0] if au else '',cu=bu[0] if bu else '',**kw)
def figure(cid,data,budget,metric,source,**kw):
    return add(cid,data,budget,metric,source=source,kind='figure',notes='Figure-reported; exact value unavailable. No digitization. '+kw.pop('notes',''),**kw)
# LIFT: original printed values, shared starred correct arm explicitly duplicated by format.
lift9=[('CMC (23)','57.74±0.89 57.40±1.37 56.27±2.06 57.06±4.24 57.40±1.09 56.27±2.22'),('TAE (48)','65.59±6.63 66.67±5.48 60.22±6.72 64.52±8.53 69.89±9.31 69.89±6.72'),('Vehicle (54)','70.20±2.73 71.96±3.09 70.20±5.34 69.22±2.72 75.29±2.04 75.29±2.04'),('German','71.33±5.20 67.83±2.72 73.00±1.87 71.67±0.94 72.33±1.70 74.17±1.25')]
for data,v in lift9:
    v=v.split()
    for cid,i,j in [('C01-A',4,2),('C01-B',5,3),('C01-C',4,0),('C01-D',5,1)]:
        pair(cid,data,'Table 9 standard split','Classification accuracy (%)',v[i],v[j],source='C01_main.pdf Table 9, p.8; SD: checklist 3(c)',model='LIFT/GPT-3',ut='SD across runs',notes='Vehicle correct I/II share starred result; caption explicitly states same template.' if data.startswith('Vehicle') else '')
lift34=[('CMC (23)','49.49±0.56 51.30±1.05 51.30±2.51 48.82±3.12 50.39±1.05'),('TAE (48)','60.22±4.02 63.44±6.08 58.06±7.90 60.21±10.64 65.59±8.47'),('Vehicle (54)','64.31±2.37 66.87±1.54 65.49±1.69 69.02±3.67 69.02±3.67')]
for data,v in lift34:
    v=v.split()
    for cid,i,j in [('C01-A',3,1),('C01-B',4,2),('C01-C',3,0),('C01-D',4,0)]:
        amb=cid[-1] in 'CD'
        pair(cid,data,'Table 34 standard split','Classification accuracy (%)',v[i],v[j],source='C01_supp.pdf D.2.1 Table 34, printed p.44 / PDF p.22',model='LIFT/GPT-J',ut='SD across runs',match='ambiguous' if amb else 'matched',notes=('Published comparator is shared W/o Names; format I/II correspondence unresolved. ' if amb else '')+('Vehicle correct I/II shared starred result.' if data.startswith('Vehicle') else ''))
# Table 35 caption does not name metric; contextual RAE identification is flagged rather than asserted.
block=read('C01_supp').split('Table 35: Investigating')[1].split('(a) linear')[0]
n=0
for line in block.splitlines():
    vals=re.findall(r'\d+\.\d+\s*±\s*\d+\.\d+',line)
    if len(vals)!=6: continue
    data='Insurance' if n<5 else 'Student'; budget=['0.2','0.4','0.6','0.8','1.0'][n%5]; n+=1
    for cid,i,j in [('C01-A',4,2),('C01-B',5,3),('C01-C',4,1),('C01-D',5,1)]:
        amb=cid[-1] in 'CD'
        pair(cid,data,'training fraction '+budget,'Regression error (metric unnamed in Table 35; RAE in surrounding regression protocol)',vals[i],vals[j],source='C01_supp.pdf D.2.1 Table 35, printed p.45 / PDF p.23; regression protocol Table 20, printed p.36 (same full-data unnamed Insurance/Student results)',model='LIFT/GPT-3',ut='SD across runs',orient='lower',match='ambiguous' if amb else 'matched',notes='Metric identity inferred from regression protocol, not explicitly labelled in Table 35. '+('Shared W/O Names; format I/II mapping unresolved.' if amb else ''))
assert n==10
for cid in ['C01-A','C01-B','C01-C','C01-D']:
    add(cid,'Insurance and Student','all Table 35 fractions','Regression performance',source='C01_supp.pdf Table 35 caption and D.2.1',kind='author_prose',stratum='qualitative',match='ambiguous' if cid[-1] in 'CD' else 'matched',sig='Authors report no significant improvements with proper feature names; no pair-specific test/p-value',notes='Broad statement about feature-name inclusion, not a separate test for every shuffled comparator or fraction.')
# TabLLM public tables: parse mean + subscript SD without losing printed precision.
txt=read('C03_main'); block=txt.split('Table 12: Test')[1].split('Table 15: Full')[0]; data=None; table=12; extracted={}
for line in block.splitlines():
    mt=re.search(r'Table (1[234]):',line)
    if mt: table=int(mt[1])
    md=re.fullmatch(r'\s*([\w-]+) Dataset\s*',line)
    if md: data=md[1]
    ma=re.search(r'TabLLM \(T0 \+ (List Template|List Only Values|List Perm\. Names|List Perm\. Values)\)\s+(.*)',line)
    if ma:
        toks=ma[2].split(); assert len(toks)==10,(data,ma[1],toks)
        extracted.setdefault(data,{})[ma[1]]=(toks,table)
assert len(extracted)==9
for data,arms in extracted.items():
    intended=arms['List Template'][0]
    for cid,arm in [('C03-A','List Perm. Names'),('C03-B','List Only Values'),('C03-C','List Perm. Values')]:
        comp,table=arms[arm]
        for budget,a,b in zip(['0','4','8','16','32','64','128','256','512','all'],intended,comp):
            def sd(t):
                m=re.fullmatch(r'(\d+\.\d{2})(\.\d{2})',t)
                return (m[1],'0'+m[2]) if m else ('','')
            av,au=sd(a);bv,bu=sd(b)
            add(cid,data,budget,'Test AUC',av,bv,iu=au,cu=bu,ut='SD across five seeds' if av and bv else 'not_reported',source=f'C03_main.pdf Table {table}; SD convention Table 12',model='T0 11B + IA3',kind='table' if av and bv else 'missing_table_cell',notes=f'Printed tokens intended={a}; comparator={b}. '+('Asterisk: experiment omitted in published table; not zero.' if not(av and bv) else ''))
# Healthcare: positional cells; preserve blank Surgery 16384.
health=[('End of Life (EoL)','.70 .74 .78 .78 .79 .81 .81','.62 .66 .70 .74 .75 .77 .79'),('Surgical Procedure (Surgery)','.67 .73 .72 .73 .75 .78 .79','.60 .68 .70 .72 .74 .77 NA'),('Likelihood of Hospitalization (LoH)','.71 .73 .73 .76 .78 .81 .82','.62 .71 .72 .75 .75 .78 .80')]
for data,aa,bb in health:
    for budget,a,b in zip(['0','16','64','256','1024','4096','16384','all'],aa.split()+['NA'],bb.split()+['NA']):
        add('C03-A',data,budget,'Test AUC','0'+a if a!='NA' else '','0'+b if b!='NA' else '',source='C03_main.pdf Table 15; §5.3',model='T0 11B + IA3',kind='missing_table_cell' if 'NA' in (a,b) else 'table',notes='Healthcare; no uncertainty printed for TabLLM. Blank Surgery 16384 or em dash all retained as missing.' if 'NA' in (a,b) else 'Healthcare results; single seed (supplement §1.2), no uncertainty printed for TabLLM.')
for cid in ['C03-A','C03-B','C03-C']:
    figure(cid,'9 public datasets (aggregate)','0,4,8,16,32,64,128,256,512','Average AUC','C03_main.pdf Figure 2, p.6',stratum='aggregate_repeat',duplicate='Tables 12–14',ut='SD displayed; exact values unavailable',model='T0 11B + IA3')
# PLATO: only frozen arms, not additional 70/90% conditions.
for cid,b in [('C04-A','0.539±0.038'),('C04-B','0.240±0.067'),('C04-C','0.412±0.011')]:
    oid=pair(cid,'BRCA','60/20/20 split; 3 splits × 3 runs','PearsonR','0.583±0.019',b,source='C04_main.pdf §4.1; '+('Table 4, p.8' if cid=='C04-C' else 'Table 3, p.7'),ut='SD across runs and splits',model='PLATO')
    if cid=='C04-B': pair(cid,'BRCA','60/20/20 split; 3 splits × 3 runs','PearsonR','0.583±0.019',b,source='C04_main.pdf Table 2, p.7',ut='SD across runs and splits',model='PLATO',stratum='duplicate',duplicate=oid)
# CARTE: complete figure panels, no point interpolation.
for cid in ['C05-A','C05-B','C05-C']:
    for task in ['Regression','Classification']:
        figure(cid,task+' benchmark aggregate','32,64,128,256,512,1024','Normalized score','C05_main.pdf Appendix C.3 Figure 10(a/b), p.21',model='CARTE')
    add(cid,'Regression and classification aggregates','Figure 10 full regime','Normalized score',source='C05_main.pdf Appendix C.3 and Figure 10 caption, p.21',model='CARTE',kind='author_prose',stratum='qualitative',direction='author_reported_favorable',sig='Caption uses significant decrease for edge/attention exclusion; no numerical pair-specific test' if cid!='C05-A' else 'not_reported',notes='Authors describe performance losses from component changes; not assigned to individual curve points.')
# FeatLLM all Table 18 cells.
block=read('C06_main').split('Table 18: Ablation study results')[1]; n=0; data=None
for line in block.splitlines():
    vals=re.findall(r'\d+\.\d+±\d+\.\d+',line)
    if len(vals)!=5: continue
    prefix=line[:line.index(vals[0])].split(); budget=prefix[-1]
    if len(prefix)>1: data=' '.join(prefix[:-1])
    pair('C06-A',data,budget,'AUC (printed percentage scale)',vals[0],vals[3],source='C06_main.pdf Appendix K.2 Table 18, p.26; SD: §4.1',model='FeatLLM / GPT-3.5',ut='SD across three trials',notes='-Description removes full description block as frozen; not isolated feature-name removal.');n+=1
assert n==65,n
for budget,base,delta,se in [('4','75.7','-1.76','1.06'),('8','77.3','-1.20','0.33'),('16','78.4','-0.26','0.31'),('32','80.3','-0.29','0.58'),('64','81.4','-0.70','0.54'),('Avg','78.6','-0.84','0.28')]:
    add('C06-A','13 datasets × three trials (aggregate)',budget,'AUC (percentage scale)',base,contrast=delta,convention='comparator_minus_intended',contrast_uncertainty=se,ut='SE of reported change',source='C06_main.pdf Table 4, p.8',model='FeatLLM / GPT-3.5',stratum='aggregate_repeat',duplicate='Table 18 per-dataset outcomes',notes='Comparator absolute score not printed; retain reported change and SE, no synthetic absolute score.')
# TabuLa both subsets, all displayed shots; prose scoped to stated regimes.
for subset,end in [('16-shot subset','16'),('32-shot subset','32')]:
    figure('C07-A','UniPredict '+subset,'all displayed shots 0–'+end,'Open-vocabulary accuracy','C07_main.pdf Appendix F.2 Figure 12, p.27',model='TabuLa-8B',ut='Shaded bands displayed; exact limits unavailable, type not stated in Figure 12 caption')
add('C07-A','UniPredict 16-shot subset','low-shot regime in 16-shot-subset panel','Open-vocabulary accuracy',source='C07_main.pdf Appendix F.2, p.26',model='TabuLa-8B',kind='author_prose',stratum='qualitative',contrast='3–5 percentage points (author-reported range)',convention='intended_minus_comparator; qualitative range',direction='author_reported_favorable',notes='Range stated by authors for 16-shot subset; no fabricated per-shot values.')
add('C07-A','UniPredict 32-shot subset','32 shots','Open-vocabulary accuracy',source='C07_main.pdf Appendix F.2, p.26',model='TabuLa-8B',kind='author_prose',stratum='qualitative',direction='author_reported_similar',notes='Authors describe effectively identical performance; not an equivalence test or exact numeric equality.')
# ConTextTab: published ranks and deltas, plus exact printed matrix cells.
ctx=[('C08-A','4.27','-2.7','-4.8','.92','.08'),('C08-B','3.49','-1.7','-3.3','.84','.16'),('C08-C','5.76','-4.8','-7.3','.96','.04'),('C08-D','4.12','-1.4','-4.3','.84','.16'),('C08-E','3.35','-1.2','-2.1','.92','.08'),('C08-F','1.20','0.0','0.0','.57','.43')]
for cid,rank,acc,r2,win,loss in ctx:
    enriched=cid=='C08-F'
    for bench in ['All','CARTE']:
        add(cid,bench+' semantic ablation aggregate','§5/§5.1: fixed test split, default context; no separate budget ladder in semantic table','Average rank',rank if enriched else '1.24','1.24' if enriched else rank,orient='lower',source='C08_main.pdf Table 2 semantic block, p.9',model='ConTextTab (one-dimensional numeric embedding)',stratum='aggregate_metric' if bench=='CARTE' else 'duplicate',duplicate='CARTE rank in same Table 2' if bench=='All' else '',notes='All rank duplicates CARTE; other benchmarks not evaluated for semantic block.')
    for metric,base,delta in [('Accuracy (percentage scale)','76.9',acc),('Soft-clipped R2 (percentage scale)','72.4',r2)]:
        add(cid,'CARTE benchmark aggregate','§5/§5.1: fixed test split, default context; no separate budget ladder in semantic table',metric,'' if enriched else base,base if enriched else '',contrast=delta,convention='intended_minus_comparator' if enriched else 'comparator_minus_intended',source='C08_main.pdf Table 2 semantic block, p.9',model='ConTextTab (one-dimensional numeric embedding)',stratum='aggregate_metric',notes='Variant cell is a change from base, not absolute performance. No error bars printed. R2 is soft-clipped per §5; negative scores mapped with tanh.')
    fig='10' if cid in ['C08-E','C08-F'] else '9'; p='28' if fig=='10' else '27'
    add(cid,'CARTE benchmark aggregate','semantic ablation evaluations','Pairwise win ratio (each arm over the other)','0'+win,'0'+loss,source=f'C08_main.pdf Appendix A.4 Figure {fig}(a,b), p.{p}',model='ConTextTab',kind='printed_figure_cell',stratum='pairwise_summary',sig=('Two-sided Wilcoxon signed-rank p=0.40 (printed)' if enriched else 'Two-sided Wilcoxon signed-rank p=0.00 (rounded as printed; not exact zero)'),notes='Both directed win-ratio cells transcribed; Model A is horizontal axis. Test applies to the aggregate pair, not each dataset or metric separately. Win ratios need not sum to one because ties are possible (§5).')
    for benchmark in ['OML-CC18','OML-CTR23','TabReD','TALENT-Tiny']:
        add(cid,benchmark,'semantic block not evaluated','All metric cells N/A',source='C08_main.pdf Table 2 semantic block, p.9',kind='not_applicable',stratum='not_applicable',notes='Published N/A cells retained by benchmark; no outcome or direction inferred.')
# TabSTAR all 20 datasets, both frozen comparisons.
block=read('C09_main').split('Table 32: Downstream performance')[1];n=0
for line in block.splitlines():
    vals=re.findall(r'\d+\.\d+±\d+\.\d+',line)
    if len(vals)!=3: continue
    data=line.split()[0];assert re.fullmatch('[CR]\\d{2}',data)
    for cid,j in [('C09-A',1),('C09-B',0)]:
        pair(cid,data,'Q3: up to 10K examples; Appendix G.4','AUROC (printed percentage scale)' if data[0]=='C' else 'R2 (printed percentage scale)',vals[2],vals[j],source='C09_main.pdf Appendix G.4 Table 32, p.54',model='TabSTAR',ut='95% CI',notes='Dataset IDs as published; top scores bolded before rounding, not a significance test.')
    n+=1
assert n==20
for task,name,bin_,full in [('Classification','0.386±0.095','0.544±0.093','0.593±0.097'),('Regression','0.386±0.081','0.584±0.076','0.596±0.079')]:
    for cid,b in [('C09-A',bin_),('C09-B',name)]:
        pair(cid,task+' aggregate','Q3: up to 10K examples','Normalized score',full,b,source='C09_main.pdf Table 4, p.10',model='TabSTAR',ut='95% CI',stratum='aggregate_repeat',duplicate='Table 32 per-dataset evaluations',notes='Retain normalized aggregate separately from raw AUROC/R2; no pooling.')
for cid in ['C09-A','C09-B']:
    figure(cid,'Classification aggregate (8 datasets)','up to 10K examples','Normalized score','C09_main.pdf Appendix G.4 Figure 8, p.52',ut='95% CI displayed; exact values unavailable',model='TabSTAR',stratum='aggregate_repeat',duplicate='Table 4 / Table 32',match='ambiguous',notes='Figure uses Numerical-Full/Range/None labels, distinct from Table 32 Name/Name+Bin/TabSTAR; presentation linkage not silently repaired.')
# TARTE official indexed publication; no preprint values or direction inferred from label order.
for cid in ['C10-A','C10-B']:
    figure(cid,'Downstream tables (pooled critical-difference diagram)','training sizes 32–1024','Average rank','Published TMLR 08/2025 TARTE §4.3 Figure 6, p.10; https://openreview.net/pdf/7dfbc481b152839b35e7f200b528bd880a6826e2.pdf',orient='lower',model='Ridge fitted on TARTE embeddings',notes='Official indexed text confirms published arms/scope; official PDF download restricted. Exact rank and pairwise significance unavailable. Preprint mirror not used.')
# Output extraction is independent of claim synthesis below.
def writecsv(name,rs):
    with (P/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
writecsv('REPORTED_OUTCOMES_V1.csv',rows)
(P/'REPORTED_OUTCOMES_V1.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
# Frozen design codes joined without modification.
claims=[]
for r in rows:
    c=C[r['Comparison ID']]; util=c['Predictive utility identifiable']['value']; content=c['Content sensitivity identifiable']['value']; d=r['Direction']
    if r['Match status']!='matched': observed='Arm correspondence unresolved; numerical record cannot support this frozen comparison.'
    elif r['Source type']=='not_applicable': observed='No published evaluation for this benchmark in the semantic block.'
    elif d=='unavailable': observed='Exact direction unavailable; no directional claim assigned.'
    elif d=='equal_at_printed_precision': observed='Equal printed point estimates; no equivalence or zero-effect conclusion.'
    elif d=='author_reported_similar': observed='Authors report similar performance in this regime; no formal equivalence conclusion.'
    else: observed=('Author-reported ' if d.startswith('author_') else 'Descriptive point-estimate ') + ('advantage for intended arm.' if 'favorable' in d else 'disadvantage for intended arm.')
    eligible=r['Match status']=='matched' and r['Source type']!='not_applicable'
    if not eligible or d=='unavailable': u='No directional utility conclusion from this row.'
    elif util=='No': u='Does not identify predictive utility of the tested component, irrespective of the performance gap.'
    elif util=='Partial': u='Predictive utility unresolved under frozen gates; observed comparison is conditional on unresolved design requirements.'
    elif d in ('favorable','author_reported_favorable'): u='Positive predictive utility for the frozen scope and reported regime; '+('author-reported qualitative evidence only.' if d.startswith('author_') else 'descriptive estimate; significance only as separately reported.')
    elif d=='adverse': u='Negative intended-minus-reference utility estimate for this scope/regime; no general benefit claim.'
    else: u='No positive utility established by this row; equality/similarity does not establish zero utility.'
    if not eligible or d=='unavailable': k='No directional content-sensitivity conclusion from this row.'
    elif content=='No': k='Does not identify intended–wrong content sensitivity for the frozen scope.'
    elif content=='Partial': k='Content sensitivity remains conditional/unresolved under frozen design gates.'
    elif d in ('favorable','adverse'): k='Descriptive intended–wrong content sensitivity; '+('intended arm better.' if d=='favorable' else 'wrong arm better; not a benefit from correctness.')
    else: k='No nonzero content effect established at printed precision; not equivalence.'
    claims.append({'Outcome ID':r['Outcome ID'],'Comparison ID':r['Comparison ID'],'Study':r['Study'],'Tested semantic scope':c['Tested semantic use'],'Dataset-task':r['Dataset-task'],'Budget-regime':r['Budget-regime'],'Metric':r['Metric'],'Match status':r['Match status'],'Summary stratum':r['Summary stratum'],'Direction':d,'Admissible reference':c['Admissible reference']['value'],'Content sensitivity identifiable':content,'Predictive utility identifiable':util,'Observed result':observed,'Supported content claim':k,'Supported utility claim':u,'Reported significance':r['Reported significance'],'Outcome evidence':r['Evidence'],'Design evidence':c['Scope evidence']})
writecsv('SUPPORTED_CLAIMS_V1.csv',claims)
# Counts are descriptive rows, not independent experiments. Keep numeric aggregates in own stratum.
def summarize(rr):
    cc=collections.Counter(r['Direction'] for r in rr); f=cc['favorable'];a=cc['adverse'];e=cc['equal_at_printed_precision'];z=cc['unavailable']
    s='mixed' if f and a else 'favorable-or-equal' if f and e else 'adverse-or-equal' if a and e else 'all favorable' if f else 'all adverse' if a else 'equal at printed precision' if e else 'direction unavailable'
    if z and s!='direction unavailable': s+='; unavailable directions also retained'
    return s,dict(cc)
summary=[]
for cid,c in C.items():
    rr=[r for r in rows if r['Comparison ID']==cid];primary=[r for r in rr if r['Match status']=='matched' and r['Summary stratum']=='primary']; agg=[r for r in rr if r['Match status']=='matched' and r['Summary stratum'] in ['aggregate_metric','pairwise_summary']]
    label,counts=summarize(primary);alabel,acounts=summarize(agg)
    summary.append({'Comparison ID':cid,'Study':c['Study'],'Tested semantic scope':c['Tested semantic use'],'Content sensitivity identifiable':c['Content sensitivity identifiable']['value'],'Predictive utility identifiable':c['Predictive utility identifiable']['value'],'Admissible reference':c['Admissible reference']['value'],'Primary synthesis':label,'Primary counts':json.dumps(counts),'Aggregate-only synthesis':alabel,'Aggregate-only counts':json.dumps(acounts),'Total extracted rows':len(rr),'Ambiguous rows':sum(r['Match status']!='matched' for r in rr),'Qualitative reports':json.dumps([{'direction':r['Direction'],'regime':r['Budget-regime'],'notes':r['Notes']} for r in rr if r['Summary stratum']=='qualitative'],ensure_ascii=False),'All outcome IDs':';'.join(r['Outcome ID'] for r in rr)})
writecsv('COMPARISON_SUMMARY_V1.csv',summary)
studies=[]
for study in dict.fromkeys(c['Study'] for c in codes):
    cc=[c for c in codes if c['Study']==study]; ss=[s for s in summary if s['Study']==study];ad=[c['Admissible reference']['value'] for c in cc]
    studies.append({'Study':study,'All comparisons':';'.join(c['Comparison ID'] for c in cc),'Utility reference status':'at least one Yes' if 'Yes' in ad else 'Unclear only (no Yes)' if 'Unclear' in ad else 'No for all comparisons','Comparison summaries':json.dumps(ss,ensure_ascii=False),'Interpretation rule':'Every comparison retained; no best-arm selection, cross-metric pooling, or independent-experiment counts.'})
writecsv('STUDY_SUMMARY_V1.csv',studies)
print(json.dumps({'studies':len(studies),'comparisons':len(summary),'outcome_rows':len(rows),'by_study':dict(collections.Counter(r['Study'] for r in rows))},indent=2))
# Readable compression preserves each comparison, with no strongest-arm selection.
lines=['# Supported published claims: study summary v1','',
'Frozen design codes are unchanged. Reported outcomes were not extracted or used in assigning the design codes. This phase joins the codes to published outcomes; it is not outcome-blind review or meta-analysis.','',
'Counts below describe extracted records, not independent experiments. Figure panels are one record per displayed regime. Numeric aggregates, pairwise summaries, author prose, ambiguous matches, N/A cells and duplicates remain distinct.','',
'| Study | Published utility-reference status | What is observed and identifiable |', '|---|---|---|']
texts={
'LIFT':'C01-A/B: mixed directions across both LM variants and tasks; content identification remains Partial. C01-C/D: each has 3 favorable and 1 adverse matched classification outcomes, but utility is No. Supplementary shared-unnamed outcomes are retained as ambiguous and cannot establish format-specific claims.',
'TabLLM':'C03-A identifies content sensitivity, with both favorable and adverse point estimates (including healthcare). C03-B values-only is non-admissible: its gains cannot be labelled feature-name utility. C03-C has favorable/equal recorded estimates but only Partial content identification and No utility identification. Missing full-data/healthcare cells remain visible.',
'PLATO':'All three frozen BRCA comparisons favor the full KG by PearsonR point estimates. C04-A utility remains Partial; C04-B/C utility is No. SD does not supply a pairwise significance test.',
'CARTE':'C05-A/B/C: both regression and classification panels retained; exact values unavailable. Authors describe losses from component ablation, but isolated utility is No/Partial/No respectively. Broad caption wording does not establish a statistical test at every train size.',
'FeatLLM':'C06-A: 42 favorable and 23 adverse per-dataset/shot estimates; aggregate -Description changes favor intended at all five shots. Utility remains Partial for the full description block; no feature-name-only conclusion.',
'TabuLa-8B':'C07-A is admissible for JOINT feature-and-target-header content. Both subset panels are retained without digitization. Authors report a 3–5 percentage-point gain in the 16-shot subset and effectively identical performance at 32 shots. This supports regime-dependent qualitative utility, not a uniform benefit or feature-only effect.',
'ConTextTab':'C08-A/B/C/D aggregate ranks, accuracy/R2 deltas and win ratios favor semantic encoding, but utility is No. C08-E is admissible: removal loses 1.2 accuracy and 2.1 R2 percentage points; base wins 0.92 vs 0.08, with Wilcoxon p printed 0.00 (rounded). C08-F remains Partial: better rank and 0.57 win ratio, but accuracy/R2 changes round to 0.0 and p=0.40.',
'TabSTAR':'Both comparisons are admissible for their narrower verbalization scopes. C09-A (quantile text conditional on name+bin): 9 favorable / 10 adverse / 1 equal. C09-B (bin/quantile content conditional on numerical branch): 14 favorable / 3 adverse / 3 equal. Aggregate normalized scores favor full in both tasks; per-dataset utility is mixed, not uniformly positive.',
'TARTE':'C10-A/B: published Figure 6 compares Ridge embeddings over sizes 32–1024. Exact ranks/directions cannot be recovered from accessible official text; no numeric direction assigned. Utility remains Partial/No. The preacceptance mirror is not a published numeric source.'}
for r in studies: lines.append(f"| {r['Study']} | {r['Utility reference status']} | {texts[r['Study']]} |")
lines+=['','## Every frozen comparison','', '| ID | Content / utility identifiable | Primary direction counts | Separate aggregate counts | Retained ambiguous rows |','|---|---|---|---|---|']
for s in summary:
    lines.append(f"| {s['Comparison ID']} | {s['Content sensitivity identifiable']} / {s['Predictive utility identifiable']} | {s['Primary synthesis']}: {s['Primary counts']} | {s['Aggregate-only counts']} | {s['Ambiguous rows']} |")
lines+=['','## Scope and handoff','',
'At least one admissible published utility reference occurs in 3/9 studies (TabuLa-8B, ConTextTab, TabSTAR). Four studies have unresolved references but no Yes, and two have only No. The 4/25 admissible comparisons are descriptive, correlated comparison counts, not four independent experiments. Outcomes do not alter these design-level counts.','',
'**TabLLM manuscript correction for the later integration phase:** published List Template vs List Permuted Names is the clean intended–wrong comparison. Published List Only Values fails Preservation and is not the utility reference. Our subsequently constructed stable-anonymous reference belongs to the separate quantitative deep dive and is not among the published outcomes here. No manuscript files were edited in this phase.','',
'**Extraction limitations:** LIFT Table 35 does not label its metric explicitly; RAE identification is contextual (Table 20 and the regression protocol), and lower-is-better ordering is retained with that note. Shared unnamed supplementary arms are ambiguous. TabSTAR Figure 8 uses different labels from its tabulated variants and is retained as an ambiguous aggregate presentation. TARTE official indexed text is available but the published PDF download remains restricted; exact rank/significance cannot be supplied. None of these limitations changes the frozen design codes.','',
'Artifacts: [raw long-format outcomes](REPORTED_OUTCOMES_V1.csv), [row-level supported claims](SUPPORTED_CLAIMS_V1.csv), [comparison summaries](COMPARISON_SUMMARY_V1.csv), [study summaries](STUDY_SUMMARY_V1.csv), [source inventory](SOURCE_COVERAGE_V1.md).']
(P/'STUDY_SUMMARY_V1.md').write_text('\n'.join(lines)+'\n')
