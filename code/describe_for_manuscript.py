#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Descriptive additions requested by the Task 12 cross-review (2026-11-11). Nothing here is a hypothesis test; every number
is written to results/*.json so that code/make_numbers.py can turn it into a macro (the manuscript never types a number).

  1. results/08b_transcript_judge_shares.json — per-judge shares of the threat-to-stop (M3) and threat-to-hurry (M2) codes
     among threat-cell stop / accelerate decisions, Stage A and Stage B (the published consensus shares require BOTH judges);
     from agent_experiment/logs/transcript_codes_<judge>.jsonl and the Stage A / Stage B call logs.
  2. results/08c_example_reasons.json — three verbatim agent reasons (one accelerate in the frontier-threat cell, one stop in
     the laggard-threat cell, one continue in the level cell) with cell and arm, chosen by a fixed rule (the first English
     Stage A call in design order whose decision and judge codes match) from the PUBLIC redacted logs.
  3. results/07c_sector_gap_counts.json — firms, lead-time-protection events and abandonment events by sector x gap group
     (from data/analysis_panel.parquet; descriptive counts only, no treatment variable).
  4. results/06b_entry_rate_extremes.json — the industry divisions at the minimum and maximum of the wave entry rate,
     with their codebook titles (data/entry_rates_industry_year.csv, data/external_industry_year.csv, item maps).
"""
import json
import os
import re
import sys
import time

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOGS = os.path.join(ROOT, "agent_experiment", "logs")
PUB = os.path.join(ROOT, "agent_experiment", "logs_public")
CATS = ["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M10"]


def load_codes(judge):
    out = {}
    for line in open(os.path.join(LOGS, f"transcript_codes_{judge}.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        try:
            codes = json.loads(re.search(r"\{.*\}", r["raw"], re.S).group(0))["codes"]
        except Exception:
            continue
        for c in codes:
            if c.get("id") in r["uids"]:
                out[c["id"]] = c
    return out


def load_decisions():
    """uid -> (stage, decision, threat, gap, model, lang, reason, design_id)"""
    dec = {}
    for fn in sorted(os.listdir(LOGS)):
        if fn.startswith("stage_a_") and fn.endswith(".jsonl") and "_mock" not in fn:
            for line in open(os.path.join(LOGS, fn), encoding="utf-8"):
                r = json.loads(line)
                if r["parse_status"] == "ok" and r.get("reason"):
                    dec[f"A:{r['design_id']}:{r['model']}"] = ("A", r["decision"], r["threat"], r["gap"], r["model"], r["lang"], r["reason"].strip(), r["design_id"], r["noise"])
        if fn.startswith("stage_b_calls_") and fn.endswith(".jsonl") and "_mock" not in fn:
            for line in open(os.path.join(LOGS, fn), encoding="utf-8"):
                r = json.loads(line)
                if r.get("parse_status") == "ok" and r.get("reason"):
                    dec[f"B:{r['episode_id']}:{r['t']}:{r['model']}"] = ("B", r["decision"], r["threat"], r["gap"], r["model"], r["lang"], r["reason"].strip(), r["episode_id"], r.get("noise"))
    return dec


def judge_shares(dec, codes_by_judge):
    res = {}
    for stage in ("A", "B"):
        for cat, decision in (("M3", "Q"), ("M2", "A")):
            uids = [u for u, d in dec.items() if d[0] == stage and d[1] == decision and d[2] == 1]
            row = {"n_threat_cell_decisions": len(uids)}
            both = 0
            for judge, codes in codes_by_judge.items():
                coded = [codes[u][cat] for u in uids if u in codes]
                row[f"share_{judge}"] = sum(coded) / len(coded) if coded else None
                row[f"n_coded_{judge}"] = len(coded)
            inter = [u for u in uids if all(u in c for c in codes_by_judge.values())]
            row["share_both"] = (sum(1 for u in inter if all(c[u][cat] == 1 for c in codes_by_judge.values())) / len(inter)) if inter else None
            row["share_either"] = (sum(1 for u in inter if any(c[u][cat] == 1 for c in codes_by_judge.values())) / len(inter)) if inter else None
            res[f"{stage}:{decision}:{cat}"] = row
    return res


def example_reasons(dec, codes_by_judge):
    """First English Stage A call (design order) per rule; reasons taken from the PUBLIC redacted log so the quoted text is
    exactly what is published."""
    pub = {}
    for fn in ("stage_a_fable_en.jsonl", "stage_a_gpt56_en.jsonl"):
        for line in open(os.path.join(PUB, fn), encoding="utf-8"):
            r = json.loads(line)
            pub[f"A:{r['design_id']}:{r['model']}"] = r
    rules = [("accelerate_frontier_threat", "A", 2, 1, "M2"), ("stop_laggard_threat", "Q", 0, 1, "M3"), ("continue_level_nothreat", "C", 1, 0, "M8")]
    out = {}
    for name, decision, gap, threat, cat in rules:
        cands = sorted([u for u, d in dec.items() if d[0] == "A" and d[5] == "en" and d[1] == decision and d[3] == gap and d[2] == threat
                        and all(u in c and c[u][cat] == 1 for c in codes_by_judge.values())], key=lambda u: (dec[u][7], dec[u][4]))
        for u in cands:
            if u in pub and pub[u].get("reason"):
                r = pub[u]
                out[name] = {"uid": u, "design_id": r["design_id"], "model": r["model"], "lang": r["lang"], "gap": r["gap"], "threat": r["threat"], "noise": r["noise"],
                             "decision": r["decision"], "reason_public_log": r["reason"].strip(), "judge_codes": {j: codes_by_judge[j][u] for j in codes_by_judge}}
                break
    return out


def sector_gap_counts():
    p = pd.read_parquet(os.path.join(ROOT, "data", "analysis_panel.parquet"))
    out = {}
    for sec in ("manufacturing", "services"):
        d = p[p["sector"] == sec]
        for g in (0, 1, 2):
            dd = d[d["gap3"] == g]
            qa = dd["quit_any"].dropna()
            out[f"{sec}:g{g}"] = {"n_firms": int(len(dd)), "preempt_events": int(dd["preempt_strategy"].sum()), "preempt_rate": float(dd["preempt_strategy"].mean()) if len(dd) else None,
                                  "n_innov_active": int(len(qa)), "quit_events": int(qa.sum()), "quit_rate": float(qa.mean()) if len(qa) else None}
    return out


def entry_rate_extremes():
    ext = pd.read_csv(os.path.join(ROOT, "data", "external_industry_year.csv"))
    labels = {"M": {}, "S": {}}
    for w, sec in (("2024M", "M"), ("2025S", "S")):
        m = json.load(open(os.path.join(ROOT, "item_maps", f"item_map_{w}.json"), encoding="utf-8"))
        reg = {e["construct_id"]: e for e in m["items"] if e.get("register")}
        for v in reg["INDUSTRY2"]["values"]:
            mm = re.match(r"^\s*(\d+)\.\s*(.+)$", v)
            if mm:
                labels[sec][int(mm.group(1))] = mm.group(2).strip()
    out = {"columns": list(ext.columns)}
    wcol, icol, rcol = "wave", "ksic2", "entry_rate"
    if all(c in ext.columns for c in (wcol, icol, rcol)):
        for w, d in ext.groupby(wcol):
            lab = labels["M" if str(w).endswith("M") else "S"]
            d = d[d[icol].isin(lab.keys())]  # KIS industries of that sector only
            labels_w = lab
            lo, hi = d.loc[d[rcol].idxmin()], d.loc[d[rcol].idxmax()]
            out[str(w)] = {"min": {"industry2": int(lo[icol]), "label_ko": labels_w.get(int(lo[icol])), "entry_rate_pct": float(lo[rcol])},
                           "max": {"industry2": int(hi[icol]), "label_ko": labels_w.get(int(hi[icol])), "entry_rate_pct": float(hi[rcol])}}
    return out


def run_metadata():
    """Bedrock model identifiers (from the client module the runners import) and the call-time span of each stage (from the logs)."""
    sys.path.insert(0, os.path.expanduser("~/.kiro/agents/ICAIF_files"))
    from llm_clients import MODELS  # noqa: E402
    out = {"models": {k: {"provider": v["provider"], "id": v["id"], "region": v.get("region")} for k, v in MODELS.items() if k in ("fable", "gpt56")}, "calls": {}}
    for stage, pat in (("A", "stage_a_"), ("B", "stage_b_calls_")):
        ts, n = [], 0
        for fn in sorted(os.listdir(LOGS)):
            if fn.startswith(pat) and fn.endswith(".jsonl") and "_mock" not in fn:
                for line in open(os.path.join(LOGS, fn), encoding="utf-8"):
                    r = json.loads(line); n += 1
                    if r.get("ts"):
                        ts.append(r["ts"])
        out["calls"][stage] = {"n_log_records": n, "first": min(ts) if ts else None, "last": max(ts) if ts else None}
    return out


if __name__ == "__main__":
    dec = load_decisions()
    codes = {"fable": load_codes("fable"), "gpt56": load_codes("gpt56")}
    js = judge_shares(dec, codes)
    # reasons by stage (all reasons sent to the judges); must equal n_reasons in results/08_transcript_codes.json, else recorded as a mismatch
    T = json.load(open(os.path.join(ROOT, "results", "08_transcript_codes.json"), encoding="utf-8"))
    by_stage = {st: sum(1 for d in dec.values() if d[0] == st) for st in ("A", "B")}
    by_stage_both = {st: sum(1 for u, d in dec.items() if d[0] == st and all(u in c for c in codes.values())) for st in ("A", "B")}
    json.dump({"built": time.strftime("%Y-%m-%d %H:%M %Z"), "note": "per-judge shares among threat-cell decisions; published consensus shares require both judges", "shares": js,
               "n_reasons_by_stage": by_stage, "n_reasons_by_stage_coded_by_both": by_stage_both,
               "n_reasons_total": len(dec), "matches_08_transcript_codes_n_reasons": len(dec) == T["n_reasons"]},
              open(os.path.join(ROOT, "results", "08b_transcript_judge_shares.json"), "w"), indent=1)
    ex = example_reasons(dec, codes)
    json.dump({"built": time.strftime("%Y-%m-%d %H:%M %Z"), "rule": "first English Stage A call in design order with the stated decision, cell and both-judge code; text from agent_experiment/logs_public", "examples": ex},
              open(os.path.join(ROOT, "results", "08c_example_reasons.json"), "w"), indent=1, ensure_ascii=False)
    sg = sector_gap_counts()
    json.dump({"built": time.strftime("%Y-%m-%d %H:%M %Z"), "counts": sg}, open(os.path.join(ROOT, "results", "07c_sector_gap_counts.json"), "w"), indent=1)
    rm = run_metadata()
    json.dump({"built": time.strftime("%Y-%m-%d %H:%M %Z"), **rm}, open(os.path.join(ROOT, "results", "04b_agent_run_metadata.json"), "w"), indent=1)
    er = entry_rate_extremes()
    json.dump({"built": time.strftime("%Y-%m-%d %H:%M %Z"), "extremes": er}, open(os.path.join(ROOT, "results", "06b_entry_rate_extremes.json"), "w"), indent=1, ensure_ascii=False)
    print(json.dumps(js, indent=1)); print(json.dumps(ex, indent=1, ensure_ascii=False)[:3000]); print(json.dumps(sg, indent=1)); print(json.dumps(er, indent=1, ensure_ascii=False)[:1500])
