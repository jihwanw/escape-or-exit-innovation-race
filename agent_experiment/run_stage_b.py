#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage B — dynamic three-period race played by LLM agents against the equilibrium rival of race_env.py (Task 8).

Design (fixed before any real call)
  Units  : 24 personas = Stage A personas P000-P011 (manufacturing) and P020-P031 (services), treatment-free attributes only.
  Factors: gap (3) x threat (2) x noise (2) = 12 cells; placebo (founding-anniversary month) randomised within persona x cell.
  Episode: one (persona, cell, language, model). Each period the agent receives the rules, the history so far and the current
           state (own stage, spend, rival's stage as observed, rival status, entry status) and returns one decision in JSON.
           Options are shown in random order per call (order logged). Up to 3 calls per episode.
  Randomness: environment draws come from numpy Generator seeded by (SEED, episode index); option order from a second
           Generator so that the environment path given the same agent actions is reproducible.
  Parsing: Stage A strict parser. If a call cannot be parsed after 3 attempts the episode stops with status 'parse_failed'
           and is counted, not dropped. Empty responses count as failed attempts.
  Logging: calls  -> logs/stage_b_calls_<model>_<lang>.jsonl   (prompt sha256, prompt, raw, parsed decision, order, state)
           episodes -> logs/stage_b_episodes_<model>_<lang>.jsonl (env.log with every draw, outcome, status)
Controls (--controls, must PASS before any LLM call): seed reproducibility, parser, forbidden vocabulary, template numbers =
  environment constants, runner two-route (mock agent playing the equilibrium policy through the full prompt/parse pipeline
  reproduces model_predictions_for_cell per cell), parse failures preserved. Writes results/05_stage_b_controls_runner.json.
Outputs: results/05_agent_stage_b.json (per cell: quit, accelerate-ever, first, finish, period-1 action shares, no-entry
  subset; hypothesis contrasts with persona bootstrap; within-cell placebo; model predictions and sign agreement).
"""
import argparse
import hashlib
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "prompts"))
sys.path.insert(0, os.path.join(ROOT, "model"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # llm_clients.py (Bedrock client) is vendored next to this script (2026-11-11; previously imported from the ICAIF_files agent directory, identical file)
import race_env as E  # noqa: E402
import race_model as R  # noqa: E402
import stage_b_templates as T  # noqa: E402
from run_stage_a import parse, forbidden_check, call_one, real_client, LETTERS  # noqa: E402

SEED = 20261111
PERSONA_IDS = [f"P{i:03d}" for i in range(0, 12)] + [f"P{i:03d}" for i in range(20, 32)]
LOGDIR = os.path.join(HERE, "logs")
OUT = os.path.join(ROOT, "results", "05_agent_stage_b.json")
CTRL = os.path.join(ROOT, "results", "05_stage_b_controls_runner.json")
DESIGN = os.path.join(HERE, "stage_b_design.csv")
ACT_OF = {"Q": R.Q, "C": R.C, "A": R.A}
KEY_OF = {R.Q: "Q", R.C: "C", R.A: "A"}
U = E.UNIT


def fmt_won(units, lang):
    """Money in 억원 (ko) or billion won (en), from model units (1 unit = 100억원)."""
    v = units * U
    if lang == "ko":
        return f"{v:g}"
    return f"{v / 10:g}"


# ------------------------------------------------------------------------------------------------------- design
def load_personas():
    per = pd.read_csv(os.path.join(HERE, "stage_a_personas.csv")).set_index("persona_id")
    missing = [p for p in PERSONA_IDS if p not in per.index]
    assert not missing, f"personas missing from stage_a_personas.csv: {missing}"
    return per.loc[PERSONA_IDS]


def build_design(rng, personas):
    rows = []
    for pid, pr in personas.iterrows():
        for gap in (0, 1, 2):
            for threat in (0, 1):
                for noise in (0, 1):
                    placebo = int(rng.integers(0, 2))
                    for lang in ("ko", "en"):
                        rows.append(dict(persona_id=pid, gap=gap, threat=threat, noise=noise, placebo=placebo, lang=lang))
    d = pd.DataFrame(rows)
    d["episode_id"] = [f"B{i:05d}" for i in range(len(d))]
    d["ep_index"] = range(len(d))
    return d


# ------------------------------------------------------------------------------------------------------- rendering
def rival_phrase(env, shown, lang):
    s = env.s["rival"]
    if s == R.QUIT:
        return T.RIVAL_QUIT_KO if lang == "ko" else T.RIVAL_QUIT_EN
    if s == R.DONE:
        return T.RIVAL_DONE_KO if lang == "ko" else T.RIVAL_DONE_EN
    est = (T.RIVAL_EST_KO if lang == "ko" else T.RIVAL_EST_EN)[env.noise]
    return (T.RIVAL_ACTIVE_KO if lang == "ko" else T.RIVAL_ACTIVE_EN).format(rx=shown, est=est)


def rival_phrase_short(env, shown, lang):
    """History-line version (no trailing sentence, no final period)."""
    s = env.s["rival"]
    if s == R.QUIT:
        return "개발을 영구히 포기했습니다" if lang == "ko" else "had abandoned its development for good"
    if s == R.DONE:
        return "이미 출시했습니다" if lang == "ko" else "had already launched"
    est = (T.RIVAL_EST_KO if lang == "ko" else T.RIVAL_EST_EN)[env.noise]
    return (f"{shown}단계를 마친 것으로 파악됐습니다{est}" if lang == "ko" else f"was understood to have completed {shown} of the 3 stages{est}")


def prize_phrase(env, lang):
    P = env.P
    scale = P.lam if env.e == 1 else 1.0
    V, W, S = fmt_won(P.V * scale, lang), fmt_won(P.W * scale, lang), fmt_won((P.V + P.W) / 2 * scale, lang)
    unit = "억원" if lang == "ko" else " billion won"
    if env.s["rival"] == R.DONE:
        return f"{W}{unit}" + (" (경쟁사가 이미 출시했으므로)" if lang == "ko" else " (the rival has already launched)")
    if env.s["rival"] == R.QUIT:
        return f"{V}{unit}" + (" (경쟁사가 포기했으므로 먼저 출시하는 것이 됩니다)" if lang == "ko" else " (the rival has abandoned, so you would be first)")
    if lang == "ko":
        return f"경쟁사보다 먼저면 {V}억원, 같은 기간에 함께면 {S}억원, 경쟁사 뒤면 {W}억원"
    return f"{V} billion won if before the rival, {S} billion won if in the same period, {W} billion won if after the rival"


def render(pr, row, env, shown, hist, perm, lang):
    ko = lang == "ko"
    header = (T.HEADER_KO if ko else T.HEADER_EN).format(
        industry=pr["industry_label"], size=(T.SIZE_KO if ko else T.SIZE_EN)[int(pr["size_band"])], age=int(pr["firm_age"]),
        group=(T.GROUP_KO if ko else T.GROUP_EN)[int(pr["group_affiliate"])], placebo=(T.PLACEBO_KO if ko else T.PLACEBO_EN)[int(row["placebo"])])
    rules = (T.RULES_KO if ko else T.RULES_EN).format(threat_rule=(T.THREAT_RULE_KO if ko else T.THREAT_RULE_EN)[env.threat],
                                                     noise_rule=(T.NOISE_RULE_KO if ko else T.NOISE_RULE_EN)[env.noise])
    h = T.HISTORY_HEAD_KO if ko else T.HISTORY_HEAD_EN
    if not hist:
        h += T.HISTORY_NONE_KO if ko else T.HISTORY_NONE_EN
    for hh in hist:
        h += (T.HISTORY_LINE_KO if ko else T.HISTORY_LINE_EN).format(
            t=hh["t"], act=(T.ACT_KO if ko else T.ACT_EN)[hh["act"]], cost=fmt_won(hh["cost_units"], lang), succ=(T.SUCC_KO if ko else T.SUCC_EN)[hh["success"]],
            rival=hh["rival_after_phrase_" + lang], entry=(T.ENTRY_HIST_KO if ko else T.ENTRY_HIST_EN)[hh["entry_state"]])
    entry_now = -1 if env.threat == 0 else env.e
    state = (T.STATE_KO if ko else T.STATE_EN).format(
        t=env.t, remaining=env.P.T - env.t + 1, ax=env.x["agent"], spent=fmt_won(env.cost["agent"], lang), rival_now=rival_phrase(env, shown, lang),
        entry_now=(T.ENTRY_NOW_KO if ko else T.ENTRY_NOW_EN)[entry_now], prize_now=prize_phrase(env, lang))
    opts = "\n".join(f"{L}. {(T.OPTIONS_KO if ko else T.OPTIONS_EN)[perm[i]]}" for i, L in enumerate(LETTERS))
    dec = (T.DECISION_KO if ko else T.DECISION_EN).format(options=opts)
    return header + "\n" + rules + "\n" + h + state + dec


# ------------------------------------------------------------------------------------------------------- episode
def play_episode(client, model, row, pr, mock=None):
    """mock: None (real LLM), 'equilibrium' (agent = solver policy through the prompt/parse pipeline), or 'garbage'
    (returns unparsable text; tests the parse-failure path)."""
    lang = row["lang"]; ep = int(row["ep_index"])
    env_rng = np.random.default_rng([SEED, ep])
    ui_rng = np.random.default_rng([SEED + 1, ep])
    env = E.RaceEnv(int(row["gap"]), int(row["threat"]), int(row["noise"]), env_rng)
    hist, calls, status = [], [], "complete"
    while not env.done:
        env.entry_shock()
        shown, true = env.observe_rival_position()
        # close the previous history line with what the agent now observes about the rival
        if hist:
            hist[-1]["rival_after_phrase_ko"] = rival_phrase_short(env, shown, "ko"); hist[-1]["rival_after_phrase_en"] = rival_phrase_short(env, shown, "en")
            hist[-1]["rival_shown_after"] = int(shown); hist[-1]["rival_status_after"] = int(env.s["rival"])
        a = None
        if env.agent_active():
            perm = ui_rng.permutation(["C", "A", "Q"]).tolist()
            prompt = render(pr, row, env, shown, hist, perm, lang)
            if mock == "equilibrium":
                act = env.equilibrium_agent_action(shown)
                raw, attempts, err = json.dumps({"decision": LETTERS[perm.index(KEY_OF[act])], "reason": "mock"}), 1, None
            elif mock == "garbage":
                raw, attempts, err = ("no json here" if ui_rng.random() < 0.3 else json.dumps({"decision": LETTERS[int(ui_rng.integers(0, 3))], "reason": "mock"})), 1, None
            else:
                raw, attempts, err = call_one(client, model, prompt)
            dec, reason, pstatus = parse(raw, perm)
            calls.append({"episode_id": row["episode_id"], "persona_id": row["persona_id"], "model": model, "lang": lang, "t": env.t,
                          "gap": int(row["gap"]), "threat": int(row["threat"]), "noise": int(row["noise"]), "placebo": int(row["placebo"]),
                          "order": "".join(perm), "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(), "prompt": prompt, "raw": raw,
                          "attempts": attempts, "error": err, "decision": dec, "reason": reason, "parse_status": pstatus,
                          "state": {"agent_x": env.x["agent"], "rival_x_true": int(true), "rival_x_shown": int(shown), "rival_status": int(env.s["rival"]),
                                    "entry": int(env.e), "spent_units": env.cost["agent"]}, "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
            if dec is None:
                status = "parse_failed"
                break
            a = ACT_OF[dec]
            hist.append({"t": env.t, "act": dec, "cost_units": R.cost(env.P, a) if a != R.Q else 0.0, "entry_state": (-1 if env.threat == 0 else int(env.e)),
                         "rival_after_phrase_ko": "", "rival_after_phrase_en": ""})
        r = env.rival_action()
        rec = env.step(a, r)
        if hist and hist[-1]["t"] == rec["t"]:
            hist[-1]["success"] = bool(rec["success"]["agent"])
    outcome = env.outcome() if status == "complete" else None
    episode = {"episode_id": row["episode_id"], "persona_id": row["persona_id"], "model": model, "lang": lang, "gap": int(row["gap"]), "threat": int(row["threat"]),
               "noise": int(row["noise"]), "placebo": int(row["placebo"]), "status": status, "n_calls": len(calls),
               "period1_decision": calls[0]["decision"] if calls else None, "decisions": [c["decision"] for c in calls],
               "env_log": env.log, "outcome": outcome, "agent_role": "L" if env.agent_is_L else "F", "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    return episode, calls


# ------------------------------------------------------------------------------------------------------- run
def run(models, langs, frac=1.0, mock=None, workers=6):
    rng = np.random.default_rng(SEED)
    personas = load_personas()
    design = build_design(rng, personas)
    design.to_csv(DESIGN, index=False)
    sub = design if frac >= 1.0 else design.sample(frac=frac, random_state=SEED)
    os.makedirs(LOGDIR, exist_ok=True)
    tag = f"_mock_{mock}" if mock else ""
    for model in models:
        client = None if mock else real_client(model)
        for lang in langs:
            todo = sub[sub["lang"] == lang]
            epf = os.path.join(LOGDIR, f"stage_b_episodes_{model}_{lang}{tag}.jsonl")
            cf = os.path.join(LOGDIR, f"stage_b_calls_{model}_{lang}{tag}.jsonl")
            done = set()
            if os.path.exists(epf):
                for line in open(epf, encoding="utf-8"):
                    try:
                        done.add(json.loads(line)["episode_id"])
                    except Exception:
                        pass
            todo = todo[~todo["episode_id"].isin(done)]
            print(f"[{model}/{lang}{tag}] episodes to play: {len(todo)} (resumed {len(done)})", flush=True)
            with open(epf, "a", encoding="utf-8") as fe, open(cf, "a", encoding="utf-8") as fc, ThreadPoolExecutor(max_workers=1 if mock else workers) as ex:
                futs = [ex.submit(play_episode, client, model, row, personas.loc[row["persona_id"]], mock) for _, row in todo.iterrows()]
                for i, fu in enumerate(as_completed(futs)):
                    episode, calls = fu.result()
                    for c in calls:
                        fc.write(json.dumps(c, ensure_ascii=False) + "\n")
                    fe.write(json.dumps(episode, ensure_ascii=False, default=str) + "\n"); fe.flush(); fc.flush()
                    if (i + 1) % 50 == 0:
                        print(f"   {i + 1}/{len(todo)}", flush=True)


def drop_failed_episodes(models, langs):
    """Remove parse_failed episodes from the episode logs so that run() replays them (call records are kept)."""
    n = 0
    for model in models:
        for lang in langs:
            epf = os.path.join(LOGDIR, f"stage_b_episodes_{model}_{lang}.jsonl")
            if not os.path.exists(epf):
                continue
            rows = [json.loads(l) for l in open(epf, encoding="utf-8")]
            keep = [r for r in rows if r["status"] == "complete"]
            n += len(rows) - len(keep)
            open(epf, "w", encoding="utf-8").write("".join(json.dumps(r, ensure_ascii=False, default=str) + "\n" for r in keep))
    print(f"dropped {n} parse_failed episodes for replay")
    return n


# ------------------------------------------------------------------------------------------------------- summary
def load_episodes(mock=None):
    tag = f"_mock_{mock}" if mock else ""
    rows = []
    for fn in os.listdir(LOGDIR):
        if fn.startswith("stage_b_episodes_") and fn.endswith(f"{tag}.jsonl") and (mock or "_mock_" not in fn):
            for line in open(os.path.join(LOGDIR, fn), encoding="utf-8"):
                rows.append(json.loads(line))
    return rows


def episode_frame(rows):
    recs = []
    for r in rows:
        o = r["outcome"] or {}
        recs.append({"episode_id": r["episode_id"], "persona_id": r["persona_id"], "model": r["model"], "lang": r["lang"], "gap": r["gap"], "threat": r["threat"],
                     "noise": r["noise"], "placebo": r["placebo"], "status": r["status"], "p1": r["period1_decision"],
                     "quit": float(o.get("agent_quit", np.nan)) if o else np.nan, "accel": float(o.get("agent_accelerated", np.nan)) if o else np.nan,
                     "first": (float(o["agent_first"]) + 0.5 * float(o["both_first"])) if o else np.nan, "finish": float(o.get("agent_finished", np.nan)) if o else np.nan,
                     "entry": float(o.get("entry_occurred", np.nan)) if o else np.nan, "cost": float(o.get("agent_cost_units", np.nan)) if o else np.nan,
                     "net": float(o.get("agent_net_units", np.nan)) if o else np.nan, "periods": o.get("periods_played") if o else None})
    return pd.DataFrame(recs)


def cm(frame, col, cond):
    sub = frame[cond(frame)]
    return float(sub[col].mean()) if len(sub) else np.nan


def contrasts_of(f):
    c = {}
    g = lambda gap, thr: (lambda x: (x.gap == gap) & (x.threat == thr))  # noqa: E731
    c["H1_accel_threat_gap2"] = cm(f, "accel", g(2, 1)) - cm(f, "accel", g(2, 0))
    c["H1_accel_threat_gap2_noentry"] = cm(f[f.entry == 0], "accel", g(2, 1)) - cm(f, "accel", g(2, 0))
    c["H2_quit_threat_gap0"] = cm(f, "quit", g(0, 1)) - cm(f, "quit", g(0, 0))
    c["H2_quit_threat_gap0_noentry"] = cm(f[f.entry == 0], "quit", g(0, 1)) - cm(f, "quit", g(0, 0))
    c["quit_threat_gap2"] = cm(f, "quit", g(2, 1)) - cm(f, "quit", g(2, 0))
    c["accel_threat_gap0"] = cm(f, "accel", g(0, 1)) - cm(f, "accel", g(0, 0))
    c["H3_quit_threat_gap0_minus_gap2"] = c["H2_quit_threat_gap0"] - c["quit_threat_gap2"]
    c["H4_accel_threat_gap2_minus_gap0"] = c["H1_accel_threat_gap2"] - c["accel_threat_gap0"]
    c["H5_quit_gap0_minus_gap2"] = cm(f, "quit", lambda x: x.gap == 0) - cm(f, "quit", lambda x: x.gap == 2)
    c["accel_threat_gap1"] = cm(f, "accel", g(1, 1)) - cm(f, "accel", g(1, 0))
    c["quit_threat_gap1"] = cm(f, "quit", g(1, 1)) - cm(f, "quit", g(1, 0))
    c["first_threat_gap2"] = cm(f, "first", g(2, 1)) - cm(f, "first", g(2, 0))
    c["noise_accel"] = cm(f, "accel", lambda x: x.noise == 1) - cm(f, "accel", lambda x: x.noise == 0)
    c["noise_quit"] = cm(f, "quit", lambda x: x.noise == 1) - cm(f, "quit", lambda x: x.noise == 0)
    for col, name in (("accel", "placebo_accel_within_cell"), ("quit", "placebo_quit_within_cell")):
        cell = f.groupby(["gap", "threat", "noise", "placebo"])[col].mean().unstack("placebo")
        c[name] = float((cell[1] - cell[0]).mean()) if (1 in cell.columns and 0 in cell.columns) else np.nan
    return c


def summarise(mock=None, n_boot=500):
    rows = load_episodes(mock)
    if not rows:
        return {"n_episodes": 0}
    df = episode_frame(rows)
    res = {"n_episodes": int(len(df)), "status_counts": df["status"].value_counts().to_dict(), "by_model_lang": {},
           "estimators": {"cells": "episode-level shares among completed episodes; accel = accelerated in at least one period; first = agent first (+0.5 if simultaneous)",
                          "noentry": "same shares among completed episodes in which no entry occurred within the 3 periods (model's threat-conditional version)",
                          "contrasts": "differences of cell shares; CI = 95 % percentile bootstrap over personas; '_noentry' contrasts use the no-entry subset in the threat cell",
                          "placebo": "within-cell contrast averaged over the 12 cells with equal weights"},
           "model_predictions": {f"g{g}t{t}n{n}": E.model_predictions_for_cell(g, t, n) for g in (0, 1, 2) for t in (0, 1) for n in (0, 1)},
           "model_period1_action_probs": {f"g{g}t{t}": E.model_period1_action_probs(g, t) for g in (0, 1, 2) for t in (0, 1)}}
    rng = np.random.default_rng(SEED)
    for (model, lang), d in df.groupby(["model", "lang"]):
        ok = d[d.status == "complete"].copy()
        cells = []
        for (gap, thr, nz), c in ok.groupby(["gap", "threat", "noise"]):
            ne = c[c.entry == 0]
            cells.append({"gap": int(gap), "threat": int(thr), "noise": int(nz), "n": int(len(c)), "P_quit": float(c.quit.mean()), "P_accel": float(c.accel.mean()),
                          "P_first": float(c["first"].mean()), "P_finish": float(c.finish.mean()), "P_entry": float(c.entry.mean()), "mean_cost_units": float(c.cost.mean()),
                          "mean_net_units": float(c.net.mean()), "p1_shares": {k: float((c.p1 == k).mean()) for k in ("C", "A", "Q")},
                          "noentry": {"n": int(len(ne)), "P_quit": float(ne.quit.mean()) if len(ne) else None, "P_accel": float(ne.accel.mean()) if len(ne) else None,
                                      "P_first": float(ne["first"].mean()) if len(ne) else None}})
        point = contrasts_of(ok)
        pids = ok.persona_id.unique()
        boots = {k: [] for k in point}
        for _ in range(n_boot):
            samp = ok[ok.persona_id.isin(rng.choice(pids, len(pids), replace=True))]
            cb = contrasts_of(samp)
            for k in boots:
                boots[k].append(cb[k])
        est = {}
        for k, v in boots.items():
            v = np.array(v, dtype=float); v = v[np.isfinite(v)]
            p2 = float(max(2 * min(np.mean(v <= 0), np.mean(v >= 0)), 1.0 / max(len(v), 1))) if len(v) else None
            est[k] = {"estimate": None if not np.isfinite(point[k]) else float(point[k]), "ci95": [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if len(v) else None,
                      "p_two_sided_boot": p2}
        # re-randomisation p-values (placebo permuted within cell, 2000 draws). The persona bootstrap keeps the placebo
        # assignment fixed; because the two models share the environment draws of each episode index within a language,
        # chance imbalance of environment luck across placebo labels is common to both arms of a language — only the
        # re-randomisation distribution is the right null for the placebo check.
        def within_cell_contrast(frame, col):
            cell = frame.groupby(["gap", "threat", "noise", "placebo"])[col].mean().unstack("placebo")
            return float((cell[1] - cell[0]).mean()) if (1 in cell.columns and 0 in cell.columns) else np.nan
        rr = np.random.default_rng(SEED + 7)
        fam = {}
        for col, name in (("accel", "placebo_accel_within_cell"), ("quit", "placebo_quit_within_cell")):
            obs = within_cell_contrast(ok, col); perm = []
            for _ in range(2000):
                sh = ok.copy(); sh["placebo"] = sh.groupby(["gap", "threat", "noise"])["placebo"].transform(lambda s_: rr.permutation(s_.values))
                perm.append(within_cell_contrast(sh, col))
            perm = np.array(perm); fam[name] = float(max(np.mean(np.abs(perm) >= abs(obs) - 1e-12), 1 / len(perm)))
        failed = d[d.status != "complete"]
        res["by_model_lang"][f"{model}/{lang}"] = {"n_complete": int(len(ok)), "n_parse_failed": int(len(failed)), "cells": cells, "contrasts": est,
                                                   "overall": {"P_quit": float(ok.quit.mean()), "P_accel": float(ok.accel.mean()), "P_first": float(ok["first"].mean())}, "null_family_p": fam,
                                                   "failed_by_cell": {f"g{g}t{t}n{n}": int(v) for (g, t, n), v in failed.groupby(["gap", "threat", "noise"]).size().items()},
                                                   "failed_by_placebo": {str(k): int(v) for k, v in failed.placebo.value_counts().items()},
                                                   "failure_note": "parse_failed episodes are fable 'refusal' stop reasons (0 output tokens, deterministic for the prompt text; probe agent_experiment/probes/probe_fable_empty_20261110.json); gpt56 had none"}
    allp = {f"{arm}:{k}": v for arm, d in res["by_model_lang"].items() for k, v in d["null_family_p"].items()}
    names = list(allp); pv = np.array([allp[k] for k in names]); order = np.argsort(pv); adj = np.empty(len(pv)); run_max = 0.0
    for rank, i in enumerate(order):
        run_max = max(run_max, min(1.0, (len(pv) - rank) * pv[i])); adj[i] = run_max
    res["null_family_holm"] = {"raw_p": allp, "holm_adjusted_p": {k: float(a) for k, a in zip(names, adj)}, "min_holm_p": float(adj.min()) if len(adj) else None,
                               "kill_test_iii_triggered": bool(len(adj) and adj.min() < 0.05),
                               "rule": "within-cell placebo contrasts (accelerate-ever, quit) in every arm form one family; p-values are two-sided re-randomisation p (placebo permuted within cell, 2000 draws); Holm-adjusted p < 0.05 fires the kill test",
                               "design_note": "episode environment draws are seeded by episode index, which is shared by the two models within a language; the two arms of a language are therefore not independent replications for this check"}
    return res


# ------------------------------------------------------------------------------------------------------- controls
def template_numbers_match_environment():
    b = E.BASE; u = E.UNIT
    expect = {"K": (b["K"], ["3단계", "3 stages"]), "T": (b["T"], ["모두 3번", "3 development periods in total"]),
              "cC": (round(b["cC"] * u), ["8억원", "0.8 billion won"]), "cA": (round(b["cA"] * u), ["25억원", "2.5 billion won"]),
              "pC": (b["pC"], ["확률 50%", "50% chance"]), "pA": (b["pA"], ["확률 80%", "80% chance"]),
              "V": (round(b["V"] * u), ["약 100억원", "about 10 billion won"]), "W": (round(b["W"] * u), ["약 30억원", "about 3 billion won"]),
              "tie": (round((b["V"] + b["W"]) / 2 * u), ["각 65억원", "6.5 billion won each"]), "theta": (E.THETA[1], ["35%의 확률", "35% probability"]),
              "lam": (b["lam"], ["절반", "halved"]), "obs_noise": (E.OBS_NOISE[1], ["10번 중 4번", "4 times in 10"]),
              "halved_prizes": (round(b["V"] * b["lam"] * u), ["50억원", "5 billion won"])}
    numeric_ok = (expect["K"][0] == 3 and expect["T"][0] == 3 and expect["cC"][0] == 8 and expect["cA"][0] == 25 and expect["pC"][0] == 0.5 and expect["pA"][0] == 0.8
                  and expect["V"][0] == 100 and expect["W"][0] == 30 and expect["tie"][0] == 65 and expect["theta"][0] == 0.35 and expect["lam"][0] == 0.5
                  and expect["obs_noise"][0] == 0.4 and expect["halved_prizes"][0] == 50)
    ko = T.RULES_KO + " ".join(T.THREAT_RULE_KO.values()) + " ".join(T.NOISE_RULE_KO.values()) + " ".join(T.OPTIONS_KO.values()) + " ".join(T.ENTRY_NOW_KO.values())
    en = T.RULES_EN + " ".join(T.THREAT_RULE_EN.values()) + " ".join(T.NOISE_RULE_EN.values()) + " ".join(T.OPTIONS_EN.values()) + " ".join(T.ENTRY_NOW_EN.values())
    missing = {k: [s for s, txt in zip(v[1], (ko, en)) if s not in txt] for k, v in expect.items()}
    missing = {k: v for k, v in missing.items() if v}
    return (numeric_ok and not missing), {"numeric_ok": numeric_ok, "missing_strings": missing, "env_constants": {k: v[0] for k, v in expect.items()}}


def controls():
    res = {"seed": SEED, "checks": {}, "status": "PASS"}

    def rec(name, ok, detail):
        res["checks"][name] = {"pass": bool(ok), "detail": detail}
        if not ok:
            res["status"] = "FAIL"
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {str(detail)[:300]}")

    personas = load_personas()
    design = build_design(np.random.default_rng(SEED), personas)
    design2 = build_design(np.random.default_rng(SEED), personas)
    rec("B1_design_seed_reproducible", design.equals(design2) and len(design) == 24 * 12 * 2, {"n_episodes_design": int(len(design)), "placebo_share": float(design.placebo.mean())})
    # B2 episode reproducibility with the equilibrium mock (same seed -> identical logs)
    row = design.iloc[7]; pr = personas.loc[row.persona_id]
    e1, c1 = play_episode(None, "mock", row, pr, mock="equilibrium"); e2, c2 = play_episode(None, "mock", row, pr, mock="equilibrium")
    rec("B2_episode_seed_reproducible", e1["env_log"] == e2["env_log"] and [c["prompt_sha256"] for c in c1] == [c["prompt_sha256"] for c in c2], {"n_calls": len(c1)})
    # B3 forbidden vocabulary on rendered prompts (all periods of mock episodes across cells)
    texts = []
    for _, r in design.head(96).iterrows():
        _, cc = play_episode(None, "mock", r, personas.loc[r.persona_id], mock="equilibrium")
        texts += [c["prompt"] for c in cc]
    hits = forbidden_check(texts)
    rec("B3_forbidden_vocabulary", not hits, {"hits": hits, "n_prompts": len(texts)})
    # B4 template numbers
    ok, det = template_numbers_match_environment()
    rec("B4_template_numbers_match_environment", ok, det)
    # B5 runner two-route: equilibrium mock through prompt/parse pipeline vs model_predictions_for_cell
    worst = 0.0; detail = {}
    for gap in (0, 1, 2):
        for thr in (0, 1):
            for nz in (0, 1):
                pred = E.model_predictions_for_cell(gap, thr, nz)["unconditional"]
                n = 1500; acc = {"P_quit": 0.0, "P_accel": 0.0, "P_first": 0.0}
                base = design[(design.gap == gap) & (design.threat == thr) & (design.noise == nz) & (design.lang == "ko")].iloc[0].copy()
                for i in range(n):
                    r = base.copy(); r["ep_index"] = 100000 + i + gap * 10000 + thr * 5000 + nz * 2500; r["episode_id"] = f"CTRL{i}"
                    ep, _ = play_episode(None, "mock", r, personas.loc[r.persona_id], mock="equilibrium")
                    o = ep["outcome"]; acc["P_quit"] += o["agent_quit"]; acc["P_accel"] += o["agent_accelerated"]; acc["P_first"] += o["agent_first"] + 0.5 * o["both_first"]
                emp = {k: v / n for k, v in acc.items()}
                d = {k: abs(emp[k] - pred[k]) for k in emp}; worst = max(worst, max(d.values()))
                detail[f"g{gap}t{thr}n{nz}"] = {"model": {k: round(pred[k], 4) for k in emp}, "runner_mock": {k: round(v, 4) for k, v in emp.items()}}
    rec("B5_runner_two_route_equilibrium_mock_vs_model", worst < 0.05, {"max_abs_diff": worst, "n_per_cell": 1500, "cells": detail})
    # B6 parse-failure path preserved (garbage mock), using temporary log files
    for fn in os.listdir(LOGDIR) if os.path.exists(LOGDIR) else []:
        if "_mock_garbage" in fn:
            os.remove(os.path.join(LOGDIR, fn))
    run(["mockmodel"], ["ko"], frac=0.1, mock="garbage")
    s = summarise(mock="garbage")
    rec("B6_parse_failures_preserved", s["n_episodes"] == int((design.sample(frac=0.1, random_state=SEED)["lang"] == "ko").sum()) and s["status_counts"].get("parse_failed", 0) > 0,
        {"n_episodes": s["n_episodes"], "status_counts": s["status_counts"]})
    # B7 state block consistency: numbers in the prompt equal env internals for a sample of calls
    bad = 0; checked = 0
    for _, r in design.head(48).iterrows():
        ep, cc = play_episode(None, "mock", r, personas.loc[r.persona_id], mock="equilibrium")
        for c in cc:
            st = c["state"]; p = c["prompt"]; checked += 1
            need = [f"3단계 중 {st['agent_x']}단계 완료" if c["lang"] == "ko" else f"{st['agent_x']} of 3 stages completed",
                    (f"쓴 돈 {st['spent_units'] * U:g}억원" if c["lang"] == "ko" else f"so far: {st['spent_units'] * U / 10:g} billion won")]
            if st["rival_status"] == R.ACTIVE:
                need.append(f"{st['rival_x_shown']}단계를 마친 것으로" if c["lang"] == "ko" else f"completed {st['rival_x_shown']} of the 3 stages")
            if any(s not in p for s in need):
                bad += 1
    rec("B7_prompt_state_matches_env", bad == 0, {"prompts_checked": checked, "mismatches": bad})
    res["built"] = time.strftime("%Y-%m-%d %H:%M %Z")
    json.dump(res, open(CTRL, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    print("STATUS", res["status"], "->", CTRL)
    return res["status"] == "PASS"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--controls", action="store_true")
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--summarise", action="store_true")
    ap.add_argument("--retry-failed", action="store_true", help="replay parse_failed episodes (drops them from the episode log first)")
    ap.add_argument("--models", default="fable,gpt56")
    ap.add_argument("--langs", default="ko,en")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    if a.controls:
        sys.exit(0 if controls() else 1)
    if a.retry_failed:
        drop_failed_episodes(a.models.split(","), a.langs.split(","))
        run(a.models.split(","), a.langs.split(","), frac=1.0, workers=a.workers)
    if a.pilot or a.full:
        run(a.models.split(","), a.langs.split(","), frac=0.05 if a.pilot else 1.0, workers=a.workers)
    if a.pilot or a.full or a.summarise or a.retry_failed:
        res = summarise(); res["built"] = time.strftime("%Y-%m-%d %H:%M %Z"); res["mode"] = "pilot" if a.pilot else "full"
        json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
        print(json.dumps({k: res[k] for k in ("n_episodes", "status_counts", "built", "mode")}, ensure_ascii=False))
        for k, v in res.get("by_model_lang", {}).items():
            print(k, "n", v["n_complete"], "overall", {kk: round(vv, 3) for kk, vv in v["overall"].items()})
            print("   contrasts", {kk: (None if vv["estimate"] is None else round(vv["estimate"], 3), None if vv["ci95"] is None else [round(x, 3) for x in vv["ci95"]]) for kk, vv in v["contrasts"].items()})
