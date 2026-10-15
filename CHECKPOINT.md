# Checkpoint

Updated: 2026-10-14 23:00 PT. Deadline: about 23:55 PT.

## Done
- Built responsive bilingual player CSS and the demo with queue, current-story highlight, summaries, and light/dark modes.
- Real sample MP3s exist for all five stories in both languages, plus two intros and two combined radio MP3s (about 2.6 MB total).
- Builder rerun with `--radio` completed with zero errors and cache reuse. Source sample is untouched.
- Added README/API/browser limitations and full copy-in integration/build-workflow instructions.
- 4 Node chunker/schema tests and 3 Python builder/real-manifest tests passed.
- Inspected the desktop Chrome screenshot. Found and fixed MP3 source changes resetting playback speed to 1x.
- Browser test suite added; real playback, both/radio transitions, mobile layout, mock speech fallback are being exercised.
- First milestone committed in a separate local Git directory: `e181290`.

## Next
- Finish browser smoke checks, inspect mobile/dark screenshots, fix any findings.
- Update this checkpoint with final validation and commit docs/tests/fixes.

## How to resume
```sh
cd /workspace/good-news-voice
date '+%Y-%m-%d %H:%M:%S %Z'
git --git-dir=.local-git --work-tree=. status --short
npm test
python3 -m unittest discover -s tests -p 'test_*.py'
python3 tests/browser_smoke.py
python3 -m http.server 8000 --bind 127.0.0.1
# http://127.0.0.1:8000/demo/
```

## Known issues
- `.git` is mounted read-only by the environment. Standard `git add/commit` fails. A copied `.local-git/` holds local commits with the original history; use `git --git-dir=.local-git --work-tree=.`. No remotes were added and nothing was pushed. Original `.git` is untouched.
- Real iOS/Android lock-screen testing is unavailable; MP3 is preferred and device-speech background support remains best effort.
- Basic Python http.server lacks byte-range seeking. Tests accelerate native playback for completion checks instead of seeking; production audio hosting should support ranges.
- Initial headless CLI screenshot succeeded using `--user-data-dir=/tmp/gn-voice-chrome`. Browser test screenshots are ignored under `test-results/`.
