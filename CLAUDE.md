# CLAUDE.md — context for Claude Code sessions on this repo

## What this is

A personal analysis project built to prepare for an interview for the **Graduate Business Intelligence Analyst, EMEA Home Print Category** role at HP. It analyses HP Inc.'s publicly reported Printing segment performance using the company's own earnings materials.

It is a **skills-demonstration artifact**, not a commercial deliverable.

## Standing rules (these override convenience)

1. **Every figure must trace to a public source URL.** No estimated, interpolated, or remembered numbers presented as reported figures. If a number can't be sourced, it doesn't go in the dataset.
2. **Never state planned work as done.** Applies to the README, commit messages, and the deck. "In progress" stays "in progress."
3. **No em dashes or en dashes in any written output** (README, deck, docs). Hard rule. Use commas, colons, or restructure.
4. **Method framing, not insight framing.** This analyses HP's numbers for HP. Never write as if delivering strategic recommendations to a company that knows its own data far better. Frame as practising the analysis, ending in questions.
5. **The human does the analytical work.** Claude Code's role here is scaffolding: data structuring, validation scripts, DAX drafting for review, deck generation. Not doing the analysis and handing over conclusions.
6. **HPQ is HP Inc.** HP on NYSE is Helmerich & Payne, an unrelated oil and gas company. Always verify ticker on any source.

## What Claude Code can and cannot do here

**Can:** parse press releases and SEC filings into structured data, write validation scripts (reconcile computed y/y against reported y/y), generate the Excel/CSV source file, draft DAX measure definitions with explanations, build the .pptx, maintain docs.

**Cannot:** build the .pbix file, or write formulas into the Sheets/Excel formula layer. Both are GUI work done by hand, and that's intentional, it's the part that does the actual skill refresh. Claude Code's role there is limited to guidance (explaining the formula pattern, checking the resulting numbers against source) and, once a workbook is handed over, validating it.

## Data sources

- Press releases: cleanest prose figures, use first
- SEC 10-Q `Financial_Report.xlsx` (EDGAR, ticker HPQ): exact figures as spreadsheet rows
- Earnings presentation PDFs (`s203.q4cdn.com`): segment mix; regional data is a chart image, cross-check it

Quarters: Q1 FY24 through Q3 FY26 (11 quarters), extended beyond the original Q3 FY25 to Q3 FY26 scope because reconciling the FY26 segment realignment required the full FY24 and FY25 history. Q3 FY26 reported 26 Aug 2026.

## Repo conventions

- `data/raw/` — downloaded source files, unmodified
- `data/processed/` — the tidy long-format tables
- `analysis/` — scripts, validation
- `spreadsheet/` — Sheets/Excel formula layer, built by hand
- `dashboards/` — .pbix and exports
- `deck/` — presentation
- `docs/` — notes, decisions, limitations

Commit messages: plain and factual. The commit history is itself part of what the repo demonstrates, so it should read like real incremental work, because it is.

## Honesty about AI assistance

This project uses AI assistance and says so plainly in the README. The framing that has to stay accurate: the analysis, the judgment, and the validation are the author's; AI helps with structuring and scaffolding. That's the same honest line used throughout the author's CV, and it must not drift.
