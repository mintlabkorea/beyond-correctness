"""First-epoch wall-time calibration; no predictions or efficacy analysis."""
import json
import time
import common as C

def main():
    design=C.verify_freeze()
    gate=C.read(C.RUN/'AUDIT_SUMMARY.json')
    assert gate['all_pass']
    b,t,m=C.base(),C.tabllm(),C.manifest()
    import torch
    started=time.monotonic()
    tokenizer,model,initial,model_audit=b.load_model(C.MODEL,C.TFEW,C.CHECKPOINT,'cuda:2')
    load_seconds=time.monotonic()-started
    d='bank'; f='R2'; a='ref_00'; n=512; s=42
    frame=b.build_full_dataset(t,C.TABLLM,d)
    split=C.read(C.RUN/'audit'/d/'memberships.json')[str(s)]
    rows=split['support'][str(n)]
    strings=C.notes(t,[row for _,row in frame.loc[rows].iterrows()],d,C.template_for(t,d,f,a,m))
    prompts=[note+'\n\n'+b.QUESTIONS[d] for note in strings]
    audit=C.audit_rows(d,f,a)
    assert all(C.textsha(p)==audit[r]['prompt_sha256'] for r,p in zip(rows,prompts))
    train=b.PreparedTrainDataset(tokenizer,prompts,frame.loc[rows,'label'].astype(int).tolist(),b.CHOICES[d],rows)
    b.reset_trainable_state(model,initial)
    torch.cuda.synchronize()
    started=time.monotonic()
    b.train_cell(model,tokenizer,train,s,n,'cuda:2',128)
    torch.cuda.synchronize()
    seconds=time.monotonic()-started
    # Structural count, without consulting historical AUROCs.
    fresh_steps=0;reuse_eligible_steps=0
    for dataset,shot,seed,family,assignment in C.cells():
        steps=30*(shot//4)
        reuse=(family=='intended' or (family=='R1' and
               (assignment in ('ref_00','ref_04','ref_22') or shot==512)))
        if reuse: reuse_eligible_steps+=steps
        else: fresh_steps+=steps
    report={'status':'first_epoch_complete','evidence_status':'timing_only_inadmissible',
        'cell':[d,n,s,f,a],'epochs':1,'optimizer_steps':128,'epoch_seconds':seconds,
        'seconds_per_step':seconds/128,'load_seconds':load_seconds,
        'expected_new_training_steps_if_reuse_validates':fresh_steps,
        'upper_training_steps_if_all_reuse_fails':fresh_steps+reuse_eligible_steps,
        'single_gpu_training_hours_at_bank_rate':fresh_steps*seconds/128/3600,
        'single_gpu_training_hours_without_reuse_at_bank_rate':(fresh_steps+reuse_eligible_steps)*seconds/128/3600,
        'limitations':'Bank is a long-input calibration; other datasets differ. Excludes all inference, serialization, checkpoint I/O, queue contention and analysis.',
        'design_sha256':C.sha(C.RUN/'FROZEN_DESIGN.json')}
    C.write(C.RUN/'timing_only/FIRST_EPOCH.json',report)
    print(json.dumps(report),flush=True)

if __name__=='__main__': main()
