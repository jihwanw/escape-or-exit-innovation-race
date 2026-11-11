#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Freeze the agent predictions (Stage A + Stage B) and the theory predictions into prereg/agent_predictions_v1.json (Task 8).

Sign calls are mechanical: for a contrast with 95 % persona-bootstrap CI [lo, hi], call '+' if lo > 0, '-' if hi < 0, else '0'.
An arm = model x language (4 arms). The agent prediction for a hypothesis is the consensus of the 4 arms if at least 3 agree,
otherwise 'mixed'. Nothing here is typed by hand: every number is read from results/*.json, and the file records the SHA256 of
every input (results, templates, runner code, environment) so that the frozen state can be re-derived.
"""
import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "agent_predictions_v1.json")

INPUTS = {
    "stage_a": "results/04_agent_stage_a.json",
    "stage_b": "results/05_agent_stage_b.json",
    "model_predictions": "results/03_model_predictions.json",
    "env_calibration": "results/05_stage_b_env_calibration.json",
    "stage_a_controls": "results/04_agent_controls.json",
    "stage_b_env_controls": "results/05_stage_b_controls.json",
    "stage_b_runner_controls": "results/05_stage_b_controls_runner.json",
    "hypotheses_doc": "docs/HYPOTHESES_GATE_B.md",
}
CODE = ["agent_experiment/prompts/stage_a_templates.py", "agent_experiment/prompts/stage_b_templates.py", "agent_experiment/run_stage_a.py",
        "agent_experiment/run_stage_b.py", "agent_experiment/race_env.py", "agent_experiment/calibrate_env.py", "model/race_model.py",
        "agent_experiment/stage_a_design.csv", "agent_experiment/stage_b_design.csv", "agent_experiment/stage_a_personas.csv"]

# hypothesis -> (theory sign, Stage A contrast key, Stage B contrast key, note). Theory signs come from docs/HYPOTHESES_GATE_B.md
# (gate B approved 2026-11-10); the mapping of contrasts to hypotheses is the one implemented in run_stage_a/run_stage_b.
HYP = {
    "H1": ("+", "H1_accel_threat_gap2", "H1_accel_threat_gap2_noentry", "threat raises acceleration of the leader one stage from completion (threat version: no realised entry)"),
    "H2": ("+", "H2_quit_threat_gap0", "H2_quit_threat_gap0", "threat raises quitting of the laggard (both versions)"),
    "H3": ("+", "H3_quit_threat_gap0_minus_gap2", "H3_quit_threat_gap0_minus_gap2", "quit effect of threat larger for laggard than leader"),
    "H4": ("+", "H4_accel_threat_gap2_minus_gap0", "H4_accel_threat_gap2_minus_gap0", "acceleration effect of threat larger for leader than laggard"),
    "H5": ("+", "H5_quit_gap0_minus_gap2", "H5_quit_gap0_minus_gap2", "laggard quits more than leader at any theta"),
    "H6": ("not +", None, "H1_accel_threat_gap2", "realised entry does not raise leader acceleration: Stage B UNCONDITIONAL threat contrast (entry realised at random) should not be positive; Stage A has no realised entry"),
}


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def sign_call(c):
    if c is None or c.get("ci95") is None or c.get("estimate") is None:
        return None
    lo, hi = c["ci95"]
    return "+" if lo > 0 else ("-" if hi < 0 else "0")


def consensus(calls):
    vals = [v for v in calls.values() if v is not None]
    if not vals:
        return None
    for s in ("+", "-", "0"):
        if sum(v == s for v in vals) >= 3:
            return s
    return "mixed"


def main():
    data = {k: (json.load(open(os.path.join(ROOT, p), encoding="utf-8")) if p.endswith(".json") else None) for k, p in INPUTS.items()}
    A, B = data["stage_a"], data["stage_b"]
    assert A.get("mode") == "full" and B.get("mode") == "full", "both stages must be full runs"
    assert A["template_version"] == "v3"
    out = {"version": "prereg-v1", "frozen_at": time.strftime("%Y-%m-%d %H:%M %Z"), "rule": __doc__.strip(),
           "environment": {"constants": data["env_calibration"]["fixed"] | {"cA": data["env_calibration"]["chosen_cA"]}, "unit_won": "1 model unit = 100억원",
                           "theta": {"0": 0.0, "1": 0.35}, "obs_noise": {"0": 0.0, "1": 0.4}, "positions_agent_rival": {"gap0": [1, 2], "gap1": [1, 1], "gap2": [2, 1]},
                           "calibration_file": INPUTS["env_calibration"]},
           "theory": {"grid_decisions": data["model_predictions"].get("decisions"), "env_cell_predictions": B["model_predictions"], "period1_action_probs": B["model_period1_action_probs"]},
           "stage_a": {"n_calls": A["n_calls"], "parse_status": A["parse_status"], "arms": {}},
           "stage_b": {"n_episodes": B["n_episodes"], "status_counts": B["status_counts"], "arms": {}},
           "predictions": {}}
    for arm, v in A["by_model_lang"].items():
        out["stage_a"]["arms"][arm] = {"n_ok": v["n_ok"], "cells": v["cells"], "contrasts": v["contrasts"], "position_share_first_option": v["position_share_first_option"]}
    for arm, v in B["by_model_lang"].items():
        out["stage_b"]["arms"][arm] = {"n_complete": v["n_complete"], "n_parse_failed": v["n_parse_failed"], "cells": v["cells"], "contrasts": v["contrasts"]}
    for h, (theory, ka, kb, note) in HYP.items():
        pa = {arm: sign_call(v["contrasts"].get(ka)) for arm, v in A["by_model_lang"].items()} if ka else None
        pb = {arm: sign_call(v["contrasts"].get(kb)) for arm, v in B["by_model_lang"].items()}
        out["predictions"][h] = {"theory_sign": theory, "note": note,
                                 "stage_a": None if pa is None else {"contrast": ka, "arm_calls": pa, "consensus": consensus(pa),
                                                                     "estimates": {arm: v["contrasts"][ka] for arm, v in A["by_model_lang"].items()}},
                                 "stage_b": {"contrast": kb, "arm_calls": pb, "consensus": consensus(pb), "estimates": {arm: v["contrasts"][kb] for arm, v in B["by_model_lang"].items()}}}
    # placebo and position checks (should be '0')
    out["checks"] = {"stage_a_placebo_within_cell": {arm: {k: v["contrasts"][k] for k in ("placebo_accel_within_cell", "placebo_quit_within_cell")} for arm, v in A["by_model_lang"].items()},
                     "stage_a_position_effect": {arm: v["contrasts"]["pos_first_option"] for arm, v in A["by_model_lang"].items()},
                     "stage_b_placebo_within_cell": {arm: {k: v["contrasts"][k] for k in ("placebo_accel_within_cell", "placebo_quit_within_cell")} for arm, v in B["by_model_lang"].items()}}
    out["hashes"] = {p: sha(os.path.join(ROOT, p)) for p in list(INPUTS.values()) + CODE if os.path.exists(os.path.join(ROOT, p))}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    digest = sha(OUT)
    open(os.path.join(HERE, "SHA256SUMS.txt"), "w").write(f"{digest}  agent_predictions_v1.json\n" + "".join(f"{v}  {k}\n" for k, v in out["hashes"].items()))
    print("frozen ->", OUT, "\nsha256", digest)
    for h, p in out["predictions"].items():
        print(h, "theory", p["theory_sign"], "| A", p["stage_a"] and p["stage_a"]["consensus"], p["stage_a"] and p["stage_a"]["arm_calls"], "| B", p["stage_b"]["consensus"], p["stage_b"]["arm_calls"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
