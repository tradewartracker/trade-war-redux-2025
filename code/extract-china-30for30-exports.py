# -*- coding: utf-8 -*-
"""Extract CHINA's import list of the U.S.-China Board of Trade "30-for-30"
framework (White House release, Sep 27, 2026) — the U.S. EXPORT side — into a
CSV in tariff-lists/. Companion to extract-china-30for30.py (the U.S. import
list).

Source: tariff-lists/sources/Usexports-China-Import-List.pdf ("中国进口产品清单", 38 pages)
— 1,619 tariff lines of China's 2026 Import and Export Tariff (中华人民共和国
进出口税则 2026), 8 digits, with China's simplified commodity names (Chinese
only). The footnote says the names are for reference and the scope of each line
is the tariff schedule's own. Valued by the two governments at roughly $30B of
calendar-2024 trade, "comparably" to the 77-code U.S. list. This is an
ANNOUNCED list, not an enacted tariff action: no rate, date or instrument.

The HS6 problem: China's 8-digit lines and U.S. Schedule B (10 digits) agree
only on their first six digits, so US export data can be matched at HS6 only.
The CSV therefore carries `hs6` and a `match` column scored from the list's own
structure (China's full 2026 schedule is not loaded here):
  whole    — the line is xxxxxx00, i.e. the whole HS6 subheading;
  residual — China splits the HS6 and the list includes its residual "other"
             line (suffix 90/99), so coverage is read as the whole subheading
             but is not verified against the schedule;
  partial  — only some named splits are listed: US exports of the HS6 are an
             upper bound on the covered trade.

Output: tariff-lists/china-30for30-china-import-list.csv
  no, tariff_line (8-digit China 2026 schedule), hs6, match, description_zh,
  source_page.

Usage: python code/extract-china-30for30-exports.py
"""
import sys
from pathlib import Path
import pandas as pd
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]   # the repository root
TL = ROOT / "tariff-lists"
PDF = TL / "sources" / "Usexports-China-Import-List.pdf"
OUT = TL / "china-30for30-china-import-list.csv"

EXPECT_N = 1619
EXPECT_HS6 = 1061


def extract_raw():
    rows = []
    with pdfplumber.open(PDF) as pdf:
        for page_no, page in enumerate(pdf.pages, 1):
            for table in page.extract_tables():
                for r in table:
                    if not r or not r[0] or not r[0].strip().isdigit():
                        continue                     # header row / footnote
                    rows.append({
                        "no": int(r[0]),
                        "tariff_line": r[1].strip(),
                        "description_zh": " ".join((r[2] or "").split()),
                        "source_page": page_no,
                    })
    return pd.DataFrame(rows)


def score_match(df):
    """whole / residual / partial per HS6, from the listed suffixes alone."""
    out = {}
    for hs6, sub in df.groupby("hs6"):
        suf = set(sub["tariff_line"].str[6:])
        if "00" in suf:
            out[hs6] = "whole"
        elif suf & {"90", "99"}:
            out[hs6] = "residual"
        else:
            out[hs6] = "partial"
    return df["hs6"].map(out)


def main():
    raw = extract_raw()
    assert len(raw) == EXPECT_N, f"expected {EXPECT_N} rows, got {len(raw)}"
    assert raw.no.tolist() == list(range(1, EXPECT_N + 1)), "row numbers not 1..N in order"
    assert raw.tariff_line.str.len().eq(8).all() and raw.tariff_line.str.isdigit().all()
    assert raw.tariff_line.is_unique, "duplicate tariff lines"
    assert raw.tariff_line.is_monotonic_increasing, "list not in code order"
    raw["hs6"] = raw.tariff_line.str[:6]
    assert raw.hs6.nunique() == EXPECT_HS6, f"expected {EXPECT_HS6} HS6, got {raw.hs6.nunique()}"
    raw["match"] = score_match(raw)
    raw = raw[["no", "tariff_line", "hs6", "match", "description_zh", "source_page"]]
    raw.to_csv(OUT, index=False, encoding="utf-8")
    by6 = raw.drop_duplicates("hs6")["match"].value_counts()
    print(f"{OUT.relative_to(ROOT)}: {len(raw)} tariff lines, {raw.hs6.nunique()} HS6, "
          f"{raw.tariff_line.str[:2].nunique()} chapters")
    print("  HS6 match: " + ", ".join(f"{k} {v}" for k, v in by6.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
