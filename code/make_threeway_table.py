#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 10 demo: theory sign x agent sign x KIS estimate, per hypothesis, from the frozen predictions and the pre-registered
results. Writes results/06_threeway_table.json and docs/THREEWAY_TABLE.md. No number is typed here."""
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
J = lambda *p: json.load(open(os.path.join(ROOT, *p), encoding="utf-8"))  # noqa: E731


def main():
    pred = J("prereg", "agent_predictions_v1.json")
    main_ = J("results", "06_kis_main.json")
    T = main_["main"]["tests"]; D = main_["main"]["decisions"]; HW = main_["main"]["holm_wild"]
    rob = main_["robustness"]
    rows = []
    for h, p in pred["predictions"].items():
        t = T[h]
        rob_signs = {k: ("+" if v["tests"][h]["estimate"] > 0 else "-") + (" (p<.05)" if v["tests"][h]["p_one_sided_wild"] < 0.05 else "") for k, v in rob.items()}
        rows.append({"hypothesis": h, "theory_sign": p["theory_sign"], "agent_stage_a": (p["stage_a"] or {}).get("consensus"), "agent_stage_b": p["stage_b"]["consensus"],
                     "kis_estimate": t["estimate"], "kis_ci95_wild": t["ci95_wild"], "kis_ci90_wild": t["ci90_wild"], "kis_p_one_sided_wild": t["p_one_sided_wild"],
                     "kis_holm_wild": HW.get(h), "kis_decision": D[h], "n": t["n"], "clusters": t["n_clusters"], "robustness_signs": rob_signs})
    extra = {"H2_objective": {"estimate": T["H2_objective"]["estimate"], "ci95_wild": T["H2_objective"]["ci95_wild"], "p_one_sided_wild": T["H2_objective"]["p_one_sided_wild"],
                              "note": "entry_rate_z x g0; slopes for g0/g1/g2 are " + ", ".join(f"{k} {v:+.3f}" for k, v in main_["main"]["coefficients"]["quit_objective"]["coef"].items() if k.startswith("x_")) +
                                      "; with industry x wave FE the slope is " + f"{rob['fe_industry_x_wave']['tests']['H2_objective']['estimate']:+.4f}" + " — a between-industry level association, not laggard-specific"},
             "placebo": {k: {kk: {"estimate": vv["estimate"], "p_two_sided_wild": vv["p_two_sided_wild"]} for kk, vv in v.items() if isinstance(vv, dict)} for k, v in main_["placebo"].items()},
             "H2_falsified_both_nonpositive": main_["main"]["H2_falsified_both_nonpositive"]}
    out = {"rows": rows, "extra": extra, "sources": {"predictions": "prereg/agent_predictions_v1.json", "kis": "results/06_kis_main.json"}, "built": time.strftime("%Y-%m-%d %H:%M %Z")}
    json.dump(out, open(os.path.join(ROOT, "results", "06_threeway_table.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    L = ["# 가설별 3자 비교표 (이론 · 에이전트 · KIS) — Task 10, 게이트 D용", "",
         f"생성 {out['built']} — `code/make_threeway_table.py`가 `prereg/agent_predictions_v1.json`(동결)과 `results/06_kis_main.json`(사전등록 스크립트 `--real`)에서 생성. 손으로 고치지 말 것.", "",
         "KIS 열: LPM 계수(처치 1 SD당 확률 변화), wild cluster bootstrap-t 95% CI, 단측 p, Holm(H1~H5) 보정 p, 사전등록 판정 규칙의 결정.", "",
         "| 가설 | 이론 | 에이전트 A | 에이전트 B | KIS 추정 | 95% CI | p(단측) | Holm | 판정 | N / 군집 |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['hypothesis']} | {r['theory_sign']} | {r['agent_stage_a'] or 'n/a'} | {r['agent_stage_b']} | {r['kis_estimate']:+.4f} | [{r['kis_ci95_wild'][0]:+.4f}, {r['kis_ci95_wild'][1]:+.4f}] | {r['kis_p_one_sided_wild']:.3f} | {('%.3f' % r['kis_holm_wild']) if r['kis_holm_wild'] is not None else '—'} | {r['kis_decision']} | {r['n']:,} / {r['clusters']} |")
    L += ["", "## 강건성 사양별 부호 (사전등록 강건성; 결정에는 쓰지 않음)", "", "| 가설 | " + " | ".join(rows[0]["robustness_signs"].keys()) + " |", "|---|" + "---|" * len(rows[0]["robustness_signs"])]
    for r in rows:
        L.append(f"| {r['hypothesis']} | " + " | ".join(r["robustness_signs"].values()) + " |")
    L += ["", "## 보조", "", f"- H2 객관(신생기업률×후발): {extra['H2_objective']['estimate']:+.4f} [{extra['H2_objective']['ci95_wild'][0]:+.4f}, {extra['H2_objective']['ci95_wild'][1]:+.4f}], 단측 p {extra['H2_objective']['p_one_sided_wild']:.3f}. {extra['H2_objective']['note']}",
          f"- H2 반증 조건(인식·객관 둘 다 ≤ 0): {extra['H2_falsified_both_nonpositive']}",
          "- 위약(두 문항 × 두 결과, 양측 wild p): " + "; ".join(f"{k.replace('_resid','')} {kk} {vv['estimate']:+.4f} (p {vv['p_two_sided_wild']:.3f})" for k, v in extra["placebo"].items() for kk, vv in v.items())]
    open(os.path.join(ROOT, "docs", "THREEWAY_TABLE.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
