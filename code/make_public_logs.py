#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Disclosure control for the public replication package (user decision 2026-11-10: option 1).

Personas were drawn from individual KIS records (registry attributes only: 2-digit industry, size band, exact firm age, group
affiliation). Within the KIS sample, 14 of the 40 Stage A personas match exactly one respondent on those four attributes
(computed below and written to results/09_persona_redaction.json), so publishing them would publish individual-level records
covered by the KIS research-use licence. Remedy:
  1. public copies of every agent log have the four persona lines of the [회사]/[Company] block replaced by one placeholder line
     carrying only the persona id; all decision-relevant content (rules, state, options, raw responses, reasons) is unchanged;
  2. a public persona table at sector x size (3 bands) x firm age (4 bands), the coarsest level that keeps every persona in a
     cell of at least k = 5 KIS respondents (actual minimum reported in the JSON);
  3. the original logs and persona file stay private (this working repository; OSF private component on request) and are
     available to editors and reviewers under the licence.
The original prompt SHA256 is kept in each record (prompt_sha256) next to the hash of the redacted prompt, so a reviewer with
the originals can verify that nothing else changed. Writes agent_experiment/logs_public/ and public/personas_public.csv.
"""
import hashlib
import json
import os
import re
import shutil
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOGS = os.path.join(ROOT, "agent_experiment", "logs")
PUB = os.path.join(ROOT, "agent_experiment", "logs_public")
PUBDIR = os.path.join(ROOT, "public")
OUT = os.path.join(ROOT, "results", "09_persona_redaction.json")

KO_BLOCK = re.compile(r"\[회사\]\n- 업종: .*\n- 상용 근로자 규모: .*\n- 설립 후 .*\n- .*\n")
EN_BLOCK = re.compile(r"\[Company\]\n- Industry \(.*?\): .*\n- Size: .*\n- Founded .*\n- .*\n")
KO_PLACEHOLDER = "[회사]\n- (KIS 응답 기업에서 추출한 네 가지 기업 속성은 공개본에서 가려짐; 페르소나 ID {pid}, 공개 페르소나 표 personas_public.csv 참조)\n"
EN_PLACEHOLDER = "[Company]\n- (four firm attributes drawn from a KIS respondent are redacted in the public copy; persona id {pid}, see personas_public.csv)\n"


def redact_prompt(prompt, pid):
    p2, n1 = KO_BLOCK.subn(KO_PLACEHOLDER.format(pid=pid), prompt)
    p2, n2 = EN_BLOCK.subn(EN_PLACEHOLDER.format(pid=pid), p2)
    return p2, n1 + n2


def redact_response(text, age, labels):
    """Agents occasionally echo persona attributes in their answers ('설립 3년차 소규모 기업'); mask the exact firm age and any
    industry label so that the public response text carries no more than the public persona table."""
    if not text:
        return text, 0
    n = 0
    for lab in labels:
        if lab in text:
            text = text.replace(lab, "[업종 가림]"); n += 1
    if age is not None:
        text, k = re.subn(rf"설립\s*(후\s*)?{age}\s*년\s*(차)?", "설립 [연수 가림]년", text); n += k
        text, k = re.subn(rf"\b{age}\s*년\s*차", "[연수 가림]년차", text); n += k
        text, k = re.subn(rf"(founded|established)\s+{age}\s+years\s+ago", r"\1 [years redacted] ago", text, flags=re.I); n += k
        text, k = re.subn(rf"\b{age}-year-old\b", "[age redacted]-year-old", text, flags=re.I); n += k
    return text, n


def bands(df):
    df = df.copy()
    df["age_band"] = pd.cut(df["firm_age"], [-1, 9, 19, 29, 10_000], labels=["0-9", "10-19", "20-29", "30+"]).astype(str)
    df["size3"] = df["size_band"].map({1: "10-49", 2: "50-299", 3: "50-299", 4: "300+", 5: "300+"})
    return df


def main():
    panel = pd.read_parquet(os.path.join(ROOT, "data", "analysis_panel.parquet"))
    per = pd.read_csv(os.path.join(ROOT, "agent_experiment", "stage_a_personas.csv"))
    # k-anonymity of the original persona attributes within the KIS sample
    k_exact = per.merge(panel.groupby(["wave", "industry2", "size_band", "firm_age", "group_affiliate"]).size().rename("k").reset_index(), how="left")["k"]
    P, Q = bands(panel), bands(per)
    k_pub = Q.merge(P.groupby(["sector", "size3", "age_band"]).size().rename("k").reset_index(), how="left")["k"]
    rep = {"n_personas": int(len(per)), "exact_attributes": {"unique_in_kis_sample": int((k_exact == 1).sum()), "k_le_3": int((k_exact <= 3).sum()), "min_k": int(k_exact.min())},
           "public_table_sector_size3_age4": {"min_k": int(k_pub.min()), "personas_below_5": int((k_pub < 5).sum())}}
    # public persona table
    os.makedirs(PUBDIR, exist_ok=True)
    pub = Q[["persona_id", "sector", "size3", "age_band"]].rename(columns={"size3": "size_band_public", "age_band": "firm_age_band_public"})
    pub.to_csv(os.path.join(PUBDIR, "personas_public.csv"), index=False)
    # redacted logs
    if os.path.exists(PUB):
        shutil.rmtree(PUB)
    os.makedirs(PUB)
    stats = {}
    leaks = 0
    attr_strings = set()
    for _, r in per.iterrows():
        attr_strings.update({r["industry_label"], f"설립 후 {int(r['firm_age'])}년", f"Founded {int(r['firm_age'])} years ago"})
    age_of = {r["persona_id"]: int(r["firm_age"]) for _, r in per.iterrows()}
    labels = sorted(set(per["industry_label"]), key=len, reverse=True)
    n_resp_red = 0
    for root, _, files in os.walk(LOGS):
        rel = os.path.relpath(root, LOGS)
        for fn in files:
            if not fn.endswith(".jsonl") or "_mock" in fn or fn.startswith("transcript_codes"):
                continue
            src = os.path.join(root, fn); dst_dir = os.path.join(PUB, rel) if rel != "." else PUB
            os.makedirs(dst_dir, exist_ok=True)
            n_rec = n_red = 0
            with open(src, encoding="utf-8") as f, open(os.path.join(dst_dir, fn), "w", encoding="utf-8") as g:
                for line in f:
                    r = json.loads(line); n_rec += 1
                    pid = r.get("persona_id", "?")
                    for fld in ("raw", "reason"):
                        if r.get(fld):
                            r[fld], k = redact_response(r[fld], age_of.get(pid), labels); n_resp_red += int(k > 0)
                    if "prompt" in r and r["prompt"]:
                        p2, n = redact_prompt(r["prompt"], pid); n_red += int(n > 0)
                        r["prompt"] = p2; r["prompt_redacted"] = True; r["prompt_sha256_redacted"] = hashlib.sha256(p2.encode()).hexdigest()
                        if any(s in p2 for s in attr_strings):
                            leaks += 1
                    g.write(json.dumps(r, ensure_ascii=False) + "\n")
            stats[os.path.join(rel, fn) if rel != "." else fn] = {"records": n_rec, "prompts_redacted": n_red}
    # episode logs have no prompt but copy them too (already handled above: they are .jsonl without 'prompt')
    rep["files"] = stats; rep["attribute_string_leaks_after_redaction"] = leaks; rep["responses_with_attribute_echo_redacted"] = n_resp_red
    rep["public_personas_csv"] = "public/personas_public.csv"; rep["built"] = time.strftime("%Y-%m-%d %H:%M %Z")
    rep["rule"] = __doc__.strip()
    json.dump(rep, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k not in ("files", "rule")}, ensure_ascii=False, indent=1))
    print({k: v for k, v in stats.items() if v["prompts_redacted"]})
    assert leaks == 0


if __name__ == "__main__":
    main()
