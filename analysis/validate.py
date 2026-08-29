#!/usr/bin/env python3
"""
Validation checks for segment_data.csv.

These are assertions, not spot checks. If a figure was mistyped during
transcription, one of these should fail. Run after any change to the dataset.
"""
import csv, sys
from collections import defaultdict

rows = list(csv.DictReader(open("../data/processed/segment_data.csv")))
rev = defaultdict(dict)
marg = defaultdict(dict)
ebt = defaultdict(dict)
for r in rows:
    k = (r["fiscal_quarter"], r["reporting_basis"])
    if r["metric"] == "net_revenue":
        rev[k][r["business_unit"]] = int(r["value"])
    elif r["metric"] == "operating_margin_pct":
        marg[k][r["business_unit"]] = float(r["value"])
    elif r["metric"] == "earnings_before_taxes":
        ebt[k][r["business_unit"]] = int(r["value"])

failures = []

# 1. The three Printing business units must sum to reported Printing.
for k, v in rev.items():
    s = v["Supplies"] + v["Commercial Printing"] + v["Consumer Printing"]
    if s != v["Printing"]:
        failures.append(f"Printing components {s} != reported {v['Printing']} for {k}")

# 2. Segments must sum to total segment net revenue.
for k, v in rev.items():
    s = v["Personal Systems"] + v["Printing"] + v["Corporate Investments"]
    if s != v["Total segment"]:
        failures.append(f"Segment sum {s} != total {v['Total segment']} for {k}")

# 3. Consumer PS + Commercial PS must equal Personal Systems.
for k, v in rev.items():
    s = v["Consumer PS"] + v["Commercial PS"]
    if s != v["Personal Systems"]:
        failures.append(f"PS components {s} != reported {v['Personal Systems']} for {k}")

# 4. Our computed restatement delta must equal HP's own published CHANGE column.
#    Source: restatement tables in the Q1 FY26 press release.
HP_PUBLISHED_PRINTING_DELTA = {
    "Q1 FY24": 0, "Q2 FY24": 1, "Q3 FY24": 7, "Q4 FY24": 10,
    "Q1 FY25": 11, "Q2 FY25": 16, "Q3 FY25": 16, "Q4 FY25": 19,
}
for q, expected in HP_PUBLISHED_PRINTING_DELTA.items():
    calc = rev[(q, "FY26 realigned")]["Printing"] - rev[(q, "as previously reported")]["Printing"]
    if calc != expected:
        failures.append(f"Printing restatement delta {calc} != HP published {expected} for {q}")

# 5. The restatement must be revenue-neutral at total segment level.
for q in HP_PUBLISHED_PRINTING_DELTA:
    a = rev[(q, "FY26 realigned")]["Total segment"]
    b = rev[(q, "as previously reported")]["Total segment"]
    if a != b:
        failures.append(f"Total segment changed across bases for {q}: {a} vs {b}")

# 6. Revenue x operating margin must reproduce reported earnings before taxes.
#    These are two independent disclosures of the same thing, so they have to
#    agree. They never agree exactly, because HP publishes margin rounded to
#    one decimal place: a printed 18.1% is really anything in [18.05, 18.15).
#    The resulting tolerance is revenue * 0.05%, which SCALES WITH REVENUE.
#    A fixed threshold would be wrong in both directions, wrongly failing
#    Personal Systems (large revenue, so large absolute rounding error) and
#    wrongly passing small units where a real error would hide under it.
checks_6 = 0
for k, units in marg.items():
    for unit, margin_pct in units.items():
        if unit not in ebt.get(k, {}) or unit not in rev.get(k, {}):
            continue
        revenue = rev[k][unit]
        implied = revenue * margin_pct / 100
        tolerance = revenue * 0.0005
        if abs(implied - ebt[k][unit]) > tolerance:
            failures.append(
                f"Implied profit {implied:.1f} vs reported {ebt[k][unit]} "
                f"for {unit} {k}, gap exceeds rounding tolerance {tolerance:.1f}")
        checks_6 += 1

# 7. Cross-source check: regional revenue comes from the SEC filings, segment
#    revenue from the press releases. They are independent transcriptions of
#    the same company, so the three regions must reconcile to total segment
#    net revenue. They differ only by HP's small "Other" reconciling line,
#    which runs 0 to 2 million, so a 5 million tolerance is generous but still
#    tight enough to catch a real transcription error.
#    This matters most for Q4, where the regional figures are DERIVED by
#    subtracting nine months from the full year rather than reported directly.
checks_7 = 0
try:
    regional = list(csv.DictReader(open("../data/processed/regional_revenue.csv")))
except FileNotFoundError:
    regional = []
    print("note: regional_revenue.csv not present, skipping check 7")

reg = defaultdict(dict)
for r in regional:
    reg[r["fiscal_quarter"]][r["region"]] = int(r["value"])

for q, v in reg.items():
    if len(v) != 3:
        failures.append(f"Regional data for {q} has {len(v)} regions, expected 3")
        continue
    total_segment = rev.get((q, "FY26 realigned"), {}).get("Total segment")
    if total_segment is None:
        continue
    if abs(sum(v.values()) - total_segment) > 5:
        failures.append(
            f"Regional sum {sum(v.values())} does not reconcile to segment "
            f"total {total_segment} for {q}")
    checks_7 += 1

if failures:
    print(f"{len(failures)} FAILURES")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print(f"All checks passed across {len(rev)} quarter/basis combinations, "
      f"{len(rows)} segment rows and {len(regional)} regional rows.")
print(f"  check 6: {checks_6} implied-profit reconciliations within rounding tolerance")
print(f"  check 7: {checks_7} quarters where regional and segment sources reconcile")
