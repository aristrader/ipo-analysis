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

## Status
Discussion saved (this file). Blind calls NOT yet graded against the +70% (owner can say "grade").
6-hour work batch: owner to specify; likely starts with #1 (banker-flag fix, cheap+backtestable)
and/or the delivery-% data pull. Runs through the standard execution pipeline.
