# 가설별 3자 비교표 (이론 · 에이전트 · KIS) — Task 10, 게이트 D용

생성 2026-11-10 15:25 KST — `code/make_threeway_table.py`가 `prereg/agent_predictions_v1.json`(동결)과 `results/06_kis_main.json`(사전등록 스크립트 `--real`)에서 생성. 손으로 고치지 말 것.

KIS 열: LPM 계수(처치 1 SD당 확률 변화), wild cluster bootstrap-t 95% CI, 단측 p, Holm(H1~H5) 보정 p, 사전등록 판정 규칙의 결정.

| 가설 | 이론 | 에이전트 A | 에이전트 B | KIS 추정 | 95% CI | p(단측) | Holm | 판정 | N / 군집 |
|---|---|---|---|---|---|---|---|---|---|
| H1 | + | + | + | +0.0144 | [+0.0019, +0.0266] | 0.016 | 0.064 | directional | 16,594 / 114 |
| H2 | + | + | + | +0.0057 | [-0.0095, +0.0204] | 0.209 | 0.418 | directional | 7,987 / 112 |
| H3 | + | + | + | -0.0033 | [-0.0206, +0.0128] | 0.675 | 0.675 | not supported | 7,987 / 112 |
| H4 | + | + | + | +0.0101 | [-0.0024, +0.0230] | 0.056 | 0.168 | directional | 16,594 / 114 |
| H5 | + | + | + | +0.0279 | [+0.0049, +0.0497] | 0.007 | 0.035 | supported | 7,987 / 112 |
| H6 | not + | n/a | 0 | -0.0418 | [-0.1072, +0.0215] | 0.886 | — | inconclusive | 16,594 / 114 |

## 강건성 사양별 부호 (사전등록 강건성; 결정에는 쓰지 않음)

| 가설 | raw_threat_0_5 | fe_industry_x_wave | weighted | excl_2023S | manufacturing_only | services_only | exit_strict | exit_full |
|---|---|---|---|---|---|---|---|---|
| H1 | + (p<.05) | + (p<.05) | + (p<.05) | + (p<.05) | + (p<.05) | - | + (p<.05) | + (p<.05) |
| H2 | - | + | + | + | - | + | + | + |
| H3 | - | - | - | - | - | + | - | - |
| H4 | + (p<.05) | + | + | + (p<.05) | + (p<.05) | - | + | + |
| H5 | + (p<.05) | + | + | + (p<.05) | + | + (p<.05) | - | + |
| H6 | - | + | + | - | - | - | - | - |

## 보조

- H2 객관(신생기업률×후발): +0.1119 [-0.0299, +0.2601], 단측 p 0.072. entry_rate_z x g0; slopes for g0/g1/g2 are x_g0 +0.112, x_g1 +0.120, x_g2 +0.107; with industry x wave FE the slope is -0.0137 — a between-industry level association, not laggard-specific
- H2 반증 조건(인식·객관 둘 다 ≤ 0): False
- 위약(두 문항 × 두 결과, 양측 wild p): placebo_demand quit_x_g0 +0.0023 (p 0.645); placebo_demand preempt_x_g2 -0.0149 (p 0.064); placebo_price quit_x_g0 -0.0017 (p 0.739); placebo_price preempt_x_g2 -0.0052 (p 0.453)
