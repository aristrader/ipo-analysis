# Newsfeed taxonomy — news category → move-type (India equities)

Research note for a future news/catalyst capability. Scope: how each *kind* of corporate/market news
typically moves an Indian-listed stock. Evidence = India event-study literature (NSE/BSE) + SEBI/exchange
microstructure facts + general event-study findings. **Not financial advice; signal quality varies wildly
by firm size, float, and how "surprising" the news is.** Magnitudes below are typical *abnormal* (vs-index)
single-name reactions, not guarantees. "Knowable" = on a calendar (you can prepare); "Surprise" = headline risk.

## Glossary
- **Drift** = price keeps moving the same way for days/weeks (under-reaction → tradable).
- **Reverse/fade** = the spike round-trips (over-reaction, or "sell the news").
- **S/N** = signal-to-noise / reliability of the *direction*.

## Category → move-type table

| # | Category | Direction | Magnitude (abnormal) | Duration | Drift vs Reverse | S/N | Knowable? | India quirks |
|---|----------|-----------|----------------------|----------|------------------|-----|-----------|--------------|
| 1 | **Quarterly RESULTS / earnings (beat/miss/guidance)** | sign of surprise | 2–8%+ day-0; small caps larger | day-0 spike **+ multi-week drift** | **DRIFT** (PEAD documented in India) | High when surprise is clean | **Knowable** (45-day filing window; calendar) | Variance ~5x on result day; small/under-covered firms drift more |
| 2 | **ORDER WINS / contracts** | + (usually) | 2–10%; can hit circuit | 1-day spike, partial fade | Mixed → often **REVERSE** if order is small vs revenue | Low–Med (size vs orderbook matters; many are immaterial) | Surprise | Capital-goods/defence/EPC pump; retail over-reacts to headline ₹-value |
| 3 | **CAPEX / expansion / new plant** | + (mild) | 1–4% | slow, weeks | weak DRIFT | Low–Med (long-dated, hard to value) | Surprise | Often already in guidance; "story" stocks react more |
| 4 | **M&A / stake-sale (as acquirer/target)** | target **+**, acquirer ~0/− | target +5–15%; acquirer ±0–2% | day-0 + days | target DRIFTs to deal price; acquirer noisy | Target High, Acquirer Low | Surprise (open-offer dates knowable) | Open-offer (SAST) floor anchors target; emerging mkt more sensitive than US |
| 5 | **MANAGEMENT change / resignation** | − if abrupt/CFO/founder; + if upgrade | 2–10% | day-0, can drift down | abrupt exits **DRIFT down** (governance flag) | Med (context-heavy) | Surprise | Sudden CFO/auditor exit = red flag, market punishes hard |
| 6 | **PROMOTER pledge / stake-change (SAST)** | pledge − ; promoter buy + | pledge −2–8%; invocation steep | day-0 + drift | pledge-invoke **DRIFTs down** (forced selling) | Med–High (pledge = distress signal) | Disclosed (SAST filings) | Lenders not price-neutral when invoking; cascades; high-pledge = avoid |
| 7 | **REGULATORY / SEBI action / ban** | − | 5–20%, can be lower-circuit-locked | day-0 + days | **DRIFT down** (overhang) | High for firm-specific orders | Surprise | *Insider-trading enforcement orders: ~no significant reaction* (already-priced/ignored) |
| 8 | **Credit-RATING change** | downgrade − ; upgrade + (muted) | 1–5%; downgrade > upgrade | mostly **pre-event** | partly anticipated; little post-drift | Med (much leaks pre-event) | Surprise (watch-listing leaks) | Reaction larger *before* announcement; weaker post-2008; agency differs (CRISIL/ICRA/CARE) |
| 9 | **LITIGATION / legal order** | − (usually) | 2–15% by materiality | day-0 + drift if existential | DRIFT down if quantum large | Low–Med (quantum often unclear) | Surprise | Tax/penalty headlines spike then fade if disclosed as contingent |
| 10 | **INDEX inclusion / exclusion** | inclusion + ; exclusion − | +3–5% permanent historically | run-up to effective date, **fades ~60d** | partial **REVERSE** after effective date | Med (effect shrinking over time) | **Knowable** (rebalance dates pre-announced) | Front-running the rebalance is the trade; MSCI/Nifty flows |
| 11 | **BLOCK / BULK deals** | direction = buyer/seller side | 1–6% | 1-day + | often **REVERSE** (liquidity, not info) | Low (who/why opaque) | Disclosed (>0.5% bulk reported EOD) | Reported post-trade; retail mis-reads as conviction |
| 12 | **ANALYST initiation / upgrade** | + (mild) | 1–3% | day-0, fades | weak; often **REVERSE** | Low (sell-side conflicted) | Surprise | Thin India coverage; big-broker initiation moves small caps more |
| 13 | **DIVIDEND / buyback / bonus / split** | + (signal) | div +1–3%; buyback +1.3% day, ~5% CAR | day-0 + days | DRIFT mild; **runs up pre-event** | Med (buyback>div as signal) | **Knowable** (board-meet calendar) | OMR buyback CAR ~5% (−10..+10); bonus/split = psychological, mostly fade |
| 14 | **Sector / POLICY news (budget, tariffs)** | sector-wide ± | 2–10% across names | day-0, can persist | persists if structural | Med (broad, not stock-specific) | Knowable (Budget) / Surprise (policy) | Union Budget day = sector rotation; PLI/tariff themes drift |
| 15 | **Fund-raising / QIP / preferential** | QIP + (if low promoter hold); pref + (marquee investor) | ±2–5%; can hit upper circuit | day-0 + | mixed; dilution can REVERSE | Med (depends on who/discount) | Disclosed (board approval) | Deep-discount QIP = weak demand → falls; marquee anchor (e.g. GQG) = pop |

## Synthesis

**(a) Cleanly tradable (real info + measurable drift):**
- **Earnings surprises (PEAD)** — the strongest, most-documented India anomaly; under-reaction → multi-week drift, biggest in small/under-covered names.
- **Regulatory/SEBI firm-specific action** — large, persistent, one-directional (down) overhang.
- **Promoter pledge creation/invocation** — distress signal with forced-selling drift.
- **M&A target** — open-offer floor anchors a clean, knowable path.
- **Management red-flags** (abrupt CFO/auditor/founder exit) — reliable negative drift.

**(b) Noise (low S/N, mostly fade):** order-wins (headline ₹-value ≠ materiality), block/bulk deals (post-trade, opaque intent), analyst initiations (conflicted, thin coverage), bonus/split (cosmetic), capex (long-dated, often pre-guided).

**(c) Already-priced by the time retail sees it:** credit-rating changes (move is *pre*-event, leaks via watch-listing), index inclusion (front-run before effective date, then fades ~60d), insider-trading enforcement orders (≈no reaction at all). Anything that has run up *into* a calendar event (results, dividend, rebalance) is already discounting it.

**India microstructure caveats (apply to ALL rows):**
- **Circuit limits** (2/5/10/20% per-stock daily bands; market-wide 10/15/20%) — strong news can lock a stock limit-up/down, so the *true* reaction is censored and bleeds over multiple days; the "move" you see understates it.
- **Retail dominance + F&O frenzy** — retail ~33% of cash turnover (declining), 91% of F&O retail lose money; retail over-reacts to headlines → exaggerated spikes that fade (good for the fade trades in bucket b).
- **T+1 settlement & EOD disclosures** — block/bulk and SAST filings hit *after* the move; calendar events (results 45-day window, board meets, index rebalances) are knowable and front-run.
- **Coverage gap** — small/SME names (this project's universe) drift more and longer because they're under-analysed — PEAD and order/initiation effects are larger but liquidity is thin (whipsaw risk).

## Sources
- PEAD in India: https://www.scirp.org/journal/paperinformation?paperid=88060 ; arXiv https://arxiv.org/pdf/2009.03094
- Earnings reaction India: https://journals.sagepub.com/doi/abs/10.1177/0972262914564042
- Buyback CAR: https://www.businessperspectives.org/index.php/journals/investment-management-and-financial-innovations ; https://www.ijtrd.com/papers/IJTRD22447.pdf
- Bonus issue: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=733043
- Dividend signaling: https://www.sciencedirect.com/science/article/abs/pii/S0275531916302781 ; https://journals.sagepub.com/doi/10.1177/097215091201300206
- Credit-rating change: https://journals.sagepub.com/doi/10.1177/09721509241299952 ; https://doi.org/10.1177/0972652719877472
- Index inclusion (Nifty/MSCI): https://macrothink.org/journal/index.php/ajfa/article/viewFile/14866/12123
- M&A returns: https://www.researchgate.net/publication/365238889_Shareholder's_reaction_to_Merger_and_acquisition_announcement_evidence_from_india's_Manufacturing_sector
- Promoter pledge: https://groww.in/blog/pledging-of-shares-by-promoters ; https://bbrc.in/wp-content/uploads/2021/05/BBRC_Vol_14_No_05_Special-Issue_02.pdf
- Insider-trading enforcement (≈no reaction): https://blog.theleapjournal.org/2026/05/market-reaction-to-insider-trading.html
- QIP/preferential: https://www.researchgate.net/publication/282245536_The_Choice_between_QIP_and_Rights_Issue_Evidence_from_India ; https://www.outlookbusiness.com/markets/ideaforge-shares-hit-upper-circuit-as-board-approves-500-cr-fundraise
- Budget/policy: https://arxiv.org/pdf/2502.15787
- Circuit limits: https://www.nseindia.com/products-services/equity-market-circuit-breakers
- Retail share / F&O losses: https://blogs.cfainstitute.org/marketintegrity/2025/11/05/indias-derivatives-market-and-retail-investors/ ; https://www.icicidirect.com/share-market-today/news/sebi-sees-dip-in-derivatives-turnover,-91percentage-of-retail-traders-lose-money-in-fy25/1615620
