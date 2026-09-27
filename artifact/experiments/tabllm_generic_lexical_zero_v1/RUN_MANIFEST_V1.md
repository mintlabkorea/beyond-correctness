# TabLLM generic-lexical zero-shot audit — run manifest v1

- Status: complete; 9/9 generic-lexical dataset groups scored and validated.
- Execution date: 2026-09-07 (Asia/Seoul).
- Device: NVIDIA B200 GPU 3; GPUs 0--2 continued the independent exhaustive
  anonymous-reference K=512 extension without interruption.
- Launch: 09:46 KST; completed: 10:00:37 KST.
- New scoring wall time summed over datasets: 513.435 seconds.
- Reference: fixed line-index identities `Feature one` through
  `Feature twenty`; maximum observed field count 20.
- Evaluation: zero shot; sorted union of five released test splits per dataset;
  intended and stable-anonymous outputs reused.
- Evidence: 9 metric files and 9 compressed per-example prediction files.
- Validation: 9/9 pass for analysis status, protocol/wrapper/base-runner hashes,
  reference family and template audit, model/checkpoint/source-tree identity,
  package versions, scoring contract, full/scored row counts, choices, all five
  split memberships and sizes, finite normalized probabilities, unique row
  IDs, prompt-hash shape, prediction file hashes, and prediction row counts.

Frozen hashes:

- Protocol: `81c2ed91a4984f87cac19f75289e4ee9c8c64f0054f4fdfd4f65191167872f97`
- Wrapper: `652192d843081a4a2442809ed33b787a1f80ddfe0c581b56e77f6915e99eaa9d`
- Base runner: `58697774da35b4d2ed573045618d66f557ebf29ffadbd269539862c2dc802b9a`
- Original summarizer: `59fb04b8da92533f9cd42496058dd84f97594a3794c93d2f7c38eb9859f3f177`
- Corrected summarizer: `94c7ff11026637376208c29423e6efc57b618cab07e84feb9982f8a3d0e0f038`
- Summary: `5a86daba85e0157d7cb8cb583cb95856a4b8784f18bd22986eb2eacd3f370505`

The first summarization attempt stopped before reading any AUROC because the
original summarizer incorrectly expected its own hash inside runner-produced
metrics.  `PRE_ADJUDICATION_CORRECTION_V1.md` records the validation-only fix;
the original summarizer is preserved as
`FROZEN_SUMMARIZER_PRE_EXECUTION_V1.py`.

Frozen verdict:
**MACRO_STABLE_ACROSS_ANONYMOUS_AND_GENERIC_LEXICAL**.  Stable-anonymous macro
utility is `+0.088370`, generic-lexical macro utility is `+0.084699`, and the
generic-minus-anonymous shift is `-0.003671`.  No dataset changes utility sign,
although dataset-level magnitudes remain heterogeneous.

Authoritative local root:
`experiments/tabllm_generic_lexical_zero_v1/`.

Mirrored execution root:
`external/tabllm_generic_lexical_zero_v1/` on the B200 server.
