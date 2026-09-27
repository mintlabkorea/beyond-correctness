# TabLLM generic-lexical zero-shot reference audit — results v1

Frozen verdict: **MACRO_STABLE_ACROSS_ANONYMOUS_AND_GENERIC_LEXICAL**.

- Stable-anonymous macro utility: `+0.088370`
- Generic-lexical macro utility: `+0.084699`
- Generic-minus-anonymous utility shift: `-0.003671`
- Paired dataset-bootstrap 95% interval: `[-0.031068, +0.027876]`
- Dataset-level utility sign changes: `0/9`
- New scoring wall time: `513.4` seconds

| Dataset | u(anonymous) | u(generic lexical) | Shift | Sign changed |
|---|---:|---:|---:|---:|
| bank | +0.089379 | +0.052825 | -0.036554 | False |
| blood | +0.114328 | +0.108181 | -0.006148 | False |
| calhousing | +0.053134 | +0.049559 | -0.003575 | False |
| car | +0.300376 | +0.367118 | +0.066742 | False |
| creditg | -0.003479 | -0.022311 | -0.018831 | False |
| diabetes | +0.164045 | +0.138384 | -0.025661 | False |
| heart | -0.020782 | -0.086036 | -0.065254 | False |
| income | +0.073816 | +0.047214 | -0.026602 | False |
| jungle | +0.024512 | +0.107354 | +0.082842 | False |

This fixed-panel zero-shot audit does not test target-support attenuation
or invariance over arbitrary lexical reference families.
