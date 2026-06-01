import pandas as pd
from layer3 import charts
from layer3.report import Finding, assemble, _guard_table


def test_charts_return_data_uris():
    assert charts.bar_png(["A", "B"], [1.0, 2.0], ns=[50, 3]).startswith("data:image/png;base64,")
    assert charts.line_png([1, 2], {"x": [0.1, 0.2]}).startswith("data:image/png;base64,")
    assert charts.scatter_png([1, 2], [3, 4], sizes=[10, 20]).startswith("data:image/png;base64,")
    assert charts.hist_png([1, 2, 3, 4]).startswith("data:image/png;base64,")


def test_guard_suppresses_subfloor_rows():
    t = pd.DataFrame({"segment": ["a", "b"], "median_alpha": [0.5, 0.9], "N": [200, 4]})
    g = _guard_table(t)
    assert g.loc[0, "median_alpha"] == 0.5            # N=200 kept
    assert "insufficient" in str(g.loc[1, "median_alpha"])  # N=4 suppressed
    assert g.loc[1, "segment"] == "b"                 # identifier never suppressed


def test_assemble_self_contained_html(tmp_path):
    f = Finding(
        id="t0", title="Demo finding", narrative="hello world",
        tables=[("cap", pd.DataFrame({"segment": ["x"], "v": [1.0], "N": [99]}))],
        charts=[("c", "data:image/png;base64,AAAA")],
        caveats=["small N somewhere"],
    )
    html = assemble([f], subtitle="test run", method_note="method note here")
    for token in ["<html", "Demo finding", "hello world", "small N somewhere",
                  "<table", "method note here", "never pooled"]:
        assert token in html
    out = tmp_path / "r.html"; out.write_text(html)
    assert out.stat().st_size > 500
