"""Telegram notifier for new actionable calls (task: scheduled fetch + notify).

Setup (one-time, ~5 min, owner):
  1. In Telegram, talk to @BotFather -> /newbot -> copy the TOKEN.
  2. Message your new bot once (any text), then visit
     https://api.telegram.org/bot<TOKEN>/getUpdates  -> copy "chat":{"id": ...}
  3. Create tools/notify/telegram.json:  {"token": "...", "chat_id": 123456789}
  4. Install the schedule:  cp tools/notify/com.ipo.calls.plist ~/Library/LaunchAgents/
                            launchctl load ~/Library/LaunchAgents/com.ipo.calls.plist

Each run: fetch live board -> gap-fill the calls ledger -> send ONE telegram message listing
calls not yet notified (state in tools/notify/.notified). --dry-run prints instead of sending.
Actionable = APPLY/AVOID on issues still open, EXIT_REVIEW, TAKE_PROFITS."""
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CFG = os.path.join(ROOT, "tools/notify/telegram.json")
STATE = os.path.join(ROOT, "tools/notify/.notified")
BOARD = os.path.join(ROOT, "data/live/board.json")
LEDGER = os.path.join(ROOT, "data/master/calls_ledger.csv")
HEALTH_STATE = os.path.join(ROOT, "tools/notify/.health_state")  # "healthy" / "failed"
LAST_RUN = os.path.join(ROOT, "tools/notify/.last_run")          # ISO ts of last good run
PY = os.path.join(ROOT, ".venv/bin/python")

# J1/J2 thresholds (kept here so tests can reference the intent; callers may override).
BOARD_MAX_AGE_HOURS = 24.0   # board older than this == stale == unusable
RUN_GAP_HOURS = 18.0         # gap since last good run beyond this == a missed scheduled slot


@dataclass
class StepResult:
    """Outcome of one pipeline step (subprocess). Pure data — no I/O."""
    name: str
    returncode: int = 0
    error: str = None
    timed_out: bool = False

    @property
    def errored(self):
        return self.timed_out or self.returncode != 0 or self.error is not None


# --------------------------------------------------------------------------- J1: detection
def board_usable(exists, empty, age_hours, max_age_hours=BOARD_MAX_AGE_HOURS):
    """True iff board.json exists, is non-empty, and is fresh enough to trust."""
    if not exists or empty:
        return False
    if age_hours is None:
        return False
    return age_hours <= max_age_hours


def detect_failure(steps, board_ok, ledger_ok):
    """Return the first StepResult representing a REAL failure, else None.

    A real failure = at least one step errored (raised / timed-out / returncode!=0)
    AND the run left no usable result behind (board unusable OR ledger unwritable).
    A step that errored but whose output is fine (transient that recovered) -> None.
    """
    if board_ok and ledger_ok:
        return None  # whatever happened mid-flight, the outcome is usable -> stay silent
    for s in steps:
        if s.errored:
            return s
    # outputs are bad but no step reported an error (e.g. silent stale board):
    # surface a synthetic failure so we never pass silently on stale data.
    if not board_ok:
        return StepResult(name="live_board", error="board.json missing/empty/stale")
    return StepResult(name="run_calls", error="calls ledger unwritable")


# --------------------------------------------------------------------------- J1: throttle
def health_transition(prev_state, failure):
    """Return (should_send, kind, new_state) for the healthy<->failed state machine.

    healthy -> failed   : send 'alert'    (transition into failure)
    failed  -> failed    : silent         (don't re-panic every cycle)
    failed  -> recovered : send 'recovery'
    healthy -> healthy   : silent
    prev_state None is treated as 'healthy' (first run).
    """
    prev = prev_state or "healthy"
    if failure is not None:
        if prev == "failed":
            return (False, "alert", "failed")
        return (True, "alert", "failed")
    # no failure now
    if prev == "failed":
        return (True, "recovery", "healthy")
    return (False, "recovery", "healthy")


# --------------------------------------------------------------------------- J2: heartbeat
def heartbeat_note(last_run_iso, now=None, gap_threshold_hours=RUN_GAP_HOURS):
    """Return a one-line gap note if the gap since the last good run is too long, else None.

    No prior run, a fresh-enough run, or an unparseable stamp -> None (stay quiet / never crash).
    """
    if not last_run_iso:
        return None
    now = now or datetime.now()
    try:
        last = datetime.fromisoformat(last_run_iso.strip())
    except (ValueError, AttributeError):
        return None
    gap_h = (now - last).total_seconds() / 3600.0
    if gap_h > gap_threshold_hours:
        return f"⚠️ RUN: first run in {gap_h:.0f}h (last good run {last.isoformat(timespec='minutes')})"
    return None


# --------------------------------------------------------------------------- pipeline runner
def _run_step(name, args, timeout):
    env = {**os.environ, "PYTHONPATH": ROOT}
    try:
        cp = subprocess.run([PY, *args], cwd=ROOT, env=env, timeout=timeout)
        err = None if cp.returncode == 0 else f"exit {cp.returncode}"
        return StepResult(name=name, returncode=cp.returncode, error=err)
    except subprocess.TimeoutExpired:
        return StepResult(name=name, returncode=-1, timed_out=True,
                          error=f"timeout after {timeout}s")
    except Exception as e:  # never let a step crash the whole notifier
        return StepResult(name=name, returncode=-1, error=f"{type(e).__name__}: {e}")


def run_pipeline():
    """Run the 3 steps, capturing each outcome. Returns list[StepResult]."""
    return [
        _run_step("live_board", ["scrapers/live_board.py"], 900),
        _run_step("run_calls", ["run_calls.py"], 3600),            # gap-fill+grade
        _run_step("run_calls --live", ["run_calls.py", "--live"], 1800),  # open issues
    ]


# --------------------------------------------------------------------------- I/O for state
def _board_state():
    """Inspect board.json on disk -> (exists, empty, age_hours)."""
    if not os.path.exists(BOARD):
        return (False, True, None)
    try:
        b = json.load(open(BOARD))
    except Exception:
        return (True, True, None)
    empty = not (b.get("open") or b.get("upcoming"))
    age_h = None
    ts = b.get("fetched_at")
    if ts:
        try:
            age_h = (datetime.now() - datetime.fromisoformat(ts)).total_seconds() / 3600.0
        except (ValueError, TypeError):
            age_h = None
    return (True, empty, age_h)


def _ledger_writable():
    """True iff the calls ledger exists and is non-empty (the run could write it)."""
    return os.path.exists(LEDGER) and os.path.getsize(LEDGER) > 0


def _read_state(path):
    if os.path.exists(path):
        return open(path).read().strip() or None
    return None


def _write_state(path, value):
    with open(path, "w") as f:
        f.write(value)


def _maybe_send(cfg, dry, text):
    """Best-effort tagged send (J1/J2) — never raises (different host than the scraper)."""
    if dry:
        print(text)
        return
    try:
        send(cfg["token"], cfg["chat_id"], text)
        print(f"sent ops msg: {text.splitlines()[0]}")
    except Exception as e:
        print(f"ops send failed (best-effort, ignored): {type(e).__name__}: {e}")


def actionable_calls():
    import csv
    from datetime import date, timedelta
    path = os.path.join(ROOT, "data/master/calls_ledger.csv")
    if not os.path.exists(path):
        return []
    recent = (date.today() - timedelta(days=14)).isoformat()
    out = []
    with open(path) as f:
        for r in csv.DictReader(f):
            if r["call_date"] >= recent and r["call_type"] in (
                    "APPLY", "AVOID", "EXIT_REVIEW", "TAKE_PROFITS",
                    "EARLY_APPLY", "EARLY_AVOID"):
                out.append(r)
    return out


def fmt(r):
    icon = {"APPLY": "🟢", "EARLY_APPLY": "🟢", "AVOID": "🔴", "EARLY_AVOID": "🔴",
            "EXIT_REVIEW": "🚨", "TAKE_PROFITS": "💰"}.get(r["call_type"], "•")
    return (f"{icon} {r['call_type']}: {r['name']} ({r['type']}) — {r['call_date']}\n"
            f"   why: {r['rules_fired']}")


def send(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=20)


def main():
    dry = "--dry-run" in sys.argv
    cfg = json.load(open(CFG)) if os.path.exists(CFG) else None

    if "--no-fetch" not in sys.argv:
        steps = run_pipeline()
        # ----- J1: fail-loud health alerts (best-effort, throttled) -----
        exists, empty, age_h = _board_state()
        board_ok = board_usable(exists, empty, age_h)
        ledger_ok = _ledger_writable()
        failure = detect_failure(steps, board_ok, ledger_ok)
        prev = _read_state(HEALTH_STATE)
        should_send, kind, new_state = health_transition(prev, failure)
        if should_send:
            if kind == "alert":
                msg = (f"🚨 HEALTH: pipeline FAILED at step '{failure.name}'\n"
                       f"   {failure.error or 'no usable result (board/ledger unusable)'}")
            else:
                msg = "✅ HEALTH: pipeline RECOVERED — runs are healthy again"
            if cfg or dry:
                _maybe_send(cfg, dry, msg)
        if not dry:
            _write_state(HEALTH_STATE, new_state)

        # ----- J2: heartbeat / last-run stamp -----
        if failure is None:
            note = heartbeat_note(_read_state(LAST_RUN))
            if note and (cfg or dry):
                _maybe_send(cfg, dry, note)
            if not dry:
                _write_state(LAST_RUN, datetime.now().isoformat(timespec="seconds"))

    seen = set()
    if os.path.exists(STATE):
        seen = set(open(STATE).read().split())
    new = [r for r in actionable_calls() if r["call_id"] not in seen]
    if not new:
        print("no new actionable calls")
        return
    text = "IPO calls update:\n\n" + "\n\n".join(fmt(r) for r in new[:20])
    if dry:
        print(text)
    else:
        if not os.path.exists(CFG):
            sys.exit("tools/notify/telegram.json missing — see this file's docstring for setup")
        cfg = json.load(open(CFG))
        send(cfg["token"], cfg["chat_id"], text)
        print(f"sent {len(new)} calls to telegram")
    with open(STATE, "a") as f:
        f.write("\n".join(r["call_id"] for r in new) + "\n")


if __name__ == "__main__":
    main()
