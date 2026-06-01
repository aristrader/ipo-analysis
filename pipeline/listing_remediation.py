"""Layer-2 FIX 2 — listing-coverage remediation (shared by pipeline/07 and
scrapers/screener_prices_merge.py).

The computed listing_open/listing_gain are WRONG for ~123 stocks because either
  (a) a split is missing from corp_actions, so the adjusted price series is on a
      different scale than the (unadjusted) issue_price → a fake ~-90% "crash"
      in listing_gain (issue_price not divided by the missing split factor), or
  (b) the price series does not truly start at listing (data begins years later),
      so the "listing_open" we picked is just the first available price, unrelated
      to the real listing.

Remediation keys off the Chittorgarh RAW listing_open (the authoritative listing
quote) vs the computed listing_open:

    implied_factor = chittorgarh_listing_open / computed_listing_open

  * implied_factor in [1.5, 12] AND the stock has NO corp_actions entry
    (by ISIN or NSE symbol)  -> UNRECORDED SPLIT.
      adj_issue = issue_price / implied_factor, then RECOMPUTE all issue-anchored
      metrics (return_from_issue_*, current_return_from_issue, max_gain_pct,
      outcome_class, listing_gain_open/close).  status = 'inferred_split'.

  * implied_factor > 12, OR Chittorgarh listing_open missing, OR (bhavcopy_daily
    stock whose price file MIN date is >30d after listing_date)  -> bad coverage.
      NULL listing_open/close + listing_gain_open/close.  status =
      'unreliable_coverage'.  Lifetime current_return is kept ONLY if the price
      series is post-issue-reliable (series starts <=30d after listing); else it
      and the issue-anchored horizons are nulled too.

  * otherwise status = 'ok'.

The caller passes the already-computed `out` dict plus context; this function
mutates `out` in place and returns the status string.
"""

def _outcome_class(cr):
    if cr is None:
        return None
    if cr <= -0.90:
        return 'wipeout'
    if cr < -0.20:
        return 'loser'
    if cr < 0.20:
        return 'flat'
    if cr < 1.00:
        return 'winner'
    return 'multibagger'


def remediate_listing(out, *, chittor_listing_open, chittor_listing_close,
                      has_action, listing_date, data_first, price_source,
                      horizons, recovered=None):
    """Mutate `out` in place per FIX 2; return listing_metrics_status.

    Args:
      out: computed metrics dict (listing_open/close, listing_gain_*,
           issue_price, issue_price_adj, return_from_issue_*, current_price,
           current_return_from_issue, max_gain_pct, all_time_high, outcome_class).
      chittor_listing_open/close: Chittorgarh RAW listing quote (float or None).
      has_action: bool, stock has a corp_actions entry (by ISIN or NSE symbol).
      listing_date: date or None.
      data_first: first (min) date of the price series, or None.
      price_source: 'bhavcopy_daily' | 'screener_weekly' | ...
      horizons: list of (label, days) for the return_from_issue_* columns.
    """
    issue_price = out.get('issue_price')

    # ----- branch 0: recovered BSE-bhavcopy listing day (authoritative, cross-checked).
    # Use it for listing metrics; the (possibly late-starting) price series still drives
    # horizon/issue metrics, which compute() already nulled where data is absent. We do
    # NOT null anything here — the recovery IS the remediation.
    if recovered is not None and recovered.get('open'):
        # recovered open/close are RAW (at-listing) bhavcopy prices; issue_price is also
        # raw → listing_gain is raw/raw (scale-invariant, correct even with later splits).
        # We STORE listing_open on the adjusted (current) scale for consistency with the
        # adjusted price series + 09's adj_listing_open: adj = raw / (issue_price/issue_adj).
        iss_raw = out.get('issue_price')
        iss_adj = out.get('issue_price_adj')
        factor = (iss_raw / iss_adj) if (iss_raw and iss_adj) else 1.0
        lo_raw = recovered['open']
        lc_raw = recovered.get('close') or lo_raw
        out['listing_open'] = lo_raw / factor
        out['listing_close'] = lc_raw / factor
        out['listing_gain_open'] = (lo_raw / iss_raw - 1) if (lo_raw and iss_raw) else None
        out['listing_gain_close'] = (lc_raw / iss_raw - 1) if (lc_raw and iss_raw) else None
        return 'recovered_bhavcopy'

    computed_open = out.get('listing_open')

    implied_factor = None
    if chittor_listing_open and computed_open and computed_open != 0:
        implied_factor = chittor_listing_open / computed_open

    # coverage gap: bhavcopy series begins >30d after listing => listing_open we
    # picked is not the real listing price
    coverage_gap = (
        price_source == 'bhavcopy_daily'
        and listing_date is not None and data_first is not None
        and (data_first - listing_date).days > 30
    )

    # ----- branch 1: unrecorded split (recompute issue-anchored on adj_issue)
    if (implied_factor is not None and 1.5 <= implied_factor <= 12
            and not has_action):
        adj_issue = (issue_price / implied_factor) if issue_price else None
        old_anchor = out.get('issue_price_adj')  # the adj_issue used by the caller's compute()
        out['issue_price_adj'] = adj_issue
        lo, lc = out.get('listing_open'), out.get('listing_close')
        out['listing_gain_open'] = (lo / adj_issue - 1) if (lo and adj_issue) else None
        out['listing_gain_close'] = (lc / adj_issue - 1) if (lc and adj_issue) else None
        # Every issue-anchored metric was computed as (close/old_anchor - 1). Re-anchor
        # to adj_issue exactly: (1+r)*old_anchor/adj_issue - 1 == close/adj_issue - 1.
        # (old_anchor == issue_price here, since the no-recorded-action stock had factor 1.)
        if old_anchor and adj_issue:
            scale = old_anchor / adj_issue
            for label, _ in horizons:
                k = 'return_from_issue_%s' % label
                v = out.get(k)
                if v is not None:
                    out[k] = (1.0 + v) * scale - 1.0
            cr = out.get('current_return_from_issue')
            if cr is not None:
                out['current_return_from_issue'] = (1.0 + cr) * scale - 1.0
            mg = out.get('max_gain_pct')
            if mg is not None:
                out['max_gain_pct'] = (1.0 + mg) * scale - 1.0
        out['outcome_class'] = _outcome_class(out.get('current_return_from_issue'))
        return 'inferred_split'

    # ----- branch 2: unreliable coverage (NULL listing metrics)
    # implied_factor > 12 = unrecorded split too large to trust; chittor missing =
    # nothing to anchor to; coverage_gap = series starts long after listing.
    # ALSO: a strong INVERSE divergence (computed listing_open ~2x the Chittorgarh
    # raw quote) with no recorded corp action means our "listing_open" is on the
    # wrong scale / the series doesn't truly start at the recorded listing_date
    # (e.g. Wonderla: recorded listing_date is months off from the real one) — the
    # listing quote can't be trusted, so null it.
    scale_inverted = (implied_factor is not None and implied_factor < 0.6
                      and not has_action)
    if (implied_factor is not None and implied_factor > 12) \
            or (chittor_listing_open is None) or coverage_gap or scale_inverted:
        out['listing_open'] = None
        out['listing_close'] = None
        out['listing_gain_open'] = None
        out['listing_gain_close'] = None
        for label, _ in horizons:
            out['return_from_listing_%s' % label] = None
            out['alpha_%s' % label] = None
        # keep lifetime current_return only if the series is post-issue-reliable
        # (starts within 30d of listing); otherwise null the issue-anchored metrics
        post_issue_reliable = (
            listing_date is not None and data_first is not None
            and (data_first - listing_date).days <= 30
        )
        if not post_issue_reliable:
            out['current_return_from_issue'] = None
            out['max_gain_pct'] = None
            out['outcome_class'] = None
            for label, _ in horizons:
                out['return_from_issue_%s' % label] = None
        return 'unreliable_coverage'

    return 'ok'
