# Spreadsheet Notes

Notes on the formula layer in `spreadsheet/formula_layer.xlsx`, built by hand in Google Sheets, downloaded as .xlsx for the repo.

---

## 1. The `matrix` tab (C1)

Revenue by business unit and quarter, on a toggleable reporting basis. Verified 2026-08-29 against the same source data `analysis/validate.py` checks:

- Every value cell is `SUMIFS`, pinned on `business_unit` (`$D:$D, $A4`) **and** `reporting_basis` (`$I:$I, $A$1`), which is what avoids both double-counting traps documented in `docs/data_quality_notes.md`.
- Quarters run chronologically (Q1 FY24 through Q3 FY26) via a sorted date row driving `XLOOKUP` for the labels, not the raw row order in the source file.
- Spot-checked against source: Q3 FY26 Printing = 3,912, Q3 FY26 Total segment = 15,679. Both exact.
- Toggling `A1` correctly zeroes the three FY26 columns under `as previously reported`, since that basis doesn't exist for FY26.

## 2. A real gotcha: Google Sheets array functions don't survive the trip to Excel

Downloading a Google Sheet as `.xlsx` converts every Sheets-native array formula (`FILTER`, `UNIQUE`, `SORT`, `TRANSPOSE` used together) into a wrapper called `__xludf.DUMMYFUNCTION`. That wrapper stores the *last computed value* as a frozen fallback, but the formula itself will not recalculate in real Microsoft Excel, because Excel doesn't have Google Sheets' `FILTER`/`UNIQUE`/`SORT` engine underneath the wrapper.

**What this means concretely for `matrix`:**

- Row 2 (the sorted quarter-end dates, built with `TRANSPOSE(SORT(UNIQUE(FILTER(...))))`) and column A (the business unit list, built with `UNIQUE(FILTER(...))`) are **frozen** in the Excel file. They'll display correctly as-is, but if the underlying `segment_data` tab changes (a new quarter added, for instance), these two ranges will not update in Excel. They would need to be rebuilt by hand, or the workbook rebuilt from Sheets again.
- The `SUMIFS` body (every value cell, rows 4 through 12) and the `XLOOKUP` in row 3 are **fully portable**. Both are native Excel functions with no Sheets dependency, and will recalculate normally on any change.

**Practical takeaway for the Power BI weekend:** don't build further Excel-only work on top of the frozen row 2 / column A ranges expecting them to stay live. Either keep doing the array-formula work in Sheets and re-download when it changes, or rebuild those two specific ranges natively in Excel (`FILTER`/`UNIQUE`/`SORT` do exist in modern Excel too, just not through this particular export path).

## 3. A cosmetic non-issue, noted so it isn't mistaken for a bug

`A1` in the workbook reads `FY26 Realigned` (capital R). The data itself uses `FY26 realigned` (lowercase r). `SUMIFS` text matching is case-insensitive in both Sheets and Excel, so every value cell still matches correctly, confirmed by the spot-checks above. Left as-is since it doesn't affect the numbers, but worth knowing if a stricter, case-sensitive tool is ever used against this same pattern.

## 4. The `yoy` tab (C2)

Independently computed y/y growth, reconciled against HP's own published percentage, for all eight business units (Corporate Investments excluded, since HP itself discloses it as "NM", not meaningful) at Q3 FY26 vs Q3 FY25. Verified 2026-08-29:

- `Current value` and `Prior value` are both `SUMIFS`, same four-criteria pattern as `matrix`, one pulling the named quarter and the other pulling the prior-year quarter.
- `Prior year qtr` (column D) is typed in directly rather than derived with a formula. That's a deliberate simplification for a tab scoped to one fixed quarter; it just means the column won't auto-update if `B` is later changed to a different quarter.
- `HP Published` (column G) is transcribed by hand from HP's Q3 FY26 press release narrative, the same source already verified live against the page earlier in this project.
- All eight rows flag `OK`. Largest gap is Commercial PS at 0.19 points (computed 21.93% against HP's rounded 22%), well inside the tolerance, consistent with HP rounding narrative growth to the nearest whole percent.
- `Printing` (row 8) reads 3,912 for the current value and 4,002 for the prior year, matching `matrix` and the source exactly. `Total segment` (row 9) reads 15,679, also matching.

## 5. The `derived` tab (C3)

Four blocks, verified 2026-08-30 against source and against the other tabs:

- **TTM.** The two earliest columns (Q2 FY24, Q3 FY24) are genuine incomplete windows, left in rather than deleted, since the dataset has no prior-year quarter to complete them. Q1 FY24 is left blank entirely rather than computing a meaningless one-quarter "trailing twelve months." First trustworthy value is Q4 FY24 (17,356); Q3 FY26 reads 16,579, matching the figure already verified in `docs/data_quality_notes.md` §8.
- **Share of parent.** Both rows reference `matrix` directly rather than re-querying `segment_data`, so they inherit `matrix`'s defense against both double-counting traps for free. Q3 FY26: Supplies is 64.8% of Printing, Printing is 25.0% of Total segment.
- **Growth contribution decomposition.** References `yoy` rather than `segment_data`, same reasoning. The three contributions sum to -0.02249, an exact match to `yoy!F8` (Printing's own computed y/y), confirming the parts add to the whole.
- **Implied operating profit.** Twelve rows, the six quarters HP discloses margin for, times Printing and Personal Systems. All twelve flag `OK`. Largest absolute gap is Personal Systems Q3 FY26 (541.3 implied vs 537 reported, tolerance ±5.9), still within the margin-rounding tolerance and the same pair `analysis/validate.py` check 6 already verifies programmatically.
