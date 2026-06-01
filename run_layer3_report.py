"""Layer 3 — Part A entry point. Load substrate -> compute all Tier-1 findings ->
write a self-contained HTML report to report/layer3_partA.html.

Run: PYTHONPATH=. python run_layer3_report.py
"""
from layer3 import spine, config
from layer3.report import assemble
from layer3.findings import (t7_benchmark, t1_base_rates, t2_survival, t6_sector,
                             t3_pop_fade, t5_ofs, t9_profitable, t8_drawdown,
                             n4_issue_size, n2_subscription, n3_demand_skew, n5_anchor,
                             n7_fundamentals, n8_accrual, n6_valuation,
                             n9_zombie, n10_migration, n11_sc_divergence, n12_banker, nonequity,
                             m1_exit_discipline, f_partial_exit, f_basket_dispersion, n13_fallen_angel,
                             f_lifecycle, n14_wipeout_anatomy, f_flip_trap, f_average_down, n15_clean_compounder)

# benchmark/coverage first (sets denominators), then the truths, then the gradients,
# then the enhancement findings, then the separate non-equity view last
FINDINGS = [t7_benchmark, t1_base_rates, t2_survival, n9_zombie, t6_sector,
            t3_pop_fade, n10_migration, t5_ofs, t9_profitable, t8_drawdown,
            n4_issue_size, n2_subscription, n3_demand_skew, n5_anchor,
            n7_fundamentals, n8_accrual, n6_valuation, n11_sc_divergence, n12_banker, n13_fallen_angel,
            n15_clean_compounder,
            m1_exit_discipline, f_partial_exit, f_basket_dispersion, f_average_down, f_lifecycle,
            n14_wipeout_anatomy, f_flip_trap, nonequity]

METHOD_NOTE = ("Method spine: maturity-gating (a horizon stat uses only IPOs old enough); distributions over "
               "means with N + Wilson CIs; competing-risks wipeout shown as a band; SME vs Mainboard never "
               "pooled; long-horizon (3y/5y) base rates carried by the 2006–19 cohort; min-N floor (N≥30 claim, "
               "≥10 hint) enforced — sub-floor cells suppressed. Base-rate tables use alpha vs <b>Nifty 50</b> "
               "for cross-segment consistency; Smallcap-250 alpha (alpha_sc_*) is in the data and used by the "
               "Part-B predictor's benchmark policy for small/micro caps, but not in these base-rate tables. "
               "<b>Alpha is measured from the LISTING price</b> (the price a public investor can actually buy at) "
               "vs Nifty over the same window — i.e. the secondary-market investor's market-adjusted return. The "
               "allottee additionally captures the listing-day pop, shown separately in T3 and as listing-gain. "
               "<b>Confirmatory vs exploratory:</b> the Tier-1 findings (T1/T2/T3/T5/T6/T7/T8/T9) are pre-registered "
               "confirmatory analyses; the mined N-series (N2–N12) are exploratory — treat their single-slice "
               "results as hypotheses (multiple-comparisons caution), and lean on cross-regime validation (run_validation.py).")


def main():
    df = spine.load_substrate()
    results = []
    for mod in FINDINGS:
        try:
            results.append(mod.compute(df))
        except Exception as e:
            import traceback
            print(f"  ! {mod.__name__} FAILED: {e}")
            traceback.print_exc()
    subtitle = f"N = {len(df)} equity IPOs · boom (2020–25) + longterm (2006–19) · generated from ipo_analysis.csv"
    html = assemble(results, subtitle=subtitle, method_note=METHOD_NOTE)
    config.REPORT_DIR.mkdir(exist_ok=True)
    out = config.REPORT_DIR / "layer3_partA.html"
    out.write_text(html)
    print(f"wrote {out}  ({len(results)}/{len(FINDINGS)} findings, {out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
