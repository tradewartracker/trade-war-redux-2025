## trade-war-redux-2025

<p float="left" align="middle">
  <img src="tariff-fig.png" width="875" />
</p>

Updated: 2026-07-22

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

7. [canada-338-analysis.ipynb](canada-338-analysis.ipynb)
   - Coverage, incidence and rate impact of the three Aug 19, 2026 Section 338 actions
     on Canada: what is hit, what is not, top products, and a decomposition of the
     +1.85pp rate step against the +2.49pp naive figure.
   - Quantifies the one real bias (the HS6 auto-parts mask, ~0.19pp down) and shows
     why the chapter-44 wood in the basket is *not* a bias (hardwood/plywood, non-232).
   - Writes figures to [figures](figures); must be run after (1).
   - Imports the tariff engine from the main notebook, same as (6).

8. [section122-to-301labor-transition.ipynb](section122-to-301labor-transition.ipynb)
   - Compares three scenarios across the Section 122 surcharge's July 24, 2026 expiry:
     the surcharge in force, the gap if nothing replaces it, and the **provisional**
     Section 301 forced-labor action taking its place. Uses the main notebook's engine and
     2024 weights; activates the staged-off labor regime by hand for the third scenario.
   - Finding: in aggregate the labor duty **more than** replaces the surcharge (national
     average ~10.8% → ~11.7%, a net +0.9pp, via a ~7.6% gap — national figures include the
     +2.3pp MFN baseline to match the tracker), because it charges 12.5% where the surcharge
     charged 10%. It also redistributes sharply — 12.5%-tier countries pay more, while the
     10% tier, USMCA (Canada/Mexico), and the flat CAFTA-DR textile carve-out leave others
     lighter. Both regimes are compared on the same exemption basis (see the aircraft note
     in the forced-labor detail section). Note: this notebook models the **provisional**
     Jun 5 proposal; the final Notice of Action (now live) is lighter (national step +0.5pp,
     see the forced-labor detail) — a dedicated provisional-vs-final comparison is planned.
   - Writes figures to [figures](figures); must be run after (1).

## Helper scripts

- [extract-301-exemptions.py](extract-301-exemptions.py)
  - Extracts the U.S. note exemption subdivisions from a USTR Section 301 Notice of
    Action PDF into a single CSV with a `category` column.
  - Asserts the expected per-category code counts and fails loudly on a mismatch —
    update the counts in `SUBDIVISIONS` for each new notice.
  - Usage: `python extract-301-exemptions.py <notice.pdf> <out.csv>`

- [extract-338-annex.py](extract-338-annex.py)
  - Extracts the target basket of each Section 338 proclamation, plus the shared
    civil-aircraft carve-out, into CSVs with `HTSUS` and `description` columns.
  - Cross-checks Annex I (descriptive) against Annex II (HTSUS legal text). The two
    restate the same codes, so disagreement means a bad parse. Unlike the hardcoded
    counts in the 301 script, this guard needs no per-notice maintenance.
  - Add a new action by appending to the `ACTIONS` table; no other change needed.
  - Usage: `python extract-338-annex.py`

- [validate-338.py](validate-338.py)
  - Independent second opinion on the Section 338 lists: re-parses the annexes with a
    different method, checks the lists against observed trade data, and asserts the
    economic magnitudes quoted downstream so a silent list change cannot move the
    published numbers unnoticed.
  - Imports its config from `extract-338-annex.py` so the two cannot disagree.
  - Usage: `python validate-338.py` (exits non-zero on failure)

- [validate-301-labor.py](validate-301-labor.py)
  - Guardrail for the **provisional** Section 301 forced-labor action. Baseline mode
    asserts the economy→tier table and the Annex A exemption list are internally
    consistent and — the load-bearing check — that Annex A is still bit-for-bit identical
    to the combined Section 122 exemption lists, which is why the notebook can reuse them.
  - Diff mode (`--diff-economies … --diff-exemptions …`) runs when the Notice of Action
    lands: it reports economies added/removed, per-economy rate changes, and Annex A code
    deltas against the committed provisional baseline, and re-checks the Section 122
    equality. It is the punch list for turning the provisional model into the real one.
  - Usage: `python validate-301-labor.py` (exits non-zero on failure)

## Key folders

- [data](data): source and helper data files.
- [data-hs2](data-hs2): generated HS2 tariff output files.
- [docs](docs): rendered HTML/chart outputs.
- [tariff-lists](tariff-lists): input tariff schedule/list files.
- [old-data](old-data): archived historical datasets not used by the main notebooks.
- [old-code](old-code): archived notebooks and code no longer part of the main workflow.
- [old-files](old-files): prior archive folder kept for backward compatibility.

## Tariff events tracked in `make-tariff-by-country-by-time.ipynb`

The notebook encodes U.S. tariff policy changes in a structured `TARIFF_ACTIONS` registry applied chronologically. Each action carries its effective date, legal authority, executive order/proclamation reference, and a short description. Actions are split into three phases: **Phase 1** resets country-level base rates (IEEPA / Section 122 layer); **Phase 2** stamps sector-specific tariffs and product exemptions on top; **Phase 3** applies stacked country actions (Section 301 and Section 338), which *add* to the rate already in place rather than replacing it, and carve out goods already subject to Section 232.

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
| Feb 24, 2026 | Section 122 | Proclamation "Imposing a Temporary Import Surcharge" | 10% universal surcharge (150-day balance-of-payments emergency); Canada/Mexico USMCA-compliant goods exempt. Annex I terminates the surcharge *at* 12:01 a.m. Jul 24, so the last covered day is Jul 23 (`end_date`) |

### Phase 2 — Sector overrides and product exemptions

| Date | Authority | Reference | Description |
|------|-----------|-----------|-------------|
| Mar 12, 2025 | Section 232 | Proclamation 10895 (aluminum), 10896 (steel) | Steel and aluminum tariffs at 25% globally |
| Apr 3, 2025 | Section 232 | Proclamation 10908 | 25% tariff on automobiles and parts; Canada/Mexico treated as ~15% |
| Apr 11, 2025 | IEEPA | Amendment to EO 14257 | Consumer electronics (phones, laptops, etc.) exempt from reciprocal tariffs |
| Apr 11, 2025 | IEEPA | EO 14257 Annex II | Annex II product-level exemptions from reciprocal tariffs |
| Jun 3, 2025 | Section 232 | Proclamation 10947 | Steel and aluminum tariffs raised to 50%; UK remains at 25% per bilateral deal |
| Aug 7, 2025 | Section 232 / IEEPA | Proclamation 10962, Proc 10908 amendments, EO 14323 Annex | Copper at 50%; auto deal rates for Japan, EU, South Korea at 15%; Brazil-specific product exemptions |
| Oct 14, 2025 | Section 232 | Proclamation 10976 | Timber/lumber: softwood 10% (all countries); upholstered wooden furniture and completed kitchen cabinets/vanities 25% (UK 10%, Japan 15%, EU 15%). Steps up Jan 1 2027 — furniture 30%, cabinets 50% (registered, not surfaced in `date_strings`). Autos take precedence per clause 6 |
| Nov 14, 2025 | IEEPA | EO 14360 | Agricultural product exemptions; China phone fentanyl component reduced to 10% |
| Dec 4, 2025 | Section 232 | ITA notice (90 FR 55964) | South Korea auto deal at 15% |
| Feb 20, 2026 | Section 232 (surviving) | EO "Ending Certain Tariff Actions" — 232 preserved | Re-apply surviving 232 tariffs: steel/aluminum 50% (UK 25%), autos (25%, deal rates for UK/JP/EU/KR), copper 50% |
| Feb 24, 2026 | Section 122 | Proclamation Annex I, subdivision (aa)(ii) | Product exemptions from surcharge: energy (Ch. 27), critical minerals, pharma, ag, electronics, fertilizers, semiconductors, etc. (~1,098 HS codes) |
| Apr 6, 2026 | Section 232 | Proclamation "Strengthening Actions..." (Apr 2, 2026) | Metals tiered restructuring: Annex I-A 50% (UK 25%), Annex I-B 25% (UK 15%), Annex III ~15% temp (through 2027), Annex II exempt; Russian alu 200% |

### Phase 3 — Stacked country actions (Section 301, Section 338)

Phase 3 holds country-level actions that **add** to the rate already in place rather than replacing it, and that carve out goods already subject to Section 232. Both properties require them to run after Phase 2. Two legal authorities sit here, and both survived the Feb 20, 2026 SCOTUS ruling on IEEPA:

- **Section 301** (19 U.S.C. §§2411–20) — stacks per U.S. note 50(a)(i)
- **Section 338** (19 U.S.C. §1338) — stacks per U.S. note 51(a); a dormant 1930 retaliation provision authorizing duties of up to 50% against a country that discriminates against U.S. commerce

They differ in exactly one respect, captured by the `scope` field of `STACKED_REGIMES`: a 301 action covers **all** goods of a country except an exemption list, while a 338 action reaches only the codes **listed** in its annex. Every action in the phase is additive, so they commute and a country may carry several at once.

New actions are added declaratively — extract the code list, register it in Section 2, and append one entry to `STACKED_REGIMES`. No new logic is required.

| Date | Authority | Reference | Description |
|------|-----------|-----------|-------------|
| Jul 22, 2026 | Section 301 | USTR Notice of Action — Brazil (Jul 15, 2026) | 25% on all goods of Brazil; exemptions for 864 listed subheadings, 11 named articles, 546 civil-aircraft codes, 705 pharmaceutical-application codes, and all Section 232 sectors |
| Jul 31, 2026 | Section 301 | USTR Notice Annex I.B — U.S. note 50(a)(vi)(8) | Patented pharmaceuticals added to the Brazil 232 carve-out (no effect — sector not modeled) |
| Aug 19, 2026 | Section 338 | Proclamation on Canadian alcoholic beverages (Jul 20, 2026), heading 9903.03.12 | 50% on 63 enumerated Canadian codes (beverages, some wood and paper) |
| Aug 19, 2026 | Section 338 | Proclamation on Canadian dairy (Jul 20, 2026), heading 9903.03.13 | 50% on 52 enumerated Canadian codes (milk products, sugars, caseins) |
| Aug 19, 2026 | Section 338 | Proclamation on Canadian motor vehicles (Jul 20, 2026), heading 9903.03.14 | 50% on 439 enumerated Canadian codes across 56 chapters |
| Jul 24, 2026 | Section 301 | USTR Notice of Actions — forced labor (Docket USTR–2026–0265/0266, Jul 23 2026) | 12.5% (10% for 18 economies) on all goods of 50 tracked economies; Annex II Part A (unconditional + pharmaceutical codes) and all Section 232 sectors exempt. Effective the day the Section 122 surcharge lapses. See the forced-labor detail below. |

Because Section 122 runs through Jul 23 and the Brazil 301 action begins Jul 22, the two overlap for two days. All start and end dates are modeled literally, so Brazil shows a brief spike (≈17.5%) on Jul 22–23 before settling at ≈13.3%.

The three Section 338 actions were issued the same day against Canada, all at 50%, all effective Aug 19, 2026, and all sharing a single U.S. note 51. Each retaliates for a distinct Canadian practice — provincial liquor-board bans, cheese TRQ allocation, and motor-vehicle tariffs and quotas — but the baskets deliberately target goods *other* than the offending sector, and are disjoint from one another. The civil-aircraft carve-out of note 51(d) (heading 9903.03.16, 554 codes) is enumerated once and shared by all three, so it is modeled as one exemption list referenced by three regimes. Neither the proclamations nor note 51 provide an in-transit grace window. Combined effect on Canada: **+1.85 pp** (5.82% → 7.67%), against +2.49 pp before carve-outs. (The 5.82%/7.67% levels sit ~0.18 pp above the pre-timber figures of 5.64%/7.49%, since the Section 232 timber action lifts Canada's whole curve from Oct 14 2025; the *step* is essentially unchanged.)

#### Section 301 forced-labor action — detail

Effective **Jul 24, 2026** (Docket USTR–2026–0265/0266, issued Jul 23 2026), the day the Section 122 surcharge lapses. USTR determined that 60 investigated economies failed to impose and/or effectively enforce a forced-labor import prohibition, and imposes additional duties on all their goods with exemptions. 50 of the 60 economies are in the panel's country universe (32 at 12.5%, 18 at 10%).

Modeled as Phase-3 stacked Section 301 regimes generated from [301-labor-economies-FINAL.csv](tariff-lists/301-labor-economies-FINAL.csv), one per tracked economy, `scope="all"`, carving out Section 232 goods per U.S. note 50(a)(vi) — identical mechanics to the Brazil 301 action, gated live by `LABOR_301_LIVE = True`. Aggregate effect: the national import-weighted average rises **+0.50 pp** on Jul 24 (10.89% → 11.39%) as the 10% Section 122 surcharge is replaced by the labor duty — the labor action slightly more than replaces the surcharge.

**Rate tiers.**

- **10%** on 18 tracked economies (imposed a prohibition or made ART/commitments): Argentina, Bangladesh, Cambodia, Canada, Ecuador, El Salvador, EU, Guatemala, Honduras, India, Indonesia, Malaysia, Mexico, Pakistan, Sri Lanka, Taiwan, Trinidad & Tobago, United Kingdom.
- **12.5%** on the remaining 32 tracked economies.
- **Net-of-MFN cap, modeled flat (MFN = 0).** For the EU and Taiwan (10% cap) and Japan, Korea and Switzerland (12.5% cap), the notice sets the 301 rate *net of MFN* — 301 = max(0, cap − MFN) — so total duty is capped at the tier. The engine has no per-HS MFN column and has never netted such caps, so it treats MFN as 0 and applies the cap flat. This is a modest **upward** bias for those five (exact on the many zero-MFN lines; it ignores the MFN offset that would reduce the duty on positive-MFN goods and zero it where MFN ≥ the cap).

**Exemptions.** Come from **Annex II Part A** ("Goods of Any Investigated Economy"), the base list applying to every economy, extracted to [301-labor-part-a.csv](tariff-lists/301-labor-part-a.csv) (2,113 codes) directly from the notice's machine-readable tables. Scope flags: `''` unconditional (856), `pharma` (700), `aircraft` (541), `ex` (16).

- **Pharma codes exempted flat; aircraft and Ex taxed (modeling choice "C").** The `pharma` codes (pharmaceutical-application conditional; 82% chapter-29 organic chemicals) are exempted — matching the Section 122 model, which already exempts 363 of these same codes as unconditional products, and following the standing flat-exemption convention for end-use carve-outs. The `aircraft` (civil-aircraft GN 6, conditional) and `ex` codes are **not** exempted, exactly as `_mask_s122_exempt` ignores the Section 122 aircraft exemption, keeping the labor duty and the surcharge on the same exemption basis. Both choices are flat because the end-use split is not resolvable from HS10 data: exempting pharma **over-exempts** its non-pharma use (a modest downward bias, smallest for the pharma-heavy exporters — EU, Switzerland, India — it mainly touches), and taxing aircraft **over-taxes** the civil-aircraft slice (small, since these are general industrial goods across 18 chapters where aircraft use is a minority).
- **Country-specific exemptions (Annex II Parts B–N) and the CAFTA/Jordan textile Part O are not modeled.** These add narrower carve-outs for the 13 ART/commitment economies; omitting them is a small **upward** bias on those economies. The Part O CAFTA textile relief is partly covered by the flat CAFTA-DR chapter 50–63 exemption below.
- **USMCA-compliant Canada/Mexico goods are exempt** (Annex I general notes ¶g/¶h). The model treats all Canada and Mexico imports as USMCA-eligible (same simplification as the Section 122 base), so the action nets to **~0% on both**. Flagged for revisit — real USMCA compliance is below 100%.
- **CAFTA-DR duty-free textiles/apparel** (Costa Rica, Dominican Republic, El Salvador, Guatemala, Honduras, Nicaragua; Annex I ¶i, GN 29(d)(v)) are exempt. Applied as a flat exemption of HTSUS chapters 50–63 for those six economies, which **over-exempts** — it also frees textile trade that entered under MFN or another program.
- The **textile mechanism** (three-year TRQs for Bangladesh, Cambodia, Indonesia and Malaysia tied to their U.S. cotton/textile imports; 10% applies until established) is not modeled — a volume-based allowance not resolvable from HS10 data. The FTZ "privileged foreign status" requirement and text-only exclusions (informational materials, donations, accompanied baggage) are likewise unmodeled and negligible.

The provisional Jun 5, 2026 files — [301-labor-economies.csv](tariff-lists/301-labor-economies.csv) and the 1,655-code [301-labor-exemptions.csv](tariff-lists/301-labor-exemptions.csv) — are retained as the archived baseline for `validate-301-labor.py` and the provisional-vs-final comparison. Running `validate-301-labor.py --diff-economies tariff-lists/301-labor-economies-FINAL.csv --diff-exemptions tariff-lists/301-labor-part-a.csv` reports the delta the final action introduced.

### Actions not yet incorporated

The following Section 232 actions require product-level HS code lists not yet available and are excluded from the current model:

| Date | Authority | Reference | Description |
|------|-----------|-----------|-------------|
| Nov 1, 2025 | Section 232 | Proclamation 10984 | Trucks/buses: 25% trucks and parts, 10% buses |
| Jan 15, 2026 | Section 232 | Proclamation 11002 | Semiconductors: 25% on narrow set of advanced chips |
| — | Section 232 | Headings 9903.04.60–.66 | Patented pharmaceuticals |

These omissions now have a second-order effect. Every Phase 3 action exempts goods already subject to Section 232 — Section 301 via U.S. note 50(a)(vi), Section 338 via note 51(c) — so goods in these three unmodeled sectors receive the **full stacked rate when they should be exempt**, biasing the affected country's effective rate upward.

The Section 338 Canada baskets are barely touched by this. Note 51(c)(4) exempts only wood in the Section 232 **timber** headings (9903.76.01–.24) — softwood lumber, upholstered furniture and completed cabinets/vanities — and of the modeled timber codes only a single cabinet line (9403.60.8093, ~$0.30B of 2025 Canadian imports) falls inside a 338 basket. Now that the timber sector is modeled it is correctly carved out (its rate moves from the 338 basket's 50% down to the timber 232 rate of 25%). The **64 chapter-44 codes in the autos basket are hardwood, plywood, fiberboard and builders' joinery (4401, 4402, 4408–4421)**, which Proclamation 10976 does *not* cover — they are not Section 232 goods and are correctly dutiable at 50%. An earlier note here treated those 64 codes as a deferred 232 carve-out bias; that was a misdiagnosis, corrected Jul 23, 2026 when the timber sector was modeled and the softwood headings (4403/4406/4407) were shown to be disjoint from the basket.

### Modeling limitations

- **End-use conditional exemptions are applied flat.** The Brazil 301 civil-aircraft exemption is conditional on meeting HTSUS general note 6, and the pharmaceutical exemption applies only to pharmaceutical end uses. Neither is resolvable from HS10 import data, so both are applied to every listed code. This **over-exempts**, partially offsetting the upward bias described above.
- **In-transit relief is ignored.** Heading 9903.05.02 exempts goods loaded before Jul 22, 2026 and entered before Jul 29, 2026. Given Brazil–U.S. transit times, most goods entering that week are exempt in practice, so the modeled Jul 22 step overstates the rate for its first week. Consistent with prior actions carrying similar grace windows, none of which are modeled.
- **Annex II interaction.** Products removed from Section 232 scope by the Apr 6, 2026 metals Annex II are no longer provided for in the 9903.82 headings, so they do *not* qualify for the Section 232 carve-out in either Phase 3 authority. The model handles this explicitly (21 products, ~0.03% of U.S. imports from Brazil).
- **The auto-parts mask is coarse, and it now over-exempts.** `_mask_auto` matches part of the Proclamation 10908 list at HS6, including `853710`. Because Phase 3 carves out Section 232 goods, every good under HS8 8537.10.91 — industrial switchgear, panelboards and programmable controllers — is treated as an exempt auto part and escapes the Section 338 duty. That is **$1.6B of 2025 Canadian imports, and it removes 0.19 pp** from Canada's post-Aug 19 rate. Note 51(c)(3) exempts only parts *of passenger vehicles and light trucks*, so most of this value should be dutiable. The HS6 approximation predates the Section 338 work; it had little consequence while the auto list only ever *set* a rate, and became material once Phase 3 began reading it as an exemption.

---

## Update notes (2026-07-23)

- **Section 301 forced-labor action went LIVE** with its final Notice of Actions
  (Docket USTR–2026–0265/0266), effective Jul 24, 2026 — the day the Section 122
  surcharge lapses. Flipped `LABOR_301_LIVE = True`; the action now moves
  `country-by-time.csv` and `daily-tariff-latest-data.csv`. National import-weighted
  average steps **+0.50pp** on Jul 24 (10.89% → 11.39%). Rates repointed to
  [301-labor-economies-FINAL.csv](tariff-lists/301-labor-economies-FINAL.csv);
  vs the provisional, five economies dropped 12.5→10 (Honduras, India, Pakistan,
  Sri Lanka, Trinidad & Tobago) plus EU 12.5→10, and EU/Taiwan/Japan/Korea/Switzerland
  moved to a net-of-MFN cap modeled flat (MFN = 0).
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

## Update notes (2026-07-22)

- Added the **Section 301 forced-labor action** as a provisional, staged-off Phase-3
  layer (FR Doc 2026-11296 — a determination and proposed action, not yet a Notice of
  Action). Generated from [301-labor-economies.csv](tariff-lists/301-labor-economies.csv)
  (60 economies, 50 tracked, two tiers) with exemptions from
  [301-labor-exemptions.csv](tariff-lists/301-labor-exemptions.csv) (1,655 codes). Gated
  by `LABOR_301_LIVE` (default `False`); published output is unchanged. See the
  "Provisional / staged actions" section above.
- Established that the labor **Annex A is bit-for-bit identical to the combined Section
  122 exemption lists**, so the engine reuses them; the equality is asserted by the new
  guardrail.
- Extended `_make_stacked_apply` with two country-conditional carve-outs (`usmca_exempt`
  for CA/MX, `cafta_textile_exempt` for the six CAFTA-DR economies), both no-ops for the
  existing Brazil/Canada regimes.
- Added [validate-301-labor.py](validate-301-labor.py) — baseline guardrail plus a diff
  mode for reconciling against the Notice of Action when it issues.

## Update notes (2026-07-21)

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

