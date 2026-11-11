#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""JSON -> paper/numbers.json + paper/numbers.tex (semantic LaTeX macros). Reads ONLY results/*.json, prereg/*.json and
docs/INSTITUTIONAL_FACTS_escape_or_exit.json. The manuscript prose cites macros, never literals. ROUND_HALF_UP formatting.
Missing inputs produce the macro text '[RESULTS-GAP: <key>]' instead of a number."""
import json
import os
import re
import time
from decimal import ROUND_HALF_UP, Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PAPER = os.path.join(ROOT, "paper")
# environment constants that are not in a results JSON are read from the environment module itself (never retyped)
import sys  # noqa: E402
sys.path.insert(0, os.path.join(ROOT, "agent_experiment"))
from race_env import THETA as ENV_THETA, OBS_NOISE as ENV_OBS_NOISE  # noqa: E402
os.makedirs(PAPER, exist_ok=True)


def J(*p):
    f = os.path.join(ROOT, *p)
    return json.load(open(f, encoding="utf-8")) if os.path.exists(f) else None


def rnd(x, nd=3):
    if x is None:
        return None
    q = Decimal(1).scaleb(-nd)
    return str(Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP))


def pct(x, nd=1):
    return None if x is None else rnd(100 * x, nd)


def pp(x, nd=2):  # probability change -> percentage points
    return None if x is None else rnd(100 * x, nd)


def signed(x, nd=3):
    if x is None:
        return None
    s = rnd(x, nd)
    return s if s.startswith("-") else "+" + s


def ptxt(p, nd=3):
    if p is None:
        return None
    if p < 0.001:
        return "<0.001"
    return rnd(p, nd)


def camel(s):
    parts = re.split(r"[^A-Za-z0-9]+", s)
    out = "".join(w[:1].upper() + w[1:] for w in parts if w)
    return re.sub(r"[0-9]", lambda m: ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"][int(m.group())], out)


ARM = {"fable/en": "FaEn", "fable/ko": "FaKo", "gpt56/en": "GpEn", "gpt56/ko": "GpKo"}
HNAME = {"H1": "HOne", "H2": "HTwo", "H3": "HThree", "H4": "HFour", "H5": "HFive", "H6": "HSix", "H2_objective": "HTwoObj"}


def main():
    N = {}  # macro name -> value (string)
    gaps = []

    def put(name, val):
        if val is None:
            gaps.append(name); N[name] = f"[RESULTS-GAP: {name}]"
        else:
            N[name] = str(val)

    # ---------------------------------------------------------------- data / sample
    marg = J("results", "02_marginals.json"); build = J("results", "01_build_summary.json"); ext = J("results", "06_external_merge.json")
    pooled = marg["A_outcome_base_rates"]["pooled"]
    put("NFirms", f"{pooled['preempt_strategy']['n']:,}"); put("NQuitSample", f"{pooled['quit_any']['n']:,}")
    put("QuitEvents", f"{pooled['quit_any']['events']:,}"); put("PreemptEvents", f"{pooled['preempt_strategy']['events']:,}")
    put("QuitRatePct", pct(pooled["quit_any"]["rate_unweighted"])); put("PreemptRatePct", pct(pooled["preempt_strategy"]["rate_unweighted"]))
    put("ExitStrictRatePct", pct(pooled["exit_strict"]["rate_unweighted"])); put("ExitFullRatePct", pct(pooled["exit_full"]["rate_unweighted"]))
    put("MarketFirstRatePct", pct(pooled["market_first"]["rate_unweighted"])); put("NMarketFirstSample", f"{pooled['market_first']['n']:,}")
    for w, d in marg["A_outcome_base_rates"]["by_wave"].items():
        put(f"N{camel(w)}", f"{d['preempt_strategy']['n']:,}"); put(f"QuitRate{camel(w)}Pct", pct(d["quit_any"]["rate_unweighted"])); put(f"PreemptRate{camel(w)}Pct", pct(d["preempt_strategy"]["rate_unweighted"]))
        put(f"NInnovActive{camel(w)}", f"{d['quit_any']['n']:,}")
    pairs = {(a, b): r for a, b, r in marg["D_explanatory_correlations"]["pairs_abs_corr_ge_0.5"]}
    put("CorrThreatPlacebo", rnd(pairs.get(("ME4", "ME6")), 2)); put("CorrThreatSigma", rnd(marg["D_explanatory_correlations"]["corr_ME4_ME5"], 2))
    # pairs of the eight market-environment items (28 pairs) with |r| >= 0.5; three named in the text. Item meanings from item_map_<wave>.json
    # [codebook Q1K2_*; questionnaire 문1-2]: ME2 'future technological developments hard to predict', ME3 'competitor products easily substitute
    # ours', ME4 'entry of new competitors threatens market position', ME5 'competitors' actions hard to predict', ME6 'changes in demand hard to predict'
    me_pairs = {k: v for k, v in pairs.items() if k[0].startswith("ME") and k[1].startswith("ME")}
    put("MEPairsGeHalf", str(len(me_pairs))); put("MEPairsTotal", str(8 * 7 // 2))
    put("CorrTechUncThreat", rnd(me_pairs.get(("ME2", "ME4")), 2)); put("CorrTechUncDemand", rnd(me_pairs.get(("ME2", "ME6")), 2)); put("CorrSubstSigma", rnd(me_pairs.get(("ME3", "ME5")), 2))
    LM = J("results", "01_literature_map_check.json"); RC = J("results", "01_ref_check.json")
    put("LitMapWorks", str(LM["n_bib_entries"]) if LM else None); put("LitMapClaims", str(LM["claim_lines_total"]) if LM else None)
    put("RefsCrossref", str(RC["n_resolved"]) if RC else None); put("RefsManual", str(RC["n_unresolved"]) if RC else None)
    cl = marg["E_clusters_and_event_counts"]
    put("NClusters", "114")  # from 06_kis_main n_clusters below (overwritten)
    pw = marg["F_power_synthetic"]
    put("MDEQuitPp", pp(pw["quit_any"]["quit_any"]["mde80_perceived_interaction_by_delta"], 1)); put("MDEPreemptPp", pp(pw["preempt_strategy"]["preempt_strategy"]["mde80_perceived_interaction_by_delta"], 1))
    put("SentinelValueRDExp", "99,999,999")
    if ext:
        cov = ext["coverage"]
        for w, d in cov.items():
            put(f"EntryRateMedian{camel(w)}Pct", rnd(d["entry_rate_pct"]["p50"], 1)); put(f"EntryRateMin{camel(w)}Pct", rnd(d["entry_rate_pct"]["min"], 1)); put(f"EntryRateMax{camel(w)}Pct", rnd(d["entry_rate_pct"]["max"], 1))
            put(f"NIndustryCells{camel(w)}", str(d["n_industry_cells"]))
        put("EntryRateMissingFirms", str(sum(d["n_firms_missing_entry_rate"] for d in cov.values()))); put("LookAheadViolations", str(ext.get("look_ahead_violations")))

    # ---------------------------------------------------------------- model
    mp = J("results", "03_model_predictions.json")
    put("GridPoints", f"{mp['n_grid_points']:,}"); put("GridRows", f"{mp['n_rows']:,}")
    put("ThetaGrid", ", ".join(str(t) for t in mp["theta_grid"])); put("SigmaGrid", ", ".join(str(s) for s in mp["sigma_grid"]))
    for pid, d in mp["decisions"].items():
        nm = camel(pid)
        put(f"Model{nm}Candidate", "yes" if d.get("candidate") else "no")
        if "share_informative_e2e" in d:
            put(f"Model{nm}Informative", pct(d.get("share_informative_e2e"), 0)); put(f"Model{nm}Holds", pct(d.get("e2e_holds_among_informative"), 0)); put(f"Model{nm}Strict", pct(d.get("strict_holds_among_informative"), 0))
        else:  # sigma predictions P5/P6: dominant direction by definition
            for sdef, (direction, share, inf) in d["dominant_direction_share_informative"].items():
                put(f"Model{nm}{camel(sdef)}Dir", direction); put(f"Model{nm}{camel(sdef)}Share", pct(share, 0)); put(f"Model{nm}{camel(sdef)}Informative", pct(inf, 0))
    MCT = J("results", "03_model_controls.json")
    if MCT:
        c9 = MCT["checks"]["C9_conditional_threat_outcomes"]["detail"]
        put("ModelControlsCount", str(len(MCT["checks"]))); put("ModelControlsStatus", MCT["status"])
        put("MCPaths", f"{c9['n_mc']:,}"); put("MCMaxDiff", rnd(max(c9["mc_vs_exact_abs_diff"].values()), 3))  # scope: max over the three outcome probabilities compared
    put("ModelMultiShare", pct(mp["multiplicity"]["share_runs_with_multiple_equilibria"], 0)); put("ModelMixedShare", pct(mp["multiplicity"]["share_runs_with_mixed_equilibria"], 0))
    # threat-conditional vs unconditional versions, main (welfare) selection rule: end-to-end sign shares over all grid points
    for ver, vn in (("threat", "Thr"), ("unconditional", "Unc")):
        e2e = mp["theta"][ver]["welfare"]
        put(f"ModelPOne{vn}Holds", pct(e2e["P1"]["end_to_end"].get("holds", 0), 0)); put(f"ModelPOne{vn}Violated", pct(e2e["P1"]["end_to_end"].get("violated", 0), 0))
        put(f"ModelPTwo{vn}Holds", pct(e2e["P2"]["end_to_end"].get("holds", 0), 0)); put(f"ModelPTwo{vn}Violated", pct(e2e["P2"]["end_to_end"].get("violated", 0), 0))
        put(f"ModelPTwoLFar{vn}Up", pct(e2e["P2L_far"]["end_to_end"].get("up", 0), 0))

    # ---------------------------------------------------------------- environment / calibration
    cal = J("results", "05_stage_b_env_calibration.json"); env = cal["fixed"] | {"cA": cal["chosen_cA"]}
    put("EnvStages", str(env["K"])); put("EnvPeriods", str(env["T"])); put("EnvContinueCost", str(round(env["cC"] * 100))); put("EnvAccelCost", str(round(env["cA"] * 100)))
    put("EnvDraftAccelCost", str(round(cal["draft_cA_was"] * 100))); put("EnvContinueSucc", pct(env["pC"], 0)); put("EnvAccelSucc", pct(env["pA"], 0))
    put("EnvPrizeFirst", str(round(env["V"] * 100))); put("EnvPrizeSecond", str(round(env["W"] * 100))); put("EnvPrizeTie", rnd((env["V"] + env["W"]) / 2 * 100, 1))
    put("EnvTheta", pct(ENV_THETA[1], 0)); put("EnvLambda", str(env["lam"])); put("EnvNoise", pct(ENV_OBS_NOISE[1], 0))  # race_env.THETA / OBS_NOISE
    chosen = next(r for r in cal["scan"] if r["cA"] == cal["chosen_cA"])
    put("EnvLeaderAccelNoThreat", rnd(chosen["summary"]["leader_accel_noentry_theta0"])); put("EnvLeaderAccelThreat", rnd(chosen["summary"]["leader_accel_noentry_theta35"]))
    put("EnvLaggardQuitNoThreat", rnd(chosen["summary"]["laggard_quit_theta0"])); put("EnvLaggardQuitThreat", rnd(chosen["summary"]["laggard_quit_theta35"]))
    draft = next(r for r in cal["scan"] if r["cA"] == cal["draft_cA_was"])
    put("EnvDraftLeaderAccelNoThreat", rnd(draft["summary"]["leader_accel_noentry_theta0"]))

    # ---------------------------------------------------------------- agents
    A = J("results", "04_agent_stage_a.json"); B = J("results", "05_agent_stage_b.json")
    put("StageACalls", f"{A['n_calls']:,}"); put("StageAParseFail", str(sum(v for k, v in A["parse_status"].items() if k != "ok")))
    put("StageAPersonas", "40"); put("StageBPersonas", "24"); put("StageBEpisodes", f"{B['n_episodes']:,}"); put("StageBParseFailed", str(B["status_counts"].get("parse_failed", 0)))
    put("StageBComplete", f"{B['status_counts'].get('complete', 0):,}")
    for h, key in (("HOne", "H1_accel_threat_gap2"), ("HTwo", "H2_quit_threat_gap0"), ("HThree", "H3_quit_threat_gap0_minus_gap2"), ("HFour", "H4_accel_threat_gap2_minus_gap0"), ("HFive", "H5_quit_gap0_minus_gap2")):
        ests = []
        for arm, v in A["by_model_lang"].items():
            c = v["contrasts"][key]; ests.append(c["estimate"])
            put(f"SA{h}{ARM[arm]}", signed(c["estimate"])); put(f"SA{h}{ARM[arm]}Lo", signed(c["ci95"][0])); put(f"SA{h}{ARM[arm]}Hi", signed(c["ci95"][1]))
        put(f"SA{h}Min", signed(min(ests))); put(f"SA{h}Max", signed(max(ests)))
    for h, key in (("HOne", "H1_accel_threat_gap2_noentry"), ("HOneUncond", "H1_accel_threat_gap2"), ("HTwo", "H2_quit_threat_gap0"), ("HThree", "H3_quit_threat_gap0_minus_gap2"),
                   ("HFour", "H4_accel_threat_gap2_minus_gap0"), ("HFive", "H5_quit_gap0_minus_gap2")):
        ests = []
        for arm, v in B["by_model_lang"].items():
            c = v["contrasts"][key]; ests.append(c["estimate"])
            put(f"SB{h}{ARM[arm]}", signed(c["estimate"])); put(f"SB{h}{ARM[arm]}Lo", signed(c["ci95"][0])); put(f"SB{h}{ARM[arm]}Hi", signed(c["ci95"][1]))
        put(f"SB{h}Min", signed(min(ests))); put(f"SB{h}Max", signed(max(ests)))
    put("StageAPlaceboMinHolm", rnd(A["null_family_holm"]["min_holm_p"], 2)); put("StageBPlaceboMinHolm", rnd(B["null_family_holm"]["min_holm_p"], 2))
    put("StageAPlaceboMinRaw", rnd(min(A["null_family_holm"]["raw_p"].values()), 3)); put("StageBPlaceboMinRaw", rnd(min(B["null_family_holm"]["raw_p"].values()), 3))
    for arm, v in A["by_model_lang"].items():
        put(f"SAOverallAccel{ARM[arm]}Pct", pct(v["overall"]["p_accel"])); put(f"SAOverallQuit{ARM[arm]}Pct", pct(v["overall"]["p_quit"])); put(f"SAOverallCont{ARM[arm]}Pct", pct(v["overall"]["p_cont"]))
    # model period-1 counterparts
    p1 = A["model_period1_action_probs"]
    put("ModelPOneLeaderAccelThreat", rnd(p1["g2t1"]["P_accel"])); put("ModelPOneLaggardQuitThreat", rnd(p1["g0t1"]["P_quit"]))
    # model whole-game predictions per cell (Stage B comparison), leader accel & laggard quit
    mpc = B["model_predictions"]
    put("ModelCellLeaderAccelNoThreat", rnd(mpc["g2t0n0"]["unconditional"]["P_accel"])); put("ModelCellLeaderAccelThreatNoEntry", rnd(mpc["g2t1n0"]["no_entry_conditional"]["P_accel"]))
    put("ModelCellLeaderAccelThreatUncond", rnd(mpc["g2t1n0"]["unconditional"]["P_accel"])); put("ModelCellLaggardQuitNoThreat", rnd(mpc["g0t0n0"]["unconditional"]["P_quit"])); put("ModelCellLaggardQuitThreat", rnd(mpc["g0t1n0"]["unconditional"]["P_quit"]))
    # agent cell ranges (Stage B) for leader accel at theta=0 and laggard quit
    la = [c["P_accel"] for v in B["by_model_lang"].values() for c in v["cells"] if c["gap"] == 2 and c["threat"] == 0]
    lq0 = [c["P_quit"] for v in B["by_model_lang"].values() for c in v["cells"] if c["gap"] == 0 and c["threat"] == 0]
    lq1 = [c["P_quit"] for v in B["by_model_lang"].values() for c in v["cells"] if c["gap"] == 0 and c["threat"] == 1]
    put("SBLeaderAccelNoThreatMin", rnd(min(la), 2)); put("SBLeaderAccelNoThreatMax", rnd(max(la), 2))
    put("SBLaggardQuitNoThreatMin", rnd(min(lq0), 2)); put("SBLaggardQuitNoThreatMax", rnd(max(lq0), 2)); put("SBLaggardQuitThreatMin", rnd(min(lq1), 2)); put("SBLaggardQuitThreatMax", rnd(max(lq1), 2))
    pred = J("prereg", "agent_predictions_v1.json")
    for h, p in pred["predictions"].items():
        put(f"Pred{HNAME[h]}Theory", p["theory_sign"]); put(f"Pred{HNAME[h]}StageA", (p["stage_a"] or {}).get("consensus") or "n/a"); put(f"Pred{HNAME[h]}StageB", p["stage_b"]["consensus"])
    put("PredSha", open(os.path.join(ROOT, "prereg", "SHA256SUMS.txt")).read().split()[0][:12])

    # ---------------------------------------------------------------- KIS main
    K = J("results", "06_kis_main.json"); M = K["main"]
    put("NClusters", str(M["tests"]["H1"]["n_clusters"])); put("NClustersQuit", str(M["tests"]["H2"]["n_clusters"]))
    put("NPreemptModel", f"{M['tests']['H1']['n']:,}"); put("NQuitModel", f"{M['tests']['H2']['n']:,}"); put("NBoot", str(M["tests"]["H1"]["n_boot"]))
    for h, t in M["tests"].items():
        nm = HNAME[h]
        put(f"KIS{nm}Est", signed(t["estimate"], 4)); put(f"KIS{nm}Pp", signed(100 * t["estimate"], 2)); put(f"KIS{nm}SE", rnd(t["se_cluster"], 4))
        put(f"KIS{nm}Lo", signed(t["ci95_wild"][0], 4)); put(f"KIS{nm}Hi", signed(t["ci95_wild"][1], 4)); put(f"KIS{nm}LoPp", signed(100 * t["ci95_wild"][0], 2)); put(f"KIS{nm}HiPp", signed(100 * t["ci95_wild"][1], 2))
        put(f"KIS{nm}NinetyLo", signed(t["ci90_wild"][0], 4)); put(f"KIS{nm}NinetyHi", signed(t["ci90_wild"][1], 4)); put(f"KIS{nm}NinetyLoPp", signed(100 * t["ci90_wild"][0], 2)); put(f"KIS{nm}NinetyHiPp", signed(100 * t["ci90_wild"][1], 2))
        put(f"KIS{nm}POne", ptxt(t["p_one_sided_wild"])); put(f"KIS{nm}PTwo", ptxt(t["p_two_sided_wild"])); put(f"KIS{nm}POneT", ptxt(t["p_one_sided_cluster_t"]))
        put(f"KIS{nm}T", rnd(t["t"], 2))
    for h, v in M["holm_wild"].items():
        put(f"KIS{HNAME[h]}Holm", ptxt(v))
    for h, v in M["decisions"].items():
        put(f"KIS{HNAME[h]}Decision", v)
    put("KISHSixDelta", rnd(M["H6_delta"], 3)); put("KISHSixDeltaPp", pp(M["H6_delta"], 1))
    put("KISHTwoFalsified", "yes" if M["H2_falsified_both_nonpositive"] else "no")
    # effect sizes relative to base rates (ratios of two JSON quantities; scope: pooled analysis samples)
    put("KISHOneRelMeanPct", pct(M["tests"]["H1"]["estimate"] / M["coefficients"]["preempt_perceived"]["mean_y"], 0))
    put("KISHFiveRelMeanPct", pct(M["tests"]["H5"]["estimate"] / M["coefficients"]["quit_perceived"]["mean_y"], 0))
    co = M["coefficients"]
    for name, nm in (("preempt_perceived", "Pre"), ("quit_perceived", "Quit"), ("quit_objective", "QuitObj"), ("preempt_objective", "PreObj")):
        for k, v in co[name]["coef"].items():
            put(f"Coef{nm}{camel(k)}", signed(v, 4)); put(f"SE{nm}{camel(k)}", rnd(co[name]["se"][k], 4))
        put(f"MeanY{nm}", rnd(co[name]["mean_y"], 4)); put(f"N{nm}Model", f"{co[name]['n']:,}")
        ame = (co[name].get("logit_ame") or {}).get("ame") or {}
        for k, v in ame.items():
            put(f"AME{nm}{camel(k)}", signed(v, 4))
    for x, v in K["placebo"].items():
        nm = "PlaceboDemand" if "demand" in x else "PlaceboPrice"
        put(f"{nm}QuitEst", signed(v["quit_x_g0"]["estimate"], 4)); put(f"{nm}QuitP", ptxt(v["quit_x_g0"]["p_two_sided_wild"]))
        put(f"{nm}PreEst", signed(v["preempt_x_g2"]["estimate"], 4)); put(f"{nm}PreP", ptxt(v["preempt_x_g2"]["p_two_sided_wild"]))
    SPEC = {"raw_threat_0_5": "Raw", "fe_industry_x_wave": "FEIW", "weighted": "Wtd", "excl_2023S": "ExclS", "manufacturing_only": "Manu", "services_only": "Serv", "exit_strict": "Strict", "exit_full": "Full"}
    for spec, rb in K["robustness"].items():
        for h in ("H1", "H2", "H2_objective", "H3", "H4", "H5", "H6"):
            t = rb["tests"][h]; put(f"Rob{SPEC[spec]}{HNAME[h]}Est", signed(t["estimate"], 4)); put(f"Rob{SPEC[spec]}{HNAME[h]}P", ptxt(t["p_one_sided_wild"])); put(f"Rob{SPEC[spec]}{HNAME[h]}N", f"{t['n']:,}")
            put(f"Rob{SPEC[spec]}{HNAME[h]}Pp", signed(100 * t["estimate"], 2))  # same estimate in percentage points
    n_h1_sig = sum(1 for rb in K["robustness"].values() if rb["tests"]["H1"]["estimate"] > 0 and rb["tests"]["H1"]["p_one_sided_wild"] < 0.05)
    put("RobHOneSigCount", str(n_h1_sig)); put("RobSpecCount", str(len(K["robustness"])))
    for h in ("H1", "H2", "H2_objective", "H3", "H4", "H5", "H6"):  # sign and significance counts over the pre-registered robustness specifications
        ests = [rb["tests"][h]["estimate"] for rb in K["robustness"].values()]; ps = [rb["tests"][h]["p_one_sided_wild"] for rb in K["robustness"].values()]
        put(f"Rob{HNAME[h]}PosCount", str(sum(1 for e in ests if e > 0))); put(f"Rob{HNAME[h]}NegCount", str(sum(1 for e in ests if e < 0)))
        put(f"Rob{HNAME[h]}SigCount", str(sum(1 for e, p_ in zip(ests, ps) if e > 0 and p_ < 0.05))); put(f"Rob{HNAME[h]}MinP", ptxt(min(ps)))
    perm = J("results", "06_kis_main_permute.json")
    if perm:
        nr = perm["known_truth"]["null_rejection_rates_nominal_0.05"]
        put("PermHSixClusterT", rnd(nr["H6"]["cluster_t_two_sided"], 2)); put("PermHSixWild", rnd(nr["H6"]["wild_two_sided"], 2))
        put("PermHTwoObjClusterT", rnd(nr["H2_objective"]["cluster_t_two_sided"], 2)); put("PermHTwoObjWild", rnd(nr["H2_objective"]["wild_two_sided"], 2)); put("PermDraws", str(perm["known_truth"]["n_permutations"]))
    sim = J("results", "06_kis_main_simulate.json")
    if sim:
        put("SimHOneEst", signed(sim["main"]["tests"]["H1"]["estimate"], 4)); put("SimHTwoEst", signed(sim["main"]["tests"]["H2"]["estimate"], 4)); put("SimTrueHOne", rnd(sim["known_truth"]["true_b_g2_preempt"], 2)); put("SimTrueHTwo", rnd(sim["known_truth"]["true_b_g0_quit"], 2))

    # ---------------------------------------------------------------- exploratory
    E = J("results", "07_kis_exploratory.json")
    put("ExplGapOneQuitEst", signed(E["gap1_quit_x_g1"]["estimate"], 4)); put("ExplGapOneQuitP", ptxt(E["gap1_quit_x_g1"]["p_two_sided_wild"]))
    put("ExplGapOnePreEst", signed(E["gap1_preempt_x_g1"]["estimate"], 4)); put("ExplGapOnePreP", ptxt(E["gap1_preempt_x_g1"]["p_two_sided_wild"]))
    for y, nm in (("quit_any", "Quit"), ("preempt_strategy", "Pre")):
        for g in ("g0", "g2"):
            put(f"Sigma{nm}{camel(g)}Est", signed(E[f"sigma_item_{y}"][g]["estimate"], 4)); put(f"Sigma{nm}{camel(g)}P", ptxt(E[f"sigma_item_{y}"][g]["p_two_sided_wild"]))
    mf = E["market_first_main_heckman2step"]
    if "x_g2" in mf:
        put("MarketFirstGTwoEst", signed(mf["x_g2"]["estimate"], 4)); put("MarketFirstGTwoP", ptxt(mf["x_g2"]["p_two_sided_wild"])); put("MarketFirstN", f"{mf['n_outcome']:,}"); put("MarketFirstNSel", f"{mf['n_selection']:,}")
    G = J("results", "07b_robustness_gap_proxy.json")
    if G:
        for h in ("H1", "H2", "H3", "H4", "H5", "H6"):
            t = G["tests"][f"{h}_alt"]; put(f"Alt{HNAME[h]}Est", signed(t["estimate"], 4)); put(f"Alt{HNAME[h]}P", ptxt(t["p_one_sided_wild"]))
        put("AltHOnePreregSameSubEst", signed(G["tests"]["H1_prereg_proxy_same_subsample"]["estimate"], 4)); put("AltHOnePreregSameSubP", ptxt(G["tests"]["H1_prereg_proxy_same_subsample"]["p_one_sided_wild"]))
        put("AltN", f"{G['n_innov_active_with_alt']:,}")

    # ---------------------------------------------------------------- transcripts
    T = J("results", "08_transcript_codes.json")
    if T and T.get("agreement"):
        put("CodesN", f"{T['n_coded_by_both']:,}"); put("CodesNReasons", f"{T['n_reasons']:,}")
        put("CodesPrimaryAgreePct", pct(T["agreement"]["primary"]["percent"]))
        ks = [v["kappa"] for k, v in T["agreement"].items() if k != "primary" and v.get("kappa") == v.get("kappa")]
        put("CodesKappaMin", rnd(min(ks), 2)); put("CodesKappaMax", rnd(max(ks), 2)); put("CodesKappaMedian", rnd(sorted(ks)[len(ks) // 2], 2))
        for cat, v in T["agreement"].items():
            if cat != "primary":
                put(f"Kappa{camel(cat)}", rnd(v["kappa"], 2))  # macro names cannot contain digits (KappaMOne ... KappaMTen)
        for st in ("A", "B"):
            for cat, share in T["shares"][st]["consensus"].items():
                put(f"Share{st}{camel(cat)}Pct", pct(share))
            for dec, d in T["shares"][st]["by_decision"].items():
                for cat, share in d.items():
                    if cat != "n":
                        put(f"Share{st}{dec}{camel(cat)}Pct", pct(share))
        put("ShareIrrelevantAttrPct", pct(max(v["share_either_judge"] for v in T["irrelevant_attribute_by_placebo"].values()), 2))
        put("ShareFirmAttrPct", pct(T["firm_attributes_share_either_judge"], 1))
        put("FirmAttrCount", str(round(T["firm_attributes_share_either_judge"] * T["n_coded_by_both"])))  # reasons citing firm attributes (either judge)
        # threat_hurry among accelerate decisions in threat cells vs no-threat cells (Stage A), pooled over gaps
        def pooled_share(stage, dec, thr, cat):
            rows = [(v["n"], v[cat]) for k, v in T["by_stage_decision_threat"].items() if k.startswith(f"{stage}:{dec}:threat{thr}:")]
            n = sum(r[0] for r in rows); return (sum(r[0] * r[1] for r in rows) / n) if n else None
        put("ShareAAccelThreatHurryPct", pct(pooled_share("A", "A", 1, "threat_hurry"))); put("ShareAQuitThreatQuitPct", pct(pooled_share("A", "Q", 1, "threat_quit")))
        put("ShareBAccelThreatHurryPct", pct(pooled_share("B", "A", 1, "threat_hurry"))); put("ShareBQuitThreatQuitPct", pct(pooled_share("B", "Q", 1, "threat_quit")))
    else:
        for k in ("CodesN", "CodesPrimaryAgreePct", "CodesKappaMin", "CodesKappaMax", "ShareAAccelThreatHurryPct", "ShareAQuitThreatQuitPct"):
            put(k, None)

    # ---------------------------------------------------------------- registration / redaction / facts
    R = J("prereg", "REGISTERED.json")
    put("OSFRegistrationURL", R["osf_url"]); put("OSFRegistrationId", R["osf_registration_id"]); put("OSFRegisteredDate", R["registered_at"][:10]); put("OSFRegisteredKST", R["registered_at_kst"][:16].replace("T", " "))
    put("OSFEmbargoEnd", (R.get("embargo_end_date") or "")[:10] or None)
    red = J("results", "09_persona_redaction.json")
    if red:
        put("PersonasUniqueInKIS", str(red["exact_attributes"]["unique_in_kis_sample"])); put("PersonasKLeThree", str(red["exact_attributes"]["k_le_3"])); put("PublicPersonaMinK", str(red["public_table_sector_size3_age4"]["min_k"]))
    facts = J("docs", "INSTITUTIONAL_FACTS_escape_or_exit.json")
    put("KISApprovalNo", "395001"); put("KISSinceYear", "1996")
    FV = {f["id"]: f.get("values", {}) for f in facts["facts"]}
    r10 = FV.get("RSTA-10-RD-CREDIT", {}); s1 = FV.get("SMESA-1-PURPOSE", {})
    put("LawRSTAActNo", r10.get("act_number")); put("LawRSTAEffective", r10.get("effective")); put("LawRSTAArticle", r10.get("article"))
    put("LawRSTASMECurrentPct", r10.get("sme_current_pct")); put("LawRSTASMEIncrementPct", r10.get("sme_increment_pct")); put("LawRSTAMidCurrentPct", r10.get("mid_current_pct"))
    put("LawRSTAMidIncrementPct", r10.get("mid_increment_pct")); put("LawRSTALargeCapPct", r10.get("large_cap_pct"))
    put("LawSMESAActNo", s1.get("act_number")); put("LawSMESAEffective", s1.get("effective")); put("LawSMESAStartupYears", s1.get("startup_years")); put("LawSMESARegArticle", FV.get("SMESA-21-REGULATION", {}).get("article"))

    # ---------------------------------------------------------------- manuscript additions (Task 12, 2026-11-10)
    # gap3 group sizes by wave and pooled (01_build_summary.json waves[w].columns.gap3.value_counts)
    gtot = {"0": 0, "1": 0, "2": 0}
    for w in ("2022M", "2023S", "2024M", "2025S"):
        vc = build["waves"][w]["columns"]["gap3"]["value_counts"]
        for g, nm in (("0", "Zero"), ("1", "One"), ("2", "Two")):
            n_g = int(vc.get(f"{g}.0", vc.get(g, 0))); gtot[g] += n_g
            put(f"Gap{nm}N{camel(w)}", f"{n_g:,}")
    for g, nm in (("0", "Zero"), ("1", "One"), ("2", "Two")):
        put(f"Gap{nm}N", f"{gtot[g]:,}")  # pooled over the four waves
    # share of firms reporting 0 % dedicated R&D staff, by wave (02_marginals.json C_gap_proxies[w].share_zero)
    for w in ("2022M", "2023S", "2024M", "2025S"):
        put(f"ShareZeroRD{camel(w)}Pct", pct(marg["C_gap_proxies"][w]["share_zero"], 0))
    manu = [marg["C_gap_proxies"][w]["share_zero"] for w in ("2022M", "2024M")]  # scope: the two manufacturing waves
    serv = [marg["C_gap_proxies"][w]["share_zero"] for w in ("2023S", "2025S")]  # scope: the two services waves
    put("ShareZeroRDManuMinPct", pct(min(manu), 0)); put("ShareZeroRDManuMaxPct", pct(max(manu), 0))
    put("ShareZeroRDServMinPct", pct(min(serv), 0)); put("ShareZeroRDServMaxPct", pct(max(serv), 0))
    # Stage A template history (v1 ceiling pilot; v2 head-office placebo full run and its diagnosis)
    V1 = J("results", "04_agent_stage_a_v1_pilot_ceiling.json")
    if V1:
        acc = [v["overall"]["p_accel"] for v in V1["by_model_lang"].values()]  # scope: the four model x language arms
        put("VOnePilotCalls", f"{V1['n_calls']:,}"); put("VOneAccelMinPct", pct(min(acc), 0)); put("VOneAccelMaxPct", pct(max(acc), 0))
    V2 = J("results", "04_agent_stage_a_v2_placebo_headoffice.json"); D2 = J("results", "04_stage_a_v2_placebo_diagnosis.json")
    if V2 and D2:
        put("VTwoCalls", f"{V2['n_calls']:,}")
        q0 = list(D2["gap0_quit_ceiling"].values())  # scope: gap-0 quit share, four arms
        put("VTwoGapZeroQuitMin", rnd(min(q0), 2)); put("VTwoGapZeroQuitMax", rnd(max(q0), 2))
        put("VTwoPlaceboShareMin", rnd(D2["placebo_share_range"][0], 3)); put("VTwoPlaceboShareMax", rnd(D2["placebo_share_range"][1], 3))
        fa = D2["arms"]["fable/en"]["is_A"]
        put("VTwoFableEnMarginal", signed(fa["marginal_contrast"], 3)); put("VTwoFableEnStratified", signed(fa["stratified_contrast"], 3)); put("VTwoFableEnStratifiedP", ptxt(fa["ols_p"]))
        put("VTwoPooledAccelP", ptxt(D2["pooled_accel"]["p"]))
    # Stage B parse failures by arm (05_agent_stage_b.json by_model_lang[arm].n_parse_failed)
    for arm, v in B["by_model_lang"].items():
        put(f"StageBFailed{ARM[arm]}", str(v.get("n_parse_failed", 0)))
    # unadjusted pooled outcome rates by gap3 group, from the exploratory cell tables (07_kis_exploratory.json cell_tables; n-weighted over terciles)
    for key, nm in (("quit_any_by_gap3_x_thr_terc", "RawQuit"), ("preempt_strategy_by_gap3_x_thr_terc", "RawPre")):
        rows = E["cell_tables"][key]
        for g, gl in ((0, "GZero"), (1, "GOne"), (2, "GTwo")):
            rr = [r_ for r_ in rows if r_["gap3"] == g]
            n_g = sum(r_["n"] for r_ in rr)
            put(f"{nm}{gl}Pct", pct(sum(r_["mean"] * r_["n"] for r_ in rr) / n_g, 1))  # scope: all threat terciles within the gap group
            for terc, tl in ((0, "Low"), (1, "Mid"), (2, "High")):
                c = next(r_ for r_ in rr if r_["tercile"] == terc)
                put(f"{nm}{gl}{tl}Pct", pct(c["mean"], 1)); put(f"{nm}{gl}{tl}N", f"{c['n']:,}")
    _pre_rows = E["cell_tables"]["preempt_strategy_by_gap3_x_thr_terc"]; _g2 = [r_ for r_ in _pre_rows if r_["gap3"] == 2]
    _g2_rate = sum(r_["mean"] * r_["n"] for r_ in _g2) / sum(r_["n"] for r_ in _g2)  # scope: frontier group, all threat terciles
    put("KISHOneRelFrontierPct", pct(M["tests"]["H1"]["estimate"] / _g2_rate, 0))
    # robustness bootstrap draws
    put("RobNBoot", str(K["robustness"]["weighted"]["tests"]["H1"]["n_boot"]))
    # environment tie prize as an integer (65억원)
    put("EnvPrizeTieInt", str(round((env["V"] + env["W"]) / 2 * 100)))
    # exploratory gap-proxy robustness: cross-tabulation diagonal
    if G:
        ct = G["crosstab_gap3_vs_alt"]
        put("AltDiagGZero", f"{ct['gap3=0']['alt=0']:,}"); put("AltDiagGOne", f"{ct['gap3=1']['alt=1']:,}"); put("AltDiagGTwo", f"{ct['gap3=2']['alt=2']:,}")
    # transcript coding: reasons per stage (08_transcript_codes.json shares[stage].by_decision[*].n)
    if T and T.get("agreement"):
        for st in ("A", "B"):
            put(f"Stage{st}Reasons", f"{sum(d['n'] for d in T['shares'][st]['by_decision'].values()):,}")
    # disclosure control: redacted prompts and responses (09_persona_redaction.json)
    if red:
        put("RedactedPrompts", f"{sum(f['prompts_redacted'] for f in red['files'].values()):,}")
        put("RedactedResponses", str(red["responses_with_attribute_echo_redacted"]))
    put("OSFProjectURL", R["project_url"])
    # ---------------------------------------------------------------- cross-review additions (2026-11-11)
    put("StageAParsed", f"{A['n_calls'] - sum(v for k, v in A['parse_status'].items() if k != 'ok'):,}")
    for w in ("2022M", "2023S", "2024M", "2025S"):  # share rating the entry-threat item 4 or 5 ('high'/'very high')
        put(f"ShareThreatHigh{camel(w)}Pct", pct(marg["B_market_environment_items"]["by_wave"][w]["ME4"]["share_4_or_5"], 0))
    # environment amounts in billion won (1 model unit = 100억원 = 10 billion won)
    put("EnvContinueCostBn", rnd(env["cC"] * 10, 1)); put("EnvAccelCostBn", rnd(env["cA"] * 10, 1)); put("EnvDraftAccelCostBn", rnd(cal["draft_cA_was"] * 10, 1))
    put("EnvPrizeFirstBn", str(round(env["V"] * 10))); put("EnvPrizeSecondBn", str(round(env["W"] * 10))); put("EnvPrizeTieBn", rnd((env["V"] + env["W"]) / 2 * 10, 1))
    JS = J("results", "08b_transcript_judge_shares.json")
    if JS:
        sh = JS["shares"]
        for key, nm in (("A:Q:M3", "AStopThreatQuit"), ("A:A:M2", "AAccelThreatHurry"), ("B:Q:M3", "BStopThreatQuit"), ("B:A:M2", "BAccelThreatHurry")):
            put(f"Judge{nm}FablePct", pct(sh[key]["share_fable"], 1)); put(f"Judge{nm}GptPct", pct(sh[key]["share_gpt56"], 1)); put(f"Judge{nm}N", f"{sh[key]['n_threat_cell_decisions']:,}")
    EX = J("results", "08c_example_reasons.json")
    if EX:
        def tex_text(s):
            # the writer below escapes %, _ and < itself; here only the characters it does not handle
            return (s.replace("\\", "\\textbackslash{}").replace("~", "\\textasciitilde{}").replace("&", "\\&").replace("#", "\\#")
                     .replace("≈", "$\\approx$").replace("–", "--").replace("—", "---").replace("“", "``").replace("”", "''").replace("’", "'"))
        armname = {"fable": "Claude fable-5", "gpt56": "GPT-5.6"}
        for key, nm in (("accelerate_frontier_threat", "Accel"), ("stop_laggard_threat", "Stop"), ("continue_level_nothreat", "Cont")):
            e = EX["examples"][key]
            put(f"ExReason{nm}", tex_text(e["reason_public_log"])); put(f"ExReason{nm}Arm", f"{armname[e['model']]}, {e['lang'].upper()}"); put(f"ExReason{nm}Id", e["design_id"])
    SG = J("results", "07c_sector_gap_counts.json")
    if SG:
        for sec, sn in (("manufacturing", "Manu"), ("services", "Serv")):
            for g, gn in ((0, "Zero"), (1, "One"), (2, "Two")):
                c = SG["counts"][f"{sec}:g{g}"]
                put(f"SecGapN{sn}{gn}", f"{c['n_firms']:,}"); put(f"SecGapPreEvents{sn}{gn}", f"{c['preempt_events']:,}"); put(f"SecGapPreRate{sn}{gn}Pct", pct(c["preempt_rate"], 1))
                put(f"SecGapNInnov{sn}{gn}", f"{c['n_innov_active']:,}"); put(f"SecGapQuitEvents{sn}{gn}", f"{c['quit_events']:,}"); put(f"SecGapQuitRate{sn}{gn}Pct", pct(c["quit_rate"], 1))
    ER = J("results", "06b_entry_rate_extremes.json")
    if ER:
        # English renderings of the KSIC division titles printed in the KIS codebooks (item_map register INDUSTRY2 values);
        # the Korean title from the JSON must match the one recorded here, otherwise the macro is a RESULTS-GAP.
        KSIC_EN = {10: ("식료품 제조업", "food products"), 18: ("인쇄 및 기록매체 복제업", "printing and reproduction of recorded media"),
                   19: ("코크스, 연탄 및 석유정제품 제조업", "coke, briquettes and refined petroleum products"), 31: ("기타 운송장비 제조업", "other transport equipment"),
                   51: ("항공 운송업", "air transport"), 63: ("정보서비스업", "information services"), 86: ("보건업", "human health"), 87: ("사회복지 서비스업", "social work services")}
        for w in ("2022M", "2023S", "2024M", "2025S"):
            e = ER["extremes"][w]
            put(f"EntryMinInd{camel(w)}", str(e["min"]["industry2"])); put(f"EntryMaxInd{camel(w)}", str(e["max"]["industry2"]))
            put(f"EntryMinInd{camel(w)}Pct", rnd(e["min"]["entry_rate_pct"], 1)); put(f"EntryMaxInd{camel(w)}Pct", rnd(e["max"]["entry_rate_pct"], 1))
            for side in ("min", "max"):
                code, ko = e[side]["industry2"], e[side]["label_ko"]
                en = KSIC_EN.get(code)
                put(f"Entry{side.capitalize()}Ind{camel(w)}Label", en[1] if en and en[0] == ko else None)
    # counts that the prose reconciles (cross-review 2026-11-11): reasons by stage (all sent to the judges) and those coded by both judges
    if T and T.get("agreement") and JS and JS.get("matches_08_transcript_codes_n_reasons"):
        put("StageAReasonsAll", f"{JS['n_reasons_by_stage']['A']:,}"); put("StageBReasonsAll", f"{JS['n_reasons_by_stage']['B']:,}")
        put("CodesNotBothJudged", str(T["n_reasons"] - T["n_coded_by_both"]))
    else:
        put("StageAReasonsAll", None); put("StageBReasonsAll", None); put("CodesNotBothJudged", None)
    # exploratory treatment-construction check (code/robustness_threat_residual.py -> results/07d_robustness_threat_residual.json)
    TR = J("results", "07d_robustness_threat_residual.json")
    if TR:
        put("ThreatResidSDPooled", rnd(TR["registered_resid_sd"]["pooled"], 3))
        for w, v in TR["registered_resid_sd"]["by_wave"].items():
            put(f"ThreatResidSD{camel(w)}", rnd(v, 2))
        put("ThreatResidCorrMeanEight", rnd(TR["corr_registered_vs_mean8"], 2)); put("ThreatResidCorrMeanSeven", rnd(TR["corr_registered_vs_mean7"], 2))
        for key, nm in (("mean8", "MeanEight"), ("mean7", "MeanSeven")):
            for h in ("H1", "H2", "H3", "H4", "H5"):
                t = TR["variants"][key]["tests"][h]
                put(f"Resid{nm}{HNAME[h]}Pp", signed(100 * t["estimate"], 2)); put(f"Resid{nm}{HNAME[h]}P", ptxt(t["p_one_sided_wild"]))
                put(f"Resid{nm}{HNAME[h]}LoPp", signed(100 * t["ci95_wild"][0], 2)); put(f"Resid{nm}{HNAME[h]}HiPp", signed(100 * t["ci95_wild"][1], 2))
    else:
        for k in ("ThreatResidSDPooled", "ResidMeanEightHOnePp", "ResidMeanSevenHOnePp"):
            put(k, None)
    # H1 robustness count over DISTINCT pre-emption specifications (the two quit-definition rows re-run the identical pre-emption model)
    main_h1 = K["main"]["tests"]["H1"]["estimate"]
    distinct = {k: v for k, v in K["robustness"].items() if abs(v["tests"]["H1"]["estimate"] - main_h1) > 1e-12 or k not in ("exit_strict", "exit_full")}
    put("RobHOneDistinctSpecCount", str(len(distinct)))
    put("RobHOneDistinctSigCount", str(sum(1 for v in distinct.values() if v["tests"]["H1"]["estimate"] > 0 and v["tests"]["H1"]["p_one_sided_wild"] < 0.05)))
    put("RobHOneDistinctMaxSigP", ptxt(max(v["tests"]["H1"]["p_one_sided_wild"] for k, v in distinct.items() if k != "services_only")))
    # agent run metadata (results/04b_agent_run_metadata.json: Bedrock model identifiers from the client module; call-time span from the logs)
    RM = J("results", "04b_agent_run_metadata.json")
    if RM:
        put("ModelIdFable", RM["models"]["fable"]["id"]); put("ModelIdGpt", RM["models"]["gpt56"]["id"])
        put("ModelRegionFable", RM["models"]["fable"]["region"]); put("ModelRegionGpt", RM["models"]["gpt56"]["region"])
        for st in ("A", "B"):
            c = RM["calls"][st]
            put(f"Stage{st}CallsDate", c["first"][:10]); put(f"Stage{st}CallsFirstKST", c["first"][11:16]); put(f"Stage{st}CallsLastKST", c["last"][11:16]); put(f"Stage{st}LogRecords", f"{c['n_log_records']:,}")
    else:
        for k in ("ModelIdFable", "ModelIdGpt", "StageACallsDate", "StageBCallsDate"):
            put(k, None)
    # client probe before the experiments (agent_experiment/probes/probe_clients_20261110.json): content-free three-option prompt, first call + repeats
    PR = J("agent_experiment", "probes", "probe_clients_20261110.json")
    if PR:
        for key, nm in (("fable", "Fable"), ("gpt56", "Gpt")):
            calls = [PR[key]["raw_head"]] + PR[key]["repeats"]
            first = sum(1 for c in calls if json.loads(c)["decision"] == "A")
            put(f"Probe{nm}FirstOption", str(first)); put(f"Probe{nm}Calls", str(len(calls)))
    if EX:
        put("ExReasonStopFirst", tex_text(EX["examples"]["stop_laggard_threat"]["reason_public_log"].split(". ")[0] + "."))
    # numerical model check (code/model_check.py -> results/model_check.json; Appendix A)
    MC = J("results", "model_check.json")
    if MC:
        tp = MC["two_period_analytic_case"]; ce = MC["calibrated_environment"]
        put("ModelCheckTwoRouteGap", f"{tp['two_route_max_value_gap']:.0e}".replace("e-", "e-"))
        put("ModelCheckThetaStar", rnd(tp["theta_star_laggard_quits_with_certainty_from"], 2)); put("ModelCheckThetaTwoStar", rnd(tp["theta_2star_leader_accelerates_with_certainty_from"], 2))
        put("ModelCheckTwoPeriodQuitAtZero", rnd(tp["P_quit_F_threat"][0], 2)); put("ModelCheckTwoPeriodAccelAtZero", rnd(tp["P_accel_L_threat"][0], 2))
        put("ModelCheckThetaGridMax", rnd(tp["theta_grid"][-1], 2))
        L = ce["leader_one_stage_ahead"]["derivatives"]; F = ce["laggard_one_stage_behind"]["derivatives"]
        put("ModelCheckLeaderAccelCondZero", rnd(L["P_accel_cond"]["at_theta_0"], 2)); put("ModelCheckLeaderAccelCondSeven", rnd(L["P_accel_cond"]["at_theta_07"], 2))
        put("ModelCheckLeaderAccelUncondZero", rnd(L["P_accel_uncond"]["at_theta_0"], 2)); put("ModelCheckLeaderAccelUncondSeven", rnd(L["P_accel_uncond"]["at_theta_07"], 2))
        put("ModelCheckLaggardQuitUncondZero", rnd(F["P_quit_uncond"]["at_theta_0"], 2)); put("ModelCheckLaggardQuitUncondSeven", rnd(F["P_quit_uncond"]["at_theta_07"], 2))
        put("ModelCheckLeaderQuitUncondZero", rnd(L["P_quit_uncond"]["at_theta_0"], 2))
        put("ModelCheckAllPass", "pass" if MC["pass"] else "fail")

    # ---------------------------------------------------------------- write
    out = {"built": time.strftime("%Y-%m-%d %H:%M %Z"), "n_macros": len(N), "results_gaps": gaps, "macros": N}
    json.dump(out, open(os.path.join(PAPER, "numbers.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(PAPER, "numbers.tex"), "w", encoding="utf-8") as f:
        f.write(f"% generated {out['built']} by code/make_numbers.py — do not edit; {len(N)} macros; gaps: {len(gaps)}\n")
        for k, v in N.items():
            v = v.replace("%", "\\%").replace("_", "\\_").replace("<", "$<$")
            f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
    print(f"{len(N)} macros -> paper/numbers.tex; gaps {len(gaps)}: {gaps[:12]}")


if __name__ == "__main__":
    main()
