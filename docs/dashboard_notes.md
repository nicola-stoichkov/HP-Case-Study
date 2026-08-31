# Dashboard Notes

Notes on the Looker Studio build (D2) and the two dimension tables that support it (D1). Power BI notes get added here once that rebuild starts.

Live report: `dashboards/looker_studio_export.pdf` is a point-in-time export from 2026-08-31. Not yet linked live, since the report is still being edited; a live share link gets added here once it's in a state worth sharing.

---

## 1. Two dimension tables (D1)

`dim_business_unit`: nine business units, with `is_rollup` flagging the three subtotal levels (Personal Systems, Printing, Total segment) so a chart or measure can filter to leaf units only without repeating the criterion every time. Also carries `parent_unit`, encoding the real hierarchy (e.g. Commercial PS's parent is Personal Systems).

`dim_date`: eleven rows, one per fiscal quarter, with an explicit `sort_order` column and three metrics carried over from `derived` (`ttm_printing_revenue`, `supplies_share_of_printing_pct`, `printing_share_of_total_pct`), since those were already computed once and verified there. Worth being honest about this one: a strict data model keeps dimension tables to descriptive attributes only, no measures. Bolting metrics onto `dim_date` is a pragmatic shortcut for getting Looker Studio a row-per-quarter shape to chart against, not textbook-correct. Fine to say so if asked.

`dim_business_unit` isn't wired into Looker Studio at all yet, deliberately. Its real payoff is Power BI's native relationship model; for Looker Studio, filtering directly on `business_unit` values in each chart was simpler and avoided blending under time pressure.

## 2. Looker Studio build (D2)

Four visuals: Printing revenue by business unit (stacked column, leaf units only), regional revenue by region (stacked column), Printing share of Total & Supplies share of Printing (line chart, from `dim_date`), and three KPI cards (revenue, y/y growth, operating margin, all for Q3 FY26).

## 3. Real bugs hit while building this, and what each one actually was

**Time series chart type restricts its dimension to Date fields only.** Tried building the share-of-parent chart as a Time series, and `fiscal_quarter` (Text) wasn't selectable, only `quarter_end_date` (Date) was. Not a data problem, the chart type itself filters the dimension picker. Fixed by switching to a plain Line chart, which has no such restriction.

**Every chart defaults to alphabetical sort on a text field.** `fiscal_quarter` sorted as Q1 FY24, Q1 FY25, Q1 FY26, Q2 FY24... because "Q1" sorts before "Q2" as text regardless of year. This is the identical trap already documented for Power BI in `spreadsheet_notes.md`, just surfacing in a second tool. Fixed the same way conceptually in both: point the chart's Sort field at `quarter_end_date` instead of the displayed dimension. Different UI, same underlying fix.

**Two percentages sharing a chart got put on separate axes by default.** Looker Studio auto-assigned a right axis to the second metric because the two values sit in different ranges (~65% vs. ~25-33%), which made two comparable percentages visually cross in a way that implied a relationship that wasn't real. Fixed by forcing both metrics onto the same (left) axis in the Style tab.

**Percent formatting behaves oppositely depending on how the source number is stored.** `operating_margin_pct` is stored as `7.8` meaning 7.8%, so applying Looker Studio's Percent format directly turned it into 780% (the format assumes a decimal fraction like `0.078`). Fixed with a calculated field dividing by 100 first. The q/q change metrics, by contrast, were already computed as ratios like `(C-B)/B`, which naturally produce `0.05` for 5%, so Percent formatting applied to those directly, no division. Same "percent" concept, opposite storage convention, and worth remembering which is which rather than pattern-matching one fix onto both cases.

**Quarter-over-quarter growth for small business units is dominated by seasonality, not signal.** A first pass at a growth-rate line for Supplies, Commercial Printing and Consumer Printing swung ±10 points and flipped sign almost every quarter. Checked the actual numbers: Q/Q growth compares Q4 (always HP's strongest quarter) against Q1 (always weakest), so a large swing shows up every single year regardless of whether anything real changed. Switching to Y/Y (same quarter, prior year) cancels the seasonal pattern and reveals real trend, exact same insight that justified building TTM in the `derived` tab in the first place, just rediscovered independently while looking at a chart rather than a table.

**A malformed cell inside a connected range broke the whole data source.** `dim_date!F2` and `!I2` briefly held a `TRANSPOSE(...)` formula sized for an entire row, placed in a single cell and colliding with values already below it. One broken cell in a Google Sheets range Looker Studio is connected to was enough to throw "Data Set Configuration Error" on every chart sourced from that tab. Fixed by pasting the two cells as plain static values, matching the rest of their own columns, which were already static values rather than live formulas. Worth noting as a real trade-off, not a full fix: those two cells no longer recompute automatically if `derived` changes upstream, the same category of caveat already recorded in the Sheets-to-Excel export notes below.

**Chart-level filters apply to every metric in a chart, not per-metric.** Wanted a Printing growth-rate line layered onto the same chart as the three leaf units' stacked revenue. Couldn't, because that chart's filter (leaf units only) would exclude a Printing-level growth row even if one existed in the same source. Building it as a second, separate, standalone chart placed directly beneath the first avoided the problem entirely rather than needing a blend.

**A chart title said EUR when every source document says USD.** Caught before it reached anyone else, but worth recording as the reminder it is: a labeling mistake in a chart title is invisible to every validation check that only looks at the numbers.

## 4. Known limitation carried from `spreadsheet_notes.md`

The `TRANSPOSE`/`FILTER`/`UNIQUE`/`SORT` fragility documented there for the Sheets-to-Excel export path is the same category of issue as the `dim_date` incident above: a live formula that only some tools evaluate correctly. Both are recorded so neither is mistaken for a data error later.
