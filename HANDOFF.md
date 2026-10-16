# HANDOFF — good-news

## Updated
2026-10-15 | Codex | branch `job/GN-6` | uncommitted review fixes (operator commits)

## Current task / claim
**GN-6** Telugu audio via local Piper — built, with P1/P2 review fixes and legacy generation compatibility implemented. Existing claim retained. Browser verification remains pending. User explicitly prohibited network, commits, pushes and branch switches; no board writes performed.

## Done this session
- Reader now presents bilingual Tap to play after autoplay rejection/paused state and calls play() synchronously on the same active audio element on the next tap. Loading/playing show Stop; its tap tears down normally.
- Empty, invalid, failed and timed-out Telugu manifest loads clear the cached promise so later taps retry; successful manifests remain cached.
- Generator accepts legacy stories lacking summary_status when both summaries are non-empty, while preserving explicit excerpt exclusion.
- Added real-reader/real-player Node regressions for thrown/rejected NotAllowedError and manifest recovery; updated paused-state expectations. Added legacy eligibility Python test.
- Expanded GN-6 Playwright coverage to six cases, including rejected-play/resume checks and screenshots at both widths; removed autoplay bypass flag.
- Updated task Checkpoint/Review response and appended D013. No changes to data/news.json or data/summaries.json.

## Verified (with evidence)
- Exact requested command passed: `python3 -m unittest discover -s tests -p 'test_*.py' && node --test tests/*.test.js && node --test voice/tests/*.test.js` (52 Python tests; both Node files pass).
- Direct `node tests/frontend.test.js` and `node voice/tests/chunker.test.js` also passed all 26 frontend and 5 voice cases, including GV-2 voice and GN-5 text scaling regressions.
- `git diff --check` passed. `git diff --quiet HEAD -- data/news.json data/summaries.json` passed: both data files remain byte-identical to HEAD.

## Unverified
- Full browser command attempted: `python3 -m pytest tests/test_legacy_feed_browser.py tests/test_voice_reader.py tests/test_text_size_browser.py tests/test_te_audio_browser.py -q`. All 24 cases failed during server setup with PermissionError creating AF_INET sockets, before browser launch.
- GN-6 screenshots, actual iPhone/Android playback, external host behavior and publication require operator verification.

## Broken / half-done
- No known implementation failures. Browser acceptance remains open because sandbox restrictions prevent execution; new screenshots were not produced.

## Next 3 steps (smallest first)
1. Run the browser command in a socket-enabled environment; inspect GN-6 playing, unavailable, tap-to-play and resumed screenshots.
2. Review uncommitted fixes and commit when satisfied.
3. Operator configures separate audio hosting; enable routine generation only after Anil approves.

## Blockers / questions for Anil
- Sandbox denies local server sockets, blocking Playwright verification. No product clarification needed.

## How to resume
```sh
cd /workspace/repos/.wt/good-news-gn6
python3 -m unittest discover -s tests -p 'test_*.py' && node --test tests/*.test.js && node --test voice/tests/*.test.js
python3 -m pytest tests/test_legacy_feed_browser.py tests/test_voice_reader.py tests/test_text_size_browser.py tests/test_te_audio_browser.py -q
```
