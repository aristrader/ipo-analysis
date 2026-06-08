# Fujiyama & Park Medi — the "winners we under-rated" case (owner, 2026-06-08)

## The real-world fact
Owner BOUGHT both and is sitting on **~+70% on each**. Both listed FLAT/NEGATIVE then ran up over
weeks. Our genuine, de-biased, point-in-time calls were:
- **Fujiyama Power Systems** (MB, listed 2025-11-20, GMP~0, sub 2.1×): score 70.4, 0 flags → **APPLY** ✓ (we DID catch it)
- **Park Medi World** (MB Healthcare, listed 2025-12-17, GMP 18.5%, sub 8.1×): score 65.5 (top-quintile)
  BUT 1 flag = *obscure lead manager* → **NEUTRAL** ✗ (knocked down by the flag; we'd have hesitated)
Neither was flagged as a *strong* winner, and the ~70% came as POST-LISTING drift our one-shot
apply/avoid never captures. (Calls verified unbiased: re-fitting weights/cutoffs on prior-only data
left both calls unchanged — Fujiyama APPLY, Park NEUTRAL.)

## THE QUESTION (owner): what checks/dimensions are we MISSING that would have caught these?
Demand signals were NOT predictive here (Fujiyama GMP~0/sub 2.1× was weak yet ran; Park's strength
was real but the banker flag vetoed it). So the missing edge is elsewhere. Candidate hypotheses to
research (this is the seed for the next work — NOT yet tested):

1. **The "obscure lead manager" flag is too crude / size-blind.** It fires when the banker has <12
   IPOs in OUR window — penalizing large reputable mainboard IPOs whose banker is merely under-
   represented in our data. FIX TO TEST: size-aware (don't apply to large MB), or banker QUALITY
   (historical listing performance) not raw frequency. Park is the poster child. **HIGH priority,
   cheap, backtestable now.**
2. **No post-listing MOMENTUM / strength signal.** Our score is a one-time IPO-decision; the 70%
   was a post-listing run after a dull open. We have day-21 persistence + day-90 capitulation
   leans, but no "this dull-lister is now building strength — get in / add" signal. Ties directly
   to the news/delivery-% threads + the TA dimension of the north-star.
3. **Sector / fundamental tailwind not captured.** Healthcare (Park) and power/industrials
   (Fujiyama) may have had sector momentum or fundamental quality that demand signals miss. The FA
   dimension of the north-star.
4. **Listing-day pop ≠ the real outcome.** Both listed negative then ran — our scorecard / calls
   lean on near-listing behavior; a signal for "negative-pop-then-recovery" winners is unexplored
   (note: dip-buy was rejected, but THIS is recovery-AFTER-a-dull-LISTING, a different thing —
   re-scope carefully vs the F1/T2e graveyard).

## How this connects
This case is the concrete motivation for the **TA + FA + news fusion** north-star
(`newsfeed_opportunity_map.md`): demand-signal IPO scoring missed these; what would've caught them
is post-listing technical strength + sector/fundamental context. Start small (the map's "do-first"
delivery-% + the banker-flag fix), prove a dimension at a time. **Scope-down decision pending.**

## GRADE — calls scored against realized outcome (2026-06-09; data as-of 2026-06-06 refresh)
Verdict logic (calls.py): APPLY = top-quintile AND 0 flags · AVOID = bottom-quintile OR ≥2 flags · else NEUTRAL.
Two entry lenses: ALLOTTEE buys at issue (adj); SECONDARY buys at listing close.

**Fujiyama (APPLY) → CORRECT ✓, but a white-knuckle hold.**
- Allottee +44.0% (₹1L→₹1.44L); secondary +57.5% (₹1L→₹1.58L). APPLY paid. (Owner's ~+70% is a further
  run AFTER our 2026-06-06 data window — current_price 328.3 here vs ~388 implied by +70% on issue 228;
  we grade only on data we have, no look-ahead.)
- PATH was brutal: −15.8% MAE by 3m, still −8.7% at 3m, −24.6% worst dip within 6m, peak only at **day 160**.
  ~5 months underwater. alpha_6m +36.6% once it ran. The call was directionally right; the journey would
  shake out anyone without conviction — and our scorecard gave no "hold through this" signal.

**Park (NEUTRAL) → A MISS ✗ — and a diagnosable, fixable one (this is the headline).**
- Allottee +73.9% (₹1L→₹1.74L); secondary +90.4% (₹1L→₹1.90L). Clear winner; alpha_3m +43.8%.
- **The NEUTRAL came SOLELY from the obscure-banker flag.** Park was top-quintile with exactly 1 flag →
  blocked from APPLY (needs flags==0), not bad enough for AVOID → NEUTRAL. Strip that one flag → top-quintile,
  0 flags → **APPLY**. The flag fired because **Nuvama Wealth Management had 10 prior IPOs in our window
  (10 < 12 threshold)** — but Nuvama (ex-Edelweiss) is a top-tier Indian merchant banker. The flag measured
  *"under-represented in OUR dataset,"* not *"low quality."* A pure false positive. (Fujiyama's banker Motilal
  Oswal had 14 prior → no flag → clean APPLY. Threshold-luck, not skill.)
- **Regret: NEUTRAL→hesitate cost ≈ ₹74k upside per ₹1L applied (allottee).** The single most actionable miss.
- Bitter irony: Park's PATH was the GENTLER of the two (−14.8% MAE, ran by day 83, max DD only −9.6%) AND the
  bigger winner — yet it's the one we waved off, while we APPLY'd the harder hold (Fujiyama).

**Two concrete targets the grade produces (for the 6-hr batch):**
1. **Banker flag = frequency-in-our-window, not quality.** Penalizes reputable banks under-represented in our
   data (Nuvama, and likely others). FIX: size/recognition-aware (don't fire on large MB) OR banker LISTING-
   PERFORMANCE quality, not raw count. Park is the proof case. HIGH priority, cheap, backtestable now.
2. **The win was POST-LISTING drift** (both listed −8.6/−8.7%, then ran over weeks). Our one-shot APPLY/AVOID
   structurally can't capture it; argues for the post-listing momentum signal (candidate #2).

## Status
Discussion saved + calls GRADED (above). Headline: Fujiyama APPLY was right (rough ride); Park NEUTRAL was a
~₹74k/₹1L MISS caused by the banker flag false-positiving on Nuvama. 6-hour work batch: owner to specify;
the grade sharpens #1 (banker-flag fix) as the clear do-first. Runs through the standard execution pipeline.
