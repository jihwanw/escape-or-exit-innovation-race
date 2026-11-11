#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scan the manuscript source for literal numbers typed into prose (single-source-of-truth rule: every statistic must be a
macro from numbers.tex). Reports every digit-bearing token in prose that is not (a) inside a macro call, (b) a year,
(c) a hypothesis/prediction/section/equation label, (d) a questionnaire block/item number, (e) a scale or count that the
text defines from the questionnaire or the registered design, or (f) inside the verbatim prompt quotation of Appendix C.
Also scans the pdftotext rendering of the main body for numbers that are not among the values of numbers.json macros or
of the table/figure PDFs (second route). Exit 1 if an unexplained literal remains in the tex prose."""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TEX = os.path.join(ROOT, "paper", "main.tex")
NUM = json.load(open(os.path.join(ROOT, "paper", "numbers.json")))["macros"]

ALLOWED_TOKENS = {
    # labels and structure
    "H1", "H2", "H3", "H4", "H5", "H6", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M10",
    # questionnaire block/item numbers (verbatim from the questionnaires; item map), scale end-points printed in the questionnaire
    "0", "1", "2", "3", "4", "5", "6", "8", "11", "33",
    # registered design constants stated in words elsewhere / template constants quoted verbatim in Appendix C
    "0.20", "0.80", "0.05", "0.05.", "90", "50",
    # significance levels / coverage levels of the registered rules
    "5", "95", "90", "0.05", "0.5",
    # CIS questionnaire version, KSIC digits
    "2020", "two-digit",
}
YEAR = re.compile(r"^(19|20)\d{2}$")
# contexts in which a digit token is a documented identifier, a questionnaire code, a registered design constant or a verbatim quotation
CONTEXT_WHITELIST = [
    r"ORCID", r"GPT-5\.6", r"fable-5", r"SHA-256", r"DT\\_6BD1101", r"Articles 33 and 34",            # identifiers (institutional fact card, model ids)
    r"founding year of 30",                                                                         # documented sentinel (01_build_summary.json)
    r"80\\% power",                                                                                  # registered power level (prereg)
    r"borrow about 40\\%",                                                                           # verbatim v2 template wording (stage_a_templates.py docstring)
    r"0--5", r"1--6", r"1/2", r"1/0", r"0--3 as 1--4",                                               # printed questionnaire codes and documented recodes (item maps)
    r"billion won", r"follower (is )?at [01]", r"leader is at 1", r"both are at 1",                   # verbatim prompt quotation (Appendix C) and model positions (Appendix A)
    r"manufacturing in 2022 and 2024, services in 2023 and 2025", r"2022--2025",                     # wave years
]


def strip_for_prose(tex):
    tex = re.sub(r"(?<!\\)%.*", "", tex)
    tex = tex.split("\\begin{document}", 1)[1]
    # drop table/figure environments, equations, quoted prompt block (Appendix C), bibliography commands
    tex = re.sub(r"\\begin\{(table|figure|equation|align|quote)\*?\}.*?\\end\{\1\*?\}", " ", tex, flags=re.S)
    tex = re.sub(r"\$[^$]*\$", " ", tex)
    tex = re.sub(r"\\(cite[tp]?|citealp|ref|label|url|input|includegraphics|bibliography|bibliographystyle|graphicspath|setcounter|renewcommand|ead|address|cortext|author|JEL)\{[^}]*\}", " ", tex)
    tex = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", " MACRO ", tex)  # macro calls become placeholders
    return tex


def main():
    tex = open(TEX, encoding="utf-8").read()
    prose = strip_for_prose(tex)
    hits = []
    for m in re.finditer(r"(?<![A-Za-z\\])[+\-]?\d[\d,]*(\.\d+)?%?", prose):
        tok = m.group(0)
        ctx = prose[max(0, m.start() - 70): m.end() + 40].replace("\n", " ")
        bare = tok.rstrip("%").rstrip(".")
        if YEAR.match(bare) or bare in ALLOWED_TOKENS or tok in ALLOWED_TOKENS:
            continue
        # section cross-references such as "Section 3", "Appendix A", item "(4)", "block 11, item 3"
        if re.search(r"(Section|Sections|Appendix|Table|Figure|Eq\.|item|block|period|stage|version|page|Article|Articles|M)\s*$", prose[max(0, m.start() - 12): m.start()], flags=re.I):
            continue
        if any(re.search(pat, ctx) for pat in CONTEXT_WHITELIST):
            continue
        hits.append((tok, ctx))
    print(f"tex prose: {len(hits)} literal digit tokens not covered by macros or whitelist")
    for tok, ctx in hits:
        print(f"  [{tok}] …{ctx}…")

    # second route: pdftotext of the body versus macro values
    pdf = os.path.join(ROOT, "paper", "main.pdf"); unknown = []
    if os.path.exists(pdf):
        txt = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout
        # the References heading may start a new page, in which case pdftotext precedes it with a form feed (\f) instead of \n (2026-11-11)
        m_ref = re.search(r"(?:^|[\n\f])References[ \t]*\n", txt)
        body = txt[: m_ref.start()] if m_ref else txt
        values = set()
        quoted_text_nums = set()  # decimals inside text-valued macros (verbatim agent reasons quoted in Section 6)
        for v in NUM.values():
            values.add(str(v).replace("+", "").replace("$<$", "<"))
            values.add(str(v).replace("+", "").replace(",", ""))
            if len(str(v)) > 24:  # a sentence, not a statistic
                quoted_text_nums |= set(re.findall(r"\d[\d,]*\.\d+", str(v)))
        values |= quoted_text_nums
        nums = re.findall(r"(?<![A-Za-z])[+\-]?\d[\d,]*\.\d+(?![\d])", body)  # decimals only (integers are too ambiguous in rendered text)
        import glob
        table_fig_text = ""
        for f in glob.glob(os.path.join(ROOT, "paper", "tables_tex", "T_*.tex")):
            table_fig_text += open(f, encoding="utf-8").read()
        for f in glob.glob(os.path.join(ROOT, "paper", "figures", "*.pdf")):
            table_fig_text += subprocess.run(["pdftotext", f, "-"], capture_output=True, text=True).stdout
        tf_nums = set(re.findall(r"[+\-]?\d[\d,]*\.\d+", table_fig_text.replace("$-$", "-").replace("\u2212", "-")))
        tf_plain = {n.lstrip("+-") for n in tf_nums}
        unknown = sorted({n for n in nums if n.replace("+", "").replace("\u2212", "-") not in values and n.lstrip("+-") not in values
                          and n.replace("\u2212", "-") not in tf_nums and n.lstrip("+-\u2212") not in tf_plain})
        unknown = [n for n in unknown if n.lstrip("+-") not in ("1.5", "3.25", "5.6", "6.5", "0.8", "2.5")]  # prompt quotation (Appendix C) and model names
        section_numbers = set(re.findall(r"^\s*(\d\.\d)\.\s+[A-Z]", body, flags=re.M))  # subsection headings rendered as "2.1. Title"
        unknown = [n for n in unknown if n not in section_numbers]
        print(f"pdftotext route: {len(set(nums))} distinct decimal tokens in the rendered body; {len(unknown)} not equal to any macro value, table cell or figure label:")
        print("  " + ", ".join(unknown[:60]))
    sys.exit(1 if (hits or unknown) else 0)


if __name__ == "__main__":
    main()
