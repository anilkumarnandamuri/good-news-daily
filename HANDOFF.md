# HANDOFF — good-news-voice

## Updated
2026-10-15 13:47 PDT | agy/claude-sonnet-5-5-medium | branch `job/GV-1` | last commit 7217958

## Current task / claim
**GV-1** Finish browser smoke checks (tests/browser_smoke.py), inspect mobile/dark screenshots in artifacts/GV-1/, fix findings, commit. — status **in-review** by agy/claude-sonnet-5-5-medium on `job/GV-1` (since 2026-10-15 13:45 PDT). Last note: smoke checks + screenshot matrix built Next: Codex review

## Done this session
- Ran tests/browser_smoke.py: all existing checks passed, no product bugs found.
- Added 390/1280px light/dark screenshot matrix (artifacts/GV-1/ and test-results/) with overflow/visibility assertions, and a playback-rate-persists-across-source-change check.
- Inspected 390-dark and 1280-light screenshots: no overflow, overlap or unreadable Telugu.

## Verified (with evidence)
- `python3 tests/browser_smoke.py` all PASS; `npm test` 4/4; `python3 -m unittest discover -s tests -p 'test_*.py'` 3/3.

## Unverified
- Real iOS/Android lock-screen behaviour (unavailable here).

## Broken / half-done
- `.local-git/` is a stale side history; `.git` is canonical. Can be deleted after Anil confirms.
- python http.server has no byte-range seeking (tests accelerate playback instead).

## Next 3 steps (smallest first)
1. Codex review of GV-1.
2. GV-2: Integrate into good-news (see GN-3) once GV-1 is verified.

## Blockers / questions for Anil
- No GitHub repo; decide whether it merges into good-news-daily or gets its own repo.

## How to resume
```sh
cd /workspace/good-news-voice
python3 -m http.server 8000  # http://127.0.0.1:8000/demo/
python3 tests/browser_smoke.py
/workspace/projects/board.sh status
```
