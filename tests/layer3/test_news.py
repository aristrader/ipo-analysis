"""News-feed (D1/D4): local category taxonomy + look-ahead-safe timestamps + idempotent staging.

These are the PURE, no-network units behind the NSE-announcement context feed. Discipline:
category is a display label only (no polarity); `actionable_from` bakes in the 15:30-IST
look-ahead rule; staging dedups on (sm_isin, an_dt, desc-hash) and stores attachment URLs only.
Spec: docs/research/newsfeed_rnd_2026-06-09.md §2.
"""
from datetime import datetime, date

from layer3.news import taxonomy, staging


# ---------- taxonomy.categorize ----------

def test_categorize_earnings():
    cats = taxonomy.categorize("Financial Results for Q2", "Audited results filing")
    assert "earnings" in cats


def test_categorize_multi_label():
    # a single filing can legitimately carry two coarse categories
    cats = taxonomy.categorize("Bonus issue and dividend declaration", "")
    assert "corp-action" in cats


def test_categorize_default_other():
    assert taxonomy.categorize("Trading window closure intimation", "") == ["other"]


def test_categorize_does_not_misfire_order_win_on_regulatory_order():
    # "Adjudication Order" / "settlement order" must NOT be tagged order-win (precision > recall)
    cats = taxonomy.categorize("Adjudication Order and penalty by SEBI", "")
    assert "sebi-regulatory" in cats
    assert "order-win" not in cats


def test_categorize_is_case_insensitive():
    assert "ratings" in taxonomy.categorize("CRISIL reaffirmed the rating", "")


def test_categorize_word_boundary_no_substring_false_positives():
    # the embeddable-substring class: "rating" inside narrating/operating/generating must NOT fire
    assert taxonomy.categorize("Narrating proceedings of the AGM", "") == ["other"]
    assert taxonomy.categorize("Updates on operating performance", "") == ["other"]
    assert taxonomy.categorize("Generating long-term shareholder value", "") == ["other"]
    # "loi" inside "loiter", "sast" inside "sastra" must NOT fire order-win / m&a
    assert "order-win" not in taxonomy.categorize("No loitering on premises", "")


def test_categorize_true_multi_bucket():
    # two DIFFERENT buckets from two different keywords
    cats = taxonomy.categorize("Tender of resignation by the Managing Director", "")
    assert "management" in cats and "order-win" in cats


def test_categorize_plural_via_optional_s():
    assert "management" in taxonomy.categorize("Appointment of additional directors", "")


# ---------- taxonomy timestamps (look-ahead rule) ----------

def test_parse_an_dt_nse_format():
    assert taxonomy.parse_an_dt("29-May-2026 15:54:27") == datetime(2026, 5, 29, 15, 54, 27)


def test_parse_an_dt_iso_fallback():
    assert taxonomy.parse_an_dt("2026-05-29 15:54:27") == datetime(2026, 5, 29, 15, 54, 27)


def test_actionable_from_after_close_rolls_to_next_session():
    # 29-May-2026 is a Friday; 15:54 is after the 15:30 close -> next session = Mon 1-Jun
    dt = datetime(2026, 5, 29, 15, 54, 27)
    assert taxonomy.actionable_from(dt) == date(2026, 6, 1)


def test_actionable_from_intraday_weekday_is_same_day():
    # 27-May-2026 is a Wednesday; 11:00 is before close -> actionable same session
    dt = datetime(2026, 5, 27, 11, 0, 0)
    assert taxonomy.actionable_from(dt) == date(2026, 5, 27)


def test_actionable_from_intraday_friday_at_exactly_close_rolls_forward():
    # exactly 15:30 counts as at/after close -> next session
    dt = datetime(2026, 5, 29, 15, 30, 0)
    assert taxonomy.actionable_from(dt) == date(2026, 6, 1)


def test_actionable_from_boundary_one_second_before_close_is_same_day():
    # 15:29:59 is still intraday (before close) -> same session
    assert taxonomy.actionable_from(datetime(2026, 5, 27, 15, 29, 59)) == date(2026, 5, 27)


def test_actionable_from_saturday_filing_rolls_to_monday():
    # a filing made on a Saturday (30-May-2026) is actionable the next session = Mon 1-Jun
    assert taxonomy.actionable_from(datetime(2026, 5, 30, 10, 0, 0)) == date(2026, 6, 1)


def test_parse_an_dt_date_only_is_treated_as_after_close():
    # unknown time (date-only) -> stamped at 15:30 close (conservative/look-ahead-safe)
    dt = taxonomy.parse_an_dt("29-May-2026")
    assert (dt.hour, dt.minute) == (15, 30)
    assert taxonomy.actionable_from(dt) == date(2026, 6, 1)  # Fri close -> Mon


# ---------- staging.normalize ----------

RAW = {
    "an_dt": "29-May-2026 15:54:27",
    "sort_date": "2026-05-29 15:54:27",
    "attchmntFile": "https://nsearchives.nseindia.com/corporate/GSP123_x.pdf",
    "attchmntText": "GSP Crop Science Limited has informed the Exchange about financial results",
    "desc": "Financial Results for Q2",
    "sm_isin": "INE713R01022",
    "sm_name": "GSP Crop Science Limited",
    "smIndustry": None,
    "symbol": "GSPCROP",
}


def test_normalize_shapes_a_staging_row():
    row = staging.normalize(RAW)
    assert row["sm_isin"] == "INE713R01022"
    assert row["symbol"] == "GSPCROP"
    assert "earnings" in row["categories"].split(";")
    assert row["actionable_from"] == "2026-06-01"
    # zero-download discipline: the attachment URL is kept, never the file
    assert row["attchmntFile"].startswith("https://")
    assert row["row_hash"]  # a stable dedup id is set


def test_normalize_has_exactly_the_staging_fields():
    row = staging.normalize(RAW)
    assert set(row.keys()) == set(staging.STAGING_FIELDS)


# ---------- staging.upsert (idempotent) ----------

def test_upsert_is_idempotent_on_repull():
    rows = [staging.normalize(RAW)]
    merged = staging.upsert(rows, [staging.normalize(RAW)])
    assert len(merged) == 1  # same announcement re-pulled -> no growth


def test_upsert_appends_genuinely_new_rows():
    rows = [staging.normalize(RAW)]
    other = dict(RAW, an_dt="30-May-2026 09:15:00", desc="Order win: bagged work order")
    merged = staging.upsert(rows, [staging.normalize(other)])
    assert len(merged) == 2
    new = [r for r in merged if r["an_dt"].startswith("30-May")][0]
    assert "order-win" in new["categories"].split(";")


def test_upsert_keeps_distinct_same_minute_filings():
    # same isin/an_dt/desc but DIFFERENT attachment text -> two real filings, must NOT collapse
    a = staging.normalize(dict(RAW, desc="Outcome of Board Meeting",
                               attchmntText="declared Q2 financial results"))
    b = staging.normalize(dict(RAW, desc="Outcome of Board Meeting",
                               attchmntText="approved fund raising via QIP"))
    assert a["row_hash"] != b["row_hash"]
    assert len(staging.upsert([a], [b])) == 2


def test_normalize_garbage_timestamp_degrades_without_crashing():
    row = staging.normalize(dict(RAW, an_dt="not-a-date", sort_date=""))
    assert row["actionable_from"] == ""  # no crash, just empty
