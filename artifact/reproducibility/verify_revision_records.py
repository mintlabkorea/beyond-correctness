"""Verify finalization additions against original aggregate outputs; stdlib only."""
import csv,hashlib,json,re
from collections import defaultdict
from statistics import mean
from audit_aggregate_records import spearman

def verify(root,add):
    def record(item,name,expected,actual,source,note=''):
        add(item,name,expected,(actual,source,name),note)
    path='experiments/crta_v3_mcr_noisy_proxy_recoverability_v1/CELL_DOSE_V1.csv'
    groups=defaultdict(list);doses=defaultdict(list)
    for r in csv.DictReader((root/path).open()):
        if float(r['sigma'])>0:groups[r['family'],r['backbone'],r['support'],r['sigma']].append(r)
    for key,rows in groups.items():
        record('Appendix D.2','realizations '+str(key),20,len(rows),path)
        doses[float(key[-1])].append(spearman([float(r['unreconstructibility']) for r in rows],[float(r['utility']) for r in rows]))
    stored={float(r['sigma']):r for r in csv.DictReader((root/'robustness/relation/within_dose_dose_means.csv').open())}
    historic={.125:'.188',.25:'.215',.5:'.329',1.:'.165',2.:'.283',4.:'.232'}
    for dose,values in sorted(doses.items()):
        record('Appendix D.2',str(dose)+' settings',8,len(values),path)
        add('Appendix D.2',str(dose)+' dose mean matches archived table',historic[dose],(mean(values),path,'mean across eight per-stratum Spearman coefficients'))
        add('Appendix D.2',str(dose)+' exported recomputation',stored[dose]['mean_rho'],(mean(values),path,'mean across eight per-stratum Spearman coefficients'),tolerance=1e-12)
    record('Appendix D.2','minimum dose mean','.165',min(map(mean,doses.values())),path)
    record('Appendix D.2','maximum dose mean','.329',max(map(mean,doses.values())),path)
    record('Appendix D.2','nonzero doses',6,len(doses),path)
    p='robustness/correspondence/candidate_inventory_1315.csv';rows=list(csv.DictReader((root/p).open()));names=[r['target_column'] for r in rows]
    pool=hashlib.sha256('\n'.join(sorted(names)).encode()).hexdigest()
    sp='experiments/crta_v3_open_world_schema_matcher_v1/SUMMARY_V1.json';summary=json.loads((root/sp).read_text())
    record('Appendix B.3','unique full-universe names',1315,len(set(names)),p)
    record('Appendix B.3','full-universe rows',1315,len(rows),p)
    hashes=summary['pool_sha256_by_draw_and_size']
    candidates=[]
    def visit(o):
        if isinstance(o,dict):
            for k,v in o.items():
                if k=='1315':candidates.append(v)
                else:visit(v)
    visit(hashes)
    record('Appendix B.3','frozen full-universe pool hash comparisons',50,len(candidates),sp)
    record('Appendix B.3','all frozen pool hashes equal exported names',1,int(all(v==pool for v in candidates)),p+';'+sp)
    path='experiments/tabllm_w2_fixed_mapping_v2/full_analysis/SUMMARY.json';obj=json.loads((root/path).read_text())
    record('Appendix C.3','paired bootstrap resamples',2000,obj['bootstrap_replicates'],path)
    path='experiments/crta_v3_survey_label_panel_endpoint_expansion_v1/SUMMARY_V1.json';obj=json.loads((root/path).read_text())['construction']
    record('tab:app-measurement-full','cancer_history KN2NH finite pairs',4,obj['coverage_by_endpoint_direction']['cancer_history']['kn2nh'],path)
    record('tab:app-measurement-full','minimum required finite pairs',8,obj['minimum_finite_pairs_required'],path)
    record('tab:app-measurement-full','coverage gate failed',0,int(obj['coverage_gate_pass']),path)
    tex=(root/'iclr_latex_v3/appendix_new.tex').read_text()
    record('Appendix C.3','bootstrap exception disclosed',1,int('2,000' in tex), 'iclr_latex_v3/appendix_new.tex')
    path='reproducibility/environments/version_audit.csv';rows=list(csv.DictReader((root/path).open()))
    record('tab:app-software-environment','version comparisons',77,len(rows),path)
    for r in rows:
        obj=json.loads((root/r['source']).read_text())
        for k in r['json_path'].strip('/').split('/'):obj=obj[k]
        normalized=str(obj).split()[0] if r['component']=='python' else str(obj)
        ok=str(obj)==r['recorded'] and normalized==r['manuscript'] and normalized in tex
        record('tab:app-software-environment',r['experiment']+'/'+r['component']+r['json_path'],1,int(ok),r['source'],'Per-run recorded version; principal baseline retained in version_audit.csv')

    # Re-read stored metrics for the thread comparison rather than trust its new summary.
    counts=defaultdict(list)
    for p in sorted((root/'experiments/_recheck_vr_threads1').glob('*/*/metrics.json')):
        rel=p.relative_to(root/'experiments/_recheck_vr_threads1')
        rerun=json.loads(p.read_text());ladder=json.loads((root/'experiments/crta_v3_mcr_redundancy_ladder_v1'/rel).read_text())
        for k in ['32','512']:
            for model in ['histgb','xgb']:
                for vr,rung,arm in [('full_free','0','free'),('full_op_true','0','op_true'),('drop_free',str(ladder['n_rungs']-1),'free'),('drop_op_true',str(ladder['n_rungs']-1),'op_true'),('drop_op_true_signed',str(ladder['n_rungs']-1),'sig_true')]:
                    counts[model].append(ladder['results'][k][model][rung]['arms'][arm]['nmse']==rerun['results'][k][model][vr]['nmse'])
    for model,values in counts.items():
        record('Appendix H.1',model+' common-arm rerun comparisons',400,len(values),'experiments/_recheck_vr_threads1;experiments/crta_v3_mcr_redundancy_ladder_v1')
        record('Appendix H.1',model+' exact stored nMSE matches',400,sum(values),'experiments/_recheck_vr_threads1;experiments/crta_v3_mcr_redundancy_ladder_v1')
    main=(root/'iclr_latex_v3/main_new.tex').read_text()
    record('Section 4.4','main six-endpoint printed value matches verification target',1,int('correspondence utility falls from $+.070$' in main),'iclr_latex_v3/main_new.tex')
    record('Section 4.4','main intended nRMSE printed value matches verification target',1,int('intended SD-normalized RMSE improves from $.738$' in main),'iclr_latex_v3/main_new.tex')
