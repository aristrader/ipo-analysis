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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CFG = os.path.join(ROOT, "tools/notify/telegram.json")
STATE = os.path.join(ROOT, "tools/notify/.notified")
PY = os.path.join(ROOT, ".venv/bin/python")


def run_pipeline():
    subprocess.run([PY, "scrapers/live_board.py"], cwd=ROOT,
                   env={**os.environ, "PYTHONPATH": ROOT}, timeout=900)
    subprocess.run([PY, "run_calls.py"], cwd=ROOT,
                   env={**os.environ, "PYTHONPATH": ROOT}, timeout=3600)


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
    if "--no-fetch" not in sys.argv:
        run_pipeline()
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
