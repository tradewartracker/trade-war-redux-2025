# -*- coding: utf-8 -*-
"""Independent second opinion on the Section 232 timber/lumber list
(Proclamation 10976, U.S. note 37), mirroring validate-338.py.

Unlike the engine, this recomputes everything from the committed list and the
Census import parquet, so a silent edit to timber-232.csv that would move the
published numbers fails loudly here. Does NOT import the tariff engine.

Usage: python code/validate-timber.py   (exits non-zero on failure)
"""
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]   # the repository root
TL = ROOT / "tariff-lists"
DATA = ROOT / "data"
CANADA = "1220"

# The 22 codes exactly as enumerated in Proclamation 10976, U.S. note 37.
# Hardcoded here as the authority so the CSV is checked against the annex,
# the same guard style as extract-301-exemptions.py's SUBDIVISIONS.
EXPECT = {
    "softwood": {  # 9903.76.01, HS8, 10% all countries
        "44031100", "44032101", "44032201", "44032301", "44032401", "44032501",
        "44032601", "44039901", "44061100", "44069100", "44071100", "44071200",
        "44071300", "44071400", "44071900",
    },
    "furniture": {  # 9903.76.02, HS10, 25% (UK 10 / JP 15 / EU 15)
        "9401614011", "9401614031", "9401616011", "9401616031",
    },
    "cabinet": {  # 9903.76.03, HS10, 25% (UK 10 / JP 15 / EU 15)
        "9403409060", "9403608093", "9403910080",
    },
}
# Canada timber rate impact (2025 weights), asserted so a list change cannot
# quietly move the published country-by-time figure. Softwood 10 / furn 25 / cab 25.
EXPECT_CANADA_PP = 0.186

ok = True


def check(label, cond, detail=""):
    global ok
    ok &= bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}{'  ' + detail if detail else ''}")


def main():
    print("=== 1. List parses and matches the Proclamation 10976 annex ===")
    df = pd.read_csv(TL / "timber-232.csv", dtype={"HTSUS": str})
    got = {cat: set(df[df.category == cat]["HTSUS"]) for cat in EXPECT}
    for cat, exp in EXPECT.items():
        check(f"{cat}: {len(exp)} codes match the annex exactly",
              got.get(cat) == exp,
              "" if got.get(cat) == exp else f"missing={sorted(exp - got.get(cat, set()))} "
              f"extra={sorted(got.get(cat, set()) - exp)}")
    check("no codes outside the three categories",
          set(df.category) == set(EXPECT), f"{sorted(set(df.category))}")
    check("no duplicate codes", df.HTSUS.is_unique)
    check("softwood are HS8, furniture/cabinet are HS10",
          all(len(c) == 8 for c in got["softwood"])
          and all(len(c) == 10 for c in got["furniture"] | got["cabinet"]))

    print("\n=== 2. Codes are observed in the Census import universe ===")
    files = sorted(DATA.glob("2025-hs10-imports*.parquet"))
    hs8u, hs10u = set(), set()
    for f in files:
        d = pd.read_parquet(f, columns=["HS10"])
        hs10u |= set(d.HS10.unique())
        hs8u |= set(d.HS10.str[:8].unique())
    print(f"    HS8 universe {len(hs8u):,} / HS10 universe {len(hs10u):,} "
          f"across {len(files)} files")
    soft_abs = got["softwood"] - hs8u
    hs10_abs = (got["furniture"] | got["cabinet"]) - hs10u
    # A code enumerated in the annex but unobserved in 2025 trade (e.g. 44061100,
    # wooden railway sleepers) carries no weight and is harmless; the exact-annex
    # match in section 1 already guards against typos, so absence is a NOTE, not a
    # failure — same posture as validate-338.py for its unshipped basket codes.
    if soft_abs:
        print(f"    NOTE: softwood codes with no 2025 trade (harmless): {sorted(soft_abs)}")
    check("most softwood HS8 codes observed in trade", len(soft_abs) <= 2,
          f"{len(got['softwood']) - len(soft_abs)}/{len(got['softwood'])} observed")
    check("all furniture/cabinet HS10 codes observed in trade (value drivers)",
          not hs10_abs, f"absent={sorted(hs10_abs)}")

    print("\n=== 3. Timber softwood is disjoint from the Section 338 baskets ===")
    # Load-bearing fact behind the ch44 correction: none of the softwood timber
    # codes fall in a 338 basket, so modeling timber does not carve the basket's
    # 64 (non-232) chapter-44 hardwood/plywood codes out of the 338 duty.
    for b in ["canada-338-autos", "canada-338-alcohol", "canada-338-dairy"]:
        codes = set(pd.read_csv(TL / f"{b}.csv", dtype=str)["HTSUS"])
        check(f"softwood disjoint from {b}", not (got["softwood"] & codes),
              f"overlap={sorted(got['softwood'] & codes)}")
    # The only timber good in any basket is the single cabinet line, by design.
    autos = set(pd.read_csv(TL / "canada-338-autos.csv", dtype=str)["HTSUS"])
    cab_overlap = {c for c in got["cabinet"] if c[:8] in autos}
    check("exactly one cabinet code overlaps the autos basket (9403608093)",
          cab_overlap == {"9403608093"}, f"{sorted(cab_overlap)}")

    print("\n=== 4. Canada rate impact magnitude (2025 weights) ===")
    d = pd.read_parquet(DATA / f"2025-hs10-imports{CANADA}.parquet")
    tot = d.imports.sum()
    sv = d[d.HS8.isin(got["softwood"])].imports.sum()
    fv = d[d.HS10.isin(got["furniture"])].imports.sum()
    cv = d[d.HS10.isin(got["cabinet"])].imports.sum()
    pp = (10 * sv + 25 * fv + 25 * cv) / tot
    print(f"    softwood ${sv/1e9:.3f}B  furniture ${fv/1e9:.3f}B  "
          f"cabinet ${cv/1e9:.3f}B  ->  +{pp:.3f}pp on Canada")
    check(f"Canada timber impact == {EXPECT_CANADA_PP}pp",
          abs(pp - EXPECT_CANADA_PP) < 0.01, f"{pp:.3f}pp")

    print("\n" + ("ALL VALIDATION PASSED" if ok else "VALIDATION FAILURES PRESENT"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
