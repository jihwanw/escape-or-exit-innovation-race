#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Exploratory robustness (NOT pre-registered; added 2026-11-11 after the Task 12 cross-review): alternative constructions of the
perceived-threat treatment.

Why. The registered loader (code/load_kis_escape_exit.py, hash in the OSF registration) builds `entry_threat_resid` as the
within-wave OLS residual of ME4 ('entry of new competitors threatens market position' [item_map ME4; questionnaire 문1-2 ④])
on the OTHER SEVEN market-environment items entered separately, and does not re-standardise it (pooled SD 1.005; by-wave SDs
0.89-1.14). The registration TEXT (prereg/PREREGISTRATION.md, 'Transformations') describes the same variable as the residual on
`me_mean8` (the eight-item mean) standardised to SD 1, and the placebo residuals in analysis_prereg.load_panel follow that text
recipe. The confirmatory results are those of the registered code; this script re-estimates H1-H5 with the treatment built by
(a) the text recipe ('mean8': residual on the eight-item mean, standardised within wave) and (b) a leave-one-out index
('mean7': residual on the mean of the other seven items, standardised within wave), with the same controls except that the
response-propensity control is the index used for residualisation. Same estimator and inference as analysis_prereg.py
(LPM, industry and wave FE, wild cluster bootstrap-t, 999 draws). Also records the SD of the registered residual by wave.
Writes results/07d_robustness_threat_residual.json.
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import statsmodels.api as sm

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analysis_prereg as A  # noqa: E402

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "07d_robustness_threat_residual.json")
ME = [f"ME{k}" for k in range(1, 9)]


def resid_std_within_wave(p, target, index_col):
    out = pd.Series(np.nan, index=p.index)
    ok = p[ME].notna().all(axis=1)
    for w, d in p[ok].groupby("wave"):
        X = sm.add_constant(d[[index_col]].astype(float))
        r = sm.OLS(d[target].astype(float), X).fit().resid
        out.loc[r.index] = (r - r.mean()) / r.std(ddof=0)
    return out


def main():
    t0 = time.time()
    p = A.load_panel()
    ok = p[ME].notna().all(axis=1)
    p["me_mean7"] = p[[c for c in ME if c != "ME4"]].mean(axis=1).where(ok)
    p["entry_threat_resid_mean8"] = resid_std_within_wave(p, "ME4", "me_mean8")
    p["entry_threat_resid_mean7"] = resid_std_within_wave(p, "ME4", "me_mean7")
    res = {"built": time.strftime("%Y-%m-%d %H:%M %Z"), "label": "exploratory (not pre-registered)",
           "registered_resid_sd": {"pooled": float(p["entry_threat_resid"].std(ddof=0)),
                                   "by_wave": {w: float(s) for w, s in p.groupby("wave")["entry_threat_resid"].std(ddof=0).items()}},
           "registered_resid_construction": "within-wave OLS residual of ME4 on ME1-ME3, ME5-ME8 entered separately; not re-standardised (code/load_kis_escape_exit.py)",
           "corr_registered_vs_mean8": float(p[["entry_threat_resid", "entry_threat_resid_mean8"]].corr().iloc[0, 1]),
           "corr_registered_vs_mean7": float(p[["entry_threat_resid", "entry_threat_resid_mean7"]].corr().iloc[0, 1]),
           "variants": {}}
    base_controls, base_controls_quit = list(A.CONTROLS), list(A.CONTROLS_QUIT)
    for name, x, idx in (("mean8", "entry_threat_resid_mean8", "me_mean8"), ("mean7", "entry_threat_resid_mean7", "me_mean7")):
        A.CONTROLS[:] = [idx if c == "me_mean8" else c for c in base_controls]
        A.CONTROLS_QUIT[:] = [idx if c == "me_mean8" else c for c in base_controls_quit]
        r = A.run_hypotheses(p, x_perc=x, n_boot=A.N_BOOT, tag=f"threat_resid_{name}")
        r["controls"] = list(A.CONTROLS); r["treatment"] = x
        for k in ("coefficients",):
            r.pop(k, None)
        res["variants"][name] = r
    A.CONTROLS[:] = base_controls; A.CONTROLS_QUIT[:] = base_controls_quit
    res["seconds"] = round(time.time() - t0, 1)
    json.dump(res, open(OUT, "w"), indent=1, default=float)
    for name, r in res["variants"].items():
        print(name, {h: (round(r["tests"][h]["estimate"], 4), round(r["tests"][h]["p_one_sided_wild"], 3)) for h in ("H1", "H2", "H3", "H4", "H5")})
    print("registered resid SD:", res["registered_resid_sd"], "corr mean8/mean7:", round(res["corr_registered_vs_mean8"], 3), round(res["corr_registered_vs_mean7"], 3))


if __name__ == "__main__":
    main()
