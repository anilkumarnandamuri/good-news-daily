# GV-2: Integrate the voice player into Good News UI using the pairs field

Status: built
Branch: job/GV-2 (base: feat/voice-integration)
Model: agy/gemini-3.8-flash-high | Playbook: Feature | Cost: cheap
Created: 2026-10-15 13:58 PDT
Test command: python3 -m unittest discover -s tests -p 'test_*.py' && node --test tests/*.test.js && node --test voice/tests/*.test.js && python3 -m pytest tests/test_legacy_feed_browser.py tests/test_voice_reader.py -q

## Task
GV-2 (see PLAN.md and HANDOFF.md): Integrate the voice player (imported under voice/, see voice/INTEGRATION.md and voice/README.md) into the Good News Daily reader (reader.js, index.html, styles.css) using the paired EN/TE summaries in data/summaries.json (the `pairs` field from the laptop branch). The reader Listen button should, when the flag is on (URL ?voice=1 or localStorage gn-voice=1; default OFF so the live site is unchanged), play the story sentence by sentence from `pairs` in the selected language (EN or TE), highlighting the current sentence, using pre-built MP3 when available and Web Speech fallback otherwise. Reuse voice/src code by importing it rather than copy-pasting. Do NOT modify data/news.json, data/summaries.json or scripts/build.py (routine-owned), and do not commit __pycache__ files. Add a Python Playwright pytest (serve the repo with python http.server on a free port, mock speechSynthesis if needed) that opens the reader with ?voice=1 at 390px and 1280px, starts Listen in EN and TE, asserts sentence highlighting advances, and saves screenshots to artifacts/GV-2/. Keep node --test tests/*.test.js green. Note: python3 -m unittest discover -s tests currently fails in tests/test_artifacts.py because routine data predates the new data contract; that is pre-existing and out of scope; do not fix it by editing data.

## Acceptance (definition of done, see .cursor/rules/done.mdc)
- [x] Checkpoint below filled and Status updated
- [x] Playwright browser test passes via the Test command
- [x] New screenshot in artifacts/GV-2/
- [ ] Codex review (artifacts/GV-2/review.md) has no [P0]-[P2] items

## Review response
### [P2] Handle an unavailable voice module before extending its class — reader.js:62-65
Resolved in `reader.js`. In `getVoiceModule()`, dynamic module import is safely guarded. If the module fails to load or import (network error, 404, or missing `VoicePlayer` class), `voicePromise` and `voiceModule` are reset to `null` and a retry query parameter (`voiceLoadAttempt`) is incremented, ensuring failed promises are never permanently cached. In `playVoice()`, `VoicePlayer` is checked for validity (`typeof VoicePlayer !== 'function'`) before extending; if unavailable, Listen falls back to the native `speechSynthesis` playback path (`speak(btn, fallbackText, lang)`). When the user clicks Listen on a subsequent attempt, `getVoiceModule()` re-attempts the import with cache busting, recovering full voice player functionality without requiring a page reload. Added Playwright test `test_voice_reader_module_failure_fallback_and_recovery` in `tests/test_voice_reader.py` demonstrating that when the voice module route is aborted, Listen falls back to `speechSynthesis`, and when the route is subsequently restored, a later click cleanly instantiates `ReaderVoicePlayer` and activates sentence highlighting without reloading.

### [P2] Route fixed feed fixtures in the voice browser tests — tests/test_voice_reader.py:275-278
Resolved in `tests/test_voice_reader.py` and `tests/fixtures/`. Created standalone fixed fixtures under `tests/fixtures/` (`news.json` and `summaries.json`) containing deterministic test data: story with bilingual pairs (`be4d5ceb60`), story with bilingual pairs and prebuilt MP3 manifest entries (`beb21be0b4`), legacy decimal story preserving `$16.8 billion` (`378259bf26`), and a story with `summary_status = 'summary'` without pairs (`summary-story-no-pairs`). Updated every browser test in `tests/test_voice_reader.py` to route `data/news.json` and `data/summaries.json` to these fixed fixtures. This completely decouples all browser tests from mutable routine feed pruning and eliminates the timeout on `test_voice_reader_mp3_playback`. Added `test_voice_reader_summary_status_no_pairs_reads_via_speech` confirming `summary_status = 'summary'` stories render bilingual blocks and read via speech fallback.

### [P1] Reconcile the shipped feed with the new summary contract — reader.js:69-74
Resolved via merge of job/GN-1 (commit 84d099d). As recorded in D003, `app.js` now contains a transitional legacy feed adapter upon fetching `data/news.json` that derives `summary_status = 'paired'` when both `sum_en` and `sum_te` are non-empty strings. `reader.js` line 69 correctly remains strict so that unmigrated saved items in localStorage safely use explicit excerpt fallback. `tests/test_artifacts.py` and `tests/test_legacy_feed_browser.py` confirm feed items render summaries and Listen controls cleanly without altering routine-owned data files.

### [P1] Clear the active player before destroying it — reader.js:29-29
Resolved in `reader.js`. `stopVoice()` now clears `activePlayer = null`, `activeBtn = null`, and `window.__readerPlayer = null` before invoking `player.destroy()`. Event listeners on `ReaderVoicePlayer` (`statechange`, `progress`, `ended`, `timeupdate`) also explicitly guard against `player.destroyed || player !== activePlayer`. When `player.destroy()` synchronously triggers `this.stop()` and emits `statechange` with `state: 'idle'`, any subsequent or re-entrant `stopVoice()` call is a no-op, eliminating recursive teardown.

### [P2] Cancel pending playback when the reader changes — reader.js:48-51
Resolved in `reader.js`. Added `playRequestId` token incremented on every `stop()` and `stopVoice()` invocation. `playVoice()` records `reqId = ++playRequestId` before awaiting `getVoiceModule()` and `getManifest()`. After the awaits resolve, it checks `if (reqId !== playRequestId || R.hidden || !cur || (story && cur.id !== story.id) || !btn.isConnected) return;`. Any stop, story navigation, or reader close immediately invalidates the request token and aborts player instantiation.

### [P2] Stop playback before replacing the reader body — reader.js:102-102
Resolved in `reader.js`. When asynchronous summary loading resolves in `getSummaries().then()`, `stopVoice()` is now invoked before `renderBody(it)`. This tears down any active playback cleanly (destroying the player, clearing `activeSentenceEls`, resetting the button state to "🔊 Listen", and nulling `activePlayer`), preventing detached playback controls and orphaned audio threads when newly loaded bilingual pairs rerender into the reader. Added `test_voice_reader_stops_playback_on_summary_load` in `tests/test_voice_reader.py` to verify active playback stops and resets the Listen button when summaries resolve.

### [P2] Verify the current route before opening a fetched sample story — reader.js:97-97
Resolved in `reader.js`. In the `getSampleNews().then()` callback, the current route is now verified against `location.hash` using `const m = location.hash.match(/^#\/s\/([\w-]+)/); if (found && m && m[1] === id && (!cur || cur.id !== id)) open(id, found);`. If the user navigates away or clears the hash while sample story lookup is in flight, the callback drops the resolution and does not reopen or replace the reader. Added `test_voice_reader_sample_lookup_aborts_if_route_changes` in `tests/test_voice_reader.py` to verify the reader remains hidden when sample news resolves after navigation.

### [P2] Keep browser dependencies optional during unittest discovery — tests/test_voice_reader.py:5-6
Resolved in `tests/test_voice_reader.py`. Replaced unconditional top-level imports of `pytest` and `playwright.sync_api` with `try...except ImportError` guards and `pytestmark = pytest.mark.skip(reason="playwright is not installed")`, mirroring `tests/test_legacy_feed_browser.py`. Updated `tests/test_compatibility.py` to pop `test_voice_reader` during playwright-absent discovery checks. Running `python3 -m unittest discover -s tests -v` now runs cleanly with zero `_FailedTest` errors even when optional browser dependencies are absent.

### [P2] Preserve decimals and abbreviations in fallback sentence splitting — reader.js:65-65
Resolved in `reader.js`. Added a unified protected sentence splitter `splitSentences(text)` that replaces decimal points between digits (`/(?<=\d)\.(?=\d)/gu`) and common abbreviations like Dr., Mr., Mrs., Ms., St., U.S., e.g., i.e., vs. (`/\b(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|St|vs|etc)\./giu` and `/\b(?:[A-Za-z]\.){2,}|\b[A-Z]\.(?=\s+[A-Z][a-z])/gu`) with private placeholders (`\ue000`) before splitting against `[^.!?।॥…]+[.!?।॥…]*|[.!?।॥…]+` and restores them after. Used `splitSentences` in both `block()` DOM rendering and `playVoice()` queue creation so that rendered spans and spoken utterances stay perfectly aligned and decimal numbers (such as `$16.8 billion` in checked-in story `378259bf26`) are never split into `$16. 8 billion`. Added comprehensive unit tests in `tests/frontend.test.js` verifying `$16.8 billion`, `Dr. Rao met U.S. officials.`, Telugu sentences with `।`, and reader DOM rendering. Also added Playwright test `test_voice_reader_legacy_decimals_preserved` in `tests/test_voice_reader.py`.

### Locator.click timeout in test_voice_reader.py::test_voice_reader_mp3_playback
Resolved in `styles.css` and `reader.js`. The `.r-listen.on` pulse animation used `@keyframes pulse { 50% { transform: scale(1.03); } }` which infinitely mutated the button's layout bounding box across animation frames, failing Playwright's stability checks during active MP3 playback. Replaced with `@keyframes pulse-listen { 50% { opacity: 0.85; } }` which preserves visual pulsing without geometry thrashing. In addition, `highlightSentence(idx)` now tracks `currentHighlightIdx` and deduplicates calls, avoiding continuous scroll calls on every `timeupdate` tick.

## Checkpoint
- **What changed**:
  - `reader.js`: Safely handled unavailable voice module by verifying `VoicePlayer` before class extension; added fallback to native `speechSynthesis` (`speak()`); prevented caching of rejected load promises by resetting `voicePromise = null` with cache-busting `voiceLoadAttempt` counter to allow retry and recovery without reload; added toggle/stop guard for speech synthesis fallback.
  - `tests/fixtures/`: Created standalone `tests/fixtures/news.json` and `tests/fixtures/summaries.json` with controlled fixtures for paired stories (`be4d5ceb60`), MP3 playback stories (`beb21be0b4`), legacy decimal stories (`378259bf26`), and summary status stories (`summary-story-no-pairs`).
  - `tests/test_voice_reader.py`: Routed `data/news.json` and `data/summaries.json` across all browser tests to fixed fixtures, eliminating reliance on mutable routine feed data and fixing the `test_voice_reader_mp3_playback` timeout; added `test_voice_reader_module_failure_fallback_and_recovery` testing speech fallback under module failure and recovery without reload; added `test_voice_reader_summary_status_no_pairs_reads_via_speech` testing speech playback on stories with `summary_status = 'summary'` (no pairs).
  - `tests/test_legacy_feed_browser.py`: Configured Chromium launch with system Google Chrome binary when available.
  - `DECISIONS.md`: Appended decision D009.
  - `tasks/GV-2.md` & `HANDOFF.md`: Updated review responses, checkpoints, test commands, and handoff documentation.
- **Files modified**:
  - `reader.js`
  - `tests/fixtures/news.json` (new)
  - `tests/fixtures/summaries.json` (new)
  - `tests/test_voice_reader.py`
  - `tests/test_legacy_feed_browser.py`
  - `DECISIONS.md`
  - `tasks/GV-2.md`
  - `HANDOFF.md`
- **Verification evidence**:
  - Full test command passed: `python3 -m unittest discover -s tests -p 'test_*.py' && node --test tests/*.test.js && node --test voice/tests/*.test.js && python3 -m pytest tests/test_legacy_feed_browser.py tests/test_voice_reader.py -q` (43 unittests passed, 15 node frontend tests passed, 5 node voice tests passed, 13 playwright browser tests passed).
  - All 5 screenshots in `artifacts/GV-2/` re-generated and verified (`mobile-390-en-active.png`, `mobile-390-te-active.png`, `desktop-1280-en-active.png`, `desktop-1280-te-active.png`, `desktop-mp3-active.png`).
  - `data/news.json` and `data/summaries.json` confirmed unmodified.
- **Open items**: None. All must-fix findings resolved and verified.

## Log
- 2026-10-15 13:58 PDT run-job started
- 2026-10-15 14:35 PDT Codex review: 3 must-fix item(s); running one fix pass
- 2026-10-15 14:47 PDT Codex review: 3 must-fix item(s) open
- 2026-10-15 16:14 PDT run-job resumed
- 2026-10-15 16:14 PDT Codex review: 3 must-fix item(s); running one fix pass
- 2026-10-15 16:15 PDT run-job resumed
- 2026-10-15 16:15 PDT Codex review: 3 must-fix item(s); running one fix pass
- 2026-10-15 16:24 PDT All must-fix findings resolved, tests passing, screenshots refreshed
- 2026-10-15 16:27 PDT Codex review: 3 must-fix item(s) open
- 2026-10-15 16:29 PDT run-job resumed
- 2026-10-15 16:29 PDT Codex review: 3 must-fix item(s); running one fix pass
- 2026-10-15 16:38 PDT All 3 new Codex review P2 findings resolved, automated tests passing cleanly with new assertions, screenshots refreshed
- 2026-10-15 16:41 PDT Codex review: 3 must-fix item(s) open
- 2026-10-15 17:30 PDT run-job resumed
- 2026-10-15 17:30 PDT Codex review: 3 must-fix item(s); running one fix pass
- 2026-10-15 17:35 PDT Codex review: 1 must-fix item(s) open
- 2026-10-15 17:37 PDT run-job resumed
- 2026-10-15 17:37 PDT Codex review: 1 must-fix item(s); running one fix pass
- 2026-10-15 17:45 PDT [P2] decimal and abbreviation splitting resolved; 14 node tests + 6 browser tests passing; screenshots updated
- 2026-10-15 17:48 PDT Codex review: 2 must-fix item(s) open
- 2026-10-15 20:55 PDT run-job resumed
- 2026-10-15 20:55 PDT Codex review: 2 must-fix item(s); running one fix pass
- 2026-10-15 21:05 PDT All must-fix findings resolved: voice module failure fallback & recovery, fixed feed fixtures routing, 13 browser tests + 20 node tests + 43 unittests passing

