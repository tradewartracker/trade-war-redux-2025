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

Later proclamations amend a basket rather than restate it. Each amendment is
applied to the basket in force the day before and written as a dated version
(see AMENDMENTS), so the engine can switch baskets on the effective date.

Usage: python extract-338-annex.py [--srcdir tariff-lists/sources] [--outdir tariff-lists]

The annex PDFs are read from --srcdir; the CSVs are written to --outdir.
"""

import argparse
import re
import sys
from pathlib import Path

import pandas as pd
import pdfplumber
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

# ── Amendments ───────────────────────────────────────────────────────────
# Each amending proclamation edits one subdivision (b)(n) of U.S. note 51 in
# its Annex II, deleting and inserting codes. Applying those edits to `base`
# gives the basket from `effective` on. Amendments run in list order, so a
# later one may build on an earlier one's output. Counts are asserted.
#
# The Sep 8 amendments also rewrite subdivision (c) so that the Section 232
# exemption names only heading 9903.03.13 (dairy): from Sep 15 the alcohol
# and autos duties stack on top of Section 232. That is set per regime in the
# engine (exempt_232) and checked against the annex text by validate-338.py.

AMENDMENTS = [
    {
        "name": "alcohol",
        "effective": "2026-09-15",
        "proclamation": "11064 (Sep 8, 2026)",
        "annex_i": "338-alcohol-scope-annex-I.pdf",
        "annex_ii": "338-alcohol-scope-annex-II.pdf",
        "subdivision": "(b)(1)",
        "base": "canada-338-alcohol.csv",
        "n_deleted": 2,
        "n_inserted": 40,
        "out": "canada-338-alcohol-2026-09-15.csv",
    },
    {
        "name": "autos",
        "effective": "2026-09-15",
        "proclamation": "11065 (Sep 8, 2026)",
        "annex_i": "338-autos-scope-annex-I.pdf",
        "annex_ii": "338-autos-scope-annex-II.pdf",
        "subdivision": "(b)(3)",
        "base": "canada-338-autos.csv",
        "n_deleted": 8,
        "n_inserted": 82,
        "out": "canada-338-autos-2026-09-15.csv",
    },
    {
        "name": "autos",
        "effective": "2026-10-30",
        "proclamation": "of Oct 23, 2026",
        "annex_i": "10-23-2026ModifyingAuto338.prc_.AnnexI-3.pdf",
        "annex_ii": "10-23-2026ModifyingAuto338.prc_.AnnexII-2.pdf",
        "subdivision": "(b)(3)",
        "base": "canada-338-autos-2026-09-15.csv",
        "n_deleted": 22,
        "n_inserted": 100,
        "out": "canada-338-autos-2026-10-30.csv",
    },
]

CODE = r"\d{4}\.\d{2}\.\d{2}"
CODE_ANY = rf"{CODE}(?:\d{{2}})?"    # HS8, or HS10 where an amendment narrows a line


def read_pdf(path):
    return "\n".join(p.extract_text() for p in pypdf.PdfReader(str(path)).pages)


def read_pdf_layout(path):
    """Text in reading order. pypdf returns the code blocks of the Sep 8 autos
    Annex II after item 2, detached from the clauses that say whether they are
    deleted or inserted, so the amending annexes are read with pdfplumber,
    which follows the page layout."""
    with pdfplumber.open(str(path)) as pdf:
        return "\n".join(p.extract_text() or "" for p in pdf.pages)


def parse_annex_i(text):
    """Annex I: HS code at the start of a line, description following.

    Descriptions wrap over several lines, so each one runs from the end of its
    code match to the start of the next. Page furniture (bare page numbers, the
    repeated 'Annex I' banner, the scope note) is stripped from the tail.
    """
    matches = list(re.finditer(rf"(?m)^({CODE_ANY})[ \t]+", text))
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


def _codes(text):
    """HS codes in a block of text, dots removed; chapter 99 headings dropped."""
    return [c.replace(".", "")
            for c in re.findall(rf"(?<![\d.]){CODE_ANY}(?!\d)", text)
            if not c.startswith("9903")]


def parse_annex_ii_edits(text, subdivision):
    """Amending Annex II: the codes deleted from and inserted into one
    subdivision of U.S. note 51.

    The edit runs to the next numbered item of the annex, which amends
    subdivision (c) and names only chapter 99 headings.
    """
    anchor = re.search(
        rf"Subdivision {re.escape(subdivision)} of U\.S\. note 51 is modified by",
        text)
    if not anchor:
        raise ValueError(f"no edit to subdivision {subdivision} found")
    tail = text[anchor.end():]
    nxt = re.search(r"(?m)^\s*\d+\.\s+Subdivision", tail)
    if nxt:
        tail = tail[:nxt.start()]
    dele = re.search(r"deleting the following subheadings", tail)
    ins = re.search(r"inserting the following subheadings", tail)
    if not (dele and ins):
        raise ValueError(f"deleting/inserting clauses not found in {subdivision}")
    return _codes(tail[dele.end():ins.start()]), _codes(tail[ins.end():])


def parse_annex_i_parts(text):
    """Amending Annex I, split into the codes it adds and the codes it removes.

    Part letters are not stable — the Sep 8 annexes put additions in Part A,
    the Oct 23 annex puts removals there — so each part is classified by title.
    """
    heads = list(re.finditer(r"(?m)^Part [A-Z]\.\s*[–-]\s*(.+)$", text))
    parts = {"added": [], "removed": []}
    for i, h in enumerate(heads):
        title = h.group(1)
        if "No Longer Covered" in title:
            kind = "removed"
        elif "New Products Covered" in title:
            kind = "added"
        else:
            raise ValueError(f"unrecognized Annex I part: {title!r}")
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        body = text[h.end():end]
        body = body[body.index("Product Description") + len("Product Description"):]
        parts[kind] += [(c.replace(".", ""), d) for c, d in parse_annex_i(body)]
    return parts


def reconcile(deleted, inserted, added_i, removed_i):
    """Problems, if any, with Annex I and Annex II describing the same change.

    The two annexes describe a narrowing differently. Annex II deletes the HS8
    line and re-inserts the HS10 lines that stay covered; Annex I lists only
    the HS10 lines that leave. So Annex I's additions must equal Annex II's
    insertions less those retained lines, and each Annex II deletion must be
    either removed outright in Annex I or narrowed with its leaving lines
    named there.
    """
    deleted, inserted = set(deleted), set(inserted)
    added_i, removed_i = set(added_i), set(removed_i)
    narrowed = {d for d in deleted
                if any(c != d and c.startswith(d) for c in inserted)}
    retained = {c for c in inserted if any(c.startswith(d) for d in narrowed)}
    leaving = removed_i - deleted
    problems = []
    if added_i != inserted - retained:
        problems.append(
            f"additions disagree — only in I: {sorted(added_i - inserted)[:5]}, "
            f"only in II: {sorted(inserted - retained - added_i)[:5]}")
    if deleted - narrowed != removed_i & deleted:
        problems.append(
            f"outright removals disagree — I: {sorted(removed_i & deleted)[:5]}, "
            f"II: {sorted(deleted - narrowed)[:5]}")
    stray = {r for r in leaving if not any(r.startswith(d) for d in narrowed)}
    if stray:
        problems.append(f"Annex I removes lines Annex II does not delete: "
                        f"{sorted(stray)[:5]}")
    silent = {d for d in narrowed if not any(r.startswith(d) for r in leaving)}
    if silent:
        problems.append(f"narrowed lines with no leaving HS10 in Annex I: "
                        f"{sorted(silent)}")
    return problems


def apply_amendment(am, outdir, srcdir):
    """Build one dated basket version. Returns (DataFrame, failures)."""
    tag = f"{am['name']} {am['effective']}"
    failures = []

    deleted, inserted = parse_annex_ii_edits(
        read_pdf_layout(srcdir / am["annex_ii"]), am["subdivision"])
    parts = parse_annex_i_parts(read_pdf_layout(srcdir / am["annex_i"]))
    added_i = dict(parts["added"])
    removed_i = [c for c, _ in parts["removed"]]

    if len(deleted) != len(set(deleted)) or len(inserted) != len(set(inserted)):
        failures.append(f"{tag}: duplicate codes in Annex II")
    if len(set(deleted)) != am["n_deleted"]:
        failures.append(f"{tag}: expected {am['n_deleted']} deletions, "
                        f"got {len(set(deleted))}")
    if len(set(inserted)) != am["n_inserted"]:
        failures.append(f"{tag}: expected {am['n_inserted']} insertions, "
                        f"got {len(set(inserted))}")
    failures += [f"{tag}: {p}"
                 for p in reconcile(deleted, inserted, added_i, removed_i)]

    base = pd.read_csv(outdir / am["base"], dtype=str)
    have = set(base["HTSUS"])
    if set(deleted) - have:
        failures.append(f"{tag}: deletes codes not in {am['base']}: "
                        f"{sorted(set(deleted) - have)[:5]}")
    if set(inserted) & have:
        failures.append(f"{tag}: inserts codes already in {am['base']}: "
                        f"{sorted(set(inserted) & have)[:5]}")

    # A retained HS10 line of a narrowed HS8 line has no Annex I entry, so it
    # carries its parent's description.
    parent = base.set_index("HTSUS")["description"]
    rows = [(c, added_i.get(c) or f"{parent[c[:8]]} (statistical line {c[8:]} only)")
            for c in inserted]
    out = (pd.concat([base[~base["HTSUS"].isin(deleted)],
                      pd.DataFrame(rows, columns=["HTSUS", "description"])])
           .sort_values("HTSUS").reset_index(drop=True))

    # An HS8 line alongside one of its own HS10 lines would cover goods twice.
    codes = set(out["HTSUS"])
    nested = sorted(c for c in codes if len(c) == 10 and c[:8] in codes)
    if nested:
        failures.append(f"{tag}: HS10 lines nested under a listed HS8: {nested[:5]}")
    expected = len(base) - am["n_deleted"] + am["n_inserted"]
    if len(out) != expected:
        failures.append(f"{tag}: expected {expected} codes, got {len(out)}")
    return out, failures


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--srcdir", default="tariff-lists/sources")
    ap.add_argument("--outdir", default="tariff-lists")
    args = ap.parse_args()
    srcdir = Path(args.srcdir)
    outdir = Path(args.outdir)

    failures = []

    for act in ACTIONS:
        ti = read_pdf(srcdir / act["annex_i"])
        tii = read_pdf(srcdir / act["annex_ii"])

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

    for am in AMENDMENTS:
        out, fails = apply_amendment(am, outdir, srcdir)
        failures += fails
        out.to_csv(outdir / am["out"], index=False)
        print(f"{am['name']:8s} {am['effective']}  -{am['n_deleted']:<3d} "
              f"+{am['n_inserted']:<3d} {len(out):4d} codes  -> {am['out']}")

    if failures:
        print("\nFAILED:", file=sys.stderr)
        for f in failures:
            print("  -", f, file=sys.stderr)
        sys.exit(1)
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
