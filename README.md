## trade-war-redux-2025

<p float="left" align="middle">
  <img src="tariff-fig.png" width="875" />
</p>

Updated: 2026-07-20

This repository tracks U.S. tariff changes and produces data + charts used in the public tracker.

## Primary workflow

1. [make-tariff-by-country-by-time.ipynb](make-tariff-by-country-by-time.ipynb)
   - Builds country/time tariff panel data.
   - Writes [country-by-time.csv](country-by-time.csv) and [daily-tariff-latest-data.csv](daily-tariff-latest-data.csv).

2. [plot-tariff-by-country-by-time.ipynb](plot-tariff-by-country-by-time.ipynb)
   - Reads the latest output files and produces website charts/tabs.
   - Uses [federal-tax-duty.csv](federal-tax-duty.csv) and [NIPA-imports.csv](NIPA-imports.csv) for historical tariff calculations.

3. [get-country-hs2-tariff.ipynb](get-country-hs2-tariff.ipynb)
   - Generates country-by-HS2 tariff outputs in [data-hs2](data-hs2).

## Standalone analysis notebooks

4. [revenue-analysis.ipynb](revenue-analysis.ipynb)
   - Estimates 2025 tariff revenue using Census import data and the tariff engine.
   - Self-contained: includes its own copy of the tariff engine pipeline (masks, apply functions, action registry).

5. [section-122-analysis.ipynb](section-122-analysis.ipynb)
   - Analyzes Section 122 surcharge exemption coverage and the pre/post SCOTUS tariff shift.
   - Reads [country-by-time.csv](country-by-time.csv) from the main notebook; must be run after (1).

6. [brazil-301-analysis.ipynb](brazil-301-analysis.ipynb)
   - Tariff impact and exemption coverage for the Jul 22, 2026 Brazil Section 301 action.
   - Writes figures to [figures](figures); must be run after (1).
   - Imports the tariff engine directly from the main notebook (executes its code cells
     up to `tariff_imports`), so it holds no duplicate copy of the masks or registry.

## Helper scripts

- [extract-301-exemptions.py](extract-301-exemptions.py)
  - Extracts the U.S. note exemption subdivisions from a USTR Section 301 Notice of
    Action PDF into a single CSV with a `category` column.
  - Asserts the expected per-category code counts and fails loudly on a mismatch —
    update the counts in `SUBDIVISIONS` for each new notice.
  - Usage: `python extract-301-exemptions.py <notice.pdf> <out.csv>`

## Key folders

- [data](data): source and helper data files.
- [data-hs2](data-hs2): generated HS2 tariff output files.
- [docs](docs): rendered HTML/chart outputs.
- [tariff-lists](tariff-lists): input tariff schedule/list files.
- [old-data](old-data): archived historical datasets not used by the main notebooks.
- [old-code](old-code): archived notebooks and code no longer part of the main workflow.
- [old-files](old-files): prior archive folder kept for backward compatibility.

## Tariff events tracked in `make-tariff-by-country-by-time.ipynb`

The notebook encodes U.S. tariff policy changes in a structured `TARIFF_ACTIONS` registry applied chronologically. Each action carries its effective date, legal authority, executive order/proclamation reference, and a short description. Actions are split into three phases: **Phase 1** resets country-level base rates (IEEPA / Section 122 layer); **Phase 2** stamps sector-specific tariffs and product exemptions on top; **Phase 3** applies Section 301 country actions, which *add* to the rate already in place rather than replacing it, and carve out goods already subject to Section 232.

### Phase 1 — Country-level base rates

| Date | Authority | Reference | Description |
|------|-----------|-----------|-------------|
| Feb 4, 2025 | IEEPA | EO 14193/14194/14195 | Fentanyl emergency: 20% on China and Hong Kong; Canada (EO 14193) and Mexico (EO 14194) also included but immediately paused |
| Mar 6, 2025 | IEEPA | Amendments to EO 14193/14194 | USMCA carve-out: Canada 8.75%, Mexico 4.5% |
| Apr 5, 2025 | IEEPA | EO 14257 | Reciprocal tariffs activate: 10% global baseline, country-specific rates from Annex I |
| Apr 8, 2025 | IEEPA | Amendment to EO 14257 | China/HK escalated to 84% reciprocal (+20% fentanyl = 104%) |
| Apr 9, 2025 | IEEPA | Amendment to EO 14257 | 90-day pause: all countries reset to 10%; China/HK raised to 125% |
| May 12, 2025 | IEEPA | U.S.-China Joint Statement (Geneva) | China/HK reciprocal from 125% to 10% (+20% fentanyl = 30%) |
| Aug 7, 2025 | IEEPA | EO 14326, EO 14323, EO 14325 | August country-specific rates from EO 14326; Brazil +40% (EO 14323); Canada fentanyl raised to 35% (EO 14325) |
| Nov 1, 2025 | IEEPA | EO 14358, EO 14357 | China 1-year truce: fentanyl reduced to 10% (net 20%); Canada rate scaled up |
| Nov 14, 2025 | IEEPA | U.S.-Switzerland Joint Statement | Switzerland rate capped at 15% |
| Dec 4, 2025 | IEEPA | ITA notice (90 FR 55964) | South Korea deal: 15% reciprocal ceiling |
| Feb 7, 2026 | IEEPA | EO suspending EO 14329; U.S.-India framework | India: Russian oil tariff removed, reciprocal reduced to 18% |
| Feb 20, 2026 | Executive Order | EO "Ending Certain Tariff Actions" | Supreme Court rules IEEPA does not authorize tariffs (*V.O.S. Selections v. United States*, 6-3); all IEEPA ad valorem duties revoked; Section 232 and 301 preserved; base rates zeroed |
| Feb 24, 2026 | Section 122 | Proclamation "Imposing a Temporary Import Surcharge" | 10% universal surcharge (150-day balance-of-payments emergency); Canada/Mexico USMCA-compliant goods exempt. Lapses after Jul 24, 2026 (`end_date`) |

### Phase 2 — Sector overrides and product exemptions

| Date | Authority | Reference | Description |
|------|-----------|-----------|-------------|
| Mar 12, 2025 | Section 232 | Proclamation 10895 (aluminum), 10896 (steel) | Steel and aluminum tariffs at 25% globally |
| Apr 3, 2025 | Section 232 | Proclamation 10908 | 25% tariff on automobiles and parts; Canada/Mexico treated as ~15% |
| Apr 11, 2025 | IEEPA | Amendment to EO 14257 | Consumer electronics (phones, laptops, etc.) exempt from reciprocal tariffs |
| Apr 11, 2025 | IEEPA | EO 14257 Annex II | Annex II product-level exemptions from reciprocal tariffs |
| Jun 3, 2025 | Section 232 | Proclamation 10947 | Steel and aluminum tariffs raised to 50%; UK remains at 25% per bilateral deal |
| Aug 7, 2025 | Section 232 / IEEPA | Proclamation 10962, Proc 10908 amendments, EO 14323 Annex | Copper at 50%; auto deal rates for Japan, EU, South Korea at 15%; Brazil-specific product exemptions |
| Nov 14, 2025 | IEEPA | EO 14360 | Agricultural product exemptions; China phone fentanyl component reduced to 10% |
| Dec 4, 2025 | Section 232 | ITA notice (90 FR 55964) | South Korea auto deal at 15% |
| Feb 20, 2026 | Section 232 (surviving) | EO "Ending Certain Tariff Actions" — 232 preserved | Re-apply surviving 232 tariffs: steel/aluminum 50% (UK 25%), autos (25%, deal rates for UK/JP/EU/KR), copper 50% |
| Feb 24, 2026 | Section 122 | Proclamation Annex I, subdivision (aa)(ii) | Product exemptions from surcharge: energy (Ch. 27), critical minerals, pharma, ag, electronics, fertilizers, semiconductors, etc. (~1,098 HS codes) |
| Apr 6, 2026 | Section 232 | Proclamation "Strengthening Actions..." (Apr 2, 2026) | Metals tiered restructuring: Annex I-A 50% (UK 25%), Annex I-B 25% (UK 15%), Annex III ~15% temp (through 2027), Annex II exempt; Russian alu 200% |

### Phase 3 — Section 301 country actions

Section 301 (19 U.S.C. §§2411–20) is a separate legal layer from IEEPA and Section 232. It survived the Feb 20, 2026 SCOTUS ruling, and per U.S. note 50(a)(i) it **stacks** on top of other chapter 99 duties rather than replacing them. Goods already subject to Section 232 are carved out.

New 301 actions are added declaratively: extract the exemption list with [extract-301-exemptions.py](extract-301-exemptions.py), add the codes to `SECTION_301_EXEMPT_LISTS`, and append one entry to `SECTION_301_REGIMES`. No new logic is required.

| Date | Authority | Reference | Description |
|------|-----------|-----------|-------------|
| Jul 22, 2026 | Section 301 | USTR Notice of Action — Brazil (Jul 15, 2026) | 25% on all goods of Brazil; exemptions for 864 listed subheadings, 11 named articles, 546 civil-aircraft codes, 705 pharmaceutical-application codes, and all Section 232 sectors |
| Jul 31, 2026 | Section 301 | USTR Notice Annex I.B — U.S. note 50(a)(vi)(8) | Patented pharmaceuticals added to the Brazil 232 carve-out (no effect — sector not modeled) |

Because Section 122 runs through Jul 24 and the Brazil 301 action begins Jul 22, the two overlap for three days. All start and end dates are modeled literally, so Brazil shows a brief spike (≈17.5%) on Jul 22–24 before settling at ≈13.3%.

### Actions not yet incorporated

The following Section 232 actions require product-level HS code lists not yet available and are excluded from the current model:

| Date | Authority | Reference | Description |
|------|-----------|-----------|-------------|
| Oct 14, 2025 | Section 232 | Proclamation 10976 | Timber/lumber: 10% softwood, 25% furniture/cabinets |
| Nov 1, 2025 | Section 232 | Proclamation 10984 | Trucks/buses: 25% trucks and parts, 10% buses |
| Jan 15, 2026 | Section 232 | Proclamation 11002 | Semiconductors: 25% on narrow set of advanced chips |
| — | Section 232 | Headings 9903.04.60–.66 | Patented pharmaceuticals |

These omissions now have a second-order effect. Section 301 country actions exempt goods already subject to Section 232, so goods in these four unmodeled sectors receive the **full 301 rate when they should be exempt**, biasing the affected country's effective rate upward. This applies to every 301 action carrying the same carve-out, not just Brazil.

### Modeling limitations

- **End-use conditional exemptions are applied flat.** The Brazil 301 civil-aircraft exemption is conditional on meeting HTSUS general note 6, and the pharmaceutical exemption applies only to pharmaceutical end uses. Neither is resolvable from HS10 import data, so both are applied to every listed code. This **over-exempts**, partially offsetting the upward bias described above.
- **In-transit relief is ignored.** Heading 9903.05.02 exempts goods loaded before Jul 22, 2026 and entered before Jul 29, 2026. Given Brazil–U.S. transit times, most goods entering that week are exempt in practice, so the modeled Jul 22 step overstates the rate for its first week. Consistent with prior actions carrying similar grace windows, none of which are modeled.
- **Annex II interaction.** Products removed from Section 232 scope by the Apr 6, 2026 metals Annex II are no longer provided for in the 9903.82 headings, so they do *not* qualify for the 301 Section 232 carve-out. The model handles this explicitly (21 products, ~0.03% of U.S. imports from Brazil).

---

## Cleanup notes (2026-02-24)

- Moved historical snapshots to [old-data](old-data):
  - [tariff-summary-05-22-2025.csv](old-data/tariff-summary-05-22-2025.csv)
  - [tariff-summary-06-03-2025.csv](old-data/tariff-summary-06-03-2025.csv)
- Moved legacy notebooks to [old-code](old-code):
  - [clean-aug7-list.ipynb](old-code/clean-aug7-list.ipynb)
  - [make-tariff-by-country-by-time-new.ipynb](old-code/make-tariff-by-country-by-time-new.ipynb)
  - [tariff-summary.ipynb](old-code/tariff-summary.ipynb)

## Cleanup notes (2026-04-03)

- Extracted revenue analysis (2025 tariff revenue estimate) from the main notebook into [revenue-analysis.ipynb](revenue-analysis.ipynb).
- Extracted Section 122 exemption and SCOTUS analysis from the main notebook into [section-122-analysis.ipynb](section-122-analysis.ipynb).
- Added April 6, 2026 Section 232 metals tiered restructuring (Proclamation of Apr 2, 2026) to the tariff engine.
- Added four new tariff list files for the metals restructuring:
  - [metals-annex-IA.csv](tariff-lists/metals-annex-IA.csv) — 50% tier (279 HS codes)
  - [metals-annex-IB.csv](tariff-lists/metals-annex-IB.csv) — 25% tier (388 HS codes)
  - [metals-annex-II-removed.csv](tariff-lists/metals-annex-II-removed.csv) — removed from scope (165 HS codes)
  - [metals-annex-III-temporary.csv](tariff-lists/metals-annex-III-temporary.csv) — temporary ~15% rate through 2027 (47 HS codes)

## Update notes (2026-07-20)

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

