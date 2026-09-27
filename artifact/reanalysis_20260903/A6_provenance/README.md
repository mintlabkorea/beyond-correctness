# A6. Provenance and timestamp audit

## Coverage finding

The exact gate was found in a contemporaneously committed protocol; it was not reconstructed from outcomes. The gate requires at least 8/10 finite intended/wrong pairs in every endpoint-direction unit. `cancer_history/kn2nh` has 4/10, so the full gate fails. See `coverage_criterion.md` and `coverage.json`.

## Timestamp finding

No retained item qualifies as A, externally timestamped before execution. Three analyses are classified B because a committed plan is present but the ordering relative to execution depends on local output/log timestamps and no push-time or immutable scheduler record is available. Five are classified C because metrics or summaries embed an exact manifest/script hash, but run time is not independently verifiable.

The local `b200/*` remote-tracking refs contain the cited commits, but the local repository does not retain when those commits were pushed. Current presence on a remote-tracking ref does not prove pre-run push time, so it was not promoted to category A.

`provenance_timestamps.csv` and `.json` contain the complete mapping from analysis to manifest/hash, commit time, estimated local run start, evidence, classification, and reason. “Run start” is explicitly an estimate from the earliest retained metric mtime minus its recorded wall time; it is not an external timestamp.

The reconstruction proxy is correctly treated as post-result exploratory. Its script is hash-linked in the output, but there is no pre-execution decision manifest for the proxy analysis itself.

## Reproduction

```bash
python reanalysis_20260903/A6_provenance/audit_provenance.py
```

Outputs: `coverage.json`, `provenance_timestamps.csv`, and `provenance_timestamps.json`.
