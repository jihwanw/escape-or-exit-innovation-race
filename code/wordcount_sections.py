#!/usr/bin/env python3
"""wordcount_sections.py — TeX word count per section of paper/main.tex.

Counts words in the prose only: table/figure environments, \\cite/\\ref/\\label/\\url/\\includegraphics arguments are removed,
every macro (\\Foo) counts as one word (a number). Reports the main-text total (Introduction .. Conclusions, i.e. everything
between \\section{Introduction} and \\appendix) against Research Policy's stated preference (Guide for Authors, Wayback
2023-03-16: 'strong preference for articles to be no more than 8-10,000 words').

Usage: python code/wordcount_sections.py [paper/main.tex] [--limit 10000]
Exit 1 if the main text exceeds --limit.
"""
import re, sys, argparse
from pathlib import Path


def words(s: str) -> int:
    s = re.sub(r"(?<!\\)%.*", "", s)
    s = re.sub(r"\\begin\{(table|figure)\*?\}.*?\\end\{\1\*?\}", " ", s, flags=re.S)
    s = re.sub(r"\\(cite[tp]?|citealp|citealt|ref|label|eqref|url|includegraphics|input)(\[[^\]]*\])?\{[^}]*\}", " ", s)
    s = re.sub(r"\\[A-Za-z]+\*?", "X", s)
    s = re.sub(r"[{}~\\$&]", " ", s)
    return len(re.findall(r"[A-Za-z0-9][\w'\-\.%]*", s))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tex", nargs="?", default="paper/main.tex"); ap.add_argument("--limit", type=int, default=10000)
    ap.add_argument("--write-tex", default=None, help="write \\MainTextWords etc. to this .tex file (title page, cover letter)")
    a = ap.parse_args()
    body = Path(a.tex).read_text(encoding="utf-8").split("\\begin{document}")[1]
    parts = re.split(r"(\\(?:sub)?section\*?\{[^}]*\}|\\appendix|\\begin\{abstract\}|\\end\{abstract\})", body)
    cur, counts, order = "front matter", {}, ["front matter"]
    for p in parts:
        if p.startswith("\\section") or p.startswith("\\subsection") or p in ("\\appendix", "\\begin{abstract}", "\\end{abstract}"):
            cur = p; order.append(cur); counts.setdefault(cur, 0)
        else:
            counts[cur] = counts.get(cur, 0) + words(p)
    main_total, in_main, app_total, in_app, abstract = 0, False, 0, False, 0
    for k in order:
        n = counts.get(k, 0)
        if k == "\\begin{abstract}": abstract = n
        if k == "\\section{Introduction}": in_main = True
        if k == "\\appendix": in_main, in_app = False, True
        if in_main: main_total += n
        elif in_app and not k.startswith("\\section*"): app_total += n
        print(f"{n:6d}  {k[:100]}")
    print(f"\nabstract {abstract} words; MAIN TEXT (Introduction..Conclusions, prose only) {main_total} words; appendices {app_total} words; limit {a.limit}")
    if a.write_tex:
        Path(a.write_tex).write_text("%% written by code/wordcount_sections.py — do not edit\n"
                                     f"\\newcommand{{\\MainTextWords}}{{{main_total:,}}}\n\\newcommand{{\\AbstractWords}}{{{abstract}}}\n"
                                     f"\\newcommand{{\\AppendixWords}}{{{app_total:,}}}\n", encoding="utf-8")
        print("wrote", a.write_tex)
    sys.exit(1 if main_total > a.limit else 0)


if __name__ == "__main__":
    main()
