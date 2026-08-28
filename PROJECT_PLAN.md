# HP Printing Segment Analysis — Project Plan

**Purpose:** Refresh Excel/Sheets and BI skills against real, role-relevant data, and produce a defensible artifact for the HP hiring-manager interview (Graduate BI Analyst, EMEA Home Print Category).

**Hard constraint:** every number must trace to a public HP source. No estimates presented as reported figures. If a number can't be sourced, it doesn't go in.

---

## Framing (read this before building anything)

This analyses HP's own reported numbers, for HP. The category team knows these figures far better than I will after a weekend. So the artifact is **a demonstration of method, not a delivery of insight.**

- Correct framing: "I used your public reporting to practice the kind of analysis this role does, and here's how I'd approach it."
- Wrong framing: "Here are my strategic recommendations for your business."
- The deck ends on **questions I'd want to ask**, not conclusions I'm confident in.

---

## Environment sequencing

Currently on Mac (no Excel, no Power BI). Windows laptop available after that. This ordering is deliberate, not a workaround:

| Phase | Tool | Machine |
|---|---|---|
| 1. Extraction | Google Sheets | Mac |
| 2. Formula layer | Google Sheets | Mac |
| 3a. First dashboard | Looker Studio | Mac |
| 3b. Rebuild | Power BI Desktop | Windows |
| 4. Deck | Slides or PowerPoint | Either |

Rebuilding the same model in two BI tools is a better talking point than one, it shows the model is understood rather than the tool memorised.

---

## Phase 1 — Data extraction

**Source priority (cleanest first):**
1. **Press releases.** State figures in plain prose: "Printing net revenue was $4.3 billion, down 4%... Consumer Printing net revenue was down 9%." Fastest reliable route.
2. **SEC 10-Q `Financial_Report.xlsx`.** Auto-generated, real spreadsheet rows, segment and regional revenue. Best for exact figures.
3. **Earnings presentation PDFs.** Good for the segment mix percentages; regional trend is a chart image, so read carefully or cross-check against the above.

**Ticker warning:** HPQ = HP Inc. (correct). HP on NYSE = Helmerich & Payne, unrelated oil and gas. Verify ticker on anything pulled.

**Target table shape (one tidy long table, not a wide one):**

| fiscal_quarter | fiscal_year | business_unit | metric | value | unit | source_url |
|---|---|---|---|---|---|---|

- `business_unit`: Consumer Printing / Commercial Printing / Supplies / Printing (total) / Personal Systems / Total HP
- `metric`: net_revenue / yoy_growth_pct / yoy_growth_cc_pct / operating_margin_pct / units_yoy_pct
- Separate table, same shape, for region: Americas / EMEA / APJ

**`source_url` per row is not optional.** It's what makes every figure defensible live, and it's the honest-sourcing habit the whole CV rests on.

**Quarters to cover:** originally scoped as Q3 FY25 through Q3 FY26. Extended in practice to Q1 FY24 through Q3 FY26 (11 quarters, both reporting bases where the realignment applies), because reconciling the restatement properly required the full FY24 and FY25 history rather than just the four most recent quarters. 222 rows in `data/processed/segment_data.csv` as of this commit: net revenue by business unit, segment operating margin, and earnings before taxes, each with a source URL.

---

## Phase 2 — Formula layer (Sheets)

Deliberately practice, don't just get the answer:

- **SUMIFS** — revenue by business unit and quarter (multi-criteria aggregation)
- **XLOOKUP** — pull prior-year quarter's value alongside current, to compute y/y independently and check it against HP's reported growth figure
- **PivotTable** — business unit by quarter
- **FILTER / UNIQUE** — already defensible, use them for the quarter and unit lists

**Validation step worth doing:** compute y/y growth from the revenue figures and compare against HP's stated growth. Where they differ, work out why (constant currency vs. nominal, rounding). Noticing and explaining that gap is exactly the reconciliation instinct worth showing.

---

## Phase 3 — Dashboard

**Data model:** a proper date/quarter dimension table related to the fact table. Having a real relationship to explain is the point, a single flat table teaches nothing.

**Measures (understand each, don't paste blindly):**
- Total revenue
- Y/Y growth %
- Supplies share of Printing revenue (the mix-shift story)
- One `CALCULATE`-based measure, since filter-context manipulation is the concept most likely to be probed

**Visuals (4, resist adding more):**
1. Printing revenue trend by business unit over the quarters
2. EMEA vs. Americas vs. APJ
3. Supplies share of Printing over time
4. KPI cards: latest quarter revenue, y/y growth, operating margin

---

## Phase 4 — Deck (5 to 6 slides)

Follows the case-study structure: question → data → what it shows → what I'd ask next.

1. What I set out to practise and why (method framing, explicitly)
2. Data and sources (name the public sources, show the sourcing discipline)
3. Printing mix: Consumer / Commercial / Supplies
4. Regional view, EMEA focus
5. What I noticed, stated as observations, not conclusions
6. What I'd want to ask the team, the questions the public data can't answer

Slide 6 is the most important one. It's where humility and genuine curiosity land.

---

## Phase 5 — Rehearse

90-second spoken walkthrough. Out loud, recorded once, listened back. Same discipline as the voice-interview prep.

---

## Definition of done

- [ ] Every figure has a source URL
- [ ] Y/Y computed independently and reconciled against HP's reported figures
- [ ] Model rebuilt in Power BI, not just Looker
- [ ] Deck ends on questions, not recommendations
- [ ] Walkthrough rehearsed aloud
- [ ] Repo public, README explains what and why
- [ ] Can defend every single element live, anything I can't goes in the limitations section

---

## Scope cut, if the interview lands early

Drop to three quarters and three visuals. Cut Phase 3a (Looker) and go straight to Power BI. **Do not cut** the sourcing discipline or the deck's final slide, those carry the most weight.
