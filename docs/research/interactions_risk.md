# Feature-combination (interaction) patterns for IPO FAILURE

**Question:** do *combinations* of pre-listing features reveal IPO failure that single features miss?
**Discipline (held hard):** theory-driven pairs only; min-N **≥20 on the BOTH (1,1) cell** (not the margin);
**cross-regime mandatory** (must hold in boom AND longterm); the pair must **BEAT the additive expectation**
(super-additive = real interaction; merely-additive = just two flags stacked). Higher skepticism than single-feature work.

Date: 2026-06-01. Scratch script: `/tmp/interactions.py` (+ `/tmp/scrutiny.py`, `/tmp/extra.py`). No repo code changed.

## Method

- **Substrate:** `spine.load_substrate()` → 2,245 equity rows; boom n=1,254, longterm n=991.
- **Failure outcome (era-appropriate, per brief):**
  - longterm → `outcome_class=='wipeout'` (mature; ~-100%/compulsory delist).
  - boom → DEAD MONEY: alive & `current_return_from_issue < -0.5` & `liquidity_flag=='low'` (or wipeout).
  - Base failure rate: **boom 13.4%** (168/1254), **longterm 15.2%** (151/991). 319 failures total.
- **Single flags use the EXACT validated repo definitions** (`layer3/findings/n14_wipeout_anatomy.py`):
  `tiny_sales` = `pre_ipo_net_sales<25`; `lossmaking` = `pre_ipo_pat<=0`; `pat_neg_latest` = `pat_yr3<=0`;
  `declining_rev` = `net_sales_yr3<net_sales_yr1`; `declining_pat` = `pat_yr3<pat_yr1`; `high_debt` = `pre_ipo_debt_equity>2`;
  `thin_margin` = `pre_ipo_pat_margin_pct<3`; `high_ofs` = `ofs_pct>50`; `small_issue` = `issue_size_cr<15`;
  `obscure_banker` = lead-manager appears in `<12` deals; `cyclical_sector` ∈ {Commodities, Industrials, Energy}.
  NaN where inputs missing — never imputed; a null flag is never a red flag.
- **2×2 per era:** base(0,0), A-only(1,0), B-only(0,1), BOTH(1,1), each with Wilson 95% CI. The **additive
  (independence) expectation** for BOTH = `base + (A_only-base) + (B_only-base)`. Super-additive ⇔ observed BOTH > expectation.
- **Pre-listing features only** — never current/post-listing fields (the reverse-causation trap that killed micro-cap).

## Results — every theory-driven pair tested

For each pair: the two single-flag rates, the no-flag base, the BOTH cell, additive expectation vs observed, and the verdict.
Rates are failure-rate % [Wilson CI]. **BOTH-cell N is the gate** (need ≥20 in *both* eras to claim anything).

| Pair (mechanism) | Era | base(0,0) | A-only | B-only | BOTH(1,1) | add.exp → obs | BOTH N |
|---|---|---|---|---|---|---|---|
| **tiny_sales × lossmaking** — micro-rev company that ALSO loses money | boom | 11.4% | 23.7% | 0.0% | **20.0%** [8,42] | 12.4→20.0 SUPER\* | 20 |
| (tiny pre-IPO base + no profit = nothing to underpin price) | long | 12.7% | 11.1% | 12.5% | **22.9%** [12,39] | 10.9→22.9 SUPER | 35 |
| tiny_sales × obscure_banker — small co + small/captive banker | boom | 8.7% | 22.3% | 20.8% | 30.0% | 34.4→30.0 sub | 30 |
| | long | 11.5% | 13.0% | 20.8% | 15.8% | 22.3→15.8 sub | **19** |
| small_issue × obscure_banker — tiny raise pushed by fringe banker | boom | 9.3% | 18.8% | 20.5% | 30.0% | 30.0→30.0 add | 30 |
| | long | 17.7% | 8.1% | 23.7% | 11.4% | 14.1→11.4 sub | 35 |
| lossmaking × high_ofs — insiders cashing out of a money-loser | boom | 15.8% | 8.9% | 1.1% | 0.0% | (artifact) | **19** |
| | long | 14.0% | 20.0% | 4.6% | 0.0% | — | **4** |
| high_debt × cyclical_sector — leverage into a cyclical | boom | 4.6% | 9.6% | 3.8% | 4.5% | 8.8→4.5 sub | 22 |
| | long | 8.4% | 16.2% | 4.9% | 0.0% | — | **16** |
| declining_rev × high_debt — shrinking top-line + leverage | boom | 11.7% | 26.1% | 9.3% | 10.0% | 23.7→10.0 sub | **10** |
| | long | 12.6% | 10.0% | 16.1% | 0.0% | — | **2** |
| thin_margin × high_debt — fragile margins + leverage | boom | 11.8% | 15.7% | 13.5% | **0.0%** | 17.4→0.0 sub | 29 |
| | long | 12.4% | 9.8% | 6.9% | **16.7%** [8,31] | 4.2→16.7 SUPER | 42 |
| declining_pat × high_debt | boom | 11.6% | 23.5% | 8.3% | 12.5% | 20.3→12.5 sub | **8** |
| | long | 14.1% | 0.0% | 9.7% | 66.7% | (N=3) | **3** |
| lossmaking × high_debt — loss-maker carrying debt | boom | 12.9% | 6.5% | 9.9% | 0.0% | 3.5→0.0 sub | **12** |
| | long | 11.3% | 15.2% | 6.7% | **45.5%** [21,72] | 10.5→45.5 SUPER | **11** |
| tiny_sales × high_debt | boom | 10.6% | 22.8% | 4.7% | 22.2% | 16.8→22.2 SUPER | **18** |
| | long | 11.2% | 12.7% | 10.7% | 20.0% | 12.3→20.0 SUPER | **15** |
| declining_rev × thin_margin | boom | 11.4% | 33.9% | 15.2% | 17.4% | 37.7→17.4 sub | 46 |
| | long | 15.0% | 0.0% | 13.8% | 13.3% | -1.3→13.3 SUPER | **15** |
| lossmaking × declining_rev | boom | 12.5% | 4.8% | 29.8% | 7.1% | 22.1→7.1 sub | **14** |
| | long | 14.1% | 20.0% | 6.7% | 0.0% | — | **3** |
| tiny_sales × cyclical_sector | boom | 4.2% | 20.8% | 4.7% | 16.7% | 21.2→16.7 sub | 24 |
| | long | 8.2% | 10.5% | 6.9% | 9.4% | 9.2→9.4 SUPER(flat) | 32 |
| obscure_banker × high_ofs | boom | 13.6% | 24.0% | 0.6% | 4.3% | 11.0→4.3 sub | 23 |
| | long | 15.5% | 22.6% | 4.0% | 6.7% | 11.1→6.7 sub | **15** |
| thin_margin × cyclical_sector | boom | 8.1% | 7.5% | 5.8% | 7.1% | 5.3→7.1 SUPER(flat) | 42 |
| | long | 6.8% | 12.8% | 9.1% | 4.3% | 15.1→4.3 sub | 46 |

Additional theory pairs tested (`/tmp/extra.py`), all FAILED the gate — listed for completeness:
`lossmaking × obscure_banker` (sub-additive both eras; both-cell N=8/6), `tiny_sales × declining_rev`
(strongly **sub**-additive — the two flags overlap heavily, 43% expected vs 27%/0% observed),
`declining_pat × thin_margin` (boom sub, long SUPER but only via a 0% A-only artifact),
`obscure_banker × high_debt` (boom sub, long both-cell N=4), `lossmaking × cyclical_sector` (sub-additive, thin),
`lossmaking × thin_margin` (insufficient-N both eras).

\* **boom super-additivity is a statistical artifact, see adjudication below.**

## Adjudication against the discipline

**Pairs that pass the BOTH-cell N≥20-in-both-eras gate at all:** only `tiny_sales × lossmaking`,
`small_issue × obscure_banker`, `thin_margin × high_debt`, `declining_rev × thin_margin` (boom 46 / **long 15** → fails),
`tiny_sales × cyclical_sector`, `thin_margin × cyclical_sector`. Everything else dies on cell-N (the whole point of the
N-on-the-cell rule: rare-flag×rare-flag cells are noise — `declining_pat×high_debt` longterm N=3 "66.7%" is exactly the
fake-pattern trap).

Of those, **cross-regime super-additive in BOTH eras:** none cleanly.

- **`tiny_sales × lossmaking`** — the only pair flagged super-additive in both eras by the additive-model test, BUT
  scrutiny (`/tmp/scrutiny.py`) shows the **boom verdict is an artifact**: lossmaking-*alone* in boom has a **0.0%**
  failure rate (N=44, k=0), which drags the additive expectation down to 12.4%, so BOTH=20% "beats" it — yet BOTH (20%,
  N=20) is actually **below** tiny_sales-alone (23.7%). It does not exceed its strongest constituent flag. In **longterm**
  the interaction is *real and clean*: tiny_sales-alone 11.1%, lossmaking-alone 12.5%, BOTH jumps to **22.9%** [12,39] —
  clearly above both. **Verdict: genuine interaction in LONGTERM only; boom is additive-at-best (single-regime).**

- **`thin_margin × high_debt`** and **`lossmaking × high_debt`** — super-additive and striking in **longterm**
  (16.7% and a dramatic 45.5%), but **sub-additive (0.0% BOTH) in boom**, and `lossmaking×high_debt` fails the cell-N gate
  (N=12/11). High-debt's destructive interactions only appear in the mature/longterm cohort — consistent with the existing
  finding that `high_debt` is a longterm-only flag. **Single-regime, not cross-regime.**

- **`tiny_sales × high_debt`** — super-additive in BOTH eras directionally (16.8→22.2 boom, 12.3→20.0 long), the most
  *symmetric* signal, but **fails the cell-N gate** (BOTH N=18 boom / 15 long, both <20) and the CIs are wide. Promising
  HYPOTHESIS, not a claim.

- `small_issue × obscure_banker` — passes cell-N but is **merely-additive** (boom 30.0 exp = 30.0 obs) / sub-additive
  (long). Two fringe-deal flags that co-occur but don't amplify. No interaction.

- `tiny_sales × cyclical_sector`, `thin_margin × cyclical_sector` — pass cell-N but flip sign across eras (super in one,
  sub in the other) and the "super" sides are essentially flat (obs ≈ exp). **No robust interaction.**

## Ranking (by strength of evidence for a genuine interaction)

1. **`tiny_sales × lossmaking`** — strongest, but **half-cross-regime**: a real super-additive interaction in longterm
   (22.9% vs ~11–12% singles), an artifact in boom. Tier: *single-regime-validated (longterm) / boom-additive*.
2. **`tiny_sales × high_debt`** — best *symmetric* candidate (super-additive directionally in both eras) but **under-powered**
   (both-cells N=18/15). Tier: *hypothesis, needs more data*.
3. `lossmaking × high_debt` / `thin_margin × high_debt` — dramatic in longterm, absent in boom; high-debt is a
   longterm-only amplifier. Tier: *single-regime (longterm)*.
4. Everything else — merely-additive, sub-additive, sign-flipping, or insufficient-N. **No interaction.**

A recurring, important null result: several intuitively "double-bad" pairs are **sub-additive** — the two flags
overlap so much they're nearly the same signal (`tiny_sales × declining_rev`: expected 43%, observed 27%/0%), or one
flag selects a *different, safer* population (`high_ofs` is protective — established firms — so `lossmaking × high_ofs`
and `obscure_banker × high_ofs` collapse toward 0%). Stacking red flags does **not** generally multiply risk.

## Caveats

- The boom failure proxy (dead-money) is younger and SME-heavy; longterm failure (wipeout) is mature. The two eras measure
  different death modes, so "cross-regime" here is a strong robustness bar by design.
- Multiple-comparisons: ~21 pairs × 2 eras tested. With single-flag base ~13–15%, isolated "super-additive" cells with
  N<20 are expected by chance — which is exactly why the N≥20-on-the-cell + both-eras gate is non-negotiable.
- Wilson CIs on the surviving both-cells are wide (e.g. tiny_sales×lossmaking longterm [12,39]); even the best interaction
  is a tendency, not a deterministic rule.

---

## BOTTOM LINE

**No combination clears the full bar (super-additive AND cross-regime AND N≥20-on-cell in both eras).** Honestly, the
single flags are essentially all there is. The closest things to a genuine interaction:

1. **tiny_sales × lossmaking** — a *real* super-additive interaction, but **only in the longterm cohort** (BOTH = 22.9%
   vs ~11–12% for either flag alone, N=35); in boom it does not beat tiny-sales alone (the "super-additive" reading there
   is an artifact of lossmaking-alone being 0%). Cross-regime: **fails** — call it single-regime.
2. **high_debt as a longterm-only amplifier** (× lossmaking → 45.5%, × thin_margin → 16.7%) — super-additive in longterm,
   vanishes in boom. Cross-regime: **fails**.
3. **tiny_sales × high_debt** — the only *symmetric* (both-era directionally super-additive) candidate, but **under-powered**
   (cell N=18/15 < 20). A hypothesis worth revisiting as the boom cohort ages — not a claim.

Net: interaction-hunting did **not** surface a new, durable, cross-regime failure predictor beyond the known single flags.
The disciplined answer is that combinations mostly stack additively (or even sub-additively, because the flags overlap),
and `high_debt`'s only real interactive bite is confined to the mature cohort.
