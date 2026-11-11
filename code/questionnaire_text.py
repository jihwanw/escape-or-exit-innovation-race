# -*- coding: utf-8 -*-
"""Questionnaire wording transcribed by the agent on 2026-11-06 from the official KIS
questionnaire PDFs (pdftotext -layout output read block by block):

  혁신조사 2022(제조업) 설문지.pdf  (18 pp)  — blocks 문1-2, 문2, 문5~7, 문11, 문12, 문14, 문17, 문19, 문31~33
  혁신조사 2024(제조업) 설문지.pdf  (12 pp)  — entire questionnaire read
  혁신조사 2023(서비스업) 설문지.pdf (15 pp)  — blocks 문1-2, 문2, 문5~7, 문11, 문12, 문17, 문19, 문31~33
  혁신조사 2025(서비스업) 설문지.pdf (14 pp)  — blocks 문1-2, 문2, 문5~7, 문11, 문12, 문17, 문19, 문31~33

Every item string below is VERIFIED programmatically by build_item_maps.py against the
pdftotext output of each wave (whitespace-normalised substring match). A string that does
not occur in a wave's questionnaire makes the build fail for that wave, so the "same
wording in all four waves" claim is tested, not assumed.

Placeholders: {y0}-{y2} = three-year reference period, {y2} = reference calendar year
(2022M: 2019-2021; 2023S: 2020-2022; 2024M: 2021-2023; 2025S: 2022-2024).
"""

SCALE_0_5_APPLIES = ["0 해당없음", "1 매우낮음", "2 낮음", "3 보통", "4 높음", "5 매우높음"]
SCALE_0_5_HINDER = ["0 해당없음", "1 매우낮음", "2 낮음", "3 보통", "4 높음", "5 매우높음"]
YESNO = ["1 예", "0 아니오"]

BLOCKS = {
    "문1-2": {
        "stem": "[문1-2] 지난 3년간({y0}~{y2}년) 아래의 각 시장 환경 상황이 귀사가 직면했던 상황을 얼마나 잘 설명하고 있는지 설명도를 평가해 주십시오.",
        "stem_match": "아래의 각 시장 환경 상황이 귀사가 직면했던 상황을",
        "printed_codes": SCALE_0_5_APPLIES,
        "scale_note": "해당 없음 = 0; 해당하는 경우 설명도 1(매우 낮음)~5(매우 높음)",
        "filter": "전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황)",
        "items": {
            1: "상품(제품 또는 서비스)이 빠르게 구식이 되어버림",
            2: "미래 기술 발전을 예측하기 어려움",
            3: "경쟁사 상품들이 귀사의 상품들을 쉽게 대체함",
            4: "새로운 경쟁사의 진입이 귀사의 시장 지위를 위협함",
            5: "경쟁사의 행동을 예측하기 어려움",
            6: "수요의 변화를 예측하기 어려움",
            7: "해외 경쟁사들과의 경쟁이 치열함",
            8: "가격 인상이 고객의 손실을 초래함",
        },
        "short_en": {1: "products become outdated quickly", 2: "future technological developments hard to predict",
                     3: "competitor products easily substitute ours", 4: "entry of new competitors threatens market position",
                     5: "competitors' actions hard to predict", 6: "changes in demand hard to predict",
                     7: "strong competition from abroad", 8: "price increases lead to loss of customers"},
        "cis2020_equivalent": "CIS 2020 §2.2 (Eurostat harmonised questionnaire) — same eight items, 4-point 'applies' scale",
    },
    "문2": {
        "stem": "[문2] 지난 3년간({y0}~{y2}년) 귀사는 귀사의 상품(제품 또는 서비스)을 보호하기 위해 아래의 활동을 하였습니까?",
        "stem_match": "귀사의 상품(제품 또는 서비스)을 보호하기",
        "printed_codes": YESNO,
        "filter": "전 기업 응답",
        "items": {1: "특허권 출원", 2: "실용신안권 등록", 3: "디자인권 등록", 4: "상표권(트레이드마크) 등록",
                  5: "저작권(카피라이트) 청구", 6: "영업비밀", 7: "복잡한 설계방식 채택", 8: "경쟁사에 앞서 시장 선점"},
        "item_notes": {6: "설문지 원문 '⑥ 영업비밀4)로 보호' (각주 4: 비밀로 유지된 생산ㆍ판매 방법 또는 기술상ㆍ경영상 정보로서 관련 법률에 의해 법적으로 보호받을 수 있는 경우에 한함); pdftotext가 각주 번호를 분리해 '영업비밀 로 보호'로 추출됨"},
        "short_en": {1: "patent application", 2: "utility model registration", 3: "design right registration", 4: "trademark registration",
                     5: "copyright claim", 6: "trade secret protection", 7: "complex design", 8: "lead-time advantage: entering the market ahead of competitors"},
    },
    "문5": {
        "stem": "[문5] 지난 3년간({y0}~{y2}년) 귀사는 아래 상품혁신1) 유형에서, 귀사의 기존 상품(제품 또는 서비스) 대비 새롭거나 획기적으로 개선된 상품을 출시하였습니까?",
        "stem_match": "귀사의 기존 상품(제품",
        "printed_codes": YESNO,
        "filter": "전 기업 응답. 하나라도 '예'이면 상품혁신 수행 → 문6으로; 모두 '아니오'이면 문9로 이동",
        "items": {1: "(제품혁신) 귀사의 기존 제품 대비 새롭거나 획기적으로 개선된 제품",
                  2: "(서비스혁신) 귀사의 기존 서비스 대비 새롭거나 획기적으로 개선된 서비스"},
        "short_en": {1: "product (goods) innovation introduced", 2: "service innovation introduced"},
    },
    "문6": {
        "stem": "[문6] 지난 3년간({y0}~{y2}년) 출시했던 귀사의 상품혁신은 어떤 것이었습니까?",
        "stem_match": "출시했던 귀사의 상품혁신은 어떤 것이었습니까",
        "printed_codes": YESNO,
        "filter": "문5에서 하나라도 '예'인 기업만 (상품혁신 기업)",
        "items": {1: "(시장최초 상품혁신) 경쟁사보다 앞서 기존에 없던 새롭거나 획기적으로 개선된 상품을 출시",
                  2: "(자사최초 상품혁신) 경쟁사에서 이미 동일/유사한 상품을 출시하여 존재하나, 귀사의 기존 상품 대비 새롭거나 획기적으로 개선된 상품을 출시"},
        "item_match": {1: "경쟁사보다 앞서 기존에 없던 새롭거나 획", 2: "경쟁사에서 이미 동일/유사한 상품을 출"},
        "short_en": {1: "new-to-market product innovation (ahead of competitors)", 2: "new-to-firm product innovation"},
    },
    "문7": {
        "stem": "[문7] 귀사의 '{y2}년 한 해' 매출액을 100%로 놓았을 때, 아래 상품 유형별 매출 기여도(비중)를 각각 기입하여 주십시오.",
        "stem_match": "매출액을 100%로 놓았을 때, 아래 상품 유형별 매출",
        "printed_codes": ["% (합계 100%)"],
        "filter": "문5에서 하나라도 '예'인 기업만",
        "items": {1: "지난 3년간({y0}~{y2}년) 시장최초 상품혁신을 통해 출시한 상품",
                  2: "지난 3년간({y0}~{y2}년) 자사최초 상품혁신을 통해 출시한 상품",
                  3: "상품혁신에 해당하지 않는 그 외 상품* (귀사의 기존 상품 포함)"},
        "item_match": {1: "시장최초 상품혁신을 통해 출시한", 2: "자사최초 상품혁신을 통해 출시한", 3: "상품혁신에 해당하지 않는 그 외 상품"},
        "short_en": {1: "sales share of new-to-market products (%)", 2: "sales share of new-to-firm products (%)", 3: "sales share of unchanged products (%)"},
    },
    "문11": {
        "stem": "[문11] 지난 3년간({y0}~{y2}년) 귀사는 아래와 같은 혁신활동1)을 하였습니까?",
        "stem_match": "귀사는 아래와 같은 혁신활동",
        "printed_codes": YESNO,
        "filter": "전 기업 응답. ①~⑥ 모두 '아니오'이면 문17로 이동(문12~16 비응답). 각주 2: 문5 또는 문9에서 하나라도 '예'이면 ①에 반드시 '예'",
        "items": {1: "지난 3년간({y0}~{y2}년) 기간 내 완료된 혁신활동 (상품혁신활동 또는 비즈니스프로세스혁신활동)",
                  2: "{y2}년 말 기준, 계속 진행 중이었던 혁신활동",
                  3: "중도포기 또는 중단된 혁신활동",
                  4: "귀사 내부에서 전체를 독자적으로 자체수행한 연구개발(R&D) 활동",
                  5: "귀사와 타 기업 또는 타 기관이 계약을 통해 공동으로 협력하여 수행한 연구개발(R&D) 활동",
                  6: "외주계약을 통해 타 기업 또는 타 기관에게 용역 전체를 의뢰하여 수행된 연구개발(R&D) 활동"},
        "item_match": {1: "기간 내 완료된 혁신활동", 2: "년 말 기준, 계속 진행 중이었던 혁신활동", 3: "중도포기 또는 중단된 혁신활동",
                       4: "귀사 내부에서 전체를 독자적으로 자체수행한", 5: "계약을 통해 공동으", 6: "외주계약을 통해 타 기업 또는 타 기관에게 용역"},
        "short_en": {1: "innovation activity completed within the period", 2: "innovation activity ongoing at year-end",
                     3: "innovation activity abandoned or suspended", 4: "in-house R&D", 5: "collaborative R&D", 6: "contracted-out R&D"},
        "cis2020_equivalent": "CIS 2020 §3 'Innovation activities that did not lead to any innovation': ongoing / abandoned or suspended / completed",
    },
    "문11-4-1": {
        "stem": "[문11 ④-1] (④에 '예'인 경우) 지난 3년간({y0}~{y2}년) 귀사의 연구개발 활동 주기는 어떠하였습니까?",
        "stem_match": "귀사의 연구개발 활동 주기는 어떠하였습니까",
        "printed_codes": ["1 지속적으로 수행(기업 내부에 상시 연구 인력이 있음)", "2 가끔 수행(필요할 때에만 수행)"],
        "filter": "문11 ④(독자 수행 R&D) '예'인 기업만",
        "items": {1: "연구개발 활동 주기"},
        "item_match": {1: "연구개발 활동 주기는 어떠하였습니까"},
        "short_en": {1: "in-house R&D: continuous (1) vs occasional (2)"},
    },
    "문12": {
        "stem": "[문12] {y2}년 한 해 기준, 귀사에서 R&D 활동과 R&D 이외의 혁신활동에 사용한 비용(지출) 총액을 기입하여 주십시오.",
        "stem_match": "귀사에서 R&D 활동과 R&D 이외의 혁신활동에 사용한",
        "printed_codes": ["백만원"],
        "filter": "문11 ①~⑥ 중 하나라도 '예'인 기업만 (혁신활동 기업)",
        "items": {1: "R&D 활동 비용", 2: "R&D 이외의 혁신활동 비용"},
        "item_match": {1: "R&D 활동 비용", 2: "R&D 이외의 혁신활동 비용"},
        "short_en": {1: "R&D expenditure in the reference year (million KRW)", 2: "non-R&D innovation expenditure (million KRW)"},
    },
    "문14": {
        "stem": "[문14] 지난 3년간({y0}~{y2}년) 귀사는 혁신활동을 수행하기 위해 타 기업 또는 타 기관과 협력한 적이 있었습니까?",
        "stem_match": "귀사는 혁신활동을 수행하기 위해 타 기업",
        "printed_codes": YESNO,
        "filter": "문11 ①~⑥ 중 하나라도 '예'인 기업만",
        "items": {1: "R&D 활동에 대해 협력한 적이 있음", 2: "R&D 이외의 혁신활동으로 협력한 적이 있음", 3: "혁신활동 이외의 일반 활동으로 협력한 적이 있음"},
        "short_en": {1: "cooperated on R&D", 2: "cooperated on non-R&D innovation", 3: "cooperated on general (non-innovation) activities"},
    },
    "문17": {
        "stem": "[문17] 지난 3년간({y0}~{y2}년) 귀사는 '혁신활동'을 위해 어떤 유형의 자금 조달을 시도하였습니까? 시도한 경우, 성공적으로 자금을 조달하였습니까?",
        "stem_match": "어떤 유형의 자금 조달을",
        "printed_codes": ["0 시도하지 않았음", "1 조달 실패", "2 부분적으로 조달 성공", "3 성공적 조달"],
        "filter": "전 기업 응답",
        "items": {1: "기업 자체자금", 2: "계열사나 제휴회사 자금", 3: "은행 등으로부터 투·융자", 4: "주식 발행", 5: "회사채 발행",
                  6: "투자전문 개인/기관의 투자금", 7: "중앙정부 지원 자금", 8: "지자체 지원 자금"},
        "item_match": {6: "투자전문 개인/기관"},
        "short_en": {1: "own funds", 2: "group/affiliate funds", 3: "bank loans/investment", 4: "equity issue", 5: "bond issue",
                     6: "angel/VC/accelerator investment", 7: "central-government funds", 8: "local-government funds"},
    },
    "문19": {
        "stem": "[문19] 지난 3년간({y0}~{y2}년) 귀사가 혁신활동을 수행하지 못하거나 또는 수행하였더라도 성공적인 실현을 저해했던 요인이 있었습니까? 그렇다면, 아래 항목별로 혁신활동 저해도를 평가하여 주십시오.",
        "stem_match": "귀사가 혁신활동을 수행하지 못하거나",
        "printed_codes": SCALE_0_5_HINDER,
        "filter": "전 기업 응답",
        "items": {12: "혁신 상품/아이디어에 대한 시장수요 불확실", 13: "과도한 시장 경쟁으로 혁신활동 수행 여력 부족", 16: "시장의 경쟁 압력이 낮아 혁신 불필요"},
        "item_match": {12: "대한 시장수요 불확실"},
        "short_en": {12: "hampering factor: uncertain market demand for innovations", 13: "hampering factor: excessive market competition leaves no capacity to innovate",
                     16: "reason not to innovate: weak competitive pressure"},
    },
    "문31": {
        "stem": "[문31] {y2}년 12월 말 기준으로 귀사의 운영 상황과 일치하는 항목에 응답하여 주십시오.",
        "stem_match": "년 12월 말 기준으로 귀사의 운영 상황과 일치하는 항목에",
        "printed_codes": ["기업 형태: 1 독립기업 / 2 국내그룹 계열사 / 3 해외그룹 계열사", "법정기업규모: 1 소기업 / 2 중기업 / 3 중견기업 / 4 대기업",
                          "인증여부(중복응답): 1 벤처기업 / 2 부설연구소/연구개발 전담 부서 / 3 이노비즈 / 4 메인비즈 / 5 그린비즈 / 6 부품소재전문기업 / 7 ISO / 8 여성기업 / 9 해당사항 없음",
                          "상장여부: 1 거래소 상장기업(KOSPI) / 2 코스닥 상장기업 / 3 코넥스 상장기업 / 4 해당사항 없음"],
        "filter": "전 기업 응답",
        "items": {"form": "기업 형태", "legal_size": "법정기업규모", "cert1": "벤처기업", "cert2": "부설연구소/연구개발 전담 부서", "cert3": "이노비즈",
                  "cert4": "메인비즈", "cert5": "그린비즈", "cert6": "부품소재전문기업", "cert7": "ISO", "cert8": "여성기업", "cert9": "해당사항 없음", "listed": "상장여부"},
        "short_en": {"form": "firm type: independent / domestic-group affiliate / foreign-group affiliate", "legal_size": "statutory firm size: small / medium / mid-sized / large",
                     "cert1": "certified venture firm", "cert2": "has a registered R&D institute or dedicated R&D department", "cert3": "Inno-Biz certification",
                     "cert4": "Main-Biz certification", "cert5": "Green-Biz certification", "cert6": "parts & materials specialist firm", "cert7": "ISO certification",
                     "cert8": "women-owned firm", "cert9": "no certification", "listed": "stock-market listing: KOSPI / KOSDAQ / KONEX / not listed"},
    },
    "문32": {
        "stem": "[문32] 지난 3년간({y0}~{y2}년) 귀사의 연간 매출액과 수출액은 얼마였습니까? 각각 금액을 기입하여 주십시오.",
        "stem_match": "귀사의 연간 매출액과 수출액",
        "printed_codes": ["백만원 (종속회사를 보유한 기업은 별도 재무제표 기준)"],
        "filter": "전 기업 응답",
        "items": {"sales": "매출액 {y2}년", "exports": "수출액 {y2}년"},
        "item_match": {"sales": "매출액", "exports": "수출액"},
        "short_en": {"sales": "sales in the reference year (million KRW)", "exports": "exports in the reference year (million KRW)"},
    },
    "문33": {
        "stem": "[문33] 지난 3년간({y0}~{y2}년)의 귀사의 인력 규모(상용 근로자 수)에 대하여 기입하여 주십시오. 특히, {y2}년에 한해서는 상용 근로자 중 여성인력, 석사학위 이상, 연구개발(R&D) 전담인력 비율(%)을 각각 기입하여 주십시오.",
        "stem_match": "상용 근로자 중 여성인력, 석사학위",
        "printed_codes": ["명 / %"],
        "filter": "전 기업 응답",
        "items": {"emp": "{y2}년 상용 근로자 수", "female": "상용 근로자 중 여성인력 비율(%)", "masters": "상용 근로자 중 석사학위 이상 비율(%)", "rd_staff": "상용 근로자 중 연구개발(R&D) 전담인력 비율(%)"},
        "item_match": {"emp": "상용 근로자 수", "female": "여성인력 비율", "masters": "석사학위 이상 비율", "rd_staff": "전담인력 비율"},
        "short_en": {"emp": "regular employees in the reference year", "female": "share of women among regular employees (%)",
                     "masters": "share with a master's degree or higher (%)", "rd_staff": "share of dedicated R&D staff among regular employees (%)"},
    },
}
