#!/usr/bin/env python3
"""Invoke recovered existing NHANES preparation; check frozen public source hashes."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--raw-root',type=Path,default=Path('data/public/nhanes_raw'));ap.add_argument('--output-dir',type=Path,default=Path('data/public/nhanes_source_lock'));ap.add_argument('--prepare',action='store_true',help='Actually build after validating every source hash; otherwise preflight only');args=ap.parse_args()
    manifest=json.loads((ROOT/'code/preprocessing/nhanes_source_lock/manifest_v2.json').read_text())
    missing=[];mismatch=[]
    for name,expected in manifest['source_sha256'].items():
        p=args.raw_root/name
        if not p.is_file():missing.append(name)
        elif digest(p)!=expected:mismatch.append(name)
    print(json.dumps({'expected_source_files':len(manifest['source_sha256']),'missing':missing,'hash_mismatch':mismatch,'preparation_requested':args.prepare},indent=2))
    if missing or mismatch:return 1
    if not args.prepare:return 0
    path=ROOT/'code/preprocessing/foundation/raw_adapter_source_locks_v2.py'
    spec=importlib.util.spec_from_file_location('original_raw_adapter',path);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    outputs=module.build_nhanes_common_panel_source_lock(raw_root=args.raw_root,output_dir=args.output_dir,created_at=manifest['created_at'])
    actual=digest(outputs['tokens']);expected=manifest['outputs']['nhanes_common_panel_tokens_v2.parquet']
    print(json.dumps({'output':str(outputs['tokens']),'sha256':actual,'frozen_sha256':expected,'byte_match':actual==expected},indent=2))
    return int(actual!=expected)
if __name__=='__main__':raise SystemExit(main())
