# Trusted sources & network policy — HARD allowlist (owner mandate 2026-06-08)

Company laptop. **Default-deny for the open web.** Only the sources below may be accessed, only
read-only, and NOTHING is ever downloaded/saved from an external site. Expand this list ONLY when
the owner explicitly deems a new source safe — never silently.

## How it's ENFORCED (not just written)
- **WebFetch is domain-allowlisted** in `.claude/settings.local.json` → `permissions.allow`. Any
  domain NOT listed there triggers a permission prompt = BLOCKED in autonomous/agent runs (proven:
  research agents got "WebFetch permission-denied" on off-list domains and fell back to search).
  There is deliberately **NO blanket `WebFetch`** allow.
- **WebSearch** is allowed (returns search snippets only; it does not fetch arbitrary sites with our
  identity, and downloads nothing) — low risk, and needed for research.
- **Playwright** is OFF by default + localhost-origin-pinned + run_code_unsafe/file_upload/
  network_request DENIED (`docs/playwright_on_off.md`).
- **No downloads:** web tools READ + parse to text only. Scrapers write ONLY parsed data into
  `data/`. Do not curl/wget files from external sites.

## WebFetch allowlist (the ONLY domains fetchable without a prompt — keep narrow)
- `www.nseindia.com` — official exchange (announcements, subscription, indices)
- `www.bseindia.com` — official exchange
- `www.screener.in` — financials/announcements (we already ingest)
- `portal.tradebrains.in` — (legacy, price cross-check)
- `seylox.github.io` — (one-off reference)
To add one: append `"WebFetch(domain:<host>)"` to `permissions.allow` in settings.local.json —
ONLY after the owner deems it safe. Candidates surfaced by research but NOT yet enabled (kept off
until approved): sebi.gov.in, moneycontrol.com, economictimes.indiatimes.com, livemint.com,
news.google.com (RSS), chittorgarh.com, webnodejs.chittorgarh.com, investorgain/ipowatch hosts.

## Scraper endpoints (hit by python via Bash, not WebFetch — bounded by HARDCODED URLs in scrapers/)
chittorgarh (webnodejs.chittorgarh.com, www.chittorgarh.com) · NSE (nseindia.com APIs via
nse_session.py) · BSE · screener.in · ipowatch (REST) · investorgain (webnodejs). These are fixed
URLs in `scrapers/*.py` — auditable there; they only fetch, and write parsed data to `data/`.
HONEST LIMITATION: this is bounded by the hardcoded URLs + code review, NOT a network firewall on
Bash. Adding OS-level network sandboxing was deemed too breakage-prone for now (owner can revisit).

## The rule (one line)
Trusted-only, read-only, zero downloads; off-list = stop and ask; expand only on explicit owner OK.
