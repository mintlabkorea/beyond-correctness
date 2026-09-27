#!/usr/bin/env python3
"""Frozen strict-content recoding, provenance checks and deterministic merge."""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.metrics import cohen_kappa_score

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
OLD = ROOT/'experiments/published_claim_match_w5_v1'
LABELS = ('Yes','No','Unclear')
SUPPORT = ('Supported','None','Unclear')
STATES = ('Matched','Mismatch','Indeterminate','Not claimed')


def load(p):
    return json.loads(Path(p).read_text())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def dump(name, obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def csvout(name, rows):
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def keyed(path):
    rows=load(path)
    keys={r['comparison_id']:r for r in rows}
    assert len(rows)==len(keys)==25
    assert set(keys)=={r['comparison_id'] for r in load(OLD/'UNITS_V1.json')}
    return keys


def originals():
    frozen=load(OUT/'PRE_CODING_FREEZE_V2.json')
    for p,h in frozen['original_files'].items():
        assert sha(ROOT/p)==h, p
    for p,h in frozen['packet_files'].items():
        assert sha(OUT/'packet'/p)==h,p


def freeze(name, paths):
    data={str(p.relative_to(OUT)):sha(p) for p in paths}
    if (OUT/name).exists():
        assert load(OUT/name)['files']==data
    else:
        dump(name,dict(time_utc=datetime.now(timezone.utc).isoformat(),files=data))


def frozen_check(name):
    for p,h in load(OUT/name)['files'].items():
        assert sha(OUT/p)==h


def normalize(text):
    return ' '.join(re.sub(r'(?<=\w)-\s+(?=\w)','',text).replace('\f',' ').split())


def validate_claims(rows):
    packet=keyed(OUT/'packet/CLAIM_WINDOWS_MASKED_V1.json')
    for cid,r in rows.items():
        assert r['claim_content'] in LABELS
        assert r['study']==packet[cid]['study']
        assert cid+'-W' in r['claim_location']
        assert r['rationale']
        source=normalize('\n'.join(w['text'] for w in packet[cid]['windows']))
        for quote in r['claim_text'].split(' | '):
            assert normalize(quote.strip().strip('“”"')) in source,(cid,quote)


def agreement(a,b):
    n=len(a); ca,cb=Counter(a),Counter(b)
    po=sum(x==y for x,y in zip(a,b))/n
    pe=sum(ca[x]*cb[x] for x in LABELS)/(n*n)
    k=(po-pe)/(1-pe) if pe<1 else None
    if k is not None:
        np.testing.assert_allclose(k,cohen_kappa_score(a,b,labels=list(LABELS)),atol=1e-14)
    return dict(n=n,agreements=sum(x==y for x,y in zip(a,b)),raw_agreement=po,
        expected_agreement=pe,kappa=k,marginal_a={x:ca[x] for x in LABELS},
        marginal_b={x:cb[x] for x in LABELS},
        confusion=[dict(coder_a=x,coder_b=y,count=sum(xx==x and yy==y for xx,yy in zip(a,b))) for x in LABELS for y in LABELS])


def match(claim,support):
    assert claim in LABELS and support in SUPPORT
    if claim=='No': return 'Not claimed'
    if claim=='Unclear': return 'Indeterminate'
    return {'Supported':'Matched','None':'Mismatch','Unclear':'Indeterminate'}[support]


def coders():
    originals()
    a,b=keyed(OUT/'coder_a_raw.json'),keyed(OUT/'coder_b_raw.json')
    validate_claims(a);validate_claims(b)
    freeze('RAW_CODER_FREEZE_V2.json',[OUT/f'coder_{c}_{part}.json' for c in ('a','b') for part in ('raw','boundary')])
    stats=agreement([a[k]['claim_content'] for k in a],[b[k]['claim_content'] for k in a])
    dump('CONTENT_AGREEMENT_V2.json',stats)
    csvout('CONTENT_AGREEMENT_V2.csv',[{k:v for k,v in stats.items() if k not in ('marginal_a','marginal_b','confusion')}])
    csvout('CONTENT_CONFUSION_V2.csv',stats['confusion'])
    differences=[dict(comparison_id=k,study=a[k]['study'],coder_a=a[k]['claim_content'],coder_b=b[k]['claim_content'],rationale_a=a[k]['rationale'],rationale_b=b[k]['rationale']) for k in a if a[k]['claim_content']!=b[k]['claim_content']]
    dump('RAW_DISAGREEMENTS_V2.json',differences)
    print(json.dumps({k:v for k,v in stats.items() if k!='confusion'},indent=2))


def finish():
    originals();frozen_check('RAW_CODER_FREEZE_V2.json')
    for p,h in load(OUT/'ADJUDICATION_PACKET_FREEZE_V2.json')['files'].items():
        assert sha(ROOT/p)==h,p
    a,b=keyed(OUT/'coder_a_raw.json'),keyed(OUT/'coder_b_raw.json')
    adj=keyed(OUT/'content_adjudicated.json');validate_claims(adj)
    freeze('ADJUDICATION_FREEZE_V2.json',[OUT/p for p in ('content_adjudicated.json','adjudication_ledger.json','adjudicator_boundary.json')])
    old=keyed(OLD/'COMPARISONS_CLAIM_MATCH_V1.json')
    rows=[];transitions=[]
    protected=('claim_utility','supports_content','supports_utility','utility_match',
        'descriptive_only','secondary_supports_content_derived','secondary_supports_utility','secondary_utility_match')
    for cid,prev in old.items():
        new=adj[cid]
        r=dict(prev)
        r.update(legacy_weak_claim_content=prev['claim_content'],legacy_content_match=prev['content_match'],
            legacy_claim_text=prev['claim_text'],legacy_claim_location=prev['claim_location'],legacy_rationale=prev['rationale'],
            legacy_claim_scope=prev['claim_scope'],legacy_claim_linkage=prev['claim_linkage'],
            claim_content=new['claim_content'],claim_text=new['claim_text'],claim_location=new['claim_location'],
            rationale=new['rationale'],claim_linkage=new['linkage'],claim_scope='Dependence on the particular semantic content supplied',
            content_match=match(new['claim_content'],prev['supports_content']),
            secondary_content_match=match(new['claim_content'],prev['secondary_supports_content_derived']),
            coder_a_content=a[cid]['claim_content'],coder_b_content=b[cid]['claim_content'],
            coder_1='Strict-content A, fresh AI context',coder_2='Strict-content B, fresh AI context',
            content_adjudication_provenance='Fresh support-blind third AI; content_adjudicated.json and adjudication_ledger.json',
            utility_coding_provenance='Unchanged adjudicated v1 utility; historical coder_a_utility/coder_b_utility fields retained',
            descriptive_only_provenance='Unchanged v1 descriptive flag; a strict No can retain a substantive weak-use interpretation',
            content_indeterminate_reason='claim_ambiguous' if new['claim_content']=='Unclear' else 'support_unclear' if new['claim_content']=='Yes' and prev['supports_content']=='Unclear' else '')
        for k in protected: assert r[k]==prev[k]
        rows.append(r)
        transitions.append(dict(comparison_id=cid,study=r['study'],v1_weak_claim=prev['claim_content'],
            v2_strict_claim=r['claim_content'],original_support=r['supports_content'],v1_content_match=prev['content_match'],
            v2_content_match=r['content_match'],strict_quote=r['claim_text'],location=r['claim_location'],rationale=r['rationale']))
    csvout('COMPARISONS_STRICT_CLAIM_MATCH_V2.csv',rows);dump('COMPARISONS_STRICT_CLAIM_MATCH_V2.json',rows)
    csvout('CONTENT_V1_TO_V2_TRANSITIONS.csv',transitions)
    crosses=[]
    for axis in ('content','utility'):
        for c in LABELS:
            for s in SUPPORT:
                rs=[r for r in rows if r['claim_'+axis]==c and r['supports_'+axis]==s]
                crosses.append(dict(axis=axis,claim=c,support=s,count=len(rs),comparison_ids=';'.join(r['comparison_id'] for r in rs)))
    csvout('CLAIM_SUPPORT_CROSSTABS_V2.csv',crosses)
    studies=[]
    for study in dict.fromkeys(r['study'] for r in rows):
        sr=[r for r in rows if r['study']==study]
        studies.append(dict(study=study,comparisons=len(sr),
            strict_yes=sum(r['claim_content']=='Yes' for r in sr),
            matched=sum(r['content_match']=='Matched' for r in sr),
            mismatch=sum(r['content_match']=='Mismatch' for r in sr),
            support_indeterminate=sum(r['content_indeterminate_reason']=='support_unclear' for r in sr),
            claim_unclear=sum(r['claim_content']=='Unclear' for r in sr),
            not_claimed=sum(r['content_match']=='Not claimed' for r in sr)))
    csvout('STUDY_STRICT_CONTENT_V2.csv',studies)
    stats=load(OUT/'CONTENT_AGREEMENT_V2.json')
    summary=dict(status='complete_strict_content_recoding_files_only',comparison_count=25,study_count=9,
        strict_content_agreement=stats,source_windows_unchanged=True,utility_and_support_unchanged=True,
        manuscript_unchanged=True,ai_not_human_reliability=True,
        claim_labels=dict(Counter(r['claim_content'] for r in rows)),
        content_states={s:sum(r['content_match']==s for r in rows) for s in STATES},
        explicit_content_claims=[r['comparison_id'] for r in rows if r['claim_content']=='Yes'],
        explicit_content_states={s:sum(r['content_match']==s and r['claim_content']=='Yes' for r in rows) for s in STATES},
        content_mismatch_ids=[r['comparison_id'] for r in rows if r['content_match']=='Mismatch'],
        strict_claim_studies=[s['study'] for s in studies if s['strict_yes']],
        mismatch_studies=[s['study'] for s in studies if s['mismatch']],
        utility_states={s:sum(r['utility_match']==s for r in rows) for s in STATES},
        utility_explicit_states={s:sum(r['utility_match']==s and r['claim_utility']=='Yes' for r in rows) for s in STATES},
        content_transition_counts={f'{x}->{y}':sum(r['legacy_weak_claim_content']==x and r['claim_content']==y for r in rows) for x in LABELS for y in LABELS})
    for axis in ('content','utility'):
        assert sum(summary[axis+'_states'].values())==25
    # Independent truth-table checks rather than only calling match again.
    for r in rows:
        c,s=r['claim_content'],r['supports_content']
        expected='Not claimed' if c=='No' else 'Indeterminate' if c=='Unclear' or s=='Unclear' else 'Matched' if s=='Supported' else 'Mismatch'
        assert expected==r['content_match']
    old_summary=load(OLD/'SUMMARY_V1.json')
    assert summary['utility_states']==old_summary['utility']['all_states']
    assert summary['utility_explicit_states']==old_summary['utility']['among_explicit_claims']
    dump('SUMMARY_V2.json',summary)
    dump('VALIDATION_V2.json',dict(status='pass',quote_rows_checked=75,comparison_count=25,
        source_packet_byte_identical=sha(OUT/'packet/CLAIM_WINDOWS_MASKED_V1.json')==sha(OLD/'claim_packet/CLAIM_WINDOWS_MASKED_V1.json'),
        old_v1_files_and_manuscript_hashes_unchanged=True,utility_and_support_fields_equal_all_25=True,
        kappa_crosschecked_sklearn=True,all_match_rules_checked=True,analysis_sha256=sha(__file__)))
    lines=['# W5 strict-content recoding v2', '',
        'Only content claims were recoded. Source windows, utility claims and original support codes are unchanged. '
        'Strict No means no claim of dependence on PARTICULAR supplied semantic content; it does not deny a weaker use claim.', '',
        '| Claim | Supported | None | Unclear |','|---|---:|---:|---:|']
    for c in LABELS:
        vals=[next(x['count'] for x in crosses if x['axis']=='content' and x['claim']==c and x['support']==s) for s in SUPPORT]
        lines.append('| '+c+' | '+' | '.join(map(str,vals))+' |')
    lines += ['',f'Pre-adjudication agreement: {stats["agreements"]}/25; unweighted Cohen kappa: {stats["kappa"]}.',
        '', 'No independence-based confidence interval is claimed. Separate fresh same-model AI contexts are not human raters. '
        'Adjudication was performed before support merge. TARTE publication-version uncertainty remains unresolved.', '',
        'Utility remains: 11 explicit claims, 2 Matched, 6 Mismatch, 3 support-Indeterminate; 10 Not claimed and 4 claim-Unclear.', '',
        'The main claim_text/rationale columns now concern STRICT CONTENT ONLY. Original v1 evidence is retained in '
        'legacy_claim_text/legacy_claim_location/legacy_rationale for the unchanged utility coding. Historical utility coder '
        'columns are not results from the new content-only coders.', '', '## Comparison-level evidence','']
    for r in rows:
        lines += [f'### {r["comparison_id"]} — {r["study"]}', '',
            f'Old weak claim: {r["legacy_weak_claim_content"]}; new strict claim: {r["claim_content"]}; '
            f'original support: {r["supports_content"]}; match: {r["content_match"]}.','',
            '> '+r['claim_text'].replace('\n','\n> '),'',r['claim_location'],'',r['rationale'],'']
    (OUT/'RESULTS_V2.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='strict_content_agreement'},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['coders','finish']);args=parser.parse_args()
    if args.phase=='coders': coders()
    else: finish()
