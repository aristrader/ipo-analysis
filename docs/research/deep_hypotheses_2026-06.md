# Deep Hypotheses — curated & deduped (2026-06-06)

Source: 5 long-leash agents (capital flows, regime conditioning, structural/SEBI calendars,
behavioral reference points, literature sweep) — 61 raw → deduped into 8 FAMILIES / ~26 distinct
tests below. Bar: second-order only (interactions, sequences, regimes, cross-IPO mechanics).
THOUGHTS ONLY — nothing tested yet; owner picks what to implement.

Key regulatory facts verified (give us natural experiments with built-in placebos):
anchor lock-in = 50% @30d + 50% @90d for issues opening ≥2022-04-01 (single 30d cliff before);
T+3 listing mandatory 2023-12-01 (T+6 before); promoter/pre-IPO lock-ins shortened ~Aug-2021
(pre-IPO holders 1y→6m). ASBA unblocks ~T+2.

## TIER 1 — strongest mechanism + all data on hand
**F1. Anchor-unlock supply waves** *(6 merged; Field&Hanka 2001 + SEBI 30/90 rule)*
   a) Event study at day-30 & day-90: abnormal alpha dip + the dose-response (dip ∝ anchor share
      of issue). b) Dip deeper when run-up-to-unlock is high (more profit to book). c) Bites only
      when demand is thin (anchor% × low-subscription × negative momentum triple). d) UNLOCK
      COLLISIONS: many IPOs' day-90s landing the same week amplify each other. e) Placebo: the
      whole day-90 effect must NOT exist pre-Apr-2022. — Tradable: a knowable-in-advance calendar.

**F2. Wallet-competition clusters** *(the owner's exemplar, formalized; 6 merged)*
   a) Within a cluster of overlapping subscription windows: GMP RANK inside the cluster (not level)
      → attention winners pop then bleed; neglected members outperform week-1→1m. b) Listing-order
      tone-setting (first lister's day-1 sets later members' opens). c) Ordinal fatigue in rapid
      streaks (Nth IPO pops less). d) Retail congestion tax: concurrent open issue-size depresses
      RETAIL subscription but not QIB → congestion-hidden quality (high QIB/low retail under
      congestion) outperforms. e) QIB rotation to the later-closing book of a strong pair.
      f) Mega-IPO shadow (giant issue drains the wallet for weeks) + drought-rebound mirror.

**F3. Regime-gated junk bounce + take-profit** *(the owner's 2nd exemplar)*
   Low-quality × BULL listing regime → reliable rentable 1-month MFE (sell-into-strength works
   THERE), same junk in bear dies on arrival. Variants: regime axis = direction vs realized-vol
   (calm-bull is the real regime?); SME elasticity ≫ MB. Re-opens the rejected unconditional
   take-profit as a CONDITIONAL rule. Test on mfe_lst_1m × score tercile × Nifty trailing state.

**F4. Regime-conditional stop-loss** — the rejected "stops lose to buy-and-hold" was maybe a
   bull-era artifact; test stops ONLY in bear-during-window cohorts (2008/2011/2022 labs).

**F5. Reference-point path dynamics** *(Kaustia 2004 documents the volume mechanism on real IPOs)*
   a) Issue-price magnet: approach-from-below stalls at issue (breakeven selling wall) vs placebo
      levels. b) Listing-day-high = trapped-supply ceiling; CONFIRMED breakout → acceleration;
      touch-and-fail → continued weakness. c) Volume-confirmed crossings beat naked ones.
   d) Double-reference ordering (reclaim issue first → odds of clearing LDH later).
   e) Anchor decay: never reclaimed issue by ~90d → capitulation regime, elevated wipeout
      (incremental to existing flags?). f) Round-number issue prices = stronger magnets.

**F6. GMP, second-order** *(raw level is in-score; these are its derivatives)*
   a) GMP-SURPRISE residual: listed above/below what GMP implied → does the surprise direction
      carry 1w/1m drift? b) GMP × retail-share interaction (self-fulfilling only when the
      GMP-watching crowd is the marginal buyer). c) GMP meaning by regime (froth in hot, scarcity
      in cold — sign flip). d) T+3 natural experiment: GMP→pop transmission tightened post-2023?

**F7. Disposition contagion / sequential learning** *(Lowry-Schwert; Kaustia-Knüpfer)*
   Prior cohort's REALIZED outcomes (trailing 60-90d listing pops / 1m alpha) → next cohort's
   retail subscription AND forward alpha; cold-streak filtering (IPOs braving a losing streak
   are demand-validated → outperform). Point-in-time-safe rolling features.

**F8. Unfilled-demand day-1 pressure** — day-1 buying ∝ how much the allotment LOTTERY denied
   (sub−1 = unfilled multiple), incremental to raw subscription level; predicts day-1 path shape.

## TIER 2 — good, run after Tier 1 (power/controls concerns)
T2a. Pre-IPO-holder 6-month unlock dip at day ~180 post-Aug-2021 (vs day ~365 before — regime diff).
T2b. First-week tape × regime → hold-horizon choice (strong week in bear = head-fake?).
T2c. Regime-transition fragility (listed-in-bull, market turns → persistence rule breaks?).
T2d. Crowded-window penalty regime-dependence (refines the in-score signal).
T2e. Drawdown-recovery odds by listing cycle-phase (late-bull listings don't get dip-bought).
T2f. Rolling-regime beats calendar-year as the real "vintage" (de-biases other findings).
T2g. Same-banker scheduling collision (we HAVE lead_manager — agent wrongly flagged it missing).
T2h. ASBA refund echo (freed money from IPO A pumps the still-open book B) — final-sub proxy only.
T2i. Day-1 flipping proxy (volume/shares-offered + day1→5 reversal) → long-run underperformance.
T2j. SME circuit-cage path signature (same shock, slower discovery → timing differences vs MB).

## TIER 3 — data-gated (scope the source FIRST, don't build blind)
T3a. Band-position × QIB (partial-adjustment analog) — needs price_band_high (we hold band_low only).
T3b. GMP trajectory/slope within the window — needs multi-day GMP history (we hold snapshots).
T3c. SME→MB migration anticipation — needs actual migration dates.
T3d. Index/F&O inclusion drift — needs review-date calendar.
T3e. Locked-share % beyond anchor — needs DRHP parsing (parked tooling exists).
T3f. SME market-maker 3-yr expiry cliff — sample thins (only ≤2023 listings observable).

## The 3-layer test protocol (owner's enhancement, 2026-06-06 — applies to EVERY family)
1. EXISTENCE — does the pattern exist (event study, falsifier, placebo where available).
2. MAGNITUDE & SHAPE — size, duration, dose-response, % of cases affected (e.g. F1: median day-90
   dip %, days it lasts, depth vs anchor-share, share of IPOs that dip at all).
3. PLAYBOOK — the conditional TRADE and its payoff distribution: pre-declared entry grid (e.g.
   buy at day+1/+2 after the dip starts), horizons 2w/1m/3m, win-rate + median/P10/P90 vs the
   buy-and-hold counterfactual, and the FAILURE CELLS (when the trade catches the knife).
   Anti-curve-fit guard: the entry/threshold grid is fixed BEFORE looking; the WHOLE grid is
   reported (no best-cell cherry-picking); any rule must hold cross-regime + on the OOS holdout.

## Suggested execution order (when approved)
Wave 1: F1 (cleanest event study + placebo), F2a (the owner's pattern), F3 (+F4 same harness).
Wave 2: F5, F6, F7, F8. Wave 3: Tier 2. Tier 3 only after a scoping pass on sources.
Every test: cross-regime cells + min-N floors + falsifiers as specified; survivors face the
OOS fold gate before touching the score; failures go to the registry graveyard.
