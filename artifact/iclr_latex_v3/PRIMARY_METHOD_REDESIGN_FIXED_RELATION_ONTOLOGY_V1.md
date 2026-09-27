# Appendix relation redesign: fixed relation ontology

결정일: 2026-08-14  
상태: appendix ablation protocol; main method는 Auto Concept

> **Concept-first supersession.** M1 complete zero-active result와 2026-08-14 사용자 결정을
> 반영해 이 문서는 더 이상 primary method를 정의하지 않는다. Fixed-ontology relation은
> 사전 지정한 M1/M4/N2 appendix ablation에만 적용되며 main task closure를 막지 않는다.

## 결정

Relation vocabulary를 LLM이 문서마다 새로 추출하거나 shortlist하지 않는다. 초기 의료
relation type은 작고 공개된 ontology로 고정한다.

- `causal_ancestor_of`
- `associated_with`
- `diagnostic_evidence_for`
- `treatment_for`
- `component_of`
- `derived_from`

`symptom_or_manifestation_of`, `complication_of`, `threshold_defines`,
`repeated_measure_of`, `temporal_transition`은 extension이며 appendix v1 freeze에는 포함하지
않는다.

고정 ontology가 hand-crafted라는 사실은 숨기지 않는다. 다만 이것은 데이터셋별 endpoint나
edge를 사람이 고르는 것이 아니라, 모든 cohort와 proposer에 동일하게 공개되는 label
space와 type signature를 정하는 것이다. 데이터셋별 concept, role, alignment, evidence,
polarity는 자동 pipeline이 결정한다.

## Appendix pipeline

```text
source/target documentation
        ↓
LLM concept extraction + exact provenance
        ↓
cross-schema concept alignment
        ↓
LLM concept-role assignment + exact provenance
        ↓
fixed ontology role-signature filtering
        ↓
deterministic exhaustive relation-instance enumeration
        ↓
document verification: +1 / 0 / -1
        ↓
shared frozen relation-text encoder + transfer adapter
```

LLM role-assignment 출력에는 relation type이나 edge가 없다. Relation instance는 검증된
aligned concept node의 모든 admissible pair에서 코드가 전수 생성한다. 따라서 relation
candidate recall이 Qwen, Gemma, Codex의 shortlist 성향에 좌우되지 않는다.

## 정확한 용어

사용할 표현:

> Document-grounded concept and role extraction with fixed-ontology relation enumeration and evidence verification.

피할 표현:

> LLM extracts an open-ended relation ontology from documents.

Relation에 대한 자동화 claim은 다음 범위다.

1. 데이터별 edge를 사람이 선택하지 않는다.
2. 고정 signature를 만족하는 edge hypothesis를 빠짐없이 생성한다.
3. 문서 근거가 없으면 `0`으로 gate한다.
4. 명시적 지지 또는 반박이 있는 `+1/-1`만 relation adapter에 활성화한다.

## Concept role의 두 channel

### Substantive semantic role

- exposure/behavior
- condition/disease
- symptom/sign
- measurement/finding
- treatment/intervention
- functional outcome
- demographic/social/environmental context

Diagnosis와 treatment처럼 substantive role이 섞인 concept은 relation endpoint에서
제외한다.

### Auxiliary member kind

- question wording
- change/dispute flag
- timing/wave qualifier
- missingness/imputation flag
- unit/format metadata
- other protocol metadata

보조 metadata는 substantive role 혼합으로 세지 않는다. 예를 들어 arthritis diagnosis와
그 question-wording flag가 한 concept에 있어도 concept의 substantive role은 disease다.

## Relation candidate와 truth의 구분

고정 ontology enumeration은 relation을 참이라고 확정하지 않는다. 다음 명제는 signature가
맞아 **검증할 후보**가 됐다는 뜻일 뿐이다.

```text
(arthritis, causal_ancestor_of, functional_limitation)
```

이후 verifier가 공급된 문서만 사용해 다음을 부여한다.

- `+1`: 같은 typed proposition을 명시적으로 지지
- `0`: 근거 부재, 불충분, 모호성, scope mismatch
- `-1`: 같은 typed proposition을 명시적으로 반박

제안되지 않은 edge는 false가 아니라 `structurally_not_evaluable` 또는
`not_enumerated`다.

## Appendix RQ

- **RQ1 — Concept/role materialization:** 문서만으로 concept과 substantive role을
  provenance와 함께 자동 생성할 수 있는가?
- **RQ2 — Relation coverage:** 고정 ontology enumeration이 proposer-dependent shortlist를
  제거하면서 검증 가능한 relation hypothesis를 안정적으로 생성하는가?
- **RQ3 — Incremental utility:** nonzero relation이 존재할 때 `Auto-Full - Auto-C`가
  개선되는가?
- **RQ4 — Boundary:** ontology, documents, role proposer, verifier, semantic encoder,
  backbone에 따라 효과가 어떻게 달라지는가?

## 실험 설계 변화

Main paper comparison은 `Base`, `Target-only`, `Auto-C`, concept specificity controls,
TransTab/CARTE다. 이 문서의 appendix comparison은 다음으로 제한한다.

- `Base+Auto-R`
- `Base+Auto-Full`
- `Base+Auto-C`

Method ablation:

- fixed exhaustive enumeration vs 이전 LLM relation shortlist
- role signature on/off
- semantic role shuffled
- relation type text vs anonymous type ID
- verified polarity vs positive-only
- ontology primary six vs extension ontology
- proposer LLM ablation은 concept/role 단계에서만 수행

이전 LLM relation shortlist는 폐기하지 않고 proposer-dependence를 보여주는 ablation과
failure analysis로 내린다.

## Downstream 실행 gate

`Base+Auto-R`과 `Base+Auto-Full`은 다음을 만족할 때만 relation-effect 실험으로 실행한다.

1. alignment-level verified `+1/-1` relation이 최소 1개
2. relation instance와 evidence provenance가 완전함
3. 같은 fixed ontology와 semantic encoder를 모든 proposer에 적용

활성 relation이 0이면 `Base+Auto-R`은 Base, `Base+Auto-Full`은 `Base+Auto-C`와 동일하므로
학습 결과를 relation 기여로 보고하지 않는다.
