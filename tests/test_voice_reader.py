import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time

try:
    import pytest
except ImportError:
    pytest = None

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts" / "GV-2"
ART.mkdir(parents=True, exist_ok=True)
FIXTURES_DIR = ROOT / "tests" / "fixtures"
NEWS_FIXTURE = (FIXTURES_DIR / "news.json").read_text(encoding="utf-8")
SUMMARIES_FIXTURE = (FIXTURES_DIR / "summaries.json").read_text(encoding="utf-8")

MOCK_SPEECH_SCRIPT = """
window.__spoken = [];
const synth = new EventTarget();
synth.voices = [
  { lang: 'te-IN', name: 'Telugu Test Voice', voiceURI: 'te-test' },
  { lang: 'en-IN', name: 'English Test Voice', voiceURI: 'en-test' }
];
synth.getVoices = () => synth.voices;
synth.speak = u => {
  window.__spoken.push(u.text);
  window.__lastUtterance = u;
  setTimeout(() => {
    if (u.onend) u.onend();
  }, 120);
};
synth.cancel = () => { window.__spoken = []; };
synth.resume = () => {};
Object.defineProperty(window, 'speechSynthesis', { value: synth, writable: true });
window.SpeechSynthesisUtterance = class {
  constructor(text) {
    this.text = text || '';
    this.lang = '';
    this.voice = null;
    this.rate = 1;
    this.onend = null;
    this.onerror = null;
  }
};
"""


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def route_fixtures(page, route_summaries=True):
    page.route("**/data/news.json", lambda route: route.fulfill(
        status=200,
        content_type="application/json; charset=utf-8",
        body=NEWS_FIXTURE
    ))
    if route_summaries:
        page.route("**/data/summaries.json", lambda route: route.fulfill(
            status=200,
            content_type="application/json; charset=utf-8",
            body=SUMMARIES_FIXTURE
        ))


if pytest is None:
    # Isolate optional browser tests from standard unittest discovery
    pass
else:
    if sync_playwright is None:
        pytestmark = pytest.mark.skip(reason="playwright is not installed")

    @pytest.fixture(scope="module")
    def server():
        srv = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(ROOT)))
        thread = threading.Thread(target=srv.serve_forever, daemon=True)
        thread.start()
        yield f"http://127.0.0.1:{srv.server_port}"
        srv.shutdown()

    @pytest.fixture(scope="module")
    def browser_instance():
        with sync_playwright() as pw:
            launch_args = {
                "headless": True,
                "args": ["--no-sandbox", "--disable-dev-shm-usage", "--autoplay-policy=no-user-gesture-required"]
            }
            if Path("/usr/bin/google-chrome").exists():
                launch_args["executable_path"] = "/usr/bin/google-chrome"
            browser = pw.chromium.launch(**launch_args)
            yield browser
            browser.close()

    @pytest.mark.parametrize("width,height,label", [
        (390, 844, "mobile-390"),
        (1280, 800, "desktop-1280"),
    ])
    def test_voice_reader_speech_sentence_highlighting(server, browser_instance, width, height, label):
        context = browser_instance.new_context(viewport={"width": width, "height": height})
        context.add_init_script(MOCK_SPEECH_SCRIPT)
        page = context.new_page()
        route_fixtures(page)

        # Open story with pairs (be4d5ceb60) behind voice flag ?voice=1
        url = f"{server}/?voice=1#/s/be4d5ceb60"
        page.goto(url)
        page.wait_for_selector("#reader:not([hidden])")
        page.wait_for_selector(".r-sum")

        # Verify sentence spans exist
        page.wait_for_selector(".r-sum[lang='en'] .r-sentence")
        page.wait_for_selector(".r-sum[lang='te'] .r-sentence")

        en_sentences = page.locator(".r-sum[lang='en'] .r-sentence")
        te_sentences = page.locator(".r-sum[lang='te'] .r-sentence")
        assert en_sentences.count() >= 4, f"Expected at least 4 paired sentences, found {en_sentences.count()}"
        assert te_sentences.count() >= 4, f"Expected at least 4 paired sentences, found {te_sentences.count()}"

        # 1. Start Listen in English
        en_listen = page.locator(".r-sum[lang='en'] .r-listen")
        en_listen.click()

        # Assert sentence 0 is highlighted
        page.wait_for_selector(".r-sum[lang='en'] .r-sentence[data-idx='0'].is-active")
        assert en_listen.locator("span").inner_text() == "⏹ Stop"

        # Save screenshot of English sentence 0
        en_shot_path = ART / f"{label}-en-active.png"
        page.screenshot(path=str(en_shot_path))
        assert en_shot_path.exists()

        # Assert highlighting advances to sentence 1
        page.wait_for_selector(".r-sum[lang='en'] .r-sentence[data-idx='1'].is-active", timeout=5000)
        # Sentence 0 should no longer be active
        assert not page.locator(".r-sum[lang='en'] .r-sentence[data-idx='0']").get_attribute("class").count("is-active")

        # Stop English playback
        en_listen.click()
        page.wait_for_function("!document.querySelector('.r-sum[lang=\"en\"] .r-sentence.is-active')")
        assert en_listen.locator("span").inner_text() == "🔊 Listen"

        # 2. Start Listen in Telugu
        te_listen = page.locator(".r-sum[lang='te'] .r-listen")
        te_listen.click()

        # Assert sentence 0 is highlighted
        page.wait_for_selector(".r-sum[lang='te'] .r-sentence[data-idx='0'].is-active")
        assert te_listen.locator("span").inner_text() == "⏹ Stop"

        # Save screenshot of Telugu sentence 0
        te_shot_path = ART / f"{label}-te-active.png"
        page.screenshot(path=str(te_shot_path))
        assert te_shot_path.exists()

        # Assert highlighting advances to sentence 1
        page.wait_for_selector(".r-sum[lang='te'] .r-sentence[data-idx='1'].is-active", timeout=5000)
        assert not page.locator(".r-sum[lang='te'] .r-sentence[data-idx='0']").get_attribute("class").count("is-active")

        # Stop Telugu playback
        te_listen.click()
        page.wait_for_function("!document.querySelector('.r-sum[lang=\"te\"] .r-sentence.is-active')")
        assert te_listen.locator("span").inner_text() == "🔊 Listen"

        context.close()

    def test_voice_reader_mp3_playback(server, browser_instance):
        """Verify pre-built MP3 playback for story beb21be0b4."""
        context = browser_instance.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        route_fixtures(page)

        # Open story with prebuilt MP3 (beb21be0b4)
        url = f"{server}/?voice=1#/s/beb21be0b4"
        page.goto(url)
        page.wait_for_selector("#reader:not([hidden])")
        page.wait_for_selector(".r-sum[lang='en'] .r-sentence")

        en_listen = page.locator(".r-sum[lang='en'] .r-listen")
        en_listen.click()

        # Assert initial sentence highlight
        page.wait_for_selector(".r-sum[lang='en'] .r-sentence[data-idx='0'].is-active")
        assert en_listen.locator("span").inner_text() == "⏹ Stop"

        shot_path = ART / "desktop-mp3-active.png"
        page.screenshot(path=str(shot_path))
        assert shot_path.exists()

        # Stop
        en_listen.click()
        page.wait_for_function("!document.querySelector('.r-sum[lang=\"en\"] .r-sentence.is-active')")
        context.close()

    def test_voice_reader_stops_playback_on_summary_load(server, browser_instance):
        """Verify reader stops active playback before rerendering when summaries resolve."""
        context = browser_instance.new_context(viewport={"width": 1280, "height": 800})
        context.add_init_script(MOCK_SPEECH_SCRIPT)
        page = context.new_page()
        route_fixtures(page, route_summaries=False)

        summaries_route_holder = []
        def handle_summaries(route):
            summaries_route_holder.append(route)

        page.route("**/data/summaries.json", handle_summaries)

        url = f"{server}/?voice=1#/s/be4d5ceb60"
        page.goto(url)
        page.wait_for_selector("#reader:not([hidden])")
        page.wait_for_selector(".r-sum")

        en_listen = page.locator(".r-sum[lang='en'] .r-listen")
        en_listen.click()

        page.wait_for_selector(".r-sum[lang='en'] .r-sentence[data-idx='0'].is-active")
        assert en_listen.locator("span").inner_text() == "⏹ Stop"

        assert len(summaries_route_holder) >= 1
        summaries_route_holder[0].fulfill(
            status=200,
            content_type="application/json; charset=utf-8",
            body=SUMMARIES_FIXTURE
        )

        # Playback is stopped cleanly upon summaries load before replacing body
        page.wait_for_function("document.querySelector('.r-sum[lang=\"en\"] .r-listen span')?.innerText.includes('Listen')")
        page.wait_for_function("!document.querySelector('.r-sentence.is-active')")
        context.close()

    def test_voice_reader_sample_lookup_aborts_if_route_changes(server, browser_instance):
        """Verify sample lookup does not open story if route changed before request resolved."""
        context = browser_instance.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        route_fixtures(page)

        sample_route_holder = []
        def handle_sample(route):
            sample_route_holder.append(route)

        page.route("**/voice/sample/news.json", handle_sample)

        page.goto(f"{server}/?voice=1")
        page.wait_for_selector("#feed")

        # Set route to a story ID that only exists in sample/news.json
        page.evaluate("location.hash = '#/s/sample-pending'")

        deadline = time.time() + 3
        while not sample_route_holder and time.time() < deadline:
            page.wait_for_timeout(50)
        assert len(sample_route_holder) >= 1

        # User closes the reader / clears hash while sample lookup is in-flight
        page.evaluate("location.hash = ''")
        page.wait_for_function("location.hash === ''")

        sample_payload = {
            "items": [
                {
                    "id": "sample-pending",
                    "title": "Sample Pending Story",
                    "summary": "Sample summary",
                    "sum_en": "Sample EN sentence.",
                    "sum_te": "నమూనా వాక్యం.",
                    "summary_status": "paired",
                    "published": "2026-10-15T00:00:00Z",
                    "source": "Sample Source",
                    "category": "science",
                    "link": "https://example.com"
                }
            ]
        }
        sample_route_holder[0].fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(sample_payload)
        )

        page.wait_for_timeout(200)

        # Reader must remain hidden because the route changed before sample resolved
        reader_hidden = page.evaluate("document.getElementById('reader').hidden")
        assert reader_hidden is True
        assert page.evaluate("location.hash") == ""
        context.close()

    def test_voice_reader_legacy_decimals_preserved(server, browser_instance):
        """Verify legacy stories without pairs preserve decimals in display and speech."""
        context = browser_instance.new_context(viewport={"width": 1280, "height": 800})
        context.add_init_script(MOCK_SPEECH_SCRIPT)
        page = context.new_page()
        route_fixtures(page)

        # Open legacy story with decimal '$16.8 billion' (378259bf26)
        url = f"{server}/?voice=1#/s/378259bf26"
        page.goto(url)
        page.wait_for_selector("#reader:not([hidden])")
        page.wait_for_selector(".r-sum[lang='en'] .r-sentence")

        en_sentences = page.locator(".r-sum[lang='en'] .r-sentence")
        assert en_sentences.count() == 2, f"Expected 2 sentences, got {en_sentences.count()}"
        en_texts = [en_sentences.nth(i).inner_text() for i in range(en_sentences.count())]
        assert any("$16.8 billion" in t for t in en_texts), f"$16.8 billion not found in {en_texts}"
        assert not any("$16. 8 billion" in t for t in en_texts), f"Corrupted decimal found in {en_texts}"

        te_sentences = page.locator(".r-sum[lang='te'] .r-sentence")
        assert te_sentences.count() == 2, f"Expected 2 Telugu sentences, got {te_sentences.count()}"
        te_texts = [te_sentences.nth(i).inner_text() for i in range(te_sentences.count())]
        assert any("$16.8" in t for t in te_texts), f"$16.8 not found in Telugu sentences {te_texts}"
        assert not any("$16. 8" in t for t in te_texts), f"Corrupted Telugu decimal found in {te_texts}"

        # Test playback highlights sentence 0 then sentence 1
        en_listen = page.locator(".r-sum[lang='en'] .r-listen")
        en_listen.click()
        page.wait_for_selector(".r-sum[lang='en'] .r-sentence[data-idx='0'].is-active")
        page.wait_for_selector(".r-sum[lang='en'] .r-sentence[data-idx='1'].is-active", timeout=5000)

        en_listen.click()
        page.wait_for_function("!document.querySelector('.r-sum[lang=\"en\"] .r-sentence.is-active')")
        context.close()

    def test_voice_reader_module_failure_fallback_and_recovery(server, browser_instance):
        """Verify Listen falls back to speechSynthesis on module failure and recovers without reload."""
        context = browser_instance.new_context(viewport={"width": 1280, "height": 800})
        context.add_init_script(MOCK_SPEECH_SCRIPT)
        page = context.new_page()
        route_fixtures(page)

        # Abort voice module loading
        page.route("**/voice/src/gn-voice.js*", lambda route: route.abort())

        url = f"{server}/?voice=1#/s/be4d5ceb60"
        page.goto(url)
        page.wait_for_selector("#reader:not([hidden])")
        page.wait_for_selector(".r-sum")

        en_listen = page.locator(".r-sum[lang='en'] .r-listen")
        en_listen.click()

        # 1. Verify fallback to speechSynthesis
        page.wait_for_selector(".r-sum[lang='en'] .r-listen.on")
        assert en_listen.locator("span").inner_text() == "⏹ Stop"

        # Verify speech was called via window.speechSynthesis
        page.wait_for_function("window.__spoken && window.__spoken.length >= 1")
        spoken = page.evaluate("window.__spoken")
        assert len(spoken) >= 1, f"Expected speech synthesis spoken text, got {spoken}"

        # Verify voice player class did not break reader or set __readerPlayer
        active_player = page.evaluate("window.__readerPlayer")
        assert active_player is None, "Should not have instantiated voice player when module failed"

        # Stop fallback playback
        en_listen.click()
        page.wait_for_function("!document.querySelector('.r-sum[lang=\"en\"] .r-listen.on')")
        assert en_listen.locator("span").inner_text() == "🔊 Listen"

        # 2. Recover WITHOUT reload: allow the voice module route
        page.unroute("**/voice/src/gn-voice.js*")

        # Click Listen again
        en_listen.click()

        # Voice player loads successfully and activates sentence highlighting
        page.wait_for_selector(".r-sum[lang='en'] .r-sentence[data-idx='0'].is-active")
        assert en_listen.locator("span").inner_text() == "⏹ Stop"
        player_active = page.evaluate("Boolean(window.__readerPlayer)")
        assert player_active is True, "Voice player should be active after recovery"

        # Stop voice player
        en_listen.click()
        page.wait_for_function("!document.querySelector('.r-sum[lang=\"en\"] .r-sentence.is-active')")
        context.close()

    def test_voice_reader_summary_status_no_pairs_reads_via_speech(server, browser_instance):
        """Verify summary_status='summary' story without pairs renders summaries and reads via speech."""
        context = browser_instance.new_context(viewport={"width": 1280, "height": 800})
        context.add_init_script(MOCK_SPEECH_SCRIPT)
        page = context.new_page()
        route_fixtures(page)

        url = f"{server}/?voice=1#/s/summary-story-no-pairs"
        page.goto(url)
        page.wait_for_selector("#reader:not([hidden])")

        # Must NOT render Publisher excerpt
        assert page.locator("h2:has-text('Publisher excerpt')").count() == 0

        # Renders bilingual summary sections with sentence spans
        page.wait_for_selector(".r-sum[lang='en'] .r-sentence")
        page.wait_for_selector(".r-sum[lang='te'] .r-sentence")

        en_listen = page.locator(".r-sum[lang='en'] .r-listen")
        en_listen.click()

        # Sentence highlighting begins at sentence 0
        page.wait_for_selector(".r-sum[lang='en'] .r-sentence[data-idx='0'].is-active")
        assert en_listen.locator("span").inner_text() == "⏹ Stop"

        # Highlighting advances to sentence 1
        page.wait_for_selector(".r-sum[lang='en'] .r-sentence[data-idx='1'].is-active", timeout=5000)

        # Stop
        en_listen.click()
        page.wait_for_function("!document.querySelector('.r-sum[lang=\"en\"] .r-sentence.is-active')")
        context.close()
