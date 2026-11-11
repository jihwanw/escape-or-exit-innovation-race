#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 2 — build the per-wave item maps for Escape or Exit from THREE sources only:

  (1) the full-read item inventory of the wave (codebook row text + value labels),
  (2) the official questionnaire PDF of the wave (pdftotext output; every wording string in
      questionnaire_text.py must occur in that wave's text or the build FAILS),
  (3) the distributed data file (observed value distribution of every mapped column).

Nothing is inferred from a variable name, a block position, or another wave. The recode
from data codes to the printed questionnaire codes is DERIVED by comparing the observed
value set with the printed code set (identity / +1 shift / 1-2 yes-no / 9998 sentinel);
if no rule fits, the variable is marked UNRESOLVED and the build fails.

Outputs
  item_maps/item_map_<wave>.json          (audit format: items[], constructs{})
  item_maps/item_map_escape_exit.json     (harmonised construct -> wave variable table)
  item_maps/questionnaire_text_<wave>.txt (pdftotext -layout output used for verification)
  docs/VARIABLE_TABLE.md                  (generated Table F.1-style variable description)
  results/02_item_map_build.json          (build log: per-wave checks, recodes, filters)
"""
import json
import os
import re
import subprocess
import sys
from collections import Counter

import openpyxl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from questionnaire_text import BLOCKS  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KIS = "/Users/jihwanw/PhD/MOT/Innovation_Survey/data/KIS"
RAW = "/Users/jihwanw/PhD/MOT/Innovation_Survey/data/00_00_한국기업혁신조사 마이크로데이터 및 설문지"
OUT_MAPS = os.path.join(ROOT, "item_maps")
OUT_LOG = os.path.join(ROOT, "results", "02_item_map_build.json")
OUT_TABLE = os.path.join(ROOT, "docs", "VARIABLE_TABLE.md")

WAVES = {
    "2022M": dict(sector="manufacturing", y0=2019, y2=2021,
                  data=f"{KIS}/KIS_2022_배포용(제조업).xlsx", sheet="데이터", header_row=1,
                  codebook=f"{KIS}/KIS_2022_배포용(제조업).xlsx", cb_cols=("변수명", "변수설명"),
                  inventory=f"{KIS}/item_inventory_2022M.json",
                  questionnaire=f"{RAW}/혁신조사 2022(제조업) 설문지.pdf", pages=18),
    "2024M": dict(sector="manufacturing", y0=2021, y2=2023,
                  data=f"{KIS}/KIS_2024_배포용(제조업).xlsx", sheet="마이크로데이터", header_row=1,
                  codebook=f"{KIS}/KIS_2024_배포용(제조업).xlsx", cb_cols=("변수명", "변수설명"),
                  inventory=f"{KIS}/item_inventory_2024M.json",
                  questionnaire=f"{RAW}/혁신조사 2024(제조업) 설문지.pdf", pages=12),
    "2023S": dict(sector="services", y0=2020, y2=2022,
                  data=f"{KIS}/KIS_2023_배포용(서비스업).xlsx", sheet="제출용", header_row=2,
                  codebook=f"{KIS}/KIS_2023_배포용(서비스업).xlsx", cb_cols=("변수명", "변수설명"),
                  inventory=f"{KIS}/item_inventory_2023S.json",
                  questionnaire=f"{RAW}/혁신조사 2023(서비스업) 설문지.pdf", pages=15),
    "2025S": dict(sector="services", y0=2022, y2=2024,
                  data=f"{RAW}/KIS_2025_제공용(서비스업).xlsx", sheet="DATA", header_row=1,
                  codebook=f"{RAW}/KIS_2025_제공용(서비스업).xlsx", cb_cols=("변수명", "변수설명"),
                  inventory=f"{KIS}/item_inventory_2025S.json",
                  questionnaire=f"{RAW}/혁신조사 2025(서비스업) 설문지.pdf", pages=14),
}

# construct id -> (block, item key, {wave: variable})  — variable names come from the inventories (read above)
def _w(m22, m24, s23, s25):
    return {"2022M": m22, "2024M": m24, "2023S": s23, "2025S": s25}

ITEMS = {}
for k in range(1, 9):
    ITEMS[f"ME{k}"] = ("문1-2", k, _w(f"문1_2_{k}", f"Q1K2_{k}", f"문1_2_{k}", f"Q1K2_{k}"))
    ITEMS[f"PROT{k}"] = ("문2", k, _w(f"문2_{k}", f"Q2_{k}", f"문2_{k}", f"Q2_{k}"))
for k in (1, 2):
    ITEMS[f"PI{k}"] = ("문5", k, _w(f"문5_{k}", f"Q5_{k}", f"문5_{k}", f"Q5_{k}"))
    ITEMS[f"MF{k}"] = ("문6", k, _w(f"문6_{k}", f"Q6_{k}", f"문6_{k}", f"Q6_{k}"))
for k in (1, 2, 3):
    ITEMS[f"SHARE{k}"] = ("문7", k, _w(f"문7_{k}", f"Q7_{k}", f"문7_{k}", f"Q7_{k}"))
for k in range(1, 7):
    ITEMS[f"IA{k}"] = ("문11", k, _w(f"문11_{k}", f"Q11_{k}", f"문11_{k}", f"Q11_{k}"))
ITEMS["RDCYCLE"] = ("문11-4-1", 1, _w("문11_4_01", "Q11K4K1", "문11_4_01", "Q11K4K1"))
ITEMS["RDEXP"] = ("문12", 1, _w("문12_1_1", "Q12K1_1", "문12_1_1", "Q12K1_1"))
ITEMS["NONRDEXP"] = ("문12", 2, _w("문12_1_2", "Q12K1_2", "문12_1_2", "Q12K1_2"))
for k in (1, 2, 3):
    ITEMS[f"COOP{k}"] = ("문14", k, _w(f"문14_{k}", f"Q14_{k}", f"문14_{k}", f"Q14_{k}"))
for k in range(1, 9):
    ITEMS[f"FUND{k}"] = ("문17", k, _w(f"문17_{k}", f"Q17_{k}", f"문17_{k}", f"Q17_{k}"))
for k in (12, 13, 16):
    ITEMS[f"HAMP{k}"] = ("문19", k, _w(f"문19_{k}", f"Q19_{k}", f"문19_{k}", f"Q19_{k}"))
ITEMS["FORM"] = ("문31", "form", _w("문31_1", "Q31K1", "문31_1", "Q31K1"))
ITEMS["LEGALSIZE"] = ("문31", "legal_size", _w("문31_2", "Q31K2", "문31_2", "Q31K2"))
for k in range(1, 9):
    ITEMS[f"CERT{k}"] = ("문31", f"cert{k}", _w(f"문31_3_{k}", f"Q31K3_{k}", f"문31_3_{k}", f"Q31K3_{k}"))
ITEMS["CERT9"] = ("문31", "cert9", _w("문31_3_9", "Q31K3_9998", "문31_3_9", "Q31K3_9998"))
ITEMS["LISTED"] = ("문31", "listed", _w("문31_4", "Q31K4", "문31_4", "Q31K4"))
ITEMS["SALES"] = ("문32", "sales", _w("문32_3_1", "Q32_3_1", "문32_3_1", "Q32_3_1"))
ITEMS["EXPORTS"] = ("문32", "exports", _w("문32_3_2", "Q32_3_2", "문32_3_2", "Q32_3_2"))
ITEMS["EMP"] = ("문33", "emp", _w("문33_1_3", "Q33K1_3", "문33_1_3", "Q33K1_3"))
ITEMS["FEMALE"] = ("문33", "female", _w("문33_2_1", "Q33K2_1_1", "문33_2_1", "Q33K2_1_1"))
ITEMS["MASTERS"] = ("문33", "masters", _w("문33_3_1", "Q33K2_1_2", "문33_3_1", "Q33K2_1_2"))
ITEMS["RDSTAFF"] = ("문33", "rd_staff", _w("문33_4_1", "Q33K2_1_3", "문33_4_1", "Q33K2_1_3"))

# register / list variables (no questionnaire item): construct -> {wave: variable}; None = not in that wave
REGISTER = {
    "ID": _w("ID", "2024제조ID", "ID", "응답자 ID"),
    "INDUSTRY2": _w("업종(중분류)", "업종", "업종(중분류)", "BR_GI_MCLS_CD"),
    "INDUSTRY1": _w(None, None, "업종(대분류)", "BR_GI_LCLS_CD"),
    "SIZECLASS": _w("종사자 수\n규모", "종사자규모", "규모(2022년 응답 기준)", "size"),
    "SIZECLASS_SBR": _w(None, None, None, "size_SBR"),
    "SBR_SCALE": _w(None, "법정유형", None, "scale"),
    "FOUNDYEAR": _w("SQ2", "설립연도", "SQ2", "OPBIZ_DE_3"),
    "REGION": _w("SQ4_2", "지역", "SQ4_2", "region"),
    "SALESCLASS": _w("매출액\n규모", None, None, None),
    "WEIGHT": _w("WT1", "WT1", "WT1", "WT1"),
}

CONSTRUCTS = {
    # name: (label_en, item construct ids, rule)
    "quit_any": ("Abandoned or suspended innovation activity (main exit outcome)", ["IA3"] + [f"IA{k}" for k in (1, 2, 4, 5, 6)],
                 "quit_any = 1 if IA3 == yes, 0 if IA3 == no; defined only for firms with any innovation activity (IA1..IA6 any yes); recoded to printed yes=1/no=0 first"),
    "exit_strict": ("Abandoned without any completed activity", ["IA3", "IA1"], "exit_strict = 1 if IA3 == yes and IA1 == no, else 0; same population as quit_any"),
    "exit_full": ("Abandoned with neither completed nor ongoing activity", ["IA3", "IA1", "IA2"], "exit_full = 1 if IA3 == yes and IA1 == no and IA2 == no, else 0; same population as quit_any"),
    "preempt_strategy": ("Protected products by entering the market ahead of competitors (lead-time; main preemption outcome)", ["PROT8"], "preempt_strategy = PROT8 recoded yes=1/no=0; all firms"),
    "market_first": ("New-to-market product innovation (secondary preemption outcome)", ["MF1", "PI1", "PI2"],
                     "market_first = MF1 recoded yes=1/no=0 among product innovators (PI1 or PI2 == yes); missing for non-innovators (selection handled separately)"),
    "entry_threat": ("Perceived threat of entry by new competitors", ["ME4"], "ME4 on printed 0-5 scale (0 = does not apply); after wave-specific recode"),
    "rival_unpredictability": ("Competitors' actions are difficult to predict (observation noise proxy)", ["ME5"], "ME5 on printed 0-5 scale"),
    "substitutability": ("Competitor products easily substitute ours", ["ME3"], "ME3 on printed 0-5 scale"),
    "foreign_competition": ("Strong competition from abroad", ["ME7"], "ME7 on printed 0-5 scale"),
    "obsolescence": ("Products become outdated quickly", ["ME1"], "ME1 on printed 0-5 scale"),
    "placebo_demand": ("Placebo: changes in demand difficult to predict", ["ME6"], "ME6 on printed 0-5 scale"),
    "placebo_price": ("Placebo: price increases lead to loss of customers", ["ME8"], "ME8 on printed 0-5 scale"),
    "tech_uncertainty": ("Future technological developments difficult to predict (control)", ["ME2"], "ME2 on printed 0-5 scale"),
    "rd_staff_share": ("Share of dedicated R&D staff among regular employees (main technology-gap proxy)", ["RDSTAFF"], "percentage 0-100 as reported; ranked within industry (2-digit) x wave for the gap tercile"),
    "rd_intensity": ("R&D expenditure / sales (secondary gap proxy, innovation-active firms only)", ["RDEXP", "SALES"], "RDEXP / SALES, both million KRW, reference calendar year; defined only where IA1..IA6 any yes and SALES > 0"),
    "export_share": ("Exports / sales in the reference year", ["EXPORTS", "SALES"], "EXPORTS / SALES; exports missing treated as 0 only where the questionnaire blank means no exports — verified in Task 3 against value distribution, otherwise missing"),
    "masters_share": ("Share of employees with a master's degree or higher", ["MASTERS"], "percentage 0-100 as reported"),
    "cert_venture": ("Venture-firm certification", ["CERT1"], "1 if the multi-response column is ticked (value == item code), else 0"),
    "cert_rd_institute": ("Registered R&D institute / dedicated R&D department", ["CERT2"], "1 if ticked, else 0"),
    "cert_innobiz": ("Inno-Biz certification", ["CERT3"], "1 if ticked, else 0"),
    "group_affiliate": ("Firm type: independent / domestic-group affiliate / foreign-group affiliate", ["FORM"], "categorical 1/2/3 as printed"),
    "legal_size": ("Statutory firm size class", ["LEGALSIZE"], "categorical 1 small / 2 medium / 3 mid-sized / 4 large as printed"),
    "listed": ("Stock-market listing", ["LISTED"], "1 if KOSPI/KOSDAQ/KONEX (codes 1-3), 0 if '해당사항 없음' (code 4 or data sentinel 9998)"),
    "portfolio_breadth": ("Number of innovation-activity types reported (portfolio-size control)", [f"IA{k}" for k in (1, 2, 4, 5, 6)], "count of yes among IA1, IA2, IA4, IA5, IA6 (IA3 excluded because it is the outcome)"),
    "rd_continuous": ("In-house R&D performed continuously (vs occasionally)", ["RDCYCLE", "IA4"], "1 if RDCYCLE == 1, 0 if RDCYCLE == 2; missing where IA4 == no"),
    "coop_rd": ("Cooperated on R&D", ["COOP1"], "recoded yes=1/no=0; innovation-active firms only"),
    "funding_public_attempt": ("Attempted central- or local-government funding", ["FUND7", "FUND8"], "1 if FUND7 or FUND8 on printed scale >= 1 (attempted), else 0"),
    "funding_bank_attempt": ("Attempted bank financing", ["FUND3"], "1 if FUND3 printed >= 1, else 0"),
    "hamp_competition": ("Hampering factor: excessive competition (auxiliary)", ["HAMP13"], "HAMP13 on printed 0-5 scale"),
    "hamp_weak_competition": ("Reason not to innovate: weak competitive pressure (auxiliary)", ["HAMP16"], "HAMP16 on printed 0-5 scale"),
    "hamp_demand_uncertainty": ("Hampering factor: uncertain demand (auxiliary)", ["HAMP12"], "HAMP12 on printed 0-5 scale"),
    "sales_share_new_to_market": ("Sales share of new-to-market products (%)", ["SHARE1", "PI1", "PI2"], "percentage among product innovators"),
    "employees": ("Regular employees in the reference year", ["EMP"], "count as reported"),
    "firm_age": ("Firm age in the reference year", ["FOUNDYEAR"], "y2 - founding year"),
    "female_share": ("Share of women among regular employees (%)", ["FEMALE"], "percentage as reported (control)"),
}


def norm(s):
    return re.sub(r"\s+", "", str(s or ""))


def pdftotext(pdf, out_txt):
    if not os.path.exists(out_txt):
        subprocess.run(["pdftotext", "-layout", pdf, out_txt], check=True)
    return open(out_txt, encoding="utf-8").read()


def load_inventory(path):
    inv = json.load(open(path, encoding="utf-8"))
    items = {}
    for it in inv["items"]:
        items[it["variable"]] = it
    return inv, items


def inv_text(it):
    """Verbatim codebook description; for blank continuation rows (multi-response grids) the
    inventory's transcribed item text is used and the fact is recorded in codebook_note."""
    return it.get("item_text_ko") or it.get("codebook_description") or it.get("item_text") or ""


def inv_values(it):
    return it.get("values") if it.get("values") is not None else (it.get("codebook_values") or [])


def read_codebook_desc(path, cb_cols):
    ws = openpyxl.load_workbook(path, read_only=True)["코드북"]
    rows = list(ws.iter_rows(values_only=True))
    hdr = [str(c).strip() if c is not None else "" for c in rows[0]]
    iv, idesc = hdr.index(cb_cols[0]), hdr.index(cb_cols[1])
    out = {}
    for r in rows[1:]:
        v = r[iv]
        if v is not None and str(v).strip():
            out[str(v).strip()] = str(r[idesc]).strip() if r[idesc] is not None else ""
    return out


def read_data(path, sheet, header_row):
    ws = openpyxl.load_workbook(path, read_only=True)[sheet]
    rows = list(ws.iter_rows(min_row=header_row, values_only=True))
    hdr = [str(c) if c is not None else None for c in rows[0]]
    cols = {}
    for j, h in enumerate(hdr):
        if h is None:
            continue
        cols[h] = [r[j] if j < len(r) else None for r in rows[1:]]
    return cols, len(rows) - 1


def observed(values):
    nonnull = [v for v in values if v is not None and str(v).strip() != ""]
    if not nonnull:
        return {"type": "empty", "n_nonnull": 0}
    try:
        nums = [float(v) for v in nonnull]
    except ValueError:
        c = Counter(str(v) for v in nonnull)
        return {"type": "text", "n_nonnull": len(nonnull), "n_unique": len(c), "examples": [k for k, _ in c.most_common(6)]}
    if len(set(nums)) <= 12 and all(float(x).is_integer() for x in nums):
        c = Counter(int(x) for x in nums)
        return {"type": "coded", "n_nonnull": len(nonnull), "value_counts": {str(k): v for k, v in sorted(c.items())}}
    return {"type": "numeric", "n_nonnull": len(nonnull), "min": min(nums), "max": max(nums), "n_unique": len(set(nums))}


def derive_recode(block, obs, codebook_vals, item_key):
    """Return (data_coding_note, recode_map or None, status). Rules are derived from the
    observed code set vs the printed questionnaire codes; nothing is assumed."""
    printed = BLOCKS[block]["printed_codes"]
    pc = [int(p.split()[0]) for p in printed if re.match(r"^\d+ ", p)]
    if obs["type"] != "coded" or (not pc and block not in ("문31", "문11-4-1")):
        return ("numeric entry (as reported)", None, "numeric")
    vals = sorted(int(k) for k in obs["value_counts"])
    if block == "문31":
        # multi-response tick columns and categorical items
        if str(item_key).startswith("cert"):
            k = int(str(item_key)[4:])
            if vals == [k]:
                return (f"tick column: value {k} when ticked, blank otherwise", {k: 1}, "ok")
            if k == 9 and vals == [9998]:
                return ("tick column: data 9998 = '9. 해당사항 없음'", {9998: 1}, "ok")
            return (f"unexpected codes {vals}", None, "UNRESOLVED")
        if item_key == "form" and set(vals) <= {1, 2, 3}:
            return ("as printed 1/2/3", {v: v for v in vals}, "ok")
        if item_key == "legal_size" and set(vals) <= {1, 2, 3, 4}:
            return ("as printed 1-4", {v: v for v in vals}, "ok")
        if item_key == "listed":
            if set(vals) <= {1, 2, 3, 4}:
                return ("as printed 1-4", {v: v for v in vals}, "ok")
            if set(vals) <= {1, 2, 3, 9998}:
                return ("data 9998 = printed 4 '해당사항 없음'", {1: 1, 2: 2, 3: 3, 9998: 4}, "ok")
        return (f"unexpected codes {vals}", None, "UNRESOLVED")
    if block == "문11-4-1":
        if set(vals) <= {1, 2}:
            return ("as printed 1/2", {v: v for v in vals}, "ok")
        return (f"unexpected codes {vals}", None, "UNRESOLVED")
    if pc == [1, 0]:  # yes/no
        if set(vals) <= {0, 1}:
            return ("as printed: 1 예 / 0 아니오", {1: 1, 0: 0}, "ok")
        if set(vals) <= {1, 2}:
            return ("data 1 예 / 2 아니오 (questionnaire prints 1/0)", {1: 1, 2: 0}, "ok")
        return (f"unexpected codes {vals}", None, "UNRESOLVED")
    if pc:  # ordinal scales starting at 0
        lo, hi = min(pc), max(pc)
        if set(vals) <= set(range(lo, hi + 1)):
            return (f"as printed {lo}-{hi}", {v: v for v in range(lo, hi + 1)}, "ok")
        if set(vals) <= set(range(lo + 1, hi + 2)):
            return (f"data {lo + 1}-{hi + 1} = printed {lo}-{hi} (+1 shift)", {v: v - 1 for v in range(lo + 1, hi + 2)}, "ok")
        return (f"unexpected codes {vals} vs printed {pc}", None, "UNRESOLVED")
    return ("no printed code set", None, "UNRESOLVED")


def main():
    os.makedirs(OUT_MAPS, exist_ok=True)
    os.makedirs(os.path.dirname(OUT_LOG), exist_ok=True)
    log = {"built": __import__("time").strftime("%Y-%m-%d %H:%M %Z"), "waves": {}, "status": "PASS"}
    harmonised = {"_meta": {"project": "Escape or Exit", "built": log["built"],
                            "rule": "Variable meanings come only from the wave's codebook row, the wave's questionnaire wording (verified against the PDF text) and the observed data values. See per-wave item_map_<wave>.json."},
                  "constructs": {}, "register": {}}
    table_rows = []

    for wave, cfg in WAVES.items():
        qtxt_path = os.path.join(OUT_MAPS, f"questionnaire_text_{wave}.txt")
        qtxt = pdftotext(cfg["questionnaire"], qtxt_path)
        qnorm = norm(qtxt)
        inv, inv_items = load_inventory(cfg["inventory"])
        cb_desc = read_codebook_desc(cfg["codebook"], cfg["cb_cols"])
        data, n_rows = read_data(cfg["data"], cfg["sheet"], cfg["header_row"])
        data_norm = {k.strip(): v for k, v in data.items()}
        wlog = {"n_rows": n_rows, "n_data_columns": len(data), "questionnaire_pages": cfg["pages"],
                "wording_checks": [], "unresolved": [], "missing_in_inventory": [], "missing_in_data": [], "codebook_drift": []}
        items_out = []
        fmt = dict(y0=cfg["y0"], y2=cfg["y2"])

        # --- questionnaire items
        for cid, (block, key, wvars) in ITEMS.items():
            var = wvars[wave]
            if var is None:
                continue
            b = BLOCKS[block]
            stem = b["stem"].format(**fmt)
            item_text_q = b["items"][key].format(**fmt)
            # verify wording against THIS wave's questionnaire text
            stem_ok = norm(b["stem_match"].format(**fmt)) in qnorm
            match_str = (b.get("item_match", {}) or {}).get(key, item_text_q)
            item_ok = norm(match_str.format(**fmt)) in qnorm
            wlog["wording_checks"].append({"construct": cid, "variable": var, "stem_found": stem_ok, "item_found": item_ok})
            if not (stem_ok and item_ok):
                log["status"] = "FAIL"
            if var not in inv_items:
                wlog["missing_in_inventory"].append(var); log["status"] = "FAIL"; continue
            it = inv_items[var]
            col = data.get(var) or data_norm.get(var.strip())
            if col is None:
                wlog["missing_in_data"].append(var); log["status"] = "FAIL"; continue
            obs = observed(col)
            coding_note, recode, status = derive_recode(block, obs, inv_values(it), key)
            if status == "UNRESOLVED":
                wlog["unresolved"].append({"variable": var, "note": coding_note}); log["status"] = "FAIL"
            cb_text = inv_text(it)
            drift = var in cb_desc and norm(cb_desc[var]) != "" and norm(cb_desc[var]) != norm(cb_text)
            if drift:
                wlog["codebook_drift"].append({"variable": var, "inventory": cb_text[:60], "codebook_sheet": cb_desc[var][:60]})
            cb_row = it.get("codebook_row")
            notes = []
            if it.get("codebook_erratum"):
                notes.append("inventory erratum: " + it["codebook_erratum"])
            if it.get("inheritance_note"):
                notes.append(it["inheritance_note"])
            if not (it.get("item_text_ko") or it.get("codebook_description")):
                notes.append("codebook row is a blank continuation row of a multi-response grid; item text taken from the inventory's questionnaire transcription")
            if norm(item_text_q) not in norm(cb_text) and norm(cb_text) not in norm(item_text_q):
                notes.append("codebook description wording differs from the questionnaire item; questionnaire is authoritative for meaning")
            if (b.get("item_notes") or {}).get(key):
                notes.append(b["item_notes"][key])
            entry = {
                "variable": var,
                "construct_id": cid,
                "item_text_ko": cb_text,  # verbatim codebook description (audit F compares this to the codebook sheet)
                "item_text_questionnaire": item_text_q,
                "questionnaire_block": block,
                "questionnaire_stem": stem,
                "questionnaire_printed_codes": b["printed_codes"],
                "filter": b["filter"],
                "values": inv_values(it) or [f"numeric entry — unit/format: {'; '.join(b['printed_codes'])} (no value labels; see data_values_observed)"],
                "data_values_observed": obs,
                "data_coding": coding_note,
                "recode_to_printed": {str(k): v for k, v in recode.items()} if recode else None,
                "short_label_en": b["short_en"][key],
                "source": (f"codebook: {os.path.basename(cfg['codebook'])} sheet 코드북 row {cb_row}; "
                           f"questionnaire: {os.path.basename(cfg['questionnaire'])} [{block}] (wording verified against pdftotext output {os.path.basename(qtxt_path)}); "
                           f"data: {os.path.basename(cfg['data'])} sheet {cfg['sheet']} (n={obs.get('n_nonnull')})"),
                "codebook_note": "; ".join(notes) if notes else "",
            }
            if drift:
                entry["codebook_note"] = (entry["codebook_note"] + "; " if entry["codebook_note"] else "") + f"inventory text differs from codebook sheet: {cb_desc[var][:80]!r}"
            items_out.append(entry)
            harmonised["constructs"].setdefault(cid, {"block": block, "item_key": str(key), "short_label_en": b["short_en"][key], "waves": {}})
            harmonised["constructs"][cid]["waves"][wave] = {"variable": var, "data_coding": coding_note, "recode_to_printed": entry["recode_to_printed"], "n_nonnull": obs.get("n_nonnull")}

        # --- register variables
        for cid, wvars in REGISTER.items():
            var = wvars[wave]
            if var is None:
                continue
            it = inv_items.get(var) or inv_items.get(var.strip())
            if it is None:
                wlog["missing_in_inventory"].append(var); log["status"] = "FAIL"; continue
            col = data.get(var) or data_norm.get(var.strip())
            if col is None:
                wlog["missing_in_data"].append(var); log["status"] = "FAIL"; continue
            obs = observed(col)
            reg_text = inv_text(it) or f"{var.strip()} — 데이터 시트 헤더(코드북 행에 설명 없음; 식별자)"
            entry = {
                "variable": var, "construct_id": cid, "register": True,
                "item_text_ko": reg_text, "values": inv_values(it) or ["register/list variable — no value labels; see data_values_observed"], "data_values_observed": obs,
                "short_label_en": {"ID": "respondent id", "INDUSTRY2": "KSIC 2-digit industry (register)", "INDUSTRY1": "KSIC section (register)",
                                   "SIZECLASS": "employment size class (register/response)", "SIZECLASS_SBR": "employment size class (SBR)",
                                   "SBR_SCALE": "firm class large/medium/small (SBR)", "FOUNDYEAR": "founding year", "REGION": "head-office region",
                                   "SALESCLASS": "sales size class (register)", "WEIGHT": "survey weight"}[cid],
                "source": f"codebook: {os.path.basename(cfg['codebook'])} sheet 코드북 row {it.get('codebook_row')} (register/list variable, no questionnaire item); data: {os.path.basename(cfg['data'])} sheet {cfg['sheet']}",
                "codebook_note": it.get("codebook_erratum") or ("codebook row carries no description; text taken from the data-sheet header" if not inv_text(it) or "코드북에 설명 없음" in inv_text(it) else ""),
            }
            items_out.append(entry)
            harmonised["register"].setdefault(cid, {"waves": {}})
            harmonised["register"][cid]["waves"][wave] = {"variable": var, "values": inv_values(it)[:8], "observed": obs}

        # --- constructs for this wave (translate construct ids to wave variables)
        id2var = {e["construct_id"]: e["variable"] for e in items_out}
        constructs_out = {}
        for name, (label, cids, rule) in CONSTRUCTS.items():
            vars_ = [id2var[c] for c in cids if c in id2var]
            if len(vars_) != len(cids):
                continue  # construct not available in this wave
            constructs_out[name] = {"label": label, "items": vars_, "rule": rule}
        wlog["n_items"] = len(items_out); wlog["n_constructs"] = len(constructs_out)
        wlog["wording_failures"] = [c for c in wlog["wording_checks"] if not (c["stem_found"] and c["item_found"])]
        log["waves"][wave] = wlog
        out = {"_meta": {"wave": wave, "sector": cfg["sector"], "reference_period": f"{cfg['y0']}-{cfg['y2']}", "built": log["built"],
                         "inventory": cfg["inventory"], "codebook": cfg["codebook"], "questionnaire": cfg["questionnaire"],
                         "data": cfg["data"], "data_sheet": cfg["sheet"], "n_rows": n_rows,
                         "rule": "item_text_ko = verbatim codebook description; item_text_questionnaire = wording transcribed from this wave's questionnaire PDF and verified against its text; recode_to_printed derived from observed data codes vs printed codes."},
               "items": items_out, "constructs": constructs_out}
        json.dump(out, open(os.path.join(OUT_MAPS, f"item_map_{wave}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        for e in items_out:
            if not e.get("register"):
                table_rows.append((e["construct_id"], wave, e["variable"], e["item_text_questionnaire"], e["short_label_en"], e["data_coding"], e["filter"]))
        print(f"[{wave}] rows={n_rows} items={len(items_out)} constructs={len(constructs_out)} wording_failures={len(wlog['wording_failures'])} unresolved={len(wlog['unresolved'])} missing_inv={wlog['missing_in_inventory']} missing_data={wlog['missing_in_data']} drift={len(wlog['codebook_drift'])}")

    harmonised["analysis_constructs"] = {n: {"label": l, "construct_ids": c, "rule": r} for n, (l, c, r) in CONSTRUCTS.items()}
    json.dump(harmonised, open(os.path.join(OUT_MAPS, "item_map_escape_exit.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(log, open(OUT_LOG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # --- generated variable table (never typed by hand)
    lines = ["# 변수 설명표 (Table F.1형) — `code/build_item_maps.py`가 item map에서 생성. 손으로 고치지 말 것.", "",
             f"생성 {log['built']}. 각 행의 문항 원문은 해당 파동 설문지 PDF 텍스트와 대조해 확인된 것이다. 데이터 코딩은 관측값과 설문지 인쇄 코드를 비교해 도출했다.", "",
             "| 구성개념 ID | 파동 | 변수명 | 설문지 문항 원문 | 영문 짧은 라벨 | 데이터 코딩 | 응답 대상(필터) |", "|---|---|---|---|---|---|---|"]
    for r in table_rows:
        lines.append("| " + " | ".join(str(x).replace("|", "/").replace("\n", " ") for x in r) + " |")
    lines += ["", "## 분석 구성개념과 구성 규칙", "", "| 구성개념 | 라벨 | 구성 항목 ID | 규칙 |", "|---|---|---|---|"]
    for n, (l, c, r) in CONSTRUCTS.items():
        lines.append(f"| `{n}` | {l} | {', '.join(c)} | {r} |")
    open(OUT_TABLE, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("status:", log["status"], "->", OUT_LOG)
    sys.exit(0 if log["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
