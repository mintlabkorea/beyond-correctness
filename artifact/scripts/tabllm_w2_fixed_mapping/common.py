"""Frozen W2 construction; imports no model until explicitly requested."""
import gzip
import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'experiments/tabllm_w2_fixed_mapping_v2'
ASSIGNMENTS = ROOT / 'experiments/tabllm_reference_space_v1/REFERENCE_MANIFEST_V1.json'
ASSIGNMENT_HASH = '7fe208e544a954ebd2c15e273473d604107a22e49230631101466ab97097d8da'
DATASETS = ('bank','blood','calhousing','car','creditg','diabetes','heart','income','jungle')
SEEDS = (42,1024,0,1,32)
SHOTS = (0,4,32,512)
FAMILIES = ('R1','R2','R3')
REFS = ('ref_00',)
PROVENANCE = 'reference lexical-realization robustness; design frozen before inspecting these outcomes'
REMOTE = Path('external/tabllm_3arm_v1')
TABLLM = REMOTE / 'repo'
TFEW = REMOTE / 't-few-upstream'
MODEL = Path('external/.cache/huggingface/hub/models--bigscience--T0/snapshots/1cfa27271f8085c29323c94bd659004b210f20b5')
CHECKPOINT = TFEW / 'pretrained_checkpoints/t011b_ia3_finish.pt'
SPLIT = REMOTE / 'split_manifest_v1.json'

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(8*1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def textsha(s):
    return hashlib.sha256(s.encode()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f'.{os.getpid()}.tmp')
    tmp.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')
    os.replace(tmp,path)

def module(name,path):
    spec = importlib.util.spec_from_file_location(name,path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

def base():
    return module('w2_frozen_base', Path(__file__).with_name('frozen_base.py'))

def tabllm():
    sys.path.insert(0,str(TABLLM))
    return module('w2_tabllm', TABLLM / 'create_external_datasets.py')

def manifest():
    assert sha(ASSIGNMENTS) == ASSIGNMENT_HASH, 'changed assignment manifest'
    return read(ASSIGNMENTS)

def parts(template):
    matches = [re.fullmatch(r'- (.*?): (\$\{.*)',line) for line in template.splitlines()]
    assert matches and all(matches), 'unexpected released list template'
    return [m[1] for m in matches], [m[2] for m in matches]

def identifiers(family, permutation):
    assert all(0 <= i < 26 for i in permutation), 'alphabetic identifier range exceeded'
    if family == 'R1':
        return [f'feature_{i+1:03d}' for i in permutation]
    noun = {'R2':'Field', 'R3':'Variable'}[family]
    return [f'{noun} {chr(65+i)}' for i in permutation]

def template_for(t, d, family, ref, m):
    original = getattr(t,f'template_{d}_list')
    if family == 'intended':
        return original
    labels,tails = parts(original)
    candidate = m['datasets'][d]['candidates'][ref]
    perm = candidate['line_to_identifier_index_zero_based']
    assert sorted(perm) == list(range(len(labels)))
    ids = identifiers(family,perm)
    assert not set(ids).intersection(labels)
    result = '\n'.join(f'- {name}: {tail}' for name,tail in zip(ids,tails))
    assert parts(result)[1] == tails
    if family == 'R1':
        assert textsha(result) == candidate['template_sha256']
    return result

def notes(t, records, d, template):
    generator = t.NoteTemplate(template, **getattr(t,f'template_config_{d}_list'))
    return [t.NoteGenerator.clean_note(generator.substitute(row)) for row in records]

def splits(b,frame,d,m):
    out = {}
    for seed in SEEDS:
        train,test = b.split_members(frame,seed)
        b.verify_split_manifest(m,d,seed,test)
        out[str(seed)] = {'test':test, 'support':{
            str(n):b.balanced_few_shot_members(frame,train,n,seed) for n in SHOTS}}
    return out

def cells(shots=SHOTS):
    for n in shots:
        for d in DATASETS:
            for s in SEEDS:
                yield d,n,s,'intended','shared'
                for a in REFS:
                    for f in FAMILIES:
                        yield d,n,s,f,a

def key(cell):
    d,n,s,f,a = cell
    return f'{d}/k{n}/seed{s}/{f}/{a}'

def verify_freeze():
    design = read(RUN / 'FROZEN_DESIGN.json')
    for rel,digest in design['files'].items():
        assert sha(ROOT/rel) == digest, f'changed frozen file: {rel}'
    assert sha(SPLIT) == design['split_sha256']
    assert sha(CHECKPOINT) == design['checkpoint_sha256']
    return design

def audit_path(d,f,a):
    return RUN/'audit'/d/f'{f}_{a}.jsonl.gz'

def audit_rows(d,f,a):
    with gzip.open(audit_path(d,f,a),'rt') as h:
        return {p['row_id']:p for p in map(json.loads,h)}
