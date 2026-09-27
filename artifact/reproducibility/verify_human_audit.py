#!/usr/bin/env python3
"""Recompute human agreement and compare final coding with manuscript tables."""
from collections import Counter
import csv,re

def read(root,name):return list(csv.DictReader((root/'published_audit'/name).open()))
def conjunction(values):return 'No' if 'No' in values else ('Yes' if all(v=='Yes' for v in values) else 'Unclear')
def support(values):return {'No':'Unsupported','Yes':'Supported','Unclear':'Indeterminate'}[conjunction(values)]
def agreement(a,b):
    n=len(a);ca=Counter(a);cb=Counter(b);same=sum(x==y for x,y in zip(a,b));pe=sum(ca[k]*cb[k] for k in set(ca)|set(cb))/(n*n)
    return same,n,(same/n-pe)/(1-pe) if pe!=1 else 1.0
def compute(root):
    a=read(root,'claim_coding_coder_a.csv');b={r['comparison_id']:r for r in read(root,'claim_coding_coder_b.csv')};out=[]
    fields=[('Content-sensitivity claim','reported_content_sensitivity_claim','reported_content_sensitivity_claim'),('Predictive-utility claim','reported_utility_claim','reported_utility_claim'),('Content-sensitivity support','supports_content_sensitivity','supports_content_sensitivity'),('Removal','pu_removal','utility_removal'),('Preservation','pu_preservation','utility_preservation'),('Interface','pu_interface','utility_interface'),('Predictive-utility support','supports_predictive_utility','supports_predictive_utility')]
    for name,ka,kb in fields:
        same,n,k=agreement([r[ka] for r in a],[b[r['comparison_id']][kb] for r in a]);out.append(dict(stage='independent_initial_claim_control',coding_item=name,agree=same,total=n,percent=100*same/n,kappa=k,coder_a_source='claim_coding_coder_a.csv',coder_b_source='claim_coding_coder_b.csv',coder_a_column=ka,coder_b_column=kb))
    pa={r['ID']:r for r in read(root,'p1_p6_coder_a.csv')};pb={r['ID']:r for r in read(root,'p1_p6_coder_b.csv')};final=read(root,'comparison_level_final.csv')
    left=[pa[r['comparison_id']][f'P{i}'] for r in final for i in range(1,7)];right=[pb[r['comparison_id']][f'P{i}'] for r in final for i in range(1,7)]
    same,n,k=agreement(left,right);out.append(dict(stage='independent_frozen_rule',coding_item='P1-P6 check agreement',agree=same,total=n,percent=100*same/n,kappa=k,coder_a_source='p1_p6_coder_a.csv',coder_b_source='p1_p6_coder_b.csv',coder_a_column='P1..P6',coder_b_column='P1..P6'))
    explicit=[r for r in final if r['predictive_utility_claim']=='Yes'];aa={r['comparison_id']:r for r in a}
    def derive(r,checks,initial,removal):
        ident=r['comparison_id'];p=checks[ident]
        return support([initial[ident][removal],conjunction([p[f'P{i}'] for i in range(1,5)]),conjunction([p[f'P{i}'] for i in range(5,7)])])
    same,n,k=agreement([derive(r,pa,aa,'pu_removal') for r in explicit],[derive(r,pb,b,'utility_removal') for r in explicit]);out.append(dict(stage='independent_frozen_rule',coding_item='Utility support among final explicit claims',agree=same,total=n,percent=100*same/n,kappa=k,coder_a_source='p1_p6_coder_a.csv + claim_coding_coder_a.csv',coder_b_source='p1_p6_coder_b.csv + claim_coding_coder_b.csv',coder_a_column='Removal + derived Preservation/Interface',coder_b_column='Removal + derived Preservation/Interface'))
    return out

def verify(root,add):
    source='published_audit/comparison_level_final.csv';final=read(root,'comparison_level_final.csv');evidence=read(root,'p1_p6_evidence_150.csv');a={r['ID']:r for r in read(root,'p1_p6_coder_a.csv')};b={r['ID']:r for r in read(root,'p1_p6_coder_b.csv')}
    def record(item,quantity,expected,actual,src=source,note=''):
        add(item,quantity,expected,(actual,src,quantity),note)
    content=read(root,'content_sensitivity_final_adjudication.csv')
    content_source='published_audit/content_sensitivity_final_adjudication.csv'
    initial_a={r['comparison_id']:r for r in read(root,'claim_coding_coder_a.csv')}
    initial_b={r['comparison_id']:r for r in read(root,'claim_coding_coder_b.csv')}
    final_by_id={r['comparison_id']:r for r in final}
    claim_by_id={r['comparison_id']:r for r in read(root,'claim_coding.csv')}
    explicit={k for k,r in initial_a.items() if r['reported_content_sensitivity_claim']=='Yes'}
    record('tab:published_audit','standalone final content records',4,len(content),content_source)
    record('tab:published_audit','standalone content record ID coverage',1,int(len({r['comparison_id'] for r in content})==4 and {r['comparison_id'] for r in content}==explicit),content_source)
    norm={'Supported':'Supported','None':'Unsupported','Unclear':'Indeterminate'}
    for r in content:
        ident=r['comparison_id'];ia=initial_a[ident];ib=initial_b[ident]
        for label,old in [('a',ia),('b',ib)]:
            record('tab:published_audit',ident+' original coder '+label+' content label retained',1,int(r['coder_'+label+'_initial']==old['supports_content_sensitivity']),content_source)
        record('tab:published_audit',ident+' final content projection matches adjudication',1,int(final_by_id[ident]['content_sensitivity_support']==r['final_support'] and claim_by_id[ident]['content_sensitivity_support']==r['final_support']),content_source)
        record('tab:published_audit',ident+' final content points to adjudication source',1,int(all('content_sensitivity_final_adjudication.csv' in obj[ident]['final_content_source'] for obj in [final_by_id,claim_by_id])),content_source)
        record('tab:published_audit',ident+' original construction evidence retained',1,int(ia['construction_source_checked'] in r['source_evidence'] and ib['construction_evidence'] in r['source_evidence']),content_source)
        record('tab:published_audit',ident+' finalization provenance and rationale present',1,int(r['record_created']=='2026-09-24' and bool(r['final_rationale']) and bool(r['provenance_note']) and bool(r['decision_source'])),content_source)
        if ident!='C01-B':
            record('tab:published_audit',ident+' agreed initial label carried forward',1,int(ia['supports_content_sensitivity']==ib['supports_content_sensitivity'] and norm[ia['supports_content_sensitivity']]==r['final_support'] and r['adjudication_status']=='initial_agreement_carried_forward'),content_source)
        else:
            detail=(root/'published_audit/C01-B_adjudication_record.md').read_text()
            record('tab:published_audit','C01-B author-supplied final decision matches record',1,int('## Final adjudication\n\nSupported.' in detail and r['final_support']=='Supported' and r['adjudication_status']=='resolved_at_finalization_author_supplied'),content_source)
            record('tab:published_audit','C01-B original disagreement and missing historic record disclosed',1,int(r['coder_a_initial']=='Unclear' and r['coder_b_initial']=='Supported' and 'contemporaneous' in r['provenance_note'] and 'not retained' in r['provenance_note']),content_source)
    for status,n in [('Supported',3),('Unsupported',1),('Indeterminate',0)]:
        record('tab:published_audit','standalone content adjudication '+status,n,sum(r['final_support']==status for r in content),content_source)
    record('tab:published_audit','comparison count',25,len(final))
    for typ,expected in [('content_sensitivity',[4,3,1,0]),('predictive_utility',[18,1,11,6])]:
        selected=[r for r in final if r[typ+'_claim']=='Yes'];record('tab:published_audit',typ+' explicit claims',expected[0],len(selected))
        for status,n in zip(['Supported','Unsupported','Indeterminate'],expected[1:]):record('tab:published_audit',typ+' '+status,n,sum(r[typ+'_support']==status for r in selected))
    tex=(root/'iclr_latex_v3/appendix_new.tex').read_text()
    block=next(s for s in re.findall(r'\\begin\{table\}.*?\\end\{table\}',tex,re.S) if '\\label{tab:app-published-audit}' in s)
    paper={m[0]:m[1:] for m in re.findall(r'&\s*(C\d\d-[A-Z])\s*&\s*([YN?])\s*&\s*(S|U|I|--)\s*&\s*([YN?])\s*&\s*(S|U|I|--)\s*\\\\',block)}
    codes={'Yes':'Y','No':'N','Unclear':'?','Supported':'S','Unsupported':'U','Indeterminate':'I','Not claimed':'--'}
    for r in final:
        ident=r['comparison_id'];values=[codes[r['content_sensitivity_claim']],codes[r['content_sensitivity_support']],codes[r['predictive_utility_claim']],codes[r['predictive_utility_support']]]
        if r['predictive_utility_claim']=='No':values[3]='--'
        for i,(actual,expected) in enumerate(zip(values,paper[ident])):record('tab:app-published-audit',f'{ident} printed coding field {i+1}',1,int(actual==expected),note=f'Printed={expected}; frozen coding={actual}; content adjudication source is explicitly labelled.')
        for name,indices in [('preservation',range(1,5)),('interface',range(5,7))]:record('tab:app-published-audit',f'{ident} derived {name}',1,int(r[name]==conjunction([r[f'P{i}'] for i in indices])))
        record('tab:app-published-audit',ident+' derived support',1,int(r['predictive_utility_support']==support([r['removal'],r['preservation'],r['interface']])))
    summary=compute(root);frozen=read(root,'agreement_summary.csv')
    block=next(s for s in re.findall(r'\\begin\{table\}.*?\\end\{table\}',tex,re.S) if '\\label{tab:app-published-audit-agreement}' in s)
    printed=re.findall(r'&\s*(\d+)/25\s*\((\d+)\\%\)\s*&\s*(\d*\.\d+)',block)
    record('tab:app-published-audit-agreement','printed agreement rows',7,len(printed))
    record('Appendix F.2','unique evidence checks',150,len({(r['ID'],r['Check']) for r in evidence}))
    record('tab:published_audit','unique comparison IDs',25,len({r['comparison_id'] for r in final}))
    for r,p in zip(summary[:7],printed):
        for key,e in zip(['agree','percent','kappa'],p):record('tab:app-published-audit-agreement',r['coding_item']+' '+key,e,r[key],'published_audit/agreement_summary.csv')
    for r in summary:
        stored=next(v for v in frozen if v['stage']==r['stage'] and v['coding_item']==r['coding_item'])
        record('Appendix F.2',r['coding_item']+' standalone summary equality',1,int(all(float(stored[k])==r[k] for k in ['agree','total','percent','kappa'])),'published_audit/agreement_summary.csv')
    record('Appendix F.2','independent P1-P6 matches',105,summary[7]['agree'],'published_audit/p1_p6_coder_a.csv;published_audit/p1_p6_coder_b.csv')
    record('Appendix F.2','independent P1-P6 total',150,summary[7]['total'])
    record('Appendix F.2','independent explicit utility support matches',15,summary[8]['agree'])
    record('Appendix F.2','independent explicit utility support kappa','.693',summary[8]['kappa'])
    fi={r['comparison_id']:r for r in final}
    for e in evidence:
        ident=e['ID'];k=e['Check'];ok=e['Coder A initial']==a[ident][k] and e['Coder B initial']==b[ident][k] and e['Final judgment']==fi[ident][k] and bool(e['Final evidence / adjudication basis']) and bool(e['Final rationale'])
        record('tab:app-published-audit',ident+'/'+k+' evidence and independent/final labels',1,int(ok),'published_audit/p1_p6_evidence_150.csv')
    sources=read(root,'source_evidence.csv')
    block=next(s for s in re.findall(r'\\begin\{table\}.*?\\end\{table\}',tex,re.S) if '\\label{tab:app-published-claim-provenance}' in s)
    ids=set(re.findall(r'C\d\d-[A-Z]',block))
    record('tab:app-published-claim-provenance','source table comparison coverage',len(ids),len(ids & {r['comparison_id'] for r in sources if r['claim_type']=='predictive_utility' and r['source_location'] and r['claim_quote']}),'published_audit/source_evidence.csv')
    old=list(csv.DictReader((root/'iclr_latex_v3/design_audit/ELIGIBILITY_SCREEN_V1.csv').open()));revision=read(root,'revision_screening_record.csv')
    record('tab:app-audit-screening','screened studies',12,len(old)+len(revision),'iclr_latex_v3/design_audit/ELIGIBILITY_SCREEN_V1.csv;published_audit/revision_screening_record.csv')
    record('tab:app-audit-screening','included studies',9,sum(r['decision']=='INCLUDE' for r in old)+sum(r['decision']=='INCLUDE' for r in revision))
