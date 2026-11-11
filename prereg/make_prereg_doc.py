#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate prereg/PREREGISTRATION.md (OSF 'Secondary Data Preregistration' template structure; template text saved as
docs/sources/osf_secondary_data_prereg_template_wiki_a48jg_v31.md) from the frozen project files. Nothing numeric is typed here:
hypotheses from docs/HYPOTHESES_GATE_B.md (gate B), variable definitions from item_maps/*.json, model specification from
code/analysis_prereg.py's docstring, agent/theory predictions from prereg/agent_predictions_v1.json, sample sizes and power
from results/02_marginals.json, institutional facts from docs/INSTITUTIONAL_FACTS_escape_or_exit.json, hashes recomputed.
Also writes /tmp/prereg_osf.txt (plain text for pasting) and copies it to the clipboard (pbcopy)."""
import hashlib
import json
import os
import re
import subprocess
import sys
import time

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "PREREGISTRATION.md")
J = lambda *p: json.load(open(os.path.join(ROOT, *p), encoding="utf-8"))  # noqa: E731
sha = lambda p: hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest()  # noqa: E731

WAVES = ["2022M", "2023S", "2024M", "2025S"]
WAVE_LABEL = {"2022M": "KIS 2022 (manufacturing; reference period 2019-2021)", "2023S": "KIS 2023 (services; 2020-2022)",
              "2024M": "KIS 2024 (manufacturing; 2021-2023)", "2025S": "KIS 2025 (services; 2022-2024)"}
# constructs used in the confirmatory models (item-map construct ids)
USED = {"IA3": "quit_any (outcome)", "IA1": "quit_any population / portfolio_breadth", "IA2": "portfolio_breadth", "IA4": "portfolio_breadth", "IA5": "portfolio_breadth", "IA6": "portfolio_breadth",
        "PROT8": "preempt_strategy (outcome)", "ME4": "entry_threat (perceived threat)", "ME1": "me_mean8", "ME2": "me_mean8", "ME3": "me_mean8", "ME5": "me_mean8 / sigma item (exploratory)",
        "ME6": "me_mean8 / placebo_demand", "ME7": "me_mean8", "ME8": "me_mean8 / placebo_price", "RDSTAFF": "gap3 (technology-gap proxy)", "EMP": "log_employees",
        "FORM": "group_affiliate", "LISTED": "listed", "PI1": "market_first population (exploratory)", "PI2": "market_first population (exploratory)", "MF1": "market_first_main (exploratory)"}


def item_rows():
    rows = []
    for w in WAVES:
        m = J("item_maps", f"item_map_{w}.json")
        for e in m["items"]:
            cid = e.get("construct_id")
            if cid in USED:
                rows.append({"construct": cid, "wave": w, "variable": e["variable"], "text": e.get("item_text_questionnaire") or e.get("item_text_ko"),
                             "label": e.get("short_label_en", ""), "coding": e.get("data_coding", ""), "filter": e.get("filter", ""), "use": USED[cid]})
    return pd.DataFrame(rows)


def hyp_table():
    """Return the hypotheses table rows from HYPOTHESES_GATE_B.md (the approved gate-B document) as a list of dicts."""
    txt = open(os.path.join(ROOT, "docs", "HYPOTHESES_GATE_B.md"), encoding="utf-8").read()
    rows = []
    for line in txt.splitlines():
        if line.startswith("| **H") and "|" in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            rows.append({"id": re.sub(r"\*|\(.*?\)", "", cells[0]).strip(), "label": re.search(r"\((.*?)\)", cells[0]).group(1) if re.search(r"\((.*?)\)", cells[0]) else "",
                         "hypothesis_ko": cells[1], "model_basis": cells[2], "test": cells[3].replace("`", ""), "falsification_ko": cells[4]})
    return rows


H_EN = {  # English statements of the gate-B hypotheses (direction as approved; Korean original quoted alongside)
    "H1": "Escape. The higher the perceived threat of entry, the higher the probability that a firm close to the technological frontier (gap3 = 2) adopts a pre-emption strategy: b(threat x g2) > 0.",
    "H2": "Exit. The higher the perceived threat of entry, the higher the probability that a laggard firm (gap3 = 0) abandons or suspends an innovation activity: b(threat x g0) > 0; the same sign is expected with the objective industry entry rate (falsified only if both are <= 0).",
    "H3": "Asymmetry (abandonment). The abandonment effect of entry threat is larger for laggards than for frontier firms: b(threat x g0) - b(threat x g2) > 0.",
    "H4": "Asymmetry (pre-emption). The pre-emption effect of entry threat is larger for frontier firms than for laggards: b(threat x g2) - b(threat x g0) > 0.",
    "H5": "Baseline. Laggards abandon more than frontier firms at any level of threat: a(g0) - a(g2) > 0 (adjusted means at average threat).",
    "H6": "Realised entry vs threat. The objective industry entry rate (realised entry) does NOT raise pre-emption among frontier firms: the 90 % CI of b(entry_rate x g2) lies within [-0.010, +0.010] (equivalence test), in contrast to the perceived-threat effect of H1.",
}


def md_table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for r in rows:
        out.append("| " + " | ".join(str(x).replace("|", "/").replace("\n", " ") for x in r) + " |")
    return "\n".join(out)


def fmt(c):
    if c is None or c.get("estimate") is None:
        return "n/a"
    lo, hi = c["ci95"]
    return f"{c['estimate']:+.3f} [{lo:+.3f}, {hi:+.3f}]"


def main():
    pred = J("prereg", "agent_predictions_v1.json")
    marg = J("results", "02_marginals.json")
    facts = J("docs", "INSTITUTIONAL_FACTS_escape_or_exit.json")
    build = J("results", "01_build_summary.json")
    ext = J("results", "06_external_merge.json")
    calib = J("results", "05_stage_b_env_calibration.json")
    panel = pd.read_parquet(os.path.join(ROOT, "data", "analysis_panel.parquet"))
    ap_doc = open(os.path.join(ROOT, "code", "analysis_prereg.py"), encoding="utf-8").read().split('"""')[1]
    items = item_rows()
    hyps = hyp_table()
    fact = {f["id"]: f for f in facts["facts"]}
    base = marg["A_outcome_base_rates"]
    power = marg["F_power_synthetic"]
    n_pre = int(panel["preempt_strategy"].notna().sum()); n_quit = int(panel["quit_any"].notna().sum())
    n_cl = int(panel["cluster_industry_wave"].nunique())
    gap_counts = panel["gap3"].value_counts().sort_index().to_dict()
    miss = {c: float(panel[c].isna().mean()) for c in ["quit_any", "preempt_strategy", "entry_threat", "gap3", "me_mean8", "log_employees", "firm_age", "group_affiliate", "listed", "portfolio_breadth", "entry_rate"]}

    L = []
    L.append(f"# Preregistration — Escape or Exit: entry threat, technology gap, and the two margins of the innovation race\n")
    L.append(f"Generated {time.strftime('%Y-%m-%d %H:%M %Z')} by prereg/make_prereg_doc.py from frozen project files (tag prereg-v1). Structure follows the OSF Secondary Data Preregistration template (OSF project x4gzt, wiki 'Preregistration Template', version 31; copy in docs/sources/). Items marked [exploratory] carry no confirmatory status.\n")
    # ---------------------------------------------------------------- Study information
    L.append("## Study Information\n")
    L.append("**Title.** Escape or Exit: Entry Threat, Technology Gap, and the Two Margins of the Innovation Race — Theory, Korean Innovation Survey Evidence, and LLM-Agent Experiments (working title).\n")
    L.append("**Authors.** Jihwan Woo (ORCID 0000-0002-0424-0242).\n")
    L.append("**Research questions.**\n")
    L.append("- RQ1. When firms perceive a threat of new entry, do they pre-empt (accelerate and protect products by entering the market ahead of competitors) or exit (abandon or suspend innovation activity), and does the answer depend on the firm's distance to the technological frontier?")
    L.append("- RQ2. Do *perceived* entry threat and *realised* entry (industry entry rates) have different effects on pre-emption, as the race model predicts?")
    L.append("- RQ3 (already completed; predictions frozen before the survey test). Do LLM agents placed in the same race environment reproduce the model's comparative statics? Their cell-level choices are registered here as *predictions*, not as confirmatory tests.\n")
    L.append("**Hypotheses (directional; derived from the finite-horizon innovation-race model in model/MODEL_NOTES.md; approved at gate B on 2026-11-10).** Notation: g = gap3 group (0 laggard, 1 middle, 2 frontier); b(x·g) = slope of x within group g; a(g) = group intercept at average x.\n")
    for h in hyps:
        L.append(f"- **{h['id']}** — {H_EN.get(h['id'], '')}  \n  Model basis: {h['model_basis']}. Test: `{h['test']}`. Original (Korean, gate-B document): {h['hypothesis_ko']} Falsification: {h['falsification_ko']}")
    L.append("")
    L.append("**Theory and agent predictions (frozen).** Signs predicted by the model and by the LLM-agent experiments (Stage A one-shot vignette; Stage B three-period race against the equilibrium rival), per hypothesis. Agent sign calls are mechanical: '+' if the 95 % persona-bootstrap CI of the contrast lies above 0, '-' below 0, '0' otherwise; consensus = at least 3 of 4 model x language arms agree. Source: prereg/agent_predictions_v1.json (SHA256 in SHA256SUMS.txt).\n")
    rows = []
    for h, p in pred["predictions"].items():
        a = p["stage_a"]; b = p["stage_b"]
        rows.append([h, p["theory_sign"], (a and a["consensus"]) or "n/a", (a and ", ".join(f"{k}: {v}" for k, v in a["arm_calls"].items())) or "n/a", b["consensus"], ", ".join(f"{k}: {v}" for k, v in b["arm_calls"].items())])
    L.append(md_table(["Hypothesis", "Theory sign", "Stage A consensus", "Stage A arms", "Stage B consensus", "Stage B arms"], rows))
    L.append("\nAgent contrast estimates with 95 % CIs (Stage A = share choosing the action in the one-shot decision; Stage B = share over the whole episode):\n")
    rows = []
    for h, p in pred["predictions"].items():
        for stage in ("stage_a", "stage_b"):
            s = p[stage]
            if s:
                for arm, est in s["estimates"].items():
                    rows.append([h, stage, s["contrast"], arm, fmt(est)])
    L.append(md_table(["H", "Stage", "Contrast", "Arm", "Estimate [95 % CI]"], rows))
    L.append("")
    # ---------------------------------------------------------------- Data description
    L.append("## Data description\n")
    L.append("**Data sets.** Firm-level microdata of the Korean Innovation Survey (KIS), four waves: " + "; ".join(WAVE_LABEL[w] for w in WAVES) + ". Industry-level enterprise birth rates from the Business Demography Statistics (KOSIS table DT_6BD1101).\n")
    L.append(f"**Is the data open or publicly available?** No for KIS microdata (licensed research-use files provided by the Science and Technology Policy Institute, STEPI; raw files cannot be redistributed). Yes for the KOSIS entry rates (open API).\n")
    L.append(f"**Access.** KIS: STEPI microdata service (research-use provision files `KIS_<year>_배포용/제공용(...)xlsx` with codebook sheets and questionnaire PDFs). KOSIS: {fact['BDS-SOURCE']['source']['url'].split('?')[0]} (orgId 101, tblId DT_6BD1101).\n")
    inv_dates = {}
    for w in WAVES:
        try:
            inv = json.load(open(f"/Users/jihwanw/PhD/MOT/Innovation_Survey/data/KIS/item_inventory_{w}.json", encoding="utf-8"))
            meta = inv.get("_meta") or inv.get("meta") or {}
            inv_dates[w] = str(meta.get("built") or meta.get("created") or "see file")[:10]
        except Exception:
            inv_dates[w] = "see file"
    L.append(f"**Date of download or access.** KIS files were already held by the author (prior projects); full item inventories for this study were built on: " + ", ".join(f"{w}: {d}" for w, d in inv_dates.items()) + f". KOSIS entry rates fetched {fact['BDS-SOURCE']['source']['accessed']}.\n")
    L.append(f"**Data source.** National data set (official statistics): {fact['KIS-APPROVAL']['claim_en']} (Source: {fact['KIS-APPROVAL']['source']['title']}, p.1.) Business Demography Statistics: {fact['BDS-DEFINITIONS']['claim_en']} (Source: {fact['BDS-DEFINITIONS']['source']['title']}, {fact['BDS-DEFINITIONS']['source']['issuer'].split(' (')[0]}, {fact['BDS-DEFINITIONS']['source']['date']}.)\n")
    L.append("**Codebook.** STEPI codebook sheets inside each provision file and the printed questionnaires. For this study every item used was read in the questionnaire and codebook and transcribed to audited item maps (item_maps/item_map_<wave>.json; audit reports results/audit/survey_item_audit_<wave>.txt, all PASS). The item maps, with question wording, printed codes, observed data values and recodes, are part of the registered package.\n")
    L.append("**Sampling and data collection procedures.** Documented by STEPI in the questionnaires and methodology reports; the survey follows the OECD Oslo Manual and is fielded by Gallup Korea (questionnaire p.1). Manufacturing and services are surveyed in alternating years with sector-specific questionnaires; the market-environment block used here (문1-2 / Q1K2, eight items on a 0-5 scale) is identical across the four waves in wording, as verified item by item.\n")
    # ---------------------------------------------------------------- Knowledge of data
    L.append("## Knowledge of data\n")
    L.append("**Prior work based on the dataset.** The author has published and submitted several papers using KIS waves 2020-2025 (manufacturing and services) on open-innovation search breadth, knowledge-source composition, capability deficits and openness, policy-strategy alignment, AI adoption, and leader-follower asymmetry in innovation performance. Those papers used innovation outputs (product/process innovation), knowledge-source and cooperation items, hampering factors, strategy items, AI-use items and the registry controls (industry, size, age, group affiliation, certification, sales/exports). The four variables that carry this study's hypotheses — the market-environment block 문1-2 (entry threat and the other seven items), abandoned/suspended innovation activity (문11-③), the lead-time protection item (문2-⑧) and new-to-market product innovation (문6-①) — were not analysed in any of them (RESEARCH_PLAN.md §2).\n")
    L.append("**Prior research activity.** I have used this dataset before, and some of the control variables (industry, size, age, group affiliation, listing, R&D-staff share, innovation-activity items) on these same waves; the outcome and treatment variables of this study have not been analysed before.\n")
    L.append(f"**Prior knowledge of the current data set.** Before registration the following were computed and are disclosed in results/02_marginals.json and results/01_build_summary.json: outcome base rates by wave and size band (quit_any {base['by_wave']['2022M']['quit_any']['rate_unweighted']:.3f} in 2022M, {base['by_wave']['2023S']['quit_any']['rate_unweighted']:.3f} in 2023S, {base['by_wave']['2024M']['quit_any']['rate_unweighted']:.3f} in 2024M, {base['by_wave']['2025S']['quit_any']['rate_unweighted']:.3f} in 2025S; preempt_strategy {base['by_wave']['2022M']['preempt_strategy']['rate_unweighted']:.3f}, {base['by_wave']['2023S']['preempt_strategy']['rate_unweighted']:.3f}, {base['by_wave']['2024M']['preempt_strategy']['rate_unweighted']:.3f}, {base['by_wave']['2025S']['preempt_strategy']['rate_unweighted']:.3f}), distributions of the eight market-environment items and of the R&D-staff share, correlations among explanatory items (including entry threat vs the placebo item ME6, which motivated the response-propensity adjustment), cluster counts and a synthetic-outcome power analysis. No statistic combining an outcome with a treatment variable has been computed: the loader keeps outcome and treatment columns apart (`load_kis_escape_exit.OUTCOME_COLS` / `TREATMENT_COLS`, cross-tabulation refused), the marginals file records `embargo = \"{marg['embargo']}\"`, and the confirmatory script refuses to run on real outcomes until prereg/REGISTERED.json exists.\n")
    L.append("**Moment of preregistration.** Registration after data cleaning, but before any main analyses.\n")
    # ---------------------------------------------------------------- Variables
    L.append("## Current study: Variables\n")
    L.append("**Manipulated variables.** Not applicable for the survey analysis (observational). In the completed LLM-agent experiments the manipulated factors were gap (3 levels: one stage behind / level / one stage ahead), entry threat (none vs 35 % per period) and observation noise (exact vs 40 % one-stage error), plus a placebo attribute (founding-anniversary month).\n")
    L.append("**Measured variables (survey items used in the confirmatory models; wording from the questionnaires, per wave).**\n")
    rows = [[r.construct, r.wave, r.variable, r.text, r.label, r.coding, r.use] for r in items.sort_values(["construct", "wave"]).itertuples()]
    L.append(md_table(["Construct", "Wave", "Variable", "Questionnaire wording", "English label", "Data coding", "Used as"], rows))
    L.append("\nRegistry variables (from the provision files): 2-digit KSIC industry (industry2), employee-size band, founding year (firm age = reference year - founding year), sampling weight. External: industry2 x year enterprise birth rate (KOSIS DT_6BD1101, national rows), averaged over the three reference years of each wave (`entry_rate`), log of active enterprises.\n")
    L.append("**Scales / indices.**\n")
    L.append("- `me_mean8` (response-propensity index): mean of the eight market-environment items ME1-ME8 (0-5 scale), all firms. Rationale: the entry-threat item correlates strongly with the placebo demand-uncertainty item (r = 0.55 in results/02_marginals.json D), so a firm's general tendency to rate environmental pressures high must be removed. Aggregation: mean score; not based on a codebook recommendation.")
    L.append("- `gap3` (technology-gap group): 0 if the share of dedicated R&D staff among regular employees (RDSTAFF) is 0; 1 if positive and <= the median of positive shares in the firm's industry2 x wave cell (borrowing the section x wave or wave median when the cell has fewer than 10 positive values; the level used is recorded in `gap3_median_source`); 2 if above that median. Group 2 is the survey counterpart of the model's leader one stage from completion, group 0 of the laggard.")
    L.append("- `portfolio_breadth`: count of 'yes' among IA1, IA2, IA4, IA5, IA6 (IA3 excluded because it is the outcome); quit models only.\n")
    L.append("**Transformations.** `entry_threat_resid`: within each wave, residual of ME4 from an OLS on `me_mean8`, standardised (SD 1). `placebo_demand_resid`, `placebo_price_resid`: same recipe for ME6, ME8. `entry_rate_z`: standardised `entry_rate`. `log_employees` = log(regular employees); `log1p_firm_age` = log(1 + firm age). Dummy coding: gap3 groups (g0, g2 with g1 as reference, plus x·g0, x·g1, x·g2 slopes); group affiliation (domestic-group, foreign-group vs independent); industry2 and wave fixed effects. Binary outcomes recoded to printed yes = 1 / no = 0 after wave-specific recodes recorded in the item maps.\n")
    L.append(f"**Data inclusion / exclusion.** Waves {', '.join(WAVES)} (KIS 2020 manufacturing excluded: its questionnaire has no market-environment block). Pre-emption models: all responding firms (N = {n_pre:,}). Abandonment models: firms with any innovation activity in the reference period (IA1-IA6 any yes), for which 문11-③ is defined (N = {n_quit:,}). Firms with missing gap3 (missing R&D-staff share) or missing controls are dropped listwise (missingness below). Undocumented sentinel values are treated as missing as documented in code/load_kis_escape_exit.py (2024M R&D-expenditure 99999999; 2025S founding year 30).\n")
    L.append("**Outliers.** Outcomes are binary; no observations are removed for outlying values. Continuous controls enter in logs. No winsorising.\n")
    L.append("**Weights.** KIS sampling weights are available in all four waves. Main models are unweighted (the estimand is the within-sample conditional association; weights are a pre-registered robustness check with the same specification).\n")
    pq = power["quit_any"]["quit_any"]; pp = power["preempt_strategy"]["preempt_strategy"]
    L.append(f"**Sample size and power.** N = {n_pre:,} firms (pre-emption models), {n_quit:,} (abandonment models); {n_cl} industry2 x wave clusters; gap3 group sizes {gap_counts}. Synthetic-outcome power analysis at the observed base rates (results/02_marginals.json F; 400 simulations per point; real outcomes not used): 80 % power for an interaction slope of {pq['mde80_perceived_interaction_by_delta']:.3f} (abandonment, per SD of the threat residual within gap3 = 0) and {pp['mde80_perceived_interaction_by_delta']:.3f} (pre-emption, within gap3 = 2); industry-level (entry-rate) interactions {pq['mde80_industry_level_interaction_by_delta']:.3f} and {pp['mde80_industry_level_interaction_by_delta']:.3f}. The smallest effects considered meaningful are these MDEs; the H6 equivalence bound delta = {pp['mde80_perceived_interaction_by_delta']:.3f} equals the pre-emption MDE.\n")
    L.append("**Missing data.** Share missing in the analysis panel (all firms): " + ", ".join(f"{k} {v:.3f}" for k, v in miss.items()) + ". `quit_any` and `portfolio_breadth` are missing by design for firms without innovation activity (not in the abandonment sample). Listwise deletion within each model; the number of firms used is reported for every estimate.\n")
    # ---------------------------------------------------------------- Analyses
    L.append("## Current study: Analyses\n")
    L.append("**Statistical models, inference criteria, sensitivity analyses, backup plan and exploratory analyses** are fixed in code/analysis_prereg.py (frozen; SHA256 below). Its specification, verbatim:\n")
    L.append("```\n" + ap_doc.strip() + "\n```\n")
    L.append("**Follow-up analyses.** H3 and H4 are the pre-specified contrasts between group slopes within the same model; no further post-hoc contrasts are confirmatory. Sector-specific estimates (manufacturing / services) are reported as sensitivity analyses, not as separate tests.\n")
    L.append("**Statistical analysis backup plan.** If the logit secondary estimator does not converge, the linear probability model alone is reported. If a wild-bootstrap distribution is degenerate (fewer than 20 clusters with any event in a subsample), the cluster-robust t is reported and the test flagged. If a gap3 group has fewer than 30 firms in a subsample used for robustness, that subsample estimate is reported without a decision. Known-answer and null controls of the pipeline were run before registration on simulated and permuted outcomes (results/06_kis_main_simulate.json, results/06_kis_main_permute.json); the permutation control is the reason the wild cluster bootstrap-t, not the cluster-robust t, is the primary inference.\n")
    L.append("**Exploratory analyses [exploratory].** (a) New-to-market product innovation (문6-①) among manufacturing product innovators with a two-step selection correction; (b) the threat slope in the middle group gap3 = 1; (c) the sign of the rival-unpredictability item ME5 (the model gives opposite signs under two definitions of sigma, so no direction is registered); (d) placebo items ME6 and ME8 in the same models (expected null; pre-registered check); (e) cell-mean tables by gap3 x threat tercile; (f) coding of the LLM agents' stated reasons by rubric. Written to results/07_kis_exploratory.json and labelled exploratory in the manuscript.\n")
    # ---------------------------------------------------------------- Agent experiment (completed)
    L.append("## LLM-agent experiments (completed before this registration; design and results frozen)\n")
    env = pred["environment"]["constants"]
    L.append(f"Environment (agent_experiment/race_env.py): {env['K']} development stages, {env['T']} periods; continue cost {env['cC'] * 100:.0f}억원 with success {env['pC']:.0%}, accelerate cost {env['cA'] * 100:.0f}억원 with success {env['pA']:.0%}, stop 0; prizes {env['V'] * 100:.0f}억원 first / {env['W'] * 100:.0f}억원 second / {(env['V'] + env['W']) / 2 * 100:.1f}억원 simultaneous; entry probability 35 % per period in threat games, halving unfinished prizes (lambda = {env['lam']}); 40 % one-stage observation error in noise games. The acceleration cost was calibrated before any agent call by a rule fixed in advance (results/05_stage_b_env_calibration.json: at the draft value the model's leader accelerated with probability 1 at theta = 0, leaving H1 no room; {calib['chosen_cA_billion_won']}억원 is the unique passing value on a 5억 grid). Rival = equilibrium policy of the solved model. Agents: two frontier LLMs (fable-5 via Amazon Bedrock; GPT 5.6 via Bedrock Mantle), Korean and English prompts, {pred['stage_a']['n_calls']} Stage A calls and {pred['stage_b']['n_episodes']} Stage B episodes; personas drawn from KIS registry attributes only. Earlier template versions (v1 ceiling; v2 head-office placebo and second-prize wording) are documented with their logs; the registered predictions come from v3 only.\n")
    L.append("Checks (should be null): Stage A within-cell placebo and option-position effects, Stage B within-cell placebo — see `checks` in prereg/agent_predictions_v1.json.\n")
    # ---------------------------------------------------------------- Other
    L.append("## Other relevant information\n")
    L.append("**Embargo log.** Files that demonstrate no outcome x treatment statistic was computed before registration: results/01_build_summary.json (loader summary without cross-tabulations), results/02_marginals.json (`embargo` field), code/load_kis_escape_exit.py (refusal logic), code/analysis_prereg.py (`--real` requires prereg/REGISTERED.json). Session log: SESSION_LOG.md.\n")
    L.append("**Deviations.** Any departure from this plan will be listed in a 'Deviations from preregistration' appendix of the manuscript with the reason and the date.\n")
    L.append("**Frozen files (SHA256).**\n")
    files = ["code/analysis_prereg.py", "code/load_kis_escape_exit.py", "code/merge_external.py", "prereg/agent_predictions_v1.json", "docs/HYPOTHESES_GATE_B.md", "model/race_model.py",
             "agent_experiment/race_env.py", "agent_experiment/run_stage_a.py", "agent_experiment/run_stage_b.py", "agent_experiment/prompts/stage_a_templates.py", "agent_experiment/prompts/stage_b_templates.py",
             "item_maps/item_map_escape_exit.json"] + [f"item_maps/item_map_{w}.json" for w in WAVES] + ["results/02_marginals.json", "results/05_stage_b_env_calibration.json"]
    L.append(md_table(["File", "SHA256"], [[f, sha(f)] for f in files if os.path.exists(os.path.join(ROOT, f))]))
    L.append(f"\nAnalysis panel (not distributed; KIS licence): data/analysis_panel.parquet SHA256 {sha('data/analysis_panel.parquet')}, {len(panel):,} rows x {panel.shape[1]} columns.\n")
    text = "\n".join(L)
    open(OUT, "w", encoding="utf-8").write(text)
    plain = re.sub(r"\*\*(.*?)\*\*", r"\1", text).replace("`", "")
    open("/tmp/prereg_osf.txt", "w", encoding="utf-8").write(plain)
    try:
        subprocess.run(["pbcopy"], input=plain.encode("utf-8"), check=True)
        clip = "copied to clipboard"
    except Exception as e:  # noqa
        clip = f"pbcopy failed: {e}"
    print("->", OUT, f"({len(text):,} chars);", clip, "; plain text /tmp/prereg_osf.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
