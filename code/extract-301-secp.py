# -*- coding: utf-8 -*-
"""Extract the PROPOSED Section 301 actions on structural excess capacity and
production (SECP) into two CSVs in tariff-lists/.

Source: the 14 pre-publication Federal Register notices USTR released on
Nov 25, 2026 ("Notice of Determination and Request for Comments Concerning
Proposed Action in the Section 301 Investigation of Acts, Policies, and
Practices of <economy> Relating to Structural Excess Capacity and Production in
Manufacturing Sectors"), saved as tariff-lists/sources/301-secp-proposed-*.pdf.
These are PROPOSALS: no effective date, no chapter 99 heading, and every rate is
"up to". Comments are due Jan 5, 2027 and the hearing is Jan 25, 2027.

Outputs
  301-secp-economies.csv — one row per economy per period: the proposed rate,
      the rate tied to an agreement (India, Singapore, Vietnam), the stated
      alternative, whether the rate is net of MFN, and whether Section 232 goods
      are exempt. The rates are entered in ECONOMIES below and each one is
      pinned to a phrase that must appear in the notice's proposed-action text.
  301-secp-annex.csv — every annex row as printed, for all 14 economies:
      economy, cty_code, annex, part, htsus, digits, description,
      scope_limitation ('' / pharma / aircraft / ex), source_page.

The annex is a list of goods NOT covered by the proposed action, except for
China: China's Annex A goods take a lower rate (up to 10%) and its Annex B (the
U.S.-China "30-for-30" U.S. import list) is the exemption.

When the final notices issue, save them alongside and re-run with
--srcdir/--prefix pointing at them, then diff with validate-301-secp.py.

Usage: python code/extract-301-secp.py
"""
import argparse
import re
import sys
from pathlib import Path

import pandas as pd
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]   # the repository root
TL = ROOT / "tariff-lists"

NET_MFN = "net of MFN rates and existing Section 301 tariffs"
NET_301 = "net of existing Section 301 tariffs"
NET_LABOR = ("net of the rate of duty applied to the good under the Section 301 "
             "investigation related to China's failure to impose and effectively "
             "enforce a prohibition on the importation of goods produced with "
             "forced labor")

# One entry per economy, in the order of the USTR release. Rates are percent.
#   proposed     the rate the notice proposes ("up to")
#   agreement    the rate the notice ties to a responsive agreement, if any
#   alternative  the higher rate proposed if consultations prove unsatisfactory
#   net_mfn      the proposed rate is net of the column-1 MFN rate
#   alt_net_mfn  the alternative rate is net of MFN
#   phrases      text that must appear in the proposed-action section
ECONOMIES = [
    dict(economy="China", cty_code="5700", stem="china",
         proposed=20, agreement=None, alternative=40, net_mfn=False, alt_net_mfn=False,
         annex_a_rate=10, alternative_ignores_annexes=True, exempt_232=False,
         phrases=[f"tariffs of up to 20 percent, {NET_LABOR}",
                  "on goods of China not identified in the Annexes to this Notice",
                  "up to 10 percent tariffs on goods identified in Annex A",
                  "exemptions for certain goods identified in Annex B",
                  f"a tariff of up to 40 percent, {NET_LABOR}, on all goods of China"],
         basis="20% net of the forced-labor 301 duty on goods outside the annexes; "
               "up to 10% on Annex A goods; Annex B (30-for-30 list) exempt. "
               "Alternative: 40% net of the labor duty on all goods. The notice "
               "does not mention Section 232."),
    dict(economy="European Union", cty_code="0003", stem="eu",
         proposed=15, agreement=None, alternative=20, net_mfn=True, alt_net_mfn=True,
         phrases=[f"a tariff rate of 15 percent, {NET_MFN}",
                  f"up to 20 percent, {NET_MFN}",
                  "this adjustment terminate on December 1, 2028"],
         adjustment_terminates="2028-12-01",
         basis="15% all-in, net of MFN and existing 301 (Framework Agreement); "
               "alternative 20%. 'This adjustment' is proposed to terminate "
               "Dec 1, 2028 - not acted on by the engine."),
    dict(economy="Japan", cty_code="5880", stem="japan",
         proposed=15, agreement=None, alternative=20, net_mfn=True, alt_net_mfn=True,
         phrases=[f"tariffs of up to 15 percent, {NET_MFN}", f"up to 20 percent, {NET_MFN}"],
         basis="15% all-in, net of MFN and existing 301; alternative 20%."),
    dict(economy="South Korea", cty_code="5800", stem="korea",
         proposed=15, agreement=None, alternative=25, net_mfn=True, alt_net_mfn=True,
         phrases=[f"of up to 15 percent, {NET_MFN}", f"up to 25 percent, {NET_MFN}"],
         basis="15% all-in, net of MFN and existing 301; alternative 25%. The "
               "engine models Korea flat, as it does the labor duty."),
    dict(economy="Switzerland", cty_code="4419", stem="switzerland",
         proposed=15, agreement=None, alternative=20, net_mfn=True, alt_net_mfn=True,
         phrases=[f"tariffs of up to 15 percent, {NET_MFN}", f"up to 20 percent, net of MFN "
                  "rates and existing Section 301 tariffs"],
         basis="15% all-in, net of MFN and existing 301; alternative 20%."),
    dict(economy="Taiwan", cty_code="5830", stem="taiwan",
         proposed=15, agreement=None, alternative=25, net_mfn=True, alt_net_mfn=False,
         phrases=[f"of up to 15 percent, {NET_MFN}", f"up to 25 percent, {NET_301}"],
         basis="15% all-in, net of MFN and existing 301; alternative 25%, net of "
               "existing 301 only."),
    dict(economy="Bangladesh", cty_code="5380", stem="bangladesh",
         proposed=18, agreement=None, alternative=20, net_mfn=False, alt_net_mfn=False,
         phrases=[f"of up to 18 percent, {NET_301}", f"up to 20 percent, {NET_301}"],
         basis="18% net of existing 301; alternative 20%."),
    dict(economy="Cambodia", cty_code="5550", stem="cambodia",
         proposed=18, agreement=None, alternative=25, net_mfn=False, alt_net_mfn=False,
         phrases=[f"of up to 18 percent, {NET_301}", f"up to 25 percent, {NET_301}"],
         basis="18% net of existing 301; alternative 25%."),
    dict(economy="Indonesia", cty_code="5600", stem="indonesia",
         proposed=18, agreement=None, alternative=25, net_mfn=False, alt_net_mfn=False,
         phrases=[f"of up to 18 percent, {NET_301}", f"up to 25 percent, {NET_301}"],
         basis="18% net of existing 301; alternative 25%."),
    dict(economy="Malaysia", cty_code="5570", stem="malaysia",
         proposed=18, agreement=None, alternative=25, net_mfn=False, alt_net_mfn=False,
         phrases=[f"of up to 18 percent, {NET_301}", f"up to 25 percent, {NET_301}"],
         basis="18% net of existing 301; alternative 25%."),
    dict(economy="Thailand", cty_code="5490", stem="thailand",
         proposed=18, agreement=None, alternative=25, net_mfn=False, alt_net_mfn=False,
         phrases=[f"of up to 18 percent, {NET_301}", f"up to 25 percent, {NET_301}"],
         basis="18% net of existing 301; alternative 25%."),
    dict(economy="India", cty_code="5330", stem="india",
         proposed=25, agreement=17, alternative=None, net_mfn=False, alt_net_mfn=False,
         phrases=[f"tariffs of up to 25 percent on all goods of India, {NET_301}",
                  "a tariff rate of 17 percent, were India to reach an Agreement on "
                  "Reciprocal Trade"],
         basis="25% net of existing 301; 17% if India reaches a responsive "
               "Agreement on Reciprocal Trade."),
    dict(economy="Singapore", cty_code="5590", stem="singapore",
         proposed=20, agreement=10, alternative=None, net_mfn=False, alt_net_mfn=False,
         phrases=[f"tariffs of up to 20 percent, {NET_301}, on all goods of Singapore",
                  "adjusting the tariff rate applied to each good to 10 percent"],
         basis="20% net of existing 301; 10% if Singapore concludes a responsive "
               "agreement (below the 12.5% labor duty, so the new duty would be zero)."),
    dict(economy="Vietnam", cty_code="5520", stem="vietnam",
         proposed=35, agreement=20, alternative=None, net_mfn=False, alt_net_mfn=False,
         phrases=[f"tariffs of up to 35 percent, {NET_301}, on all goods of Vietnam",
                  "a tariff rate of 20 percent, were Vietnam to reach an Agreement on "
                  "Reciprocal Trade"],
         basis="35% net of existing 301; 20% if Vietnam reaches a responsive "
               "Agreement on Reciprocal Trade."),
]

S232_PHRASE = "currently subject to tariffs under Section 232 of the Trade Expansion Act of 1962"
DATE_PHRASES = ["January 5, 2027", "January 25, 2027"]

# Annex rows per economy, as printed: {(annex, part): rows}. Asserted on every run.
EXPECT_ROWS = {
    "China":          {("A", ""): 2121, ("B", ""): 77},
    "European Union": {("", "I"): 2121, ("", "II"): 45},
    "Japan":          {("", ""): 2121},
    "South Korea":    {("", ""): 2121},
    "Switzerland":    {("", "I"): 2121, ("", "II"): 134},
    "Taiwan":         {("A", "I"): 2121, ("A", "II"): 118},
    "Bangladesh":     {("A", "I"): 2121, ("A", "II"): 87},
    "Cambodia":       {("A", "I"): 2121, ("A", "II"): 157},
    "Indonesia":      {("", "I"): 2121, ("", "II"): 148},
    "Malaysia":       {("", "I"): 2121, ("", "II"): 104},
    "Thailand":       {("", ""): 2121},
    "India":          {("A", ""): 2121},
    "Singapore":      {("", ""): 2121},
    "Vietnam":        {("", ""): 2121},
}

# 8-digit subheadings, and 10-digit statistical lines printed as 0712.90.8550
CODE = re.compile(r"^\d{4}\.\d{2}\.\d{2}(\.?\d{2})?$")
FLAGS = {"": "", "pharma": "pharma", "aircraft": "aircraft", "ex": "ex"}


def _norm(s):
    """Collapse whitespace and straighten quotes and dashes."""
    s = " ".join((s or "").split())
    return (s.replace("’", "'").replace("‘", "'")
             .replace("“", '"').replace("”", '"')
             .replace("–", "-").replace("—", "-"))


def read_notice(pdf_path):
    """Return (prose, annex rows) for one notice.

    The prose is the body text before the annex with footnotes (set in a
    smaller font) and page numbers removed, so a sentence that runs across a
    page break reads continuously. Annex rows come from the three-column tables
    (HTSUS, Description, Scope Limitations); a row with no code continues the
    description of the row above."""
    prose, rows = [], []
    annex, in_annex = "", False
    with pdfplumber.open(pdf_path) as pdf:
        for page_no, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            m = re.search(r"^\s*ANNEX( [A-Z])?\s*$", text, flags=re.M)
            if m:
                in_annex, annex = True, (m.group(1) or "").strip()
            tables = page.extract_tables()
            if not in_annex and tables and any(
                    CODE.match((r[0] or "").strip()) for t in tables for r in t):
                in_annex = True          # an annex that starts without a heading
            if not in_annex:
                body = page.filter(lambda o: o.get("object_type") != "char"
                                   or o.get("size", 12) >= 11.5)
                lines = [l for l in (body.extract_text() or "").splitlines()
                         if not re.fullmatch(r"\s*\d{1,3}\s*", l)]
                prose.append("\n".join(lines))
                continue
            part = ""
            for table in tables:
                for r in table:
                    c0 = (r[0] or "").strip()
                    if c0.startswith("Goods of"):
                        pm = re.search(r"Part (I{1,3})\b", _norm(c0))
                        part = pm.group(1) if pm else ""
                        continue
                    if c0 == "HTSUS":
                        continue
                    desc = _norm(r[1]) if len(r) > 1 else ""
                    flag = _norm(r[2]).lower() if len(r) > 2 else ""
                    if not c0:                       # continuation of the row above
                        if rows and desc:
                            rows[-1]["description"] += " " + desc
                        if rows and flag and not rows[-1]["scope_limitation"]:
                            rows[-1]["scope_limitation"] = FLAGS[flag]
                        continue
                    if not CODE.match(c0):
                        raise ValueError(f"{pdf_path.name} p{page_no}: unexpected cell {c0!r}")
                    if flag not in FLAGS:
                        raise ValueError(f"{pdf_path.name} p{page_no}: unknown scope {flag!r}")
                    rows.append({"annex": annex, "part": part, "htsus": c0,
                                 "digits": c0.replace(".", ""), "description": desc,
                                 "scope_limitation": FLAGS[flag], "source_page": page_no})
    return _norm(" ".join(prose)), rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--srcdir", default=str(TL / "sources"), help="folder holding the notice PDFs")
    ap.add_argument("--prefix", default="301-secp-proposed-", help="PDF file-name prefix")
    ap.add_argument("--outdir", default=str(TL), help="folder for the two CSVs")
    ap.add_argument("--suffix", default="", help="appended to the output file names, e.g. -FINAL")
    args = ap.parse_args()
    src, out = Path(args.srcdir), Path(args.outdir)

    econ_rows, annex_rows, problems = [], [], []
    for e in ECONOMIES:
        pdf_path = src / f"{args.prefix}{e['stem']}.pdf"
        prose, rows = read_notice(pdf_path)

        # the proposed-action section: every rate is pinned to its sentence
        i = prose.find("Pursuant to Sections 301(b) and (c), the Trade Representative proposes")
        j = prose.find("Request for Public Comments", i)
        assert 0 <= i < j, f"{e['economy']}: proposed-action section not found"
        section = prose[i:j]
        for ph in e["phrases"]:
            assert _norm(ph) in section, f"{e['economy']}: phrase not found: {ph!r}"
        has_232 = S232_PHRASE in section
        exempt_232 = e.get("exempt_232", True)
        assert has_232 == exempt_232, f"{e['economy']}: Section 232 exemption text = {has_232}"
        if not exempt_232:
            assert "232" not in prose, f"{e['economy']}: unexpected mention of Section 232"
        for ph in DATE_PHRASES:
            assert ph in prose, f"{e['economy']}: date not found: {ph}"
        dk = re.search(r"Docket Nos?\. (USTR-\d{4}-\d{4}), (USTR-\d{4}-\d{4})", prose)
        assert dk, f"{e['economy']}: docket numbers not found"

        # the annex
        df = pd.DataFrame(rows)
        got = {k: len(g) for k, g in df.groupby(["annex", "part"])}
        if got != EXPECT_ROWS[e["economy"]]:
            problems.append(f"{e['economy']}: annex rows {got}, expected {EXPECT_ROWS[e['economy']]}")
        dup = df[df.duplicated(["annex", "part", "digits"], keep=False)]
        assert dup.empty, f"{e['economy']}: duplicate codes {sorted(set(dup.htsus))}"
        assert df.digits.str.len().isin([8, 10]).all()
        df.insert(0, "cty_code", e["cty_code"])
        df.insert(0, "economy", e["economy"])
        annex_rows.append(df)

        econ_rows.append({
            "economy": e["economy"], "cty_code": e["cty_code"],
            "proposed_rate_pct": e["proposed"],
            "agreement_rate_pct": e["agreement"],
            "alternative_rate_pct": e["alternative"],
            "net_of_mfn": e["net_mfn"],
            "alternative_net_of_mfn": e["alt_net_mfn"],
            "annex_a_rate_pct": e.get("annex_a_rate"),
            "alternative_ignores_annexes": e.get("alternative_ignores_annexes", False),
            "exempt_232": exempt_232,
            "effective_date": "",          # none proposed; the engine holds a placeholder
            "end_date": "",
            "adjustment_terminates": e.get("adjustment_terminates", ""),
            "comment_docket": dk.group(2), "hearing_docket": dk.group(1),
            "basis": e["basis"], "source": pdf_path.name,
        })
        parts = ", ".join(f"{('Annex ' + a + ' ') if a else ''}{('Part ' + p) if p else ''}".strip()
                          + f" {n}" for (a, p), n in got.items())
        print(f"  {e['economy']:15s} {len(df):5d} annex rows  ({parts.strip()})")

    assert not problems, "annex row counts changed:\n  " + "\n  ".join(problems)
    econ = pd.DataFrame(econ_rows)
    for c in ("proposed_rate_pct", "agreement_rate_pct", "alternative_rate_pct", "annex_a_rate_pct"):
        econ[c] = econ[c].astype("Float64")
    annex = pd.concat(annex_rows, ignore_index=True)
    econ_out = out / f"301-secp-economies{args.suffix}.csv"
    annex_out = out / f"301-secp-annex{args.suffix}.csv"
    econ.to_csv(econ_out, index=False, encoding="utf-8")
    annex.to_csv(annex_out, index=False, encoding="utf-8")
    print(f"{econ_out.name}: {len(econ)} economies")
    print(f"{annex_out.name}: {len(annex)} rows, {annex.digits.nunique()} distinct codes; "
          f"scope flags {annex.scope_limitation.replace('', 'none').value_counts().to_dict()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
