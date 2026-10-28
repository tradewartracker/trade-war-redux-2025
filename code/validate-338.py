"""
Validate the Section 338 HS code lists produced by extract-338-annex.py.

The extractor already guards itself (Annex I must agree with Annex II, and the
per-action counts are asserted). This script is the independent second opinion:
it re-derives the code sets with a different parsing method, checks the lists
against observed trade data, and confirms the economic magnitudes that get
quoted downstream.

Run it after extract-338-annex.py whenever a new Section 338 action is added.
The action config is imported from the extractor rather than duplicated, so the
two cannot disagree about which PDF is which.

Usage: python code/validate-338.py
Exits non-zero if any check fails.
"""

import glob
import importlib.util
import re
import sys
from pathlib import Path

import pandas as pd
import pypdf

ROOT = Path(__file__).resolve().parents[1]   # the repository root
TL = ROOT / "tariff-lists"
SRC = TL / "sources"          # the proclamation PDFs
DATA = ROOT / "data"
CANADA = "1220"

# Expected magnitudes, asserted so a silent list change cannot quietly move the
# published numbers. Update deliberately when a new action is added.
EXPECT_UNION_PP = 2.63       # percentage points added to Canada's rate
EXPECT_AIRCRAFT_OVERLAP = 28  # aircraft carve-out codes inside the autos basket
EXPECT_CH44_CODES = 64        # ch44 in autos basket — hardwood/plywood, NOT 232 timber

# Baskets in force on each panel date, by CSV. Amendments (extract-338-annex.py
# AMENDMENTS) replace a basket from their effective date; dairy is never amended.
IN_FORCE = {
    "2026-08-22": ["canada-338-alcohol.csv", "canada-338-dairy.csv",
                   "canada-338-autos.csv"],
    "2026-09-15": ["canada-338-alcohol-2026-09-15.csv", "canada-338-dairy.csv",
                   "canada-338-autos-2026-09-15.csv"],
    "2026-10-30": ["canada-338-alcohol-2026-09-15.csv", "canada-338-dairy.csv",
                   "canada-338-autos-2026-10-30.csv"],
}
# Union impact on each date (50% x share of 2025 Canadian imports, before any
# carve-out), asserted like EXPECT_UNION_PP.
EXPECT_UNION_PP_BY_DATE = {"2026-08-22": 2.63, "2026-09-15": 2.65, "2026-10-30": 2.66}
# Sep 8 import bans (Procs 11061-11063), effective Sep 29. Modeled at the 50%
# basket rate, which is only a no-op if every banned code is in a basket.
BANS = {"338-alcohol-ban-annex.pdf": 53, "338-dairy-ban-annex.pdf": 14,
        "338-autos-ban-annex.pdf": 1}


def load_extractor():
    """Import the hyphenated extractor script for its ACTIONS config."""
    spec = importlib.util.spec_from_file_location(
        "extract_338_annex", Path(__file__).parent / "extract-338-annex.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ok = True


def check(label, cond, detail=""):
    global ok
    ok &= bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}{'  ' + detail if detail else ''}")


def read_pdf(name):
    return "\n".join(p.extract_text() for p in pypdf.PdfReader(str(SRC / name)).pages)


def main():
    ex = load_extractor()
    actions = {a["name"]: a for a in ex.ACTIONS}
    csvs = {n: pd.read_csv(TL / a["out"], dtype=str) for n, a in actions.items()}
    air = pd.read_csv(TL / ex.CARVEOUT_OUT, dtype=str)

    print("\n=== 1. Schema and format ===")
    for name, df in list(csvs.items()) + [("aircraft", air)]:
        c = df["HTSUS"]
        check(f"{name}: all 8-digit numeric HS8",
              c.str.fullmatch(r"\d{8}").all(), f"n={len(c)}")
        check(f"{name}: no duplicates", c.is_unique)
        check(f"{name}: no nulls", c.notna().all())
    for name, df in csvs.items():
        d = df["description"]
        check(f"{name}: descriptions present and non-trivial",
              d.notna().all() and (d.str.len() > 5).all(),
              f"min len={d.str.len().min()}")
        check(f"{name}: no description begins with a leaked HS code",
              not d.str.contains(r"^\d{4}\.\d{2}\.\d{2}").any())

    print("\n=== 2. Independent re-parse of Annex I ===")
    # Deliberately unlike the extractor's line-anchored parser: scan the whole
    # body for code tokens. A loose scan also catches codes cross-referenced
    # inside a description (6203.41.60 reads "other than of heading
    # 6203.41.25"), so require the CSV to be a subset and every extra token to
    # be traceable to description prose.
    for name, a in actions.items():
        body = read_pdf(a["annex_i"])
        body = body[body.index("Product Description"):]
        alt = {c.replace(".", "") for c in
               re.findall(r"(?<![\d.])(\d{4}\.\d{2}\.\d{2})(?![\d])", body)}
        got = set(csvs[name]["HTSUS"])
        prose = " ".join(csvs[name]["description"]).replace(".", "")
        unexplained = {c for c in (alt - got) if c not in prose}
        check(f"{name}: CSV is a subset of an independent parse", got <= alt,
              f"missing={sorted(got - alt)[:4]}")
        check(f"{name}: every extra token is a description cross-reference",
              not unexplained, f"unexplained={sorted(unexplained)[:4]}")
        check(f"{name}: count == expected {a['n_codes']}", len(got) == a["n_codes"])

    print("\n=== 3. Cross-annex agreement (Annex II legal text) ===")
    for name, a in actions.items():
        blk = {c.replace(".", "") for c in
               ex.parse_annex_ii_basket(read_pdf(a["annex_ii"]), a["heading"])}
        check(f"{name}: Annex II basket == CSV ({a['heading']})",
              blk == set(csvs[name]["HTSUS"]))

    print("\n=== 4. Disjointness ===")
    # The proclamations partition their baskets; overlap would double-count.
    names = list(csvs)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = set(csvs[names[i]]["HTSUS"]), set(csvs[names[j]]["HTSUS"])
            check(f"{names[i]} vs {names[j]} disjoint", not (a & b),
                  f"overlap={len(a & b)}")

    print("\n=== 5. Content plausibility ===")
    autos = set(csvs["autos"]["HTSUS"])
    ch = lambda s, n=3: pd.Series([c[:2] for c in s]).value_counts().head(n).to_dict()
    check("alcohol basket dominated by ch22 beverages",
          ch(csvs["alcohol"]["HTSUS"], 1).get("22", 0) >= 40,
          str(ch(csvs["alcohol"]["HTSUS"])))
    check("dairy basket dominated by ch04/17 dairy and sugars",
          sum(ch(csvs["dairy"]["HTSUS"], 5).get(c, 0) for c in ("04", "17")) >= 25,
          str(ch(csvs["dairy"]["HTSUS"])))
    check("autos basket is a broad retaliation basket",
          len({c[:2] for c in autos}) > 25,
          f"chapters={len({c[:2] for c in autos})}")
    check("autos basket contains no ch87 vehicles beyond motorcycles",
          {c for c in autos if c.startswith("87")} == {"87115000"},
          str({c for c in autos if c.startswith("87")}))

    print("\n=== 6. Coverage against Canadian import data ===")
    # Pool both weight years: a line with zero trade in one year (bulk rum,
    # prune wine) still appears in the other, so one year alone understates
    # which HS codes actually exist.
    files = sorted(glob.glob(str(DATA / "202[45]-hs10-imports*.parquet")))
    universe = set()
    for f in files:
        universe |= set(pd.read_parquet(f, columns=["HS8"]).HS8.unique())
    print(f"    HS8 universe across {len(files)} country-year files: {len(universe):,}")

    d = pd.read_parquet(DATA / f"2025-hs10-imports{CANADA}.parquet")
    tot = d.imports.sum()
    allc = set()
    for name, df in csvs.items():
        c = set(df["HTSUS"])
        allc |= c
        hit = d[d.HS8.isin(c)]
        v = hit.imports.sum()
        print(f"    {name:8s} {len(c):4d} codes  matched {hit.HS8.nunique():4d}  "
              f"${v/1e9:6.3f}B  {100*v/tot:5.2f}%  +{50*v/tot:.3f}pp")
        # Missing from Canada's file usually just means Canada does not ship it.
        # The real test is whether the code exists in the HTS at all; anything
        # absent everywhere must be a quota/note tier line, which carries no
        # trade by construction.
        absent = c - set(d.HS8) - universe
        if absent:
            desc = df.set_index("HTSUS")["description"]
            unexplained = {u for u in absent if not re.search(
                r"General Note 15|additional U\.S\. note|note \d+ to chapter|quota",
                desc[u])}
            check(f"{name}: codes absent from the HTS universe are quota/note lines",
                  not unexplained,
                  f"{len(absent)} absent, {len(unexplained)} unexplained"
                  + (f" e.g. {sorted(unexplained)[:3]}" if unexplained else ""))
        else:
            check(f"{name}: every code observed in the HTS universe", True)

    v = d[d.HS8.isin(allc)].imports.sum()
    pp = 50 * v / tot
    print(f"    {'UNION':8s} {len(allc):4d} codes  ${v/1e9:.3f}B  "
          f"{100*v/tot:.2f}%  +{pp:.2f}pp")
    check("union count == sum of parts", len(allc) == sum(len(x) for x in csvs.values()))
    check(f"union impact == {EXPECT_UNION_PP}pp", abs(pp - EXPECT_UNION_PP) < 0.02,
          f"{pp:.3f}pp")

    print("\n=== 7. Carve-out interactions ===")
    airs = set(air["HTSUS"])
    check(f"aircraft list is {ex.CARVEOUT_N} codes", len(airs) == ex.CARVEOUT_N)
    ov = {n: len(set(df["HTSUS"]) & airs) for n, df in csvs.items()}
    print(f"    aircraft-list overlap by basket: {ov}")
    check(f"aircraft carve-out overlaps autos basket ({EXPECT_AIRCRAFT_OVERLAP} codes)",
          ov["autos"] == EXPECT_AIRCRAFT_OVERLAP)
    br = TL / "brazil-301-exemptions.csv"
    if br.exists():
        b = pd.read_csv(br, dtype=str)
        bair = set(b[b["category"] == "aircraft"]["HTSUS"])
        check("338 aircraft list differs from the Brazil 301 list (separate notices)",
              bair != airs,
              f"brazil={len(bair)} vs 338={len(airs)}, shared={len(bair & airs)}")

    print("\n=== 8. Chapter-44 wood in autos basket (NOT the Proc 10976 carve-out) ===")
    # Note 51(c)(4) exempts only wood in the Section 232 timber headings
    # (9903.76.*): softwood 4403/4406/4407, furniture 9401.61, cabinets 9403.
    # The ch44 codes here are hardwood, plywood, fiberboard and joinery, which
    # Proc 10976 does NOT cover — they are non-232 and correctly dutiable at 50%.
    # An earlier note treated them as a deferred 232 carve-out; that was a
    # misdiagnosis (corrected Jul 23, 2026 when the timber sector was modeled).
    w = {c for c in autos if c.startswith("44")}
    wv = d[d.HS8.isin(w)].imports.sum()
    bv = d[d.HS8.isin(autos)].imports.sum()
    print(f"    ch44 in autos basket: {len(w)} codes, ${wv/1e9:.3f}B "
          f"({100*wv/bv:.1f}% of basket)")
    check(f"ch44 in basket still {EXPECT_CH44_CODES} codes", len(w) == EXPECT_CH44_CODES)
    # The load-bearing fact behind the correction: none of the Proc 10976
    # softwood timber codes (9903.76.01) are in the autos basket, so modeling
    # timber does not carve any of these 64 ch44 codes out of the 338 duty.
    tl = TL / "timber-232.csv"
    if tl.exists():
        soft = set(pd.read_csv(tl, dtype=str).query("category=='softwood'")["HTSUS"])
        check("Proc 10976 softwood codes are disjoint from the autos basket",
              not (soft & autos), f"overlap={sorted(soft & autos)}")

    print("\n=== 9. Amended baskets (dated versions) ===")
    # Independent of the extractor, which parses Annex II positionally with
    # pdfplumber: here pypdf, order-free. Every non-chapter-99 code in an
    # amending Annex II is either deleted (it is in the base) or inserted (it is
    # not), which holds as long as no amendment re-inserts a code it keeps — and
    # the extractor guards that.
    def covered(code, basket):
        return code in basket or code[:8] in basket

    hts10 = pd.read_csv(TL / "mfn-per-code.csv", dtype=str, usecols=["HS10"])["HS10"]
    for am in ex.AMENDMENTS:
        tag = f"{am['name']} {am['effective']}"
        base = set(pd.read_csv(TL / am["base"], dtype=str)["HTSUS"])
        got = pd.read_csv(TL / am["out"], dtype=str)
        codes = {c for c in ex._codes(read_pdf(am["annex_ii"]))}
        rederived = (base - codes) | (codes - base)
        check(f"{tag}: CSV == base edited by an order-free parse of Annex II",
              set(got["HTSUS"]) == rederived,
              f"n={len(got)}, diff={sorted(set(got['HTSUS']) ^ rederived)[:4]}")
        check(f"{tag}: HS8/HS10 numeric, unique, described",
              got["HTSUS"].str.fullmatch(r"\d{8}|\d{10}").all()
              and got["HTSUS"].is_unique and (got["description"].str.len() > 5).all())
        # A narrowing keeps some HS10 lines of a deleted HS8 line and Annex I
        # names the rest as leaving. Together they must be every HS10 line under
        # that HS8 in the HTS, or goods would silently fall out of scope.
        parts = ex.parse_annex_i_parts(ex.read_pdf_layout(SRC / am["annex_i"]))
        leaving = {c for c, _ in parts["removed"] if len(c) == 10}
        kept = {c for c in got["HTSUS"] if len(c) == 10} - base
        for parent in sorted({c[:8] for c in kept | leaving}):
            under = set(hts10[hts10.str.startswith(parent)])
            mine = {c for c in kept | leaving if c.startswith(parent)}
            check(f"{tag}: narrowing of {parent} accounts for every HTS line",
                  under <= mine, f"kept+leaving={len(mine)}, HTS={len(under)}, "
                  f"unaccounted={sorted(under - mine)}")

    # Note 51(c) carries the Section 232 exemption. The Sep 8 annexes repoint it
    # to dairy alone (exempt_232=False for alcohol and autos from Sep 15); the
    # Oct 23 annex must leave it alone.
    t_alc = " ".join(ex.read_pdf_layout(SRC / "338-alcohol-scope-annex-II.pdf").split())
    t_aut = " ".join(ex.read_pdf_layout(SRC / "338-autos-scope-annex-II.pdf").split())
    t_oct = ex.read_pdf_layout(SRC / ex.AMENDMENTS[-1]["annex_ii"])
    check("Sep 15: alcohol annex drops 9903.03.12 from note 51(c)",
          "Subdivision (c) of U.S. note 51 is modified by deleting “9903.03.12” "
          "and inserting “9903.03.13”" in t_alc)
    check("Sep 15: autos annex leaves note 51(c) naming heading 9903.03.13 only",
          re.search(r"Subdivision \(c\) of U\.S\. note 51 is modified by deleting "
                    r"“headings 9903\.03\.13.9903\.03\.14” and inserting "
                    r"“heading 9903\.03\.13”", t_aut) is not None)
    check("Oct 30: annex does not touch note 51(c)",
          "Subdivision (c)" not in t_oct)

    frames = {}
    for date, files in IN_FORCE.items():
        frames[date] = {f: set(pd.read_csv(TL / f, dtype=str)["HTSUS"]) for f in files}
        b = list(frames[date].values())
        shared = {c for i in range(len(b)) for j in range(len(b)) if i != j
                  for c in b[i] if covered(c, b[j])}
        check(f"{date}: baskets in force are disjoint", not shared,
              f"shared={sorted(shared)[:4]}")

    for pdf, n in BANS.items():
        banned = set(ex._codes(read_pdf(pdf)))
        check(f"Sep 29 ban {pdf}: {n} codes", len(banned) == n, f"got {len(banned)}")
        for date in ("2026-09-15", "2026-10-30"):
            union = set().union(*frames[date].values())
            out = sorted(c for c in banned if not covered(c, union))
            check(f"  every banned code in a basket in force on {date}", not out,
                  f"not covered={out[:5]}")

    for date in IN_FORCE:
        union = set().union(*frames[date].values())
        hit = d["HS8"].isin({c for c in union if len(c) == 8}) | d["HS10"].isin(
            {c for c in union if len(c) == 10})
        pp = 50 * d.loc[hit, "imports"].sum() / tot
        check(f"{date}: union impact == {EXPECT_UNION_PP_BY_DATE[date]}pp",
              abs(pp - EXPECT_UNION_PP_BY_DATE[date]) < 0.02,
              f"{len(union)} codes, {pp:.3f}pp")

    print("\n" + ("ALL VALIDATION PASSED" if ok else "VALIDATION FAILURES PRESENT"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
