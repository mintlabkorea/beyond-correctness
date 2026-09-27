# Executable DSL v1

Version: `crta-dsl-1.0.0`

## 목적

DSL은 LLM이 arbitrary formula나 코드를 생성하지 못하게 하면서, medical과 industrial 문서에서 발견되는 작은 relation operation을 동일한 compiler로 실행하기 위한 allowlist다. LLM은 operation 이름, 고정 argument binding, 제한된 parameter만 선택한다.

## 공통 compiler 의미론

1. Column 값은 input contract에 기록된 scale과 offset으로 canonical unit에 변환한다.
2. Concept endpoint는 해당 concept의 `mean`, `std`, `range`, `observed_fraction` channel 중 명시된 하나로 해석한다.
3. Concept channel은 각 schema-local member를 outcome-blind reference partition에서 표준화한 뒤 계산한다. Source는 source-train, target은 target-support만 사용하며 target query는 normalization fit에 사용하지 않는다.
4. Relation operation은 canonicalized value에 row-wise 적용한다. Temporal operation은 group 안에서 stable order sort 후 과거 행만 사용한다.
5. 0 denominator, non-finite value, 부족한 past window는 0으로 대체하지 않고 missing으로 표시한다. 별도 availability mask를 adapter에 전달한다.
6. Compiled cue의 location/scale normalization도 source-train 또는 target-support에서만 fit한다. Query statistic은 사용하지 않는다.
7. Candidate confidence는 primary compiler의 weight가 아니다.
8. Runtime에서 relation cue missing fraction이 `dsl_v1.json`의 한계를 넘으면 candidate를 삭제하지 않는다. 고정 bank는 유지하고 해당 cell에서 cue mask를 보고한다. 이 규칙은 test-set 결과를 보고 topology를 바꾸는 것을 막는다.

## Operation vocabulary

| Operation | Direction | 핵심 조건 |
|---|---|---|
| `difference` | ordered | 두 argument가 같은 unit dimension |
| `absolute_difference` | symmetric | 두 argument가 같은 unit dimension |
| `safe_ratio` | ordered | numeric; denominator runtime mask |
| `normalized_difference` | ordered | 같은 dimension; denominator runtime mask |
| `product` | symmetric | compositional/physical relation에만 허용 |
| `sum2` | set | 같은 dimension의 두 값 |
| `ratio_of_differences` | ordered | 각 difference pair 안에서 dimension 일치 |
| `lag_difference` | temporal | positive lag, group_key, time_index, 과거만 사용 |
| `trailing_slope` | temporal | window 2--32, group_key, time_index, 과거만 사용 |

정확한 arguments, semantic type compatibility, parameter range는 `dsl_v1.json`이 authoritative source다. V1은 generic arithmetic과 past-only temporal primitive만 포함하며, 특정 medical construct나 industrial mechanism에 맞춘 named operation은 포함하지 않는다.

## Concept compiler

Concept candidate는 LLM이 aggregation을 선택하지 않는다. 모든 accepted concept에 같은 compiler를 적용한다.

```text
member-wise standardized values
    -> mean
    -> standard deviation
    -> range
    -> observed fraction
```

이렇게 해야 proposer model에 따라 concept feature width가 달라지지 않는다. 한쪽 schema에 member가 하나뿐이면 `std=0`, `range=0`으로 관례적으로 채우되 availability channel을 함께 보존한다. Pure 1:1 source--target mapping은 concept acceptance 단계에서 제거한다.

## DSL에 없는 관계

문서가 broad association, clinical plausibility 또는 causal language만 제공하고 위 operation으로 실행할 수 없다면 relation candidate가 아니라 abstention으로 기록한다. DSL 확장은 development result를 본 뒤 기존 v1 파일을 수정하는 방식이 아니라 새 contract version으로만 허용한다.
