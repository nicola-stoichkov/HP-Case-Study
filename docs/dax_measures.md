# DAX Measures

**Status note, 2026-09-02.** This file was drafted first, proposing a DAX-based approach for the Power BI model. The actual `.pbix` (D3) was built with Power Query conditional columns instead, under time pressure ahead of the interview, not with the measures below. The report works correctly on that Power Query approach alone. Measures 1 to 5 stay here as spec, to build if time allows before the interview. See `docs/dashboard_notes.md` §5 for the build-side account of the divergence.

**Update, same day.** Measures 1, 2, and 4 (`Net Revenue`, `Printing Revenue`, `Regional Revenue`) are built and in active use across the finished three-page report. Measure 8 (`Operating Margin`) was added during that build to fix a live bug, see below. Measures 6 and 7 (`Region % of Total`, `Segment % of Total`) were built and debugged at length but never got working, see the outcome note under Measure 7. Full build account in `docs/dashboard_notes.md` §6.

Drafted for review rather than pasting. Each one below says what it does and why it is written that way, because a measure you cannot explain is worse than no measure. Type them yourself in Power BI; the point of the exercise is the model, not the file.

Column references match the tabs in `spreadsheet/formula_layer.xlsx`.

---

## Before any measure: three model setup steps

**1. Fix the quarter sort order.** Power BI sorts text alphabetically, so `fiscal_quarter` will order as Q1 FY24, Q1 FY25, Q1 FY26, Q2 FY24, and so on. Select the `fiscal_quarter` column, then Column tools, then Sort by column, and choose `quarter_end_date`.

This is the same trap already hit in Looker Studio and documented in `docs/dashboard_notes.md`. Not a bug in either tool, just what every BI tool does by default with a text column, and worth recognising as a category of problem rather than two unrelated incidents.

**2. Build the relationships.** In Model view, drag to connect:

- `dim_date[fiscal_quarter]` to `segment_data[fiscal_quarter]`
- `dim_date[fiscal_quarter]` to `regional_revenue[fiscal_quarter]`
- `dim_business_unit[business_unit]` to `segment_data[business_unit]`

All three are one to many, from the dimension side to the fact side. Power BI usually infers this correctly; check that the arrow points from the dimension table toward the fact table.

**3. Know what `is_rollup` looks like after import.** It comes in as the numbers 0 and 1 rather than TRUE and FALSE, so filter it as `= 0` for leaf units, not `= FALSE`. This is the column that encodes trap 1 (leaf rows sitting alongside their own subtotals) into the model, so a chart can exclude subtotals without every visual having to list business units by hand. This is the thing Looker Studio could not do, and the reason `dim_business_unit` exists.

---

## Measure 1: the base

```dax
Net Revenue =
CALCULATE(
    SUM(segment_data[value]),
    segment_data[metric] = "net_revenue",
    segment_data[reporting_basis] = "FY26 realigned"
)
```

**What `CALCULATE` does.** It evaluates an expression while changing the filters that apply to it. Everything after the first argument is a filter. Here it sums the value column, but only over rows where the metric is net revenue and the basis is the realigned one.

**Why it matters that this lives in one place.** The `value` column mixes net revenue, operating margin percentages, earnings before taxes, and growth rates. A plain `SUM(segment_data[value])` would add a margin percentage to a revenue figure and return a meaningless number without erroring. Pinning `metric` here means every measure built on top of this one inherits the fix.

The `reporting_basis` pin is trap 2, defended once rather than in every visual.

**Filter context is the concept most likely to be probed.** Worth being able to say: a measure does not have one fixed answer, it recalculates against whatever filters are active where it is used. Drop `Net Revenue` in a table sliced by quarter and it evaluates once per quarter, with that quarter silently added to the filters `CALCULATE` already applies.

---

## Measure 2: composing on the base

```dax
Printing Revenue =
CALCULATE(
    [Net Revenue],
    segment_data[business_unit] = "Printing"
)
```

Note it takes `[Net Revenue]` rather than repeating the `SUM` and the two filters. Measures composing on other measures is what keeps a model maintainable: change the base once and everything downstream follows. If the reporting basis ever needed switching, this measure would need no edit at all.

---

## Measure 3: a ratio

```dax
Supplies Share of Printing =
DIVIDE(
    CALCULATE([Net Revenue], segment_data[business_unit] = "Supplies"),
    CALCULATE([Net Revenue], segment_data[business_unit] = "Printing")
)
```

**Use `DIVIDE`, not a slash.** `DIVIDE` returns blank when the denominator is zero, where `/` returns an error that propagates into the visual. Small thing, asked about often.

Format the result as a percentage in the Measure tools ribbon. Note this produces a true ratio (0.648), so Power BI's percentage format displays it correctly with no division by 100. That is the opposite of `operating_margin_pct`, which is stored as `18.1` meaning 18.1 percent and would need dividing by 100 first. Same word, two storage conventions, documented in `docs/dashboard_notes.md` after it caused a 780% scorecard in Looker Studio.

---

## Measure 4: the other fact table

```dax
Regional Revenue =
CALCULATE(
    SUM(regional_revenue[value]),
    regional_revenue[period_type] = "quarter"
)
```

The `period_type` filter is load bearing. That table holds full year rows as well as quarterly ones, so without it every year would be added to its own quarters and roughly double the total. A third instance of the same double counting shape, in a different file, which is why `period_type` exists as a column at all.

---

## Measure 5, optional: leaf units only

```dax
Leaf Revenue =
CALCULATE(
    [Net Revenue],
    dim_business_unit[is_rollup] = 0
)
```

This is `dim_business_unit` doing the job it was built for: reported subtotals excluded through a relationship, rather than by naming the three leaf units by hand in every chart's filter. Worth building even if unused, because it is the clearest demonstration that the trap is handled in the model rather than per visual.

---

## Measure 6: percent of total, region

```dax
Region % of Total =
DIVIDE(
    [Regional Revenue],
    CALCULATE([Regional Revenue], ALL(regional_revenue[region]))
)
```

**The `ALL()` pattern.** `ALL(regional_revenue[region])` removes any filter on the `region` column, wherever the measure is being evaluated, while leaving every other active filter (the quarter, from the chart's axis) untouched. So the denominator is always "this quarter's total across every region," regardless of which single region the numerator is looking at. This is the cleaner, more idiomatic way to write a share-of-total measure than repeating explicit filters for every category, and it is genuinely safe here: `region` only ever holds `Americas`, `EMEA`, `APJ`, confirmed directly against `regional_revenue.csv`, no rollup row exists in that column to accidentally sum in.

---

## Measure 7: percent of total, segment, and why it is not the same pattern

```dax
Segment % of Total =
DIVIDE(
    [Net Revenue],
    CALCULATE([Net Revenue], segment_data[business_unit] = "Total segment")
)
```

**Why this one does not use `ALL(segment_data[business_unit])`.** That would look like the natural twin of Measure 6, and it would be wrong. `segment_data[business_unit]` is not a flat list of leaves, it holds three hierarchy levels in one column: leaf units, the `Personal Systems`/`Printing` subtotals, and the `Total segment` grand total itself. Removing the filter with `ALL()` would sum all three levels together, exactly trap 1 from `docs/calculation_layer.md` (the unconstrained-sum example that comes out three times too large). So instead of removing the filter, this measure **repoints** it: `CALCULATE` overrides `business_unit` to the single named row `"Total segment"`, regardless of whatever row the outer chart context supplies. Numerator and denominator never touch a leaf-plus-subtotal double count, because the denominator only ever reads one row.

**The pairing is deliberate.** Two measures that answer the same kind of question (Measure 6, Measure 7) end up using two different DAX techniques, `ALL()` filter removal versus an explicit filter override, because the two source columns have genuinely different shapes: one flat, one hierarchical. That is a better interview answer than reaching for the same pattern twice, it shows the pattern was chosen by looking at the data, not memorised.

Verifies against numbers already published elsewhere in this repo: `Printing / Total segment` at Q3 FY26 is 3,912 / 15,679 = 25.0%, the same figure already in `deck/printing_segment_briefing.html` and `docs/dashboard_notes.md`. If this measure ever produced a different percentage for the same quarter, that would be the signal something upstream had drifted, not a rounding quirk to wave off.

**Outcome, 2026-09-02: neither this nor Measure 6 ever worked, and the cause was never identified.** Both reasoning above is correct, and both formulas match this pattern exactly when typed into Power BI. In practice, every version tried, including this one, including a fresh version built with no dependency on `Regional Revenue` or `Net Revenue` at all, returned the same constant for every category rather than a real ratio: sometimes exactly `1.0`, once exactly `65.33%` (the correct Supplies/Printing ratio, but for the sum across all eleven quarters rather than the filtered one), once exactly `3.00` (the correct trap-1 ratio, all nine business-unit rows summed against `Total segment`, meaning the category filter reached the underlying `SUM` but not the `DIVIDE` wrapper around it). A table visual confirmed the base measures (`Regional Revenue`, `Net Revenue`) sliced correctly by category on their own. Never got further than that in the time available. Both percentage visuals in the finished report read the original `dim_date` precomputed share columns instead (already verified against source in the first Power BI pass), not these measures. Left here rather than deleted, because a DAX approach that was tried, understood, and abandoned under time pressure is worth being able to describe honestly, and is a better interview answer than a working measure with no story behind it.

---

## Measure 8: fixing a live percent-format bug

```dax
Operating Margin =
CALCULATE(
    SUM(segment_data[value]),
    segment_data[metric] = "operating_margin_pct"
)
```

Built to fix a real bug in the finished report, not drafted speculatively like Measures 1 to 7. A Card visual summing `segment_data[value]` filtered to `operating_margin_pct` showed **780.00%**. The `value` column stores margin as `7.8` meaning 7.8%, and Power BI's built-in Percentage number format assumes a decimal fraction, so it multiplied by 100 on top of a number that was already a whole percent, the identical trap already documented in `docs/dashboard_notes.md` for the Looker Studio scorecard, same convention mismatch, second tool.

**Why a measure plus a custom format string, not a calculated column.** The `value` column is shared across every metric, revenue, margin, earnings, growth rates, all in one column. Dividing it by 100 anywhere would have silently broken every revenue and earnings figure that reads the same column. Isolating the fix inside a measure that only ever touches `operating_margin_pct` rows keeps it from leaking anywhere else. The format string itself, `0.0"%"`, appends a literal percent character to the number as printed rather than multiplying it, so `7.8` displays as `7.8%` with no arithmetic involved at all.

---

## Verification

Put a table visual on the page with `fiscal_quarter` from `dim_date` and the measures below. All of these are confirmed built and correct in the finished report, as of 2026-09-02.

| Check | Expected |
|---|---|
| `Printing Revenue`, Q3 FY26 | 3,912 |
| `Net Revenue` filtered to Total segment, Q3 FY26 | 15,679 |
| `Supplies Share of Printing`, Q3 FY26 | 64.8% |
| `Regional Revenue`, Q3 FY26 | 15,677 |
| `Operating Margin` filtered to Total segment, Q3 FY26 | 7.8% |

`Net Revenue` and `Regional Revenue` differ by 2 (15,679 vs 15,677): regional data sums to total **net** revenue while `Total segment` sums the business units, and the gap is HP's small "Other" reconciling line. That is expected, documented in `docs/data_quality_notes.md`, and is exactly why check 7 in `analysis/validate.py` uses a tolerance rather than requiring an exact match.

**`Region % of Total` and `Segment % of Total` are not in this table.** They were built to the same target values documented under Measure 7 above (Americas 41.4%, EMEA 33.0%, APJ 25.6%, Printing 25.0%, Personal Systems 75.0%), but never actually produced them, see the outcome note. Both are unused in the finished report.

**If Power BI and the spreadsheet disagree for the same filters, the spreadsheet is right.** Every figure in it has been verified against HP's own filings. The cause is almost always one of the two traps, except where noted above as an unresolved DAX issue rather than a data issue.
