"""Regression tests for the investing.com (smallcap250) parse fix.

The old parser did `dt[:11]` on 'Jun 17, 2026' (12 chars), chopping the year's last digit, so EVERY
2-digit-day row failed and all 1,836 rows were dropped. These lock in the fix.
"""
from scrapers.indices import _parse_investing_rows


def test_iso_timestamp_preferred():
    rows = [{"rowDateTimestamp": "2026-06-17T00:00:00Z", "rowDate": "Jun 17, 2026",
             "last_closeRaw": "17495.75", "last_close": "17,495.75"}]
    out, dropped = _parse_investing_rows(rows)
    assert dropped == 0 and out == [("2026-06-17", 17495.75)]


def test_two_digit_day_display_no_truncation():
    # the exact bug: 'Jun 17, 2026' with no ISO timestamp must still parse (not be truncated/dropped)
    rows = [{"rowDate": "Jun 17, 2026", "last_close": "17,495.75"}]
    out, dropped = _parse_investing_rows(rows)
    assert dropped == 0 and out == [("2026-06-17", 17495.75)]


def test_one_digit_day_display():
    rows = [{"rowDate": "Jun 7, 2026", "last_close": "1,234.5"}]
    out, dropped = _parse_investing_rows(rows)
    assert out == [("2026-06-07", 1234.5)]


def test_malformed_rows_dropped_not_fabricated():
    rows = [{"rowDate": "garbage", "last_close": "x"}, {"rowDate": None, "last_close": None}]
    out, dropped = _parse_investing_rows(rows)
    assert out == [] and dropped == 2
