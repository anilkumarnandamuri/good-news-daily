import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts" / "GV-2"
ART.mkdir(parents=True, exist_ok=True)

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
        browser = pw.chromium.launch(
            executable_path="/usr/bin/google-chrome",
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--autoplay-policy=no-user-gesture-required"]
        )
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
