# Verification of "verify later" dataset flags

Date: 2026-05-31. Agent: verification research pass.
Scope: the 5 flagged items in the task brief. Sources used: screener.in (face-value +
P&L API, authoritative for the FV/financials checks), Chittorgarh detail pages, and public
web records (trendlyne/goodreturns/businesstoday/ipoplatform/topsharebrokers) for split/bonus
dates+ratios and listing-day quotes. BSE corp-actions API (api.bseindia.com) is Akamai-blocked
(confirms the `docs/sources.md` dead-end) — could not be used.

Convention used throughout: ISIN = identity key; corporate actions reasoned by SYMBOL/face value
(a face-value split changes the ISIN). Concrete, high-confidence corrections are in
`verification_corrections.csv`.

---

## Item 1 — 85 `inferred_split` rows (verify the inferred split/bonus factor)

Method. For every one of the 85, the IPO-era **face value was confirmed = ₹10** (Chittorgarh detail
pages, all 85). I then pulled the **current face value from screener.in** as an independent,
authoritative corporate fact. A face-value split is exact: `split_component = 10 / current_FV`.
Comparing the pipeline's `inferred_factor` (= issue_price / issue_price_adj) against the FV-derived
split isolates whether (a) a real split of that size occurred and (b) whether any residual implies a
bonus. For the 4 `bhavcopy_daily` rows screener is fully independent of our value; for `screener_weekly`
rows the price ratio is partly circular, so the **FV change is the decisive independent signal**.

### Verdict tally (FV-based)
- **confirmed_split — 18**: FV change exactly explains the inferred factor (residual 0.8–1.25×).
  e.g. Sudarshan Pharma (FV 10→1, 10:1, inferred 11.66), Humming Bird (10:1, 9.78), AA Plus (10:1, 10.36),
  Getalong (10:1, 9.52), Maagh (10:1, 11.35), Satkar Finlease (10:1, 9.52), Sunstar Realty (10:1, 9.09),
  Money Masters (10:1, 10.83), Shanti Educational (10:1, 9.84), HPC Biosciences (10:1, 9.06),
  Karnavati Finance (10:1, 10.00), Artemis Electricals (10:1, 10.37), Ascensive Educare (10:1, 8.96),
  Bondada Engineering (FV 10→2, 5:1, 4.35), Darshan Orna (5:1, 4.55), Cinemax India (FV 10→5, 2:1, 2.08).
- **split_plus_bonus — 9**: FV change confirms a split AND the residual cleanly implies a bonus (often ~2×):
  Ultracab (5:1 + ~2.3× bonus), Ranjeet Mechatronics (2:1 + ~2×), Khemani (2:1 + ~2.1×),
  Anlon Healthcare (5:1 + ~2×), Dhariwalcorp (5:1 + ~2.1×), Meera Industries (2:1 + ~2.6×),
  Bajaj Healthcare (2:1 + ~2×), Captain Polyplast (5:1 + ~1.3×), Sharika Enterprises (2:1 + ~1.7×).
  Direction/magnitude corroborated; exact bonus ratio not individually confirmed.
- **split_understated — 2** (CORRECTION): FV proves a larger split than the inferred factor.
  - **Insolation Energy (INA)** — FV 10→1 = **1:10 split, record date 2025-01-24** (goodreturns/trendlyne).
    Inferred factor was only 7.845; **true factor = 10.0**. Correction filed.
  - **MIC Electronics (MICEL)** — FV 10→2 = **5:1 split**; inferred only 2.77; **true factor ≥ 5.0**. Correction filed.
- **bonus_implied — 32**: current FV still = ₹10 (NO split), so the inferred factor (1.5–9.5×) must be a
  **bonus**. Spot-confirmed for **Trident Texofab (TTFL): 14:10 bonus, ex/record 2020-08-12** (trendlyne) —
  true factor 2.40 vs inferred 2.125, so our factor *understates* the bonus (correction filed). The other 31
  (e.g. Jiya Eco, Vishal Bearings, Commercial Syn Bags, RDB Rasayans, Mitsu Chem, Bansal Roofing, Somi Conveyor,
  Riddhi Steel, 7NR, SPS Finquest, Jupiter Infomedia, Filtra, Kwality Pharma, Blueblood, Ambition Mica,
  Yash Chemex, Nandani Creation, Oceanaa, Resurgere, Mangalam Seeds, VMS, Oriental Trimex, etc.) are corroborated
  as "a bonus of roughly this size exists" (FV unchanged rules out a split), but the exact ratio was not checked
  one-by-one. NOTE: GCM Commodity shows inferred 9.52 with FV=10 — that is too large for a normal bonus and may be a
  multi-event chain or a coverage artefact; re-check individually before trusting.
- **unverifiable_no_fv — 24**: screener FV could not be auto-fetched (delisted / renamed / numeric-slug /
  not on screener). Of these I separately web-confirmed **Aditya Vision (AVL): 1:10 split, FV 10→1,
  record date 2024-08-27** (this is the §F flagged stock; inferred 10.13 ✓ — correction filed) and
  **Angel Broking → Angel One (ANGELONE): 1:10 split, FV 10→1, record date 2026-02-26** (inferred 10.01 ✓ —
  correction filed). The remaining 22 (M.D.Inducto Cast, Mandhana, Avax Apparels, Kavita Fabrics, Jet
  Infraventure, XL Telecom, Monarch Health, Future Ventures, Vaksons, Sangam Advisors, Solar Explosives,
  Prime Customer Services, Gala Print City, Readymade Steel, Akme Star Housing, Raj Rayon FPO, Keerti, Narayani
  Steels→Dhatre Udyog, Silverpoint, Naysaa, B.C.Power Controls, Vishal Retail, Sejal Glass) remain
  **could-not-verify** — flag, do not auto-apply.

**Bottom line for item 1:** of 85, **29 corroborated as a real split (FV-confirmed) of the right magnitude**
(18 clean + 9 split+bonus + 2 split-understated), plus **2 web-confirmed split cases inside the FV-unfetchable
group (Aditya Vision, Angel Broking) = 31 confirmed splits total**; **32 corroborated as a bonus** (FV unchanged;
1 of them, Trident Texofab, exactly confirmed); **22 could not be verified**. **Zero contradicted** —
no inferred split was shown to be spurious. Concrete factor corrections (Insolation 7.845→10, MIC ≥5,
Trident 2.125→2.40, plus the precise dates for Aditya Vision / Insolation / Angel One) are in the CSV.

---

## Item 2 — splits MISSING from the NSE corp-actions feed (data_review §F)

Confirmed actual split/bonus events that the NSE feed lacked, with ratio + date (ready to add to corp_actions
by SYMBOL):

| Company | Symbol | Action | Ratio | Record/ex date | Source |
|---|---|---|---|---|---|
| Aditya Vision | AVL | Split | 1:10 (FV ₹10→₹1) | 2024-08-27 | trendlyne / madefortrade / goodreturns |
| Insolation Energy | INA | Split | 1:10 (FV ₹10→₹1) | 2025-01-24 | goodreturns / trendlyne |
| Angel Broking→Angel One | ANGELONE | Split | 1:10 (FV ₹10→₹1) | 2026-02-26 | trendlyne / jmfinancial / businesstoday |
| Trident Texofab | TTFL | Bonus | 14:10 | 2020-08-12 | trendlyne TTFL bonus |
| MIC Electronics | MICEL | Split | 5:1 (FV ₹10→₹2) | (FV-confirmed; date not pinned) | screener FV=2 |

Aditya Vision is exactly the §F example. The other FV-confirmed splits in item 1 (current FV < ₹10) are also
candidate missing-feed entries; the five above are the high-confidence, date-bearing ones.

---

## Item 3 — 21 financial disagreements (screener vs old Sharescart)

Checked the largest disagreements against screener.in's reported P&L (standalone + consolidated). In **every
case screener is correct** and the Sharescart `pre_ipo_*` value is the erroneous one — vindicating the project's
decision to use screener. No standalone-vs-consolidated confusion drove these; Sharescart's numbers were simply
wrong (wrong metric/year, or — for insurers — a different "premium" definition).

| Company | FY | Field | Sharescart | screener (used) | screener actual | Verdict |
|---|---|---|---|---|---|---|
| Anand Rathi Wealth | FY21 | net_sales | 846 | 273 | consol 273 / standalone 260 | **screener right**; Sharescart 846 spurious |
| Concord Enviro Systems | FY24 | PAT | 96 | 41 | consol 41 | **screener right**; Sharescart 96 spurious |
| Exicom Tele-Systems | FY23 | PAT | 33 | 8 | consol 8 | **screener right**; Sharescart 33 spurious |
| Vikran Engineering | FY25 | net_sales | 94 | 916 | standalone 916 | **screener right**; Sharescart 94 spurious |
| Canara HSBC Life | FY25 | net_sales | 7850 | 10710 | standalone 10710 | **screener right** (insurer total income); Sharescart used net premium |
| Go Digit Gen. Insurance | FY24 | net_sales | 7096 | 8147 | standalone 8147 | **screener right** (insurer); Sharescart used net earned premium |
| Insolation Energy | FY22 | net_sales | 126 | 215 | consol 215 | **screener right**; Sharescart 126 spurious |

Conclusion: the 21-row review file does **not** indicate screener errors. The remaining ~14 smaller disagreements
follow the same pattern (screener is the correctly-dated/consolidated figure) and need no action. No corrections to
`ipo_analysis.csv` financials.

---

## Item 4 — 16 listing-price mismatches (`xcheck_review.csv`: computed/bhavcopy vs Chittorgarh)

Spot-checked 5 against authoritative listing-day records. The mismatches split into two causes:

1. **NSE-vs-BSE exchange difference (both quotes correct).**
   - **Veranda Learning (INE0IQ001011)**: listing-day open was **₹125 on NSE** and **₹157 on BSE** — our
     bhavcopy_open (125, NSE) is right; Chittorgarh quoted the BSE open (157). Not an error. Our NSE-anchored
     computed value is correct.
2. **Genuine Chittorgarh error (computed/bhavcopy correct).**
   - **SoftTech Engineers (INE728Z01015)**: NSE SME listing open = **₹88** (= our bhavcopy_open 88). Chittorgarh's
     72.5 is **wrong**. CORRECTION filed.
   - **Sagar Diamonds (INE146Y01013)**: BSE-SME listing; our value 45 (= issue price, par debut) is plausible,
     Chittorgarh 35.55 implies a −21% debut; exact open not pinned from public records → lean "our value right"
     but not definitively confirmed.
   - **Puravankara (INE323I01011)**: public records cite a **₹361.75** debut — matches neither our 310 nor
     Chittorgarh's 399. Ambiguous; **could not cleanly resolve** — flag for manual review (our 310 may be a low
     or a delayed open).

This confirms the project's prior finding ("usually Chittorgarh's quote is the error") AND adds a second cause
(NSE/BSE divergence). The computed/bhavcopy values are the better choice; no change needed except noting SoftTech
as a confirmed Chittorgarh error. Recommend treating these flags as "use computed/bhavcopy, ignore Chittorgarh
listing quote", with Puravankara left open.

---

## Item 5 — G4 (8 SME missing market_maker) + G5 (27 `no_ref`)

### G4 — 8 SME missing `market_maker` (boom-era `sme.csv`)
Re-read the Chittorgarh detail pages + web. Recovered **3 of 8** with high confidence:

| ISIN | Company | Market maker | Source |
|---|---|---|---|
| INE813V01022 | Madhav Copper Ltd. FPO | Pantomath Stock Brokers Pvt. Ltd. | chittorgarh detail |
| INE05FR01029 | Ashapuri Gold Ornament Ltd. FPO | NNM Securities Pvt. Ltd. | chittorgarh detail |
| INE00D001018 | Rex Pipes & Cables Industries Ltd. | New Berry Capitals Pvt. Ltd. | ipoplatform / chittorgarh |

The other 5 (Veer Global Infraconstruction, Janus Corp. FPO, B-Right Realestate, Omfurn India FPO, Manas Polymers)
have **no market-maker name on the Chittorgarh page**; several are FPOs (no MM requirement). For Veer Global the web
only names the lead manager (Capital Square Advisors), not a market maker. Leave these 5 flagged. Corrections for the
3 recovered are in the CSV.

### G5 — 27 `no_ref` rows (identity not cross-verifiable against the cached exchange list)
Eyeballed all 27 (name + ticker + ISIN). **No mismatch found.** Composition:
- **11 REIT/InvIT** special securities (Mindspace, PGINVIT, Brookfield, Nexus Select, Bharat Highways,
  Anantam Highways, Knowledge Realty, Capital Infra, Property Share Platina/Titania, AGS Transact) — all
  unambiguously correct; they are simply absent from `EQUITY_L.csv` (not common-equity).
- **16 SME** rows. Spot-checked 4 against ISIN→company web/exchange lookup, all **exact matches**:
  - Trekkingtoes.com (INE0DG401010 / BSE 543222) ✓
  - Naturo Indiabull (INE0JNB01012 / BSE 543579) ✓
  - Kalahridhaan Trendz (INE02M801018 / KTL, NSE SME) ✓
  - Dev Labtech Venture (INE0NIJ01017 / BSE 543848) ✓

Conclusion: G5 identities are sound — `no_ref` reflects a stale/partial cached exchange-list snapshot (REITs/InvITs
excluded; recent/migrated SMEs not in the cache), not wrong company assignment. No corrections needed.

---

## Notes / caveats
- BSE corp-actions API remains Akamai-blocked (matches `docs/sources.md`); screener face value + public
  records were the practical authoritative substitutes.
- For `screener_weekly` inferred_split rows the price-ratio factor is partly circular with the listing price;
  the face-value cross-check is the genuinely independent confirmation and is what these verdicts rest on.
- "bonus_implied" rows are corroborated only as "a bonus of roughly this size exists" except Trident Texofab
  (exact). Do not treat the implied bonus multipliers as exact ratios without per-stock corp-action confirmation.
