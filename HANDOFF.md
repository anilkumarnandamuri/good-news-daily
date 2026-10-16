# HANDOFF — good-news

## Updated
2026-10-15 21:55 PDT | agy/gemini-3.8-flash-high | branch `job/GV-2` | last commit 469202d

## Current task / claim
**GV-2** Integrate voice player into Good News UI using the `pairs` field — status **claimed** by agy/gemini-3.8-flash-high on `job/GV-2` (since 2026-10-15 13:58 PDT). Last note: fix pass 469202d resolved 2 prior P2s; fresh Codex review found 2 new P2s (reader.js:133,135); awaiting Anil Next: Codex fix pass for 2 new P2s if Anil approves

## Done this session
- Fixed Codex review [P2] finding (Handle an unavailable voice module before extending its class — reader.js:62-65):
  - In `getVoiceModule()`, safely wrapped dynamic import; if import fails or `VoicePlayer` is missing/not a function, reset `voicePromise = null; voiceModule = null;` and incremented `voiceLoadAttempt` query counter so rejected promises are not permanently cached.
  - In `playVoice()`, verified `typeof VoicePlayer === 'function'` before extending `VoicePlayer`; if unavailable, falls back gracefully to native `speechSynthesis` via `speak(btn, fallbackText, lang)`.
  - Added toggle/stop guard `speaking === btn` so repeated clicks on the Listen button while in speech fallback cleanly cancel and stop playback without re-triggering.
  - Added recovery mechanism without reload: subsequent clicks re-attempt dynamic import with cache-busting, cleanly instantiating `ReaderVoicePlayer` once connectivity is restored.
  - Added Playwright test `test_voice_reader_module_failure_fallback_and_recovery` in `tests/test_voice_reader.py` demonstrating that when the voice module route is aborted, Listen falls back to `speechSynthesis` without throwing, and when the route is restored, a subsequent click activates `ReaderVoicePlayer` and sentence highlighting without reloading.
- Fixed Codex review [P2] finding (Route fixed feed fixtures in the voice browser tests — tests/test_voice_reader.py:275-278):
  - Created standalone fixed fixtures under `tests/fixtures/` (`news.json` and `summaries.json`) containing deterministic stories covering: bilingual sentence pairs (`be4d5ceb60`), bilingual pairs with prebuilt MP3 manifest entries (`beb21be0b4`), legacy decimal preservation (`378259bf26`), and `summary_status = 'summary'` without pairs (`summary-story-no-pairs`).
  - Decoupled all browser tests in `tests/test_voice_reader.py` from mutable routine data by intercepting `data/news.json` and `data/summaries.json` requests with these fixtures, fixing the `test_voice_reader_mp3_playback` timeout caused by feed story pruning.
  - Added `test_voice_reader_summary_status_no_pairs_reads_via_speech` confirming `summary_status = 'summary'` stories render bilingual blocks and read via speech fallback.
- Updated `tests/test_legacy_feed_browser.py` to use system Google Chrome binary when available (`executable_path="/usr/bin/google-chrome"`).
- Appended decision D009 in `DECISIONS.md`.
- Regenerated and verified all 5 screenshots in `artifacts/GV-2/`.
- Updated `tasks/GV-2.md` with status `built`, full test command, review responses, and checkpoint.

## Verified (with evidence)
- Full test command passed: `python3 -m unittest discover -s tests -p 'test_*.py' && node --test tests/*.test.js && node --test voice/tests/*.test.js && python3 -m pytest tests/test_legacy_feed_browser.py tests/test_voice_reader.py -q`
  - 43 unittests passed in 0.16s
  - 15 Node frontend tests passed in 180ms
  - 5 Node voice tests passed in 126ms
  - 13 Playwright browser tests passed in 18.47s (8 voice reader tests + 5 legacy feed browser tests)
- `artifacts/GV-2/` screenshots refreshed and verified:
  - `mobile-390-en-active.png`
  - `mobile-390-te-active.png`
  - `desktop-1280-en-active.png`
  - `desktop-1280-te-active.png`
  - `desktop-mp3-active.png`
- `/workspace/tools/agent-workflow/done-check.sh /workspace/repos/.wt/good-news-voice-integration GV-2`:
  - `PASS  task file updated (Status: built, checkpoint 21 lines)`
  - `PASS  browser test passes`
  - `PASS  new screenshot(s)`
- Routine-owned files verified unmodified: `git diff data/news.json data/summaries.json` is clean.

## Unverified
- Production GitHub Pages deployment (handled by scheduled workflow routines).

## Broken / half-done
- None. All must-fix review findings resolved and automated tests passing cleanly.

## Next 3 steps (smallest first)
1. Codex review on task GV-2.
2. Once review passes, merge `job/GV-2` into base branch `feat/voice-integration`.
3. Proceed to GN-2 / next planned milestones in `PLAN.md`.
2026-10-15 21:38 PDT | codex/gpt-6.1-sol | branch `job/GN-5` | last commit ba412a0

## Current task / claim
**GN-5** Fix mobile text-size regressions from 2026-10-15 merge: default normal ~16px body (was forced 125% root + Large text on by default), one unified working text-size control (A-/A+ with bounds+persistence; Large-text pill removed from the header), compact Today's 5 / hero cards on the first screen at 384px; Playwright assertions. — status **in-review** by codex/gpt-6.1-sol on `job/GN-5` (since 2026-10-15 21:28 PDT). Last note: text size + landing fixes built by codex gpt-6.1-sol; codex review 0 must-fix; all tests pass; NOT pushed Next: Anil approves; merge job/GN-5 into main and push (avoid ~6:30 AM PT routine window)

## Done this session
- Made hero and Today's 5 cards grow with normal-flow text over the existing absolute photo/gradient layers. Minimum heights retain 360px mobile heroes, 300px mobile Today's 5 cards, and 400px wider cards.
- Added a three-line hero headline clamp; retained the two-line hero excerpt clamp.
- Reduced phone reader images to `min(30vh,240px)` below 760px.
- Extended browser tests for 160% scale preset before load in All, Science and Health: body/heading containment and headline clamps. Added the default phone reader summary-top assertion before any scrolling, plus maximum-scale screenshots.
- Appended the fix-pass note to tasks/GN-5.md. No protected paths changed.

## Verified (with evidence)
- `python3 -m unittest discover -s tests -p 'test_*.py'`: 43 passed.
- `node --test tests/*.test.js`: passed.
- `node --test voice/tests/*.test.js`: passed.
- `git diff --check`: passed.

## Unverified
- `python3 -m pytest tests/test_text_size_browser.py -q`: all five cases blocked in server fixture setup by `PermissionError: [Errno 1] Operation not permitted` creating an AF_INET socket, before browser launch.
- Visual layout, exact default card sizes, reader summary position and screenshots remain unverified in this sandbox. No new screenshots generated.

## Broken / half-done
- Fix pass complete; browser acceptance remains pending in a socket-enabled environment.

## Next 3 steps (smallest first)
1. Run `python3 -m pytest tests/test_text_size_browser.py -q` in a socket-enabled environment.
2. Inspect default landing/reader screenshots and `artifacts/GN-5/gn5-max-scale-{all,science,health}-384.png`.
3. Review the uncommitted fix pass; commit only when authorized.

## Blockers / questions for Anil
- Sandbox socket creation blocks browser tests and screenshots. No product clarification needed.

## How to resume
```sh
cd /workspace/repos/.wt/good-news-voice-integration
python3 -m unittest discover -s tests -p 'test_*.py' && node --test tests/*.test.js && node --test voice/tests/*.test.js && python3 -m pytest tests/test_legacy_feed_browser.py tests/test_voice_reader.py -q
/workspace/projects/board.sh status
```
