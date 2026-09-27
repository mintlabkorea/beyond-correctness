#!/usr/bin/env python3
"""Compile unchanged *_new sources using temporary aliases for legacy includes."""
import json,os,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    out=ROOT/'generated/manuscript';out.mkdir(parents=True,exist_ok=True)
    report={'source_policy':'Unchanged main_new.tex and appendix_new.tex copied as main.tex and appendix.tex in a temporary directory to satisfy existing cross-references. The builder does not edit sources; reporting revisions already present in those sources are documented in REVISION_REPORT.md. Figures regenerated from included outputs; conceptual diagram metadata sanitized.','commands':[]}
    with tempfile.TemporaryDirectory(prefix='anonymous_paper_') as tmp:
        work=Path(tmp)
        for p in (ROOT/'iclr_latex_v3').iterdir():
            if p.suffix in {'.sty','.bst','.bib','.tex'} and p.name not in {'main_new.tex','appendix_new.tex'}:shutil.copyfile(p,work/p.name)
        for stem in ['main','appendix']:shutil.copyfile(ROOT/'iclr_latex_v3'/f'{stem}_new.tex',work/f'{stem}.tex')
        (work/'figures').mkdir()
        for p in (ROOT/'generated/figures').iterdir():
            if p.suffix in {'.pdf','.png'}:shutil.copyfile(p,work/'figures'/p.name)
        env=dict(os.environ,SOURCE_DATE_EPOCH='315532800',FORCE_SOURCE_DATE='1')
        sequence=[('pdflatex','appendix'),('bibtex','appendix'),('pdflatex','appendix'),('pdflatex','appendix'),('pdflatex','appendix'),('pdflatex','main'),('bibtex','main'),('pdflatex','main'),('pdflatex','main')]
        for tool,stem in sequence:
            cmd=([tool,'-interaction=nonstopmode','-halt-on-error','-file-line-error',stem+'.tex'] if tool=='pdflatex' else [tool,stem])
            r=subprocess.run(cmd,cwd=work,env=env,capture_output=True,text=True)
            report['commands'].append({'command':' '.join(cmd),'returncode':r.returncode})
            if r.returncode:
                report['status']='FAIL';report['error_tail']=r.stdout[-4000:].replace(tmp,'.')
                break
        else:
            for stem in ['main','appendix']:
                cmd=['gs','-q','-dBATCH','-dNOPAUSE','-sDEVICE=pdfwrite','-dOmitXMP=true','-sOutputFile='+str(out/(stem+'_new.pdf')),str(work/(stem+'.pdf')),'-c','[ /Author (Anonymous Authors) /Creator (Anonymous artifact) /DOCINFO pdfmark']
                subprocess.run(cmd,env=env,check=True,capture_output=True)
            report['status']='PASS'
            report['warnings']={stem:[l for l in (work/(stem+'.log')).read_text(errors='replace').splitlines() if 'Warning:' in l or 'Overfull' in l] for stem in ['main','appendix']}
    (ROOT/'reproducibility/manuscript_build_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
    return int(report['status']!='PASS')
if __name__=='__main__':raise SystemExit(main())
