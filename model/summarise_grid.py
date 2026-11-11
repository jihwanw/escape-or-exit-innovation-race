#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 5 — re-summarise results/03_grid_outcomes.parquet (no re-solving) with
  (i) two monotonicity criteria: strict (every step weakly in direction; one strict) and end-to-end (sign of outcome(theta_max)
      minus outcome(0), with |diff| > 1e-6 counted as informative);
  (ii) the frontier distance of the leader n_L = K - xL0 as a conditioning variable (Aghion et al. 2009: escape-entry
      operates for firms close to the technological frontier).
Kill test (iv): a prediction is a pre-registration candidate when, on the stated domain and under the main selection rule,
  the end-to-end sign agrees on >= 90 % of informative grid points AND strict monotonicity holds on >= 50 % of informative
  points, AND the end-to-end sign agrees on >= 90 % under the two alternative selection rules.
Writes results/03_model_predictions.json (overwrites the summary produced by run_grid.py; grid file untouched) and
docs/MODEL_PREDICTIONS.md (generated)."""
import json
import os
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GRID = os.path.join(ROOT, "results", "03_grid_outcomes.parquet")
OUT_JSON = os.path.join(ROOT, "results", "03_model_predictions.json")
OUT_MD = os.path.join(ROOT, "docs", "MODEL_PREDICTIONS.md")

PRED = {
    "P1": ("P_accel_L", +1, "theta ↑ → leader accelerates (escape entry)", "nL==1"),
    "P1_all": ("P_accel_L", +1, "theta ↑ → leader accelerates, all leaders", "all"),
    "P1_far": ("P_accel_L", +1, "theta ↑ → leader accelerates, leaders with nL>=2", "nL>=2"),
    "P2": ("P_quit_F", +1, "theta ↑ → laggard quits", "all"),
    "P2_far": ("P_quit_F", +1, "theta ↑ → laggard quits, laggards with nF>=2", "nF>=2"),
    "P3": ("dquit", +1, "theta effect on quitting: laggard > leader", "all"),
    "P3_near": ("dquit", +1, "theta effect on quitting: laggard > leader, nL==1", "nL==1"),
    "P4": ("daccel", +1, "theta effect on accelerating: leader > laggard", "all"),
    "P4_near": ("daccel", +1, "theta effect on accelerating: leader > laggard, nL==1", "nL==1"),
    "P7": ("level_quit_gap", +1, "laggard quits more than leader (level, d>=1, any theta)", "all"),
    "P8": ("P_first_L", +1, "theta ↑ → leader first to market", "all"),
    "P8_near": ("P_first_L", +1, "theta ↑ → leader first to market, nL==1", "nL==1"),
    "P2L": ("P_quit_L", 0, "theta effect on leader quitting (reported)", "all"),
    "P2L_far": ("P_quit_L", 0, "theta effect on leader quitting, nL>=2 (reported)", "nL>=2"),
}
SIGMA_PRED = {"P5": ("P_quit_F", "sigma effect on laggard quitting"), "P6": ("P_accel_L", "sigma effect on leader acceleration"),
              "P5L": ("P_quit_L", "sigma effect on leader quitting"), "P6F": ("P_accel_F", "sigma effect on laggard acceleration")}


def series(g, col, pre):
    if col == "dquit":
        return (g[pre + "P_quit_F"] - g[pre + "P_quit_L"]).values
    if col == "daccel":
        return (g[pre + "P_accel_L"] - g[pre + "P_accel_F"]).values
    return g[pre + col].values


def strict_class(seq, direction):
    d = np.diff(np.asarray(seq, float)); d[np.abs(d) < 1e-10] = 0.0
    if np.all(d == 0):
        return "flat"
    if direction == 0:
        return "up" if np.all(d >= 0) else ("down" if np.all(d <= 0) else "nonmonotone")
    return "holds" if np.all(direction * d >= 0) else "violated"


def e2e_class(seq, direction):
    diff = float(seq[-1] - seq[0])
    if abs(diff) < 1e-6:
        return "flat"
    if direction == 0:
        return "up" if diff > 0 else "down"
    return "holds" if direction * diff > 0 else "violated"


def domain_mask(g0, dom):
    nL, nF = g0["K"] - g0["xL0"], g0["K"] - g0["xF0"]
    return {"all": True, "nL==1": nL == 1, "nL>=2": nL >= 2, "nF>=2": nF >= 2}[dom]


def main():
    df = pd.read_parquet(GRID)
    df["nL"] = df["K"] - df["xL0"]; df["nF"] = df["K"] - df["xF0"]
    res = {"built": time.strftime("%Y-%m-%d %H:%M %Z"), "source_grid": os.path.basename(GRID), "n_rows": int(len(df)),
           "theta_grid": sorted(df.theta.unique().tolist()), "sigma_grid": sorted(df.sigma.unique().tolist()),
           "n_grid_points": int(df.gi.nunique()), "theta": {}, "sigma": {}, "decisions": {}, "levels": {}}
    base = df[(df.sigma == 0.0) & (df.sigma_def == "tremble")]
    for version, pre in (("threat", "thr_"), ("unconditional", "")):
        res["theta"][version] = {}
        for sel, dsel in base.groupby("sel"):
            out = {}
            for pid, (col, direction, desc, dom) in PRED.items():
                cs = {"holds": 0, "flat": 0, "violated": 0, "up": 0, "down": 0, "nonmonotone": 0}
                ce = {"holds": 0, "flat": 0, "violated": 0, "up": 0, "down": 0}
                n = 0
                for gi, g in dsel.groupby("gi"):
                    g = g.sort_values("theta"); g0 = g.iloc[0]
                    if g0["d"] < 1 or not domain_mask(g0, dom):
                        continue
                    n += 1
                    if col == "level_quit_gap":
                        v = float((g[pre + "P_quit_F"] - g[pre + "P_quit_L"]).mean())
                        ce["holds" if v > 1e-6 else ("flat" if abs(v) <= 1e-6 else "violated")] += 1
                        cs["holds" if v > 1e-6 else ("flat" if abs(v) <= 1e-6 else "violated")] += 1
                        continue
                    seq = series(g, col, pre)
                    cs[strict_class(seq, direction)] += 1
                    ce[e2e_class(seq, direction)] += 1
                out[pid] = {"outcome": col, "direction": direction, "domain": dom, "description": desc, "n_points": n,
                            "strict": {k: round(v / n, 4) for k, v in cs.items() if v} if n else {},
                            "end_to_end": {k: round(v / n, 4) for k, v in ce.items() if v} if n else {}}
            res["theta"][version][sel] = out
    # sigma (main rule), both definitions, both versions
    for sdef in ("tremble", "obs_noise"):
        res["sigma"][sdef] = {}
        dd = df[(df.sel == "welfare") & ((df.sigma_def == sdef) | (df.sigma == 0.0))]
        for version, pre in (("threat", "thr_"), ("unconditional", "")):
            for pid, (col, desc) in SIGMA_PRED.items():
                cs = {"flat": 0, "up": 0, "down": 0, "nonmonotone": 0}; ce = {"flat": 0, "up": 0, "down": 0}; n = 0
                for (gi, th), g in dd.groupby(["gi", "theta"]):
                    g = g.drop_duplicates("sigma").sort_values("sigma")
                    if len(g) < len(res["sigma_grid"]) or g.iloc[0]["d"] < 1:
                        continue
                    n += 1; seq = g[pre + col].values
                    cs[strict_class(seq, 0)] += 1; ce[e2e_class(seq, 0)] += 1
                res["sigma"][sdef][f"{version}:{pid}"] = {"outcome": col, "description": desc, "n_series": n,
                                                          "strict": {k: round(v / n, 4) for k, v in cs.items() if v}, "end_to_end": {k: round(v / n, 4) for k, v in ce.items() if v}}
    # decisions (kill test iv) on the threat version
    for pid, (col, direction, desc, dom) in PRED.items():
        if direction == 0:
            continue
        t = res["theta"]["threat"]
        e = t["welfare"][pid]["end_to_end"]; s = t["welfare"][pid]["strict"]
        inf_e = e.get("holds", 0) + e.get("violated", 0); inf_s = s.get("holds", 0) + s.get("violated", 0)
        e_share = e.get("holds", 0) / inf_e if inf_e else 0.0; s_share = s.get("holds", 0) / inf_s if inf_s else 0.0
        alt_ok = True
        for sel in ("leader", "laggard"):
            ee = t[sel][pid]["end_to_end"]; ie = ee.get("holds", 0) + ee.get("violated", 0)
            alt_ok &= (ee.get("holds", 0) / ie if ie else 0.0) >= 0.9
        cand = e_share >= 0.9 and s_share >= 0.5 and inf_e >= 0.2 and alt_ok
        res["decisions"][pid] = {"candidate": bool(cand), "domain": dom, "n_points": t["welfare"][pid]["n_points"], "share_informative_e2e": round(inf_e, 4),
                                 "e2e_holds_among_informative": round(e_share, 4), "strict_holds_among_informative": round(s_share, 4), "alt_rules_e2e_ok": bool(alt_ok),
                                 "end_to_end": e, "strict": s}
    for pid in ("P5", "P6"):
        shares = {sd: res["sigma"][sd][f"threat:{pid}"]["end_to_end"] for sd in ("tremble", "obs_noise")}
        dom_dir = {}
        for sd, sh in shares.items():
            inf = sh.get("up", 0) + sh.get("down", 0)
            dom_dir[sd] = (("up" if sh.get("up", 0) >= sh.get("down", 0) else "down"), round(max(sh.get("up", 0), sh.get("down", 0)) / inf, 4) if inf else 0.0, round(inf, 4))
        same = dom_dir["tremble"][0] == dom_dir["obs_noise"][0] and all(v[1] >= 0.9 for v in dom_dir.values()) and all(v[2] >= 0.2 for v in dom_dir.values())
        res["decisions"][pid] = {"candidate": bool(same), "dominant_direction_share_informative": dom_dir, "end_to_end": shares}
    # levels for the figure/table: grid medians by theta, threat version, main rule, nL==1 vs nL>=2
    for lab, m in (("nL==1", base.nL == 1), ("nL>=2", base.nL >= 2)):
        dsub = base[(base.sel == "welfare") & m & (base.d >= 1)]
        res["levels"][lab] = dsub.groupby("theta")[["thr_P_accel_L", "thr_P_quit_F", "thr_P_quit_L", "thr_P_first_L", "thr_P_accel_F"]].median().round(4).to_dict()
    res["multiplicity"] = {"share_runs_with_multiple_equilibria": float((df.n_multi > 0).mean()), "share_runs_with_mixed_equilibria": float((df.n_mixed > 0).mean())}
    json.dump(res, open(OUT_JSON, "w"), indent=1)
    write_md(res)
    print(json.dumps(res["decisions"], indent=1)); print("wrote", OUT_JSON, OUT_MD)


def write_md(r):
    L = ["# 경주 모형 예측표 (Task 5, 게이트 B용)", "", f"생성 {r['built']} — `model/summarise_grid.py`가 `results/03_model_predictions.json`에서 생성. 손으로 고치지 말 것.",
         f"격자 점 {r['n_grid_points']}개 × θ {r['theta_grid']} × σ {r['sigma_grid']} × 선택 규칙 3종. 결과변수는 **위협 버전**(진입이 기간 내 실현되지 않은 분기에 조건부; MODEL_NOTES §4). 통제 실험 9종 PASS(`results/03_model_controls.json`).", "",
         "판정 규칙(죽이기 기준 iv): 주 선택 규칙에서 끝점 부호가 정보 있는 점의 90% 이상 일치 + 엄격 단조가 50% 이상 + 정보 있는 점이 20% 이상 + 다른 두 선택 규칙에서도 끝점 부호 90% 이상.", "",
         "| 예측 | 영역 | 점 수 | 끝점 부호 성립(정보 있는 점 중) | 엄격 단조 성립 | 평탄 비율 | 후보 |", "|---|---|---|---|---|---|---|"]
    for pid, d in r["decisions"].items():
        if pid in ("P5", "P6"):
            continue
        L.append(f"| {pid} | {d['domain']} | {d['n_points']} | {d['e2e_holds_among_informative']:.2f} | {d['strict_holds_among_informative']:.2f} | {1 - d['share_informative_e2e']:.2f} | {'**예**' if d['candidate'] else '아니오'} |")
    L += ["", "σ(경쟁사 행동 예측 어려움) 예측 — 부호를 가정하지 않고 도출; 두 정의(실행 교란 / 관측 잡음)에서 같은 우세 부호가 90% 이상이어야 후보:", ""]
    for pid in ("P5", "P6"):
        d = r["decisions"][pid]; L.append(f"- {pid}: 우세 방향(정의별: 방향, 정보 있는 점 중 비율, 정보 있는 점 비율) = {d['dominant_direction_share_informative']} → 후보 {'예' if d['candidate'] else '아니오'}")
    L += ["", "## 격자 중위값(위협 버전, 주 규칙, d ≥ 1)", ""]
    for lab, lv in r["levels"].items():
        L.append(f"### 선두의 잔여 거리 {lab}"); L.append(""); L.append("| θ | P_accel_L | P_quit_F | P_quit_L | P_first_L | P_accel_F |"); L.append("|---|---|---|---|---|---|")
        ths = sorted(lv["thr_P_accel_L"].keys(), key=float)
        for th in ths:
            L.append(f"| {float(th):.2f} | {lv['thr_P_accel_L'][th]:.3f} | {lv['thr_P_quit_F'][th]:.3f} | {lv['thr_P_quit_L'][th]:.3f} | {lv['thr_P_first_L'][th]:.3f} | {lv['thr_P_accel_F'][th]:.3f} |")
        L.append("")
    L += [f"복수균형이 나온 실행 비율 {r['multiplicity']['share_runs_with_multiple_equilibria']:.2f}, 혼합균형 {r['multiplicity']['share_runs_with_mixed_equilibria']:.2f}.", ""]
    open(OUT_MD, "w", encoding="utf-8").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
