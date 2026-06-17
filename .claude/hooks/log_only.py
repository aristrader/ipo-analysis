#!/usr/bin/env python3
"""LOG-ONLY PreToolUse hook (owner 2026-06-17) — records every action, NEVER blocks.

A passive audit trail for the unattended consolidation run. Unlike the old guard, this
NEVER exits non-zero: it logs and always exits 0, so it can never stop or slow the work.
Fails open on any error.

Appends one line per action to docs/research/foundation_run_log.tsv:
  ISO-timestamp \t tool \t detail(command or file_path, one-lined, truncated)
"""
import sys
import json
import os
import datetime

REPO = "/Users/swapnilagarwal/Visual_Studio_Projects/ipo-analysis"
LOG = os.path.join(REPO, "docs/research", "foundation_run_log.tsv")


def main():
    try:
        d = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    try:
        tool = d.get("tool_name", "?")
        ti = d.get("tool_input") or {}
        detail = ti.get("command") or ti.get("file_path") or ""
        one = " ".join(str(detail).split())
        if len(one) > 1000:
            one = one[:1000] + "...[truncated]"
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        ts = datetime.datetime.now().isoformat(timespec="seconds")
        with open(LOG, "a") as f:
            f.write(f"{ts}\t{tool}\t{one}\n")
    except Exception:
        pass
    sys.exit(0)  # ALWAYS allow — log-only, never blocks


if __name__ == "__main__":
    main()
