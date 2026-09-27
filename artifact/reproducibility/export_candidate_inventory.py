#!/usr/bin/env python3
"""Optional schema-only export; requires authorized local prepared input and pyarrow.
No row values are loaded. Existing frozen source/pool hashes must match.
"""
import argparse,csv,hashlib,json
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);args=p.parse_args()
    import pyarrow.parquet as pq
    summary=json.loads((ROOT/'experiments/crta_v3_open_world_schema_matcher_v1/SUMMARY_V1.json').read_text())
    file_hash=sha(args.source)
    if file_hash!=summary['provenance']['knhanes_sha256']:raise ValueError('Input is not the frozen prepared source')
    names=pq.read_schema(args.source).names;pool=hashlib.sha256('\n'.join(sorted(names)).encode()).hexdigest()
    pools=[]
    def visit(o):
        if isinstance(o,dict):
            for k,v in o.items():
                if k=='1315':pools.append(v)
                else:visit(v)
    visit(summary['pool_sha256_by_draw_and_size'])
    if len(set(names))!=1315 or len(pools)!=50 or any(v!=pool for v in pools):raise ValueError('Schema does not match all frozen candidate pools')
    args.output_dir.mkdir(parents=True,exist_ok=True)
    with (args.output_dir/'candidate_inventory_1315.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['original_schema_index','target_column']);w.writerows(enumerate(names))
    (args.output_dir/'schema_export_check.json').write_text(json.dumps(dict(origin='New schema-only projection; not a historical CSV',creation_date=date.today().isoformat(),source_file_sha256=file_hash,sorted_names_newline_sha256=pool,count=len(names),row_values_read=False),indent=2)+'\n')
    print('PASS: 1,315 names match the frozen file and 50 full-pool hashes; no row values loaded.')
if __name__=='__main__':main()
