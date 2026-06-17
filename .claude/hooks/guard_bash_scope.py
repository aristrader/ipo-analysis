#!/usr/bin/env python3
"""PreToolUse scope-guard for Bash (owner 2026-06-17) + per-action logging.

Layered safety for the unattended design run:
  1. OS SANDBOX is the real isolation. Only `agy` may disable it (network). Any other command that
     tries to disable the sandbox is BLOCKED -> python etc. stay confined by the OS.
  2. This hook is the POLICY layer (the sandbox still allows writes INSIDE the repo, so we must protect
     the repo's own code/data): no writes outside docs/research, no rm/mv/truncate/dd (no deletion),
     no destructive/committing git, no sudo/chmod/chown, no network (agy is the only sanctioned path).
  3. LOG every Bash action (timestamp, allow/block, command) to docs/research/night_run/bash_action_log.tsv.

Heuristic, not a kernel sandbox. Fails OPEN on parse error so it can never brick the session.
agy commands are trusted+logged and skip the content scans (their argument is a quoted prompt, not shell).
"""
import sys, json, re, os, datetime

REPO = "/Users/swapnilagarwal/Visual_Studio_Projects/ipo-analysis"
DOCS = os.path.join(REPO, "docs/research")
LOG = os.path.join(DOCS, "night_run", "bash_action_log.tsv")


def _norm(p):
    p = p.strip().strip("'\"")
    if not p:
        return ""
    p = os.path.expanduser(p)
    if not p.startswith("/"):
        p = os.path.normpath(os.path.join(REPO, p))
    return p


def write_outside_docs(p):
    n = _norm(p)
    if not n.startswith("/"):
        return False
    if n.startswith("/tmp") or n.startswith("/private/var/folders"):
        return False
    if n.startswith("/dev/"):  # /dev/null, /dev/stdout, /dev/stderr — harmless sinks
        return False
    return not (n == DOCS or n.startswith(DOCS + "/"))


def decide(ti):
    cmd = ti.get("command", "") or ""
    low = cmd.lower()
    disable = bool(ti.get("dangerouslyDisableSandbox", False))
    first = (cmd.split() or [""])[0]
    is_agy = os.path.basename(first) == "agy"

    # only agy may disable the OS sandbox; everything else stays confined
    if disable and not is_agy:
        return "only agy may run with the sandbox disabled; python/other must stay sandboxed."

    # agy is trusted + allow-listed; its arg is a quoted prompt (not executed shell) -> skip content scans
    if is_agy:
        return None

    # protect git / main / history
    if re.search(r"\bgit\s+(push|commit|reset|clean|checkout|restore|rebase|merge|stash\s+drop|branch\s+-d)\b", low):
        return "destructive/committing git op not allowed during the design run."

    # no deletion / move (owner: no unnecessary deletion)
    if (re.search(r"\brm\b", low) or re.search(r"\bmv\b", low) or re.search(r"\btruncate\b", low)
            or re.search(r"\bdd\b", low) or re.search(r"-delete\b", low) or re.search(r"-exec\b", low)):
        return "rm/mv/truncate/dd/find-delete/-exec not allowed (no deletions/arbitrary exec)."

    # no escalation / perms
    if re.search(r"\bsudo\b", low) or re.search(r"\bchmod\b", low) or re.search(r"\bchown\b", low):
        return "sudo/chmod/chown not allowed."

    # no network (agy is the only sanctioned path)
    if re.search(r"\b(curl|wget|nc|ssh|scp|rsync|telnet)\b", low):
        return "network command not allowed (use agy for sanctioned reads)."

    # shell redirection writing to a path (only flag real path-looking targets to avoid python '>' comparisons)
    for m in re.findall(r">>?\s*([^\s;|&>]+)", cmd):
        t = m.strip().strip("'\"")
        if (t.startswith("/") or t.startswith("~") or "/" in t) and write_outside_docs(t):
            return f"refusing to write outside docs/research: {t}"

    # python open(...,'w'/'a'/'x') must stay under docs/research (protects repo code/data)
    if "python" in low:
        for path, mode in re.findall(r"open\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([rwaxbt+]+)['\"]", cmd):
            if ("w" in mode or "a" in mode or "x" in mode) and write_outside_docs(path):
                return f"refusing to open-for-write outside docs/research: {path}"

    return None  # allow


def _log(decision, cmd):
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        ts = datetime.datetime.now().isoformat(timespec="seconds")
        one = " ".join(cmd.split())
        if len(one) > 1000:
            one = one[:1000] + "...[truncated]"
        with open(LOG, "a") as f:
            f.write(f"{ts}\t{decision}\t{one}\n")
    except Exception:
        pass


def main():
    try:
        d = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    tool = d.get("tool_name")
    ti = d.get("tool_input") or {}
    # log file modifications (Write/Edit/MultiEdit) for the audit trail — log-only, never block
    if tool in ("Write", "Edit", "MultiEdit"):
        fp = ti.get("file_path", "") or ""
        if write_outside_docs(fp):
            _log("BLOCK", tool + " " + fp)
            print("scope-guard BLOCKED: refusing to " + tool + " outside docs/research: " + fp, file=sys.stderr)
            sys.exit(2)
        _log(tool.lower(), fp)
        sys.exit(0)
    if tool not in (None, "Bash"):
        sys.exit(0)
    cmd = ti.get("command", "") or ""
    reason = decide(ti)
    _log("BLOCK" if reason else "allow", cmd)
    if reason:
        print("scope-guard BLOCKED: " + reason, file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
