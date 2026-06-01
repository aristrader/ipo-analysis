"""matplotlib -> base64 PNG helpers. Sub-floor (N<hint) bars are greyed so a bar at
N=3 never looks like a bar at N=300 (methodology fix #6)."""
import base64
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from layer3 import config

_OK = "#2c6fbb"
_LOW = "#c9c9c9"   # sub-floor / insufficient N


def _uri(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def bar_png(labels, values, ns=None, title="", ylabel="", xlabel=""):
    """Bar chart. If ns (per-bar N) is given, bars with N<MIN_N_HINT are greyed."""
    fig, ax = plt.subplots(figsize=(7.2, 4))
    colors = _OK
    if ns is not None:
        colors = [_OK if (n or 0) >= config.MIN_N_HINT else _LOW for n in ns]
    ax.bar([str(x) for x in labels], values, color=colors)
    ax.axhline(0, color="#888", lw=0.8)
    ax.set_title(title); ax.set_ylabel(ylabel); ax.set_xlabel(xlabel)
    if ns is not None:
        for i, (v, n) in enumerate(zip(values, ns)):
            ax.annotate(f"N={n}", (i, v), ha="center",
                        va="bottom" if (v or 0) >= 0 else "top", fontsize=8, color="#555")
    fig.autofmt_xdate(rotation=20)
    return _uri(fig)


def line_png(x, series, title="", ylabel="", xlabel=""):
    """series = {label: [y...]}; x shared. Markers + legend."""
    fig, ax = plt.subplots(figsize=(7.2, 4))
    for label, ys in series.items():
        ax.plot([str(v) for v in x], ys, marker="o", label=label)
    ax.axhline(0, color="#888", lw=0.6)
    ax.set_title(title); ax.set_ylabel(ylabel); ax.set_xlabel(xlabel); ax.legend(fontsize=9)
    return _uri(fig)


def scatter_png(xs, ys, sizes=None, labels=None, title="", xlabel="", ylabel=""):
    """Bubble scatter (e.g. sector alpha vs wipeout-rate, bubble = N)."""
    fig, ax = plt.subplots(figsize=(7.2, 5))
    ax.scatter(xs, ys, s=[max(20, (s or 0)) for s in (sizes or [40] * len(xs))],
               alpha=0.55, color=_OK, edgecolors="#1a3f6b")
    if labels:
        for x, y, t in zip(xs, ys, labels):
            ax.annotate(str(t), (x, y), fontsize=7, alpha=0.8)
    ax.axhline(0, color="#888", lw=0.6); ax.axvline(0, color="#888", lw=0.6)
    ax.set_title(title); ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    return _uri(fig)


def hist_png(values, bins=30, title="", xlabel="", ylabel="count"):
    fig, ax = plt.subplots(figsize=(7.2, 4))
    ax.hist(values, bins=bins, color=_OK, alpha=0.8)
    ax.set_title(title); ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    return _uri(fig)
