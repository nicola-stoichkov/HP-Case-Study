# Dashboard Notes

Notes on the Looker Studio build (D2), the two dimension tables that support it (D1), and the Power BI rebuild (D3).

Live report: `dashboards/looker_studio_export.pdf` is a point-in-time export from 2026-08-31. Not yet linked live, since the report is still being edited; a live share link gets added here once it's in a state worth sharing.

---

## 1. Two dimension tables (D1)

`dim_business_unit`: nine business units, with `is_rollup` flagging the three subtotal levels (Personal Systems, Printing, Total segment) so a chart or measure can filter to leaf units only without repeating the criterion every time. Also carries `parent_unit`, encoding the real hierarchy (e.g. Commercial PS's parent is Personal Systems).

`dim_date`: eleven rows, one per fiscal quarter, with an explicit `sort_order` column and three metrics carried over from `derived` (`ttm_printing_revenue`, `supplies_share_of_printing_pct`, `printing_share_of_total_pct`), since those were already computed once and verified there. Worth being honest about this one: a strict data model keeps dimension tables to descriptive attributes only, no measures. Bolting metrics onto `dim_date` is a pragmatic shortcut for getting Looker Studio a row-per-quarter shape to chart against, not textbook-correct. Fine to say so if asked.

`dim_business_unit` isn't wired into Looker Studio at all yet, deliberately. Its real payoff is Power BI's native relationship model; for Looker Studio, filtering directly on `business_unit` values in each chart was simpler and avoided blending under time pressure.

## 2. Looker Studio build (D2)

Final layout, revised 2026-09-01 to a deliberate broad-to-narrow structure: three scorecards (zero dimensions, the broadest possible view) leading the page, then three levels of a single drill-down, each level pairing an absolute view with a rate-or-share view beside it.

| Level | Absolute | Rate / share |
|---|---|---|
| Total | Revenue, y/y growth, operating margin (Q3 FY26) | — |
| Region | Americas/EMEA/APJ, stacked column | Regional share of total, quarterly, line |
| Segment | Personal Systems vs. Printing, stacked column | Segment share of total, line |
| Business unit | Printing sub-units, stacked column | Printing sub-units, Y/Y growth, line |

Two things deliberately left out, and why:

- **A 100% stacked view of Printing's own sub-units.** Composition barely moves (Supplies runs 64.3% to 66.8% across all eleven quarters), so the chart would be flat and add nothing beyond what the absolute chart and the data quality notes already say.
- **A chart mixing all five leaf categories (both segments) as a share of total.** It doesn't fit a single-branch drill-down, since it cuts laterally across Personal Systems' and Printing's leaves at once rather than going one level deeper into either. The underlying finding (Commercial PS +4.9pp against Supplies -3.2pp, Q1-Q3 basis FY24 to FY26) stays valid and citable from the `yearly_share` tab, just isn't charted.

Regional share was originally planned as a yearly (Q1-Q3 basis) comparison to avoid comparing non-matching quarters, then reverted to quarterly once checked properly: share-of-total is a level, not a difference, so it doesn't get distorted by seasonality the way a growth *rate* does. Quarterly resolution shows the real seasonal wobble (Americas share dips every Q1, peaks every Q3/Q4) sitting on top of the real trend (Americas losing share to APJ), which is more honest than a clean 3-point chart that hides the texture.

## 3. Real bugs hit while building this, and what each one actually was

**Time series chart type restricts its dimension to Date fields only.** Tried building the share-of-parent chart as a Time series, and `fiscal_quarter` (Text) wasn't selectable, only `quarter_end_date` (Date) was. Not a data problem, the chart type itself filters the dimension picker. Fixed by switching to a plain Line chart, which has no such restriction.

**Every chart defaults to alphabetical sort on a text field.** `fiscal_quarter` sorted as Q1 FY24, Q1 FY25, Q1 FY26, Q2 FY24... because "Q1" sorts before "Q2" as text regardless of year. This is the identical trap already documented for Power BI in `spreadsheet_notes.md`, just surfacing in a second tool. Fixed the same way conceptually in both: point the chart's Sort field at `quarter_end_date` instead of the displayed dimension. Different UI, same underlying fix.

**Two percentages sharing a chart got put on separate axes by default.** Looker Studio auto-assigned a right axis to the second metric because the two values sit in different ranges (~65% vs. ~25-33%), which made two comparable percentages visually cross in a way that implied a relationship that wasn't real. Fixed by forcing both metrics onto the same (left) axis in the Style tab.

**Percent formatting behaves oppositely depending on how the source number is stored.** `operating_margin_pct` is stored as `7.8` meaning 7.8%, so applying Looker Studio's Percent format directly turned it into 780% (the format assumes a decimal fraction like `0.078`). Fixed with a calculated field dividing by 100 first. The q/q change metrics, by contrast, were already computed as ratios like `(C-B)/B`, which naturally produce `0.05` for 5%, so Percent formatting applied to those directly, no division. Same "percent" concept, opposite storage convention, and worth remembering which is which rather than pattern-matching one fix onto both cases.

**Quarter-over-quarter growth for small business units is dominated by seasonality, not signal.** A first pass at a growth-rate line for Supplies, Commercial Printing and Consumer Printing swung ±10 points and flipped sign almost every quarter. Checked the actual numbers: Q/Q growth compares Q4 (always HP's strongest quarter) against Q1 (always weakest), so a large swing shows up every single year regardless of whether anything real changed. Switching to Y/Y (same quarter, prior year) cancels the seasonal pattern and reveals real trend, exact same insight that justified building TTM in the `derived` tab in the first place, just rediscovered independently while looking at a chart rather than a table.

**A malformed cell inside a connected range broke the whole data source.** `dim_date!F2` and `!I2` briefly held a `TRANSPOSE(...)` formula sized for an entire row, placed in a single cell and colliding with values already below it. One broken cell in a Google Sheets range Looker Studio is connected to was enough to throw "Data Set Configuration Error" on every chart sourced from that tab. Fixed by pasting the two cells as plain static values, matching the rest of their own columns, which were already static values rather than live formulas. Worth noting as a real trade-off, not a full fix: those two cells no longer recompute automatically if `derived` changes upstream, the same category of caveat already recorded in the Sheets-to-Excel export notes below.

**Chart-level filters apply to every metric in a chart, not per-metric.** Wanted a Printing growth-rate line layered onto the same chart as the three leaf units' stacked revenue. Couldn't, because that chart's filter (leaf units only) would exclude a Printing-level growth row even if one existed in the same source. Building it as a second, separate, standalone chart placed directly beneath the first avoided the problem entirely rather than needing a blend.

**A chart title said EUR when every source document says USD.** Caught before it reached anyone else, but worth recording as the reminder it is: a labeling mistake in a chart title is invisible to every validation check that only looks at the numbers.

**A missing filter silently summed different metrics together.** The Personal Systems vs. Printing chart was built straight from `segment_data` without a `metric = net_revenue` filter, so from Q1 FY25 onward (the first quarter where operating margin and earnings before taxes exist alongside revenue) it was adding revenue dollars, margin percentage points, profit dollars, and, for FY26 quarters, growth-rate percentages, all into one number. Every value looked plausible, since the wrong sum still landed in roughly the right range and roughly the right shape. Confirmed by reconstructing the exact arithmetic: Q1 FY26 Personal Systems showed 10,799, which is precisely 10,251 (revenue) + 511 (EBT) + 5.0 (margin) + 11 + 9 + 12 (three growth-rate metrics). This is the same shape of failure as the two double-counting traps documented in `docs/calculation_layer.md`, just one level up: those are about summing the *right* metric across the *wrong* rows, this was summing the *wrong* metrics across the *right* rows. Same lesson either way: a plausible number is not a checked number.

**The phantom-row bug came back after a column reshuffle.** The `TRANSPOSE` incident above was fixed by pasting two cells as static values, but a later reorganisation of `dim_date`'s columns left an empty row 13 hanging off the end of the table (present as a row with empty cells, not deleted). Same failure mode as before: an artifact inside a connected range, invisible until the connection itself misbehaves. Deleting the row (not just clearing its cells) fixed it. Worth remembering as a pattern rather than a one-off: any edit that shifts a table's shape is worth checking for leftover rows or columns at the boundary, not just verifying the cells that were intentionally changed.

## 4. Known limitation carried from `spreadsheet_notes.md`

The `TRANSPOSE`/`FILTER`/`UNIQUE`/`SORT` fragility documented there for the Sheets-to-Excel export path is the same category of issue as the `dim_date` incident above: a live formula that only some tools evaluate correctly. Both are recorded so neither is mistaken for a data error later.

## 5. Power BI (D3), first pass, 2026-09-02

`dashboards/power_bi_report.pbix`. Six of seven planned visuals built (the three scorecards, Power BI's `Card` visual, not yet added). Not styled yet, by the builder's own assessment, and not marked done on the board for a second reason below.

**Built with Power Query conditional columns, not DAX measures.** `docs/dax_measures.md` was drafted assuming a DAX approach and was not actually used to build this. That gap needs resolving, either by adding real DAX measures on top of what exists (the original plan's `CALCULATE`, `DIVIDE`, and filter-context-override Y/Y pattern all still have genuine teaching value for the interview) or by rewriting `dax_measures.md` to describe what was actually built. Left open deliberately rather than silently reconciled, since it's the user's call which direction to take.

**A circular dependency, and why it happened.** Sorting `region` by a calculated column (`region_sort_order`, built with `SWITCH(regional_revenue[region], ...)`) failed with "a circular dependency was detected." The calculated column's DAX formula reads `region`, so Power BI's dependency graph sees `region_sort_order` depending on `region`; asking it to also sort `region` *by* `region_sort_order` closes the loop, even though no single row's value actually depends on another row's sort order. Power BI's checker doesn't distinguish the two. Fixed by moving the same logic into a Power Query Conditional Column instead, computed at load time, before the DAX dependency graph exists, so the circularity check never triggers. The general lesson: a column meant to control the sort order of a field it's also derived from needs to be built in Power Query, not DAX, whenever the two would otherwise reference each other.

**Validated by reading the report's own JSON, not by re-deriving the numbers.** Power BI's newer PBIR format stores each visual's field bindings and filters as plain, readable JSON (`Report/definition/pages/.../visuals/*/visual.json`), unlike the `DataModel` binary, which is proprietary and wasn't parseable here. That let the filter configuration on every visual be checked directly: two of three column charts (Personal Systems vs. Printing, Printing sub-units) have `business_unit`, `metric = net_revenue`, and `reporting_basis = FY26 realigned` all correctly pinned. The third, the regional stacked column, is missing `period_type = "quarter"`, so it will show thirteen categories instead of eleven, the two full-year summary rows appearing as extra bars alongside the real quarters. Structure was verifiable this way; the actual computed values in `DataModel` were not, so this is a structural check, not a full reconciliation against source the way the spreadsheet got.

**First read of the filter JSON was wrong, worth recording why.** Read `visual.filterConfig` (nested inside the `visual` object) and found nothing, concluded all six visuals had zero filters. `filterConfig` actually sits as a sibling of `visual` at the top level of the file, one level up from where it was checked. Caught by grepping the raw file text for the word "filter" and finding real matches the structured parse had missed, then re-parsing with the correct path. The lesson repeats one already in this project's history: a validation check that returns a clean result is only as trustworthy as the path it actually looked at.
