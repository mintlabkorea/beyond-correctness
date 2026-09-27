"""Paired, overlapping-split-aware row bootstrap and automatic W2 rules."""
import argparse
import csv
import gzip
import json
from pathlib import Path
import numpy as np
from sklearn.metrics import roc_auc_score
import common as C

def category(ci,delta=.02):
    lo,hi=ci
    if lo>delta: return 'positive'
    if hi<-delta: return 'negative'
    if lo>=-delta and hi<=delta: return 'near-zero'
    return 'unresolved'

def result(point,draws):
    ci=np.quantile(draws,[.025,.975]).tolist()
    return {'estimate':float(point),'ci95':ci,'category':category(ci),
            'equivalent':ci[0]>=-.02 and ci[1]<=.02,
            'ci_excludes_zero':ci[0]>0 or ci[1]<0}

def weighted_auc(y,scores,weights):
    """Exact weighted binary AUROC, with half-credit for tied scores."""
    order=np.argsort(scores,kind='stable')
    sorted_scores=np.asarray(scores)[order]
    starts=np.r_[0,np.flatnonzero(np.diff(sorted_scores))+1]
    w=np.asarray(weights[:,order],dtype=np.float64)
    positive=np.add.reduceat(w*np.asarray(y)[order],starts,axis=1)
    negative=np.add.reduceat(w*(1-np.asarray(y)[order]),starts,axis=1)
    before=np.cumsum(negative,axis=1)-negative
    denominator=positive.sum(axis=1)*negative.sum(axis=1)
    assert (denominator>0).all(), 'bootstrap lost a class'
    return (positive*(before+.5*negative)).sum(axis=1)/denominator

def auc(y,p):
    if p.shape[1]==2: return roc_auc_score(y,p[:,1])
    return roc_auc_score(y,p,multi_class='ovr',average='macro')

def weights_for(d,union,labels,splits,B):
    rng=np.random.default_rng(20260910+C.DATASETS.index(d))
    classes=np.unique(labels)
    indices=[np.flatnonzero(labels==c) for c in classes]
    weights=np.zeros((B,len(union)),dtype=np.int16)
    positions={r:i for i,r in enumerate(union)}
    split_class_indices=[np.array([positions[r] for r in s['test'] if labels[positions[r]]==c])
                         for s in splits.values() for c in classes]
    for b in range(B):
        while True:
            for idx in indices:
                weights[b,idx]=rng.multinomial(len(idx),np.full(len(idx),1/len(idx)))
            if all(weights[b,idx].sum()>0 for idx in split_class_indices): break
    return weights

def dataset_analysis(d,shots,B):
    splits=C.read(C.RUN/'audit'/d/'memberships.json')
    union=sorted({r for s in splits.values() for r in s['test']})
    positions={r:i for i,r in enumerate(union)}
    labelmap={}
    paths={}
    hashes={}
    for cell in C.cells(shots):
        if cell[0]!=d: continue
        path=C.RUN/'evidence'/C.key(cell)
        meta=C.read(path/'metrics.json')
        assert meta['design_sha256']==C.sha(C.RUN/'FROZEN_DESIGN.json')
        assert C.sha(path/'predictions.jsonl.gz')==meta['predictions_sha256']
        hashes[C.key(cell)]=meta['predictions_sha256']
        paths[cell]=(path,meta)
    # Label union is built from shared intended predictions, with overlap checks.
    for s in C.SEEDS:
        path,_=paths[(d,shots[0],s,'intended','shared')]
        with gzip.open(path/'predictions.jsonl.gz','rt') as h:
            for p in map(json.loads,h):
                r=p['row_id']; y=p['label']
                assert r not in labelmap or labelmap[r]==y
                labelmap[r]=y
    assert sorted(labelmap)==union
    yunion=np.array([labelmap[r] for r in union])
    weights=weights_for(d,union,yunion,splits,B)
    scores={}; draws={}
    for n in shots:
        # Cache only verified aggregate draws and bind every source prediction hash.
        cache=C.RUN/'analysis_cache'/f'{d}_k{n}.npz'
        signature=C.textsha(json.dumps({k:v for k,v in hashes.items() if f'/k{n}/' in k},sort_keys=True))
        if cache.exists():
            old=np.load(cache,allow_pickle=False)
            assert str(old['signature'])==signature
            scores[n]=old['scores']; draws[n]=old['draws']
            continue
        point=np.zeros((4,24,5))
        boot=np.zeros((4,24,5,B))
        for si,s in enumerate(C.SEEDS):
            for fi,f in enumerate(('intended',)+C.FAMILIES):
                refs=('shared',) if f=='intended' else C.REFS
                for ai,a in enumerate(refs):
                    path,meta=paths[(d,n,s,f,a)]
                    with gzip.open(path/'predictions.jsonl.gz','rt') as h:
                        predictions=[json.loads(line) for line in h]
                    rows=[p['row_id'] for p in predictions]
                    assert rows==splits[str(s)]['test']
                    y=np.array([p['label'] for p in predictions])
                    assert np.array_equal(y,[labelmap[r] for r in rows])
                    p=np.array([p['class_probabilities'] for p in predictions])
                    assert np.isfinite(p).all() and (p>=0).all() and np.allclose(p.sum(1),1,atol=1e-6)
                    point[fi,ai,si]=auc(y,p)
                    assert abs(point[fi,ai,si]-meta['metrics']['auc'])<1e-12
                    indices=np.array([positions[r] for r in rows])
                    for start in range(0,B,32):
                        w=weights[start:start+32,indices]
                        if p.shape[1]==2:
                            values=weighted_auc(y,p[:,1],w)
                        else:
                            values=np.mean([weighted_auc((y==c).astype(int),p[:,c],w)
                                            for c in range(p.shape[1])],axis=0)
                        boot[fi,ai,si,start:start+32]=values
                if f=='intended':
                    point[fi,:,si]=point[fi,0,si]
                    boot[fi,:,si,:]=boot[fi,0,si,:]
        scores[n]=point; draws[n]=boot
        cache.parent.mkdir(parents=True,exist_ok=True)
        np.savez_compressed(cache,signature=signature,scores=point,draws=boot)
        print(json.dumps({'analysis_dataset':d,'n_adapt':n,'status':'complete'}),flush=True)
    return scores,draws

def adjudicate(macro,datasets):
    cats=[macro[f]['category'] for f in C.FAMILIES]
    if cats[1]!=cats[0] or cats[2]!=cats[0]: return 'C'
    if all(c=='positive' for c in cats):
        agree=sum(len({v['utility'][f]['category'] for f in C.FAMILIES})==1 for v in datasets.values())
        if macro['R2-R1']['equivalent'] and macro['R3-R1']['equivalent'] and agree>=7: return 'A'
        return 'B'
    return 'unresolved'

def main():
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=('primary','full'),required=True)
    args=p.parse_args()
    design=C.verify_freeze()
    gate=C.read(C.RUN/'AUDIT_SUMMARY.json')
    assert gate['all_pass']
    shots=(0,) if args.phase=='primary' else C.SHOTS
    B=design['bootstrap_replicates']
    point=np.zeros((9,len(shots),3));boot=np.zeros((9,len(shots),3,B))
    for di,d in enumerate(C.DATASETS):
        q,qb=dataset_analysis(d,shots,B)
        for ni,n in enumerate(shots):
            for fi in range(3):
                point[di,ni,fi]=(q[n][0]-q[n][fi+1]).mean()
                boot[di,ni,fi]=(qb[n][0]-qb[n][fi+1]).mean(axis=(0,1))
    macro_point=point.mean(axis=0);macro_boot=boot.mean(axis=0)
    datasets={}
    rows=[]
    for di,d in enumerate(C.DATASETS):
        utility={f:result(point[di,0,fi],boot[di,0,fi]) for fi,f in enumerate(C.FAMILIES)}
        shifts={f'{f}-R1':result(point[di,0,fi]-point[di,0,0],boot[di,0,fi]-boot[di,0,0])
                for fi,f in enumerate(C.FAMILIES) if fi}
        categories={v['category'] for v in utility.values()}
        if len(categories)>1: robust='reference-family sensitive'
        elif all(v['equivalent'] for v in shifts.values()): robust='reference-family robust'
        elif any(v['ci95'][0]>.02 or v['ci95'][1]<-.02 for v in shifts.values()): robust='magnitude-sensitive'
        else: robust='category agreement; magnitude unresolved'
        datasets[d]={'utility':utility,'shifts':shifts,'robustness':robust}
        for nidx,n in enumerate(shots):
            for fi,f in enumerate(C.FAMILIES):
                r=result(point[di,nidx,fi],boot[di,nidx,fi])
                rows.append({'dataset':d,'n_adapt':n,'family':f,'utility':r['estimate'],
                             'ci_low':r['ci95'][0],'ci_high':r['ci95'][1],'category':r['category']})
    macro={f:result(macro_point[0,fi],macro_boot[0,fi]) for fi,f in enumerate(C.FAMILIES)}
    macro.update({f'{f}-R1':result(macro_point[0,fi]-macro_point[0,0],macro_boot[0,fi]-macro_boot[0,0])
                  for fi,f in enumerate(C.FAMILIES) if fi})
    rng=np.random.default_rng(20260910)
    ds_indices=rng.integers(0,9,size=(10000,9))
    dsboot=point[ds_indices,0,:].mean(axis=1)
    sensitivity={f:result(macro_point[0,fi],dsboot[:,fi]) for fi,f in enumerate(C.FAMILIES)}
    sensitivity.update({f'{f}-R1':result(macro_point[0,fi]-macro_point[0,0],dsboot[:,fi]-dsboot[:,0])
                        for fi,f in enumerate(C.FAMILIES) if fi})
    secondary={}
    if len(shots)>1:
        for fi,f in enumerate(C.FAMILIES):
            secondary[f]={
                'utility_by_support':{str(n):result(macro_point[ni,fi],macro_boot[ni,fi]) for ni,n in enumerate(shots)},
                'strict_point_monotonicity':bool(np.all(np.diff(macro_point[:,fi])<0)),
                'endpoint_attenuation':result(macro_point[0,fi]-macro_point[-1,fi],macro_boot[0,fi]-macro_boot[-1,fi]),
                'adjacent_attenuation':{f'{shots[i]}-{shots[i+1]}':result(macro_point[i,fi]-macro_point[i+1,fi],
                    macro_boot[i,fi]-macro_boot[i+1,fi]) for i in range(len(shots)-1)},
                'family_by_support':{str(n):result(
                    (macro_point[0,fi]-macro_point[ni,fi])-(macro_point[0,0]-macro_point[ni,0]),
                    (macro_boot[0,fi]-macro_boot[ni,fi])-(macro_boot[0,0]-macro_boot[ni,0]))
                    for ni,n in enumerate(shots) if ni and fi}}
    out=C.RUN/('primary_analysis' if args.phase=='primary' else 'full_analysis')
    summary={'provenance':C.PROVENANCE,'design_sha256':C.sha(C.RUN/'FROZEN_DESIGN.json'),
        'phase':args.phase,'delta':.02,'bootstrap_replicates':B,
        'primary_macro':macro,'datasets':datasets,'secondary':secondary,
        'dataset_resampling_sensitivity':sensitivity,'verdict':adjudicate(macro,datasets),
        'scope':'fixed nine-dataset panel, fixed 24 assignments and five adaptation draws; pointwise intervals'}
    C.write(out/'SUMMARY.json',summary)
    with (out/'dataset_utility.csv').open('w') as h:
        writer=csv.DictWriter(h,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    np.savez_compressed(out/'paired_bootstrap.npz',point=point,bootstrap=boot,macro_point=macro_point,
                        macro_bootstrap=macro_boot,supports=shots)
    with (out/'provenance.csv').open('w') as h:
        writer=csv.writer(h);writer.writerow(['experiment','category','design_sha256','audit_sha256'])
        writer.writerow(['TabLLM W2',C.PROVENANCE,C.sha(C.RUN/'FROZEN_DESIGN.json'),C.sha(C.RUN/'AUDIT_SUMMARY.json')])
    lines=['# W2 lexical-realization result',f"Verdict: {summary['verdict']}",
           f'Phase: {args.phase}; delta=.02; paired row bootstrap B={B}.','',
           '| Contrast | Estimate | 95% CI | Category |','|---|---:|---|---|']
    for name,v in macro.items():
        lines.append(f"| {name} | {v['estimate']:+.6f} | [{v['ci95'][0]:+.6f}, {v['ci95'][1]:+.6f}] | {v['category']} |")
    lines += ['',C.PROVENANCE,'',summary['scope'],
              'Generic-label robustness does not by itself demonstrate absence of OOD effects.']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'phase':args.phase,'verdict':summary['verdict'],'status':'analysis_complete'}),flush=True)

if __name__=='__main__': main()
