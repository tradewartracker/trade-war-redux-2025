# Methodology

How the tariff rates in this repository are built: the data and weights, how each legal
authority's tariffs stack on one another, how individual actions are modeled, and what the
model leaves out. For a short overview see the [README](README.md); for how to run the
code see [TECHNICAL-README.md](TECHNICAL-README.md).

**Contents**

1. [How the rate is computed](#1-how-the-rate-is-computed)
2. [Tariff actions and how they stack](#2-tariff-actions-and-how-they-stack)
3. [Actions not yet incorporated](#3-actions-not-yet-incorporated)
4. [Modeling limitations](#4-modeling-limitations)
5. [Open issues](#5-open-issues)

A note on names: three different documents have an "Annex II". Here they are always
qualified: the **reciprocal-tariff Annex II** (EO 14257's product exemptions, 2025), the
**metals Annex II** (products removed from Section 232 steel and aluminum scope, Apr 6,
2026), and **labor Annex II Part A** (the forced-labor action's product exemptions, 2026).

## 1. How the rate is computed

**Import data and weights.** For each trading partner, the model uses the Census Bureau's
international trade API for calendar-2024 imports for consumption (`CON_VAL_YR`) and
calculated duties (`CAL_DUT_YR`) at the 10-digit HTS level. These values are cached as
parquet files in [data](data). The 2024 import values are the weights throughout. They
are fixed: the basket does not change when trade shifts in response to tariffs.

**Trading partners.** The panel covers 50 partners: the 49 largest non-EU suppliers,
ranked by cumulative imports since 2013 in `make-country-list.ipynb`, plus the 27-member
European Union as one bloc (Census code 0003). Together they supplied $3.21 trillion of
2024 imports. Other countries are left out of the averages.

**Country rates.** For each partner and each policy date, every HS10 line starts at zero
added duty, and every tariff action in force on that date is applied in the order set out
in section 2. The country rate is the average of those line rates, weighted by 2024 import
shares. It is the tariff *increase* since January 2025 (the `effective tariff` column of
`country-by-time.csv`). The `2024 tariff` column holds the duty actually collected in
2024, calculated duties divided by imports.

**National rate.** The headline is the average of the country rates weighted by each
partner's 2024 imports, plus a flat 2.3% for the tariffs in place before 2025. The 2.3% is
a single number for all partners. It also covers the 2018–19 Section 301 duties on China,
which are part of the 2024 baseline rather than modeled as actions.

**Dates.** The engine evaluates the panel only on policy dates, the days an action takes
effect (`date_strings` in the main notebook; 27 dates as of Nov 25, 2026). The daily
series in `daily-tariff-latest-data.csv` carries each value forward to the next policy
date. It runs 60 days past the latest run, or 30 days past the last policy date if that is
later, so a future-dated step shows as a level rather than as a single last point.

**Future-dated rows.** Two of the policy dates are after the latest run, and their rows are
not law in force.

- **Jan 1, 2027 is scheduled.** The Section 232 rates on upholstered furniture and kitchen
  cabinets step up under Proclamation 10976, which is already in force. National average
  11.46% → 11.50%.
- **Feb 1, 2027 is assumed.** From that date the series includes the Section 301
  excess-capacity tariffs that USTR proposed on Nov 25, 2026. They are not in force, no
  notice proposes a date, and the rates are the proposed ceilings. National average
  11.50% → 14.39%. See the
  [proposed excess-capacity action](#proposed--section-301-structural-excess-capacity-in-the-series-from-an-assumed-date).

Otherwise, days after the run assume no further change. One later scheduled step, the
expiry of the metals Annex III rate on Jan 1, 2028, is registered in the code but not yet
added to the panel.

## 2. Tariff actions and how they stack

The notebook encodes U.S. tariff policy changes in a structured `TARIFF_ACTIONS` registry applied chronologically. Each action carries its effective date, legal authority, executive order/proclamation reference, and a short description. Actions are split into three phases: **Phase 1** resets country-level base rates (IEEPA / Section 122 layer); **Phase 2** stamps sector-specific tariffs and product exemptions on top; **Phase 3** applies stacked country actions (Section 301 and Section 338), which *add* to the rate already in place rather than replacing it, and carve out goods already subject to Section 232. A fourth phase, for caps on the all-in Section 301 rate, holds one action that is not in force: the proposed excess-capacity tariffs, which enter the panel from an assumed date. It is described under the [proposed excess-capacity action](#proposed--section-301-structural-excess-capacity-in-the-series-from-an-assumed-date).

### Phase 1 — Country-level base rates

| Date | Authority | Reference | Description |
|------|-----------|-----------|-------------|
| Feb 4, 2025 | IEEPA | EO 14193/14194/14195 | Fentanyl emergency: 20% on China and Hong Kong; Canada (EO 14193) and Mexico (EO 14194) also included but immediately paused |
| Mar 6, 2025 | IEEPA | Amendments to EO 14193/14194 | USMCA carve-out: Canada 8.75%, Mexico 4.5% |
| Apr 5, 2025 | IEEPA | EO 14257 | Reciprocal tariffs activate at the 10% global baseline (China/HK 30% with fentanyl). The Annex I country rates do not start until Apr 9 (s.3(a)) |
| Apr 9, 2025 | IEEPA | EO 14257 s.3(a), EO 14259 | Annex I country rates take effect, for one day; China/HK escalated to 84% reciprocal (+20% fentanyl = 104%) |
| Apr 10, 2025 | IEEPA | EO 14266 | 90-day pause: all countries reset to 10%; China/HK reciprocal raised to 125% (+20% fentanyl = 145%) |
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
| Apr 5, 2025 | IEEPA | EO 14257 s.3(b), Annex II | Annex II product exemptions from the reciprocal tariff: 1,039 HS8 subheadings, matched on HS8. Only the reciprocal duty is exempt, so China/HK still pay fentanyl and Brazil (from Aug 7) its 40%. Canada/Mexico are on hold: they keep the pre-correction list from Apr 11 (see [Open issues](#5-open-issues)) |
| Apr 11, 2025 | IEEPA | Amendment to EO 14257 | Consumer electronics (phones, laptops, etc.) exempt from reciprocal tariffs; China/HK still pay fentanyl |
| Jun 3, 2025 | Section 232 | Proclamation 10947 | Steel and aluminum tariffs raised to 50%; UK remains at 25% per bilateral deal |
| Aug 7, 2025 | Section 232 / IEEPA | Proclamation 10962, Proc 10908 amendments, EO 14323 Annex | Copper at 50%; auto deal rates for Japan, EU, South Korea at 15%; Brazil exemptions. Brazil's two duties keep separate lists: Annex II and electronics remove only the 10% reciprocal, EO 14323's Annex I removes only the 40% |
| Oct 14, 2025 | Section 232 | Proclamation 10976 | Timber/lumber: softwood 10% (all countries); upholstered wooden furniture and completed kitchen cabinets/vanities 25% (UK 10%, Japan 15%, EU 15%). Steps up Jan 1, 2027 — furniture 30%, cabinets 50% (a scheduled step; in the panel as a future-dated row since Nov 25, 2026). Autos take precedence per clause 6 |
| Nov 1, 2025 | IEEPA | EO 14357 | China/HK Annex II and electronics goods pay only the fentanyl duty, now 10% |
| Nov 14, 2025 | IEEPA | EO 14360, EO 14361 | Annex II widened to agricultural goods; China/HK keep the 10% fentanyl duty on them; Brazil's 40% lifted on the EO 14361 list (238 subheadings + 11 described articles, retroactive to Nov 13) |
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

An action that a later proclamation amends is split into dated versions. The existing entry gets an `end_date` (the last day it applies), and a new entry starts the next day with its own basket and carve-outs. Editing an entry in place would rewrite every earlier date in the panel.

| Date | Authority | Reference | Description |
|------|-----------|-----------|-------------|
| Jul 22, 2026 | Section 301 | USTR Notice of Action — Brazil (Jul 15, 2026) | 25% on all goods of Brazil; exemptions for 864 listed subheadings, 11 named articles, 546 civil-aircraft codes, 705 pharmaceutical-application codes, and all Section 232 sectors |
| Jul 24, 2026 | Section 301 | USTR Notice of Actions — forced labor (Docket USTR–2026–0265/0266, Jul 23 2026) | 12.5% (10% for 18 economies) on all goods of 50 tracked economies; Annex II Part A (unconditional + pharmaceutical codes) and all Section 232 sectors exempt. Effective the day the Section 122 surcharge lapses. See the forced-labor detail below. |
| Jul 31, 2026 | Section 301 | USTR Notice Annex I.B — U.S. note 50(a)(vi)(8) | Patented pharmaceuticals added to the Brazil 232 carve-out (no effect — sector not modeled) |
| Aug 22 – Sep 14, 2026 | Section 338 | Proclamation 11046 on Canadian alcoholic beverages (Jul 20, 2026), heading 9903.03.12; effective date amended by Proclamation 11056 | 50% on 63 enumerated Canadian codes (beverages, some wood and paper) |
| Aug 22, 2026 | Section 338 | Proclamation 11047 on Canadian dairy (Jul 20, 2026), heading 9903.03.13; effective date amended by Proclamation 11056 | 50% on 52 enumerated Canadian codes (milk products, sugars, caseins) |
| Aug 22 – Sep 14, 2026 | Section 338 | Proclamation 11048 on Canadian motor vehicles (Jul 20, 2026), heading 9903.03.14; effective date amended by Proclamation 11056 | 50% on 439 enumerated Canadian codes across 56 chapters |
| Aug 19–21, 2026 | Section 338 | Proclamation 11056 (Aug 18, 2026), FR Doc 2026‑17294 | 3‑day suspension of the three Canada actions during negotiations; Annex II chapeau of Procs 11046/11047/11048 amended from Aug 19 to Aug 22. Negotiations failed; duties took effect Aug 22 (no-op row — encoded as the regimes' effective date) |
| Sep 15, 2026 | Section 338 | Proclamation 11064 (Sep 8, 2026) modifying Proclamation 11046, heading 9903.03.12 | Alcohol basket −2 / +40 → 101 codes (cheese, hides, furskins, boats added; whisky and liqueurs over 4 liters leave). Now applies **in addition to** Section 232 |
| Sep 15 – Oct 29, 2026 | Section 338 | Proclamation 11065 (Sep 8, 2026) modifying Proclamation 11048, heading 9903.03.14 | Autos basket −8 / +82 → 513 codes (steel and aluminum structures, furniture, lamps, golf carts added; salt, cement, refined lead leave). Now applies **in addition to** Section 232 |
| Sep 29, 2026 | Section 338 | Proclamations 11061, 11062, 11063 (Sep 8, 2026) | Import bans on packaged beer, wine and spirits; whey, molasses and non-alcoholic beer; motorcycles over 800cc. Every banned code is already in a basket and is kept at the 50% basket rate (no-op row) |
| Oct 30, 2026 | Section 338 | Proclamation of Oct 23, 2026 further modifying Proclamation 11048, heading 9903.03.14 | Autos basket −22 / +100 → 591 codes (cocoa powder, paints, soaps, carpets, fiberboard, freezers, valves added; plywood, packaging and some machinery leave). Still in addition to Section 232 |

Because Section 122 runs through Jul 23 and the Brazil 301 action begins Jul 22, the two overlap for two days. All start and end dates are modeled literally, so Brazil shows a brief spike (≈17.5%) on Jul 22–23 before settling at ≈13.3%.

The three Section 338 actions (Proclamations 11046, 11047, 11048) were issued the same day against Canada, all at 50%, all originally effective Aug 19, 2026, and all sharing a single U.S. note 51. On Aug 18, Proclamation 11056 suspended them for three days while Canada negotiated on a "commitment to remove" the discriminations, moving the effective date to **Aug 22, 2026**; the talks failed and the duties took effect on that date. Nothing else in the three proclamations changed. Each retaliates for a distinct Canadian practice — provincial liquor-board bans, cheese TRQ allocation, and motor-vehicle tariffs and quotas — but the baskets deliberately target goods *other* than the offending sector, and are disjoint from one another. The civil-aircraft carve-out of note 51(d) (heading 9903.03.16, 554 codes) is enumerated once and shared by all three, so it is modeled as one exemption list referenced by three regimes. Neither the proclamations nor note 51 provide an in-transit grace window. Combined effect on Canada: **+1.85 pp** (5.82% → 7.66%), against +2.49 pp before carve-outs. (The 5.82%/7.66% levels sit ~0.18 pp above the pre-timber figures of 5.64%/7.49%, since the Section 232 timber action lifts Canada's whole curve from Oct 14 2025; the *step* is essentially unchanged.)

**Amendments.** Two later rounds changed the alcohol and autos baskets. Dairy was never amended.

- **Sep 15, 2026 (Procs 11064 and 11065, signed Sep 8).** Both baskets were reshuffled, and note 51(c) was rewritten so that its Section 232 exemption names only the dairy heading (9903.03.13). From Sep 15 the alcohol and autos duties apply *in addition to* Section 232.
- **Sep 29, 2026 (Procs 11061–11063, signed Sep 8).** Some basket goods were banned from importation. The model keeps them at 50%: every banned code is already in a basket, and 50% is the rate that applies if a ban is struck down.
- **Oct 30, 2026 (Proclamation of Oct 23, 2026; Federal Register number pending).** The autos basket changed again.

Each amended basket is a dated version that `extract-338-annex.py` builds from the amending Annex II.

Effect on Canada: **+0.28 pp** on Sep 15 (7.66% → 7.94%) and **+0.02 pp** on Oct 30 (→ 7.97%). The national average goes 11.43% → 11.46% → 11.46%. The Sep 15 step breaks down as:
- +0.20 pp from steel and aluminum structures (7308.90, 7604, 7608), new to the autos basket and now paying on top of Section 232;
- +0.11 pp from goods the model treats as auto parts — mainly HS8 8537.10.91 switchgear (see the modeling limitations) — which the autos basket no longer exempts;
- −0.03 pp from the reshuffle of other goods.

The Oct 30 change is close to a swap. Tariffs fall from 50% to 0% on about $2.3B of 2024 Canadian imports, mostly packaging (plastic sacks, crates, corrugated cartons) and packing machinery. They rise from 0% to 50% on $2.5B, mostly chemicals and consumer products (lab reagents, detergents, shampoo, caulk, paints), surgical instruments, valves and paper. The carpets and cocoa powder the announcement led with barely register: carpets add $8M, and the cocoa-powder lines carried no 2024 imports.

#### Section 301 forced-labor action — detail

Effective **Jul 24, 2026** (Docket USTR–2026–0265/0266, issued Jul 23 2026), the day the Section 122 surcharge lapses. USTR determined that 60 investigated economies failed to impose and/or effectively enforce a forced-labor import prohibition, and imposes additional duties on all their goods with exemptions. 50 of the 60 economies are in the panel's country universe (32 at 12.5%, 18 at 10%).

Modeled as Phase-3 stacked Section 301 regimes generated from [301-labor-economies-FINAL.csv](tariff-lists/301-labor-economies-FINAL.csv), one per tracked economy, `scope="all"`, carving out Section 232 goods per U.S. note 50(a)(vi) — identical mechanics to the Brazil 301 action, gated live by `LABOR_301_LIVE = True`. Aggregate effect: the national import-weighted average rises **+0.33 pp** on Jul 24 (10.86% → 11.19%) as the 10% Section 122 surcharge is replaced by the labor duty — the labor action slightly more than replaces the surcharge.

**Rate tiers.**

- **10%** on 18 tracked economies (imposed a prohibition or made ART/commitments): Argentina, Bangladesh, Cambodia, Canada, Ecuador, El Salvador, EU, Guatemala, Honduras, India, Indonesia, Malaysia, Mexico, Pakistan, Sri Lanka, Taiwan, Trinidad & Tobago, United Kingdom.
- **12.5%** on the remaining 32 tracked economies.
- **Net-of-MFN cap.** For the EU and Taiwan (10% cap) and Japan, Korea and Switzerland (12.5% cap), the notice sets the 301 rate *net of a product's column-1 MFN* — "the sum of the MFN tariff and the section 301 tariff" equals the cap, and the 301 is zero where MFN ≥ the cap. The model implements this as `301 = max(0, cap − MFN)` per HS10, using the statutory column-1 rate in [mfn-per-code.csv](tariff-lists/mfn-per-code.csv) (HTS statutory where the rate is a clean ad valorem, pooled 2024 customs AVE as a fallback for specific/compound duties; built in [mfn-per-code-comparison.ipynb](code/mfn-per-code-comparison.ipynb)). Applied to the four **non-FTA** economies (EU, Taiwan, Japan, Switzerland). **Korea is deliberately left on the flat cap:** the HTS headings set both the general and special column-1 rate to the flat cap (9903.05.71 = "12.5% / 12.5%"), so a KORUS claim is overridden to the flat rate, and against Korea's ~0 FTA-preferenced 2024 baseline the full cap *is* the added tariff — netting would understate it. A small residual **upward** bias remains only on codes absent from the MFN table (treated as MFN = 0 = full cap).

**Exemptions.** Come from **Annex II Part A** ("Goods of Any Investigated Economy"), the base list applying to every economy, extracted to [301-labor-part-a.csv](tariff-lists/301-labor-part-a.csv) (2,113 codes) directly from the notice's machine-readable tables. Scope flags: `''` unconditional (856), `pharma` (700), `aircraft` (541), `ex` (16).

- **Pharma codes exempted flat; aircraft and Ex taxed (modeling choice "C").** The `pharma` codes (pharmaceutical-application conditional; 82% chapter-29 organic chemicals) are exempted — matching the Section 122 model, which already exempts 363 of these same codes as unconditional products, and following the standing flat-exemption convention for end-use carve-outs. The `aircraft` (civil-aircraft GN 6, conditional) and `ex` codes are **not** exempted, exactly as `_mask_s122_exempt` ignores the Section 122 aircraft exemption, keeping the labor duty and the surcharge on the same exemption basis. Both choices are flat because the end-use split is not resolvable from HS10 data: exempting pharma **over-exempts** its non-pharma use (a modest downward bias, smallest for the pharma-heavy exporters — EU, Switzerland, India — it mainly touches), and taxing aircraft **over-taxes** the civil-aircraft slice (small, since these are general industrial goods across 18 chapters where aircraft use is a minority).
- **Country-specific exemptions (Annex II Parts B–N) and the CAFTA/Jordan textile Part O are not modeled** — a documented limitation to revisit. They add narrower carve-outs for the 13 ART/commitment economies; omitting them is a small **upward** bias, quantified (2024 weights) at **~0.03pp nationally**. It is negligible for all but two economies: **Indonesia +0.92pp** (Part L exempts palm oil and palm oleochemicals — HS 1511.90, 1513.29, 3823.19/70) and **Ecuador +0.78pp** (Part M exempts fresh cut flowers — HS 0603.11/19); every other economy is < 0.35pp, most < 0.1pp. The giant Part O textile list (1,736 codes) is essentially redundant with the flat CAFTA-DR chapter 50–63 exemption below — it adds only +0.13pp (El Salvador) / +0.07pp (Guatemala). The extracted code lists are preserved in [301-labor-parts-BO.csv](tariff-lists/301-labor-parts-BO.csv) for a future revisit; modeling Parts L and M alone would remove nearly all the bias.
- **USMCA-compliant Canada/Mexico goods are exempt** (Annex I general notes ¶g/¶h). The model treats all Canada and Mexico imports as USMCA-eligible (same simplification as the Section 122 base), so the action nets to **~0% on both**. Flagged for revisit — real USMCA compliance is below 100%.
- **CAFTA-DR duty-free textiles/apparel** (Costa Rica, Dominican Republic, El Salvador, Guatemala, Honduras, Nicaragua; Annex I ¶i, GN 29(d)(v)) are exempt. Applied as a flat exemption of HTSUS chapters 50–63 for those six economies, which **over-exempts** — it also frees textile trade that entered under MFN or another program.
- The **textile mechanism** (three-year TRQs for Bangladesh, Cambodia, Indonesia and Malaysia tied to their U.S. cotton/textile imports; 10% applies until established) is not modeled — a volume-based allowance not resolvable from HS10 data. The FTZ "privileged foreign status" requirement and text-only exclusions (informational materials, donations, accompanied baggage) are likewise unmodeled and negligible.

The provisional Jun 5, 2026 files — [301-labor-economies.csv](tariff-lists/301-labor-economies.csv) and the 1,655-code [301-labor-exemptions.csv](tariff-lists/301-labor-exemptions.csv) — are retained as the archived baseline for `validate-301-labor.py` and the provisional-vs-final comparison. Running `validate-301-labor.py --diff-economies tariff-lists/301-labor-economies-FINAL.csv --diff-exemptions tariff-lists/301-labor-part-a.csv` reports the delta the final action introduced.

### Announced, not enacted — U.S.-China "30-for-30" list (staged off)

On Sep 27, 2026 the White House released the working procedures of a U.S.-China **Board of
Trade** and the terms of reference of its **"30-for-30" framework**
([US-China-Board-of-Trade-Working-Procedures.pdf](tariff-lists/sources/US-China-Board-of-Trade-Working-Procedures.pdf),
[Terms-of-Reference-for-30-for-30-Framework.pdf](tariff-lists/sources/Terms-of-Reference-for-30-for-30-Framework.pdf)):
the two sides approved comparably valued lists of goods, roughly $30B each at calendar-2024
trade values, "with a view toward providing reduced tariff treatment to those goods in a
reciprocal manner." The U.S. import list
([china-USimports-Public-List.pdf](tariff-lists/sources/china-USimports-Public-List.pdf)) names
**77 HTS8 codes** of Chinese consumer goods — toys ($13.5B alone), plastic tableware, small
kitchen appliances, home textiles, juvenile furniture and car seats, sporting goods,
Christmas articles, fishing tackle, vacuum flasks (chapters 36, 39, 63, 66, 67, 84, 85, 94,
95, 96).

**This is a framework, not a tariff action.** The terms of reference say future tariff
reductions "will be determined and implemented in accordance with each side's domestic legal
processes": there is no rate, effective date, legal authority, chapter 99 heading or Federal
Register notice. Nothing is in force, so nothing enters the published series. The list is
extracted, validated and wired as a **staged-off** Phase-3 regime (`CHINA_30FOR30_LIVE =
False`, placeholder date) so going live is a flag flip when the implementing notice lands.

- **Extraction.** [china-30for30-us-import-list.csv](tariff-lists/china-30for30-us-import-list.csv)
  is the list as printed. Eight rows carry an "Ex-Out" limiting the line to its description.
  Seven are juvenile furniture (highchairs/boosters, infant walkers, bouncers, swings, child
  safety seats, play yards) whose HTS10 statistical suffixes isolate exactly those products,
  so, unlike the aircraft and pharma carve-outs, they are resolved rather than applied flat:
  [china-30for30-model-list.csv](tariff-lists/china-30for30-model-list.csv) swaps the seven
  HS8 lines for 13 HTS10 lines. Resolving them moves the 2024 value covered from $32.5B
  (flat HS8) to **$29.6B**, which is what lands on "roughly $30 billion." The eighth ex-out,
  9503.00.00 toys excluding items "enabled with radio frequency, Wi-Fi, Ethernet, or
  Bluetooth", is not resolvable at HTS10 and is applied flat (a small over-inclusion when live).
- **What the list carries today.** Every listed code carries exactly one modeled duty for
  China: the 12.5% forced-labor Section 301 (Jul 24, 2026). None is in a modeled Section 232
  sector (9401.71/.79 left steel/aluminum derivative scope on Apr 6, 2026) and none is an
  active labor Part A exemption. The legacy 2018-19 China 301 lists barely touch the basket:
  toys were List 4B, never imposed, and only ~$2.7B carries List 3/4A duties, which in any
  case sit in the 2024 baseline, not the engine. IEEPA and Section 122 are gone and MFN cuts
  need Congress, so a meaningful reduction almost has to arrive as a **USTR Section 301
  modification** excluding the list from the labor action.
- **Staged model.** A dated *reversal* of the labor duty on the listed codes: a Phase-3
  `scope="listed"` regime for China with a **negative rate** (−12.5) that mirrors the labor
  regime's own carve-outs (232, Part A), so it undoes exactly the labor duty and the list
  returns to its 2024 tariff level. `_make_stacked_apply` now floors the result at zero, a
  no-op for every positive regime. A dated regime, rather than adding the list to the China
  labor regime's exemptions, keeps the Jul 24 → go-live rows correct. Hong Kong is not
  covered (the list is of "Chinese products"; HK exposure ~$0.09B).
- **Size if enacted as a full exclusion** (2024 weights): China **11.94% → 11.07% (−0.86pp)**,
  national **−0.12pp**. A partial reduction scales linearly; a companion cut to the legacy
  301 lists would add only −0.04pp to China. Detail in
  [china-30for30-analysis.ipynb](code/analysis/china-30for30-analysis.ipynb).
- **China's list of U.S. goods** (the other half of the framework) is not modeled, since it
  is a Chinese tariff; [extract-china-30for30-exports.py](code/extract-china-30for30-exports.py)
  extracts it. On U.S. export statistics it covers **$25.0B** of 2024 exports to China
  (17.5%), against the stated ~$30B. The gap is CIF/origin-based Chinese import statistics
  vs FAS U.S. export statistics, not the HS6 match, which can only overstate. Notably
  absent: commercial soybeans (only seed soybeans 1201.10 are listed), crude oil, LPG, LNG,
  civil aircraft, semiconductors and passenger cars — the eight biggest U.S. exports to
  China in 2024 are all off it.
- **Go-live checklist.** Confirm the mechanism (labor exclusion, legacy-301 modification, or
  both), the rate (zero or partial), the effective date and Hong Kong; diff the notice's code
  list against the saved CSV; check whether the ex-outs are by description or new statistical
  suffixes; then set `CHINA_30FOR30_EFFECTIVE_DATE`, flip `CHINA_30FOR30_LIVE`, add the date
  to `date_strings`, re-run the main notebook, refresh the downstream TRI-tracker.

### Proposed — Section 301 structural excess capacity (in the series from an assumed date)

On Mar 11, 2026 USTR self-initiated 16 Section 301(b) investigations of "structural excess
capacity and production in manufacturing sectors" (Dockets USTR–2026–0067/0068). On
**Nov 25, 2026** it made determinations and **proposed** actions in 14 of them: China, the
European Union, Japan, Korea, Switzerland, Taiwan, Bangladesh, Cambodia, Indonesia,
Malaysia, Thailand, India, Singapore and Vietnam. It made no determination for Mexico or
Norway. The 14 economies are all in the panel and supplied $1,921B of 2024 imports, 59.9%
of the panel.

**These are proposals, not actions.** Each notice proposes "to consider applying" a tariff
"up to" a rate. None has an effective date or a chapter 99 heading. Comments and requests
to appear are due Jan 5, 2027, and the hearing is Jan 25, 2027. Nothing is in force. The
sources are the 14 pre-publication notices in
[tariff-lists/sources](tariff-lists/sources) (`301-secp-proposed-*.pdf`).

**In the series from an assumed date.** Since Nov 25, 2026 the published series includes
the proposals at the rates as written from **Feb 1, 2027**, so that it shows where rates
are headed (`SECP_301_LIVE = True`). The date is an assumption: it is the first of the
month after the hearing, and no notice proposes one. Rows from Feb 1, 2027 on are
therefore a projection, not law. Every row before that date is unchanged. Before Nov 25,
2026 the tracker's rule was to keep announced and proposed actions out of the series
until an implementing notice was published; the U.S.-China 30-for-30 list above still
follows that rule.

**Proposed rates.** Every rate is on all goods of the economy, "net of existing Section 301
tariffs", so the forced-labor duty already in place counts toward it. The table is
[301-secp-economies.csv](tariff-lists/301-secp-economies.csv).

| Economy | Labor 301 now | Proposed | Other rate in the notice |
|---|---|---|---|
| EU | 10, incl. MFN | 15, incl. MFN | 20 if consultations fail |
| Japan, Switzerland | 12.5, incl. MFN | 15, incl. MFN | 20 if consultations fail |
| Korea | 12.5 | 15, incl. MFN | 25 if consultations fail |
| Taiwan | 10, incl. MFN | 15, incl. MFN | 25 if consultations fail, MFN not netted |
| Bangladesh | 10 | 18 | 20 if consultations fail |
| Cambodia, Indonesia, Malaysia | 10 | 18 | 25 if consultations fail |
| Thailand | 12.5 | 18 | 25 if consultations fail |
| India | 10 | 25 | 17 with a responsive agreement |
| Singapore | 12.5 | 20 | 10 with a responsive agreement |
| Vietnam | 12.5 | 35 | 20 with a responsive agreement |
| China | 12.5 | 20; Annex A goods 10; Annex B exempt | 40 on all goods |

The last column runs in two directions. Eleven notices, China's included, say the proposed
rate "accounts for" the commitments in an existing deal or framework, and name the higher
rate USTR would consider if it finds those commitments or the ongoing consultations
"unsatisfactory". India, Singapore and Vietnam are the reverse: the proposed rate is the
rate without a deal, and the notice names the lower rate USTR would consider if the economy
concludes an Agreement on Reciprocal Trade "responsive to the determinations in this
investigation". Vietnam's 20 is the rate in its Oct 26, 2025 framework. Singapore's 10 is
below its 12.5 labor duty, so the top-up would be zero.

**Phase 4: a cap, not an add-on.** "Net of existing Section 301 tariffs" means the new duty
tops a product up to the stated rate. On each HS10 line it is

    max(0, cap − MFN (where the notice nets it) − Section 301 duty already on the line)

so the action pins the all-in rate. If the labor duty on a line later changes or ends, the
top-up moves the other way and no rate has to be re-derived. The engine runs these caps in
a separate last phase, for two reasons. A top-up depends on everything stacked before it,
so inside Phase 3 it would depend on list position; a separate phase leaves Phase 3
additive and order-free. And the cap nets against a running `s301` column, the Section 301
duty Phase 3 has put on each line, rather than against the tariff column, which also holds
base rates, Section 232 and Section 338 duties.

**Exemptions.**

- **Section 232 goods** are exempt in 13 notices, which name steel, aluminum, copper,
  passenger vehicles and parts, medium and heavy vehicles and parts, wood products,
  patented pharmaceuticals and semiconductors. **China's notice does not mention
  Section 232.** Read as written, its duty reaches Chinese Section 232 goods, on top of
  their Section 232 rate. The model follows the text (`SECP_CHINA_EXEMPT_232 =
  False`); the carve-out is a one-argument variant.
- **The annex.** Every notice carries the same 2,121-code list, in the format of the labor
  notice (HTSUS, description, scope limitation). It is the 2,113 codes of labor Annex II
  Part A, with identical scope flags, plus 8: agglomerated iron ore (2601.12.00) and seven
  10-digit lines (seeds for sowing, one nonconiferous wood line, sintered neodymium
  magnets). Scope flags follow the labor convention: unconditional and pharmaceutical codes
  are applied flat, aircraft and "Ex" codes are not applied.
- **Country-specific Part II.** Seven notices add a second part: EU 45 codes, Switzerland
  134, Taiwan 118, Bangladesh 87, Cambodia 157, Indonesia 148, Malaysia 104. These track,
  but do not equal, each economy's country part of the labor notice. They are modeled for
  this action. Only Indonesia's matters: it covers 9.2% of Indonesian imports, mostly palm
  oil, and ignoring it would overstate Indonesia's step by 0.74 points. The labor duty's
  own country parts remain unmodeled, so those goods escape the new duty but still pay the
  labor duty in the model.
- **China's annexes are different.** Annex A is the common list, but its goods are not
  exempt: they pay up to 10%. Since the labor duty exempts them, this is a new 10% on goods
  that pay no Section 301 duty today (26.8% of Chinese imports). Annex B, the exemption, is
  exactly the 77-code 30-for-30 U.S. import list, with the same eight "Ex" rows; the engine
  reuses its form of that list, with the juvenile-furniture ex-outs resolved to HTS10. Hong
  Kong is not covered.

All of it is in [301-secp-annex.csv](tariff-lists/301-secp-annex.csv), every annex row as
printed, built by [extract-301-secp.py](code/extract-301-secp.py) and guarded by
[validate-301-secp.py](code/validate-301-secp.py).

**Modeling choices.**

- **The date is assumed.** Feb 1, 2027 is one setting in the engine
  (`SECP_301_EFFECTIVE_DATE`), and the same setting supplies the panel date. An effective
  date entered in an economy's CSV row overrides it. If USTR has not acted as the date
  approaches, the setting has to be moved before the date arrives; otherwise the series
  would show a duty in force that is not.
- **The rate in the series is the proposed rate as written**, including India 25,
  Singapore 20 and Vietnam 35. The agreement and alternative rates are columns of the same
  CSV and are run as scenarios.
- **Netting against MFN follows the labor duty.** The EU, Japan, Switzerland and Taiwan are
  netted per HS10 against the statutory column-1 rate. **Korea is modeled flat**, although
  its notice says "net of MFN", for the reason given under the labor action; one setting
  (`NET_OF_MFN_CTY`) drives both duties, so the two halves of one all-in rate cannot
  diverge. Netting Korea's top-up would lower its step from +0.61 to +0.38 points.
- **The China 30-for-30 staging is separate.** The notice uses the list as an exemption
  from the new duty. It does not reduce the labor duty, which is what the staged
  `CHINA_30FOR30` regime models. Both can be live at once.
- **The EU termination clause is not acted on.** The EU notice proposes that "this
  adjustment terminate on December 1, 2028". Whether that ends the duty or only the
  deal-based 15% rate is not clear from the text. It is recorded in the CSV
  (`adjustment_terminates`) and left out of the engine.

**Size as written** (2024 weights). In the published series the step lands on Feb 1, 2027,
after the Jan 1 timber increase, and takes the national average from **11.50% to 14.39%
(+2.89 points)**. The scenarios below are evaluated at Oct 30, 2026 rates, before the
timber increase, where the same step is **11.46% → 14.36%**, almost exactly the last level
under the IEEPA tariffs (14.28% on Feb 7, 2026).

| Scenario | National average | Step |
|---|---|---|
| Proposed, as written | 14.36% | +2.89 |
| India 17, Singapore 10, Vietnam 20 (agreements) | 13.83% | +2.37 |
| Every stated alternative (China 40 on all goods) | 18.39% | +6.92 |
| Proposed, with China's Section 232 goods carved out | 13.85% | +2.39 |

Steps by economy, as written: Vietnam +12.5, China +10.0, India +8.1, Bangladesh +8.0,
Cambodia +7.1, Indonesia +5.6, Malaysia +3.7, Singapore +2.9, Thailand +2.6, EU +2.2,
Taiwan +1.2, Switzerland +0.9, Japan +0.9, Korea +0.6. China contributes 1.34 of the 2.89
points, Vietnam 0.55 and the EU 0.41. Detail, figures and sensitivities are in
[section301-secp-overview.ipynb](code/analysis/section301-secp-overview.ipynb).

**Until the final notices publish.** Revisit the assumed date after the Jan 25, 2027
hearing. If no final action is in sight, move `SECP_301_EFFECTIVE_DATE` later and re-run
the main notebook before Feb 1, 2027 arrives. Because the date is still in the future,
moving it changes no row that describes law in force.

**When the final notices publish.**

1. Save the final notices and re-run `extract-301-secp.py` on them (`--prefix`,
   `--suffix -FINAL`).
2. Diff them against the proposal: `validate-301-secp.py --diff-economies … --diff-annex …`.
3. Put each economy's effective date, and any end date, in its CSV row; these override the
   assumed date. A later change for one economy is a new row, not new code.
4. Settle, from the chapter 99 headings: China's Section 232 treatment, Korea's netting,
   the EU termination, and whether Mexico or Norway has been added.
5. Put the real date or dates in `date_strings` in place of the assumed one, re-run the
   main notebook, and check that every row before the first changed date is identical.
   Then refresh the downstream TRI-tracker.

## 3. Actions not yet incorporated

The following Section 232 actions require product-level HS code lists not yet available and are excluded from the current model:

| Date | Authority | Reference | Description |
|------|-----------|-----------|-------------|
| Nov 1, 2025 | Section 232 | Proclamation 10984 | Trucks/buses: 25% trucks and parts, 10% buses |
| Jan 15, 2026 | Section 232 | Proclamation 11002 | Semiconductors: 25% on narrow set of advanced chips |
| — | Section 232 | Headings 9903.04.60–.66 | Patented pharmaceuticals |

These omissions now have a second-order effect. Every Phase 3 action exempts goods already subject to Section 232 — Section 301 via U.S. note 50(a)(vi), Section 338 via note 51(c) — so goods in these three unmodeled sectors receive the **full stacked rate when they should be exempt**, biasing the affected country's effective rate upward.

The Section 338 Canada baskets are barely touched by this, and from Sep 15, 2026 only the dairy basket still carves out Section 232 goods, so for alcohol and autos it applies only through Sep 14. Note 51(c)(4) exempts only wood in the Section 232 **timber** headings (9903.76.01–.24) — softwood lumber, upholstered furniture and completed cabinets/vanities — and of the modeled timber codes only a single cabinet line (9403.60.8093, ~$0.30B of 2025 Canadian imports) falls inside a 338 basket. Now that the timber sector is modeled it is correctly carved out through Sep 14, 2026 (its rate moves from the 338 basket's 50% down to the timber 232 rate of 25%). It sits in the autos basket, so from Sep 15 it pays both. The **64 chapter-44 codes in the autos basket are hardwood, plywood, fiberboard and builders' joinery (4401, 4402, 4408–4421)**, which Proclamation 10976 does *not* cover — they are not Section 232 goods and are correctly dutiable at 50%. The softwood headings that the timber action does cover (4403, 4406, 4407) are disjoint from the basket.

## 4. Modeling limitations

- **End-use conditional exemptions are applied flat.** The Brazil 301 civil-aircraft exemption is conditional on meeting HTSUS general note 6, and the pharmaceutical exemption applies only to pharmaceutical end uses. Neither is resolvable from HS10 import data, so both are applied to every listed code. This **over-exempts**, partially offsetting the upward bias described above.
- **In-transit relief is ignored.** Heading 9903.05.02 exempts goods loaded before Jul 22, 2026 and entered before Jul 29, 2026. Given Brazil–U.S. transit times, most goods entering that week are exempt in practice, so the modeled Jul 22 step overstates the rate for its first week. Consistent with prior actions carrying similar grace windows, none of which are modeled.
- **Metals Annex II interaction.** Products removed from Section 232 scope by the Apr 6, 2026 metals Annex II are no longer provided for in the 9903.82 headings, so they do *not* qualify for the Section 232 carve-out in either Phase 3 authority. The model handles this explicitly (21 products, ~0.03% of U.S. imports from Brazil).
- **The auto-parts list is applied flat by HS code.** The Proclamation 10908 parts list (HTSUS chapter 99, U.S. note 33(g)) names 130 provisions, some at six or four digits, such as 8537.10 (control boards) and 8507.60 (lithium-ion batteries). The 232 duty reaches only the goods in those provisions that are *parts of passenger vehicles and light trucks*; note 33(h) sends everything else, along with USMCA-qualifying parts, to heading 9903.94.06. Whether a good is a car part cannot be resolved from HS10 data, so `_mask_auto` applies the list to every good in a listed provision, the same convention as the end-use exemptions above. `auto-tariffs.csv` matches the list's own granularity — checked Oct 26, 2026 against the Apr 2025 annex and HTSUS 2026 Revision 21 — so the mask is not coarser than the law. The flat rule cuts both ways:
  - It charges the auto-parts rate on non-automotive goods in listed provisions. The largest are lithium-ion batteries (8507.60, $22B of 2024 imports from the partners the model tracks) and control boards (8537.10, $18B).
  - It carves the same goods out of any Phase 3 action that exempts Section 232 goods. In the Section 338 autos basket this exempts all of HS8 8537.10.91 — industrial switchgear, panelboards and programmable controllers, **$1.6B of 2024 Canadian imports, 0.19 pp** of Canada's rate from Aug 22 to Sep 14, 2026 — although note 51(c)(3) exempts only parts of passenger vehicles and light trucks. This only became material once Phase 3 began reading the list as an exemption; before that it only ever *set* a rate. From Sep 15 the autos basket applies on top of Section 232, so these goods pay the 338 duty as well.

## 5. Open issues

The Oct 26, 2026 check of `auto-tariffs.csv` against Proclamation 10908 (the Apr 2025 annex and HTSUS 2026 Revision 21, U.S. note 33) found three problems that are not yet corrected. Fixing any of them changes the published series back to 2025.

1. **Canada and Mexico auto parts are charged 15%.** Note 33(h)(i) sends USMCA-qualifying parts to heading 9903.94.06, which carries no Section 232 duty, and elsewhere the model treats all Canadian and Mexican imports as USMCA-qualifying. The 15% on parts adds about **0.68 pp** to Canada's rate and **2.12 pp** to Mexico's (2024 weights).
2. **Three codes in `auto-tariffs.csv` are mistyped.** `86122020`, `86122040` and `882721` should be 8512.20.20 and 8512.20.40 (vehicle lighting) and 8527.21 (car radios). The typos match no goods, so about **$7.6B** of 2024 imports, mostly from Mexico, never takes the auto-parts rate.
3. **Parts take effect a month early.** The parts duty began May 3, 2025 (CBP CSMS 64913145), but `_apply_auto_initial` applies the whole list, vehicles and parts, from Apr 3, 2025. This affects the five panel dates from Apr 3 to Apr 11, 2025.

The Oct 27, 2026 correction of the reciprocal-tariff Annex II left three items open. Fixing any of them also changes the published series back to 2025.

1. **Canada and Mexico Annex II goods are on hold.** Annex II exempts goods only from the reciprocal tariff, which never applied to Canada or Mexico (EO 14257 s.3(d)–(e)). Under the model's USMCA-adjusted rates their Annex II goods would pay the same rate as their other goods, not 0%. Until that is decided they keep the pre-correction treatment, [annex-II-exemptions-legacy.csv](tariff-lists/annex-II-exemptions-legacy.csv) matched on HS10 from Apr 11 (`_apply_annex_ii_camx_legacy`), so their published rates do not move. Applying the USMCA-adjusted rate to those goods raises Canada by about 1.9 pp in May 2025 and 6.2 pp from Nov 14, 2025, mostly on energy. Non-USMCA Canadian energy and potash paid 10% under the fentanyl order rather than the full rate, so the natural refinement is 0.35 × 10% for those goods.
2. **The electronics exemption starts on Apr 11, but it applied from Apr 5.** CBP applied the Apr 11 memorandum to entries from Apr 5, with refunds by post-summary correction. The model taxes those goods on the Apr 5 and Apr 9–10 panel dates.
3. **The Geneva reduction takes effect May 12 in the model, but by law on May 14** (EO 14298). The model drops China from 145% to 30% two days early.

The Nov 25, 2026 work on the proposed excess-capacity action found one problem in the forced-labor list. Fixing it changes the published series from Jul 24, 2026.

1. **Seven 10-digit lines are missing from the labor exemption list.** Annex II Part A of the final forced-labor notice lists seven statistical lines printed as, for example, `8505.11.0070`: sweet corn, flax, rape (two lines) and sunflower seeds for sowing, one nonconiferous wood line (4407.99.0295) and sintered neodymium-iron-boron magnets (8505.11.0070). [301-labor-part-a.csv](tariff-lists/301-labor-part-a.csv) holds only the 2,113 eight-digit codes, so the model charges these goods the labor duty. They are $0.30B of 2024 panel imports, mostly magnets, or about 0.001 points on the national average. The excess-capacity annex lists the same seven lines and its CSV includes them; `validate-301-secp.py` pins the difference.
