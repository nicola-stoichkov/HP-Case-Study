# The Calculation Layer: Two Traps and How Every Tab Defends Against Them

This is a single reference for something that is otherwise scattered across `data_quality_notes.md` and `spreadsheet_notes.md`: the two ways this dataset silently produces a plausible, wrong number if aggregated carelessly, and exactly how `matrix`, `yoy` and `derived` are each built to avoid them.

Both traps share the same shape. Neither one throws an error. Neither one looks wrong. Each produces a number with a sensible shape and a believable trend, and it is simply not the right number. That is the failure mode worth taking seriously, because it is the one that survives review and reaches a slide.

---

## Trap 1: mixed granularity, leaf rows next to their own subtotal

`segment_data.csv`'s `business_unit` column holds two different kinds of row at once. Supplies, Commercial Printing and Consumer Printing are leaves, the actual reported components. Printing is their subtotal. Total segment is the subtotal of the subtotals (Printing plus Personal Systems plus Corporate Investments). All three levels sit in the same column, because that is how HP itself publishes the table.

Sum the `value` column for one quarter without constraining `business_unit`, and every dollar is counted at every level it appears in: once as a leaf, once inside its segment subtotal, once inside the grand total.

**Worked example, Q3 FY26, verified against source:**

| What's summed | Result |
|---|---|
| All nine business units, unconstrained | 47,037 |
| The true figure, `Total segment` | 15,679 |
| Ratio | exactly 3.0x |

Exactly three, because there are exactly three levels of hierarchy in this particular table. A chart built on the unconstrained sum would look completely normal in shape. It would simply be three times too large.

## Trap 2: mixed reporting basis, two published figures for one quarter

Effective Q1 FY26, HP moved its Print-as-a-Service business out of Corporate Investments and into Printing, and restated the affected prior periods on an as-if basis (full detail in `data_quality_notes.md` §1). The result: the same fiscal quarter has two different published revenue figures, depending on which release you read. The dataset keeps both, tagged in `reporting_basis` as `FY26 realigned` or `as previously reported`, because comparing them deliberately is what reveals the restatement. Adding them together is meaningless.

**Worked example, Q3 FY25 Printing:**

| Basis | Revenue |
|---|---|
| FY26 realigned | 4,002 |
| As previously reported | 3,986 |
| Summed by accident | 7,988 |

Roughly double, not exact, because the two bases differ by a small reclassification rather than a clean multiple. This one is the more dangerous of the two, because only the eight quarters that exist on both bases are affected. The three FY26 quarters have only one basis, so a chart built on the unconstrained sum would be correct at the recent end and roughly doubled at the older end. That reads as dramatic growth that never happened, which is a worse failure than being uniformly wrong, since a uniform error is at least easy to spot.

---

## How each tab defends against both, specifically

**`matrix`** (C1). Every value cell is a four-criteria `SUMIFS`, and two of the four criteria exist purely to defend against these two traps: `business_unit` is pinned to one row at a time (defends trap 1), and `reporting_basis` is pinned to the selector cell `$A$1` (defends trap 2). Toggling `$A$1` to `as previously reported` correctly blanks the three FY26 columns, since that basis does not exist for those quarters, confirming the pin is live rather than decorative.

**`yoy`** (C2). Same four-criteria pattern, run twice per row: once against the named quarter, once against the prior-year quarter. Both pulls are pinned on `business_unit` and hardcoded to `reporting_basis = "FY26 realigned"`, since a y/y comparison spanning the restatement boundary must use one consistent basis throughout, not a toggle. That is a deliberate choice, not a missed generalisation.

**`derived`** (C3), three different defenses depending on the block:
- **TTM** hardcodes `reporting_basis = "FY26 realigned"` rather than reading a toggle, for the same reason as `yoy`: a rolling twelve-month window that crossed the FY25/FY26 boundary on a mixed basis would blend two different definitions of Printing revenue into one sum, and the error would be invisible in the shape of the trend line.
- **Growth contribution decomposition** does not requery `segment_data` at all. It reuses the already-pinned `yoy` values directly, so it inherits `yoy`'s defense against both traps rather than needing its own.
- **Implied operating profit** pins `business_unit`, `metric`, and `reporting_basis` on both the revenue pull and the margin pull, since margin and EBT exist only for Printing and Personal Systems, never for a leaf-vs-rollup pair that could be confused with each other, and never on the previously-reported basis for FY26 quarters.

---

## Why this is worth more than the numbers it produces

Both traps are structural, not accidental. They exist because the source data legitimately contains hierarchy (trap 1) and legitimately contains a restatement (trap 2), and a tidy long-format table has no way to express "don't sum these two rows together" except through discipline in every formula that touches it. `analysis/validate.py` checks 1, 2, 3 and 5 exist specifically to catch a formula that got this wrong; `spreadsheet_notes.md` records the same defense verified independently in each tab, by hand, against source.
