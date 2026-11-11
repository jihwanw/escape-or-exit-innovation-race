# Perceived entry threat is associated with pre-emption by frontier firms, and the predicted abandonment response of laggards is not detected: a pre-registered innovation-race test with Korean survey data and LLM agents

Reproduction package for the manuscript of that title (Woo, 2026; single author; prepared for submission to *Research Policy*).

The paper derives two margins of an innovation race from a finite-horizon model with a technology gap and a stochastic entrant
(pre-emption by firms close to completion, abandonment by firms far from it), freezes the comparative statics of the model and the
choices of two LLM agents as pre-registered predictions, and tests six hypotheses on four waves of the Korean Innovation Survey
(16,595 firms; 7,988 with innovation activity). This repository holds the code that built every number,
table and figure in the manuscript, the aggregate result files those numbers come from, the agent prompts and the redacted agent
logs, the audited survey item maps and the pre-registration package. The licensed survey microdata are not included.

## Pre-registration
Registered on the Open Science Framework on 2026-11-10 15:07 KST (https://osf.io/tj9uv/; Secondary Data
Preregistration template; project https://osf.io/3kcvb/), embargoed until 2028-11-10. `prereg/PREREGISTRATION.md` is the
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
Stage A: 40 personas x 12 cells x 2 languages x 2 models = 1,920 one-shot calls; Stage B:
1,152 three-period episodes against the model's equilibrium rival (us.anthropic.claude-fable-5, us-east-1;
openai.gpt-5.6-sol, us-east-2; called 2026-11-10). Personas were drawn from KIS register attributes, and
14 of the 40 match a single respondent, so the public logs (`agent_experiment/logs_public/`)
replace the four company lines of every prompt (6,318 prompts) with a persona id and mask attribute echoes in
responses; `public/personas_public.csv` gives the attributes at sector x size band x age band (every persona matches at least
487 respondents). Each record keeps the SHA-256 of the original prompt. The unredacted logs stay with the author
and are available to editors and referees under the KIS licence.

## Manuscript sources
`paper/main.tex` (full version), `paper/main_blinded.tex` (double-blind build), `paper/numbers.tex` (all numbers as macros),
`paper/tables_tex/`, `paper/figures/`, `paper/refs.bib` + `paper/refs_manual.bib`, `paper/highlights.tex`.
Build: `cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main`.

## Releases and archive
- `prereg-v1` (in the working repository): the frozen predictions and analysis script at registration.
- `v1.0-submission`: the archived submission release (Zenodo version DOI to be added to this line when the archive is minted).

## Licence
MIT (see `LICENSE`) for the code, prompts, documentation and aggregate results in this repository. The KIS microdata are
licensed by STEPI and are not included; KOSIS data are open government data; the Korean statute texts under `docs/sources/law/`
are reproduced from the National Law Information Center (law.go.kr).
