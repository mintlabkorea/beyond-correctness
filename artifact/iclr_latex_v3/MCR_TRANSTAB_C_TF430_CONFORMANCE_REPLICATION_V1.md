# TransTab C-only transformers-4.30 conformance replication, v1

**Frozen before replication evidence execution:** 2026-08-25. This is an
environment-conformance replication triggered after the complete v1 results
were reviewed. It is neither blind nor confirmatory and cannot upgrade the
review-triggered parent extension into an original confirmatory claim.

## Reason for the replication

The completed v1 grid used the pre-existing server environment's
`transformers==5.12.0`. The frozen official TransTab source declares
`transformers<=4.30.0` in `requirements.txt` (SHA-256
`44da21453f6b7438c2d05f5efc3b163c5fdee7e9393ea303197efbd266699f4d`).
Although v1 completed without runtime or numerical failure, it is not an
official-dependency-range reproduction. This replication changes that one
environmental axis.

## Immutable parent binding

- Parent result summary SHA-256:
  `ff8b5ab665401add954475ff057d44e22ff169983906528760d0193a925206d7`.
- Exact evidence runner SHA-256:
  `b293ba1140eb956d485ea43f5f2d3dc58fff06cd875d0194031366f76f2f5b78`.
- Parent protocol SHA-256:
  `238899a7c7f996f4f73badf46b7b9a5666709e2b4d6917737f095b1165904637`.
- Official TransTab commit:
  `fdb34cf38abda73ee6a741b802fe226cc89ba7b5`; fixed source-tree SHA-256:
  `6db3ddac43009ff15e0bc6b2f34f0cc900c39c632c323413840fc1c84b83f80e`.

The same runner is invoked, not copied or edited. Therefore all 60 frozen MCR
cells, three arms (`correct`, `c_wrong`, `c_reference`), K in {32, 512}, source
and query rows, seeds, feature preparation, label normalization, model defaults,
50 epochs, optimizer, and raw-regression-logit evaluation are identical to v1.
The disclosed dataset-indexing correction is also identical.

## Allowed environment difference

The replication uses a fresh overlay virtual environment with
`transformers==4.30.0` and the dependency versions resolved for that exact
package. The inherited CUDA/PyTorch, NumPy, pandas, scikit-learn, hardware, and
official TransTab source remain unchanged. The environment's `pip freeze` and
package-location audit are saved with the result tree before the full grid is
opened.

An engineering smoke may run additive realization 0, K=32, and all three arms
for two epochs in a separate `_smoke` tree. It is inadmissible for analysis and
may only test imports, CUDA, tokenizer loading, raw-logit prediction, and
finite outputs.

**Engineering-smoke disclosure:** the allowed smoke completed all three arms
in 17.037 seconds with `transformers==4.30.0`, `tokenizers==0.13.3`, finite raw
regression outputs, and the frozen runner/source hashes. Its three nMSE values
were bit-identical to the earlier v1 engineering smoke. No data, model,
hyperparameter, arm, comparison, or reporting choice changed after the smoke.

## Completion and comparison

The replication is complete only with 60/60 realization cells, one provenance
tuple, `transformers==4.30.0` in every cell, identical construction hashes
against v1, finite metrics for all 360 fits, and no runtime failure. The frozen
v1 summarizer is rerun on the replication tree.

A paired environment comparison reports, for every family, support budget,
arm, and frozen contrast, the replication-minus-v1 difference and a
realization-bootstrap interval. Because v1 outcomes were known before this
document, no post-hoc numerical equivalence margin or pass threshold is added.
Agreement, disagreement, and sign changes are all reported. The v1 result tree
is never overwritten.

## Hardware

One family runs on each of B200 GPUs 0, 1, and 2. GPU 3 remains unused under
the user's explicit allocation. Concurrent CARTE execution may change wall
time but not the frozen statistical or model contract.
