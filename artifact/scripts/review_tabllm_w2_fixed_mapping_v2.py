"""Read-only review of frozen W2 evidence; writes separate review artifacts."""
import collections
import concurrent.futures
import gzip
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from sklearn.metrics import roc_auc_score

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/tabllm_w2_fixed_mapping'))
import common as C
import analyze as A
RUN=C.RUN
OUT=RUN/'review_20260913'

def records(path):
    with gzip.open(path,'rt') as h:
        return [json.loads(line) for line in h]

def review_dataset(d):
    gate=C.read(RUN/'AUDIT_SUMMARY.json')
    design=C.read(RUN/'FROZEN_DESIGN.json')
    design_sha=C.sha(RUN/'FROZEN_DESIGN.json')
    audit_sha=C.sha(RUN/'AUDIT_SUMMARY.json')
    audit={}
    for f in ('intended',)+C.FAMILIES:
        a='shared' if f=='intended' else 'ref_00'
        path=C.audit_path(d,f,a)
        assert C.sha(path)==gate['datasets'][d]['arms'][f'{f}/{a}']['sha256']
        audit[f]={p['row_id']:p for p in records(path)}
    split=C.read(RUN/'audit'/d/'memberships.json')
    assert C.sha(RUN/'audit'/d/'memberships.json')==gate['datasets'][d]['memberships_sha256']
    caches={n:np.load(RUN/'analysis_cache'/f'{d}_k{n}.npz') for n in C.SHOTS}
    result={'dataset':d,'cells':0,'prediction_rows':0,'reused':0,'max_auc_error':0.0,
            'bootstrap_checks':0,'max_bootstrap_error':0.0,'scores':[]}
    labels={};zero={};sample={}
    prediction_hashes={}
    for cell in C.cells():
        if cell[0]!=d:continue
        _,n,s,f,a=cell
        path=RUN/'evidence'/C.key(cell)
        meta=C.read(path/'metrics.json')
        assert meta['cell']==list(cell)
        assert meta['design_sha256']==design_sha and meta['audit_sha256']==audit_sha
        assert meta['checkpoint_sha256']==design['checkpoint_sha256']
        assert meta['split_sha256']==design['split_sha256'] and meta['model_files']==design['model_files']
        assert meta['predictions_sha256']==C.sha(path/'predictions.jsonl.gz')
        prediction_hashes[C.key(cell)]=meta['predictions_sha256']
        assert meta['test_membership']==split[str(s)]['test']
        assert meta['train_membership']==split[str(s)]['support'][str(n)]
        assert not set(meta['test_membership']).intersection(meta['train_membership'])
        trainmeta=meta['original_provenance'] if 'reused_from' in meta else meta
        assert trainmeta['training']['executed_steps']==30*(n//4)
        values=records(path/'predictions.jsonl.gz')
        assert [p['row_id'] for p in values]==meta['test_membership']
        for p in values:
            r=p['row_id']
            assert all(p[k]==v for k,v in audit[f][r].items())
            assert p['n_adapt']==n and p['seed']==s and p['family']==f and p['assignment']==a
            assert not p['truncated']
            assert r not in labels or labels[r]==p['label']
            labels[r]=p['label']
        probs=np.array([p['class_probabilities'] for p in values])
        y=np.array([p['label'] for p in values])
        assert np.isfinite(probs).all() and (probs>=0).all() and (probs<=1).all()
        assert np.allclose(probs.sum(1),1,atol=1e-6)
        score=A.auc(y,probs)
        err=abs(score-meta['metrics']['auc'])
        assert err<1e-12
        fi=('intended',)+C.FAMILIES
        assert abs(score-caches[n]['scores'][fi.index(f),0,C.SEEDS.index(s)])<1e-12
        result['max_auc_error']=max(result['max_auc_error'],err)
        result['cells']+=1;result['prediction_rows']+=len(values)
        result['reused']+=int('reused_from' in meta)
        result['scores'].append({'support':n,'seed':s,'family':f,'auc':score})
        if s==42:sample[(n,f)]=(np.array(meta['test_membership']),y,probs)
        if n==0:
            for p in values:zero.setdefault((f,p['row_id']),[]).append(p['class_probabilities'])
    for n,cache in caches.items():
        signature=C.textsha(json.dumps({k:v for k,v in prediction_hashes.items() if f'/k{n}/' in k},sort_keys=True))
        assert str(cache['signature'])==signature
    result['zero_shot_max_cross_split_probability_range']=max(
        float(np.ptp(np.array(v),axis=0).max()) for v in zero.values())
    union=sorted(labels);positions={r:i for i,r in enumerate(union)}
    weights=A.weights_for(d,union,np.array([labels[r] for r in union]),split,2000)
    for (n,f),(rows,y,p) in sample.items():
        for bi in (0,999,1999):
            w=weights[bi,[positions[r] for r in rows]]
            score=roc_auc_score(y,p[:,1],sample_weight=w) if p.shape[1]==2 else roc_auc_score(
                y,p,multi_class='ovr',average='macro',sample_weight=w)
            saved=caches[n]['draws'][(('intended',)+C.FAMILIES).index(f),0,0,bi]
            err=abs(score-saved)
            assert err<1e-12
            result['bootstrap_checks']+=1
            result['max_bootstrap_error']=max(result['max_bootstrap_error'],err)
    return result

def main():
    design=C.read(RUN/'FROZEN_DESIGN.json')
    assert all(C.sha(ROOT/path)==digest for path,digest in design['files'].items())
    gate=C.read(RUN/'AUDIT_SUMMARY.json')
    assert gate['all_pass'] and gate['design_sha256']==C.sha(RUN/'FROZEN_DESIGN.json')
    assert all(C.sha(RUN/'audit'/d/'COMPLETE.json')==digest for d,digest in gate['dataset_audit_sha256'].items())
    assert {str(p.parent.relative_to(RUN/'evidence')) for p in (RUN/'evidence').rglob('metrics.json')}=={C.key(c) for c in C.cells()}
    with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
        results=list(pool.map(review_dataset,C.DATASETS))
    summary=C.read(RUN/'full_analysis/SUMMARY.json')
    points=np.array([[[np.mean([x['auc'] for x in r['scores'] if x['support']==n and x['family']=='intended'])-
        np.mean([x['auc'] for x in r['scores'] if x['support']==n and x['family']==f]) for f in C.FAMILIES]
        for n in C.SHOTS] for r in results])
    saved=np.load(RUN/'full_analysis/paired_bootstrap.npz')
    np.testing.assert_allclose(points,saved['point'],atol=1e-12,rtol=0)
    for ni,n in enumerate(C.SHOTS):
        for fi,f in enumerate(C.FAMILIES):
            estimate=points[:,ni,fi].mean()
            assert abs(estimate-summary['secondary'][f]['utility_by_support'][str(n)]['estimate'])<1e-12
    assert A.adjudicate(summary['primary_macro'],summary['datasets'])==summary['primary_verdict']
    assert A.adjudicate_full(summary['primary_verdict'],summary['primary_macro'],summary['secondary'])==summary['final_verdict']
    old=C.read(ROOT/'experiments/tabllm_generic_lexical_zero_v1/SUMMARY_V1.json')
    report={'status':'PASS','cells':sum(r['cells'] for r in results),
        'prediction_rows':sum(r['prediction_rows'] for r in results),'reused':sum(r['reused'] for r in results),
        'max_auc_error':max(r['max_auc_error'] for r in results),
        'real_bootstrap_checks':sum(r['bootstrap_checks'] for r in results),
        'max_bootstrap_error':max(r['max_bootstrap_error'] for r in results),
        'design_sha256':C.sha(RUN/'FROZEN_DESIGN.json'),'final_summary_sha256':C.sha(RUN/'full_analysis/SUMMARY.json'),
        'r1_macro_shift_from_previous_zero_shot':points[:,0,0].mean()-old['macro']['u_anonymous'],
        'per_dataset':results,
        'limitations':'Trained checkpoint files and raw model/data files remain remote. Verified their manifest linkage here, not their remote bytes.'}
    C.write(OUT/'VALIDATION.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='per_dataset'}))

if __name__=='__main__':main()
