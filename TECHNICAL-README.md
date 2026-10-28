# Technical Documentation

How to run, check and extend the tariff model. For what the numbers mean, see the
[README](README.md) and [METHODOLOGY.md](METHODOLOGY.md). Every change is logged in
[CHANGELOG.md](CHANGELOG.md).

## Requirements

Python 3 with pandas, numpy, pyarrow, matplotlib and bokeh. The extraction scripts also
use pdfplumber and pypdf. Import data is cached in [data](data) as parquet, so the
notebooks run offline; downloading it again needs a Census API key.

## Repository layout

- The root holds the documentation and the two published data files.
- [code](code): the two build notebooks, the notebooks that build model inputs, and the
  extraction and validation scripts.
  - [code/analysis](code/analysis): notebooks that each examine one action.
- [tariff-lists](tariff-lists): the code lists the engine reads.
  - [tariff-lists/sources](tariff-lists/sources): the legal texts (PDF) the lists are
    extracted from.
- [data](data): the cached Census import files, the country lists and the long-run tariff
  history.
- [figures](figures): figures written by the notebooks, including the README chart.
- [docs](docs): website chart pages written by the plot notebook.
- [archive](archive): notebooks and data no longer in the workflow, kept for reference.
  Archived notebooks are not maintained and their paths no longer resolve.

**Paths are relative to the repository root.** Each notebook in `code/` starts with a cell
that moves to the root when the notebook is opened from its own folder. Each script finds
the root from its own location. Both therefore run from any directory. A new notebook
should start with the same cell.

**Three locations are fixed by outside users:**
- The two CSVs stay at the root. The tracker's ETL reads them by absolute path, and
  outside users link to them.
- The code lists stay directly in `tariff-lists/`. The trade-miner repository reads them
  by absolute path (`C:\github\trade-war-redux-2025\tariff-lists`).
- `docs/` is served by GitHub Pages, so its file names are public URLs.

## Updating the tracker

Run these in order after any change to a tariff action or list:

1. [code/make-tariff-by-country-by-time.ipynb](code/make-tariff-by-country-by-time.ipynb)
   builds the country-by-date panel and writes [country-by-time.csv](country-by-time.csv)
   and [daily-tariff-latest-data.csv](daily-tariff-latest-data.csv).
2. [code/plot-tariff-by-country-by-time.ipynb](code/plot-tariff-by-country-by-time.ipynb)
   reads those files and writes:
   - the website charts in [docs](docs);
   - the README chart, [figures/tariff-fig.png](figures/tariff-fig.png) (also saved as
     `figures/tariff-fig.pdf`).

   It also uses [data/federal-tax-duty.csv](data/federal-tax-duty.csv) and
   [data/NIPA-imports.csv](data/NIPA-imports.csv) for the long-run tariff history. The
   README chart's event labels are the `EVENTS` list in its "README header figure" cell.
   Each label reads its rate from the data, so only a new action needs a new entry.
3. Refresh the tracker app. Its ETL, `TRI-tracker-update.ipynb` in the
   `how-restrictive-us-trade` repository, reads the two CSVs from step 1 from local disk.
   Re-run it, then redeploy the app.

**The CSV columns are a contract with the app.** It reads `country-by-time.csv` columns
`date` (`%Y-%m-%d`), `country_name`, `effective tariff` and `2024 tariff`, and
`daily-tariff-latest-data.csv` columns `date` and `import_weighted_avg_tariff`, all in
percent. Renaming any of them breaks the app. The row `EUROPEAN UNION` must exist: the
app gives any country missing from the file the EU's rate.

**Running notebooks headless.** On Windows, `jupyter nbconvert --execute` is unreliable
here. Use nbclient with the selector event loop:

```python
import asyncio; asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import nbformat
from nbclient import NotebookClient
nb = nbformat.read(path, as_version=4)
NotebookClient(nb, timeout=3600, kernel_name="python3",
               resources={"metadata": {"path": repo_dir}}).execute()
nbformat.write(nb, path)
```

## Adding or changing a tariff action

Every action is an entry in the `TARIFF_ACTIONS` registry of the main notebook: an
effective date, legal authority, reference, description and an apply function. The engine
applies them in three phases, described in
[METHODOLOGY.md](METHODOLOGY.md#2-tariff-actions-and-how-they-stack).

**A stacked country action (Section 301 or 338)** needs no new logic:

1. Put the legal text in [tariff-lists/sources](tariff-lists/sources) and extract its code
   list into [tariff-lists](tariff-lists): `code/extract-301-exemptions.py` for a 301
   notice, `code/extract-338-annex.py` for a 338 proclamation.
2. Load the list in the Section 2 cell of the main notebook (the product lists) and
   register it in `STACKED_EXEMPT_LISTS` or `STACKED_INCLUDE_LISTS`. Lists are keyed by
   list name, not by action, so several actions can share one.
3. Append one entry to `STACKED_REGIMES`, in the Section 3 cell that starts with the
   Phase 1 rate functions. `scope="all"` covers every good of the country except the
   exemption list (Section 301); `scope="listed"` covers only the listed codes
   (Section 338).
4. Add the effective date to `date_strings` in Section 6. The panel has rows only on
   listed dates.

If the action uses a new legal authority, also add its phrase to `AUTHORITY_PHRASES` in
the plot notebook, which builds chart captions from the registry.

**An amended action** is split into dated versions rather than edited in place. Give the
existing entry an `end_date` (the last day it applies) and start a new entry the next day
with its own lists. Editing in place would rewrite every earlier date in the panel.

**An announced or proposed action** is built and validated but switched off behind a
flag, so going live is a flag flip. `LABOR_301_LIVE` (now `True`) and
`CHINA_30FOR30_LIVE` (now `False`) follow this pattern. The 30-for-30 go-live checklist is
in [METHODOLOGY.md](METHODOLOGY.md#announced-not-enacted--us-china-30-for-30-list-staged-off).

Each new list should get a `validate-*.py` guardrail that pins its code counts and
quoted magnitudes, so a silent change cannot move the published numbers unnoticed.

## Analysis notebooks

Each answers one question about one action. Five of them load the engine by executing the
code cells of the main notebook up to `tariff_imports`, so they must be run after it.
`section-122-analysis` and `metals-restructuring-analysis` carry their own partial copies
of the engine, and `annex-ii-revision` compares the published CSVs with an earlier
commit. Figures go to [figures](figures).

| Notebook | Question |
|---|---|
| [brazil-301-analysis.ipynb](code/analysis/brazil-301-analysis.ipynb) | Coverage, exemptions and rate impact of the Jul 22, 2026 Brazil Section 301 action |
| [canada-338-analysis.ipynb](code/analysis/canada-338-analysis.ipynb) | What the Section 338 Canada baskets hit and miss, the rate step, and the Sep 15 and Oct 30 amendments |
| [section301-labor-overview.ipynb](code/analysis/section301-labor-overview.ipynb) | The final forced-labor action: the Section 122 → labor transition, and the proposal → final change split into rate, net-of-MFN cap and exemption effects |
| [section122-to-301labor-transition.ipynb](code/analysis/section122-to-301labor-transition.ipynb) | The same transition under the June 5 **proposal**; kept as a record, superseded by the overview |
| [china-30for30-analysis.ipynb](code/analysis/china-30for30-analysis.ipynb) | China's rate if the 30-for-30 list were excluded from the labor duty (staged off) |
| [section-122-analysis.ipynb](code/analysis/section-122-analysis.ipynb) | Section 122 surcharge exemption coverage and the shift at the Supreme Court ruling |
| [metals-restructuring-analysis.ipynb](code/analysis/metals-restructuring-analysis.ipynb) | Coverage and impact of the Apr 6, 2026 Section 232 metals tiers |
| [annex-ii-revision.ipynb](code/analysis/annex-ii-revision.ipynb) | Old vs. corrected series for the Oct 27, 2026 reciprocal-tariff Annex II fix; a record, compares against commit `aa4e228`. Do not re-run |

The 2025 tariff revenue estimate, `revenue-analysis.ipynb`, is in [archive](archive). It
carried its own older copy of the engine, which later fixes (including the Oct 27, 2026
Annex II correction) never reached.

## Scripts and input builders

Extraction scripts turn the legal texts in [tariff-lists/sources](tariff-lists/sources)
into the code lists in [tariff-lists](tariff-lists). Validation scripts are independent
checks; each exits non-zero on failure.

- [extract-301-exemptions.py](code/extract-301-exemptions.py): the exemption subdivisions
  of a USTR Section 301 Notice of Action PDF, as one CSV with a `category` column. Asserts
  the expected per-category counts in `SUBDIVISIONS`, which must be updated for each
  notice. Usage: `python code/extract-301-exemptions.py <notice.pdf> <out.csv>`
- [extract-annex-ii.py](code/extract-annex-ii.py): the IEEPA product exemptions. EO 14257
  Annex II ([Annex-II.pdf](tariff-lists/sources/Annex-II.pdf)) becomes
  [annex-II-exemptions.csv](tariff-lists/annex-II-exemptions.csv), 1,039 HS8 subheadings
  matched on HS8. EO 14361 Annex II becomes
  [brazil-ag-exemptions-nov13.csv](tariff-lists/brazil-ag-exemptions-nov13.csv), the 238
  subheadings and 11 described articles taken out of Brazil's 40% from Nov 13, 2025.
  Asserts the counts, and that every code in the pre-correction list
  ([annex-II-exemptions-legacy.csv](tariff-lists/annex-II-exemptions-legacy.csv)) is in
  Annex II. Reads with pdfplumber; pypdf scrambles the Annex II layout.
  Usage: `python code/extract-annex-ii.py`
- [extract-338-annex.py](code/extract-338-annex.py): the basket of each Section 338
  proclamation and the shared civil-aircraft carve-out, with `HTSUS` and `description`
  columns. Cross-checks Annex I (descriptive) against Annex II (legal text), which restate
  the same codes. New actions go in the `ACTIONS` table. Amending proclamations go in
  `AMENDMENTS`: their Annex II deletions and insertions are applied to the basket in force
  the day before and written as a dated version (e.g. `canada-338-autos-2026-10-30.csv`).
  Reads the PDFs from `--srcdir` (default `tariff-lists/sources`) and writes to `--outdir`
  (default `tariff-lists`). Usage: `python code/extract-338-annex.py`
- [validate-338.py](code/validate-338.py): re-parses the 338 annexes by a different
  method, checks the lists against trade data, and pins the magnitudes quoted downstream.
  For the dated versions it checks that narrowings are complete, that the note 51(c)
  wording matches each version's Section 232 setting, that the baskets in force on each
  date are disjoint, and that every banned code is already in a basket.
  Usage: `python code/validate-338.py`
- [validate-301-labor.py](code/validate-301-labor.py): guardrail for the forced-labor
  lists. Baseline mode checks the provisional economy tiers and exemption list; diff mode
  (`--diff-economies … --diff-exemptions …`) reports what a new notice changed against
  them. Usage: `python code/validate-301-labor.py`
- [validate-timber.py](code/validate-timber.py): guardrail for the Section 232 timber list
  ([timber-232.csv](tariff-lists/timber-232.csv)) and its Canada impact.
  Usage: `python code/validate-timber.py`
- [extract-china-30for30.py](code/extract-china-30for30.py): the U.S. import list of the
  Sep 27, 2026 U.S.-China framework, as printed
  ([china-30for30-us-import-list.csv](tariff-lists/china-30for30-us-import-list.csv), 77
  HTS8 codes) and in engine form
  ([china-30for30-model-list.csv](tariff-lists/china-30for30-model-list.csv), with the
  seven juvenile-furniture ex-outs resolved to 13 HTS10 lines).
  Usage: `python code/extract-china-30for30.py`
- [validate-china-30for30.py](code/validate-china-30for30.py): pins the 30-for-30 list to
  the PDF, its $29.6B of 2024 China imports, its disjointness from the Section 232 and
  labor Part A lists, and the −0.86 pp China step.
  Usage: `python code/validate-china-30for30.py`
- [extract-china-30for30-exports.py](code/extract-china-30for30-exports.py): the other
  half of the framework, China's list of U.S. goods
  ([china-30for30-china-import-list.csv](tariff-lists/china-30for30-china-import-list.csv),
  1,619 Chinese 8-digit lines). Chinese and U.S. codes agree only at HS6, so each HS6
  carries a `match` score (`whole`, `residual` or `partial`). Not used by the engine,
  since it is a Chinese tariff; consumed by the trade-miner's `miner/china_30for30.py`.
  Usage: `python code/extract-china-30for30-exports.py`

Two notebooks build model inputs rather than answer a question:

- [mfn-per-code-comparison.ipynb](code/mfn-per-code-comparison.ipynb) builds the per-code
  MFN rates ([mfn-per-code.csv](tariff-lists/mfn-per-code.csv)) used by the net-of-MFN
  cap, and compares them with the pooled alternative.
- [make-country-list.ipynb](code/make-country-list.ipynb) built the trading-partner list;
  see below before re-running it.

## Trading partners

The panel is the list in [top_50_non_eu.csv](data/top_50_non_eu.csv) plus the EU bloc,
which the main notebook adds as Census code 0003. `make-country-list.ipynb` built that
list by ranking non-EU countries on cumulative imports since 2013, excluding the members
in [eu-list.csv](data/eu-list.csv). Re-running it re-ranks the whole list against current
Census data and can change which countries are in the panel, so edit the CSV directly for
a targeted change. A new partner also needs its import data downloaded to `data/` and a
rate in every country-specific action.
