#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Finite-horizon innovation race with entry threat (theta) and rival unpredictability (sigma).
Specification: model/MODEL_NOTES.md (authoritative). Nothing here is tuned; comparative statics are
read off the whole parameter grid by run_grid.py.

Public API
  Params                      frozen dataclass of all parameters
  solve_finite_horizon(P)     -> Solution (values U, equilibrium policies, multiplicity record)
  forward_outcomes(P, sol, obs_noise=0.0) -> dict of outcome probabilities (exact state-distribution propagation)
  solve_two_period(P)         -> closed-form values/policies for T=2, K=2, xL0=1, xF0=0, sigma=0 (independent code path)
"""
from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, replace
from typing import Dict, List, Tuple

import numpy as np

Q, C, A = 0, 1, 2
ACT = (Q, C, A)
ACTIVE, QUIT, DONE = 0, 1, 2
TOL = 1e-10


@dataclass(frozen=True)
class Params:
    K: int = 3
    T: int = 3
    xL0: int = 2
    xF0: int = 1
    V: float = 1.0
    W: float = 0.3
    lam: float = 0.4
    theta: float = 0.2
    sigma: float = 0.0
    pC: float = 0.5
    pA: float = 0.75
    cC: float = 0.05
    cA: float = 0.15
    beta: float = 1.0
    selection: str = "welfare"  # welfare | leader | laggard

    def check(self):
        assert 0 <= self.xF0 <= self.xL0 < self.K, "need 0 <= xF0 <= xL0 < K"
        assert 0 < self.pC < self.pA <= 1 and 0 < self.cC < self.cA, "need pC<pA, cC<cA"
        assert self.cA / self.cC > self.pA / self.pC, "convexity: cA/cC must exceed pA/pC"
        assert 0 <= self.theta <= 1 and 0 <= self.sigma <= 1 and 0 <= self.lam <= 1 and 0 <= self.W <= self.V
        assert self.selection in ("welfare", "leader", "laggard")


def cost(P: Params, a: int) -> float:
    return 0.0 if a == Q else (P.cC if a == C else P.cA)


def psucc(P: Params, a: int) -> float:
    return 0.0 if a == Q else (P.pC if a == C else P.pA)


def realized_dist(P: Params, a: int) -> List[Tuple[int, float]]:
    """Implementation tremble: intended C/A is replaced by a uniform draw over {C, A} with prob sigma. Q never trembles."""
    if a == Q:
        return [(Q, 1.0)]
    s = P.sigma
    return [(a, 1.0 - s + s / 2.0), (C if a == A else A, s / 2.0)] if s > 0 else [(a, 1.0)]


# ----------------------------------------------------------------------------------------------------------------------
# Nash equilibria of a small bimatrix game
# ----------------------------------------------------------------------------------------------------------------------
def pure_nash(ML: np.ndarray, MF: np.ndarray, actsL, actsF):
    out = []
    for i, aL in enumerate(actsL):
        for j, aF in enumerate(actsF):
            if ML[i, j] >= ML[:, j].max() - TOL and MF[i, j] >= MF[i, :].max() - TOL:
                pL = np.zeros(len(actsL)); pL[i] = 1.0
                pF = np.zeros(len(actsF)); pF[j] = 1.0
                out.append((pL, pF))
    return out


def mixed_nash(ML: np.ndarray, MF: np.ndarray):
    """Support enumeration over all non-empty support pairs (handles 3x3 and smaller). Returns verified NE list."""
    m, n = ML.shape
    found = []
    for k in range(1, m + 1):
        for SL in itertools.combinations(range(m), k):
            for l in range(1, n + 1):
                for SF in itertools.combinations(range(n), l):
                    if k == 1 and l == 1:
                        continue  # pure profiles handled separately
                    # F's mix q on SF makes L indifferent on SL ; L's mix p on SL makes F indifferent on SF
                    q = _solve_mix(ML[np.ix_(SL, SF)], l)
                    p = _solve_mix(MF[np.ix_(SL, SF)].T, k)
                    if q is None or p is None:
                        continue
                    pL = np.zeros(m); pL[list(SL)] = p
                    pF = np.zeros(n); pF[list(SF)] = q
                    if _is_nash(ML, MF, pL, pF):
                        if not any(np.allclose(pL, a, atol=1e-8) and np.allclose(pF, b, atol=1e-8) for a, b in found):
                            found.append((pL, pF))
    return found


def _solve_mix(Msub: np.ndarray, nvars: int):
    """Find q >= 0, sum q = 1, with Msub @ q = v * 1 (same value on every row). Returns q or None."""
    k = Msub.shape[0]
    # unknowns: q (nvars) and v (1)
    Aeq = np.zeros((k + 1, nvars + 1))
    beq = np.zeros(k + 1)
    Aeq[:k, :nvars] = Msub
    Aeq[:k, nvars] = -1.0
    Aeq[k, :nvars] = 1.0
    beq[k] = 1.0
    sol, *_ = np.linalg.lstsq(Aeq, beq, rcond=None)
    if np.linalg.norm(Aeq @ sol - beq) > 1e-8:
        return None
    q = sol[:nvars]
    if (q < -1e-9).any():
        return None
    q = np.clip(q, 0, None)
    return q / q.sum()


def _is_nash(ML, MF, pL, pF):
    uL = ML @ pF
    uF = pL @ MF
    vL = pL @ uL
    vF = uF @ pF
    return (uL.max() <= vL + 1e-8) and (uF.max() <= vF + 1e-8)


def select_equilibrium(P: Params, eqs, ML, MF, actsL, actsF, nL, nF):
    """Selection rule of MODEL_NOTES §3.
    Step 0 (symmetric states, nL == nF and both active): if a label-symmetric equilibrium exists (pL == pF) take the one
    with the highest joint payoff among those; otherwise the equilibrium set consists of mirror pairs and the players are
    assumed to coordinate on a fair public coin over each mirror pair (a correlated equilibrium with the same expected
    payoffs for both). This keeps the solution label-symmetric at d = 0 and lets the model be compared with its mirror.
    Steps 1-3 (asymmetric states): welfare | leader | laggard with the tie-breakers of MODEL_NOTES §3.
    Returns (pL, pF, mix) where mix is a list of (weight, (pL_k, pF_k)) describing the realised profile distribution."""
    def value(e):
        pL, pF = e
        return float(pL @ ML @ pF), float(pL @ MF @ pF)

    def n_accel(e):
        pL, pF = e
        iA_L = actsL.index(A) if A in actsL else None
        iA_F = actsF.index(A) if A in actsF else None
        return (pL[iA_L] if iA_L is not None else 0.0) + (pF[iA_F] if iA_F is not None else 0.0)

    def laggard_effort(e):
        pL, pF = e
        if nF > nL:
            return float(sum(pF[i] * actsF[i] for i in range(len(actsF))))
        return float(sum(pL[i] * actsL[i] for i in range(len(actsL))))

    if nL == nF and len(actsL) == len(actsF) == 3:
        sym = [e for e in eqs if np.allclose(e[0], e[1], atol=1e-8)]
        if sym:
            best = min(sym, key=lambda e: (-(sum(value(e))), n_accel(e)))
            return best[0], best[1], [(1.0, best)]
        # pair each equilibrium with its mirror; coin-flip within the pair, pick the pair by welfare then fewer accelerations
        pairs, used = [], set()
        for i, (pL, pF) in enumerate(eqs):
            if i in used:
                continue
            j = next((k for k, (qL, qF) in enumerate(eqs) if k != i and np.allclose(pL, qF, atol=1e-8) and np.allclose(pF, qL, atol=1e-8)), None)
            if j is None:
                pairs.append([(pL, pF)]); used.add(i)
            else:
                pairs.append([(pL, pF), eqs[j]]); used.update({i, j})
        def pair_key(pr):
            w = sum(sum(value(e)) for e in pr) / len(pr)
            return (-w, sum(n_accel(e) for e in pr) / len(pr))
        pr = min(pairs, key=pair_key)
        mix = [(1.0 / len(pr), e) for e in pr]
        return None, None, mix

    if P.selection == "welfare":
        key = lambda e: (-(sum(value(e))), n_accel(e), laggard_effort(e))  # noqa: E731
    elif P.selection == "leader":
        key = lambda e: (-(value(e)[0] if nL <= nF else value(e)[1]), n_accel(e), laggard_effort(e))  # noqa: E731
    else:
        key = lambda e: (-(value(e)[1] if nF >= nL else value(e)[0]), n_accel(e), laggard_effort(e))  # noqa: E731
    best = min(eqs, key=key)
    return best[0], best[1], [(1.0, best)]


# ----------------------------------------------------------------------------------------------------------------------
# Backward induction
# ----------------------------------------------------------------------------------------------------------------------
class Solution:
    def __init__(self, P: Params):
        self.P = P
        self.U: Dict[tuple, Tuple[float, float]] = {}        # pre-shock value at (t, xL, sL, xF, sF, e)
        self.policy: Dict[tuple, Tuple[list, tuple, tuple]] = {}  # post-shock state -> (mix=[(w,(pL,pF))], actsL, actsF)
        self.n_states = 0
        self.n_multi = 0
        self.n_mixed = 0
        self.stage: Dict[tuple, Tuple[np.ndarray, np.ndarray, list]] = {}  # post-shock state -> (ML, MF, equilibrium set)


def solve_finite_horizon(P: Params) -> Solution:
    P.check()
    sol = Solution(P)
    memo_post: Dict[tuple, Tuple[float, float]] = {}

    def U(t, xL, sL, xF, sF, e):
        key = (t, xL, sL, xF, sF, e)
        if key in sol.U:
            return sol.U[key]
        if t > P.T or (sL != ACTIVE and sF != ACTIVE):
            sol.U[key] = (0.0, 0.0)
            return sol.U[key]
        if e == 1 or P.theta == 0.0:
            val = Upost(t, xL, sL, xF, sF, e)
        else:
            v0 = Upost(t, xL, sL, xF, sF, 0)
            v1 = Upost(t, xL, sL, xF, sF, 1)
            val = ((1 - P.theta) * v0[0] + P.theta * v1[0], (1 - P.theta) * v0[1] + P.theta * v1[1])
        sol.U[key] = val
        return val

    def stage_payoff(t, xL, sL, xF, sF, e, aL, aF):
        """Expected payoff pair for INTENDED actions (aL, aF) at post-shock state."""
        scale = P.lam if e == 1 else 1.0
        tot = [0.0, 0.0]
        distL = realized_dist(P, aL) if sL == ACTIVE else [(None, 1.0)]
        distF = realized_dist(P, aF) if sF == ACTIVE else [(None, 1.0)]
        for rL, wL in distL:
            for rF, wF in distF:
                w = wL * wF
                if w == 0.0:
                    continue
                cL = cost(P, rL) if rL is not None else 0.0
                cF = cost(P, rF) if rF is not None else 0.0
                pL = psucc(P, rL) if rL is not None else 0.0
                pF = psucc(P, rF) if rF is not None else 0.0
                sL1 = QUIT if rL == Q else sL
                sF1 = QUIT if rF == Q else sF
                for sucL, sucF in ((1, 1), (1, 0), (0, 1), (0, 0)):
                    pr = (pL if sucL else 1 - pL) * (pF if sucF else 1 - pF)
                    if pr == 0.0:
                        continue
                    nxL, nxF = xL + (sucL and sL1 == ACTIVE), xF + (sucF and sF1 == ACTIVE)
                    nsL, nsF = sL1, sF1
                    prizeL = prizeF = 0.0
                    finL = nsL == ACTIVE and nxL >= P.K
                    finF = nsF == ACTIVE and nxF >= P.K
                    if finL and finF:
                        prizeL = prizeF = (P.V + P.W) / 2 * scale
                    elif finL:
                        prizeL = (P.W if sF == DONE else P.V) * scale
                    elif finF:
                        prizeF = (P.W if sL == DONE else P.V) * scale
                    if finL:
                        nsL, nxL = DONE, P.K
                    if finF:
                        nsF, nxF = DONE, P.K
                    cont = U(t + 1, nxL, nsL, nxF, nsF, e)
                    tot[0] += w * pr * (prizeL + P.beta * cont[0])
                    tot[1] += w * pr * (prizeF + P.beta * cont[1])
        tot[0] -= sum(wL * (cost(P, rL) if rL is not None else 0.0) for rL, wL in distL)
        tot[1] -= sum(wF * (cost(P, rF) if rF is not None else 0.0) for rF, wF in distF)
        return tot[0], tot[1]

    def Upost(t, xL, sL, xF, sF, e):
        key = (t, xL, sL, xF, sF, e)
        if key in memo_post:
            return memo_post[key]
        sol.n_states += 1
        actsL = ACT if sL == ACTIVE else (None,)
        actsF = ACT if sF == ACTIVE else (None,)
        ML = np.zeros((len(actsL), len(actsF)))
        MF = np.zeros((len(actsL), len(actsF)))
        for i, aL in enumerate(actsL):
            for j, aF in enumerate(actsF):
                ML[i, j], MF[i, j] = stage_payoff(t, xL, sL, xF, sF, e, aL, aF)
        nL, nF = P.K - xL, P.K - xF
        if sL == ACTIVE and sF == ACTIVE:
            eqs = pure_nash(ML, MF, actsL, actsF)
            if not eqs:
                eqs = mixed_nash(ML, MF)
                sol.n_mixed += 1
            if len(eqs) > 1:
                sol.n_multi += 1
            if not eqs:
                raise RuntimeError(f"no equilibrium found at {key}")
            sol.stage[key] = (ML.copy(), MF.copy(), eqs)
            _, _, mix = select_equilibrium(P, eqs, ML, MF, actsL, actsF, nL, nF)
        elif sL == ACTIVE:
            col = ML[:, 0]
            i = max(range(len(actsL)), key=lambda k: (round(col[k], 12), -actsL[k]))  # ties -> lower effort
            pL = np.zeros(len(actsL)); pL[i] = 1.0; pF = np.ones(1)
            mix = [(1.0, (pL, pF))]
        elif sF == ACTIVE:
            row = MF[0, :]
            j = max(range(len(actsF)), key=lambda k: (round(row[k], 12), -actsF[k]))
            pF = np.zeros(len(actsF)); pF[j] = 1.0; pL = np.ones(1)
            mix = [(1.0, (pL, pF))]
        else:
            mix = [(1.0, (np.ones(1), np.ones(1)))]
        val = (sum(w * float(pL @ ML @ pF) for w, (pL, pF) in mix), sum(w * float(pL @ MF @ pF) for w, (pL, pF) in mix))
        memo_post[key] = val
        sol.policy[key] = (mix, actsL, actsF)
        return val

    U(1, P.xL0, ACTIVE, P.xF0, ACTIVE, 0)
    # Solve every post-shock state (not only the ones reachable from the initial state) so that the observation-noise
    # variant never needs a fallback policy: any observed (possibly counterfactual) state has a genuine equilibrium.
    for t in range(1, P.T + 1):
        for xL in range(P.K):
            for xF in range(P.K):
                for sL in (ACTIVE, QUIT, DONE):
                    for sF in (ACTIVE, QUIT, DONE):
                        if sL != ACTIVE and sF != ACTIVE:
                            continue
                        for e in (0, 1):
                            xl = P.K if sL == DONE else xL
                            xf = P.K if sF == DONE else xF
                            Upost(t, xl, sL, xf, sF, e)
    sol.policy_complete = True
    return sol


# ----------------------------------------------------------------------------------------------------------------------
# Forward propagation of the exact state distribution
# ----------------------------------------------------------------------------------------------------------------------
def forward_outcomes(P: Params, sol: Solution, obs_noise: float = 0.0, condition_no_entry: bool = False) -> dict:
    """Exact propagation. State augmented with flags (accelL, accelF) = intended A at least once.
    obs_noise > 0: each firm observes the rival's position with a one-step error w.p. obs_noise (clipped to [0, K-1]) and
    plays its full-information equilibrium action for the OBSERVED state (bounded-rationality variant, MODEL_NOTES §1).
    condition_no_entry: propagate only the branch in which entry never occurs within the horizon and renormalise by its
    probability (1-theta)^T. Behaviour along this branch is still shaped by the THREAT of entry (continuation values embed
    theta), so these are the ex-ante 'threat' comparative statics; the unconditional outcomes mix threat and realised entry."""
    dist = {(P.xL0, ACTIVE, P.xF0, ACTIVE, 0, 0, 0): 1.0}
    out = {"P_quit_L": 0.0, "P_quit_F": 0.0, "P_first_L": 0.0, "P_first_F": 0.0, "P_finish_L": 0.0, "P_finish_F": 0.0,
           "E_cost_L": 0.0, "E_cost_F": 0.0, "E_accel_periods_L": 0.0, "E_accel_periods_F": 0.0, "mass_check": []}

    def joint_action_dist(t, xL, sL, xF, sF, e):
        """Joint intended-action distribution over (aL, aF) at the post-shock true state.
        obs_noise == 0: the selected profile mix (public coin over mirror equilibria at symmetric states).
        obs_noise > 0: each firm plays its marginal from the full-information mix at the state it OBSERVES (rival position
        misread one step w.p. obs_noise); the two firms' draws are then independent."""
        actsL = ACT if sL == ACTIVE else (None,)
        actsF = ACT if sF == ACTIVE else (None,)
        if obs_noise == 0.0:
            mix, aL_, aF_ = sol.policy[(t, xL, sL, xF, sF, e)]
            out = {}
            for w, (pL, pF) in mix:
                for i, aL in enumerate(aL_):
                    for j, aF in enumerate(aF_):
                        if pL[i] * pF[j] > 0:
                            out[(aL, aF)] = out.get((aL, aF), 0.0) + w * pL[i] * pF[j]
            return list(out.items())
        def marginal(firm):
            res = {}
            rival_x, rival_s = (xF, sF) if firm == 0 else (xL, sL)
            obs = [(rival_x, 1.0)]
            if rival_s == ACTIVE and obs_noise > 0:
                lo, hi = max(rival_x - 1, 0), min(rival_x + 1, P.K - 1)
                obs = [(rival_x, 1.0 - obs_noise), (lo, obs_noise / 2), (hi, obs_noise / 2)]
            for ox, w in obs:
                st = (t, xL, sL, ox, sF, e) if firm == 0 else (t, ox, sL, xF, sF, e)
                assert st in sol.policy, f"observed state {st} has no solved policy (solver must cover all states)"
                mix, aL_, aF_ = sol.policy[st]
                for wm, (pL, pF) in mix:
                    pairs = list(zip(aL_, pL)) if firm == 0 else list(zip(aF_, pF))
                    for a, p in pairs:
                        res[a] = res.get(a, 0.0) + w * wm * p
            return res
        mL = marginal(0) if sL == ACTIVE else {None: 1.0}
        mF = marginal(1) if sF == ACTIVE else {None: 1.0}
        return [((aL, aF), wL * wF) for aL, wL in mL.items() for aF, wF in mF.items() if wL * wF > 0]

    for t in range(1, P.T + 1):
        new = {}
        # under conditioning, a flow realised at t survives into the conditioning event only if no entry occurs in t+1..T
        fw = (1 - P.theta) ** (P.T - t) if condition_no_entry else 1.0
        for (xL, sL, xF, sF, e, fL, fF), mass in dist.items():
            if mass == 0.0:
                continue
            if sL != ACTIVE and sF != ACTIVE:
                # absorbing state: payoffs no longer depend on entry, but the entry process keeps running so that the
                # event 'no entry during the horizon' has probability exactly (1-theta)^T in every branch
                if e == 0 and P.theta > 0:
                    new[(xL, sL, xF, sF, 0, fL, fF)] = new.get((xL, sL, xF, sF, 0, fL, fF), 0.0) + mass * (1 - P.theta)
                    if not condition_no_entry:
                        new[(xL, sL, xF, sF, 1, fL, fF)] = new.get((xL, sL, xF, sF, 1, fL, fF), 0.0) + mass * P.theta
                else:
                    new[(xL, sL, xF, sF, e, fL, fF)] = new.get((xL, sL, xF, sF, e, fL, fF), 0.0) + mass
                continue
            shocks = [(e, 1.0)] if e == 1 else ([(0, 1 - P.theta)] if condition_no_entry else [(0, 1 - P.theta), (1, P.theta)])
            for e1, we in shocks:
                if we == 0.0:
                    continue
                scale = P.lam if e1 == 1 else 1.0
                for (aL, aF), wj in joint_action_dist(t, xL, sL, xF, sF, e1):
                    if True:
                        if wj == 0.0:
                            continue
                        m1 = mass * we * wj
                        fL1 = 1 if (fL or aL == A) else 0
                        fF1 = 1 if (fF or aF == A) else 0
                        out["E_accel_periods_L"] += fw * m1 * (aL == A)
                        out["E_accel_periods_F"] += fw * m1 * (aF == A)
                        rdL = realized_dist(P, aL) if aL is not None else [(None, 1.0)]
                        rdF = realized_dist(P, aF) if aF is not None else [(None, 1.0)]
                        for rL, vL in rdL:
                            for rF, vF in rdF:
                                m2 = m1 * vL * vF
                                if m2 == 0.0:
                                    continue
                                out["E_cost_L"] += fw * m2 * (cost(P, rL) if rL is not None else 0.0)
                                out["E_cost_F"] += fw * m2 * (cost(P, rF) if rF is not None else 0.0)
                                sL1 = QUIT if rL == Q else sL
                                sF1 = QUIT if rF == Q else sF
                                if rL == Q:
                                    out["P_quit_L"] += fw * m2
                                if rF == Q:
                                    out["P_quit_F"] += fw * m2
                                pL = psucc(P, rL) if rL is not None else 0.0
                                pF = psucc(P, rF) if rF is not None else 0.0
                                for sucL, sucF in ((1, 1), (1, 0), (0, 1), (0, 0)):
                                    pr = (pL if sucL else 1 - pL) * (pF if sucF else 1 - pF)
                                    if pr == 0.0:
                                        continue
                                    m3 = m2 * pr
                                    nxL = xL + (sucL and sL1 == ACTIVE); nxF = xF + (sucF and sF1 == ACTIVE)
                                    nsL, nsF = sL1, sF1
                                    finL = nsL == ACTIVE and nxL >= P.K
                                    finF = nsF == ACTIVE and nxF >= P.K
                                    if finL and finF:
                                        out["P_first_L"] += fw * 0.5 * m3; out["P_first_F"] += fw * 0.5 * m3
                                    elif finL:
                                        out["P_first_L"] += fw * m3 * (sF != DONE)
                                    elif finF:
                                        out["P_first_F"] += fw * m3 * (sL != DONE)
                                    if finL:
                                        out["P_finish_L"] += fw * m3; nsL, nxL = DONE, P.K
                                    if finF:
                                        out["P_finish_F"] += fw * m3; nsF, nxF = DONE, P.K
                                    k = (nxL, nsL, nxF, nsF, e1, fL1, fF1)
                                    new[k] = new.get(k, 0.0) + m3
        dist = new
        out["mass_check"].append(sum(dist.values()))
    out["P_accel_L"] = sum(m for (xL, sL, xF, sF, e, fL, fF), m in dist.items() if fL)
    out["P_accel_F"] = sum(m for (xL, sL, xF, sF, e, fL, fF), m in dist.items() if fF)
    out["P_entry"] = sum(m for (xL, sL, xF, sF, e, fL, fF), m in dist.items() if e)
    out["final_mass"] = sum(dist.values())
    if condition_no_entry:
        z = out["final_mass"]
        assert abs(z - (1 - P.theta) ** P.T) < 1e-9, (z, (1 - P.theta) ** P.T)
        for k in list(out):
            if k not in ("mass_check", "final_mass", "P_entry"):
                out[k] = out[k] / z if z > 0 else float("nan")
        out["mass_check"] = [m / z for m in out["mass_check"]] if z > 0 else out["mass_check"]
        out["conditioned_on_no_entry"] = True
    return out


# ----------------------------------------------------------------------------------------------------------------------
# Independent closed-form route for T=2, K=2, xL0=1, xF0=0, sigma=0  (MODEL_NOTES §6)
# ----------------------------------------------------------------------------------------------------------------------
def _g(P: Params, R: float):
    """Single firm one step from finishing with prize R: value and action (ties -> lower effort)."""
    cands = [(0.0, Q), (-P.cC + P.pC * R, C), (-P.cA + P.pA * R, A)]
    best = max(cands, key=lambda z: (round(z[0], 12), -z[1]))
    return best


def _nash_select_closed(P: Params, uL: np.ndarray, uF: np.ndarray, nL: int, nF: int):
    """Same selection rule as the general solver but written independently (pure NE by best-response check;
    mixed via the shared support enumeration only if no pure NE exists)."""
    eqs = []
    for i in ACT:
        for j in ACT:
            if uL[i, j] >= uL[:, j].max() - TOL and uF[i, j] >= uF[i, :].max() - TOL:
                pL = np.zeros(3); pL[i] = 1; pF = np.zeros(3); pF[j] = 1
                eqs.append((pL, pF))
    if not eqs:
        eqs = mixed_nash(uL, uF)
    pL, pF, mix = select_equilibrium(P, eqs, uL, uF, ACT, ACT, nL, nF)
    return mix


def solve_two_period(P: Params) -> dict:
    assert P.T == 2 and P.K == 2 and P.xL0 == 1 and P.xF0 == 0 and P.sigma == 0.0 and P.beta == 1.0
    V, W, lam, th = P.V, P.W, P.lam, P.theta
    M = (V + W) / 2

    def period2(s):
        """Returns dict of period-2 values given prize scale s."""
        vF2a, aF2a = _g(P, W * s)          # (2a) laggard alone, second prize
        vL2d, aL2d = _g(P, V * s)          # (2d) leader alone
        vFalone, aFalone = _g(P, V * s)    # laggard alone after leader quit, first prize
        # (2c) neck-and-neck last period
        uL = np.zeros((3, 3)); uF = np.zeros((3, 3))
        for i in ACT:
            for j in ACT:
                pi, pj = psucc(P, i), psucc(P, j)
                uL[i, j] = -cost(P, i) + pi * s * (V - pj * (V - M))
                uF[i, j] = -cost(P, j) + pj * s * (V - pi * (V - M))
        mix = _nash_select_closed(P, uL, uF, 1, 1)
        uL2c = sum(w * float(pL @ uL @ pF) for w, (pL, pF) in mix)
        uF2c = sum(w * float(pL @ uF @ pF) for w, (pL, pF) in mix)
        return {"vF2a": vF2a, "vL2d": vL2d, "vFalone": vFalone, "uL2c": uL2c, "uF2c": uF2c, "mix2c": mix}

    def E2(e1, key):
        if e1 == 1:
            return period2(lam)[key]
        return (1 - th) * period2(1.0)[key] + th * period2(lam)[key]

    def period1(e1):
        s1 = lam if e1 == 1 else 1.0
        uL = np.zeros((3, 3)); uF = np.zeros((3, 3))
        for aL in ACT:
            for aF in ACT:
                pL, pF = psucc(P, aL), psucc(P, aF)
                uL[aL, aF] = -cost(P, aL) + pL * V * s1 + (1 - pL) * (pF * E2(e1, "uL2c") + (1 - pF) * E2(e1, "vL2d"))
                if aL == Q:
                    uF[aL, aF] = -cost(P, aF) + pF * E2(e1, "vFalone")
                else:
                    uF[aL, aF] = -cost(P, aF) + pF * (pL * E2(e1, "vF2a") + (1 - pL) * E2(e1, "uF2c"))
        mix = _nash_select_closed(P, uL, uF, 1, 2)
        assert len(mix) == 1, "asymmetric state (nL=1, nF=2) must select a single profile"
        pL, pF = mix[0][1]
        return {"uL": float(pL @ uL @ pF), "uF": float(pL @ uF @ pF), "pL": pL, "pF": pF}

    r0, r1 = period1(0), period1(1)
    U0 = ((1 - th) * r0["uL"] + th * r1["uL"], (1 - th) * r0["uF"] + th * r1["uF"])
    # outcome probabilities (quit of F ever, accelerate of L ever, L first) by explicit enumeration
    def outcomes(e1, r):
        s1 = lam if e1 == 1 else 1.0
        PqF = PaL = PfirstL = 0.0
        for aL in ACT:
            for aF in ACT:
                w = r["pL"][aL] * r["pF"][aF]
                if w == 0:
                    continue
                PaL += w * (aL == A)
                PqF += w * (aF == Q)
                pL, pF = psucc(P, aL), psucc(P, aF)
                PfirstL += w * pL  # leader finishing at t=1 is always first (F cannot finish at t=1)
                # period 2 contributions
                for e2, we in ([(1, 1.0)] if e1 == 1 else [(0, 1 - th), (1, th)]):
                    s2 = lam if e2 == 1 else 1.0
                    p2 = period2(s2)
                    # L failed (prob 1-pL): if F succeeded -> 2c; else -> 2d
                    if aL != Q:
                        for wm, (pl2c, pf2c) in p2["mix2c"]:
                            # L first at t=2 in 2c: L succeeds and F fails (+ half if both)
                            PfirstL += wm * w * we * (1 - pL) * pF * sum(pl2c[i] * pf2c[j] * (psucc(P, i) * (1 - psucc(P, j)) + 0.5 * psucc(P, i) * psucc(P, j)) for i in ACT for j in ACT)
                            PaL += wm * w * we * (1 - pL) * pF * pl2c[A] * (aL != A)
                            PqF += wm * w * we * (1 - pL) * pF * pf2c[Q]
                        # 2d: F at 0 quits (if it had not quit); L alone
                        vL2d, aL2d = _g(P, V * s2)
                        PfirstL += w * we * (1 - pL) * (1 - pF) * (psucc(P, aL2d))
                        PaL += w * we * (1 - pL) * (1 - pF) * (aL2d == A) * (aL != A)
                        PqF += w * we * (1 - pL) * (1 - pF) * (aF != Q)  # F at x=0 cannot finish -> quits at t=2
                        # 2a: L finished, F at 1 alone with W
                        vF2a, aF2a = _g(P, W * s2)
                        PqF += w * we * pL * pF * (aF2a == Q)
                        PqF += w * we * pL * (1 - pF) * (aF != Q)  # 2b: F at 0 quits
                    else:
                        vFa, aFa = _g(P, V * s2)
                        PqF += w * we * pF * (aFa == Q) + w * we * (1 - pF) * (aF != Q)
        return PqF, PaL, PfirstL
    o0, o1 = outcomes(0, r0), outcomes(1, r1)
    PqF = (1 - th) * o0[0] + th * o1[0]
    PaL = (1 - th) * o0[1] + th * o1[1]
    PfL = (1 - th) * o0[2] + th * o1[2]
    return {"U0": U0, "policy_t1_e0": (r0["pL"], r0["pF"]), "policy_t1_e1": (r1["pL"], r1["pF"]),
            "P_quit_F": PqF, "P_accel_L": PaL, "P_first_L": PfL}
