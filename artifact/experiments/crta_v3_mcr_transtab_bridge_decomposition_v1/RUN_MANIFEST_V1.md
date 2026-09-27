# TransTab bridge decomposition run manifest, v1

- Analysis status: post-result, review-triggered mechanism extension.
- Completion: 60/60 family-by-realization cells (3 families x 20
  realizations); each cell contains K in {32, 512} and all four arms.
- Arms: `correct`, `shared_anonymous`, `distinct_anonymous`, `c_wrong`.
- Scientific freeze:
  `iclr_latex_v3/MCR_TRANSTAB_BRIDGE_DECOMPOSITION_FREEZE_V1.md`.
- Protocol SHA-256:
  `63c2cf9079259518b268d71bd621be131720e8ff59f166a19d6617ecd79a585a`.
- Runner SHA-256:
  `07c33bf9ddb219127c77c2a509843a986b90c47d4332c2bf4f795bd17a91ef19`.
- Summarizer SHA-256:
  `e64be3e0eb050191dead76b579e93e6868a218e5fff3c339e83aa029ff4d4d48`.
- Bootstrap: 10,000 paired realization resamples within each fixed
  family-by-support stratum.
- Score: Q = -MSE / Var(y_query); positive favors the first named arm.
- Full machine-readable summary: `SUMMARY_V1.json`.

## Frozen-contrast outcome

At K=32, conventional correct-minus-wrong content is +.491 to +.577.
Name/token content beyond shared identity is -.011 to +.001, shared identity
is +.114 to +.129, and the false bridge is -.456 to -.361.  The magnitude of
false-bridge damage is 74--80% of the conventional gap.

At K=512, conventional content is +.157 to +.165.  Name/token content remains
non-positive, shared identity attenuates to +.007 to +.009, and the false
bridge is -.165 to -.152.  The magnitude of false-bridge damage is 97--100%
of the conventional gap.

No name/token-content interval is positive in any of the six strata.  The
exact algebraic decomposition residual is at most 1.11e-16.
