#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Numerical check of the comparative statics stated in the manuscript (Appendix A), written for the mechanism-claim gate
(skills/mechanism_claim_audit.py check E: "appendix model with equations needs a numerical check artefact").

It does not change any result file; it re-derives, from model/race_model.py, the quantities the text claims:
  1. two-period analytic case (MODEL_NOTES.md §6): brute-force the thresholds theta* (laggard switches C -> Q) and
     theta** (leader switches C -> A) on a fine theta grid and confirm the closed-form solver and the general
     backward-induction solver agree on values, policies and outcomes at every grid point;
  2. calibrated Stage B environment (agent_experiment/race_env.py BASE): numerically differentiate the threat-conditional
     and unconditional outcome probabilities with respect to theta (central differences on a fine grid) for the
     one-stage-ahead leader and the one-stage-behind laggard, and record the sign pattern that H1, H2, H5 and H6 rest on;
  3. choice set: the model's per-period choice set is {stop, continue, accelerate}; 'continue' is the option to wait
     (the project stays alive and the acceleration decision is deferred to the next period), so the pre-emption
     comparative static is computed against the value of waiting, not against doing nothing;
  4. invariances: lam = 1 (entry harmless) and theta = 0 (no threat) leave all outcomes unchanged.
Writes results/model_check.json. Exit code 1 if any check fails.
"""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "model"))
sys.path.insert(0, os.path.join(ROOT, "agent_experiment"))
import race_model as R  # noqa: E402
import race_env as E  # noqa: E402

OUT = os.path.join(ROOT, "results", "model_check.json")


def outcomes(P, cond):
    sol = R.solve_finite_horizon(P)
    return R.forward_outcomes(P, sol, condition_no_entry=cond), sol


def two_period_thresholds():
    """Brute-force theta* and theta** for the T=2, K=2 analytic case at a representative parameter point, and check the two
    code paths agree everywhere on the grid."""
    base = dict(K=2, T=2, xL0=1, xF0=0, V=1.0, W=0.3, lam=0.5, sigma=0.0, pC=0.5, pA=0.8, cC=0.08, cA=0.25)
    grid = np.round(np.linspace(0.0, 0.95, 96), 4)
    max_gap = 0.0
    quitF, accelL = [], []
    for th in grid:
        P = R.Params(**base, theta=float(th))
        cf = R.solve_two_period(P)
        ou, sol = outcomes(P, cond=False)   # the closed form returns unconditional outcome probabilities
        oc, _ = outcomes(P, cond=True)
        # both routes must give the same initial-state value (t = 1, before the entry shock) for L and F, and the same outcomes
        uL, uF = sol.U[(1, P.xL0, R.ACTIVE, P.xF0, R.ACTIVE, 0)]
        max_gap = max(max_gap, abs(uL - cf["U0"][0]), abs(uF - cf["U0"][1]),
                      abs(ou["P_quit_F"] - cf["P_quit_F"]), abs(ou["P_accel_L"] - cf["P_accel_L"]), abs(ou["P_first_L"] - cf["P_first_L"]))
        quitF.append(float(oc["P_quit_F"])); accelL.append(float(oc["P_accel_L"]))
    quitF = np.array(quitF); accelL = np.array(accelL)
    # thresholds: the smallest grid theta from which the laggard quits with certainty (theta*) / the leader accelerates with
    # certainty (theta**) and stays there for every larger theta on the grid
    def first_certain(y):
        for i in range(len(grid)):
            if np.all(y[i:] > 1 - 1e-9):
                return float(grid[i])
        return None
    th_star = first_certain(quitF); th_2star = first_certain(accelL)
    mono_quit = bool(np.all(np.diff(quitF) >= -1e-9)); mono_accel = bool(np.all(np.diff(accelL) >= -1e-9))
    return {"params": base, "theta_grid": [float(t) for t in grid], "two_route_max_value_gap": max_gap,
            "P_quit_F_threat": quitF.tolist(), "P_accel_L_threat": accelL.tolist(),
            "theta_star_laggard_quits_with_certainty_from": th_star, "theta_2star_leader_accelerates_with_certainty_from": th_2star,
            "P_quit_F_weakly_increasing": mono_quit, "P_accel_L_weakly_increasing": mono_accel,
            "P_quit_F_endpoint_change": float(quitF[-1] - quitF[0]), "P_accel_L_endpoint_change": float(accelL[-1] - accelL[0]),
            "note": "at theta = 0 the period-1 game has a mixed (attrition-type) equilibrium; P_accel_L is not strictly monotone because a small theta first makes the laggard quit, which lowers the leader's need to accelerate, before the leader's own threshold is reached (MODEL_PREDICTIONS.md)",
            "pass": max_gap < 1e-8 and mono_quit and quitF[-1] > quitF[0] and accelL[-1] > accelL[0]}


def env_comparative_statics():
    """Central differences of outcome probabilities in theta at the calibrated environment, for the agent's seat."""
    res = {}
    grid = np.round(np.linspace(0.0, 0.7, 36), 4)
    for gap, role in ((2, "leader_one_stage_ahead"), (0, "laggard_one_stage_behind")):
        ax, rx = E.POSITIONS[gap]
        rows = {"theta": [], "P_accel_cond": [], "P_accel_uncond": [], "P_quit_cond": [], "P_quit_uncond": []}
        for th in grid:
            if ax >= rx:
                P = R.Params(**E.BASE, theta=float(th), xL0=ax, xF0=rx); side = "L"
            else:
                P = R.Params(**E.BASE, theta=float(th), xL0=rx, xF0=ax); side = "F"
            oc, _ = outcomes(P, cond=True); ou, _ = outcomes(P, cond=False)
            rows["theta"].append(float(th))
            rows["P_accel_cond"].append(float(oc[f"P_accel_{side}"])); rows["P_accel_uncond"].append(float(ou[f"P_accel_{side}"]))
            rows["P_quit_cond"].append(float(oc[f"P_quit_{side}"])); rows["P_quit_uncond"].append(float(ou[f"P_quit_{side}"]))
        d = {}
        for k in ("P_accel_cond", "P_accel_uncond", "P_quit_cond", "P_quit_uncond"):
            y = np.array(rows[k]); dy = np.gradient(y, np.array(rows["theta"]))
            d[k] = {"at_theta_0": float(y[0]), "at_theta_035": float(np.interp(0.35, rows["theta"], y)), "at_theta_07": float(y[-1]),
                    "endpoint_change": float(y[-1] - y[0]), "mean_derivative": float(dy.mean()),
                    "share_grid_derivative_positive": float(np.mean(dy > 1e-9)), "share_grid_derivative_negative": float(np.mean(dy < -1e-9))}
        res[role] = {"positions_agent_rival": [ax, rx], "path": rows, "derivatives": d}
    # H1: leader accel (threat-conditional) rises; H6 logic: unconditional does not rise; H2: laggard quit rises (both versions);
    # H5: laggard quits more than leader at theta = 0
    L, F = res["leader_one_stage_ahead"]["derivatives"], res["laggard_one_stage_behind"]["derivatives"]
    checks = {
        "H1_leader_accel_threat_conditional_rises": L["P_accel_cond"]["endpoint_change"] > 0,
        "H6_leader_accel_unconditional_does_not_rise": L["P_accel_uncond"]["endpoint_change"] <= 1e-9,
        "H2_laggard_quit_rises_conditional": F["P_quit_cond"]["endpoint_change"] > 0,
        "H2_laggard_quit_rises_unconditional": F["P_quit_uncond"]["endpoint_change"] > 0,
        "H5_laggard_quits_more_than_leader_at_theta_0": F["P_quit_uncond"]["at_theta_0"] > L["P_quit_uncond"]["at_theta_0"],
        "H3_quit_response_laggard_exceeds_leader": F["P_quit_cond"]["endpoint_change"] > L["P_quit_cond"]["endpoint_change"],
        "H4_accel_response_leader_exceeds_laggard": L["P_accel_cond"]["endpoint_change"] > F["P_accel_cond"]["endpoint_change"],
    }
    res["checks"] = {k: bool(v) for k, v in checks.items()}
    res["pass"] = all(checks.values())
    return res


def choice_set_and_invariances():
    out = {"choice_set": {"actions": ["stop (Q)", "continue (C)", "accelerate (A)"], "option_to_wait": "continue (C): the project stays alive at the base effort and the acceleration decision is deferred to the next period",
                          "source": "model/race_model.py ACT = (Q, C, A); MODEL_NOTES.md §1"}}
    base = dict(E.BASE); base.pop("sigma", None)
    P0 = R.Params(**E.BASE, theta=0.35, xL0=2, xF0=1)
    # lam = 1: entry harmless -> outcomes identical across theta
    o_a, _ = outcomes(R.Params(**{**E.BASE, "lam": 1.0}, theta=0.0, xL0=2, xF0=1), cond=False)
    o_b, _ = outcomes(R.Params(**{**E.BASE, "lam": 1.0}, theta=0.6, xL0=2, xF0=1), cond=False)
    keys = [k for k in o_a if k.startswith("P_") and k != "P_entry"]  # P_entry is theta by construction
    lam_gap = max(abs(o_a[k] - o_b[k]) for k in keys)
    # theta = 0: lam irrelevant
    o_c, _ = outcomes(R.Params(**{**E.BASE, "lam": 0.1}, theta=0.0, xL0=2, xF0=1), cond=False)
    o_d, _ = outcomes(R.Params(**{**E.BASE, "lam": 0.9}, theta=0.0, xL0=2, xF0=1), cond=False)
    th_gap = max(abs(o_c[k] - o_d[k]) for k in keys)
    out["invariances"] = {"lam_1_max_outcome_gap_across_theta": lam_gap, "theta_0_max_outcome_gap_across_lam": th_gap, "pass": lam_gap < 1e-9 and th_gap < 1e-9}
    out["calibrated_params"] = {k: getattr(P0, k) for k in ("K", "T", "V", "W", "lam", "pC", "pA", "cC", "cA")}
    return out


if __name__ == "__main__":
    t0 = time.time()
    rep = {"two_period_analytic_case": two_period_thresholds(), "calibrated_environment": env_comparative_statics(), "structure": choice_set_and_invariances()}
    rep["pass"] = bool(rep["two_period_analytic_case"]["pass"] and rep["calibrated_environment"]["pass"] and rep["structure"]["invariances"]["pass"])
    rep["built"] = time.strftime("%Y-%m-%d %H:%M %Z"); rep["seconds"] = round(time.time() - t0, 1)
    def _py(o):
        if isinstance(o, dict): return {k: _py(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)): return [_py(v) for v in o]
        if isinstance(o, (np.bool_,)): return bool(o)
        if isinstance(o, (np.integer,)): return int(o)
        if isinstance(o, (np.floating,)): return float(o)
        return o
    rep = _py(rep)
    json.dump(rep, open(OUT, "w"), indent=1)
    tp = rep["two_period_analytic_case"]; ce = rep["calibrated_environment"]
    print(f"two-period: two-route max gap {tp['two_route_max_value_gap']:.1e}; theta* {tp['theta_star_laggard_quits_with_certainty_from']}, theta** {tp['theta_2star_leader_accelerates_with_certainty_from']}; quit monotone {tp['P_quit_F_weakly_increasing']}, accel monotone {tp['P_accel_L_weakly_increasing']}")
    for k, v in ce["checks"].items():
        print(f"  {'PASS' if v else 'FAIL'} {k}")
    print(f"invariances: {rep['structure']['invariances']}")
    print(f"model_check: {'PASS' if rep['pass'] else 'FAIL'} ({rep['seconds']}s) -> {OUT}")
    sys.exit(0 if rep["pass"] else 1)
