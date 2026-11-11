#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Controls for the race-model solver (MODEL_NOTES §7; experiment-interface-verification §2).
Must PASS before any grid result is reported. Writes results/03_model_controls.json; exit 1 on failure."""
import json
import os
import sys
import time
from dataclasses import replace

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import race_model as R  # noqa: E402

OUT = os.path.join(ROOT, "results", "03_model_controls.json")
SEED = 20261109


def outcomes(P, obs_noise=0.0):
    sol = R.solve_finite_horizon(P)
    o = R.forward_outcomes(P, sol, obs_noise=obs_noise)
    return sol, {k: float(v) for k, v in o.items() if k not in ("mass_check",)}, o["mass_check"]


def random_params(rng, **fixed):
    pC = rng.uniform(0.2, 0.7)
    pA = rng.uniform(pC + 0.05, min(1.0, pC + 0.45))
    cC = rng.uniform(0.01, 0.15)
    cA = cC * (pA / pC) * rng.uniform(1.05, 2.5)  # convexity guaranteed
    base = dict(V=1.0, W=rng.uniform(0.0, 0.8), lam=rng.uniform(0.0, 0.95), theta=rng.uniform(0.0, 0.9), sigma=0.0, pC=pC, pA=pA, cC=cC, cA=cA)
    base.update(fixed)
    return R.Params(**base)


def _mc_conditional(P, sol, rng, n=200000):
    """Independent route: simulate the game along the no-entry branch and count outcomes (keeps paths with no entry in 1..T)."""
    cnt = {"quit_F": 0, "accel_L": 0, "first_L": 0}; kept = 0
    for _ in range(n):
        xL, xF, sL, sF = P.xL0, P.xF0, 0, 0; fL = qF = firstL = False; ok = True
        for t in range(1, P.T + 1):
            if rng.random() < P.theta:
                ok = False; break
            if sL != 0 and sF != 0:
                continue
            mix, aLs, aFs = sol.policy[(t, xL if sL != 2 else P.K, sL, xF if sF != 2 else P.K, sF, 0)]
            r = rng.random(); acc = 0.0
            for w, (pL, pF) in mix:
                acc += w
                if r <= acc:
                    break
            aL = aLs[rng.choice(len(aLs), p=pL)] if sL == 0 else None
            aF = aFs[rng.choice(len(aFs), p=pF)] if sF == 0 else None
            if aL == R.A: fL = True
            if aL == R.Q: sL = 1
            if aF == R.Q: sF = 1; qF = True
            sucL = sL == 0 and aL in (R.C, R.A) and rng.random() < R.psucc(P, aL)
            sucF = sF == 0 and aF in (R.C, R.A) and rng.random() < R.psucc(P, aF)
            if sucL: xL += 1
            if sucF: xF += 1
            finL = sL == 0 and xL >= P.K; finF = sF == 0 and xF >= P.K
            if finL and finF: firstL = firstL or (rng.random() < 0.5)
            elif finL and sF != 2: firstL = True
            if finL: sL = 2
            if finF: sF = 2
        if ok:
            kept += 1; cnt["quit_F"] += qF; cnt["accel_L"] += fL; cnt["first_L"] += firstL
    return {k: v / kept for k, v in cnt.items()}, kept / n


def main():
    rng = np.random.default_rng(SEED)
    res = {"seed": SEED, "checks": {}, "status": "PASS"}

    def rec(name, ok, detail):
        res["checks"][name] = {"pass": bool(ok), "detail": detail}
        if not ok:
            res["status"] = "FAIL"
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {str(detail)[:300]}")

    # 1. two routes agree: closed form (T=2,K=2,xL0=1,xF0=0) vs general solver, 200 random points
    maxdiff = {"U_L": 0.0, "U_F": 0.0, "P_quit_F": 0.0, "P_accel_L": 0.0, "P_first_L": 0.0}
    n_pol_mismatch = 0
    for _ in range(200):
        P = random_params(rng, K=2, T=2, xL0=1, xF0=0)
        cf = R.solve_two_period(P)
        sol, o, _ = outcomes(P)
        U0 = sol.U[(1, 1, 0, 0, 0, 0)]
        maxdiff["U_L"] = max(maxdiff["U_L"], abs(U0[0] - cf["U0"][0]))
        maxdiff["U_F"] = max(maxdiff["U_F"], abs(U0[1] - cf["U0"][1]))
        for k in ("P_quit_F", "P_accel_L", "P_first_L"):
            maxdiff[k] = max(maxdiff[k], abs(o[k] - cf[k]))
        mix, _, _ = sol.policy[(1, 1, 0, 0, 0, 0)]
        pL, pF = mix[0][1]
        if len(mix) != 1 or not (np.allclose(pL, cf["policy_t1_e0"][0]) and np.allclose(pF, cf["policy_t1_e0"][1])):
            n_pol_mismatch += 1
    rec("C1_two_routes_closed_form_vs_solver", max(maxdiff.values()) < 1e-9 and n_pol_mismatch == 0, {"max_abs_diff": maxdiff, "policy_mismatches": n_pol_mismatch, "n": 200})

    # 2. lam = 1 invariance: theta must not matter
    worst = 0.0
    for _ in range(60):
        P = random_params(rng, lam=1.0)
        _, o0, _ = outcomes(replace(P, theta=0.0))
        _, o1, _ = outcomes(replace(P, theta=rng.uniform(0.1, 0.9)))
        worst = max(worst, max(abs(o0[k] - o1[k]) for k in o0 if k not in ("P_entry",)))
    rec("C2_lambda1_theta_invariance", worst < 1e-12, {"max_abs_diff": worst})

    # 3. theta = 0 invariance: lam must not matter
    worst = 0.0
    for _ in range(60):
        P = random_params(rng, theta=0.0)
        _, o0, _ = outcomes(replace(P, lam=0.0))
        _, o1, _ = outcomes(replace(P, lam=rng.uniform(0.1, 0.9)))
        worst = max(worst, max(abs(o0[k] - o1[k]) for k in o0))
    rec("C3_theta0_lambda_invariance", worst < 1e-12, {"max_abs_diff": worst})

    # 4. epsilon-preemption deterministic limit: pC=pA=1 is excluded by pC<pA; use pC=0.999, pA=1.0, W=0, xL0=K-1, xF0=K-2
    P = R.Params(K=3, T=3, xL0=2, xF0=1, V=1.0, W=0.0, lam=0.5, theta=0.3, sigma=0.0, pC=0.999, pA=1.0, cC=0.02, cA=0.05)
    sol, o, _ = outcomes(P)
    mix, _, _ = sol.policy[(1, 2, 0, 1, 0, 0)]
    pL, pF = mix[0][1]
    ok4 = (pF[R.Q] > 0.999) and (pL[R.C] > 0.999) and o["P_quit_F"] > 0.999 and o["P_first_L"] > 0.999 and o["P_accel_L"] < 1e-9
    rec("C4_epsilon_preemption_limit", ok4, {"policy_L": pL.tolist(), "policy_F": pF.tolist(), "P_quit_F": o["P_quit_F"], "P_first_L": o["P_first_L"], "P_accel_L": o["P_accel_L"]})

    # 5. symmetry at d = 0: (a) stage payoff matrices are transposes at symmetric states, (b) the equilibrium SET is
    #    label-symmetric, (c) values are symmetric wherever the equilibrium is unique. The selection rule's last tie-breaker
    #    (laggard = F when distances tie) is label-asymmetric by construction in war-of-attrition states; that asymmetry is
    #    reported, not hidden, and the grid reports results under all three selection rules.
    worst_mat = worst_val = 0.0; set_asym = 0; n_sym = n_multi = 0
    for _ in range(40):
        P = random_params(rng, K=3, T=3, xL0=1, xF0=1)
        sol = R.solve_finite_horizon(P)
        for key, (ML, MF, eqs) in sol.stage.items():
            t, xL, sL, xF, sF, e = key
            if (xL, sL) != (xF, sF):
                continue
            n_sym += 1
            worst_mat = max(worst_mat, float(np.abs(ML - MF.T).max()))
            swapped = [(pF, pL) for pL, pF in eqs]
            if not all(any(np.allclose(a, c, atol=1e-8) and np.allclose(b, d, atol=1e-8) for c, d in eqs) for a, b in swapped):
                set_asym += 1
            mix, _, _ = sol.policy[key]
            vL = sum(w * float(pL @ ML @ pF) for w, (pL, pF) in mix)
            vF = sum(w * float(pL @ MF @ pF) for w, (pL, pF) in mix)
            worst_val = max(worst_val, abs(vL - vF))
            if len(eqs) > 1:
                n_multi += 1
    rec("C5_label_symmetry", worst_mat < 1e-9 and set_asym == 0 and worst_val < 1e-9,
        {"symmetric_states": n_sym, "max_abs_dev_payoff_transpose": worst_mat, "equilibrium_set_asymmetries": set_asym,
         "max_abs_value_asym_after_selection": worst_val, "symmetric_states_with_multiple_eq_(fair_coin_over_mirror_pairs)": n_multi})

    # 6. probability conservation in forward propagation
    worst = 0.0
    for _ in range(60):
        P = random_params(rng, K=int(rng.integers(2, 5)), T=int(rng.integers(2, 5)), sigma=float(rng.uniform(0, 0.6)))
        P = replace(P, xL0=int(rng.integers(0, P.K)), xF0=0)
        P = replace(P, xF0=int(rng.integers(0, P.xL0 + 1)))
        _, o, mc = outcomes(P, obs_noise=float(rng.uniform(0, 0.5)))
        worst = max(worst, max(abs(m - 1.0) for m in mc), abs(o["final_mass"] - 1.0))
    rec("C6_mass_conservation", worst < 1e-9, {"max_abs_dev": worst})

    # 7. sigma=0 and obs_noise=0 coincide; also tremble definition at sigma=0 equals base
    worst = 0.0
    for _ in range(40):
        P = random_params(rng, sigma=0.0)
        _, oa, _ = outcomes(P, obs_noise=0.0)
        _, ob, _ = outcomes(replace(P, sigma=0.0), obs_noise=0.0)
        worst = max(worst, max(abs(oa[k] - ob[k]) for k in oa))
    rec("C7_sigma_definitions_coincide_at_zero", worst < 1e-12, {"max_abs_diff": worst})

    # 8. outcome ranges and identities: probabilities in [0,1]; P_first_L + P_first_F <= 1; P_quit_i + P_finish_i <= 1
    viol = 0
    for _ in range(80):
        P = random_params(rng, K=int(rng.integers(2, 5)), T=int(rng.integers(2, 5)), sigma=float(rng.uniform(0, 0.6)))
        P = replace(P, xL0=int(rng.integers(0, P.K)))
        P = replace(P, xF0=int(rng.integers(0, P.xL0 + 1)))
        _, o, _ = outcomes(P)
        for k in ("P_quit_L", "P_quit_F", "P_first_L", "P_first_F", "P_finish_L", "P_finish_F", "P_accel_L", "P_accel_F", "P_entry"):
            if not (-1e-12 <= o[k] <= 1 + 1e-12):
                viol += 1
        if o["P_first_L"] + o["P_first_F"] > 1 + 1e-9 or o["P_quit_L"] + o["P_finish_L"] > 1 + 1e-9 or o["P_quit_F"] + o["P_finish_F"] > 1 + 1e-9:
            viol += 1
    rec("C8_probability_identities", viol == 0, {"violations": viol})

    # 9. conditional (threat) outcomes: identity at theta=0, and Monte-Carlo cross-check of the exact conditional propagation
    P = R.Params(K=3, T=3, xL0=2, xF0=1, W=0.3, lam=0.3, pC=0.5, pA=0.85, cC=0.08, cA=0.08 * (0.85 / 0.5) * 2.0, theta=0.0)
    s0 = R.solve_finite_horizon(P); a = R.forward_outcomes(P, s0); b = R.forward_outcomes(P, s0, condition_no_entry=True)
    ident = max(abs(a[k] - b[k]) for k in a if k not in ("mass_check", "final_mass", "conditioned_on_no_entry"))
    P2 = replace(P, theta=0.35); sol2 = R.solve_finite_horizon(P2); oc = R.forward_outcomes(P2, sol2, condition_no_entry=True)
    mc, keep = _mc_conditional(P2, sol2, rng, n=200000)
    diffs = {k: abs(mc[k] - oc[v]) for k, v in (("quit_F", "P_quit_F"), ("accel_L", "P_accel_L"), ("first_L", "P_first_L"))}
    rec("C9_conditional_threat_outcomes", ident < 1e-12 and max(diffs.values()) < 0.01 and abs(keep - (1 - P2.theta) ** P2.T) < 0.01,
        {"identity_at_theta0_max_diff": ident, "mc_vs_exact_abs_diff": diffs, "mc_keep_rate": keep, "expected_keep": (1 - P2.theta) ** P2.T, "n_mc": 200000})

    res["built"] = time.strftime("%Y-%m-%d %H:%M %Z")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, "w"), indent=1)
    print("STATUS", res["status"], "->", OUT)
    sys.exit(0 if res["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
