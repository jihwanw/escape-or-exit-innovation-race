#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_public_readme.py — write README.md, CITATION.cff, .zenodo.json, LICENSE and .gitignore for the public reproduction
package produced by code/export_public_repo.py. Every count in the README is read from paper/numbers.tex (macros built by
code/make_numbers.py from results/*.json); nothing numeric is typed here. The manuscript title is read from paper/main.tex.

Usage: python code/make_public_readme.py --out ../Escape_or_Exit_public [--version-doi 10.5281/zenodo.NNN --concept-doi 10.5281/zenodo.MMM]
"""
import argparse
import datetime as dt
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = "https://github.com/jihwanw/escape-or-exit-innovation-race"
TAG = "v1.0-submission"


def macros():
    tex = open(os.path.join(ROOT, "paper", "numbers.tex"), encoding="utf-8").read()
    return dict(re.findall(r"\\newcommand\{\\([A-Za-z]+)\}\{(.*)\}", tex))


def title():
    tex = open(os.path.join(ROOT, "paper", "main.tex"), encoding="utf-8").read()
    tex = re.sub(r"(?<!\\)%.*", "", tex)                      # drop comments (one mentions "\title{}")
    m = re.search(r"^\\title\{([^}]+)\}", tex, re.M)
    return m.group(1).strip()


MIT = """MIT License

Copyright (c) {year} Jihwan Woo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True); ap.add_argument("--version-doi", default=""); ap.add_argument("--concept-doi", default="")
    a = ap.parse_args()
    out = os.path.abspath(a.out); M = macros(); T = title(); year = dt.date.today().year
    vdoi, cdoi = a.version_doi.strip(), a.concept_doi.strip()
    doi_line = (f"- `{TAG}`: the archived submission release; Zenodo version DOI: {vdoi} (https://doi.org/{vdoi})."
                + (f" Concept DOI (always resolves to the latest version): {cdoi}." if cdoi else "")) if vdoi else \
        f"- `{TAG}`: the archived submission release (Zenodo version DOI to be added to this line when the archive is minted)."
    readme = f"""# {T}

Reproduction package for the manuscript of that title (Woo, {year}; single author; prepared for submission to *Research Policy*).

The paper derives two margins of an innovation race from a finite-horizon model with a technology gap and a stochastic entrant
(pre-emption by firms close to completion, abandonment by firms far from it), freezes the comparative statics of the model and the
choices of two LLM agents as pre-registered predictions, and tests six hypotheses on four waves of the Korean Innovation Survey
({M['NFirms']} firms; {M['NQuitSample']} with innovation activity). This repository holds the code that built every number,
table and figure in the manuscript, the aggregate result files those numbers come from, the agent prompts and the redacted agent
logs, the audited survey item maps and the pre-registration package. The licensed survey microdata are not included.

## Pre-registration
Registered on the Open Science Framework on {M['OSFRegisteredKST']} KST ({M['OSFRegistrationURL']}; Secondary Data
Preregistration template; project {M['OSFProjectURL']}), embargoed until {M['OSFEmbargoEnd']}. `prereg/PREREGISTRATION.md` is the
registered document, `prereg/agent_predictions_v1.json` the frozen agent and model predictions (SHA-256 in
`prereg/SHA256SUMS.txt`), `prereg/REGISTERED.json` the registration record that `code/analysis_prereg.py` requires before it will
touch a real outcome-by-treatment statistic.

## Data (licensed; not redistributed)
- Korean Innovation Survey (KIS), Science and Technology Policy Institute (STEPI): 2022 and 2024 manufacturing waves, 2023 and 2025
  services waves (research-use provision files `KIS_<year>_배포용(<sector>).xlsx`). Obtain them from STEPI; place them where
  `code/load_kis_escape_exit.py` expects (see its header). The item maps in `item_maps/` record, for every variable used, the
  codebook row, the questionnaire wording and the observed value distribution (`code/build_item_maps.py`).
- Business Demography Statistics, KOSIS table DT_6BD1101 (enterprise birth rates by two-digit industry and year), fetched by
  `code/fetch_entry_rates.py`; the fetched aggregates and their provenance are in `data/`.

## Pipeline (Python 3.13; pandas, numpy, scipy, statsmodels, pyarrow; LaTeX with xelatex for the tables)
```
python model/controls_model.py && python model/run_grid.py && python model/summarise_grid.py     # race model: controls, grid, comparative statics (results/03_*)
python code/build_item_maps.py && python code/load_kis_escape_exit.py && python code/test_panel.py   # item maps -> harmonised panel (needs the KIS files)
python code/fetch_entry_rates.py && python code/merge_external.py                                   # KOSIS entry rates -> panel
python code/marginals_power.py                                                                      # pre-registration marginals and power (no outcome x treatment statistic)
python agent_experiment/calibrate_env.py && python agent_experiment/controls_stage_b.py             # Stage B environment calibrated and controlled before any call
python agent_experiment/run_stage_a.py && python agent_experiment/run_stage_b.py                    # LLM agent experiments (Amazon Bedrock; logs under agent_experiment/logs/)
python prereg/build_agent_predictions.py && python prereg/make_prereg_doc.py                        # frozen predictions and the registration document
python code/analysis_prereg.py --real                                                               # pre-registered confirmatory test (refuses to run without prereg/REGISTERED.json)
python code/robustness_gap_proxy.py && python code/robustness_threat_residual.py && python code/describe_for_manuscript.py   # exploratory and descriptive additions
python agent_experiment/code_transcripts.py                                                         # rubric coding of the agents' reasons by two judge models
python code/make_public_logs.py                                                                     # redacted public copies of the agent logs (agent_experiment/logs_public/, public/personas_public.csv)
python code/make_numbers.py && python code/make_tables.py && python code/make_figures.py            # results JSON -> paper/numbers.tex, paper/tables_tex/, paper/figures/
python code/scan_literal_numbers.py                                                                 # every number in the manuscript prose traces to a macro
```
`code/model_check.py` re-derives the comparative statics quoted in Appendix A; `code/make_threeway_table.py` builds the
theory x agents x survey comparison from the frozen predictions and the confirmatory results.

## Agent experiments and disclosure control
Stage A: {M['StageAPersonas']} personas x 12 cells x 2 languages x 2 models = {M['StageACalls']} one-shot calls; Stage B:
{M['StageBEpisodes']} three-period episodes against the model's equilibrium rival ({M['ModelIdFable']}, {M['ModelRegionFable']};
{M['ModelIdGpt']}, {M['ModelRegionGpt']}; called {M['StageACallsDate']}). Personas were drawn from KIS register attributes, and
{M['PersonasUniqueInKIS']} of the {M['StageAPersonas']} match a single respondent, so the public logs (`agent_experiment/logs_public/`)
replace the four company lines of every prompt ({M['RedactedPrompts']} prompts) with a persona id and mask attribute echoes in
responses; `public/personas_public.csv` gives the attributes at sector x size band x age band (every persona matches at least
{M['PublicPersonaMinK']} respondents). Each record keeps the SHA-256 of the original prompt. The unredacted logs stay with the author
and are available to editors and referees under the KIS licence.

## Manuscript sources
`paper/main.tex` (full version), `paper/main_blinded.tex` (double-blind build), `paper/numbers.tex` (all numbers as macros),
`paper/tables_tex/`, `paper/figures/`, `paper/refs.bib` + `paper/refs_manual.bib`, `paper/highlights.tex`.
Build: `cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main`.

## Releases and archive
- `prereg-v1` (in the working repository): the frozen predictions and analysis script at registration.
{doi_line}

## Licence
MIT (see `LICENSE`) for the code, prompts, documentation and aggregate results in this repository. The KIS microdata are
licensed by STEPI and are not included; KOSIS data are open government data; the Korean statute texts under `docs/sources/law/`
are reproduced from the National Law Information Center (law.go.kr).
"""
    open(os.path.join(out, "README.md"), "w", encoding="utf-8").write(readme)
    open(os.path.join(out, "LICENSE"), "w", encoding="utf-8").write(MIT.format(year=year))
    cff = f"""cff-version: 1.2.0
message: "If you use this code, please cite the manuscript and the archived release."
title: "{T}"
type: software
authors:
  - family-names: Woo
    given-names: Jihwan
    orcid: "https://orcid.org/0000-0002-0424-0242"
    affiliation: "Amazon Web Services, Seoul, Republic of Korea"
license: MIT
repository-code: "{REPO}"
version: "{TAG}"
""" + (f"doi: {cdoi or vdoi}\n" if (cdoi or vdoi) else "")
    open(os.path.join(out, "CITATION.cff"), "w", encoding="utf-8").write(cff)
    zen = {
        "title": T,
        "upload_type": "software",
        "description": (f"Reproduction package for the manuscript \"{T}\" (Woo, {year}). The repository holds the race-model solver and "
                        "its comparative statics, the LLM-agent experiment scripts, prompts and redacted logs, the audited Korean Innovation "
                        "Survey item maps and the pre-registration package, the pre-registered analysis script and robustness scripts, every "
                        "aggregate result file behind the manuscript's numbers, and the generators of the manuscript's numbers, tables and "
                        "figures. The licensed KIS microdata are not redistributed."),
        "creators": [{"name": "Woo, Jihwan", "affiliation": "Amazon Web Services, Seoul, Republic of Korea", "orcid": "0000-0002-0424-0242"}],
        "license": "MIT",
        "access_right": "open",
        "keywords": ["entry threat", "innovation race", "pre-emption", "abandoned innovation", "Korean Innovation Survey", "preregistration",
                     "LLM agents", "reproduction code"],
    }
    json.dump(zen, open(os.path.join(out, ".zenodo.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    open(os.path.join(out, ".gitignore"), "w").write("__pycache__/\n*.pyc\n.DS_Store\npaper/*.aux\npaper/*.bbl\npaper/*.blg\npaper/*.log\npaper/*.out\npaper/*.spl\npaper/*.pdf\ndata/analysis_panel.parquet\n")
    print("wrote README.md, LICENSE, CITATION.cff, .zenodo.json, .gitignore in", out)


if __name__ == "__main__":
    main()
