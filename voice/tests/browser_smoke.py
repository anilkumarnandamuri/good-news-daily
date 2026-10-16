#!/usr/bin/env python3
"""Optional integration checks: python3 tests/browser_smoke.py (requires Playwright + Chrome)."""
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'test-results'
OUT.mkdir(exist_ok=True)
ART = ROOT / 'artifacts' / 'GV-1'
ART.mkdir(parents=True, exist_ok=True)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{server.server_port}/demo/'
P = "document.querySelector('gn-voice-player').player"


def ready(page):
    page.goto(URL)
    page.wait_for_function(f'{P}.stories.length === 5')
    page.wait_for_selector('.story-button')


def finish_clip(page):
    page.wait_for_function(f"{P}.state === 'playing' && {P}.audio.duration > 0")
    run = page.evaluate(f'{P}.runId')
    # SimpleHTTPRequestHandler has no byte-range seeking. Decode to a native ended
    # event at accelerated test-only speed instead of synthesizing completion.
    page.evaluate(f'{P}.audio.playbackRate = 16')
    page.wait_for_function(f"{P}.runId !== {run} || {P}.state === 'ended'")


try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True,
                                     args=['--no-sandbox', '--disable-dev-shm-usage'])
        context = browser.new_context(viewport={'width': 1440, 'height': 1250})
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        ready(page)
        page.screenshot(path=str(OUT / 'desktop-full.png'), full_page=True)
        assert page.locator('.story-button[aria-current=true]').count() == 1
        page.locator('.gn-play').click()
        page.wait_for_function(f"{P}.state === 'playing'")
        assert page.evaluate(f"{P}.mode") == 'audio'
        assert page.evaluate(f'{P}.audio.playbackRate') == 0.9
        assert page.evaluate('navigator.mediaSession.metadata.title')
        page.wait_for_function(f'{P}.audio.currentTime > 0.1')
        page.locator('.gn-play').click()
        assert page.evaluate(f'{P}.state') == 'paused'
        paused = page.evaluate(f'{P}.audio.currentTime')
        page.wait_for_timeout(150)
        assert abs(page.evaluate(f'{P}.audio.currentTime') - paused) < .05
        page.locator('.gn-play').click()
        page.wait_for_function(f"{P}.state === 'playing'")
        assert page.evaluate(f'{P}.audio.currentTime') >= paused
        page.locator('.gn-next').click()
        page.wait_for_function(f"{P}.index === 1 && {P}.state === 'playing'")
        assert page.locator('.story-button[aria-current=true]').get_attribute('data-index') == '1'
        page.locator('.gn-previous').click()
        page.wait_for_function(f'{P}.index === 0')
        page.locator('.gn-stop').click()
        assert page.evaluate(f"{P}.state === 'idle' && {P}.audio.paused && !{P}.audio.getAttribute('src')")
        # Both must play Telugu to completion, then English, then stop.
        page.locator('[data-language=both]').click()
        page.locator('.gn-play').click()
        finish_clip(page)
        page.wait_for_function(f"{P}.snapshot.currentLanguage === 'en' && {P}.state === 'playing'")
        finish_clip(page)
        page.wait_for_function(f"{P}.state === 'ended'")
        assert page.evaluate(f'{P}.index === 0 && {P}.progress === 1')
        # Radio: intro -> summary -> next story intro, and last story loops to first.
        page.locator('[data-language=te]').click()
        page.locator('.gn-radio-input').check()
        page.locator('.gn-play').click()
        page.wait_for_function(f'{P}.snapshot.intro')
        finish_clip(page)
        page.wait_for_function(f'!{P}.snapshot.intro')
        finish_clip(page)
        page.wait_for_function(f'{P}.index === 1 && {P}.snapshot.intro')
        page.evaluate(f'{P}.select(4)')
        finish_clip(page)
        page.wait_for_function(f'!{P}.snapshot.intro')
        finish_clip(page)
        page.wait_for_function(f'{P}.index === 0 && {P}.snapshot.intro')
        page.locator('.gn-stop').click()
        # Settings and persistence; input with keyboard is a real accessibility path.
        page.locator('.gn-settings summary').click()
        page.locator('.gn-rate').focus()
        page.keyboard.press('ArrowRight')
        assert page.evaluate(f'{P}.rate') == 1.0
        page.locator('[data-language=en]').click()
        page.reload()
        page.wait_for_function(f'{P}.stories.length === 5')
        assert page.evaluate(f"{P}.rate === 1 && {P}.language === 'en'")
        assert not errors, errors
        print('PASS: real MP3, pause/resume/stop, navigation, both, radio transitions/loop, metadata, keyboard rate, persistence')
        for width, scheme, name in [(390, 'light', 'mobile'), (320, 'light', 'narrow'), (390, 'dark', 'dark-mobile')]:
            mobile = browser.new_context(viewport={'width': width, 'height': 844}, color_scheme=scheme,
                                         reduced_motion='reduce', is_mobile=True, has_touch=True)
            view = mobile.new_page()
            ready(view)
            view.locator('.gn-settings summary').click()
            assert view.evaluate('document.documentElement.scrollWidth <= innerWidth'), name
            targets = view.locator('gn-voice-player button:visible, gn-voice-player select:visible, gn-voice-player summary:visible, .story-button').all()
            for target in targets:
                box = target.bounding_box()
                assert box['height'] >= 55.5, (name, target.inner_text(), box)
            view.screenshot(path=str(OUT / f'{name}.png'), full_page=True)
            mobile.close()
        print('PASS: 320/390px layout, dark mode, reduced motion, >=56px controls')
        # Screenshot matrix for review: 390/1280 wide x light/dark, saved to artifacts/GV-1/.
        for width, height in [(390, 844), (1280, 900)]:
            for scheme in ('light', 'dark'):
                shot = browser.new_context(viewport={'width': width, 'height': height}, color_scheme=scheme,
                                           reduced_motion='reduce')
                view = shot.new_page()
                ready(view)
                view.locator('.gn-settings summary').click()
                name = f'{width}-{scheme}'
                assert view.evaluate('document.documentElement.scrollWidth <= innerWidth'), name
                # Nothing inside the player may overflow horizontally or be clipped off-screen.
                assert view.evaluate('''() => [...document.querySelectorAll('gn-voice-player *')].every(el => {
                  const r = el.getBoundingClientRect();
                  return r.width === 0 || (r.left >= -0.5 && r.right <= innerWidth + 0.5);
                })'''), name
                # Telugu text must not be invisible against its background.
                assert view.evaluate('''() => {
                  const c = getComputedStyle(document.querySelector('.story-button'));
                  return c.color !== c.backgroundColor && parseFloat(c.fontSize) >= 14;
                }'''), name
                view.screenshot(path=str(ART / f'{name}.png'), full_page=True)
                view.screenshot(path=str(OUT / f'{name}.png'), full_page=True)
                shot.close()
        print('PASS: 390/1280px light/dark screenshots saved to artifacts/GV-1/')
        # Playback rate must persist across MP3 source changes.
        rate = browser.new_page()
        ready(rate)
        rate.evaluate(f'{P}.setRate(1.1)')
        rate.locator('.gn-play').click()
        rate.wait_for_function(f"{P}.state === 'playing' && {P}.mode === 'audio'")
        rate.locator('.gn-next').click()
        rate.wait_for_function(f"{P}.index === 1 && {P}.state === 'playing'")
        assert abs(rate.evaluate(f'{P}.audio.playbackRate') - 1.1) < 1e-6
        rate.close()
        print('PASS: playback rate persists across source changes')
        # Deterministic speech engine for voiceschanged, chunking, cancellation and missing-voice behavior.
        speech = browser.new_context()
        speech.add_init_script('''
          window.__spoken = []; window.__cancels = 0;
          const synth = new EventTarget(); synth.voices = [];
          synth.getVoices = () => synth.voices;
          synth.speak = u => { window.__spoken.push(u); window.__last = u; };
          synth.cancel = () => { window.__cancels++; };
          synth.resume = () => {};
          Object.defineProperty(window, 'speechSynthesis', { value: synth });
          window.SpeechSynthesisUtterance = class { constructor(text) { this.text = text; } };
        ''')
        mock = speech.new_page()
        ready(mock)
        # Even with preferAudio off, missing Telugu voice must still use the MP3.
        mock.evaluate(f'{P}.setPreferAudio(false)')
        mock.locator('.gn-play').click()
        mock.wait_for_function(f"{P}.state === 'playing' && {P}.mode === 'audio'")
        mock.locator('.gn-stop').click()
        mock.evaluate('''() => {
          speechSynthesis.voices = [
            {lang:'te-IN',name:'Telugu test voice',voiceURI:'te-test'},
            {lang:'en-IN',name:'English test voice',voiceURI:'en-test'}];
          speechSynthesis.dispatchEvent(new Event('voiceschanged'));
        }''')
        assert mock.locator('.gn-voice-te option').count() == 2
        mock.locator('.gn-settings summary').click()
        mock.locator('.gn-voice-te').select_option('te-test')
        mock.locator('.gn-play').click()
        assert mock.evaluate(f"{P}.mode === 'speech' && __last.lang === 'te-IN' && __last.voice.voiceURI === 'te-test'")
        assert mock.evaluate('__last.text.length <= 160')
        first = mock.evaluate('__last.text')
        mock.locator('.gn-play').click()
        assert mock.evaluate(f"{P}.state === 'paused' && __last.onend === null")
        mock.locator('.gn-play').click()
        assert mock.evaluate('__last.text') == first
        mock.evaluate('__last.onend()')
        assert mock.evaluate('__last.text') != first
        mock.locator('.gn-stop').click()
        assert mock.evaluate('__last.onend === null && __last.onerror === null')
        # No recording and no Telugu device voice produces an actionable error.
        mock.evaluate(f'''() => {{
          const p = {P}; p.setStories(p.stories, {{manifest: {{}}}});
          speechSynthesis.voices = []; speechSynthesis.dispatchEvent(new Event('voiceschanged'));
          p.play();
        }}''')
        assert mock.evaluate(f"{P}.state === 'error' && {P}.message.includes('MP3')")
        # Missing recording should fall through to English speech without pretending Telugu exists.
        mock.evaluate(f'''() => {{
          const p = {P}; p.setLanguage('en'); p.setPreferAudio(true);
          p.setStories(p.stories, {{manifest: {{stories: {{[p.story.id]: {{en: {{file:'missing.mp3'}}}}}}}}, manifestURL: document.baseURI}});
          p.play();
        }}''')
        mock.wait_for_function(f"{P}.mode === 'speech' && {P}.state === 'playing'")
        mock.locator('.gn-stop').click()
        # Component lifecycle must tear down and reconnect cleanly.
        mock.evaluate("window.__el = document.querySelector('gn-voice-player'); __el.remove(); document.querySelector('.player-column').prepend(__el)")
        assert mock.evaluate(f'{P}.stories.length === 5 && !{P}.destroyed')
        print('PASS: async voices, Telugu MP3 fallback, speech chunking/pause/cancellation, missing audio fallback, missing voice error, reconnect')
        browser.close()
finally:
    server.shutdown()
