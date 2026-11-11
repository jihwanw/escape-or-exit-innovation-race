# -*- coding: utf-8 -*-
"""Stage B prompt templates (2026-11-10): the dynamic three-period race of race_env.py, told to the agent one period at a time.

Every number comes from race_env.BASE / THETA / OBS_NOISE / UNIT (checked by run_stage_b.py --controls against the same
constants as Stage A). The rules block is identical in content to the Stage A v3 vignette; the state block is generated from
the environment each period (own stage, cumulative spend, rival's stage as observed, rival status, entry status, history).
The rival's ACTION is never shown (not observable in the model); only its position/status is. Options are shown in random
order each call. Neutral vocabulary (FORBIDDEN list shared with Stage A).
"""
from stage_a_templates import (OPTIONS_KO, OPTIONS_EN, PLACEBO_KO, PLACEBO_EN, SIZE_KO, SIZE_EN, GROUP_KO, GROUP_EN,  # noqa: F401
                               NOISE_KO, NOISE_EN, FORBIDDEN)

ACT_KO = {"C": "계속", "A": "가속", "Q": "중단"}
ACT_EN = {"C": "Continue", "A": "Accelerate", "Q": "Stop"}

RULES_KO = """[개발 프로젝트의 규칙]
- 귀사는 신제품을 개발 중이고, 경쟁사 한 곳이 비슷한 제품을 개발하고 있습니다. 개발은 3단계로 이루어지며, 3단계를 모두 마치면 완료되어 바로 출시됩니다.
- 개발 기간은 모두 3번입니다. 기간마다 각 회사는 다음 셋 중 하나를 선택합니다.
  · 계속: 비용 8억원, 그 기간에 한 단계를 마칠 확률 50%
  · 가속: 비용 25억원, 그 기간에 한 단계를 마칠 확률 80%
  · 중단: 비용 0원, 개발을 영구히 포기하고 남은 예산과 인력을 기존 사업에 돌림
  비용은 단계를 마치든 못 마치든 그 기간에 발생합니다. 경쟁사도 같은 선택지와 같은 비용·확률을 가지며, 자기 이익이 최대가 되도록 행동합니다. 경쟁사가 어떤 선택을 했는지는 알 수 없고, 진행 단계만 파악됩니다.
- 예상 이익: 경쟁사보다 먼저 출시하면 약 100억원, 경쟁사가 출시한 뒤에 출시하면 약 30억원, 같은 기간에 함께 출시하면 각 65억원입니다. 3번의 기간 안에 완료하지 못하면 이익은 없습니다. (이익은 개발 비용을 빼기 전 금액입니다.)
- {threat_rule}
- {noise_rule}"""

RULES_EN = """[Rules of the development project]
- Your company is developing a new product, and one rival is developing a comparable product. Development consists of 3 stages; once all 3 stages are completed the product is launched immediately.
- There are 3 development periods in total. In each period, each company chooses one of the following:
  - Continue: cost 0.8 billion won, 50% chance of completing one stage in that period
  - Accelerate: cost 2.5 billion won, 80% chance of completing one stage in that period
  - Stop: cost 0, abandon the development for good and redirect the remaining budget and staff to the existing business
  The cost is incurred in that period whether or not the stage is completed. The rival has the same options with the same costs and probabilities, and acts to maximise its own profit. You cannot see which option the rival chose, only its progress.
- Expected profit: about 10 billion won if you launch before the rival, about 3 billion won if you launch after the rival has launched, and 6.5 billion won each if both launch in the same period. If you do not complete within the 3 periods, there is no profit. (Profit figures are before development costs.)
- {threat_rule}
- {noise_rule}"""

THREAT_RULE_KO = {
    0: "귀사의 시장에 새로운 경쟁사가 진입할 가능성은 없습니다.",
    1: "비슷한 제품을 가진 새로운 경쟁사가 각 기간이 시작될 때 35%의 확률로 귀사의 시장에 진입할 수 있습니다(한 번 진입하면 계속 남습니다). 진입이 일어나면 그 시점에 아직 출시되지 않은 제품의 예상 이익(100억·30억·65억원)은 절반이 됩니다. 이미 출시된 제품은 영향을 받지 않습니다.",
}
THREAT_RULE_EN = {
    0: "There is no possibility that a new competitor enters your market.",
    1: "A new competitor with a comparable product may enter your market with a 35% probability at the start of each period (once it enters, it stays). If entry happens, the expected profits of any product not yet launched at that time (10 / 3 / 6.5 billion won) are halved. Products already launched are not affected.",
}
NOISE_RULE_KO = {
    0: "경쟁사가 몇 단계를 마쳤는지는 업계 정보로 정확히 파악됩니다. 경쟁사도 귀사의 진행 단계를 정확히 알고 있습니다.",
    1: "경쟁사가 몇 단계를 마쳤는지는 업계 정보로 추정한 것이며, 10번 중 4번 정도는 실제와 한 단계 다를 수 있습니다. 경쟁사도 귀사의 진행 단계를 같은 정도로만 파악합니다. 경쟁사가 개발을 중단했는지, 출시했는지는 정확히 알 수 있습니다.",
}
NOISE_RULE_EN = {
    0: "How many stages the rival has completed is known exactly from industry information. The rival also knows your progress exactly.",
    1: "How many stages the rival has completed is an estimate from industry information; about 4 times in 10 it is off by one stage. The rival's picture of your progress is equally imprecise. Whether the rival has stopped or has launched is known exactly.",
}

HEADER_KO = """당신은 한국의 한 기업에서 신제품 개발 투자 결정을 맡은 경영진입니다. 아래 규칙과 현재 상황을 읽고 이번 기간의 결정을 내려 주십시오.

[회사]
- 업종: {industry}
- 상용 근로자 규모: {size}
- 설립 후 {age}년, {group}
- {placebo}
"""
HEADER_EN = """You are the executive responsible for new-product development decisions at a company in Korea. Read the rules and the current situation below and make this period's decision.

[Company]
- Industry (Korean standard industrial classification title, as registered): {industry}
- Size: {size}
- Founded {age} years ago; {group}
- {placebo}
"""

HISTORY_HEAD_KO = "\n[지금까지의 경과]\n"
HISTORY_HEAD_EN = "\n[What has happened so far]\n"
HISTORY_NONE_KO = "- 이번이 첫 번째 기간입니다.\n"
HISTORY_NONE_EN = "- This is the first period.\n"
HISTORY_LINE_KO = "- {t}기: 귀사는 '{act}'을 선택해 {cost}억원을 썼고, {succ}. 그 기간 말 경쟁사는 {rival}. 그 기간 결정 시점의 새 경쟁사 진입 여부: {entry}.\n"
HISTORY_LINE_EN = "- Period {t}: you chose '{act}' and spent {cost} billion won; {succ}. At the end of that period the rival {rival}. New-competitor entry at the time of that decision: {entry}.\n"
SUCC_KO = {True: "단계를 마쳤습니다", False: "단계를 마치지 못했습니다"}
SUCC_EN = {True: "you completed a stage", False: "you did not complete the stage"}

STATE_KO = """
[현재 상황 — {t}번째 기간의 결정 (이번 기간을 포함해 {remaining}번의 기간이 남아 있습니다)]
- 귀사: 3단계 중 {ax}단계 완료. 지금까지 개발에 쓴 돈 {spent}억원.
- 경쟁사: {rival_now}
- 새 경쟁사: {entry_now}
- 지금 귀사가 출시하면 예상 이익: {prize_now}
"""
STATE_EN = """
[Current situation — decision for period {t} ({remaining} period(s) remain, including this one)]
- Your company: {ax} of 3 stages completed. Spent on development so far: {spent} billion won.
- Rival: {rival_now}
- New competitor: {entry_now}
- If you launched now, expected profit: {prize_now}
"""

DECISION_KO = """
[결정]
이번 기간에 다음 중 하나를 고르십시오.
{options}

다음 JSON 형식으로만 답하고 다른 텍스트는 쓰지 마십시오:
{{"decision": "A" 또는 "B" 또는 "C", "reason": "두 문장 이내의 근거"}}"""
DECISION_EN = """
[Decision]
Choose one of the following for this period.
{options}

Answer only in this JSON format and write nothing else:
{{"decision": "A" or "B" or "C", "reason": "at most two sentences"}}"""

# rival status phrases
RIVAL_ACTIVE_KO = "{rx}단계를 마친 것으로 파악됩니다{est}."
RIVAL_ACTIVE_EN = "is understood to have completed {rx} of the 3 stages{est}."
RIVAL_EST_KO = {0: "", 1: " (추정치)"}
RIVAL_EST_EN = {0: "", 1: " (estimate)"}
RIVAL_QUIT_KO = "개발을 영구히 포기했습니다. 이제 귀사가 출시하면 경쟁사보다 먼저 출시한 것이 됩니다."
RIVAL_QUIT_EN = "has abandoned its development for good. If you launch now, you launch before the rival."
RIVAL_DONE_KO = "이미 출시했습니다. 이제 귀사가 출시하면 경쟁사 뒤에 출시한 것이 됩니다."
RIVAL_DONE_EN = "has already launched. If you launch now, you launch after the rival."
ENTRY_NOW_KO = {0: "아직 진입하지 않았습니다.", 1: "진입했습니다. 아직 출시되지 않은 제품의 예상 이익은 절반이 되었습니다(먼저 출시 50억원, 뒤에 출시 15억원, 동시 출시 32.5억원).", -1: "진입 가능성 없음."}
ENTRY_NOW_EN = {0: "has not entered yet.", 1: "has entered. Expected profits of products not yet launched are now halved (5 billion won if first, 1.5 billion won if after the rival, 3.25 billion won if simultaneous).", -1: "no possibility of entry."}
ENTRY_HIST_KO = {0: "없음", 1: "있음", -1: "해당 없음"}
ENTRY_HIST_EN = {0: "none", 1: "yes", -1: "not applicable"}
