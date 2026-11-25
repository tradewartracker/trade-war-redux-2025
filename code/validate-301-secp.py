# -*- coding: utf-8 -*-
"""Guardrail for the PROPOSED Section 301 structural-excess-capacity (SECP)
lists (USTR notices of Nov 25, 2026), mirroring validate-301-labor.py.

Baseline mode recomputes everything from the committed CSVs and the Census
import parquet without importing the engine, so a silent edit to either list
fails loudly here. It pins:
  1. the economy table (14 economies, their three rates, netting, Section 232);
  2. the annex as printed (row counts, formats, scope flags);
  3. the two relationships the engine relies on: every notice carries the same
     common list, which is the forced-labor Annex II Part A list plus 8 codes;
     and China's Annex B is the U.S.-China 30-for-30 U.S. import list;
  4. how much 2024 trade the lists cover.

Diff mode reports what a later notice changed against the committed baseline:
    python code/validate-301-secp.py --diff-economies <economies.csv> --diff-annex <annex.csv>
Build the two files from the final notices with
    python code/extract-301-secp.py --prefix <prefix> --suffix -FINAL

Usage: python code/validate-301-secp.py   (exits non-zero on failure)
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]   # the repository root
TL = ROOT / "tariff-lists"
DATA = ROOT / "data"

# economy: (code, proposed, agreement, alternative, net of MFN, alt net of MFN, 232 exempt)
EXPECT_ECON = {
    "China":          ("5700", 20, None, 40, False, False, False),
    "European Union": ("0003", 15, None, 20, True,  True,  True),
    "Japan":          ("5880", 15, None, 20, True,  True,  True),
    "South Korea":    ("5800", 15, None, 25, True,  True,  True),
    "Switzerland":    ("4419", 15, None, 20, True,  True,  True),
    "Taiwan":         ("5830", 15, None, 25, True,  False, True),
    "Bangladesh":     ("5380", 18, None, 20, False, False, True),
    "Cambodia":       ("5550", 18, None, 25, False, False, True),
    "Indonesia":      ("5600", 18, None, 25, False, False, True),
    "Malaysia":       ("5570", 18, None, 25, False, False, True),
    "Thailand":       ("5490", 18, None, 25, False, False, True),
    "India":          ("5330", 25, 17,   None, False, False, True),
    "Singapore":      ("5590", 20, 10,   None, False, False, True),
    "Vietnam":        ("5520", 35, 20,   None, False, False, True),
}
EXPECT_COMMON = 2121
EXPECT_COMMON_FLAGS = {"": 864, "pharma": 700, "aircraft": 541, "ex": 16}
# Codes in the common list that the labor Annex II Part A CSV does not have.
# Seven are 10-digit statistical lines; the labor notice lists them too, but
# 301-labor-part-a.csv dropped them (an open issue, see METHODOLOGY.md).
# 2601.12.00, agglomerated iron ore, is new to this action.
EXPECT_NEW_VS_LABOR = {"0712908550", "1204000010", "1205100010", "1205900010",
                       "1206000031", "4407990295", "8505110070", "26011200"}
EXPECT_PART_II = {"European Union": 45, "Switzerland": 134, "Taiwan": 118,
                  "Bangladesh": 87, "Cambodia": 157, "Indonesia": 148, "Malaysia": 104}
EXPECT_ANNEX_B = 77
# Part II codes that the notices also print in the common list (agglomerated cork).
EXPECT_PART_II_IN_COMMON = {"45049000"}
# Share of each economy's 2024 imports in its ACTIVE annex list (scope flag ''
# or pharma; the common list plus Part II), percent. For China: Annex A.
EXPECT_ACTIVE_SHARE = {
    "China": 26.82, "European Union": 34.12, "Japan": 13.46, "South Korea": 21.77,
    "Switzerland": 60.64, "Taiwan": 65.66, "Bangladesh": 0.29, "Cambodia": 0.83,
    "Indonesia": 20.72, "Malaysia": 47.41, "Thailand": 32.36, "India": 32.81,
    "Singapore": 59.07, "Vietnam": 32.87,
}
# Share of 2024 imports in the active country-specific Part II alone, percent.
EXPECT_PART_II_SHARE = {"European Union": 0.38, "Switzerland": 0.52, "Taiwan": 0.07,
                        "Bangladesh": 0.00, "Cambodia": 0.39, "Indonesia": 9.19,
                        "Malaysia": 0.75}
EXPECT_ANNEX_B_BN = 29.63   # China, 30-for-30 list with ex-outs resolved, $B

ok = True


def check(label, cond, detail=""):
    global ok
    ok &= bool(cond)
    tail = "  " + detail if detail else ""
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}{tail}")


def load(econ_path, annex_path):
    econ = pd.read_csv(econ_path, dtype=str, keep_default_na=False)
    annex = pd.read_csv(annex_path, dtype=str, keep_default_na=False)
    return econ, annex


def common_of(annex, economy):
    g = annex[(annex.economy == economy) & (annex.part != "II")
              & ~((annex.economy == "China") & (annex.annex == "B"))]
    return dict(zip(g.digits, g.scope_limitation))


def baseline():
    econ, annex = load(TL / "301-secp-economies.csv", TL / "301-secp-annex.csv")

    print("=== 1. Economy table ===")
    check("14 economies, in the expected order", econ.economy.tolist() == list(EXPECT_ECON))
    panel = set(pd.read_csv(DATA / "top_50_non_eu.csv", dtype=str).CTY_CODE) | {"0003"}
    check("every economy is in the tracked panel", set(econ.cty_code) <= panel,
          f"missing={sorted(set(econ.cty_code) - panel)}")

    def num(x):
        return None if x == "" else float(x)
    bad = []
    for r in econ.itertuples():
        got = (r.cty_code, num(r.proposed_rate_pct), num(r.agreement_rate_pct),
               num(r.alternative_rate_pct), r.net_of_mfn == "True",
               r.alternative_net_of_mfn == "True", r.exempt_232 == "True")
        if got != tuple(EXPECT_ECON.get(r.economy, ())):
            bad.append((r.economy, got))
    check("rates, netting and Section 232 treatment as pinned", not bad, f"{bad}" if bad else "")
    check("only China lacks the Section 232 exemption",
          econ.loc[econ.exempt_232 != "True", "economy"].tolist() == ["China"])
    cn = econ[econ.economy == "China"].iloc[0]
    check("China: Annex A tier is 10% and the alternative ignores the annexes",
          cn.annex_a_rate_pct == "10.0" and cn.alternative_ignores_annexes == "True")
    check("no effective or end dates yet (a proposal)",
          (econ.effective_date == "").all() and (econ.end_date == "").all())

    labor = pd.read_csv(TL / "301-labor-economies-FINAL.csv", dtype=str, keep_default_na=False)
    tier = dict(zip(labor.cty_code, labor.proposed_rate_pct.astype(float)))
    check("every economy already pays the forced-labor duty", set(econ.cty_code) <= set(tier))
    below = [(r.economy, num(r.agreement_rate_pct), tier[r.cty_code]) for r in econ.itertuples()
             if num(r.agreement_rate_pct) is not None and num(r.agreement_rate_pct) < tier[r.cty_code]]
    check("every proposed cap is above the labor tier",
          all(float(r.proposed_rate_pct) > tier[r.cty_code] for r in econ.itertuples()))
    print(f"    NOTE: agreement rates below the labor tier (new duty would be zero): {below}")

    print("\n=== 2. Annex as printed ===")
    check("scope flags are '', pharma, aircraft or ex",
          set(annex.scope_limitation) <= {"", "pharma", "aircraft", "ex"})
    check("codes are 8 or 10 digits and match their printed form",
          annex.digits.str.len().isin([8, 10]).all()
          and (annex.htsus.str.replace(".", "", regex=False) == annex.digits).all())
    check("no code repeats within an economy's annex part",
          not annex.duplicated(["economy", "annex", "part", "digits"]).any())
    check("every economy in the table has an annex", set(annex.economy) == set(EXPECT_ECON))

    print("\n=== 3. The common list ===")
    ref = common_of(annex, "Japan")
    check(f"{EXPECT_COMMON} codes", len(ref) == EXPECT_COMMON, f"{len(ref)}")
    flags = pd.Series(ref).value_counts().to_dict()
    check("scope flags as pinned", flags == EXPECT_COMMON_FLAGS, f"{flags}")
    differ = [e for e in EXPECT_ECON if common_of(annex, e) != ref]
    check("identical in all 14 notices, codes and flags", not differ, f"differ={differ}")
    lab = pd.read_csv(TL / "301-labor-part-a.csv", dtype=str, keep_default_na=False)
    L = dict(zip(lab.digits, lab.scope_limitation))
    check("contains every forced-labor Annex II Part A code", set(L) <= set(ref),
          f"missing={sorted(set(L) - set(ref))}")
    check("same scope flag on every shared code", all(ref[k] == L[k] for k in L if k in ref))
    new = set(ref) - set(L)
    check("the 8 codes beyond the labor CSV are the pinned ones", new == EXPECT_NEW_VS_LABOR,
          f"{sorted(new ^ EXPECT_NEW_VS_LABOR)}" if new != EXPECT_NEW_VS_LABOR else "")

    print("\n=== 4. Country-specific Part II ===")
    p2 = annex[annex.part == "II"]
    got = p2.groupby("economy").size().to_dict()
    check("Part II row counts as pinned", got == EXPECT_PART_II, f"{got}")
    both = set(p2.digits) & set(ref)
    check("Part II overlaps the common list only in the pinned codes",
          both == EXPECT_PART_II_IN_COMMON, f"{sorted(both)}")
    bo = pd.read_csv(TL / "301-labor-parts-BO.csv", dtype=str, keep_default_na=False)
    for e, code in [(e, v[0]) for e, v in EXPECT_ECON.items() if e in EXPECT_PART_II]:
        s = set(p2.loc[p2.economy == e, "digits"])
        lp = set(bo.loc[bo.cty_code == code, "digits"])
        print(f"    {e:15s} Part II {len(s):4d} | labor country part {len(lp):4d} | "
              f"shared {len(s & lp):4d} | new here {len(s - lp):3d} | labor only {len(lp - s):3d}")

    print("\n=== 5. China ===")
    b = annex[(annex.economy == "China") & (annex.annex == "B")]
    us = pd.read_csv(TL / "china-30for30-us-import-list.csv", dtype=str, keep_default_na=False)
    check(f"Annex B has {EXPECT_ANNEX_B} codes", len(b) == EXPECT_ANNEX_B, f"{len(b)}")
    check("Annex B is the 30-for-30 U.S. import list", set(b.digits) == set(us.HTSUS))
    check("Annex B 'ex' rows are the list's ex-outs",
          set(b.loc[b.scope_limitation == "ex", "digits"]) == set(us.loc[us.ex_out == "X", "HTSUS"]))
    model = pd.read_csv(TL / "china-30for30-model-list.csv", dtype=str, keep_default_na=False)
    check("the engine's 30-for-30 model list maps onto Annex B",
          set(model.list_hts8) == set(b.digits))
    a_act = set(annex.loc[(annex.economy == "China") & (annex.annex == "A")
                          & annex.scope_limitation.isin(["", "pharma"]), "digits"])
    ov = {c for c in model.HTSUS if c in a_act or c[:8] in a_act}
    check("no 30-for-30 line is in the active Annex A tier", not ov, f"{sorted(ov)}")

    print("\n=== 6. 2024 trade covered (import shares, percent) ===")
    active = annex[annex.scope_limitation.isin(["", "pharma"])]
    got_act, got_p2 = {}, {}
    for e, v in EXPECT_ECON.items():
        code = v[0]
        d = pd.read_parquet(DATA / f"2024-hs10-imports{code}.parquet", columns=["HS10", "imports"])
        d["HS8"] = d.HS10.str[:8]
        g = active[(active.economy == e) & ~((active.economy == "China") & (active.annex == "B"))]
        m = d.HS8.isin(g.digits) | d.HS10.isin(g.digits)
        got_act[e] = round(100 * d.loc[m, "imports"].sum() / d.imports.sum(), 2)
        g2 = g[g.part == "II"]
        if len(g2):
            m2 = d.HS8.isin(g2.digits) | d.HS10.isin(g2.digits)
            got_p2[e] = round(100 * d.loc[m2, "imports"].sum() / d.imports.sum(), 2)
        if e == "China":
            mb = d.HS8.isin(model.HTSUS) | d.HS10.isin(model.HTSUS)
            bn = d.loc[mb, "imports"].sum() / 1e9
    for e in EXPECT_ECON:
        tail = f"   Part II {got_p2[e]:5.2f}" if e in got_p2 else ""
        print(f"    {e:15s} active annex {got_act[e]:6.2f}{tail}")
    off = {e: float(got_act[e]) for e in EXPECT_ECON
           if abs(got_act[e] - EXPECT_ACTIVE_SHARE.get(e, -1)) >= 0.02}
    check("active-annex shares as pinned", not off, f"{off}" if off else "")
    off2 = {e: float(v) for e, v in got_p2.items()
            if abs(v - EXPECT_PART_II_SHARE.get(e, -1)) >= 0.02}
    check("Part II shares as pinned",
          got_p2.keys() == EXPECT_PART_II_SHARE.keys() and not off2, f"{off2}" if off2 else "")
    check(f"China Annex B covers ${EXPECT_ANNEX_B_BN}B", abs(bn - EXPECT_ANNEX_B_BN) < 0.05, f"{bn:.2f}")

    print("\n" + ("ALL VALIDATION PASSED" if ok else "VALIDATION FAILURES PRESENT"))
    return 0 if ok else 1


def diff(econ_path, annex_path):
    """Report what a later notice changed against the committed baseline."""
    e0, a0 = load(TL / "301-secp-economies.csv", TL / "301-secp-annex.csv")
    e1, a1 = load(econ_path, annex_path)

    print("=== Economies ===")
    for e in sorted(set(e0.economy) - set(e1.economy)):
        print(f"  dropped: {e}")
    for e in sorted(set(e1.economy) - set(e0.economy)):
        print(f"  added:   {e}")
    cols = [c for c in e0.columns if c not in ("basis", "source")]
    m = e0.merge(e1, on="economy", suffixes=("_old", "_new"))
    for r in m.to_dict("records"):
        ch = [f"{c}: {r[c + '_old']!r} -> {r[c + '_new']!r}" for c in cols
              if c != "economy" and c + "_new" in r and r[c + "_old"] != r[c + "_new"]]
        if ch:
            print(f"  {r['economy']}: " + "; ".join(ch))

    print("\n=== Annex ===")
    key = ["economy", "annex", "part"]
    for k, g1 in a1.groupby(key):
        g0 = a0[(a0.economy == k[0]) & (a0.annex == k[1]) & (a0.part == k[2])]
        f0, f1 = dict(zip(g0.digits, g0.scope_limitation)), dict(zip(g1.digits, g1.scope_limitation))
        added, removed = sorted(set(f1) - set(f0)), sorted(set(f0) - set(f1))
        flag = sorted(c for c in set(f0) & set(f1) if f0[c] != f1[c])
        name = " ".join(x for x in (k[0], f"Annex {k[1]}" if k[1] else "", f"Part {k[2]}" if k[2] else "") if x)
        print(f"  {name:28s} {len(f0):5d} -> {len(f1):5d} codes | +{len(added)} -{len(removed)} | "
              f"{len(flag)} scope flags changed")
        for label, codes in (("added", added), ("removed", removed), ("flag changed", flag)):
            if codes:
                print(f"      {label}: {', '.join(codes[:12])}{' ...' if len(codes) > 12 else ''}")
    gone = sorted(set(map(tuple, a0[key].drop_duplicates().values)) -
                  set(map(tuple, a1[key].drop_duplicates().values)))
    if gone:
        print(f"  annex parts no longer present: {gone}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--diff-economies", help="economies CSV built from a later notice")
    ap.add_argument("--diff-annex", help="annex CSV built from a later notice")
    args = ap.parse_args()
    if args.diff_economies or args.diff_annex:
        if not (args.diff_economies and args.diff_annex):
            ap.error("diff mode needs both --diff-economies and --diff-annex")
        sys.exit(diff(args.diff_economies, args.diff_annex))
    sys.exit(baseline())
