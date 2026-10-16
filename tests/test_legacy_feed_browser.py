import json
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request

try:
    import pytest
except ImportError:
    pytest = None

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / "artifacts" / "GN-1"

CONTROLLED_LEGACY_FEED = {
    "generated": "2026-10-15T14:00:00Z",
    "count": 2,
    "items": [
        {
            "id": "legacy-sample-paired",
            "title": "Community Solar Microgrid Brings 24-Hour Reliable Power to Health Center",
            "link": "https://example.com/solar-health",
            "published": "Thu, 15 Oct 2026 12:00:00 GMT",
            "source": "Solar Daily",
            "category": "science",
            "score": 0.88,
            "summary": "Solar microgrid powers clinic around the clock.",
            "sum_en": "A new solar microgrid ensures continuous power for the primary health center. Critical vaccine storage and emergency equipment now operate uninterrupted day and night.",
            "sum_te": "నూతన సౌర మైక్రోగ్రిడ్ ప్రాథమిక ఆరోగ్య కేంద్రానికి నిరంతర విద్యుత్ సరఫరాను అందిస్తుంది. అత్యవసర టీకాలు మరియు పరికరాలు ఇప్పుడు రోజుకు 24 గంటలు పనిచేస్తాయి.",
            "read_time": 2,
        },
        {
            "id": "legacy-sample-excerpt",
            "title": "Local Youth Plant 5,000 Saplings in Weekend Reforestation Drive",
            "link": "https://example.com/reforestation",
            "published": "Thu, 15 Oct 2026 11:00:00 GMT",
            "source": "Green Earth",
            "category": "environment",
            "score": 0.82,
            "summary": "Volunteers planted 5,000 saplings across community lands.",
            "sum_en": "",
            "sum_te": "",
            "read_time": 1,
        },
    ],
}

if pytest is None:
    # Isolate optional browser tests from standard unittest discovery
    pass
else:
    if sync_playwright is None:
        pytestmark = pytest.mark.skip(reason="playwright is not installed")

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

        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(viewport={"width": width, "height": height})

            def handle_route(route):
                url = route.request.url
                if "/data/news.json" in url:
                    route.fulfill(
                        status=200,
                        content_type="application/json; charset=utf-8",
                        body=json.dumps(CONTROLLED_LEGACY_FEED),
                    )
                elif "127.0.0.1" in url or "localhost" in url:
                    route.continue_()
                else:
                    route.abort()

            context.route("**/*", handle_route)
            page = context.new_page()

            # Test legacy item with summaries: adapter derives summary_status='paired'
            page.goto(f"{server}/#/s/legacy-sample-paired")
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

    def test_legacy_feed_excerpt_fallback(server):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(viewport={"width": 390, "height": 844})

            def handle_route(route):
                url = route.request.url
                if "/data/news.json" in url:
                    route.fulfill(
                        status=200,
                        content_type="application/json; charset=utf-8",
                        body=json.dumps(CONTROLLED_LEGACY_FEED),
                    )
                elif "127.0.0.1" in url or "localhost" in url:
                    route.continue_()
                else:
                    route.abort()

            context.route("**/*", handle_route)
            page = context.new_page()

            # Test legacy item without summaries: adapter derives summary_status='excerpt'
            page.goto(f"{server}/#/s/legacy-sample-excerpt")
            page.wait_for_selector("#reader:not([hidden])")

            excerpt_heading = page.locator('.r-sum h2:has-text("Publisher excerpt")')
            excerpt_heading.wait_for(state="visible", timeout=5000)
            assert excerpt_heading.is_visible()

            listen_btn = page.locator('.r-listen[data-lang="en"]')
            assert listen_btn.count() == 0

            browser.close()
