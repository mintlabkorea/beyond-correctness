# TabLLM retrospective audit run manifest, v1

- Status: frozen full-grid output; 36/36 dataset--arm cells complete.
- Execution date: 2026-08-27.
- Hardware: NVIDIA B200 (183,359 MiB), driver 570.211.01.
- Runtime: Linux 5.15.0-174-generic; PyTorch
  `2.12.0.dev20260408+cu128`; CUDA runtime 12.8.
- Parallelization: one arm per visible GPU; deterministic zero-shot scoring,
  no task-specific fit.
- Cell outputs plus summary (excluding this manifest): 73 files, 27 MiB;
  aggregate sorted-file SHA-256
  `b3440d414c55f92f9142f118f5ce88ddc3cafbbf4a7dd8965560d1e66f630779`.
- Frozen split manifest SHA-256:
  `119e48aab7999475d82d4258dedb0875d54fa2613c8c31aae1dbda2a1942c831`.
- Summary SHA-256:
  `e6d85f64f13a122ed9e30adb0795ed1c42785b2b6729504432da76f7c52c1600`.

Each cell's `metrics.json` records the TabLLM and T-Few commits, aggregate
raw-data/serialization hash, protocol and runner hashes, local T0 snapshot
revision, IA3 checkpoint hash, package versions, scoring contract, device,
and compatibility/source discrepancy.  Each compressed prediction record
contains the stable example ID, label, normalized class scores, prediction,
arm, and prompt hash.

Compatibility repairs made before the full grid was inspected:

1. The TabLLM repository vendors only a subset of T-Few, so the complete
   corresponding upstream T-Few commit supplies `modify_model.py`.
2. Protobuf uses the pure-Python compatibility implementation in the pinned
   execution environment.
3. IA3 parameters created in float32 are cast with the complete modified T0
   module to bfloat16, matching released T-Few compute precision.

The paper names T0pp once, while the released `t011b` configuration and IA3
checkpoint use `bigscience/T0`; this run follows the released executable
configuration.  With modern compatibility dependencies, 21/27 reproduced
published-arm means are within .015 AUROC of the paper's two-decimal printed
values and the maximum deviation is .0347.  The run is therefore called a
released-code compatibility reproduction, not a bit-exact numerical
reproduction of the printed tables.
