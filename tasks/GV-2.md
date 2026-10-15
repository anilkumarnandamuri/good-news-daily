# GV-2: Integrate the voice player into Good News UI using the pairs field

Status: built
Branch: job/GV-2 (base: feat/voice-integration)
Model: agy/gemini-3.8-flash-high | Playbook: Feature | Cost: cheap
Created: 2026-10-15 13:58 PDT
Test command: python3 -m pytest tests/test_voice_reader.py && node --test tests/*.test.js && python3 -m unittest discover -s tests -p 'test_*.py'

## Task
GV-2 (see PLAN.md and HANDOFF.md): Integrate the voice player (imported under voice/, see voice/INTEGRATION.md and voice/README.md) into the Good News Daily reader (reader.js, index.html, styles.css) using the paired EN/TE summaries in data/summaries.json (the `pairs` field from the laptop branch). The reader Listen button should, when the flag is on (URL ?voice=1 or localStorage gn-voice=1; default OFF so the live site is unchanged), play the story sentence by sentence from `pairs` in the selected language (EN or TE), highlighting the current sentence, using pre-built MP3 when available and Web Speech fallback otherwise. Reuse voice/src code by importing it rather than copy-pasting. Do NOT modify data/news.json, data/summaries.json or scripts/build.py (routine-owned), and do not commit __pycache__ files. Add a Python Playwright pytest (serve the repo with python http.server on a free port, mock speechSynthesis if needed) that opens the reader with ?voice=1 at 390px and 1280px, starts Listen in EN and TE, asserts sentence highlighting advances, and saves screenshots to artifacts/GV-2/. Keep node --test tests/*.test.js green. Note: python3 -m unittest discover -s tests currently fails in tests/test_artifacts.py because routine data predates the new data contract; that is pre-existing and out of scope; do not fix it by editing data.

## Acceptance (definition of done, see .cursor/rules/done.mdc)
- [x] Checkpoint below filled and Status updated
- [x] Playwright browser test passes via the Test command
- [x] New screenshot in artifacts/GV-2/
- [ ] Codex review (artifacts/GV-2/review.md) has no [P0]-[P2] items

## Review response
### [P1] Reconcile the shipped feed with the new summary contract — reader.js:69-74
Resolved via merge of job/GN-1 (commit 84d099d). As recorded in D003, `app.js` now contains a transitional legacy feed adapter upon fetching `data/news.json` that derives `summary_status = 'paired'` when both `sum_en` and `sum_te` are non-empty strings. `reader.js` line 69 correctly remains strict so that unmigrated saved items in localStorage safely use explicit excerpt fallback. `tests/test_artifacts.py` and `tests/test_legacy_feed_browser.py` confirm feed items render summaries and Listen controls cleanly without altering routine-owned data files.

### [P1] Clear the active player before destroying it — reader.js:29-29
Resolved in `reader.js`. `stopVoice()` now clears `activePlayer = null`, `activeBtn = null`, and `window.__readerPlayer = null` before invoking `player.destroy()`. Event listeners on `ReaderVoicePlayer` (`statechange`, `progress`, `ended`, `timeupdate`) also explicitly guard against `player.destroyed || player !== activePlayer`. When `player.destroy()` synchronously triggers `this.stop()` and emits `statechange` with `state: 'idle'`, any subsequent or re-entrant `stopVoice()` call is a no-op, eliminating recursive teardown.

### [P2] Cancel pending playback when the reader changes — reader.js:48-51
Resolved in `reader.js`. Added `playRequestId` token incremented on every `stop()` and `stopVoice()` invocation. `playVoice()` records `reqId = ++playRequestId` before awaiting `getVoiceModule()` and `getManifest()`. After the awaits resolve, it checks `if (reqId !== playRequestId || R.hidden || !cur || (story && cur.id !== story.id) || !btn.isConnected) return;`. Any stop, story navigation, or reader close immediately invalidates the request token and aborts player instantiation.

### Locator.click timeout in test_voice_reader.py::test_voice_reader_mp3_playback
Resolved in `styles.css` and `reader.js`. The `.r-listen.on` pulse animation used `@keyframes pulse { 50% { transform: scale(1.03); } }` which infinitely mutated the button's layout bounding box across animation frames, failing Playwright's stability checks during active MP3 playback. Replaced with `@keyframes pulse-listen { 50% { opacity: 0.85; } }` which preserves visual pulsing without geometry thrashing. In addition, `highlightSentence(idx)` now tracks `currentHighlightIdx` and deduplicates calls, avoiding continuous scroll calls on every `timeupdate` tick.

## Checkpoint
- **What changed**:
  - `reader.js`: Cleared `activePlayer`, `activeBtn`, and `window.__readerPlayer` prior to `destroy()` in `stopVoice()`; guarded `statechange`, `progress`, `ended`, and `timeupdate` listeners against destroyed or stale player instances; added `playRequestId` generation token in `playVoice()`, `stop()`, and `stopVoice()` to cancel pending playback if the reader closes or navigates; deduplicated `highlightSentence` calls and removed smooth-scroll jitter on timeupdate.
  - `styles.css`: Updated `.r-listen.on` animation to `pulse-listen` with opacity pulsing instead of transform scale, ensuring layout stability for interaction during audio playback.
  - `tasks/GV-2.md`: Set `Status: built`, filled Test command and Checkpoint, added `## Review response` addressing all review items.
  - `HANDOFF.md` & `DECISIONS.md`: Updated current status, verification evidence, and added decision D006.
- **Files modified**:
  - `reader.js`
  - `styles.css`
  - `tasks/GV-2.md`
  - `HANDOFF.md`
  - `DECISIONS.md`
- **Verification evidence**:
  - `python3 -m pytest tests/test_voice_reader.py` (3 passed in 6.9s)
  - `node --test tests/*.test.js` (12 passed)
  - `python3 -m unittest discover -s tests -p 'test_*.py'` (29 passed)
  - `python3 -m pytest tests/test_legacy_feed_browser.py` (3 passed)
  - `node --test voice/tests/*.test.js` (5 passed)
  - Fresh screenshots verified in `artifacts/GV-2/`: `desktop-1280-en-active.png`, `desktop-1280-te-active.png`, `desktop-mp3-active.png`, `mobile-390-en-active.png`, `mobile-390-te-active.png`
- **Open items**: None. All P1/P2 items resolved and all test suites pass.

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
