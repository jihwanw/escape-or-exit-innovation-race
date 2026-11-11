# 변수 설명표 (Table F.1형) — `code/build_item_maps.py`가 item map에서 생성. 손으로 고치지 말 것.

생성 2026-11-09 20:00 KST. 각 행의 문항 원문은 해당 파동 설문지 PDF 텍스트와 대조해 확인된 것이다. 데이터 코딩은 관측값과 설문지 인쇄 코드를 비교해 도출했다.

| 구성개념 ID | 파동 | 변수명 | 설문지 문항 원문 | 영문 짧은 라벨 | 데이터 코딩 | 응답 대상(필터) |
|---|---|---|---|---|---|---|
| ME1 | 2022M | 문1_2_1 | 상품(제품 또는 서비스)이 빠르게 구식이 되어버림 | products become outdated quickly | as printed 0-5 | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT1 | 2022M | 문2_1 | 특허권 출원 | patent application | as printed: 1 예 / 0 아니오 | 전 기업 응답 |
| ME2 | 2022M | 문1_2_2 | 미래 기술 발전을 예측하기 어려움 | future technological developments hard to predict | as printed 0-5 | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT2 | 2022M | 문2_2 | 실용신안권 등록 | utility model registration | as printed: 1 예 / 0 아니오 | 전 기업 응답 |
| ME3 | 2022M | 문1_2_3 | 경쟁사 상품들이 귀사의 상품들을 쉽게 대체함 | competitor products easily substitute ours | as printed 0-5 | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT3 | 2022M | 문2_3 | 디자인권 등록 | design right registration | as printed: 1 예 / 0 아니오 | 전 기업 응답 |
| ME4 | 2022M | 문1_2_4 | 새로운 경쟁사의 진입이 귀사의 시장 지위를 위협함 | entry of new competitors threatens market position | as printed 0-5 | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT4 | 2022M | 문2_4 | 상표권(트레이드마크) 등록 | trademark registration | as printed: 1 예 / 0 아니오 | 전 기업 응답 |
| ME5 | 2022M | 문1_2_5 | 경쟁사의 행동을 예측하기 어려움 | competitors' actions hard to predict | as printed 0-5 | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT5 | 2022M | 문2_5 | 저작권(카피라이트) 청구 | copyright claim | as printed: 1 예 / 0 아니오 | 전 기업 응답 |
| ME6 | 2022M | 문1_2_6 | 수요의 변화를 예측하기 어려움 | changes in demand hard to predict | as printed 0-5 | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT6 | 2022M | 문2_6 | 영업비밀 | trade secret protection | as printed: 1 예 / 0 아니오 | 전 기업 응답 |
| ME7 | 2022M | 문1_2_7 | 해외 경쟁사들과의 경쟁이 치열함 | strong competition from abroad | as printed 0-5 | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT7 | 2022M | 문2_7 | 복잡한 설계방식 채택 | complex design | as printed: 1 예 / 0 아니오 | 전 기업 응답 |
| ME8 | 2022M | 문1_2_8 | 가격 인상이 고객의 손실을 초래함 | price increases lead to loss of customers | as printed 0-5 | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT8 | 2022M | 문2_8 | 경쟁사에 앞서 시장 선점 | lead-time advantage: entering the market ahead of competitors | as printed: 1 예 / 0 아니오 | 전 기업 응답 |
| PI1 | 2022M | 문5_1 | (제품혁신) 귀사의 기존 제품 대비 새롭거나 획기적으로 개선된 제품 | product (goods) innovation introduced | as printed: 1 예 / 0 아니오 | 전 기업 응답. 하나라도 '예'이면 상품혁신 수행 → 문6으로; 모두 '아니오'이면 문9로 이동 |
| MF1 | 2022M | 문6_1 | (시장최초 상품혁신) 경쟁사보다 앞서 기존에 없던 새롭거나 획기적으로 개선된 상품을 출시 | new-to-market product innovation (ahead of competitors) | as printed: 1 예 / 0 아니오 | 문5에서 하나라도 '예'인 기업만 (상품혁신 기업) |
| PI2 | 2022M | 문5_2 | (서비스혁신) 귀사의 기존 서비스 대비 새롭거나 획기적으로 개선된 서비스 | service innovation introduced | as printed: 1 예 / 0 아니오 | 전 기업 응답. 하나라도 '예'이면 상품혁신 수행 → 문6으로; 모두 '아니오'이면 문9로 이동 |
| MF2 | 2022M | 문6_2 | (자사최초 상품혁신) 경쟁사에서 이미 동일/유사한 상품을 출시하여 존재하나, 귀사의 기존 상품 대비 새롭거나 획기적으로 개선된 상품을 출시 | new-to-firm product innovation | as printed: 1 예 / 0 아니오 | 문5에서 하나라도 '예'인 기업만 (상품혁신 기업) |
| SHARE1 | 2022M | 문7_1 | 지난 3년간(2019~2021년) 시장최초 상품혁신을 통해 출시한 상품 | sales share of new-to-market products (%) | numeric entry (as reported) | 문5에서 하나라도 '예'인 기업만 |
| SHARE2 | 2022M | 문7_2 | 지난 3년간(2019~2021년) 자사최초 상품혁신을 통해 출시한 상품 | sales share of new-to-firm products (%) | numeric entry (as reported) | 문5에서 하나라도 '예'인 기업만 |
| SHARE3 | 2022M | 문7_3 | 상품혁신에 해당하지 않는 그 외 상품* (귀사의 기존 상품 포함) | sales share of unchanged products (%) | numeric entry (as reported) | 문5에서 하나라도 '예'인 기업만 |
| IA1 | 2022M | 문11_1 | 지난 3년간(2019~2021년) 기간 내 완료된 혁신활동 (상품혁신활동 또는 비즈니스프로세스혁신활동) | innovation activity completed within the period | as printed: 1 예 / 0 아니오 | 전 기업 응답. ①~⑥ 모두 '아니오'이면 문17로 이동(문12~16 비응답). 각주 2: 문5 또는 문9에서 하나라도 '예'이면 ①에 반드시 '예' |
| IA2 | 2022M | 문11_2 | 2021년 말 기준, 계속 진행 중이었던 혁신활동 | innovation activity ongoing at year-end | as printed: 1 예 / 0 아니오 | 전 기업 응답. ①~⑥ 모두 '아니오'이면 문17로 이동(문12~16 비응답). 각주 2: 문5 또는 문9에서 하나라도 '예'이면 ①에 반드시 '예' |
| IA3 | 2022M | 문11_3 | 중도포기 또는 중단된 혁신활동 | innovation activity abandoned or suspended | as printed: 1 예 / 0 아니오 | 전 기업 응답. ①~⑥ 모두 '아니오'이면 문17로 이동(문12~16 비응답). 각주 2: 문5 또는 문9에서 하나라도 '예'이면 ①에 반드시 '예' |
| IA4 | 2022M | 문11_4 | 귀사 내부에서 전체를 독자적으로 자체수행한 연구개발(R&D) 활동 | in-house R&D | as printed: 1 예 / 0 아니오 | 전 기업 응답. ①~⑥ 모두 '아니오'이면 문17로 이동(문12~16 비응답). 각주 2: 문5 또는 문9에서 하나라도 '예'이면 ①에 반드시 '예' |
| IA5 | 2022M | 문11_5 | 귀사와 타 기업 또는 타 기관이 계약을 통해 공동으로 협력하여 수행한 연구개발(R&D) 활동 | collaborative R&D | as printed: 1 예 / 0 아니오 | 전 기업 응답. ①~⑥ 모두 '아니오'이면 문17로 이동(문12~16 비응답). 각주 2: 문5 또는 문9에서 하나라도 '예'이면 ①에 반드시 '예' |
| IA6 | 2022M | 문11_6 | 외주계약을 통해 타 기업 또는 타 기관에게 용역 전체를 의뢰하여 수행된 연구개발(R&D) 활동 | contracted-out R&D | as printed: 1 예 / 0 아니오 | 전 기업 응답. ①~⑥ 모두 '아니오'이면 문17로 이동(문12~16 비응답). 각주 2: 문5 또는 문9에서 하나라도 '예'이면 ①에 반드시 '예' |
| RDCYCLE | 2022M | 문11_4_01 | 연구개발 활동 주기 | in-house R&D: continuous (1) vs occasional (2) | as printed 1/2 | 문11 ④(독자 수행 R&D) '예'인 기업만 |
| RDEXP | 2022M | 문12_1_1 | R&D 활동 비용 | R&D expenditure in the reference year (million KRW) | numeric entry (as reported) | 문11 ①~⑥ 중 하나라도 '예'인 기업만 (혁신활동 기업) |
| NONRDEXP | 2022M | 문12_1_2 | R&D 이외의 혁신활동 비용 | non-R&D innovation expenditure (million KRW) | numeric entry (as reported) | 문11 ①~⑥ 중 하나라도 '예'인 기업만 (혁신활동 기업) |
| COOP1 | 2022M | 문14_1 | R&D 활동에 대해 협력한 적이 있음 | cooperated on R&D | as printed: 1 예 / 0 아니오 | 문11 ①~⑥ 중 하나라도 '예'인 기업만 |
| COOP2 | 2022M | 문14_2 | R&D 이외의 혁신활동으로 협력한 적이 있음 | cooperated on non-R&D innovation | as printed: 1 예 / 0 아니오 | 문11 ①~⑥ 중 하나라도 '예'인 기업만 |
| COOP3 | 2022M | 문14_3 | 혁신활동 이외의 일반 활동으로 협력한 적이 있음 | cooperated on general (non-innovation) activities | as printed: 1 예 / 0 아니오 | 문11 ①~⑥ 중 하나라도 '예'인 기업만 |
| FUND1 | 2022M | 문17_1 | 기업 자체자금 | own funds | as printed 0-3 | 전 기업 응답 |
| FUND2 | 2022M | 문17_2 | 계열사나 제휴회사 자금 | group/affiliate funds | as printed 0-3 | 전 기업 응답 |
| FUND3 | 2022M | 문17_3 | 은행 등으로부터 투·융자 | bank loans/investment | as printed 0-3 | 전 기업 응답 |
| FUND4 | 2022M | 문17_4 | 주식 발행 | equity issue | as printed 0-3 | 전 기업 응답 |
| FUND5 | 2022M | 문17_5 | 회사채 발행 | bond issue | as printed 0-3 | 전 기업 응답 |
| FUND6 | 2022M | 문17_6 | 투자전문 개인/기관의 투자금 | angel/VC/accelerator investment | as printed 0-3 | 전 기업 응답 |
| FUND7 | 2022M | 문17_7 | 중앙정부 지원 자금 | central-government funds | as printed 0-3 | 전 기업 응답 |
| FUND8 | 2022M | 문17_8 | 지자체 지원 자금 | local-government funds | as printed 0-3 | 전 기업 응답 |
| HAMP12 | 2022M | 문19_12 | 혁신 상품/아이디어에 대한 시장수요 불확실 | hampering factor: uncertain market demand for innovations | as printed 0-5 | 전 기업 응답 |
| HAMP13 | 2022M | 문19_13 | 과도한 시장 경쟁으로 혁신활동 수행 여력 부족 | hampering factor: excessive market competition leaves no capacity to innovate | as printed 0-5 | 전 기업 응답 |
| HAMP16 | 2022M | 문19_16 | 시장의 경쟁 압력이 낮아 혁신 불필요 | reason not to innovate: weak competitive pressure | as printed 0-5 | 전 기업 응답 |
| FORM | 2022M | 문31_1 | 기업 형태 | firm type: independent / domestic-group affiliate / foreign-group affiliate | as printed 1/2/3 | 전 기업 응답 |
| LEGALSIZE | 2022M | 문31_2 | 법정기업규모 | statutory firm size: small / medium / mid-sized / large | as printed 1-4 | 전 기업 응답 |
| CERT1 | 2022M | 문31_3_1 | 벤처기업 | certified venture firm | tick column: value 1 when ticked, blank otherwise | 전 기업 응답 |
| CERT2 | 2022M | 문31_3_2 | 부설연구소/연구개발 전담 부서 | has a registered R&D institute or dedicated R&D department | tick column: value 2 when ticked, blank otherwise | 전 기업 응답 |
| CERT3 | 2022M | 문31_3_3 | 이노비즈 | Inno-Biz certification | tick column: value 3 when ticked, blank otherwise | 전 기업 응답 |
| CERT4 | 2022M | 문31_3_4 | 메인비즈 | Main-Biz certification | tick column: value 4 when ticked, blank otherwise | 전 기업 응답 |
| CERT5 | 2022M | 문31_3_5 | 그린비즈 | Green-Biz certification | tick column: value 5 when ticked, blank otherwise | 전 기업 응답 |
| CERT6 | 2022M | 문31_3_6 | 부품소재전문기업 | parts & materials specialist firm | tick column: value 6 when ticked, blank otherwise | 전 기업 응답 |
| CERT7 | 2022M | 문31_3_7 | ISO | ISO certification | tick column: value 7 when ticked, blank otherwise | 전 기업 응답 |
| CERT8 | 2022M | 문31_3_8 | 여성기업 | women-owned firm | tick column: value 8 when ticked, blank otherwise | 전 기업 응답 |
| CERT9 | 2022M | 문31_3_9 | 해당사항 없음 | no certification | tick column: value 9 when ticked, blank otherwise | 전 기업 응답 |
| LISTED | 2022M | 문31_4 | 상장여부 | stock-market listing: KOSPI / KOSDAQ / KONEX / not listed | as printed 1-4 | 전 기업 응답 |
| SALES | 2022M | 문32_3_1 | 매출액 2021년 | sales in the reference year (million KRW) | numeric entry (as reported) | 전 기업 응답 |
| EXPORTS | 2022M | 문32_3_2 | 수출액 2021년 | exports in the reference year (million KRW) | numeric entry (as reported) | 전 기업 응답 |
| EMP | 2022M | 문33_1_3 | 2021년 상용 근로자 수 | regular employees in the reference year | numeric entry (as reported) | 전 기업 응답 |
| FEMALE | 2022M | 문33_2_1 | 상용 근로자 중 여성인력 비율(%) | share of women among regular employees (%) | numeric entry (as reported) | 전 기업 응답 |
| MASTERS | 2022M | 문33_3_1 | 상용 근로자 중 석사학위 이상 비율(%) | share with a master's degree or higher (%) | numeric entry (as reported) | 전 기업 응답 |
| RDSTAFF | 2022M | 문33_4_1 | 상용 근로자 중 연구개발(R&D) 전담인력 비율(%) | share of dedicated R&D staff among regular employees (%) | numeric entry (as reported) | 전 기업 응답 |
| ME1 | 2024M | Q1K2_1 | 상품(제품 또는 서비스)이 빠르게 구식이 되어버림 | products become outdated quickly | as printed 0-5 | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT1 | 2024M | Q2_1 | 특허권 출원 | patent application | as printed: 1 예 / 0 아니오 | 전 기업 응답 |
| ME2 | 2024M | Q1K2_2 | 미래 기술 발전을 예측하기 어려움 | future technological developments hard to predict | as printed 0-5 | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT2 | 2024M | Q2_2 | 실용신안권 등록 | utility model registration | as printed: 1 예 / 0 아니오 | 전 기업 응답 |
| ME3 | 2024M | Q1K2_3 | 경쟁사 상품들이 귀사의 상품들을 쉽게 대체함 | competitor products easily substitute ours | as printed 0-5 | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT3 | 2024M | Q2_3 | 디자인권 등록 | design right registration | as printed: 1 예 / 0 아니오 | 전 기업 응답 |
| ME4 | 2024M | Q1K2_4 | 새로운 경쟁사의 진입이 귀사의 시장 지위를 위협함 | entry of new competitors threatens market position | as printed 0-5 | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT4 | 2024M | Q2_4 | 상표권(트레이드마크) 등록 | trademark registration | as printed: 1 예 / 0 아니오 | 전 기업 응답 |
| ME5 | 2024M | Q1K2_5 | 경쟁사의 행동을 예측하기 어려움 | competitors' actions hard to predict | as printed 0-5 | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT5 | 2024M | Q2_5 | 저작권(카피라이트) 청구 | copyright claim | as printed: 1 예 / 0 아니오 | 전 기업 응답 |
| ME6 | 2024M | Q1K2_6 | 수요의 변화를 예측하기 어려움 | changes in demand hard to predict | as printed 0-5 | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT6 | 2024M | Q2_6 | 영업비밀 | trade secret protection | as printed: 1 예 / 0 아니오 | 전 기업 응답 |
| ME7 | 2024M | Q1K2_7 | 해외 경쟁사들과의 경쟁이 치열함 | strong competition from abroad | as printed 0-5 | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT7 | 2024M | Q2_7 | 복잡한 설계방식 채택 | complex design | as printed: 1 예 / 0 아니오 | 전 기업 응답 |
| ME8 | 2024M | Q1K2_8 | 가격 인상이 고객의 손실을 초래함 | price increases lead to loss of customers | as printed 0-5 | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT8 | 2024M | Q2_8 | 경쟁사에 앞서 시장 선점 | lead-time advantage: entering the market ahead of competitors | as printed: 1 예 / 0 아니오 | 전 기업 응답 |
| PI1 | 2024M | Q5_1 | (제품혁신) 귀사의 기존 제품 대비 새롭거나 획기적으로 개선된 제품 | product (goods) innovation introduced | as printed: 1 예 / 0 아니오 | 전 기업 응답. 하나라도 '예'이면 상품혁신 수행 → 문6으로; 모두 '아니오'이면 문9로 이동 |
| MF1 | 2024M | Q6_1 | (시장최초 상품혁신) 경쟁사보다 앞서 기존에 없던 새롭거나 획기적으로 개선된 상품을 출시 | new-to-market product innovation (ahead of competitors) | as printed: 1 예 / 0 아니오 | 문5에서 하나라도 '예'인 기업만 (상품혁신 기업) |
| PI2 | 2024M | Q5_2 | (서비스혁신) 귀사의 기존 서비스 대비 새롭거나 획기적으로 개선된 서비스 | service innovation introduced | as printed: 1 예 / 0 아니오 | 전 기업 응답. 하나라도 '예'이면 상품혁신 수행 → 문6으로; 모두 '아니오'이면 문9로 이동 |
| MF2 | 2024M | Q6_2 | (자사최초 상품혁신) 경쟁사에서 이미 동일/유사한 상품을 출시하여 존재하나, 귀사의 기존 상품 대비 새롭거나 획기적으로 개선된 상품을 출시 | new-to-firm product innovation | as printed: 1 예 / 0 아니오 | 문5에서 하나라도 '예'인 기업만 (상품혁신 기업) |
| SHARE1 | 2024M | Q7_1 | 지난 3년간(2021~2023년) 시장최초 상품혁신을 통해 출시한 상품 | sales share of new-to-market products (%) | numeric entry (as reported) | 문5에서 하나라도 '예'인 기업만 |
| SHARE2 | 2024M | Q7_2 | 지난 3년간(2021~2023년) 자사최초 상품혁신을 통해 출시한 상품 | sales share of new-to-firm products (%) | numeric entry (as reported) | 문5에서 하나라도 '예'인 기업만 |
| SHARE3 | 2024M | Q7_3 | 상품혁신에 해당하지 않는 그 외 상품* (귀사의 기존 상품 포함) | sales share of unchanged products (%) | numeric entry (as reported) | 문5에서 하나라도 '예'인 기업만 |
| IA1 | 2024M | Q11_1 | 지난 3년간(2021~2023년) 기간 내 완료된 혁신활동 (상품혁신활동 또는 비즈니스프로세스혁신활동) | innovation activity completed within the period | as printed: 1 예 / 0 아니오 | 전 기업 응답. ①~⑥ 모두 '아니오'이면 문17로 이동(문12~16 비응답). 각주 2: 문5 또는 문9에서 하나라도 '예'이면 ①에 반드시 '예' |
| IA2 | 2024M | Q11_2 | 2023년 말 기준, 계속 진행 중이었던 혁신활동 | innovation activity ongoing at year-end | as printed: 1 예 / 0 아니오 | 전 기업 응답. ①~⑥ 모두 '아니오'이면 문17로 이동(문12~16 비응답). 각주 2: 문5 또는 문9에서 하나라도 '예'이면 ①에 반드시 '예' |
| IA3 | 2024M | Q11_3 | 중도포기 또는 중단된 혁신활동 | innovation activity abandoned or suspended | as printed: 1 예 / 0 아니오 | 전 기업 응답. ①~⑥ 모두 '아니오'이면 문17로 이동(문12~16 비응답). 각주 2: 문5 또는 문9에서 하나라도 '예'이면 ①에 반드시 '예' |
| IA4 | 2024M | Q11_4 | 귀사 내부에서 전체를 독자적으로 자체수행한 연구개발(R&D) 활동 | in-house R&D | as printed: 1 예 / 0 아니오 | 전 기업 응답. ①~⑥ 모두 '아니오'이면 문17로 이동(문12~16 비응답). 각주 2: 문5 또는 문9에서 하나라도 '예'이면 ①에 반드시 '예' |
| IA5 | 2024M | Q11_5 | 귀사와 타 기업 또는 타 기관이 계약을 통해 공동으로 협력하여 수행한 연구개발(R&D) 활동 | collaborative R&D | as printed: 1 예 / 0 아니오 | 전 기업 응답. ①~⑥ 모두 '아니오'이면 문17로 이동(문12~16 비응답). 각주 2: 문5 또는 문9에서 하나라도 '예'이면 ①에 반드시 '예' |
| IA6 | 2024M | Q11_6 | 외주계약을 통해 타 기업 또는 타 기관에게 용역 전체를 의뢰하여 수행된 연구개발(R&D) 활동 | contracted-out R&D | as printed: 1 예 / 0 아니오 | 전 기업 응답. ①~⑥ 모두 '아니오'이면 문17로 이동(문12~16 비응답). 각주 2: 문5 또는 문9에서 하나라도 '예'이면 ①에 반드시 '예' |
| RDCYCLE | 2024M | Q11K4K1 | 연구개발 활동 주기 | in-house R&D: continuous (1) vs occasional (2) | as printed 1/2 | 문11 ④(독자 수행 R&D) '예'인 기업만 |
| RDEXP | 2024M | Q12K1_1 | R&D 활동 비용 | R&D expenditure in the reference year (million KRW) | numeric entry (as reported) | 문11 ①~⑥ 중 하나라도 '예'인 기업만 (혁신활동 기업) |
| NONRDEXP | 2024M | Q12K1_2 | R&D 이외의 혁신활동 비용 | non-R&D innovation expenditure (million KRW) | numeric entry (as reported) | 문11 ①~⑥ 중 하나라도 '예'인 기업만 (혁신활동 기업) |
| COOP1 | 2024M | Q14_1 | R&D 활동에 대해 협력한 적이 있음 | cooperated on R&D | as printed: 1 예 / 0 아니오 | 문11 ①~⑥ 중 하나라도 '예'인 기업만 |
| COOP2 | 2024M | Q14_2 | R&D 이외의 혁신활동으로 협력한 적이 있음 | cooperated on non-R&D innovation | as printed: 1 예 / 0 아니오 | 문11 ①~⑥ 중 하나라도 '예'인 기업만 |
| COOP3 | 2024M | Q14_3 | 혁신활동 이외의 일반 활동으로 협력한 적이 있음 | cooperated on general (non-innovation) activities | as printed: 1 예 / 0 아니오 | 문11 ①~⑥ 중 하나라도 '예'인 기업만 |
| FUND1 | 2024M | Q17_1 | 기업 자체자금 | own funds | as printed 0-3 | 전 기업 응답 |
| FUND2 | 2024M | Q17_2 | 계열사나 제휴회사 자금 | group/affiliate funds | as printed 0-3 | 전 기업 응답 |
| FUND3 | 2024M | Q17_3 | 은행 등으로부터 투·융자 | bank loans/investment | as printed 0-3 | 전 기업 응답 |
| FUND4 | 2024M | Q17_4 | 주식 발행 | equity issue | as printed 0-3 | 전 기업 응답 |
| FUND5 | 2024M | Q17_5 | 회사채 발행 | bond issue | as printed 0-3 | 전 기업 응답 |
| FUND6 | 2024M | Q17_6 | 투자전문 개인/기관의 투자금 | angel/VC/accelerator investment | as printed 0-3 | 전 기업 응답 |
| FUND7 | 2024M | Q17_7 | 중앙정부 지원 자금 | central-government funds | as printed 0-3 | 전 기업 응답 |
| FUND8 | 2024M | Q17_8 | 지자체 지원 자금 | local-government funds | as printed 0-3 | 전 기업 응답 |
| HAMP12 | 2024M | Q19_12 | 혁신 상품/아이디어에 대한 시장수요 불확실 | hampering factor: uncertain market demand for innovations | as printed 0-5 | 전 기업 응답 |
| HAMP13 | 2024M | Q19_13 | 과도한 시장 경쟁으로 혁신활동 수행 여력 부족 | hampering factor: excessive market competition leaves no capacity to innovate | as printed 0-5 | 전 기업 응답 |
| HAMP16 | 2024M | Q19_16 | 시장의 경쟁 압력이 낮아 혁신 불필요 | reason not to innovate: weak competitive pressure | as printed 0-5 | 전 기업 응답 |
| FORM | 2024M | Q31K1 | 기업 형태 | firm type: independent / domestic-group affiliate / foreign-group affiliate | as printed 1/2/3 | 전 기업 응답 |
| LEGALSIZE | 2024M | Q31K2 | 법정기업규모 | statutory firm size: small / medium / mid-sized / large | as printed 1-4 | 전 기업 응답 |
| CERT1 | 2024M | Q31K3_1 | 벤처기업 | certified venture firm | tick column: value 1 when ticked, blank otherwise | 전 기업 응답 |
| CERT2 | 2024M | Q31K3_2 | 부설연구소/연구개발 전담 부서 | has a registered R&D institute or dedicated R&D department | tick column: value 2 when ticked, blank otherwise | 전 기업 응답 |
| CERT3 | 2024M | Q31K3_3 | 이노비즈 | Inno-Biz certification | tick column: value 3 when ticked, blank otherwise | 전 기업 응답 |
| CERT4 | 2024M | Q31K3_4 | 메인비즈 | Main-Biz certification | tick column: value 4 when ticked, blank otherwise | 전 기업 응답 |
| CERT5 | 2024M | Q31K3_5 | 그린비즈 | Green-Biz certification | tick column: value 5 when ticked, blank otherwise | 전 기업 응답 |
| CERT6 | 2024M | Q31K3_6 | 부품소재전문기업 | parts & materials specialist firm | tick column: value 6 when ticked, blank otherwise | 전 기업 응답 |
| CERT7 | 2024M | Q31K3_7 | ISO | ISO certification | tick column: value 7 when ticked, blank otherwise | 전 기업 응답 |
| CERT8 | 2024M | Q31K3_8 | 여성기업 | women-owned firm | tick column: value 8 when ticked, blank otherwise | 전 기업 응답 |
| CERT9 | 2024M | Q31K3_9998 | 해당사항 없음 | no certification | tick column: value 9 when ticked, blank otherwise | 전 기업 응답 |
| LISTED | 2024M | Q31K4 | 상장여부 | stock-market listing: KOSPI / KOSDAQ / KONEX / not listed | as printed 1-4 | 전 기업 응답 |
| SALES | 2024M | Q32_3_1 | 매출액 2023년 | sales in the reference year (million KRW) | numeric entry (as reported) | 전 기업 응답 |
| EXPORTS | 2024M | Q32_3_2 | 수출액 2023년 | exports in the reference year (million KRW) | numeric entry (as reported) | 전 기업 응답 |
| EMP | 2024M | Q33K1_3 | 2023년 상용 근로자 수 | regular employees in the reference year | numeric entry (as reported) | 전 기업 응답 |
| FEMALE | 2024M | Q33K2_1_1 | 상용 근로자 중 여성인력 비율(%) | share of women among regular employees (%) | numeric entry (as reported) | 전 기업 응답 |
| MASTERS | 2024M | Q33K2_1_2 | 상용 근로자 중 석사학위 이상 비율(%) | share with a master's degree or higher (%) | numeric entry (as reported) | 전 기업 응답 |
| RDSTAFF | 2024M | Q33K2_1_3 | 상용 근로자 중 연구개발(R&D) 전담인력 비율(%) | share of dedicated R&D staff among regular employees (%) | numeric entry (as reported) | 전 기업 응답 |
| ME1 | 2023S | 문1_2_1 | 상품(제품 또는 서비스)이 빠르게 구식이 되어버림 | products become outdated quickly | data 1-6 = printed 0-5 (+1 shift) | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT1 | 2023S | 문2_1 | 특허권 출원 | patent application | data 1 예 / 2 아니오 (questionnaire prints 1/0) | 전 기업 응답 |
| ME2 | 2023S | 문1_2_2 | 미래 기술 발전을 예측하기 어려움 | future technological developments hard to predict | data 1-6 = printed 0-5 (+1 shift) | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT2 | 2023S | 문2_2 | 실용신안권 등록 | utility model registration | data 1 예 / 2 아니오 (questionnaire prints 1/0) | 전 기업 응답 |
| ME3 | 2023S | 문1_2_3 | 경쟁사 상품들이 귀사의 상품들을 쉽게 대체함 | competitor products easily substitute ours | data 1-6 = printed 0-5 (+1 shift) | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT3 | 2023S | 문2_3 | 디자인권 등록 | design right registration | data 1 예 / 2 아니오 (questionnaire prints 1/0) | 전 기업 응답 |
| ME4 | 2023S | 문1_2_4 | 새로운 경쟁사의 진입이 귀사의 시장 지위를 위협함 | entry of new competitors threatens market position | data 1-6 = printed 0-5 (+1 shift) | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT4 | 2023S | 문2_4 | 상표권(트레이드마크) 등록 | trademark registration | data 1 예 / 2 아니오 (questionnaire prints 1/0) | 전 기업 응답 |
| ME5 | 2023S | 문1_2_5 | 경쟁사의 행동을 예측하기 어려움 | competitors' actions hard to predict | data 1-6 = printed 0-5 (+1 shift) | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT5 | 2023S | 문2_5 | 저작권(카피라이트) 청구 | copyright claim | data 1 예 / 2 아니오 (questionnaire prints 1/0) | 전 기업 응답 |
| ME6 | 2023S | 문1_2_6 | 수요의 변화를 예측하기 어려움 | changes in demand hard to predict | data 1-6 = printed 0-5 (+1 shift) | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT6 | 2023S | 문2_6 | 영업비밀 | trade secret protection | data 1 예 / 2 아니오 (questionnaire prints 1/0) | 전 기업 응답 |
| ME7 | 2023S | 문1_2_7 | 해외 경쟁사들과의 경쟁이 치열함 | strong competition from abroad | data 1-6 = printed 0-5 (+1 shift) | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT7 | 2023S | 문2_7 | 복잡한 설계방식 채택 | complex design | data 1 예 / 2 아니오 (questionnaire prints 1/0) | 전 기업 응답 |
| ME8 | 2023S | 문1_2_8 | 가격 인상이 고객의 손실을 초래함 | price increases lead to loss of customers | data 1-6 = printed 0-5 (+1 shift) | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT8 | 2023S | 문2_8 | 경쟁사에 앞서 시장 선점 | lead-time advantage: entering the market ahead of competitors | data 1 예 / 2 아니오 (questionnaire prints 1/0) | 전 기업 응답 |
| PI1 | 2023S | 문5_1 | (제품혁신) 귀사의 기존 제품 대비 새롭거나 획기적으로 개선된 제품 | product (goods) innovation introduced | data 1 예 / 2 아니오 (questionnaire prints 1/0) | 전 기업 응답. 하나라도 '예'이면 상품혁신 수행 → 문6으로; 모두 '아니오'이면 문9로 이동 |
| MF1 | 2023S | 문6_1 | (시장최초 상품혁신) 경쟁사보다 앞서 기존에 없던 새롭거나 획기적으로 개선된 상품을 출시 | new-to-market product innovation (ahead of competitors) | data 1 예 / 2 아니오 (questionnaire prints 1/0) | 문5에서 하나라도 '예'인 기업만 (상품혁신 기업) |
| PI2 | 2023S | 문5_2 | (서비스혁신) 귀사의 기존 서비스 대비 새롭거나 획기적으로 개선된 서비스 | service innovation introduced | data 1 예 / 2 아니오 (questionnaire prints 1/0) | 전 기업 응답. 하나라도 '예'이면 상품혁신 수행 → 문6으로; 모두 '아니오'이면 문9로 이동 |
| MF2 | 2023S | 문6_2 | (자사최초 상품혁신) 경쟁사에서 이미 동일/유사한 상품을 출시하여 존재하나, 귀사의 기존 상품 대비 새롭거나 획기적으로 개선된 상품을 출시 | new-to-firm product innovation | data 1 예 / 2 아니오 (questionnaire prints 1/0) | 문5에서 하나라도 '예'인 기업만 (상품혁신 기업) |
| SHARE1 | 2023S | 문7_1 | 지난 3년간(2020~2022년) 시장최초 상품혁신을 통해 출시한 상품 | sales share of new-to-market products (%) | numeric entry (as reported) | 문5에서 하나라도 '예'인 기업만 |
| SHARE2 | 2023S | 문7_2 | 지난 3년간(2020~2022년) 자사최초 상품혁신을 통해 출시한 상품 | sales share of new-to-firm products (%) | numeric entry (as reported) | 문5에서 하나라도 '예'인 기업만 |
| SHARE3 | 2023S | 문7_3 | 상품혁신에 해당하지 않는 그 외 상품* (귀사의 기존 상품 포함) | sales share of unchanged products (%) | numeric entry (as reported) | 문5에서 하나라도 '예'인 기업만 |
| IA1 | 2023S | 문11_1 | 지난 3년간(2020~2022년) 기간 내 완료된 혁신활동 (상품혁신활동 또는 비즈니스프로세스혁신활동) | innovation activity completed within the period | data 1 예 / 2 아니오 (questionnaire prints 1/0) | 전 기업 응답. ①~⑥ 모두 '아니오'이면 문17로 이동(문12~16 비응답). 각주 2: 문5 또는 문9에서 하나라도 '예'이면 ①에 반드시 '예' |
| IA2 | 2023S | 문11_2 | 2022년 말 기준, 계속 진행 중이었던 혁신활동 | innovation activity ongoing at year-end | data 1 예 / 2 아니오 (questionnaire prints 1/0) | 전 기업 응답. ①~⑥ 모두 '아니오'이면 문17로 이동(문12~16 비응답). 각주 2: 문5 또는 문9에서 하나라도 '예'이면 ①에 반드시 '예' |
| IA3 | 2023S | 문11_3 | 중도포기 또는 중단된 혁신활동 | innovation activity abandoned or suspended | data 1 예 / 2 아니오 (questionnaire prints 1/0) | 전 기업 응답. ①~⑥ 모두 '아니오'이면 문17로 이동(문12~16 비응답). 각주 2: 문5 또는 문9에서 하나라도 '예'이면 ①에 반드시 '예' |
| IA4 | 2023S | 문11_4 | 귀사 내부에서 전체를 독자적으로 자체수행한 연구개발(R&D) 활동 | in-house R&D | data 1 예 / 2 아니오 (questionnaire prints 1/0) | 전 기업 응답. ①~⑥ 모두 '아니오'이면 문17로 이동(문12~16 비응답). 각주 2: 문5 또는 문9에서 하나라도 '예'이면 ①에 반드시 '예' |
| IA5 | 2023S | 문11_5 | 귀사와 타 기업 또는 타 기관이 계약을 통해 공동으로 협력하여 수행한 연구개발(R&D) 활동 | collaborative R&D | data 1 예 / 2 아니오 (questionnaire prints 1/0) | 전 기업 응답. ①~⑥ 모두 '아니오'이면 문17로 이동(문12~16 비응답). 각주 2: 문5 또는 문9에서 하나라도 '예'이면 ①에 반드시 '예' |
| IA6 | 2023S | 문11_6 | 외주계약을 통해 타 기업 또는 타 기관에게 용역 전체를 의뢰하여 수행된 연구개발(R&D) 활동 | contracted-out R&D | data 1 예 / 2 아니오 (questionnaire prints 1/0) | 전 기업 응답. ①~⑥ 모두 '아니오'이면 문17로 이동(문12~16 비응답). 각주 2: 문5 또는 문9에서 하나라도 '예'이면 ①에 반드시 '예' |
| RDCYCLE | 2023S | 문11_4_01 | 연구개발 활동 주기 | in-house R&D: continuous (1) vs occasional (2) | as printed 1/2 | 문11 ④(독자 수행 R&D) '예'인 기업만 |
| RDEXP | 2023S | 문12_1_1 | R&D 활동 비용 | R&D expenditure in the reference year (million KRW) | numeric entry (as reported) | 문11 ①~⑥ 중 하나라도 '예'인 기업만 (혁신활동 기업) |
| NONRDEXP | 2023S | 문12_1_2 | R&D 이외의 혁신활동 비용 | non-R&D innovation expenditure (million KRW) | numeric entry (as reported) | 문11 ①~⑥ 중 하나라도 '예'인 기업만 (혁신활동 기업) |
| COOP1 | 2023S | 문14_1 | R&D 활동에 대해 협력한 적이 있음 | cooperated on R&D | data 1 예 / 2 아니오 (questionnaire prints 1/0) | 문11 ①~⑥ 중 하나라도 '예'인 기업만 |
| COOP2 | 2023S | 문14_2 | R&D 이외의 혁신활동으로 협력한 적이 있음 | cooperated on non-R&D innovation | data 1 예 / 2 아니오 (questionnaire prints 1/0) | 문11 ①~⑥ 중 하나라도 '예'인 기업만 |
| COOP3 | 2023S | 문14_3 | 혁신활동 이외의 일반 활동으로 협력한 적이 있음 | cooperated on general (non-innovation) activities | data 1 예 / 2 아니오 (questionnaire prints 1/0) | 문11 ①~⑥ 중 하나라도 '예'인 기업만 |
| FUND1 | 2023S | 문17_1 | 기업 자체자금 | own funds | data 1-4 = printed 0-3 (+1 shift) | 전 기업 응답 |
| FUND2 | 2023S | 문17_2 | 계열사나 제휴회사 자금 | group/affiliate funds | data 1-4 = printed 0-3 (+1 shift) | 전 기업 응답 |
| FUND3 | 2023S | 문17_3 | 은행 등으로부터 투·융자 | bank loans/investment | data 1-4 = printed 0-3 (+1 shift) | 전 기업 응답 |
| FUND4 | 2023S | 문17_4 | 주식 발행 | equity issue | data 1-4 = printed 0-3 (+1 shift) | 전 기업 응답 |
| FUND5 | 2023S | 문17_5 | 회사채 발행 | bond issue | as printed 0-3 | 전 기업 응답 |
| FUND6 | 2023S | 문17_6 | 투자전문 개인/기관의 투자금 | angel/VC/accelerator investment | data 1-4 = printed 0-3 (+1 shift) | 전 기업 응답 |
| FUND7 | 2023S | 문17_7 | 중앙정부 지원 자금 | central-government funds | data 1-4 = printed 0-3 (+1 shift) | 전 기업 응답 |
| FUND8 | 2023S | 문17_8 | 지자체 지원 자금 | local-government funds | data 1-4 = printed 0-3 (+1 shift) | 전 기업 응답 |
| HAMP12 | 2023S | 문19_12 | 혁신 상품/아이디어에 대한 시장수요 불확실 | hampering factor: uncertain market demand for innovations | data 1-6 = printed 0-5 (+1 shift) | 전 기업 응답 |
| HAMP13 | 2023S | 문19_13 | 과도한 시장 경쟁으로 혁신활동 수행 여력 부족 | hampering factor: excessive market competition leaves no capacity to innovate | data 1-6 = printed 0-5 (+1 shift) | 전 기업 응답 |
| HAMP16 | 2023S | 문19_16 | 시장의 경쟁 압력이 낮아 혁신 불필요 | reason not to innovate: weak competitive pressure | data 1-6 = printed 0-5 (+1 shift) | 전 기업 응답 |
| FORM | 2023S | 문31_1 | 기업 형태 | firm type: independent / domestic-group affiliate / foreign-group affiliate | as printed 1/2/3 | 전 기업 응답 |
| LEGALSIZE | 2023S | 문31_2 | 법정기업규모 | statutory firm size: small / medium / mid-sized / large | as printed 1-4 | 전 기업 응답 |
| CERT1 | 2023S | 문31_3_1 | 벤처기업 | certified venture firm | tick column: value 1 when ticked, blank otherwise | 전 기업 응답 |
| CERT2 | 2023S | 문31_3_2 | 부설연구소/연구개발 전담 부서 | has a registered R&D institute or dedicated R&D department | tick column: value 2 when ticked, blank otherwise | 전 기업 응답 |
| CERT3 | 2023S | 문31_3_3 | 이노비즈 | Inno-Biz certification | tick column: value 3 when ticked, blank otherwise | 전 기업 응답 |
| CERT4 | 2023S | 문31_3_4 | 메인비즈 | Main-Biz certification | tick column: value 4 when ticked, blank otherwise | 전 기업 응답 |
| CERT5 | 2023S | 문31_3_5 | 그린비즈 | Green-Biz certification | numeric entry (as reported) | 전 기업 응답 |
| CERT6 | 2023S | 문31_3_6 | 부품소재전문기업 | parts & materials specialist firm | numeric entry (as reported) | 전 기업 응답 |
| CERT7 | 2023S | 문31_3_7 | ISO | ISO certification | tick column: value 7 when ticked, blank otherwise | 전 기업 응답 |
| CERT8 | 2023S | 문31_3_8 | 여성기업 | women-owned firm | tick column: value 8 when ticked, blank otherwise | 전 기업 응답 |
| CERT9 | 2023S | 문31_3_9 | 해당사항 없음 | no certification | tick column: data 9998 = '9. 해당사항 없음' | 전 기업 응답 |
| LISTED | 2023S | 문31_4 | 상장여부 | stock-market listing: KOSPI / KOSDAQ / KONEX / not listed | data 9998 = printed 4 '해당사항 없음' | 전 기업 응답 |
| SALES | 2023S | 문32_3_1 | 매출액 2022년 | sales in the reference year (million KRW) | numeric entry (as reported) | 전 기업 응답 |
| EXPORTS | 2023S | 문32_3_2 | 수출액 2022년 | exports in the reference year (million KRW) | numeric entry (as reported) | 전 기업 응답 |
| EMP | 2023S | 문33_1_3 | 2022년 상용 근로자 수 | regular employees in the reference year | numeric entry (as reported) | 전 기업 응답 |
| FEMALE | 2023S | 문33_2_1 | 상용 근로자 중 여성인력 비율(%) | share of women among regular employees (%) | numeric entry (as reported) | 전 기업 응답 |
| MASTERS | 2023S | 문33_3_1 | 상용 근로자 중 석사학위 이상 비율(%) | share with a master's degree or higher (%) | numeric entry (as reported) | 전 기업 응답 |
| RDSTAFF | 2023S | 문33_4_1 | 상용 근로자 중 연구개발(R&D) 전담인력 비율(%) | share of dedicated R&D staff among regular employees (%) | numeric entry (as reported) | 전 기업 응답 |
| ME1 | 2025S | Q1K2_1 | 상품(제품 또는 서비스)이 빠르게 구식이 되어버림 | products become outdated quickly | as printed 0-5 | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT1 | 2025S | Q2_1 | 특허권 출원 | patent application | as printed: 1 예 / 0 아니오 | 전 기업 응답 |
| ME2 | 2025S | Q1K2_2 | 미래 기술 발전을 예측하기 어려움 | future technological developments hard to predict | as printed 0-5 | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT2 | 2025S | Q2_2 | 실용신안권 등록 | utility model registration | as printed: 1 예 / 0 아니오 | 전 기업 응답 |
| ME3 | 2025S | Q1K2_3 | 경쟁사 상품들이 귀사의 상품들을 쉽게 대체함 | competitor products easily substitute ours | as printed 0-5 | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT3 | 2025S | Q2_3 | 디자인권 등록 | design right registration | as printed: 1 예 / 0 아니오 | 전 기업 응답 |
| ME4 | 2025S | Q1K2_4 | 새로운 경쟁사의 진입이 귀사의 시장 지위를 위협함 | entry of new competitors threatens market position | as printed 0-5 | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT4 | 2025S | Q2_4 | 상표권(트레이드마크) 등록 | trademark registration | as printed: 1 예 / 0 아니오 | 전 기업 응답 |
| ME5 | 2025S | Q1K2_5 | 경쟁사의 행동을 예측하기 어려움 | competitors' actions hard to predict | as printed 0-5 | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT5 | 2025S | Q2_5 | 저작권(카피라이트) 청구 | copyright claim | as printed: 1 예 / 0 아니오 | 전 기업 응답 |
| ME6 | 2025S | Q1K2_6 | 수요의 변화를 예측하기 어려움 | changes in demand hard to predict | as printed 0-5 | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT6 | 2025S | Q2_6 | 영업비밀 | trade secret protection | as printed: 1 예 / 0 아니오 | 전 기업 응답 |
| ME7 | 2025S | Q1K2_7 | 해외 경쟁사들과의 경쟁이 치열함 | strong competition from abroad | as printed 0-5 | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT7 | 2025S | Q2_7 | 복잡한 설계방식 채택 | complex design | as printed: 1 예 / 0 아니오 | 전 기업 응답 |
| ME8 | 2025S | Q1K2_8 | 가격 인상이 고객의 손실을 초래함 | price increases lead to loss of customers | as printed 0-5 | 전 기업 응답 (I. 전략과 지식흐름 파트: '혁신'에 국한하지 않은 일반적인 상황) |
| PROT8 | 2025S | Q2_8 | 경쟁사에 앞서 시장 선점 | lead-time advantage: entering the market ahead of competitors | as printed: 1 예 / 0 아니오 | 전 기업 응답 |
| PI1 | 2025S | Q5_1 | (제품혁신) 귀사의 기존 제품 대비 새롭거나 획기적으로 개선된 제품 | product (goods) innovation introduced | as printed: 1 예 / 0 아니오 | 전 기업 응답. 하나라도 '예'이면 상품혁신 수행 → 문6으로; 모두 '아니오'이면 문9로 이동 |
| MF1 | 2025S | Q6_1 | (시장최초 상품혁신) 경쟁사보다 앞서 기존에 없던 새롭거나 획기적으로 개선된 상품을 출시 | new-to-market product innovation (ahead of competitors) | as printed: 1 예 / 0 아니오 | 문5에서 하나라도 '예'인 기업만 (상품혁신 기업) |
| PI2 | 2025S | Q5_2 | (서비스혁신) 귀사의 기존 서비스 대비 새롭거나 획기적으로 개선된 서비스 | service innovation introduced | as printed: 1 예 / 0 아니오 | 전 기업 응답. 하나라도 '예'이면 상품혁신 수행 → 문6으로; 모두 '아니오'이면 문9로 이동 |
| MF2 | 2025S | Q6_2 | (자사최초 상품혁신) 경쟁사에서 이미 동일/유사한 상품을 출시하여 존재하나, 귀사의 기존 상품 대비 새롭거나 획기적으로 개선된 상품을 출시 | new-to-firm product innovation | as printed: 1 예 / 0 아니오 | 문5에서 하나라도 '예'인 기업만 (상품혁신 기업) |
| SHARE1 | 2025S | Q7_1 | 지난 3년간(2022~2024년) 시장최초 상품혁신을 통해 출시한 상품 | sales share of new-to-market products (%) | numeric entry (as reported) | 문5에서 하나라도 '예'인 기업만 |
| SHARE2 | 2025S | Q7_2 | 지난 3년간(2022~2024년) 자사최초 상품혁신을 통해 출시한 상품 | sales share of new-to-firm products (%) | numeric entry (as reported) | 문5에서 하나라도 '예'인 기업만 |
| SHARE3 | 2025S | Q7_3 | 상품혁신에 해당하지 않는 그 외 상품* (귀사의 기존 상품 포함) | sales share of unchanged products (%) | numeric entry (as reported) | 문5에서 하나라도 '예'인 기업만 |
| IA1 | 2025S | Q11_1 | 지난 3년간(2022~2024년) 기간 내 완료된 혁신활동 (상품혁신활동 또는 비즈니스프로세스혁신활동) | innovation activity completed within the period | as printed: 1 예 / 0 아니오 | 전 기업 응답. ①~⑥ 모두 '아니오'이면 문17로 이동(문12~16 비응답). 각주 2: 문5 또는 문9에서 하나라도 '예'이면 ①에 반드시 '예' |
| IA2 | 2025S | Q11_2 | 2024년 말 기준, 계속 진행 중이었던 혁신활동 | innovation activity ongoing at year-end | as printed: 1 예 / 0 아니오 | 전 기업 응답. ①~⑥ 모두 '아니오'이면 문17로 이동(문12~16 비응답). 각주 2: 문5 또는 문9에서 하나라도 '예'이면 ①에 반드시 '예' |
| IA3 | 2025S | Q11_3 | 중도포기 또는 중단된 혁신활동 | innovation activity abandoned or suspended | as printed: 1 예 / 0 아니오 | 전 기업 응답. ①~⑥ 모두 '아니오'이면 문17로 이동(문12~16 비응답). 각주 2: 문5 또는 문9에서 하나라도 '예'이면 ①에 반드시 '예' |
| IA4 | 2025S | Q11_4 | 귀사 내부에서 전체를 독자적으로 자체수행한 연구개발(R&D) 활동 | in-house R&D | as printed: 1 예 / 0 아니오 | 전 기업 응답. ①~⑥ 모두 '아니오'이면 문17로 이동(문12~16 비응답). 각주 2: 문5 또는 문9에서 하나라도 '예'이면 ①에 반드시 '예' |
| IA5 | 2025S | Q11_5 | 귀사와 타 기업 또는 타 기관이 계약을 통해 공동으로 협력하여 수행한 연구개발(R&D) 활동 | collaborative R&D | as printed: 1 예 / 0 아니오 | 전 기업 응답. ①~⑥ 모두 '아니오'이면 문17로 이동(문12~16 비응답). 각주 2: 문5 또는 문9에서 하나라도 '예'이면 ①에 반드시 '예' |
| IA6 | 2025S | Q11_6 | 외주계약을 통해 타 기업 또는 타 기관에게 용역 전체를 의뢰하여 수행된 연구개발(R&D) 활동 | contracted-out R&D | as printed: 1 예 / 0 아니오 | 전 기업 응답. ①~⑥ 모두 '아니오'이면 문17로 이동(문12~16 비응답). 각주 2: 문5 또는 문9에서 하나라도 '예'이면 ①에 반드시 '예' |
| RDCYCLE | 2025S | Q11K4K1 | 연구개발 활동 주기 | in-house R&D: continuous (1) vs occasional (2) | as printed 1/2 | 문11 ④(독자 수행 R&D) '예'인 기업만 |
| RDEXP | 2025S | Q12K1_1 | R&D 활동 비용 | R&D expenditure in the reference year (million KRW) | numeric entry (as reported) | 문11 ①~⑥ 중 하나라도 '예'인 기업만 (혁신활동 기업) |
| NONRDEXP | 2025S | Q12K1_2 | R&D 이외의 혁신활동 비용 | non-R&D innovation expenditure (million KRW) | numeric entry (as reported) | 문11 ①~⑥ 중 하나라도 '예'인 기업만 (혁신활동 기업) |
| COOP1 | 2025S | Q14_1 | R&D 활동에 대해 협력한 적이 있음 | cooperated on R&D | as printed: 1 예 / 0 아니오 | 문11 ①~⑥ 중 하나라도 '예'인 기업만 |
| COOP2 | 2025S | Q14_2 | R&D 이외의 혁신활동으로 협력한 적이 있음 | cooperated on non-R&D innovation | as printed: 1 예 / 0 아니오 | 문11 ①~⑥ 중 하나라도 '예'인 기업만 |
| COOP3 | 2025S | Q14_3 | 혁신활동 이외의 일반 활동으로 협력한 적이 있음 | cooperated on general (non-innovation) activities | as printed: 1 예 / 0 아니오 | 문11 ①~⑥ 중 하나라도 '예'인 기업만 |
| FUND1 | 2025S | Q17_1 | 기업 자체자금 | own funds | as printed 0-3 | 전 기업 응답 |
| FUND2 | 2025S | Q17_2 | 계열사나 제휴회사 자금 | group/affiliate funds | as printed 0-3 | 전 기업 응답 |
| FUND3 | 2025S | Q17_3 | 은행 등으로부터 투·융자 | bank loans/investment | as printed 0-3 | 전 기업 응답 |
| FUND4 | 2025S | Q17_4 | 주식 발행 | equity issue | as printed 0-3 | 전 기업 응답 |
| FUND5 | 2025S | Q17_5 | 회사채 발행 | bond issue | as printed 0-3 | 전 기업 응답 |
| FUND6 | 2025S | Q17_6 | 투자전문 개인/기관의 투자금 | angel/VC/accelerator investment | as printed 0-3 | 전 기업 응답 |
| FUND7 | 2025S | Q17_7 | 중앙정부 지원 자금 | central-government funds | as printed 0-3 | 전 기업 응답 |
| FUND8 | 2025S | Q17_8 | 지자체 지원 자금 | local-government funds | as printed 0-3 | 전 기업 응답 |
| HAMP12 | 2025S | Q19_12 | 혁신 상품/아이디어에 대한 시장수요 불확실 | hampering factor: uncertain market demand for innovations | as printed 0-5 | 전 기업 응답 |
| HAMP13 | 2025S | Q19_13 | 과도한 시장 경쟁으로 혁신활동 수행 여력 부족 | hampering factor: excessive market competition leaves no capacity to innovate | as printed 0-5 | 전 기업 응답 |
| HAMP16 | 2025S | Q19_16 | 시장의 경쟁 압력이 낮아 혁신 불필요 | reason not to innovate: weak competitive pressure | as printed 0-5 | 전 기업 응답 |
| FORM | 2025S | Q31K1 | 기업 형태 | firm type: independent / domestic-group affiliate / foreign-group affiliate | as printed 1/2/3 | 전 기업 응답 |
| LEGALSIZE | 2025S | Q31K2 | 법정기업규모 | statutory firm size: small / medium / mid-sized / large | as printed 1-4 | 전 기업 응답 |
| CERT1 | 2025S | Q31K3_1 | 벤처기업 | certified venture firm | tick column: value 1 when ticked, blank otherwise | 전 기업 응답 |
| CERT2 | 2025S | Q31K3_2 | 부설연구소/연구개발 전담 부서 | has a registered R&D institute or dedicated R&D department | tick column: value 2 when ticked, blank otherwise | 전 기업 응답 |
| CERT3 | 2025S | Q31K3_3 | 이노비즈 | Inno-Biz certification | tick column: value 3 when ticked, blank otherwise | 전 기업 응답 |
| CERT4 | 2025S | Q31K3_4 | 메인비즈 | Main-Biz certification | tick column: value 4 when ticked, blank otherwise | 전 기업 응답 |
| CERT5 | 2025S | Q31K3_5 | 그린비즈 | Green-Biz certification | tick column: value 5 when ticked, blank otherwise | 전 기업 응답 |
| CERT6 | 2025S | Q31K3_6 | 부품소재전문기업 | parts & materials specialist firm | tick column: value 6 when ticked, blank otherwise | 전 기업 응답 |
| CERT7 | 2025S | Q31K3_7 | ISO | ISO certification | tick column: value 7 when ticked, blank otherwise | 전 기업 응답 |
| CERT8 | 2025S | Q31K3_8 | 여성기업 | women-owned firm | tick column: value 8 when ticked, blank otherwise | 전 기업 응답 |
| CERT9 | 2025S | Q31K3_9998 | 해당사항 없음 | no certification | tick column: value 9 when ticked, blank otherwise | 전 기업 응답 |
| LISTED | 2025S | Q31K4 | 상장여부 | stock-market listing: KOSPI / KOSDAQ / KONEX / not listed | as printed 1-4 | 전 기업 응답 |
| SALES | 2025S | Q32_3_1 | 매출액 2024년 | sales in the reference year (million KRW) | numeric entry (as reported) | 전 기업 응답 |
| EXPORTS | 2025S | Q32_3_2 | 수출액 2024년 | exports in the reference year (million KRW) | numeric entry (as reported) | 전 기업 응답 |
| EMP | 2025S | Q33K1_3 | 2024년 상용 근로자 수 | regular employees in the reference year | numeric entry (as reported) | 전 기업 응답 |
| FEMALE | 2025S | Q33K2_1_1 | 상용 근로자 중 여성인력 비율(%) | share of women among regular employees (%) | numeric entry (as reported) | 전 기업 응답 |
| MASTERS | 2025S | Q33K2_1_2 | 상용 근로자 중 석사학위 이상 비율(%) | share with a master's degree or higher (%) | numeric entry (as reported) | 전 기업 응답 |
| RDSTAFF | 2025S | Q33K2_1_3 | 상용 근로자 중 연구개발(R&D) 전담인력 비율(%) | share of dedicated R&D staff among regular employees (%) | numeric entry (as reported) | 전 기업 응답 |

## 분석 구성개념과 구성 규칙

| 구성개념 | 라벨 | 구성 항목 ID | 규칙 |
|---|---|---|---|
| `quit_any` | Abandoned or suspended innovation activity (main exit outcome) | IA3, IA1, IA2, IA4, IA5, IA6 | quit_any = 1 if IA3 == yes, 0 if IA3 == no; defined only for firms with any innovation activity (IA1..IA6 any yes); recoded to printed yes=1/no=0 first |
| `exit_strict` | Abandoned without any completed activity | IA3, IA1 | exit_strict = 1 if IA3 == yes and IA1 == no, else 0; same population as quit_any |
| `exit_full` | Abandoned with neither completed nor ongoing activity | IA3, IA1, IA2 | exit_full = 1 if IA3 == yes and IA1 == no and IA2 == no, else 0; same population as quit_any |
| `preempt_strategy` | Protected products by entering the market ahead of competitors (lead-time; main preemption outcome) | PROT8 | preempt_strategy = PROT8 recoded yes=1/no=0; all firms |
| `market_first` | New-to-market product innovation (secondary preemption outcome) | MF1, PI1, PI2 | market_first = MF1 recoded yes=1/no=0 among product innovators (PI1 or PI2 == yes); missing for non-innovators (selection handled separately) |
| `entry_threat` | Perceived threat of entry by new competitors | ME4 | ME4 on printed 0-5 scale (0 = does not apply); after wave-specific recode |
| `rival_unpredictability` | Competitors' actions are difficult to predict (observation noise proxy) | ME5 | ME5 on printed 0-5 scale |
| `substitutability` | Competitor products easily substitute ours | ME3 | ME3 on printed 0-5 scale |
| `foreign_competition` | Strong competition from abroad | ME7 | ME7 on printed 0-5 scale |
| `obsolescence` | Products become outdated quickly | ME1 | ME1 on printed 0-5 scale |
| `placebo_demand` | Placebo: changes in demand difficult to predict | ME6 | ME6 on printed 0-5 scale |
| `placebo_price` | Placebo: price increases lead to loss of customers | ME8 | ME8 on printed 0-5 scale |
| `tech_uncertainty` | Future technological developments difficult to predict (control) | ME2 | ME2 on printed 0-5 scale |
| `rd_staff_share` | Share of dedicated R&D staff among regular employees (main technology-gap proxy) | RDSTAFF | percentage 0-100 as reported; ranked within industry (2-digit) x wave for the gap tercile |
| `rd_intensity` | R&D expenditure / sales (secondary gap proxy, innovation-active firms only) | RDEXP, SALES | RDEXP / SALES, both million KRW, reference calendar year; defined only where IA1..IA6 any yes and SALES > 0 |
| `export_share` | Exports / sales in the reference year | EXPORTS, SALES | EXPORTS / SALES; exports missing treated as 0 only where the questionnaire blank means no exports — verified in Task 3 against value distribution, otherwise missing |
| `masters_share` | Share of employees with a master's degree or higher | MASTERS | percentage 0-100 as reported |
| `cert_venture` | Venture-firm certification | CERT1 | 1 if the multi-response column is ticked (value == item code), else 0 |
| `cert_rd_institute` | Registered R&D institute / dedicated R&D department | CERT2 | 1 if ticked, else 0 |
| `cert_innobiz` | Inno-Biz certification | CERT3 | 1 if ticked, else 0 |
| `group_affiliate` | Firm type: independent / domestic-group affiliate / foreign-group affiliate | FORM | categorical 1/2/3 as printed |
| `legal_size` | Statutory firm size class | LEGALSIZE | categorical 1 small / 2 medium / 3 mid-sized / 4 large as printed |
| `listed` | Stock-market listing | LISTED | 1 if KOSPI/KOSDAQ/KONEX (codes 1-3), 0 if '해당사항 없음' (code 4 or data sentinel 9998) |
| `portfolio_breadth` | Number of innovation-activity types reported (portfolio-size control) | IA1, IA2, IA4, IA5, IA6 | count of yes among IA1, IA2, IA4, IA5, IA6 (IA3 excluded because it is the outcome) |
| `rd_continuous` | In-house R&D performed continuously (vs occasionally) | RDCYCLE, IA4 | 1 if RDCYCLE == 1, 0 if RDCYCLE == 2; missing where IA4 == no |
| `coop_rd` | Cooperated on R&D | COOP1 | recoded yes=1/no=0; innovation-active firms only |
| `funding_public_attempt` | Attempted central- or local-government funding | FUND7, FUND8 | 1 if FUND7 or FUND8 on printed scale >= 1 (attempted), else 0 |
| `funding_bank_attempt` | Attempted bank financing | FUND3 | 1 if FUND3 printed >= 1, else 0 |
| `hamp_competition` | Hampering factor: excessive competition (auxiliary) | HAMP13 | HAMP13 on printed 0-5 scale |
| `hamp_weak_competition` | Reason not to innovate: weak competitive pressure (auxiliary) | HAMP16 | HAMP16 on printed 0-5 scale |
| `hamp_demand_uncertainty` | Hampering factor: uncertain demand (auxiliary) | HAMP12 | HAMP12 on printed 0-5 scale |
| `sales_share_new_to_market` | Sales share of new-to-market products (%) | SHARE1, PI1, PI2 | percentage among product innovators |
| `employees` | Regular employees in the reference year | EMP | count as reported |
| `firm_age` | Firm age in the reference year | FOUNDYEAR | y2 - founding year |
| `female_share` | Share of women among regular employees (%) | FEMALE | percentage as reported (control) |
