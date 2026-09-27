# CAMELS-US → CAMELS-GB development screen v1

상태: development evidence complete, external-domain primary scope **not locked**  
작성일: 2026-08-13

## 무엇을 고정했는가

- Source: original CAMELS-US native Daymet forcing와 non-outcome catchment attributes
- Target: original CAMELS-GB v2 native daily forcing와 non-outcome attributes
- Target: daily specific discharge, `mm/day`
- Split: row/date가 아니라 `gauge_id`
- Target support: 1/3/5 basins
- Query: 고정된 별도 12 basins
- Source: outcome을 보지 않은 hash ordering으로 선택한 64 basins
- Period: 1981-01-01–2008-09-30, 30-day warm-up
- Input: current value와 3/7/30-day trailing mean; lagged discharge 없음
- Screen cadence: 매 7일 한 row
- Base: source/target native union schema, missingness channel, date Fourier features
- Proposer input: 44 source와 54 target eligible variables를 모두 유지한 outcome-blind payload
- Proposer: Codex `gpt-5.6-sol`, frozen prompt, high reasoning, tools/retrieval disabled

Qwen3 tokenizer로 측정한 prompt input은 17,802 tokens다. Fixed 16,384-token output budget까지 합쳐도 40,960 context에서 6,774 tokens가 남는다. Registry evidence를 여덟 행 단위로 deterministic하게 묶었지만, variable이나 documentation text를 선택적으로 제거하지 않았다.

## Automatic bank

Codex는 15 concepts와 1 relation을 제안했고 strict acceptance가 15/15 concepts와 1/1 relation을 수용했다.

Concept surface는 precipitation, PET, soil texture, elevation, area, porosity, conductivity, root depth, precipitation-event statistics, temperature, soil depth, forest/woodland, precipitation regime, land cover였다. Relation은 문서에 식이 명시된 `aridity = mean PET / mean precipitation` 하나였다.

중요하게도 proposer는 다음을 relation으로 만들지 않고 abstain했다.

- 강수에서 유출량으로 가는 outcome relation
- 문서에 executable formula가 없는 soil pedotransfer relation
- target과 source 모두에 완전한 protocol이 없는 temporal relation

따라서 이 bank는 물리 지식 그래프나 인과 그래프가 아니라, 문서로 지지되고 현재 DSL이 실행할 수 있는 input-side candidate bank다.

## 실행한 비교

1/3/5 support basins × 3 seeds × 9 arms의 81 result cells를 실행했다.

- Target-only
- Base
- Auto-C
- Auto-R
- Auto-Full
- capacity-matched Random-C
- capacity-matched Random-Full
- source Auto-C + target random binding
- source Auto-Full + target random binding

CAMELS에는 결과를 보기 전에 고정된 독립 manual bank가 없었다. Codex bank와 첫 결과를 본 뒤 사람이 manual bank를 만드는 것은 공정한 manual comparison이 아니므로 이번 screen에는 넣지 않았다. Manual reference를 쓸 경우 Caravan 또는 별도 hydrology expert mapping을 confirmatory 결과를 열기 전에 동결해야 한다.

## Primary metric 결과

Primary metric은 `log1p(mm/day)` RMSE다. 아래 improvement는 양수가 왼쪽 arm에 유리하도록 정의했다. CI는 9개의 support-count × seed paired cells를 재표집한 development-only bootstrap이다.

| 비교 | 평균 improvement | 95% bootstrap CI | wins |
|---|---:|---:|---:|
| Auto-C − Base | +0.00208 | [-0.00256, +0.00668] | 5/9 |
| Auto-R − Base | -0.00079 | [-0.00361, +0.00197] | 4/9 |
| Auto-Full − Base | +0.00158 | [-0.00458, +0.00742] | 5/9 |
| Auto-Full − Auto-C | -0.00050 | [-0.00257, +0.00164] | 3/9 |
| Auto-C − Random-C | +0.01565 | [+0.00652, +0.03187] | 9/9 |
| Auto-Full − Random-Full | +0.01703 | [+0.00557, +0.03351] | 8/9 |
| Auto-C − wrong target binding | +0.01765 | [+0.01134, +0.02521] | 9/9 |
| Auto-Full − wrong target binding | +0.01922 | [+0.00987, +0.02997] | 9/9 |
| Base − Target-only | +0.01353 | [+0.00209, +0.02406] | 8/9 |

Support count별 평균은 다음과 같다.

| Support basins | Base | Auto-C | Auto-R | Auto-Full |
|---:|---:|---:|---:|---:|
| 1 | 0.3792 | 0.3814 | 0.3803 | 0.3816 |
| 3 | 0.3282 | 0.3267 | 0.3332 | 0.3297 |
| 5 | 0.3202 | 0.3133 | 0.3165 | 0.3116 |

## 해석

현재 결과는 두 문장을 분리해서 말해야 한다.

첫째, **LLM이 고른 cross-schema semantics는 무작위 membership이나 틀린 target binding보다 일관되게 낫다.** Primary log-RMSE에서 Auto-C와 Auto-Full은 random/wrong controls를 거의 모든 cell에서 이겼고 interval도 0을 넘었다. 따라서 candidate bank가 단순한 extra feature capacity로만 작동했다는 설명은 약하다.

둘째, **강한 native-union Base 위의 incremental gain은 아직 안정적이지 않다.** Auto-C와 Auto-Full의 Base 대비 평균 방향은 양수지만 CI가 0을 통과하고 wins가 5/9다. 5-basin support에서는 이득이 더 컸지만 1-basin에서는 반대였다. 그러므로 이 결과만으로 CAMELS를 main external confirmation으로 lock하면 안 된다.

Relation은 특히 제한적으로 해석해야 한다. Accepted relation이 하나뿐이고, 그 ratio로 재구성되는 `aridity` raw attribute가 두 native schema와 Base에 이미 존재한다. 따라서 Auto-R이 Base를 안정적으로 이기지 못하는 것은 relation compiler의 실패라기보다 이번 documentation/DSL surface에서 relation이 거의 중복 정보라는 뜻에 가깝다. 이 결과로 “hydrologic relation 전체가 쓸모없다”거나 반대로 “relation이 기여한다”고 주장할 수 없다.

NSE와 KGE에서는 일부 양의 방향이 있지만 metric별 결론이 다르다. 특히 mean basin NSE는 분산이 작은 어려운 basin에 민감하므로 primary claim으로 승격하지 않는다. Primary scope 판단은 predeclared log-RMSE에 둔다.

## Scope 결정

- Medical NHANES→KNHANES primary scope는 그대로 유지한다.
- CAMELS는 공개 문서가 충분하고 semantic-specificity evidence가 강하므로 non-medical secondary track으로 보존한다.
- CAMELS를 C-MAPSS를 대체하는 main external confirmation으로 아직 lock하지 않는다.
- CAMELS-AUS/CL은 열지 않은 sealed candidate로 유지한다.

## 다음 confirmatory 전에 필요한 것

1. 더 많은 source/query basins와 geographic-block split을 포함한 protocol 재동결
2. Base, target-only, TransTab/CARTE 또는 해당 interface에 맞는 strong backbone 비교
3. target weighting과 weekly subsampling sensitivity
4. Codex 외 proposer의 CAMELS bank와 bank-overlap 분석
5. outcome을 쓰지 않으면서도 중복 raw attribute가 아닌 relation을 지원할 문서/DSL이 실제로 있는지 사전 점검
6. 독립 manual mapping을 쓸 경우 결과를 열기 전에 provenance와 mapping을 동결

Raw result 및 machine-readable summary는 `experiments/crta_v3_camels_native_screen_v1/` 아래에 있다.

