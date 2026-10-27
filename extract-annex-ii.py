"""
Extract the IEEPA product-exemption lists read by make-tariff-by-country-by-time.ipynb.

1. EO 14257 Annex II (Apr 2, 2025) -> tariff-lists/annex-II-exemptions.csv
   Products exempt from the reciprocal tariff. The annex note says coverage is
   "all products that are classified in the 8-digit subheadings" listed, so the
   list is kept at HS8 and matched on HS8.

2. EO 14361 Annex II (Nov 20, 2025) -> tariff-lists/brazil-ag-exemptions-nov13.csv
   Agricultural goods taken out of the Brazil 40% duty (EO 14323) from Nov 13,
   2025: 238 subheadings added to U.S. note 2(x)(iii)(a) ("listed") plus the 11
   articles of new subdivision (x)(iii)(b) ("described"). The described
   articles are ex-outs (some for religious purposes only); the engine applies
   them flat by HS8, the standing convention for conditional exemptions.

pypdf scrambles the layout of the Annex II PDF, so both are read with pdfplumber.

Usage:
    python extract-annex-ii.py
"""
import re
import pandas as pd
import pdfplumber

ANNEX_II_PDF = "data/Annex-II.pdf"
ANNEX_II_OUT = "tariff-lists/annex-II-exemptions.csv"
ANNEX_II_LEGACY = "tariff-lists/annex-II-exemptions-legacy.csv"
BRAZIL_PDF = "tariff-lists/brazil-EO14361-annexes.pdf"
BRAZIL_OUT = "tariff-lists/brazil-ag-exemptions-nov13.csv"


def pdf_text(path):
    with pdfplumber.open(path) as pdf:
        return "\n".join(p.extract_text() or "" for p in pdf.pages)


def annex_ii():
    text = pdf_text(ANNEX_II_PDF)
    if "8-digit subheadings" not in text.replace("\n", " "):
        raise SystemExit("Annex II coverage note not found")

    # Each row starts with the bare 8-digit subheading.
    codes = re.findall(r"(?m)^(\d{8})\b", text)
    if len(codes) != len(set(codes)) or len(codes) != 1039:
        raise SystemExit(f"expected 1,039 unique subheadings, got {len(codes)}")

    # The pre-Oct 2026 list held 720 of these, padded to 10 digits.
    legacy = pd.read_csv(ANNEX_II_LEGACY, dtype={"HTSUS": str})["HTSUS"]
    missing = set(legacy.str[:8]) - set(codes)
    if missing:
        raise SystemExit(f"legacy codes not in Annex II: {sorted(missing)}")

    pd.DataFrame({"HTSUS": codes}).to_csv(ANNEX_II_OUT, index=False)
    print(f"{ANNEX_II_OUT}: {len(codes)} HS8 subheadings")


def brazil_ag():
    text = pdf_text(BRAZIL_PDF)
    listed_block = (text.split("the following provisions of the HTSUS in numerical order:")[1]
                        .split("ii. by inserting")[0])
    described_block = text.split("new subdivision (x)(iii)(b)")[1]

    listed = re.findall(r"\b(\d{4})\.(\d{2})\.(\d{2})\b", listed_block)
    described = re.findall(r"subheading\s+(\d{4})\.(\d{2})\.(\d{2})", described_block)
    if len(listed) != 238 or len(described) != 11:
        raise SystemExit(f"expected 238 listed + 11 described, got {len(listed)} + {len(described)}")

    rows = ([("".join(c), "listed") for c in listed]
            + [("".join(c), "described") for c in described])
    out = pd.DataFrame(rows, columns=["HTSUS", "category"])
    if out["HTSUS"].duplicated().any():
        raise SystemExit("duplicate subheadings in the Brazil list")

    out.to_csv(BRAZIL_OUT, index=False)
    print(f"{BRAZIL_OUT}: {len(listed)} listed + {len(described)} described")


if __name__ == "__main__":
    annex_ii()
    brazil_ag()
