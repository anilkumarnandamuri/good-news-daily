# HANDOFF — good-news

## Updated
2026-10-15 | Codex | branch `job/GN-6` | uncommitted builder work (operator commits)

## Current task / claim
**GN-6** Telugu audio via local Piper — status **built** in `tasks/GN-6.md`; existing claim retained. Implementation complete; browser verification and review pending. No branch changes, commits, board writes, network, publication or audio-repo creation performed.

## Done this session
- Added default-off `scripts/tts_audio.py` build hook after summarization: normalized voice/rate/text hashes, cached MP3 reuse, atomic mono 22.05 kHz/32 kbps encoding, version-1 manifest, seven-day unreferenced retention, shared budget, tool detection and failure isolation.
- Added separate-checkout `scripts/publish_audio.sh` and documented operator setup, hosting, size, retention and licences. Optional `data/audio-config.json` supports configured audio hosts; it is written only by opted-in builds.
- Default Telugu Listen now uses the existing voice module, then device speech, then a friendly inline bilingual status. Default English and the GV-2 preview remain intact. GN-5 typography untouched.
- Added eight fake-only generator tests, four real-reader/real-player Node regressions, and a four-case routed Playwright test. Generated one short real Piper fixture (9526 bytes).
- Filled task checkpoint and appended D012. Routine-owned data files are unchanged.

## Verified (with evidence)
- Exact requested command passed: `python3 -m unittest discover -s tests -p 'test_*.py' && node --test tests/*.test.js && node --test voice/tests/*.test.js` — 51 Python tests, 24 frontend Node cases, 5 voice Node cases.
- `git diff --check` and `bash -n scripts/publish_audio.sh` passed.
- ffprobe: real fixture 2.324898 seconds, mono 22050 Hz, 32000 bps, 9526 bytes.
- `data/news.json` SHA256 `9aa5dacfacd1c4b0fa73b150607b310bd490eb2aabe904608b66daf372b529f5` and `data/summaries.json` SHA256 `760a11a535607d5302363898370a16988ec39aa864dbc956fa3c22eed882a382` are byte-identical to HEAD.
- Evidence: `artifacts/GN-6/verification.txt`.

## Unverified
- `python3 -m pytest tests/test_te_audio_browser.py -q`: four cases blocked during local-server setup by `PermissionError: [Errno 1] Operation not permitted` creating AF_INET sockets, before browser launch. Screenshots not produced.
- Browser regressions across legacy/GV-2/GN-5, actual iPhone/Android playback, external Pages CORS/MIME/range behavior, full real-story synthesis, and publication require operator verification. No live build was run because it requires network and changes routine-owned data.

## Broken / half-done
- No known implementation failures. Browser acceptance checkbox remains open pending socket-enabled execution; task is built, not reviewed/done.

## Next 3 steps (smallest first)
1. Run the full task Test command in a socket-enabled environment; inspect four screenshots in `artifacts/GN-6/`.
2. Review the uncommitted GN-6 implementation and commit when satisfied.
3. Operator creates/configures the separate audio checkout and Pages host; enable routine generation only after Anil approves.

## Blockers / questions for Anil
- Sandbox denies local sockets, blocking browser verification. No product clarification needed.

## How to resume
```sh
cd /workspace/repos/.wt/good-news-gn6
python3 -m unittest discover -s tests -p 'test_*.py' && node --test tests/*.test.js && node --test voice/tests/*.test.js
python3 -m pytest tests/test_legacy_feed_browser.py tests/test_voice_reader.py tests/test_text_size_browser.py tests/test_te_audio_browser.py -q
```
