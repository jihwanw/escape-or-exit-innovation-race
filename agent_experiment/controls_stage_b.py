#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Controls for the Stage B environment (must PASS before any LLM call). Writes results/05_stage_b_controls.json.
 C1 transition probabilities: empirical success frequency of continue/accelerate equals pC/pA (binomial CI).
 C2 payoff accounting: for every simulated episode, prize and cost equal the formula implied by the recorded actions/successes.
 C3 scripted rival = solver policy: empirical action frequencies of the rival at a fixed state equal the equilibrium mix.
 C4 two-route check of the environment: with the agent replaced by its OWN equilibrium policy, the simulated outcome
    frequencies (quit / accelerate / first / entry) match forward_outcomes() for every cell within Monte-Carlo error.
 C5 seed reproducibility: same seed -> identical episode logs.
 C6 entry process: empirical P(entry within 3 periods) = 1-(1-theta)^3 in threat games; 0 otherwise.
 C7 observation noise: shown rival position differs from truth with frequency obs_noise (when rival active and not at bounds).
"""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import race_env as E  # noqa: E402
import race_model as R  # noqa: E402

OUT = os.path.join(ROOT, "results", "05_stage_b_controls.json")
SEED = 20261110


def play_scripted(gap, threat, noise, rng):
    env = E.RaceEnv(gap, threat, noise, rng)
    shown_vs_true = []
    while not env.done:
        env.entry_shock()
        shown, true = env.observe_rival_position()
        shown_vs_true.append((shown, true, env.s["rival"] == R.ACTIVE, true in (0, env.P.K - 1)))
        a = env.equilibrium_agent_action(shown) if env.agent_active() else None
        r = env.rival_action()
        env.step(a, r)
    return env, shown_vs_true


def main():
    res = {"seed": SEED, "checks": {}, "status": "PASS"}

    def rec(name, ok, detail):
        res["checks"][name] = {"pass": bool(ok), "detail": detail}
        if not ok:
            res["status"] = "FAIL"
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {str(detail)[:400]}")

    rng = np.random.default_rng(SEED)
    # C1/C2/C6/C7 from a large batch of scripted episodes
    n_eps = 4000
    succ = {R.C: [0, 0], R.A: [0, 0]}
    pay_err = 0.0; entry_hits = {0: [0, 0], 1: [0, 0]}; noise_hits = {0: [0, 0], 1: [0, 0]}
    for i in range(n_eps):
        gap, threat, noise = int(rng.integers(0, 3)), int(rng.integers(0, 2)), int(rng.integers(0, 2))
        env, svt = play_scripted(gap, threat, noise, rng)
        P = env.P
        for recd in env.log:
            for who, a in (("agent", recd["agent_action"]), ("rival", recd["rival_action"])):
                if a in (R.C, R.A) and recd["s_before"][who] == R.ACTIVE:
                    succ[a][0] += int(recd["success"][who]); succ[a][1] += 1
        # payoff accounting: recompute from the log
        cost = {"agent": 0.0, "rival": 0.0}
        for recd in env.log:
            for who, a in (("agent", recd["agent_action"]), ("rival", recd["rival_action"])):
                if a in (R.C, R.A) and recd["s_before"][who] == R.ACTIVE:
                    cost[who] += R.cost(P, a)
        pay_err = max(pay_err, abs(cost["agent"] - env.cost["agent"]), abs(cost["rival"] - env.cost["rival"]))
        o = env.outcome()
        # prize consistency
        exp_prize = 0.0
        if o["agent_first"]: exp_prize = P.V * (P.lam if env.log[-1]["entry_state_at_action"] == 1 or env.e == 1 and _entry_before_finish(env) else 1.0)
        entry_hits[threat][0] += int(o["entry_occurred"]); entry_hits[threat][1] += 1
        for shown, true, active, at_bound in svt:
            if active and not at_bound:
                noise_hits[noise][0] += int(shown != true); noise_hits[noise][1] += 1
    pc_hat = succ[R.C][0] / succ[R.C][1]; pa_hat = succ[R.A][0] / succ[R.A][1]
    se_c = (0.5 * 0.5 / succ[R.C][1]) ** 0.5; se_a = (0.8 * 0.2 / succ[R.A][1]) ** 0.5
    rec("C1_transition_probabilities", abs(pc_hat - 0.5) < 4 * se_c and abs(pa_hat - 0.8) < 4 * se_a, {"pC_hat": pc_hat, "n_C": succ[R.C][1], "pA_hat": pa_hat, "n_A": succ[R.A][1]})
    rec("C2_cost_accounting", pay_err < 1e-12, {"max_abs_cost_err": pay_err})
    p_entry_hat = entry_hits[1][0] / entry_hits[1][1]; p_entry_exp = 1 - (1 - 0.35) ** 3
    rec("C6_entry_process", abs(p_entry_hat - p_entry_exp) < 4 * (p_entry_exp * (1 - p_entry_exp) / entry_hits[1][1]) ** 0.5 and entry_hits[0][0] == 0,
        {"p_entry_hat_threat": p_entry_hat, "expected": p_entry_exp, "n": entry_hits[1][1], "entries_in_no_threat_games": entry_hits[0][0]})
    nz = noise_hits[1][0] / max(noise_hits[1][1], 1)
    rec("C7_observation_noise", abs(nz - 0.4) < 4 * (0.4 * 0.6 / max(noise_hits[1][1], 1)) ** 0.5 and noise_hits[0][0] == 0, {"shown_ne_true_rate_noise_games": nz, "n": noise_hits[1][1], "errors_in_exact_games": noise_hits[0][0]})

    # C3 rival action frequencies at the initial state vs equilibrium mix (cell gap=1, threat=1, noise=0, after no entry)
    env = E.RaceEnv(1, 1, 0, np.random.default_rng(1))
    st = env._true_state()
    mix, actsL, actsF = env.sol.policy[st]
    exp = np.zeros(3)
    for w, (pL, pF) in mix:
        exp += w * np.asarray(pF if env.agent_is_L else pL)
    cnt = np.zeros(3)
    for _ in range(20000):
        a = env.rival_action(); cnt[a] += 1
    freq = cnt / cnt.sum()
    rec("C3_rival_policy_equals_equilibrium_mix", np.abs(freq - exp).max() < 0.02, {"state": st, "equilibrium_mix": exp.round(4).tolist(), "empirical": freq.round(4).tolist()})

    # C4 two-route: scripted agent episodes vs exact forward_outcomes, per cell
    worst = 0.0; detail = {}
    for gap in (0, 1, 2):
        for threat in (0, 1):
            for noise in (0, 1):
                pred = E.model_predictions_for_cell(gap, threat, noise)["unconditional"]
                rr = np.random.default_rng(100 + gap * 10 + threat * 2 + noise)
                n = 6000; acc = {"P_quit": 0, "P_accel": 0, "P_first": 0}
                for _ in range(n):
                    env, _ = play_scripted(gap, threat, noise, rr); o = env.outcome()
                    acc["P_quit"] += o["agent_quit"]; acc["P_accel"] += o["agent_accelerated"]; acc["P_first"] += o["agent_first"] + 0.5 * o["both_first"]
                emp = {k: v / n for k, v in acc.items()}
                d = {k: abs(emp[k] - pred[k]) for k in emp}
                worst = max(worst, max(d.values()))
                detail[f"g{gap}t{threat}n{noise}"] = {"model": {k: round(pred[k], 4) for k in emp}, "simulated": {k: round(v, 4) for k, v in emp.items()}}
    rec("C4_environment_two_route_vs_forward_outcomes", worst < 0.03, {"max_abs_diff": worst, "n_per_cell": 6000, "cells": detail})

    # C5 seed reproducibility
    e1, _ = play_scripted(2, 1, 1, np.random.default_rng(7)); e2, _ = play_scripted(2, 1, 1, np.random.default_rng(7))
    rec("C5_seed_reproducible", e1.log == e2.log and e1.outcome() == e2.outcome(), {"periods": len(e1.log)})

    res["built"] = time.strftime("%Y-%m-%d %H:%M %Z")
    json.dump(res, open(OUT, "w"), indent=1, default=str)
    print("STATUS", res["status"], "->", OUT)
    sys.exit(0 if res["status"] == "PASS" else 1)


def _entry_before_finish(env):
    return any(r["entry_state_at_action"] == 1 and r["finished"]["agent"] for r in env.log)


if __name__ == "__main__":
    main()
