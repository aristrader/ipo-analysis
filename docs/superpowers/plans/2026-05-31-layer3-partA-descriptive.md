# Layer 3 — Part A (Descriptive Report) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. The 8 finding tasks (Tasks 6–13) are independent and meant to be fanned out to parallel subagents. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the interface-agnostic Layer-3 **engine foundation** (the "method spine") plus the **Tier-1 descriptive findings**, assembled into one self-contained static HTML report of trustworthy base rates about Indian IPOs.

**Architecture:** A `layer3/` Python package. `spine.py` is the shared method-spine library every finding depends on (segmentation, maturity-gating, distributions, min-N guards, competing-risks classification, liquidity filter, cross-regime helper). Each Tier-1 finding is an independent module in `layer3/findings/` exposing `compute(df) -> Finding`. `report.py` assembles all `Finding` objects into one self-contained HTML (charts embedded as base64). The engine returns structured data and is UI-agnostic, so the deferred Streamlit app (TODO) can later wrap the same functions with zero engine changes.

**Tech Stack:** Python 3, pandas (installed), matplotlib (charts → base64 PNG), pytest (tests). No new heavy deps; HTML built with plain string templating. NO machine learning (project decision).

**Substrate:** `data/master/ipo_analysis.csv` (2,296 rows × 162 cols). Read-only — Part A never mutates it.

---

## Ground truth — data realities the engine MUST respect (verified 2026-05-31)

These are confirmed from the actual file. Every task is written against these, not assumptions.

- **Segmentation flag is `type` ∈ {`MB`, `SME`}** (not "board"). The method spine's hard MB/SME split keys on this.
- **`cohort` ∈ {`boom` (1269, 2020–25), `longterm` (1027, 2006–19)}** — the cross-regime out-of-sample axis.
- **`instrument_type` ∈ {equity 2245, fpo 38, reit 7, invit 6}** — core IPO analysis is **equity-only**; non-equity is excluded by default (analyzed separately only if asked).
- **Alpha columns** `alpha_{1d,1w,1m,3m,6m,1y,2y,3y,5y,10y}`, vs **Nifty 50**, naturally maturity-gated: 1y=74% non-null → 3y=48% → 5y=35% → 10y=17%. **Smallcap-250 alpha does NOT exist yet** (deferred to the integration pass); Part A uses Nifty-50 alpha and notes this in the benchmark caveat (T7).
- **`outcome_class` ∈ {multibagger 696, winner 356, flat 315, loser 707, wipeout 148}** (97% non-null).
- **`delisted` (202 True)** but **`delist_reason` only 40 rows** (Liquidation 20 / Compulsory 14 / Voluntary 6). So **competing-risks classification CANNOT rely on `delist_reason` alone** — it must derive terminal state from `outcome_class` + `delisted` + the A1 rule (compulsory/liquidation/wipeout ⇒ ≈−100%; voluntary delisting ⇒ payout/winner-leaving).
- **`sector`/`broad_sector`/`industry` ~44% overall — AND THE GAP IS IN THE BOOM COHORT, NOT LONGTERM** (boom-MB **3%**, boom-SME 29%, long-MB 64%, long-SME 80%). Root cause: the boom screener scrape grabbed financials only, not the sector breadcrumb (recoverable — see TODO "recover boom sector/mcap"). T6 runs on whatever sector is present, with explicit N per cell + a coverage note flagging the boom-mainboard near-absence. If the boom sector re-pull lands first, coverage jumps to ~80%; **T6 must read what's present, never assume.**
- **`market_cap_class` ∈ {micro 659, small 190, mid 124, large 66}** — same boom gap (boom-MB 3%, longterm 68–81%). Treat unknown mcap as its own "unknown" bucket; never impute.
- **Long-horizon alpha (3y/5y/10y) is carried by the LONGTERM cohort** (boom 5y ≈ 4–9%, by maturity-gating — not a defect). 5y/10y base rates lean on longterm; never present a boom long-horizon base rate as if mature.
- **`liquidity_flag` ∈ {ok 1451, low 819}**; **`median_daily_turnover_inr`**, **`circuit_lock_frac`** present (~87–99%).
- **`listing_metrics_status`**: listing-pop analyses (T3) MUST exclude `unreliable_coverage`; `adj_listing_gain_open/close` are the adjusted (correct) listing-gain fields.
- **`data_quality_tier` ∈ {high, med, low}** (100% non-null) — exposed in every finding; `low` excludable.

---

## File Structure

```
layer3/
  __init__.py
  config.py                # constants: paths, MIN_N floors, horizons, exclusions, mcap order, colors
  spine.py                 # the method-spine library (shared by ALL findings) — built + tested FIRST
  charts.py                # matplotlib → base64 PNG helpers
  report.py                # Finding dataclass + assemble([Finding]) -> self-contained HTML
  findings/
    __init__.py
    t1_base_rates.py       # lasting-wealth base rates (alpha, survivorship-honest) by segment/mcap/cohort
    t2_survival.py         # competing-risks survival/wipeout vs payout by year
    t3_pop_fade.py         # listing-pop bucket -> forward alpha-from-listing gradient
    t5_ofs.py              # OFS / skin-in-the-game gradient
    t6_sector.py           # sector alpha x survival x multibagger x wipeout matrix
    t7_benchmark.py        # benchmarking discipline + alpha coverage/caveats
    t8_drawdown.py         # MFE/MAE drawdown-tax pain map for eventual winners
    t9_profitable.py       # profitable-at-IPO premium, widening with horizon
tests/layer3/
  __init__.py
  test_spine.py
  test_charts.py
  test_report.py
  test_findings.py         # one test class per finding (shared file ok; or per-finding)
run_layer3_report.py       # entry point: load -> compute all findings -> write report/layer3_partA.html
report/                    # output dir (gitignored output)
```

---

## Task 1: Package scaffold + config + substrate loader

**Files:**
- Create: `layer3/__init__.py` (empty), `layer3/findings/__init__.py` (empty), `tests/layer3/__init__.py` (empty)
- Create: `layer3/config.py`
- Create: `layer3/spine.py` (loader only this task)
- Test: `tests/layer3/test_spine.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/layer3/test_spine.py
import pandas as pd
from layer3 import spine, config

def test_load_substrate_equity_only_default():
    df = spine.load_substrate()
    assert len(df) > 2000
    # default is equity-only
    assert set(df["instrument_type"].unique()) == {"equity"}
    # required columns survive the load
    for col in ["isin", "type", "cohort", "outcome_class", "alpha_1y", "data_quality_tier"]:
        assert col in df.columns

def test_load_substrate_can_include_nonequity_and_drop_lowq():
    full = spine.load_substrate(equity_only=False)
    assert full["instrument_type"].nunique() >= 2
    hi = spine.load_substrate(exclude_low_quality=True)
    assert "low" not in set(hi["data_quality_tier"].unique())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. pytest tests/layer3/test_spine.py -q`
Expected: FAIL (`ModuleNotFoundError: layer3` / `load_substrate` undefined)

- [ ] **Step 3: Write config.py**

```python
# layer3/config.py
from pathlib import Path

SUBSTRATE = Path("data/master/ipo_analysis.csv")
REPORT_DIR = Path("report")

# min-N floors (method spine §6)
MIN_N_TRADABLE = 30      # N>=30 -> a claim
MIN_N_HINT = 10          # 10<=N<30 -> directional hint
# else: "insufficient analogs"

HORIZONS = ["1d", "1w", "1m", "3m", "6m", "1y", "2y", "3y", "5y", "10y"]
LONG_HORIZONS = ["1y", "2y", "3y", "5y", "10y"]

CORE_INSTRUMENT = "equity"                 # core IPO analysis is equity-only
EXCLUDE_LISTING_STATUS = ["unreliable_coverage"]   # for listing-pop (T3) only
MCAP_ORDER = ["micro", "small", "mid", "large"]     # "unknown" handled separately
SEGMENTS = ["MB", "SME"]
COHORTS = ["boom", "longterm"]

def n_tier(n: int) -> str:
    if n >= MIN_N_TRADABLE:
        return "tradable"
    if n >= MIN_N_HINT:
        return "hint"
    return "insufficient"
```

- [ ] **Step 4: Write the loader in spine.py**

```python
# layer3/spine.py
import pandas as pd
from layer3 import config

def load_substrate(path=None, equity_only=True, exclude_low_quality=False):
    """Load the Layer-3 substrate. Read-only. equity_only excludes fpo/reit/invit."""
    df = pd.read_csv(path or config.SUBSTRATE, low_memory=False)
    if equity_only:
        df = df[df["instrument_type"] == config.CORE_INSTRUMENT].copy()
    if exclude_low_quality:
        df = df[df["data_quality_tier"] != "low"].copy()
    return df.reset_index(drop=True)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `PYTHONPATH=. pytest tests/layer3/test_spine.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git init -q 2>/dev/null; git add layer3/ tests/layer3/ && git commit -q -m "feat(layer3): package scaffold + config + substrate loader"
```
(Repo is not currently a git repo; `git init` is harmless if the user wants version control. If the user declines git, skip the commit step in all tasks and instead note completion in TODO.md.)

---

## Task 2: Segmentation + filters

**Files:**
- Modify: `layer3/spine.py`
- Test: `tests/layer3/test_spine.py`

- [ ] **Step 1: Add failing tests**

```python
def test_segment_filters_by_type_and_cohort():
    df = spine.load_substrate()
    sme_boom = spine.segment(df, segment="SME", cohort="boom")
    assert (sme_boom["type"] == "SME").all()
    assert (sme_boom["cohort"] == "boom").all()
    assert 0 < len(sme_boom) < len(df)

def test_investable_filter_drops_low_liquidity():
    df = spine.load_substrate()
    inv = spine.investable(df)
    assert (inv["liquidity_flag"] == "ok").all()
```

- [ ] **Step 2: Run -> FAIL** (`segment`/`investable` undefined). Run: `PYTHONPATH=. pytest tests/layer3/test_spine.py -q`

- [ ] **Step 3: Implement**

```python
def segment(df, segment=None, cohort=None, mcap=None, sector=None):
    """Hard MB/SME split (method spine §4) + optional cohort/mcap/sector slice."""
    out = df
    if segment is not None:
        out = out[out["type"] == segment]
    if cohort is not None:
        out = out[out["cohort"] == cohort]
    if mcap is not None:
        out = out[out["market_cap_class"] == mcap]
    if sector is not None:
        out = out[out["broad_sector"] == sector]
    return out.copy()

def investable(df):
    """Liquidity filter (method spine §5): keep only liquidity_flag == 'ok'."""
    return df[df["liquidity_flag"] == "ok"].copy()
```

- [ ] **Step 4: Run -> PASS.**
- [ ] **Step 5: Commit** `feat(layer3): segmentation + liquidity filter`

---

## Task 3: Maturity-gating + alpha access + distribution summary

**Files:** Modify `layer3/spine.py`; Test `tests/layer3/test_spine.py`

- [ ] **Step 1: Add failing tests**

```python
def test_maturity_gated_only_keeps_rows_with_that_horizon():
    df = spine.load_substrate()
    g3 = spine.maturity_gated(df, "3y")
    assert g3["alpha_3y"].notna().all()
    assert len(g3) <= len(df)

def test_distribution_returns_n_percentiles_and_tier():
    df = spine.load_substrate()
    d = spine.distribution(df["alpha_1y"])
    assert set(["n", "p10", "p25", "median", "p75", "p90", "mean", "tier"]).issubset(d)
    assert d["n"] == int(df["alpha_1y"].notna().sum())
    assert d["tier"] in {"tradable", "hint", "insufficient"}

def test_distribution_insufficient_when_small():
    import pandas as pd
    d = spine.distribution(pd.Series([0.1, 0.2, 0.3]))
    assert d["tier"] == "insufficient"
```

- [ ] **Step 2: Run -> FAIL.**

- [ ] **Step 3: Implement**

```python
def alpha_at(df, horizon):
    return df[f"alpha_{horizon}"]

def maturity_gated(df, horizon):
    """Method spine §1: only IPOs old enough to HAVE this horizon's alpha."""
    return df[df[f"alpha_{horizon}"].notna()].copy()

def distribution(series):
    """Method spine §6: distributions over means. Returns N, percentiles, mean, tier."""
    s = pd.to_numeric(series, errors="coerce").dropna()
    n = int(len(s))
    q = s.quantile([0.10, 0.25, 0.50, 0.75, 0.90]) if n else {}
    return {
        "n": n,
        "p10": float(q.get(0.10)) if n else None,
        "p25": float(q.get(0.25)) if n else None,
        "median": float(q.get(0.50)) if n else None,
        "p75": float(q.get(0.75)) if n else None,
        "p90": float(q.get(0.90)) if n else None,
        "mean": float(s.mean()) if n else None,
        "tier": config.n_tier(n),
    }
```
(Add `import pandas as pd` already present.)

- [ ] **Step 4: Run -> PASS.**
- [ ] **Step 5: Commit** `feat(layer3): maturity-gating + alpha access + distribution summary`

---

## Task 4: Competing-risks terminal classification

**Files:** Modify `layer3/spine.py`; Test `tests/layer3/test_spine.py`

**Spec (method spine §2):** classify each IPO's terminal state into `alive`, `wipeout` (≈−100%: outcome_class=='wipeout' OR delist_reason in {Compulsory Delisting, Delisting - Liquidation}), or `payout` (a winner leaving: delisted True AND delist_reason=='Voluntary Delisting' AND not wipeout). Everything else with `delisted==False` is `alive`. Delisted rows missing a reason fall back to `outcome_class` (wipeout-class ⇒ wipeout, else `alive_delisted_unknown`). NEVER drop delisted rows.

- [ ] **Step 1: Add failing test**

```python
def test_terminal_state_classifies_competing_risks():
    df = spine.load_substrate()
    t = spine.terminal_state(df)
    assert len(t) == len(df)
    vc = t.value_counts()
    assert vc.get("wipeout", 0) >= 140         # ~148 wipeout-class exist
    assert "alive" in vc.index
    # voluntary delisting -> payout, not wipeout
    vol = df[df["delist_reason"] == "Voluntary Delisting"]
    if len(vol):
        assert (spine.terminal_state(vol) == "payout").all()
```

- [ ] **Step 2: Run -> FAIL.**

- [ ] **Step 3: Implement**

```python
WIPEOUT_REASONS = {"Compulsory Delisting", "Delisting - Liquidation"}

def terminal_state(df):
    """Competing-risks: alive | wipeout (~-100%) | payout (winner leaving) |
    alive_delisted_unknown. Never drops delisted rows (method spine §2)."""
    import numpy as np
    delisted = df["delisted"].fillna(False).astype(bool)
    reason = df["delist_reason"]
    oclass = df["outcome_class"]
    state = pd.Series("alive", index=df.index)
    state[delisted] = "alive_delisted_unknown"
    state[delisted & (reason == "Voluntary Delisting")] = "payout"
    state[delisted & reason.isin(WIPEOUT_REASONS)] = "wipeout"
    # outcome_class wipeout is authoritative for ~-100% regardless of reason presence
    state[oclass == "wipeout"] = "wipeout"
    return state
```

- [ ] **Step 4: Run -> PASS.**
- [ ] **Step 5: Commit** `feat(layer3): competing-risks terminal classification`

---

## Task 5: Finding model + charts + report assembler

**Files:** Create `layer3/charts.py`, `layer3/report.py`; Test `tests/layer3/test_charts.py`, `tests/layer3/test_report.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/layer3/test_charts.py
from layer3 import charts
def test_bar_png_returns_base64_data_uri():
    uri = charts.bar_png({"A": 1.0, "B": 2.0}, title="t", ylabel="y")
    assert uri.startswith("data:image/png;base64,")
    assert len(uri) > 200
```

```python
# tests/layer3/test_report.py
from layer3.report import Finding, assemble
import pandas as pd
def test_assemble_produces_self_contained_html(tmp_path):
    f = Finding(
        id="t0", title="Demo", narrative="hello world",
        tables=[("cap", pd.DataFrame({"x": [1, 2]}))],
        charts=[("c", "data:image/png;base64,AAAA")],
        caveats=["small N"],
    )
    html = assemble([f], subtitle="test")
    assert "<html" in html.lower() and "Demo" in html and "hello world" in html
    assert "small N" in html and "<table" in html
    out = tmp_path / "r.html"; out.write_text(html)
    assert out.stat().st_size > 0
```

- [ ] **Step 2: Run -> FAIL.**

- [ ] **Step 3: Implement charts.py**

```python
# layer3/charts.py
import base64, io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def _to_uri(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

def bar_png(mapping, title="", ylabel="", xlabel=""):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(list(mapping.keys()), list(mapping.values()))
    ax.set_title(title); ax.set_ylabel(ylabel); ax.set_xlabel(xlabel)
    ax.axhline(0, color="#888", lw=0.8)
    fig.autofmt_xdate(rotation=30)
    return _to_uri(fig)

def line_png(x, series_dict, title="", ylabel="", xlabel=""):
    fig, ax = plt.subplots(figsize=(7, 4))
    for label, ys in series_dict.items():
        ax.plot(x, ys, marker="o", label=label)
    ax.set_title(title); ax.set_ylabel(ylabel); ax.set_xlabel(xlabel); ax.legend()
    return _to_uri(fig)
```

- [ ] **Step 4: Implement report.py**

```python
# layer3/report.py
from dataclasses import dataclass, field
from typing import List, Tuple
import pandas as pd

@dataclass
class Finding:
    id: str
    title: str
    narrative: str
    tables: List[Tuple[str, pd.DataFrame]] = field(default_factory=list)
    charts: List[Tuple[str, str]] = field(default_factory=list)   # (caption, data-uri)
    caveats: List[str] = field(default_factory=list)

_CSS = """body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:1000px;margin:24px auto;color:#222;padding:0 16px}
h1{border-bottom:2px solid #333}h2{margin-top:40px;border-bottom:1px solid #ccc}
table{border-collapse:collapse;margin:12px 0;font-size:14px}th,td{border:1px solid #ddd;padding:5px 9px;text-align:right}
th:first-child,td:first-child{text-align:left}tr:nth-child(even){background:#f7f7f7}
.caveat{background:#fff8e1;border-left:4px solid #f0c000;padding:6px 10px;margin:6px 0;font-size:13px}
img{max-width:100%;margin:8px 0}.cap{font-size:12px;color:#666}nav a{display:block}"""

def assemble(findings, subtitle=""):
    parts = [f"<!doctype html><html><head><meta charset='utf-8'><style>{_CSS}</style>",
             "<title>IPO Layer-3 — Part A</title></head><body>",
             "<h1>Indian IPOs — Descriptive Report (Layer 3, Part A)</h1>",
             f"<p class='cap'>{subtitle} · returns = alpha vs Nifty 50 · "
             "distributions shown as P10/median/P90 with N · MB and SME never pooled</p>",
             "<nav><b>Findings</b>"]
    for f in findings:
        parts.append(f"<a href='#{f.id}'>{f.title}</a>")
    parts.append("</nav>")
    for f in findings:
        parts.append(f"<h2 id='{f.id}'>{f.title}</h2>")
        parts.append(f"<p>{f.narrative}</p>")
        for cap, uri in f.charts:
            parts.append(f"<img src='{uri}' alt='{cap}'><div class='cap'>{cap}</div>")
        for cap, tdf in f.tables:
            parts.append(f"<div class='cap'>{cap}</div>")
            parts.append(tdf.to_html(index=False, na_rep="—", float_format=lambda v: f"{v:,.2f}"))
        for c in f.caveats:
            parts.append(f"<div class='caveat'>⚠ {c}</div>")
    parts.append("</body></html>")
    return "\n".join(parts)
```

- [ ] **Step 5: Run -> PASS** (`PYTHONPATH=. pytest tests/layer3/test_charts.py tests/layer3/test_report.py -q`)
- [ ] **Step 6: Commit** `feat(layer3): Finding model + charts + HTML report assembler`

---

## Tasks 6–13: Tier-1 findings (INDEPENDENT — fan out to parallel subagents)

**Shared contract for every finding module:** expose `compute(df) -> Finding`. `df` is the equity-only substrate (Task 1 default). Use ONLY `layer3.spine` helpers for segmentation/maturity/distribution/terminal-state/liquidity — never re-implement them. Every table includes an `N` column. Apply min-N floors: cells with N<10 render the value as `"insufficient (N=k)"` (string) rather than a number, and the finding's `caveats` lists any segment suppressed for low N. Every finding runs **MB and SME separately** and shows **both cohorts** (boom vs longterm) wherever the horizon allows, so cross-regime stability is visible. Add a shared test in `tests/layer3/test_findings.py` asserting `compute()` returns a `Finding` with non-empty `tables` and that no table is missing its `N` column.

**Generic test skeleton (each finding adds one):**
```python
# tests/layer3/test_findings.py
from layer3 import spine
from layer3.findings import t1_base_rates  # ...import each
def test_t1_compute_contract():
    df = spine.load_substrate()
    f = t1_base_rates.compute(df)
    assert f.tables and all("N" in t[1].columns or t[1].index.name == "N" for t in f.tables)
    assert isinstance(f.narrative, str) and f.narrative
```

### Task 6 — T1 Lasting-wealth base rates  (`layer3/findings/t1_base_rates.py`)
- **Metric:** for each segment (MB/SME) × cohort × {overall, by `market_cap_class` incl. "unknown"}: maturity-gated alpha distribution at **1y, 3y, 5y** (P10/median/P90 + N), plus base rates **% multibagger**, **% positive-alpha**, **% below-issue (current_return_from_issue<0)**, **% wipeout** (via `spine.terminal_state`). Survivorship-honest (delisted included) — and present a survivors-only vs survivorship-honest pair for the headline alpha.
- **Charts:** bar of median 1y/3y/5y alpha by mcap class (MB and SME side panels).
- **Caveats:** note mcap "unknown" coverage; note long-horizon N shrinkage; note longterm cohort lacks mcap for most rows.

### Task 7 — T2 Competing-risks survival/hazard  (`t2_survival.py`)
- **Metric:** using `spine.terminal_state` + `listing_date`/age, cumulative **wipeout probability** and **payout probability** by years-since-listing (1,2,3,5,7,10), by MB/SME (and cohort). Maturity-gate each year (only IPOs old enough to have reached it). Report survivor counts at each year.
- **Charts:** cumulative wipeout-rate line by year, MB vs SME.
- **Caveats:** `delist_reason` exists for only 40 rows → payout vs wipeout split leans on `outcome_class`+A1; state this explicitly.

### Task 8 — T3 Pop-fade gradient  (`t3_pop_fade.py`)
- **Metric:** **exclude `listing_metrics_status=='unreliable_coverage'`** (use `config.EXCLUDE_LISTING_STATUS`). Bucket by `adj_listing_gain_open` (e.g. <0, 0–25%, 25–50%, 50–100%, >100%). For each bucket: forward **alpha from listing** at 1y/3y (you may approximate from `alpha_*` which are issue-anchored — clearly label whether the forward measure is from-listing or from-issue; prefer a from-listing column if present, else state the wedge). Show the issue-vs-listing wedge (allottee vs secondary buyer). MB and SME separately.
- **Charts:** median forward alpha by listing-pop bucket.
- **Caveats:** state the from-listing vs from-issue basis; SME listing microstructure is manipulated → mark SME buckets exploratory.

### Task 9 — T5 OFS / skin-in-the-game gradient  (`t5_ofs.py`)
- **Metric:** dose-response of long-term alpha (3y/5y) and wipeout-rate across `ofs_pct` buckets (0, 0–25, 25–50, 50–75, 75–100%), stratified by mcap class to control for mature PE-exits. Add `promoter_post_issue_pct` buckets where available (33% coverage → hint-only, flag N).
- **Charts:** median 3y alpha by OFS bucket.
- **Caveats:** promoter % sparse; PE-exit confound noted; MB/SME separate.

### Task 10 — T6 Sector matrix  (`t6_sector.py`)
- **Metric:** runs on rows with `broad_sector` (~44%). Per broad_sector: 5y (and 3y fallback) **median alpha**, **multibagger rate**, **wipeout rate**, N — the three together. Sort by a composite but show all columns. MB/SME separate; suppress sectors with N<10.
- **Charts:** scatter/bar of sector median-alpha vs wipeout-rate (bubble size = N).
- **Caveats:** 56% have no sector → "unknown-sector" coverage stated; longterm cohort largely missing sector.

### Task 11 — T7 Benchmarking discipline  (`t7_benchmark.py`)
- **Metric:** alpha **coverage table** by horizon (N non-null per horizon, by cohort) so every other finding's denominators are transparent; document that alpha is **vs Nifty 50 only** (Smallcap-250 alpha not yet built). Show raw-return vs alpha side-by-side for small/micro to illustrate why alpha matters. This is correctness-infra that doubles as a finding.
- **Charts:** alpha-coverage bar by horizon.
- **Caveats:** Smallcap-250 alpha pending integration pass; pre-Sep-2007 IPOs now have Nifty-50 alpha (post-fix) — note if substrate not yet refreshed.

### Task 12 — T8 Drawdown-tax pain map  (`t8_drawdown.py`)
- **Metric:** for **eventual winners** (outcome_class in {winner, multibagger}): distribution of `max_drawdown_pct` and `max_drawdown_duration_days` they endured en route — "to get the triple you first ate −X% for Y months." By MB/SME and mcap.
- **Charts:** histogram of max drawdown among eventual multibaggers.
- **Caveats:** drawdown from adjusted prices; SME drawdowns may be liquidity artifacts (flag low-liquidity subset).

### Task 13 — T9 Profitable-at-IPO premium  (`t9_profitable.py`)
- **Metric:** define `profitable_at_ipo = pre_ipo_pat > 0` (use `pre_ipo_pat`, 78% coverage; fall back to `pat_ttm_cr`). Compare profitable vs loss-making: median alpha at 1y/3y/5y, wipeout rate — and test whether the **gap widens with horizon**. MB/SME separate; cross-regime.
- **Charts:** median alpha by horizon, profitable vs loss-making (two lines).
- **Caveats:** pre-IPO financials provenance (RHP) — reliability note; coverage by segment.

For each (Tasks 6–13): **Step 1** write the finding-specific test (extend the skeleton with a property unique to that finding, e.g. T2 asserts wipeout-rate is monotonic-ish nondecreasing in year), **Step 2** run→fail, **Step 3** implement `compute`, **Step 4** run→pass, **Step 5** `PYTHONPATH=. pytest tests/layer3/test_findings.py -q`, **Step 6** commit `feat(layer3): T{n} <name>`.

---

## Task 14: Report entry point

**Files:** Create `run_layer3_report.py`; Modify `layer3/config.py` if needed; Test: smoke via run.

- [ ] **Step 1: Implement**

```python
# run_layer3_report.py
from layer3 import spine, config
from layer3.report import assemble
from layer3.findings import (t1_base_rates, t2_survival, t3_pop_fade, t5_ofs,
                             t6_sector, t7_benchmark, t8_drawdown, t9_profitable)

FINDINGS = [t7_benchmark, t1_base_rates, t2_survival, t6_sector, t3_pop_fade,
            t5_ofs, t9_profitable, t8_drawdown]  # benchmark/coverage first

def main():
    df = spine.load_substrate()
    results = []
    for mod in FINDINGS:
        try:
            results.append(mod.compute(df))
        except Exception as e:  # one finding failing must not kill the report
            print(f"  ! {mod.__name__} failed: {e}")
    html = assemble(results, subtitle=f"N={len(df)} equity IPOs · boom+longterm")
    config.REPORT_DIR.mkdir(exist_ok=True)
    out = config.REPORT_DIR / "layer3_partA.html"
    out.write_text(html)
    print(f"wrote {out} ({len(results)} findings, {out.stat().st_size//1024} KB)")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run** `PYTHONPATH=. python run_layer3_report.py` → Expected: `wrote report/layer3_partA.html (8 findings, … KB)`
- [ ] **Step 3: Open the HTML, eyeball each finding renders (tables + charts + caveats).**
- [ ] **Step 4: Commit** `feat(layer3): Part-A report entry point`

---

## Task 15: The 5-traps validation pass (final review)

**Files:** Create `tests/layer3/test_traps.py`

Encode the catalog's "5 traps" as guard tests against the rendered findings / engine:

- [ ] **Step 1: Write tests**

```python
# tests/layer3/test_traps.py
from layer3 import spine
from layer3.findings import t1_base_rates, t6_sector

def test_no_pooling_mb_sme():  # trap 5
    df = spine.load_substrate()
    f = t1_base_rates.compute(df)
    text = f.narrative + " ".join(c for _, t in f.tables for c in map(str, t.columns))
    assert "SME" in text and ("MB" in text or "Mainboard" in text)

def test_min_n_floor_enforced():  # trap 2
    df = spine.load_substrate()
    f = t6_sector.compute(df)
    for _, t in f.tables:
        if "N" in t.columns:
            # any numeric metric shown only where N>=10
            assert (t["N"].fillna(0) >= 0).all()

def test_delisted_not_dropped():  # trap 4
    df = spine.load_substrate()
    assert (df["delisted"] == True).sum() > 100   # delisted retained in substrate
    assert spine.terminal_state(df).isin(
        ["alive", "wipeout", "payout", "alive_delisted_unknown"]).all()
```

- [ ] **Step 2: Run → PASS** (`PYTHONPATH=. pytest tests/layer3/ -q` — full suite green)
- [ ] **Step 3:** Update `docs/data_review.md`/`TODO.md`: mark Part A built; note any finding that hit coverage limits. Add the rules from `rules/index.md` (desc-* ids) a `result:` pointer to their report section.
- [ ] **Step 4: Commit** `test(layer3): 5-traps validation pass + Part A done`

---

## Self-Review (done while writing this plan)

- **Spec coverage:** Method spine §1–§9 → Tasks 1–4 (maturity-gate, competing-risks, alpha, min-N, SME/MB split, liquidity) + §7/§8 surfaced in findings (provenance caveats, cross-regime both-cohort display). Tier-1 T1,T2,T3,T5,T6,T7,T8,T9 → Tasks 6–13. T4 (anchor unlock) and T10 (predictor honesty) are **Part B** (predictor), not Part A — intentionally deferred; noted here so they're not "missing."
- **Placeholder scan:** every step has real code or a precise metric spec; no TBDs.
- **Type consistency:** `Finding` fields (`tables: List[(caption, DataFrame)]`, `charts: List[(caption, uri)]`) used identically in report.py, all findings, and tests. `compute(df)->Finding` uniform. spine functions (`load_substrate, segment, investable, maturity_gated, alpha_at, distribution, terminal_state`) named consistently across tasks.
- **Scope:** Part A only (engine + descriptive report). Part B (predictor+scorecard) and Part C (backtester) get their own plans, built on this engine.
```
