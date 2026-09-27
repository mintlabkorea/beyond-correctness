# W8 — published semantic-knowledge audit 후보 10편

작성일: 2026-09-08 (KST, 세션 날짜). 단계: **후보 목록 작성 완료**.
적용 기준: [INCLUSION_RULE_FREEZE_V1.md](INCLUSION_RULE_FREEZE_V1.md).
기준 파일과 SHA-256을 먼저 기록한 뒤 아래 외부 검색을 수행했다.

**10편은 최종 포함 논문 수가 아니다.** 정식 출판 정보와 semantic
predictive-method 관련성에 근거한 screening queue다. 모든 행의 최종
eligibility는 `PENDING_FULL_TEXT`; semantic ablation의 존재·정확한 조건·
출판본 위치는 다음 단계에서 확인한다. 성능 수치, 효과 방향, admissibility,
wrong/reference/compound 판정과 supported claim은 아직 추출하지 않았다.

## 고정한 inclusion rule 요약

정식 peer-reviewed conference/journal 논문 중, tabular classification 또는
regression에 명시적인 semantic information을 사용하고, 그 정보를 제거·교란·
대체·변형하는 predictive comparison을 출판본/공식 supplement에 보고한 연구를
포함한다. Single-table도 허용하되 cross-table과 구분한다. Semantic input과
architecture를 함께 바꾸는 ablation도 포함 대상이다. Reference가 적합한지는
포함 조건이 아니라 이후 audit의 판정 대상이다.

검색 범위는 현재 RW와 최근 방법을 출발점으로 하는 bounded retrospective
audit다. 2026-09-08까지의 문헌 전체를 망라했다는 의미가 아니다. 6–8편은
예상치이며, screening 후 9–10편이 모두 적격이면 모두 유지한다.

## 후보 목록 — 다음 screening도 이 ID 순서로 진행

| ID | 연구 / 저자 | 확인된 출판 | 후보 근거와 semantic use | 유입 경로 | 다음 단계 확인 사항 |
|---|---|---|---|---|---|
| C01 | [LIFT: Language-Interfaced Fine-Tuning for Non-language Machine Learning Tasks](https://proceedings.neurips.cc/paper_files/paper/2022/hash/4ce7fe1d2730f53cb3857032952cd1b8-Abstract-Conference.html) — Dinh et al. | NeurIPS 2022 | 비언어 예측 문제를 LM 입력으로 표현; feature-name semantics 후보 | 현재 RW `dinh2022lift`; 첨부문 | tabular subset의 semantic-name intervention을 출판본에서 확인; 비정형 데이터 실험은 audit 범위와 구분 |
| C02 | [TransTab: Learning Transferable Tabular Transformers Across Tables](https://proceedings.neurips.cc/paper_files/paper/2022/hash/1377f76686d56439a2bd7a91859972f5-Abstract-Conference.html) — Wang & Sun | NeurIPS 2022 | column description과 cell을 입력으로 쓰는 cross-table 모델 | 현재 RW `wang2022transtab`; 사용자 요청 | 원논문의 semantic intervention 존재 여부; 우리 0.0.7 scratch regression extension은 포함 근거로 사용하지 않음 |
| C03 | [TabLLM: Few-shot Classification of Tabular Data with Large Language Models](https://proceedings.mlr.press/v206/hegselmann23a.html) — Hegselmann et al. | AISTATS 2023 | tabular records의 natural-language serialization | 현재 RW `hegselmann2023tabllm`; 기존 quantitative case | published serialization ablations의 조건과 위치; 우리 신규 reference 실험과 분리 |
| C04 | [High dimensional, tabular deep learning with an auxiliary knowledge graph](https://papers.neurips.cc/paper_files/paper/2023/hash/53dd219b6b11abc8ce523921c18c7a3e-Abstract-Conference.html) — Ruiz et al. (PLATO) | NeurIPS 2023 | auxiliary KG로 feature별 MLP weight를 구성 | 현재 RW `ruiz2023plato`; 첨부문 | KG intervention과 동반 model 변경을 출판본에서 확인; 예상 compound 판정을 미리 채우지 않음 |
| C05 | [CARTE: Pretraining and Transfer for Tabular Learning](https://proceedings.mlr.press/v235/kim24d.html) — Kim, Grinsztajn & Varoquaux | ICML 2024 | open-vocabulary table representation과 pretrained transfer | 현재 RW `kim2024carte`; 사용자 요청 | 원논문의 name/representation semantic intervention 존재 여부; 우리 M/C/R 실험과 분리 |
| C06 | [Large Language Models Can Automatically Engineer Features for Few-Shot Tabular Learning](https://proceedings.mlr.press/v235/han24f.html) — Han et al. (FeatLLM) | ICML 2024 | LLM으로 predictive features/rules 생성 | 현재 RW `han2024featllm`; 첨부문 | description/context intervention이 published comparison인지 확인; 단순 generation tuning과 구분 |
| C07 | [Large Scale Transfer Learning for Tabular Data via Language Modeling](https://proceedings.neurips.cc/paper_files/paper/2024/hash/4fd5cfd2e31bebbccfa5ffa354c04bdc-Abstract-Conference.html) — Gardner, Perdomo & Schmidt (TabuLa-8B) | NeurIPS 2024 | tabular classification 및 binned regression용 pretrained LM | 현재 RW `gardner2024tabula`; W8가 직접 지목 | header-semantic intervention을 출판본에서 확인; availability나 비용을 추정해 제외하지 않음 |
| C08 | [ConTextTab: A Semantics-Aware Tabular In-Context Learner](https://proceedings.neurips.cc/paper_files/paper/2025/hash/d807e7678ba3afd3a904f4af52819e77-Abstract-Conference.html) — Spinaci et al. | NeurIPS 2025 | semantic alignment와 modality별 embedding을 쓰는 table-native ICL | 첨부문의 최근 방법 lead + 공식 proceedings 확인 | semantic encoding intervention인지 generic architecture ablation인지 원문으로 확인 |
| C09 | [TabSTAR: A Tabular Foundation Model for Tabular Data with Text Fields](https://proceedings.neurips.cc/paper_files/paper/2025/hash/faf6e23e198314c7728eaa6ac44ae079-Abstract-Conference.html) — Arazi, Shapira & Reichart | NeurIPS 2025 | pretrained text encoder와 target-aware textual representation | 첨부문의 최근 방법 lead + 공식 proceedings 확인 | semantic verbalization/target-context intervention이 출판본에 있는지 확인 |
| C10 | [Table Foundation Models: on knowledge pre-training for tabular learning](https://openreview.net/pdf?id=QV4P8Csw17) — Kim, Lefebvre, Brison, Perez-Lebel & Varoquaux (TARTE) | TMLR, 08/2025 | column names/entries의 semantics와 relational pretraining으로 reusable table representation 생성 | 최근 방법 broad query → 원저자 arXiv → 공식 TMLR PDF 검색 기록 | semantic intervention 존재 여부와 accepted-version 조건 확인; CARTE와 별개 논문이지만 계보 중복은 이후 해석에 명시 |

각 링크는 제목/출판/방법 관련성의 1차 출처다. Ablation의 존재나 적합성을
확정하는 citation으로 사용해서는 안 된다. TARTE의 공식 OpenReview PDF 검색
결과에는 `Published in Transactions on Machine Learning Research (08/2025)`가
명시되어 있으나 직접 forum/PDF 열기는 429/browser challenge를 반환했다.
다음 full-text 단계에서 원문 접근과 버전 확보가 필요하다.

## 이번 단계에서 정리한 경계

- **Gardner et al.은 C07에 포함했다.** 왜 이전 quantitative evaluation에서
  빠졌는지에 대한 실제 의사결정 기록은 이번 검색으로 확인되지 않았다.
  비용·재현 불가능·control 부족 같은 이유를 만들어 쓰지 않는다. 향후
  design audit 포함은 새로운 재현 실험을 했다는 뜻도 아니며, learner
  coverage의 약점을 실험적으로 해소했다고 주장할 수 없다.
- **TransTab/CARTE도 같은 rule로 screen한다.** 우리 extension이 있다는
  사실만으로 원논문을 eligible로 처리하지 않는다.
- **TabSTAR는 출판본 제목을 사용한다.** 초기 preprint의
  “A Foundation Tabular Model With Semantically Target-Aware Representations”와
  별도 연구로 이중 집계하지 않는다.
- **TARTE는 새로 찾은 10번째 후보다.** semantics 중심의 정식 출판 방법이라는
  이유로 추가했으며, ablation 결과나 예상 판정에 따른 보충이 아니다.
- 현재 RW의 schema-matching/harmonization 및 일반 control-theory 문헌은
  배경 문헌이다. 이 단계에서 해당 논문 전체의 eligibility를 판정한 것은
  아니며, 이 목록이 RW 전체를 exhaustive screen한 결과라고 쓰지 않는다.

## 검색 기록과 노출 한계

검색은 inclusion freeze와 hash 생성 후 실행했다. 아래 순서는 논리적 검색
묶음 순서이며, 묶음 내부 tool query는 동시에 요청될 수 있다.

| 묶음 | 실제 검색/열람 | 용도 / 처리 |
|---|---|---|
| Q1 | `ConTextTab NeurIPS 2025`; `TabSTAR 2025 publication`; `semantic tabular foundation model 2025 2026` | 최근 방법 발견. 두 지명 후보의 NeurIPS 기록과 TARTE lead 확보 |
| Q2 | `site.proceedings.neurips.cc 2024 Large Scale Transfer Learning Tabular Language Modeling Gardner`; `site.proceedings.neurips.cc LIFT Language Interfaced Fine Tuning 2022`; `site.proceedings.neurips.cc High Dimensional Tabular Deep Learning Auxiliary Knowledge Graph 2023` | RW seed의 identity/venue 확인 |
| Q3 | C02/C03/C05/C08/C09 공식 landing pages; FeatLLM 기존 OpenReview URL; `"Table Foundation Models: on knowledge pre-training for tabular learning" NeurIPS 2025` | TARTE는 NeurIPS가 아니라 TMLR 08/2025로 확인; FeatLLM OpenReview는 challenge |
| Q4 | C02/C04/C08/C09 abstract pages; TARTE forum; FeatLLM PMLR URL 탐색 | 추정 `han24d.html`은 다른 논문이므로 사용하지 않음; TARTE forum 429 |
| Q5 | `site.proceedings.mlr.press/v235/ "Large Language Models Can Automatically Engineer"`; `site.openreview.net "QV4P8Csw17" "2025"`; TARTE PDF 및 C03/C05 landing pages | FeatLLM의 정확한 `han24f.html` 확인; 공식 TARTE PDF의 출판 표시 검색 결과 확인 |

Q1은 TabFM, Data Language Models 등의 2026 lead도 반환했다. 이들은 이번
bounded query에서 primary peer-reviewed publication과 semantic-method scope를
모두 확인한 추가 후보가 아니며, formal exclusion으로 세지 않는다. 7개 RW
seed와 3개 2025 published lead로 10편에 도달하여 검색을 종료했다. 다른 최근
방법을 모두 검토했거나 2026 방법이 없다는 의미가 아니다. 검색 결과에 포함된
서베이·뉴스·집계 사이트는 최종 후보의 근거 출처로 사용하지 않았다.

첨부문에 C01/C03/C04/C06/C07/C08/C09의 ablation 및 결과/예상 판정이 이미
노출되어 있었다. 기존 프로젝트에는 TabLLM 및 우리 TransTab/CARTE 결과가
있다. 이번 검색에서도 abstracts/snippets가 일부 성능 주장과 정량 정보를
자동으로 노출했다(예: Gardner, TransTab, PLATO). 이 정보는 선정 변수로
사용하거나 이 후보표에 추출하지 않았지만, **완전한 outcome blinding은
성립하지 않는다.** 향후 원고에는 “결과를 보기 전에 paper set을 정했다”는
문장을 쓰지 말고, retrospective discovery와 design-first coding의 실제
수행 범위를 구분하여 기술해야 한다.

## 다음 단계 인계

이번 요청의 완료 지점은 여기다. 다음에는 C01→C10 순서로 출판본과 공식
supplement를 확보해 criterion 1–5 각각의 근거와 정확한 section/table을
기록하고 eligible / excluded / unresolved를 결정한다. 그 결과로 study set을
고정한 뒤 control coding으로 넘어간다. 원고 본문·부록 표, 성능 숫자,
Removal/Preservation/Interface 판정은 이번 산출물에 포함하지 않았다.
