#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage B environment: a three-period innovation race in which one firm is played by an external agent (LLM or a
scripted policy) and the rival follows the equilibrium policy of model/race_model.py at the TRUE state.

The environment is the model of MODEL_NOTES.md with concrete money units for the prompt (1 unit = 100억원):
  prize first V = 100억, second W = 30억, simultaneous (V+W)/2 = 65억; nothing if unfinished by the end of period 3
  per-period cost: continue 8억 (success 50 %), accelerate 25억 (success 80 %); stop: 0 and out
  entry: in a 'threat' game a new competitor enters at the start of each period with probability 35 % (once; permanent);
         after entry, prizes for products not yet finished are halved (λ = 0.5)
  observation: in a 'noise' game the rival's position is shown with a one-step error with probability 40 %
Parameters are therefore P = Params(K=3, T=3, V=1, W=0.3, lam=0.5, theta=0.35 or 0, sigma=0, pC=0.5, pA=0.8, cC=0.08, cA=0.25).
cA/cC = 3.125 > pA/pC = 1.6 (convex) — checked by Params.check().
The acceleration cost was 20억 in the Task 8 draft; at 20억 the model's leader one stage from completion accelerates with
probability 1.000 already at theta = 0 (the model's own ceiling, so H1 has no room). calibrate_env.py scans cA on a 5억 grid
with a rule fixed before the scan and 25억 is the unique value that passes (results/05_stage_b_env_calibration.json;
2026-11-10, before any Stage B LLM call). At 25억 the model gives, for the agent's seat: gap 2 leader accelerate | no entry
0.375 (theta 0) -> 0.572 (theta 0.35); gap 0 laggard quit 0.375 -> 0.863; leader quit 0.

Cells: gap 0 = agent at x=1 vs rival x=2 (one stage behind); gap 1 = both at x=1 (even); gap 2 = agent x=2 vs rival x=1 (one stage
ahead, one stage from completion). (0,2) was rejected on 2026-11-10 because the model's laggard then quits with probability 1 at every
theta, leaving no theta-variation to compare against; with (1,2) the model gives quit 0.50 -> 1.00 as theta goes 0 -> 0.35.
All randomness comes from a numpy Generator passed in; every draw is logged in the episode record.
"""
import sys
import os
from dataclasses import replace

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "model"))
import race_model as R  # noqa: E402

UNIT = 100.0  # 억원 per model unit
BASE = dict(K=3, T=3, V=1.0, W=0.3, lam=0.5, sigma=0.0, pC=0.5, pA=0.8, cC=0.08, cA=0.25)  # cA: calibrate_env.py (was 0.20)
THETA = {0: 0.0, 1: 0.35}
OBS_NOISE = {0: 0.0, 1: 0.4}
POSITIONS = {0: (1, 2), 1: (1, 1), 2: (2, 1)}  # agent x, rival x
ACT_NAMES = {R.Q: "stop", R.C: "continue", R.A: "accelerate"}


class RaceEnv:
    def __init__(self, gap, threat, noise, rng):
        self.gap, self.threat, self.noise = gap, threat, noise
        self.rng = rng
        ax, rx = POSITIONS[gap]
        # solver requires xL0 >= xF0: agent is L when ahead or even, F when behind
        if ax >= rx:
            self.agent_is_L = True
            self.P = R.Params(**BASE, theta=THETA[threat], xL0=ax, xF0=rx)
        else:
            self.agent_is_L = False
            self.P = R.Params(**BASE, theta=THETA[threat], xL0=rx, xF0=ax)
        self.sol = R.solve_finite_horizon(self.P)
        self.obs_noise = OBS_NOISE[noise]
        self.reset()

    # ------------------------------------------------------------------ state
    def reset(self):
        ax, rx = POSITIONS[self.gap]
        self.t = 1
        self.x = {"agent": ax, "rival": rx}
        self.s = {"agent": R.ACTIVE, "rival": R.ACTIVE}
        self.e = 0
        self.cost = {"agent": 0.0, "rival": 0.0}
        self.prize = {"agent": 0.0, "rival": 0.0}
        self.first = None
        self.log = []
        self.done = False
        self.agent_accelerated = False
        self.agent_quit = False

    def _true_state(self):
        if self.agent_is_L:
            return (self.t, self.x["agent"], self.s["agent"], self.x["rival"], self.s["rival"], self.e)
        return (self.t, self.x["rival"], self.s["rival"], self.x["agent"], self.s["agent"], self.e)

    def entry_shock(self):
        """Start-of-period entry draw (before actions). Returns whether entry happened this period."""
        happened = False
        if self.e == 0 and self.P.theta > 0:
            if self.rng.random() < self.P.theta:
                self.e = 1; happened = True
        return happened

    def _observe(self, who):
        """Position of `who` as seen by the other party: exact, or one step off w.p. obs_noise (noise games), as in the
        model's observation-noise variant (MODEL_NOTES §1). Status (active/quit/done) is always observed exactly."""
        x = self.x[who]
        if self.s[who] != R.ACTIVE or self.obs_noise == 0.0:
            return x, x
        if self.rng.random() < self.obs_noise:
            shown = max(x - 1, 0) if self.rng.random() < 0.5 else min(x + 1, self.P.K - 1)
            return shown, x
        return x, x

    def observe_rival_position(self):
        """What the agent is shown about the rival's position. Returns (shown, true)."""
        return self._observe("rival")

    def _state_as_seen_by(self, who, other_shown_x):
        """Post-shock state with the OTHER party's position replaced by what `who` observes."""
        if who == "agent":
            ax, rx = self.x["agent"], other_shown_x
        else:
            ax, rx = other_shown_x, self.x["rival"]
        if self.agent_is_L:
            return (self.t, ax, self.s["agent"], rx, self.s["rival"], self.e)
        return (self.t, rx, self.s["rival"], ax, self.s["agent"], self.e)

    def rival_action(self):
        """Equilibrium action of the rival at the state it observes (agent's position possibly misread in noise games)."""
        if self.s["rival"] != R.ACTIVE:
            return None
        shown_agent_x, _ = self._observe("agent")
        st = self._state_as_seen_by("rival", shown_agent_x)
        mix, actsL, actsF = self.sol.policy[st]
        u = self.rng.random(); acc = 0.0
        for w, (pL, pF) in mix:
            acc += w
            if u <= acc:
                break
        p = pF if self.agent_is_L else pL
        acts = actsF if self.agent_is_L else actsL
        return int(self.rng.choice(acts, p=np.asarray(p) / np.sum(p)))

    def equilibrium_agent_action(self, shown_rival_x=None):
        """The agent's own equilibrium action at the state it observes (scripted-agent control)."""
        if self.s["agent"] != R.ACTIVE:
            return None
        if shown_rival_x is None:
            shown_rival_x = self.x["rival"]
        st = self._state_as_seen_by("agent", shown_rival_x)
        mix, actsL, actsF = self.sol.policy[st]
        u = self.rng.random(); acc = 0.0
        for w, (pL, pF) in mix:
            acc += w
            if u <= acc:
                break
        p = pL if self.agent_is_L else pF
        acts = actsL if self.agent_is_L else actsF
        return int(self.rng.choice(acts, p=np.asarray(p) / np.sum(p)))

    # ------------------------------------------------------------------ step
    def step(self, agent_action, rival_action):
        """Apply intended actions (sigma = 0 so intended = realised). Returns a dict describing what happened."""
        P = self.P
        scale = P.lam if self.e == 1 else 1.0
        rec = {"t": self.t, "entry_state_at_action": self.e, "agent_action": agent_action, "rival_action": rival_action,
               "x_before": dict(self.x), "s_before": dict(self.s)}
        succ = {}
        for who, a in (("agent", agent_action), ("rival", rival_action)):
            if a is None or self.s[who] != R.ACTIVE:
                succ[who] = False; continue
            if a == R.Q:
                self.s[who] = R.QUIT; succ[who] = False
                if who == "agent": self.agent_quit = True
                continue
            if who == "agent" and a == R.A:
                self.agent_accelerated = True
            self.cost[who] += R.cost(P, a)
            succ[who] = bool(self.rng.random() < R.psucc(P, a))
            if succ[who]:
                self.x[who] += 1
        fin = {who: (self.s[who] == R.ACTIVE and self.x[who] >= P.K) for who in ("agent", "rival")}
        if fin["agent"] and fin["rival"]:
            self.prize["agent"] = self.prize["rival"] = (P.V + P.W) / 2 * scale; self.first = "both"
        elif fin["agent"]:
            self.prize["agent"] = (P.W if self.s["rival"] == R.DONE else P.V) * scale
            if self.s["rival"] != R.DONE: self.first = "agent"
        elif fin["rival"]:
            self.prize["rival"] = (P.W if self.s["agent"] == R.DONE else P.V) * scale
            if self.s["agent"] != R.DONE: self.first = "rival"
        for who in ("agent", "rival"):
            if fin[who]:
                self.s[who] = R.DONE; self.x[who] = P.K
        rec.update({"success": succ, "finished": fin, "x_after": dict(self.x), "s_after": dict(self.s), "cost_so_far": dict(self.cost), "prize": dict(self.prize)})
        self.log.append(rec)
        self.t += 1
        if self.t > P.T or (self.s["agent"] != R.ACTIVE and self.s["rival"] != R.ACTIVE):
            self.done = True
            # the entry process keeps running in the remaining periods (it no longer affects payoffs); this keeps
            # P(entry within the horizon) = 1-(1-theta)^T and makes 'no entry' episodes comparable with the model's
            # threat-conditional outcomes
            while self.t <= P.T:
                self.entry_shock(); self.t += 1
        return rec

    def agent_active(self):
        return self.s["agent"] == R.ACTIVE and not self.done

    def outcome(self):
        return {"agent_quit": self.agent_quit, "agent_accelerated": self.agent_accelerated, "agent_finished": self.s["agent"] == R.DONE,
                "agent_first": self.first == "agent", "both_first": self.first == "both", "rival_first": self.first == "rival",
                "entry_occurred": self.e == 1, "agent_cost_units": self.cost["agent"], "agent_prize_units": self.prize["agent"],
                "agent_net_units": self.prize["agent"] - self.cost["agent"], "periods_played": len(self.log)}


def model_period1_action_probs(gap, threat):
    """Equilibrium action probabilities of the agent's seat at the period-1 decision state (t = 1, no entry yet, true
    positions), averaged over the solver's equilibrium-selection mix. This is the model counterpart of the Stage A
    one-shot vignette (which describes exactly this state). Returns {'P_quit', 'P_cont', 'P_accel'}."""
    env = RaceEnv(gap, threat, 0, np.random.default_rng(0))
    st = env._true_state()
    mix, actsL, actsF = env.sol.policy[st]
    acts = actsL if env.agent_is_L else actsF
    probs = np.zeros(3)
    for w, (pL, pF) in mix:
        p = np.asarray(pL if env.agent_is_L else pF, dtype=float)
        p = p / p.sum()
        for a, pa in zip(acts, p):
            probs[int(a)] += w * pa
    return {"P_quit": float(probs[R.Q]), "P_cont": float(probs[R.C]), "P_accel": float(probs[R.A]), "state": [int(v) for v in st],
            "agent_role": "L" if env.agent_is_L else "F"}


def model_predictions_for_cell(gap, threat, noise):
    """Exact model outcomes for the agent's role in this cell (unconditional and threat-conditional), both sigma definitions."""
    env = RaceEnv(gap, threat, noise, np.random.default_rng(0))
    o_u = R.forward_outcomes(env.P, env.sol, obs_noise=env.obs_noise)
    o_c = R.forward_outcomes(env.P, env.sol, obs_noise=env.obs_noise, condition_no_entry=True)
    side = "L" if env.agent_is_L else "F"
    pick = lambda o: {"P_quit": float(o[f"P_quit_{side}"]), "P_accel": float(o[f"P_accel_{side}"]), "P_first": float(o[f"P_first_{side}"]), "P_finish": float(o[f"P_finish_{side}"])}  # noqa: E731
    return {"agent_role": side, "params": {k: getattr(env.P, k) for k in ("K", "T", "xL0", "xF0", "V", "W", "lam", "theta", "sigma", "pC", "pA", "cC", "cA")},
            "obs_noise": env.obs_noise, "unconditional": pick(o_u), "no_entry_conditional": pick(o_c)}
