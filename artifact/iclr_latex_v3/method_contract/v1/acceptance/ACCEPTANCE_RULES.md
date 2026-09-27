# Mechanical acceptance rules v1

Version: `crta-1.0.0`

## Acceptance의 의미

`accepted`는 candidate가 참이거나 인과적으로 옳다는 판정이 아니다. 다음 단계의 deterministic compiler가 안전하게 실행할 수 있고, outcome-blind documentation provenance가 있으며, 사전에 고정된 hypothesis-bank budget 안에 들어간다는 뜻이다.

사람의 semantic review, LLM confidence threshold, downstream validation score는 acceptance에 사용하지 않는다.

## 처리 순서

1. Input/output JSON syntax와 JSON Schema를 검사한다.
2. Contract version, schema pair, document span hash, source/target table 구성을 검사한다.
3. Concept를 `(rank, candidate_id)` 순으로 검사한다.
4. Valid concept 중 fingerprint가 중복되지 않고 budget 안에 있는 candidate를 accept한다.
5. Relation을 `(rank, candidate_id)` 순으로 검사한다. Concept endpoint는 앞 단계에서 accept된 concept만 참조할 수 있다.
6. Valid relation 중 fingerprint가 중복되지 않고 budget 안에 있는 candidate를 accept한다.
7. 모든 candidate에 decision과 reason code를 남기고, raw output과 분리된 accepted bank를 materialize한다.

Invalid candidate가 앞 rank에서 reject되어도 budget을 소비하지 않는다. Budget을 넘긴 valid candidate는 reject한다. Confidence는 정렬이나 수용에 쓰지 않는다.

V1의 공통 최대 budget은 concept 24개, relation 48개다. 이는 목표 개수가 아니라 cap이다. 근거가 부족하면 더 적게 생성하거나 abstain하며, domain별로 cap을 조정하지 않는다.

## Concept acceptance

모든 조건을 만족해야 한다.

- Source와 target 양쪽에 member가 하나 이상 있다.
- 전체 member가 세 개 이상이고 적어도 한쪽에 member가 두 개 이상 있다.
- 각 member column이 해당 schema에 존재한다.
- 각 member는 `candidate_eligible=true`이고 role이 `feature`다.
- 각 member evidence가 input의 해당 column `evidence_span_ids`에 연결되어 있다.
- Evidence span이 존재하고 candidate-eligible이며 해당 table side에 적용된다.
- 같은 column을 한 concept 안에서 중복 사용하지 않는다.
- 이미 accepted된 concept와 source/target member fingerprint가 같지 않다.
- Accepted concept 수가 `max_concepts`를 넘지 않는다.

## Relation acceptance

모든 조건을 만족해야 한다.

- Operation이 DSL에 존재한다.
- `semantic_type`, `direction`, argument 이름, parameter가 DSL contract와 정확히 맞는다.
- Source와 target binding이 같은 argument set을 가진다.
- Value endpoint column은 numeric/integer이고 eligible feature다.
- Concept endpoint는 accepted concept와 고정 concept channel을 참조한다.
- Temporal `group`과 `order`만 각각 `group_key`, `time_index` role을 참조할 수 있다.
- Target/outcome proxy/post-outcome/identifier/protected/unknown column을 value로 참조하지 않는다.
- 각 argument slot의 source/target unit dimension과 endpoint kind가 호환된다.
- DSL이 지정한 same-dimension group을 만족한다.
- Positive argument가 필요한 operation은 input value-domain metadata가 `positive` 또는 `nonnegative`다.
- Lag/window는 양수 범위이며 future look-ahead를 표현할 수 없다.
- Source와 target 각각 eligible relation evidence span을 하나 이상 가진다.
- 동일 operation과 endpoint binding fingerprint를 가진 relation이 이미 accept되지 않았다.
- Accepted relation 수가 `max_relations`를 넘지 않는다.

## Rejection codes

| Code | 의미 |
|---|---|
| `R_CONTRACT_MISMATCH` | contract version 또는 schema pair 불일치 |
| `R_DUPLICATE_ID` | candidate ID 중복 |
| `R_DUPLICATE_RANK` | candidate kind 안에서 rank 중복 |
| `R_BUDGET_EXCEEDED` | valid candidate이지만 고정 budget 초과 |
| `R_CONCEPT_NOT_CROSS_SCHEMA` | source 또는 target member 없음 |
| `R_CONCEPT_NOT_GROUP` | pure 1:1 mapping 등 group 최소 조건 실패 |
| `R_DUPLICATE_MEMBER` | 한 concept 안의 column 중복 |
| `R_COLUMN_NOT_FOUND` | schema에 없는 column 참조 |
| `R_COLUMN_INELIGIBLE` | candidate-eligible이 아닌 column 참조 |
| `R_LEAKAGE_ROLE` | 금지된 role을 value/member로 사용 |
| `R_EVIDENCE_NOT_FOUND` | 없는 span ID 참조 |
| `R_EVIDENCE_INELIGIBLE` | 제외된 span 참조 |
| `R_EVIDENCE_SCOPE` | span이 해당 source/target side에 적용되지 않음 |
| `R_MEMBER_EVIDENCE_NOT_LINKED` | concept member의 column documentation과 evidence 불일치 |
| `R_RELATION_EVIDENCE_MISSING` | relation side에 evidence가 없음 |
| `R_UNKNOWN_OPERATION` | DSL 밖 operation 사용 |
| `R_SEMANTIC_TYPE_MISMATCH` | operation과 semantic type 불일치 |
| `R_DIRECTION_MISMATCH` | operation direction contract 불일치 |
| `R_ARGUMENT_SET_MISMATCH` | argument 이름 누락·추가 또는 양쪽 binding 불일치 |
| `R_PARAMETER_MISMATCH` | parameter 이름, type 또는 범위 불일치 |
| `R_REF_NOT_ACCEPTED` | reject/unknown concept 참조 |
| `R_ENDPOINT_KIND_MISMATCH` | 같은 argument slot의 source/target endpoint kind 불일치 |
| `R_DUPLICATE_ENDPOINT` | 서로 달라야 할 value argument에 같은 endpoint 반복 |
| `R_NON_NUMERIC_ARGUMENT` | value operation에 비수치 column 사용 |
| `R_UNIT_DIMENSION_UNKNOWN` | 필요한 unit dimension이 unknown |
| `R_UNIT_CONTRACT` | same-dimension 또는 cross-schema unit contract 실패 |
| `R_VALUE_DOMAIN` | positive-domain operation의 metadata 조건 실패 |
| `R_TEMPORAL_CONTEXT_ROLE` | temporal structural argument role 불일치 |
| `R_DUPLICATE_CANDIDATE` | 이미 accepted된 semantic fingerprint와 중복 |

한 candidate는 여러 rejection code를 가질 수 있다. 이 ledger는 RQ1의 accepted/rejected count와 rejection-reason table의 원자료가 된다.
