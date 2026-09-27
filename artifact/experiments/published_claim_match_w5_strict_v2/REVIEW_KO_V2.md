# W5 strict content 재코딩 리뷰

**재코딩 완료. 기존 weak-content Yes 18개가 strict-content Yes 6개로 줄었다.** 엄격한 주장 6개를 기존 support와 대조한 결과는 Matched 1, Mismatch 2, support-Indeterminate 3이다. 기존 **14/18은 새 정의에서 유효한 headline이 아니므로 사용하지 않는다.** 새 집계도 논문 전체의 과장 비율로 해석하지 않는다.

## 최종 결과

| Strict reported content claim | Supported | None | Unclear | 합계 |
|---|---:|---:|---:|---:|
| Yes | 1 | 2 | 3 | 6 |
| No | 0 | 16 | 0 | 16 |
| Unclear | 0 | 3 | 0 | 3 |

전체 25개 상태는 Matched 1, Mismatch 2, Indeterminate 6, Not claimed 16이다. Indeterminate 6개는 **명시적 claim은 있지만 support가 불명확한 3개**와 **claim 자체가 불명확한 3개**로 구분된다.

| 판정 | Comparison ID | 해석 |
|---|---|---|
| Matched | C03-A | TabLLM의 feature-name permutation |
| Mismatch | C01-C, C01-D | LIFT의 names-present / names-absent, 형식 I·II |
| Yes + support Unclear | C01-A, C01-B, C03-C | LIFT의 shuffled-name 두 비교 및 TabLLM의 value permutation |
| Claim Unclear | C03-B | TabLLM values-only 비교에 강한 association 해석까지 귀속되는지 불명확 |
| Claim Unclear | C10-A, C10-B | TARTE의 publication-version 문구 검증 미완료 |

Strict Yes는 LIFT와 TabLLM **2개 연구의 6개 비교**에 집중되어 있고, mismatch 2개는 모두 **LIFT 한 연구**에 속한다. 이를 2개의 독립적인 연구 증거로 세지 않는다.

LIFT의 C01-C/D가 Yes로 남은 이유는 제거 ablation이기 때문이 아니다. 같은 해석 문단이 앞서 서술한 성능 개선을 **“correct feature/value association”**에 귀속하고, **“aforementioned performance improvements”**가 names-present/absent 개선까지 연결하기 때문이다. A/B 및 제3 검토자는 이를 `explicit_group`으로 판정했다. 해당 문단에는 셔플 비교도 포함되므로, 제거 비교 하나가 단독으로 충분한지에 대한 mismatch를 원 논문의 종합적인 association 주장 전체가 무근거라는 결론으로 바꿀 수 없다. 남은 핵심 한계는 이 **묶음 결론의 개별 comparison 귀속**이다.

기존 라벨에서의 전이는 Yes→Yes 6, Yes→No 11, Yes→Unclear 1, No→No 3, Unclear→No 2, Unclear→Unclear 2이다. 새 정의에서 강도가 부족한 weak-use 해석을 strict No로 분리했으며, 모든 이전 라벨은 보존했다.

새 A/B 원시 코딩은 **25/25 일치(100%), unweighted Cohen's κ=1.000**였다. 두 코더의 주변분포는 모두 Yes 6 / No 16 / Unclear 3이고, 우연 일치 기대값은 0.4816이다. 제3 검토자가 전체 25개를 재검토했으며 라벨 수정은 없었다. 이 값은 **동일 모델의 별도 AI 컨텍스트 간 재현성**이며 인간 코더 신뢰도가 아니다.

Utility 축은 변경하지 않았다. 명시적 utility claim 11개 중 Matched 2 / Mismatch 6 / support-Indeterminate 3, 나머지는 Not claimed 10 / claim-Unclear 4로 기존 결과와 같다.

## 수정 범위와 판단 기준

사용자가 제안한 A안을 적용했다. `claim_content=Yes`는 해당 comparison의 해석이 **제공된 특정 의미 내용·대응관계에 대한 의존성**을 주장할 때만 부여한다. 단순히 의미 정보를 사용하거나, 구성요소가 중요하거나, 이를 제거하면 성능이 낮아진다는 해석만으로는 Yes가 아니다. 이로써 기존 `supports_content`가 평가하는 content-sensitivity 주장과 claim strength를 맞춘다.

다만 claim 코딩은 저자가 무엇을 해석했는지를 묻는다. 제거 실험이라는 이유만으로 자동 No, 셔플 실험이라는 이유만으로 자동 Yes로 처리하지 않는다. 통제가 불충분한 비교라도 강한 해석이 명시되어 있으면 Yes일 수 있다. 이는 claim과 support를 같은 판정으로 만들어 mismatch를 없애는 순환을 피하기 위한 규칙이다.

기존 9 studies / 25 comparisons, claim window, `claim_utility`, `supports_content`, `supports_utility`, `descriptive_only`는 그대로 유지했다. 새 논문이나 비교를 추가하지 않았고, 원고를 수정하지 않았다. strict `No`는 해당 논문이 약한 사용 주장을 하지 않았다는 뜻이 아니다. 기존 약한 content 라벨과 인용·scope·linkage를 `legacy_*` 열에 남겼다.

## 독립 코딩과 검증 범위

새 코드북을 먼저 고정하고, 이전 라벨·support·utility 코드와 성능 수치를 가린 기존 packet을 새로운 AI 컨텍스트 A/B에 제공했다. A/B 원시 결과를 해시로 고정한 뒤 일치도를 계산했다. 제3의 새 AI 컨텍스트는 같은 codebook과 window 및 고정된 A/B 결과만 읽고, 모든 25개 행의 판단·귀속을 검토했다. 제3 검토 결과도 support 병합 전에 고정했다.

여기서 독립성은 별도 컨텍스트와 읽기 지침에 의한 것이다. 기술적인 파일 접근 격리는 아니며, 같은 모델의 AI 코딩 일치도를 인간 코더 간 신뢰도로 보고할 수 없다. 이 정의 수정은 사후 분석 설계이며 사전등록이 아니다. 여러 비교가 같은 연구·문단을 공유하므로 25개 독립 표본을 가정한 비율 신뢰구간이나 유의성 검정도 제시하지 않는다.

## 해석상 남는 경계

strict claim과 strict support의 강도는 맞추었지만, **comparison 단위 판정과 논문의 전체 논증에 대한 평가는 구분해야 한다.** 여러 ablation을 묶은 결론이 `explicit_group`으로 귀속되면, 한 비교의 통제가 그 강한 주장을 단독으로 지지하는지와 다른 비교까지 합친 논문의 증거가 충분한지는 다른 질문이다. 최종 집계는 고정된 comparison 단위의 claim–control 판정이다. 연구 전체가 잘못 주장했다는 비율로 바꾸지 않는다.

TARTE 두 비교는 이전과 동일하게 accepted publication과 로컬 arXiv v2의 문구 동등성이 확인되지 않은 source-version 불확실성을 가진다. 기존의 후보 선정·스크리닝 기록은 [v1 문서](../published_claim_match_w5_v1/SELECTION_AND_BOUNDARIES_V1.md)에 보존되어 있다. 이번 작업은 원래의 제한된 후보 풀을 systematic review로 재해석하지 않는다.

기존 utility 축의 증거는 새 strict-content 인용문과 혼동하지 않도록 CSV의 `legacy_claim_text`, `legacy_claim_location`, `legacy_rationale`, `legacy_claim_scope`, `legacy_claim_linkage`에 보존했다. utility의 원래 A/B 코더 열도 유지했다.

## 검증 및 검토 파일

[25행 분석 CSV](COMPARISONS_STRICT_CLAIM_MATCH_V2.csv), [이전→새 판정 대조표](CONTENT_V1_TO_V2_TRANSITIONS.csv), [전체 인용·근거](RESULTS_V2.md), [제3 검토 기록](adjudication_ledger.json)을 함께 검토하면 각 판정을 추적할 수 있다.

[검증 결과](VALIDATION_V2.json)는 pass다. A/B/제3 검토 75개 행의 인용을 masked source window와 대조했고, 25개 unit 일치, κ의 별도 구현 대조, 자동 match 규칙, utility/support 필드 보존, 원래 v1 파일과 `main.tex`·`appendix.tex`의 작업 시작 시점 해시 일치를 확인했다. 기존 source packet은 바이트 단위로 동일하다. GPU 작업은 수행하지 않았다.
