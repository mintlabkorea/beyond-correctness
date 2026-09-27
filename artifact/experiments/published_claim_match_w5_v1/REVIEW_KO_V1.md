# W5 분석 및 검토 결과 — 논문 미반영

기존 **9 studies / 25 comparisons**를 그대로 유지하고, 각 비교에 연결된
저자 주장을 두 축으로 새로 코딩했다. 결과 파일만 생성했으며 `main.tex`,
`appendix.tex`, 기존 audit 판정은 수정하지 않았다. 원고·기존 support 파일의
시작/종료 SHA-256 일치를 확인했다.

## 핵심 결과

**명시적인 utility claim은 25개 중 11개**였다. 기존 primary support 판정과
결합하면 이 11개는 **Matched 2, Mismatch 6, Indeterminate 3**이다.
Utility claim이 없는 10개는 Not claimed이고, claim 자체가 불명확한 4개는
별도로 남겼다. 따라서 기존의 `Utility: None`을 일괄 결함으로 읽는 해석은
성립하지 않는다.

| 축 | 명시적 claim Yes | 그중 Matched | 그중 Mismatch | 그중 support Unclear | Claim No | Claim Unclear |
|---|---:|---:|---:|---:|---:|---:|
| Content | 18 | 1 | 14 | 3 | 3 | 4 |
| Utility | 11 | 2 | 6 | 3 | 10 | 4 |

Content의 14개 mismatch는 아래 검토에서 설명하는 **claim 강도 정렬 문제**가
있으므로 곧바로 “14개 과도한 주장”이라는 headline으로 쓰면 안 된다.

Utility claim × 기존 control support의 전체 교차표:

| Reported utility claim | Supported | None | Unclear |
|---|---:|---:|---:|
| Yes | 2 | 6 | 3 |
| No | 2 | 8 | 0 |
| Unclear | 0 | 2 | 2 |

Utility mismatch 6개는 LIFT의 네 비교(C01-A/B/C/D), PLATO의 Full KG vs No KG
(C04-B), CARTE의 Minhash 교체(C05-A)다. 이는 **3개 연구**에 속하며,
같은 논문의 문단·데이터·arm을 공유하므로 여섯 개의 독립 증거로 해석하지 않는다.
명시적 utility claim은 전체 7개 연구에서 확인됐다.

## 리뷰어의 핵심 지적을 실제로 확인한 사례

- **TabLLM의 세 비교는 utility claim=No**다. 해당 문단은 feature names 및
  name–value association에 대한 의존성을 해석한다. 따라서 기존 utility
  support=None이어도 utility mismatch로 세지 않는다. 세 행 모두 Not claimed다.
- **ConTextTab C08-E**는 원래 utility를 평가할 수 있는 control이지만,
  해당 창에서의 해석을 보수적으로 코딩하면 content를 활용한다는 주장이고
  별도 utility claim은 No다. Control의 능력과 실제 주장도 서로 다를 수 있다.
- **TabSTAR C09-A**에 수치 정보의 일반적 성능 이점을 그대로 귀속하지 않았다.
  그 비교는 추가 quantile 정보의 효과이며, 저자들은 추가 효과가 제한적이라고
  서술한다. Name-only와의 다른 비교인 C09-B에는 명시적 utility claim이 있다.
- **CARTE C05-B/C**는 table context의 활용/성능 기여를 논하지만, 그 문구가
  semantic content 자체를 가리키는지는 모호하다. 한 코더는 Yes, 다른 코더는
  Unclear였고, 별도 조정자가 보수적 규칙에 따라 두 축 모두 Unclear로 판정했다.
- **TARTE C10-A/B**는 로컬 원문이 출판 전 arXiv v2라는 한계를 유지했다.
  정식 출판본과의 동일성을 확인하지 못했으므로 원 논문의 claim 판정은
  두 축 모두 Unclear다. 행을 제외하거나 주장이 없었다고 처리하지 않았다.

각 판정의 짧은 원문 인용과 위치는 `COMPARISONS_CLAIM_MATCH_V1.csv` 및
`RESULTS_V1.md`에 있다. 숫자가 포함된 인용은 `[NUM]`으로 명시적으로 가렸고,
인용 문구는 공백·줄바꿈 하이픈 정규화만 허용했다. 원래의 전체 추출 창은
`extraction_earlier.json`, `extraction_later.json`에 보존했다.

## 새 claim 코딩의 조정 전 일치도

| 항목 | Raw agreement | Cohen κ |
|---|---:|---:|
| claim_content | 23/25 = 92.0% | 0.7984 |
| claim_utility | 23/25 = 92.0% | 0.8663 |
| descriptive_only | 25/25 = 100% | 정의되지 않음 |

descriptive_only는 두 코더 모두 모든 행을 No로 판정해 변이가 없으므로
κ를 1로 표시하지 않았다. 세 범주를 순서형으로 가정하지 않는 unweighted κ를
사용했고, confusion matrix와 marginal counts를 함께 저장했다.

두 claim 축의 불일치는 CARTE C05-B/C 두 비교에서 발생했다. 세 번째 코더는
기존 support 판정을 모른 채 이를 조정하고, 나머지 합의 행도 검토했다.
세 건의 linkage granularity 차이도 기록했다. 합의된 claim label을 뒤집은
사례는 없었다. Raw A/B 파일은 보존하며 조정 후 값을 이용해 κ를 부풀리지 않았다.

**이는 같은 모델의 별도 AI context 간 재현성이지, 독립적인 사람 두 명의
inter-rater reliability가 아니다.** 공통 packet, 모델, codebook을 공유한다.
또한 연구/arm이 겹치므로 25개 독립 관측을 가정한 κ 신뢰구간을 제시하지 않았다.
Nominal agreement coefficient: [Cohen, 1960](https://doi.org/10.1177/001316446002000104).

## 기존 support 판정의 신뢰도와 민감도

사용 가능한 기존 primary/second AI design coding을 재사용했다. 이번 W5에서
새로운 support 코더를 실행한 것은 아니다. 원래 두 코딩의 scope 차이도 보존했다.

| 항목 | Agreement | κ |
|---|---:|---:|
| Utility support | 16/25 = 64% | 0.4458 |
| Removal gate | 24/25 = 96% | 0.9265 |
| Preservation gate | 14/25 = 56% | 0.3649 |
| Interface gate | 21/25 = 84% | 0.6622 |

두 번째 historical coder는 별도의 content-support label을 작성하지 않았다.
공통 Wrong-like 분류와 각자의 Preservation/Interface gate로 계산한 파생
content-support는 25/25 일치하지만, 이를 독립 content 코딩의 완벽한 신뢰도로
보고해서는 안 된다. 계산값은 원자료와 함께 별도 필드에만 보존했다.

같은 최종 utility claims를 두 번째 support 판정과 결합하면:

| Support 판정 | Matched | Mismatch | Indeterminate | 분모 |
|---|---:|---:|---:|---:|
| 기존 primary | 2 | 6 | 3 | 11 explicit claims |
| 기존 second coder | 2 | 4 | 5 | 11 explicit claims |

두 판정에서 공통으로 mismatch인 것은 **3개 비교**다:
C01-A, C01-B, C04-B. Primary에서만 mismatch인 것은 C01-C/D와 C05-A,
second에서만 mismatch인 것은 C06-A다. 즉 단순히 6개 중 4개가 유지된다는
뜻이 아니다. 비교별 변화는 `UTILITY_SUPPORT_SENSITIVITY_V1.csv`에 있다.

## 파일 검토에서 남은 중요한 문제

1. **Content claim의 강도와 기존 support 정의가 여전히 다르다.** 이번 사용자
   규칙의 claim_content는 “semantic information을 사용/의존한다”는 약한
   주장도 포함한다. 기존 supports_content는 intended–wrong contrast가
   엄격한 content sensitivity를 식별하는지 묻기 때문에 removal-only 비교를
   일괄 None으로 분류한다. 따라서 적합한 제거 비교가 약한 “정보를 사용한다”는
   주장을 지지해도 기계적 content mismatch가 생길 수 있다. 요청된 계산은
   그대로 제공했지만, **content 14/18을 원 논문들의 과장 비율로 사용하지 않는
   것이 적절하다.** 원고 반영 전 claim 강도와 support의 동일한 질문 정렬이 필요하다.
2. **Utility 6/11도 원래 framework의 scope에 조건부다.** Primary/secondary
   sensitivity와 Preservation의 낮은 일치도를 함께 보고해야 한다.
   정당화되지 않은 None을 명확한 실패처럼 강화하거나, Unclear를 mismatch로
   재분류해서는 안 된다. 이 수치는 해당 고정 조건에서의 claim–control 불일치이며
   논문 전체의 과장·오류·방법 무효를 입증하는 지표가 아니다.
3. **Human reliability 요구를 충족했다고 쓰면 안 된다.** 이번 작업은 실제로
   분리된 두 AI 코더와 조정자를 사용했지만 같은 모델이다. 사람 간 검증은
   수행하지 않았다. 준비된 masked packet과 25행 시트는 그 후속 작업에도 쓸 수 있다.
4. **문헌 선정은 bounded retrospective sample이다.** 기존 기록은 후보
   10편 → 포함 9편/제외 1편의 경위를 뒷받침한다. 새로운 systematic search나
   전체 분야의 mismatch prevalence를 주장하지 말아야 한다. 기존 prior exposure도
   숨기지 않는다. 자세한 검색·스크리닝 경위는 `SELECTION_AND_BOUNDARIES_V1.md` 참조.
5. **TARTE 두 행은 출판본 확인의 잔여 한계다.** 지금 표본은 25행을 유지하지만,
   25행 모두가 정식 출판본의 claim까지 확인됐다고 말할 수 없다.

## 검증 및 재현

- 25개 comparison ID, 9개 study 고정 및 누락/추가 없음.
- 원문 147개 window instance의 파일·줄 범위 일치와 수치 masking 확인.
- A/B/조정본 총 75개 행의 인용을 masked 원문과 대조해 통과.
- Claim κ와 historical support/gate κ를 sklearn 계산과 별도 대조.
- 50개 claim–support 상태 전이를 검증. Claim No/Unclear 또는 support Unclear가
  definitive mismatch로 들어가지 않음.
- 기존 support 파일과 `main.tex`/`appendix.tex` 해시 일치 확인.

**검토 결론:** utility에서는 “실제 주장한 11개 중 6개가 primary framework와
불일치하며, secondary support 판정에서는 4개”라는 조건부 결과가 기존 성적표식
요약보다 타당하다. Content 축은 요청한 자동 계산을 보존하되, 약한 use claim과
엄격한 content-sensitivity 식별 기준의 차이를 해소하기 전에는 headline으로
사용하지 않는 것이 좋다. 이번 파일은 검토용이며 논문에는 반영하지 않았다.
