"""Default-site Telugu MP3 and unavailable-state acceptance; no network required."""
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading

try:
    import pytest
except ImportError:
    pytest = None
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'artifacts' / 'GN-6'
FIXTURES = ROOT / 'tests' / 'fixtures'
NEWS = json.loads((FIXTURES / 'te-audio-news.json').read_text(encoding='utf-8'))
STORY = NEWS['items'][0]
NO_VOICES = """
const synth = new EventTarget();
synth.getVoices = () => [];
synth.cancel = () => {};
synth.resume = () => {};
synth.speak = () => { throw Error('No device voice should be used'); };
Object.defineProperty(window, 'speechSynthesis', {value:synth, configurable:true});
"""


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


if pytest is not None:
    if sync_playwright is None:
        pytestmark = pytest.mark.skip(reason='playwright is not installed')

    @pytest.fixture(scope='module')
    def server():
        srv = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(ROOT)))
        thread = threading.Thread(target=srv.serve_forever, daemon=True)
        thread.start()
        try:
            yield f'http://127.0.0.1:{srv.server_port}'
        finally:
            srv.shutdown()
            srv.server_close()
            thread.join()

    @pytest.fixture(scope='module')
    def browser_instance():
        with sync_playwright() as pw:
            args = dict(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage',
                                            '--autoplay-policy=no-user-gesture-required'])
            if Path('/usr/bin/google-chrome').exists():
                args['executable_path'] = '/usr/bin/google-chrome'
            browser = pw.chromium.launch(**args)
            yield browser
            browser.close()

    @pytest.mark.parametrize('width', [390, 1280])
    @pytest.mark.parametrize('available', [True, False])
    def test_telugu_default_site(server, browser_instance, width, available):
        ART.mkdir(parents=True, exist_ok=True)
        context = browser_instance.new_context(viewport=dict(width=width, height=844))
        context.add_init_script(NO_VOICES)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        def route_request(route):
            url = route.request.url
            if url.endswith('/data/news.json'):
                route.fulfill(json=NEWS)
            elif url.endswith('/data/summaries.json'):
                route.fulfill(json={})
            elif url.endswith('/data/audio-config.json'):
                route.fulfill(json={'base_url':'https://audio.example/'})
            elif url == 'https://audio.example/manifest.json':
                route.fulfill(headers={'Access-Control-Allow-Origin':'*'}, json={'version':1, 'stories':{STORY['id']:{'te':{
                    'file':'te/fixture.mp3', 'text':STORY['sum_te']}}} if available else {}})
            elif url == 'https://audio.example/te/fixture.mp3':
                route.fulfill(path=str(FIXTURES / 'audio' / 'te-maya.mp3'), content_type='audio/mpeg',
                              headers={'Access-Control-Allow-Origin':'*'})
            elif url.startswith(server + '/'):
                route.continue_()
            else:
                route.abort()  # no fonts, SDKs, or other requests may reach the network
        page.route('**/*', route_request)
        try:
            page.goto(f'{server}/#/s/te-audio')  # deliberately no ?voice=1
            button = page.locator('.r-sum[lang="te"] .r-listen')
            button.wait_for()
            page.evaluate('document.fonts.ready')
            button.scroll_into_view_if_needed()
            button.click()
            if available:
                page.wait_for_function("window.__readerPlayer?.mode === 'audio' && window.__readerPlayer.audio.currentTime > 0 && !window.__readerPlayer.audio.paused")
                assert button.inner_text() == '⏹ Stop'
                assert page.evaluate('window.__readerPlayer.audio.src') == 'https://audio.example/te/fixture.mp3'
                page.screenshot(path=str(ART / f'te-mp3-playing-{width}.png'))
                button.click()
                page.wait_for_function('window.__readerPlayer === null')
                assert button.inner_text() == '🔊 Listen'
            else:
                note = page.locator('.r-sum[lang="te"] .r-audio-status[role="status"]')
                note.wait_for()
                assert 'ఈ వార్తకు ఆడియో ఇంకా అందుబాటులో లేదు' in note.inner_text()
                assert "Audio isn't available for this story yet" in note.inner_text()
                note.scroll_into_view_if_needed()
                assert button.inner_text() == '🔊 Listen'
                page.screenshot(path=str(ART / f'te-audio-unavailable-{width}.png'))
            assert not errors
        finally:
            context.close()
