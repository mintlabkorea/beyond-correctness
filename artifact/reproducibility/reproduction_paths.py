#!/usr/bin/env python3
"""Check original-input prerequisites; never launch model training."""
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('level',choices=['public','full']);args=ap.parse_args()
    required=['data/public/nhanes_source_lock/nhanes_common_panel_tokens_v2.parquet']
    if args.level=='full':required+=['data/nhanes_knhanes/datasets/knhanes/processed/L3/L3_9815_pr90_with_mpls.parquet','data/private/crta_v3/m3_inputs_v1/nhkn_canonical_source_v1.parquet','data/private/crta_v3/m3_inputs_v1/hrs_v1_concept_transfer_snapshot.parquet']
    missing=[p for p in required if not (ROOT/p).is_file()]
    print(json.dumps({'level':args.level,'missing_local_inputs':missing,'status':'BLOCKED' if missing else 'INPUT_PATHS_PRESENT_NOT_AUTHORIZATION','exact_external_preparation':'Public NHANES builder/source lock recovered; historical builder revision/environment and full clinical preparation remain partial. See DATA_ACCESS.md/I03.','training_started':False},indent=2))
    print('\nControlled primary grid, AFTER the original public panel is prepared and the historical environment is installed:')
    print('python3 scripts/run_crta_v3_mcr_factorial_semisynth_v1.py --input data/public/nhanes_source_lock/nhanes_common_panel_tokens_v2.parquet --out-root generated/reproduction/controlled --modes primary --families additive pairwise sparse --realizations '+' '.join(map(str,range(20)))+' --threads 2')
    print('\nCAMELS sign probe, AFTER original native-screen preparation (source.pkl, target.pkl, split_manifest.json):')
    print('python3 scripts/run_crta_v3_camels_sign_probe_v2.py --out-root generated/reproduction/camels --seeds '+' '.join(map(str,range(20,40)))+' --support-basins 1 3 5 --n-jobs 2')
    print('\nSafe analysis-only path from included split-level aggregates: make verify')
    print('Re-estimating row bootstraps requires externally held predictions. No row predictions are shipped. Frozen intervals remain directly verifiable.')
    if args.level=='full':print('\nClinical authorization gates remain active. Exact source-product versions, external approved preprocessing and reviewer authorization are required in addition to these paths. See DATA_ACCESS.md. TabLLM and learner extension commands/configuration are documented in tabllm/README.md and model_coverage/README.md; weights are external.')
    return int(bool(missing))
if __name__=='__main__':raise SystemExit(main())
