# HP Printing Segment Analysis

An analysis of HP Inc.'s publicly reported Printing segment performance, built as preparation for an interview and as a way to work with data that's genuinely close to the role.

**Status: in progress.**

## What this is

HP reports its Printing segment split three ways, Consumer Printing, Commercial Printing and Supplies, and reports revenue across three regions, Americas, EMEA and APJ. This project pulls those figures from HP's own quarterly reporting, reconciles them, and builds a dashboard and short deck on top.

It's a demonstration of method rather than a delivery of insight. HP's own teams know these numbers far better than any outside analysis of public filings could. What this shows is how I approach the work: sourcing every figure, validating computed numbers against reported ones, and being explicit about what public data cannot answer.

## Data sources

All figures come from HP Inc.'s public reporting:

- Quarterly press releases
- SEC filings (10-Q, 10-K, ticker HPQ)
- Quarterly earnings presentations

Every row in the processed dataset carries the URL it came from. Where a figure computed here differs from a figure HP reports (for example nominal versus constant-currency growth), the difference is documented rather than smoothed over.

Note on ticker: HPQ is HP Inc. HP on the NYSE is Helmerich & Payne, an unrelated company.

## Structure

```
data/raw/          source files as downloaded
data/processed/    tidy tables, one row per figure, with sources
analysis/          extraction and validation scripts
spreadsheet/       Sheets/Excel formula layer (SUMIFS, XLOOKUP, y/y reconciliation)
dashboards/        Power BI file and exports
deck/              summary presentation
docs/              notes, decisions, limitations
```

## Tools

Google Sheets and Excel for the extraction and formula layer, Looker Studio and Power BI for the dashboards, Python for validation.

Built with AI assistance for structuring and scaffolding. The analysis, the judgment calls and the validation are mine.

## Limitations

Stated up front rather than left to be found:

- Public segment reporting only. No internal, SKU-level or country-level data.
- HP reports Home Printing within Consumer Printing, so it cannot be isolated from public filings.
- Regional figures in the earnings presentations appear as charts rather than tables, so those values are read from the charts and cross-checked against the filings where possible.
- Eleven fiscal quarters (Q1 FY24 through Q3 FY26), net revenue by business unit on both the pre- and post-realignment reporting basis, plus segment operating margin and earnings before taxes where HP discloses them. Still public segment data, not a substitute for trend claims a company could make from its own internals.

## Author

Nicola Stoichkov
[nicola-stoichkov.github.io](https://nicola-stoichkov.github.io)
