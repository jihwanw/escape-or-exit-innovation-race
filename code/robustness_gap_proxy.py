#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 11 robustness (NOT pre-registered; labelled exploratory): replace the technology-gap proxy.
gap3 (pre-registered) uses the share of dedicated R&D staff. Here gap3_alt uses R&D intensity (RDEXP / SALES, innovation-active
firms with SALES > 0; item map constructs RDEXP, SALES): 0 = no R&D expenditure, 1 = positive <= industry2 x wave median of
positives (section / wave median borrowed when < 10 positives, as for gap3), 2 = above the median. Because R&D expenditure is
asked only of innovation-active firms (문12, filter IA1-IA6 any yes), the pre-emption model is estimated on that subsample too.
Same estimator and inference as analysis_prereg.py (wild cluster bootstrap-t, 999 draws). Writes results/07b_robustness_gap_proxy.json.
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analysis_prereg as A  # noqa: E402

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "07b_robustness_gap_proxy.json")


def add_gap_alt(p):
    d = p.copy()
    ri = d["rd_intensity"]
    pos = d[ri > 0]
    med_cell = pos.groupby(["wave", "industry2"])["rd_intensity"].agg(["median", "size"]).rename(columns={"median": "m_cell", "size": "n_cell"})
    med_sec = pos.groupby(["wave", "section"])["rd_intensity"].agg(["median", "size"]).rename(columns={"median": "m_sec", "size": "n_sec"})
    med_wave = pos.groupby("wave")["rd_intensity"].median().rename("m_wave")
    d = d.merge(med_cell, left_on=["wave", "industry2"], right_index=True, how="left").merge(med_sec, left_on=["wave", "section"], right_index=True, how="left").merge(med_wave, left_on="wave", right_index=True, how="left")
    use_cell = d["n_cell"].fillna(0) >= 10; use_sec = d["n_sec"].fillna(0) >= 10
    med = np.where(use_cell, d["m_cell"], np.where(use_sec, d["m_sec"], d["m_wave"]))
    d["gap3_alt"] = np.where(ri.isna(), np.nan, np.where(ri == 0, 0, np.where(ri <= med, 1, 2))).astype(float)
    d["gap3_alt_median_source"] = np.where(use_cell, "industry2", np.where(use_sec, "section", "wave"))
    return d


def main():
    p = A.load_panel()
    p = add_gap_alt(p)
    sub = p[(p["innov_active"] == 1) & p["gap3_alt"].notna()].copy()
    sub["gap3_prereg"] = sub["gap3"]
    sub["gap3"] = sub["gap3_alt"]  # reuse the pre-registered design() with the alternative grouping
    res = {"label": "EXPLORATORY robustness: gap proxy = R&D intensity groups (not pre-registered)", "n_innov_active_with_alt": int(len(sub)),
           "gap3_alt_counts": {str(int(k)): int(v) for k, v in sub["gap3_alt"].value_counts().sort_index().items()},
           "median_source_counts": {k: int(v) for k, v in sub["gap3_alt_median_source"].value_counts().items()},
           "crosstab_gap3_vs_alt": {f"gap3={int(g)}": {f"alt={int(a)}": int(n) for a, n in row.items()} for g, row in pd.crosstab(sub["gap3_prereg"], sub["gap3_alt"]).iterrows()},
           "tests": {}}
    yq, Xq, cq, _ = A.design(sub, "quit_any", "entry_threat_resid", A.CONTROLS_QUIT)
    yp, Xp, cp, _ = A.design(sub, "preempt_strategy", "entry_threat_resid", A.CONTROLS)
    ypo, Xpo, cpo, _ = A.design(sub, "preempt_strategy", "entry_rate_z", A.CONTROLS)
    res["tests"]["H1_alt"] = A.wild_cluster_bootstrap_t(yp, Xp, cp, {"x_g2": 1.0}, 999, A.SEED + 31)
    res["tests"]["H2_alt"] = A.wild_cluster_bootstrap_t(yq, Xq, cq, {"x_g0": 1.0}, 999, A.SEED + 32)
    res["tests"]["H3_alt"] = A.wild_cluster_bootstrap_t(yq, Xq, cq, {"x_g0": 1.0, "x_g2": -1.0}, 999, A.SEED + 33)
    res["tests"]["H4_alt"] = A.wild_cluster_bootstrap_t(yp, Xp, cp, {"x_g2": 1.0, "x_g0": -1.0}, 999, A.SEED + 34)
    res["tests"]["H5_alt"] = A.wild_cluster_bootstrap_t(yq, Xq, cq, {"g0": 1.0, "g2": -1.0}, 999, A.SEED + 35)
    res["tests"]["H6_alt"] = A.wild_cluster_bootstrap_t(ypo, Xpo, cpo, {"x_g2": 1.0}, 999, A.SEED + 36)
    # pre-registered proxy on the same subsample, for a like-for-like comparison
    sub2 = p[(p["innov_active"] == 1) & p["gap3_alt"].notna()].copy()
    yp2, Xp2, cp2, _ = A.design(sub2, "preempt_strategy", "entry_threat_resid", A.CONTROLS)
    res["tests"]["H1_prereg_proxy_same_subsample"] = A.wild_cluster_bootstrap_t(yp2, Xp2, cp2, {"x_g2": 1.0}, 999, A.SEED + 37)
    res["built"] = time.strftime("%Y-%m-%d %H:%M %Z")
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    for k, t in res["tests"].items():
        print(f"{k:34s} est {t['estimate']:+.4f} wild95 [{t['ci95_wild'][0]:+.4f},{t['ci95_wild'][1]:+.4f}] p1 {t['p_one_sided_wild']:.3f} n {t['n']}")
    print(res["gap3_alt_counts"], res["crosstab_gap3_vs_alt"])


if __name__ == "__main__":
    main()
