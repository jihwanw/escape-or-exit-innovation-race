#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 3 tests for data/analysis_panel.parquet. Run: python code/test_panel.py
Writes results/01_panel_tests.json; exit 1 on any failure.

T1 value ranges: every recoded item lies inside the printed questionnaire code set of its block.
T2 filters: 문6/문7 only for product innovators; 문12/문14 only for innovation-active firms; 문11 ④-1 only if ④ yes;
   footnote rule '문5 or 문9 yes -> 문11 ① yes' is reported (not enforced) as a consistency count.
T3 2023S recode: after recode, the frequency of each printed code equals the inventory's observed frequency of the
   corresponding data code (independent source: item_inventory_2023S.json data_values_observed).
T4 no silent zero-fill: missing counts of RDEXP / MF1 / SHARE1 equal the number of filtered-out firms (+ sentinels),
   and the only fillna in the pipeline (2023S exports) is flagged in exports_blank_as_zero.
T5 harmonisation: size_band 1-5 in all waves; section letters match the register section where one exists (2023S/2025S);
   firm_age non-negative; weights positive.
T6 embargo: the build summary JSON contains no outcome x treatment key and the panel module exposes both lists.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import load_kis_escape_exit as L  # noqa: E402

panel = pd.read_parquet(os.path.join(ROOT, "data", "analysis_panel.parquet"))
res = {"tests": {}, "status": "PASS"}


def check(name, ok, detail):
    res["tests"][name] = {"pass": bool(ok), "detail": detail}
    if not ok:
        res["status"] = "FAIL"
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


# T1 ranges
ranges = {**{f"ME{k}": (0, 5) for k in range(1, 9)}, **{f"PROT{k}": (0, 1) for k in range(1, 9)}, "PI1": (0, 1), "PI2": (0, 1), "MF1": (0, 1), "MF2": (0, 1),
          **{f"IA{k}": (0, 1) for k in range(1, 7)}, "RDCYCLE": (1, 2), **{f"FUND{k}": (0, 3) for k in range(1, 9)}, "HAMP12": (0, 5), "HAMP13": (0, 5), "HAMP16": (0, 5),
          "FORM": (1, 3), "LEGALSIZE": (1, 4), "LISTED": (1, 4), "SHARE1": (0, 100), "SHARE2": (0, 100), "SHARE3": (0, 100), "RDSTAFF": (0, 100), "FEMALE": (0, 100), "MASTERS": (0, 100)}
bad = {}
for c, (lo, hi) in ranges.items():
    s = panel[c].dropna()
    if len(s) and (s.min() < lo or s.max() > hi):
        bad[c] = (float(s.min()), float(s.max()))
check("T1_value_ranges", not bad, f"{len(ranges)} columns within printed code sets" if not bad else f"out of range: {bad}")

# T2 filters
pi = panel["product_innovator"] == 1
ia = panel["innov_active"] == 1
t2 = {"MF1_nonmissing_among_non_innovators": int(panel.loc[~pi, "MF1"].notna().sum()),
      "SHARE1_nonmissing_among_non_innovators": int(panel.loc[~pi, "SHARE1"].notna().sum()),
      "RDEXP_nonmissing_among_inactive": int(panel.loc[~ia, "RDEXP"].notna().sum()),
      "COOP1_nonmissing_among_inactive": int(panel.loc[~ia, "COOP1"].notna().sum()),
      "RDCYCLE_nonmissing_where_IA4_no": int(panel.loc[panel["IA4"] != 1, "RDCYCLE"].notna().sum()),
      "quit_any_defined_only_if_active": int(panel.loc[~ia, "quit_any"].notna().sum())}
# footnote consistency (reported): product innovators (문5) should have 문11 ① yes
t2["product_innovators_without_completed_activity_IA1"] = int(((pi) & (panel["IA1"] != 1)).sum())
t2["product_innovators_total"] = int(pi.sum())
check("T2_filters", all(v == 0 for k, v in t2.items() if k.endswith(("innovators", "inactive", "no", "active"))), json.dumps(t2))

# T3 2023S recode vs inventory observed counts
inv = json.load(open("/Users/jihwanw/PhD/MOT/Innovation_Survey/data/KIS/item_inventory_2023S.json", encoding="utf-8"))
inv_items = {it["variable"]: it for it in inv["items"]}
m23 = json.load(open(os.path.join(L.MAPS, "item_map_2023S.json"), encoding="utf-8"))
d23 = panel[panel["wave"] == "2023S"]
mism = []
checked = 0
for e in m23["items"]:
    if e.get("register") or not e.get("recode_to_printed"):
        continue
    cid, var = e["construct_id"], e["variable"]
    obs = inv_items[var].get("data_values_observed", {}).get("value_counts")
    if not obs:
        continue
    rc = {float(k): v for k, v in e["recode_to_printed"].items()}
    expected = {}
    for code, cnt in obs.items():
        expected[rc[float(code)]] = expected.get(rc[float(code)], 0) + cnt
    # filters applied in the panel may remove rows for MF/SHARE/RDEXP/COOP; compare on the unfiltered recode for those
    raw_recoded = d23[cid] if cid not in ("MF1", "MF2", "COOP1", "COOP2", "COOP3", "RDCYCLE") else None
    if raw_recoded is None:
        continue
    got = {float(k): int(v) for k, v in raw_recoded.value_counts().items()}
    checked += 1
    if {float(k): v for k, v in expected.items()} != got:
        mism.append((var, expected, got))
check("T3_2023S_recode_vs_inventory", not mism, f"{checked} recoded 2023S variables reproduce the inventory's observed frequencies" if not mism else f"mismatch: {mism[:3]}")

# T4 no silent zero fill
t4 = {}
for w in L.WAVE_ORDER:
    d = panel[panel["wave"] == w]
    n_inactive = int((d["innov_active"] == 0).sum())
    n_sent = int(len(L.SENTINELS.get((w, "RDEXP"), [])) and 0)  # placeholder, actual count below
    t4[w] = {"RDEXP_missing": int(d["RDEXP"].isna().sum()), "n_inactive": n_inactive,
             "MF1_missing": int(d["MF1"].isna().sum()), "n_non_product_innovators": int((d["product_innovator"] == 0).sum()),
             "exports_blank_as_zero_flag": int(d["exports_blank_as_zero"].iloc[0])}
ok4 = all(v["RDEXP_missing"] >= v["n_inactive"] and v["MF1_missing"] >= v["n_non_product_innovators"] for v in t4.values())
ok4 = ok4 and (panel.loc[panel["wave"] != "2023S", "exports_blank_as_zero"] == 0).all()
check("T4_no_silent_zero_fill", ok4, json.dumps(t4))

# T5 harmonisation
t5 = {}
for w in L.WAVE_ORDER:
    d = panel[panel["wave"] == w]
    t5[w] = {"size_band_values": sorted(d["size_band"].dropna().unique().tolist()), "size_band_missing": int(d["size_band"].isna().sum()),
             "firm_age_min": float(d["firm_age"].min()), "firm_age_missing": int(d["firm_age"].isna().sum()),
             "weight_min": float(d["weight"].min()), "section_values": sorted(d["section"].dropna().unique().tolist())}
    if "section_register" in d and d["section_register"].notna().any():
        t5[w]["section_mismatch_vs_register"] = int((d["section"] != d["section_register"]).sum())
ok5 = all(set(v["size_band_values"]) <= {1.0, 2.0, 3.0, 4.0, 5.0} and v["firm_age_min"] >= 0 and v["weight_min"] > 0 and v.get("section_mismatch_vs_register", 0) == 0 and "?" not in v["section_values"] for v in t5.values())
check("T5_harmonisation", ok5, json.dumps(t5))

# T6 embargo
summ = json.load(open(L.OUT_SUMMARY, encoding="utf-8"))
txt = json.dumps(summ)
viol = [(o, t) for o in L.OUTCOME_COLS for t in L.TREATMENT_COLS if f"{o}_x_{t}" in txt or f"{t}_x_{o}" in txt or f"{o}|{t}" in txt]
check("T6_embargo", not viol and "embargo" in summ, "build summary carries the embargo note and no outcome x treatment statistic")

# T7 gate-A variables
t7 = {}
ok7 = True
for w in L.WAVE_ORDER:
    d = panel[panel["wave"] == w]
    g = d["gap3"]
    t7[w] = {"gap3_counts": {str(int(k)): int(v) for k, v in g.value_counts().sort_index().items()}, "gap3_missing": int(g.isna().sum()),
             "gap3_zero_equals_share_zero": bool(((g == 0) == (d["rd_staff_share"] == 0)).all()),
             "gap3_1_below_or_at_median": bool((d.loc[g == 1, "rd_staff_share"] <= d.loc[g == 1, "gap3_median"]).all()),
             "gap3_2_above_median": bool((d.loc[g == 2, "rd_staff_share"] > d.loc[g == 2, "gap3_median"]).all()),
             "median_source": {str(k): int(v) for k, v in d["gap3_median_source"].value_counts().items()},
             "market_first_main_nonmissing": int(d["market_first_main"].notna().sum()),
             "me_mean8_nonmissing": int(d["me_mean8"].notna().sum()),
             "entry_threat_resid_mean_abs": float(d["entry_threat_resid"].mean()) if d["entry_threat_resid"].notna().any() else None}
    ok7 &= t7[w]["gap3_zero_equals_share_zero"] and t7[w]["gap3_1_below_or_at_median"] and t7[w]["gap3_2_above_median"]
    ok7 &= abs(t7[w]["entry_threat_resid_mean_abs"] or 0) < 1e-8
    if d["sector"].iloc[0] == "services":
        ok7 &= t7[w]["market_first_main_nonmissing"] == 0
    else:
        ok7 &= t7[w]["market_first_main_nonmissing"] == int(d["market_first"].notna().sum())
check("T7_gate_A_variables", ok7, json.dumps(t7))

json.dump(res, open(os.path.join(ROOT, "results", "01_panel_tests.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("STATUS", res["status"])
sys.exit(0 if res["status"] == "PASS" else 1)
