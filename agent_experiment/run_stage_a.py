#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage A — one-shot vignette experiment with LLM agents (Task 7).

Design (fixed before any real call; see prompts/stage_a_templates.py and INTERFACE_CARD_llm_clients.md)
  Units  : N_PERSONAS firm profiles sampled (seed) from real KIS rows of data/analysis_panel.parquet, using ONLY
           treatment-free attributes (sector, industry label from the codebook, size band, age, group affiliation).
  Factors: gap (3) x threat (2) x noise (2) x placebo (2) = 24 cells, assigned by seeded randomisation within persona
           blocks so each persona appears in every (gap, threat, noise) cell once with a random placebo value.
  Order  : the three options are shown in a random permutation; the permutation is logged.
  Models : 'fable' and 'gpt56'; languages: ko (primary), en (paraphrase). Each (persona, cell, language, model) once.
  Parsing: own strict parser; decision must be one of the shown letters -> mapped back to {C, A, Q}; anything else is
           recorded as missing with the raw text kept (never dropped).
  Logging: one JSON line per call in agent_experiment/logs/stage_a_<model>_<lang>.jsonl (prompt sha256, prompt, raw
           response, parsed decision, reason, order, attempts, timestamp).
Controls (run_stage_a.py --controls): mock-client dry run (balance, parsing, seed reproducibility, forbidden vocabulary) and the
  interface control that every number in the vignette equals the Stage B environment constant (race_env.BASE).
Pilot: --pilot runs 5 % of the design; --full runs everything (resume-safe).
Outputs: results/04_agent_stage_a.json (cell means; hypothesis contrasts H1-H5 with persona-bootstrap CIs; WITHIN-CELL placebo
  contrast; position effect; model period-1 action probabilities per cell for the theory-vs-agent sign table).
Version history: v1 (ceiling, logs/v1_pilot_ceiling), v2 (head-office placebo, gap-0 quit ceiling; logs/v2_placebo_headoffice,
  results/04_agent_stage_a_v2_placebo_headoffice.json, results/04_stage_a_v2_placebo_diagnosis.json), v3 = current templates.
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
sys.path.insert(0, os.path.join(HERE, "prompts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # llm_clients.py (Bedrock client) is vendored next to this script (2026-11-11; previously imported from the ICAIF_files agent directory, identical file)
import stage_a_templates as T  # noqa: E402

SEED = 20261110
N_PERSONAS = 40
LOGDIR = os.path.join(HERE, "logs")
OUT = os.path.join(ROOT, "results", "04_agent_stage_a.json")
CTRL = os.path.join(ROOT, "results", "04_agent_controls.json")
DESIGN = os.path.join(HERE, "stage_a_design.csv")
LETTERS = ["A", "B", "C"]


# ------------------------------------------------------------------------------------------------------- personas
def industry_labels():
    """Industry names from the codebook value labels in the audited item maps (never typed)."""
    out = {}
    for w in ("2024M", "2025S"):
        m = json.load(open(os.path.join(ROOT, "item_maps", f"item_map_{w}.json"), encoding="utf-8"))
        reg = {e["construct_id"]: e for e in m["items"] if e.get("register")}
        for v in reg["INDUSTRY2"]["values"]:
            mm = re.match(r"^\s*(\d+)\.\s*(.+)$", v)
            if mm:
                out[int(mm.group(1))] = mm.group(2).strip()
    return out


def sample_personas(rng, n):
    p = pd.read_parquet(os.path.join(ROOT, "data", "analysis_panel.parquet"))
    cols = ["wave", "sector", "industry2", "size_band", "firm_age", "group_affiliate"]
    d = p[cols].dropna().copy()
    d["industry2"] = d["industry2"].astype(int); d["size_band"] = d["size_band"].astype(int)
    d["group_affiliate"] = d["group_affiliate"].astype(int); d["firm_age"] = d["firm_age"].astype(int)
    # stratify: half manufacturing, half services
    out = []
    for sec, k in (("manufacturing", n // 2), ("services", n - n // 2)):
        idx = rng.choice(d.index[d["sector"] == sec], size=k, replace=False)
        out.append(d.loc[idx])
    per = pd.concat(out).reset_index(drop=True)
    labels = industry_labels()
    per["industry_label"] = per["industry2"].map(labels)
    assert per["industry_label"].notna().all(), "industry label missing"
    per["persona_id"] = [f"P{i:03d}" for i in range(len(per))]
    return per[["persona_id", "wave", "sector", "industry2", "industry_label", "size_band", "firm_age", "group_affiliate"]]


def build_design(rng, personas):
    rows = []
    for _, pr in personas.iterrows():
        for gap in (0, 1, 2):
            for threat in (0, 1):
                for noise in (0, 1):
                    placebo = int(rng.integers(0, 2))
                    for lang in ("ko", "en"):
                        perm = rng.permutation(["C", "A", "Q"]).tolist()  # letters A,B,C map to perm[0..2]
                        rows.append(dict(persona_id=pr["persona_id"], gap=gap, threat=threat, noise=noise, placebo=placebo, lang=lang,
                                         order="".join(perm)))
    return pd.DataFrame(rows)


def render(pr, row):
    perm = list(row["order"])  # e.g. ['Q','C','A'] => A=Q, B=C, C=A
    if row["lang"] == "ko":
        opts = "\n".join(f"{L}. {T.OPTIONS_KO[perm[i]]}" for i, L in enumerate(LETTERS))
        txt = T.PROMPT_KO.format(industry=pr["industry_label"], size=T.SIZE_KO[int(pr["size_band"])], age=int(pr["firm_age"]), group=T.GROUP_KO[int(pr["group_affiliate"])],
                                 placebo=T.PLACEBO_KO[row["placebo"]], gap=T.GAP_KO[row["gap"]], noise=T.NOISE_KO[row["noise"]], threat=T.THREAT_KO[row["threat"]],
                                 options=opts, k1="A", k2="B", k3="C")
    else:
        opts = "\n".join(f"{L}. {T.OPTIONS_EN[perm[i]]}" for i, L in enumerate(LETTERS))
        txt = T.PROMPT_EN.format(industry=pr["industry_label"], size=T.SIZE_EN[int(pr["size_band"])], age=int(pr["firm_age"]), group=T.GROUP_EN[int(pr["group_affiliate"])],
                                 placebo=T.PLACEBO_EN[row["placebo"]], gap=T.GAP_EN[row["gap"]], noise=T.NOISE_EN[row["noise"]], threat=T.THREAT_EN[row["threat"]],
                                 options=opts, k1="A", k2="B", k3="C")
    return txt, perm


def parse(raw, perm):
    """Strict parser. Returns (decision in {C,A,Q} or None, reason or None, status)."""
    if raw is None or not str(raw).strip():
        return None, None, "empty"
    m = re.search(r"\{.*?\}", raw, re.DOTALL)
    if not m:
        return None, None, "no_json"
    try:
        js = json.loads(m.group())
    except Exception:
        # tolerate a trailing comma / single quotes once
        try:
            js = json.loads(m.group().replace("'", '"'))
        except Exception:
            return None, None, "bad_json"
    if not isinstance(js, dict) or "decision" not in js:
        return None, None, "no_decision_key"
    dec = str(js["decision"]).strip().upper()
    dec = dec[0] if dec and dec[0] in LETTERS else dec
    if dec not in LETTERS:
        return None, str(js.get("reason", ""))[:500], "decision_not_in_options"
    return perm[LETTERS.index(dec)], str(js.get("reason", ""))[:500], "ok"


def forbidden_check(texts):
    hits = []
    for t in texts:
        low = t.lower()
        for w in T.FORBIDDEN:
            if w.lower() in low:
                hits.append(w)
    return sorted(set(hits))


# ------------------------------------------------------------------------------------------------------- clients
class MockClient:
    """Deterministic mock for dry runs: answers by a fixed rule so that balance/parsing/seed logic can be tested."""
    def __init__(self, rng):
        self.rng = rng

    def call(self, prompt, **kw):
        r = self.rng.random()
        if r < 0.03:
            return "I think the answer is B but let me explain at length without JSON."
        if r < 0.05:
            return '{"decision": "D", "reason": "x"}'
        letter = self.rng.choice(LETTERS)
        return f'Here is my answer: {{"decision": "{letter}", "reason": "mock"}}'


def real_client(model):
    from llm_clients import FrontierClient
    return FrontierClient(model, workers=6)


def call_one(client, model, prompt, max_attempts=3):
    """Up to max_attempts calls. An empty/whitespace response counts as a failed attempt (fable returned '' in 2/48 pilot
    calls at max_tokens=4000: the thinking block can consume the budget before any text block; the client returns text
    blocks only, so the stop reason is not visible). fable is called with max_tokens=16000 for that reason."""
    err = None
    for a in range(max_attempts):
        try:
            raw = client.call(prompt, max_tokens=32000) if model == "fable" else client.call(prompt)
            if raw is not None and str(raw).strip():
                return raw, a + 1, err
            err = "empty_response"
        except Exception as e:  # noqa
            err = str(e)[:300]
        time.sleep(3 * (a + 1))
    return None, max_attempts, err


# ------------------------------------------------------------------------------------------------------- run
def run(models, langs, frac, mock=False, workers=6):
    rng = np.random.default_rng(SEED)
    personas = sample_personas(rng, N_PERSONAS)
    design = build_design(rng, personas)
    design["design_id"] = [f"D{i:05d}" for i in range(len(design))]
    design.to_csv(DESIGN, index=False)
    personas.to_csv(os.path.join(HERE, "stage_a_personas.csv"), index=False)
    pr_by = personas.set_index("persona_id")
    # forbidden vocabulary on all rendered prompts
    rendered = {d["design_id"]: render(pr_by.loc[d["persona_id"]], d) for _, d in design.iterrows()}
    hits = forbidden_check([t for t, _ in rendered.values()])
    assert not hits, f"forbidden vocabulary in prompts: {hits}"
    sub = design if frac >= 1.0 else design.sample(frac=frac, random_state=SEED)
    os.makedirs(LOGDIR, exist_ok=True)
    summary = {}
    for model in models:
        client = MockClient(np.random.default_rng(SEED + 1)) if mock else real_client(model)
        for lang in langs:
            todo = sub[sub["lang"] == lang]
            logf = os.path.join(LOGDIR, f"stage_a_{model}_{lang}{'_mock' if mock else ''}.jsonl")
            done = set()
            if os.path.exists(logf):
                for line in open(logf, encoding="utf-8"):
                    try:
                        done.add(json.loads(line)["design_id"])
                    except Exception:
                        pass
            todo = todo[~todo["design_id"].isin(done)]
            print(f"[{model}/{lang}] to call: {len(todo)} (resumed {len(done)})", flush=True)

            def work(row):
                prompt, perm = rendered[row["design_id"]]
                raw, attempts, err = call_one(client, model, prompt)
                dec, reason, status = parse(raw, perm)
                return {"design_id": row["design_id"], "persona_id": row["persona_id"], "model": model, "lang": lang,
                        "gap": int(row["gap"]), "threat": int(row["threat"]), "noise": int(row["noise"]), "placebo": int(row["placebo"]),
                        "order": row["order"], "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(), "prompt": prompt,
                        "raw": raw, "attempts": attempts, "error": err, "decision": dec, "reason": reason, "parse_status": status,
                        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z")}

            with open(logf, "a", encoding="utf-8") as f, ThreadPoolExecutor(max_workers=1 if mock else workers) as ex:
                futs = [ex.submit(work, row) for _, row in todo.iterrows()]
                for i, fu in enumerate(as_completed(futs)):
                    f.write(json.dumps(fu.result(), ensure_ascii=False) + "\n"); f.flush()
                    if (i + 1) % 50 == 0:
                        print(f"   {i + 1}/{len(todo)}", flush=True)
            summary[f"{model}/{lang}"] = logf
    return summary


def summarise(mock=False):
    rows = []
    for fn in os.listdir(LOGDIR):
        if fn.startswith("stage_a_") and fn.endswith(".jsonl") and (("_mock" in fn) == mock):
            for line in open(os.path.join(LOGDIR, fn), encoding="utf-8"):
                rows.append(json.loads(line))
    if not rows:
        return {"n": 0}
    df = pd.DataFrame(rows)
    rng = np.random.default_rng(SEED)
    res = {"n_calls": int(len(df)), "parse_status": df["parse_status"].value_counts().to_dict(), "by_model_lang": {},
           "template_version": "v3", "estimators": {
               "cell_means": "share of parsed decisions per (gap, threat, noise) cell, pooled over placebo and option order",
               "hypothesis_contrasts": "differences of cell means (threat 1 - threat 0 within a gap; gap 0 - gap 2 pooled over threat); CI = 95 % percentile bootstrap over personas (500 draws)",
               "placebo": "WITHIN-CELL contrast mean(y | placebo 1) - mean(y | placebo 0) averaged over the 12 cells with equal weights (the v2 marginal contrast was biased by chance imbalance of the placebo across cells; results/04_stage_a_v2_placebo_diagnosis.json)",
               "position": "share of decisions equal to the first-listed option minus 1/3 (order randomised per row)"}}
    # model counterpart of the one-shot period-1 decision, per (gap, threat)
    try:
        sys.path.insert(0, HERE)
        import race_env as E
        res["model_period1_action_probs"] = {f"g{g}t{t}": E.model_period1_action_probs(g, t) for g in (0, 1, 2) for t in (0, 1)}
    except Exception as e:  # noqa
        res["model_period1_action_probs"] = {"error": str(e)[:200]}

    def cellmean(frame, col, cond):
        sub = frame[cond(frame)]
        return sub[col].mean() if len(sub) else np.nan

    def contrasts_of(frame):
        c = {}
        c["H1_accel_threat_gap2"] = cellmean(frame, "is_A", lambda f: (f.gap == 2) & (f.threat == 1)) - cellmean(frame, "is_A", lambda f: (f.gap == 2) & (f.threat == 0))
        c["H2_quit_threat_gap0"] = cellmean(frame, "is_Q", lambda f: (f.gap == 0) & (f.threat == 1)) - cellmean(frame, "is_Q", lambda f: (f.gap == 0) & (f.threat == 0))
        c["quit_threat_gap2"] = cellmean(frame, "is_Q", lambda f: (f.gap == 2) & (f.threat == 1)) - cellmean(frame, "is_Q", lambda f: (f.gap == 2) & (f.threat == 0))
        c["accel_threat_gap0"] = cellmean(frame, "is_A", lambda f: (f.gap == 0) & (f.threat == 1)) - cellmean(frame, "is_A", lambda f: (f.gap == 0) & (f.threat == 0))
        c["H3_quit_threat_gap0_minus_gap2"] = c["H2_quit_threat_gap0"] - c["quit_threat_gap2"]
        c["H4_accel_threat_gap2_minus_gap0"] = c["H1_accel_threat_gap2"] - c["accel_threat_gap0"]
        c["H5_quit_gap0_minus_gap2"] = cellmean(frame, "is_Q", lambda f: f.gap == 0) - cellmean(frame, "is_Q", lambda f: f.gap == 2)
        c["accel_threat_gap1"] = cellmean(frame, "is_A", lambda f: (f.gap == 1) & (f.threat == 1)) - cellmean(frame, "is_A", lambda f: (f.gap == 1) & (f.threat == 0))
        c["quit_threat_gap1"] = cellmean(frame, "is_Q", lambda f: (f.gap == 1) & (f.threat == 1)) - cellmean(frame, "is_Q", lambda f: (f.gap == 1) & (f.threat == 0))
        c["noise_accel"] = cellmean(frame, "is_A", lambda f: f.noise == 1) - cellmean(frame, "is_A", lambda f: f.noise == 0)
        c["noise_quit"] = cellmean(frame, "is_Q", lambda f: f.noise == 1) - cellmean(frame, "is_Q", lambda f: f.noise == 0)
        for col, name in (("is_A", "placebo_accel_within_cell"), ("is_Q", "placebo_quit_within_cell")):
            cell = frame.groupby(["gap", "threat", "noise", "placebo"])[col].mean().unstack("placebo")
            c[name] = float((cell[1] - cell[0]).mean()) if (1 in cell.columns and 0 in cell.columns) else np.nan
        first = frame["order"].str[0]
        c["pos_first_option"] = (frame["decision"] == first).mean() - 1 / 3
        return c

    for (model, lang), d in df.groupby(["model", "lang"]):
        ok = d[d["parse_status"] == "ok"].copy()
        for a in ("A", "Q", "C"):
            ok[f"is_{a}"] = (ok["decision"] == a).astype(float)
        cells = ok.groupby(["gap", "threat", "noise"]).agg(n=("decision", "size"), p_accel=("is_A", "mean"), p_quit=("is_Q", "mean"), p_cont=("is_C", "mean")).reset_index()
        pids = ok["persona_id"].unique()
        point = contrasts_of(ok)
        boots = {k: [] for k in point}
        for _ in range(500):
            samp = ok[ok["persona_id"].isin(rng.choice(pids, len(pids), replace=True))]
            cb = contrasts_of(samp)
            for k in boots:
                boots[k].append(cb[k])
        est = {}
        for k, v in boots.items():
            v = np.array(v, dtype=float); v = v[np.isfinite(v)]
            # percentile-bootstrap two-sided p for H0: contrast = 0 (2 x min tail share, floored at 1/B)
            p2 = float(max(2 * min(np.mean(v <= 0), np.mean(v >= 0)), 1.0 / max(len(v), 1))) if len(v) else None
            est[k] = {"estimate": float(point[k]) if np.isfinite(point[k]) else None, "ci95": [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if len(v) else None,
                      "p_two_sided_boot": p2}
        # re-randomisation p-values for the null family: the placebo and the option order were randomised WITHIN cell, so the
        # correct null distribution permutes those labels within cell (the persona bootstrap keeps the assignment fixed and
        # ignores chance imbalance of the assignment itself)
        def within_cell_contrast(frame, col):
            cell = frame.groupby(["gap", "threat", "noise", "placebo"])[col].mean().unstack("placebo")
            return float((cell[1] - cell[0]).mean()) if (1 in cell.columns and 0 in cell.columns) else np.nan
        rr = np.random.default_rng(SEED + 7)
        fam = {}
        for col, name in (("is_A", "placebo_accel_within_cell"), ("is_Q", "placebo_quit_within_cell")):
            obs = within_cell_contrast(ok, col); perm = []
            for _ in range(2000):
                sh = ok.copy(); sh["placebo"] = sh.groupby(["gap", "threat", "noise"])["placebo"].transform(lambda s_: rr.permutation(s_.values))
                perm.append(within_cell_contrast(sh, col))
            perm = np.array(perm); fam[name] = float(max(np.mean(np.abs(perm) >= abs(obs) - 1e-12), 1 / len(perm)))
        obs = float((ok["decision"] == ok["order"].str[0]).mean() - 1 / 3); perm = []
        for _ in range(2000):
            sh_order = ok.groupby(["gap", "threat", "noise"])["order"].transform(lambda s_: rr.permutation(s_.values))
            perm.append(float((ok["decision"] == sh_order.str[0]).mean() - 1 / 3))
        perm = np.array(perm); fam["pos_first_option"] = float(max(np.mean(np.abs(perm) >= abs(obs) - 1e-12), 1 / len(perm)))
        res["by_model_lang"][f"{model}/{lang}"] = {"n_ok": int(len(ok)), "cells": cells.round(4).to_dict("records"), "contrasts": est,
                                                   "overall": {"p_accel": float(ok["is_A"].mean()), "p_quit": float(ok["is_Q"].mean()), "p_cont": float(ok["is_C"].mean())},
                                                   "position_share_first_option": float((ok["decision"] == ok["order"].str[0]).mean()), "null_family_p": fam}
    # kill test (iii): the placebo/position family across all arms, Holm-adjusted (family = 3 checks x arms)
    allp = {f"{arm}:{k}": v for arm, d in res["by_model_lang"].items() for k, v in d["null_family_p"].items()}
    names = list(allp); pv = np.array([allp[k] for k in names]); order = np.argsort(pv); adj = np.empty(len(pv)); run_max = 0.0
    for rank, i in enumerate(order):
        run_max = max(run_max, min(1.0, (len(pv) - rank) * pv[i])); adj[i] = run_max
    res["null_family_holm"] = {"raw_p": allp, "holm_adjusted_p": {k: float(a) for k, a in zip(names, adj)}, "min_holm_p": float(adj.min()) if len(adj) else None,
                               "kill_test_iii_triggered": bool(len(adj) and adj.min() < 0.05),
                               "rule": "placebo (within-cell, accelerate and quit) and option-position contrasts in every arm form one family; p-values are two-sided re-randomisation p (labels permuted within cell, 2000 draws); the kill test fires if any Holm-adjusted p < 0.05"}
    return res


def template_numbers_match_environment():
    """Interface control: every number stated in the Stage A text must equal the Stage B environment constant it describes
    (race_env.BASE / THETA / OBS_NOISE / UNIT). Returns (ok, detail)."""
    sys.path.insert(0, HERE)
    import race_env as E
    b = E.BASE; u = E.UNIT
    expect = {
        "K_stages": (b["K"], ["3단계", "3 stages"]), "T_periods": (b["T"], ["최대 3번", "At most 3 development periods"]),
        "cC": (round(b["cC"] * u), ["8억원", "0.8 billion won"]), "cA": (round(b["cA"] * u), ["25억원", "2.5 billion won"]),
        "pC": (b["pC"], ["확률 50%", "50% chance"]), "pA": (b["pA"], ["확률 80%", "80% chance"]),
        "V": (round(b["V"] * u), ["약 100억원", "about 10 billion won"]), "W": (round(b["W"] * u), ["약 30억원", "about 3 billion won"]),
        "tie": (round((b["V"] + b["W"]) / 2 * u), ["각 65억원", "6.5 billion won each"]),
        "theta": (E.THETA[1], ["35%의 확률", "35% probability"]), "lam": (b["lam"], ["절반", "halved"]),
        "obs_noise": (E.OBS_NOISE[1], ["10번 중 4번", "4 times in 10"]),
    }
    # numeric expectations that the strings encode (hand-checked mapping, asserted here so a parameter change breaks the run)
    numeric_ok = (expect["K_stages"][0] == 3 and expect["T_periods"][0] == 3 and expect["cC"][0] == 8 and expect["cA"][0] == 25 and expect["pC"][0] == 0.5
                  and expect["pA"][0] == 0.8 and expect["V"][0] == 100 and expect["W"][0] == 30 and expect["tie"][0] == 65 and expect["theta"][0] == 0.35
                  and expect["lam"][0] == 0.5 and expect["obs_noise"][0] == 0.4)
    texts_ko = T.PROMPT_KO + " ".join(T.OPTIONS_KO.values()) + " ".join(T.THREAT_KO.values()) + " ".join(T.NOISE_KO.values()) + " ".join(T.GAP_KO.values())
    texts_en = T.PROMPT_EN + " ".join(T.OPTIONS_EN.values()) + " ".join(T.THREAT_EN.values()) + " ".join(T.NOISE_EN.values()) + " ".join(T.GAP_EN.values())
    missing = {k: [s for s, txt in zip(v[1], (texts_ko, texts_en)) if s not in txt] for k, v in expect.items()}
    missing = {k: v for k, v in missing.items() if v}
    positions_ok = all(f"{ax}단계를 마쳤고" in T.GAP_KO[g] or (ax == rx and "모두 3단계 중 1단계" in T.GAP_KO[g]) for g, (ax, rx) in E.POSITIONS.items())
    return (numeric_ok and not missing and positions_ok), {"numeric_ok": numeric_ok, "missing_strings": missing, "positions_ok": positions_ok,
                                                           "env_constants": {k: v[0] for k, v in expect.items()}}


def controls():
    """Dry-run controls with the mock client: balance, parsing, seed reproducibility, forbidden vocabulary."""
    rng = np.random.default_rng(SEED)
    personas = sample_personas(rng, N_PERSONAS); design = build_design(rng, personas)
    rng2 = np.random.default_rng(SEED)
    personas2 = sample_personas(rng2, N_PERSONAS); design2 = build_design(rng2, personas2)
    res = {"seed_reproducible": bool(personas.equals(personas2) and design.equals(design2)),
           "n_design_rows": int(len(design)), "n_personas": int(len(personas)),
           "balance_cells": design.groupby(["gap", "threat", "noise"]).size().value_counts().to_dict(),
           "placebo_share": float(design["placebo"].mean()),
           "order_counts": design["order"].value_counts().to_dict(),
           "sector_split": personas["sector"].value_counts().to_dict()}
    # parser tests
    perm = ["Q", "C", "A"]
    tests = {
        "clean": parse('{"decision": "B", "reason": "x"}', perm),
        "prose_around": parse('Sure. {"decision":"C","reason":"y"} Hope this helps', perm),
        "invalid_letter": parse('{"decision": "D", "reason": "z"}', perm),
        "no_json": parse("I would continue.", perm),
        "empty": parse("", perm),
        "error_dict": parse('{"error": "timeout"}', perm),
        "lower_case": parse('{"decision": "a", "reason": ""}', perm),
    }
    res["parser_tests"] = {k: list(v) for k, v in tests.items()}
    res["parser_expected_ok"] = bool(tests["clean"][0] == "C" and tests["prose_around"][0] == "A" and tests["lower_case"][0] == "Q"
                                     and tests["invalid_letter"][2] == "decision_not_in_options" and tests["no_json"][2] == "no_json"
                                     and tests["empty"][2] == "empty" and tests["error_dict"][2] == "no_decision_key")
    # mock run (small) to test logging/resume/missing preservation
    for fn in os.listdir(LOGDIR) if os.path.exists(LOGDIR) else []:
        if "_mock" in fn:
            os.remove(os.path.join(LOGDIR, fn))
    run(["fable"], ["ko"], frac=0.1, mock=True)
    s = summarise(mock=True)
    res["mock_run"] = {"n_calls": s["n_calls"], "parse_status": s["parse_status"]}
    expected_n = int((design.sample(frac=0.1, random_state=SEED)["lang"] == "ko").sum())  # same sampling as run(): sample first, then filter language
    res["missing_preserved"] = bool(sum(v for k, v in s["parse_status"].items() if k != "ok") > 0 and s["n_calls"] == expected_n)
    res["mock_expected_n"] = expected_n
    pr_by = personas.set_index("persona_id")
    hits = forbidden_check([render(pr_by.loc[d["persona_id"]], d)[0] for _, d in design.head(200).iterrows()])
    res["forbidden_vocabulary_hits"] = hits
    tm_ok, tm_detail = template_numbers_match_environment()
    res["template_numbers_match_environment"] = {"ok": tm_ok, **tm_detail}
    res["status"] = "PASS" if (res["seed_reproducible"] and res["parser_expected_ok"] and res["missing_preserved"] and not hits and len(res["balance_cells"]) == 1 and tm_ok) else "FAIL"
    res["built"] = time.strftime("%Y-%m-%d %H:%M %Z")
    json.dump(res, open(CTRL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in ("status", "seed_reproducible", "parser_expected_ok", "missing_preserved", "forbidden_vocabulary_hits", "balance_cells", "n_design_rows", "mock_run", "template_numbers_match_environment")}, ensure_ascii=False, indent=1))
    return res["status"] == "PASS"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--controls", action="store_true")
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--models", default="fable,gpt56")
    ap.add_argument("--langs", default="ko,en")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--summarise", action="store_true", help="re-summarise existing logs without calling any model")
    a = ap.parse_args()
    if a.controls:
        sys.exit(0 if controls() else 1)
    if a.pilot or a.full:
        run(a.models.split(","), a.langs.split(","), frac=0.05 if a.pilot else 1.0, workers=a.workers)
    if a.pilot or a.full or a.summarise:
        res = summarise(); res["built"] = time.strftime("%Y-%m-%d %H:%M %Z"); res["mode"] = "pilot" if a.pilot else "full"
        json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(json.dumps({k: v for k, v in res.items() if k != "by_model_lang"}, ensure_ascii=False, indent=1))
        for k, v in res.get("by_model_lang", {}).items():
            print(k, "overall", {kk: round(vv, 3) for kk, vv in v["overall"].items()}, "| first-option share", round(v["position_share_first_option"], 3))
            print("   contrasts", {kk: (None if vv["estimate"] is None else round(vv["estimate"], 3), None if vv["ci95"] is None else [round(x, 3) for x in vv["ci95"]]) for kk, vv in v["contrasts"].items()})
