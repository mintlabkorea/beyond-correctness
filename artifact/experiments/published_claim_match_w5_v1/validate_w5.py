#!/usr/bin/env python3
"""Independently validate W5 provenance, quotations, agreement and merge."""
import json
import re
from pathlib import Path

import numpy as np
from sklearn.metrics import cohen_kappa_score

import analyze_w5 as a


def normalize(text):
    text=re.sub(r'(?<=\w)-\s+(?=\w)','',text)
    return ' '.join(text.replace('\f',' ').split())


def main():
    a.verify_originals()
    units=a.keyed(a.OUT/'UNITS_V1.json')
    packets=a.keyed(a.OUT/'claim_packet/CLAIM_WINDOWS_MASKED_V1.json')
    raw_a=a.keyed(a.OUT/'coder_a_raw.json')
    raw_b=a.keyed(a.OUT/'coder_b_raw.json')
    adj=a.keyed(a.OUT/'claims_adjudicated.json')
    merged=a.keyed(a.OUT/'COMPARISONS_CLAIM_MATCH_V1.json')
    quote_checks=[]
    for name,records in [('A',raw_a),('B',raw_b),('adjudicated',adj)]:
        for cid,r in records.items():
            text='\n'.join(w['text'] for w in packets[cid]['windows'])
            # Coders delimit multiple literal extracts with a vertical bar.
            pieces=[s.strip().strip('“”"') for s in r['claim_text'].split(' | ')]
            for quote in pieces:
                assert normalize(quote) in normalize(text),(name,cid,quote)
            assert cid+'-W' in r['claim_location'],(name,cid,'window location missing')
            assert r['claim_content'] in a.LABELS and r['claim_utility'] in a.LABELS
            assert r['descriptive_only'] in ('Yes','No')
            quote_checks.append(dict(coder=name,comparison_id=cid,quote_count=len(pieces),verified=True))
    kappa_checks=[]
    rel=a.load(a.OUT/'CLAIM_AGREEMENT_V1.json')
    for field in a.AXES:
        x=[raw_a[k][field] for k in units];y=[raw_b[k][field] for k in units]
        labels=list(a.LABELS if field!='descriptive_only' else ('Yes','No'))
        if rel[field]['kappa'] is None:
            assert len(set(x+y))==1
        else:
            expected=float(cohen_kappa_score(x,y,labels=labels))
            np.testing.assert_allclose(rel[field]['kappa'],expected,atol=1e-14)
        assert rel[field]['agreements']==sum(xx==yy for xx,yy in zip(x,y))
        kappa_checks.append(field)
    for cid,row in merged.items():
        for axis in ('content','utility'):
            claim=row['claim_'+axis];support=row['supports_'+axis]
            expected=('Not claimed' if claim=='No' else 'Indeterminate' if claim=='Unclear' or support=='Unclear' else 'Matched' if support=='Supported' else 'Mismatch')
            assert row[axis+'_match']==expected
            if row[axis+'_match']=='Mismatch':
                assert claim=='Yes' and support=='None'
            assert claim==adj[cid]['claim_'+axis]
        assert row['study']==units[cid]['study']
    summary=a.load(a.OUT/'SUMMARY_V1.json')
    assert summary['comparison_count']==25 and summary['study_count']==9
    for axis in ('content','utility'):
        assert sum(summary[axis]['all_states'].values())==25
        assert sum(summary[axis]['among_explicit_claims'].values())==summary[axis]['explicit_claim_count']
    for freeze_name in ('CODER_RAW_FREEZE_V1.json','ADJUDICATION_FREEZE_V1.json'):
        for path,expected in a.load(a.OUT/freeze_name)['files'].items():
            assert a.digest(a.OUT/path)==expected
    original=[]
    for path,h in a.load(a.OUT/'PRE_EXTRACTION_FREEZE_V1.json')['files'].items():
        if path.endswith('.tex'):
            assert a.digest(a.ROOT/path)==h
            original.append(path)
    a.write_json('VALIDATION_V1.json',dict(status='pass',comparison_count=25,study_count=9,
        quote_rows_checked=len(quote_checks),quote_checks=quote_checks,kappa_sklearn_checks=kappa_checks,
        original_manuscripts_unchanged=original,all_original_support_hashes_unchanged=True,
        all_match_transitions_verified=True,validator_sha256=a.digest(__file__)))
    print('PASS: 75 quoted coder/adjudicated rows; kappa; 50 match transitions; original support and manuscript hashes')


if __name__=='__main__':
    main()
