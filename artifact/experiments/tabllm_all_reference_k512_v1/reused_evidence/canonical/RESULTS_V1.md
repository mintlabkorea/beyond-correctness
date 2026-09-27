# TabLLM stable-anonymous support ladder — results v1

Frozen verdict: **SUPPORTED_WITHIN_FIXED_PANEL**.

The unweighted macro point trajectory for `S - R_anon` is +0.0884 → +0.0727 → +0.0350 → +0.0071 at
`k = 0, 4, 32, 512`.  The primary decay is +0.0813; its
dataset-cluster bootstrap 95% interval is [+0.0245, +0.1479]
and its Student-t interval is [+0.0044, +0.1582].
The predeclared supervised-only decay (`k=4` to `k=512`) is
+0.0656.  Dropping Car, the primary decay is
+0.0548.

This directly addresses the format confound in the published `List Only Values`
ladder: `R_anon` preserves List Template serialization and changes only stable
feature-name strings.  The claim is limited to TabLLM's externally fixed but
purposively assembled nine-dataset panel.  Macro monotonicity, if present, is a
descriptive point trajectory and not a dataset-wise or population-level law.

All 270 nonzero-shot cells passed artifact, pairing, step-count, probability,
checkpoint, and metric-recomputation validation before this report was written.
