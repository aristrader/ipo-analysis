"""Calls engine property tests: event anchors, thresholds, NO-LOOK-AHEAD, grading
immutability, idempotence, gap-fill equivalence (spec 2026-06-07-calls-engine-design.md)."""
import os
import pandas as pd
import pytest

from layer3 import calls


def _mini_df():
    return pd.DataFrame([
        {"isin": "INE0TEST1", "company_name": "A", "type": "MB", "cohort": "boom",
         "open_date": "2024-01-08", "close_date": "2024-01-10", "listing_date": "2024-01-15",
         "issue_price_adj": 100.0, "listing_metrics_status": "ok",
         "adj_listing_gain_open": 0.10},
        {"isin": "INE0TEST2", "company_name": "B", "type": "SME", "cohort": "boom",
         "open_date": "2024-02-05", "close_date": "2024-02-07", "listing_date": "2024-02-12",
         "issue_price_adj": 50.0, "listing_metrics_status": "ok",
         "adj_listing_gain_open": -0.05},
        {"isin": "INE0BAD03", "company_name": "C", "type": "MB", "cohort": "boom",
         "open_date": "2024-03-04", "close_date": "2024-03-06", "listing_date": "2024-03-11",
         "issue_price_adj": 10.0, "listing_metrics_status": "unreliable_coverage",
         "adj_listing_gain_open": 0.0},
    ])


def _pit():
    pit = pd.DataFrame([
        {"isin": "INE0TEST1", "score": 90.0, "n14_flags": 0},
        {"isin": "INE0TEST2", "score": 10.0, "n14_flags": 2},
    ])
    return calls.add_quintiles(pit, _mini_df())


# ---------------------------------------------------------------- events
def test_events_between_emits_all_anchor_types():
    ev = calls.events_between("2024-01-01", "2024-12-31", _mini_df(), corp_actions=pd.DataFrame())
    kinds = {e["kind"] for e in ev}
    assert {"verdict", "track", "persist", "capit"} <= kinds


def test_events_are_date_bounded_and_sorted():
    ev = calls.events_between("2024-01-01", "2024-01-31", _mini_df(), corp_actions=pd.DataFrame())
    dates = [e["date"] for e in ev]
    assert dates == sorted(dates)
    assert all("2024-01-01" <= d <= "2024-01-31" for d in dates)


def test_unreliable_coverage_excluded():
    ev = calls.events_between("2024-01-01", "2024-12-31", _mini_df(), corp_actions=pd.DataFrame())
    assert not any(e["isin"] == "INE0BAD03" for e in ev)


def test_trading_day_offset_uses_nifty_calendar():
    d = calls.td_offset(pd.Timestamp("2024-01-15"), 21)
    assert d is not None and d > pd.Timestamp("2024-02-09")


def test_corp_action_event_window():
    ca = pd.DataFrame([
        {"isin": "INE0TEST1", "symbol": "A", "action_type": "bonus", "ex_date": "2024-06-20"},
        {"isin": "INE0TEST1", "symbol": "A", "action_type": "split", "ex_date": "2027-01-01"},
    ])
    ev = calls.events_between("2024-01-01", "2024-12-31", _mini_df(), corp_actions=ca)
    cas = [e for e in ev if e["kind"] == "corp_action"]
    assert len(cas) == 1 and cas[0]["date"] == "2024-06-20"   # the >365d one excluded


# ---------------------------------------------------------------- make_call
def test_verdict_call_thresholds():
    pit = _pit()
    df = _mini_df()
    c1 = calls.make_call({"date": "2024-01-10", "kind": "verdict", "isin": "INE0TEST1",
                          "row": df.iloc[0]}, pit, df, prices_root="data/prices")
    assert c1["call_type"] == "APPLY"
    assert "score_q=" in c1["rules_fired"]
    c2 = calls.make_call({"date": "2024-02-07", "kind": "verdict", "isin": "INE0TEST2",
                          "row": df.iloc[1]}, pit, df, prices_root="data/prices")
    assert c2["call_type"] == "AVOID"
    for c in (c1, c2):
        assert c["grade_status"] == "pending"
        assert set(calls.LEDGER_COLUMNS) <= set(c.keys())


def _write_prices(tmp_path, isin, listing, closes):
    dates = pd.bdate_range(listing, periods=len(closes))
    pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "open": closes, "high": closes,
                  "low": closes, "close": closes, "volume": 1000}).to_csv(
        tmp_path / f"{isin}.csv", index=False)


def test_no_look_ahead_capit_ignores_future_rally(tmp_path):
    closes = [50.0] * 95 + [500.0] * 30          # never above issue(100) to d90; rallies AFTER
    _write_prices(tmp_path, "INE0TEST1", "2024-01-15", closes)
    df = _mini_df()
    ev_date = calls.td_offset(pd.Timestamp("2024-01-15"), 90).strftime("%Y-%m-%d")
    call = calls.make_call({"date": ev_date, "kind": "capit", "isin": "INE0TEST1",
                            "row": df.iloc[0]}, _pit(), df, prices_root=str(tmp_path))
    assert call["call_type"] == "EXIT_REVIEW"


def test_capit_cleared_when_above_issue(tmp_path):
    closes = [120.0] * 130
    _write_prices(tmp_path, "INE0TEST1", "2024-01-15", closes)
    df = _mini_df()
    ev_date = calls.td_offset(pd.Timestamp("2024-01-15"), 90).strftime("%Y-%m-%d")
    call = calls.make_call({"date": ev_date, "kind": "capit", "isin": "INE0TEST1",
                            "row": df.iloc[0]}, _pit(), df, prices_root=str(tmp_path))
    assert call["call_type"] == "CLEARED_ISSUE"


def test_persist_call_directions(tmp_path):
    up = [100 + i for i in range(40)]            # steadily up month-1
    _write_prices(tmp_path, "INE0TEST1", "2024-01-15", up)
    df = _mini_df()
    ev_date = calls.td_offset(pd.Timestamp("2024-01-15"), 21).strftime("%Y-%m-%d")
    call = calls.make_call({"date": ev_date, "kind": "persist", "isin": "INE0TEST1",
                            "row": df.iloc[0]}, _pit(), df, prices_root=str(tmp_path))
    assert call["call_type"] == "PERSIST_HOLD"
    down = [100 - i for i in range(40)]
    _write_prices(tmp_path, "INE0TEST2", "2024-02-12", down)
    ev2 = calls.td_offset(pd.Timestamp("2024-02-12"), 21).strftime("%Y-%m-%d")
    call2 = calls.make_call({"date": ev2, "kind": "persist", "isin": "INE0TEST2",
                             "row": df.iloc[1]}, _pit(), df, prices_root=str(tmp_path))
    assert call2["call_type"] == "PERSIST_EXIT_LEAN"


# ---------------------------------------------------------------- grading
def test_grade_immutability_and_horizons(tmp_path):
    closes = [100.0 + i * 0.5 for i in range(300)]
    _write_prices(tmp_path, "INE0TEST1", "2024-01-15", closes)
    df = _mini_df()
    led = calls.walk(df.iloc[[0]], _pit(), "2024-01-01", "2024-03-31",
                     mode="historical_sim", ledger=None, prices_root=str(tmp_path))
    g = calls.grade_calls(led, df, prices_root=str(tmp_path), today=pd.Timestamp("2026-01-01"))
    row = g[g["call_type"] == "APPLY"].iloc[0]
    assert pd.notna(row["alpha_1m"]) and row["grade_status"] == "final"
    # poison a final grade; re-grade must NOT touch it
    g.loc[g["call_type"] == "APPLY", "alpha_1m"] = 9.99
    g2 = calls.grade_calls(g, df, prices_root=str(tmp_path), today=pd.Timestamp("2026-01-01"))
    assert float(g2[g2["call_type"] == "APPLY"].iloc[0]["alpha_1m"]) == 9.99


# ---------------------------------------------------------------- walk
def test_walk_idempotent(tmp_path):
    df, pit = _mini_df(), _pit()
    l1 = calls.walk(df, pit, "2024-01-01", "2024-12-31", mode="historical_sim",
                    ledger=None, prices_root=str(tmp_path))
    l2 = calls.walk(df, pit, "2024-01-01", "2024-12-31", mode="historical_sim",
                    ledger=l1, prices_root=str(tmp_path))
    assert len(l2) == len(l1)
    assert l1["call_id"].is_unique


def test_gap_fill_equals_one_shot(tmp_path):
    df, pit = _mini_df(), _pit()
    a = calls.walk(df, pit, "2024-01-01", "2024-06-30", mode="historical_sim",
                   ledger=None, prices_root=str(tmp_path))
    a = calls.walk(df, pit, "2024-07-01", "2024-12-31", mode="historical_sim",
                   ledger=a, prices_root=str(tmp_path))
    b = calls.walk(df, pit, "2024-01-01", "2024-12-31", mode="historical_sim",
                   ledger=None, prices_root=str(tmp_path))
    assert sorted(a["call_id"]) == sorted(b["call_id"])
