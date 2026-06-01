"""M1 — Exit discipline & stop-losses (the movement lens).

The user's question, made a base rate: "was the stock ever profitable — did it ever give an exit
chance even if it dipped below the price; if so, what would a take-profit (break-even / +X%) have
captured? And does a stop-loss protect you or just stop you out of names that recover?"

Everything here is split by ENTRY because the answer depends on how you got in:
  • allottee  (entry='issue')   — you also own the listing pop.
  • secondary (entry='listing') — you buy on listing day; the pop is already gone.

Built on within-horizon peak/trough (MFE/MAE), so it is movement-based, not a single endpoint.
HONESTY: reaching a level = the move was *available*; capturing it needs timing. The stop-loss is
modelled SL-only (no take-profit interaction) so it's unambiguous from MAE; a combined TP+SL would
be order-ambiguous (MFE/MAE don't tell us which was touched first) and is deliberately not shown.
"""
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding

ENTRIES = [("issue", "allottee"), ("listing", "secondary")]


def compute(df):
    tables, charts, caveats = [], [], []

    # --- 1. Take-profit / break-even exit ladder, segment × cohort × entry (1y) ---
    rows = []
    for seg in config.SEGMENTS:
        for cohort in config.COHORTS:
            sub = spine.maturity_gated(spine.segment(df, segment=seg, cohort=cohort), "1y")
            for entry, elab in ENTRIES:
                if entry == "listing":
                    sub = sub[sub.get("listing_metrics_status") != "unreliable_coverage"] \
                        if "listing_metrics_status" in sub.columns else sub
                es = spine.exit_strategy(sub, entry=entry, horizon="1y")
                if es["n"] < config.MIN_N_HINT:
                    continue
                r = {"segment": seg, "cohort": cohort, "entry": elab, "N": es["n"],
                     "ever_gave_exit_%": es["pct_ever_gave_an_exit"]}
                for lad in es["ladder"]:
                    if lad["exit_rule"] in ("break-even", "+20%", "+50%"):
                        r[f"{lad['exit_rule']}: got"] = lad["pct_got_the_exit"]
                        r[f"{lad['exit_rule']}: mean"] = lad["mean_captured_%"]
                rows.append(r)
    tables.append(("Take-profit / break-even exit discipline (1y, maturity-gated). 'ever_gave_exit' = "
                   "share that traded at/above the buyer's entry at some point (the chance to get out "
                   "flat-or-better). For each target: 'got' = % that ever touched it; 'mean' = the "
                   "rule's average return (exit at the target if touched, else hold to year-end). "
                   "Allottee numbers include the listing pop; secondary do not.",
                   pd.DataFrame(rows)))

    # --- 2. Stop-loss base rates: does cutting at −X% protect, or stop you out of recoverers? (1y) ---
    sl_rows = []
    for seg in config.SEGMENTS:
        sub = spine.maturity_gated(spine.segment(df, segment=seg, cohort="boom"), "1y")
        for entry, elab in ENTRIES:
            s = sub
            if entry == "listing" and "listing_metrics_status" in s.columns:
                s = s[s["listing_metrics_status"] != "unreliable_coverage"]
            sl = spine.stop_loss_strategy(s, entry=entry, horizon="1y")
            if sl["n"] < config.MIN_N_HINT:
                continue
            for lad in sl["ladder"]:
                sl_rows.append({"segment": seg, "entry": elab, "N": sl["n"],
                                "stop": lad["stop_rule"],
                                "stopped_out_%": lad["pct_stopped_out"],
                                "of_those_recovered_%": lad["stopped_but_recovered_%"],
                                "stop_saved_%": lad["stop_saved_%"],
                                "mean_with_stop_%": lad["mean_with_stop_%"],
                                "vs_buy_hold_mean_%": sl["buy_hold_mean_%"]})
    tables.append(("Stop-loss base rates (boom cohort, 1y, maturity-gated). 'stopped_out' = % that "
                   "touched −X% (so a stop would fire). 'of_those_recovered' = of the stopped names, "
                   "the share that ENDED above the buyer's entry anyway — i.e. the stop booked a loss "
                   "on a name that came back (the cost). 'stop_saved' = of the stopped names, the share "
                   "whose year-end was even worse than −X% (the benefit). Compare 'mean_with_stop' to "
                   "'vs_buy_hold' to see whether the stop helped on average.",
                   pd.DataFrame(sl_rows)))

    # --- 3. Allottee-vs-secondary reach wedge: how much upside is just the pop? (MB boom, 1y) ---
    sub = spine.maturity_gated(spine.segment(df, segment="MB", cohort="boom"), "1y")
    subL = sub[sub.get("listing_metrics_status") != "unreliable_coverage"] \
        if "listing_metrics_status" in sub.columns else sub
    ai, al = spine.reach_curve(sub, "1y", entry="issue"), spine.reach_curve(subL, "1y", entry="listing")
    wedge = []
    for u_i, u_l in zip(ai["reach_up"], al["reach_up"]):
        wedge.append({"reached_at_least": u_i["move"],
                      "allottee_%": u_i["pct_reached"], "secondary_%": u_l["pct_reached"]})
    tables.append((f"Reach wedge — allottee (from issue, N={ai['n']}) vs secondary (from listing, "
                   f"N={al['n']}): chance the price TOUCHED each level within 1y. The gap is the "
                   "listing-pop head-start the secondary buyer never gets.", pd.DataFrame(wedge)))

    caveats += [
        "TAUTOLOGY WARNING (secondary entry): for the secondary buyer the 'ever gave an exit ≥ break-even' "
        "is mechanically 100% and the break-even take-profit row is mechanically 0.0% — because the listing "
        "day itself is inside the window, so the price 'touched' its own listing close on day one. Only the "
        "PROFIT targets (+20/+50%) are informative for the secondary buyer; the allottee's break-even (<100%, "
        "mean ≠ 0) IS informative because a from-issue day-1 high can sit below the issue price.",
        "Reaching a level = the move was AVAILABLE, not booked — capturing it needs timing you didn't "
        "model. That's why every exit number is paired with the buy-and-hold mean.",
        "Stop-loss is modelled SL-only (no take-profit). A combined take-profit+stop-loss is "
        "order-ambiguous from MFE/MAE (we can't tell which was touched first) and is deliberately omitted.",
        "Stop-loss table is boom-cohort only for cleaner entry coverage; the SIGN (tight stops hurt the "
        "secondary buyer via whipsaw) should be re-checked on the longterm cohort before trusting it.",
        "Secondary-entry cuts exclude `unreliable_coverage` listing rows (bad listing-day prices).",
        "~75 split-remediated rows (flag `mfe_mae_clamped=1`, mostly screener-weekly SME) have their peak/trough "
        "FLOORED at the endpoint return (the listing-split rescaling hits returns but not the raw price series), so "
        "their reach/exit upside is conservatively understated, never overstated.",
        "Reconcile with T8's forward-recovery table: SHALLOW dips (−10%) recover often, so a tight stop whipsaws "
        "you out of recoverers (it hurts); DEEP troughs (≤−30%) rarely recover by year-end, so a deep stop seldom "
        "cuts a winner — yet it still doesn't beat holding on the mean, because the few survivors' upside pays for "
        "the rest. Net: no single stop level is a free lunch.",
        "CROSS-REGIME nuance (checked on longterm 2026-06-01, so we don't over-claim): 'no stop beats buy-and-hold' "
        "holds wherever IPOs show their characteristic RIGHT TAIL — boom (both segments) and SME — and tight −10% "
        "stops HURT the secondary buyer there (robust). BUT in MB/longterm — a net-LOSING, tail-less cohort — stops "
        "DO beat hold, by the SAME mechanism as the partial-exit paradox: exits/stops trade the tail for the body, "
        "so they help only when there's no tail to protect. So the validated truth is the MECHANISM, not a blanket "
        "'stops never help'. A stop is a bet that this IPO has no right tail — true for the median name, false for "
        "the cohort's average.",
    ]
    narrative = ("Beyond 'where did it end up' — did the IPO ever give you a chance to get out at "
                 "break-even or a profit, what would a take-profit rule have captured, and would a "
                 "stop-loss have protected you or whipsawed you out of a name that recovered? All split "
                 "by whether you were an allottee (own the pop) or a secondary buyer (bought at listing).")
    return Finding(id="m1", title="M1 · Exit discipline & stop-losses (allottee vs secondary)",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)
