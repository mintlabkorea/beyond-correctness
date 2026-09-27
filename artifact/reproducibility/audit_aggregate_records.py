#!/usr/bin/env python3
"""New, explicitly labelled packaging analyses of existing aggregate records."""
import csv,json,math
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def csvwrite(p,rows):
    with (ROOT/p).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def rank(a):
    order=sorted(range(len(a)),key=a.__getitem__);r=[0.]*len(a);i=0
    while i<len(a):
        j=i+1
        while j<len(a) and a[order[j]]==a[order[i]]:j+=1
        for k in range(i,j):r[order[k]]=(i+j-1)/2
        i=j
    return r
def spearman(a,b):
    x=rank(a);y=rank(b);mx=sum(x)/len(x);my=sum(y)/len(y)
    return sum((a-mx)*(b-my) for a,b in zip(x,y))/math.sqrt(sum((a-mx)**2 for a in x)*sum((b-my)**2 for b in y))
def main():
    # 40 paired cells, two support sizes and five identical ladder/VR arms.
    rows=[];stats=defaultdict(list)
    for p in sorted((ROOT/'experiments/_recheck_vr_threads1').glob('*/*/metrics.json')):
        rel=p.relative_to(ROOT/'experiments/_recheck_vr_threads1')
        rerun=json.loads(p.read_text())
        old=json.loads((ROOT/'experiments/crta_v3_mcr_value_redundancy_v1'/rel).read_text())
        ladder=json.loads((ROOT/'experiments/crta_v3_mcr_redundancy_ladder_v1'/rel).read_text())
        for k in ['32','512']:
            for model in ['histgb','xgb']:
                for vr,rung,arm in [('full_free','0','free'),('full_op_true','0','op_true'),('drop_free',str(ladder['n_rungs']-1),'free'),('drop_op_true',str(ladder['n_rungs']-1),'op_true'),('drop_op_true_signed',str(ladder['n_rungs']-1),'sig_true')]:
                    lv=ladder['results'][k][model][rung]['arms'][arm]['nmse']
                    for name,obj in [('original_value_redundancy',old),('one_thread_rerun',rerun)]:
                        other=obj['results'][k][model][vr]['nmse'];diff=lv-other
                        rows.append(dict(family=ladder['family'],realization=ladder['realization'],support=k,backbone=model,vr_arm=vr,ladder_rung=rung,ladder_arm=arm,comparison=name,ladder_nmse=lv,comparison_nmse=other,difference=diff,exact_equal=lv==other))
                        stats[name,model].append(abs(diff))
    csvwrite('reproducibility/thread_count_audit/paired_aggregate_comparison.csv',rows)
    summary=[dict(comparison=key[0],backbone=key[1],n=len(values),exact_unequal=sum(x!=0 for x in values),unequal_at_1e12=sum(x>1e-12 for x in values),maximum_absolute_difference=max(values)) for key,values in sorted(stats.items())]
    (ROOT/'reproducibility/thread_count_audit/recomputed_summary.json').write_text(json.dumps({'origin':'NEW packaging analysis of original stored aggregate metrics; no fits rerun','comparisons':summary,'scope':'Five common arm nMSEs only. Stored JSON numeric equality, not in-memory binary identity. Thread=1 is explicit in ladder metrics; original VR/rerun metrics omit thread field; historical prose supplies that attribution.'},indent=2)+'\n')
    # Reproduce the archived table: average eight stratum coefficients at each dose.
    groups=defaultdict(list)
    p='experiments/crta_v3_mcr_noisy_proxy_recoverability_v1/CELL_DOSE_V1.csv'
    for r in csv.DictReader((ROOT/p).open()):
        if float(r['sigma'])>0:groups[r['family'],r['backbone'],r['support'],r['sigma']].append(r)
    rows=[];means=defaultdict(list);dose_means=defaultdict(list)
    for key,rs in sorted(groups.items()):
        rho=spearman([float(r['unreconstructibility']) for r in rs],[float(r['utility']) for r in rs]);means[key[:3]].append(rho);dose_means[float(key[3])].append(rho)
        rows.append(dict(family=key[0],backbone=key[1],support=key[2],sigma=key[3],n=len(rs),rho=rho,origin='NEW packaging calculation from frozen CELL_DOSE_V1.csv; average-tie ranks'))
    csvwrite('robustness/relation/within_dose_recomputed.csv',rows)
    csvwrite('robustness/relation/within_dose_setting_means.csv',[dict(family=k[0],backbone=k[1],support=k[2],mean_rho=sum(v)/len(v),n_doses=len(v)) for k,v in sorted(means.items())])
    csvwrite('robustness/relation/within_dose_dose_means.csv',[dict(sigma=k,mean_rho=sum(v)/len(v),n_settings=len(v),positive_settings=sum(x>0 for x in v)) for k,v in sorted(dose_means.items())])
    print(json.dumps({'thread_metric_comparisons':len(rows) if False else sum(len(v) for v in stats.values()),'within_dose_correlations':len(rows)}))
if __name__=='__main__':main()
