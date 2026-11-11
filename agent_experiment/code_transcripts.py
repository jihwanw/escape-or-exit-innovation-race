#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 11 — rubric coding of the agents' stated reasons (Stage A one-shot reasons and Stage B period reasons) by two judge
models, with inter-judge agreement. Mechanism categories follow the race model (MODEL_NOTES.md) plus text-level checks:

  M1 first_mover_prize     wants to launch before the rival / win the larger (100억) prize; being first is the stated goal
  M2 threat_hurry          the possible new entrant (prize halving) is given as a reason to speed up or finish sooner
  M3 threat_quit           the possible/realised new entrant (prize halving) is given as a reason to stop or not invest further
  M4 rival_position        reasons from the rival's stage / chance of being overtaken or of catching up
  M5 expected_value        explicit cost-benefit or expected-value arithmetic (probabilities x prizes vs costs)
  M6 sunk_or_salvage       money already spent, or redirecting budget/staff to the existing business, is used as a reason
  M7 noise_uncertainty     unreliability of the information about the rival's progress is used as a reason
  M8 wait_and_see          keep the option open / decide later with new information as a reason to continue (not accelerate)
  M9 firm_attributes       the firm's industry, size, age or group affiliation is used as a reason
  M10 irrelevant_attribute the founding-anniversary month (or any other decision-irrelevant attribute) is used as a reason
  primary: the single category that best describes the main justification (one of M1..M10, or 'other')

Judges: 'fable' and 'gpt56' (same clients as the experiments), English instructions, reasons in their original language,
25 reasons per call, strict JSON parsing, resume-safe logs (agent_experiment/logs/transcript_codes_<judge>.jsonl).
Controls (--controls): known-answer texts that both judges must code as expected; parser tests.
Output: results/08_transcript_codes.json (category shares by stage x decision x threat x gap, judge agreement (percent and
Cohen's kappa) per category, primary-label agreement) and results/08_validation_sample_50.csv for manual validation.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # llm_clients.py (Bedrock client) is vendored next to this script (2026-11-11; previously imported from the ICAIF_files agent directory, identical file)
LOGDIR = os.path.join(HERE, "logs")
OUT = os.path.join(ROOT, "results", "08_transcript_codes.json")
CTRL = os.path.join(ROOT, "results", "08_transcript_controls.json")
SEED = 20261110
BATCH = 25
CATS = ["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M10"]
CAT_NAMES = {"M1": "first_mover_prize", "M2": "threat_hurry", "M3": "threat_quit", "M4": "rival_position", "M5": "expected_value", "M6": "sunk_or_salvage",
             "M7": "noise_uncertainty", "M8": "wait_and_see", "M9": "firm_attributes", "M10": "irrelevant_attribute"}

INSTR = """You are coding short justifications written by decision-makers in a product-development scenario. In the scenario a firm races a rival through 3 development stages over at most 3 periods; each period it can continue (8억원, 50% chance of a stage), accelerate (25억원, 80%), or stop. Launching first pays about 100억원, second about 30억원, simultaneous 65억원; a possible new competitor may enter (35% per period) and halve the profits of products not yet launched; the rival's stage may be known exactly or only estimated.

For EACH justification below, code the following binary categories (1 = the justification uses this reason, 0 = it does not) and one primary label:
M1 first_mover_prize: wants to launch before the rival / win the larger prize; being first is the stated goal.
M2 threat_hurry: the possible new entrant (profit halving) is given as a reason to speed up or finish sooner.
M3 threat_quit: the possible or realised new entrant (profit halving) is given as a reason to stop or not invest further.
M4 rival_position: reasons from the rival's stage, the chance of being overtaken, or of catching up.
M5 expected_value: explicit cost-benefit or expected-value arithmetic (probabilities, prizes, costs compared numerically).
M6 sunk_or_salvage: money already spent, or redirecting budget/staff to the existing business, is used as a reason.
M7 noise_uncertainty: unreliability of the information about the rival's progress is used as a reason.
M8 wait_and_see: keeping options open / deciding later with new information is given as a reason to continue rather than accelerate.
M9 firm_attributes: the firm's industry, size, age or group affiliation is used as a reason.
M10 irrelevant_attribute: the founding-anniversary month or any other decision-irrelevant attribute is used as a reason.
primary: the one label among M1..M10 that best describes the main justification, or "other".

Justifications may be in Korean or English. Code what the text says, not what a rational agent should have said. Answer ONLY with a JSON object of the form
{"codes": [{"id": "<id>", "M1": 0 or 1, ..., "M10": 0 or 1, "primary": "<label>"}, ...]}
with exactly one entry per justification id, in the same order, and nothing else.

Justifications:
"""


def load_reasons():
    rows = []
    for fn in sorted(os.listdir(LOGDIR)):
        if fn.startswith("stage_a_") and fn.endswith(".jsonl") and "_mock" not in fn:
            for line in open(os.path.join(LOGDIR, fn), encoding="utf-8"):
                r = json.loads(line)
                if r["parse_status"] == "ok" and r.get("reason"):
                    rows.append({"uid": f"A:{r['design_id']}:{r['model']}", "stage": "A", "model": r["model"], "lang": r["lang"], "persona_id": r["persona_id"], "gap": r["gap"], "threat": r["threat"],
                                 "noise": r["noise"], "placebo": r["placebo"], "t": 1, "decision": r["decision"], "reason": r["reason"].strip()})
        if fn.startswith("stage_b_calls_") and fn.endswith(".jsonl") and "_mock_" not in fn:
            for line in open(os.path.join(LOGDIR, fn), encoding="utf-8"):
                r = json.loads(line)
                if r["parse_status"] == "ok" and r.get("reason"):
                    rows.append({"uid": f"B:{r['episode_id']}:{r['t']}:{r['model']}", "stage": "B", "model": r["model"], "lang": r["lang"], "persona_id": r["persona_id"], "gap": r["gap"], "threat": r["threat"],
                                 "noise": r["noise"], "placebo": r["placebo"], "t": r["t"], "decision": r["decision"], "reason": r["reason"].strip(),
                                 "entry": r["state"]["entry"], "rival_status": r["state"]["rival_status"]})
    df = pd.DataFrame(rows).drop_duplicates("uid").reset_index(drop=True)
    return df


def render(batch):
    lines = [INSTR]
    for _, r in batch.iterrows():
        lines.append(f'[{r["uid"]}] (decision: {r["decision"]}) {r["reason"]}')
    return "\n".join(lines)


def parse(raw, uids):
    if not raw or not str(raw).strip():
        return None, "empty"
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return None, "no_json"
    try:
        js = json.loads(m.group())
    except Exception:
        return None, "bad_json"
    codes = js.get("codes") if isinstance(js, dict) else None
    if not isinstance(codes, list):
        return None, "no_codes"
    out = {}
    for c in codes:
        if not isinstance(c, dict) or c.get("id") not in uids:
            continue
        rec = {}
        ok = True
        for k in CATS:
            v = c.get(k)
            try:
                v = int(v)
            except Exception:
                ok = False; break
            if v not in (0, 1):
                ok = False; break
            rec[k] = v
        if not ok:
            continue
        p = str(c.get("primary", "other")).strip()
        rec["primary"] = p if p in CATS else "other"
        out[c["id"]] = rec
    if not out:
        return None, "no_valid_entries"
    return out, "ok" if len(out) == len(uids) else "partial"


def call_judge(client, judge, prompt):
    from run_stage_a import call_one
    return call_one(client, judge, prompt, max_attempts=3)


def run(judges, mock=False, workers=8):
    df = load_reasons()
    rng = np.random.default_rng(SEED)
    order = rng.permutation(len(df))  # shuffle so that batches mix stages/cells
    batches = [df.iloc[order[i:i + BATCH]] for i in range(0, len(df), BATCH)]
    print(f"reasons: {len(df)} ({(df.stage == 'A').sum()} Stage A, {(df.stage == 'B').sum()} Stage B); batches: {len(batches)}")
    for judge in judges:
        logf = os.path.join(LOGDIR, f"transcript_codes_{judge}{'_mock' if mock else ''}.jsonl")
        done = {}
        if os.path.exists(logf):
            for line in open(logf, encoding="utf-8"):
                r = json.loads(line)
                for uid, c in (r.get("codes") or {}).items():
                    done[uid] = c
        todo = [b for b in batches if any(u not in done for u in b["uid"])]
        print(f"[{judge}] batches to code: {len(todo)} (coded reasons so far {len(done)})", flush=True)
        if mock:
            client = None
        else:
            from run_stage_a import real_client
            client = real_client(judge)

        def work(b):
            uids = list(b["uid"])
            prompt = render(b)
            if mock:
                raw = json.dumps({"codes": [{"id": u, **{k: int(rng.random() < 0.3) for k in CATS}, "primary": "M5"} for u in uids]}); attempts, err = 1, None
            else:
                raw, attempts, err = call_judge(client, judge, prompt)
            codes, status = parse(raw, set(uids))
            return {"judge": judge, "uids": uids, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(), "raw": raw, "attempts": attempts, "error": err,
                    "parse_status": status, "codes": codes, "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z")}

        with open(logf, "a", encoding="utf-8") as f, ThreadPoolExecutor(max_workers=1 if mock else workers) as ex:
            futs = [ex.submit(work, b) for b in todo]
            for i, fu in enumerate(as_completed(futs)):
                f.write(json.dumps(fu.result(), ensure_ascii=False) + "\n"); f.flush()
                if (i + 1) % 20 == 0:
                    print(f"   {i + 1}/{len(todo)}", flush=True)
    return df


def kappa(a, b):
    a = np.asarray(a); b = np.asarray(b)
    po = np.mean(a == b)
    pe = np.mean(a) * np.mean(b) + (1 - np.mean(a)) * (1 - np.mean(b))
    return float((po - pe) / (1 - pe)) if pe < 1 else float("nan")


def summarise(judges, mock=False):
    df = load_reasons()
    codes = {}
    for judge in judges:
        logf = os.path.join(LOGDIR, f"transcript_codes_{judge}{'_mock' if mock else ''}.jsonl")
        d = {}
        if os.path.exists(logf):
            for line in open(logf, encoding="utf-8"):
                r = json.loads(line)
                for uid, c in (r.get("codes") or {}).items():
                    d[uid] = c
        codes[judge] = d
    for judge in judges:
        for k in CATS + ["primary"]:
            df[f"{judge}_{k}"] = df["uid"].map(lambda u, j=judge, k=k: (codes[j].get(u) or {}).get(k))
    both = df.dropna(subset=[f"{j}_M1" for j in judges]).copy()
    res = {"n_reasons": int(len(df)), "n_coded_by_judge": {j: int(df[f"{j}_M1"].notna().sum()) for j in judges}, "n_coded_by_both": int(len(both)), "categories": CAT_NAMES,
           "agreement": {}, "shares": {}, "by_stage_decision_threat": {}}
    if len(judges) == 2 and len(both):
        j1, j2 = judges
        for k in CATS:
            a = both[f"{j1}_{k}"].astype(int); b = both[f"{j2}_{k}"].astype(int)
            res["agreement"][k] = {"percent": float(np.mean(a == b)), "kappa": kappa(a, b), "share_j1": float(a.mean()), "share_j2": float(b.mean())}
        res["agreement"]["primary"] = {"percent": float(np.mean(both[f"{j1}_primary"] == both[f"{j2}_primary"]))}
        # consensus code = 1 only if both judges say 1 (conservative)
        for k in CATS:
            both[f"cons_{k}"] = ((both[f"{j1}_{k}"].astype(int) + both[f"{j2}_{k}"].astype(int)) == 2).astype(int)
            both[f"any_{k}"] = ((both[f"{j1}_{k}"].astype(int) + both[f"{j2}_{k}"].astype(int)) >= 1).astype(int)
        for stage in ("A", "B"):
            s = both[both.stage == stage]
            for (dec, thr, gap), g in s.groupby(["decision", "threat", "gap"]):
                res["by_stage_decision_threat"][f"{stage}:{dec}:threat{thr}:gap{gap}"] = {"n": int(len(g)), **{CAT_NAMES[k]: float(g[f"cons_{k}"].mean()) for k in CATS}}
            res["shares"][stage] = {"n": int(len(s)), "consensus": {CAT_NAMES[k]: float(s[f"cons_{k}"].mean()) for k in CATS}, "either_judge": {CAT_NAMES[k]: float(s[f"any_{k}"].mean()) for k in CATS},
                                    "by_decision": {dec: {CAT_NAMES[k]: float(g[f"cons_{k}"].mean()) for k in CATS} | {"n": int(len(g))} for dec, g in s.groupby("decision")},
                                    "by_model": {m: {CAT_NAMES[k]: float(g[f"cons_{k}"].mean()) for k in CATS} | {"n": int(len(g))} for m, g in s.groupby("model")}}
        # text-level placebo check: share of reasons invoking the irrelevant attribute, by placebo value
        res["irrelevant_attribute_by_placebo"] = {str(pv): {"n": int(len(g)), "share_either_judge": float(g["any_M10"].mean())} for pv, g in both.groupby("placebo")}
        res["firm_attributes_share_either_judge"] = float(both["any_M9"].mean())
        # validation sample for the user (50, stratified by stage and decision)
        rng = np.random.default_rng(SEED)
        samp = both.groupby(["stage", "decision"], group_keys=False).apply(lambda g: g.sample(min(len(g), 9), random_state=SEED)).head(50)
        cols = ["uid", "stage", "model", "lang", "gap", "threat", "noise", "t", "decision", "reason"] + [f"{j}_{k}" for j in judges for k in CATS + ["primary"]]
        samp[cols].to_csv(os.path.join(ROOT, "results", "08_validation_sample_50.csv"), index=False)
        res["validation_sample_csv"] = "results/08_validation_sample_50.csv"
    return res


def controls():
    """Known-answer texts (both judges) + parser tests."""
    known = [("K1", "A", "경쟁사보다 먼저 출시해 100억원을 확보하는 것이 핵심이므로 가속한다.", {"M1": 1}),
             ("K2", "Q", "A new competitor may enter and halve the profit of an unfinished product, so continuing is not worth 8억원 more; we stop.", {"M3": 1}),
             ("K3", "C", "이미 16억원을 썼고 남은 예산은 기존 사업에 돌리는 것이 낫지만, 경쟁사 진행 정보가 추정치라 불확실하다.", {"M6": 1, "M7": 1}),
             ("K4", "C", "Expected value of continuing is 0.5 x 100 - 8 = 42억원 versus 0.8 x 100 - 25 = 55억원 for accelerating; the rival is two stages behind so we can wait and decide next period.", {"M5": 1, "M4": 1, "M8": 1}),
             ("K5", "A", "Our founding anniversary is in September, so we should accelerate.", {"M10": 1})]
    df = pd.DataFrame([{"uid": u, "decision": d, "reason": r} for u, d, r, _ in known])
    prompt = render(df)
    res = {"known_answer": {}, "parser_tests": {}, "status": "PASS"}
    from run_stage_a import real_client
    for judge in ("fable", "gpt56"):
        raw, attempts, err = call_judge(real_client(judge), judge, prompt)
        codes, status = parse(raw, set(df["uid"]))
        hits = {}
        for u, d, r, exp in known:
            got = (codes or {}).get(u, {})
            hits[u] = {k: (got.get(k) == v) for k, v in exp.items()}
        all_ok = all(all(v.values()) for v in hits.values())
        res["known_answer"][judge] = {"parse_status": status, "expected_hits": hits, "all_expected_recovered": all_ok, "codes": codes}
        if not all_ok:
            res["status"] = "FAIL"
    uids = {"x", "y"}
    tests = {"clean": parse('{"codes": [{"id": "x", "M1": 1, "M2": 0, "M3": 0, "M4": 0, "M5": 0, "M6": 0, "M7": 0, "M8": 0, "M9": 0, "M10": 0, "primary": "M1"}]}', uids)[1],
             "bad_value": parse('{"codes": [{"id": "x", "M1": 2, "M2": 0, "M3": 0, "M4": 0, "M5": 0, "M6": 0, "M7": 0, "M8": 0, "M9": 0, "M10": 0, "primary": "M1"}]}', uids)[1],
             "no_json": parse("I cannot code this.", uids)[1], "empty": parse("", uids)[1]}
    res["parser_tests"] = tests
    if not (tests["clean"] == "partial" and tests["bad_value"] == "no_valid_entries" and tests["no_json"] == "no_json" and tests["empty"] == "empty"):
        res["status"] = "FAIL"
    res["built"] = time.strftime("%Y-%m-%d %H:%M %Z")
    json.dump(res, open(CTRL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"status": res["status"], "parser_tests": tests, "known": {j: v["all_expected_recovered"] for j, v in res["known_answer"].items()}}, ensure_ascii=False))
    return res["status"] == "PASS"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--controls", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--summarise", action="store_true")
    ap.add_argument("--judges", default="fable,gpt56")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    sys.path.insert(0, HERE)
    if a.controls:
        sys.exit(0 if controls() else 1)
    if a.run:
        run(a.judges.split(","), workers=a.workers)
    if a.run or a.summarise:
        res = summarise(a.judges.split(",")); res["built"] = time.strftime("%Y-%m-%d %H:%M %Z")
        json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(json.dumps({k: res[k] for k in ("n_reasons", "n_coded_by_judge", "n_coded_by_both")}, ensure_ascii=False))
        print("agreement:", {k: (round(v.get("percent", 0), 3), round(v.get("kappa", float("nan")), 3) if "kappa" in v else None) for k, v in res.get("agreement", {}).items()})
        for st, v in res.get("shares", {}).items():
            print(st, "consensus shares:", {k: round(x, 3) for k, x in v["consensus"].items()})
