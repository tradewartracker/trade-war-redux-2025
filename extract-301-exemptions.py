"""
Extract Section 301 country-action exemption lists from a USTR Notice of Action PDF.

Parses the U.S. note subdivisions in Annex I into a single CSV with a `category`
column, one file per 301 country regime.

Usage:
    python extract_301.py <pdf> <out.csv>
"""
import re
import sys
import pandas as pd
import pypdf

# Subdivision boundaries, keyed by the ch.99 heading each one is "provided in".
# (start_marker_regex, category, expected_count)
SUBDIVISIONS = [
    (r"\(ii\)\s+As provided in heading 9903\.05\.03",  "flat",     864),
    (r"\(iii\)\s+As provided in heading 9903\.05\.04", "named",     11),
    (r"\(iv\)\s+As provided in heading 9903\.05\.05",  "aircraft", 546),
    (r"\(v\)\s+As provided in heading 9903\.05\.06",   "pharma",   705),
    (r"\(vi\)\s+As provided in heading 9903\.05\.07",  None,      None),  # terminator
]

HTS_RE = re.compile(r"\b(\d{4})\.(\d{2})\.(\d{2})(\d{2})?\b")


def pdf_text(path):
    reader = pypdf.PdfReader(path)
    return "\n".join(p.extract_text() or "" for p in reader.pages)


def extract(path):
    text = pdf_text(path)

    # Locate each subdivision's start offset.
    bounds = []
    for pattern, category, expected in SUBDIVISIONS:
        m = re.search(pattern, text)
        if not m:
            raise SystemExit(f"could not locate subdivision marker: {pattern}")
        bounds.append((m.start(), category, expected))

    rows = []
    for i, (start, category, expected) in enumerate(bounds[:-1]):
        end = bounds[i + 1][0]
        chunk = text[start:end]

        codes = []
        for m in HTS_RE.finditer(chunk):
            code = "".join(g for g in m.groups() if g)
            if code.startswith("9903"):
                continue  # ch.99 cross-references, not product codes
            codes.append(code)

        # Order-preserving dedupe; the source lists should already be unique.
        seen, unique = set(), []
        for c in codes:
            if c not in seen:
                seen.add(c)
                unique.append(c)

        if len(unique) != expected:
            raise SystemExit(
                f"{category}: extracted {len(unique)} codes, expected {expected}"
            )
        if len(codes) != len(unique):
            print(f"  warning: {category} had {len(codes) - len(unique)} duplicates")

        rows.extend({"HTSUS": c, "category": category} for c in unique)
        print(f"  {category:9s} {len(unique):4d} codes")

    return pd.DataFrame(rows)


if __name__ == "__main__":
    pdf_path, out_path = sys.argv[1], sys.argv[2]
    df = extract(pdf_path)

    # Sanity checks before writing.
    assert df["HTSUS"].str.len().isin([8, 10]).all(), "unexpected code length"
    dupes = df[df.duplicated("HTSUS", keep=False)]
    if len(dupes):
        print(f"\nnote: {dupes['HTSUS'].nunique()} codes appear in >1 category:")
        print(dupes.sort_values("HTSUS").to_string(index=False))

    ch98 = df[df["HTSUS"].str[:2] == "98"]
    if len(ch98):
        print(f"\nnote: {len(ch98)} chapter-98 codes (never match Census HS10 data): "
              f"{', '.join(ch98['HTSUS'])}")

    df.to_csv(out_path, index=False)
    print(f"\nwrote {len(df)} rows -> {out_path}")
