# HANDOFF — good-news

## Updated
2026-10-15 | Codex | branch `job/GN-6` | uncommitted review fixes (operator commits)

## Current task / claim
**GN-6** Telugu audio via local Piper — built, with P1/P2 review fixes and legacy generation compatibility implemented. Existing claim retained. Browser verification remains pending. User explicitly prohibited network, commits, pushes and branch switches; no board writes performed.

## Done this session
- Addressed the latest GN-6 P1: prefetch Telugu config/manifest and voice module when opening a story; resolved taps use cached results without awaiting before speech or MP3 play.
- Pending manifest requests show Stop and can be cancelled. If device speech needs to follow the asynchronous lookup, show bilingual Tap to listen; its next tap invokes speech synchronously without fetching again. Stop/navigation/rerender clear the pending action.
- Failed/empty manifests remain retryable. Existing rejected-MP3 same-element resume remains intact.
- Added four frontend regression cases and updated existing cases for story-open prefetch. GV-2 and GN-5 regression checks pass.
- Updated task Review response/Checkpoint and appended D014. No changes to data/news.json or data/summaries.json. No commits, pushes, branch switches or network.

## Verified (with evidence)
- Exact requested command passed: `python3 -m unittest discover -s tests -p 'test_*.py' && node --test tests/*.test.js && node --test voice/tests/*.test.js` (52 Python tests; both Node files pass).
- Direct `node tests/frontend.test.js` and `node voice/tests/chunker.test.js` also passed all 30 frontend and 5 voice cases, including GV-2 voice and GN-5 text scaling regressions.
- `git diff --check` passed. `git diff --quiet HEAD -- data/news.json data/summaries.json` passed: both data files remain byte-identical to HEAD.

## Unverified
- This session reran `python3 -m pytest tests/test_te_audio_browser.py -q`: six setup errors from sandbox-denied AF_INET sockets, before browser launch; no screenshots produced.
- Earlier full browser command attempted: `python3 -m pytest tests/test_legacy_feed_browser.py tests/test_voice_reader.py tests/test_text_size_browser.py tests/test_te_audio_browser.py -q`. All 24 cases failed during server setup with PermissionError creating AF_INET sockets, before browser launch.
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
