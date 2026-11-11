#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnosis of the Stage A v2 placebo result (2026-11-10), kill test (iii).

The v2 summary reported placebo_accel = +0.06..+0.10 with 95 % CIs excluding 0 in 3 of 4 model/language arms. Two things
were checked before concluding anything (rule: a result this clean is a bug first):
 1. Estimator. The v2 summariser used the MARGINAL contrast mean(accelerate | placebo=1) - mean(accelerate | placebo=0)
    over all cells. The placebo was randomised within persona x (gap, threat, noise) cell, and by chance its share ranged
    from 0.375 to 0.675 across the 12 cells (stage_a_design.csv); cells differ enormously in acceleration (0 to 100 %).
    The marginal contrast therefore inherits the cell imbalance. The correct estimand is the WITHIN-CELL contrast.
    This script reports both, with a persona-cluster bootstrap and a cell-fixed-effects OLS with persona-clustered SEs.
 2. Wording. Even within cells, the one arm with a non-zero stratified effect (fable/en, +0.026, p = 0.027) is driven by the
    single non-degenerate cell g2t1n1 (placebo=1: 0.48 vs placebo=0: 0.12, n = 23 vs 17). "Moved head office to a new
    building" can plausibly be read as a signal of growth/financial slack, which is not irrelevant to a decision about
    borrowing 40 % of the R&D budget. So the v2 placebo was a weak negative control regardless of significance.
Decision recorded here: (a) the summariser is fixed to the stratified estimator; (b) the placebo is replaced by an attribute
with no plausible link to financing (founding-anniversary month: March vs September); (c) Stage A is re-run as v3 with the
payoffs of the calibrated Stage B environment, so that Stage A is the period-1 decision of the same game (v2 wording
"launching after the rival barely covers the remaining cost" was my own approximation and made quitting dominant for every
gap-0 cell, p_quit = 0.88-1.00, a ceiling of the same kind as v1).
Writes results/04_stage_a_v2_placebo_diagnosis.json. v2 logs are kept in agent_experiment/logs/v2_placebo_headoffice/.
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOGDIR = os.path.join(HERE, "logs", "v2_placebo_headoffice")
OUT = os.path.join(ROOT, "results", "04_stage_a_v2_placebo_diagnosis.json")
SEED = 20261110


def main():
    rows = []
    for fn in sorted(os.listdir(LOGDIR)):
        if fn.startswith("stage_a_") and fn.endswith(".jsonl") and "_mock" not in fn:
            for line in open(os.path.join(LOGDIR, fn), encoding="utf-8"):
                rows.append(json.loads(line))
    df = pd.DataFrame(rows)
    df = df[df.parse_status == "ok"].copy()
    df["is_A"] = (df.decision == "A").astype(float); df["is_Q"] = (df.decision == "Q").astype(float)
    df["cell"] = df.gap.astype(str) + df.threat.astype(str) + df.noise.astype(str)
    design = pd.read_csv(os.path.join(HERE, "stage_a_design.csv"))
    share = design[design.lang == "ko"].groupby(["gap", "threat", "noise"])["placebo"].mean()
    res = {"placebo_share_by_cell_design": {f"g{g}t{t}n{n}": float(v) for (g, t, n), v in share.items()},
           "placebo_share_range": [float(share.min()), float(share.max())], "arms": {}}
    rng = np.random.default_rng(SEED)
    for (m, l), g in df.groupby(["model", "lang"]):
        pids = g.persona_id.unique()
        def strat(frame, col):
            cell = frame.groupby(["cell", "placebo"])[col].mean().unstack("placebo")
            return float((cell[1] - cell[0]).mean())
        arm = {}
        for col in ("is_A", "is_Q"):
            marg = float(g[g.placebo == 1][col].mean() - g[g.placebo == 0][col].mean())
            boots = []
            for _ in range(1000):
                samp = g[g.persona_id.isin(rng.choice(pids, len(pids), replace=True))]
                boots.append(strat(samp, col))
            fit = smf.ols(f"{col} ~ C(cell) + placebo", data=g).fit(cov_type="cluster", cov_kwds={"groups": g.persona_id})
            se = float(fit.bse["placebo"]); degenerate = (not np.isfinite(se)) or se < 1e-8  # no within-cell variance -> p is meaningless
            arm[col] = {"marginal_contrast": marg, "stratified_contrast": strat(g, col),
                        "stratified_boot_ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
                        "ols_cell_fe_coef": float(fit.params["placebo"]), "ols_cluster_se": None if degenerate else se,
                        "ols_p": None if degenerate else float(fit.pvalues["placebo"]), "degenerate_no_variance": bool(degenerate)}
        cellwise = g.groupby(["cell", "placebo"]).is_A.mean().unstack("placebo")
        arm["within_cell_accel_diff"] = {c: float(v) for c, v in (cellwise[1] - cellwise[0]).items()}
        res["arms"][f"{m}/{l}"] = arm
    g = df.copy(); g["arm"] = g.model + "/" + g.lang
    fit = smf.ols("is_A ~ C(cell):C(arm) + placebo", data=g).fit(cov_type="cluster", cov_kwds={"groups": g.persona_id})
    res["pooled_accel"] = {"ols_coef": float(fit.params["placebo"]), "cluster_se": float(fit.bse["placebo"]), "p": float(fit.pvalues["placebo"])}
    s = df[(df.model == "fable") & (df.lang == "en") & (df.cell == "211")].groupby("placebo").is_A.agg(["mean", "size"])
    res["fable_en_g2t1n1_by_placebo"] = {str(k): {"mean": float(v["mean"]), "n": int(v["size"])} for k, v in s.iterrows()}
    res["gap0_quit_ceiling"] = {f"{m}/{l}": float(gg[gg.gap == 0].is_Q.mean()) for (m, l), gg in df.groupby(["model", "lang"])}
    res["decision"] = __doc__.strip()
    res["built"] = time.strftime("%Y-%m-%d %H:%M %Z")
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for k, v in res["arms"].items():
        print(k, {c: (round(v[c]["marginal_contrast"], 3), round(v[c]["stratified_contrast"], 3), [round(x, 3) for x in v[c]["stratified_boot_ci95"]], v[c]["ols_p"] and round(v[c]["ols_p"], 3)) for c in ("is_A", "is_Q")})
    print("pooled", res["pooled_accel"]); print("gap0 quit", res["gap0_quit_ceiling"]); print("->", OUT)


if __name__ == "__main__":
    sys.exit(main())
