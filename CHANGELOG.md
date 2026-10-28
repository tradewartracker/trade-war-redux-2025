# Changelog

Dated notes on every change to the model and its data, newest first. Each entry is a
snapshot: its figures are the ones published that day and are not revised later, so an
older entry can quote a number that a later correction changed.

## Revisions to published history

Most entries add new actions, which leave earlier dates untouched. These changed rates
that had already been published.

| Revised | What changed | Dates affected | Effect on the national average |
|---|---|---|---|
| Oct 28, 2026 | Slovakia, an EU member, was counted a second time as a non-EU partner. Removed. | Feb 4, 2025 onward | −0.04 to +0.01 points. Today 11.50% → 11.46%; Aug 7, 2025 17.07% → 17.05%. |
| Oct 27, 2026 | Product exemptions from the reciprocal tariffs (EO 14257 Annex II) matched on 8-digit codes and completed; April 2025 dates corrected; China at 145% during the pause. | Apr 5, 2025 – Feb 19, 2026 | Apr 5–8, 2025: down 11–17 points. Apr 9 – May 11: up at most 1.2. May 12 – Nov 13: down about 1–2 (Aug 7: 18.9% → 17.1%). Nov 14 – Feb 19, 2026: up 0.07. |
| Jul 23, 2026 | Section 232 timber and lumber tariffs (in force since Oct 14, 2025) added. | Oct 14, 2025 onward | About +0.03 points; Vietnam +0.80, Cambodia +0.59, Canada +0.18. |

## 2026-10-28

- **Slovakia removed as a separate partner.** [eu-list.csv](data/eu-list.csv) gave Slovakia
  the code 4371; its Census code is 4359. So `make-country-list.ipynb` did not recognize it
  as an EU member and it entered [top_50_non_eu.csv](data/top_50_non_eu.csv) as a non-EU
  partner. Its imports were counted twice, once inside the EU bloc and once on their own,
  and the separate copy paid non-EU rates (21.7% on Oct 30, 2026, against the EU's 8.4%).
  - Corrected Slovakia's code in `eu-list.csv`, and Malta's (4600 → 4730; Malta was never
    in the panel). Removed the Slovakia row from `top_50_non_eu.csv` by hand rather than
    re-running `make-country-list.ipynb`, which would re-rank the whole list. The panel is
    now 49 partners plus the EU.
  - Re-ran the main and plot notebooks. `country-by-time.csv` loses its 25 Slovakia rows;
    every other row is unchanged. The national average moves by −0.04 to +0.01 points:
    11.50% → 11.46% today, 17.07% → 17.05% on Aug 7, 2025. Steps between dates are
    unchanged to two decimals, including the +0.33 pp forced-labor step (now
    10.86% → 11.19%).
  - The website headline in the plot notebook averaged the 50 largest of the 51 rows, so
    it left out the smallest partner. With 50 rows it now covers every partner and matches
    the daily series.
  - The tracker app reads countries by name and gives any partner missing from
    `country-by-time.csv` the EU rate, so it needs no change.
  - Re-ran the analysis notebooks that print national figures: `section-122-analysis`,
    `brazil-301-analysis`, `canada-338-analysis`, `section122-to-301labor-transition`,
    `section301-labor-overview` and `china-30for30-analysis`. Not re-run:
    `annex-ii-revision.ipynb`, which compares against the series before Oct 27 and stays a
    record of that revision.
- **`section122-to-301labor-transition.ipynb` repaired.** It assumed the forced-labor action
  was staged off. Since the action went live on Jul 23, re-running it stacked the proposed
  duty on top of the final one. It now removes the live action and rebuilds the June 5
  proposal, as `section301-labor-overview.ipynb` does. National average: 10.85% with the
  surcharge, 7.68% with nothing in its place, 11.72% under the proposal (+0.86 pp).
- **README restructured** for readers outside the project. The methodology moved to
  [METHODOLOGY.md](METHODOLOGY.md), the notebook and script guide to
  [TECHNICAL-README.md](TECHNICAL-README.md), and the dated notes to this file.
- **README chart replaced.** [tariff-fig.png](tariff-fig.png) is now an annotated chart in
  the house figure style, drawn by the "README header figure" cell of
  `plot-tariff-by-country-by-time.ipynb` and also saved as `figures/tariff-fig.pdf`. It replaces the headless-browser snapshot of
  the website chart.

## 2026-10-27

- **Annex II exemptions corrected (EO 14257).** The annex covers every product in a listed
  8-digit subheading. The model padded each code to 10 digits and matched on HS10, so it
  reached only statistical lines ending in 00 and missed most crude-oil and pharmaceutical
  lines. The list also held only 720 of the annex's 1,039 subheadings; 108 of the missing
  ones are chapter 29 chemicals.
  - [annex-II-exemptions.csv](tariff-lists/annex-II-exemptions.csv) is now the full list,
    built by the new [extract-annex-ii.py](extract-annex-ii.py) and matched on HS8.
  - It starts on Apr 5, 2025, when Annex II took effect, instead of Apr 11.
  - The Nov 14 list was already matched on HS8, so the error ran from Apr 11 to Nov 13, 2025.
- **Annex II removes only the reciprocal duty** (EO 14257 s.3(b)), so other IEEPA duties now
  stay on Annex II goods:
  - **China/HK** pay the fentanyl duty: 20%, then 10% from a new Nov 1 action, which also
    covers electronics. The Nov 14 agricultural goods now pay 10% (they were at 0%), and
    Hong Kong electronics now pay the fentanyl duty like China's (they were at 0%).
  - **Brazil's** 40% (EO 14323) applies to Annex II and electronics goods. Brazil's own
    Annex I removes only the 40%, so its listed goods that are not in Annex II, such as civil
    aircraft and orange juice, pay the 10% reciprocal duty.
  - From Nov 14, Brazil's list also includes the 238 subheadings and 11 described articles
    of EO 14361 (Nov 20, retroactive to Nov 13),
    [brazil-ag-exemptions-nov13.csv](tariff-lists/brazil-ag-exemptions-nov13.csv). The
    described articles are ex-outs, some for religious use only, and are applied flat by HS8.
  - **India** is unchanged: heading 9903.01.86 exempts Annex II goods from the Russian-oil 25%.
- **Canada and Mexico are on hold.** They keep the pre-correction list, renamed
  [annex-II-exemptions-legacy.csv](tariff-lists/annex-II-exemptions-legacy.csv), from Apr 11,
  so their rates are unchanged at every date. See [open issues](METHODOLOGY.md#5-open-issues).
- **April 2025 dates corrected.**
  - EO 14257 s.3(a) starts the Annex I country rates on Apr 9, not Apr 5. Apr 5–8 was the 10%
    baseline (China/HK 30% with fentanyl).
  - The Apr 8 step moves to Apr 9: the country rates for one day, with China at 104%.
  - The 90-day pause moves from Apr 9 to Apr 10, the date EO 14266 took effect.
- **China/HK during the pause are at 145%, not 125%:** the 125% reciprocal rate plus the 20%
  fentanyl duty.
- Re-ran the main and plot notebooks.
  - `country-by-time.csv` replaces its 2025-04-08 rows with 2025-04-10 and changes only the
    dates from Apr 5, 2025 to Feb 7, 2026.
  - Nothing from Feb 20, 2026 on moves, and Canada and Mexico are unchanged at every date.
  - The daily series now runs to Dec 26, 2026.

  | Date | National before | National after |
  |---|---|---|
  | Apr 5, 2025 | 25.51 | 14.48 |
  | Apr 8, 2025 | 31.42 | 14.48 |
  | Apr 9, 2025 | 27.10 | 28.27 |
  | Apr 10, 2025 | 27.10 | 27.33 |
  | Apr 11, 2025 | 22.61 | 22.76 |
  | May 12, 2025 | 14.29 | 13.24 |
  | Aug 7, 2025 | 18.89 | 17.07 |
  | Nov 1, 2025 | 17.98 | 15.89 |
  | Nov 14, 2025 | 14.77 | 14.84 |
  | Feb 7, 2026 | 14.24 | 14.31 |

  On Aug 7, 2025 Switzerland goes from 38.6% to 24.3%, India 43.0% → 33.6%, the EU
  15.2% → 11.2%, Singapore 9.5% → 4.8% and Iraq 31.3% → 0.8%. Brazil goes up,
  27.2% → 29.7%.
- `revenue-analysis.ipynb` keeps its own copy of the older engine and was not updated.

## 2026-10-26

- **Section 338 Canada amendments modeled.** See the Phase 3 table and the amendments
  paragraph under it in [METHODOLOGY.md](METHODOLOGY.md#phase-3--stacked-country-actions-section-301-section-338).
  - Sep 15: Procs 11064/11065 change the alcohol and autos baskets, and both now stack on
    Section 232.
  - Sep 29: Procs 11061–11063 impose import bans, kept at the 50% basket rate (no-op).
  - Oct 30: the Proclamation of Oct 23, 2026 changes the autos basket again (−22, +100).
- Phase 3 regimes can now end: the registry loop passes `end_date` through, so the
  alcohol and autos regimes are split into dated versions instead of being edited in place.
- New lists:
  - [canada-338-alcohol-2026-09-15.csv](tariff-lists/canada-338-alcohol-2026-09-15.csv) (101 codes)
  - [canada-338-autos-2026-09-15.csv](tariff-lists/canada-338-autos-2026-09-15.csv) (513)
  - [canada-338-autos-2026-10-30.csv](tariff-lists/canada-338-autos-2026-10-30.csv) (591)

  They are built by the new `AMENDMENTS` table in `extract-338-annex.py`, and
  `validate-338.py` gained a section that checks them.
- Added 2026-09-15 and 2026-10-30 to `date_strings` and re-ran the main notebook.
  - `country-by-time.csv` is unchanged for every earlier date and gains rows for the two
    new dates.
  - `daily-tariff-latest-data.csv` is unchanged through Sep 14 and now runs to Dec 25, 2026.
  - Canada 7.66% → 7.94% → 7.97%; national 11.46% → 11.49% → 11.50%.
  - Oct 30 falls after this run, so it appears in the series as a scheduled step.
- Corrected Canada's Aug 22 level from 7.67% to 7.66% (it is 7.6647; earlier notes rounded
  it up). The +1.85 pp step is unchanged.
- Corrected the auto-parts modeling limitation. It called `_mask_auto` a coarse HS6
  approximation; it is not. Checked against the Proclamation 10908 annex and HTSUS
  note 33(g), `auto-tariffs.csv` lists codes at the same granularity as the law (8537.10
  is listed there at six digits). The Section 338 switchgear effect, 0.19 pp, comes
  from applying the list's passenger-vehicle end-use condition flat by HS code — the
  same convention as the aircraft and pharma exemptions. No rates changed by this
  correction.
- The same check found three Proclamation 10908 problems that are logged under
  [open issues](METHODOLOGY.md#5-open-issues) and not yet corrected.

## 2026-10-23

- Re-ran the main notebook so the daily series again runs `BUFFER_DAYS` (60) past the run
  date; the Aug 24 run ended on Oct 23. No rates changed: `country-by-time.csv` is
  byte-identical, and `daily-tariff-latest-data.csv` is identical through Oct 23 and
  forward-filled at 11.46% to Dec 22, 2026.
- Corrected figures left over from before the net-of-MFN cap fix: the Jul 24 national step
  is **+0.33pp** (10.89% → 11.22%), not +0.50pp, in the forced-labor detail and notebook
  entries 8 and 9, and the proposal → final change is now split three ways (rates −0.26,
  net-of-MFN cap −0.18, pharma −0.09pp).
- Committed the five input lists the main notebook reads but that were never tracked
  ([301-labor-economies-FINAL.csv](tariff-lists/301-labor-economies-FINAL.csv),
  [301-labor-part-a.csv](tariff-lists/301-labor-part-a.csv),
  [mfn-per-code.csv](tariff-lists/mfn-per-code.csv),
  [timber-232.csv](tariff-lists/timber-232.csv),
  [china-30for30-model-list.csv](tariff-lists/china-30for30-model-list.csv)), so a fresh
  clone can run it.

## 2026-09-28

- **U.S.-China "30-for-30" list reviewed and staged off.** The Sep 27, 2026 Board of Trade
  release is a framework with an approved 77-code U.S. import list but no rate, date or
  instrument, so nothing enters the published series (`country-by-time.csv` and
  `daily-tariff-latest-data.csv` are unchanged). See the "Announced, not enacted"
  section of [METHODOLOGY.md](METHODOLOGY.md#announced-not-enacted--us-china-30-for-30-list-staged-off).
- Added [extract-china-30for30.py](extract-china-30for30.py), which writes two CSVs to
  `tariff-lists/` (the list as printed; the engine form with the seven juvenile-furniture
  ex-outs resolved to 13 HTS10 lines), and [validate-china-30for30.py](validate-china-30for30.py),
  which pins the list to the PDF, the $29.6B 2024 coverage, the disjointness from the 232
  and labor Part A lists, and the −0.86pp China step.
- Main notebook: the list is loaded as `STACKED_INCLUDE_LISTS["China-30for30"]`; a staged
  regime `China-30for30` (Section 301, `scope="listed"`, rate −12.5, labor carve-outs
  mirrored) is appended to `STACKED_REGIMES` only when `CHINA_30FOR30_LIVE` is True (default
  False). `_make_stacked_apply` floors the stacked result at zero so a negative-rate
  regime models a dated reduction; positive regimes are unaffected. Smoke-tested: flag off
  reproduces the published China figure bit-for-bit; flag on moves only the 124 listed
  HTS10 lines, each from 12.5 to 0.
- Added [china-30for30-analysis.ipynb](china-30for30-analysis.ipynb): what China's rate does
  if the list is excluded from the labor 301 (−0.86pp China, −0.12pp national), by product
  group, with the legacy-301 residual.

## 2026-08-24

- **Section 338 Canada actions deferred three days by Proclamation 11056** (Aug 18, 2026;
  FR Doc 2026‑17294, [338-pause-2026-17294.pdf](tariff-lists/338-pause-2026-17294.pdf)).
  The proclamation suspended the alcohol, dairy and motor-vehicle duties for 3 days pending
  negotiations and amended the effective date in each Annex II chapeau from Aug 19 to
  **Aug 22, 2026**. Negotiations failed at the last minute, so the duties are in force from
  Aug 22. Baskets, the 50% rate and the note 51 carve-outs are unchanged.
- Modeled purely as a date change: the three `Canada-338-*` regimes' `effective_date` moved
  to `2026-08-22`, the `date_strings` panel point moved with it, and a no-op registry row for
  Proclamation 11056 keeps the action timeline a faithful record. Canada's +1.85pp step
  (5.82% → 7.67%) is unchanged in size; only Aug 19–21 differ, where Canada (and the national
  average) now sit at the pre‑338 level.
- Also fixed the stale `_make_stacked_apply` docstring, which still described timber as an
  unmodeled Section 232 sector and cited the chapter‑44 carve-out misdiagnosis corrected Jul 23.
- Refreshed `canada-338-analysis.ipynb` to the Aug 22 step date.

## 2026-07-23

- **Section 301 forced-labor action went LIVE** with its final Notice of Actions
  (Docket USTR–2026–0265/0266), effective Jul 24, 2026 — the day the Section 122
  surcharge lapses. Flipped `LABOR_301_LIVE = True`; the action now moves
  `country-by-time.csv` and `daily-tariff-latest-data.csv`. National import-weighted
  average steps **+0.33pp** on Jul 24 (10.89% → 11.22%). Rates repointed to
  [301-labor-economies-FINAL.csv](tariff-lists/301-labor-economies-FINAL.csv);
  vs the provisional, five economies dropped 12.5→10 (Honduras, India, Pakistan,
  Sri Lanka, Trinidad & Tobago) plus EU 12.5→10, and EU/Taiwan/Japan/Korea/Switzerland
  moved to a net-of-MFN cap. The cap now nets against each product's statutory column-1
  MFN (`301 = max(0, cap − MFN)` per HS10) for the four non-FTA economies (EU, Taiwan,
  Japan, Switzerland); Korea stays on the flat cap because KORUS is overridden to the
  flat rate. Netting the four lowers their Jul-24 effective tariff (EU −0.66, Switzerland
  −0.70, Taiwan −0.43, Japan −0.40 pp) and the national step from +0.50 to **+0.33pp**;
  the EU now *falls* across the §122 lapse (8.95% → 8.40%) rather than rising.
- Exemptions now come from **Annex II Part A** ([301-labor-part-a.csv](tariff-lists/301-labor-part-a.csv),
  2,113 codes), parsed directly from the notice's machine-readable tables (no OCR).
  Modeling choice **C**: `pharma`-flagged codes (700) are exempted flat, `aircraft`
  (541) and `ex` (16) are taxed — see the forced-labor detail section. Country-specific
  Annex II Parts B–O are not modeled (documented as a small upward bias).
- Provisional Jun 5 files ([301-labor-economies.csv](tariff-lists/301-labor-economies.csv),
  [301-labor-exemptions.csv](tariff-lists/301-labor-exemptions.csv)) retained as the
  archived baseline for `validate-301-labor.py` diff mode and the planned
  provisional-vs-final comparison notebook.
- Added the **Section 232 timber/lumber action** (Proclamation 10976, effective
  Oct 14, 2025) as a Phase-2 sector override. Rates: softwood timber/lumber 10%
  (all countries), upholstered wooden furniture and completed kitchen
  cabinets/vanities 25% (UK 10%, Japan 15%, EU 15%). The Jan 1 2027 step-up
  (furniture 30%, cabinets 50%; deferred one year by the Dec 2025 amendment) is
  registered but intentionally left out of `date_strings`, so it does not yet move
  the published panel — same convention as the metals Annex III expiry.
- Source list [timber-232.csv](tariff-lists/timber-232.csv): 22 codes enumerated
  directly from the proclamation's U.S. note 37 annex (softwood 4403/4406/4407,
  furniture 9401.61, cabinets 9403), so no extraction script is needed.
- Added `_mask_timber` to `_mask_all_232`, so timber-sector goods are now carved
  out of the Section 122 surcharge and the Phase-3 Section 301/338 stacked actions,
  and (per Proc 10976 clause 4) take the timber rate instead of the IEEPA/301 base.
- **Impact on `country-by-time.csv` from Oct 14 2025** (2024 weights): wood
  exporters move — Vietnam **+0.80pp**, Cambodia **+0.59pp**, Canada **+0.18pp**,
  China **+0.13pp** (furniture/cabinets rise to 25%); Brazil **−0.08pp** and New
  Zealand **−0.16pp**, where wood previously took a *higher* IEEPA/301 base and now
  takes the lower timber 232 rate. No date before Oct 14 2025 changes.
- **Corrected the chapter-44 "deferred wood carve-out" note.** The 64 chapter-44
  codes in the Canada-338 autos basket are hardwood/plywood/joinery, *not*
  Proclamation 10976 timber, so they are correctly dutiable and were never a 232
  carve-out bias. The only timber↔338 overlap is a single cabinet code
  (9403.60.8093), now correctly carved out (50% → 25%). Canada's Section 338 step
  is essentially unchanged (~1.85pp). The correction is reflected in the README
  modeling notes, `canada-338-analysis.ipynb`, and `validate-338.py`.
- Added [validate-timber.py](validate-timber.py); `validate-338.py` still passes
  (its magnitudes are raw-basket computations, independent of the engine).

## 2026-07-22

- Added the **Section 301 forced-labor action** as a provisional, staged-off Phase-3
  layer (FR Doc 2026-11296 — a determination and proposed action, not yet a Notice of
  Action). Generated from [301-labor-economies.csv](tariff-lists/301-labor-economies.csv)
  (60 economies, 50 tracked, two tiers) with exemptions from
  [301-labor-exemptions.csv](tariff-lists/301-labor-exemptions.csv) (1,655 codes). Gated
  by `LABOR_301_LIVE` (default `False`); published output is unchanged. That section has since become the forced-labor detail in
  [METHODOLOGY.md](METHODOLOGY.md#section-301-forced-labor-action--detail).
- Established that the labor **Annex A is bit-for-bit identical to the combined Section
  122 exemption lists**, so the engine reuses them; the equality is asserted by the new
  guardrail.
- Extended `_make_stacked_apply` with two country-conditional carve-outs (`usmca_exempt`
  for CA/MX, `cafta_textile_exempt` for the six CAFTA-DR economies), both no-ops for the
  existing Brazil/Canada regimes.
- Added [validate-301-labor.py](validate-301-labor.py) — baseline guardrail plus a diff
  mode for reconciling against the Notice of Action when it issues.

## 2026-07-21

- Generalized Phase 3 from "Section 301 country actions" into a **stacked country action**
  layer covering both Section 301 and Section 338. `SECTION_301_REGIMES` became
  `STACKED_REGIMES`, gaining `authority` and `scope` fields; `_mask_301_exempt` became
  `_mask_stacked_exempt`, joined by a new `_mask_stacked_include` for inclusion-scoped
  actions. The Section 232 carve-out logic was reused unchanged — notes 50(a)(vi) and
  51(c) reference the same 9903.82 headings.
- Exemption and include lists are now keyed by **list name rather than by regime**, so
  several regimes can share one list. The three Section 338 actions share a single
  civil-aircraft carve-out.
- Added the three Section 338 Canada actions (alcohol, dairy, motor vehicles), all
  effective Aug 19, 2026 at 50%.
- Added four list files extracted from the proclamation annexes:
  - [canada-338-alcohol.csv](tariff-lists/canada-338-alcohol.csv) — 63 codes
  - [canada-338-dairy.csv](tariff-lists/canada-338-dairy.csv) — 52 codes
  - [canada-338-autos.csv](tariff-lists/canada-338-autos.csv) — 439 codes
  - [canada-338-aircraft-exempt.csv](tariff-lists/canada-338-aircraft-exempt.csv) — 554
    codes, shared carve-out
- Added [extract-338-annex.py](extract-338-annex.py) and [validate-338.py](validate-338.py).
- **Fixed the Section 122 end-date off-by-one.** Annex I terminates the surcharge *at*
  12:01 a.m. Jul 24, 2026, so the last covered day is Jul 23; the registry previously
  carried `end_date: 2026-07-24` and the engine tests `date <= end_date`, applying the
  surcharge one day too long. Rates are unaffected — only the width of the Brazil
  overlap spike, now correctly Jul 22–23.
- Documented two biases newly visible in the Section 338 results: the deferred chapter 44
  wood carve-out (upward bias) and the coarse HS6 auto-parts mask (downward bias, 0.19 pp).

## 2026-07-20

- Added a third phase to the tariff engine for Section 301 country actions, applied
  after Section 232 so that 232 goods can be carved out and the 301 duty stacked on
  what remains.
- Added the Brazil Section 301 action (USTR Notice of Action, Jul 15, 2026), driven by
  a declarative `SECTION_301_REGIMES` config so subsequent 301 country actions need
  only a list file and a config entry.
- Added [brazil-301-exemptions.csv](tariff-lists/brazil-301-exemptions.csv) — 2,126 HS
  codes across four exemption categories (`flat`, `named`, `aircraft`, `pharma`),
  extracted from the notice with [extract-301-exemptions.py](extract-301-exemptions.py).
- Gave the Section 122 surcharge an `end_date` of 2026-07-24. It previously had none,
  so the 10% surcharge ran indefinitely past the end of its 150-day authority.
- Factored the Section 232 union into a single `_mask_all_232` helper, replacing the
  expression previously inlined in `_apply_s122_exemptions`, so future 232 sectors only
  need adding in one place.
- Extended the daily series in the plotting cell from 2026-06-30 to 2026-12-31; the
  previous end date would have truncated the July actions out of the chart.

## 2026-04-03 (cleanup)

- Extracted revenue analysis (2025 tariff revenue estimate) from the main notebook into [revenue-analysis.ipynb](revenue-analysis.ipynb).
- Extracted Section 122 exemption and SCOTUS analysis from the main notebook into [section-122-analysis.ipynb](section-122-analysis.ipynb).
- Added April 6, 2026 Section 232 metals tiered restructuring (Proclamation of Apr 2, 2026) to the tariff engine.
- Added four new tariff list files for the metals restructuring:
  - [metals-annex-IA.csv](tariff-lists/metals-annex-IA.csv) — 50% tier (279 HS codes)
  - [metals-annex-IB.csv](tariff-lists/metals-annex-IB.csv) — 25% tier (388 HS codes)
  - [metals-annex-II-removed.csv](tariff-lists/metals-annex-II-removed.csv) — removed from scope (165 HS codes)
  - [metals-annex-III-temporary.csv](tariff-lists/metals-annex-III-temporary.csv) — temporary ~15% rate through 2027 (47 HS codes)

## 2026-02-24 (cleanup)

- Moved historical snapshots to [old-data](old-data):
  - [tariff-summary-05-22-2025.csv](old-data/tariff-summary-05-22-2025.csv)
  - [tariff-summary-06-03-2025.csv](old-data/tariff-summary-06-03-2025.csv)
- Moved legacy notebooks to [old-code](old-code):
  - [clean-aug7-list.ipynb](old-code/clean-aug7-list.ipynb)
  - [make-tariff-by-country-by-time-new.ipynb](old-code/make-tariff-by-country-by-time-new.ipynb)
  - [tariff-summary.ipynb](old-code/tariff-summary.ipynb)
