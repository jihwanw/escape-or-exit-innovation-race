#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Register the preregistration on OSF through the API v2 (user's own token; sole author Jihwan Woo).

Verified sources (2026-11-10):
  - schema: GET /v2/schemas/registrations/ -> 'Secondary Data Preregistration' id 64775783798e08000a70407e (v3);
    question keys from GET /v2/schemas/registrations/{id}/schema_blocks/ (saved: docs/sources/osf_schema_blocks_secondary_data_v3.json)
  - draft creation/update: developer.osf.io swagger (POST /v2/draft_registrations/ requires relationships.registration_schema;
    optional branched_from; PATCH attributes.registration_responses)
  - registration creation: osf.io source api/registrations/serializers.py RegistrationCreateSerializer — for API version >= 2.19
    POST /v2/registrations/ with attributes {draft_registration_id, embargo_end_date (null = immediate), included_node_ids};
    the registration then enters a 48-hour approval window (website/settings/defaults.py REGISTRATION_APPROVAL_TIME = 2 days;
    EMBARGO_END_DATE_MIN 2 days, MAX 4 years).
Stages (each writes prereg/osf_state.json): --project  --upload  --draft  --fill  --register. The last one is irreversible.
"""
import argparse
import configparser
import json
import os
import re
import sys
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STATE = os.path.join(HERE, "osf_state.json")
API = "https://api.osf.io/v2"
VER = "2.20"
SCHEMA_ID = "64775783798e08000a70407e"  # Secondary Data Preregistration v3
TITLE = "Escape or Exit: Entry Threat, Technology Gap, and the Two Margins of the Innovation Race (preregistration; KIS 2022-2025 and LLM-agent experiments)"
UPLOADS = [("/tmp/escape_or_exit_prereg-v1_no_logs.zip", "escape_or_exit_prereg-v1_code_results.zip"),
           (os.path.join(HERE, "PREREGISTRATION.md"), "PREREGISTRATION.md"), (os.path.join(HERE, "agent_predictions_v1.json"), "agent_predictions_v1.json"),
           (os.path.join(HERE, "SHA256SUMS.txt"), "SHA256SUMS.txt"), (os.path.join(ROOT, "code", "analysis_prereg.py"), "analysis_prereg.py"),
           (os.path.join(ROOT, "docs", "HYPOTHESES_GATE_B.md"), "HYPOTHESES_GATE_B.md"), (os.path.join(ROOT, "model", "MODEL_NOTES.md"), "MODEL_NOTES.md"),
           (os.path.join(ROOT, "item_maps", "item_map_escape_exit.json"), "item_map_escape_exit.json")]


def token():
    cfg = configparser.ConfigParser(); cfg.read("/Users/jihwanw/PhD/code/api_info/api_keys.ini")
    return cfg["osf"]["token"]


def H():
    return {"Authorization": f"Bearer {token()}", "Content-Type": "application/vnd.api+json", "Accept": f"application/vnd.api+json;version={VER}"}


def load_state():
    return json.load(open(STATE, encoding="utf-8")) if os.path.exists(STATE) else {}


def save_state(st):
    st["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S%z"); json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def check(r, what):
    if r.status_code >= 300:
        print(what, "FAILED", r.status_code, r.text[:1500]); sys.exit(1)
    return r.json() if r.text else {}


# ------------------------------------------------------------------------------------------------------- responses
def md_sections():
    """Parse PREREGISTRATION.md into {label: text} using the '**Label.**' paragraph convention and '## ' headings."""
    txt = open(os.path.join(HERE, "PREREGISTRATION.md"), encoding="utf-8").read()
    out = {}
    cur = None; buf = []
    for line in txt.split("\n"):
        m = re.match(r"^\*\*(.+?)\*\*\s*(.*)$", line)
        h = re.match(r"^## (.+)$", line)
        if m or h:
            if cur: out[cur] = "\n".join(buf).strip()
            cur = (m.group(1) if m else "##" + h.group(1)).strip().rstrip("."); buf = [m.group(2)] if m else []
        else:
            buf.append(line)
    if cur: out[cur] = "\n".join(buf).strip()
    return out


def plain(s):
    s = re.sub(r"\*\*(.*?)\*\*", r"\1", s); s = re.sub(r"`([^`]*)`", r"\1", s)
    return s.strip()


def build_responses():
    S = md_sections()
    pred = json.load(open(os.path.join(HERE, "agent_predictions_v1.json"), encoding="utf-8"))
    get = lambda k: plain(S.get(k, ""))  # noqa: E731
    # hypotheses: H1-H6 bullets + frozen prediction table (plain text)
    hyp = get("Hypotheses (directional; derived from the finite-horizon innovation-race model in model/MODEL_NOTES.md; approved at gate B on 2026-11-10)")
    tbl = ["Frozen theory and agent predictions (prereg/agent_predictions_v1.json, SHA256 " + open(os.path.join(HERE, "SHA256SUMS.txt")).read().split()[0] + "):"]
    for h, p in pred["predictions"].items():
        a = p["stage_a"]; b = p["stage_b"]
        tbl.append(f"{h}: theory {p['theory_sign']}; Stage A consensus {a['consensus'] if a else 'n/a'} ({', '.join(f'{k} {v}' for k, v in a['arm_calls'].items()) if a else '-'}); "
                   f"Stage B consensus {b['consensus']} ({', '.join(f'{k} {v}' for k, v in b['arm_calls'].items())}).")
    hyp_full = ("Six directional hypotheses derived from the finite-horizon innovation-race model (model/MODEL_NOTES.md), approved at gate B on 2026-11-10. " + hyp + "\n\n" + "\n".join(tbl)) + "\n\nSign calls: '+' if the 95% persona-bootstrap CI of the agent contrast lies above 0, '-' below 0, '0' otherwise; consensus = at least 3 of 4 model x language arms agree. All six hypotheses are directional (direction stated above)."
    measured = (get("Measured variables (survey items used in the confirmatory models; wording from the questionnaires, per wave)") + "\n\n" +
                "Scales / indices.\n" + get("Scales / indices") + "\n\nTransformations and coding.\n" + get("Transformations"))
    models = get("Statistical models, inference criteria, sensitivity analyses, backup plan and exploratory analyses")
    models = ("The statistical models, inference criteria, sensitivity analyses, backup plan and exploratory analyses " +
              models.replace("(frozen; SHA256 below)", "(frozen; SHA256 in the attached SHA256SUMS.txt)").replace("```", "")).strip()
    agent = get("##LLM-agent experiments (completed before this registration; design and results frozen)")
    R = {
        "72-2": get("Research questions"),
        "72-4": hyp_full,
        "72-7": get("Data sets"),
        "72-9": "The dataset is available through protected access",
        "72-14": "KIS microdata: research-use provision files from STEPI (licensed, not redistributable; the analysis panel is excluded from the public package and identified by SHA256). KOSIS entry rates: open API.",
        "72-16": "KIS: officially approved national statistic no. 395001 (STEPI), waves 2022, 2023, 2024, 2025. KOSIS table DT_6BD1101 (Business Demography Statistics), https://kosis.kr/openapi/Param/statisticsParameterData.do (orgId 101).",
        "72-18": get("Date of download or access"),
        "72-20": get("Data source") + "\n\n" + get("Sampling and data collection procedures"),
        "72-24": get("Codebook") + " Files attached to this registration: PREREGISTRATION.md, agent_predictions_v1.json, SHA256SUMS.txt, analysis_prereg.py, HYPOTHESES_GATE_B.md, MODEL_NOTES.md, item_map_escape_exit.json and escape_or_exit_prereg-v1_code_results.zip (git tag prereg-v1 without agent logs and persona file).",
        "72-29": get("Manipulated variables") + "\n\n" + agent,
        "72-33": measured,
        "72-35": get("Missing data"),
        "72-37": get("Data inclusion / exclusion") + "\n\n" + get("Sample size and power").split(" Synthetic-outcome")[0],
        "72-39": get("Outliers"),
        "72-41": get("Weights"),
        "72-44": get("Prior work based on the dataset") + "\n\nPrior research activity: " + get("Prior research activity"),
        "72-46": get("Prior knowledge of the current data set") + "\n\nMoment of preregistration: " + get("Moment of preregistration") + "\n\nEmbargo log: " + get("Embargo log"),
        "72-49": models + "\n\nFollow-up analyses: " + get("Follow-up analyses"),
        "72-51": "Minimum effects of interest = the 80%-power MDEs of the synthetic-outcome power analysis (results/02_marginals.json F): abandonment interaction 0.015 (probability change per SD of the threat residual within gap3 = 0), pre-emption interaction 0.010 (within gap3 = 2); industry-level (entry-rate) interactions 0.015 and 0.010. H6 equivalence bound delta = 0.010.",
        "72-53": get("Sample size and power"),
        "72-55": "See the decision rule in the Statistical models field: one-sided tests for H1-H5 at alpha = 0.05 with Holm adjustment across the five; primary inference = wild cluster bootstrap-t (Rademacher, 999 draws, clusters = industry2 x wave) p-values and percentile-t confidence intervals; cluster-robust t reported as secondary. 'Supported' requires the predicted sign and Holm-adjusted one-sided wild p < 0.05. H6 is an equivalence test: 90% wild percentile-t CI of b(entry_rate x g2) within [-0.010, +0.010]. Pre-registered placebo items (ME6, ME8) must show no significant interaction (two-sided 5%). H2 is falsified only if both the perceived and the objective coefficient are <= 0.",
        "72-57": get("Statistical analysis backup plan"),
        "72-59": "Pre-registered robustness (reported, not used for the decision): raw 0-5 entry_threat instead of the residual; industry2 x wave fixed effects; KIS sampling weights; excluding wave 2023S; manufacturing / services split; exit_strict and exit_full as alternative abandonment outcomes; logit average marginal effects. Pipeline controls run before registration: known-answer simulation (results/06_kis_main_simulate.json) and 30-draw permutation null (results/06_kis_main_permute.json), which is the reason the wild cluster bootstrap-t is the primary inference.",
        "72-61": get("Exploratory analyses [exploratory]"),
    }
    for k, v in R.items():
        assert v and len(v) > 10, f"empty response for {k}"
    return R


# ------------------------------------------------------------------------------------------------------- stages
def stage_project(st):
    if st.get("node_id"):
        print("project exists", st["node_id"]); return
    body = {"data": {"type": "nodes", "attributes": {"title": TITLE, "category": "project", "public": False,
                                                        "description": "Preregistration container for 'Escape or Exit' (theory + Korean Innovation Survey 2022-2025 + LLM-agent experiments). Sole author: Jihwan Woo. Frozen state = git tag prereg-v1.",
                                                        "tags": ["preregistration", "innovation race", "Korean Innovation Survey", "entry threat", "LLM agents"]}}}
    d = check(requests.post(f"{API}/nodes/", headers=H(), json=body, timeout=60), "create project")
    st["node_id"] = d["data"]["id"]; st["node_url"] = d["data"]["links"]["html"]; save_state(st)
    print("project created", st["node_id"], st["node_url"])


def stage_upload(st):
    files_meta = check(requests.get(f"{API}/nodes/{st['node_id']}/files/", headers=H(), timeout=60), "list providers")
    osfstorage = [p for p in files_meta["data"] if p["attributes"]["name"] == "osfstorage"][0]
    upload_url = osfstorage["links"]["upload"]
    st.setdefault("uploads", {})
    for path, name in UPLOADS:
        if name in st["uploads"]:
            print("already uploaded", name); continue
        with open(path, "rb") as f:
            r = requests.put(upload_url, params={"kind": "file", "name": name}, headers={"Authorization": f"Bearer {token()}"}, data=f, timeout=600)
        if r.status_code == 409:
            print("exists (409)", name); st["uploads"][name] = {"status": "exists"}; save_state(st); continue
        d = check(r, f"upload {name}")
        st["uploads"][name] = {"id": d["data"]["id"], "size": d["data"]["attributes"].get("size"), "sha256": (d["data"]["attributes"].get("extra") or {}).get("hashes", {}).get("sha256")}
        save_state(st); print("uploaded", name, st["uploads"][name])


def stage_draft(st):
    if st.get("draft_id"):
        print("draft exists", st["draft_id"]); return
    body = {"data": {"type": "draft_registrations", "attributes": {"title": TITLE},
                     "relationships": {"registration_schema": {"data": {"type": "registration-schemas", "id": SCHEMA_ID}},
                                       "branched_from": {"data": {"type": "nodes", "id": st["node_id"]}}}}}
    d = check(requests.post(f"{API}/draft_registrations/", headers=H(), json=body, timeout=60), "create draft")
    st["draft_id"] = d["data"]["id"]; save_state(st); print("draft created", st["draft_id"])


def stage_fill(st):
    R = build_responses()
    body = {"data": {"id": st["draft_id"], "type": "draft_registrations", "attributes": {"registration_responses": R, "title": TITLE,
                                                                                      "description": "Preregistration of a confirmatory analysis of the Korean Innovation Survey (2022-2025) testing innovation-race predictions about entry threat, technology gap, pre-emption and abandonment, with LLM-agent predictions frozen before the survey test.",
                                                                                      "category": "project"}}}
    d = check(requests.patch(f"{API}/draft_registrations/{st['draft_id']}/", headers=H(), json=body, timeout=120), "fill draft")
    got = d["data"]["attributes"]["registration_responses"]
    missing = [k for k in R if not got.get(k)]
    st["filled_keys"] = sorted(got.keys()); st["response_chars"] = {k: len(v) for k, v in R.items()}; save_state(st)
    print("draft filled; keys", len(got), "missing", missing, "total chars", sum(len(v) for v in R.values()))
    json.dump(R, open(os.path.join(HERE, "osf_registration_responses.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def stage_register(st, embargo_end):
    if st.get("registration_id"):
        print("registration exists", st["registration_id"]); return
    attrs = {"draft_registration_id": st["draft_id"], "included_node_ids": []}
    attrs["embargo_end_date"] = embargo_end  # None => public immediately after the 48 h approval window
    body = {"data": {"type": "registrations", "attributes": attrs}}
    d = check(requests.post(f"{API}/registrations/", headers=H(), json=body, timeout=120), "create registration")
    a = d["data"]["attributes"]
    st["registration_id"] = d["data"]["id"]; st["registration_url"] = d["data"]["links"]["html"]
    st["registration_attributes"] = {k: a.get(k) for k in ("date_registered", "registration_supplement", "pending_registration_approval", "pending_embargo_approval", "embargo_end_date", "public", "withdrawn")}
    save_state(st); print("REGISTERED", st["registration_id"], st["registration_url"], st["registration_attributes"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    for s in ("project", "upload", "draft", "fill", "register", "dry"):
        ap.add_argument(f"--{s}", action="store_true")
    ap.add_argument("--embargo-end", default=None, help="ISO datetime, e.g. 2028-11-10T00:00:00; omit for a public registration")
    a = ap.parse_args()
    st = load_state()
    if a.dry:
        R = build_responses(); print({k: len(v) for k, v in R.items()}); print(R["72-9"]); print(R["72-18"]); sys.exit(0)
    if a.project: stage_project(st)
    if a.upload: stage_upload(st)
    if a.draft: stage_draft(st)
    if a.fill: stage_fill(st)
    if a.register: stage_register(st, a.embargo_end)
