#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 6b — merge the objective entry indicator into the analysis panel.

Reference period per wave (from each questionnaire's '지난 3년간' wording, Task 2):
  2022M: 2019-2021 | 2023S: 2020-2022 | 2024M: 2021-2023 | 2025S: 2022-2024.
For each firm, entry_rate = mean over the wave's three reference years of the KSIC-2-digit firm birth rate
(KOSIS DT_6BD1101, 전국, item T04 '신생률', %, see data/provenance_entry_rates.json). No year outside the reference period
is used (look-ahead check below). Also kept: entry_rate_last (final reference year), active firms (log), and a
within-wave z-score so that one unit = one SD across industries in that wave.

Writes data/analysis_panel.parquet (adds columns), data/external_industry_year.csv, results/06_external_merge.json.
Embargo: no outcome column is touched or summarised here.
"""
import json
import os
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PANEL = os.path.join(ROOT, "data", "analysis_panel.parquet")
ENTRY = os.path.join(ROOT, "data", "entry_rates_industry_year.csv")
OUT_EXT = os.path.join(ROOT, "data", "external_industry_year.csv")
OUT_LOG = os.path.join(ROOT, "results", "06_external_merge.json")
REF = {"2022M": (2019, 2021), "2023S": (2020, 2022), "2024M": (2021, 2023), "2025S": (2022, 2024)}


def main():
    panel = pd.read_parquet(PANEL)
    er = pd.read_csv(ENTRY, dtype={"ksic2": str})
    # C2 contains the KSIC section letters (A..U, section totals) and '0' (전체) besides the 2-digit division codes;
    # keep divisions only (checked 2026-11-10: non-numeric codes are the 21 section letters)
    er = er[er["ksic2"].str.fullmatch(r"\d{2}")].copy()
    er["ksic2"] = er["ksic2"].astype(int)
    # industry x wave table restricted to reference years
    rows = []
    for w, (y0, y2) in REF.items():
        sub = er[(er["year"] >= y0) & (er["year"] <= y2)]
        g = sub.groupby("ksic2").agg(entry_rate=("birth_rate_official", "mean"), entry_rate_last=("birth_rate_official", lambda s: s.iloc[-1]),
                                     births_mean=("births", "mean"), active_mean=("active", "mean"), n_years=("year", "nunique"),
                                     years_used=("year", lambda s: ",".join(map(str, sorted(s.unique())))))
        g["wave"] = w
        rows.append(g.reset_index())
    ext = pd.concat(rows, ignore_index=True)
    ext["log_active_firms"] = np.log(ext["active_mean"])
    ext.to_csv(OUT_EXT, index=False, encoding="utf-8-sig")
    # look-ahead check: every year used lies inside the reference window
    la = []
    for _, r in ext.iterrows():
        y0, y2 = REF[r["wave"]]
        ys = [int(y) for y in r["years_used"].split(",")]
        if min(ys) < y0 or max(ys) > y2:
            la.append((r["wave"], int(r["ksic2"]), r["years_used"]))
    # merge
    keep = ["wave", "ksic2", "entry_rate", "entry_rate_last", "log_active_firms", "n_years"]
    m = panel.drop(columns=[c for c in ["entry_rate", "entry_rate_last", "log_active_firms", "entry_rate_z", "entry_n_years"] if c in panel.columns])
    m = m.merge(ext[keep].rename(columns={"ksic2": "industry2", "n_years": "entry_n_years"}), on=["wave", "industry2"], how="left")
    m["entry_rate_z"] = m.groupby("wave")["entry_rate"].transform(lambda s: (s - s.mean()) / s.std())
    assert len(m) == len(panel), "merge changed row count"
    m.to_parquet(PANEL, index=False)
    cov = {}
    for w, d in m.groupby("wave"):
        cov[w] = {"n_firms": int(len(d)), "n_firms_missing_entry_rate": int(d["entry_rate"].isna().sum()),
                  "industries_missing": sorted(d.loc[d["entry_rate"].isna(), "industry2"].dropna().astype(int).unique().tolist()),
                  "n_years_per_cell": sorted(d["entry_n_years"].dropna().unique().astype(int).tolist()),
                  "entry_rate_pct": {"min": float(d["entry_rate"].min()), "p50": float(d["entry_rate"].median()), "max": float(d["entry_rate"].max()), "sd_across_firms": float(d["entry_rate"].std())},
                  "n_industry_cells": int(d["industry2"].nunique())}
    log = {"built": time.strftime("%Y-%m-%d %H:%M %Z"), "reference_periods": {k: list(v) for k, v in REF.items()}, "source": "data/entry_rates_industry_year.csv (KOSIS DT_6BD1101 T04 신생률, 전국)",
           "look_ahead_violations": la, "coverage": cov, "n_panel_rows": int(len(m)), "columns_added": ["entry_rate", "entry_rate_last", "log_active_firms", "entry_n_years", "entry_rate_z"],
           "embargo": "no outcome column read or summarised in this step"}
    json.dump(log, open(OUT_LOG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(log, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
