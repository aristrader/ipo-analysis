# Pattern Hypotheses — IPO Analysis

> **See `docs/strategies.md`** — the prioritized, critically-reviewed Layer-3 catalog (built from a strategy panel) that consolidates and supersedes this raw list. This file is kept as the original brainstorm. Anchor lock-in expiry is now included there.


All pattern ideas to investigate once data is collected. Not all are in v1.
Layer 1 = event data only. Layer 1+2 = needs price history.

---

## Descriptive (Layer 1 only)

- How many stocks are currently above vs below their IPO issue price?
- How many opened higher vs lower than issue price on listing day?
- Distribution of listing gains across MB vs SME
- Distribution of subscription multiples (QIB / NII / Retail) — what is "normal"?
- GMP accuracy: how often does GMP predict listing gain direction?
- Sector-level patterns: which sectors have best/worst listing performance?
- Issue size correlation: do larger issues (more supply) list lower?
- Min investment (lot cost) correlation: does lower lot cost → higher retail subscription → higher listing gain?
- OFS % correlation: do high-OFS IPOs list lower or underperform post-listing?
- Lead manager patterns: do IPOs managed by certain bankers consistently perform better?
- Book-built vs fixed-price: different listing gain distributions?
- Company age at IPO: do younger companies have higher variance in listing performance?

---

## Conditional / predictive (Layer 1 mostly)

- **Subscription as predictor:** does >30x retail sub → higher listing gain? At what threshold does it stop mattering?
- **GMP as predictor:** does GMP > 20% → opening above issue price more than X% of the time?
- **Combined condition:** low min_investment + high retail sub + positive GMP → listing gain distribution
- **Promoter holding post-issue:** does lower dilution (higher post-issue promoter %) correlate with better long-term performance?
- **Financial quality filter:** do IPOs with PAT margin > 15% have better sustained performance vs sub-5% margin IPOs?
- **Debt-heavy IPOs:** do high debt/equity companies underperform operationally strong ones post-listing?
- **Growth trajectory:** 3-year revenue growth before IPO → does it predict listing or 1-month return?
- **Issue purpose:** do debt-repayment raises underperform capex raises post-listing?
- **OFS-heavy IPOs:** does ofs_pct > 50% predict worse 1-month return?
- **S-HNI vs B-HNI split:** when S-HNI is much higher than B-HNI, does it signal leveraged flipping risk on listing day?

---

## Strategy backtests (Layer 1 + Layer 2)

These assume you did NOT get allotment — so what should you do?

- **Strategy A — Buy on listing day:** buy at listing open, hold 1 month. Average return? Distribution?
- **Strategy B — Buy after X% fall from listing price:** wait for X% dip, buy, hold 1 month. Test X = 5%, 10%, 15%, 20%.
- **Strategy C — Buy after X% fall from issue price:** same but anchored to issue price, not listing price.
- For each: what % of the time are you up at 1 month? Median return? Worst case?
- Do strategies behave differently for SME vs Mainboard?
- Do they behave differently conditional on subscription level?

---

## Within-window flags (Layer 2, computed → Layer 3)

Columns to compute and store in `data/derived/`:

| Column | Type | Definition |
|---|---|---|
| opened_above_issue | bool | listing_open > issue_price |
| listed_below_but_hit_issue | bool | listing_open < issue_price but intraday high ≥ issue_price on listing day |
| sustained_1m | bool | closing price > issue_price every day for 30 days post-listing |
| max_gain_1m | float | (max intraday high in 30 days − issue_price) / issue_price × 100 |
| up_30pct | bool | hit a price 30% above issue price within the window |
| recovery_after_dip | bool | listed below issue price but recovered above it within 30 days |

### Compound query (from original problem statement)
- Of IPOs where `listed_below_but_hit_issue = True` (opened below issue but briefly touched above intraday), how many then went on to `sustained_1m = True`?
- This is the specific scenario: stock lists weak, shows a brief recovery signal on day one — is that signal meaningful or a dead-cat bounce?

---

## Seasonality (Layer 1 only)

- Which calendar months / quarters have the best average listing gain? (use `open_date`)
- Is there a "IPO season" effect — do issuers time IPOs when markets are hot, leading to clustering of high-subscription periods?
- Do IPOs that open in bull-market months outperform those in flat/bear months, or does strong subscription override market timing?
- SME vs Mainboard: does seasonality pattern differ between the two segments?

---

## Price band width (Layer 1 only)

`price_band_width_pct = (issue_price − price_band_low) / price_band_low × 100`

- Does a wider price band (e.g. ₹90–₹100 = 11% width) indicate issuer/banker uncertainty about valuation → correlate with lower subscription or weaker listing?
- Does a very narrow band (or fixed-price) signal high confidence → stronger listing?
- Fixed-price IPOs (band_width = 0) as a separate cohort: do they behave differently from book-built?

---

## Market maker patterns (SME only, needs market_maker column)

| Pattern | Question |
|---|---|
| By name | Does MM firm X sustain prices above issue more often than MM firm Y? |
| By firm size | Do larger / better-capitalised MMs produce lower post-listing volatility? |
| MM + subscription combo | High sub + reputable MM → better 30-day sustain rate? |

Active SME market makers to group by: Emkay Global, Nikunj Stock Brokers, Marwadi Shares, GYR Capital, Systematix Shares, Anand Rathi (field is ~15–20 names, tractable).

---

## Methodology rules (apply to every pattern)

- **Holdout:** The most recent ~3 months of IPOs are reserved. Never use them during discovery.
- **Cross-year check:** Does the pattern hold in 2023, 2024, and 2025 independently? Or only one year?
- **Size check:** How many IPOs does the pattern apply to? Fewer than ~20 is noise, especially for SME.
- **Survivorship bias check:** Are delisted/failed IPOs included? If not, patterns will be biased upward.
