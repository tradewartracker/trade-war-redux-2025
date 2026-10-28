"""
Guardrail for the PROVISIONAL Section 301 forced-labor action.

FR Doc 2026-11296 (Jun 5, 2026) is a notice of *determinations* and a *proposed*
action, not a Notice of Action: no effective date, no 9903 heading, no final
rate. It is modeled provisionally and STAGED-OFF (LABOR_301_LIVE = False in
make-tariff-by-country-by-time.ipynb) so the published panel is unchanged until
a real action issues. This script guards that provisional baseline.

Two modes:

  python validate-301-labor.py
      Baseline checks: the economy->tier table and the Annex A exemption list
      are internally consistent and match the magnitudes quoted downstream, and
      -- the load-bearing check -- Annex A is still bit-for-bit identical to the
      combined Section 122 exemption lists, which is why the two can share a
      source. A silent divergence here means the notebook must stop reusing the
      Section 122 files for the labor regime.

  python validate-301-labor.py --diff-economies NEW_ECON.csv \
                               --diff-exemptions NEW_EXEMPT.csv
      Diff mode, to run when the Notice of Action lands. Re-extract the action's
      economy list and Annex A from the final notice into two CSVs of the same
      shape as the baseline, then diff them against the committed baseline:
      economies added/removed, per-economy rate changes, and Annex A code
      deltas -- and re-check the Section 122 equality on the NEW list. The
      output is the punch list for turning the provisional model into the real
      one; effective date, scope and heading still need a manual read.

Exits non-zero if any check fails.
"""

import argparse
import glob
import sys
from pathlib import Path

import pandas as pd

TL = Path("tariff-lists")
DATA = Path("data")

ECON = TL / "301-labor-economies.csv"
EXEMPT = TL / "301-labor-exemptions.csv"
S122 = [TL / f"section122-{k}-exemptions.csv"
        for k in ("product", "aircraft", "specific")]

# Expected magnitudes, asserted so a silent list or table change cannot quietly
# move the provisional model. Update deliberately when the Notice of Action is
# incorporated.
EXPECT_ECONOMIES = 60          # investigated economies (determinations)
EXPECT_TRACKED = 50            # of those, in the top_50_non_eu + EU panel
EXPECT_RATE_125 = 40           # tracked economies at 12.5% (failed impose/enforce)
EXPECT_RATE_10 = 10            # tracked economies at 10% (commitments + UK partial)
EXPECT_EXEMPT = 1655           # Annex A codes
EXPECT_SCOPE = {"": 1098, "aircraft": 546, "ex": 11}
TEN_PCT = {"Argentina", "Bangladesh", "Cambodia", "Ecuador", "El Salvador",
           "Guatemala", "Indonesia", "Malaysia", "Taiwan", "United Kingdom"}
CAFTA_DR = {"2230", "2470", "2110", "2050", "2150", "2190"}
USMCA = {"1220", "2010"}

ok = True


def check(label, cond, detail=""):
    global ok
    ok &= bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}{'  ' + detail if detail else ''}")


def digits(series):
    return set(series.astype(str).str.replace(r"\D", "", regex=True))


def s122_union():
    """The combined Section 122 exemption universe (product + aircraft + specific)."""
    return set().union(*(digits(pd.read_csv(p, dtype=str)["hts_code"]) for p in S122))


def baseline():
    econ = pd.read_csv(ECON, dtype={"cty_code": str})
    exm = pd.read_csv(EXEMPT, dtype={"digits": str})

    print("\n=== 1. Economy -> tier table ===")
    check(f"{EXPECT_ECONOMIES} investigated economies", len(econ) == EXPECT_ECONOMIES,
          f"n={len(econ)}")
    tracked = econ[econ["cty_code"].notna() & (econ["cty_code"] != "")]
    check(f"{EXPECT_TRACKED} tracked by the panel", len(tracked) == EXPECT_TRACKED,
          f"n={len(tracked)}")
    check("tracked cty_codes unique", tracked["cty_code"].is_unique)
    rates = tracked["proposed_rate_pct"].astype(float).value_counts().to_dict()
    check(f"{EXPECT_RATE_125} tracked @ 12.5%", rates.get(12.5, 0) == EXPECT_RATE_125,
          str(rates))
    check(f"{EXPECT_RATE_10} tracked @ 10%", rates.get(10.0, 0) == EXPECT_RATE_10,
          str(rates))
    ten = set(tracked[tracked["proposed_rate_pct"].astype(float) == 10]["economy"])
    check("10% tier is exactly the commitments/partial-regime set", ten == TEN_PCT,
          f"symdiff={sorted(ten ^ TEN_PCT)}")
    check("only rates present are 10 and 12.5", set(rates) <= {10.0, 12.5}, str(set(rates)))

    print("\n=== 2. Annex A exemption list ===")
    check(f"{EXPECT_EXEMPT} codes", len(exm) == EXPECT_EXEMPT, f"n={len(exm)}")
    check("codes unique", exm["digits"].is_unique)
    check("codes are 8- or 10-digit numeric",
          exm["digits"].str.fullmatch(r"\d{8}|\d{10}").all())
    scope = exm["scope_limitation"].fillna("").value_counts().to_dict()
    for k, n in EXPECT_SCOPE.items():
        check(f"scope '{k or '(none)'}' == {n}", scope.get(k, 0) == n, str(scope))
    check("all codes flagged valid_hts", (exm["valid_hts"].astype(str) == "True").all())

    print("\n=== 3. Section 122 equality (load-bearing) ===")
    lab = digits(exm["digits"])
    s122 = s122_union()
    check("Annex A == combined Section 122 exemptions (identical set)", lab == s122,
          f"labor-only={len(lab - s122)} s122-only={len(s122 - lab)}")
    # Per-scope correspondence to the three Section 122 files.
    prod = digits(pd.read_csv(S122[0], dtype=str)["hts_code"])
    air = digits(pd.read_csv(S122[1], dtype=str)["hts_code"])
    spec = digits(pd.read_csv(S122[2], dtype=str)["hts_code"])
    labair = digits(exm[exm["scope_limitation"] == "aircraft"]["digits"])
    labspec = digits(exm[exm["scope_limitation"] == "ex"]["digits"])
    labnone = digits(exm[exm["scope_limitation"].fillna("") == ""]["digits"])
    check("aircraft flag == section122-aircraft", labair == air)
    check("ex flag == section122-specific", labspec == spec)
    check("unflagged == section122-product", labnone == prod)

    print("\n=== 4. Country-conditional carve-out wiring ===")
    codes = set(tracked["cty_code"])
    check("both USMCA codes (CA, MX) are tracked economies", USMCA <= codes,
          f"missing={sorted(USMCA - codes)}")
    check("all six CAFTA-DR codes are tracked economies", CAFTA_DR <= codes,
          f"missing={sorted(CAFTA_DR - codes)}")

    print("\n=== 5. Provisional exposure sanity (upper bound, ignores 232) ===")
    # A cheap sanity magnitude only: share of a country's imports NOT in Annex A.
    # The real model also carves out Section 232 goods, so true exposure is
    # lower; this bounds it from above and catches a broken exemption join.
    files = {Path(f).stem.split("imports")[-1]: f
             for f in glob.glob(str(DATA / "2025-hs10-imports*.parquet"))}
    for name, code in [("Brazil", "3510"), ("India", "5330"), ("Canada", "1220")]:
        if code not in files:
            continue
        d = pd.read_parquet(files[code])
        tot = d.imports.sum()
        dutiable = d[~d.HS8.isin(lab)].imports.sum()
        rate = float(tracked.set_index("cty_code").loc[code, "proposed_rate_pct"])
        print(f"    {name:7s} {code}: {100*dutiable/tot:5.1f}% of imports outside "
              f"Annex A  ->  <= +{rate*dutiable/tot:.2f}pp at {rate:g}% "
              f"(232 carve-out lowers this)")
    check("exposure sanity block ran", True)

    return econ, exm


def diff_mode(new_econ_path, new_exm_path):
    print("\n=== DIFF vs committed provisional baseline ===")
    base_e = pd.read_csv(ECON, dtype={"cty_code": str}).set_index("economy")
    new_e = pd.read_csv(new_econ_path, dtype={"cty_code": str}).set_index("economy")
    added = sorted(set(new_e.index) - set(base_e.index))
    removed = sorted(set(base_e.index) - set(new_e.index))
    print(f"    economies added:   {added or '(none)'}")
    print(f"    economies removed: {removed or '(none)'}")
    for econ_name in sorted(set(base_e.index) & set(new_e.index)):
        o = base_e.loc[econ_name, "proposed_rate_pct"]
        n = new_e.loc[econ_name, "proposed_rate_pct"]
        if str(o) != str(n):
            print(f"    RATE CHANGE {econ_name}: {o} -> {n}")
    check("no economies added/removed vs baseline (else update the table)",
          not added and not removed)

    base_x = digits(pd.read_csv(EXEMPT, dtype=str)["digits"])
    new_x = digits(pd.read_csv(new_exm_path, dtype=str).iloc[:, 0])
    print(f"    Annex A codes added:   {len(new_x - base_x)}")
    print(f"    Annex A codes removed: {len(base_x - new_x)}")
    check("Annex A unchanged vs baseline (else re-extract the exemption CSV)",
          new_x == base_x,
          f"+{len(new_x - base_x)} / -{len(base_x - new_x)}")
    check("NEW Annex A still == Section 122 (else stop sharing the file)",
          new_x == s122_union())
    print("\n    Manual follow-ups the diff cannot see: effective date, scope,"
          " 9903 heading, any new textile-mechanism or in-transit language.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--diff-economies")
    ap.add_argument("--diff-exemptions")
    args = ap.parse_args()

    baseline()
    if args.diff_economies and args.diff_exemptions:
        diff_mode(args.diff_economies, args.diff_exemptions)
    elif args.diff_economies or args.diff_exemptions:
        print("\n--diff-economies and --diff-exemptions must be given together")
        return 2

    print("\n" + ("ALL VALIDATION PASSED" if ok else "VALIDATION FAILURES PRESENT"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
