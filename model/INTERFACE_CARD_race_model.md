# INTERFACE CARD — race_model.py (own solver; commit state of 2026-11-09 20:5x KST)

규칙: `~/.kiro/steering/no_assumptions_in_experiment_code.md`. 이 카드는 솔버·전향계산기의 입력·출력 규약을 소스 줄과 통제 실험 결과 파일로 확정한다. 출처 없는 항목은 [UNVERIFIED].

## 입력 (`Params`, `model/race_model.py` `@dataclass Params`)
- 위치 `xL0 ≥ xF0`, `0 ≤ x < K`; 완료 = K 도달. 출처: `Params.check()` assert 줄 + `stage_payoff` `finL = nsL == ACTIVE and nxL >= P.K`.
- 비용·확률 볼록성 `cA/cC > pA/pC`, `pC < pA`, `cC < cA`: `Params.check()`.
- `theta` = 매 기간 시작 시 진입 확률(진입 1회, 영구): `U()`의 `v0/v1` 혼합 줄과 `forward_outcomes`의 `shocks = [(e,1.0)] if e == 1 else [(0,1-θ),(1,θ)]`.
- `lam` = 진입 뒤 **미완료 기업**의 상금 배율: `stage_payoff` `scale = P.lam if e == 1 else 1.0`; 완료한 기업은 상금을 이미 받았으므로 영향 없음(상금은 완료 기간에 즉시 지급: `prizeL + β·cont`).
- `sigma` = 의도 C/A가 {C,A} 균등으로 재추첨될 확률(Q 제외): `realized_dist()`.
- `W ≤ V`, 동시 완료 시 (V+W)/2: `stage_payoff` `finL and finF` 분기.
- `selection ∈ {welfare, leader, laggard}`: `select_equilibrium()`. d = 0 대칭 상태에서는 대칭 균형 우선, 없으면 거울 쌍에 공정 동전(상관균형) — 선택 규칙 무관하게 적용.

## 출력
- `Solution.U[(t, xL, sL, xF, sF, e)]` = 진입 충격 **전** 기대 보수 (L, F). `Solution.policy[post-shock state] = (mix, actsL, actsF)`, `mix = [(w, (pL, pF))]`. 행동 인덱스 Q=0, C=1, A=2(`ACT`); 활동하지 않는 기업의 actions는 `(None,)`.
- `forward_outcomes()` 반환 키와 뜻(소스 줄 `out[...] +=`):
  - `P_quit_i`: i가 Q를 **실현**할 총확률(활동 중 상태에서만 가능; 비가역이므로 ≤ 1).
  - `P_accel_i`: i가 한 번 이상 A를 **의도**한 최종 상태 질량(플래그 fL/fF).
  - `P_first_i`: i가 먼저 완료(동시 완료는 0.5씩; 상대가 이미 완료한 뒤의 완료는 0).
  - `P_finish_i`, `E_cost_i`(실현 비용), `E_accel_periods_i`(의도 A 기간 수 기대값), `P_entry`, `mass_check`(기간별 질량), `final_mass`.
- 설문 대응(MODEL_NOTES §4): P_quit ↔ 문11 ③, P_accel ↔ 문2 ⑧, P_first ↔ 문6 ①.

## 난수
- 없음. 전향 계산은 상태 분포를 정확히 전개(`forward_outcomes`), 몬테카를로 없음. 통제 실험의 무작위 매개변수만 `np.random.default_rng(20261109)`.

## 통제 실험으로 확정한 항목 (`results/03_model_controls.json`, 2026-11-09, 전부 PASS)
- C1 두 경로 일치: 해석해 `solve_two_period`(독립 코드) vs 일반 솔버, 무작위 200점에서 가치·정책·P_quit_F·P_accel_L·P_first_L 최대 차 5.6e-16.
- C2 λ=1이면 θ 무관(8.9e-16), C3 θ=0이면 λ 무관(0.0).
- C4 ε-선점 극한(pC=0.999, pA=1, W=0, 선두 1칸·후발 2칸): 후발 즉시 Q, 선두 C, P_quit_F=1, P_first_L≈1, P_accel_L=0.
- C5 d=0 대칭: 단계 보수행렬 전치 일치 2.2e-16, 균형 집합 거울 대칭 위배 0, 선택 후 가치 대칭 2.2e-16 (대칭 상태 720개 중 복수균형 20개는 공정 동전).
- C6 질량 보존 4.4e-16(σ·관측잡음 포함). C7 σ=0에서 두 σ 정의 일치. C8 확률 항등식 위배 0.

## 미확인 [UNVERIFIED]
- 없음(이 카드 범위). 모형 "가정"(진입이 미완료 상금만 깎음, 한 칸 전진, 상금 즉시 지급)은 모델링 선택이며 MODEL_NOTES §1에 명시; 데이터 인터페이스가 아니다.
