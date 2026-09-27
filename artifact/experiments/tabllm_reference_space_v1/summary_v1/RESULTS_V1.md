# TabLLM admissible-reference space audit — results v1

Frozen verdict: **MAGNITUDE_SENSITIVE_SIGN_ROBUST**.

Canonical macro utility: `+0.0884` AUROC.
Combinatorial macro reference envelope: `[+0.0486, +0.1618]` (span `0.1133`).
Independent-uniform product-space SD: `0.0101`; 95% Monte Carlo interval `[+0.0858, +0.1255]`.
Canonical percentile in that product space: `0.044`.

The envelope is a prespecified sensitivity summary over the frozen
candidate library. Its extremal members are not selected as revised
references, and the result is limited to this tightly matched anonymous-
identifier space and fixed nine-dataset panel.

## Dataset envelopes

| Dataset | Canonical | Minimum | Maximum | Span | Positive refs |
|---|---:|---:|---:|---:|---:|
| bank | +0.0894 | +0.0223 | +0.1659 | 0.1436 | 24/24 |
| blood | +0.1143 | +0.0933 | +0.2461 | 0.1527 | 24/24 |
| calhousing | +0.0531 | -0.0109 | +0.1049 | 0.1159 | 21/24 |
| car | +0.3004 | +0.2701 | +0.3453 | 0.0752 | 24/24 |
| creditg | -0.0035 | -0.0402 | +0.0454 | 0.0856 | 15/24 |
| diabetes | +0.1640 | +0.0877 | +0.2174 | 0.1297 | 24/24 |
| heart | -0.0208 | -0.0208 | +0.1425 | 0.1633 | 20/24 |
| income | +0.0738 | +0.0553 | +0.1063 | 0.0510 | 24/24 |
| jungle | +0.0245 | -0.0196 | +0.0828 | 0.1023 | 22/24 |
