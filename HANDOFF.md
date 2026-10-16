# HANDOFF — good-news

## Updated
2026-10-15 17:48 PDT | agy/gemini-3.8-flash-high | branch `job/GV-2` | last commit 99844db

## Current task / claim
**GV-2** Integrate voice player into Good News UI using the `pairs` field — status **claimed** by agy/gemini-3.8-flash-high on `job/GV-2` (since 2026-10-15 13:58 PDT). Last note: agy/gemini-3.8-flash-high build finished; done-check FAIL (see artifacts/GV-2/done-check.txt) Next: fix done-check failures on job/GV-2

## Done this session
- Implemented protected sentence splitter `splitSentences(text)` in `reader.js` (and exposed on `window.splitSentences`) protecting decimal points between digits (`/(?<=\d)\.(?=\d)/gu`) and common abbreviations/initialisms (`/\b(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|St|vs|etc)\./giu` and `/\b(?:[A-Za-z]\.){2,}|\b[A-Z]\.(?=\s+[A-Z][a-z])/gu`) with private placeholders (`\ue000`) before splitting against `[^.!?।॥…]+[.!?।॥…]*|[.!?।॥…]+` and restoring them after.
- Applied `splitSentences` consistently in both `block()` DOM rendering and `playVoice()` queue creation in `reader.js`, keeping rendered sentence spans and speech chunk boundaries aligned and preventing decimals like `$16.8 billion` (checked-in story `378259bf26`) from corrupting into separate spans or utterances.
- Safely wrapped dynamic voice module import in `getVoiceModule()` in `reader.js` with `try...catch` for environment safety.
- Added comprehensive unit tests in `tests/frontend.test.js` covering `$16.8 billion`, `Dr. Rao met U.S. officials.`, Telugu sentences with `।`, and reader rendering of `$16.8 billion` with `?voice=1`.
- Added Playwright test `test_voice_reader_legacy_decimals_preserved` in `tests/test_voice_reader.py` verifying legacy story `378259bf26` renders `$16.8 billion` intact and speech highlighting advances properly.
- Re-verified full test suite: `python3 -m pytest tests/test_voice_reader.py` (6 passed), `node --test tests/*.test.js` (14 passed), `python3 -m unittest discover -s tests -p 'test_*.py'` (29 passed), `python3 -m pytest tests/test_legacy_feed_browser.py` (3 passed), `node --test voice/tests/*.test.js` (5 passed).
- Refreshed all 5 screenshots in `artifacts/GV-2/`.
- Appended decision D008 to `DECISIONS.md`.
- Updated `tasks/GV-2.md` with status, test command, review responses, and checkpoint.

## Verified (with evidence)
- `python3 -m pytest tests/test_voice_reader.py`: 6 passed in 11.16s (mobile-390, desktop-1280 sentence highlighting, desktop MP3 playback, summary load teardown, sample route verification, legacy decimal preservation).
- `node --test tests/*.test.js`: 14 passed in 230ms (including new tests for `$16.8 billion`, `Dr. Rao met U.S. officials.`, Telugu sentences with `।`, and reader rendering with `?voice=1`).
- `python3 -m unittest discover -s tests -p 'test_*.py'`: 29 passed in 0.10s (including `test_unittest_discovery_succeeds_when_playwright_is_absent`).
- `python3 -m pytest tests/test_legacy_feed_browser.py`: 3 passed in 2.83s.
- `node --test voice/tests/*.test.js`: 5 passed in 180ms.
- Verified fresh screenshots in `artifacts/GV-2/`: `mobile-390-en-active.png`, `mobile-390-te-active.png`, `desktop-1280-en-active.png`, `desktop-1280-te-active.png`, `desktop-mp3-active.png`.

## Unverified
- Live GitHub Pages deployment (deployments are handled by workflow routines).
2026-10-15 20:15 PDT | agy/gemini-3.8-flash-high | branch `job/GN-4` | last commit 81f37fd

## Current task / claim
**GN-4** Summaries fallback: v6 falls back to the live extract-and-translate method when no LLM hook is configured (no excerpt-only regression) — status **done** by agy/gemini-3.8-flash-high on `job/GN-4` (since 2026-10-15 19:56 PDT). Last note: merged+pushed good-news main 81f37fd (v5 fallback in v6; routine sim 116/116)

## Done this session
- Fixed Codex review [P1] finding (Routine regression gate: short new items regress to excerpt-only):
  - Updated `validate_pairs(pairs, min_sentences=MIN_SENTENCES, max_sentences=MAX_SENTENCES)` to accept an optional `min_sentences` parameter while defaulting to 4 (`MIN_SENTENCES`), preserving strict 4–6 sentence pair validation for `llm_pairs()` and `legacy_pairs()`.
  - In `extract_and_translate()`, when 1–3 sentences are extracted and translated, validated the pairs with `validate_pairs(pairs, min_sentences=1)` and marked the item with `summary_status = 'summary'`, while 4–6 sentences are marked `summary_status = 'paired'`.
  - In `run()`, when `status == 'summary'`, stored `generated["en"]`, `generated["te"]`, and `generated["pairs"]` in cache under `summary_status = 'summary'`, enabling instant reuse on subsequent runs without network calls or re-translation.
  - Updated `_tok` in `scripts/summarize.py` to `re.findall(r"[\w\u0C00-\u0C7F]{3,}", text.casefold())` matching the v5 tokenization logic so Telugu sentences with Unicode combining vowel marks are properly recognized and extracted.
  - Added comprehensive offline unit tests in `tests/test_summaries.py` covering: 1-sentence EN fallback -> summary, 2-sentence TE fallback -> summary, 5-sentence fallback -> paired, empty translation -> excerpt, cached summary reuse without translate, and LLM hook 4–6 pair strictness.
  - Appended decision D008 in `DECISIONS.md` and updated `README.md` and `tasks/GN-4.md`.
  - Re-ran Playwright browser tests and regenerated screenshots in `artifacts/GN-4/` (`gn4-summary-390.png` and `gn4-summary-1280.png`).

## Verified (with evidence)
- `python3 -m unittest discover -s tests -p 'test_*.py' && node --test tests/*.test.js && node --test voice/tests/*.test.js && python3 -m pytest tests/test_legacy_feed_browser.py -q` all pass (43 unittest pass, 13 node frontend pass, 5 node voice pass, 5 playwright browser pass).
- `/workspace/tools/agent-workflow/done-check.sh /workspace/repos/.wt/good-news-gn4 GN-4` passes task file, browser test, and screenshot checks.
- Mobile (`artifacts/GN-4/gn4-summary-390.png`) and desktop (`artifacts/GN-4/gn4-summary-1280.png`) screenshots verified.
- `data/news.json`, `data/summaries.json`, `scripts/build.py`, `push.js`, `OneSignalSDKWorker.js`, `scripts/send_push.py`, `scripts/digest.py` verified byte-identical to origin/main baseline.

## Unverified
- None.

## Broken / half-done
- None. All must-fix review findings resolved and automated tests passing cleanly.

## Next 3 steps (smallest first)
1. Codex review on task GV-2.
2. Once review passes, merge `job/GV-2` into base branch `feat/voice-integration`.
3. Proceed to GN-2 / next planned milestones in `PLAN.md`.

## Blockers / questions for Anil
- None.

## How to resume
```sh
cd /workspace/repos/.wt/good-news-voice-integration
python3 -m pytest tests/test_voice_reader.py && node --test tests/*.test.js && python3 -m unittest discover -s tests -p 'test_*.py'
/workspace/projects/board.sh status
```
