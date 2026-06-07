# Playwright (app-testing browser) — ON only for testing, OFF otherwise

**Owner rule (2026-06-08): Playwright stays DISABLED by default. Turn it ON only for an app
test/verify session, then turn it OFF again when done.** Company laptop — no idle test browser
should ever be running or able to notify.

## Current state
DISABLED. `.claude/settings.local.json` has `"disabledMcpjsonServers": ["playwright"]`.
The server does not start, so no "Google Chrome for Testing" process launches.

## TURN ON (only when about to test/verify the Streamlit app)
1. Edit `.claude/settings.local.json`: change `"disabledMcpjsonServers"` → `"enabledMcpjsonServers"`
   (the `["playwright"]` value stays the same; the key name is the switch).
2. Restart the Claude session (or run `/mcp` → reconnect) so the server starts.
3. It launches localhost-pinned, isolated, headless chromium (see `.mcp.json`). Safe to walk
   `http://localhost:8597`.

## TURN OFF (the moment app testing is done — DO NOT leave it on)
1. Close the browser (`browser_close`) if a tool session is open.
2. Kill any leftover processes:
   `ps aux | grep -iE "playwright|chrome for testing" | grep -v grep` → `kill <pids>`
   (orphan test browsers are what trigger the macOS notifications).
3. Edit `.claude/settings.local.json`: `"enabledMcpjsonServers"` → `"disabledMcpjsonServers"`.
4. Confirm clean: `ps aux | grep -iE "playwright|chrome for testing" | grep -v grep | wc -l` → 0.

## Belt-and-braces (one-time, optional)
System Settings → Notifications → "Google Chrome for Testing" → Allow Notifications OFF.
Then even an accidental launch can never prompt you.

## Notes
- `.mcp.json` keeps the pinned/secure config (version 0.0.75, --isolated --headless,
  --allowed-origins localhost only) so re-enabling is always safe — the switch is purely on/off.
- The deny rules (run_code_unsafe / file_upload / network_request) stay in settings regardless.
