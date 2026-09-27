"""Resumable W2 cells, using the unchanged frozen IA3 math and sampling."""
import argparse
import datetime
import fcntl
import gzip
import json
import os
import time
from pathlib import Path
import common as C

def load_predictions(path):
    with gzip.open(path,'rt') as h:
        return [json.loads(line) for line in h]

def try_reuse(cell, audit, memberships, design, b, t, frame, manifest):
    d,n,s,f,a=cell
    candidates=[]
    home=Path('external')
    if f=='intended' or (f=='R1' and a=='ref_00'):
        arm='list_template' if f=='intended' else 'list_stable_anonymous'
        candidates.append(home/'tabllm_ranon_support_ladder_v1/evidence_v1'/arm/d/f'k{n}'/f'seed{s}')
    if f=='R1' and a in ('ref_04','ref_22') and n:
        candidates.append(home/'tabllm_reference_envelope_support_ladder_v1/evidence_v1'/a/d/f'k{n}'/f'seed{s}')
    if f=='R1' and n==512 and a not in ('ref_00','ref_04','ref_22'):
        candidates.append(home/'tabllm_all_reference_k512_v1/evidence_v1'/a/d/f'k{n}'/f'seed{s}')
    for source in candidates:
        if not (source/'metrics.json').exists():
            continue
        meta=C.read(source/'metrics.json')
        if meta.get('base_runner_sha256',meta.get('runner_sha256')) != C.sha(Path(__file__).with_name('frozen_base.py')):
            continue
        if Path(meta.get('model_path','/nonexistent')) != C.MODEL:
            continue
        expected={
            'raw_and_serialization_tree_sha256':design['raw_and_serialization_tree_sha256'],
            'versions':design['versions'],
            'ia3_checkpoint_sha256':design['checkpoint_sha256'],
            'split_manifest_sha256':design['split_sha256'],
            'train_membership_row_ids_sha256':b.sha256_ints(memberships['support'][str(n)]),
            'test_row_ids_sha256':b.sha256_ints(memberships['test']),
        }
        if any(meta.get(k)!=v for k,v in expected.items()):
            continue
        contract=meta.get('training_contract',{})
        if any(contract.get(k)!=v for k,v in {
            'epochs':30,'batch_size':4,'lr':.003,'max_length':1024,
            'loss':'lm + multiple_choice + unlikely','length_norm':1}.items()):
            continue
        if meta.get('analysis_status','').startswith('engineering'):
            continue
        if meta.get('training',{}).get('executed_steps') != 30*(n//4):
            continue
        path=source/'predictions.jsonl.gz'
        if not path.exists() or C.sha(path)!=meta['predictions_sha256']:
            continue
        predictions=load_predictions(path)
        if [p['row_id'] for p in predictions]!=memberships['test']:
            continue
        if any(p['prompt_sha256']!=audit[p['row_id']]['prompt_sha256'] for p in predictions):
            continue
        train_rows=memberships['support'][str(n)]
        template=C.template_for(t,d,f,a,manifest)
        train_notes=C.notes(t,[row for _,row in frame.loc[train_rows].iterrows()],d,template)
        train_prompts=[note+'\n\n'+b.QUESTIONS[d] for note in train_notes]
        assert all(C.textsha(p)==audit[r]['prompt_sha256'] for r,p in zip(train_rows,train_prompts))
        if meta.get('train_prompt_sha256')!=b.sha256_strings(train_prompts):
            continue
        # A reused cell's original executable, data and checkpoints stay accessible.
        return predictions,{'reused_from':str(source),'source_metrics_sha256':C.sha(source/'metrics.json'),
                            'source_predictions_sha256':C.sha(path),'original_provenance':meta}
    return None

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--gpu',type=int,required=True,choices=(0,2,3))
    parser.add_argument('--phase',choices=('primary','secondary'),required=True)
    args=parser.parse_args()
    design=C.verify_freeze()
    gate=C.read(C.RUN/'AUDIT_SUMMARY.json')
    assert gate['design_sha256']==C.sha(C.RUN/'FROZEN_DESIGN.json')
    assert gate['all_pass'], 'full-panel admissibility failed; no outcome scoring'
    for d,digest in gate['dataset_audit_sha256'].items():
        assert C.sha(C.RUN/'audit'/d/'COMPLETE.json')==digest
    if args.phase=='secondary':
        assert all((C.RUN/'evidence'/C.key(cell)/'metrics.json').exists() for cell in C.cells((0,)))
    b,t,m=C.base(),C.tabllm(),C.manifest()
    import numpy as np
    import torch
    assert torch.cuda.is_available()
    device=f'cuda:{args.gpu}'
    tokenizer=model=initial=None
    frames={}
    last_note_key=None
    note_map=None
    shots=(0,) if args.phase=='primary' else (4,32,512)
    for cell in C.cells(shots):
        d,n,s,f,a=cell
        dest=C.RUN/'evidence'/C.key(cell)
        dest.mkdir(parents=True,exist_ok=True)
        with (dest/'worker.lock').open('a') as lock:
            try:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if (dest/'metrics.json').exists():
                meta=C.read(dest/'metrics.json')
                assert meta['design_sha256']==C.sha(C.RUN/'FROZEN_DESIGN.json')
                assert meta['predictions_sha256']==C.sha(dest/'predictions.jsonl.gz')
                continue
            started=time.monotonic()
            audit=C.audit_rows(d,f,a)
            arm_audit=gate['datasets'][d]['arms'][f'{f}/{a}']
            assert C.sha(C.audit_path(d,f,a))==arm_audit['sha256']
            split=C.read(C.RUN/'audit'/d/'memberships.json')[str(s)]
            assert C.sha(C.RUN/'audit'/d/'memberships.json')==gate['datasets'][d]['memberships_sha256']
            if d not in frames:
                frames[d]=b.build_full_dataset(t,C.TABLLM,d)
            frame=frames[d]
            reused=try_reuse(cell,audit,split,design,b,t,frame,m)
            if reused:
                predictions,extra=reused
            else:
                if model is None:
                    # Verify model and source hashes before the first model load.
                    for name,digest in design['model_files'].items():
                        assert C.sha(C.MODEL/name)==digest, f'changed model file: {name}'
                    for path,digest in design['source_files'].items():
                        assert C.sha(path)==digest, f'changed model/data source: {path}'
                    tokenizer,model,initial,model_audit=b.load_model(C.MODEL,C.TFEW,C.CHECKPOINT,device)
                if last_note_key!=(d,f,a):
                    rows=sorted(audit)
                    template=C.template_for(t,d,f,a,m)
                    assert C.textsha(template)==arm_audit['template_sha256']
                    strings=C.notes(t,[row for _,row in frame.loc[rows].iterrows()],d,template)
                    note_map={r:note+'\n\n'+b.QUESTIONS[d] for r,note in zip(rows,strings)}
                    assert all(C.textsha(note_map[r])==audit[r]['prompt_sha256'] for r in rows)
                    last_note_key=(d,f,a)
                reset=b.reset_trainable_state(model,initial)
                train_rows=split['support'][str(n)]
                train=b.PreparedTrainDataset(tokenizer,[note_map[r] for r in train_rows],
                    frame.loc[train_rows,'label'].astype(int).tolist(),b.CHOICES[d],train_rows)
                training=b.train_cell(model,tokenizer,train,s,n,device,0)
                test_rows=split['test']
                with b.temporary_bfloat16_trainable_state(model):
                    probabilities=b.score_texts(tokenizer,model,[note_map[r] for r in test_rows],
                                               b.CHOICES[d],16,device)
                predictions=[{'row_id':r,'label':int(frame.loc[r,'label']),
                    'class_probabilities':probabilities[i].tolist()} for i,r in enumerate(test_rows)]
                checkpoint_hash=b.save_checkpoint(dest/'ia3_finish.pt',model)
                extra={'training':training,'model_audit':model_audit,
                       'initial_trainable_state_sha256':reset,'trained_checkpoint_sha256':checkpoint_hash}
            for p in predictions:
                r=p['row_id']
                assert p['label']==int(frame.loc[r,'label'])
                p.update(audit[r])
                p.update({'dataset':d,'n_adapt':n,'seed':s,'family':f,'assignment':a})
            probs=np.array([p['class_probabilities'] for p in predictions])
            assert np.isfinite(probs).all() and (probs>=0).all()
            assert np.allclose(probs.sum(axis=1),1,atol=1e-6)
            assert probs.shape==(len(split['test']),len(b.CHOICES[d]))
            metrics=b.compute_metrics(np.array([p['label'] for p in predictions]),probs)
            path=dest/'predictions.jsonl.gz'
            tmp=dest/'predictions.tmp.gz'
            with gzip.open(tmp,'wt') as h:
                for p in predictions:
                    h.write(json.dumps(p,sort_keys=True)+'\n')
            os.replace(tmp,path)
            C.write(dest/'metrics.json',{
                'cell':cell,'design_sha256':C.sha(C.RUN/'FROZEN_DESIGN.json'),
                'audit_sha256':C.sha(C.RUN/'AUDIT_SUMMARY.json'),
                'prompt_audit_sha256':arm_audit['sha256'],
                'feature_to_identifier':arm_audit['feature_to_identifier'],
                'checkpoint_sha256':design['checkpoint_sha256'],
                'model_files':design['model_files'], 'split_sha256':design['split_sha256'],
                'train_membership':split['support'][str(n)],'test_membership':split['test'],
                'predictions_sha256':C.sha(path),'metrics':metrics,
                'seconds':time.monotonic()-started,'gpu':args.gpu,
                'completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                **extra})
            # Progress deliberately does not print efficacy outcomes.
            print(json.dumps({'cell':cell,'status':'complete','reused':bool(reused),
                              'seconds':time.monotonic()-started}),flush=True)

if __name__=='__main__':
    main()
