# Thread-count audit

Original frozen aggregate metrics are included for all 40 cells under `experiments/_recheck_vr_threads1/`, the earlier value-redundancy run and the redundancy ladder. `reproducibility/H-03_thread_count_audit.tex` preserves the historical prose unchanged.

Run `python3 reproducibility/audit_aggregate_records.py` for a NEW packaging-time comparison. `paired_aggregate_comparison.csv` compares five common arm nMSEs × 40 cells × two supports, separately for each learner. The rerun has 400/400 exact stored numeric matches for each learner. Against the earlier run, HistGB has 104 exact differences, of which 92 exceed 1e-12 (maximum .007528); XGB has 16 exact differences, all at most 2.23e-16. JSON numeric equality does not establish in-memory bitwise identity. The archived prose's 800 HistGB values and bitwise wording are preserved as historical text; current Appendix H.1 reports the verifiable 400 common-arm stored nMSE values and the distinction between exact numeric equality and the 1e-12 tolerance. See resolved I07.

Ladder metrics explicitly record one thread. The original value-redundancy and rerun metrics omit a thread field; the one-/two-thread attribution is recorded in the historical prose. The controlled primary runner defaults to two threads. Do not impose a common thread count on historical runs. No models were refitted during packaging.
