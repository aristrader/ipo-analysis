# News / catalyst / signal-expansion — OPPORTUNITY MAP (converged 2026-06-08)

The single authoritative synthesis of an 8-agent research sweep (RESEARCH ONLY — nothing built).
Detail docs: `newsfeed_{sources,taxonomy,mechanics,hypotheses,redteam,grand_vision,synthesis_draft,
coverage_critique}.md`. Purpose: map the FULL potential + a layered task breakdown so we scope
down from a complete picture later. Honesty/ethos rules from `execution_pipeline.md` apply.

## BOTTOM LINE (read this first)
News-REACTION trading is structurally **not for us**: we're daily, free, public-feed, thrice-daily —
we can never be early, and the edge decays in minutes. What SURVIVES the red-team: (a) **explanatory**
context ("the +20% had a real filing behind it"), (b) **slow drift in ILLIQUID names** (PEAD is real
precisely in our SME/microcap cohort, plays out over weeks), (c) a few **backtestable-today** signals
that need NO news feed. The surprise winner isn't news at all — it's **delivery-volume %**. Everything
predictive-from-news is gated behind a realistic **~18–36 month forward-collection clock**.

## THE LAYERED TASK BREAKDOWN (the deliverable — for scoping later)
### ⭐ DO FIRST (free, fully historical, backtestable NOW, zero new fragility)
- **Delivery-volume % conviction signal** — free, in the bhavcopy family we already pull, 2006+ (cross-
  regime), the honest daily-data "real-move vs noise" proxy. If it can't clear our bar, the whole
  catalyst direction probably can't. (3-layer test; could become display or score-candidate.)
- **H7 — corp-action euphoria-top backtest** — `corp_actions.csv` (1,509 rows, 2006+, ISIN-keyed), no
  news feed, no look-ahead. Widens the thin F10 flag (n=31). Run it to KILL-or-keep (watch F10 double-count).

### LOW-EFFORT
- **Start the NSE-announcements staging pull NOW (forward-collect)** — the only way to start the
  18–36mo clock that makes ANY predictive news hypothesis testable later. Stage raw, don't interpret.
- **Pin the look-ahead-safe timestamp rule** (filing field = "first public"; post-15:30 → actionable D+2).

### MEDIUM
- **RUNG 1 — explanatory NSE-announcement context feed** on the IPO Detail card (dated, ISIN-keyed,
  category-tagged by structured fields + a local keyword taxonomy — NO LLM, NO egress). Display-only,
  "context not signal" chip → cannot break the honesty moat. The honest near-term product.
- Drift-vs-reversal-by-news-stamp + volume/D+1 follow-through tests (need the staged feed first).

### BIG BET / DATA-GATED (forward-only, boom-only, likely fail cross-regime — collect quietly, test later)
- H1–H4, H6, H8, H10, H11 (news overrides day-21 lean; pledge flips hold→exit; SME order-win sell-the-
  spike; etc.) — all need a forward-collected news date+category+direction; ~18–36mo to a clean verdict.

### NOT-VIABLE / KILL (don't rabbit-hole)
- ALL social sentiment (Twitter paid; Reddit/Telegram/StockTwits = pump-and-dump, inverts the signal)
- Hosted-LLM headline polarity (cost + company-laptop egress = hard NO)
- RSS/free-text fuzzy ISIN-matching (drops back into the F11 swamp)
- F&O/options-OI (our SME/microcap names aren't in F&O)
- H9 block-deal-history (the endpoint probe FAILED; low signal-to-noise)
- **RUNG 3/4: all-stocks universe + TA+FA+news fusion** — combinatorial false-discovery + an unbounded
  quarterly-fundamentals SLA for ~2,000 names; negative-ROI for a solo owner; breaks the bounded,
  survivorship-clean moat. Intellectually interesting, not worth the maintenance tax.

## THE GRAND-VISION LADDER (what the owner sketched — mapped, with honest verdicts)
- RUNG 0 (here): IPO terminal — rate/apply-avoid/leans/track-record/alerts. ✅
- RUNG 1: news for hold/exit (explanatory) — DO (medium); de-risked, moat-safe.
- RUNG 2: news-driven buy/sell calls — DATA-GATED (forward clock) + must beat do-nothing.
- RUNG 3: all-stocks universe — XL, fragile, negative-ROI → PARK/KILL.
- RUNG 4: TA+FA+news fusion (north star) — KILL as a build; the *delivery-%* + corp-action items are the
  honest, bounded way to add a TA-ish / catalyst dimension WITHOUT the fusion sprawl.

## SOURCE SPINE (only the trusted, ISIN-matchable, free ones; full table in newsfeed_sources.md)
NSE corporate-announcements API (free JSON, `sm_isin` in payload — the spine) · NSE board-meetings/
events calendar (forward catalysts) · NSE SAST/insider · screener.in announcements (fallback +
ratings, arrive as Reg-30) · Google-News RSS (only for real-world/order news; live-only, fuzzy match).
Network access is allowlisted per `trusted_sources.md` (default-deny, no downloads).

## HIGHEST-SIGNAL NEWS CATEGORIES (if/when we do RUNG 1-2; from newsfeed_taxonomy.md)
earnings-surprise (PEAD drift) · SEBI/regulatory action (negative overhang) · promoter pledge/SAST
(distress) · M&A target (drifts to offer price) · management red-flags (governance) · index-inclusion
(front-run the run-up, fade the event). Don't-trade-the-headline: insider-enforcement, rating changes
(both already priced).

## RECOMMENDATION
Scope down to the **3 worth doing**: (1) delivery-% [first], (2) H7 corp-action backtest, (3) RUNG 1
explanatory feed (+ start the announcement staging clock). Park the forward-only hypotheses (collect
raw history quietly). Kill social / LLM-polarity / all-stocks fusion. Each "do" item enters the
standard pipeline when picked.

## RE-RANK 2026-06-09 (R&D update — `newsfeed_rnd_2026-06-09.md`, supersedes the order above)
The delivery-% history finding is the linchpin: `sec_bhavdata_full` delivery data is **boom-only (~2017+)**
and a SEPARATE pull from our cm-bhavcopy → it **cannot be cross-regime-validated → cannot enter the score**;
realistic ceiling = display-only, with only a weak (practitioner, non-academic) prior. So:
- **(1→ now 3) Delivery-%: DEMOTE** to "one disciplined, falsifiable, display-only experiment" — not the linchpin.
- **(2→ now 1) H7 corp-action backtest: PROMOTE to DO-FIRST** — only item that is data-in-hand (corp_actions.csv,
  2006+) AND cross-regime-capable AND extends a shipped flag (F10), zero new fragility.
- **(3) RUNG-1 explanatory feed: KEEP (medium)** — best near-term PRODUCT (turnkey spec in the R&D doc §2),
  moat-safe display-only; start the announcement staging clock now. KILLs unchanged.
