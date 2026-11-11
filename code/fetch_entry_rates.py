#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 6a — objective entry indicator: KSIC 2-digit × year firm birth rate from Statistics Korea's
기업생멸행정통계 (Business Demography Statistics), KOSIS table DT_6BD1101
'시도별 산업중분류별 기업 수(활동/신생/소멸)' (11차 개정, 2011~), 전국 (C1 = '00') rows.

Interface facts read from the API response itself on 2026-11-10 (not assumed):
  ITM_ID T01 = 활동 (active firms), T02 = 신생 (births), T04 = 신생률 (birth rate, %), C2 = KSIC 2-digit division code
  (string, '0' = 전체), PRD_SE = 'Y', PRD_DE = calendar year. The official rate T04 is compared with the ratio
  T02/T01 × 100 computed here as a two-route check (reported in provenance; any |diff| > 0.05 pp is listed).

Outputs:
  data/entry_rates_industry_year.csv      (year, ksic2, active, births, birth_rate_official, birth_rate_computed)
  data/provenance_entry_rates.json         (URL template, table id, fetch time, item definitions as returned, coverage)
Usage: python code/fetch_entry_rates.py  (requires KOSIS api_key in api_keys.ini; the key is never printed)
"""
import configparser
import json
import os
import time
import urllib.parse
import urllib.request

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_CSV = os.path.join(ROOT, "data", "entry_rates_industry_year.csv")
OUT_PROV = os.path.join(ROOT, "data", "provenance_entry_rates.json")
TBL = "DT_6BD1101"
ORG = "101"
YEARS = list(range(2011, 2026))


def api_key():
    cfg = configparser.ConfigParser()
    cfg.read("/Users/jihwanw/PhD/code/api_info/api_keys.ini")
    return cfg["kosis"]["api_key"]


def fetch_year(key, year):
    url = ("https://kosis.kr/openapi/Param/statisticsParameterData.do?method=getList"
           f"&apiKey={key}&itmId=ALL&objL1=00&objL2=ALL&objL3=&objL4=&objL5=&objL6=&objL7=&objL8="
           f"&format=json&jsonVD=Y&prdSe=Y&startPrdDe={year}&endPrdDe={year}&orgId={ORG}&tblId={TBL}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.loads(r.read().decode("utf-8"))
    if isinstance(d, dict):  # KOSIS error object
        return None, d
    return d, None


def main():
    key = api_key()
    rows, errors, raw_items = [], {}, {}
    for y in YEARS:
        d, err = fetch_year(key, y)
        if err:
            errors[str(y)] = err
            continue
        for x in d:
            raw_items[(x["ITM_ID"], x["ITM_NM"])] = x.get("UNIT_NM")
            rows.append({"year": int(x["PRD_DE"]), "region": x["C1_NM"], "ksic2": x["C2"], "ksic2_name": x["C2_NM"],
                         "item": x["ITM_ID"], "item_name": x["ITM_NM"], "unit": x.get("UNIT_NM"), "value": x["DT"]})
        time.sleep(0.4)
    df = pd.DataFrame(rows)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    wide = df.pivot_table(index=["year", "ksic2", "ksic2_name"], columns="item", values="value", aggfunc="first").reset_index()
    wide = wide.rename(columns={"T01": "active", "T02": "births", "T04": "birth_rate_official"})
    wide["birth_rate_computed"] = 100.0 * wide["births"] / wide["active"]
    wide["abs_diff_pp"] = (wide["birth_rate_official"] - wide["birth_rate_computed"]).abs()
    wide = wide.sort_values(["ksic2", "year"])
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    wide.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    # provenance + checks
    kis_mfg = [str(c) for c in range(10, 35)]
    kis_svc = ["45", "46", "47", "49", "50", "51", "52", "55", "56", "58", "59", "60", "61", "62", "63", "64", "65", "66", "68", "70", "71", "72", "73", "74", "75", "76", "85", "86", "87", "90", "91", "95", "96"]
    have = set(wide["ksic2"].astype(str))
    prov = {
        "fetched": time.strftime("%Y-%m-%d %H:%M %Z"),
        "source": "통계청, 기업생멸행정통계 (Business Demography Statistics), KOSIS OpenAPI",
        "table": {"orgId": ORG, "tblId": TBL, "name": "시도별 산업중분류별 기업 수(활동/신생/소멸)", "classification_revision": "KSIC 11차 개정(2011~) list J2_6_001_004"},
        "request_template": "https://kosis.kr/openapi/Param/statisticsParameterData.do?method=getList&apiKey=<KEY>&itmId=ALL&objL1=00&objL2=ALL&format=json&jsonVD=Y&prdSe=Y&startPrdDe=<Y>&endPrdDe=<Y>&orgId=101&tblId=DT_6BD1101",
        "items_as_returned": {f"{k[0]} {k[1]}": v for k, v in raw_items.items()},
        "region_filter": "objL1=00 (전국)",
        "years_requested": YEARS, "years_returned": sorted(wide["year"].unique().tolist()), "errors": errors,
        "n_ksic2_codes": int(wide["ksic2"].nunique()),
        "coverage_kis_manufacturing_codes_10_34": {"missing": sorted(set(kis_mfg) - have)},
        "coverage_kis_services_codes": {"missing": sorted(set(kis_svc) - have)},
        "two_route_check_official_vs_computed_rate": {"max_abs_diff_pp": float(wide["abs_diff_pp"].max()), "n_rows_diff_gt_0.05pp": int((wide["abs_diff_pp"] > 0.05).sum())},
        "definition_note": "birth_rate_official = KOSIS item T04 '신생률' as published (unit as returned); birth_rate_computed = 100*T02/T01. The published definition of 신생기업/활동기업 is Statistics Korea's (기업생멸행정통계 설명자료) — to be quoted from the official explanatory document in the manuscript; not restated here from memory.",
    }
    json.dump(prov, open(OUT_PROV, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: prov[k] for k in ("years_returned", "errors", "n_ksic2_codes", "coverage_kis_manufacturing_codes_10_34", "coverage_kis_services_codes", "two_route_check_official_vs_computed_rate", "items_as_returned")}, ensure_ascii=False, indent=1))
    print("wrote", OUT_CSV)


if __name__ == "__main__":
    main()
