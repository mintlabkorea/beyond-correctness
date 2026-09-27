"""Outcome-blind freeze and full prompt audit. Never loads model weights."""
import argparse
import datetime
import gzip
import json
import os
import re
import importlib.metadata
import platform
from pathlib import Path
import common as C

def erase_labels(notes,names,dataset):
    # Released clean_note removes the trailing blank after an empty value.
    # Replace only the label and colon, preserving every remaining byte.
    pattern = re.compile(r'(?m)^- ('+'|'.join(re.escape(x) for x in names)+r'):')
    result=[]
    for note in notes:
        normalized,count=pattern.subn('- <FIELD>:',note)
        assert count==len(names), ('rendered field count',dataset,count,len(names))
        result.append(normalized)
    return result

def freeze():
    assert not (C.RUN/'FROZEN_DESIGN.json').exists(), 'design already frozen'
    assignments=C.manifest()
    for d in C.DATASETS:
        perm=assignments['datasets'][d]['candidates']['ref_00']['line_to_identifier_index_zero_based']
        assert perm==list(range(len(perm))), 'primary mapping differs from historical canonical builder'
    files = list(Path(__file__).parent.glob('*.py')) + [
        C.ROOT/'iclr_latex_v3/TABLLM_W4_AUROC_EQUIVALENCE_FREEZE_V1.md',
        C.ROOT/'iclr_latex_v3/TABLLM_W2_FIXED_MAPPING_FREEZE_V2.md',
        C.ASSIGNMENTS, C.RUN/'USER_DESIGN.txt']
    inputs = [p for p in C.MODEL.iterdir() if p.is_file()]
    sources = [p for p in (C.TABLLM/'datasets').rglob('*') if p.is_file()]
    sources += [C.TABLLM/p for p in ('create_external_datasets.py',
        'helper/external_datasets_variables.py','helper/note_generator.py','helper/note_template.py')]
    sources += [p for p in (C.TFEW/'src/models').rglob('*.py')]
    b=C.base()
    serialization_sources=[p for p in (C.TABLLM/'datasets').rglob('*') if p.is_file()] + [
        C.TABLLM/p for p in ('create_external_datasets.py','helper/external_datasets_variables.py',
                            'helper/note_generator.py','helper/note_template.py')]
    design = {
        'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'provenance':C.PROVENANCE, 'delta':0.02, 'bootstrap_replicates':2000,
        'bootstrap_seed':20260910, 'datasets':C.DATASETS, 'seeds':C.SEEDS,
        'supports':C.SHOTS, 'families':{'R1':'feature_{i:03d}','R2':'Field {letter(i)}','R3':'Variable {letter(i)}'},
        'reference_cells':540, 'intended_cells':180,
        'primary_mapping':'ref_00', 'optional_extra_mappings':False,
        'raw_and_serialization_tree_sha256':b.aggregate_tree_hash(C.TABLLM,serialization_sources),
        'versions':{'python':platform.python_version(), **{name:importlib.metadata.version(package)
            for name,package in [('torch','torch'),('numpy','numpy'),('pandas','pandas'),
            ('transformers','transformers'),('datasets','datasets'),('scikit_learn','scikit-learn')]}},
        'files':{str(p.relative_to(C.ROOT)):C.sha(p) for p in files},
        'split_sha256':C.sha(C.SPLIT), 'checkpoint_sha256':C.sha(C.CHECKPOINT),
        'model_files':{p.name:C.sha(p) for p in inputs},
        'source_files':{str(p):C.sha(p) for p in sources},
    }
    C.write(C.RUN/'FROZEN_DESIGN.json',design)
    print(json.dumps({'status':'frozen','sha256':C.sha(C.RUN/'FROZEN_DESIGN.json')}),flush=True)

def audit(datasets):
    design = C.verify_freeze()
    for name,digest in design['model_files'].items():
        # Weight files are hash-bound at freeze; the audit uses tokenizer only.
        if not name.endswith(('.bin','.safetensors','.h5','.msgpack')):
            assert C.sha(C.MODEL/name) == digest
    for path,digest in design['source_files'].items():
        assert C.sha(path) == digest, f'changed source: {path}'
    b,t,m = C.base(),C.tabllm(),C.manifest()
    tokenizer = b.AutoTokenizer.from_pretrained(C.MODEL)
    tokenizer.model_max_length = b.MAX_LENGTH
    for d in datasets:
        done = C.RUN/'audit'/d/'COMPLETE.json'
        if done.exists():
            continue
        frame = b.build_full_dataset(t,C.TABLLM,d)
        split = C.splits(b,frame,d,C.read(C.SPLIT))
        rows = sorted({r for s in split.values() for r in s['test']} |
                      {r for s in split.values() for rs in s['support'].values() for r in rs})
        C.write(C.RUN/'audit'/d/'memberships.json',split)
        # Match the released runner's Series coercion exactly (iterrows may
        # represent mixed numeric rows differently from to_dict records).
        records = [row for _,row in frame.loc[rows].iterrows()]
        original = getattr(t,f'template_{d}_list')
        labels,tails = C.parts(original)
        originals = C.notes(t,records,d,original)
        # Strip only known field-label positions. Value text remains byte exact.
        normalized_originals = erase_labels(originals,labels,d)
        summary = {'dataset':d,'n_audited_rows':len(rows),'feature_count':len(labels),
                   'memberships_sha256':C.sha(C.RUN/'audit'/d/'memberships.json'), 'arms':{}}
        arms = [('intended','shared')] + [(f,a) for a in C.REFS for f in C.FAMILIES]
        for f,a in arms:
            path = C.audit_path(d,f,a)
            template = C.template_for(t,d,f,a,m)
            rendered_labels,_ = C.parts(template)
            rendered = originals if f=='intended' else C.notes(t,records,d,template)
            assert erase_labels(rendered,rendered_labels,d) == normalized_originals, (d,f,a,'value mutation')
            prompts = [note+'\n\n'+b.QUESTIONS[d] for note in rendered]
            counts = []
            for start in range(0,len(prompts),512):
                encoded = tokenizer(prompts[start:start+512],truncation=False,
                                    padding=False,add_special_tokens=True)
                counts.extend(map(len,encoded['input_ids']))
            mapping = dict(zip(labels,rendered_labels))
            path.parent.mkdir(parents=True,exist_ok=True)
            tmp = path.with_suffix('.tmp')
            with gzip.open(tmp,'wt') as h:
                for r,p,count in zip(rows,prompts,counts):
                    h.write(json.dumps({'dataset':d,'family':f,'assignment':a,'row_id':r,
                        'prompt_sha256':C.textsha(p),'token_count':count,
                        'truncated':count>b.MAX_LENGTH,
                        'retained_feature_value_pairs':len(labels) if count<=b.MAX_LENGTH else None,
                        'retention_status':'all' if count<=b.MAX_LENGTH else 'inadmissible_not_certified',
                    },sort_keys=True)+'\n')
            os.replace(tmp,path)
            summary['arms'][f'{f}/{a}'] = {'sha256':C.sha(path),
                'max_token_count':max(counts),'min_token_count':min(counts),'mean_token_count':sum(counts)/len(counts),
                'truncated_rows':sum(n>b.MAX_LENGTH for n in counts),
                'feature_to_identifier':mapping,'template_sha256':C.textsha(template)}
            print(json.dumps({'dataset':d,'family':f,'assignment':a,
                              'max_tokens':max(counts),'truncated':sum(n>b.MAX_LENGTH for n in counts)}),flush=True)
        C.write(done,summary)
    if all((C.RUN/'audit'/d/'COMPLETE.json').exists() for d in C.DATASETS):
        reports = {d:C.read(C.RUN/'audit'/d/'COMPLETE.json') for d in C.DATASETS}
        original_pass = all(r['arms']['intended/shared']['truncated_rows']==0 for r in reports.values())
        admissible = {f:original_pass and all(r['arms'][f'{f}/{a}']['truncated_rows']==0
            for r in reports.values() for a in C.REFS) for f in C.FAMILIES}
        C.write(C.RUN/'AUDIT_SUMMARY.json',{
            'completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'design_sha256':C.sha(C.RUN/'FROZEN_DESIGN.json'),
            'dataset_audit_sha256':{d:C.sha(C.RUN/'audit'/d/'COMPLETE.json') for d in C.DATASETS},
            'admissible_families':admissible, 'all_pass':all(admissible.values()),
            'performance_inspected':False, 'datasets':reports})
        print(json.dumps({'status':'audit_complete','admissible':admissible}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('mode',choices=['freeze','audit'])
    p.add_argument('--datasets',nargs='+',default=C.DATASETS,choices=C.DATASETS)
    args=p.parse_args()
    freeze() if args.mode=='freeze' else audit(args.datasets)
