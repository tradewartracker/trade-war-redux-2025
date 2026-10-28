# -*- coding: utf-8 -*-
"""Extract the U.S. import list of the U.S.-China Board of Trade "30-for-30"
framework (White House release, Sep 27, 2026) into two CSVs in tariff-lists/.

Source: tariff-lists/sources/china-USimports-Public-List.pdf — 77 HTSUS 8-digit codes of
Chinese goods approved "with a view toward providing reduced tariff treatment",
valued at roughly $30B of calendar-2024 bilateral trade (Terms of Reference).
This is an ANNOUNCED list, not an enacted tariff action: no rate, effective
date, legal authority or chapter 99 heading exists yet.

Outputs
  china-30for30-us-import-list.csv  — the list exactly as printed (provenance):
      no, HTSUS (8-digit), ex_out ('X' where the PDF limits the line to its
      product description), description, source_page.
  china-30for30-model-list.csv      — the engine form used by
      make-tariff-by-country-by-time.ipynb: the plain HS8 codes plus, for the
      seven juvenile-furniture "Ex-Out" rows, the HTS10 statistical lines that
      carry exactly the described products (the HTS added those suffixes in
      2022 for CPSC purposes, so the ex-outs ARE resolvable at HS10). The one
      ex-out that is not resolvable — 9503.00.00 toys, which excludes items
      "enabled with radio frequency, Wi-Fi, Ethernet, or Bluetooth" — is kept
      flat at HS8 and flagged resolution='flat'.

Usage: python extract-china-30for30.py
"""
import sys
from pathlib import Path
import pandas as pd
import pdfplumber

TL = Path("tariff-lists")
PDF = TL / "sources" / "china-USimports-Public-List.pdf"
RAW_OUT = TL / "china-30for30-us-import-list.csv"
MODEL_OUT = TL / "china-30for30-model-list.csv"
PARQUET = Path("data") / "2024-hs10-imports5700.parquet"   # for HS10 descriptions

# HS10 resolution of the juvenile-furniture ex-outs, read literally from each
# row's product description in the PDF. Only the products NAMED in the text are
# included: e.g. 9401.71.00 names highchairs/boosters, infant walkers and
# bouncers, but not swings (9401.71.0007) or activity centers (9401.71.0008),
# whereas 9401.79.00 does name swings. Descriptions are checked against the
# Census HS10 labels by validate-china-30for30.py.
JUVENILE_HS10 = {
    "94017100": ["9401710001", "9401710005", "9401710006"],
    "94017900": ["9401790001", "9401790002", "9401790003", "9401790004"],
    "94018020": ["9401802001"],
    "94018040": ["9401804001"],
    "94018060": ["9401806021", "9401806023"],
    "94037040": ["9403704003"],
    "94037080": ["9403708003"],
}
FLAT_EX_OUT = {"95030000"}   # connectivity ex-out, not resolvable at HS10


def extract_raw():
    rows = []
    with pdfplumber.open(PDF) as pdf:
        for page_no, page in enumerate(pdf.pages, 1):
            for table in page.extract_tables():
                for r in table:
                    if r[0] == "No.":
                        continue
                    rows.append({
                        "no": int(r[0]),
                        "HTSUS": r[1].strip(),
                        "ex_out": (r[2] or "").strip(),
                        "description": " ".join(r[3].split()),
                        "source_page": page_no,
                    })
    return pd.DataFrame(rows)


def build_model(raw):
    desc10 = {}
    if PARQUET.exists():
        d = pd.read_parquet(PARQUET, columns=["HS10", "I_COMMODITY_SDESC"])
        desc10 = dict(zip(d.HS10, d.I_COMMODITY_SDESC))
    out = []
    for r in raw.itertuples():
        if r.HTSUS in JUVENILE_HS10:
            for c in JUVENILE_HS10[r.HTSUS]:
                out.append({"HTSUS": c, "list_hts8": r.HTSUS, "no": r.no,
                            "ex_out": "X", "resolution": "hs10",
                            "description": desc10.get(c, r.description)})
        else:
            out.append({"HTSUS": r.HTSUS, "list_hts8": r.HTSUS, "no": r.no,
                        "ex_out": r.ex_out,
                        "resolution": "flat" if r.HTSUS in FLAT_EX_OUT else "hs8",
                        "description": r.description})
    return pd.DataFrame(out)


def main():
    raw = extract_raw()
    assert len(raw) == 77, f"expected 77 rows, got {len(raw)}"
    assert raw.HTSUS.is_unique and raw.HTSUS.str.len().eq(8).all()
    assert set(raw.loc[raw.ex_out == "X", "HTSUS"]) == set(JUVENILE_HS10) | FLAT_EX_OUT
    raw.to_csv(RAW_OUT, index=False, encoding="utf-8")
    model = build_model(raw)
    model.to_csv(MODEL_OUT, index=False, encoding="utf-8")
    n8 = (model.HTSUS.str.len() == 8).sum()
    n10 = (model.HTSUS.str.len() == 10).sum()
    print(f"{RAW_OUT}: {len(raw)} rows ({(raw.ex_out == 'X').sum()} ex-outs)")
    print(f"{MODEL_OUT}: {len(model)} rows ({n8} HS8 + {n10} HS10)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
