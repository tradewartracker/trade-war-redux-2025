# -*- coding: utf-8 -*-
"""Guardrail for the U.S.-China "30-for-30" U.S. import list (White House,
Sep 27, 2026), mirroring validate-timber.py. Recomputes everything from the
committed CSVs and the Census import parquet without importing the engine, so a
silent edit to either list fails loudly here.

Also pins the two facts the staged regime relies on: (1) no listed code is in a
modeled Section 232 list or an active labor Annex II Part A exemption, which is
why reversing the 12.5% labor duty nets the list to exactly zero added tariff;
and (2) the size of that reversal on China's rate.

Usage: python validate-china-30for30.py   (exits non-zero on failure)
"""
import re
import sys
from pathlib import Path
import pandas as pd

TL = Path("tariff-lists")
DATA = Path("data")
CHINA = "5700"

EXPECT_N_RAW = 77
EXPECT_EX_OUT = {"94017100", "94017900", "94018020", "94018040", "94018060",
                 "94037040", "94037080", "95030000"}
EXPECT_N_HS10 = 13
EXPECT_CHAPTERS = {"36", "39", "63", "66", "67", "84", "85", "94", "95", "96"}
# 2024 China imports covered. The Terms of Reference value the list at ~$30B of
# calendar-2024 trade. Flat HS8 overstates it because the 9401/9403 ex-outs are
# a small juvenile slice of large seat/furniture lines; the resolved figure is
# the one that lands on "roughly $30 billion".
EXPECT_FLAT_B = 32.45
EXPECT_RESOLVED_B = 29.63
# 12.5 x resolved import share of China = the China rate step if the list is
# excluded from the labor 301 (2024 weights). Asserted so a list change cannot
# quietly move the figure quoted in the README / analysis notebook.
EXPECT_CHINA_PP = 0.863
# Products named in the ex-out descriptions; every resolved HS10 Census label
# must name one of them.
KEYWORDS = re.compile(r"HIGHCHAIR|WALKER|BOUNCER|SWING|CHILDREN.S SEATS|"
                      r"CHILD SAFETY|PLAY YARD")
# Suffixes under a resolved parent that name a keyword product but are
# deliberately NOT included, because the parent's own description omits them:
# 9401.71.0007 swings (the 9401.71.00 text names highchairs, walkers, bouncers
# only, whereas 9401.79.00 does name swings).
ALLOWED_UNINCLUDED = {"9401710007"}

ok = True


def check(label, cond, detail=""):
    global ok
    ok &= bool(cond)
    tail = "  " + detail if detail else ""
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}{tail}")


def _codes(path, col="HTSUS"):
    s = pd.read_csv(path, dtype=str)[col].dropna()
    return set(s.str.replace(".", "", regex=False).str.strip())


def main():
    print("=== 1. Raw list matches the PDF as printed ===")
    raw = pd.read_csv(TL / "china-30for30-us-import-list.csv", dtype={"HTSUS": str})
    check(f"{EXPECT_N_RAW} rows", len(raw) == EXPECT_N_RAW, f"{len(raw)}")
    check("numbered 1..77 in order", raw.no.tolist() == list(range(1, EXPECT_N_RAW + 1)))
    check("all 8-digit, unique, ascending",
          raw.HTSUS.str.len().eq(8).all() and raw.HTSUS.is_unique
          and raw.HTSUS.is_monotonic_increasing)
    got_ex = set(raw.loc[raw.ex_out == "X", "HTSUS"])
    check("ex-out rows are the 8 expected codes", got_ex == EXPECT_EX_OUT,
          "" if got_ex == EXPECT_EX_OUT else f"{sorted(got_ex ^ EXPECT_EX_OUT)}")
    check("chapters as expected", set(raw.HTSUS.str[:2]) == EXPECT_CHAPTERS,
          f"{sorted(set(raw.HTSUS.str[:2]))}")
    hts8 = {c[:8] for c in _codes(TL / "hts-general-rates.csv", col="code")}
    check("every code is a valid HTS8 (hts-general-rates.csv)",
          set(raw.HTSUS) <= hts8, f"invalid={sorted(set(raw.HTSUS) - hts8)}")

    print("\n=== 2. Model list is the raw list with the juvenile ex-outs resolved ===")
    model = pd.read_csv(TL / "china-30for30-model-list.csv",
                        dtype={"HTSUS": str, "list_hts8": str})
    hs8 = model[model.HTSUS.str.len() == 8]
    hs10 = model[model.HTSUS.str.len() == 10]
    resolved_parents = EXPECT_EX_OUT - {"95030000"}
    check("every model row maps to a raw row", set(model.list_hts8) == set(raw.HTSUS))
    check(f"{EXPECT_N_HS10} HS10 rows resolving 7 parents",
          len(hs10) == EXPECT_N_HS10 and set(hs10.list_hts8) == resolved_parents,
          f"{len(hs10)} rows, parents={sorted(set(hs10.list_hts8))}")
    check("HS10 rows sit under their parent", (hs10.HTSUS.str[:8] == hs10.list_hts8).all())
    check("HS8 rows = raw minus the 7 resolved parents",
          set(hs8.HTSUS) == set(raw.HTSUS) - resolved_parents)
    check("only 9503.00.00 is flagged flat",
          set(model.loc[model.resolution == "flat", "HTSUS"]) == {"95030000"})
    check("no duplicate codes", model.HTSUS.is_unique)

    print("\n=== 3. Codes observed in 2024 China trade; HS10 labels match the ex-out text ===")
    d = pd.read_parquet(DATA / f"2024-hs10-imports{CHINA}.parquet")
    d["HS8"] = d.HS10.str[:8]
    lab = dict(zip(d.HS10, d.I_COMMODITY_SDESC))
    absent8 = set(hs8.HTSUS) - set(d.HS8)
    if absent8:
        print(f"    NOTE: HS8 codes with no 2024 China trade (harmless): {sorted(absent8)}")
    check("at most 2 HS8 codes unobserved", len(absent8) <= 2)
    check("all resolved HS10 codes observed", set(hs10.HTSUS) <= set(d.HS10),
          f"absent={sorted(set(hs10.HTSUS) - set(d.HS10))}")
    bad = [c for c in hs10.HTSUS if not KEYWORDS.search(lab.get(c, ""))]
    check("every resolved HS10 label names a listed juvenile product", not bad,
          f"{[(c, lab.get(c)) for c in bad]}")
    under = d[d.HS8.isin(resolved_parents) & ~d.HS10.isin(hs10.HTSUS)]
    named = set(under.loc[under.I_COMMODITY_SDESC.str.contains(KEYWORDS), "HS10"])
    check("no unincluded suffix names a listed product (except 9401.71 swings)",
          named <= ALLOWED_UNINCLUDED, f"{sorted(named - ALLOWED_UNINCLUDED)}")

    print("\n=== 4. Value covered (2024 China imports) ===")
    tot = d.imports.sum()
    flat = d[d.HS8.isin(raw.HTSUS)].imports.sum() / 1e9
    m = d.HS8.isin(hs8.HTSUS) | d.HS10.isin(hs10.HTSUS)
    res = d[m].imports.sum() / 1e9
    share = d.loc[m, "share"].sum()
    print(f"    flat-HS8 ${flat:.2f}B   resolved ${res:.2f}B = {100*share:.2f}% "
          f"of China imports (${tot/1e9:.1f}B)")
    check(f"flat value == ${EXPECT_FLAT_B}B", abs(flat - EXPECT_FLAT_B) < 0.05, f"{flat:.2f}")
    check(f"resolved value == ${EXPECT_RESOLVED_B}B", abs(res - EXPECT_RESOLVED_B) < 0.05,
          f"{res:.2f}")
    check("resolved value is 'roughly $30 billion' (25-35)", 25 <= res <= 35)

    print("\n=== 5. Interaction with the engine's other lists (why the reversal nets to zero) ===")
    l8, l10 = set(hs8.HTSUS), set(hs10.HTSUS)
    parents8 = l8 | {c[:8] for c in l10}

    def overlap(codes):
        hit = set()
        for c in codes:
            if len(c) == 10 and (c in l10 or c[:8] in l8):
                hit.add(c)
            elif len(c) == 8 and c in parents8:
                hit.add(c)
            elif len(c) == 6 and any(x.startswith(c) for x in parents8):
                hit.add(c)
        return hit

    for f in ["steel-tariffs", "alu-tariffs", "auto-tariffs", "copper-list", "timber-232",
              "metals-annex-IA", "metals-annex-IB", "metals-annex-III-temporary"]:
        ov = overlap(_codes(TL / f"{f}.csv"))
        check(f"disjoint from {f}", not ov, f"overlap={sorted(ov)}")
    pa = pd.read_csv(TL / "301-labor-part-a.csv", dtype=str)
    active = set(pa.loc[pa.scope_limitation.fillna("").isin(["", "pharma"]), "digits"])
    ov = overlap(active)
    check("disjoint from the ACTIVE labor Part A exemptions (unconditional + pharma)",
          not ov, f"overlap={sorted(ov)}")
    rem = _codes(TL / "metals-annex-II-removed.csv") & parents8
    print(f"    NOTE: codes removed from 232 scope by metals Annex II on Apr 6, 2026 "
          f"(now non-232, so dutiable and reversible): {sorted(rem)}")

    print("\n=== 6. China rate impact of excluding the list from the 12.5% labor 301 (2024 weights) ===")
    pp = 12.5 * share
    print(f"    12.5 x {100*share:.2f}% = -{pp:.3f}pp on China's effective tariff")
    check(f"China impact == -{EXPECT_CHINA_PP}pp", abs(pp - EXPECT_CHINA_PP) < 0.01, f"{pp:.3f}")

    print("\n" + ("ALL VALIDATION PASSED" if ok else "VALIDATION FAILURES PRESENT"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
