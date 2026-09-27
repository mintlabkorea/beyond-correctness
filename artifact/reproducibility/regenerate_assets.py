#!/usr/bin/env python3
"""Run original frozen-output plotting functions, changing output location only."""
import argparse,atexit,hashlib,importlib.util,json,os,shutil,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
_mpl_cache=tempfile.TemporaryDirectory(prefix='artifact_plot_cache_')
atexit.register(_mpl_cache.cleanup)
os.environ.setdefault('MPLCONFIGDIR',_mpl_cache.name)
os.environ['MPLBACKEND']='Agg'
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'iclr_latex_v3/scripts'))
sys.path.insert(0,str(ROOT/'scripts'))

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;spec.loader.exec_module(m);return m

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--figures',action='store_true');ap.add_argument('--tables',action='store_true');args=ap.parse_args()
    import matplotlib.figure
    import matplotlib.pyplot as plt
    output=ROOT/'generated/figures';output.mkdir(parents=True,exist_ok=True)
    original_save=matplotlib.figure.Figure.savefig
    emitted=[]
    def save(self,fname,*a,**kw):
        target=output/Path(fname).name
        if target.suffix=='.pdf':kw['metadata']={'Creator':'Anonymous artifact','Author':None,'CreationDate':None,'ModDate':None}
        elif target.suffix=='.png':kw['metadata']={'Software':'Anonymous artifact'}
        result=original_save(self,target,*a,**kw);emitted.append(str(target.relative_to(ROOT)));return result
    matplotlib.figure.Figure.savefig=save
    mf=module('make_main_figures','iclr_latex_v3/scripts/make_main_figures.py');mf.OUT_DIR=output
    af=module('make_appendix_assets','iclr_latex_v3/scripts/make_appendix_assets.py');af.FIG_DIR=output;af.GEN_DIR=ROOT/'generated/tables';af.GEN_DIR.mkdir(parents=True,exist_ok=True)
    ref=module('artifact_reference_plot','iclr_latex_v3/scripts/make_reference_sensitivity_figure.py')
    paired=module('artifact_paired_plot','scripts/plot_tabllm_paired_reference_v1.py')
    report={'figures':[],'tables':[]}
    mapping={r['paper_item']:r for r in __import__('csv').DictReader((ROOT/'reproducibility/table_figure_map.csv').open())}
    actions=[('fig:ref_sensitivity',ref.main),('fig:real_support_reference',mf.make_real_support_reference_figure),
      ('fig:app-correspondence-decoy-damage',af.plot_a7_decoy_damage),('fig:app-measurement-dose',af.plot_a2_mismatch_grid),
      ('fig:app-redundancy-ladder',af.plot_redundancy_ladder),('fig:app-tabllm-support-by-dataset',af.plot_tabllm_support_by_dataset),
      ('fig:app-interaction-controlled-real',af.plot_controlled_real_mechanism)]
    if args.figures:
        with tempfile.TemporaryDirectory(prefix='paired_plot_',dir=ROOT/'generated') as tmp:
            paired.OUT=Path(tmp)
            for n in ['SUMMARY_V1.json','utility_intervals.csv']:shutil.copyfile(ROOT/'experiments/tabllm_paired_reference_decomposition_v2'/n,paired.OUT/n)
            actions.append(('fig:app-tabllm-reference-noise',paired.main))
            for label,fn in actions:
                emitted.clear();row={'paper_item':label,'generator':mapping[label]['generating_script'],'inputs':mapping[label]['artifact_input'].split(';')}
                try:fn();row.update(status='PASS',outputs=emitted.copy())
                except Exception as e:row.update(status='FAIL',outputs=emitted.copy(),error=type(e).__name__+': '+str(e).replace(str(ROOT),'.'))
                row['input_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in row['inputs'] if (ROOT/p).is_file()}
                report['figures'].append(row);plt.close('all')
        # Conceptual illustration has no data-generating experiment.
        diagram=ROOT/'iclr_latex_v3/figures/reference_build.pdf'
        if diagram.exists():
            shutil.copyfile(diagram,output/diagram.name)
            report['figures'].append({'paper_item':'fig:reference_construction','generator':'frozen conceptual illustration','inputs':[str(diagram.relative_to(ROOT))],'outputs':['generated/figures/reference_build.pdf'],'status':'PASS'})
    if args.tables:
        for name in ['table_a1_measurement','table_a2_mismatch_fixed','table_a3_real_units','table_a4_factorial','table_a5_value_channel','table_a6_monotone','table_a7_decoy_matcher','table_a8_llm_panel','table_a9_loo','table_a10_relation','table_correspondence_interfaces','table_exam_no_bridge_reference','table_relation_audit_effect','table_camels_per_relation','table_a11_registry','table_factorial_c_simple_effects']:
            try:getattr(af,name)();report['tables'].append({'generator':name,'status':'PASS'})
            except Exception as e:report['tables'].append({'generator':name,'status':'FAIL','error':type(e).__name__+': '+str(e).replace(str(ROOT),'.')})
    # Plotting routines record their output destinations; keep these portable.
    for p in output.glob('*.json'):
        p.write_text(p.read_text().replace(str(ROOT)+'/', ''))
    dest=ROOT/'reproducibility'/('figure_generation_report.json' if args.figures else 'table_generation_report.json')
    dest.write_text(json.dumps(report,indent=2)+'\n')
    failures=sum(r['status']!='PASS' for v in report.values() for r in v)
    print(json.dumps({'figures':len(report['figures']),'tables':len(report['tables']),'failures':failures}))
    return int(failures>0)
if __name__=='__main__':raise SystemExit(main())
