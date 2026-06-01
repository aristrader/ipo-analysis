"""Predictor orchestration: a NEW IPO's features -> analog cohort -> outcome distribution +
scorecard + named comparables + a plain-language 'what to expect'. Transparent, no forecast of
the query's own number — only "this is what N similar past IPOs did."
"""
import pandas as pd
from layer3 import spine, config
from layer3.predictor import analogs, scorecard


def predict(query, df=None, profile="balanced", k=50):
    if df is None:
        df = spine.load_substrate()
    ar = analogs.find_analogs(query, df=df, k=k, exclude_isin=query.get("isin"))
    cohort = ar["cohort"]
    sc = scorecard.scorecard(query, cohort, ar, profile=profile, df=df)

    # outcome distribution of the cohort (maturity-gated 3y, fallback 1y)
    h = "3y" if len(spine.maturity_gated(cohort, "3y")) >= config.MIN_N_HINT else "1y"
    gm = spine.maturity_gated(cohort, h)
    dist = spine.distribution(spine.alpha_series(gm, h))
    wb = spine.wipeout_band(cohort)

    # named comparables (closest 10) with their realized outcome
    cols = ["isin", "company_name", "type", "cohort", "broad_sector", "market_cap_class",
            "listing_date", f"alpha_{h}", "outcome_class", "analog_distance"]
    named = cohort[[c for c in cols if c in cohort.columns]].head(10).copy()

    return {"query": query, "profile": profile, "analog": ar, "scorecard": sc,
            "distribution": {"horizon": h, **dist}, "wipeout_band": wb,
            "outcome_profile": spine.outcome_profile(cohort, h),
            "outcome_breakdown": spine.outcome_breakdown(cohort, h),
            "wipeout_flags": scorecard.wipeout_flags(query, df=df),
            "risk_assessment": scorecard.risk_assessment(query, df=df),
            "reach_curve": spine.reach_curve(cohort, "1y"),
            "reach_curve_h": spine.reach_curve(cohort, h),
            "named_analogs": named}


def _pct(x):
    return "—" if x is None else f"{100*x:+.0f}%"


def format_text(r):
    sc = r["scorecard"]; conf = sc["confidence"]; d = r["distribution"]; ar = r["analog"]
    q = r["query"]
    L = []
    L.append("=" * 64)
    L.append(f"IPO SCORECARD — {q.get('name', q.get('type','?')+' IPO')}  [{q.get('type')}, "
             f"{q.get('broad_sector','sector?')}, {q.get('market_cap_class','mcap?')}]")
    L.append("=" * 64)
    L.append(f"Analogs: {ar['n_cohort']} similar past IPOs  (gate: {ar['rung_label']}; "
             f"{'RELAXED — ' if ar['relaxed'] else ''}confidence: {conf['label'].upper()})")
    if ar.get("sector_note"):
        L.append(f"  note: {ar['sector_note']}")
    if ar["n_cohort"] < config.MIN_N_HINT:
        L.append("  ⚠ INSUFFICIENT ANALOGS — treat everything below as a weak hint, not a base rate.")
    L.append("")
    L.append("COMPONENT SCORES (0–100):")
    names = {"return_potential": "Return potential", "multibagger_odds": "Multibagger odds",
             "downside_safety": "Downside safety", "liquidity": "Liquidity", "quality": "Quality",
             "tradeable_upside": "Tradeable upside", "wipeout_safety": "Wipeout-safety"}
    for k, c in sc["components"].items():
        s = c.get("score")
        w = sc.get("weights", {}).get(k, 0)
        zero = "  [weight 0 — shown, NOT in combined score]" if (s is not None and not w) else ""
        L.append(f"  {names[k]:18s}: {('%5.0f' % s) if s is not None else ' n/a '}  "
                 + _component_detail(k, c) + zero)
    L.append("")
    L.append(f"  >> COMBINED ({sc['profile']}): "
             f"{sc['combined_score'] if sc['combined_score'] is not None else 'n/a'} / 100")
    # calibration readout: where this score falls + what that meant historically (validated)
    from layer3.predictor import weights as _W
    cal = _W.load_calibration()
    cs = sc.get("combined_score")
    if cal and cs is not None:
        q = cal["score_quintiles"]; quint = sum(cs >= t for t in q) + 1   # 1..5
        L.append(f"  calibration: score {cs} → quintile {quint}/5 (thresholds {q}). In-sample, top-quintile-score "
                 f"IPOs led the field by ~+{cal['top_quintile_lift_pp']}pp (INDICATIVE — in-sample weights, partly "
                 f"vintage sorting; NOT out-of-sample-validated; n={cal['n_scored']}).")
    L.append("")
    # wipeout-risk gauge (standalone, separate from the return score)
    ra = r.get("wipeout_flags") and r.get("risk_assessment") or {}
    if ra.get("risk_score_0_100") is not None:
        L.append("WIPEOUT-RISK: %.0f/100 (%s) — 50=typical for %s; SEPARATE from the return score above" % (
            ra["risk_score_0_100"], ra.get("risk_band"), ra.get("segment")))
    if ra.get("n_flags"):
        L.append("  🚩 %d red flag(s): %s" % (ra["n_flags"], "; ".join("%s (%s)" % (n, w) for n, w in ra["flags"])))
    elif ra.get("n_checked"):
        L.append("  ✓ no validated wipeout red flags among the %d checked" % ra["n_checked"])
    if ra.get("fail_rate_at_this_flag_load_%") is not None:
        L.append("  historically failed %s%% (basis %s) vs %s%% for a typical %s IPO" % (
            ra["fail_rate_at_this_flag_load_%"], ra.get("basis"), ra.get("segment_base_fail_%"), ra.get("segment")))
    for pf in ra.get("per_flag", []):
        L.append("    • %s: failed %s%% WITH vs %s%% without (N=%s)" % (
            pf["flag"], pf["failed_with_flag_%"], pf["failed_without_%"], pf["n_with"]))
    if ra.get("unknown"):
        L.append("  not checked (no input): %s — unknown ≠ safe" % ", ".join(ra["unknown"]))
    # the full-picture breakdown (ALL outcomes incl. failures)
    ob = r.get("outcome_breakdown", {})
    if ob.get("n"):
        b = ob["horizon_buckets"]
        L.append("")
        L.append("FULL PICTURE — what the %d most-similar IPOs did (by %s, from issue):" % (ob["n"], ob["horizon"]))
        L.append("   doubled+ %s | up20-100%% %s | flat %s | down %s" % (
            b.get("doubled+ (≥2x)_%"), b.get("up (20–100%)_%"), b.get("≈flat (±20%)_%"), b.get("down (<−20%)_%")))
        L.append("   best(P90) %s%%  |  base-rate(median) %s%%  |  worst(P10) %s%%" % (
            ob.get("best_case_p90_%"), ob.get("base_rate_median_%"), ob.get("worst_case_p10_%")))
        wbb = ob.get("terminal_wipeout_band_%", (None, None))
        L.append("   terminal risk: dead-money %s%% | wipeout band %s-%s%%" % (
            ob.get("terminal_dead_money_%"), wbb[0], wbb[1]))
        if r["query"].get("type") == "SME" and (ob.get("terminal_dead_money_%") or 0) >= 5:
            L.append("   🔑 SME dead-money rule: failure here is usually un-sellable dead money, not −100%; "
                     "those names gave an exit in YEAR 1 (~half hit +20%) then the float closed — treat the "
                     "first-year peak as the exit.")
    L.append("")
    L.append(f"WHAT {ar['n_cohort']} SIMILAR IPOs DID (alpha vs Nifty, {d['horizon']}, maturity-gated; N={d['n']}):")
    L.append(f"   median {_pct(d['median'])} | P10 {_pct(d['p10'])} → P90 {_pct(d['p90'])}")
    # distribution shape (a median can hide a barbell)
    import numpy as np
    av = spine.alpha_series(spine.maturity_gated(r["analog"]["cohort"], d["horizon"]), d["horizon"]).dropna()
    if len(av) >= config.MIN_N_HINT:
        edges = np.linspace(-1.0, 2.0, 9); cnt, _ = np.histogram(np.clip(av, -1.0, 2.0), bins=edges)
        blocks = "▁▂▃▄▅▆▇█"; mx = max(cnt) or 1
        spark = "".join(blocks[min(7, int(7 * c / mx))] for c in cnt)
        L.append(f"   shape −100%[{spark}]+200% alpha")
        deep, big = float((av < -0.3).mean()), float((av > 0.5).mean())
        if deep > 0.25 and big > 0.25:
            L.append(f"   ⚠ BIMODAL/barbell: {deep:.0%} deep-loss vs {big:.0%} big-win — the median describes NOBODY; "
                     "this IPO likely lands in one camp, not the middle.")
    L.append(f"   wipeout rate: {_pct(r['wipeout_band']['wipeout_lower_rate'])} – "
             f"{_pct(r['wipeout_band']['wipeout_upper_rate'])} (band)")
    rc = r.get("reach_curve", {})
    if rc and rc.get("n"):
        ladder = "  ".join(f"{u['move']}→{u['pct_reached']:.0f}%" for u in rc["reach_up"]
                           if u["pct_reached"] is not None)
        L.append(f"   REACH-WITHIN-1y (chance the price TOUCHED each level, from issue):")
        L.append(f"     {ladder}")
        L.append(f"     downside: " + "  ".join(f"{d['move']}→{d['pct_fell_to']:.0f}%" for d in rc["reach_down"]
                                                if d["pct_fell_to"] is not None))
        L.append(f"   → median peaked {rc['median_peak_pct']}%, dipped {rc['median_trough_pct']}%, but only "
                 f"{rc['pct_ended_positive']}% ENDED year 1 positive (you'd have to time the exit).")
    L.append("")
    L.append("CLOSEST COMPARABLES:")
    for _, a in r["named_analogs"].head(6).iterrows():
        ac = a.get(f"alpha_{d['horizon']}")
        oc = a.get("outcome_class")
        oc = str(oc) if pd.notna(oc) else "?"
        L.append(f"   {str(a.get('company_name'))[:34]:34s} {str(a.get('listing_date'))[:10]}  "
                 f"{oc:11s} α{d['horizon']}={_pct(ac if pd.notna(ac) else None)}")
    L.append("")
    L.append(f"CONFIDENCE: {conf['label'].upper()}  (analogs={conf['n_analogs']}, rung='{conf['ladder_rung']}', "
             f"3y-maturity-cov={_pct(conf['maturity_coverage_3y'])}, data-quality={conf['mean_data_quality_1to3']})")
    L.append(f"   analog recency: median listing year {conf.get('analog_median_listing_year')}, "
             f"{_pct(conf.get('analog_boom_frac'))} from the 2020+ boom era"
             + ("  ⚠ analogs are mostly OLD — different market era" if (conf.get('analog_boom_frac') or 1) < 0.3 else ""))
    L.append("This is what similar past IPOs did — NOT a forecast or a buy/sell recommendation.")
    return "\n".join(L)


def _component_detail(k, c):
    if c.get("score") is None:
        return f"(insufficient, N={c.get('n', 0)})"
    if k == "return_potential":
        return f"(median α{c['horizon']} {_pct(c['median_alpha'])}, N={c['n']})"
    if k == "multibagger_odds":
        ev = (f"; EVER touched 2x {_pct(c.get('pct_ever_2x'))}" if c.get('pct_ever_2x') is not None else "")
        return (f"({_pct(c['pct_2x_from_listing'])} ended 2x, {_pct(c['pct_5x_from_listing'])} ended 5x "
                f"from listing{ev}, N={c['n']})")
    if k == "downside_safety":
        return f"(wipeout≤{_pct(c['wipeout_upper'])}, below-issue {_pct(c['pct_below_issue'])})"
    if k == "liquidity":
        return f"({_pct(c['pct_investable'])} investable, N={c['n']})"
    if k == "quality":
        return f"({', '.join(c.get('factors', [])) or 'no fundamentals given'})"
    if k == "tradeable_upside":
        return (f"({_pct(c.get('pct_reached'))} ever touched {c.get('reach_level')} from {c.get('entry')}; "
                f"endpoint median {_pct(c.get('median_endpoint'))}, N={c['n']})")
    return ""
