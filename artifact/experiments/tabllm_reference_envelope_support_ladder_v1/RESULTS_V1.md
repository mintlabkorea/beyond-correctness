# TabLLM global-reference envelope support ladder — results v1

Sensitivity verdict: **SIGN_ROBUST_ACROSS_SELECTED_REFERENCES**.

This is a post-result, three-reference sensitivity analysis. It has not been
incorporated into manuscript text, tables, or figures.

| Reference | Role | u(0) | u(4) | u(32) | u(512) | Decay 0→512 | Bootstrap 95% CI | t 95% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `ref_00` | lower_canonical | +0.0884 | +0.0727 | +0.0350 | +0.0071 | +0.0813 | [+0.0245, +0.1479] | [+0.0044, +0.1582] |
| `ref_22` | center | +0.1060 | +0.0754 | +0.0304 | +0.0058 | +0.1002 | [+0.0451, +0.1597] | [+0.0292, +0.1712] |
| `ref_04` | upper | +0.1240 | +0.0863 | +0.0371 | +0.0098 | +0.1142 | [+0.0573, +0.1786] | [+0.0382, +0.1902] |

Decay magnitude range: `+0.0813` to `+0.1142`. All bootstrap and t lower bounds positive: `True`.

All 270 new cells and 270 reused nonzero cells passed artifact, step-count, pairing, probability, and metric validation.
