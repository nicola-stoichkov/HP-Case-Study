# DAX Measures

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

## Verification

Put a table visual on the page with `fiscal_quarter` from `dim_date` and the measures above.

| Check | Expected |
|---|---|
| `Printing Revenue`, Q3 FY26 | 3,912 |
| `Net Revenue` filtered to Total segment, Q3 FY26 | 15,679 |
| `Supplies Share of Printing`, Q3 FY26 | 64.8% |
| `Regional Revenue`, Q3 FY26 | 15,677 |

Note the last two differ by 2: regional data sums to total **net** revenue while `Total segment` sums the business units, and the gap is HP's small "Other" reconciling line. That is expected, documented in `docs/data_quality_notes.md`, and is exactly why check 7 in `analysis/validate.py` uses a tolerance rather than requiring an exact match.

**If Power BI and the spreadsheet disagree for the same filters, the spreadsheet is right.** Every figure in it has been verified against HP's own filings; the Power BI model has not been checked against anything yet. The cause is almost always one of the two traps.
