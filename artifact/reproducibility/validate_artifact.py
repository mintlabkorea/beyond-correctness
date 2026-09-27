#!/usr/bin/env python3
"""Portable hygiene, integrity and scientific-completeness checks; no downloads."""
from __future__ import annotations
import ast,argparse,csv,hashlib,json,re,subprocess,sys,tempfile,zipfile,stat,xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[1]
CATEGORIES=['code/experiments','code/analysis','code/preprocessing','code/plotting','code/utilities','configs','provenance','published_audit','tabllm','robustness/measurement','robustness/correspondence','robustness/relation','robustness/interaction','robustness/resolution','model_coverage','method_contract','extraction','reproducibility/environments','reproducibility/thread_count_audit']
FORBIDDEN_PARTS={'.git','__pycache__','.pytest_cache','.idea','.vscode','.DS_Store','.ssh','.aws','.runtime'}
FORBIDDEN_SUFFIXES={'.parquet','.pkl','.pickle','.npy','.npz','.pt','.pth','.safetensors','.ckpt','.dta','.sas7bdat','.xpt','.sqlite','.db'}
TEXT={'.py','.sh','.json','.csv','.md','.txt','.tex','.bib','.sty','.bst','.yaml','.yml','.toml','.sha256','.diff'}
def digest(p):
    if p not in HASH_CACHE:HASH_CACHE[p]=hashlib.sha256(p.read_bytes()).hexdigest()
    return HASH_CACHE[p]
HASH_CACHE={}

def static_string(node):
    """Decode literal strings/concatenations/joins without executing source code."""
    if isinstance(node,ast.Constant) and isinstance(node.value,str):return node.value
    if isinstance(node,(ast.List,ast.Tuple)):return [static_string(x) for x in node.elts]
    if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Add):return static_string(node.left)+static_string(node.right)
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='join' and len(node.args)==1:
        return static_string(node.func.value).join(static_string(node.args[0]))
    raise ValueError('Not a static string')

def scan(fingerprint=None):
    findings=[];checks=Counter()
    identities=json.loads(fingerprint.read_text()) if fingerprint and fingerprint.exists() else {'token_sha256':[],'phrase_sha256':{}}
    def finding(path,kind,level='HIGH',detail='Matched content is withheld to avoid repeating sensitive material.'):
        findings.append({'path':path,'check':kind,'severity':level,'detail':detail})
    identity_tokens=set(identities['token_sha256'])
    def textscan(rel,s):
        # Generic patterns contain no original identifying strings.
        if re.search(r'(?<![\w:/])/(?:home|Users|root|mnt|media|scratch|workspace|var/tmp|tmp|opt/conda)/[A-Za-z0-9_.-]+',s):finding(rel,'absolute local path')
        if re.search(r'\b[A-Za-z]:\\(?:Users|Documents)\\',s):finding(rel,'absolute Windows path')
        if '@' in s and re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}',s):finding(rel,'email')
        if re.search(r'\b\d{4}-\d{4}-\d{4}-\d{3}[\dX]\b',s):finding(rel,'ORCID-like identifier')
        words=re.findall(r'[\w.-]+',s.casefold()) if identity_tokens or identities.get('phrase_sha256') else []
        if any(hashlib.sha256(w.encode()).hexdigest() in identity_tokens for w in set(words)):finding(rel,'repository identity token')
        for n,hashes in identities.get('phrase_sha256',{}).items():
            n=int(n)
            if any(hashlib.sha256(' '.join(words[i:i+n]).encode()).hexdigest() in hashes for i in range(len(words)-n+1)):finding(rel,'repository identity phrase')
        secret_patterns=[r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',r'\b(?:ghp_|github_pat_|hf_)[A-Za-z0-9_]{20,}',r'\bAKIA[A-Z0-9]{16}\b',r'\bsk-[A-Za-z0-9_-]{24,}',r'https?://[^\s/]+:[^\s/]+@',r'(?i)(?:password|api_key|access_token|secret_key)\s*[:=]\s*[\"\'][A-Za-z0-9_+/=-]{20,}[\"\']']
        if any(re.search(pattern,s) for pattern in secret_patterns):finding(rel,'secret pattern')
        if re.search(r'(?m)^\s*#(?:SBATCH|PBS).*?(?:--account|--mail-user|--nodelist| -A | -M )',s):finding(rel,'scheduler identity')
        if re.search(r'(?i)(?:wandb_entity|wandb_user|hostname|username)\s*[\"\']?\s*[:=]\s*[\"\'](?!anonymous|\{)[^\"\']+[\"\']',s):finding(rel,'account metadata','REVIEW')

    inventory=sorted(ROOT.rglob('*'))
    for p in inventory:
        rel=p.relative_to(ROOT).as_posix()
        if p.is_symlink():finding(rel,'symlink');continue
        if any(x in FORBIDDEN_PARTS for x in p.relative_to(ROOT).parts):finding(rel,'cache or private directory');continue
        if not p.is_file():continue
        checks['files']+=1
        if any(x in p.name.casefold() for x in ['인적사항','personnel','identity_roster']):finding(rel,'personnel file');continue
        if p.suffix.lower() in FORBIDDEN_SUFFIXES:finding(rel,'unapproved data or model binary')
        if p.name.startswith('.env') or p.name in {'id_rsa','id_ed25519','credentials','known_hosts'}:finding(rel,'credential file')
        if p.suffix=='.xlsx':
            checks['xlsx_workbooks']+=1
            try:
                with zipfile.ZipFile(p) as z:
                    for member in z.infolist():
                        name=member.filename;location=rel+'!'+name
                        if PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts or stat.S_ISLNK(member.external_attr>>16):finding(location,'unsafe nested ZIP member');continue
                        if name.endswith(('.xml','.rels')):
                            raw=z.read(member).decode('utf-8');checks['xlsx_xml_members']+=1
                            node=ET.fromstring(raw)
                            textscan(location,' '.join(node.itertext())+' '+' '.join(v for el in node.iter() for v in el.attrib.values()))
                            for el in node.iter():
                                tag=el.tag.rsplit('}',1)[-1]
                                if tag in {'creator','lastModifiedBy','author'} and el.text and el.text.strip() not in {'Anonymous','Anonymous Authors','Anonymous artifact'}:finding(location,'XLSX author metadata')
                                if el.attrib.get('TargetMode')=='External':finding(location,'XLSX external relationship')
                        elif not name.endswith('/'):
                            finding(location,'unexpected XLSX binary member')
            except (ValueError,UnicodeError,zipfile.BadZipFile,ET.ParseError):finding(rel,'invalid XLSX container','ERROR')
            continue
        if p.suffix not in TEXT and p.suffix and p.name not in {'Makefile','LICENSE','SHA256SUMS'}:continue
        try:s=p.read_text(encoding='utf-8')
        except UnicodeError:finding(rel,'nontext in text inventory');continue
        checks['text_files']+=1
        textscan(rel,s)
        if p.suffix=='.py':
            try:tree=ast.parse(s)
            except SyntaxError:finding(rel,'invalid Python syntax','ERROR');continue
            checks['python_ast_files']+=1
            seen=set()
            for node in ast.walk(tree):
                if not isinstance(node,(ast.Constant,ast.BinOp,ast.Call)):continue
                try:value=static_string(node)
                except (ValueError,TypeError,AttributeError):continue
                if isinstance(value,str) and value not in seen:
                    seen.add(value);checks['decoded_python_strings']+=1
                    textscan(rel+':'+str(getattr(node,'lineno',0))+' (decoded string)',value)
        if p.suffix=='.json':
            try:obj=json.loads(s)
            except ValueError:finding(rel,'invalid JSON','ERROR');continue
            def private(o):
                if isinstance(o,dict):
                    for k,v in o.items():
                        if re.fullmatch(r'(?:subject_ids?|participant_ids?|patient_ids?|row_ids|y_true|y_pred|query_labels|support_labels)',k,re.I) and isinstance(v,(list,dict)):return True
                        if private(v):return True
                elif isinstance(o,list):return any(private(v) for v in o)
                return False
            if private(obj):finding(rel,'person-level structured record')
    # PDFs are limited to freshly regenerated figures and one metadata-sanitized diagram.
    for p in (p for p in inventory if p.suffix=='.pdf'):
        checks['pdfs']+=1
        try:r=subprocess.run(['pdfinfo',str(p)],capture_output=True,text=True)
        except FileNotFoundError:continue
        if r.returncode:finding(p.relative_to(ROOT).as_posix(),'unreadable PDF','ERROR');continue
        for line in r.stdout.splitlines():
            if line.startswith('Author:') and line.split(':',1)[1].strip() not in {'','Anonymous','Anonymous Authors','Anonymous artifact'}:finding(p.relative_to(ROOT).as_posix(),'PDF author metadata')
    return findings,dict(checks)

def validate(require_full=False):
    rows=[]
    def check(name,ok,detail=''):rows.append({'check':name,'status':'PASS' if ok else 'FAIL','detail':detail})
    for category in CATEGORIES:check('category '+category,(ROOT/category).is_dir())
    excluded=json.loads((ROOT/'reproducibility/release_exclusions.json').read_text())['excluded_paths']
    check('excluded legacy scripts absent',all(not (ROOT/p).exists() for p in excluded))
    m=ROOT/'reproducibility/table_figure_map.csv'
    mapping=list(csv.DictReader(m.open())) if m.exists() else []
    expected=set()
    for name in ['main_new.tex','appendix_new.tex']:
        s=(ROOT/'iclr_latex_v3'/name).read_text()
        for block in re.findall(r'\\begin\{(?:table|figure)\}.*?\\end\{(?:table|figure)\}',s,re.S):
            match=re.search(r'\\label\{([^}]+)\}',block)
            if match:expected.add(match.group(1))
    check('every manuscript table and figure mapped',expected=={r['paper_item'] for r in mapping},f'{len(expected)} expected; {len(mapping)} mapped')
    for row in mapping:
        for path in filter(None,row['artifact_input'].split(';')):check('mapped input '+path,(ROOT/path).exists(),row['paper_item'])
        script=row['generating_script'].split(':')[0]
        if script and not script.isupper():check('mapped generator '+script,(ROOT/script).is_file(),row['paper_item'])
    for path in ['reproducibility/verify_reported_results.py','reproducibility/regenerate_assets.py','reproducibility/reproduction_paths.py','reproducibility/validate_artifact.py','reproducibility/environments/verification-requirements.txt','method_contract/input_boundary_audit.json']:
        check('reviewer command/input '+path,(ROOT/path).is_file())
    primary='iclr_latex_v3/method_contract/v1/runs/proposer_bank_v2/models/gpt-5.6-sol/medical_nhanes_knhanes_full_documents_v2_attempt_02/'
    for record in json.loads((ROOT/'method_contract/input_boundary_audit.json').read_text())['hash_checks']:
        path=(primary if record['component']=='raw_response.txt' else 'method_contract/')+record['component']
        check('executed contract hash '+record['component'],(ROOT/path).is_file() and digest(ROOT/path)==record['recorded'])
    extraction=list(csv.DictReader((ROOT/'extraction/model_audit.csv').open()))
    check('seven-model extraction inventory',len(extraction)==7)
    for record in extraction:check('extraction response hash '+record['model'],digest(ROOT/record['raw_response'])==record['raw_response_sha256'])
    hashes=ROOT/'SHA256SUMS';manifest=ROOT/'ARTIFACT_MANIFEST.csv'
    check('SHA256SUMS exists',hashes.is_file());check('ARTIFACT_MANIFEST.csv exists',manifest.is_file())
    if hashes.is_file():
        records={line.split('  ',1)[1]:line.split('  ',1)[0] for line in hashes.read_text().splitlines() if line}
        files={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and p!=hashes}
        check('checksum inventory complete',files==set(records),f'{len(files)} actual; {len(records)} recorded')
        wrong=[p for p,h in records.items() if not (ROOT/p).is_file() or digest(ROOT/p)!=h]
        check('SHA256SUMS content integrity',not wrong,';'.join(wrong[:20]))
    if manifest.is_file():
        wrong=[r['path'] for r in csv.DictReader(manifest.open()) if not (ROOT/r['path']).is_file() or digest(ROOT/r['path'])!=r['sha256']]
        check('manifest content integrity',not wrong,';'.join(wrong[:20]))
    with tempfile.TemporaryDirectory(prefix='artifact_verify_') as tmp:
        r=subprocess.run([sys.executable,str(ROOT/'reproducibility/verify_reported_results.py'),'--output-dir',tmp],cwd=ROOT,capture_output=True,text=True)
        report=Path(tmp)/'result_verification.csv'
        check('result verifier completes',r.returncode in {0,1} and report.exists(),r.stdout.strip())
        check('all scientific verification passes',r.returncode==0,'Any missing evidence or manuscript/output discrepancy fails validation.')
    promises=list(csv.DictReader((ROOT/'reproducibility/promise_checklist.csv').open()))
    incomplete={r['Promise'] for r in promises if r['Status'] in {'PARTIAL','MISSING'}}
    declared=json.loads((ROOT/'reproducibility/reconstruction_limitations.json').read_text())['limitations']
    described={r['promise'] for r in declared}
    check('all reconstruction limitations explicitly disclosed',incomplete==described and all(r['reason'] and r['author_action'] and (ROOT/r['record']).is_file() for r in declared),f'{len(incomplete)} incomplete reconstruction promises; this is not full reconstruction PASS')
    check('no missing Level 1 evidence',not any(r['Status']=='MISSING' for r in promises))
    if require_full:check('manuscript promises fully satisfied',not incomplete,f'{len(incomplete)} PARTIAL/MISSING; see MISSING_ARTIFACTS.md')
    return rows

def zipcheck(path):
    with zipfile.ZipFile(path) as z:
        bad=z.testzip()
        names=z.namelist()
        ok=not bad and all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts for n in names) and len({n.split('/')[0] for n in names})==1 and all(not stat.S_ISLNK(i.external_attr>>16) for i in z.infolist())
        if not ok:return False
        with tempfile.TemporaryDirectory(prefix='artifact_zipcheck_') as tmp:
            z.extractall(tmp)
            folder=Path(tmp)/names[0].split('/')[0]
            r=subprocess.run([sys.executable,str(folder/'reproducibility/validate_artifact.py'),'--scan-only'],cwd=folder,capture_output=True,text=True)
            return r.returncode==0

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--scan-only',action='store_true');ap.add_argument('--require-full-completeness',action='store_true');ap.add_argument('--zip',type=Path);ap.add_argument('--output-dir',type=Path);ap.add_argument('--identity-file',type=Path,help='Optional local reviewer-held fingerprints; never redistribute author identifiers.');args=ap.parse_args()
    findings,counts=scan(args.identity_file);hygiene=not any(r['severity'] in {'HIGH','ERROR'} for r in findings)
    rows=[] if args.scan_only else validate(args.require_full_completeness)
    if args.zip:rows.append({'check':'ZIP safe extraction and extracted anonymity scan','status':'PASS' if zipcheck(args.zip) else 'FAIL','detail':'Fresh temporary directory'})
    result={'hygiene':'PASS' if hygiene else 'FAIL','scientific_and_integrity_checks':rows,'scan_counts':counts,'findings':findings}
    result['full_reconstruction_completeness']='PARTIAL' if any(r['Status'] in {'PARTIAL','MISSING'} for r in csv.DictReader((ROOT/'reproducibility/promise_checklist.csv').open())) else 'PASS'
    result['overall']='PASS' if hygiene and all(r['status']=='PASS' for r in rows) else 'FAIL'
    if args.output_dir:
        args.output_dir.mkdir(parents=True,exist_ok=True)
        (args.output_dir/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'overall':result['overall'],'hygiene':result['hygiene'],'full_reconstruction_completeness':result['full_reconstruction_completeness'],'files':counts['files'],'findings':findings,'failed_checks':[r for r in rows if r['status']=='FAIL']},indent=2))
    return int(result['overall']!='PASS')
if __name__=='__main__':raise SystemExit(main())
