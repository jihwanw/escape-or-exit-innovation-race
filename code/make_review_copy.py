#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_review_copy.py — anonymised copy of the public reproduction package for Research Policy's double-blind review.

Starts from the export written by code/export_public_repo.py, removes the files that name the author (README.md, LICENSE,
CITATION.cff, .zenodo.json, code/make_public_readme.py, code/export_public_repo.py), redacts the author line of
prereg/PREREGISTRATION.md and the author block / repository URL in paper/main.tex, writes a short anonymised README, scans every
text file for identifying strings and aborts on any hit, then zips the result for upload to the anonymised OSF review component.

Usage: python code/make_review_copy.py --src ../Escape_or_Exit_public --out /tmp/review_copy
"""
import argparse
import os
import re
import shutil
import sys

IDENTIFIERS = re.compile(r"(Jihwan|Woo,|\bWoo\b|jihwanw|0000-0002-0424-0242|Amazon Web Services|jihwan\.woo|github\.com/jihwanw|escape-or-exit-innovation-race)")
DROP = ["README.md", "LICENSE", "CITATION.cff", ".zenodo.json", "code/make_public_readme.py", "code/export_public_repo.py",
        "code/make_review_copy.py"]

README = """# Anonymised review copy — reproduction package

This is the anonymised copy, for double-blind review, of the reproduction package that accompanies the manuscript
"Perceived entry threat is associated with pre-emption by frontier firms, and the predicted abandonment response of laggards is
not detected: a pre-registered innovation-race test with Korean survey data and LLM agents". The public repository, its release
tag and the archived version DOI are given on the title page (available to the editor) and will be inserted into the manuscript
on acceptance. Files that would identify the author (licence, citation metadata, repository README) are omitted here; the author
line of the registered pre-registration document is redacted; nothing else differs from the public package.

Contents: `code/` (loader, pre-registered analysis script, robustness, generators of every number, table and figure),
`model/` (race-model solver, grid, controls), `agent_experiment/` (prompts, designs, environment, runners, probes, redacted logs
under `logs_public/`), `public/personas_public.csv`, `item_maps/` (audited survey item maps with questionnaire wording and value
distributions), `data/` (KOSIS entry-rate aggregates and provenance), `results/` (every aggregate result file), `prereg/`
(registered document, frozen predictions, SHA-256 sums, registration record), `docs/` (hypotheses, model predictions, variable
table, fact cards with primary-source law texts), `paper/` (LaTeX sources, numbers macros, tables, figures, bibliography).
The Korean Innovation Survey microdata are licensed research-use files and are not included.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    src, out = os.path.abspath(a.src), os.path.abspath(a.out)
    if os.path.exists(out):
        shutil.rmtree(out)
    shutil.copytree(src, out, ignore=shutil.ignore_patterns(".git", "__pycache__", ".DS_Store"))
    for rel in DROP:
        p = os.path.join(out, rel)
        if os.path.exists(p):
            os.remove(p)
    # redactions
    pre = os.path.join(out, "prereg", "PREREGISTRATION.md")
    t = open(pre, encoding="utf-8").read()
    t2, n = re.subn(r"^\*\*Authors\.\*\* .*$", "**Authors.** [redacted for double-blind review]", t, flags=re.M)
    if n != 1:
        sys.exit("author line of PREREGISTRATION.md not found exactly once")
    open(pre, "w", encoding="utf-8").write(t2)
    tex = os.path.join(out, "paper", "main.tex")
    t = open(tex, encoding="utf-8").read()
    t, n1 = re.subn(r"\\ifanon\\else\n\\author.*?\n\\fi\n", "\\\\ifanon\\\\else\n% author block removed in the review copy\n\\\\fi\n", t, flags=re.S)
    t, n2 = re.subn(r"\\newcommand\{\\RepoURL\}\{[^}]*\}", "\\\\newcommand{\\\\RepoURL}{[repository URL withheld for review]}", t)
    t, n3 = re.subn(r"pdfauthor=\{Jihwan Woo\}", "pdfauthor={}", t)
    if (n1, n2, n3) != (1, 1, 1):
        sys.exit(f"main.tex redactions did not match exactly once: {(n1, n2, n3)}")
    open(tex, "w", encoding="utf-8").write(t)
    open(os.path.join(out, "README.md"), "w", encoding="utf-8").write(README)
    # generic redactions in provenance strings (local paths carry the user name; two prereg scripts name the author)
    REDACT = [(re.compile(r"/Users/jihwanw"), "/Users/[user]"), (re.compile(r"Jihwan Woo"), "[author]"),
              (re.compile(r"0000-0002-0424-0242"), "[ORCID redacted]")]
    n_red = 0
    for dirpath, _, files in os.walk(out):
        for f in files:
            p = os.path.join(dirpath, f)
            if p.endswith((".pdf", ".png", ".parquet")):
                continue
            txt = open(p, encoding="utf-8", errors="replace").read(); new = txt
            for rx, rep in REDACT:
                new, k = rx.subn(rep, new); n_red += k
            if new != txt:
                open(p, "w", encoding="utf-8").write(new)
    print(f"generic redactions applied: {n_red}")
    # scan
    hits = []
    for dirpath, _, files in os.walk(out):
        for f in files:
            p = os.path.join(dirpath, f); r = os.path.relpath(p, out)
            if r.endswith((".pdf", ".png", ".parquet")):
                continue
            txt = open(p, encoding="utf-8", errors="replace").read()
            for m in IDENTIFIERS.finditer(txt):
                ctx = txt[max(0, m.start() - 40): m.end() + 40].replace("\n", " ")
                hits.append((r, m.group(0), ctx))
    if hits:
        for r, w, ctx in hits[:40]:
            print(f"[IDENTIFIER] {r}: {w!r} … {ctx!r}")
        sys.exit(f"review copy aborted: {len(hits)} identifying strings")
    zip_base = out.rstrip("/")
    shutil.make_archive(zip_base, "zip", root_dir=os.path.dirname(out), base_dir=os.path.basename(out))
    print(f"review copy: {out} — identifier scan 0 hits; zip {zip_base}.zip ({os.path.getsize(zip_base + '.zip') / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
