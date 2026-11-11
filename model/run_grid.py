#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 5 — comparative statics over the WHOLE parameter grid (no parameter is chosen).

For each grid point (all parameters except the one being moved), the solver is run along the theta grid (or the sigma grid)
and each candidate prediction P1..P8 of MODEL_NOTES §5 is classified as
  'holds'    : outcome weakly monotone in the predicted direction with at least one strict move,
  'flat'     : never changes,
  'violated' : at least one move in the opposite direction.
The share of grid points in each class is reported under the three equilibrium-selection rules and, for sigma, under both
definitions (implementation tremble; observation noise). A prediction is a pre-registration candidate only if it 'holds' on
at least 50 % of the grid and is 'violated' on at most 10 % under the main rule (kill test iv), and the direction agrees
across selection rules.

Expected ranges written BEFORE running (experiment-interface-verification §3):
  - P1 (theta -> leader accelerates) and P2 (theta -> laggard quits) should hold on a majority of the grid but NOT on all
    of it: the closed-form derivation (MODEL_NOTES §6) shows monotonicity can fail where the rival's period-2 action switches
    with entry. If either holds on 100 % of points the monotonicity test is suspect (too clean -> check the classifier).
  - P7 (laggard quits more than leader at d > 0) should hold on nearly all points with d >= 1 and be 'flat' only where
    nobody quits; a violation share above a few % would indicate a bug.
  - sigma predictions P5/P6: no sign assumed; a split (both signs common) is an acceptable outcome and would mean sigma
    hypotheses are dropped.
Writes results/03_model_predictions.json and results/03_grid_outcomes.parquet; figure via make_model_figure.py.
"""
import itertools
import json
import os
import sys
import time
from dataclasses import replace

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import race_model as R  # noqa: E402

OUT_JSON = os.path.join(ROOT, "results", "03_model_predictions.json")
OUT_GRID = os.path.join(ROOT, "results", "03_grid_outcomes.parquet")

THETA = [0.0, 0.1, 0.2, 0.35, 0.5, 0.7]
SIGMA = [0.0, 0.1, 0.25, 0.4]
GRID = dict(
    K=[3, 4], T=[3],
    gap=[(2, 1), (2, 0), (1, 0), (3, 1), (3, 2)],  # (xL0, xF0); filtered to xL0 < K
    W=[0.0, 0.3, 0.6], lam=[0.0, 0.3, 0.6],
    pC=[0.35, 0.5], pA=[0.65, 0.85], cC=[0.03, 0.08], cA_mult=[1.3, 2.0],  # cA = cC * (pA/pC) * cA_mult  (convex)
)
PRED = {
    "P1": ("P_accel_L", +1, "theta up -> leader more likely to accelerate (escape entry)"),
    "P2": ("P_quit_F", +1, "theta up -> laggard more likely to quit"),
    "P3": ("dquit_F_minus_L", +1, "theta effect on quitting larger for laggard than leader"),
    "P4": ("daccel_L_minus_F", +1, "theta effect on acceleration larger for leader than laggard"),
    "P8": ("P_first_L", +1, "theta up -> leader more likely to be first to market"),
    "P2L": ("P_quit_L", 0, "theta effect on leader quitting (sign not predicted; reported)"),
    "P1F": ("P_accel_F", 0, "theta effect on laggard acceleration (sign not predicted; reported)"),
}
PRED_SIGMA = {
    "P5": ("P_quit_F", 0, "sigma effect on laggard quitting (sign derived)"),
    "P6": ("P_accel_L", 0, "sigma effect on leader acceleration (sign derived)"),
    "P5L": ("P_quit_L", 0, "sigma effect on leader quitting"),
    "P6F": ("P_accel_F", 0, "sigma effect on laggard acceleration"),
}


def classify(seq, direction):
    d = np.diff(np.asarray(seq, dtype=float))
    d[np.abs(d) < 1e-10] = 0.0
    if np.all(d == 0):
        return "flat"
    if direction == 0:  # report dominant sign
        if np.all(d >= 0):
            return "up"
        if np.all(d <= 0):
            return "down"
        return "nonmonotone"
    if np.all(direction * d >= 0):
        return "holds"
    return "violated"


def grid_points():
    for K, T, (xL0, xF0), W, lam, pC, pA, cC, cm in itertools.product(GRID["K"], GRID["T"], GRID["gap"], GRID["W"], GRID["lam"], GRID["pC"], GRID["pA"], GRID["cC"], GRID["cA_mult"]):
        if xL0 >= K:
            continue
        cA = cC * (pA / pC) * cm
        yield dict(K=K, T=T, xL0=xL0, xF0=xF0, V=1.0, W=W, lam=lam, pC=pC, pA=pA, cC=cC, cA=cA)


def run():
    t0 = time.time()
    rows = []
    pts = list(grid_points())
    print(f"grid points: {len(pts)} x theta {len(THETA)} x sigma {len(SIGMA)} x selection 3")
    for sel in ("welfare", "leader", "laggard"):
        for gi, g in enumerate(pts):
            for th in THETA:
                for sg in SIGMA:
                    P = R.Params(**g, theta=th, sigma=sg, selection=sel)
                    sol = R.solve_finite_horizon(P)
                    o = R.forward_outcomes(P, sol)
                    oc = R.forward_outcomes(P, sol, condition_no_entry=True)
                    rows.append(dict(sel=sel, gi=gi, **g, theta=th, sigma=sg, sigma_def="tremble", n_multi=sol.n_multi, n_mixed=sol.n_mixed,
                                     **{k: float(v) for k, v in o.items() if k not in ("mass_check",)},
                                     **{"thr_" + k: float(v) for k, v in oc.items() if k not in ("mass_check", "conditioned_on_no_entry")}))
                    if sg > 0:  # observation-noise definition: full-information policies with sigma_obs = sg
                        P0 = R.Params(**g, theta=th, sigma=0.0, selection=sel)
                        sol0 = R.solve_finite_horizon(P0)
                        o2 = R.forward_outcomes(P0, sol0, obs_noise=sg)
                        oc2 = R.forward_outcomes(P0, sol0, obs_noise=sg, condition_no_entry=True)
                        rows.append(dict(sel=sel, gi=gi, **g, theta=th, sigma=sg, sigma_def="obs_noise", n_multi=sol0.n_multi, n_mixed=sol0.n_mixed,
                                         **{k: float(v) for k, v in o2.items() if k not in ("mass_check",)},
                                         **{"thr_" + k: float(v) for k, v in oc2.items() if k not in ("mass_check", "conditioned_on_no_entry")}))
        print(f"  {sel} done ({time.time() - t0:.0f}s)")
    df = pd.DataFrame(rows)
    df["d"] = df["xL0"] - df["xF0"]
    df.to_parquet(OUT_GRID, index=False)
    return df


def summarise(df):
    res = {"built": time.strftime("%Y-%m-%d %H:%M %Z"), "grid": {k: (v if not isinstance(v, list) or not isinstance(v[0], tuple) else [list(x) for x in v]) for k, v in GRID.items()},
           "theta_grid": THETA, "sigma_grid": SIGMA, "n_rows": int(len(df)), "theta_predictions": {}, "sigma_predictions": {}, "multiplicity": {}}
    # theta comparative statics at sigma = 0 (tremble def), per selection rule, per grid point;
    # version 'threat' = conditional on no realised entry (ex-ante incentive effect of the threat), 'unconditional' = realised mix
    base = df[(df.sigma == 0.0) & (df.sigma_def == "tremble")]
    for version in ("threat", "unconditional"):
      pre = "thr_" if version == "threat" else ""
      res["theta_predictions"][version] = {}
      for sel, dsel in base.groupby("sel"):
        out = {}
        for pid, (col, direction, desc) in PRED.items():
            classes = {"holds": 0, "flat": 0, "violated": 0, "up": 0, "down": 0, "nonmonotone": 0}
            by_d = {}
            for gi, g in dsel.groupby("gi"):
                g = g.sort_values("theta")
                if col == "dquit_F_minus_L":
                    seq = (g[pre + "P_quit_F"] - g[pre + "P_quit_L"]).values
                elif col == "daccel_L_minus_F":
                    seq = (g[pre + "P_accel_L"] - g[pre + "P_accel_F"]).values
                else:
                    seq = g[pre + col].values
                c = classify(seq, direction)
                classes[c] += 1
                dd = int(g["d"].iloc[0])
                by_d.setdefault(dd, {"holds": 0, "flat": 0, "violated": 0, "up": 0, "down": 0, "nonmonotone": 0})[c] += 1
            n = sum(classes.values())
            out[pid] = {"outcome": col, "predicted_direction": direction, "description": desc, "n_grid_points": n,
                        "share": {k: round(v / n, 4) for k, v in classes.items() if v}, "by_gap_d": {str(k): {kk: vv for kk, vv in v.items() if vv} for k, v in sorted(by_d.items())}}
        res["theta_predictions"][version][sel] = out
    # sigma comparative statics at each theta, both definitions, main selection rule
    for sdef in ("tremble", "obs_noise"):
        dd = df[(df.sel == "welfare") & ((df.sigma_def == sdef) | (df.sigma == 0.0))]
        out = {}
        for pid, (col, direction, desc) in PRED_SIGMA.items():
            for version, pre in (("unconditional", ""), ("threat", "thr_")):
                classes = {"flat": 0, "up": 0, "down": 0, "nonmonotone": 0}
                for (gi, th), g in dd.groupby(["gi", "theta"]):
                    g = g.drop_duplicates("sigma").sort_values("sigma")
                    if len(g) < len(SIGMA):
                        continue
                    classes[classify(g[pre + col].values, 0)] += 1
                n = sum(classes.values())
                out[f"{version}:{pid}"] = {"outcome": col, "description": desc, "n_series": n, "share": {k: round(v / n, 4) for k, v in classes.items() if v}}
        res["sigma_predictions"][sdef] = out
    # multiplicity
    res["multiplicity"] = {"share_runs_with_multiple_equilibria": float((df["n_multi"] > 0).mean()), "share_runs_with_mixed_equilibria": float((df["n_mixed"] > 0).mean())}
    # decision per kill test (iv): main rule welfare, holds >= 0.5 and violated <= 0.1, and same dominant direction under other rules
    decisions = {}
    for version in ("threat", "unconditional"):
      for pid in PRED:
        if PRED[pid][1] == 0:
            continue
        tp = res["theta_predictions"][version]
        w = tp["welfare"][pid]["share"]
        # 'flat' points carry no information about the sign; the decision is taken on the informative points
        inf = w.get("holds", 0) + w.get("violated", 0)
        hold_share_inf = w.get("holds", 0) / inf if inf > 0 else 0.0
        ok = w.get("holds", 0) >= 0.5 and w.get("violated", 0) <= 0.10
        ok_inf = hold_share_inf >= 0.9 and inf >= 0.25
        other = all(tp[s][pid]["share"].get("holds", 0) >= 0.5 for s in ("leader", "laggard"))
        decisions[f"{version}:{pid}"] = {"candidate_for_preregistration": bool(ok and other), "candidate_on_informative_points": bool(ok_inf),
                                         "welfare_share": w, "share_informative": round(inf, 4), "holds_share_among_informative": round(hold_share_inf, 4),
                                         "leader_holds": tp["leader"][pid]["share"].get("holds", 0), "laggard_holds": tp["laggard"][pid]["share"].get("holds", 0)}
    for pid in ("unconditional:P5", "unconditional:P6", "threat:P5", "threat:P6"):
        shares = {sd: res["sigma_predictions"][sd][pid]["share"] for sd in ("tremble", "obs_noise")}
        dom = {sd: max(((k, v) for k, v in s.items() if k in ("up", "down")), key=lambda z: z[1], default=(None, 0)) for sd, s in shares.items()}
        same = dom["tremble"][0] is not None and dom["tremble"][0] == dom["obs_noise"][0] and all(v[1] >= 0.5 for v in dom.values())
        decisions[pid] = {"candidate_for_preregistration": bool(same), "dominant_direction": {sd: dom[sd][0] for sd in dom}, "shares": shares}
    res["kill_test_iv_decisions"] = decisions
    json.dump(res, open(OUT_JSON, "w"), indent=1)
    return res


if __name__ == "__main__":
    df = run()
    res = summarise(df)
    print(json.dumps({k: res[k] for k in ("kill_test_iv_decisions", "multiplicity")}, indent=1))
    print("wrote", OUT_JSON)
