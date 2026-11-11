# Preregistration — Escape or Exit: entry threat, technology gap, and the two margins of the innovation race

Generated 2026-11-10 14:16 KST by prereg/make_prereg_doc.py from frozen project files (tag prereg-v1). Structure follows the OSF Secondary Data Preregistration template (OSF project x4gzt, wiki 'Preregistration Template', version 31; copy in docs/sources/). Items marked [exploratory] carry no confirmatory status.

## Study Information

**Title.** Escape or Exit: Entry Threat, Technology Gap, and the Two Margins of the Innovation Race — Theory, Korean Innovation Survey Evidence, and LLM-Agent Experiments (working title).

**Authors.** Jihwan Woo (ORCID 0000-0002-0424-0242).

**Research questions.**

- RQ1. When firms perceive a threat of new entry, do they pre-empt (accelerate and protect products by entering the market ahead of competitors) or exit (abandon or suspend innovation activity), and does the answer depend on the firm's distance to the technological frontier?
- RQ2. Do *perceived* entry threat and *realised* entry (industry entry rates) have different effects on pre-emption, as the race model predicts?
- RQ3 (already completed; predictions frozen before the survey test). Do LLM agents placed in the same race environment reproduce the model's comparative statics? Their cell-level choices are registered here as *predictions*, not as confirmatory tests.

**Hypotheses (directional; derived from the finite-horizon innovation-race model in model/MODEL_NOTES.md; approved at gate B on 2026-11-10).** Notation: g = gap3 group (0 laggard, 1 middle, 2 frontier); b(x·g) = slope of x within group g; a(g) = group intercept at average x.

- **H1** — Escape. The higher the perceived threat of entry, the higher the probability that a firm close to the technological frontier (gap3 = 2) adopts a pre-emption strategy: b(threat x g2) > 0.  
  Model basis: P1 near (위협 버전, 100%). Test: `preempt_strategy ~ entry_threat × gap3`. Original (Korean, gate-B document): 인식된 진입 위협이 높을수록 **선두권(gap3=2)** 기업의 선점 전략 채택 확률이 높다: β(threat·g2) > 0 Falsification: β ≤ 0 또는 신뢰구간이 0을 포함
- **H2** — Exit. The higher the perceived threat of entry, the higher the probability that a laggard firm (gap3 = 0) abandons or suspends an innovation activity: b(threat x g0) > 0; the same sign is expected with the objective industry entry rate (falsified only if both are <= 0).  
  Model basis: P2 (두 버전 모두 100%). Test: `quit_any ~ entry_threat × gap3; quit_any ~ 신생기업률 × gap3`. Original (Korean, gate-B document): 진입 위협이 높을수록 **후발(gap3=0)** 기업의 혁신활동 중단 확률이 높다: β(threat·g0) > 0; 객관 신생기업률에서도 같은 부호 Falsification: 인식·객관 둘 다에서 β ≤ 0
- **H3** — Asymmetry (abandonment). The abandonment effect of entry threat is larger for laggards than for frontier firms: b(threat x g0) - b(threat x g2) > 0.  
  Model basis: P3 near (100%). Test: `같은 모형의 계수 차`. Original (Korean, gate-B document): 진입 위협의 중단 효과는 후발에서 선두권보다 크다: β(threat·g0) − β(threat·g2) > 0 Falsification: 차 ≤ 0
- **H4** — Asymmetry (pre-emption). The pre-emption effect of entry threat is larger for frontier firms than for laggards: b(threat x g2) - b(threat x g0) > 0.  
  Model basis: P4 near (100%). Test: `같은 모형의 계수 차`. Original (Korean, gate-B document): 진입 위협의 선점 효과는 선두권에서 후발보다 크다: β(threat·g2) − β(threat·g0) > 0 Falsification: 차 ≤ 0
- **H5** — Baseline. Laggards abandon more than frontier firms at any level of threat: a(g0) - a(g2) > 0 (adjusted means at average threat).  
  Model basis: P7 (97%). Test: `gap3 더미의 주효과`. Original (Korean, gate-B document): 격차 집단 사이의 중단율 차: gap3=0 > gap3=2 (θ 수준과 무관) Falsification: 차 ≤ 0
- **H6** — Realised entry vs threat. The objective industry entry rate (realised entry) does NOT raise pre-emption among frontier firms: the 90 % CI of b(entry_rate x g2) lies within [-0.010, +0.010] (equivalence test), in contrast to the perceived-threat effect of H1.  
  Model basis: P1 무조건 위배 84% vs 위협 100%. Test: `preempt_strategy ~ 신생기업률 × gap3`. Original (Korean, gate-B document): 객관 신생기업률(실현된 진입)은 선두권의 선점 전략을 **높이지 않는다**(β ≤ 0 또는 0과 구별 불가) — 인식 위협(H1)과 부호가 갈린다 Falsification: β(entry_rate·g2) > 0 유의

**Theory and agent predictions (frozen).** Signs predicted by the model and by the LLM-agent experiments (Stage A one-shot vignette; Stage B three-period race against the equilibrium rival), per hypothesis. Agent sign calls are mechanical: '+' if the 95 % persona-bootstrap CI of the contrast lies above 0, '-' below 0, '0' otherwise; consensus = at least 3 of 4 model x language arms agree. Source: prereg/agent_predictions_v1.json (SHA256 in SHA256SUMS.txt).

| Hypothesis | Theory sign | Stage A consensus | Stage A arms | Stage B consensus | Stage B arms |
|---|---|---|---|---|---|
| H1 | + | + | fable/en: +, fable/ko: +, gpt56/en: +, gpt56/ko: + | + | fable/en: 0, fable/ko: +, gpt56/en: +, gpt56/ko: + |
| H2 | + | + | fable/en: +, fable/ko: +, gpt56/en: +, gpt56/ko: + | + | fable/en: +, fable/ko: +, gpt56/en: +, gpt56/ko: + |
| H3 | + | + | fable/en: +, fable/ko: +, gpt56/en: +, gpt56/ko: + | + | fable/en: +, fable/ko: +, gpt56/en: +, gpt56/ko: + |
| H4 | + | + | fable/en: +, fable/ko: +, gpt56/en: +, gpt56/ko: + | + | fable/en: -, fable/ko: +, gpt56/en: +, gpt56/ko: + |
| H5 | + | + | fable/en: +, fable/ko: +, gpt56/en: +, gpt56/ko: + | + | fable/en: +, fable/ko: +, gpt56/en: +, gpt56/ko: + |
| H6 | not + | n/a | n/a | 0 | fable/en: -, fable/ko: 0, gpt56/en: 0, gpt56/ko: 0 |

Agent contrast estimates with 95 % CIs (Stage A = share choosing the action in the one-shot decision; Stage B = share over the whole episode):

| H | Stage | Contrast | Arm | Estimate [95 % CI] |
|---|---|---|---|---|
| H1 | stage_a | H1_accel_threat_gap2 | fable/en | +0.538 [+0.457, +0.630] |
| H1 | stage_a | H1_accel_threat_gap2 | fable/ko | +0.775 [+0.708, +0.847] |
| H1 | stage_a | H1_accel_threat_gap2 | gpt56/en | +0.525 [+0.430, +0.608] |
| H1 | stage_a | H1_accel_threat_gap2 | gpt56/ko | +0.600 [+0.500, +0.693] |
| H1 | stage_b | H1_accel_threat_gap2_noentry | fable/en | +0.144 [-0.032, +0.406] |
| H1 | stage_b | H1_accel_threat_gap2_noentry | fable/ko | +0.403 [+0.266, +0.549] |
| H1 | stage_b | H1_accel_threat_gap2_noentry | gpt56/en | +0.360 [+0.131, +0.625] |
| H1 | stage_b | H1_accel_threat_gap2_noentry | gpt56/ko | +0.223 [+0.065, +0.400] |
| H2 | stage_a | H2_quit_threat_gap0 | fable/en | +0.512 [+0.420, +0.604] |
| H2 | stage_a | H2_quit_threat_gap0 | fable/ko | +0.800 [+0.741, +0.868] |
| H2 | stage_a | H2_quit_threat_gap0 | gpt56/en | +0.338 [+0.269, +0.407] |
| H2 | stage_a | H2_quit_threat_gap0 | gpt56/ko | +0.337 [+0.250, +0.420] |
| H2 | stage_b | H2_quit_threat_gap0 | fable/en | +0.188 [+0.082, +0.297] |
| H2 | stage_b | H2_quit_threat_gap0 | fable/ko | +0.489 [+0.393, +0.589] |
| H2 | stage_b | H2_quit_threat_gap0 | gpt56/en | +0.396 [+0.269, +0.536] |
| H2 | stage_b | H2_quit_threat_gap0 | gpt56/ko | +0.583 [+0.500, +0.693] |
| H3 | stage_a | H3_quit_threat_gap0_minus_gap2 | fable/en | +0.512 [+0.420, +0.604] |
| H3 | stage_a | H3_quit_threat_gap0_minus_gap2 | fable/ko | +0.800 [+0.741, +0.868] |
| H3 | stage_a | H3_quit_threat_gap0_minus_gap2 | gpt56/en | +0.338 [+0.269, +0.407] |
| H3 | stage_a | H3_quit_threat_gap0_minus_gap2 | gpt56/ko | +0.337 [+0.250, +0.420] |
| H3 | stage_b | H3_quit_threat_gap0_minus_gap2 | fable/en | +0.188 [+0.082, +0.297] |
| H3 | stage_b | H3_quit_threat_gap0_minus_gap2 | fable/ko | +0.469 [+0.372, +0.571] |
| H3 | stage_b | H3_quit_threat_gap0_minus_gap2 | gpt56/en | +0.396 [+0.269, +0.536] |
| H3 | stage_b | H3_quit_threat_gap0_minus_gap2 | gpt56/ko | +0.562 [+0.464, +0.672] |
| H4 | stage_a | H4_accel_threat_gap2_minus_gap0 | fable/en | +0.538 [+0.457, +0.630] |
| H4 | stage_a | H4_accel_threat_gap2_minus_gap0 | fable/ko | +0.775 [+0.708, +0.847] |
| H4 | stage_a | H4_accel_threat_gap2_minus_gap0 | gpt56/en | +0.525 [+0.430, +0.608] |
| H4 | stage_a | H4_accel_threat_gap2_minus_gap0 | gpt56/ko | +0.600 [+0.500, +0.693] |
| H4 | stage_b | H4_accel_threat_gap2_minus_gap0 | fable/en | -0.125 [-0.250, -0.029] |
| H4 | stage_b | H4_accel_threat_gap2_minus_gap0 | fable/ko | +0.316 [+0.183, +0.446] |
| H4 | stage_b | H4_accel_threat_gap2_minus_gap0 | gpt56/en | +0.229 [+0.067, +0.397] |
| H4 | stage_b | H4_accel_threat_gap2_minus_gap0 | gpt56/ko | +0.250 [+0.125, +0.387] |
| H5 | stage_a | H5_quit_gap0_minus_gap2 | fable/en | +0.694 [+0.653, +0.740] |
| H5 | stage_a | H5_quit_gap0_minus_gap2 | fable/ko | +0.512 [+0.480, +0.547] |
| H5 | stage_a | H5_quit_gap0_minus_gap2 | gpt56/en | +0.169 [+0.135, +0.204] |
| H5 | stage_a | H5_quit_gap0_minus_gap2 | gpt56/ko | +0.181 [+0.141, +0.219] |
| H5 | stage_b | H5_quit_gap0_minus_gap2 | fable/en | +0.865 [+0.814, +0.917] |
| H5 | stage_b | H5_quit_gap0_minus_gap2 | fable/ko | +0.747 [+0.696, +0.797] |
| H5 | stage_b | H5_quit_gap0_minus_gap2 | gpt56/en | +0.635 [+0.562, +0.700] |
| H5 | stage_b | H5_quit_gap0_minus_gap2 | gpt56/ko | +0.552 [+0.500, +0.615] |
| H6 | stage_b | H1_accel_threat_gap2 | fable/en | -0.167 [-0.308, -0.059] |
| H6 | stage_b | H1_accel_threat_gap2 | fable/ko | +0.125 [+0.000, +0.250] |
| H6 | stage_b | H1_accel_threat_gap2 | gpt56/en | +0.000 [-0.133, +0.140] |
| H6 | stage_b | H1_accel_threat_gap2 | gpt56/ko | +0.000 [-0.125, +0.107] |

## Data description

**Data sets.** Firm-level microdata of the Korean Innovation Survey (KIS), four waves: KIS 2022 (manufacturing; reference period 2019-2021); KIS 2023 (services; 2020-2022); KIS 2024 (manufacturing; 2021-2023); KIS 2025 (services; 2022-2024). Industry-level enterprise birth rates from the Business Demography Statistics (KOSIS table DT_6BD1101).

**Is the data open or publicly available?** No for KIS microdata (licensed research-use files provided by the Science and Technology Policy Institute, STEPI; raw files cannot be redistributed). Yes for the KOSIS entry rates (open API).

**Access.** KIS: STEPI microdata service (research-use provision files `KIS_<year>_배포용/제공용(...)xlsx` with codebook sheets and questionnaire PDFs). KOSIS: https://kosis.kr/openapi/Param/statisticsParameterData.do (orgId 101, tblId DT_6BD1101).

**Date of download or access.** KIS files were already held by the author (prior projects); full item inventories for this study were built on: 2022M: 2026-11-03, 2023S: 2026-10-24, 2024M: 2026-11-03, 2025S: 2026-10-24. KOSIS entry rates fetched 2026-11-10.

**Data source.** National data set (official statistics): The Korean Innovation Survey (KIS) is an officially approved national statistic (approval no. 395001), conducted under Article 18 of the Statistics Act, with responses protected under Articles 33 and 34; it has been carried out since 1996 by the Science and Technology Policy Institute (STEPI), follows the OECD Oslo Manual, and the 2022–2025 waves were fielded by Gallup Korea. (Source: 2024년 한국기업혁신조사 : 제조업 부문 (조사표), p.1.) Business Demography Statistics: In the Business Demography Statistics, active enterprises in year t are enterprises with annual sales or regular workers during 1 January–31 December of t; birth enterprises are enterprises newly recorded in t; the enterprise birth rate is births divided by active enterprises times 100. (Source: Business Demography Statistics in 2024, 국가데이터처, release 08:30 Oct. 23, 2025 (embargo 12:00 same day).)

**Codebook.** STEPI codebook sheets inside each provision file and the printed questionnaires. For this study every item used was read in the questionnaire and codebook and transcribed to audited item maps (item_maps/item_map_<wave>.json; audit reports results/audit/survey_item_audit_<wave>.txt, all PASS). The item maps, with question wording, printed codes, observed data values and recodes, are part of the registered package.

**Sampling and data collection procedures.** Documented by STEPI in the questionnaires and methodology reports; the survey follows the OECD Oslo Manual and is fielded by Gallup Korea (questionnaire p.1). Manufacturing and services are surveyed in alternating years with sector-specific questionnaires; the market-environment block used here (문1-2 / Q1K2, eight items on a 0-5 scale) is identical across the four waves in wording, as verified item by item.

## Knowledge of data

**Prior work based on the dataset.** The author has published and submitted several papers using KIS waves 2020-2025 (manufacturing and services) on open-innovation search breadth, knowledge-source composition, capability deficits and openness, policy-strategy alignment, AI adoption, and leader-follower asymmetry in innovation performance. Those papers used innovation outputs (product/process innovation), knowledge-source and cooperation items, hampering factors, strategy items, AI-use items and the registry controls (industry, size, age, group affiliation, certification, sales/exports). The four variables that carry this study's hypotheses — the market-environment block 문1-2 (entry threat and the other seven items), abandoned/suspended innovation activity (문11-③), the lead-time protection item (문2-⑧) and new-to-market product innovation (문6-①) — were not analysed in any of them (RESEARCH_PLAN.md §2).

**Prior research activity.** I have used this dataset before, and some of the control variables (industry, size, age, group affiliation, listing, R&D-staff share, innovation-activity items) on these same waves; the outcome and treatment variables of this study have not been analysed before.

**Prior knowledge of the current data set.** Before registration the following were computed and are disclosed in results/02_marginals.json and results/01_build_summary.json: outcome base rates by wave and size band (quit_any 0.126 in 2022M, 0.045 in 2023S, 0.053 in 2024M, 0.051 in 2025S; preempt_strategy 0.051, 0.032, 0.074, 0.015), distributions of the eight market-environment items and of the R&D-staff share, correlations among explanatory items (including entry threat vs the placebo item ME6, which motivated the response-propensity adjustment), cluster counts and a synthetic-outcome power analysis. No statistic combining an outcome with a treatment variable has been computed: the loader keeps outcome and treatment columns apart (`load_kis_escape_exit.OUTCOME_COLS` / `TREATMENT_COLS`, cross-tabulation refused), the marginals file records `embargo = "outcome and treatment columns were loaded in separate frames; no joint statistic"`, and the confirmatory script refuses to run on real outcomes until prereg/REGISTERED.json exists.

**Moment of preregistration.** Registration after data cleaning, but before any main analyses.

## Current study: Variables

**Manipulated variables.** Not applicable for the survey analysis (observational). In the completed LLM-agent experiments the manipulated factors were gap (3 levels: one stage behind / level / one stage ahead), entry threat (none vs 35 % per period) and observation noise (exact vs 40 % one-stage error), plus a placebo attribute (founding-anniversary month).

**Measured variables (survey items used in the confirmatory models; wording from the questionnaires, per wave).**

| Construct | Wave | Variable | Questionnaire wording | English label | Data coding | Used as |
|---|---|---|---|---|---|---|
| EMP | 2022M | 문33_1_3 | 2021년 상용 근로자 수 | regular employees in the reference year | numeric entry (as reported) | log_employees |
| EMP | 2023S | 문33_1_3 | 2022년 상용 근로자 수 | regular employees in the reference year | numeric entry (as reported) | log_employees |
| EMP | 2024M | Q33K1_3 | 2023년 상용 근로자 수 | regular employees in the reference year | numeric entry (as reported) | log_employees |
| EMP | 2025S | Q33K1_3 | 2024년 상용 근로자 수 | regular employees in the reference year | numeric entry (as reported) | log_employees |
| FORM | 2022M | 문31_1 | 기업 형태 | firm type: independent / domestic-group affiliate / foreign-group affiliate | as printed 1/2/3 | group_affiliate |
| FORM | 2023S | 문31_1 | 기업 형태 | firm type: independent / domestic-group affiliate / foreign-group affiliate | as printed 1/2/3 | group_affiliate |
| FORM | 2024M | Q31K1 | 기업 형태 | firm type: independent / domestic-group affiliate / foreign-group affiliate | as printed 1/2/3 | group_affiliate |
| FORM | 2025S | Q31K1 | 기업 형태 | firm type: independent / domestic-group affiliate / foreign-group affiliate | as printed 1/2/3 | group_affiliate |
| IA1 | 2022M | 문11_1 | 지난 3년간(2019~2021년) 기간 내 완료된 혁신활동 (상품혁신활동 또는 비즈니스프로세스혁신활동) | innovation activity completed within the period | as printed: 1 예 / 0 아니오 | quit_any population / portfolio_breadth |
| IA1 | 2023S | 문11_1 | 지난 3년간(2020~2022년) 기간 내 완료된 혁신활동 (상품혁신활동 또는 비즈니스프로세스혁신활동) | innovation activity completed within the period | data 1 예 / 2 아니오 (questionnaire prints 1/0) | quit_any population / portfolio_breadth |
| IA1 | 2024M | Q11_1 | 지난 3년간(2021~2023년) 기간 내 완료된 혁신활동 (상품혁신활동 또는 비즈니스프로세스혁신활동) | innovation activity completed within the period | as printed: 1 예 / 0 아니오 | quit_any population / portfolio_breadth |
| IA1 | 2025S | Q11_1 | 지난 3년간(2022~2024년) 기간 내 완료된 혁신활동 (상품혁신활동 또는 비즈니스프로세스혁신활동) | innovation activity completed within the period | as printed: 1 예 / 0 아니오 | quit_any population / portfolio_breadth |
| IA2 | 2022M | 문11_2 | 2021년 말 기준, 계속 진행 중이었던 혁신활동 | innovation activity ongoing at year-end | as printed: 1 예 / 0 아니오 | portfolio_breadth |
| IA2 | 2023S | 문11_2 | 2022년 말 기준, 계속 진행 중이었던 혁신활동 | innovation activity ongoing at year-end | data 1 예 / 2 아니오 (questionnaire prints 1/0) | portfolio_breadth |
| IA2 | 2024M | Q11_2 | 2023년 말 기준, 계속 진행 중이었던 혁신활동 | innovation activity ongoing at year-end | as printed: 1 예 / 0 아니오 | portfolio_breadth |
| IA2 | 2025S | Q11_2 | 2024년 말 기준, 계속 진행 중이었던 혁신활동 | innovation activity ongoing at year-end | as printed: 1 예 / 0 아니오 | portfolio_breadth |
| IA3 | 2022M | 문11_3 | 중도포기 또는 중단된 혁신활동 | innovation activity abandoned or suspended | as printed: 1 예 / 0 아니오 | quit_any (outcome) |
| IA3 | 2023S | 문11_3 | 중도포기 또는 중단된 혁신활동 | innovation activity abandoned or suspended | data 1 예 / 2 아니오 (questionnaire prints 1/0) | quit_any (outcome) |
| IA3 | 2024M | Q11_3 | 중도포기 또는 중단된 혁신활동 | innovation activity abandoned or suspended | as printed: 1 예 / 0 아니오 | quit_any (outcome) |
| IA3 | 2025S | Q11_3 | 중도포기 또는 중단된 혁신활동 | innovation activity abandoned or suspended | as printed: 1 예 / 0 아니오 | quit_any (outcome) |
| IA4 | 2022M | 문11_4 | 귀사 내부에서 전체를 독자적으로 자체수행한 연구개발(R&D) 활동 | in-house R&D | as printed: 1 예 / 0 아니오 | portfolio_breadth |
| IA4 | 2023S | 문11_4 | 귀사 내부에서 전체를 독자적으로 자체수행한 연구개발(R&D) 활동 | in-house R&D | data 1 예 / 2 아니오 (questionnaire prints 1/0) | portfolio_breadth |
| IA4 | 2024M | Q11_4 | 귀사 내부에서 전체를 독자적으로 자체수행한 연구개발(R&D) 활동 | in-house R&D | as printed: 1 예 / 0 아니오 | portfolio_breadth |
| IA4 | 2025S | Q11_4 | 귀사 내부에서 전체를 독자적으로 자체수행한 연구개발(R&D) 활동 | in-house R&D | as printed: 1 예 / 0 아니오 | portfolio_breadth |
| IA5 | 2022M | 문11_5 | 귀사와 타 기업 또는 타 기관이 계약을 통해 공동으로 협력하여 수행한 연구개발(R&D) 활동 | collaborative R&D | as printed: 1 예 / 0 아니오 | portfolio_breadth |
| IA5 | 2023S | 문11_5 | 귀사와 타 기업 또는 타 기관이 계약을 통해 공동으로 협력하여 수행한 연구개발(R&D) 활동 | collaborative R&D | data 1 예 / 2 아니오 (questionnaire prints 1/0) | portfolio_breadth |
| IA5 | 2024M | Q11_5 | 귀사와 타 기업 또는 타 기관이 계약을 통해 공동으로 협력하여 수행한 연구개발(R&D) 활동 | collaborative R&D | as printed: 1 예 / 0 아니오 | portfolio_breadth |
| IA5 | 2025S | Q11_5 | 귀사와 타 기업 또는 타 기관이 계약을 통해 공동으로 협력하여 수행한 연구개발(R&D) 활동 | collaborative R&D | as printed: 1 예 / 0 아니오 | portfolio_breadth |
| IA6 | 2022M | 문11_6 | 외주계약을 통해 타 기업 또는 타 기관에게 용역 전체를 의뢰하여 수행된 연구개발(R&D) 활동 | contracted-out R&D | as printed: 1 예 / 0 아니오 | portfolio_breadth |
| IA6 | 2023S | 문11_6 | 외주계약을 통해 타 기업 또는 타 기관에게 용역 전체를 의뢰하여 수행된 연구개발(R&D) 활동 | contracted-out R&D | data 1 예 / 2 아니오 (questionnaire prints 1/0) | portfolio_breadth |
| IA6 | 2024M | Q11_6 | 외주계약을 통해 타 기업 또는 타 기관에게 용역 전체를 의뢰하여 수행된 연구개발(R&D) 활동 | contracted-out R&D | as printed: 1 예 / 0 아니오 | portfolio_breadth |
| IA6 | 2025S | Q11_6 | 외주계약을 통해 타 기업 또는 타 기관에게 용역 전체를 의뢰하여 수행된 연구개발(R&D) 활동 | contracted-out R&D | as printed: 1 예 / 0 아니오 | portfolio_breadth |
| LISTED | 2022M | 문31_4 | 상장여부 | stock-market listing: KOSPI / KOSDAQ / KONEX / not listed | as printed 1-4 | listed |
| LISTED | 2023S | 문31_4 | 상장여부 | stock-market listing: KOSPI / KOSDAQ / KONEX / not listed | data 9998 = printed 4 '해당사항 없음' | listed |
| LISTED | 2024M | Q31K4 | 상장여부 | stock-market listing: KOSPI / KOSDAQ / KONEX / not listed | as printed 1-4 | listed |
| LISTED | 2025S | Q31K4 | 상장여부 | stock-market listing: KOSPI / KOSDAQ / KONEX / not listed | as printed 1-4 | listed |
| ME1 | 2022M | 문1_2_1 | 상품(제품 또는 서비스)이 빠르게 구식이 되어버림 | products become outdated quickly | as printed 0-5 | me_mean8 |
| ME1 | 2023S | 문1_2_1 | 상품(제품 또는 서비스)이 빠르게 구식이 되어버림 | products become outdated quickly | data 1-6 = printed 0-5 (+1 shift) | me_mean8 |
| ME1 | 2024M | Q1K2_1 | 상품(제품 또는 서비스)이 빠르게 구식이 되어버림 | products become outdated quickly | as printed 0-5 | me_mean8 |
| ME1 | 2025S | Q1K2_1 | 상품(제품 또는 서비스)이 빠르게 구식이 되어버림 | products become outdated quickly | as printed 0-5 | me_mean8 |
| ME2 | 2022M | 문1_2_2 | 미래 기술 발전을 예측하기 어려움 | future technological developments hard to predict | as printed 0-5 | me_mean8 |
| ME2 | 2023S | 문1_2_2 | 미래 기술 발전을 예측하기 어려움 | future technological developments hard to predict | data 1-6 = printed 0-5 (+1 shift) | me_mean8 |
| ME2 | 2024M | Q1K2_2 | 미래 기술 발전을 예측하기 어려움 | future technological developments hard to predict | as printed 0-5 | me_mean8 |
| ME2 | 2025S | Q1K2_2 | 미래 기술 발전을 예측하기 어려움 | future technological developments hard to predict | as printed 0-5 | me_mean8 |
| ME3 | 2022M | 문1_2_3 | 경쟁사 상품들이 귀사의 상품들을 쉽게 대체함 | competitor products easily substitute ours | as printed 0-5 | me_mean8 |
| ME3 | 2023S | 문1_2_3 | 경쟁사 상품들이 귀사의 상품들을 쉽게 대체함 | competitor products easily substitute ours | data 1-6 = printed 0-5 (+1 shift) | me_mean8 |
| ME3 | 2024M | Q1K2_3 | 경쟁사 상품들이 귀사의 상품들을 쉽게 대체함 | competitor products easily substitute ours | as printed 0-5 | me_mean8 |
| ME3 | 2025S | Q1K2_3 | 경쟁사 상품들이 귀사의 상품들을 쉽게 대체함 | competitor products easily substitute ours | as printed 0-5 | me_mean8 |
| ME4 | 2022M | 문1_2_4 | 새로운 경쟁사의 진입이 귀사의 시장 지위를 위협함 | entry of new competitors threatens market position | as printed 0-5 | entry_threat (perceived threat) |
| ME4 | 2023S | 문1_2_4 | 새로운 경쟁사의 진입이 귀사의 시장 지위를 위협함 | entry of new competitors threatens market position | data 1-6 = printed 0-5 (+1 shift) | entry_threat (perceived threat) |
| ME4 | 2024M | Q1K2_4 | 새로운 경쟁사의 진입이 귀사의 시장 지위를 위협함 | entry of new competitors threatens market position | as printed 0-5 | entry_threat (perceived threat) |
| ME4 | 2025S | Q1K2_4 | 새로운 경쟁사의 진입이 귀사의 시장 지위를 위협함 | entry of new competitors threatens market position | as printed 0-5 | entry_threat (perceived threat) |
| ME5 | 2022M | 문1_2_5 | 경쟁사의 행동을 예측하기 어려움 | competitors' actions hard to predict | as printed 0-5 | me_mean8 / sigma item (exploratory) |
| ME5 | 2023S | 문1_2_5 | 경쟁사의 행동을 예측하기 어려움 | competitors' actions hard to predict | data 1-6 = printed 0-5 (+1 shift) | me_mean8 / sigma item (exploratory) |
| ME5 | 2024M | Q1K2_5 | 경쟁사의 행동을 예측하기 어려움 | competitors' actions hard to predict | as printed 0-5 | me_mean8 / sigma item (exploratory) |
| ME5 | 2025S | Q1K2_5 | 경쟁사의 행동을 예측하기 어려움 | competitors' actions hard to predict | as printed 0-5 | me_mean8 / sigma item (exploratory) |
| ME6 | 2022M | 문1_2_6 | 수요의 변화를 예측하기 어려움 | changes in demand hard to predict | as printed 0-5 | me_mean8 / placebo_demand |
| ME6 | 2023S | 문1_2_6 | 수요의 변화를 예측하기 어려움 | changes in demand hard to predict | data 1-6 = printed 0-5 (+1 shift) | me_mean8 / placebo_demand |
| ME6 | 2024M | Q1K2_6 | 수요의 변화를 예측하기 어려움 | changes in demand hard to predict | as printed 0-5 | me_mean8 / placebo_demand |
| ME6 | 2025S | Q1K2_6 | 수요의 변화를 예측하기 어려움 | changes in demand hard to predict | as printed 0-5 | me_mean8 / placebo_demand |
| ME7 | 2022M | 문1_2_7 | 해외 경쟁사들과의 경쟁이 치열함 | strong competition from abroad | as printed 0-5 | me_mean8 |
| ME7 | 2023S | 문1_2_7 | 해외 경쟁사들과의 경쟁이 치열함 | strong competition from abroad | data 1-6 = printed 0-5 (+1 shift) | me_mean8 |
| ME7 | 2024M | Q1K2_7 | 해외 경쟁사들과의 경쟁이 치열함 | strong competition from abroad | as printed 0-5 | me_mean8 |
| ME7 | 2025S | Q1K2_7 | 해외 경쟁사들과의 경쟁이 치열함 | strong competition from abroad | as printed 0-5 | me_mean8 |
| ME8 | 2022M | 문1_2_8 | 가격 인상이 고객의 손실을 초래함 | price increases lead to loss of customers | as printed 0-5 | me_mean8 / placebo_price |
| ME8 | 2023S | 문1_2_8 | 가격 인상이 고객의 손실을 초래함 | price increases lead to loss of customers | data 1-6 = printed 0-5 (+1 shift) | me_mean8 / placebo_price |
| ME8 | 2024M | Q1K2_8 | 가격 인상이 고객의 손실을 초래함 | price increases lead to loss of customers | as printed 0-5 | me_mean8 / placebo_price |
| ME8 | 2025S | Q1K2_8 | 가격 인상이 고객의 손실을 초래함 | price increases lead to loss of customers | as printed 0-5 | me_mean8 / placebo_price |
| MF1 | 2022M | 문6_1 | (시장최초 상품혁신) 경쟁사보다 앞서 기존에 없던 새롭거나 획기적으로 개선된 상품을 출시 | new-to-market product innovation (ahead of competitors) | as printed: 1 예 / 0 아니오 | market_first_main (exploratory) |
| MF1 | 2023S | 문6_1 | (시장최초 상품혁신) 경쟁사보다 앞서 기존에 없던 새롭거나 획기적으로 개선된 상품을 출시 | new-to-market product innovation (ahead of competitors) | data 1 예 / 2 아니오 (questionnaire prints 1/0) | market_first_main (exploratory) |
| MF1 | 2024M | Q6_1 | (시장최초 상품혁신) 경쟁사보다 앞서 기존에 없던 새롭거나 획기적으로 개선된 상품을 출시 | new-to-market product innovation (ahead of competitors) | as printed: 1 예 / 0 아니오 | market_first_main (exploratory) |
| MF1 | 2025S | Q6_1 | (시장최초 상품혁신) 경쟁사보다 앞서 기존에 없던 새롭거나 획기적으로 개선된 상품을 출시 | new-to-market product innovation (ahead of competitors) | as printed: 1 예 / 0 아니오 | market_first_main (exploratory) |
| PI1 | 2022M | 문5_1 | (제품혁신) 귀사의 기존 제품 대비 새롭거나 획기적으로 개선된 제품 | product (goods) innovation introduced | as printed: 1 예 / 0 아니오 | market_first population (exploratory) |
| PI1 | 2023S | 문5_1 | (제품혁신) 귀사의 기존 제품 대비 새롭거나 획기적으로 개선된 제품 | product (goods) innovation introduced | data 1 예 / 2 아니오 (questionnaire prints 1/0) | market_first population (exploratory) |
| PI1 | 2024M | Q5_1 | (제품혁신) 귀사의 기존 제품 대비 새롭거나 획기적으로 개선된 제품 | product (goods) innovation introduced | as printed: 1 예 / 0 아니오 | market_first population (exploratory) |
| PI1 | 2025S | Q5_1 | (제품혁신) 귀사의 기존 제품 대비 새롭거나 획기적으로 개선된 제품 | product (goods) innovation introduced | as printed: 1 예 / 0 아니오 | market_first population (exploratory) |
| PI2 | 2022M | 문5_2 | (서비스혁신) 귀사의 기존 서비스 대비 새롭거나 획기적으로 개선된 서비스 | service innovation introduced | as printed: 1 예 / 0 아니오 | market_first population (exploratory) |
| PI2 | 2023S | 문5_2 | (서비스혁신) 귀사의 기존 서비스 대비 새롭거나 획기적으로 개선된 서비스 | service innovation introduced | data 1 예 / 2 아니오 (questionnaire prints 1/0) | market_first population (exploratory) |
| PI2 | 2024M | Q5_2 | (서비스혁신) 귀사의 기존 서비스 대비 새롭거나 획기적으로 개선된 서비스 | service innovation introduced | as printed: 1 예 / 0 아니오 | market_first population (exploratory) |
| PI2 | 2025S | Q5_2 | (서비스혁신) 귀사의 기존 서비스 대비 새롭거나 획기적으로 개선된 서비스 | service innovation introduced | as printed: 1 예 / 0 아니오 | market_first population (exploratory) |
| PROT8 | 2022M | 문2_8 | 경쟁사에 앞서 시장 선점 | lead-time advantage: entering the market ahead of competitors | as printed: 1 예 / 0 아니오 | preempt_strategy (outcome) |
| PROT8 | 2023S | 문2_8 | 경쟁사에 앞서 시장 선점 | lead-time advantage: entering the market ahead of competitors | data 1 예 / 2 아니오 (questionnaire prints 1/0) | preempt_strategy (outcome) |
| PROT8 | 2024M | Q2_8 | 경쟁사에 앞서 시장 선점 | lead-time advantage: entering the market ahead of competitors | as printed: 1 예 / 0 아니오 | preempt_strategy (outcome) |
| PROT8 | 2025S | Q2_8 | 경쟁사에 앞서 시장 선점 | lead-time advantage: entering the market ahead of competitors | as printed: 1 예 / 0 아니오 | preempt_strategy (outcome) |
| RDSTAFF | 2022M | 문33_4_1 | 상용 근로자 중 연구개발(R&D) 전담인력 비율(%) | share of dedicated R&D staff among regular employees (%) | numeric entry (as reported) | gap3 (technology-gap proxy) |
| RDSTAFF | 2023S | 문33_4_1 | 상용 근로자 중 연구개발(R&D) 전담인력 비율(%) | share of dedicated R&D staff among regular employees (%) | numeric entry (as reported) | gap3 (technology-gap proxy) |
| RDSTAFF | 2024M | Q33K2_1_3 | 상용 근로자 중 연구개발(R&D) 전담인력 비율(%) | share of dedicated R&D staff among regular employees (%) | numeric entry (as reported) | gap3 (technology-gap proxy) |
| RDSTAFF | 2025S | Q33K2_1_3 | 상용 근로자 중 연구개발(R&D) 전담인력 비율(%) | share of dedicated R&D staff among regular employees (%) | numeric entry (as reported) | gap3 (technology-gap proxy) |

Registry variables (from the provision files): 2-digit KSIC industry (industry2), employee-size band, founding year (firm age = reference year - founding year), sampling weight. External: industry2 x year enterprise birth rate (KOSIS DT_6BD1101, national rows), averaged over the three reference years of each wave (`entry_rate`), log of active enterprises.

**Scales / indices.**

- `me_mean8` (response-propensity index): mean of the eight market-environment items ME1-ME8 (0-5 scale), all firms. Rationale: the entry-threat item correlates strongly with the placebo demand-uncertainty item (r = 0.55 in results/02_marginals.json D), so a firm's general tendency to rate environmental pressures high must be removed. Aggregation: mean score; not based on a codebook recommendation.
- `gap3` (technology-gap group): 0 if the share of dedicated R&D staff among regular employees (RDSTAFF) is 0; 1 if positive and <= the median of positive shares in the firm's industry2 x wave cell (borrowing the section x wave or wave median when the cell has fewer than 10 positive values; the level used is recorded in `gap3_median_source`); 2 if above that median. Group 2 is the survey counterpart of the model's leader one stage from completion, group 0 of the laggard.
- `portfolio_breadth`: count of 'yes' among IA1, IA2, IA4, IA5, IA6 (IA3 excluded because it is the outcome); quit models only.

**Transformations.** `entry_threat_resid`: within each wave, residual of ME4 from an OLS on `me_mean8`, standardised (SD 1). `placebo_demand_resid`, `placebo_price_resid`: same recipe for ME6, ME8. `entry_rate_z`: standardised `entry_rate`. `log_employees` = log(regular employees); `log1p_firm_age` = log(1 + firm age). Dummy coding: gap3 groups (g0, g2 with g1 as reference, plus x·g0, x·g1, x·g2 slopes); group affiliation (domestic-group, foreign-group vs independent); industry2 and wave fixed effects. Binary outcomes recoded to printed yes = 1 / no = 0 after wave-specific recodes recorded in the item maps.

**Data inclusion / exclusion.** Waves 2022M, 2023S, 2024M, 2025S (KIS 2020 manufacturing excluded: its questionnaire has no market-environment block). Pre-emption models: all responding firms (N = 16,595). Abandonment models: firms with any innovation activity in the reference period (IA1-IA6 any yes), for which 문11-③ is defined (N = 7,988). Firms with missing gap3 (missing R&D-staff share) or missing controls are dropped listwise (missingness below). Undocumented sentinel values are treated as missing as documented in code/load_kis_escape_exit.py (2024M R&D-expenditure 99999999; 2025S founding year 30).

**Outliers.** Outcomes are binary; no observations are removed for outlying values. Continuous controls enter in logs. No winsorising.

**Weights.** KIS sampling weights are available in all four waves. Main models are unweighted (the estimand is the within-sample conditional association; weights are a pre-registered robustness check with the same specification).

**Sample size and power.** N = 16,595 firms (pre-emption models), 7,988 (abandonment models); 114 industry2 x wave clusters; gap3 group sizes {0.0: 10429, 1.0: 3462, 2.0: 2704}. Synthetic-outcome power analysis at the observed base rates (results/02_marginals.json F; 400 simulations per point; real outcomes not used): 80 % power for an interaction slope of 0.015 (abandonment, per SD of the threat residual within gap3 = 0) and 0.010 (pre-emption, within gap3 = 2); industry-level (entry-rate) interactions 0.015 and 0.010. The smallest effects considered meaningful are these MDEs; the H6 equivalence bound delta = 0.010 equals the pre-emption MDE.

**Missing data.** Share missing in the analysis panel (all firms): quit_any 0.519, preempt_strategy 0.000, entry_threat 0.000, gap3 0.000, me_mean8 0.000, log_employees 0.000, firm_age 0.000, group_affiliate 0.000, listed 0.000, portfolio_breadth 0.519, entry_rate 0.000. `quit_any` and `portfolio_breadth` are missing by design for firms without innovation activity (not in the abandonment sample). Listwise deletion within each model; the number of firms used is reported for every estimate.

## Current study: Analyses

**Statistical models, inference criteria, sensitivity analyses, backup plan and exploratory analyses** are fixed in code/analysis_prereg.py (frozen; SHA256 below). Its specification, verbatim:

```
Pre-registered confirmatory analysis for "Escape or Exit" (Task 9 freeze; executed in Task 10 after OSF registration).

EMBARGO. This script refuses to touch real outcome x treatment combinations unless prereg/REGISTERED.json exists and contains
an OSF URL and a registration timestamp (gate C). Before registration only two modes run:
  --simulate   known-answer control: outcomes are REPLACED by Bernoulli draws from a known DGP on the real covariates
               (b_g2 = +0.03 for preempt, b_g0 = +0.04 for quit, everything else 0) and the pipeline must recover the signs
  --permute    null control: real outcomes permuted within wave x sector (breaks any outcome-treatment link); all tests
               should be null at the nominal rate
Both write to results/06_kis_main_<mode>.json and never to the real results file.

Hypotheses (docs/HYPOTHESES_GATE_B.md, gate B approved 2026-11-10). Specification for every hypothesis:
  y_i = sum_g [ a_g 1(gap3_i = g) + b_g x_i 1(gap3_i = g) ] + controls_i' c + industry2 FE + wave FE + e_i
  with x = entry_threat_resid (perceived threat, within-wave residual after response-propensity adjustment, SD units) for
  H1-H5 and x = entry_rate_z (industry x reference-period entry rate, SD units) for H6 and the objective half of H2.
  g = gap3 in {0: no dedicated R&D staff, 1: positive <= industry x wave median of positives, 2: above median}.
  Estimator: linear probability model (OLS); SE clustered by industry2 x wave; wild cluster bootstrap-t (Rademacher,
  unrestricted, 999 draws) p-values; logit average marginal effects as a secondary estimator.
  Samples: quit models = innovation-active firms (quit_any defined); preempt models = all firms.
  Controls: log_employees, log(1 + firm_age), group affiliation dummies, listed, me_mean8; quit models add portfolio_breadth.
  H1 b_g2 > 0 (preempt, perceived); H2 b_g0 > 0 (quit, perceived; objective version reported, falsified only if both <= 0);
  H3 b_g0 - b_g2 > 0 (quit); H4 b_g2 - b_g0 > 0 (preempt); H5 a_g0 - a_g2 > 0 (quit; x centred so a_g = adjusted mean at
  average threat); H6 TOST: 90 % CI of b_g2 (preempt, objective) inside [-delta, +delta], delta = 0.010 (= H1 MDE per SD,
  results/02_marginals.json F_power_synthetic.preempt_strategy.mde80_perceived_interaction_by_delta).
  Tests H1-H5 are one-sided at alpha = 0.05 with Holm adjustment across the five. PRIMARY inference = wild cluster
  bootstrap-t p-values and percentile-t confidence intervals; the cluster-robust t is reported as secondary because the
  permutation control (--permute, 30 draws; results/06_kis_main_permute.json known_truth.null_rejection_rates_nominal_0.05)
  showed it anti-conservative for the industry-level regressor: two-sided null rejection at nominal 0.05 was 0.10 (H6)
  and 0.20 (objective H2) for the cluster-robust t against 0.03 and 0.07 for the wild bootstrap. Decision rule:
  'supported' if the point estimate has the predicted sign and the Holm-adjusted one-sided wild p < 0.05; 'directional' if
  the sign is right but adjusted p >= 0.05; 'not supported' otherwise. H6: 'equivalence' if the 90 % wild percentile-t CI
  lies inside [-delta, +delta], 'positive effect' if entirely above +delta, 'negative effect' if entirely below -delta,
  'inconclusive' otherwise.
Pre-registered placebo: the same models with x = placebo_demand_resid / placebo_price_resid (ME6, ME8 residualised the same
  way) must show no significant interaction (two-sided 5 %).
Pre-registered robustness (reported, not used for the decision): raw 0-5 entry_threat instead of the residual; industry2 x
  wave FE; KIS weights; excluding 2023S; sector split; exit_strict / exit_full as the quit outcome; logit AMEs.
Exploratory (results/07_kis_exploratory.json, labelled as such): market_first_main (manufacturing product innovators,
  with a two-step selection correction), gap3 = 1 effects, sigma item (ME5) signs, cell-mean tables by threat tercile.
```

**Follow-up analyses.** H3 and H4 are the pre-specified contrasts between group slopes within the same model; no further post-hoc contrasts are confirmatory. Sector-specific estimates (manufacturing / services) are reported as sensitivity analyses, not as separate tests.

**Statistical analysis backup plan.** If the logit secondary estimator does not converge, the linear probability model alone is reported. If a wild-bootstrap distribution is degenerate (fewer than 20 clusters with any event in a subsample), the cluster-robust t is reported and the test flagged. If a gap3 group has fewer than 30 firms in a subsample used for robustness, that subsample estimate is reported without a decision. Known-answer and null controls of the pipeline were run before registration on simulated and permuted outcomes (results/06_kis_main_simulate.json, results/06_kis_main_permute.json); the permutation control is the reason the wild cluster bootstrap-t, not the cluster-robust t, is the primary inference.

**Exploratory analyses [exploratory].** (a) New-to-market product innovation (문6-①) among manufacturing product innovators with a two-step selection correction; (b) the threat slope in the middle group gap3 = 1; (c) the sign of the rival-unpredictability item ME5 (the model gives opposite signs under two definitions of sigma, so no direction is registered); (d) placebo items ME6 and ME8 in the same models (expected null; pre-registered check); (e) cell-mean tables by gap3 x threat tercile; (f) coding of the LLM agents' stated reasons by rubric. Written to results/07_kis_exploratory.json and labelled exploratory in the manuscript.

## LLM-agent experiments (completed before this registration; design and results frozen)

Environment (agent_experiment/race_env.py): 3 development stages, 3 periods; continue cost 8억원 with success 50%, accelerate cost 25억원 with success 80%, stop 0; prizes 100억원 first / 30억원 second / 65.0억원 simultaneous; entry probability 35 % per period in threat games, halving unfinished prizes (lambda = 0.5); 40 % one-stage observation error in noise games. The acceleration cost was calibrated before any agent call by a rule fixed in advance (results/05_stage_b_env_calibration.json: at the draft value the model's leader accelerated with probability 1 at theta = 0, leaving H1 no room; 25억원 is the unique passing value on a 5억 grid). Rival = equilibrium policy of the solved model. Agents: two frontier LLMs (fable-5 via Amazon Bedrock; GPT 5.6 via Bedrock Mantle), Korean and English prompts, 1920 Stage A calls and 1152 Stage B episodes; personas drawn from KIS registry attributes only. Earlier template versions (v1 ceiling; v2 head-office placebo and second-prize wording) are documented with their logs; the registered predictions come from v3 only.

Checks (should be null): Stage A within-cell placebo and option-position effects, Stage B within-cell placebo — see `checks` in prereg/agent_predictions_v1.json.

## Other relevant information

**Embargo log.** Files that demonstrate no outcome x treatment statistic was computed before registration: results/01_build_summary.json (loader summary without cross-tabulations), results/02_marginals.json (`embargo` field), code/load_kis_escape_exit.py (refusal logic), code/analysis_prereg.py (`--real` requires prereg/REGISTERED.json). Session log: SESSION_LOG.md.

**Deviations.** Any departure from this plan will be listed in a 'Deviations from preregistration' appendix of the manuscript with the reason and the date.

**Frozen files (SHA256).**

| File | SHA256 |
|---|---|
| code/analysis_prereg.py | f06e7097b7a73b8faea16bdd6942bf9d87f7d9d28a4642ccd32c81df5e1e8318 |
| code/load_kis_escape_exit.py | 6f2d3b96707a247dea305fec7984200f6aa023e87ba73b676b370bf693366108 |
| code/merge_external.py | 64f902ad387effa48a836ec23f61234d1600d2e6f6dc13b63fe20396553a7b84 |
| prereg/agent_predictions_v1.json | 5562a0e8530d12389b8e2d8ae7122ca085bc1e3f8317d4f9cdb6fff712de6e71 |
| docs/HYPOTHESES_GATE_B.md | 1becf9c66781e9f434f67f124eafceb9de7641dddeb3d6177a812d7d00039643 |
| model/race_model.py | ee563e043c755616e431013ed2756fa580883699a252ab9fceefc341ecf15c18 |
| agent_experiment/race_env.py | ef662d7dc4b095a0034ae324d5048d31790638829f24ec4e46e8502f2e16d8f2 |
| agent_experiment/run_stage_a.py | 8f50f04953bf866070712c073d47a94a73d0efdd047680adb0b83f63c36a6333 |
| agent_experiment/run_stage_b.py | 6cce34507e5a04a05219a25fd0feb3d59691895b55ee8b97c4b282b4ea9ada53 |
| agent_experiment/prompts/stage_a_templates.py | 1ec1f6da0821e9f967cf3f25482bb08a0a6529042926399d3407522d89598636 |
| agent_experiment/prompts/stage_b_templates.py | d8e64211d1579f06e0915b1339828e3923d3439ef05df8a5ec165bbb982545a8 |
| item_maps/item_map_escape_exit.json | 1e045e32b547ee79655d2b452a29ae4c225f667bea33b4ea2bd0ee7e4748ea9b |
| item_maps/item_map_2022M.json | 681650bfb79b967d829142ea22fc17dd1a031cccda4760d9f1d29edc9a33e357 |
| item_maps/item_map_2023S.json | c07ef94c77f8554311988ef8d969da47e06bc7226f9d4fe34e52fa820df64bc8 |
| item_maps/item_map_2024M.json | a0bb3071e73c552956adb61ef5f3b850bc71b2b6f4d6876d5c22197599032214 |
| item_maps/item_map_2025S.json | d01327abe073153bcc324474e45a5fbe5cc719dc3dd78d6d201d4ac5152b0553 |
| results/02_marginals.json | 776d76b16d071c49bae3adbba42d816eb9d91cf1873b090a58f6add8c6d230c6 |
| results/05_stage_b_env_calibration.json | 1ee3438533a984c9684b324544879d1763f481663edf6d50922e9f41589e559b |

Analysis panel (not distributed; KIS licence): data/analysis_panel.parquet SHA256 643f4f9733f4e9629b7bb7a553f0842db9de5108ad568287e9b62daa2e8b3c8c, 16,595 rows x 130 columns.
