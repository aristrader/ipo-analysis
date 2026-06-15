# Enhancing the portfolio / per-stock / scorecard MVPs — the serious-investor lens

_What would make these genuinely decision-grade, not just summary numbers. Lens: a serious retail IPO
investor's money. Each idea: what · why · feasibility from data we HAVE · effort · ethos. Ranked by
value/effort at the end. Traps flagged. No new data, no ML, survivorship-honest. Not financial advice._

Data on hand: ledger has isin/name/type/mode/call_type/call_date/score/score_quintile/tape_state/
crowding_pctl/alpha_1m,3m,1y. Substrate has sector/broad_sector/issue_size_cr/market_cap_class/dates/
outcome_class/delisted + per-horizon alpha & **mfe/mae** (peak/trough) & days_to_mfe/mae. Per-ISIN daily
adjusted prices exist. So curves, drawdown, attribution, regime cuts are all derivable from owned data.

## A. ₹1L portfolio simulator — into its 2nd/3rd dimension
1. **Real equity CURVE over time (not just endpoint multiple).** Stitch each APPLY position's daily
   ₹-value (capital × close/entry) onto a common calendar, sum across open positions, plot the basket
   vs same-dated Nifty. WHY: the owner sees the *path* — the 2022 drawdown, the recovery — not one number.
   FEASIBLE: prices per ISIN + listing_date already drive growth_of_1l; just aggregate across the ledger.
   Effort **M**. Ethos ✓. TRAP: a "lump-sum at t0" curve is fiction (calls arrive over years) — must use
   **capital-deployed-as-calls-arrive** accounting (see #4), else it overstates compounding.
2. **Max drawdown + time-under-water on the basket curve.** Peak-to-trough % and longest recovery gap.
   WHY: the single most decision-relevant risk number a retail investor feels; endpoint multiple hides it.
   FEASIBLE: trivial once #1's curve exists. Effort **S** (rides on #1). Ethos ✓.
3. **Best/worst position attribution — which picks made/lost the money.** Rank positions by ₹ P&L
   contribution; show top-5 winners / bottom-5 losers with name, mode, ₹ gained/lost, hold length.
   WHY: tells the owner whether returns are broad or one-Trent-carries-everything (concentration risk),
   and surfaces the wipeouts. FEASIBLE: simulate() already yields per-position values — just diff vs ₹1L
   and sort. Effort **S**. Ethos ✓ (honest about right-tail dependence). TRAP: pooling modes — keep split.
4. **Capital-as-it-arrives vs lump-sum (money-weighted / XIRR).** Deploy ₹1L on each call_date as the
   call fires; compute a money-weighted return (IRR over the dated cashflows) alongside the naive equal
   ₹1L multiple. WHY: this is what the owner's brokerage actually shows; equal-weight endpoint flatters
   old big winners. FEASIBLE: call_date + entry/exit dates + prices → dated cashflows → IRR (numpy/pure
   bisection, no ML). Effort **M**. Ethos ✓.
5. **"₹1L/month SIP into APPLYs" view.** Fixed monthly budget split across that month's APPLY calls;
   track units, plot vs a Nifty SIP. WHY: matches how a salaried investor actually funds IPOs (cashflow,
   not infinite capital); shows whether disciplined drip-buying beats index SIP. FEASIBLE: group ledger
   by month, allocate budget, value forward from prices. Effort **M**. Ethos ✓. TRAP: months with zero
   APPLYs must roll cash forward (idle cash), not vanish — else it fakes always-invested.
6. **Counterfactual toggles: "skip the AVOIDs" / "only top-decile score" / "every IPO baseline".**
   Re-run the basket under alternate selection rules side by side. WHY: directly answers "did my calls
   add value vs just buying everything?" — the only honest proof the rating earns its keep. FEASIBLE:
   filter ledger by call_type/score_quintile, reuse the same sim. Effort **S** (config flag on sim).
   Ethos ✓ — this is the integrity test. TRAP: tiny live N → label clearly, lean on backfilled/sim.

## B. Per-stock growth-of-₹1L chart — decision-grade reference layers
7. **Mark the peak (MFE) and trough (MAE) with date + "if you'd sold here" annotation.** WHY: shows the
   timing tax — the gap between best-exit and hold-to-today — concretely on the owner's chart. FEASIBLE:
   mfe_lst_*/mae_lst_* + days_to_* already in substrate; just plot the points. Effort **S**. Ethos ✓.
8. **Add issue-price & break-even reference lines + the call_date marker.** Horizontal line at ₹1L
   (break-even) and at issue-vs-listing entry; a vertical rule on the date the call was made. WHY:
   instant read of "am I above water" and "what did the tool say, when". FEASIBLE: scalars on hand.
   Effort **S**. Ethos ✓.
9. **Sector-median analog band ("typical IPO like this").** Shade the P25–P75 growth band of same-sector
   same-segment IPOs behind the stock's line. WHY: is THIS IPO a star or just riding a hot sector? Pure
   analog — exactly the tool's no-ML ethos. FEASIBLE: substrate sector + per-ISIN prices; precompute
   sector cohort curves. Effort **L** (alignment by trading-day-since-listing across cohort). Ethos ✓✓.
   TRAP: align by *days-since-listing*, not calendar date, or you mix regimes; show N of the band.

## C. Were-we-right scorecard — cuts a sceptic demands
10. **"Beat buying every IPO" baseline column.** Next to APPLY hit-rate/median-α, show the same metric
    for the *whole field* in that window. WHY: APPLY +13% is only impressive if the field wasn't +13%
    too; this is the honest benchmark. FEASIBLE: substrate field median by window vs ledger APPLY subset.
    Effort **S**. Ethos ✓✓ (THE credibility cut).
11. **Cut by sector / issue-size band / segment.** Scorecard sliced by broad_sector, issue_size_cr
    tertile (small/mid/large), MB vs SME. WHY: reveals where the edge lives and where it's noise — owner
    can trust calls selectively. FEASIBLE: join ledger.isin → substrate cuts. Effort **M**. Ethos ✓
    (min-N floor + Wilson CI already in calibration.py — reuse). TRAP: slicing explodes N → many cells
    hit the floor; show CI, grey out sub-floor cells, never rank on n<10.
12. **Cut by tape regime + recent-vs-old.** Scorecard split by tape_state (already in ledger) and by
    call_date era (≤2023 vs 2024+). WHY: did the edge survive the cold tape / is it decaying? FEASIBLE:
    ledger has tape_state + call_date. Effort **S**. Ethos ✓.
13. **Calibration over time (is the score *still* well-ordered?).** score_reliability() but windowed by
    year. WHY: catches signal decay early. FEASIBLE: reuse score_reliability per era. Effort **S**.
    Ethos ✓. TRAP: per-year N is thin live — lean on backfilled/sim, label mode.

## Traps to avoid (survivorship & framing)
- **Lump-sum-at-day-0 basket curve** — fakes compounding from capital you didn't have; use dated arrival.
- **Pooling modes / pooling MB+SME** — evidence strength & base rates differ; always split (house rule).
- **Endpoint multiple as the hero** — hides drawdown & path; pair every multiple with #2 max-DD.
- **Delisted/stale positions vs a fresh-dated Nifty** — already fixed in portfolio.py (anchor bench to
  exit_date); preserve that when aggregating the curve.
- **Survivorship in the analog band (#9)** — include delisted/wipeout cohort members or the band lies up.
- **Ranking on sub-floor cells (#11)** — Wilson CI + min-N floor, grey out, never headline a thin cell.
- **SIP view dropping zero-APPLY months** — roll idle cash, or it pretends to be always invested.

## Ranked by value-per-effort (top first)
1. **#10 "beat every IPO" baseline** (S, ✓✓) — the one cut that proves the calls add value.
2. **#3 best/worst attribution** (S) — surfaces concentration & wipeouts; nearly free off simulate().
3. **#6 counterfactual toggles** (S) — skip-AVOID / top-decile / buy-all; the integrity test.
4. **#1+#2 equity curve + max drawdown** (M) — the path & the felt risk; unlocks #4/#5.
5. **#11 scorecard by sector/size/segment** (M) — where the edge actually lives.
