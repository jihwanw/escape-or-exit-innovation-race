#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 3 — harmonised four-wave analysis panel for Escape or Exit.

Every analysis column is built from a variable listed in the wave's audited item map
(item_maps/item_map_<wave>.json, Task 2). Codes are first mapped to the PRINTED
questionnaire codes with the map's `recode_to_printed` (derived from the data in Task 2),
and only then combined. Nothing here reads a variable name for its meaning; every
variable-defining line cites its item-map construct id and questionnaire block.

EMBARGO (RESEARCH_PLAN §4.2): until the OSF registration (gate C) no statistic may combine
an outcome with a treatment variable. This module exposes OUTCOME_COLS and TREATMENT_COLS
and the summary writer refuses any cross-tabulation between the two sets.

Outputs: data/analysis_panel.parquet, results/01_build_summary.json
"""
import json
import os
import re
import sys
import time

import numpy as np
import openpyxl
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MAPS = os.path.join(ROOT, "item_maps")
OUT_PARQUET = os.path.join(ROOT, "data", "analysis_panel.parquet")
OUT_SUMMARY = os.path.join(ROOT, "results", "01_build_summary.json")

WAVE_ORDER = ["2022M", "2023S", "2024M", "2025S"]
Y2 = {"2022M": 2021, "2023S": 2022, "2024M": 2023, "2025S": 2024}  # reference calendar year [questionnaire 문7/문12/문31/문32/문33 of each wave]

OUTCOME_COLS = ["quit_any", "exit_strict", "exit_full", "preempt_strategy", "market_first", "market_first_main", "IA3", "PROT8", "MF1", "SHARE1", "sales_share_new_to_market"]
TREATMENT_COLS = ["entry_threat", "rival_unpredictability", "substitutability", "foreign_competition", "obsolescence",
                  "placebo_demand", "placebo_price", "tech_uncertainty", "ME1", "ME2", "ME3", "ME4", "ME5", "ME6", "ME7", "ME8",
                  "gap_rank", "gap_tercile", "gap3", "rd_staff_share", "me_mean8", "entry_threat_resid", "rival_unpredictability_resid"]

# Undocumented sentinel values found in Task 2 data scans (results/02_item_map_build.json + scan 2026-11-09):
#   2024M Q12K1_1/_2/_3 contain 99999999 (19/15/25 firms) — 1e8 million KRW (100 trillion) is not a possible R&D outlay for any Korean firm; the codebook 비고 says only '단위: 백만원'. Treated as missing.
#   2025S OPBIZ_DE_3 (founding year, SBR register) contains one value 30 — treated as missing (implausible year).
SENTINELS = {("2024M", "RDEXP"): [99999999], ("2024M", "NONRDEXP"): [99999999]}
FOUNDYEAR_MIN = 1800

# KSIC (10th rev.) section letter from the 2-digit division code. Source: KSIC structure as reproduced in the
# codebook value labels of 업종(중분류)/업종(대분류) (2023S inventory) and BR_GI_LCLS_CD/BR_GI_MCLS_CD (2025S); the derived
# letter is cross-checked against the register section variable where one exists (see build summary 'section_check').
KSIC_SECTION = [(10, 34, "C"), (45, 47, "G"), (49, 52, "H"), (55, 56, "I"), (58, 63, "J"), (64, 66, "K"), (68, 68, "L"),
                (70, 73, "M"), (74, 76, "N"), (85, 85, "P"), (86, 87, "Q"), (90, 91, "R"), (94, 96, "S")]
# 2023S 업종(대분류) numeric codes -> section letter, from the codebook value labels read in the inventory
# ('1.도매 및 소매업' … '12. 협회 및 단체, 수리 및 기타 개인 서비스업')
S2023_SECTION = {1: "G", 2: "H", 3: "I", 4: "J", 5: "K", 6: "L", 7: "M", 8: "N", 9: "P", 10: "Q", 11: "R", 12: "S"}


def section_from_div(code):
    if pd.isna(code):
        return np.nan
    c = int(code)
    for lo, hi, s in KSIC_SECTION:
        if lo <= c <= hi:
            return s
    return "?"


def load_map(wave):
    m = json.load(open(os.path.join(MAPS, f"item_map_{wave}.json"), encoding="utf-8"))
    return m, {e["construct_id"]: e for e in m["items"]}


def read_sheet(path, sheet, header_row):
    ws = openpyxl.load_workbook(path, read_only=True)[sheet]
    rows = list(ws.iter_rows(min_row=header_row, values_only=True))
    hdr = [str(c) if c is not None else f"_blank{j}" for j, c in enumerate(rows[0])]
    df = pd.DataFrame(rows[1:], columns=hdr)
    df.columns = [c.strip() for c in df.columns]
    return df


def recode(series, entry, wave):
    """Map raw codes to printed questionnaire codes using the item map; numeric entries pass through."""
    s = pd.to_numeric(series, errors="coerce")
    rc = entry.get("recode_to_printed")
    sent = SENTINELS.get((wave, entry["construct_id"]))
    if sent:
        s = s.where(~s.isin(sent))
    if rc:
        mapping = {float(k): v for k, v in rc.items()}
        out = s.map(mapping)
        # any observed code outside the derived map must surface, not be silently dropped
        unexpected = s.dropna()[~s.dropna().isin(list(mapping))]
        if len(unexpected):
            raise ValueError(f"{wave} {entry['variable']}: codes outside the item-map recode: {sorted(unexpected.unique())[:10]}")
        return out.astype("float")
    return s.astype("float")


def label_map(entry):
    """Parse '11. 서울' / '1.서울' style value labels into {code: label}."""
    out = {}
    for v in entry.get("values", []):
        mm = re.match(r"^\s*(\d+)\s*\.\s*(.+)$", str(v))
        if mm:
            out[int(mm.group(1))] = mm.group(2).strip()
    return out


def build_wave(wave):
    m, items = load_map(wave)
    meta = m["_meta"]
    raw = read_sheet(meta["data"], meta["data_sheet"], 2 if wave == "2023S" else 1)
    n = len(raw)
    df = pd.DataFrame(index=raw.index)
    df["wave"] = wave
    df["sector"] = meta["sector"]
    df["ref_year"] = Y2[wave]
    col = lambda cid: raw[items[cid]["variable"].strip()]  # noqa: E731

    # ---- questionnaire items -> printed codes (construct ids from item_map; blocks cited in item_map 'questionnaire_block')
    for cid, e in items.items():
        if e.get("register"):
            continue
        df[cid] = recode(col(cid), e, wave)

    # ---- register variables
    df["firm_id"] = col("ID").astype(str).str.strip()
    df["industry2"] = pd.to_numeric(col("INDUSTRY2"), errors="coerce").astype("Int64")  # KSIC 2-digit [item_map INDUSTRY2, register]
    df["section"] = df["industry2"].map(section_from_div)
    if "INDUSTRY1" in items:  # services waves carry a register section variable; cross-check
        reg = col("INDUSTRY1")
        reg_letter = reg.map(S2023_SECTION) if wave == "2023S" else reg.astype(str).str.strip()
        df["section_register"] = reg_letter
    sz = pd.to_numeric(col("SIZECLASS"), errors="coerce")
    # size bands harmonised from the codebook value labels read in Task 2:
    #   2022M/2024M: 1 10~49 | 2 50~99 | 3 100~299 | 4 300~499 | 5 500+          [item_map SIZECLASS values]
    #   2023S:       1 10~29 | 2 30~49 | 3 50~99 | 4 100~299 | 5 300~499 | 6 500+ [item_map SIZECLASS values]
    #   2025S:       2 10~29 | 3 30~49 | 4 50~99 | 5 100~299 | 6 300~499 | 7 500+ [item_map SIZECLASS values; 1 = 5~9 absent]
    if wave in ("2022M", "2024M"):
        band = sz
    elif wave == "2023S":
        band = sz.map({1: 1, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5})
    else:
        band = sz.map({1: np.nan, 2: 1, 3: 1, 4: 2, 5: 3, 6: 4, 7: 5})
    df["size_band"] = band.astype("float")  # 1 10-49, 2 50-99, 3 100-299, 4 300-499, 5 500+
    fy = pd.to_numeric(col("FOUNDYEAR"), errors="coerce")
    fy = fy.where(fy >= FOUNDYEAR_MIN)
    df["found_year"] = fy
    df["firm_age"] = Y2[wave] - fy  # [item_map FOUNDYEAR; reference year of the wave]
    # region harmonised to province names via the codebook labels [item_map REGION values]
    lm = label_map(items["REGION"])
    regraw = col("REGION")
    if regraw.dtype == object and regraw.astype(str).str.contains(r"\.").any():
        regcode = pd.to_numeric(regraw.astype(str).str.extract(r"^\s*(\d+)")[0], errors="coerce")
    else:
        regcode = pd.to_numeric(regraw, errors="coerce")
    df["region"] = regcode.map(lm)
    df["weight"] = pd.to_numeric(col("WEIGHT"), errors="coerce")  # [item_map WEIGHT: 표본가중치*응답률가중치 (2023S codebook)]

    # ---- filters from the questionnaire routing (item_map 'filter' fields)
    ia_any = (df[[f"IA{k}" for k in range(1, 7)]] == 1).any(axis=1)  # 문11 ①~⑥ any yes -> innovation-active [item_map IA1..IA6 filter]
    df["innov_active"] = ia_any.astype(int)
    pi_any = (df[["PI1", "PI2"]] == 1).any(axis=1)  # 문5 any yes -> product innovator [item_map PI1/PI2 filter]
    df["product_innovator"] = pi_any.astype(int)
    for cid in ("MF1", "MF2", "SHARE1", "SHARE2", "SHARE3"):  # 문6/문7 asked only of product innovators
        df.loc[~pi_any, cid] = np.nan
    for cid in ("RDEXP", "NONRDEXP", "COOP1", "COOP2", "COOP3"):  # 문12/문14 asked only of innovation-active firms
        df.loc[~ia_any, cid] = np.nan
    df.loc[df["IA4"] != 1, "RDCYCLE"] = np.nan  # 문11 ④-1 only if ④ yes

    # ---- outcomes (constructs from item_map 'constructs')
    df["quit_any"] = np.where(ia_any, (df["IA3"] == 1).astype(float), np.nan)           # construct quit_any
    df["exit_strict"] = np.where(ia_any, ((df["IA3"] == 1) & (df["IA1"] == 0)).astype(float), np.nan)  # construct exit_strict
    df["exit_full"] = np.where(ia_any, ((df["IA3"] == 1) & (df["IA1"] == 0) & (df["IA2"] == 0)).astype(float), np.nan)  # construct exit_full
    df["preempt_strategy"] = df["PROT8"]                                                   # construct preempt_strategy (all firms)
    df["market_first"] = df["MF1"]                                                         # construct market_first (product innovators)
    df["sales_share_new_to_market"] = df["SHARE1"]                                         # construct sales_share_new_to_market

    # ---- treatments / conditions (printed 0-5 scale; 0 = does not apply) [item_map ME1..ME8]
    df["entry_threat"] = df["ME4"]; df["rival_unpredictability"] = df["ME5"]; df["substitutability"] = df["ME3"]
    df["foreign_competition"] = df["ME7"]; df["obsolescence"] = df["ME1"]; df["tech_uncertainty"] = df["ME2"]
    df["placebo_demand"] = df["ME6"]; df["placebo_price"] = df["ME8"]

    # ---- technology-gap proxies
    df["rd_staff_share"] = df["RDSTAFF"]                                                   # construct rd_staff_share (%, all firms)
    sales = df["SALES"].where(df["SALES"] > 0)
    df["rd_intensity"] = np.where(ia_any, df["RDEXP"] / sales, np.nan)                    # construct rd_intensity (innovation-active, sales>0)
    exports = df["EXPORTS"]
    if wave == "2023S":
        # 2023S stores exports only for exporters (202 positive, 0 zeros, 3,798 blank) whereas 2025S (same services form) stores
        # 3,845 explicit zeros; the blank is therefore read as 'no exports'. Flagged so robustness can drop the wave. [scan 2026-11-09]
        exports = exports.fillna(0.0)
        df["exports_blank_as_zero"] = 1
    else:
        df["exports_blank_as_zero"] = 0
    df["export_share"] = exports / sales                                                    # construct export_share
    df["masters_share"] = df["MASTERS"]
    df["cert_venture"] = df["CERT1"].notna().astype(int)                                   # tick columns [item_map CERT1..]
    df["cert_rd_institute"] = df["CERT2"].notna().astype(int)
    df["cert_innobiz"] = df["CERT3"].notna().astype(int)
    df["group_affiliate"] = df["FORM"]                                                     # 1 independent / 2 domestic group / 3 foreign group
    df["legal_size"] = df["LEGALSIZE"]
    df["listed"] = np.where(df["LISTED"].isna(), np.nan, (df["LISTED"].isin([1, 2, 3])).astype(float))
    df["portfolio_breadth"] = (df[["IA1", "IA2", "IA4", "IA5", "IA6"]] == 1).sum(axis=1).where(ia_any)  # construct portfolio_breadth
    df["rd_continuous"] = np.where(df["RDCYCLE"].isna(), np.nan, (df["RDCYCLE"] == 1).astype(float))
    df["coop_rd"] = df["COOP1"]
    df["funding_public_attempt"] = ((df["FUND7"] >= 1) | (df["FUND8"] >= 1)).astype(float).where(df["FUND7"].notna() | df["FUND8"].notna())
    df["funding_bank_attempt"] = (df["FUND3"] >= 1).astype(float).where(df["FUND3"].notna())
    df["hamp_competition"] = df["HAMP13"]; df["hamp_weak_competition"] = df["HAMP16"]; df["hamp_demand_uncertainty"] = df["HAMP12"]
    df["employees"] = df["EMP"]
    df["female_share"] = df["FEMALE"]
    df["log_employees"] = np.log(df["EMP"].where(df["EMP"] > 0))
    df["log_sales"] = np.log(sales)
    return df, n


def add_gap_ranks(panel):
    """Within industry2 x wave percentile rank of the R&D-staff share (main gap proxy) and terciles.
    Ties (many zeros) get the average rank; terciles use the rank so that the zero mass stays in the bottom group."""
    g = panel.groupby(["wave", "industry2"], dropna=False)["rd_staff_share"]
    panel["gap_rank"] = g.rank(pct=True, method="average")
    panel["gap_tercile"] = pd.cut(panel["gap_rank"], [0, 1 / 3, 2 / 3, 1.0001], labels=[1, 2, 3], include_lowest=True).astype("float")
    panel["cluster_industry_wave"] = panel["wave"] + "_" + panel["industry2"].astype(str)
    return panel


def add_gate_a_variables(panel):
    """Gate A decisions (user, 2026-11-09): 1a market_first used only in manufacturing waves; 2a three-group gap;
    3a response-propensity adjustment of the perceived-competition items. All inputs are treatment/outcome columns
    taken separately; nothing here combines an outcome with a treatment."""
    # 1a — secondary preemption outcome restricted to manufacturing (services waves have 10 and 15 events; see results/02_marginals.json)
    panel["market_first_main"] = panel["market_first"].where(panel["sector"] == "manufacturing")
    # 2a — gap3: 0 = no dedicated R&D staff (share == 0, the 'laggard' mass);
    #            1 = positive share at or below the median of POSITIVE shares in the same industry2 x wave cell;
    #            2 = above that median ('leader-like').
    #       Cells with fewer than GAP_MIN_POS positive shares borrow the median of positive shares of the same KSIC section x wave,
    #       and if that is still too small, of the wave. The borrowed level is recorded in gap3_median_source.
    GAP_MIN_POS = 10
    pos = panel["rd_staff_share"] > 0
    med_cell = panel[pos].groupby(["wave", "industry2"])["rd_staff_share"].agg(["median", "size"]).rename(columns={"median": "m_cell", "size": "n_cell"})
    med_sec = panel[pos].groupby(["wave", "section"])["rd_staff_share"].agg(["median", "size"]).rename(columns={"median": "m_sec", "size": "n_sec"})
    med_wave = panel[pos].groupby("wave")["rd_staff_share"].median().rename("m_wave")
    panel = panel.merge(med_cell, left_on=["wave", "industry2"], right_index=True, how="left")
    panel = panel.merge(med_sec, left_on=["wave", "section"], right_index=True, how="left")
    panel = panel.merge(med_wave, left_on="wave", right_index=True, how="left")
    use_cell = panel["n_cell"].fillna(0) >= GAP_MIN_POS
    use_sec = (~use_cell) & (panel["n_sec"].fillna(0) >= GAP_MIN_POS)
    panel["gap3_median"] = np.where(use_cell, panel["m_cell"], np.where(use_sec, panel["m_sec"], panel["m_wave"]))
    panel["gap3_median_source"] = np.where(use_cell, "industry2", np.where(use_sec, "section", "wave"))
    share = panel["rd_staff_share"]
    panel["gap3"] = np.where(share.isna(), np.nan, np.where(share == 0, 0, np.where(share <= panel["gap3_median"], 1, 2))).astype(float)
    panel = panel.drop(columns=["m_cell", "n_cell", "m_sec", "n_sec", "m_wave"])
    # 3a — response propensity: mean of the eight market-environment items (printed 0-5) for respondents with all eight answered,
    #       and the within-wave residual of ME4 (entry threat) and ME5 (rival unpredictability) on the other seven items.
    me_cols = [f"ME{k}" for k in range(1, 9)]
    allme = panel[me_cols].notna().all(axis=1)
    panel["me_mean8"] = panel[me_cols].mean(axis=1).where(allme)
    for target, name in (("ME4", "entry_threat_resid"), ("ME5", "rival_unpredictability_resid")):
        others = [c for c in me_cols if c != target]
        resid = pd.Series(np.nan, index=panel.index)
        for w, d in panel[allme].groupby("wave"):
            X = np.column_stack([np.ones(len(d))] + [d[c].values for c in others])
            y = d[target].values
            beta, *_ = np.linalg.lstsq(X, y, rcond=None)
            resid.loc[d.index] = y - X @ beta
        panel[name] = resid
    return panel


def summary_no_crosstab(panel):
    """Marginal summaries only. Refuses to emit anything that pairs an outcome with a treatment."""
    out = {}
    for wave, d in panel.groupby("wave"):
        w = {"n": int(len(d)), "n_innov_active": int(d["innov_active"].sum()), "n_product_innovator": int(d["product_innovator"].sum()),
             "columns": {}}
        for c in d.columns:
            if c in ("wave", "sector", "firm_id", "region", "section", "section_register", "cluster_industry_wave", "gap3_median_source"):
                continue
            s = pd.to_numeric(d[c], errors="coerce")
            info = {"n_nonmissing": int(s.notna().sum()), "n_missing": int(s.isna().sum())}
            if s.notna().any():
                if s.dropna().nunique() <= 8:
                    info["value_counts"] = {str(k): int(v) for k, v in s.value_counts(dropna=True).sort_index().items()}
                else:
                    info.update({"min": float(s.min()), "p50": float(s.median()), "max": float(s.max())})
            w["columns"][c] = info
        if "section_register" in d:
            w["section_check"] = {"n_mismatch": int((d["section"] != d["section_register"]).sum()), "n": int(len(d))}
        w["industry2_counts"] = {str(k): int(v) for k, v in d["industry2"].value_counts().sort_index().items()}
        w["gap3_median_source_counts"] = {str(k): int(v) for k, v in d["gap3_median_source"].value_counts().items()}
        w["gap3_counts"] = {str(k): int(v) for k, v in d["gap3"].value_counts().sort_index().items()}
        w["weight"] = {"min": float(d["weight"].min()), "max": float(d["weight"].max()), "sum": float(d["weight"].sum())}
        out[wave] = w
    # embargo guard: the summary must not contain any key that names both an outcome and a treatment
    txt = json.dumps(out)
    for o in OUTCOME_COLS:
        for t in TREATMENT_COLS:
            assert f"{o}_x_{t}" not in txt and f"{t}_x_{o}" not in txt, "embargo violated"
    return out


def main():
    t0 = time.time()
    frames, ns = [], {}
    for w in WAVE_ORDER:
        df, n = build_wave(w)
        frames.append(df); ns[w] = n
        print(f"[{w}] rows={n} cols={df.shape[1]}")
    panel = pd.concat(frames, ignore_index=True)
    panel = add_gap_ranks(panel)
    panel = add_gate_a_variables(panel)
    os.makedirs(os.path.dirname(OUT_PARQUET), exist_ok=True)
    panel.to_parquet(OUT_PARQUET, index=False)
    summ = {"built": time.strftime("%Y-%m-%d %H:%M %Z"), "embargo": "no outcome x treatment statistic computed (gate C pending)",
            "rows_per_wave": ns, "n_total": int(len(panel)), "n_columns": int(panel.shape[1]),
            "sentinels_treated_as_missing": {f"{k[0]}:{k[1]}": v for k, v in SENTINELS.items()},
            "founding_year_min_accepted": FOUNDYEAR_MIN,
            "waves": summary_no_crosstab(panel), "seconds": round(time.time() - t0, 1)}
    os.makedirs(os.path.dirname(OUT_SUMMARY), exist_ok=True)
    json.dump(summ, open(OUT_SUMMARY, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"panel {panel.shape} -> {OUT_PARQUET}; summary -> {OUT_SUMMARY}")


if __name__ == "__main__":
    main()
