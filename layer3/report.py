"""Finding model + HTML report assembler.

The assembler enforces the min-N floor UNBYPASSABLY (methodology fix #6): any table that
carries an 'N' column has its numeric metric cells suppressed to 'insufficient (N=k)' on
rows where N < MIN_N_HINT — a finding cannot accidentally print a confident number off N=3.
"""
from dataclasses import dataclass, field
from typing import List, Tuple
import pandas as pd
from layer3 import config

# identifier columns never suppressed (count columns are detected separately)
_ID_COLS = {"segment", "cohort", "mcap", "market_cap_class", "sector", "broad_sector",
            "bucket", "listing_pop_bucket", "ofs_bucket", "group", "horizon", "year", "label",
            "metric", "range",
            # new-findings label columns (must survive suppression as identifiers)
            "sub_total_x_band", "qib_retail_skew", "issue_size_cr_band", "anchor_pct_tertile",
            "pe_vs_sector", "tertile", "cash_vs_profit", "listing_class", "instrument_type",
            "lead_manager"}


def _is_count(c):
    return c == "N" or c == "n" or c.startswith("N_") or c.startswith("n_")


@dataclass
class Finding:
    id: str
    title: str
    narrative: str
    tables: List[Tuple[str, pd.DataFrame]] = field(default_factory=list)
    charts: List[Tuple[str, str]] = field(default_factory=list)   # (caption, data-uri)
    caveats: List[str] = field(default_factory=list)


def _guard_table(t: pd.DataFrame) -> pd.DataFrame:
    """Suppress metric cells on rows whose SMALLEST count column is below the hint floor.
    Guarding on the minimum count means a row is only as trustworthy as its smallest sample
    (so a metric computed on a maturity-gated subset can't slip through on a large total N).
    Detects count columns by pattern (N, n, N_*, n_*) so N_matured / N_winners are caught."""
    counts = [c for c in t.columns if _is_count(c)]
    if not counts:
        return t
    t = t.copy()
    metric_cols = [c for c in t.columns if c not in _ID_COLS and not _is_count(c)]

    def _row_min(i):
        vals = []
        for c in counts:
            try:
                vals.append(int(t.at[i, c]))
            except (TypeError, ValueError):
                pass
        return min(vals) if vals else 0

    subfloor = [i for i in t.index if _row_min(i) < config.MIN_N_HINT]
    if not subfloor:
        return t
    for c in metric_cols:                      # object dtype so a string can replace a float
        t[c] = t[c].astype(object)
    for i in subfloor:
        tag = f"insufficient (N={_row_min(i)})"
        for c in metric_cols:
            t.at[i, c] = tag
    return t


_CSS = """body{font-family:-apple-system,Segoe UI,Roboto,Helvetica,sans-serif;max-width:1040px;
margin:24px auto;color:#222;padding:0 18px;line-height:1.45}
h1{border-bottom:3px solid #2c6fbb;padding-bottom:6px}h2{margin-top:46px;border-bottom:1px solid #ccc;padding-top:8px}
table{border-collapse:collapse;margin:12px 0;font-size:13px}th,td{border:1px solid #ddd;padding:4px 9px;text-align:right}
th:first-child,td:first-child{text-align:left}thead th{background:#eef3f9}tr:nth-child(even){background:#fafafa}
.caveat{background:#fff8e1;border-left:4px solid #f0c000;padding:6px 11px;margin:6px 0;font-size:12.5px}
.note{background:#eef7ee;border-left:4px solid #4a9}
img{max-width:100%;margin:10px 0;border:1px solid #eee}.cap{font-size:12px;color:#666;margin-top:4px}
nav{background:#f5f7fa;border:1px solid #e2e6ea;padding:10px 16px;border-radius:6px}
nav a{margin-right:14px;font-size:13px}.meta{color:#666;font-size:12.5px}"""


def assemble(findings, subtitle="", method_note=""):
    p = [f"<!doctype html><html><head><meta charset='utf-8'><title>IPO Layer-3 Part A</title>",
         f"<style>{_CSS}</style></head><body>",
         "<h1>Indian IPOs — Descriptive Report (Layer 3, Part A)</h1>",
         f"<p class='meta'>{subtitle}<br>Returns = <b>alpha vs Nifty 50</b> in all base-rate tables. "
         "Distributions shown P10 / median / P90 with N. <b>SME and Mainboard are never pooled.</b> "
         "Sub-floor cells (N&lt;10) are suppressed. Not financial advice.</p>"]
    if method_note:
        p.append(f"<div class='caveat note'>{method_note}</div>")
    p.append("<nav><b>Findings:</b> " + " ".join(f"<a href='#{f.id}'>{f.title}</a>" for f in findings) + "</nav>")
    for f in findings:
        p.append(f"<h2 id='{f.id}'>{f.title}</h2>")
        p.append(f"<p>{f.narrative}</p>")
        for cap, uri in f.charts:
            p.append(f"<img src='{uri}' alt='{cap}'><div class='cap'>{cap}</div>")
        for cap, tdf in f.tables:
            p.append(f"<div class='cap'>{cap}</div>")
            p.append(_guard_table(tdf).to_html(index=False, na_rep="—", border=0,
                                                float_format=lambda v: f"{v:,.2f}"))
        for c in f.caveats:
            p.append(f"<div class='caveat'>⚠ {c}</div>")
    p.append("</body></html>")
    return "\n".join(p)
