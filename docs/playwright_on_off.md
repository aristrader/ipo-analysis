# Playwright (app-testing browser) — ALWAYS ON, localhost-pinned

**Owner rule (2026-06-10, supersedes the 2026-06-08 OFF-by-default rule): Playwright stays ENABLED.**
Deemed safe because `.mcp.json` pins it to **localhost origins ONLY** + `--isolated` (fresh profile, no
access to the real Chrome/Google account) + `--headless` + version-locked, and run_code_unsafe / file_upload /
network_request are DENIED in settings. So there is **no external-network surface** — the only sites it can
reach are the local Streamlit ports.

**ONE-TIME setup to neutralise the residual** (the only concern the localhost pin does NOT cover — a leftover
"Chrome for Testing" process can post macOS notifications): **System Settings → Notifications → "Google Chrome
for Testing" → Allow Notifications OFF.** Do this once and an idle/orphan test browser can never prompt you.
Also: prefer `browser_close` when a walk is done (tidy, not safety-critical now).

## Current state
ENABLED. `.claude/settings.local.json` has `"enabledMcpjsonServers": ["playwright"]`. The MCP server loads each
session; the chromium browser launches lazily on first navigate (localhost-pinned). The TURN-OFF steps below are
kept only for the rare case you want it off (e.g. debugging a stray process).

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
