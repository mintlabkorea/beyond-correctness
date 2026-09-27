# Ten-endpoint survey-label panel: frozen adjudication

Date: 2026-08-20  
Pre-registration: `iclr_latex_v3/SURVEY_LABEL_PANEL_ENDPOINT_EXPANSION_PREREGISTRATION_V1.md`

## Verdicts

The ten-endpoint `pipeline_table` versus capacity-matched `placebo_table`
contrast is **not confirmatorily evaluable**, despite a large positive numerical
contrast. The raw-code below-chance reversal **does not generalize**.

### P1: correct table versus capacity-matched wrong table

- Endpoint-cluster mean gain: `+0.2494` AUROC.
- Hierarchical endpoint-cluster CI95: `[+0.1824,+0.3087]`.
- Both directions are positive: NHANES->KNHANES `+0.2870`,
  KNHANES->NHANES `+0.2139`.
- All 10 endpoint-cluster means are positive; diabetes-excluded mean `+0.2318`;
  drop-best-two mean `+0.2210`.

However, the frozen construction gate required at least 8/10 finite paired
seeds in every endpoint-direction unit. Cancer KNHANES->NHANES has only 4/10
because the inherited placebo generator sometimes maps away every usable
training label. The gate therefore fails, and the numerical result cannot be
reported as a passed n=10 confirmation of the old `+0.29` headline.

### R1: raw-code reversal

- Pooled raw AUROC: `0.5557`, CI95 `[0.4991,0.6080]`.
- NHANES->KNHANES: `0.5986`; KNHANES->NHANES: `0.5127`.
- Only 3/10 endpoint-cluster raw AUROCs are below `.5`.

Thus the original three-endpoint raw reversal is real and exactly reproduced,
but it is endpoint-specific rather than a general property of the frozen
ten-item panel.

## Endpoint decomposition

| endpoint | pipeline-placebo gain | raw AUROC | pipeline AUROC |
|---|---:|---:|---:|
| angina | +.281 | .669 | .716 |
| arthritis | +.318 | .521 | .791 |
| asthma | +.022 | .587 | .568 |
| cancer | +.237* | .579 | .709 |
| current smoking | +.191 | .425 | .660 |
| diabetes | +.408 | .411 | .928 |
| heart attack | +.277 | .654 | .764 |
| hypertension | +.290 | .474 | .847 |
| kidney disease | +.205 | .602 | .777 |
| stroke | +.265 | .632 | .769 |

`*` Cancer's gain averages only four finite reverse-direction placebo seeds and
therefore fails the construction coverage rule.

## Robust descriptive contrast

The pre-registered descriptive `raw - pipeline_table` contrast is `-0.1973`,
endpoint-cluster CI95 `[-0.2939,-0.1102]`, and is negative in both directions.
Nine of ten endpoint means favor the mapped table; asthma is the exception
(`raw-pipeline=+0.0187`). Pipeline absolute AUROC is `0.7530`, CI95
`[0.6925,0.8112]`.

This is useful evidence that code-to-meaning alignment matters beyond the
original three endpoints, but it was not the registered primary contrast and
must remain descriptive in the current paper.

## Construction and provenance audit

- Complete grid: 10 endpoints x 2 directions x 10 seeds = 200 cells.
- The original three endpoints reproduce all 60 frozen K=256 cells exactly,
  including the two pre-existing reverse-hypertension `NaN` placebo cells.
- The seven added `llm_table` slots equal `pipeline_table` exactly and are
  tagged `codebook_registry_not_llm`; no pooled ten-endpoint LLM claim is made.
- Finite pipeline/placebo coverage is at least 8/10 in 19 of 20
  endpoint-direction units; cancer KNHANES->NHANES is 4/10.

## Paper consequence

Do not promote `+0.29` from effective n=3 to a confirmatory n=10 result, and do
not describe raw transfer as generally below chance. The defensible wording is:

> The original three survey labels show a large correct-versus-placebo gain and
> below-chance raw transfer. Across the frozen ten-endpoint extension, mapped
> labels outperform raw labels by about 0.20 AUROC descriptively, while the
> capacity-matched-placebo confirmation is blocked by comparator evaluability
> in one endpoint-direction unit.
