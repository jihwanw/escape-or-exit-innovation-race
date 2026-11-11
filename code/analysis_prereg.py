#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pre-registered confirmatory analysis for "Escape or Exit" (Task 9 freeze; executed in Task 10 after OSF registration).

EMBARGO. This script refuses to touch real outcome x treatment combinations unless prereg/REGISTERED.json exists and contains
an OSF URL and a registration timestamp (gate C). Before registration only two modes run:
  --simulate   known-answer control: outcomes are REPLACED by Bernoulli draws from a known DGP on the real covariates
               (b_g2 = +0.03 for preempt, b_g0 = +0.04 for quit, everything else 0) and the pipeline must recover the signs
  --permute    null control: real outcomes permuted within wave x sector (breaks any outcome-treatment link); all tests
               should be null at the nominal rate
Both write to results/06_kis_main_<mode>.json and never to the real results file.

Hypotheses (docs/HYPOTHESES_GATE_B.md, gate B approved 2026-11-10). Specification for every hypothesis:
  y_i = sum_g [ a_g 1(gap3_i = g) + b_g x_i 1(gap3_i = g) ] + controls_i' c + industry2 FE + wave FE + e_i
  with x = entry_threat_resid (perceived threat, within-wave residual after response-propensity adjustment, SD units) for
  H1-H5 and x = entry_rate_z (industry x reference-period entry rate, SD units) for H6 and the objective half of H2.
  g = gap3 in {0: no dedicated R&D staff, 1: positive <= industry x wave median of positives, 2: above median}.
  Estimator: linear probability model (OLS); SE clustered by industry2 x wave; wild cluster bootstrap-t (Rademacher,
  unrestricted, 999 draws) p-values; logit average marginal effects as a secondary estimator.
  Samples: quit models = innovation-active firms (quit_any defined); preempt models = all firms.
  Controls: log_employees, log(1 + firm_age), group affiliation dummies, listed, me_mean8; quit models add portfolio_breadth.
  H1 b_g2 > 0 (preempt, perceived); H2 b_g0 > 0 (quit, perceived; objective version reported, falsified only if both <= 0);
  H3 b_g0 - b_g2 > 0 (quit); H4 b_g2 - b_g0 > 0 (preempt); H5 a_g0 - a_g2 > 0 (quit; x centred so a_g = adjusted mean at
  average threat); H6 TOST: 90 % CI of b_g2 (preempt, objective) inside [-delta, +delta], delta = 0.010 (= H1 MDE per SD,
  results/02_marginals.json F_power_synthetic.preempt_strategy.mde80_perceived_interaction_by_delta).
  Tests H1-H5 are one-sided at alpha = 0.05 with Holm adjustment across the five. PRIMARY inference = wild cluster
  bootstrap-t p-values and percentile-t confidence intervals; the cluster-robust t is reported as secondary because the
  permutation control (--permute, 30 draws; results/06_kis_main_permute.json known_truth.null_rejection_rates_nominal_0.05)
  showed it anti-conservative for the industry-level regressor: two-sided null rejection at nominal 0.05 was 0.10 (H6)
  and 0.20 (objective H2) for the cluster-robust t against 0.03 and 0.07 for the wild bootstrap. Decision rule:
  'supported' if the point estimate has the predicted sign and the Holm-adjusted one-sided wild p < 0.05; 'directional' if
  the sign is right but adjusted p >= 0.05; 'not supported' otherwise. H6: 'equivalence' if the 90 % wild percentile-t CI
  lies inside [-delta, +delta], 'positive effect' if entirely above +delta, 'negative effect' if entirely below -delta,
  'inconclusive' otherwise.
Pre-registered placebo: the same models with x = placebo_demand_resid / placebo_price_resid (ME6, ME8 residualised the same
  way) must show no significant interaction (two-sided 5 %).
Pre-registered robustness (reported, not used for the decision): raw 0-5 entry_threat instead of the residual; industry2 x
  wave FE; KIS weights; excluding 2023S; sector split; exit_strict / exit_full as the quit outcome; logit AMEs.
Exploratory (results/07_kis_exploratory.json, labelled as such): market_first_main (manufacturing product innovators,
  with a two-step selection correction), gap3 = 1 effects, sigma item (ME5) signs, cell-mean tables by threat tercile.
"""
import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PANEL = os.path.join(ROOT, "data", "analysis_panel.parquet")
REGISTERED = os.path.join(ROOT, "prereg", "REGISTERED.json")
SEED = 20261110
N_BOOT = 999
DELTA_H6 = 0.010
ALPHA = 0.05

CONTROLS = ["log_employees", "log1p_firm_age", "group_dom", "group_for", "listed", "me_mean8"]
CONTROLS_QUIT = CONTROLS + ["portfolio_breadth"]


# ------------------------------------------------------------------------------------------------------- data
def load_panel():
    p = pd.read_parquet(PANEL)
    p["log1p_firm_age"] = np.log1p(p["firm_age"])
    p["group_dom"] = (p["group_affiliate"] == 2).astype(float)
    p["group_for"] = (p["group_affiliate"] == 3).astype(float)
    # residualised placebo items, same recipe as entry_threat_resid (within wave, on me_mean8, standardised)
    for src, name in (("placebo_demand", "placebo_demand_resid"), ("placebo_price", "placebo_price_resid")):
        out = pd.Series(np.nan, index=p.index)
        for w, d in p.groupby("wave"):
            X = sm.add_constant(d[["me_mean8"]].astype(float))
            r = sm.OLS(d[src].astype(float), X, missing="drop").fit().resid
            out.loc[r.index] = (r - r.mean()) / r.std(ddof=0)
        p[name] = out
    return p


def design(df, y, x, controls, fe_interacted=False):
    """Return (y, X DataFrame with named columns, cluster ids) for the interaction specification."""
    cols = [y, x, "gap3", "industry2", "wave", "cluster_industry_wave"] + controls
    d = df.dropna(subset=cols).copy()
    g0 = (d["gap3"] == 0).astype(float); g1 = (d["gap3"] == 1).astype(float); g2 = (d["gap3"] == 2).astype(float)
    X = pd.DataFrame({"g0": g0, "g2": g2, "x_g0": d[x] * g0, "x_g1": d[x] * g1, "x_g2": d[x] * g2}, index=d.index)
    for c in controls:
        X[c] = d[c].astype(float)
    if fe_interacted:
        fe = pd.get_dummies(d["cluster_industry_wave"].astype(str), prefix="iw", drop_first=True, dtype=float)
    else:
        fe = pd.concat([pd.get_dummies(d["industry2"].astype(int).astype(str), prefix="ind", drop_first=True, dtype=float),
                        pd.get_dummies(d["wave"].astype(str), prefix="w", drop_first=True, dtype=float)], axis=1)
    X = pd.concat([X, fe], axis=1)
    X.insert(0, "const", 1.0)
    # drop constant/collinear FE columns (e.g., an industry present in one wave only is fine; all-zero columns are not)
    X = X.loc[:, (X != 0).any(axis=0)]
    return d[y].astype(float), X, d["cluster_industry_wave"].astype(str), d["weight"].astype(float)


# ------------------------------------------------------------------------------------------------------- estimation
def ols_cluster(y, X, clusters, weights=None):
    model = sm.WLS(y, X, weights=weights) if weights is not None else sm.OLS(y, X)
    return model.fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(clusters)[0]})


def linear_combo(fit, combo):
    """combo: dict column -> coefficient. Returns estimate, SE (cluster), t, one-sided p (H: combo > 0), two-sided p, df."""
    names = list(fit.params.index)
    c = np.zeros(len(names))
    for k, v in combo.items():
        c[names.index(k)] = v
    est = float(c @ fit.params.values)
    var = float(c @ fit.cov_params().values @ c)
    se = var ** 0.5
    t = est / se if se > 0 else np.nan
    return est, se, t


def wild_cluster_bootstrap_t(y, X, clusters, combo, n_boot=N_BOOT, seed=SEED, weights=None):
    """Unrestricted wild cluster bootstrap-t (Rademacher) for the linear combination combo (one- and two-sided p)."""
    rng = np.random.default_rng(seed)
    fit = ols_cluster(y, X, clusters, weights)
    est, se, t0 = linear_combo(fit, combo)
    resid = fit.resid.values; fitted = fit.fittedvalues.values
    cl = pd.factorize(clusters)[0]; G = cl.max() + 1
    Xv = X.values; XtX_inv = np.linalg.pinv(Xv.T @ Xv) if weights is None else None
    names = list(X.columns); c = np.zeros(len(names))
    for k, v in combo.items():
        c[names.index(k)] = v
    ts = np.empty(n_boot)
    for b in range(n_boot):
        w = rng.choice([-1.0, 1.0], size=G)[cl]
        yb = fitted + resid * w
        if weights is None:
            beta_b = XtX_inv @ (Xv.T @ yb)
            e_b = yb - Xv @ beta_b
            # cluster-robust variance of c'beta
            meat = np.zeros((Xv.shape[1], Xv.shape[1]))
            Xe = Xv * e_b[:, None]
            S = np.zeros((G, Xv.shape[1]))
            np.add.at(S, cl, Xe)
            meat = S.T @ S
            V = XtX_inv @ meat @ XtX_inv
            # small-sample correction as statsmodels: G/(G-1) * (N-1)/(N-K)
            N, K = Xv.shape
            V *= (G / (G - 1)) * ((N - 1) / (N - K))
            est_b = float(c @ beta_b); se_b = float(np.sqrt(c @ V @ c))
        else:
            fb = ols_cluster(pd.Series(yb, index=y.index), X, clusters, weights)
            est_b, se_b, _ = linear_combo(fb, combo)
        ts[b] = (est_b - est) / se_b if se_b > 0 else 0.0
    p_two = float(np.mean(np.abs(ts) >= abs(t0)))
    p_one_pos = float(np.mean(ts >= t0))  # H1: combo > 0 -> small p when t0 is large positive
    q = lambda a: float(np.quantile(ts, a))  # noqa: E731  (percentile-t: CI = [est - q_hi*se, est - q_lo*se])
    return {"estimate": est, "se_cluster": se, "t": t0, "p_two_sided_cluster_t": float(2 * stats.t.sf(abs(t0), df=G - 1)),
            "p_one_sided_cluster_t": float(stats.t.sf(t0, df=G - 1)), "p_two_sided_wild": p_two, "p_one_sided_wild": p_one_pos,
            "ci95_cluster": [est - stats.t.ppf(0.975, G - 1) * se, est + stats.t.ppf(0.975, G - 1) * se],
            "ci90_cluster": [est - stats.t.ppf(0.95, G - 1) * se, est + stats.t.ppf(0.95, G - 1) * se],
            "ci95_wild": [est - q(0.975) * se, est - q(0.025) * se], "ci90_wild": [est - q(0.95) * se, est - q(0.05) * se],
            "n": int(len(y)), "n_clusters": int(G), "n_boot": n_boot}


def logit_ame(y, X, clusters, combo_cols):
    """Logit with the same columns; average marginal effect of x within each gap group (secondary estimator). Returns dict or error."""
    try:
        Xl = X.copy()
        try:
            fit = sm.Logit(y, Xl).fit(disp=0, maxiter=100, method="newton")
        except Exception:
            fit = sm.Logit(y, Xl).fit(disp=0, maxiter=500, method="bfgs")
        out = {}
        for col in combo_cols:
            # AME of a one-unit increase in the interaction column among the rows where the group dummy is active
            idx = Xl[col] != 0
            if idx.sum() == 0:
                continue
            X1 = Xl[idx].copy(); X1[col] = X1[col] + 1.0
            out[col] = float(np.mean(fit.predict(X1) - fit.predict(Xl[idx])))
        return {"ame": out, "converged": bool(fit.mle_retvals.get("converged", True)), "llf": float(fit.llf)}
    except Exception as e:  # noqa
        return {"error": str(e)[:200]}


def holm(pvals):
    """Holm step-down adjusted p-values for a dict name -> p."""
    names = list(pvals); p = np.array([pvals[k] for k in names], dtype=float); m = len(p)
    order = np.argsort(p); adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        val = min(1.0, (m - rank) * p[i]); running = max(running, val); adj[i] = running
    return {k: float(v) for k, v in zip(names, adj)}


# ------------------------------------------------------------------------------------------------------- hypotheses
def run_hypotheses(p, x_perc="entry_threat_resid", x_obj="entry_rate_z", fe_interacted=False, weighted=False, quit_y="quit_any", n_boot=N_BOOT, tag="main"):
    res = {"tag": tag, "x_perceived": x_perc, "x_objective": x_obj, "fe_interacted": fe_interacted, "weighted": weighted, "quit_outcome": quit_y, "tests": {}}
    # quit models (innovation-active firms; quit_y defined only there)
    yq, Xq, cq, wq = design(p[p["innov_active"] == 1], quit_y, x_perc, CONTROLS_QUIT, fe_interacted)
    yp, Xp, cp, wp = design(p, "preempt_strategy", x_perc, CONTROLS, fe_interacted)
    yqo, Xqo, cqo, wqo = design(p[p["innov_active"] == 1], quit_y, x_obj, CONTROLS_QUIT, fe_interacted)
    ypo, Xpo, cpo, wpo = design(p, "preempt_strategy", x_obj, CONTROLS, fe_interacted)
    W = (lambda w: w) if weighted else (lambda w: None)
    res["tests"]["H1"] = wild_cluster_bootstrap_t(yp, Xp, cp, {"x_g2": 1.0}, n_boot, SEED + 1, W(wp))
    res["tests"]["H2"] = wild_cluster_bootstrap_t(yq, Xq, cq, {"x_g0": 1.0}, n_boot, SEED + 2, W(wq))
    res["tests"]["H2_objective"] = wild_cluster_bootstrap_t(yqo, Xqo, cqo, {"x_g0": 1.0}, n_boot, SEED + 3, W(wqo))
    res["tests"]["H3"] = wild_cluster_bootstrap_t(yq, Xq, cq, {"x_g0": 1.0, "x_g2": -1.0}, n_boot, SEED + 4, W(wq))
    res["tests"]["H4"] = wild_cluster_bootstrap_t(yp, Xp, cp, {"x_g2": 1.0, "x_g0": -1.0}, n_boot, SEED + 5, W(wp))
    res["tests"]["H5"] = wild_cluster_bootstrap_t(yq, Xq, cq, {"g0": 1.0, "g2": -1.0}, n_boot, SEED + 6, W(wq))
    res["tests"]["H6"] = wild_cluster_bootstrap_t(ypo, Xpo, cpo, {"x_g2": 1.0}, n_boot, SEED + 7, W(wpo))
    # all slope coefficients for the tables
    res["coefficients"] = {}
    for name, (y, X, c, w) in {"quit_perceived": (yq, Xq, cq, wq), "preempt_perceived": (yp, Xp, cp, wp), "quit_objective": (yqo, Xqo, cqo, wqo), "preempt_objective": (ypo, Xpo, cpo, wpo)}.items():
        fit = ols_cluster(y, X, c, W(w))
        keep = ["g0", "g2", "x_g0", "x_g1", "x_g2"] + [k for k in (CONTROLS_QUIT if "quit" in name else CONTROLS)]
        res["coefficients"][name] = {"n": int(len(y)), "n_clusters": int(c.nunique()), "mean_y": float(y.mean()),
                                     "coef": {k: float(fit.params[k]) for k in keep if k in fit.params}, "se": {k: float(fit.bse[k]) for k in keep if k in fit.bse},
                                     "logit_ame": logit_ame(y, X, c, ["x_g0", "x_g1", "x_g2"]) if not weighted else None}
    # Holm across H1-H5 (one-sided), separately for cluster-t and wild p
    primary = ["H1", "H2", "H3", "H4", "H5"]
    res["holm_cluster_t"] = holm({h: res["tests"][h]["p_one_sided_cluster_t"] for h in primary})
    res["holm_wild"] = holm({h: res["tests"][h]["p_one_sided_wild"] for h in primary})
    res["decisions"] = {}
    for h in primary:
        t = res["tests"][h]; sign_ok = t["estimate"] > 0
        res["decisions"][h] = "supported" if (sign_ok and res["holm_wild"][h] < ALPHA) else ("directional" if sign_ok else "not supported")
    lo, hi = res["tests"]["H6"]["ci90_wild"]
    res["decisions"]["H6"] = "equivalence (no positive effect)" if (lo > -DELTA_H6 and hi < DELTA_H6) else ("positive effect" if lo > DELTA_H6 else ("negative effect" if hi < -DELTA_H6 else "inconclusive"))
    res["H6_delta"] = DELTA_H6
    # H2 falsification condition: both perceived and objective <= 0
    res["H2_falsified_both_nonpositive"] = bool(res["tests"]["H2"]["estimate"] <= 0 and res["tests"]["H2_objective"]["estimate"] <= 0)
    return res


def run_placebos(p, n_boot=N_BOOT):
    out = {}
    for x in ("placebo_demand_resid", "placebo_price_resid"):
        yq, Xq, cq, _ = design(p[p["innov_active"] == 1], "quit_any", x, CONTROLS_QUIT)
        yp, Xp, cp, _ = design(p, "preempt_strategy", x, CONTROLS)
        out[x] = {"quit_x_g0": wild_cluster_bootstrap_t(yq, Xq, cq, {"x_g0": 1.0}, n_boot, SEED + 11), "preempt_x_g2": wild_cluster_bootstrap_t(yp, Xp, cp, {"x_g2": 1.0}, n_boot, SEED + 12)}
        out[x]["any_significant_two_sided_5pct"] = bool(out[x]["quit_x_g0"]["p_two_sided_wild"] < 0.05 or out[x]["preempt_x_g2"]["p_two_sided_wild"] < 0.05)
    return out


def cell_tables(p):
    """Descriptive cell means: outcome by gap3 x tercile of the perceived-threat residual (within wave) and by entry-rate tercile."""
    out = {}
    d = p.copy()
    d["thr_terc"] = d.groupby("wave")["entry_threat_resid"].transform(lambda s: pd.qcut(s.rank(method="first"), 3, labels=[0, 1, 2]))
    d["er_terc"] = d.groupby("wave")["entry_rate_z"].transform(lambda s: pd.qcut(s.rank(method="first"), 3, labels=[0, 1, 2]))
    for y, sub in (("quit_any", d[d["innov_active"] == 1]), ("preempt_strategy", d)):
        for tcol in ("thr_terc", "er_terc"):
            t = sub.groupby(["gap3", tcol], observed=True)[y].agg(["mean", "size"]).reset_index()
            out[f"{y}_by_gap3_x_{tcol}"] = [{"gap3": int(r.gap3), "tercile": int(r[tcol]), "mean": float(r["mean"]), "n": int(r["size"])} for _, r in t.iterrows()]
    return out


def run_robustness(p, n_boot=299):
    rob = {}
    rob["raw_threat_0_5"] = run_hypotheses(p, x_perc="entry_threat", n_boot=n_boot, tag="raw_threat")
    rob["fe_industry_x_wave"] = run_hypotheses(p, fe_interacted=True, n_boot=n_boot, tag="fe_iw")
    rob["weighted"] = run_hypotheses(p, weighted=True, n_boot=n_boot, tag="weighted")
    rob["excl_2023S"] = run_hypotheses(p[p["wave"] != "2023S"], n_boot=n_boot, tag="excl_2023S")
    rob["manufacturing_only"] = run_hypotheses(p[p["sector"] == "manufacturing"], n_boot=n_boot, tag="manufacturing")
    rob["services_only"] = run_hypotheses(p[p["sector"] == "services"], n_boot=n_boot, tag="services")
    rob["exit_strict"] = run_hypotheses(p, quit_y="exit_strict", n_boot=n_boot, tag="exit_strict")
    rob["exit_full"] = run_hypotheses(p, quit_y="exit_full", n_boot=n_boot, tag="exit_full")
    return rob


def run_exploratory(p, n_boot=299):
    ex = {"label": "EXPLORATORY — not pre-registered as confirmatory; no decision attached"}
    # market_first_main among manufacturing product innovators, with a two-step selection correction for being a product innovator
    m = p[p["sector"] == "manufacturing"].copy()
    sel_cols = CONTROLS + ["gap3", "entry_threat_resid", "industry2", "wave"]
    ms = m.dropna(subset=sel_cols + ["product_innovator"]).copy()
    Xs = pd.concat([pd.DataFrame({"const": 1.0, "g0": (ms.gap3 == 0).astype(float), "g2": (ms.gap3 == 2).astype(float), "x": ms.entry_threat_resid}, index=ms.index),
                    ms[CONTROLS].astype(float), pd.get_dummies(ms["industry2"].astype(int).astype(str), prefix="ind", drop_first=True, dtype=float),
                    pd.get_dummies(ms["wave"].astype(str), prefix="w", drop_first=True, dtype=float)], axis=1)
    try:
        probit = sm.Probit(ms["product_innovator"].astype(float), Xs).fit(disp=0, maxiter=200)
        xb = probit.fittedvalues
        imr = stats.norm.pdf(xb) / stats.norm.cdf(xb)
        ms["imr"] = imr
        mi = ms[ms["product_innovator"] == 1]
        y, X, c, _ = design(mi.assign(imr=mi["imr"]), "market_first_main", "entry_threat_resid", CONTROLS + ["imr"])
        ex["market_first_main_heckman2step"] = {"note": "selection = product innovator; probit on the same covariates (no exclusion restriction — identification by non-linearity only)",
                                                "n_selection": int(len(ms)), "n_outcome": int(len(y)), "x_g2": wild_cluster_bootstrap_t(y, X, c, {"x_g2": 1.0}, n_boot, SEED + 21),
                                                "x_g0": wild_cluster_bootstrap_t(y, X, c, {"x_g0": 1.0}, n_boot, SEED + 22)}
    except Exception as e:  # noqa
        ex["market_first_main_heckman2step"] = {"error": str(e)[:300]}
    # gap3 = 1 group and sigma item
    yq, Xq, cq, _ = design(p[p["innov_active"] == 1], "quit_any", "entry_threat_resid", CONTROLS_QUIT)
    yp, Xp, cp, _ = design(p, "preempt_strategy", "entry_threat_resid", CONTROLS)
    ex["gap1_quit_x_g1"] = wild_cluster_bootstrap_t(yq, Xq, cq, {"x_g1": 1.0}, n_boot, SEED + 23)
    ex["gap1_preempt_x_g1"] = wild_cluster_bootstrap_t(yp, Xp, cp, {"x_g1": 1.0}, n_boot, SEED + 24)
    for y, sub, ctrl in (("quit_any", p[p["innov_active"] == 1], CONTROLS_QUIT), ("preempt_strategy", p, CONTROLS)):
        ys, Xs2, cs, _ = design(sub, y, "rival_unpredictability_resid", ctrl)
        ex[f"sigma_item_{y}"] = {g: wild_cluster_bootstrap_t(ys, Xs2, cs, {f"x_{g}": 1.0}, n_boot, SEED + 25) for g in ("g0", "g2")}
    ex["cell_tables"] = cell_tables(p)
    return ex


# ------------------------------------------------------------------------------------------------------- modes
def simulate_outcomes(p, rng):
    """Known-answer DGP on the real covariates: preempt ~ 0.04 + 0.03 * x * 1(g2); quit ~ 0.07 + 0.04 * x * 1(g0) + 0.03 * 1(g0) - 0.0 (others 0)."""
    q = p.copy()
    x = q["entry_threat_resid"].fillna(0.0)
    pp = np.clip(0.04 + 0.03 * x * (q["gap3"] == 2), 0.001, 0.999)
    pq = np.clip(0.07 + 0.04 * x * (q["gap3"] == 0) + 0.03 * (q["gap3"] == 0), 0.001, 0.999)
    q["preempt_strategy"] = (rng.random(len(q)) < pp).astype(float)
    q["quit_any"] = np.where(q["innov_active"] == 1, (rng.random(len(q)) < pq).astype(float), np.nan)
    q["exit_strict"] = q["quit_any"]; q["exit_full"] = q["quit_any"]
    q["market_first_main"] = np.where(q["market_first_main"].notna(), (rng.random(len(q)) < 0.1).astype(float), np.nan)
    return q, {"true_b_g2_preempt": 0.03, "true_b_g0_quit": 0.04, "true_a_g0_minus_a_g2_quit": 0.03,
               "true_H6": "not exactly 0: the simulated preempt outcome depends on perceived threat, which may correlate with entry_rate_z within gap3 = 2, so the objective-rate coefficient picks up that projection (omitted perceived threat); the H6 pipeline is checked for mechanics only"}


def permute_outcomes(p, rng):
    """Permute each outcome within wave x sector among the rows where it is defined (missingness pattern kept)."""
    q = p.copy()
    for y in ("quit_any", "exit_strict", "exit_full", "preempt_strategy", "market_first_main"):
        for (w, s), idx in q.groupby(["wave", "sector"]).groups.items():
            sub = q.loc[idx, y]
            ok = sub.index[sub.notna()]
            q.loc[ok, y] = rng.permutation(sub.loc[ok].values)
    return q


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--simulate", action="store_true")
    ap.add_argument("--permute", action="store_true")
    ap.add_argument("--real", action="store_true")
    ap.add_argument("--n-boot", type=int, default=N_BOOT)
    ap.add_argument("--skip-robustness", action="store_true")
    ap.add_argument("--n-perm", type=int, default=30)
    a = ap.parse_args()
    t0 = time.time()
    p = load_panel()
    rng = np.random.default_rng(SEED)
    if a.real:
        if not os.path.exists(REGISTERED):
            sys.exit("EMBARGO: prereg/REGISTERED.json not found — register on OSF first (gate C).")
        reg = json.load(open(REGISTERED, encoding="utf-8"))
        assert reg.get("osf_url") and reg.get("registered_at"), "REGISTERED.json must contain osf_url and registered_at"
        mode = "real"; truth = None
    elif a.simulate:
        p, truth = simulate_outcomes(p, rng); mode = "simulate"
    elif a.permute:
        # null-control: K permutations, rejection rates of each primary test under the null for both inference methods
        K = a.n_perm; rates = {}
        for k in range(K):
            q = permute_outcomes(p, np.random.default_rng(SEED + 1000 + k))
            r = run_hypotheses(q, n_boot=199, tag=f"perm{k}")
            for h, t in r["tests"].items():
                rates.setdefault(h, {"cluster_t_two_sided": 0, "wild_two_sided": 0, "cluster_t_one_sided": 0, "wild_one_sided": 0})
                rates[h]["cluster_t_two_sided"] += t["p_two_sided_cluster_t"] < 0.05; rates[h]["wild_two_sided"] += t["p_two_sided_wild"] < 0.05
                rates[h]["cluster_t_one_sided"] += t["p_one_sided_cluster_t"] < 0.05; rates[h]["wild_one_sided"] += t["p_one_sided_wild"] < 0.05
            print(f"  permutation {k + 1}/{K} done", flush=True)
        null_rates = {h: {m: v / K for m, v in d.items()} for h, d in rates.items()}
        p = permute_outcomes(p, rng); mode = "permute"; truth = {"null_rejection_rates_nominal_0.05": null_rates, "n_permutations": K}
    else:
        sys.exit("choose --simulate, --permute or --real")
    out = {"mode": mode, "seed": SEED, "script_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(),
           "panel_sha256": hashlib.sha256(open(PANEL, "rb").read()).hexdigest(), "n_boot": a.n_boot, "known_truth": truth}
    out["main"] = run_hypotheses(p, n_boot=a.n_boot)
    out["placebo"] = run_placebos(p, n_boot=a.n_boot)
    if not a.skip_robustness:
        out["robustness"] = run_robustness(p, n_boot=min(299, a.n_boot))
    out["seconds"] = round(time.time() - t0, 1)
    out["built"] = time.strftime("%Y-%m-%d %H:%M %Z")
    if mode == "real":
        ex = run_exploratory(p, n_boot=min(299, a.n_boot)); ex["built"] = out["built"]
        json.dump(ex, open(os.path.join(ROOT, "results", "07_kis_exploratory.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
        target = os.path.join(ROOT, "results", "06_kis_main.json")
    else:
        target = os.path.join(ROOT, "results", f"06_kis_main_{mode}.json")
    json.dump(out, open(target, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    print(f"[{mode}] ->", target, f"({out['seconds']} s)")
    for h, t in out["main"]["tests"].items():
        print(f"  {h:13s} est {t['estimate']:+.4f} se {t['se_cluster']:.4f} p1(t) {t['p_one_sided_cluster_t']:.3f} p1(wild) {t['p_one_sided_wild']:.3f}  n {t['n']} G {t['n_clusters']}")
    print("  decisions", out["main"]["decisions"])
    print("  placebo any significant:", {k: v["any_significant_two_sided_5pct"] for k, v in out["placebo"].items()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
