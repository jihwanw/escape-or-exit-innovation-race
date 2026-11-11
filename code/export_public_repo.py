#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""export_public_repo.py — build the clean public reproduction package (Task 13).

The working repository's history contains the unredacted agent logs and the persona file (individual KIS register attributes),
so the public repository is a fresh export with no history, not a push of this repository. What is exported:
  code/ model/ prereg/ (registration package without OSF state/keys) agent_experiment/ (scripts, prompts, designs, probes,
  logs_public/) public/personas_public.csv item_maps/*.json data/ (KOSIS aggregates + provenance) results/ (aggregate JSON/CSV,
  minus the manual-validation sample drawn from the raw logs) docs/ (hypotheses, model predictions, variable table, pilot
  marginals, external indicators, three-way table, literature map, fact cards, law texts, CIS excerpt) paper/ (LaTeX sources,
  numbers, bib, figures, table PDFs; no built manuscript PDFs, no review files).
Never exported: KIS microdata (not in this repo either), agent_experiment/logs/ (unredacted), agent_experiment/stage_a_personas.csv,
results/08_validation_sample_50.csv, item_maps/questionnaire_text_*.txt and the KIS questionnaire dump (STEPI documents),
docs/sources/RP_guide*, docs/abstracts.json and the abstract caches (third-party text), docs/JOURNAL_FACTS.md,
docs/RP_EDITORIAL_VOICE_PROFILE.md, prereg/osf_state.json, prereg/osf_view_only_links.json (access keys), RESEARCH_PLAN.md,
SESSION_LOG.md, paper/reviews/, paper/*.pdf, paper/title_page.tex, paper/cover_letter*.

After copying, every exported text file is scanned for (a) the persona attribute blocks and industry labels of the private
persona file, (b) persona rows with exact attributes, (c) credential patterns. Any hit aborts the export.

Usage: python code/export_public_repo.py --out ../Escape_or_Exit_public [--force]
"""
import argparse
import os
import re
import shutil
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

INCLUDE_DIRS = {
    "code": lambda f: f.endswith(".py"),
    "model": lambda f: not f.endswith(".pyc") and "__pycache__" not in f,
    "agent_experiment/prompts": lambda f: f.endswith(".py"),
    "agent_experiment/probes": lambda f: f.endswith(".json"),
    "agent_experiment/logs_public": lambda f: f.endswith((".jsonl", ".csv", ".py", ".json", ".md")),
    "public": lambda f: f.endswith(".csv"),
    "data": lambda f: f.endswith((".csv", ".json")),
    "results": lambda f: f.endswith((".json", ".csv")) and f != "08_validation_sample_50.csv",
    "paper/figures": lambda f: f.endswith((".pdf", ".png")),
    "paper/tables_tex": lambda f: f.endswith((".tex", ".pdf")),
    "docs/sources/law": lambda f: f.endswith(".txt"),
}
INCLUDE_FILES = [
    "agent_experiment/INTERFACE_CARD_llm_clients.md", "agent_experiment/calibrate_env.py", "agent_experiment/code_transcripts.py",
    "agent_experiment/controls_stage_b.py", "agent_experiment/diagnose_stage_a_v2_placebo.py", "agent_experiment/race_env.py",
    "agent_experiment/run_stage_a.py", "agent_experiment/run_stage_b.py", "agent_experiment/llm_clients.py", "agent_experiment/stage_a_design.csv",
    "agent_experiment/stage_b_design.csv",
    "prereg/PREREGISTRATION.md", "prereg/REGISTERED.json", "prereg/SHA256SUMS.txt", "prereg/agent_predictions_v1.json",
    "prereg/build_agent_predictions.py", "prereg/make_prereg_doc.py", "prereg/osf_register.py", "prereg/osf_registration_responses.json",
    "item_maps/item_map_2022M.json", "item_maps/item_map_2023S.json", "item_maps/item_map_2024M.json", "item_maps/item_map_2025S.json",
    "item_maps/item_map_escape_exit.json",
    "docs/HYPOTHESES_GATE_B.md", "docs/MODEL_PREDICTIONS.md", "docs/VARIABLE_TABLE.md", "docs/PILOT_MARGINALS.md",
    "docs/EXTERNAL_INDICATORS.md", "docs/THREEWAY_TABLE.md", "docs/LITERATURE_MAP.md", "docs/REFS_TABLE.md",
    "docs/INSTITUTIONAL_FACTS_escape_or_exit.json", "docs/CIS2020_items_excerpt.txt",
    "paper/main.tex", "paper/main_blinded.tex", "paper/numbers.tex", "paper/numbers.json", "paper/refs.bib", "paper/refs_manual.bib",
    "paper/highlights.tex",
]
NEVER = ["agent_experiment/logs/", "agent_experiment/stage_a_personas.csv", "results/08_validation_sample_50.csv",
         "questionnaire_text_", "KIS_2024_manufacturing_questionnaire", "RP_guide", "abstracts", "JOURNAL_FACTS", "RP_EDITORIAL",
         "osf_state.json", "osf_view_only_links.json", "check_journal_facts.py", "fetch_abstracts.py", "check_literature_map.py", "build_refs.py", "RESEARCH_PLAN.md", "SESSION_LOG.md", "paper/reviews/", "title_page",
         "cover_letter", "review_links", "editor_links", "analysis_panel.parquet"]
CRED = re.compile(r"(Bearer\s+[A-Za-z0-9_\-]{12,}|api[_-]?key\s*[=:]\s*['\"]?[A-Za-z0-9]{12,}|PGPASSWORD=\S+|ghp_[A-Za-z0-9]{20,}|view_only=[0-9a-f]{32})")


def copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True); ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    if os.path.exists(out):
        if not a.force:
            sys.exit(f"{out} exists; use --force to replace its exported files")
        for name in os.listdir(out):
            if name == ".git":
                continue
            p = os.path.join(out, name)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    exported = []
    for rel, keep in INCLUDE_DIRS.items():
        base = os.path.join(ROOT, rel)
        for dirpath, _, files in os.walk(base):
            if "__pycache__" in dirpath:
                continue
            for f in files:
                src = os.path.join(dirpath, f); r = os.path.relpath(src, ROOT)
                if keep(f) and not any(n in r for n in NEVER):
                    copy(src, os.path.join(out, r)); exported.append(r)
    for r in INCLUDE_FILES:
        src = os.path.join(ROOT, r)
        if not os.path.exists(src):
            sys.exit(f"missing expected file: {r}")
        if any(n in r for n in NEVER):
            sys.exit(f"file in NEVER list requested: {r}")
        copy(src, os.path.join(out, r)); exported.append(r)
    # ---- leak scan
    # A KSIC division title on its own is a public classification label (codebooks, KOSIS tables, results name them); the
    # disclosure risk is the filled persona block (industry + size + exact age + affiliation) or a persona row with exact
    # attributes. Template placeholders such as "- 업종: {industry_label}" are not values.
    per = pd.read_csv(os.path.join(ROOT, "agent_experiment", "stage_a_personas.csv"))
    exact_rows = [re.compile(r"^%s,%s,%s,%s," % (r.persona_id, r.wave, r.sector, r.industry2), re.M) for r in per.itertuples()]
    patterns = exact_rows + [
        re.compile(r"\[회사\]\n- 업종: (?!\{)"), re.compile(r"\[Company\]\n- Industry \([^)]*\): (?!\{)"),
        re.compile(r"Founded \d+ years ago"), re.compile(r"설립 후 \d+년")]
    hits = []
    for r in sorted(set(exported)):
        p = os.path.join(out, r)
        if r.endswith((".pdf", ".png", ".parquet")):
            continue
        try:
            txt = open(p, encoding="utf-8", errors="replace").read()
        except Exception as e:  # noqa
            hits.append((r, f"unreadable: {e}")); continue
        for pat in patterns:
            m = pat.search(txt)
            if m:
                hits.append((r, f"persona attribute pattern {pat.pattern[:40]!r}")); break
        m = CRED.search(txt) if not r.endswith("export_public_repo.py") else None
        if m:
            hits.append((r, f"credential pattern {m.group(0)[:20]!r}"))
    print(f"exported {len(set(exported))} files to {out}")
    if hits:
        for r, why in hits:
            print("[LEAK]", r, "—", why)
        sys.exit("export aborted: remove or redact the files above")
    print("leak scan: 0 hits (filled persona blocks, exact persona rows, attribute echoes, credentials)")
    home = sum(1 for r in set(exported) if not r.endswith((".pdf", ".png")) and "/Users/jihwanw" in open(os.path.join(out, r), encoding="utf-8", errors="replace").read())
    print(f"note: {home} exported text files mention a local home path (harmless; listed for tidiness)")


if __name__ == "__main__":
    main()
