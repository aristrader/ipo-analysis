# Newsfeed research — COVERAGE CRITIQUE + 2nd red-team (2026-06-08)

Reviewer role: completeness critic + cold-eye skeptic over all six newsfeed docs (sources / taxonomy /
mechanics / hypotheses / redteam / grand_vision). I did NOT build anything. Verdict-first below; evidence
ground-checked against the repo (corp_actions.csv = 1,509 rows 2006+; F10 = n=31 display-only; scope probe
exists). Not financial advice.

## MISSING DIMENSIONS (a thorough map must at least name these — most should be PARKED, not built)

1. **Delivery-volume % — the cheapest unexplored signal, and it's FREE + BACKTESTABLE.** Absent from all six
   docs. NSE/BSE publish daily *deliverable qty / traded qty* in the bhavcopy family we ALREADY pull. It is the
   honest daily-data proxy for "real conviction vs intraday churn" that Mechanic-2 reaches for and can't get
   from volume alone. Unlike news it has full 2006+ history → clears the cross-regime gate. This is a bigger
   miss than anything the news docs cover.
2. **F&O / options-OI as early-information proxy — correctly absent for OUR universe, but say so.** Almost no
   recent SME/microcap IPO is in F&O; OI is irrelevant for the cohort that drives this tool. The docs should
   explicitly KILL it (not silently omit) so a future agent doesn't rediscover it as "unexplored."
3. **Look-ahead-safe filing timestamp — under-specified.** Mechanics names "next-session-open" but no doc pins
   the operational rule: which field is the *first public* time (`an_dt` vs `dt` vs attachment mtime vs edited
   pubDate), and the post-1530 → D+2 (not D+1) cutoff. This is THE number that decides whether any backtest is
   honest; it deserves one explicit paragraph, not a hand-wave.
4. **Forward-collection clock — never quantified.** "Forward-only, years to prove" is stated but not costed:
   rare events (results 4/yr/name, order-wins << that) × min-N-12 floor × no-look-ahead window = a realistic
   first *clean* verdict is ~18–36 months out on a thin sample. Without that number the rungs read shippable.
5. **Maintenance/fragility tax — asserted, not budgeted.** Redteam says "feeds break weekly" but no doc gives
   the concrete carry: NSE session-cookie rotation + anti-bot is the single most fragile thing in the repo;
   3–5 scrapers = 3–5 independent weekly-breakage surfaces on a company laptop with no remote/CI. One scraper
   (NSE announcements) is a tolerable tax; three is a part-time job.
6. **LLM classification cost/egress — left abstract.** Concretely: a *local* small model (egress-safe, ethos-
   fit) is the only allowed polarity path and it's blocked-pending-signoff; any hosted LLM = scraped-content
   egress off a work laptop = a hard NO, not a "tension." Decision should be binary-stated, not deferred.
7. **Block/bulk-deal HISTORY depth (H9's load-bearing claim).** H9 says NSE bulk/block-deal archive is
   "historically downloadable" → backtestable. The sources doc probe FAILED on the block-deal endpoint (#14,
   "wrong variant"), and redteam never revisits it. So H9's one feasibility advantage is UNVERIFIED. The CSV
   archive does exist on nseindia, but intent (who/why) is opaque and reported EOD post-move (taxonomy row 11,
   S/N "Low") — so even if backtestable, it's low-S/N. H9 is weaker than its rank-4 billing.
8. **Promoter-pledge history archive** — H3 needs it for the cross-regime gate; no doc confirms a free historical
   SAST/pledge source exists (probe was n=1 live-only). Likely forward-only, which demotes H3.
9. **"No news found" ≠ "no event"** — redteam flags survivorship in coverage but no doc specifies the denominator
   discipline (dead names stop filing). Needs to be a spine invariant, like the existing no-look-ahead rule.

## OVER-OPTIMISM CHECK (which claims die on contact with our sample + free-data latency)

- **H7 (corp-action euphoria top) is the ONLY genuinely clean backtestable claim — and it's still thinner than
  sold.** Ground-checked: corp_actions.csv = 1,509 rows 2006+, so it IS in-hand and cross-regime-capable, and it
  has NO news-feed dependency → no look-ahead-via-timestamp trap (ex-dates are clean dated facts). BUT: it
  widens F10 (n=31, −22% fwd-3m, *display-only*), and the honest risk is the opposite of optimism — with larger
  N the −22% likely *regresses toward controls* (F10's own falsifier). It's worth running precisely because it
  can KILL a thin survivor, not because it'll confirm. Also watch **F10-overlap / double-counting**: H7 and the
  existing F10 use the same corp_action events — re-running must not present the same finding twice as if
  independent confirmation.
- **H1/H2/H4/H6/H10/H11 are all forward-only and boom-only.** Each needs a dated+classified+directional feed we
  don't have, on a rare-event small sample, with the cross-regime gate almost certainly failing (no longterm
  feed). Realistically: descriptive/illustrative at best for years. Don't rank them as near-term.
- **Grand vision RUNG 3→4 (all-stocks TA×FA×news fusion):** redteam's "combinatorial collapse" is correct and
  decisive. Add the un-named killer: RUNG 3's quarterly fundamentals pull for ~2,000 names via screener (1
  worker + aggressive blocks) is a multi-DAY fragile grind to REFRESH every quarter — an unbounded operational
  SLA for a single owner. The fundamentals freshness problem alone sinks RUNG 3 as a personal project.
- **The deepest over-optimism is structural (redteam nailed it):** news edge = SPEED we can't have. Daily, free,
  public, thrice-daily alerts cannot be early on a reaction that decays in minutes. The only defensible framings
  are EXPLANATORY (label a move we already see) and SLOW-DRIFT (PEAD over weeks). Everything else is fantasy.

## HONEST BOTTOM LINE

**3 things genuinely worth doing:**
1. **Delivery-% conviction signal** (FREE, full history, backtestable NOW, no scraper, no LLM, no egress) — the
   missing daily proxy the mechanics doc needed. Test it like any signal; likely beats adding news at all.
2. **H7 corp-action euphoria top** (in-hand data, cross-regime, kills-or-keeps a thin survivor) — but run it as
   a falsification of F10, watch the overlap, and expect regression-to-control.
3. **RUNG 1 explanatory NSE-announcements context feed** — category-only, rule-based, local, `sm_isin`-keyed,
   ONE scraper, next-session-open actionability rule, "context NOT a signal" chip. Turns "+20%, cause unknown"
   into "+20% on a results filing." Touches no money number → can't break the moat.

**The 1 thing FIRST:** **Delivery-%** — it's the only item that is free, fully historical, backtestable today,
needs zero new fragile infra, and directly serves the conviction question news was being recruited to answer.
If it doesn't clear the bar, that's strong evidence the whole catalyst direction won't either.

**PARK:** RUNG 1 context feed (do it AFTER delivery-%, accept it's display-only); H9 block-deal (verify the
archive + intent-opacity before any work); H1/H2/H3/H4/H6/H10/H11 (forward-collect a raw dated feed quietly to
accrue history, but expect no clean verdict for 18–36 months).

**KILL (don't rabbit-hole):** all social/forum/Twitter/Telegram sentiment (permanent, ethos+ToS+pump-and-dump);
any hosted-LLM polarity (egress off a work laptop); RSS free-text → fuzzy-ISIN matching (re-opens the parked
F11 swamp); RUNG 3 all-stocks universe + RUNG 4 fusion (combinatorial false-discovery + unbounded fundamentals-
refresh SLA — the honesty moat dies operationally). F&O/OI for this universe: not applicable, state and move on.

**Is the whole thing positive-ROI for a single user?** Marginally, and only for the 3 above. Delivery-% and H7
pay off in weeks with zero new fragility. RUNG 1 pays in usefulness (honest explanation) but never in a money
number. Everything past RUNG 1 is negative-ROI for a solo owner: years-to-prove on a tiny rare-event sample,
multiplying weekly-breaking scrapers, against an edge we are structurally too slow to capture. Intellectually
interesting ≠ worth the maintenance tax.
