#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Greyscale comparative-statics figure from results/03_grid_outcomes.parquet (no numbers typed).
Panel (a): P_quit for laggard vs leader as a function of theta — grid median with interquartile band, main rule, sigma=0.
Panel (b): P_accel for leader vs laggard. Panel (c): P_first_L. Style: manuscript-figure-style memory (greyscale, STIX serif,
uniform markers, reference line, value labels at the ends)."""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
plt.rcParams.update({"font.family": "serif", "font.serif": ["STIXGeneral"], "mathtext.fontset": "stix", "font.size": 9})

df = pd.read_parquet(os.path.join(ROOT, "results", "03_grid_outcomes.parquet"))
d = df[(df.sel == "welfare") & (df.sigma == 0.0) & (df.sigma_def == "tremble") & (df.d >= 1)]
g = d.groupby("theta")

fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.4))
panels = [("P_quit_F", "P_quit_L", "Pr(abandon)", "laggard", "leader"),
          ("P_accel_L", "P_accel_F", "Pr(accelerate at least once)", "leader", "laggard"),
          ("P_first_L", "P_first_F", "Pr(first to market)", "leader", "laggard")]
for ax, (c1, c2, ylab, l1, l2) in zip(axes, panels):
    for col, lab, ls, mk in ((c1, l1, "-", "o"), (c2, l2, "--", "s")):
        med = g[col].median(); q1 = g[col].quantile(.25); q3 = g[col].quantile(.75)
        ax.fill_between(med.index, q1.values, q3.values, color="0.85" if ls == "-" else "0.93", lw=0)
        ax.plot(med.index, med.values, ls, color="0.1" if ls == "-" else "0.45", marker=mk, ms=3.5, lw=1.1, label=lab)
        ax.annotate(f"{med.values[-1]:.2f}", (med.index[-1], med.values[-1]), textcoords="offset points", xytext=(4, 0), fontsize=7, va="center", color="0.1" if ls == "-" else "0.45")
    ax.set_xlabel(r"entry threat $\theta$"); ax.set_ylabel(ylab); ax.set_ylim(-0.02, 1.02); ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=7, loc="best")
fig.suptitle("Grid medians (shaded: interquartile range across grid points with d ≥ 1), main selection rule, σ = 0", fontsize=8, y=1.02)
fig.tight_layout()
out = os.path.join(ROOT, "results", "fig_model_comparative_statics.pdf")
fig.savefig(out, bbox_inches="tight"); fig.savefig(out.replace(".pdf", ".png"), dpi=150, bbox_inches="tight")
print("wrote", out)
