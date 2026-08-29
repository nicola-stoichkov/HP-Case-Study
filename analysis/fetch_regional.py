#!/usr/bin/env python3
"""
Extract HP Inc. net revenue by region from SEC filings.

HP does not disclose regional revenue in its press release segment tables.
It appears only in the 10-Q and 10-K filings, in a table named
"Supplementary Financial Information - Schedule of Net Revenue by Region".

Two things this script deliberately does not do:

1. It does not hardcode the table's file number. SEC renders each filing's
   tables as R1.htm, R2.htm and so on, and the number for this table moves
   between filings (R50, R51, R52 and R103 have all been observed). The
   script reads FilingSummary.xml and locates the table by name instead,
   because a hardcoded number would break silently rather than loudly.

2. It does not treat Q4 as reported. Q4 never appears in a 10-Q, because
   the 10-K replaces it. Q4 is therefore derived as the full fiscal year
   minus the nine months ended in July, and those rows are marked
   source_type = computed rather than reported.

Cross-check built in: the three regions must sum to total net revenue.
Note this is total NET revenue, not total SEGMENT net revenue. The two
differ by HP's small "Other" reconciling line.
"""
import csv
import re
import html
import time
import sys
import subprocess
from collections import defaultdict

CIK = "0000047217"  # HP Inc. Not Helmerich & Payne, which is HP on NYSE.
UA = "nikola.stoichkovv@gmail.com"
BASE = "https://www.sec.gov/Archives/edgar/data/47217"

# Filings needed. Each 10-Q carries the current quarter and the same quarter
# a year earlier, so six of them cover Q1 to Q3 across FY24, FY25 and FY26.
# The two 10-Ks supply the full years needed to derive Q4.
FILINGS = [
    ("10-Q", "Q3 FY26", "0000047217-26-000051"),
    ("10-Q", "Q2 FY26", "0000047217-26-000029"),
    ("10-Q", "Q1 FY26", "0000047217-26-000011"),
    ("10-K", "FY25",    "0000047217-25-000071"),
    ("10-Q", "Q3 FY25", "0000047217-25-000063"),
    ("10-Q", "Q2 FY25", "0000047217-25-000043"),
    ("10-Q", "Q1 FY25", "0000047217-25-000025"),
    ("10-K", "FY24",    "0000047217-24-000080"),
]

# XBRL member names, not display labels. Note HP displays the third region as
# "Asia-Pacific and Japan" but tags it srt_AsiaPacificMember, so trusting the
# display text here would not work. Prefixes vary too (srt_ and us-gaap_),
# which is why the parser splits on the last underscore rather than assuming
# a prefix shape.
REGION_MAP = {
    "AmericasMember": "Americas",
    "EMEAMember": "EMEA",
    "AsiaPacificMember": "APJ",
}

MONTH = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
         "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}

QUARTER_OF_MONTH = {1: "Q1", 4: "Q2", 7: "Q3", 10: "Q4"}


def get(url):
    """
    Fetch a URL, politely. SEC asks for an identifying User-Agent.

    Uses curl rather than urllib deliberately. The python.org framework build
    of Python on macOS does not read the system certificate store, so urllib
    fails with CERTIFICATE_VERIFY_FAILED unless extra certificates are
    installed. curl uses the system trust store and needs no setup.
    """
    result = subprocess.run(
        ["curl", "-sS", "--fail", "-H", f"User-Agent: {UA}", url],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"fetch failed for {url}: {result.stderr.strip()}")
    time.sleep(0.7)  # stay well inside SEC's rate limit
    return result.stdout


def find_regional_report(accession):
    """Locate the regional revenue table by NAME, not by file number."""
    acc = accession.replace("-", "")
    summary = get(f"{BASE}/{acc}/FilingSummary.xml")
    for m in re.finditer(r"<Report[^>]*>(.*?)</Report>", summary, re.S):
        block = m.group(1)
        name = re.search(r"<ShortName>(.*?)</ShortName>", block)
        fname = re.search(r"<HtmlFileName>(.*?)</HtmlFileName>", block)
        if name and fname and "net revenue by region" in name.group(1).lower():
            return f"{BASE}/{acc}/{fname.group(1)}"
    return None


def parse_regional_table(page):
    """
    Return {(region, period_months, end_date): value}.

    Table shape: a header giving period lengths and end dates, then body rows
    where a class="rh" row carrying a StatementGeographicalAxis marker sets
    the region for the revenue rows beneath it. Rows before any such marker
    are the company total.
    """
    table = re.search(r"<table.*?</table>", page, re.S)
    if not table:
        return {}
    table = table.group(0)
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.S)

    # Header: expand colspans so each value column gets its period length,
    # then pair those with the date cells from the following header row.
    periods = []
    for cell in re.findall(r'<th[^>]*colspan="(\d+)"[^>]*>(.*?)</th>', rows[0], re.S):
        span, text = int(cell[0]), re.sub(r"<[^>]+>", "", cell[1])
        m = re.search(r"(\d+)\s+Months\s+Ended", text)
        if m:
            periods.extend([int(m.group(1))] * span)

    dates = []
    for cell in re.findall(r"<th[^>]*>(.*?)</th>", rows[1], re.S):
        text = html.unescape(re.sub(r"<[^>]+>", "", cell)).strip()
        m = re.match(r"([A-Z][a-z]{2})\.?\s+(\d{1,2}),\s+(\d{4})", text)
        if m:
            dates.append(f"{m.group(3)}-{MONTH[m.group(1)]:02d}-{int(m.group(2)):02d}")

    if len(periods) != len(dates):
        return {}

    out = {}
    unknown = set()
    region = "TOTAL"
    for row in rows[2:]:
        marker = re.search(r"StatementGeographicalAxis=([\w\-]+)", row)
        if marker:
            member = marker.group(1).split("_")[-1]
            region = REGION_MAP.get(member)
            if region is None:
                unknown.add(member)
            continue
        if "defref_us-gaap_Revenues" not in row:
            continue
        if region is None:
            continue
        values = re.findall(r'<td class="nump">(.*?)</td>', row, re.S)
        if not values:
            continue
        cleaned = []
        for v in values:
            v = html.unescape(re.sub(r"<[^>]+>", "", v))
            v = v.replace("$", "").replace(",", "").strip()
            cleaned.append(int(v) if re.fullmatch(r"-?\d+", v) else None)
        for i, val in enumerate(cleaned):
            if val is not None and i < len(dates):
                out[(region, periods[i], dates[i])] = val
    if unknown:
        # Loud, not silent. An unrecognised region member means the parser is
        # dropping data, which is exactly the failure that must never pass quietly.
        print(f"  WARNING: unrecognised geographic members {sorted(unknown)}")
    return out


def main():
    facts = {}
    for form, label, accession in FILINGS:
        url = find_regional_report(accession)
        if not url:
            print(f"  WARNING: no regional table found in {form} {label}")
            continue
        parsed = parse_regional_table(get(url))
        print(f"  {form} {label}: {len(parsed)} facts")
        facts.update(parsed)
        source = (f"https://www.sec.gov/Archives/edgar/data/47217/"
                  f"{accession.replace('-', '')}/")
        for key in parsed:
            facts.setdefault("_src", {})[key] = source

    sources = facts.pop("_src", {})
    regions = ["Americas", "EMEA", "APJ", "TOTAL"]
    rows = []
    quarter_value = {}  # (region, fiscal_year, quarter_num) -> value, for Q4 below

    # Quarters reported directly: the three month columns.
    quarters = sorted({d for (r, p, d) in facts if p == 3})
    for date in quarters:
        year, month = int(date[:4]), int(date[5:7])
        q = QUARTER_OF_MONTH.get(month)
        if not q:
            continue
        for region in regions:
            key = (region, 3, date)
            if key in facts:
                fy = f"FY{str(year)[2:]}"
                rows.append({
                    "fiscal_quarter": f"{q} {fy}",
                    "quarter_end_date": date,
                    "fiscal_year": fy,
                    "period_type": "quarter",
                    "region": region,
                    "metric": "net_revenue",
                    "value": facts[key],
                    "unit": "USD millions",
                    "source_type": "reported",
                    "source_url": sources.get(key, ""),
                })
                quarter_value[(region, fy, q)] = facts[key]

    # Full fiscal year, as reported directly in the 10-K. Kept as its own row
    # rather than only used internally, so the Q4 derivation below is checkable
    # by anyone reading the CSV: FY total minus (Q1 + Q2 + Q3) = Q4, with every
    # number in that sum sitting in this same table. Confirmed by hand 2026-08-29
    # that HP's disclosed "nine months ended" figure equals summing the three
    # separately reported quarters exactly, in all three regions, so deriving
    # Q4 from the quarterly rows already in this file (rather than from a nine
    # month figure that never appears here) changes nothing about the result.
    for fy_end in ("2024-10-31", "2025-10-31"):
        year = int(fy_end[:4])
        fy = f"FY{str(year)[2:]}"
        for region in regions:
            full = facts.get((region, 12, fy_end))
            if full is None:
                print(f"  WARNING: no full-year figure for {region} {fy}")
                continue
            rows.append({
                "fiscal_quarter": fy,
                "quarter_end_date": fy_end,
                "fiscal_year": fy,
                "period_type": "full_year",
                "region": region,
                "metric": "net_revenue",
                "value": full,
                "unit": "USD millions",
                "source_type": "reported",
                "source_url": sources.get((region, 12, fy_end), ""),
            })

            three_q = [quarter_value.get((region, fy, q)) for q in ("Q1", "Q2", "Q3")]
            if None in three_q:
                print(f"  WARNING: cannot derive Q4 {fy} for {region}, "
                      f"missing quarterly data")
                continue
            rows.append({
                "fiscal_quarter": f"Q4 {fy}",
                "quarter_end_date": fy_end,
                "fiscal_year": fy,
                "period_type": "quarter",
                "region": region,
                "metric": "net_revenue",
                "value": full - sum(three_q),
                "unit": "USD millions",
                "source_type": "computed",
                "source_url": f"{fy} row above, minus Q1+Q2+Q3 {fy} rows above",
            })

    # Cross-check: the three regions must sum to total net revenue.
    by_quarter = defaultdict(dict)
    for r in rows:
        by_quarter[r["fiscal_quarter"]][r["region"]] = r["value"]
    failures = []
    checked = 0
    for q, v in sorted(by_quarter.items()):
        missing = [k for k in ("Americas", "EMEA", "APJ", "TOTAL") if k not in v]
        if missing:
            # Incompleteness is itself a failure. Silently skipping these and
            # then reporting "all checks passed" would be a false all-clear.
            failures.append(f"{q}: missing {', '.join(missing)}")
            continue
        s = v["Americas"] + v["EMEA"] + v["APJ"]
        if s != v["TOTAL"]:
            failures.append(f"{q}: regions sum to {s}, total is {v['TOTAL']}")
        checked += 1

    rows = [r for r in rows if r["region"] != "TOTAL"]
    rows.sort(key=lambda r: (r["quarter_end_date"], r["region"]))

    fields = ["fiscal_quarter", "quarter_end_date", "fiscal_year", "period_type",
              "region", "metric", "value", "unit", "source_type", "source_url"]
    out = "../data/processed/regional_revenue.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    print(f"\nwrote {out}: {len(rows)} rows across {len(by_quarter)} quarters")
    if failures:
        print(f"{len(failures)} CROSS-CHECK FAILURES")
        for f_ in failures:
            print("  -", f_)
        sys.exit(1)
    print(f"Cross-check passed: regions sum to total net revenue "
          f"in all {checked} quarters.")


if __name__ == "__main__":
    main()
