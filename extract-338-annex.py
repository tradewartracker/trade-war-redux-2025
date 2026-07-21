"""
Extract HS code lists from the Section 338 proclamation annexes.

Each Section 338 action publishes two annexes:

  Annex I   the target list, one HS8 code per line followed by a plain-English
            product description
  Annex II  the HTSUS legal text, which restates the same codes as a bare
            block inside subdivision (b)(n) of U.S. note 51

The two are redundant by construction, which this script uses as its
correctness check: the code sets must match exactly, or extraction failed.
That guard needs no per-notice maintenance, unlike the hardcoded counts in
extract-301-exemptions.py.

The three Canada actions of Jul 20, 2026 share a single U.S. note 51. The
civil-aircraft carve-out in subdivision (d) is enumerated only once, in the
annex of the action that creates the note (alcohol); the later actions merely
repoint the heading reference. It is therefore written to its own CSV and
referenced by all three regimes.

Usage: python extract-338-annex.py [--outdir tariff-lists]
"""

import argparse
import re
import sys
from pathlib import Path

import pandas as pd
import pypdf

# ── Configuration ────────────────────────────────────────────────────────
# One entry per Section 338 action. `heading` is the chapter 99 heading the
# action creates; `n_codes` is the expected basket size (asserted).
# `defines_carveout` marks the action whose annex creates U.S. note 51 and
# therefore carries the shared civil-aircraft list.

ACTIONS = [
    {
        "name": "alcohol",
        "annex_i": "338-alcohol-annex-I.pdf",
        "annex_ii": "338-alcohol-annex-II.pdf",
        "heading": "9903.03.12",
        "n_codes": 63,
        "out": "canada-338-alcohol.csv",
        "defines_carveout": True,
    },
    {
        "name": "dairy",
        "annex_i": "338-dairy-annex-I.pdf",
        "annex_ii": "338-dairy-annex-II.pdf",
        "heading": "9903.03.13",
        "n_codes": 52,
        "out": "canada-338-dairy.csv",
        "defines_carveout": False,
    },
    {
        "name": "autos",
        "annex_i": "338-autos-annex-I.pdf",
        "annex_ii": "338-autos-annex-II.pdf",
        "heading": "9903.03.14",
        "n_codes": 439,
        "out": "canada-338-autos.csv",
        "defines_carveout": False,
    },
]

CARVEOUT_OUT = "canada-338-aircraft-exempt.csv"
CARVEOUT_N = 554

CODE = r"\d{4}\.\d{2}\.\d{2}"


def read_pdf(path):
    return "\n".join(p.extract_text() for p in pypdf.PdfReader(str(path)).pages)


def parse_annex_i(text):
    """Annex I: HS8 code at the start of a line, description following.

    Descriptions wrap over several lines, so each one runs from the end of its
    code match to the start of the next. Page furniture (bare page numbers, the
    repeated 'Annex I' banner, the scope note) is stripped from the tail.
    """
    matches = list(re.finditer(rf"(?m)^({CODE})[ \t]+", text))
    rows = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        desc = text[m.end():end]
        desc = re.sub(r"(?m)^\s*\d+\s*$", " ", desc)        # page numbers
        desc = re.sub(r"Annex I\s*", " ", desc)             # page banner
        desc = re.sub(r"\s+", " ", desc).strip()
        rows.append((m.group(1), desc))
    return rows


def parse_annex_ii_basket(text, heading):
    """Annex II: the bare code block in subdivision (b)(n) for `heading`.

    The block starts at the sentence naming the heading. Its end depends on
    which action is being parsed: in the action that creates U.S. note 51 the
    whole note is a single quotation, so (b)(1) is followed directly by
    subdivision (c) with no closing quote; in the later amending actions the
    subdivision is quoted on its own and does end with one. Stop at whichever
    boundary comes first.

    Chapter 99 headings are dropped — subdivision (c) enumerates them, and they
    are not HTSUS articles.
    """
    anchor = re.search(
        rf"Heading {re.escape(heading)} applies to articles", text)
    if not anchor:
        raise ValueError(f"could not locate the (b) block for {heading}")
    tail = text[anchor.end():]

    bounds = [m.start() for m in [re.search(r"”", tail),
                                  re.search(r"\(c\)\s+As provided", tail)]
              if m]
    if not bounds:
        raise ValueError(f"unterminated (b) block for {heading}")
    return [c for c in re.findall(CODE, tail[:min(bounds)])
            if not c.startswith("9903")]


def parse_carveout(text):
    """The civil-aircraft list in subdivision (d) of U.S. note 51.

    Anchored on the subdivision's own opening clause rather than a bare "(d)",
    which also occurs in subdivision (a) as a cross-reference. The block cannot
    be closed on the first curly quote either — subdivision (d) quotes the
    phrase "Free (C)" partway through — so it runs to the heading-insertion
    clause that follows the note.

    Codes named before the list itself are chapter 99 headings (9903.xx.xx)
    identifying the carve-out heading, not HTSUS articles, so they are dropped.
    """
    start = re.search(r"\(d\)\s+As provided in heading", text)
    if not start:
        raise ValueError("subdivision (d) not found")
    tail = text[start.end():]
    stop = re.search(r"\d+\.\s+The following new heading", tail)
    if stop:
        tail = tail[:stop.start()]
    return [c for c in re.findall(CODE, tail) if not c.startswith("9903")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="tariff-lists")
    args = ap.parse_args()
    outdir = Path(args.outdir)

    failures = []

    for act in ACTIONS:
        ti = read_pdf(outdir / act["annex_i"])
        tii = read_pdf(outdir / act["annex_ii"])

        rows = parse_annex_i(ti)
        basket_ii = parse_annex_ii_basket(tii, act["heading"])

        codes_i = [c for c, _ in rows]
        set_i, set_ii = set(codes_i), set(basket_ii)

        # ── Guards ──
        if len(codes_i) != len(set_i):
            failures.append(f"{act['name']}: duplicate codes in Annex I")
        if set_i != set_ii:
            failures.append(
                f"{act['name']}: Annex I/II disagree — "
                f"only in I: {sorted(set_i - set_ii)[:5]}, "
                f"only in II: {sorted(set_ii - set_i)[:5]}")
        if len(set_i) != act["n_codes"]:
            failures.append(
                f"{act['name']}: expected {act['n_codes']} codes, got {len(set_i)}")
        if any(not d for _, d in rows):
            failures.append(f"{act['name']}: blank description(s) in Annex I")

        df = pd.DataFrame(rows, columns=["HTSUS", "description"])
        df["HTSUS"] = df["HTSUS"].str.replace(".", "", regex=False)
        df.to_csv(outdir / act["out"], index=False)
        print(f"{act['name']:8s} {act['heading']}  {len(df):4d} codes  "
              f"-> {act['out']}")

        if act["defines_carveout"]:
            air = parse_carveout(tii)
            if not air:
                raise ValueError("carve-out block parsed as empty")
            if len(air) != len(set(air)):
                failures.append("carve-out: duplicate codes")
            if len(set(air)) != CARVEOUT_N:
                failures.append(
                    f"carve-out: expected {CARVEOUT_N} codes, got {len(set(air))}")
            ac = pd.DataFrame({"HTSUS": sorted(set(air))})
            ac["HTSUS"] = ac["HTSUS"].str.replace(".", "", regex=False)
            ac["category"] = "aircraft"
            ac.to_csv(outdir / CARVEOUT_OUT, index=False)
            print(f"{'aircraft':8s} 9903.03.16  {len(ac):4d} codes  "
                  f"-> {CARVEOUT_OUT}  (shared by all three actions)")

    if failures:
        print("\nFAILED:", file=sys.stderr)
        for f in failures:
            print("  -", f, file=sys.stderr)
        sys.exit(1)
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
