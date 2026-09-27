# A1. TabLLM reference-construction sensitivity

## Result

Retained, within-run predictions support a direct comparison of two neutral control constructions:

- `Rpub`: published `List Only Values`
- `Ranon`: stable-anonymous `List Template`

The nine-dataset macro estimates are:

| Estimand | Estimate | 95% CI |
|---|---:|---:|
| `U_pub = S - Rpub` | 0.0800 | [0.0047, 0.1539] |
| `U_anon = S - Ranon` | 0.0884 | [0.0323, 0.1540] |
| `Delta_ref = U_anon - U_pub` | 0.0084 | [-0.0469, 0.0600] |

Inference uses the retained fixed split rows, paired example-level AUROC influence covariance and a Gaussian multiplier within each dataset, followed by a dataset bootstrap. There are 10,000 draws.

`Delta_ref` is not separated from zero at macro level, so the macro conclusion is qualitatively stable. Dataset-level differences are heterogeneous: the CI for `Delta_ref` is above zero for bank, calhousing, creditg, and diabetes; below zero for heart and jungle; and includes zero for blood, car, and income. The largest absolute differences are heart (-0.1619), creditg (+0.1363), diabetes (+0.0695), and bank (+0.0668).

Credit-g changes qualitative interpretation with control construction: `U_pub=-0.1398 [-0.2023,-0.0790]`, whereas `U_anon=-0.0035 [-0.0471,0.0396]`. Thus Rpub implies significant negative utility while Ranon is unresolved near zero. This is why the result is a reference/control-construction sensitivity, not evidence that the two controls instantiate an identical estimand.

This does not establish that both controls are equally admissible. It only compares their numerical consequences. The manuscript's design rationale for treating `Ranon` as the format-matched reference remains a separate issue.

## Unavailable extension

The retained support ladder has `Ranon` but no matching within-run `Rpub` predictions. A two-reference support-ladder comparison would require new fitting and was therefore not run.

## Reproduction

```bash
python reanalysis_20260903/A1_tabllm_reference/analyze_tabllm_reference.py
```

Machine-readable outputs are `tabllm_reference_sensitivity.csv` and `tabllm_reference_sensitivity_macro.json`. The latter records SHA-256 identifiers for every consumed prediction and metric artifact. Parent arm point estimates reproduce with maximum error 0.

Primary sources: `experiments/tabllm_retrospective_audit_v1/`, `experiments/tabllm_retrospective_split_manifest_v1.json`, and `scripts/summarize_tabllm_retrospective_audit_v1.py`.
