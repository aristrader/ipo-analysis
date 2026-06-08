# IPO Analysis Tool — Product Overview (one-page spec)

_What the tool actually does today. Honest scope — capabilities AND deliberate non-features.
Living doc; update when a capability ships or is retired. Not financial advice._

## What it is
A personal research terminal over **~2,384 Indian IPOs (2006–2026, Mainboard + SME, incl. delisted)**.
Turns historical patterns into (a) a rating for any IPO, (b) dated/graded calls, (c) an honest
track record. Free data only. **No ML** — analog-based ("what similar past IPOs did"),
cross-regime validated (boom 2020–26 vs longterm 2006–19). Returns = **alpha vs Nifty 50**.

## Core functions
1. **Rate any IPO — anytime.** 8-component scorecard → 0–100 (return_potential · multibagger_odds ·
   downside_safety · liquidity · quality · wipeout_safety · crowded_window) + a separate WIPEOUT
   red-flag badge (tiny sales / loss-making / obscure banker). Works on an existing IPO or a typed
   hypothetical/upcoming one. Pre-listing capable.
2. **Apply / Avoid — at SUBSCRIPTION time** (the allottee decision, before money goes in).
   Graded call anchored to the **close date** (final subscription evening). APPLY = top-quintile +
   0 flags · AVOID = bottom-quintile or ≥2 flags · else NEUTRAL. **EARLY_APPLY/AVOID** = a
   provisional read on **day 1** of the window (day-1 sub + GMP), forward-only (accuracy being
   measured). NOT a listing-day call.
3. **Post-listing — hold/exit LEANS only (no buy/sell trade calls).**
   - Persistence lean @ day 21 (PERSIST_HOLD / PERSIST_EXIT_LEAN from month-1 trading).
   - Exit review @ day 90 (never closed above issue in 90d = validated capitulation flag).
   - Take-profits alert (early bonus/split after a big run-up = validated euphoria-top tell).
   - Coarse tape-timing read (engage vs wait) — months-long, not daily.
4. **Track record — self-grading.** Every call logged to `data/master/calls_ledger.csv` (~5,170),
   graded as time passes, labeled by evidence strength: live / gap_filled (forward truth) ·
   backfilled (2026 OOS) · historical_sim (dress rehearsal). 2026 OOS: APPLY +13.6%/+16.4% vs
   AVOID −3.6%/−3.1% (1m/3m). Sim: APPLY vs AVOID +34pp @1y.
5. **Phone alerts — live.** Telegram (@IPO_call_bot), thrice daily, ONLY on new actionable calls.

## App (7 screens · `PYTHONPATH=. streamlit run app.py`, localhost-only)
Home · Recommendations (centerpiece: live board + calls + alerts + track record) · IPO Detail
(8-section read) · Evidence Browser (hypotheses + graveyard) · Signal Registry · Track Record
(+ backtester + validation) · Data/methodology. Glossary, trust chips, staleness alarm,
mode labels, min-N floors throughout.

## Deliberately NOT built (tested & rejected — not gaps)
❌ Daily/swing buy-sell trade calls (take-profit/stop-loss lose to buy-and-hold; right tail carries
returns) · ❌ intraday (daily prices only) · ❌ news/catalyst awareness (logged future idea) ·
❌ dip-buy "buy after a fall" (rejected) · ❌ ML price targets (analog-only by design).

## Honest limits
Live track record is young (forward proof accrues over months) · day-1 early-call accuracy unproven
(collecting) · data is as-of last refresh, not real-time (freshness stamped + alarmed) · Apply/Avoid
is a ranking vs history, not a guarantee (N shown; "insufficient analogs" flagged, never faked).

## One-liner
A **"should I apply to this IPO, and what do I watch after it lists"** tool — rating +
subscription-time apply/avoid + post-listing hold/exit flags + self-grading track record + phone
alerts. NOT a day-trading / buy-the-listed-stock tool, by evidence-backed choice.
