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
for r in rows:
    if r["metric"] == "net_revenue":
        rev[(r["fiscal_quarter"], r["reporting_basis"])][r["business_unit"]] = int(r["value"])

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

if failures:
    print(f"{len(failures)} FAILURES")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print(f"All checks passed across {len(rev)} quarter/basis combinations, {len(rows)} rows.")
