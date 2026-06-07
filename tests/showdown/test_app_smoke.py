"""Execution proof #3: the Streamlit app boots headless, every screen of the
st.navigation multipage app renders, and no exception text appears anywhere.
Playwright chromium; server killed in teardown.

(Phase-2: the app moved from a 5-tab layout to a 7-page st.navigation app —
HOME, Recommendations, IPO Detail, Evidence, Registry, Track Record, Data.
This test visits each route directly + exercises the in-page tabs that remain
on Track Record, asserting no traceback/exception text on any of them.)
"""
import os
import socket
import subprocess
import sys
import time

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PORT = 8761


def _port_open(port):
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


@pytest.fixture(scope="module")
def app_server():
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py",
         "--server.headless", "true", "--server.port", str(PORT),
         "--browser.gatherUsageStats", "false"],
        cwd=ROOT, env={**os.environ, "PYTHONPATH": ROOT},
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):                      # up to 60s to boot
        if _port_open(PORT):
            break
        time.sleep(1)
    else:
        proc.terminate()
        pytest.fail("streamlit never opened its port")
    yield f"http://127.0.0.1:{PORT}"
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:            # streamlit can be slow to exit
        proc.kill()
        proc.wait(timeout=10)


# the seven screens of the multipage app, as direct routes (st.navigation slugs)
SCREENS = ["/", "/recommendations", "/ipo_detail", "/evidence",
           "/registry", "/track_record", "/data"]
ERROR_MARKERS = ("Traceback", "Exception:", "KeyError", "AttributeError",
                 "NameError", "TypeError", "ValueError:")


def test_all_screens_render_without_exceptions(app_server):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip("playwright not installed")
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch()
        except Exception as e:                   # browser binaries missing
            pytest.skip(f"chromium unavailable: {e}")
        page = browser.new_page()
        # every screen renders clean
        for route in SCREENS:
            page.goto(app_server + route, timeout=60_000)
            page.wait_for_load_state("networkidle", timeout=60_000)
            page.wait_for_timeout(3500)          # let the screen compute/render
            body = page.inner_text("body")
            for marker in ERROR_MARKERS:
                assert marker not in body, f"screen {route} shows error text: {marker}"
        # the in-page tabs that remain (Track Record: track / backtester / validation)
        page.goto(app_server + "/track_record", timeout=60_000)
        page.wait_for_load_state("networkidle", timeout=60_000)
        page.wait_for_timeout(4000)
        tabs = page.locator('button[role="tab"]')
        for i in range(tabs.count()):
            tabs.nth(i).click()
            page.wait_for_timeout(3000)
            body = page.inner_text("body")
            for marker in ERROR_MARKERS:
                assert marker not in body, f"track-record tab {i} shows error text: {marker}"
        # an IPO Detail page with a real ISIN must render its 8 sections clean
        page.goto(app_server + "/ipo_detail?isin=INE002L01015", timeout=60_000)
        page.wait_for_load_state("networkidle", timeout=60_000)
        page.wait_for_timeout(4500)
        body = page.inner_text("body")
        for marker in ERROR_MARKERS:
            assert marker not in body, f"ipo_detail?isin shows error text: {marker}"
        browser.close()
