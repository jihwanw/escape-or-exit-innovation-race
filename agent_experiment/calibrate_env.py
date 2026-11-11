#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Calibration of the Stage B environment BEFORE any LLM call (2026-11-10).

Why: with the Task 8 draft parameters (accelerate cost 20억, success 80 %; continue 8억, 50 %) the model's leader at one stage
from completion accelerates with probability 1.000 at theta = 0 (results/05_stage_b_controls.json, C4 cells g2t0*), i.e. the
environment sits on the model's own ceiling for the H1 comparative static (MODEL_PREDICTIONS.md: 50 % of grid points are flat
for P1). An experiment run there cannot show the predicted threat effect even if agents behaved exactly like the model.

Rule (fixed here, before the scan is read): keep every other parameter of the draft environment (V = 100억, W = 30억,
lam = 0.5, theta in {0, 0.35}, pC = 0.5, pA = 0.8, cC = 8억, K = T = 3, positions (1,2)/(1,1)/(2,1)) and vary ONLY the
acceleration cost cA on a 5억 grid. Choose the SMALLEST cA such that, in the model,
  (i)   gap-2 leader: P(accelerate | no entry) at theta = 0 lies in [0.20, 0.80]  (room in both directions),
  (ii)  gap-2 leader: P(accelerate | no entry) rises by >= 0.05 from theta = 0 to 0.35  (H1 direction present),
  (iii) gap-0 laggard: P(quit) at theta = 0 lies in [0.20, 0.80] and rises by >= 0.05 to theta = 0.35 (H2 direction present),
  (iv)  gap-0 laggard quits more than the gap-2 leader at theta = 0 (H5 direction present),
  (v)   convexity cA/cC > pA/pC (Params.check()).
Writes results/05_stage_b_env_calibration.json with the full scan so the choice is auditable.
"""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "model"))
import race_model as R  # noqa: E402

OUT = os.path.join(ROOT, "results", "05_stage_b_env_calibration.json")
FIXED = dict(K=3, T=3, V=1.0, W=0.3, lam=0.5, sigma=0.0, pC=0.5, pA=0.8, cC=0.08)
POSITIONS = {0: (1, 2), 1: (1, 1), 2: (2, 1)}
THETAS = (0.0, 0.35)
CA_GRID = [round(0.10 + 0.05 * i, 2) for i in range(7)]  # 10억 .. 40억


def cell_preds(base, gap, theta, obs_noise=0.0):
    ax, rx = POSITIONS[gap]
    if ax >= rx:
        P = R.Params(**base, theta=theta, xL0=ax, xF0=rx); side = "L"
    else:
        P = R.Params(**base, theta=theta, xL0=rx, xF0=ax); side = "F"
    sol = R.solve_finite_horizon(P)
    u = R.forward_outcomes(P, sol, obs_noise=obs_noise)
    c = R.forward_outcomes(P, sol, obs_noise=obs_noise, condition_no_entry=True)
    pick = lambda o: {k: float(o[f"{k}_{side}"]) for k in ("P_quit", "P_accel", "P_first")}  # noqa: E731
    return side, pick(u), pick(c)


def main():
    scan = []
    for cA in CA_GRID:
        base = dict(FIXED, cA=cA)
        try:
            R.Params(**base, theta=0.0, xL0=2, xF0=1).check()
            convex = True
        except Exception as e:  # noqa
            convex = False
        row = {"cA": cA, "cA_billion_won": round(cA * 100), "convex": convex, "cells": {}}
        if convex:
            for gap in (0, 1, 2):
                for th in THETAS:
                    side, u, c = cell_preds(base, gap, th)
                    row["cells"][f"gap{gap}_theta{th}"] = {"role": side, "unconditional": u, "no_entry_conditional": c}
            l0 = row["cells"]["gap2_theta0.0"]["no_entry_conditional"]["P_accel"]
            l35 = row["cells"]["gap2_theta0.35"]["no_entry_conditional"]["P_accel"]
            f0 = row["cells"]["gap0_theta0.0"]["unconditional"]["P_quit"]
            f35 = row["cells"]["gap0_theta0.35"]["unconditional"]["P_quit"]
            lq0 = row["cells"]["gap2_theta0.0"]["unconditional"]["P_quit"]
            row["criteria"] = {"i_leader_accel0_in_range": bool(0.20 <= l0 <= 0.80), "ii_H1_room": bool(l35 - l0 >= 0.05),
                               "iii_laggard_quit0_in_range_and_H2_room": bool(0.20 <= f0 <= 0.80 and f35 - f0 >= 0.05),
                               "iv_H5_laggard_quits_more": bool(f0 > lq0), "v_convex": True}
            row["all_pass"] = all(row["criteria"].values())
            row["summary"] = {"leader_accel_noentry_theta0": l0, "leader_accel_noentry_theta35": l35, "laggard_quit_theta0": f0, "laggard_quit_theta35": f35, "leader_quit_theta0": lq0}
        else:
            row["criteria"] = {"v_convex": False}; row["all_pass"] = False
        scan.append(row)
        print(f"cA={cA:.2f} ({row['cA_billion_won']}억) convex={convex} pass={row['all_pass']} " + (json.dumps({k: round(v, 3) for k, v in row['summary'].items()}) if convex else ""))
    chosen = next((r for r in scan if r["all_pass"]), None)
    res = {"rule": __doc__.strip(), "fixed": FIXED, "cA_grid": CA_GRID, "scan": scan,
           "chosen_cA": chosen["cA"] if chosen else None, "chosen_cA_billion_won": chosen["cA_billion_won"] if chosen else None,
           "draft_cA_was": 0.20, "built": time.strftime("%Y-%m-%d %H:%M %Z")}
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("chosen cA:", res["chosen_cA"], "->", OUT)
    return 0 if chosen else 1


if __name__ == "__main__":
    sys.exit(main())
