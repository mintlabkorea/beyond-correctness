# Compute requirements

No runtime is invented. Recorded worker-seconds are not wall-clock makespan.

| Path | CPU/GPU | VRAM | Runtime | Storage/downloads |
|---|---|---|---|---|
| Lightweight verify/scan | CPU, standard library | none | measured during packaging; see final report | archive only |
| Controlled/public tree experiments | CPU; retain per-run thread count | none | per-cell wall_seconds retained; whole-grid makespan not recorded | prepared public NHANES panel required |
| TabPFN and MLP extensions | recorded per-run CPU/GPU configuration | not recorded as a minimum | per-cell wall_seconds where present | models downloaded externally |
| TabLLM T0 11B and IA3 adaptation | recorded NVIDIA B200, CUDA 12.8 | 183,359 MiB device memory in manifest; not a measured minimum | run/worker timing retained; full archive-wide makespan not recorded | T0, IA3, T-Few and dataset downloads; weights omitted |
| TransTab | GPU in frozen extension | not recorded as a minimum | per-cell wall_seconds retained | pinned upstream code and prepared input |
| CARTE | GPU in frozen extension | not recorded as a minimum | per-cell wall_seconds retained | pretrained weights and fastText assets |
| Restricted clinical | CPU for frozen XGBoost path | none | per-cell timing retained; total not recorded | authorized HRS/KNHANES inputs; never bundled |

No expensive experiment was launched while packaging. `make reproduce-public/full` are explicit preflights, not queued training jobs.

Public NHANES preparation uses the recovered source-lock code and requires externally downloaded public XPT components; original whole-preparation runtime was not recorded. The output hash must match before controlled model execution.
