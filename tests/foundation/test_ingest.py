"""Tests for foundation.ingest — the scraper honesty layer (T0.1 scaffolding)."""
import requests

from foundation import config, ingest


# --- parse helpers: never mint a placeholder (honesty rule 1) ----------------------
def test_num_preserves_real_zero_but_nulls_missing():
    assert ingest.num("0") == 0.0          # a REAL zero must survive
    assert ingest.num("0.00") == 0.0
    assert ingest.num("") is None          # missing -> None, NOT 0
    assert ingest.num("-") is None
    assert ingest.num("N/A") is None
    assert ingest.num(None) is None


def test_num_cleans_formatting():
    assert ingest.num("1,234.5") == 1234.5
    assert ingest.num("₹500") == 500.0
    assert ingest.num("2.5x") == 2.5       # subscription multiple
    assert ingest.num("12%") == 12.0


def test_text_nulls_placeholders():
    assert ingest.text("  Infosys ") == "Infosys"
    assert ingest.text("") is None
    assert ingest.text("NA") is None
    assert ingest.text("—") is None


def test_ratio_parts_no_fabrication():
    assert ingest.ratio_parts("1:10") == (1.0, 10.0)
    assert ingest.ratio_parts("5") is None        # bare number is not a ratio form
    assert ingest.ratio_parts("bonus:") is None    # partial -> None, never a fabricated 1.0


def test_ratios_equal_uses_relative_tolerance():
    assert ingest.ratios_equal(1.428571, 1.4285714) is True   # same ratio, float jitter
    assert ingest.ratios_equal(5.0, 10.0) is False
    assert ingest.ratios_equal(None, 5.0) is False


# --- fetch: distinguishes failure kinds (honesty rule 2) ---------------------------
class _Resp:
    def __init__(self, code, text="payload"):
        self.status_code = code
        self.text = text


class _Sess:
    def __init__(self, resp=None, exc=None):
        self._resp, self._exc = resp, exc

    def get(self, url, **kw):
        if self._exc:
            raise self._exc
        return self._resp


def test_fetch_ok():
    f = ingest.fetch("http://x", session=_Sess(_Resp(200)), pace=False)
    assert f.status == ingest.OK and f.ok


def test_fetch_genuine_http_error_not_retryable():
    f = ingest.fetch("http://x", session=_Sess(_Resp(404, "nope")), pace=False)
    assert f.status == ingest.HTTP_ERROR and not f.retryable


def test_fetch_blocked_is_retryable():
    f = ingest.fetch("http://x", session=_Sess(_Resp(429)), retries=1, pace=False)
    assert f.status == ingest.BLOCKED and f.retryable


def test_fetch_empty_payload():
    f = ingest.fetch("http://x", session=_Sess(_Resp(200, "   ")), pace=False)
    assert f.status == ingest.EMPTY


def test_fetch_network_error_is_retryable():
    f = ingest.fetch("http://x", session=_Sess(exc=requests.ConnectionError("boom")),
                     retries=1, pace=False)
    assert f.status == ingest.NETWORK_ERROR and f.retryable


# --- save_raw: preserves the raw payload (honesty rule 3) --------------------------
def test_save_raw_writes_under_output_root(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "OUTPUT_ROOT", tmp_path)
    p = ingest.save_raw("chittorgarh", "INE123.html", "<html>raw</html>")
    assert p.exists()
    assert p.read_text() == "<html>raw</html>"
    assert p.parent == tmp_path / "raw" / "chittorgarh" / "raw"
