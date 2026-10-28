# Tracking U.S. Tariffs, 2025–2026

This repository measures the average U.S. tariff rate, day by day and for each major
trading partner, from the first new tariffs of February 2025 to today. It produces the
statutory tariff series in the [Trade War Tracker](https://www.tradewartracker.com).

How the numbers are built is in [METHODOLOGY.md](METHODOLOGY.md). How to run and extend the
code is in [TECHNICAL-README.md](TECHNICAL-README.md). Every change to the data is logged in
[CHANGELOG.md](CHANGELOG.md).

> **Citation:** If you use or quote this data, please cite as:
>
> Waugh, Michael E. "Tracking U.S. Tariffs, 2025–2026." https://github.com/tradewartracker/trade-war-redux-2025

![U.S. average tariff rate, 2025–2026](figures/tariff-fig.png)

**Updated Oct 28, 2026.** The average U.S. tariff rate is **11.5%**, up from 2.3% before
2025. It peaked at 28.3% on Apr 9, 2025.

> [!NOTE]
> **Recent revisions.** On Oct 28, 2026 Slovakia, which had been counted twice, was
> removed as a separate partner; the national average moves by at most 0.04 points. On
> Oct 27, 2026 the product exemptions from the 2025 reciprocal tariffs were corrected,
> lowering the national average by about 1–2 points for most of Apr 2025 – Feb 2026. All
> revisions to past values are listed at the top of the [changelog](CHANGELOG.md).

---

**Contents**

1. [What the number measures](#1-what-the-number-measures)
2. [What happened](#2-what-happened)
3. [Key modeling choices](#3-key-modeling-choices)
4. [The data](#4-the-data)
5. [What's in the repository](#5-whats-in-the-repository)
6. [Known issues](#6-known-issues)

---

## 1. What the number measures

The headline is the average tariff on U.S. imports implied by the tariffs legally in force
on a given day. It is built up from individual products:

1. Each tariff action is coded from its legal text: which countries, which products (by
   10-digit tariff code), what rate, and from what date.
2. For each of 50 trading partners, the rates on its products are averaged using each
   product's 2024 import value as the weight. The partners are the 49 largest non-EU
   suppliers plus the European Union, counted as one. Together they supplied $3.2 trillion
   of 2024 imports.
3. The partner rates are averaged using each partner's 2024 imports, and the 2.3% average
   tariff in place before 2025 is added.

Three things follow from this design.

- **It is a statutory rate.** It measures what the law says is owed, not what customs
  collects. Collected duties differ because importers change suppliers, claim exemptions
  and pay with a lag. The tracker's other measures use customs data to capture that.
- **The import basket is fixed at 2024.** When buyers move away from heavily tariffed
  goods, this measure does not follow them, so it tends to run above the duties actually
  collected. In exchange, every move in the series is a change in policy.
- **It changes only on the days a policy takes effect** and is flat in between.

## 2. What happened

| Date | What happened | Average tariff |
|---|---|---:|
| Before 2025 | Ordinary tariffs only | 2.3% |
| Feb 4, 2025 | Fentanyl tariffs on China (Canada and Mexico paused) | 5.0% |
| Mar 2025 | Fentanyl tariffs on Canada and Mexico, sparing USMCA goods; steel and aluminum 25% | 7.5% |
| Apr 3, 2025 | Autos and auto parts 25% | 9.7% |
| Apr 5, 2025 | Reciprocal tariffs begin at a 10% baseline | 14.5% |
| Apr 9, 2025 | Full country rates, for one day; China 104% | **28.3%** |
| Apr 10–11, 2025 | 90-day pause at 10%, with China raised to 145%; electronics exempted | 22.8% |
| May 12, 2025 | Geneva deal cuts China to 30% | 13.2% |
| Jun 3, 2025 | Steel and aluminum raised to 50% | 14.2% |
| Aug 7, 2025 | New country rates and trade deals; Brazil +40%; copper 50% | 17.1% |
| Nov 2025 | China truce; Swiss deal; farm goods exempted | 14.8% |
| Feb 20, 2026 | Supreme Court ends the IEEPA tariffs | 6.2% |
| Feb 24, 2026 | 10% Section 122 surcharge for 150 days | 9.9% |
| Apr 6, 2026 | Steel and aluminum tariffs restructured into tiers | 10.8% |
| Jul 22–24, 2026 | Brazil Section 301 (25%); forced-labor duties replace the expiring surcharge | 11.2% |
| Aug 22, 2026 | Section 338 duties on Canada | 11.4% |
| Sep 15 and Oct 30, 2026 | Canadian baskets amended | 11.5% |

The record falls into three periods, each defined by the legal authority behind the
tariffs. Underneath all three sit the Section 232 sector tariffs on steel, aluminum, autos
and parts, copper and lumber, which rest on a separate statute and survived the Supreme
Court's ruling.

**IEEPA tariffs (Feb 2025 – Feb 2026).** The first wave rested on the International
Emergency Economic Powers Act. Fentanyl-related duties on China, Canada and Mexico came
first. The reciprocal tariffs followed in April: a 10% baseline from Apr 5, then the full
country rates on Apr 9 for a single day before a 90-day pause that left China at 145%. The
Geneva deal in May cut China to 30%. On Aug 7 new country rates and a series of trade deals
took effect, and the average held near 17% until November, when a truce with China, a deal
with Switzerland and wider exemptions for farm goods brought it down to about 15%.

**Section 122 surcharge (Feb 24 – Jul 23, 2026).** On Feb 20, 2026 the Supreme Court ruled
that IEEPA does not authorize tariffs. Every IEEPA duty ended, leaving only Section 232, and
the average fell to 6.2%. Four days later a 10% surcharge took effect under Section 122, a
balance-of-payments provision, for its 150-day maximum. It exempted goods qualifying under
USMCA and about 1,100 products, including energy, pharmaceuticals and critical minerals.

**Sections 301 and 338 (from Jul 22, 2026).** As the surcharge expired it was replaced by
country-specific actions under trade laws that survived the ruling. Under Section 301,
Brazil faces 25% from Jul 22, and 50 tracked economies face 10% or 12.5% from Jul 24 for
failing to bar imports made with forced labor. Under Section 338, a 1930 retaliation
provision, three baskets of Canadian goods face 50% from Aug 22. The baskets were amended on
Sep 15 and Oct 30.

**Announced but not in force.** On Sep 27, 2026 the United States and China approved lists
of goods, about $30 billion each, for future tariff reductions. No rate, date or legal
instrument has been published, so the list is not in the series. If the U.S. list were
fully excluded from the forced-labor duty, the national average would fall by about 0.12
points.

| Authority | What it allows | Status |
|---|---|---|
| IEEPA | Measures against threats under a declared national emergency | Ruled not to authorize tariffs, Feb 20, 2026 |
| Section 232 | Tariffs on imports that threaten national security, sector by sector | In force |
| Section 122 | A surcharge of up to 15% for up to 150 days, for a balance-of-payments problem | Expired Jul 23, 2026 |
| Section 301 | Tariffs against a country's unreasonable or discriminatory trade practices | In force |
| Section 338 | Tariffs of up to 50% on a country that discriminates against U.S. commerce | In force |

Every action, with its legal reference, is listed in
[METHODOLOGY.md](METHODOLOGY.md#2-tariff-actions-and-how-they-stack).

## 3. Key modeling choices

| Choice | Effect on the measured rate |
|---|---|
| **Statutory rates, full compliance.** Every importer pays exactly what the legal text says. | Above the duties actually collected. |
| **Fixed 2024 weights.** No substitution away from tariffed goods. | Above the duties actually collected. Every change in the series is a change in policy. |
| **All Canadian and Mexican goods count as USMCA-qualifying.** Actual compliance is below 100%. | Understates Canada and Mexico wherever USMCA goods are exempt. |
| **Section 232 goods take their sector rate** and are exempt from the other tariffs, as the legal texts provide. The exception: from Sep 15, 2026 the Canadian alcohol and autos baskets apply on top of Section 232. | Follows the law. |
| **Exemptions that depend on end use** (civil aircraft, pharmaceuticals, auto parts) apply to the whole tariff code, because import data cannot tell end uses apart. | Mixed: some goods are over-exempted, others overcharged. |
| **Three Section 232 sectors are not modeled**: heavy trucks and buses, semiconductors, and patented pharmaceuticals. Their product lists are not available. | Those goods miss their Section 232 duty but pay Section 301 and 338 duties they should be exempt from. |
| **Only actions in legal force count.** Announced or proposed actions are built and checked but switched off until an implementing notice is published. | None. |
| **Dates are taken literally.** Grace periods for goods already in transit are ignored. | Overstates the first days after an increase. |

The full list of choices and limitations, with size estimates, is in
[METHODOLOGY.md](METHODOLOGY.md#4-modeling-limitations).

## 4. The data

| File | One row per | Columns |
|---|---|---|
| [country-by-time.csv](country-by-time.csv) | Partner and policy date | `date`; `country_name` (Census style, e.g. `KOREA, SOUTH`; `EUROPEAN UNION` is the 27-member bloc); `effective tariff`, the tariff increase since January 2025 (%); `total imports`, 2024 imports (US$); `2024 tariff`, duties collected in 2024 divided by imports (%) |
| [daily-tariff-latest-data.csv](daily-tariff-latest-data.csv) | Day | `date`; `import_weighted_avg_tariff`, the national average including the 2.3% baseline (%) |

- A partner's total tariff rate is `effective tariff` plus `2024 tariff`.
- `country-by-time.csv` has rows only on policy dates. Between them a partner's rate is the
  one on the latest earlier date.
- The daily file runs 60 days past the latest update. Days after the update assume no
  further change.
- The tariff codes covered by every action are in [tariff-lists](tariff-lists), and the
  legal texts they come from are in [tariff-lists/sources](tariff-lists/sources).

## 5. What's in the repository

- [code/make-tariff-by-country-by-time.ipynb](code/make-tariff-by-country-by-time.ipynb)
  codes every tariff action and builds the two data files.
- [code/plot-tariff-by-country-by-time.ipynb](code/plot-tariff-by-country-by-time.ipynb)
  draws the tracker's charts and the chart above.
- [code/analysis](code/analysis) holds notebooks that examine individual actions: the
  Brazil and forced-labor Section 301 actions, the Section 338 actions against Canada, the
  U.S.-China list and the Section 122 surcharge.
- [tariff-lists](tariff-lists) holds the product lists extracted from each legal text.
  The texts themselves are in [tariff-lists/sources](tariff-lists/sources), and the
  scripts that extract and validate the lists are in [code](code).
- [data](data) holds the Census import data by partner and product; the 2024 files supply
  the weights.

[TECHNICAL-README.md](TECHNICAL-README.md) describes each notebook and script and how to run
them.

## 6. Known issues

These errors are known and not yet corrected. Fixing any of them changes past values.

| Issue | Effect | Dates |
|---|---|---|
| Canadian and Mexican auto parts are charged 15%, although parts qualifying under USMCA owe no Section 232 duty. | Canada +0.68 points, Mexico +2.12 points | From Apr 2025 |
| Three auto-parts codes (vehicle lighting, car radios) are mistyped, so those goods never take the auto-parts rate. | About $7.6 billion of 2024 imports, mostly from Mexico, undercharged | From Apr 2025 |
| The auto-parts duty starts with the vehicle duty on Apr 3, 2025. By law it began May 3. | Overstated | Apr 3 – May 2, 2025 |
| Canada and Mexico keep the old treatment of the reciprocal-tariff product exemptions while their handling is reviewed. | Switching would raise Canada by about 1.9 points (May 2025) to 6.2 points (from Nov 14, 2025) | Apr 2025 – Feb 2026 |
| The electronics exemption starts Apr 11, 2025. Customs applied it from Apr 5. | Electronics overcharged | Apr 5–10, 2025 |
| The Geneva cut for China takes effect May 12, 2025. By law it took effect May 14. | China undercharged | May 12–13, 2025 |

Details are in [METHODOLOGY.md](METHODOLOGY.md#5-open-issues).
