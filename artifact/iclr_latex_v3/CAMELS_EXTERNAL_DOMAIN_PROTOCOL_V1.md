# CAMELS external-domain protocol v1

상태: local native-data inventory 이후 task design 동결 전 초안  
작성일: 2026-08-13

## 결정

Medical NHANES→KNHANES는 이미 고정된 primary scope로 유지한다. 비의료 적용 범위
실험은 C-MAPSS보다 **CAMELS-US→CAMELS-GB**를 우선한다. CAMELS development
screen이 통과하면 C-MAPSS는 main external-domain evidence에서 빼고 legacy/appendix
결과로만 보존한다.

이 선택의 이유는 두 국가 데이터가 같은 일별 유출량 예측 문제를 제공하면서도
기상 forcing, 토양·토지피복·지형 변수, 단위와 산출 provenance가 native schema마다
다르고, 각 정의를 설명하는 공개 문서가 충분하기 때문이다. Caravan은 여러
국가별 CAMELS의 비표준화를 별도로 표준화한 reference이므로, native schema를
입력으로 쓰는 본 실험의 독립적인 mapping reference가 될 수 있다.

## 고정할 예측 문제

- Source: original CAMELS-US native files
- Development target: original CAMELS-GB v2 native files
- Sealed confirmation 후보: original CAMELS-AUS, 대안 CAMELS-CL
- Prediction unit: basin-day
- Target: catchment-specific daily discharge, `mm/day`
- Target label은 proposer payload에서 완전히 숨긴다.
- Source USGS `ft³/s`는 forcing header의 basin area `m²`를 사용해 `mm/day`로 변환한다.
- Target GB는 제공된 `discharge_spec`을 사용한다.
- Primary dynamic forcing: US Daymet native columns, GB native daily columns
- Static inputs: climatic, topographic, soil, land-cover and geology/hydrogeology
  attributes. 유량으로부터 계산된 hydrologic signatures는 모두 제외한다.
- Recurrent model을 새로 제안하지 않는다. 각 basin-day를 tabular row로 두고, native
  forcing마다 현재값과 3/7/30일 trailing summary를 deterministic하게 생성한다.
  Lagged discharge는 primary input에 넣지 않는다.

## 누수 없는 split

- split 단위는 날짜/row가 아니라 `gauge_id`다.
- Target support는 1/3/5개 유역으로 정의한다.
- Query는 support와 겹치지 않는 target 유역으로만 구성한다.
- Development 중 basin pool과 seed를 고정하고, CAMELS-AUS/CL은 열지 않은 external
  confirmation으로 남긴다.
- 같은 날짜의 공간 상관이 과대평가를 만들 수 있으므로 기본 random-basin split과
  별도로 geographic-block sensitivity를 둔다.

## 평가와 공정한 baseline

- 같은 native tabular rows, support basin과 query basin을 모든 arm에 재사용한다.
- Base는 exact-name overlap을 포함한 native union schema와 missingness channel을
  사용한다. 공통 이름 28개를 숨겨 concept adapter에 유리하게 만들지 않는다.
- Primary regression score는 `log1p(mm/day)` RMSE로 두고, 원 단위의 basin-wise NSE,
  KGE, MAE와 bias를 함께 보고한다. 최종 metric 우선순위는 development 결과를 보기
  전에 scope-lock 문서에서 확정한다.
- 비교 arm은 Base, target-only, Auto-C, Auto-R, Auto-Full, manual/wrong/random control,
  TransTab/CARTE 중 현재 data interface에 맞는 strong baseline이다.

## Concept/relation extraction 경계

LLM은 원 국가 문서와 native schema에서 후보를 추출한다. 다음 이름을 사람이
candidate bank에 직접 넣지 않는다. 예상 가능한 concept surface는 기상 forcing,
기온, 강수, 유역 지형, 토양 물성·조성, 토지피복과 기후 regime이다. Relation은
outcome인 유출량을 참조할 수 없으며, 입력 변수 사이의 문서화되고 DSL로 실행 가능한
관계만 허용한다. 예를 들면 aridity의 PET/precipitation ratio, soil composition,
또는 basin/time index를 사용한 documented temporal operation이다.

Caravan은 proposer 문서, candidate acceptance 또는 model input에 넣지 않는다.
원 국가 schema에서 LLM이 만든 mapping을 나중에 비교하는 reference/audit에만 쓴다.

모든 proposer가 같은 context budget을 사용하도록 CAMELS-GB soil attribute의 반복된
5/50/95 percentile 열은 payload에서 제외하고 공식 aggregate 열만 유지한다. 이는
cross-schema concept을 선택하는 규칙이 아니라 동일 native variable의 통계적 복제
폭을 줄이는 입력 크기 규칙이며, document inventory에는 원 열을 그대로 보존한다.

## 최소 실행 순서

1. native document inventory와 파일 provenance 고정
2. outcome-blind US→GB payload builder와 unit registry 작성
3. 공통 frozen prompt로 Codex bank 생성
4. Auto-C/R/Full, Base, manual/wrong/random small screen
5. 양의 신호와 leakage check를 확인한 뒤 external-domain scope lock
6. proposer/backbone ablation과 geographic-block confirmatory rerun

EPA AQS→EEA는 CAMELS가 tabularized time-series라는 이유로 논문 정체성을 흐릴 때의
2순위다. ICOS/AmeriFlux→NEON과 Landsat→Sentinel은 문서성은 강하지만 현재 adapter에
필요한 전처리와 estimand 차이가 더 크므로 이번 main extension에는 동시에 넣지 않는다.
