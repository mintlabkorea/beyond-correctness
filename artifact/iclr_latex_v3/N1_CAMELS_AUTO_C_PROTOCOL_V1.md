# N1 CAMELS-US -> CAMELS-GB Auto-C protocol v1

Status: data/split and method protocol frozen; efficacy sealed behind task-order gate  
Frozen: 2026-08-14  
Parent contract: [`AUTO_C_BENCHMARK_COMMON_CONTRACT_V1.md`](AUTO_C_BENCHMARK_COMMON_CONTRACT_V1.md)

## Task and leakage-safe split

- Direction: CAMELS-US native source -> CAMELS-GB v2 native target
- Endpoint: daily specific discharge in mm/day, modeled as `log1p(discharge)`
- Split unit: basin/gauge ID; no row-level split is permitted
- Source basins: 64; source rows: 90,776 on the fixed weekly cadence
- Target support pool: 12 basins; fixed query: 12 disjoint basins; target rows: 33,543
- Support levels: 1, 3, and 5 target basins
- Frozen support-order seeds: 50--59; support levels are nested within a seed
- Date window: 1981-01-01 through 2008-09-30, with a 30-day feature warm-up
- Features: documentation-listed native static attributes, native meteorology, past-only 3/7/30
  day trailing meteorology, and deterministic seasonal terms
- Forbidden features: discharge lags, future values, query-fitted normalization, and target-derived
  outcome features

The confirmatory target split excludes all 24 basins used anywhere in the earlier development
target query/support pools before hash selection. Audit found zero development-target overlap and
zero support/query overlap. A first candidate split with overlap was abandoned before any model or
metric execution and is visibly marked as excluded.

- confirmatory split salt: `crta-v3-n1-camels-confirmatory-20260814-v2`
- source data SHA-256:
  `a386a89918150c703ccdc3c11610c119ba4d1fb7fe9911552f7b5f8f7ca6a773`
- target data SHA-256:
  `230664333d85c5d711286d650a07cfd16e1568290df1835567f96752b8d97624`
- split manifest SHA-256:
  `1f51025cf226347840fa0d1addec7f54e6520b5f2c780a75d70ebce4aa71075a`

## Frozen proposer and compiler contract

- schema pair: `camels_us_to_gb_native_v1`
- proposer payload SHA-256:
  `5c528002b46b0523427907ae2a81b64d89fdcb8136997f92d855d6db0f6c8819`
- prompt SHA-256:
  `cc514066bfbcc33d0674905dc6c7271bf548393f64e361a9c77a0a04c43eb88b`
- DSL SHA-256:
  `ffeb22b6502d431ec276d44c558d42fbc5bc5ffb5b079c52986bc248facbc28b`
- fixed adapter interface width: 192

The frozen Codex GPT-5.6-Sol ledger is contract-valid with 12 accepted concepts and one relation;
the utility matrix compiles only the 12 concepts. Its decision-ledger SHA-256 is
`22e2493d96678041aeb5b9bbe053c87ad3c907bfbb386166e724a90f919aaf31`.
Other frozen model banks remain classified under the common nonempty/empty/invalid/blocked policy.
The hydrology bank is not derived from or mixed with medical concept vocabulary.

## Utility execution and analysis

Shared Base and each usable model-specific Auto-C use identical source rows, support basins, query
basins, base features, target weight, and fixed-width adapter. The learner is XGBoost on
`log1p(discharge)`: 300 trees, depth 6, learning rate 0.05, min-child-weight 5,
subsample/column-sample 0.8, and target-support weight 10. Base has an all-zero 192-slot block.

The first-pass grid is 3 supports x 10 seeds = 30 shared Base cells and 30 Auto-C cells per usable
nonempty model. Valid-empty banks are declared zero-gain identities without redundant training;
invalid or blocked banks remain visible `N/A` rows.

Primary utility is the positive-when-better mean of paired **basin-specific** log1p-RMSE
reductions over the 12 fixed query basins, three supports, and ten support seeds. This makes the
prespecified basin/support/seed hierarchy explicit before efficacy is opened; pooled-row log1p-RMSE,
native RMSE and MAE, and mean/median basin NSE remain secondary. Every summary must serialize source,
support, query, query-outcome, data, payload, ledger, DSL, prediction, and compiler hashes. Aggregation is prohibited
until all expected cells pass completeness, finite-metric, role, width, bank, data, and split-hash
checks. Intervals use 50,000 basin/support/seed hierarchical bootstrap draws with seed 20260814.

Relation is absent from the N1 main matrix. TransTab regression is structural `N/A`; CARTE runs only
if its native-interface preflight and sealed source-budget manifest pass before efficacy opens.
