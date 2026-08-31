# Project Board

The working backlog for this project. Committed before the work it describes, so the git history shows planning ahead of execution rather than a backlog reconstructed afterwards.

Mirrored as a GitHub Project board. Items convert to issues when started, and the commit that finishes an item closes its issue.

**Status vocabulary:** `Backlog` not started, `In progress` started, `Done` finished and committed. Nothing is marked `Done` before it is committed.

---

## Workstream A: project setup

| ID | Task | Status | Acceptance criteria |
|---|---|---|---|
| A1 | Publish project board and backlog | Done | This file committed, every task carries acceptance criteria |
| A2 | Create public GitHub Project board | In progress | Board public, linked to repo, backlog seeded, columns Backlog / In progress / Done |
| A3 | Convert active items to issues and link commits | Backlog | At least one issue closed by a commit message |

## Workstream B: data

| ID | Task | Status | Acceptance criteria |
|---|---|---|---|
| B1 | Extract segment data from HP quarterly press releases | Done | 11 fiscal quarters, both reporting bases, every row carries a source URL |
| B2 | Validate segment dataset against published source | Done | 5 assertions pass, including reconciliation against HP's own published restatement deltas. Triple checked the methodology of Claude's data retrieving and actual numbers. Source of Q2 and Q3 for FY26 needed changes (globenewswire link was bot-blocked, swapped for HP's own investor.hp.com mirror of the same release). Committed. |
| B3 | Add revenue times margin reconciliation check | Done | Check 6 in `validate.py`, tolerance scaled to revenue rather than fixed |
| B4 | Extract regional revenue from SEC filings | Done | Americas, EMEA and APJ for all 11 quarters, table located by name rather than hardcoded file number |
| B5 | Derive Q4 regional figures by subtraction | Done | Q4 rows marked `source_type = computed`, method documented |
| B6 | Add cross-source reconciliation check | Done | Check 7 in `validate.py`, regional (SEC) reconciled against segment (press release) |
| B7 | Add hardware units and constant currency figures | Done | Sourced from press release narrative, enabling price and mix and FX proxies. Issue #20. |

## Workstream C: calculation layer

| ID | Task | Status | Acceptance criteria |
|---|---|---|---|
| C1 | Build revenue matrix by business unit and quarter | Done | `SUMIFS` pinned on both business unit and reporting basis, quarters in chronological order. Built by hand in Sheets, validated against source: Q3 FY26 Printing 3,912, Total segment 15,679, both exact. Issue #10. |
| C2 | Build growth layer and reconcile against HP figures | Done | Y/Y computed independently, compared against HP's published rate, differences flagged. Eight business units, Q3 FY26 vs Q3 FY25, all flag OK. Issue #11. |
| C3 | Build derived metrics | Done | TTM, share of parent, growth contribution decomposition, implied operating profit. All 12 implied-profit rows flag OK, decomposition sum matches yoy!F8 exactly. Issue #12. |
| C4 | Document the calculation layer | Done | Both double counting traps written up in `docs/calculation_layer.md`, with worked numbers from the tabs. Issue #13. |

## Workstream D: dashboards

| ID | Task | Status | Acceptance criteria |
|---|---|---|---|
| D1 | Build date and business unit dimension tables | Backlog | Fiscal quarters sort chronologically, reported subtotals flagged so they cannot be summed with leaf rows |
| D2 | Build Looker Studio dashboard | Backlog | Four visuals, totals agree with the spreadsheet layer |
| D3 | Rebuild the model in Power BI | Backlog | Same figures as Looker for the same filters |
| D4 | Draft and review DAX measures | Backlog | Includes at least one `CALCULATE` measure, each explained rather than pasted |

## Workstream E: presentation

| ID | Task | Status | Acceptance criteria |
|---|---|---|---|
| E1 | Draft the deck | Backlog | Six slides, ends on questions rather than recommendations |
| E2 | Rehearse the walkthrough aloud | Backlog | 90 seconds, recorded once and listened back |

## Out of scope, deliberately

| ID | Task | Rationale |
|---|---|---|
| X1 | Competitor comparison (Canon, Epson, Brother, Lexmark) | All report in yen on different fiscal calendars with different segment definitions. Doing it badly would be worse than not doing it. Named here because deciding what not to build is part of the method. |
| X2 | EMEA Printing revenue specifically | Not a scope decision. HP discloses revenue by region for the company as a whole and by business unit globally, but never the two crossed. This cannot be derived from public filings at any level of effort. |

---

## Known limitations carried throughout

Stated here rather than discovered late:

- Home Printing sits inside Consumer Printing in HP's reporting and cannot be isolated
- Q4 regional figures are derived by subtraction, not reported directly
- Eleven quarters is enough to demonstrate method, not enough to support strong trend claims
- Everything is transcribed or parsed from public filings, so the validation layer is what stands between a transcription error and a wrong chart
