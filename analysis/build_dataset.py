#!/usr/bin/env python3
"""
Build the HP segment dataset in long format from figures transcribed from
HP Inc.'s quarterly press releases.

Most figures below were read from the SEGMENT/BUSINESS UNIT INFORMATION
tables. Constant-currency growth and hardware unit growth (CC_GROWTH,
UNITS_GROWTH, YOY_NOMINAL) come instead from the narrative prose in each
release, since HP never tables those figures. Nothing here is estimated;
everything is either a table cell or a number printed in running text,
and each block of constants says which.

Note on a source quirk: HP's own restatement tables label the Q2 column
"Apr 31" in both the FY24 and FY25 blocks. April has 30 days. Treated as
April 30 here and recorded in docs/data_quality_notes.md.
"""
import csv

PR_Q3FY26 = "https://investor.hp.com/news-events/news/news-details/2026/HP-Inc--Reports-Fiscal-2026-Third-Quarter-Results/default.aspx"
# Originally the globenewswire wire release. Swapped 2026-08-29: globenewswire
# returns a bot-blocked error page in a normal browser, so it was not usable
# as a citation someone else could actually click through and check. This
# investor.hp.com URL is HP's own mirror of the identical release; the figures
# transcribed below are unchanged, only the citation improved.
PR_Q1FY26 = "https://investor.hp.com/news-events/news/news-details/2026/HP-Inc--Reports-Fiscal-2026-First-Quarter-Results/default.aspx"
PR_Q2FY26 = "https://investor.hp.com/news-events/news/news-details/2026/HP-Inc--Reports-Fiscal-2026-Second-Quarter-Results/default.aspx"

QUARTER_END = {
    "Q1 FY24": "2024-01-31", "Q2 FY24": "2024-04-30",
    "Q3 FY24": "2024-07-31", "Q4 FY24": "2024-10-31",
    "Q1 FY25": "2025-01-31", "Q2 FY25": "2025-04-30",
    "Q3 FY25": "2025-07-31", "Q4 FY25": "2025-10-31",
    "Q1 FY26": "2026-01-31", "Q2 FY26": "2026-04-30",
    "Q3 FY26": "2026-07-31",
}

UNITS = ["Commercial PS", "Consumer PS", "Personal Systems", "Supplies",
         "Commercial Printing", "Consumer Printing", "Printing",
         "Corporate Investments", "Total segment"]

# ---------------------------------------------------------------------------
# NET REVENUE, USD millions
# ---------------------------------------------------------------------------
# FY24 and FY25, both bases, from the restatement tables in the Q1 FY26 release.
# Order of quarters: Q1, Q2, Q3, Q4
REVISED = {
    "FY24": {
        "Commercial PS":         [6045, 6242, 6677, 6522],
        "Consumer PS":           [2764, 2184, 2692, 3069],
        "Personal Systems":      [8809, 8426, 9369, 9591],
        "Supplies":              [2863, 2864, 2704, 2867],
        "Commercial Printing":   [1227, 1205, 1147, 1262],
        "Consumer Printing":     [285, 300, 299, 333],
        "Printing":              [4375, 4369, 4150, 4462],
        "Corporate Investments": [2, 4, 0, 1],
        "Total segment":         [13186, 12799, 13519, 14054],
    },
    "FY25": {
        "Commercial PS":         [6645, 6786, 7036, 6971],
        "Consumer PS":           [2579, 2238, 2895, 3382],
        "Personal Systems":      [9224, 9024, 9931, 10353],
        "Supplies":              [2829, 2728, 2609, 2767],
        "Commercial Printing":   [1144, 1167, 1113, 1209],
        "Consumer Printing":     [307, 302, 280, 309],
        "Printing":              [4280, 4197, 4002, 4285],
        "Corporate Investments": [0, 0, 0, 0],
        "Total segment":         [13504, 13221, 13933, 14638],
    },
}

AS_PREVIOUSLY_REPORTED = {
    "FY24": {
        "Commercial PS":         [6045, 6242, 6677, 6522],
        "Consumer PS":           [2764, 2184, 2692, 3069],
        "Personal Systems":      [8809, 8426, 9369, 9591],
        "Supplies":              [2863, 2864, 2703, 2865],
        "Commercial Printing":   [1227, 1205, 1147, 1262],
        "Consumer Printing":     [285, 299, 293, 325],
        "Printing":              [4375, 4368, 4143, 4452],
        "Corporate Investments": [2, 5, 7, 11],
        "Total segment":         [13186, 12799, 13519, 14054],
    },
    "FY25": {
        "Commercial PS":         [6645, 6786, 7036, 6971],
        "Consumer PS":           [2579, 2238, 2895, 3382],
        "Personal Systems":      [9224, 9024, 9931, 10353],
        "Supplies":              [2826, 2725, 2604, 2761],
        "Commercial Printing":   [1144, 1167, 1113, 1209],
        "Consumer Printing":     [299, 289, 269, 296],
        "Printing":              [4269, 4181, 3986, 4266],
        "Corporate Investments": [11, 16, 16, 19],
        "Total segment":         [13504, 13221, 13933, 14638],
    },
}

# FY26 quarters, realigned basis only (no prior basis exists for these).
FY26 = {
    "Q1 FY26": {"Commercial PS": 7253, "Consumer PS": 2998, "Personal Systems": 10251,
                "Supplies": 2799, "Commercial Printing": 1105, "Consumer Printing": 283,
                "Printing": 4187, "Corporate Investments": 0, "Total segment": 14438},
    "Q2 FY26": {"Commercial PS": 7743, "Consumer PS": 2470, "Personal Systems": 10213,
                "Supplies": 2754, "Commercial Printing": 1168, "Consumer Printing": 273,
                "Printing": 4195, "Corporate Investments": 0, "Total segment": 14408},
    "Q3 FY26": {"Commercial PS": 8579, "Consumer PS": 3188, "Personal Systems": 11767,
                "Supplies": 2536, "Commercial Printing": 1101, "Consumer Printing": 275,
                "Printing": 3912, "Corporate Investments": 0, "Total segment": 15679},
}
FY26_SOURCE = {"Q1 FY26": PR_Q1FY26, "Q2 FY26": PR_Q3FY26, "Q3 FY26": PR_Q3FY26}

# ---------------------------------------------------------------------------
# SEGMENT OPERATING MARGIN, percent
# ---------------------------------------------------------------------------
OP_MARGIN = {
    "Q1 FY25": {"Personal Systems": 5.5, "Printing": 18.7, "Total segment": 9.6},
    "Q4 FY25": {"Personal Systems": 5.8, "Printing": 18.5, "Total segment": 9.3},
    "Q3 FY25": {"Personal Systems": 5.4, "Printing": 17.0, "Total segment": 8.6},
    "Q1 FY26": {"Personal Systems": 5.0, "Printing": 18.3, "Total segment": 8.7},
    "Q2 FY26": {"Personal Systems": 5.2, "Printing": 18.3, "Total segment": 8.8},
    "Q3 FY26": {"Personal Systems": 4.6, "Printing": 18.1, "Total segment": 7.8},
}
OP_MARGIN_SOURCE = {
    "Q1 FY25": PR_Q1FY26, "Q4 FY25": PR_Q1FY26, "Q3 FY25": PR_Q3FY26,
    "Q1 FY26": PR_Q1FY26, "Q2 FY26": PR_Q3FY26, "Q3 FY26": PR_Q3FY26,
}

# ---------------------------------------------------------------------------
# EARNINGS BEFORE TAXES, USD millions (FY25 both bases, FY26 realigned)
# ---------------------------------------------------------------------------
EBT_REVISED_FY25 = {
    "Personal Systems":      [507, 409, 541, 597],
    "Printing":              [801, 804, 681, 793],
    "Corporate Investments": [-18, -27, -24, -22],
}
EBT_PREV_FY25 = {
    "Personal Systems":      [507, 409, 541, 597],
    "Printing":              [810, 814, 689, 805],
    "Corporate Investments": [-27, -37, -32, -34],
}
EBT_FY26 = {
    "Q1 FY26": {"Personal Systems": 511, "Printing": 765, "Corporate Investments": -24},
    "Q2 FY26": {"Personal Systems": 530, "Printing": 767, "Corporate Investments": -29},
    "Q3 FY26": {"Personal Systems": 537, "Printing": 709, "Corporate Investments": -28},
}

# ---------------------------------------------------------------------------
# CONSTANT-CURRENCY Y/Y GROWTH and HARDWARE UNIT Y/Y GROWTH, percent
# ---------------------------------------------------------------------------
# These exist only in the narrative bullets ("Fiscal 2026 [quarter] segment
# results"), never in a table, which is exactly why they are worth having:
# they are not derivable from net_revenue, since that would require FX rates
# and unit counts this project has no other access to. Each release narrates
# only its own current quarter against the same quarter a year earlier, so
# coverage is the three FY26 quarters where the release itself was fetched.
#
# Two things HP does that this transcription preserves rather than smooths:
# - Some quarters print "flat" instead of a number. Recorded as 0, since
#   that is what "flat" means at the one-percent rounding HP publishes at,
#   but it is HP's word, not a precise reading, and this note is the record
#   of that.
# - Q1 FY26 does not give Consumer/Commercial Printing units separately
#   ("both reflecting similar declines"), so those two cells are absent
#   rather than guessed at. Absence here means not disclosed, not zero.
CC_GROWTH = {
    "Q1 FY26": {"Personal Systems": 9, "Printing": -3, "Supplies": -2},
    "Q2 FY26": {"Personal Systems": 10, "Printing": -2, "Supplies": 0},
    "Q3 FY26": {"Personal Systems": 17, "Printing": -4, "Supplies": -4},
}
CC_GROWTH_SOURCE = {"Q1 FY26": PR_Q1FY26, "Q2 FY26": PR_Q2FY26, "Q3 FY26": PR_Q3FY26}

UNITS_GROWTH = {
    "Q1 FY26": {
        "Personal Systems": 12, "Consumer PS": 14, "Commercial PS": 11,
        "Printing": -6,
        # Consumer/Commercial Printing units not separately disclosed this quarter.
    },
    "Q2 FY26": {
        "Personal Systems": -7, "Consumer PS": -8, "Commercial PS": -7,
        "Printing": -7, "Consumer Printing": -8, "Commercial Printing": -4,
    },
    "Q3 FY26": {
        "Personal Systems": -16, "Consumer PS": -19, "Commercial PS": -14,
        "Printing": -7, "Consumer Printing": -9, "Commercial Printing": -2,
    },
}
UNITS_GROWTH_SOURCE = CC_GROWTH_SOURCE

# Nominal y/y revenue growth for the units that don't get their own net_revenue
# row above: Consumer PS, Commercial PS, Consumer Printing, Commercial Printing,
# Supplies all already have revenue in REVISED/FY26 dicts, so their nominal
# growth is computable from those directly and is not re-stated here. This
# table exists only for the two totals HP narrates with an explicit headline
# percent alongside the constant-currency figure, letting validate.py check
# the two against each other the same way check 4 checks the restatement.
YOY_NOMINAL = {
    "Q1 FY26": {"Personal Systems": 11, "Printing": -2},
    "Q2 FY26": {"Personal Systems": 13, "Printing": 0},
    "Q3 FY26": {"Personal Systems": 18, "Printing": -2},
}

# ---------------------------------------------------------------------------

rows = []

def add(q, unit, metric, value, unit_label, basis, source):
    rows.append({
        "fiscal_quarter": q,
        "quarter_end_date": QUARTER_END[q],
        "fiscal_year": "FY" + q.split("FY")[1],
        "business_unit": unit,
        "segment": ("Printing" if unit in ("Supplies", "Commercial Printing",
                                           "Consumer Printing", "Printing")
                    else "Personal Systems" if unit in ("Commercial PS", "Consumer PS",
                                                        "Personal Systems")
                    else "Other"),
        "metric": metric,
        "value": value,
        "unit": unit_label,
        "reporting_basis": basis,
        "source_type": "reported",
        "source_url": source,
    })

# Net revenue, FY24 and FY25, both bases
for fy, qs in (("FY24", ["Q1 FY24", "Q2 FY24", "Q3 FY24", "Q4 FY24"]),
               ("FY25", ["Q1 FY25", "Q2 FY25", "Q3 FY25", "Q4 FY25"])):
    for unit in UNITS:
        for i, q in enumerate(qs):
            add(q, unit, "net_revenue", REVISED[fy][unit][i],
                "USD millions", "FY26 realigned", PR_Q1FY26)
            add(q, unit, "net_revenue", AS_PREVIOUSLY_REPORTED[fy][unit][i],
                "USD millions", "as previously reported", PR_Q1FY26)

# Net revenue, FY26 quarters
for q, vals in FY26.items():
    for unit in UNITS:
        add(q, unit, "net_revenue", vals[unit], "USD millions",
            "FY26 realigned", FY26_SOURCE[q])

# Operating margin
for q, vals in OP_MARGIN.items():
    for unit, v in vals.items():
        add(q, unit, "operating_margin_pct", v, "percent",
            "FY26 realigned", OP_MARGIN_SOURCE[q])

# Earnings before taxes
for unit, vals in EBT_REVISED_FY25.items():
    for i, q in enumerate(["Q1 FY25", "Q2 FY25", "Q3 FY25", "Q4 FY25"]):
        add(q, unit, "earnings_before_taxes", vals[i], "USD millions",
            "FY26 realigned", PR_Q1FY26)
for unit, vals in EBT_PREV_FY25.items():
    for i, q in enumerate(["Q1 FY25", "Q2 FY25", "Q3 FY25", "Q4 FY25"]):
        add(q, unit, "earnings_before_taxes", vals[i], "USD millions",
            "as previously reported", PR_Q1FY26)
for q, vals in EBT_FY26.items():
    for unit, v in vals.items():
        add(q, unit, "earnings_before_taxes", v, "USD millions",
            "FY26 realigned", FY26_SOURCE[q])

# Constant-currency y/y growth, hardware unit y/y growth, and nominal y/y
# growth for the two totals HP narrates explicitly. Prose-only figures,
# see the CC_GROWTH comment above for what "flat" and absent cells mean.
for q, vals in CC_GROWTH.items():
    for unit, v in vals.items():
        add(q, unit, "yoy_growth_cc_pct", v, "percent",
            "FY26 realigned", CC_GROWTH_SOURCE[q])
for q, vals in UNITS_GROWTH.items():
    for unit, v in vals.items():
        add(q, unit, "units_yoy_pct", v, "percent",
            "FY26 realigned", UNITS_GROWTH_SOURCE[q])
for q, vals in YOY_NOMINAL.items():
    for unit, v in vals.items():
        add(q, unit, "yoy_growth_pct", v, "percent",
            "FY26 realigned", CC_GROWTH_SOURCE[q])

FIELDS =["fiscal_quarter", "quarter_end_date", "fiscal_year", "business_unit",
          "segment", "metric", "value", "unit", "reporting_basis",
          "source_type", "source_url"]

OUT_PATH = "../data/processed/segment_data.csv"

with open(OUT_PATH, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)

print(f"wrote {OUT_PATH}: {len(rows)} rows")
