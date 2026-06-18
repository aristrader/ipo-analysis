# 10 — Foundation issue tracker (fix one-by-one)

Every actionable issue found in the T1.1 review + the overnight research (docs 01–09), consolidated so we
work through them in order. **Data status: NO re-pull needed** — all fixes are solvable from the saved
`data_build/` raw + the frozen `data/` baseline (verified: the subscription final figures are already in our
saved chittorgarh raw). The only *new* fetch ever needed is the owner-gated worklist (ISS-23).

Status key: ⬜ open · 🔧 in progress · ✅ done · ⏸ deferred (needs owner decision).

## GROUP 1 — Fix what we built in T1.1 (do FIRST, before committing T1.1)
| ID | Issue | Fix | Status |
|----|-------|-----|--------|
| ISS-1 | `subscription_x_valid` uses a board rule ("SME 0 → real") — false; a listed IPO can't be 0-subscribed | Reject `0`/negative → invalid; keep `>0`; no board; no ≥1 floor | ⬜ |
| ISS-2 | `columns.yaml` `sub_total_x` description says "SME 0x can be REAL" | Rewrite description to match ISS-1 | ⬜ |
| ISS-3 | `validate_gmp_nonzero` assumes source `0%` GMP is always a placeholder (a real 0% is plausible) | OWNER DECISION (F3): placeholder-but-flagged vs accept-real-0 | ⏸ |
| ISS-4 | T1.1 tests encode the old wrong rules | Flip SME-0→`Missing_data`; add `=0` impossible + `0<x<1` real-listing cases; drop board | ⬜ |
| ISS-5 | After ISS-1..4: re-run suite + verify, update task-log, then commit corrected T1.1 | — | ⬜ |

## GROUP 2 — Subscription data quality (the early-snapshot bug, A2)
| ID | Issue | Fix | Status |
|----|-------|-----|--------|
| ISS-6 | `nse` subscription = early snapshot, not final (Adani Wilmar 0.26 vs true 17.37; Antony Waste 0.50 vs 9.82; Radiant 0.53 vs 1.10) | Re-parse the day-wise table → take the **final/close-of-bidding row**; data is in saved raw | ⬜ |
| ISS-7 | Cross-source pick chose bad `nse` (0.26) over `chittorgarh` (13.44) silently | The match must **flag >N× disagreement**, not pick by priority alone | ⬜ |
| ISS-8 | Source↔source joins were done by NAME → missed renamed cos (AWL "Adani Wilmar") | **ISIN-only joins** everywhere; re-run the subscription disagreement census by ISIN for the true count | ⬜ |

## GROUP 3 — Phase 1 provenance (recovery + cross-field)
| ID | Issue | Fix | Status |
|----|-------|-----|--------|
| ISS-9 | T1.3 subscription recovery identity only 78% (systematic 0.72× = anchor-basis), concentrated in book-built MB | Recover SME/non-book-built directly; for book-built MB recover against net-offer base (issue_size − anchor) | ⬜ |
| ISS-10 | T1.2 tranche check as equality flags 401 legit rows | **DECIDED: DOWNGRADE to optional low-priority sanity flag.** We have the total directly (`sub_total_x`) + 0 rows need total-reconstruction + the real check is the cross-source match (ISS-6/7/8). Keep at most a cheap `Σparts ≤ total` flag. | ⏬ low |
| (min-investment recovery is CLEAN — no issue) | | | ✅ |

## GROUP 4 — Corp-actions (Phase 5) — the D-1 over-count AND the new under-coverage
| ID | Issue | Fix | Status |
|----|-------|-----|--------|
| ISS-11 | Fresh NSE fetch (rolling window) DROPPED 25 real recent corp-actions (MCX, LICI, IRB…) | **Union-merge corp-actions across fetches (append-only); never replace** | ⬜ |
| ISS-12 | Same-event double-count → fake multibaggers (Rolex 152×, NPST 161×, Cantabil) | Collapse key `(symbol, round-ratio, ≥2 sources, ≤45d)` → one event (45d, not 30d) | ⬜ |
| ISS-13 | 5 `verification_2026-05-31` golden rows dropped by fresh scrape | Re-inject via the overlay (append-only golden) | ⬜ |
| ISS-14 | 09 cross-source listing-price tripwire disabled for ALL corp-action stocks (423 rows / 18%) | Re-enable it for corp-action stocks (09:88-89) | ⬜ |
| ISS-15 | 03l hardcodes `action_type='split'` for all 354 yfinance rows | Preserve/derive the real yfinance action_type | ⬜ |
| ISS-16 | Golden corp-action catalog needs verified ratios | Seed: ROLEXRINGS 10× (one split, no 2nd factor), MCX 5× (new ISIN), LICI 2× bonus; verify NPST/CANTABIL dates | ⬜ |

## GROUP 5 — Reconciliation / data-copy-merge (the swap)
| ID | Issue | Fix | Status |
|----|-------|-----|--------|
| ISS-17 | Wholesale replace would lose 12 delisted price histories the re-fetch can't regenerate | Swap = **union/preserve** for prices (keep frozen file where re-fetch has none) | ⬜ |
| ISS-18 | `delisting.csv` is now a full status table (2384: active 2100/delisted 139/…), not delisted-only | Consumers (07, Phase-5) must **filter on `status`** | ⬜ |

## GROUP 6 — Structural (Phase 2) & Identity (Phase 3)
| ID | Issue | Fix | Status |
|----|-------|-----|--------|
| ISS-19 | Standard Chartered IDRS mislabeled `instrument_type='equity'` (no `idr` rows exist) | Relabel to `idr` (1 row) | ⬜ |
| ISS-20 | Date-ordering: 3 close>listing + 14 null listing + 15 long close→listing gaps | CR-date whole-chain validity (open ≤ close ≤ listing), resolve corrupt field from prices | ⬜ |
| ISS-21 | Wrong-entity joins (Bajaj Corp ₹292,355cr = a different Bajaj; +33-row worklist) — not ratio-detectable | ISIN-only joins + `_src_entity` stamping + identity-history golden file; manual-verify the 33 | ⬜ |
| ISS-22 | Identity coverage: 1027 longterm never-verified; `ticker_needs_review` dead; 4 overlapping ticker cols | Encode not-verified explicitly; retire/populate dead col; one canonical resolved ticker | ⬜ |

## GROUP 7 — Overlay / golden / deferred
| ID | Issue | Fix | Status |
|----|-------|-----|--------|
| ISS-23 | Refetch worklist (18 MB-sub + 10 GMP, no source has them) | Owner-gated targeted fetch (T1.4) — the ONLY new-fetch need | ⏸ |
| ISS-24 | Indiabulls Power "bonus" fix is likely phantom (= RattanIndia Power, has NO bonus/split ever) | Verify vs exchange; likely DELETE-EVENT or reclassify as rights issue; add identity-golden name-change entry | ⬜ |
| ISS-25 | Scattered hand-fixes (manual_overrides 3 + corp 39 + drhp 16) must consolidate into one overlay | Migrate to append-only overlay ledger; reconstruct `old_value` from frozen baseline | ⬜ |
| ISS-26 | `kpi_market_cap_post_ipo` gross parse errors (HDFC AMC ₹7.8cr vs ₹2800cr) | Parse-quality pass before any use; stays display-only / blocked on BL-1 | ⬜ |

## GROUP 8 — Found in the 2-agent review (2026-06-18) — NEW, not in the original 26
| ID | Issue | Fix | Sev | Status |
|----|-------|-----|-----|--------|
| ISS-27 | **MFE/MAE use RAW `issue_price` while `return_from_issue` uses ADJUSTED `issue_price_adj`** → 41 impossible values (mfe<endpoint) across 30 corp-action stocks; ~489 adjusted rows silently mis-based. The whole issue-anchored movement lens (reach_curve, exit ladder, P(EVER 2x), tradeable_upside) is biased. `mfe_lst_*` are correct (0 violations). | Recompute `mfe_*`/`mae_*` against `issue_price_adj`. **DECIDED: SEQUENCE AFTER the corp-action fixes (ISS-11/12/16)** — `issue_price_adj` is only correct once split factors are fixed; do it in the same step-07 recompute. | **CRIT** | ⬜ (after Ph5) |
| ISS-28 | **`market_cap_cr` / `market_cap_class` are CURRENT (as-of) → look-ahead leak** if used at-IPO (76 multibaggers now class `large`, 119 `mid` — they grew INTO size via returns). Distinct from ISS-26 (that's a parse bug; this is temporal leakage on a cleanly-parsed col). | **DECIDED: mark `current`/display-only + EXPLICITLY state it's excluded/not-used (loud). Building an at-IPO cap = deferred Bucket-B decision (BL-1).** | **CRIT** | ⬜ |
| ISS-29 | **38 FPO rows carry fake listing-day metrics** (FPOs are already-listed; "listing pop" is meaningless) — 28 have `adj_listing_gain_open`, some extreme (Tantia FPO +260%). Pollutes listing-pop analysis (CLAUDE.md only excludes `unreliable_coverage`). Same class as IDR (ISS-19) but FPO not covered. | Exclude `instrument_type in (fpo,reit,invit)` from listing-pop/gain analyses (or null their listing metrics) | HIGH | ⬜ |
| ISS-30 | **Insolation Energy (INE0LGX01024) band/lot/min cross-contaminated** (web-confirmed): `price_band_low=131 > issue_price=38` (impossible), lot/min wrong (real lot 3000, min ₹114k). | Repair from source; add invariants `price_band_low ≤ issue_price` and `min_inv ≈ lot×band` as tripwires | HIGH | ⬜ |
| ISS-31 | **Raw `listing_open=0`** on Udayshivakumar (INE0N0Y01013). **VERIFIED root cause = SOURCE** (chittorgarh's own `details.csv` has 0; not our parse). Deeper: the row is stamped `status='ok'` but its price file starts 2024-12-20 vs listing 2023-04-03 (**~20-mo coverage gap**) + the anchor open is 0 → it SHOULD be `unreliable_coverage`. The `listing_remediation.py` 0-anchor/coverage-gap check has a HOLE. `adj_listing_open=30` is of murky origin. | (a) treat raw `0` as missing; (b) tighten remediation so 0-anchor/coverage-gap → `unreliable_coverage` not `ok`; (c) **AUDIT how many other rows are mislabeled `ok` the same way** (ties to ISS-37). | MED→HIGH | ⬜ |
| ISS-32 | **7 active companies have `market_cap_cr=0` with real current prices** (Bansal Multiflex cp=19500, Supreme Impex, Pushpanjali…) — computation failure (missing share count), forces them to `micro`. Distinct from ISS-26. | Recompute share count or null+flag | MED | ⬜ |
| ISS-33 | **`eps_ttm` vs `pat_ttm_cr` opposite signs** — Sahasra (INE0RBQ01018): eps +1.3 but PAT −2.0 (1 row). | Reconcile against source financials | LOW | ⬜ |
| ISS-34 | **4 rows `min_investment_rs` disagrees with `lot×price` by >15%** (Anand Rathi Wealth, Vikran, Rulka, NSB BPO) — possible HNI/band-base mixups. | Parse-quality pass (NEW-4 proves the detector finds real corruption) | LOW | ⬜ |
| ISS-35 | **`issue_expenses_cr` = 100% empty dead column** (0/2384). | Source from chittorgarh RHP, or retire like `ticker_needs_review` | LOW | ⬜ |
| ISS-36 | **`kpi_roce_pre_ipo` 100% empty, `kpi_roe_pre_ipo` ~0% (2 rows)** — the longterm KPI fetch (03g) failed for ROE/ROCE. | Decide: re-source or retire | LOW | ⬜ |
| ISS-37 | **`listing_metrics_status` counts drifted; CLAUDE.md is STALE** — live: ok 1935 / unreliable_coverage 223 / recovered 153 / inferred_split 57 / null 16 (vs documented 2048/80/153/1/14). The "exclude unreliable_coverage from pop analysis" rule now drops **223 rows, not 1**. | **DECIDED: CENTRALISE — add `listing_metrics_status` breakdown to the canonical-facts block (project_map.py → verify.py → MAP.md, computed from the substrate); REMOVE the hardcoded counts from CLAUDE.md/BUILD_SPEC, replace with a pointer. Self-updates, can't drift.** Still confirm the 222 reclassified rows are genuinely unreliable. | MED | ⬜ |
| ISS-38 | **`delist_reason` present only for 40 MB delistings, ZERO for SME** (214 delisted total). The compulsory/liquidation→−100% rule (decision A1) has no reason text for SME. | Source SME delisting reasons; gate the −100% rule on reason presence | MED | ⬜ |
| ISS-39 | **Most fields are SINGLE-SOURCE** (only 3 of 15 `_src` are multi-source) → the cross-source match (ISS-7/8) can't corroborate chittorgarh-only fields without re-parsing raw or adding a source. | Decide per-field corroboration strategy (re-parse raw vs accept-authoritative-single-source) | MED | ⬜ |
| ISS-40 | **`listing_remediation.py` ("FIX 2") is a SECOND, heuristic split system parallel to corp_actions** (never reviewed in this rebuild). (a) **0-anchor hole:** checks `chittor_open is None` but not `≤0`, so a `0`/negative chittorgarh anchor evades both branches → wrongly stamped `ok` (the ISS-31 mechanism). (b) **`inferred_split` false-positive:** guesses a split from `chittor_open/computed_open ∈ [1.5,12]` when no corp-action → a REAL ~80-90% listing crash with no recorded action gets "re-anchored" as a fake split, **erasing the real crash**. (c) **Double-handling:** splits must be resolved ONCE in the corp-action golden + price-gap arbiter, not guessed here in parallel. | (1) treat `chittor_open ≤ 0` as missing-anchor; (2) once corp_actions is fixed (union-merge + golden + arbiter), **RETIRE the ad-hoc inferred_split** — fold it into the price-gap arbiter (single split authority); (3) AUDIT the 57 `inferred_split` rows against corrected corp_actions for erased-crash false-positives | HIGH | ⬜ |
| — | **Test-case exhibit (not a new issue):** Honasa `sub_total_x=0.0` carries `_src='sharescart'` (real ~7.6x) — a concrete I1-stamp laundering row; use as a golden regression test for ISS-1/the gate. | — | — | note |

**Clean negatives (verified, no issue):** 0 duplicate/malformed ISINs; 0 company_name across multiple ISINs; cross-field sums (ofs+fresh vs size, amount vs size, ofs_pct) clean; promoter %/ofs_pct in range; dates all 2006–2026, none future; returns respect the −100% floor (the 34 exact −1 = delisting convention); `mfe ≥ mae` holds; `all_time_high ≥ all_time_low` always.

## Working order (proposed)
Group 1 (commit corrected T1.1) → Group 2 & 3 (Phase-1 data quality) → then per the phase plan: Group 6
(Ph2/3) → Group 4 (Ph5 corp-actions) → Group 5 (reconciliation/swap) → Group 7 (overlay). Owner decides
ISS-3 (GMP) and ISS-23 (refetch) when we reach them. Update status here as each is fixed.
