# Data Quality Notes

Findings recorded while extracting the dataset. Written as they were found, kept in place rather than tidied away.

---

## 1. The FY26 segment realignment

**What HP did.** Effective Q1 FY26, HP moved its Print-as-a-Service business from the Corporate Investments segment into Printing, and restated prior periods on an as-if basis. Revenue and costs were reclassified into Supplies and Consumer Printing.

**Why it matters for analysis.** The same fiscal quarter now has two published revenue figures depending on which release you read. Building a time series by pulling each quarter from its own original release would produce a chart with an invisible discontinuity at the FY25/FY26 boundary.

**Scale of the change, Printing segment net revenue, USD millions:**

| Quarter | As previously reported | Revised | Change |
|---|---|---|---|
| Q1 FY24 | 4,375 | 4,375 | 0 |
| Q2 FY24 | 4,368 | 4,369 | +1 |
| Q3 FY24 | 4,143 | 4,150 | +7 |
| Q4 FY24 | 4,452 | 4,462 | +10 |
| Q1 FY25 | 4,269 | 4,280 | +11 |
| Q2 FY25 | 4,181 | 4,197 | +16 |
| Q3 FY25 | 3,986 | 4,002 | +16 |
| Q4 FY25 | 4,266 | 4,285 | +19 |

The reclassification grows over time, from nothing in Q1 FY24 to 19 million by Q4 FY25, consistent with a Print-as-a-Service business that was itself growing.

**Effect on Consumer Printing is proportionally much larger.** Consumer Printing is a small business unit (roughly 275 to 335 million per quarter), so the same absolute reclassification is a bigger relative shift. Q4 FY25 Consumer Printing moved from 296 to 309, about 4.4%. Anyone tracking Consumer Printing growth across the boundary without noticing would attribute a reporting change to business performance.

**Revenue neutral overall.** Total segment net revenue is identical on both bases in every quarter. The change moves revenue between segments, it does not create or destroy any. This is asserted in `validate.py` rather than assumed.

**Also affects profitability.** Printing earnings before taxes was revised *down* in every FY25 quarter (39 million lower across the year) while Corporate Investments improved by exactly the offsetting amount. So the realignment moved a loss-making activity into Printing: revenue up, earnings down.

**How the dataset handles it.** Every row carries a `reporting_basis` column, either `FY26 realigned` or `as previously reported`. The two can be compared deliberately but never silently mixed. Any analysis must filter to one basis.

---

## 2. Validation approach

`validate.py` runs eight assertions. The first five are internal consistency:

1. Supplies + Commercial Printing + Consumer Printing equals reported Printing.
2. Personal Systems + Printing + Corporate Investments equals reported total segment.
3. Consumer PS + Commercial PS equals reported Personal Systems.
4. Computed restatement deltas equal HP's own published CHANGE column.
5. Total segment revenue is unchanged across the two bases.

Checks 6, 7 and 8 are described in sections 7 and 8 below. Of the eight, the ones that carry real weight are 4, 6, 7 and 8, because each tests the data against something *outside itself*: HP's own published arithmetic, a second disclosure of the same quantity, a separately sourced dataset, and narrative prose against a table, respectively. Checks 1 to 3 would all pass happily on a consistently mistyped dataset.

All checks currently pass on 253 segment rows and 39 regional rows.

---

## 3. A typo in the source

HP's restatement tables label the second-quarter column **"Apr 31"** in both the FY24 and FY25 blocks. April has 30 days. HP's own consolidated statements elsewhere in the same release correctly use April 30.

Treated as April 30 in this dataset. Noted because a date parser reading the table headers literally would either fail or silently produce a wrong date, and because it is a small reminder that published sources contain errors and should be read rather than trusted blindly.

---

## 4. Known limitations

- **Home Printing cannot be isolated.** HP reports Consumer Printing, which contains home printing but is not equivalent to it. No public breakdown goes below this level.
- **Regional revenue is company-wide only.** Americas, EMEA and APJ are now extracted from the SEC filings (section 6), but only for HP as a whole. Regional revenue cannot be split by segment, so EMEA Printing specifically is not obtainable.
- **FY26 quarters have no prior-basis figures**, because the realignment took effect at the start of FY26. Comparisons across the boundary must use the revised basis throughout.
- **Q2 FY25 and Q2 FY24 operating margins are not yet captured**, since they appear only in releases not yet extracted.
- **Everything here is transcribed by hand from HTML tables.** The validation checks are what stand between a typo and a wrong chart, which is why check 4 against HP's own published deltas matters more than the internal consistency checks.

---

## 5. Source cross-check, 2026-08-28

Re-fetched both source press releases directly and compared every figure against the live pages, rather than trusting the transcription alone.

**Confirmed exact matches:**
- Net revenue by business unit (all nine units) for Q1 FY26, Q4 FY25, Q3 FY25, Q2 FY26, Q3 FY26.
- The full FY24 and FY25 restatement reconciliation table (Supplies, Consumer Printing, Printing total, Corporate Investments, revised vs. as-previously-reported, all 8 quarters).
- Segment operating margin (Personal Systems, Printing, Total segment) for Q1 FY25, Q4 FY25, Q3 FY25, Q1 FY26, Q2 FY26, Q3 FY26.
- Earnings before taxes by segment for the same six quarters.

**Not independently re-checked in that pass:** Commercial PS, Consumer PS and Personal Systems total for Q2 FY25 and all four FY24 quarters. These are structurally unaffected by the realignment (identical on both reporting bases in the dataset, which is consistent with HP's own footnote that the change only touched Corporate Investments, Supplies and Consumer Printing), but they were not re-pulled from a live source table in this pass. Worth a manual spot check: open the Q1 FY26 press release (`investor.hp.com`, "HP Inc. Reports Fiscal 2026 First Quarter Results"), find the `SEGMENT/BUSINESS UNIT INFORMATION` table, and compare the Personal Systems row for Q1 FY25 against the figure printed there. That table shows three columns (two quarters back, one quarter back, year-ago quarter), so one release only ever gives partial FY24 coverage; the FY24 figures likely require the original FY24 quarterly releases rather than the Q1 FY26 restatement table, since that table's stated purpose is the Printing/Corporate Investments reclassification and does not necessarily reprint unaffected Personal Systems rows for periods outside its own three-quarter window.

---

## 6. Regional revenue: extraction and its hard limitation

Regional revenue is not in the press release segment tables at all. It appears only in the SEC filings, in a table named `Supplementary Financial Information - Schedule of Net Revenue by Region`. Extracted by `analysis/fetch_regional.py` into `data/processed/regional_revenue.csv`, 33 rows covering 11 quarters.

**The limitation that shapes the whole project.** HP discloses revenue by region for the company as a whole, and by business unit globally, but never the two crossed. **EMEA Printing revenue does not exist in any public filing.** This is a disclosure boundary, not a research failure, and no amount of additional sourcing gets past it. It is recorded here rather than discovered late because it determines what this analysis can and cannot claim.

**Q4 is derived, not reported.** Q4 never appears in a 10-Q, because the 10-K replaces it. So:

> Q4 = full fiscal year, from the 10-K, minus (Q1 + Q2 + Q3), from the three 10-Qs

The full fiscal year figure is kept as its own row (`period_type = full_year`, `source_type = reported`) rather than only used internally and discarded, so the whole derivation is auditable from the CSV alone: any Q4 row's value equals its matching `FY` row minus the sum of that year's three `source_type = reported` quarterly rows, with every input to that subtraction sitting in the same table. Confirmed by hand 2026-08-29 that HP's disclosed "nine months ended" figure equals summing the three separately reported quarterly figures exactly, in all three regions, so this is equivalent to the original derivation, just checkable without leaving the file.

The derivation also checks out against an independent source: computed Q4 FY25 regional revenue totals 14,639, and HP separately prints total net revenue of 14,639 for that quarter in the Q1 FY26 press release. Different document, different table, same number.

**Two parser traps worth recording**, both of which produced silently wrong output before being caught:

1. The R file number for the regional table moves between filings (R50, R51, R52 and R103 all observed), so it is located by name. A hardcoded number would have broken silently.
2. HP displays the third region as "Asia-Pacific and Japan" but tags it `srt_AsiaPacificMember`, and EMEA carries a `us-gaap_` prefix while the others carry `srt_`. An early version of the parser matched only the `srt_` shape and dropped EMEA and APJ entirely while still reporting success, because the cross-check skipped quarters with missing regions instead of failing them. Both the parser and the check were fixed. Unrecognised region members now print a warning rather than being silently dropped.

The second one is the more useful lesson: the bug was not the parser, it was a validation check that could report all-clear on incomplete data.

## 7. Validation checks now in place

`analysis/validate.py` runs eight, and the last three are new:

6. **Revenue times operating margin must reproduce reported earnings before taxes.** Two independent disclosures of the same thing, so they have to agree. They never agree exactly, because margin is published rounded to one decimal, meaning a printed 18.1% is really anything in [18.05, 18.15). The tolerance is therefore `revenue * 0.05%`, which **scales with revenue**. A fixed threshold would be wrong in both directions: it would wrongly fail Personal Systems, where large revenue produces a large absolute rounding error, and wrongly pass small business units where a genuine error could hide beneath it. 12 reconciliations pass.

7. **Cross-source reconciliation.** Regional revenue comes from the SEC filings, segment revenue from the press releases. Independent transcriptions of the same company, so the three regions must reconcile to total segment net revenue, differing only by HP's small "Other" line of 0 to 2 million. 11 quarters pass.

8. **Narrative growth against tabled revenue.** The nominal y/y percent HP states in prose must match what the net_revenue table cells themselves imply, within HP's own one-percent rounding. Described fully in section 8. 6 reconciliations pass.

Check 7 is the most valuable of the eight, because it is the only one that tests two separately sourced datasets against each other rather than testing one dataset against itself.

---

## 8. Narrative-only figures: constant currency and hardware units

Two metrics exist only in each release's prose ("Fiscal 2026 [quarter] segment results"), never in a table: constant-currency y/y growth and hardware unit y/y growth. Added by `analysis/build_dataset.py` (`CC_GROWTH`, `UNITS_GROWTH`, `YOY_NOMINAL`) for the three FY26 quarters, since narrative coverage only extends to whichever quarter each release is itself reporting.

**Two things preserved rather than smoothed over in transcription:**

- HP prints "flat" for some quarters instead of a number (Printing nominal growth, Q2 FY26; Supplies constant currency, Q2 FY26). Recorded as `0`, since that is what "flat" means at HP's one-percent rounding, but it is HP's word choice, not a precise reading. Noted here so `0` in those two cells is never mistaken for a sharper measurement than the source actually gives.
- Q1 FY26 does not disclose Consumer Printing and Commercial Printing units separately ("both reflecting similar declines"). Those cells are absent from `UNITS_GROWTH`, not filled with a guess. Absence means not disclosed.

**Check 8** reconciles the transcribed nominal y/y figures against what the tabled `net_revenue` rows themselves imply, the same logic as check 6 but between narrative and table rather than between margin and profit. 6 reconciliations pass within a 0.5 point band, matching HP's own one-percent rounding.

**What the two derived proxies show, verified against the data 2026-08-29:**

- **FX tailwind, growing across FY26.** Nominal growth minus constant-currency growth: Printing +0.8pp (Q1) to +2.0pp (Q2) to +1.8pp (Q3). Consistent with EMEA and APJ revenue growth outpacing Americas across the same quarters (see EMEA y/y in section 6's context). A weakening dollar is flattering HP's reported growth, and it is helping Printing more than it would matter to a segment growing faster in USD terms already.
- **Consumer Printing ASP.** Q3 FY26: revenue -1.8%, units -9.0%, implying average selling price up roughly 7 points. This is the single most role-relevant number in the dataset for a Home Print category role: volume is falling faster than revenue, meaning HP is pushing price or mix, not chasing unit share.
