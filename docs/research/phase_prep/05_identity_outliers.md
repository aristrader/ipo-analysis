# 05 — Identity & wrong-entity joins (Phase 3)

## 1. Wrong-entity joins — confirmed, but NOT ratio-detectable alone (important method note)
The spec's "Bajaj cap 36× too large — Bajaj isn't the only one" needs a careful detector. Two naive attempts:
- **`market_cap_cr / issue_amount_cr > 50×` → 217 rows.** ❌ Mostly FALSE positives — real winners (Page
  Industries, Info Edge, Persistent, Bajaj-? ) legitimately have current cap ≫ IPO size. Useless as a filter.
- **Share-count-normalized** (`implied_total_shares = mcap/price` vs `fresh_shares = issue_amt/issue_price`,
  flag mult >200× or <0.3×) → **33 rows.** Better, but STILL confounded: bonus/split-heavy names (Fineotex
  +5,700%, IRB after its 1:1 bonus) inflate share count legitimately, and penny stocks blow up the ratio.

**Confirmed genuine wrong-entity join:**
- **Bajaj Corp Ltd — `market_cap_cr = ₹292,355cr` at price ₹552.** Bajaj Corp is a *small FMCG* (Almond Drops
  hair oil), real cap a few-thousand crore. ₹292,355cr is a *large Bajaj-group* entity's value
  (Holdings/Finserv-scale). **The cap was joined from the wrong "Bajaj".** (Tellingly, a web search for "Bajaj
  Corp" itself returned Bajaj Holdings/Finance — the exact name-collision that causes these joins.)

**Method conclusion (for Phase 3):** wrong-entity joins **cannot be found by a single ratio** — winners and
bonus names masquerade as outliers. The reliable path is the spec's design:
1. **ISIN-only auto-joins**; names only FLAG (never merge) — enforce everywhere.
2. **A curated identity-history golden file** (D14-gate) is the real fix — verify the entity behind each
   ambiguous name (the "Bajaj" family, "Birla" family, etc.).
3. As a *triage* list for manual verification, the 33 share-normalized outliers are a good starting worklist;
   each needs a price×shares sanity check against a trusted source (the worst: Bajaj Corp, Atlanta, G G
   Engineering, Salasar). Do NOT auto-correct — flag and verify (the spec's "never guess").
4. The clean structural signal that *did* work: market_cap_cr that is **0/missing while price is live**
   (Bansal Multiflex, Supreme Impex, Pushpanjali) — those are data-quality nulls, not wrong entity.

## 2. Identity-verification columns — coverage census (confirms ID-verify)
- `isin_xchg_check`: 1,303 `match` / 39 `unchecked` / 15 `renamed_confirmed` / **1,027 NULL** (never verified).
- `name_isin_check`: 1,304 `match` / 38 `no_ref` / 15 `renamed_confirmed` / **1,027 NULL**.
- **`ticker_needs_review`: NULL on all 2,384 → DEAD column** (confirms spec; retire or populate in Phase 3).
- The 1,027 never-verified are the longterm (2006–19) cohort — never identity-checked. The 38–39
  `no_ref`/`unchecked` are the disagreement set (spec's "39", now 38–39 — minor drift).
- `rows with NO trading ticker at all` (all of nse_symbol/bse/ticker_ns/ticker_bo null): **0** — so the spec's
  "283 with no usable ticker" refers to a *single* canonical ticker column being blank, not all four. Phase 3
  should define ONE canonical resolved trading symbol with a fallback order across the 4 overlapping columns.

## Action items into Phase 3
1. Build the **identity-history golden file** (the real wrong-entity fix) — start with the 33 outlier worklist
   + the ambiguous name families. Verify-don't-guess.
2. Encode "not-verified" as an explicit present/absent state for the 1,027 longterm rows (not silent trust).
3. Retire or populate the dead `ticker_needs_review`; define a single canonical resolved trading symbol.
4. `market_cap_cr` wrong-entity rows (Bajaj Corp et al.) → overlay correction once verified; until then,
   flag display-side (it never feeds the predictor, so analyses are safe — display is the only exposure).
