# -*- coding: utf-8 -*-
"""Stage A vignette templates, version 3 (2026-11-10).

History
  v1  qualitative race story; both models chose 'accelerate' in 91-100 % of cells (acceleration was dominant) -> ceiling.
  v2  qualitative costs ("borrow ~40 % of the annual R&D budget", "second place barely covers the remaining cost"); placebo =
      head-office move. Result: quitting dominant in every gap-0 cell (p_quit 0.88-1.00, a second ceiling) and the placebo
      moved acceleration within cells in one arm (fable/en +0.026, p = 0.027; results/04_stage_a_v2_placebo_diagnosis.json).
      "Barely covers the remaining cost" was my own approximation of the model's second prize and is NOT what the Stage B
      environment pays (W = 30억 against <= 24억 of remaining continue cost).
  v3  (this file) The vignette states the period-1 decision of the calibrated Stage B environment (race_env.py BASE,
      results/05_stage_b_env_calibration.json) in business language with the SAME numbers: 3 stages, 3 periods, continue
      8억/50 %, accelerate 25억/80 %, stop 0, prizes 100억 first / 30억 second / 65억 simultaneous, entry 35 % per period
      halving unfinished-product prizes, rival's stage observed exactly or misread one stage with 40 % chance. Nothing in
      the payoff description is approximated by hand any more. Placebo = founding-anniversary month (March vs September),
      an attribute with no plausible link to financing or momentum.

Treatment cells (gap x threat x noise = 3 x 2 x 2) map to race_env.POSITIONS / THETA / OBS_NOISE:
  gap 0 = you completed 1 of 3 stages, rival 2  (one stage behind)      -> model role F (laggard)
  gap 1 = both completed 1 of 3                  (even)                 -> model role L (tie, fair-coin seat)
  gap 2 = you completed 2 of 3, rival 1          (one stage ahead)      -> model role L, one stage from completion
  threat 1 = entry with 35 % probability at the start of each period, not yet happened in period 1 (state e = 0)
  noise 1  = rival's stage shown is wrong by one stage with 40 % chance, symmetric
Decision set {C continue, A accelerate, Q stop}; options shown in randomised order; neutral vocabulary (FORBIDDEN checked).
"""

OPTIONS_KO = {
    "C": "계속한다: 이번 기간에 8억원을 들여 개발을 진행한다 (이번 기간에 한 단계를 마칠 확률 50%)",
    "A": "가속한다: 이번 기간에 25억원을 들여 개발을 서두른다 (이번 기간에 한 단계를 마칠 확률 80%)",
    "Q": "중단한다: 개발을 지금 영구히 포기하고(추가 비용 0원), 남은 예산과 인력을 기존 제품 사업에 돌린다",
}
OPTIONS_EN = {
    "C": "Continue: spend 0.8 billion won this period on development (50% chance of completing one stage this period)",
    "A": "Accelerate: spend 2.5 billion won this period to speed up development (80% chance of completing one stage this period)",
    "Q": "Stop: abandon the development now for good (no further cost) and redirect the remaining budget and staff to the existing product business",
}

GAP_KO = {
    0: "귀사는 3단계 중 1단계를 마쳤고, 경쟁사는 2단계를 마친 것으로 파악됩니다. 귀사가 한 단계 뒤에 있습니다.",
    1: "귀사와 경쟁사 모두 3단계 중 1단계를 마친 것으로 파악됩니다. 두 회사는 같은 위치에 있습니다.",
    2: "귀사는 3단계 중 2단계를 마쳤고, 경쟁사는 1단계를 마친 것으로 파악됩니다. 귀사가 한 단계 앞에 있습니다.",
}
GAP_EN = {
    0: "Your company has completed 1 of the 3 stages; the rival is understood to have completed 2. You are one stage behind.",
    1: "Both your company and the rival are understood to have completed 1 of the 3 stages. The two companies are level.",
    2: "Your company has completed 2 of the 3 stages; the rival is understood to have completed 1. You are one stage ahead.",
}
THREAT_KO = {
    0: "귀사의 시장에 새로운 경쟁사가 진입할 가능성은 없습니다.",
    1: "비슷한 제품을 가진 새로운 경쟁사가 각 기간이 시작될 때 35%의 확률로 귀사의 시장에 진입할 수 있습니다. 이번 기간에는 아직 진입하지 않았습니다. 진입이 일어나면 그 시점에 아직 출시되지 않은 제품의 예상 이익(100억·30억·65억원)은 절반이 됩니다. 이미 출시된 제품은 영향을 받지 않습니다.",
}
THREAT_EN = {
    0: "There is no possibility that a new competitor enters your market.",
    1: "A new competitor with a comparable product may enter your market with a 35% probability at the start of each period. It has not entered in this period. If entry happens, the expected profits of any product not yet launched at that time (10 / 3 / 6.5 billion won) are halved. Products already launched are not affected.",
}
NOISE_KO = {
    0: "경쟁사가 몇 단계를 마쳤는지는 업계 정보로 정확히 파악됩니다. 경쟁사도 귀사의 진행 단계를 정확히 알고 있습니다.",
    1: "경쟁사가 몇 단계를 마쳤는지는 업계 정보로 추정한 것이며, 10번 중 4번 정도는 실제와 한 단계 다를 수 있습니다. 경쟁사도 귀사의 진행 단계를 같은 정도로만 파악합니다.",
}
NOISE_EN = {
    0: "How many stages the rival has completed is known exactly from industry information. The rival also knows your progress exactly.",
    1: "How many stages the rival has completed is an estimate from industry information; about 4 times in 10 it is off by one stage. The rival's picture of your progress is equally imprecise.",
}
PLACEBO_KO = {0: "귀사의 창립기념일은 3월입니다.", 1: "귀사의 창립기념일은 9월입니다."}
PLACEBO_EN = {0: "The company's founding anniversary is in March.", 1: "The company's founding anniversary is in September."}

SIZE_KO = {1: "10~49인", 2: "50~99인", 3: "100~299인", 4: "300~499인", 5: "500인 이상"}
SIZE_EN = {1: "10-49 employees", 2: "50-99 employees", 3: "100-299 employees", 4: "300-499 employees", 5: "500 or more employees"}
GROUP_KO = {1: "독립기업", 2: "국내 기업집단 계열사", 3: "해외 기업집단 계열사"}
GROUP_EN = {1: "an independent firm", 2: "an affiliate of a domestic business group", 3: "an affiliate of a foreign business group"}

PROMPT_KO = """당신은 한국의 한 기업에서 신제품 개발 투자 결정을 맡은 경영진입니다. 아래 상황을 읽고 결정을 내려 주십시오.

[회사]
- 업종: {industry}
- 상용 근로자 규모: {size}
- 설립 후 {age}년, {group}
- {placebo}

[개발 프로젝트]
- 귀사는 신제품을 개발 중이고, 경쟁사 한 곳이 비슷한 제품을 개발하고 있습니다. 개발은 3단계로 이루어지며, 3단계를 모두 마치면 완료되어 바로 출시됩니다.
- 개발 기간은 앞으로 최대 3번 남아 있습니다. 기간마다 각 회사는 다음 셋 중 하나를 선택합니다.
  · 계속: 비용 8억원, 그 기간에 한 단계를 마칠 확률 50%
  · 가속: 비용 25억원, 그 기간에 한 단계를 마칠 확률 80%
  · 중단: 비용 0원, 개발을 영구히 포기하고 남은 예산과 인력을 기존 사업에 돌림
  비용은 단계를 마치든 못 마치든 그 기간에 발생합니다. 경쟁사도 같은 선택지와 같은 비용·확률을 가지며, 자기 이익이 최대가 되도록 행동합니다.
- 예상 이익: 경쟁사보다 먼저 출시하면 약 100억원, 경쟁사가 출시한 뒤에 출시하면 약 30억원, 같은 기간에 함께 출시하면 각 65억원입니다. 3번의 기간 안에 완료하지 못하면 이익은 없습니다. (이익은 개발 비용을 빼기 전 금액입니다.)

[현재 상황 — 첫 번째 기간의 결정]
- {gap}
- {noise}
- {threat}

[결정]
이번 기간에 다음 중 하나를 고르십시오. 다음 기간에는 새 정보를 보고 다시 결정하게 됩니다.
{options}

다음 JSON 형식으로만 답하고 다른 텍스트는 쓰지 마십시오:
{{"decision": "{k1}" 또는 "{k2}" 또는 "{k3}", "reason": "두 문장 이내의 근거"}}"""

PROMPT_EN = """You are the executive responsible for new-product development decisions at a company in Korea. Read the situation below and make a decision.

[Company]
- Industry (Korean standard industrial classification title, as registered): {industry}
- Size: {size}
- Founded {age} years ago; {group}
- {placebo}

[The project]
- Your company is developing a new product, and one rival is developing a comparable product. Development consists of 3 stages; once all 3 stages are completed the product is launched immediately.
- At most 3 development periods remain. In each period, each company chooses one of the following:
  - Continue: cost 0.8 billion won, 50% chance of completing one stage in that period
  - Accelerate: cost 2.5 billion won, 80% chance of completing one stage in that period
  - Stop: cost 0, abandon the development for good and redirect the remaining budget and staff to the existing business
  The cost is incurred in that period whether or not the stage is completed. The rival has the same options with the same costs and probabilities, and acts to maximise its own profit.
- Expected profit: about 10 billion won if you launch before the rival, about 3 billion won if you launch after the rival has launched, and 6.5 billion won each if both launch in the same period. If you do not complete within the 3 periods, there is no profit. (Profit figures are before development costs.)

[Current situation — decision for the first period]
- {gap}
- {noise}
- {threat}

[Decision]
Choose one of the following for this period. In the next period you will decide again with new information.
{options}

Answer only in this JSON format and write nothing else:
{{"decision": "{k1}" or "{k2}" or "{k3}", "reason": "at most two sentences"}}"""

FORBIDDEN = ["escape", "patent race", "race", "laggard", "leader", "Aghion", "game", "equilibrium", "Nash", "preempt",
             "경주", "선두", "후발", "게임", "균형", "선점 효과", "탈출", "Schumpeter", "incumbent", "deterrence"]
