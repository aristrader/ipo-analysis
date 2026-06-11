# ENVIRONMENT & CONFIG — recreate the parts that don't travel

A fresh account/clone gets all TRACKED files, but two config layers are gitignored and must be recreated,
plus the regenerable data must be re-pulled. This doc has the exact contents.

## 1. Python environment
- `python -m venv .venv` (the repo expects `.venv/` at the root) → `source .venv/bin/activate`.
- Install: pandas, numpy, curl_cffi, beautifulsoup4, lxml, streamlit, pytest, requests. **NO scipy / NO
  statsmodels** (deliberate — use the pure-Python `srho`/Wilson/bootstrap helpers in `layer3/spine.py`).
- Always run with `PYTHONPATH=.` (e.g. `PYTHONPATH=. python run_all.py`, `PYTHONPATH=. pytest tests -q`).
- Python 3.14 was in use; any 3.11+ should work.

## 2. `.claude/settings.local.json` (GITIGNORED — recreate verbatim)
This holds the **network allowlist** (default-deny: only these domains are fetchable), the **per-turn verify
hook**, enabled plugins, and the Playwright MCP enablement + its denied dangerous tools. Recreate exactly:

```json
{
  "permissions": {
    "allow": [
      "WebFetch(domain:www.screener.in)",
      "WebSearch",
      "WebFetch(domain:portal.tradebrains.in)",
      "WebFetch(domain:www.bseindia.com)",
      "WebFetch(domain:www.nseindia.com)",
      "WebFetch(domain:seylox.github.io)",
      "WebFetch(domain:sebi.gov.in)",
      "WebFetch(domain:www.sebi.gov.in)",
      "WebFetch(domain:moneycontrol.com)",
      "WebFetch(domain:www.moneycontrol.com)",
      "WebFetch(domain:economictimes.indiatimes.com)",
      "WebFetch(domain:livemint.com)",
      "WebFetch(domain:www.livemint.com)",
      "mcp__playwright__browser_navigate",
      "mcp__playwright__browser_snapshot",
      "mcp__playwright__browser_close",
      "mcp__playwright__browser_click",
      "mcp__playwright__browser_type",
      "mcp__playwright__browser_press_key",
      "mcp__playwright__browser_hover",
      "mcp__playwright__browser_select_option",
      "mcp__playwright__browser_fill_form",
      "mcp__playwright__browser_wait_for",
      "mcp__playwright__browser_console_messages",
      "mcp__playwright__browser_take_screenshot",
      "mcp__playwright__browser_navigate_back",
      "mcp__playwright__browser_resize",
      "mcp__playwright__browser_tabs",
      "mcp__playwright__browser_handle_dialog"
    ],
    "deny": [
      "mcp__playwright__browser_run_code_unsafe",
      "mcp__playwright__browser_file_upload",
      "mcp__playwright__browser_network_request"
    ]
  },
  "hooks": {
    "UserPromptSubmit": [
      { "hooks": [ { "type": "command",
        "command": "cd \"$CLAUDE_PROJECT_DIR\" && .venv/bin/python verify.py --quiet",
        "timeout": 30 } ] }
    ]
  },
  "enabledPlugins": {
    "frontend-design@claude-plugins-official": true,
    "skill-creator@claude-plugins-official": true,
    "duckdb-skills@claude-plugins-official": true,
    "pyright-lsp@claude-plugins-official": true
  },
  "enabledMcpjsonServers": [ "playwright" ]
}
```
**Network rule reminder:** this allowlist is the ENFORCEMENT of default-deny. Don't add domains casually —
the expand-only-if-deemed-safe rule + the trusted-source registry live in `docs/research/trusted_sources.md`.
The per-turn `verify.py --quiet` hook is what keeps `MAP.md` regenerated + catches structural/invariant drift.

## 3. `.mcp.json` (TRACKED — already in the repo, here for reference)
Playwright pinned to localhost origins only, isolated + headless + version-locked:
```json
{ "mcpServers": { "playwright": { "command": "npx", "args": [
  "@playwright/mcp@0.0.75", "--browser", "chromium", "--isolated", "--headless",
  "--allowed-origins",
  "http://localhost:8501;http://localhost:8597;http://localhost:8598;http://localhost:8599;http://127.0.0.1:8501;http://127.0.0.1:8597;http://127.0.0.1:8598;http://127.0.0.1:8599"
] } } }
```
One-time OS step (avoids notification spam): System Settings → Notifications → "Google Chrome for Testing" → OFF.

## 4. Gitignored DATA to regenerate (the `.gitignore` lists these)
- `data/raw/`, `data/prices/<isin>.csv`, `data/reference/bhavcopy/` — re-pulled by the scrapers via
  `run_all.py` (resume-safe, rate-limited). Long pulls.
- `data/live/news/` — the NSE announcement staging (~180MB+); re-pull with
  `PYTHONPATH=. python scrapers/announcements.py` (full history comes by default).
- Notifier state files (`tools/notify/.health_state`, `.last_run`, `telegram.json`) — local, recreated on run.
- **The canonical outputs `data/master/*.csv` ARE tracked** — the analysis substrate travels with the repo.

## 5. Optional: Telegram ops notifier
`tools/notify/notify_calls.py` (thrice-daily + login-catch-up) needs `tools/notify/telegram.json`
(bot token + chat id — gitignored, recreate if you want the alerts). The `com.ipo.calls.plist` launchd job
schedules it. Entirely optional; the analysis works without it.
