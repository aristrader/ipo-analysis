"""Execution proof #3: the Streamlit app boots headless, all 5 tabs render, and no
exception text appears anywhere. Playwright chromium; server killed in teardown.
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
    proc.wait(timeout=10)


def test_all_tabs_render_without_exceptions(app_server):
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
        page.goto(app_server, timeout=60_000)
        page.wait_for_load_state("networkidle", timeout=60_000)
        tabs = page.locator('button[role="tab"]')
        n = tabs.count()
        assert n >= 5, f"expected >=5 tabs, found {n}"
        for i in range(n):
            tabs.nth(i).click()
            page.wait_for_timeout(2500)          # let the tab compute/render
            body = page.inner_text("body")
            for marker in ("Traceback", "Exception:", "KeyError", "AttributeError"):
                assert marker not in body, f"tab {i} shows error text: {marker}"
        browser.close()
