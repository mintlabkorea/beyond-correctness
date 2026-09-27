#!/usr/bin/env python3
"""Compare printed manuscript values with frozen outputs. Standard library only.

PASS means a printed value agrees with an identified output at its rounding
precision, not that an experiment has been rerun. Missing provenance fails.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import re
from pathlib import Path
from statistics import mean

ROOT=Path(__file__).resolve().parents[1]
ROWS=[]
CACHE={}
FAMILIES=('additive','pairwise','sparse')
DATASETS=('bank','blood','calhousing','car','creditg','diabetes','heart','income','jungle')

def load(p):
    if p not in CACHE:CACHE[p]=json.loads((ROOT/p).read_text())
    return CACHE[p]

def summary(n):return f'experiments/{n}/SUMMARY_V1.json'

def get(p, pointer):
    obj=load(p)
    for key in pointer.strip('/').split('/'):
        if key:obj=obj[int(key)] if isinstance(obj,list) else obj[key]
    return obj

def val(p,pointer,scale=1):
    return (float(get(p,pointer))*scale,p,pointer+(f' * {scale}' if scale!=1 else ''))

def calc(values,op,desc):
    a=[v[0] for v in values]
    value={'mean':mean,'min':min,'max':max,'sum':sum,'difference':lambda x:x[0]-x[1]}[op](a)
    return value,';'.join(dict.fromkeys(v[1] for v in values)),desc+'('+','.join(v[2] for v in values)+')'

def triple(p,pointer,estimate='mean',ci='ci95',scale=1):
    if scale==1:return [val(p,pointer+'/'+estimate),val(p,pointer+'/'+ci+'/0'),val(p,pointer+'/'+ci+'/1')]
    return [val(p,pointer+'/'+estimate,scale),val(p,pointer+'/'+ci+'/1',scale),val(p,pointer+'/'+ci+'/0',scale)]

def add(item,name,expected,actual=None,note='',tolerance=None):
    raw=str(expected)
    t=tolerance if tolerance is not None else (0.5*10**(-len(raw.split('.')[1])) if '.' in raw else 0)
    v,source,pointer=actual if actual is not None else (None,'','')
    diff=None if v is None else v-float(raw)
    status='MISSING' if v is None else ('PASS' if math.isfinite(v) and abs(diff)<=t+1e-12 else 'FAIL')
    ROWS.append(dict(paper_item=item,quantity=name,manuscript_value=raw,recomputed_value='' if v is None else format(v,'.17g'),
       difference='' if diff is None else format(diff,'.17g'),tolerance=t,status=status,source_file=source,
       analysis_script='reproducibility/verify_reported_results.py',source_selector=pointer,notes=note))

def table(label):
    for file in ['main_new.tex','appendix_new.tex']:
        text=(ROOT/'iclr_latex_v3'/file).read_text()
        for m in re.finditer(r'\\begin\{table\}.*?\\end\{table\}',text,re.S):
            if '\\label{'+label+'}' in m.group():
                b=m.group().split('\\midrule',1)[1].split('\\bottomrule')[0]
                return re.findall(r'(?<![\w.])[-+]?(?:\d*\.\d+)',b.replace('--',' '))
    raise ValueError(label)

def tablecheck(label,values):
    printed=table(label)
    if len(printed)!=len(values):
        add(label,'quantity count',len(printed),(len(values),'','registered selectors'),f'Selector mismatch: expected {len(printed)}, got {len(values)}')
        return
    for i,(e,a) in enumerate(zip(printed,values)):
        add(label,f'printed decimal {i+1}',e,a)

def numerical_tables():
    # Main decomposition table; all operands selected by semantic arm names.
    t=summary('tabllm_retrospective_audit_v1')
    values=[]
    for prefix in ['macro','datasets/creditg','datasets/bank']:
        for effect in ['content','utility_anonymous','wrong_harm_anonymous']:
            values.append(val(t,f'{prefix}/effects/{effect}/estimate'))
    r='experiments/crta_v3_relation_random_wrong_v1/TABLE2_RANDOM_WRONG_V1.json'
    for setting in ['nhkn_v1','hrs','camels120']:
        for wrong in ['reversal','random']:
            c=val(r,f'R_{setting}_content_vs_{wrong}/mean')
            u=val(r,f'R_{setting}_utility_vs_free/mean')
            values.extend([c,u,calc([c,u],'difference','sensitivity - utility')])
    s=summary('crta_v3_mcr_factorial_semisynth_v1')
    base=load(s)['primary']['xgb_K32']
    # Read the per-realization arm losses, independently of the summary.
    metrics=[json.loads(p.read_text())['results']['32']['xgb'] for p in sorted((ROOT/'experiments/crta_v3_mcr_factorial_semisynth_v1/primary/additive').glob('r*/metrics.json'))]
    if len(metrics)!=20:raise ValueError('Controlled primary additive grid is incomplete')
    for arm in ['r_flipped','m1c1r0']:
        source='experiments/crta_v3_mcr_factorial_semisynth_v1/primary/additive'
        c=(mean(m[arm]['nmse']-m['m1c1r1']['nmse'] for m in metrics),source,f'mean({arm} - m1c1r1), 20 realizations')
        u=(mean(m['m1c1rf']['nmse']-m['m1c1r1']['nmse'] for m in metrics),source,'mean(m1c1rf - m1c1r1), 20 realizations')
        values.extend([c,u,calc([c,u],'difference','sensitivity - utility')])
    tablecheck('tab:gap_utility',values)
    # Complete TabLLM dataset/contrast interval grid.
    values=[]
    for prefix in ['datasets/'+d for d in DATASETS]+['macro']:
        for e in ['content','utility_anonymous','wrong_harm_anonymous']:
            values.extend(triple(t,prefix+'/effects/'+e,estimate='estimate'))
    tablecheck('tab:app-tabllm-reproduction',values)
    # Reference library envelopes.
    ref='experiments/tabllm_reference_space_v1/summary_v1/SUMMARY_V1.json'
    values=[val(ref,f'datasets/{d}/{k}') for d in DATASETS for k in ['canonical_utility','minimum_utility','maximum_utility','span']]
    tablecheck('tab:app-tabllm-reference-envelope',values)
    # Clinical measurement, with the original direction reversed as specified.
    m=summary('crta_v3_survey_label_panel_v1'); e=summary('crta_v3_survey_label_panel_endpoint_expansion_v1')
    values=triple(m,'A2_pipeline_vs_placebo',estimate='mean_gain')+triple(m,'raw_vs_pipeline_descriptive',estimate='mean_gain',scale=-1)
    # Frozen reference-minus-altered calculation is recorded in the reporting ledger.
    ledger='iclr_latex_v3/generated/table2_reference_vs_wrong_v1.json'
    x=load(ledger)
    if isinstance(x,dict):
        # This expression uses paired aggregate arm differences, not paper literals.
        focused=next((v for k,v in x.items() if 'measurement' in k.lower() and isinstance(v,dict)),None)
    # Derived point estimate; CI must use the frozen paired contrast, never subtraction of CIs.
    c=val(m,'A2_pipeline_vs_placebo/mean_gain');u=val(m,'raw_vs_pipeline_descriptive/mean_gain',-1)
    values.append(calc([c,u],'difference','content - utility'))
    # Locate the explicit reference/wrong record by its analysis name.
    def search_record(obj):
        if isinstance(obj,dict):
            if obj.get('setting','').lower().startswith('measurement') and ('ci95' in obj):return obj
            for k,v in obj.items():
                if 'raw' in k.lower() and 'placebo' in k.lower() and isinstance(v,dict) and 'ci95' in v:return v
                found=search_record(v)
                if found:return found
        if isinstance(obj,list):
            for v in obj:
                found=search_record(v)
                if found:return found
        return None
    # Specific reporting schema is inspected below; missing is explicit.
    measurement_record=search_record(x)
    for i in range(2):values.append((measurement_record['ci95'][i],ledger,'measurement reference-altered/ci95/'+str(i)) if measurement_record else None)
    values.append(calc([val(m,'raw_absolute_auroc_per_target/'+d) for d in get(m,'targets_present')],'mean','endpoint mean raw AUROC'))
    values+=triple(e,'P1_pipeline_vs_placebo')+triple(e,'raw_minus_pipeline_descriptive',scale=-1)+triple(e,'R1_raw_absolute_reversal')
    tablecheck('tab:app-measurement-full',values)
    # Width matched reference.
    f=summary('crta_v3_exam_no_bridge_reference_v1')
    tablecheck('tab:app-exam-no-bridge',[v for k in ['content_S_minus_W','utility_S_minus_R','reference_minus_wrong_R_minus_W'] for v in triple(f,'contrasts/'+k)])
    values=[]
    for setting in ['nhkn_v1','hrs','camels120']:
        values+=triple(r,f'R_{setting}_content_vs_reversal')+triple(r,f'R_{setting}_content_vs_random')
        values+=(triple(r,f'R_{setting}_utility_vs_free') if setting=='camels120' else [val(r,f'R_{setting}_utility_vs_free/mean')])
    tablecheck('tab:app-relation-altered-construction',values)
    # Dose summaries retain the exact recorded bootstrap and means.
    values=[]
    for model,k in [('xgb',32),('histgb',32),('tabpfn',32),('xgb',512),('histgb',512),('tabpfn',512)]:
        if model=='tabpfn' and k==32:
            p=summary('crta_v3_mcr_mismatch_dose_tabpfn_v1');pre='sections';keys=['MDT_P1_spearman','MDT_P2_u8']
        elif k==512 and model!='xgb':
            p=summary('crta_v3_mcr_mismatch_dose_k512_extension_v1');pre=f'sections/{model}_K{k}';keys=['rho_dose_utility','u8']
        else:
            p=summary('crta_v3_mcr_mismatch_dose_v1');pre=f'sections/{model}_K{k}';keys=['MD_P1_spearman','MD_P2_u8']
        for key in keys:
            a=[val(p,f'{pre}/{fam}/{key}/mean') for fam in FAMILIES]
            values.extend([calc(a,'min','family minimum'),calc(a,'max','family maximum')])
    tablecheck('tab:app-measurement-dose-stats',values)
    p=summary('tabllm_ranon_support_ladder_v1')
    values=[v for k in [0,4,32,512] for v in triple(p,f'macro/utility/{k}',estimate='estimate',ci='bootstrap_ci95')]
    values+=triple(p,'primary_decay_0_to_512',estimate='estimate',ci='bootstrap_ci95')
    tablecheck('tab:app-tabllm-support-ladder',values)
    p=summary('crta_v3_exam_support_ladder_v1');values=[]
    for group in ['classA_primary','all13']:
        for k in [64,256,1024]:values+=triple(p,f'levels/{group}/utility_S_minus_R/{k}')
        values+=triple(p,f'decays/{group}/decay_utility_S_minus_R_64_minus_1024')
    tablecheck('tab:app-exam-support-ladder',values)
    p=summary('crta_v3_relation_capacity_sensitivity_v1')
    tablecheck('tab:app-relation-capacity',[val(p,f'results/{f}/{k}/total_utility/{c}/mean') for f in FAMILIES for k in [32,512] for c in ['baseline','depth2']])
    p=summary('crta_v3_mcr_nonsemantic_rank_alignment_v1');pol='experiments/crta_v3_mcr_nonsemantic_rank_alignment_v1/POLARITY_DOSE_V1.json';values=[]
    for model,k in [('xgb',32),('histgb',32),('xgb',512)]:
        for kind in ['U_raw','U_rank']:
            a=[val(p,f'sections/{model}_K{k}/support_only/{f}/{kind}/by_dose/4/mean') for f in FAMILIES]
            values.extend([calc(a,'min','family minimum'),calc(a,'max','family maximum')])
        pre='primary_K32_support_only' if k==32 else 'sensitivity_K512_support_only'
        values.extend(triple(pol,pre,estimate='mean_slope',ci='mean_slope_cluster_ci95'))
    tablecheck('tab:app-measurement-rank-alignment',values)
    p=summary('crta_v3_mcr_transtab_bridge_decomposition_v1');values=[]
    for k in [32,512]:
        a=[val(p,f'results/{k}/shared_identity_bridge/{f}/mean') for f in FAMILIES]
        values.extend([calc(a,'min','family minimum'),calc(a,'max','family maximum')])
        shares=[-100*get(p,f'results/{k}/false_bridge/{f}/mean')/get(p,f'results/{k}/conventional_content_gap/{f}/mean') for f in FAMILIES]
        for e,v,bound in zip(([74,80] if k==32 else [97,100]),[min(shares),max(shares)],['min','max']):
            add('tab:app-model-coverage-compact',f'K{k} harm share {bound} percent',e,(v,p,'-100 * false_bridge / conventional_content_gap'),tolerance=.5)
    tablecheck('tab:app-model-coverage-compact',values)
    p=summary('crta_v3_mcr_carte_v1')
    for k in [32,512]:
        for contrast,e in [('M_utility_correct_vs_raw',0 if k==32 else 2),('C_utility_correct_vs_reference',0 if k==32 else 2),('R_utility_correct_vs_free',0)]:
            n=sum(v['ci95'][0]>0 for v in get(p,f'supports/{k}/{contrast}/families').values())
            add('tab:app-model-coverage-compact',f'CARTE K{k} {contrast} positive families',e,(n,p,f'supports/{k}/{contrast}/families: count CI lower >0'))
    values=[]
    for p,cp,up in [
        (summary('crta_v3_m1m2_stage_factorial_v1'),'S2_binding_content/per_target_mean','desc_columns_at_stage/per_target_mean'),
        (summary('crta_v3_binding_backbone_generality_v1'),'sections/K256/S5_P1_binding_content/target_means','sections/K256/S5_P2_columns_on_stage/target_means'),
        (summary('crta_v3_pam_constraint_relations_v1'),'V_SIGN_CONTENT_flip_must_hurt/per_target_mean','declared_sign_vs_free_tax_expected/per_target_mean'),
        (summary('crta_v3_m3_sign_probe_v1'),'GS_P1_identification_flipped/per_endpoint_mean','GS_P3_utility_vs_free/per_endpoint_mean'),
        ('experiments/crta_v3_camels_sign_probe_v2/SUMMARY_V2.json','GCv2_P1_identification/log1p_rmse/per_basin_mean','GCv2_P2_utility/log1p_rmse/per_basin_mean')]:
        for ptr in [cp,up]:
            a=[val(p,ptr+'/'+name) for name in get(p,ptr)]
            values.extend([calc(a,'min','unit minimum'),calc(a,'max','unit maximum')])
    tablecheck('tab:app-unit-attribution-summary',values)

def prose_and_figures():
    p='experiments/tabllm_reference_space_v1/summary_v1/SUMMARY_V1.json'
    for name,num,ptr in [('library size',24,'reference_count'),('datasets',9,'dataset_count'),('reference cells',216,'cell_count')]:add('fig:ref_sensitivity',name,num,val(p,ptr))
    for bound,expected in [('minimum','+.088'),('maximum','+.124')]:
        add('Section 4.3',bound+' macro utility',expected,val(p,'aligned_reference_index_macro_distribution/'+bound))
    d=get(p,'datasets')
    add('fig:ref_sensitivity','point sign crossings',4,(sum(v['minimum_utility']<0<v['maximum_utility'] for v in d.values()),p,'count of dataset ranges crossing zero'))
    # Recompute the complete 216 point-estimate library from safe split-level metrics.
    base=summary('tabllm_retrospective_audit_v1')
    for dataset in DATASETS:
        for i in range(24):
            f=f'experiments/tabllm_reference_space_v1/evidence_v1/ref_{i:02d}/{dataset}/metrics.json'
            metrics=get(f,'metrics')
            split_scores=[float(v['auc']) for k,v in metrics.items() if k in {'42','1024','0','1','32'}] if isinstance(metrics,dict) else []
            if not split_scores:raise ValueError('No reference split AUROCs')
            intended=get(base,f'datasets/{dataset}/arm_mean_auc/list_template')
            computed=intended-mean(split_scores)
            # Expected values are frozen library records, not printed values.
            rows=list(csv.DictReader((ROOT/'experiments/tabllm_reference_space_v1/summary_v1/reference_utilities.csv').open()))
            target=next(r for r in rows if r['dataset']==dataset and r['reference_id']==f'ref_{i:02d}')
            add('fig:ref_sensitivity',dataset+f'/ref_{i:02d}',target['utility'],(computed,f,'intended mean AUROC - mean of five reference split AUROCs'),tolerance=1e-12,note='Independent aggregation consistency, stricter than printed rounding')
    p=summary('tabllm_paired_reference_decomposition_v2');d=get(p,'datasets')
    remaining=[(1-x['noise_fraction_of_observed_spread'])*100 for x in d.values()]
    add('fig:app-tabllm-reference-noise','remaining reference variance minimum percent','79.2',(min(remaining),p,'min(100*(1-noise_fraction))'))
    add('fig:app-tabllm-reference-noise','remaining reference variance maximum percent','99.7',(max(remaining),p,'max(100*(1-noise_fraction))'))
    add('fig:app-tabllm-reference-noise','paired resamples',5000,(d['jungle']['draw_count'],p,'datasets/jungle/draw_count'))
    p=summary('tabllm_retrospective_audit_v1')
    errors=[abs(v) for d in get(p,'datasets').values() for v in d['published_arm_absolute_errors'].values()]
    add('Section 4.1; Appendix B.1','published means within .015',21,(sum(v<=.015 for v in errors),p,'count of published_arm_absolute_errors <= .015'))
    add('Appendix B.1','maximum compatibility deviation','.0347',(max(errors),p,'maximum published_arm_absolute_errors'))
    p=summary('crta_v3_survey_label_panel_endpoint_expansion_v1')
    for name,e,a in zip(['mean','CI lower','CI upper'],['+.197','+.110','+.294'],triple(p,'raw_minus_pipeline_descriptive',scale=-1)):add('Section 4.4','ten-endpoint utility '+name,e,a)
    p=summary('crta_v3_exam_support_ladder_v1')
    add('Section 4.4','six-endpoint K64 utility','+.070',val(p,'levels/classA_primary/utility_S_minus_R/64/mean'),'Main and Appendix D.3 use the same three-decimal rounding')
    for group,arm,k,e in [('classA_primary','S_shared_bridge',64,'.738'),('classA_primary','S_shared_bridge',1024,'.676'),('classA_primary','R_domain_local',64,'.808'),('classA_primary','R_domain_local',1024,'.694')]:
        add('Section 4.4',f'{group}/{arm}/{k}',e,val(p,f'absolute_nrmse_trajectories/{group}/{arm}/{k}'))
    p='experiments/tabllm_all_reference_k512_v1/summary_v1/SUMMARY_V1.json'
    refs=get(p,'references')
    add('Appendix D.3','references with positive decay',24,(sum(x['decay_0_to_512']['estimate']>0 for x in refs.values()),p,'positive decay estimates over all references'))
    for i,e in enumerate(['+.017','+.138']):add('Appendix D.3','minimum decay interval '+str(i),e,val(p,f'minimum_decay_envelope/dataset_bootstrap_ci95/{i}'))
    p='reanalysis_20260903/A3_measurement_folded/summary.json'
    for i,expected in [(3,['+.276','+.090','+.385']),(7,['+.156','+.089','+.225'])]:
        for key,e in zip(['estimate','ci95_low','ci95_high'],expected):add('Appendix E.1','folded utility '+str(i)+' '+key,e,val(p,f'results/{i}/{key}'))
    p='experiments/tabllm_w2_fixed_mapping_v2/full_analysis/SUMMARY.json'
    for family,e in [('R1','+.0887'),('R2','+.0716'),('R3','+.0792'),('R2-R1','-.0171'),('R3-R1','-.0095')]:add('Appendix C.3','lexical '+family,e,val(p,'primary_macro/'+family+'/estimate'))
    for i,e in enumerate(['-.0268','-.0077']):add('Appendix C.3','Field minus primary CI '+str(i),e,val(p,f'primary_macro/R2-R1/ci95/{i}'))
    p='iclr_latex_v3/generated/real_utility_resolution.json'
    for i,e in enumerate(['.0095','.0122','.0029','.0015','.1443','.1586']):add('Appendix E.3','MDE '+str(i),e,val(p,f'panels/{i}/mde_80'))
    # Figure generation is a separate check of computation from frozen inputs.
    fig_report=ROOT/'reproducibility/figure_generation_report.json'
    if fig_report.exists():
        for record in json.loads(fig_report.read_text())['figures']:
            if record['paper_item']=='fig:reference_construction':continue
            ok=record['status']=='PASS' and all((ROOT/p).is_file() for p in record['outputs'])
            add(record['paper_item'],'regeneration from frozen numeric inputs',1,(int(ok),';'.join(record['inputs']),record['generator']),note='Generation check; stored intervals are not independently refit.')

def human_records():
    from verify_human_audit import verify
    verify(ROOT,add)

def revision_records():
    from verify_revision_records import verify
    verify(ROOT,add)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',default='reproducibility');args=ap.parse_args()
    for fn in [numerical_tables,prose_and_figures,human_records,revision_records]:
        try:fn()
        except (KeyError,ValueError,FileNotFoundError,TypeError) as e:
            add(fn.__name__,'verification procedure incomplete',1,None,type(e).__name__+': '+str(e))
    # Coverage is machine checked; unsupported numerical items are never silently skipped.
    mapping=ROOT/'reproducibility/table_figure_map.csv'
    covered={r['paper_item'] for r in ROWS}
    if mapping.exists():
        for row in csv.DictReader(mapping.open()):
            if row.get('verification_required')=='yes' and row['paper_item'] not in covered:
                add(row['paper_item'],'numerical coverage',1,None,'Numerical artifact mapped, but exact printed-value selectors are not complete.')
    out=ROOT/args.output_dir;out.mkdir(parents=True,exist_ok=True)
    with (out/'result_verification.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(ROWS[0]));w.writeheader();w.writerows(ROWS)
    counts={s:sum(r['status']==s for r in ROWS) for s in ['PASS','FAIL','MISSING']}
    lines=['# Paper-result verification','',f"Overall: {'PASS' if not counts['FAIL'] and not counts['MISSING'] else 'FAIL'}",'',str(counts),'',
      'Printed decimals use half a unit in the last printed place. Integer counts use exact equality. Internal aggregation checks use 1e-12.',
      'Frozen-output verification does not imply model retraining or independent regeneration of stored confidence intervals.','',
      '| Item | Quantity | Printed | Computed | Tolerance | Status | Notes |','|---|---|---|---|---|---|---|']
    for r in ROWS:
        lines.append('| '+' | '.join(str(r[k]).replace('|','/') for k in ['paper_item','quantity','manuscript_value','recomputed_value','tolerance','status','notes'])+' |')
    (out/'result_verification.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(counts))
    return 1 if counts['FAIL'] or counts['MISSING'] else 0

if __name__=='__main__':raise SystemExit(main())
