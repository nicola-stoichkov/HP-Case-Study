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

`validate.py` runs five assertions:

1. Supplies + Commercial Printing + Consumer Printing equals reported Printing.
2. Personal Systems + Printing + Corporate Investments equals reported total segment.
3. Consumer PS + Commercial PS equals reported Personal Systems.
4. Computed restatement deltas equal HP's own published CHANGE column.
5. Total segment revenue is unchanged across the two bases.

Check 4 is the meaningful one. HP publishes its own restatement reconciliation, so the transcription can be checked against the source's own arithmetic rather than only against itself. All eight quarters match exactly.

All checks currently pass on 222 rows across 19 quarter and basis combinations.

---

## 3. A typo in the source

HP's restatement tables label the second-quarter column **"Apr 31"** in both the FY24 and FY25 blocks. April has 30 days. HP's own consolidated statements elsewhere in the same release correctly use April 30.

Treated as April 30 in this dataset. Noted because a date parser reading the table headers literally would either fail or silently produce a wrong date, and because it is a small reminder that published sources contain errors and should be read rather than trusted blindly.

---

## 4. Known limitations

- **Home Printing cannot be isolated.** HP reports Consumer Printing, which contains home printing but is not equivalent to it. No public breakdown goes below this level.
- **No regional split in this dataset yet.** Americas, EMEA and APJ revenue is not in the press release segment tables. It appears in the 10-Q filings and in the earnings presentation charts. To be added.
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

**Not independently re-checked this session:** Commercial PS, Consumer PS and Personal Systems total for Q2 FY25 and all four FY24 quarters. These are structurally unaffected by the realignment (identical on both reporting bases in the dataset, which is consistent with HP's own footnote that the change only touched Corporate Investments, Supplies and Consumer Printing), but they were not re-pulled from a live source table in this pass. Worth a manual spot check: open the Q1 FY26 press release (`investor.hp.com`, "HP Inc. Reports Fiscal 2026 First Quarter Results"), find the `SEGMENT/BUSINESS UNIT INFORMATION` table, and compare the Personal Systems row for Q1 FY25 against the figure printed there. That table shows three columns (two quarters back, one quarter back, year-ago quarter), so one release only ever gives partial FY24 coverage; the FY24 figures likely require the original FY24 quarterly releases rather than the Q1 FY26 restatement table, since that table's stated purpose is the Printing/Corporate Investments reclassification and does not necessarily reprint unaffected Personal Systems rows for periods outside its own three-quarter window.
