#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""JSON -> figures (greyscale, serif/STIX, uniform markers, value labels). Writes paper/figures/fig_agents.pdf|png and
paper/figures/fig_kis_coefficients.pdf|png; copies the model comparative-statics figure from results/. Reads only results JSON."""
import json
import os
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIG = os.path.join(ROOT, "paper", "figures")
os.makedirs(FIG, exist_ok=True)
J = lambda *p: json.load(open(os.path.join(ROOT, *p), encoding="utf-8"))  # noqa: E731
plt.rcParams.update({"font.family": "serif", "font.serif": ["STIXGeneral"], "mathtext.fontset": "stix", "font.size": 9, "axes.labelsize": 9, "legend.fontsize": 7.5, "xtick.labelsize": 8, "ytick.labelsize": 8})
ARMS = ["fable/en", "fable/ko", "gpt56/en", "gpt56/ko"]
STYLE = {"fable/en": dict(marker="o", ls="-", color="0.15"), "fable/ko": dict(marker="o", ls="--", color="0.15"), "gpt56/en": dict(marker="s", ls="-", color="0.55"), "gpt56/ko": dict(marker="s", ls="--", color="0.55")}
LABEL = {"fable/en": "Claude fable-5, EN", "fable/ko": "Claude fable-5, KO", "gpt56/en": "GPT-5.6, EN", "gpt56/ko": "GPT-5.6, KO"}


def cell(S, arm, g, t, key):
    vals = [c[key] for c in S["by_model_lang"][arm]["cells"] if c["gap"] == g and c["threat"] == t]
    return sum(vals) / len(vals)  # pooled over the two noise cells (equal n)


def fig_agents():
    A = J("results", "04_agent_stage_a.json"); B = J("results", "05_agent_stage_b.json")
    p1 = A["model_period1_action_probs"]; mp = B["model_predictions"]
    panels = [("(a) Stage A: frontier firm accelerates (period-1 decision)", A, 2, "p_accel", [p1["g2t0"]["P_accel"], p1["g2t1"]["P_accel"]], "Model, period-1 policy"),
              ("(b) Stage A: laggard stops (period-1 decision)", A, 0, "p_quit", [p1["g0t0"]["P_quit"], p1["g0t1"]["P_quit"]], "Model, period-1 policy"),
              ("(c) Stage B: frontier firm accelerates at least once (episode)", B, 2, "P_accel", [(mp["g2t0n0"]["unconditional"]["P_accel"] + mp["g2t0n1"]["unconditional"]["P_accel"]) / 2, (mp["g2t1n0"]["unconditional"]["P_accel"] + mp["g2t1n1"]["unconditional"]["P_accel"]) / 2], "Model, unconditional"),
              ("(d) Stage B: laggard stops (episode)", B, 0, "P_quit", [(mp["g0t0n0"]["unconditional"]["P_quit"] + mp["g0t0n1"]["unconditional"]["P_quit"]) / 2, (mp["g0t1n0"]["unconditional"]["P_quit"] + mp["g0t1n1"]["unconditional"]["P_quit"]) / 2], "Model, unconditional")]
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.8))

    def spread(items, gap=0.055):
        """items: list of (value, label, color, italic); returns label y positions with a minimum vertical gap, keeping order."""
        items = sorted(items, key=lambda t: t[0]); ys = [t[0] for t in items]
        for i in range(1, len(ys)):
            if ys[i] - ys[i - 1] < gap:
                ys[i] = ys[i - 1] + gap
        return list(zip(items, ys))

    for ax, (title, S, g, key, model, mlab) in zip(axes.flat, panels):
        labels = {0: [], 1: []}
        for arm in ARMS:
            y = [cell(S, arm, g, 0, key), cell(S, arm, g, 1, key)]
            ax.plot([0, 1], y, markersize=5, lw=1.0, label=LABEL[arm], **STYLE[arm])
            for x, v in zip([0, 1], y):
                labels[x].append((v, f"{v:.2f}", STYLE[arm]["color"], False))
        ax.plot([0, 1], model, ls=":", color="0.4", lw=1.2, marker="D", markersize=4, markerfacecolor="white", label=mlab)
        for x, v in zip([0, 1], model):
            labels[x].append((v, f"{v:.2f}", "0.4", True))
        for x in (0, 1):
            for (v, txt, col, it), yy in spread(labels[x]):
                ax.annotate(txt, (x, yy), textcoords="offset points", xytext=(7 if x == 1 else -7, 0), ha="left" if x == 1 else "right", va="center", fontsize=6.5, color=col, style="italic" if it else "normal")
        ax.set_xticks([0, 1]); ax.set_xticklabels(["no entry threat", "entry threat (35%/period)"]); ax.set_xlim(-0.35, 1.35); ax.set_ylim(-0.03, 1.08)
        ax.set_ylabel("share of decisions / episodes"); ax.set_title(title, fontsize=8.5, loc="left")
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    axes[0, 0].legend(frameon=False, loc="upper left", ncol=1)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_agents.pdf")); fig.savefig(os.path.join(FIG, "fig_agents.png"), dpi=200); plt.close(fig)


def fig_kis():
    K = J("results", "06_kis_main.json"); M = K["main"]
    order = [("H1", "H1 Escape: threat × frontier → pre-emption"), ("H4", "H4 Asymmetry: pre-emption, frontier − laggard"), ("H2", "H2 Exit: threat × laggard → quit"), ("H3", "H3 Asymmetry: quit, laggard − frontier"),
             ("H5", "H5 Baseline: laggard − frontier quit"), ("H2_objective", "H2 (objective): entry rate × laggard → quit"), ("H6", "H6 Entry rate × frontier → pre-emption")]
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    ys = list(range(len(order)))[::-1]
    for y, (h, lab) in zip(ys, order):
        t = M["tests"][h]; est = 100 * t["estimate"]; lo, hi = 100 * t["ci95_wild"][0], 100 * t["ci95_wild"][1]
        ax.plot([lo, hi], [y, y], color="0.2", lw=1.2)
        if h == "H6":
            l90, h90 = 100 * t["ci90_wild"][0], 100 * t["ci90_wild"][1]; ax.plot([l90, h90], [y, y], color="0.2", lw=3.0, solid_capstyle="butt")
        ax.plot(est, y, marker="o", color="0.1", markersize=5, markerfacecolor="white" if M["decisions"].get(h, "") != "supported" else "0.1")
        dec = M["decisions"].get(h, "reported with H2").replace("_", " ")
        ptxt = f"p = {t['p_one_sided_wild']:.3f}" if h not in ("H6",) else "TOST"
        wide = hi > 13.5
        ax.annotate(f"{est:+.2f} pp [{lo:+.2f}, {hi:+.2f}]; {ptxt}; {dec}", (min(hi, 13.5) if not wide else est, y), textcoords="offset points", xytext=(6, 0) if not wide else (-40, 9),
                    va="center" if not wide else "bottom", ha="left", fontsize=6.8, color="0.2")
    ax.axvline(0, color="0.5", ls="--", lw=0.8)
    delta = 100 * M["H6_delta"]; ax.axvspan(-delta, delta, color="0.92", zorder=0)
    ax.set_yticks(ys); ax.set_yticklabels([lab for _, lab in order], fontsize=7.5)
    ax.set_xlabel("change in outcome probability per unit of the treatment (percentage points; threat residual pooled SD ≈ 1, entry rate standardised)\n95% wild cluster bootstrap-t CI; H6: 90% CI in bold, equivalence band ±1 pp shaded", fontsize=8)
    ax.set_xlim(-12, 27)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_kis_coefficients.pdf")); fig.savefig(os.path.join(FIG, "fig_kis_coefficients.png"), dpi=200); plt.close(fig)


if __name__ == "__main__":
    fig_agents(); fig_kis()
    for ext in ("pdf", "png"):
        src = os.path.join(ROOT, "results", f"fig_model_comparative_statics.{ext}")
        if os.path.exists(src):
            shutil.copy(src, os.path.join(FIG, f"fig_model_comparative_statics.{ext}"))
    print("figures ->", FIG, os.listdir(FIG))
