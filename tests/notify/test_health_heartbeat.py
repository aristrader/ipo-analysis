"""J1 (fail-loud health alerts) + J2 (heartbeat) pure-logic tests.

These exercise notify_calls.py's NEW decision logic ONLY — no network, no subprocess.
State + step results are injected; nothing here sends a Telegram message.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools", "notify"))
import notify_calls as nc  # noqa: E402


# ---------------------------------------------------------------------------
# J1 — failure-detection predicate: detect_failure(steps, board_ok, ledger_ok)
# A REAL failure = a step errored AND no usable result was left behind.
# ---------------------------------------------------------------------------

def _step(name, returncode=0, error=None, timed_out=False):
    return nc.StepResult(name=name, returncode=returncode, error=error, timed_out=timed_out)


def test_clean_run_is_healthy():
    steps = [_step("live_board"), _step("run_calls"), _step("run_calls --live")]
    failed = nc.detect_failure(steps, board_ok=True, ledger_ok=True)
    assert failed is None  # no failure


def test_step_raised_and_board_unusable_is_real_failure():
    steps = [_step("live_board", returncode=1, error="ConnectionError"),
             _step("run_calls"), _step("run_calls --live")]
    failed = nc.detect_failure(steps, board_ok=False, ledger_ok=True)
    assert failed is not None
    assert failed.name == "live_board"
    assert "ConnectionError" in (failed.error or "")


def test_transient_recovered_stays_silent():
    # step returned nonzero (a DNS blip) BUT board.json is fresh + non-empty -> recovered.
    steps = [_step("live_board", returncode=1, error="transient DNS"),
             _step("run_calls"), _step("run_calls --live")]
    failed = nc.detect_failure(steps, board_ok=True, ledger_ok=True)
    assert failed is None


def test_timeout_with_unusable_board_is_real_failure():
    steps = [_step("live_board", timed_out=True, error="timeout after 900s"),
             _step("run_calls"), _step("run_calls --live")]
    failed = nc.detect_failure(steps, board_ok=False, ledger_ok=True)
    assert failed is not None
    assert failed.name == "live_board"


def test_ledger_unwritable_is_real_failure_even_with_fresh_board():
    steps = [_step("live_board"), _step("run_calls", returncode=2, error="permission denied"),
             _step("run_calls --live")]
    failed = nc.detect_failure(steps, board_ok=True, ledger_ok=False)
    assert failed is not None


def test_first_failed_step_is_reported():
    steps = [_step("live_board", returncode=1, error="boom"),
             _step("run_calls", returncode=1, error="cascade"),
             _step("run_calls --live")]
    failed = nc.detect_failure(steps, board_ok=False, ledger_ok=False)
    assert failed.name == "live_board"  # earliest failing step named


# ---------------------------------------------------------------------------
# board freshness/usability: board_usable(exists, empty, age_hours, max_age_hours)
# ---------------------------------------------------------------------------

def test_board_missing_is_unusable():
    assert nc.board_usable(exists=False, empty=True, age_hours=None) is False


def test_board_empty_is_unusable():
    assert nc.board_usable(exists=True, empty=True, age_hours=0.1) is False


def test_board_stale_is_unusable():
    assert nc.board_usable(exists=True, empty=False, age_hours=30.0, max_age_hours=24.0) is False


def test_board_fresh_nonempty_is_usable():
    assert nc.board_usable(exists=True, empty=False, age_hours=0.5, max_age_hours=24.0) is True


# ---------------------------------------------------------------------------
# J1 throttle/dedupe transitions: health_transition(prev_state, failure)
# returns (should_send, message_kind, new_state)
# ---------------------------------------------------------------------------

def test_healthy_to_failed_sends_alert():
    send, kind, new = nc.health_transition(prev_state="healthy",
                                            failure=_step("live_board", error="x"))
    assert send is True
    assert kind == "alert"
    assert new == "failed"


def test_failed_to_failed_is_silent():
    send, kind, new = nc.health_transition(prev_state="failed",
                                           failure=_step("live_board", error="x"))
    assert send is False
    assert new == "failed"


def test_failed_to_recovered_sends_recovery():
    send, kind, new = nc.health_transition(prev_state="failed", failure=None)
    assert send is True
    assert kind == "recovery"
    assert new == "healthy"


def test_healthy_to_healthy_is_silent():
    send, kind, new = nc.health_transition(prev_state="healthy", failure=None)
    assert send is False
    assert new == "healthy"


def test_missing_prev_state_treated_as_healthy():
    # first ever run, no state file -> prev None behaves like healthy
    send, kind, new = nc.health_transition(prev_state=None, failure=None)
    assert send is False
    assert new == "healthy"
    send2, kind2, new2 = nc.health_transition(prev_state=None,
                                              failure=_step("live_board", error="x"))
    assert send2 is True and new2 == "failed"


# ---------------------------------------------------------------------------
# J2 — heartbeat gap calc: heartbeat_note(last_run_iso, now, gap_threshold_hours)
# returns None (no note), or a string note (gap exceeded).
# ---------------------------------------------------------------------------
from datetime import datetime, timedelta  # noqa: E402


def test_no_prior_run_no_note():
    assert nc.heartbeat_note(None, now=datetime(2026, 6, 10, 8, 0)) is None


def test_recent_run_no_note():
    last = (datetime(2026, 6, 10, 8, 0) - timedelta(hours=6)).isoformat()
    assert nc.heartbeat_note(last, now=datetime(2026, 6, 10, 8, 0),
                             gap_threshold_hours=18.0) is None


def test_long_gap_produces_note():
    last = (datetime(2026, 6, 10, 8, 0) - timedelta(hours=30)).isoformat()
    note = nc.heartbeat_note(last, now=datetime(2026, 6, 10, 8, 0),
                             gap_threshold_hours=18.0)
    assert note is not None
    assert "⚠️" in note or "RUN" in note


def test_gap_boundary_just_under_threshold_silent():
    last = (datetime(2026, 6, 10, 8, 0) - timedelta(hours=17, minutes=59)).isoformat()
    assert nc.heartbeat_note(last, now=datetime(2026, 6, 10, 8, 0),
                             gap_threshold_hours=18.0) is None


def test_garbage_last_run_is_safe():
    # corrupt state file must not crash the run
    assert nc.heartbeat_note("not-a-timestamp", now=datetime(2026, 6, 10, 8, 0)) is None
