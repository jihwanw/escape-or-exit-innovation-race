#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""JSON -> standalone LaTeX tables (booktabs) -> PDF in paper/tables_tex/. Reads ONLY results/*.json, prereg/*.json and
item_maps/*.json. ROUND_HALF_UP. Every cell traces to a JSON key. Compiled with xelatex (Korean wording in the variable table)."""
import json
import os
import subprocess
import time
from decimal import ROUND_HALF_UP, Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TDIR = os.path.join(ROOT, "paper", "tables_tex")
os.makedirs(TDIR, exist_ok=True)
J = lambda *p: json.load(open(os.path.join(ROOT, *p), encoding="utf-8"))  # noqa: E731
import sys  # noqa: E402
sys.path.insert(0, os.path.join(ROOT, "agent_experiment"))
from race_env import THETA as ENV_THETA, OBS_NOISE as ENV_OBS_NOISE  # noqa: E402  (environment constants, never retyped)
WAVES = ["2022M", "2023S", "2024M", "2025S"]
ARMS = ["fable/en", "fable/ko", "gpt56/en", "gpt56/ko"]
ARML = {"fable/en": "Claude (fable-5), EN", "fable/ko": "Claude (fable-5), KO", "gpt56/en": "GPT-5.6, EN", "gpt56/ko": "GPT-5.6, KO"}


def r(x, nd=3, sign=False):
    if x is None:
        return "--"
    s = str(Decimal(str(x)).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP))
    if sign and not s.startswith("-"):
        s = "+" + s
    return s


def ptx(p):
    if p is None:
        return "--"
    return "$<$0.001" if p < 0.001 else r(p, 3)


def esc(s):
    return str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("~", "\\textasciitilde{}")


PRE = r"""\documentclass[varwidth=\maxdimen,border=4pt]{standalone}
\usepackage{booktabs,array,fontspec}
\usepackage{xeCJK}
\setmainfont{Times New Roman}
\setCJKmainfont{Apple SD Gothic Neo}
\xeCJKsetup{CJKspace=true}
\renewcommand{\arraystretch}{1.12}
\begin{document}\small
"""
POST = "\n\\end{document}\n"


def write(name, body, size="\\small"):
    tex = PRE.replace("\\small", size) + body + POST
    path = os.path.join(TDIR, f"T_{name}.tex")
    open(path, "w", encoding="utf-8").write(tex)
    res = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", f"T_{name}.tex"], cwd=TDIR, capture_output=True, text=True)
    ok = res.returncode == 0 and os.path.exists(os.path.join(TDIR, f"T_{name}.pdf"))
    for ext in (".aux", ".log"):
        p = os.path.join(TDIR, f"T_{name}{ext}")
        if ok and os.path.exists(p):
            os.remove(p)
    print(("OK   " if ok else "FAIL ") + f"T_{name}" + ("" if ok else "\n" + res.stdout[-1500:]))
    return ok


def tabular(cols, header, rows, notes=None):
    """Tabular saved in a box so that the notes paragraph takes exactly the tabular's width (standalone has no \\linewidth)."""
    out = ["\\newsavebox{\\tb}\\sbox{\\tb}{%", f"\\begin{{tabular}}{{{cols}}}", "\\toprule", " & ".join(header) + " \\\\", "\\midrule"]
    for row in rows:
        if row == "MIDRULE":
            out.append("\\midrule"); continue
        out.append(" & ".join(str(c) for c in row) + " \\\\")
    out.append("\\bottomrule")
    out.append("\\end{tabular}}")
    out.append("\\usebox{\\tb}")
    if notes:
        out.append(f"\\par\\vspace{{3pt}}\\parbox{{\\wd\\tb}}{{\\footnotesize {notes}}}")
    return "\n".join(out)


# ------------------------------------------------------------------------------------------------------------- tables
def t_variables():
    rows = []
    used = {"IA3": "Outcome: abandoned/suspended innovation activity (quit)", "PROT8": "Outcome: lead-time protection (pre-emption)", "ME4": "Treatment: perceived entry threat",
            "RDSTAFF": "Gap proxy: dedicated R&D staff share", "ME1": "Response-propensity index (me_mean8)", "ME2": "Index; control (tech. uncertainty)", "ME3": "Index", "ME5": "Index; exploratory sigma item",
            "ME6": "Index; placebo", "ME7": "Index", "ME8": "Index; placebo", "IA1": "Sample filter; portfolio breadth", "IA2": "Portfolio breadth", "IA4": "Portfolio breadth", "IA5": "Portfolio breadth", "IA6": "Portfolio breadth",
            "EMP": "Control: regular employees (log)", "FORM": "Control: group affiliation", "LISTED": "Control: listing", "MF1": "Exploratory outcome: new-to-market product", "PI1": "Filter for MF1", "PI2": "Filter for MF1"}
    m = {w: J("item_maps", f"item_map_{w}.json") for w in WAVES}
    order = ["IA3", "PROT8", "ME4", "RDSTAFF", "ME1", "ME2", "ME3", "ME5", "ME6", "ME7", "ME8", "IA1", "IA2", "IA4", "IA5", "IA6", "EMP", "FORM", "LISTED", "MF1", "PI1", "PI2"]
    for cid in order:
        ents = {w: next((e for e in m[w]["items"] if e.get("construct_id") == cid), None) for w in WAVES}
        e24 = ents["2024M"] or next(v for v in ents.values() if v)
        varnames = "/".join(sorted({ents[w]["variable"] for w in WAVES if ents[w]}))
        text = e24.get("item_text_questionnaire") or e24.get("item_text_ko")
        rows.append([cid, esc(varnames), esc(text), esc(e24.get("short_label_en", "")), esc(e24.get("questionnaire_block", "")), esc(used[cid])])
    body = tabular("l l p{5.2cm} p{4.2cm} l p{3.6cm}", ["Construct", "Variable (by wave)", "Questionnaire wording (verbatim)", "English label", "Block", "Role"], rows,
                   notes="Wording from the printed questionnaires of the four waves (identical across waves except reference years); variable names as in the STEPI provision files (2022/2023 문-style, 2024/2025 Q-style). Full per-wave item maps with printed codes and observed values: item\\_maps/item\\_map\\_<wave>.json.")
    return write("variables", body, "\\footnotesize")


def t_base_rates():
    marg = J("results", "02_marginals.json"); bw = marg["A_outcome_base_rates"]["by_wave"]; pooled = marg["A_outcome_base_rates"]["pooled"]
    rows = []
    for w in WAVES:
        d = bw[w]
        rows.append([w, f"{d['preempt_strategy']['n']:,}", f"{d['quit_any']['n']:,}", f"{d['quit_any']['events']:,}", r(100 * d["quit_any"]["rate_unweighted"], 1), f"{d['preempt_strategy']['events']:,}", r(100 * d["preempt_strategy"]["rate_unweighted"], 1)])
    rows.append("MIDRULE")
    rows.append(["Pooled", f"{pooled['preempt_strategy']['n']:,}", f"{pooled['quit_any']['n']:,}", f"{pooled['quit_any']['events']:,}", r(100 * pooled["quit_any"]["rate_unweighted"], 1), f"{pooled['preempt_strategy']['events']:,}", r(100 * pooled["preempt_strategy"]["rate_unweighted"], 1)])
    body = tabular("l r r r r r r", ["Wave", "Firms", "Innovation-active", "Quit events", "Quit rate (\\%)", "Pre-emption events", "Pre-emption rate (\\%)"], rows,
                   notes="Quit = abandoned or suspended innovation activity (questionnaire block 11, item 3), defined for innovation-active firms; pre-emption = lead-time protection (block 2, item 8), all firms. Unweighted. Source: results/02\\_marginals.json.")  # circled digits dropped 2026-11-11: no glyph in the table fonts
    return write("base_rates", body)


def t_model_predictions():
    mp = J("results", "03_model_predictions.json")["decisions"]
    label = {"P1": "Threat raises leader acceleration (leader one stage from completion)", "P1_all": "Threat raises leader acceleration (all leaders)", "P1_far": "Threat raises leader acceleration (leader $\\geq$ 2 stages away)",
             "P2": "Threat raises laggard quitting", "P2_far": "Threat raises laggard quitting (laggard $\\geq$ 2 away)", "P3": "Quit effect of threat: laggard $>$ leader", "P3_near": "Quit effect: laggard $>$ leader (near)",
             "P4": "Acceleration effect: leader $>$ laggard", "P4_near": "Acceleration effect: leader $>$ laggard (near)", "P7": "Laggard quits more than leader", "P8": "Threat raises leader's first-launch probability", "P8_near": "Threat raises first-launch (near)"}
    rows = []
    for pid, d in mp.items():
        if "share_informative_e2e" not in d:
            continue
        rows.append([esc(pid), label.get(pid, pid), f"{d['n_points']:,}", r(100 * d["share_informative_e2e"], 0), r(100 * d["e2e_holds_among_informative"], 0), r(100 * d["strict_holds_among_informative"], 0), "yes" if d["candidate"] else "no"])
    body = tabular("l p{7.2cm} r r r r l", ["Prediction", "Statement (threat version, $\\theta$: 0 $\\to$ 0.7)", "Grid points", "Informative (\\%)", "Sign holds (\\%)", "Strict monotone (\\%)", "Candidate"], rows,
                   notes="Grid: 1,152 parameter points $\\times$ 6 $\\theta$ values $\\times$ 3 equilibrium-selection rules. 'Informative' = the outcome moves with $\\theta$; 'holds' = end-point sign agrees among informative points; candidate = holds $\\geq$ 90\\% and strict monotone $\\geq$ 50\\% under all three selection rules. Source: results/03\\_model\\_predictions.json.")
    return write("model_predictions", body, "\\footnotesize")


def t_environment():
    B = J("results", "05_agent_stage_b.json"); mp = B["model_predictions"]
    cal = J("results", "05_stage_b_env_calibration.json"); env = cal["fixed"] | {"cA": cal["chosen_cA"]}  # model unit = 100억원 = 10 billion won
    bn = lambda x: r(x * 10, 1).rstrip("0").rstrip(".")
    rows = []
    for g, gl in ((0, "one stage behind (laggard)"), (1, "level"), (2, "one stage ahead (leader)")):
        for t in (0, 1):
            for n in (0, 1):
                c = mp[f"g{g}t{t}n{n}"]; u = c["unconditional"]; ne = c["no_entry_conditional"]
                rows.append([gl if (t == 0 and n == 0) else "", "yes" if t else "no", "yes" if n else "no", r(u["P_quit"], 2), r(u["P_accel"], 2), r(u["P_first"], 2), r(ne["P_quit"], 2), r(ne["P_accel"], 2), r(ne["P_first"], 2)])
        rows.append("MIDRULE")
    rows.pop()
    body = tabular("l c c r r r r r r", ["Agent position", "Threat", "Noise", "Quit", "Accel.", "First", "Quit", "Accel.", "First"], rows,
                   notes=(f"Model outcomes for the agent's seat in the calibrated Stage B environment ({env['K']} stages, {env['T']} periods; continue {bn(env['cC'])} billion won/{r(100 * env['pC'], 0)}\\%, "
                          f"accelerate {bn(env['cA'])} billion won/{r(100 * env['pA'], 0)}\\%; prizes {bn(env['V'])}/{bn(env['W'])}/{bn((env['V'] + env['W']) / 2)} billion won; "
                          f"entry {r(100 * ENV_THETA[1], 0)}\\% per period multiplying unfinished prizes by {env['lam']}; {r(100 * ENV_OBS_NOISE[1], 0)}\\% one-stage observation error). "
                          "Columns 4--6 unconditional; 7--9 conditional on no entry within the horizon. Source: results/05\\_agent\\_stage\\_b.json (model\\_predictions), results/05\\_stage\\_b\\_env\\_calibration.json."))
    hdr = "\\multicolumn{3}{c}{} & \\multicolumn{3}{c}{Unconditional} & \\multicolumn{3}{c}{No entry within horizon} \\\\ \\cmidrule(lr){4-6}\\cmidrule(lr){7-9}\n"
    body = body.replace("\\toprule\n", "\\toprule\n" + hdr, 1)
    return write("environment", body)


def t_stage_cells(stage):
    S = J("results", "04_agent_stage_a.json") if stage == "A" else J("results", "05_agent_stage_b.json")
    rows = []
    for g, gl in ((0, "behind"), (1, "level"), (2, "ahead")):
        for t in (0, 1):
            for n in (0, 1):
                row = [gl if (t == 0 and n == 0) else "", "yes" if t else "no", "yes" if n else "no"]
                for arm in ARMS:
                    c = next(x for x in S["by_model_lang"][arm]["cells"] if x["gap"] == g and x["threat"] == t and x["noise"] == n)
                    if stage == "A":
                        row += [r(c["p_accel"], 2), r(c["p_quit"], 2)]
                    else:
                        row += [r(c["P_accel"], 2), r(c["P_quit"], 2)]
                rows.append(row)
        rows.append("MIDRULE")
    rows.pop()
    model_note = ""
    if stage == "A":  # the model's own period-1 equilibrium policy for the agent's seat (results/04_agent_stage_a.json, model_period1_action_probs)
        rows.append("MIDRULE")
        mp = S["model_period1_action_probs"]
        for g, gl in ((0, "behind"), (1, "level"), (2, "ahead")):
            for t in (0, 1):
                c = mp[f"g{g}t{t}"]
                rows.append([f"Model period-1 policy, {gl}" if t == 0 else "", "yes" if t else "no", "--"] + ["\\multicolumn{2}{c}{" + f"{r(c['P_accel'], 2)} / {r(c['P_quit'], 2)}" + "}"] + ["\\multicolumn{2}{c}{}"] * 3)
        model_note = "The last six rows give the model's period-1 equilibrium action probabilities (accelerate / stop) for the agent's seat at the true state; the observation-noise cell is not distinguished because the model is solved at the true state. "
    hdr = "\\multicolumn{3}{c}{} & " + " & ".join(f"\\multicolumn{{2}}{{c}}{{{ARML[a]}}}" for a in ARMS) + " \\\\ " + "".join(f"\\cmidrule(lr){{{4 + 2 * i}-{5 + 2 * i}}}" for i in range(4)) + "\n"
    body = tabular("l c c " + "r r " * 4, ["Position", "Threat", "Noise"] + ["Accel.", "Quit"] * 4, rows,
                   notes=("Stage A: share of the one-shot period-1 decision (n = 40 personas per cell and arm). " if stage == "A" else "Stage B: share of episodes in which the agent accelerated at least once / stopped (n = 24 per cell and arm, completed episodes). ") + model_note +
                         f"Source: results/0{'4' if stage == 'A' else '5'}\\_agent\\_stage\\_{stage.lower()}.json.")
    body = body.replace("\\toprule\n", "\\toprule\n" + hdr, 1)
    return write(f"stage{stage}_cells", body, "\\footnotesize")


def t_agent_contrasts():
    pred = J("prereg", "agent_predictions_v1.json")
    rows = []
    for h, p in pred["predictions"].items():
        for stage, lab in (("stage_a", "A"), ("stage_b", "B")):
            s = p[stage]
            if not s:
                continue
            for arm in ARMS:
                e = s["estimates"][arm]
                rows.append([h if (stage == "stage_a" and arm == ARMS[0]) or (stage == "stage_b" and arm == ARMS[0] and not p["stage_a"]) else "", lab if arm == ARMS[0] else "", esc(s["contrast"]) if arm == ARMS[0] else "", ARML[arm],
                             r(e["estimate"], 3, True) if e["estimate"] is not None else "--", f"[{r(e['ci95'][0], 3, True)}, {r(e['ci95'][1], 3, True)}]" if e["ci95"] else "--", s["arm_calls"][arm] or "--"])
        rows.append("MIDRULE")
    rows.pop()
    body = tabular("l l l l r l c", ["H", "Stage", "Contrast", "Arm", "Estimate", "95\\% CI", "Sign"], rows,
                   notes="Contrasts are differences of cell shares; CI = percentile bootstrap over personas (500 draws). Sign call: + if the CI lies above 0, $-$ below 0, 0 otherwise. Frozen in prereg/agent\\_predictions\\_v1.json before the survey test.")
    return write("agent_contrasts", body, "\\footnotesize")


def t_kis_main():
    TRS = J("results", "07d_robustness_threat_residual.json") if os.path.exists(os.path.join(ROOT, "results", "07d_robustness_threat_residual.json")) else None
    sd_txt = (r(TRS["registered_resid_sd"]["pooled"], 3) if TRS else "[RESULTS-GAP: 07d registered_resid_sd]")
    K = J("results", "06_kis_main.json"); M = K["main"]
    lab = {"H1": "H1 Escape: threat $\\times$ frontier $\\to$ pre-emption", "H2": "H2 Exit: threat $\\times$ laggard $\\to$ quit", "H2_objective": "H2 (objective): entry rate $\\times$ laggard $\\to$ quit",
           "H3": "H3 Quit asymmetry: laggard $-$ frontier", "H4": "H4 Pre-emption asymmetry: frontier $-$ laggard", "H5": "H5 Baseline: laggard $-$ frontier quit", "H6": "H6 Entry rate $\\times$ frontier $\\to$ pre-emption (TOST)"}
    rows = []
    for h in ("H1", "H2", "H2_objective", "H3", "H4", "H5", "H6"):
        t = M["tests"][h]
        ci = t["ci90_wild"] if h == "H6" else t["ci95_wild"]
        rows.append([lab[h], r(t["estimate"], 4, True), r(t["se_cluster"], 4), f"[{r(ci[0], 4, True)}, {r(ci[1], 4, True)}]" + (" (90\\%)" if h == "H6" else ""), ptx(t["p_one_sided_wild"]) if h != "H6" else ptx(t["p_two_sided_wild"]) + " (2-s.)",
                     ptx(M["holm_wild"][h]) if h in M["holm_wild"] else "--", M["decisions"].get(h, "--").replace("_", " "), f"{t['n']:,} / {t['n_clusters']}"])
    body = tabular("p{6.3cm} r r l r r l l", ["Hypothesis (pre-registered)", "Estimate", "Cluster SE", "Wild CI", "$p$ (one-sided, wild)", "Holm", "Decision", "N / clusters"], rows,
                   notes="Linear probability models with industry (2-digit) and wave fixed effects and controls; estimate = change in probability per unit of the treatment within the gap group (perceived threat: within-wave residual of the entry-threat item on the other seven market-environment items, pooled SD " + sd_txt + "; entry rate: standardised; H5: difference of group intercepts at average threat). Inference: wild cluster bootstrap-t, Rademacher, 999 draws, clusters = industry $\\times$ wave; Holm across H1--H5. Decision rule as pre-registered (OSF tj9uv). Source: results/06\\_kis\\_main.json.")
    return write("kis_main", body, "\\footnotesize")


def t_kis_coefficients():
    K = J("results", "06_kis_main.json"); co = K["main"]["coefficients"]
    names = [("g0", "Laggard group (gap3 = 0)"), ("g2", "Frontier group (gap3 = 2)"), ("x_g0", "Treatment $\\times$ laggard"), ("x_g1", "Treatment $\\times$ middle"), ("x_g2", "Treatment $\\times$ frontier"),
             ("log_employees", "log employees"), ("log1p_firm_age", "log(1 + firm age)"), ("group_dom", "Domestic-group affiliate"), ("group_for", "Foreign-group affiliate"), ("listed", "Listed"), ("me_mean8", "Response-propensity index"), ("portfolio_breadth", "Portfolio breadth")]
    models = [("preempt_perceived", "Pre-emption, perceived threat"), ("quit_perceived", "Quit, perceived threat"), ("preempt_objective", "Pre-emption, entry rate"), ("quit_objective", "Quit, entry rate")]
    rows = []
    for k, lab in names:
        row = [lab]
        for mkey, _ in models:
            c = co[mkey]["coef"].get(k); s = co[mkey]["se"].get(k)
            row.append(f"{r(c, 4, True)} ({r(s, 4)})" if c is not None else "--")
        rows.append(row)
    rows.append("MIDRULE")
    rows.append(["Mean of outcome"] + [r(co[m]["mean_y"], 4) for m, _ in models])
    rows.append(["N"] + [f"{co[m]['n']:,}" for m, _ in models])
    rows.append(["Clusters"] + [str(co[m]["n_clusters"]) for m, _ in models])
    body = tabular("l r r r r", ["", *[l for _, l in models]], rows,
                   notes="Coefficients with cluster-robust SEs in parentheses (industry $\\times$ wave). Middle group (gap3 = 1) is the reference for the group intercepts. Industry and wave fixed effects included. Treatments: perceived threat = within-wave residual of the entry-threat item on the other seven market-environment items (not re-standardised; pooled SD close to one, see Table 8 note); entry rate = standardised industry $\\times$ reference-period birth rate. Source: results/06\\_kis\\_main.json.")
    return write("kis_coefficients", body, "\\footnotesize")


def t_robustness():
    K = J("results", "06_kis_main.json"); rob = K["robustness"]; G = J("results", "07b_robustness_gap_proxy.json")
    SPEC = [("raw_threat_0_5", "Raw 0--5 threat item"), ("fe_industry_x_wave", "Industry $\\times$ wave FE"), ("weighted", "KIS sampling weights"), ("excl_2023S", "Excluding 2023S"), ("manufacturing_only", "Manufacturing only"),
            ("services_only", "Services only"), ("exit_strict", "Quit = abandoned without completion"), ("exit_full", "Quit = abandoned, nothing completed/ongoing")]
    rows = [["Main (pre-registered)"] + [f"{r(K['main']['tests'][h]['estimate'], 4, True)} ({ptx(K['main']['tests'][h]['p_one_sided_wild'])})" for h in ("H1", "H2", "H4", "H5")] + [r(K["main"]["tests"]["H6"]["estimate"], 4, True)], "MIDRULE"]
    for key, lab in SPEC:
        rb = rob[key]
        rows.append([lab] + [f"{r(rb['tests'][h]['estimate'], 4, True)} ({ptx(rb['tests'][h]['p_one_sided_wild'])})" for h in ("H1", "H2", "H4", "H5")] + [r(rb["tests"]["H6"]["estimate"], 4, True)])
    if G:
        rows.append("MIDRULE")
        rows.append(["Gap proxy = R\\&D intensity groups [exploratory]"] + [f"{r(G['tests'][h + '_alt']['estimate'], 4, True)} ({ptx(G['tests'][h + '_alt']['p_one_sided_wild'])})" for h in ("H1", "H2", "H4", "H5")] + [r(G["tests"]["H6_alt"]["estimate"], 4, True)])
    TR = J("results", "07d_robustness_threat_residual.json") if os.path.exists(os.path.join(ROOT, "results", "07d_robustness_threat_residual.json")) else None
    if TR:
        for key, lab in (("mean8", "Threat residual on eight-item mean, standardised [exploratory]"), ("mean7", "Threat residual on leave-one-out mean, standardised [exploratory]")):
            v = TR["variants"][key]["tests"]
            rows.append([lab] + [f"{r(v[h]['estimate'], 4, True)} ({ptx(v[h]['p_one_sided_wild'])})" for h in ("H1", "H2", "H4", "H5")] + ["--"])
    body = tabular("p{5.6cm} r r r r r", ["Specification", "H1 (pre-emption)", "H2 (quit)", "H4 (asym.)", "H5 (baseline)", "H6 (est.)"], rows,
                   notes="Estimate (one-sided wild bootstrap $p$; 299 draws for pre-registered robustness rows, 999 for the main and exploratory rows). Pre-registered robustness specifications are reported, not used for decisions; the two quit-definition rows change only the abandonment outcome, so their H1 and H4 entries repeat the main pre-emption model. The R\\&D-intensity proxy row is exploratory (innovation-active firms only, N = " + (f"{G['n_innov_active_with_alt']:,}" if G else "--") + "). The two threat-residual rows rebuild the treatment as the within-wave residual of the entry-threat item on the eight-item mean (the recipe in the registration text) or on the mean of the other seven items, standardised, with the same index as the response-propensity control; H6 does not use the perceived treatment. Sources: results/06\\_kis\\_main.json, results/07b\\_robustness\\_gap\\_proxy.json, results/07d\\_robustness\\_threat\\_residual.json.")
    return write("robustness", body, "\\footnotesize")


def t_placebo_exploratory():
    K = J("results", "06_kis_main.json"); E = J("results", "07_kis_exploratory.json")
    rows = []
    for x, lab in (("placebo_demand_resid", "Placebo: demand hard to predict (ME6)"), ("placebo_price_resid", "Placebo: price rises lose customers (ME8)")):
        v = K["placebo"][x]
        rows.append([lab + " $\\times$ laggard $\\to$ quit", r(v["quit_x_g0"]["estimate"], 4, True), f"[{r(v['quit_x_g0']['ci95_wild'][0], 4, True)}, {r(v['quit_x_g0']['ci95_wild'][1], 4, True)}]", ptx(v["quit_x_g0"]["p_two_sided_wild"]), "pre-registered placebo"])
        rows.append([lab + " $\\times$ frontier $\\to$ pre-emption", r(v["preempt_x_g2"]["estimate"], 4, True), f"[{r(v['preempt_x_g2']['ci95_wild'][0], 4, True)}, {r(v['preempt_x_g2']['ci95_wild'][1], 4, True)}]", ptx(v["preempt_x_g2"]["p_two_sided_wild"]), "pre-registered placebo"])
    rows.append("MIDRULE")
    for k, lab in (("gap1_quit_x_g1", "Threat $\\times$ middle group $\\to$ quit"), ("gap1_preempt_x_g1", "Threat $\\times$ middle group $\\to$ pre-emption")):
        t = E[k]; rows.append([lab, r(t["estimate"], 4, True), f"[{r(t['ci95_wild'][0], 4, True)}, {r(t['ci95_wild'][1], 4, True)}]", ptx(t["p_two_sided_wild"]), "exploratory"])
    for y, yl in (("quit_any", "quit"), ("preempt_strategy", "pre-emption")):
        for g, gl in (("g0", "laggard"), ("g2", "frontier")):
            t = E[f"sigma_item_{y}"][g]; rows.append([f"Rival unpredictability (ME5) $\\times$ {gl} $\\to$ {yl}", r(t["estimate"], 4, True), f"[{r(t['ci95_wild'][0], 4, True)}, {r(t['ci95_wild'][1], 4, True)}]", ptx(t["p_two_sided_wild"]), "exploratory"])
    mf = E["market_first_main_heckman2step"]
    if "x_g2" in mf:
        for g, gl in (("x_g2", "frontier"), ("x_g0", "laggard")):
            t = mf[g]; rows.append([f"Threat $\\times$ {gl} $\\to$ new-to-market product (manuf., selection-corrected)", r(t["estimate"], 4, True), f"[{r(t['ci95_wild'][0], 4, True)}, {r(t['ci95_wild'][1], 4, True)}]", ptx(t["p_two_sided_wild"]), f"exploratory (N = {t['n']:,})"])
    body = tabular("p{7.4cm} r l r l", ["Test", "Estimate", "95\\% wild CI", "$p$ (two-sided)", "Status"], rows,
                   notes="Same specification as the main models. Placebo items were residualised like the threat item. Exploratory tests were listed in the registration as exploratory and carry no decision. Sources: results/06\\_kis\\_main.json (placebo), results/07\\_kis\\_exploratory.json.")
    return write("placebo_exploratory", body, "\\footnotesize")


def t_threeway():
    T = J("results", "06_threeway_table.json")
    rows = []
    for x in T["rows"]:
        rows.append([x["hypothesis"], x["theory_sign"], x["agent_stage_a"] or "n/a", x["agent_stage_b"], r(x["kis_estimate"], 4, True), f"[{r(x['kis_ci95_wild'][0], 4, True)}, {r(x['kis_ci95_wild'][1], 4, True)}]", ptx(x["kis_p_one_sided_wild"]) if x["hypothesis"] != "H6" else "--",
                     x["kis_decision"].replace("_", " ")])
    body = tabular("l c c c r l r l", ["Hypothesis", "Theory", "Agents: Stage A", "Agents: Stage B", "KIS estimate", "95\\% wild CI", "$p$ (one-sided)", "KIS decision"], rows,
                   notes="Theory sign from the model grid; agent signs = consensus of four model $\\times$ language arms (frozen before the survey test); KIS from the pre-registered models. H6 is an equivalence test (90\\% CI within $\\pm$0.010); its KIS column shows the 95\\% CI for reference. Source: results/06\\_threeway\\_table.json.")
    return write("threeway", body)


def t_mechanisms():
    T = J("results", "08_transcript_codes.json")
    if not T or not T.get("agreement"):
        print("SKIP T_mechanisms (codes not ready)"); return False
    cats = T["categories"]
    rows = []
    for stage in ("A", "B"):
        s = T["shares"][stage]
        for dec, dl in (("A", "accelerate"), ("C", "continue"), ("Q", "stop")):
            d = s["by_decision"].get(dec)
            if not d:
                continue
            rows.append([f"Stage {stage}" if dec == "A" else "", dl, f"{d['n']:,}"] + [r(100 * d[cats[k]], 0) for k in cats])
        rows.append("MIDRULE")
    rows.append(["Judge agreement", "$\\kappa$", f"{T['n_coded_by_both']:,}"] + [(r(T["agreement"][k]["kappa"], 2) if T["agreement"][k]["kappa"] == T["agreement"][k]["kappa"] else "n/a$^{\\dagger}$") for k in cats])
    hdr_names = {"M1": "First-mover prize", "M2": "Threat $\\to$ hurry", "M3": "Threat $\\to$ stop", "M4": "Rival position", "M5": "Expected value", "M6": "Sunk / salvage", "M7": "Noise", "M8": "Wait-and-see", "M9": "Firm attributes", "M10": "Irrelevant attribute"}
    body = tabular("l l r " + "r" * len(cats), ["Stage", "Decision", "n"] + [hdr_names[k] for k in cats], rows,
                   notes="Share (\\%) of stated reasons coded 1 by BOTH judge models (Claude fable-5 and GPT-5.6), by stage and decision; last row = Cohen's $\\kappa$ between judges per category. Multi-label coding of " + f"{T['n_reasons']:,}" + " reasons in 25-reason batches; rubric in agent\\_experiment/code\\_transcripts.py. $^{\\dagger}$ $\\kappa$ undefined because both judges coded every reason 0 (percent agreement 100\\%). Source: results/08\\_transcript\\_codes.json.")
    return write("mechanisms", body, "\\scriptsize")


if __name__ == "__main__":
    t0 = time.time()
    res = {"variables": t_variables(), "base_rates": t_base_rates(), "model_predictions": t_model_predictions(), "environment": t_environment(), "stageA_cells": t_stage_cells("A"), "stageB_cells": t_stage_cells("B"),
           "agent_contrasts": t_agent_contrasts(), "kis_main": t_kis_main(), "kis_coefficients": t_kis_coefficients(), "robustness": t_robustness(), "placebo_exploratory": t_placebo_exploratory(), "threeway": t_threeway(), "mechanisms": t_mechanisms()}
    json.dump({"built": time.strftime("%Y-%m-%d %H:%M %Z"), "tables": res}, open(os.path.join(TDIR, "_build.json"), "w"), indent=1)
    print(f"{sum(bool(v) for v in res.values())}/{len(res)} tables in {time.time() - t0:.0f}s")
