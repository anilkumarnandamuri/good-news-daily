import json
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request
import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / "artifacts" / "GN-1"


@pytest.fixture(scope="session")
def server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]

    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 5
    started = False
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{url}/index.html", timeout=1) as resp:
                if resp.status == 200:
                    started = True
                    break
        except Exception:
            time.sleep(0.05)
    if not started:
        proc.terminate()
        raise RuntimeError("Failed to start local http server")

    yield url
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.mark.parametrize(
    "width,height,filename",
    [
        (390, 844, "gn1-reader-390.png"),
        (1280, 800, "gn1-reader-1280.png"),
    ],
)
def test_legacy_feed_story_reader(server, width, height, filename):
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    news = json.loads((ROOT / "data/news.json").read_text(encoding="utf-8"))
    first_story = news["items"][0]
    story_id = first_story["id"]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": width, "height": height})
        context.route(
            "**/*",
            lambda route: route.continue_()
            if "127.0.0.1" in route.request.url or "localhost" in route.request.url
            else route.abort(),
        )
        page = context.new_page()

        page.goto(f"{server}/#/s/{story_id}")
        page.wait_for_selector("#reader:not([hidden])")

        in_short_heading = page.locator('.r-sum h2:has-text("In short")')
        in_short_heading.wait_for(state="visible", timeout=5000)
        assert in_short_heading.is_visible()

        listen_btn = page.locator('.r-listen[data-lang="en"]')
        assert listen_btn.is_visible()

        excerpt_heading = page.locator('h2:has-text("Publisher excerpt")')
        assert excerpt_heading.count() == 0

        page.screenshot(path=str(ARTIFACTS_DIR / filename))
        browser.close()
