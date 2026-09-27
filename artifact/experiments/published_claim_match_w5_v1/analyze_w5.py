#!/usr/bin/env python3
"""Compute frozen W5 agreement and deterministic claim/control cross-tabs."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
AUDIT = ROOT / 'iclr_latex_v3/design_audit'
AXES = ('claim_content', 'claim_utility', 'descriptive_only')
LABELS = ('Yes', 'No', 'Unclear')
SUPPORT = ('Supported', 'None', 'Unclear')
STATES = ('Matched', 'Mismatch', 'Indeterminate', 'Not claimed')


def load(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(name, data):
    (OUT/name).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def write_csv(name, rows):
    with (OUT/name).open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def keyed(path, key='comparison_id'):
    rows = load(path)
    assert isinstance(rows, list) and len(rows) == 25
    d = {r[key]:r for r in rows}
    assert len(d) == 25
    assert set(d) == {u['comparison_id'] for u in load(OUT/'UNITS_V1.json')}
    return d


def verify_originals():
    freeze = load(OUT/'PRE_EXTRACTION_FREEZE_V1.json')
    for path, expected in freeze['files'].items():
        assert digest(ROOT/path) == expected, f'Changed original/frozen file: {path}'
    packet = load(OUT/'CLAIM_PACKET_FREEZE_V1.json')
    for name, expected in packet['packet_hashes'].items():
        assert digest(OUT/'claim_packet'/name) == expected
    for path, expected in packet['source_text_hashes'].items():
        assert digest(ROOT/path) == expected


def agreement(a, b, labels):
    assert len(a) == len(b) and set(a+b) <= set(labels)
    n = len(a)
    counts_a, counts_b = Counter(a), Counter(b)
    agree = sum(x==y for x,y in zip(a,b))
    po = agree/n
    pe = sum(counts_a[x]*counts_b[x] for x in labels)/(n*n)
    kappa = (po-pe)/(1-pe) if pe < 1 else None
    return dict(n=n, agreements=agree, raw_agreement=po, expected_agreement=pe, kappa=kappa,
        marginal_a={x:counts_a[x] for x in labels}, marginal_b={x:counts_b[x] for x in labels},
        confusion=[dict(coder_a=x,coder_b=y,count=sum(v==x and w==y for v,w in zip(a,b))) for x in labels for y in labels])


def match(claim, support):
    assert claim in LABELS and support in SUPPORT
    if claim == 'No':
        return 'Not claimed'
    if claim == 'Unclear':
        return 'Indeterminate'
    return {'Supported':'Matched','None':'Mismatch','Unclear':'Indeterminate'}[support]


def checks():
    # Cross-check actual kappa formula with sklearn, including degenerate cases.
    import math
    from sklearn.metrics import cohen_kappa_score
    a=['Yes','Yes','No','Unclear','No','Yes']
    b=['Yes','No','No','Unclear','Yes','Unclear']
    assert math.isclose(agreement(a,b,LABELS)['kappa'],cohen_kappa_score(a,b,labels=list(LABELS)),abs_tol=1e-14)
    assert agreement(['No']*25,['No']*25,LABELS)['kappa'] is None
    expected={('Yes','Supported'):'Matched',('Yes','None'):'Mismatch',('Yes','Unclear'):'Indeterminate'}
    for c in LABELS:
        for s in SUPPORT:
            assert match(c,s)==('Not claimed' if c=='No' else 'Indeterminate' if c=='Unclear' else expected[(c,s)])


def claims():
    verify_originals()
    a,b=keyed(OUT/'coder_a_raw.json'),keyed(OUT/'coder_b_raw.json')
    keys=list(a)
    for rows in (a,b):
        for r in rows.values():
            assert r['claim_content'] in LABELS and r['claim_utility'] in LABELS
            assert r['descriptive_only'] in ('Yes','No')
            assert r['claim_text'] and r['claim_location'] and r['rationale']
            if r['descriptive_only']=='Yes':
                assert r['claim_content']==r['claim_utility']=='No'
    paths=[OUT/f'coder_{c}_{s}.json' for c in ('a','b') for s in ('raw','boundary')]
    freeze=dict(time_utc=datetime.now(timezone.utc).isoformat(),files={p.name:digest(p) for p in paths},
                packet_freeze_sha256=digest(OUT/'CLAIM_PACKET_FREEZE_V1.json'))
    frozen=OUT/'CODER_RAW_FREEZE_V1.json'
    if frozen.exists():
        for p,expected in load(frozen)['files'].items():
            assert digest(OUT/p)==expected
    else:
        write_json(frozen.name,freeze)
    reliabilities={axis:agreement([a[k][axis] for k in keys],[b[k][axis] for k in keys],LABELS if axis!='descriptive_only' else ('Yes','No')) for axis in AXES}
    write_json('CLAIM_AGREEMENT_V1.json',reliabilities)
    write_csv('CLAIM_AGREEMENT_V1.csv',[dict(field=k,**{z:v[z] for z in ('n','agreements','raw_agreement','expected_agreement','kappa')}) for k,v in reliabilities.items()])
    write_csv('CLAIM_CONFUSION_V1.csv',[dict(field=k,**row) for k,v in reliabilities.items() for row in v['confusion']])
    differences=[]
    for k in keys:
        for field in AXES:
            if a[k][field]!=b[k][field]:
                differences.append(dict(comparison_id=k,study=a[k]['study'],field=field,coder_a=a[k][field],coder_b=b[k][field],rationale_a=a[k]['rationale'],rationale_b=b[k]['rationale']))
    if differences:
        write_csv('CLAIM_DISAGREEMENTS_RAW_V1.csv',differences)
    write_json('CLAIM_DISAGREEMENTS_RAW_V1.json',differences)
    print(json.dumps({k:{f:v[f] for f in ('n','agreements','kappa')} for k,v in reliabilities.items()},indent=2))


def support_rows():
    primary=keyed(AUDIT/'phase_c_v1/CLAIM_IDENTIFICATION_V1.json','Comparison ID')
    secondary=keyed(AUDIT/'second_coder_v1/independent/CODES_SECOND_V1.json','Comparison ID')
    m={'Yes':'Supported','No':'None','Partial':'Unclear','Unclear':'Unclear'}
    rows=[]
    for cid,p in primary.items():
        s=secondary[cid]
        # Historical second coder recorded gates, not a standalone content code.
        # Apply the original unchanged derivation under shared Wrong-like labels.
        sc=('Yes' if all(s[g]['value']=='Pass' for g in ('Preservation','Interface')) else 'Partial') if p['Wrong-like']['value']=='Yes' else 'No'
        rows.append(dict(comparison_id=cid,study=p['Study'],
            supports_content=m[p['Content sensitivity identifiable']['value']],
            supports_utility=m[p['Predictive utility identifiable']['value']],
            secondary_supports_content_derived=m[sc],
            secondary_supports_utility=m[s['Admissible reference']['value']],
            primary_scope=p['Tested semantic use'],secondary_scope=s['Tested semantic use'],
            primary_preservation=p['Preservation']['value'],secondary_preservation=s['Preservation']['value'],
            primary_interface=p['Interface']['value'],secondary_interface=s['Interface']['value']))
    return rows,primary,secondary


def merge():
    verify_originals()
    for p,h in load(OUT/'CODER_RAW_FREEZE_V1.json')['files'].items():
        assert digest(OUT/p)==h
    freeze=load(OUT/'ADJUDICATION_FREEZE_V1.json')
    for p,h in freeze['files'].items():
        assert digest(OUT/p)==h
    adjudicated=keyed(OUT/'claims_adjudicated.json')
    a,b=keyed(OUT/'coder_a_raw.json'),keyed(OUT/'coder_b_raw.json')
    units=keyed(OUT/'UNITS_V1.json')
    sups,primary,secondary=support_rows()
    sup={s['comparison_id']:s for s in sups}
    write_csv('SUPPORT_PRIMARY_SECONDARY_V1.csv',sups)
    historical={}
    for name,one,two,labels in [
        ('utility_support_historical',[s['supports_utility'] for s in sups],[s['secondary_supports_utility'] for s in sups],SUPPORT),
        ('content_support_historical_derived',[s['supports_content'] for s in sups],[s['secondary_supports_content_derived'] for s in sups],SUPPORT)]:
        historical[name]=agreement(one,two,labels)
    for gate in ('Removal','Preservation','Interface'):
        historical['gate_'+gate]=agreement([primary[k][gate]['value'] for k in units],[secondary[k][gate]['value'] for k in units],('Pass','Fail','Unclear'))
    write_json('SUPPORT_AGREEMENT_HISTORICAL_V1.json',historical)
    write_csv('SUPPORT_AGREEMENT_HISTORICAL_V1.csv',[dict(field=k,**{z:v[z] for z in ('n','agreements','raw_agreement','expected_agreement','kappa')}) for k,v in historical.items()])
    merged=[]
    for cid,u in units.items():
        r=adjudicated[cid];s=sup[cid]
        row=dict(study=u['study'],comparison_id=cid,paper_section=u['location_hint'],
            compared_conditions=u['intended']+' vs '+u['comparator'],semantic_component=u['semantic_component'],
            claim_text=r['claim_text'],claim_location=r['claim_location'],
            claim_content=r['claim_content'],claim_utility=r['claim_utility'],descriptive_only=r['descriptive_only'],
            supports_content=s['supports_content'],supports_utility=s['supports_utility'],
            content_match=match(r['claim_content'],s['supports_content']),utility_match=match(r['claim_utility'],s['supports_utility']),
            rationale=r['rationale'],coder_1='A (separate AI context)',coder_2='B (separate AI context)',adjudicated='Yes',
            coder_a_content=a[cid]['claim_content'],coder_b_content=b[cid]['claim_content'],
            coder_a_utility=a[cid]['claim_utility'],coder_b_utility=b[cid]['claim_utility'],
            coder_a_descriptive_only=a[cid]['descriptive_only'],coder_b_descriptive_only=b[cid]['descriptive_only'],
            claim_scope=r.get('claim_scope',''),claim_linkage=r.get('linkage',''),
            source_version_status='unverified_preacceptance_mirror' if cid.startswith('C10') else 'archived_publication',
            content_indeterminate_reason='claim_ambiguous' if r['claim_content']=='Unclear' else 'support_unclear' if r['claim_content']=='Yes' and s['supports_content']=='Unclear' else '',
            utility_indeterminate_reason='claim_ambiguous' if r['claim_utility']=='Unclear' else 'support_unclear' if r['claim_utility']=='Yes' and s['supports_utility']=='Unclear' else '',
            secondary_supports_content_derived=s['secondary_supports_content_derived'],secondary_supports_utility=s['secondary_supports_utility'],
            secondary_content_match=match(r['claim_content'],s['secondary_supports_content_derived']),
            secondary_utility_match=match(r['claim_utility'],s['secondary_supports_utility']))
        merged.append(row)
    write_csv('COMPARISONS_CLAIM_MATCH_V1.csv',merged)
    write_json('COMPARISONS_CLAIM_MATCH_V1.json',merged)
    crosses=[];summary={}
    for axis in ('content','utility'):
        for c in LABELS:
            for s in SUPPORT:
                selected=[r for r in merged if r['claim_'+axis]==c and r['supports_'+axis]==s]
                crosses.append(dict(axis=axis,reported_claim=c,control_support=s,count=len(selected),comparison_ids=';'.join(r['comparison_id'] for r in selected)))
        claims_yes=[r for r in merged if r['claim_'+axis]=='Yes']
        summary[axis]=dict(all_comparison_count=25,explicit_claim_count=len(claims_yes),
            explicit_claim_study_count=len({r['study'] for r in claims_yes}),
            claim_labels=dict(Counter(r['claim_'+axis] for r in merged)),
            all_states={state:sum(r[axis+'_match']==state for r in merged) for state in STATES},
            among_explicit_claims={state:sum(r[axis+'_match']==state for r in claims_yes) for state in STATES},
            mismatch_ids=[r['comparison_id'] for r in merged if r[axis+'_match']=='Mismatch'],
            mismatch_studies=sorted({r['study'] for r in merged if r[axis+'_match']=='Mismatch'}),
            secondary_among_explicit_claims={state:sum(r['secondary_'+axis+'_match']==state for r in claims_yes) for state in STATES})
    write_csv('CLAIM_SUPPORT_CROSSTABS_V1.csv',crosses)
    study_rows=[]
    for study in dict.fromkeys(r['study'] for r in merged):
        rs=[r for r in merged if r['study']==study]
        row=dict(study=study,comparison_count=len(rs))
        for axis in ('content','utility'):
            row[axis+'_claim_yes']=sum(r['claim_'+axis]=='Yes' for r in rs)
            for state in STATES:
                row[axis+'_'+state.replace(' ','_').lower()]=sum(r[axis+'_match']==state for r in rs)
        study_rows.append(row)
    write_csv('STUDY_CLAIM_MATCH_V1.csv',study_rows)
    summary.update(status='complete_files_only',comparison_count=25,study_count=9,
        claim_agreement=load(OUT/'CLAIM_AGREEMENT_V1.json'),historical_support_agreement=historical,
        adjudication_freeze_sha256=digest(OUT/'ADJUDICATION_FREEZE_V1.json'),
        manuscript_unchanged=True,any_axis_mismatch_count=sum(r['content_match']=='Mismatch' or r['utility_match']=='Mismatch' for r in merged),
        ai_not_human_reliability=True,source_version_unverified_ids=['C10-A','C10-B'])
    write_json('SUMMARY_V1.json',summary)
    lines=['# Claim-matched audit: computed results', '',
        'Fixed 25 comparisons / nine studies. Original support codes are unchanged. '
        'Mismatch means an explicit author claim paired with support=None under the frozen framework; '
        'it is not a paper-quality score or proof the substantive scientific claim is false.', '',
        '| Axis | Explicit claims | Matched | Mismatch | Support indeterminate | Not claimed | Claim unclear |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for axis in ('content','utility'):
        s=summary[axis];v=s['among_explicit_claims']
        lines.append(f'| {axis} | {s["explicit_claim_count"]} | {v["Matched"]} | {v["Mismatch"]} | {v["Indeterminate"]} | {s["claim_labels"].get("No",0)} | {s["claim_labels"].get("Unclear",0)} |')
    lines += ['', '## Pre-adjudication reported-claim agreement', '', '| Axis | Exact agreement | Cohen kappa |','|---|---:|---:|']
    for axis,s in summary['claim_agreement'].items():
        lines.append(f'| {axis} | {s["agreements"]}/{s["n"]} ({100*s["raw_agreement"]:.1f}%) | {s["kappa"] if s["kappa"] is not None else "undefined"} |')
    for axis in ('content','utility'):
        lines += ['', f'## {axis}: reported claim × original control support', '', '| Claim | Supported | None | Unclear |','|---|---:|---:|---:|']
        for c in LABELS:
            counts=[next(x['count'] for x in crosses if x['axis']==axis and x['reported_claim']==c and x['control_support']==s) for s in SUPPORT]
            lines.append('| '+c+' | '+' | '.join(map(str,counts))+' |')
    lines += ['', '## Reliability limits', '',
        'Claim coding uses two fresh same-model AI contexts and one common masked packet. '
        'This is AI reproducibility, not human inter-rater reliability. Numeric magnitudes and original support labels '
        'were withheld; qualitative result language was necessarily visible. Source extraction was not blinded. '
        'The read boundary was instructional. Kappa is unweighted with label marginals retained; '
        'no comparison-independence confidence intervals are reported. '
        'See [Cohen (1960)](https://doi.org/10.1177/001316446002000104) for the nominal-agreement coefficient.', '',
        'Historical support reliability reuses previously frozen primary/second AI gates, with differing declared scopes. '
        'The historical second coder did not supply a standalone content-support label: that column is deterministically '
        'derived from its Preservation/Interface gates and the shared original Wrong-like intervention classification. '
        'Do not present its kappa as a new independently coded content rating. '
        'TARTE remains a preacceptance-mirror source limitation, not a source-verified published-claim determination.', '',
        '## Every comparison and its evidence', '']
    for r in merged:
        lines += [f'### {r["comparison_id"]} — {r["study"]}', '',r['compared_conditions'],'',
            '> '+r['claim_text'].replace('\n','\n> '),'',r['claim_location'],'',
            f'Claim content / utility: {r["claim_content"]} / {r["claim_utility"]}. '
            f'Original support: {r["supports_content"]} / {r["supports_utility"]}. '
            f'Match: {r["content_match"]} / {r["utility_match"]}.', '',r['rationale'],'']
    (OUT/'RESULTS_V1.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({axis:summary[axis] for axis in ('content','utility')},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=['self-test','claims','merge'])
    args=parser.parse_args()
    if args.phase=='self-test':
        checks(); print('PASS: kappa against sklearn, degenerate kappa, all nine match transitions')
    elif args.phase=='claims':
        claims()
    else:
        merge()
