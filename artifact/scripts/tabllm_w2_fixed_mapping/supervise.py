"""Audit -> timing -> primary -> analysis -> secondary -> final analysis."""
import datetime
import fcntl
import os
import subprocess
import sys
from pathlib import Path
import common as C

def status(state,**kwargs):
    C.write(C.RUN/'STATUS.json',{'state':state,'pid':os.getpid(),
        'updated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**kwargs})

def run(name,*args):
    status(name)
    with (C.RUN/'logs'/f'{name}.log').open('a') as h:
        subprocess.run([sys.executable,str(Path(__file__).with_name(args[0])),*args[1:]],
                       stdout=h,stderr=subprocess.STDOUT,check=True)

def main():
    (C.RUN/'logs').mkdir(parents=True,exist_ok=True)
    with (C.RUN/'supervisor.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            if not (C.RUN/'FROZEN_DESIGN.json').exists(): run('freeze','audit.py','freeze')
            C.verify_freeze()
            run('input_audit','audit.py','audit')
            gate=C.read(C.RUN/'AUDIT_SUMMARY.json')
            if not gate['all_pass']:
                status('inadmissible_stop',admissible_families=gate['admissible_families'])
                return
            used=int(subprocess.check_output(['nvidia-smi','-i','2','--query-gpu=memory.used',
                                              '--format=csv,noheader,nounits'],text=True).strip())
            if used>=1024: raise RuntimeError(f'GPU 2 is no longer free: {used} MiB')
            if not (C.RUN/'timing_only/FIRST_EPOCH.json').exists(): run('first_epoch_timing','timing.py')
            run('primary_evidence','worker.py','--gpu','2','--phase','primary')
            run('primary_analysis','analyze.py','--phase','primary')
            run('secondary_evidence','worker.py','--gpu','2','--phase','secondary')
            run('full_analysis','analyze.py','--phase','full')
            status('complete')
        except Exception as exc:
            status('failed',error=repr(exc))
            raise

if __name__=='__main__': main()
