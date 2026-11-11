#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 4 — marginal distributions and power, under the embargo (no outcome x treatment statistic).

What is computed
  A. Outcome base rates by wave (unweighted and WT1-weighted) and by size band — outcomes only.
  B. Market-environment items (ME1..ME8): distribution of the printed 0-5 codes by wave — treatments only.
  C. Gap proxies: R&D-staff share distribution, share of zeros, rank/tercile sizes by wave — treatments only.
  D. Correlations among explanatory variables (ME items, gap, controls) — outcomes excluded.
  E. Clusters: industry2 x wave cell counts; number of quit / preempt EVENTS per cell (outcome only) — kill test (i).
  F. Power: minimum detectable effect for the gap x entry-threat interaction and for an industry-level treatment, by
     simulation with SYNTHETIC outcomes drawn at the observed base rate (the real outcome column is never used
     together with the real treatments). Cluster-robust SE at industry2 x wave; seed fixed.

Guard: before writing, the script asserts that no statistic in the output was produced from a frame containing both an
outcome column and a treatment column at the same time (the two column sets are only ever loaded separately).
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import statsmodels.api as sm

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import load_kis_escape_exit as L  # noqa: E402

SEED = 20261109
OUT_JSON = os.path.join(ROOT, "results", "02_marginals.json")
OUT_MD = os.path.join(ROOT, "docs", "PILOT_MARGINALS.md")

OUTCOMES = ["quit_any", "exit_strict", "exit_full", "preempt_strategy", "market_first"]
ME = {"ME1": "구식화", "ME2": "기술 예측 어려움", "ME3": "대체 용이성", "ME4": "진입 위협", "ME5": "경쟁사 행동 예측 어려움", "ME6": "수요 예측 어려움(위약)", "ME7": "해외 경쁁", "ME8": "가격 민감도(위약)"}
ME["ME7"] = "해외 경쟁"
CONTROLS = ["log_employees", "firm_age", "group_affiliate", "listed", "cert_rd_institute", "cert_venture", "portfolio_breadth", "export_share", "masters_share"]


def wmean(x, w):
    m = x.notna() & w.notna()
    return float(np.average(x[m], weights=w[m])) if m.any() else float("nan")


def part_a(panel_out):
    out = {}
    for wave, d in panel_out.groupby("wave"):
        o = {}
        for y in OUTCOMES:
            s = d[y]
            o[y] = {"n": int(s.notna().sum()), "events": int(s.sum(skipna=True)), "rate_unweighted": float(s.mean()), "rate_weighted": wmean(s, d["weight"])}
            o[y]["by_size_band"] = {str(int(b)): {"n": int(g[y].notna().sum()), "events": int(g[y].sum(skipna=True)), "rate": float(g[y].mean()) if g[y].notna().any() else None}
                                    for b, g in d.groupby("size_band") if not np.isnan(b)}
        out[wave] = o
    pooled = {y: {"n": int(panel_out[y].notna().sum()), "events": int(panel_out[y].sum(skipna=True)), "rate_unweighted": float(panel_out[y].mean())} for y in OUTCOMES}
    pooled_mfg = {y: {"n": int(panel_out.loc[panel_out.sector == "manufacturing", y].notna().sum()), "events": int(panel_out.loc[panel_out.sector == "manufacturing", y].sum(skipna=True))} for y in OUTCOMES}
    return {"by_wave": out, "pooled": pooled, "pooled_manufacturing": pooled_mfg}


def part_b(panel_trt):
    out = {}
    for wave, d in panel_trt.groupby("wave"):
        o = {}
        for c, lab in ME.items():
            s = d[c].dropna()
            o[c] = {"label_ko": lab, "n": int(len(s)), "share_0_not_applicable": float((s == 0).mean()), "mean_0_5": float(s.mean()),
                    "mean_1_5_given_applies": float(s[s > 0].mean()) if (s > 0).any() else None, "share_4_or_5": float((s >= 4).mean()),
                    "dist": {str(k): int(v) for k, v in s.value_counts().sort_index().items()}}
        out[wave] = o
    # inter-item correlation of ME items (pooled)
    corr = panel_trt[list(ME)].corr().round(3)
    return {"by_wave": out, "me_intercorrelation_pooled": corr.to_dict()}


def part_c(panel_trt):
    out = {}
    for wave, d in panel_trt.groupby("wave"):
        s = d["rd_staff_share"].dropna()
        out[wave] = {"n": int(len(s)), "share_zero": float((s == 0).mean()), "p25": float(s.quantile(.25)), "p50": float(s.median()), "p75": float(s.quantile(.75)), "p90": float(s.quantile(.9)), "mean": float(s.mean()),
                     "tercile_sizes": {str(int(k)): int(v) for k, v in d["gap_tercile"].value_counts().sort_index().items()},
                     "rd_intensity": {"n": int(d["rd_intensity"].notna().sum()), "p50": float(d["rd_intensity"].median()) if d["rd_intensity"].notna().any() else None},
                     "share_firms_with_zero_rdstaff_in_bottom_tercile": float((d.loc[d["gap_tercile"] == 1, "rd_staff_share"] == 0).mean()) if (d["gap_tercile"] == 1).any() else None}
    return out


def part_d(panel_trt):
    cols = list(ME) + ["rd_staff_share", "gap_rank"] + CONTROLS
    c = panel_trt[cols].corr().round(3)
    high = [(a, b, float(c.loc[a, b])) for i, a in enumerate(cols) for b in cols[i + 1:] if abs(c.loc[a, b]) >= 0.5]
    return {"columns": cols, "pairs_abs_corr_ge_0.5": high, "corr_ME4_ME5": float(c.loc["ME4", "ME5"]), "corr_ME4_ME3": float(c.loc["ME4", "ME3"]), "corr_ME4_ME7": float(c.loc["ME4", "ME7"])}


def part_e(panel_out):
    out = {}
    for wave, d in panel_out.groupby("wave"):
        cells = d.groupby("industry2").agg(n=("firm_id", "size"), n_active=("quit_any", "count"), quit_events=("quit_any", "sum"), preempt_events=("preempt_strategy", "sum"), mf_events=("market_first", "sum"))
        out[wave] = {"n_industry_cells": int(len(cells)), "cells_with_ge5_quit_events": int((cells["quit_events"] >= 5).sum()), "cells_with_zero_quit_events": int((cells["quit_events"] == 0).sum()),
                     "cells_with_ge5_preempt_events": int((cells["preempt_events"] >= 5).sum()), "median_cell_n": float(cells["n"].median()), "min_cell_n": int(cells["n"].min()),
                     "quit_rate_across_cells": {"min": float((cells["quit_events"] / cells["n_active"]).min()), "max": float((cells["quit_events"] / cells["n_active"]).max()), "sd": float((cells["quit_events"] / cells["n_active"]).std())}}
    out["total_industry_wave_clusters"] = int(panel_out.groupby(["wave", "industry2"]).ngroups)
    return out


def part_f(panel_trt, base_rates, n_sim=400):
    """MDE by simulation with synthetic outcomes. Design: y* = p0 + delta * (gap_top - gap_bottom) * z(ME4) + noise, LPM, cluster SE."""
    rng = np.random.default_rng(SEED)
    d = panel_trt.dropna(subset=["entry_threat", "gap_tercile", "industry2"]).copy()
    d["z_entry"] = (d["entry_threat"] - d["entry_threat"].mean()) / d["entry_threat"].std()
    d["top"] = (d["gap_tercile"] == 3).astype(float)
    d["bottom"] = (d["gap_tercile"] == 1).astype(float)
    d["inter"] = (d["top"] - d["bottom"]) * d["z_entry"]
    X = sm.add_constant(pd.get_dummies(d[["z_entry", "top", "bottom", "inter", "wave"]], columns=["wave"], drop_first=True, dtype=float))
    groups = pd.factorize(d["wave"] + "_" + d["industry2"].astype(str))[0]
    # industry-level treatment: a random normal draw per industry x wave (stands in for the objective indicator, whose power
    # depends only on the cluster structure, not on its realised values)
    ind_draw = pd.Series(rng.standard_normal(groups.max() + 1))[groups].values
    d["ind_trt"] = ind_draw
    d["ind_inter"] = (d["top"] - d["bottom"]) * d["ind_trt"]
    X2 = sm.add_constant(pd.get_dummies(d[["ind_trt", "top", "bottom", "ind_inter", "wave"]], columns=["wave"], drop_first=True, dtype=float))

    def power(Xmat, col, p0, delta, nsim):
        rej = 0
        xcol = Xmat[col].values
        for _ in range(nsim):
            p = np.clip(p0 + delta * xcol, 0.001, 0.999)
            y = rng.binomial(1, p)
            fit = sm.OLS(y, Xmat.values).fit(cov_type="cluster", cov_kwds={"groups": groups})
            j = list(Xmat.columns).index(col)
            rej += abs(fit.params[j] / fit.bse[j]) > 1.96
        return rej / nsim

    out = {"n_used": int(len(d)), "n_clusters": int(groups.max() + 1), "n_sim_per_point": n_sim, "seed": SEED, "note": "synthetic Bernoulli outcomes at the observed base rate; real outcomes not used"}
    for yname, p0 in base_rates.items():
        grid = [0.005, 0.01, 0.015, 0.02, 0.03, 0.04]
        out[yname] = {"p0": p0,
                      "power_perceived_interaction_by_delta": {str(dl): power(X, "inter", p0, dl, n_sim) for dl in grid},
                      "power_industry_level_interaction_by_delta": {str(dl): power(X2, "ind_inter", p0, dl, n_sim // 2) for dl in grid},
                      "power_industry_level_main_by_delta": {str(dl): power(X2, "ind_trt", p0, dl, n_sim // 2) for dl in grid}}
        for key in ("power_perceived_interaction_by_delta", "power_industry_level_interaction_by_delta", "power_industry_level_main_by_delta"):
            pw = out[yname][key]
            mde = next((float(k) for k, v in pw.items() if v >= 0.8), None)
            out[yname][key.replace("power_", "mde80_")] = mde
    return out


def main():
    t0 = time.time()
    panel = pd.read_parquet(L.OUT_PARQUET)
    base = ["wave", "sector", "industry2", "size_band", "weight", "firm_id", "innov_active", "product_innovator"]
    panel_out = panel[base + OUTCOMES].copy()                                             # outcomes only
    panel_trt = panel[base + list(ME) + ["entry_threat", "rd_staff_share", "gap_rank", "gap_tercile", "rd_intensity"] + CONTROLS].copy()  # treatments/controls only
    assert not set(OUTCOMES) & set(panel_trt.columns) and not (set(ME) | {"entry_threat", "gap_tercile", "gap_rank", "rd_staff_share"}) & set(panel_out.columns), "embargo: frames overlap"

    A = part_a(panel_out); B = part_b(panel_trt); C = part_c(panel_trt); D = part_d(panel_trt); E = part_e(panel_out)
    base_rates = {"quit_any_active_firms": A["pooled"]["quit_any"]["rate_unweighted"], "preempt_strategy_all_firms": A["pooled"]["preempt_strategy"]["rate_unweighted"]}
    # power for quit uses the active-firm frame; approximate by restricting the design to active firms
    F = {}
    F["quit_any"] = part_f(panel_trt[panel_trt["innov_active"] == 1], {"quit_any": base_rates["quit_any_active_firms"]})
    F["preempt_strategy"] = part_f(panel_trt, {"preempt_strategy": base_rates["preempt_strategy_all_firms"]})
    res = {"built": time.strftime("%Y-%m-%d %H:%M %Z"), "embargo": "outcome and treatment columns were loaded in separate frames; no joint statistic", "seed": SEED,
           "A_outcome_base_rates": A, "B_market_environment_items": B, "C_gap_proxies": C, "D_explanatory_correlations": D, "E_clusters_and_event_counts": E, "F_power_synthetic": F,
           "seconds": round(time.time() - t0, 1)}
    json.dump(res, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    write_md(res)
    print("wrote", OUT_JSON, "and", OUT_MD, f"({res['seconds']}s)")


def pct(x):
    return "—" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{100 * x:.1f}%"


def write_md(r):
    A, B, C, D, E, F = (r[k] for k in ("A_outcome_base_rates", "B_market_environment_items", "C_gap_proxies", "D_explanatory_correlations", "E_clusters_and_event_counts", "F_power_synthetic"))
    L_ = ["# 주변분포·검정력 보고 (Task 4, 게이트 A용)", "", f"생성 {r['built']} — `code/marginals_power.py`가 `results/02_marginals.json`에서 생성. 손으로 고치지 말 것.",
          "**금기 준수**: 결과변수와 처치변수는 서로 다른 데이터프레임에 따로 적재했고, 둘을 함께 쓴 통계는 없다. 검정력은 관측 기저율로 만든 가짜 결과변수로 계산했다.", "",
          "## A. 결과변수 기저율 (파동별)", "", "| 파동 | 중단(혁신활동 기업 중) | 완료 없이 중단 | 완료·진행 모두 없이 중단 | 선점 전략(전 기업) | 시장최초(상품혁신 기업 중) |", "|---|---|---|---|---|---|"]
    for w, o in A["by_wave"].items():
        L_.append(f"| {w} | {o['quit_any']['events']}/{o['quit_any']['n']} = {pct(o['quit_any']['rate_unweighted'])} (가중 {pct(o['quit_any']['rate_weighted'])}) | {o['exit_strict']['events']} ({pct(o['exit_strict']['rate_unweighted'])}) | {o['exit_full']['events']} ({pct(o['exit_full']['rate_unweighted'])}) | {o['preempt_strategy']['events']}/{o['preempt_strategy']['n']} = {pct(o['preempt_strategy']['rate_unweighted'])} (가중 {pct(o['preempt_strategy']['rate_weighted'])}) | {o['market_first']['events']}/{o['market_first']['n']} = {pct(o['market_first']['rate_unweighted'])} |")
    p = A["pooled"]
    L_ += [f"| **합계** | {p['quit_any']['events']}/{p['quit_any']['n']} = {pct(p['quit_any']['rate_unweighted'])} | {p['exit_strict']['events']} | {p['exit_full']['events']} | {p['preempt_strategy']['events']}/{p['preempt_strategy']['n']} = {pct(p['preempt_strategy']['rate_unweighted'])} | {p['market_first']['events']}/{p['market_first']['n']} = {pct(p['market_first']['rate_unweighted'])} |", "",
           "규모 구간별 중단율(혁신활동 기업 중):", "", "| 파동 | 10~49인 | 50~99인 | 100~299인 | 300~499인 | 500인+ |", "|---|---|---|---|---|---|"]
    for w, o in A["by_wave"].items():
        bs = o["quit_any"]["by_size_band"]
        L_.append("| " + w + " | " + " | ".join(f"{bs[b]['events']}/{bs[b]['n']} ({pct(bs[b]['rate'])})" if b in bs else "—" for b in ["1", "2", "3", "4", "5"]) + " |")
    L_ += ["", "## B. 시장환경 문항 (인쇄 코드 0~5; 0 = 해당 없음)", "", "| 파동 | 항목 | 해당 없음 비율 | 평균(0~5) | 4~5 비율 |", "|---|---|---|---|---|"]
    for w, o in B["by_wave"].items():
        for c in ("ME4", "ME5", "ME3", "ME7", "ME1", "ME6", "ME8", "ME2"):
            x = o[c]; L_.append(f"| {w} | {c} {x['label_ko']} | {pct(x['share_0_not_applicable'])} | {x['mean_0_5']:.2f} | {pct(x['share_4_or_5'])} |")
    ic = B["me_intercorrelation_pooled"]
    L_ += ["", f"항목 간 상관(통합): 진입 위협–경쟁사 예측 어려움 r = {ic['ME4']['ME5']:.2f}, 진입 위협–대체 용이성 r = {ic['ME4']['ME3']:.2f}, 진입 위협–해외 경쟁 r = {ic['ME4']['ME7']:.2f}, 진입 위협–수요 예측(위약) r = {ic['ME4']['ME6']:.2f}, 진입 위협–가격 민감도(위약) r = {ic['ME4']['ME8']:.2f}.", "",
           "## C. 기술 격차 대리변수: 연구개발 전담인력 비율(%)", "", "| 파동 | n | 0% 비율 | 중위 | 75% | 90% | 평균 | 하위 3분위 중 0% 비율 |", "|---|---|---|---|---|---|---|---|"]
    for w, o in C.items():
        L_.append(f"| {w} | {o['n']} | {pct(o['share_zero'])} | {o['p50']:.1f} | {o['p75']:.1f} | {o['p90']:.1f} | {o['mean']:.1f} | {pct(o['share_firms_with_zero_rdstaff_in_bottom_tercile'])} |")
    L_ += ["", "## D. 설명변수 간 상관 (결과변수 제외)", "", f"|r| ≥ 0.5인 쌍: {D['pairs_abs_corr_ge_0.5'] if D['pairs_abs_corr_ge_0.5'] else '없음'}", "",
           "## E. 군집(업종×파동)과 사건 수 — 죽이기 기준 (i)", "", "| 파동 | 업종 셀 수 | 중단 사건 ≥5 셀 | 중단 사건 0 셀 | 선점 사건 ≥5 셀 | 셀 내 중단율 범위(최소~최대, SD) | 셀 n 중위(최소) |", "|---|---|---|---|---|---|---|"]
    for w, o in E.items():
        if w == "total_industry_wave_clusters": continue
        q = o["quit_rate_across_cells"]; L_.append(f"| {w} | {o['n_industry_cells']} | {o['cells_with_ge5_quit_events']} | {o['cells_with_zero_quit_events']} | {o['cells_with_ge5_preempt_events']} | {pct(q['min'])}~{pct(q['max'])} (SD {100*q['sd']:.1f}p) | {o['median_cell_n']:.0f} ({o['min_cell_n']}) |")
    L_ += [f"", f"업종×파동 군집 총수: {E['total_industry_wave_clusters']}.", "", "## F. 검정력 (가짜 결과변수, 관측 기저율, 업종×파동 군집 SE, seed 고정)", "",
           "δ = 격차 상위 3분위와 하위 3분위 사이의 '진입 위협 1 SD당 결과 확률 차이'(확률 단위). 80% 검정력에 필요한 최소 δ(MDE):", "",
           "| 결과 | 기저율 | n | 군집 | MDE: 인식 변수 × 격차 상호작용 | MDE: 업종 수준 지표 × 격차 상호작용 | MDE: 업종 수준 지표 주효과 |", "|---|---|---|---|---|---|---|"]
    for y, f in F.items():
        k = [kk for kk in f if kk not in ("n_used", "n_clusters", "n_sim_per_point", "seed", "note")][0]
        g = f[k]
        fmt = lambda v: "—(>0.04)" if v is None else f"{v:.3f} ({100*v:.1f}p)"  # noqa: E731
        L_.append(f"| {y} | {pct(g['p0'])} | {f['n_used']} | {f['n_clusters']} | {fmt(g['mde80_perceived_interaction_by_delta'])} | {fmt(g['mde80_industry_level_interaction_by_delta'])} | {fmt(g['mde80_industry_level_main_by_delta'])} |")
    L_ += ["", "검정력 곡선(δ별 기각률)은 `results/02_marginals.json` → `F_power_synthetic`.", "",
           "## 게이트 A에서 결정할 것", "",
           "1. 중단 기저율(혁신활동 기업 중 약 5~13%, 2022M이 높음)과 셀별 사건 수로 업종 고정효과 추정이 가능한지.",
           "2. 서비스 두 파동의 시장최초(문6 ①) 사건 수가 매우 적어(각 10·15건) 시장최초 결과는 제조업 두 파동에서만 쓰는 것으로 한정할지.",
           "3. 연구개발 전담인력 비율 0%가 많은 파동에서 하위 3분위가 전부 0%로 묶이는 문제 — 격차 3분위 대신 {0%, 0 초과~업종 중위, 중위 초과}의 3구간 정의로 바꿀지(사전등록 전에 결정).",
           "4. MDE가 이론적으로 기대하는 효과 크기(Aghion 외 2009의 특허·생산성 효과와 직접 비교는 불가) 대비 받아들일 만한지."]
    open(OUT_MD, "w", encoding="utf-8").write("\n".join(L_) + "\n")


if __name__ == "__main__":
    main()
