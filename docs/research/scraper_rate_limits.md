# Scraper rate-limit reference (measured 2026-06-17)

Measured via polite probes (8-request robots.txt bursts + 6-request real-endpoint bursts), owner-authorized
network-on run from the company laptop. Purpose: configure the scraper throttling for the full re-fetch (Phase 0 / T0.1).

| Source | Endpoint tested | Result | Recommended scraper config |
|---|---|---|---|
| **screener.in** | `/company/INFY/` (228 KB real page) | 6 rapid reqs, ~0.07s each, **no throttle** | Historically strict → **owner-set cap: max 2 parallel calls** + ~0.5–1s delay; do NOT exceed 2 concurrent |
| **NSE** | `/api/marketStatus` (session-primed) | No throttle, fast | Prime session (homepage → cookies) then hit API; keep `nse_session.py` priming |
| **BSE** | homepage | No throttle | Modest delay |
| **chittorgarh** | robots.txt | ~0.4s/req, no throttle | Modest delay (~0.5s) |
| **investorgain** | robots.txt | No throttle | Fine |
| **ipowatch** | robots.txt | No throttle | Fine |
| **sharescart** | robots.txt | First req ~2.5s then fast | Fine; allow a generous timeout |
| **Yahoo** (query1/query2) | `/v8/finance/chart` | ✅ **Works when paced**; brief 429 only after a burst | Initial all-429 was a TRANSIENT throttle from ~12 back-to-back probe hits — NOT a hard block. On a paced retry, raw query1/query2 returned 200 and `yfinance` lib (v1.4.1) fetched cleanly. Config: prefer the **yfinance library** for splits/history, pace ~0.5–1s, back off on 429. |

## Notes
- `robots.txt` is a cheap cached file — NOT representative of heavy data pulls. The screener real-page test (above) is the meaningful one for that source.
- The previously-strict screener limiting was **not** observed on a 6-request burst of a real company page. Re-fetch should not take days. Still start conservative (1 worker + delay) and watch for 429s.
- **Yahoo is NOT blocked** (corrected after diagnosis): the initial all-429 was a transient throttle caused by our own back-to-back probe bursts (~12 hits in seconds). On a paced retry, raw query1/query2 returned HTTP 200 and the `yfinance` library (v1.4.1) fetched history cleanly. Yahoo just needs polite pacing + back-off on 429; prefer the yfinance library for splits/history.
- All scrapers will gain `fetch_error` vs `no_data` distinction (the honesty contract), so any throttle/failure during the real run is recorded, never faked.
