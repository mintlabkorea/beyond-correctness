# Pre-registration: CAMELS query-basin extension, v1 (utility-bound tightening)

Drafted 2026-08-24; to be freeze-committed before any extension basin is
evaluated.

## Motivation and prior observation disclosure

The frozen G-SIGN-CAMELS v2 addendum found: content separates (documented vs
flipped, 12/12 basins) and utility (documented vs free) does not, with the
E1a positive-control MDE bounding any true utility below ≈ the detectable
range on 12 query-basin clusters. All of that is observed and remains the
paper's confirmatory result. Because the MDE is dominated by the number of
basin clusters (not by seeds), the only honest way to tighten the utility
bound is to add query basins under the frozen outcome-blind selection rule.

This extension is a **precision extension, not a second attempt at the
utility claim**. Declared now: if the utility contrast separates on the
extended cluster set, it is reported as a post-freeze precision finding
clearly distinguished from the frozen 12-basin verdict; if it does not, the
tightened MDE replaces the looser bound in the bounded-null statement. Both
outcomes are reported with the same adjudication rule.

## Frozen design

- **Selection.** Continue the frozen selection rule
  `ascending_sha256(split_salt|"target"|gauge_id)` with the original salt
  over the CAMELS-GB basins that (i) have a v2-daily timeseries file and a
  static-registry row, and (ii) are not among the 24 frozen basins
  (12 query + 12 support pool), using the existing
  `--exclude-target-manifest` machinery of the frozen prepare script. Take
  the next **108** basins in hash order as additional query basins
  (target: 120 query clusters total). A selected basin with no valid
  outcome rows in the fixed 1981–2008 window is dropped and **not
  replaced**; the dropped count is reported.
- **No refitting changes.** Source rows, the 12-basin support pool, support
  draws (`crta-camels-support-v1` hash order), seeds 20–39, support sizes
  {1, 3, 5}, robust channels calibrated on support rows only, the XGBoost
  configuration, and all four arms (`free`, `sign_documented`,
  `sign_flipped`, `sign_random`) are byte-identical to the frozen probe v2.
  Extension basins enter only as additional query rows; they cannot affect
  any fit.
- **Replication gate.** For every support×seed cell and every arm, the
  per-basin metrics on the original 12 query basins must reproduce the
  frozen probe v2 values within 1e-9. A cell failing this gate invalidates
  the run (it would mean the fits were not identical).
- Sign source: the hand-keyed water-balance table (primary). The LLM-table
  replication is out of scope here.

## Adjudication (frozen)

Identical to the frozen v2 addendum: query basin is the independent cluster;
hierarchical basin bootstrap (10,000 reps, seed 20260819); separation =
mean > 0 ∧ CI95 low > 0 ∧ win ≥ 0.60; log1p-RMSE is the verdict metric with
NSE descriptive. On the extended cluster set (12 frozen + retained
extension basins):

- **X1 content**: documented − flipped.
- **X2 utility**: documented − free.
- **X3 content-vs-random**: documented − random.
- **X-MDE**: the E1a injection procedure (constant delta added to the
  documented arm, grid 0 to 0.05 step 0.0005, same separation rule) run on
  the extended cluster set; report the smallest verdict-flipping delta as
  the new bound for the bounded-null statement.

Descriptive: per-basin effect distribution, frozen-12 vs extension-basin
subgroup means (heterogeneity check), and the frozen 12-cluster results
recomputed alongside for continuity.

## Execution

Prepare: the frozen `prepare_crta_v3_camels_native_screen_v1.py`, out-dir
`experiments/crta_v3_camels_query_extension_v1/data`, target-query-count
108, target-support-pool-count 0, `--exclude-target-manifest` pointing at
the frozen manifest. Runner:
`scripts/run_crta_v3_camels_query_extension_probe_v1.py` (imports the
frozen native-screen module; 60 cells; per-cell metrics.json with all
extended-query per-basin values plus the replication-gate report).
Summarizer: `scripts/summarize_crta_v3_camels_query_extension_v1.py`
(X1–X3 and X-MDE). Output:
`experiments/crta_v3_camels_query_extension_v1/`. Committed before launch.
CPU only.
