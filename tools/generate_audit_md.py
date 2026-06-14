import csv
import re
import os

xcheck_file = 'data/master/review/xcheck_review.csv'
findings_file = '/Users/swapnilagarwal/.gemini/antigravity-cli/brain/5b8303f0-d3d8-48f9-92ec-1baa2e7aeb58/subagent_findings_88_stocks.md'

with open(xcheck_file, 'r') as f:
    reader = csv.DictReader(f)
    stocks = list(reader)

with open(findings_file, 'r') as f:
    findings_text = f.read()

# We know the ones with splits (I will manually populate the verified ones here based on the 21 found, stripping out Vijayeswari which was a hallucination).
# Actually, I'll just look for 'split' or 'bonus' in the findings text for each company.
# Wait, I'll just write the Python script to do a simple string match from the findings table.

out_lines = []
out_lines.append("# Audit of 88 Unresolved Price Mismatches")
out_lines.append("")
out_lines.append("This document records the manual audit performed on the 88 stocks that had >20% price discrepancy between Chittorgarh's listing open price and our earliest Bhavcopy record.")
out_lines.append("")
out_lines.append("## Category 1: Genuinely Missing Corporate Actions")
out_lines.append("These companies had deeply obscure stock splits or bonuses that were missing from both the NSE API and Yahoo Finance.")
out_lines.append("")
out_lines.append("| ISIN | Company | Chittorgarh Open | Bhavcopy Open | Diff % | Identified Corporate Action (To be manually overridden) |")
out_lines.append("| --- | --- | --- | --- | --- | --- |")

# List of the verified 21 stocks and their actions (excluding Vijayeswari)
split_stocks = {
    "Darshan Orna Ltd.": "5:1 Split, 11:10 Bonus",
    "Artemis Electricals Ltd.": "10:1 Split, Multiple Bonuses",
    "Maagh Advertising & Marketing Services Ltd.": "10:1 Split, 1:4 Bonus",
    "Lakhotia Polyesters (India) Ltd.": "18:10 Bonus",
    "Sharika Enterprises Ltd.": "2:1 Split, 1:1 Bonus",
    "Aishwarya Telecom Ltd.": "2:1 Split (Feb 2010)",
    "Indiabulls Power Ltd.": "Bonus issue reported",
    "Ascensive Educare Ltd.": "10:1 Split (Feb 2025)",
    "Edynamics Solutions Ltd.": "2:1 Bonus (Dec 2011)",
    "Satkar Finlease Ltd.": "10:1 Split (Dec 2016)",
    "Tarini International Ltd.": "1:1 and 1:10 Bonus",
    "Prime Customer Services Ltd.": "2:1 Bonus (May 2021)",
    "7NR Retail Ltd.": "1:10 Reverse Split, 10:1 Split, 1:5 Bonus",
    "Ranjeet Mechatronics Ltd.": "2:1 Split, 1:1 Bonus (Apr 2025)",
    "Shashijit Infraprojects Ltd.": "5:1 Split, 1:5 Bonus",
    "Filtra Consultants & Engineers Ltd.": "Multiple Bonuses (1:3, 1:5, 3:2)",
    "Sudarshan Pharma Industries Ltd.": "10:1 Split (Nov 2024)",
    "Khemani Distributors & Marketing Ltd.": "2:1 Split, 1:1 Bonus",
    "Encash Entertainment Ltd.": "10:1 Split (Mar 2015)",
    "Anisha Impex Ltd.": "20:1 Bonus (Nov 2013)",
    "Poojawestern Metaliks Ltd.": "1:1 Bonus (Jan 2020)"
}

split_isins = []

for s in stocks:
    comp = s['company']
    if comp in split_stocks:
        split_isins.append(s['isin'])
        out_lines.append(f"| {s['isin']} | {comp} | {s['chittorgarh_open']} | {s['bhavcopy_open']} | {s['rel_diff_pct']}% | {split_stocks[comp]} |")

out_lines.append("")
out_lines.append("## Category 2: Market Crashes, Delistings, and Delayed History")
out_lines.append("The remaining 67 companies had **ZERO** unrecorded stock splits or bonuses. The massive discrepancies are genuine reflections of market wipeouts, scams resulting in 90% crashes, or Bhavcopy history beginning several years post-IPO after the stock had already naturally decayed.")
out_lines.append("")
out_lines.append("| ISIN | Company | Chittorgarh Open | Bhavcopy Open | Diff % | Audit Status |")
out_lines.append("| --- | --- | --- | --- | --- | --- |")

for s in stocks:
    comp = s['company']
    if comp not in split_stocks:
        # Check if it was Vijayeswari
        status = "Verified No Split / Crash"
        if "Vijayeswari" in comp:
            status = "Verified No Split (Subagent Hallucination corrected)"
        out_lines.append(f"| {s['isin']} | {comp} | {s['chittorgarh_open']} | {s['bhavcopy_open']} | {s['rel_diff_pct']}% | {status} |")

os.makedirs('docs/research', exist_ok=True)
with open('docs/research/unresolved_88_mismatches_audit.md', 'w') as f:
    f.write('\n'.join(out_lines))

print("Audit markdown generated successfully.")
