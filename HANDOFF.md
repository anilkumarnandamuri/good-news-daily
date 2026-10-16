# HANDOFF — good-news

## Updated
2026-10-15 21:30 PDT | Codex | branch `job/GN-5` | changes intentionally uncommitted

## Current task / claim
**GN-5** — implementation ready for review; browser verification pending. Existing claim retained on `job/GN-5`. PLAN.md and the external board were not changed: the user explicitly limited work to this directory and prohibited commits.

## Done this session
- Restored normal root/body typography, smaller metadata/pills, 300px mobile Today's 5 cards, 400px wider cards, photo gradients and three-line headlines. Hero height is 360px mobile and 400px wider; image markup, focus styles and touch targets retained.
- Removed the header Large text control and its app/CSS logic.
- Added GN.textScale in sticky.js: early root application, 0.85–1.6 bounds, 0.15 steps, two-decimal rounding, GN.LS persistence and legacy migration/cleanup. Reader A−/A+ use this single setting with disabled/aria-disabled bounds and role=status percentage toasts. Removed --rfs multipliers.
- Updated frontend unit checks; added tests/test_text_size_browser.py for real-feed 384x832 DPR3 touch/mobile and 1280x900 desktop, typography/layout assertions, reader size changes, hash reload persistence, bounds and screenshot capture.
- Updated README.md and appended D009 in DECISIONS.md.

## Verified (with evidence)
- `python3 -m unittest discover -s tests -p 'test_*.py'`: 43 passed.
- `node --test tests/*.test.js`: passed; direct execution confirms 14 frontend tests passed.
- `node --test voice/tests/*.test.js`: passed; direct execution confirms 5 voice tests passed.
- `python3 -m pytest tests/ -q`: 43 passed, 156 subtests passed, 7 browser setup errors from sandbox socket denial.
- Targeted GN-5 browser run: both parameterizations hit the same socket denial before browser launch.
- `git diff --check`: passed. No changes to data/*.json, scripts/, push.js, OneSignalSDKWorker.js, or voice/ source.

## Unverified
- Browser layout, interaction assertions and screenshots: the shared http.server fixture cannot create an AF_INET socket (`PermissionError: [Errno 1] Operation not permitted`). No GN-5 screenshots were generated; no visual acceptance is claimed.

## Broken / half-done
- Implementation complete; browser acceptance remains pending in a socket-enabled environment. No known application failure from available checks.

## Next 3 steps (smallest first)
1. Run `python3 -m pytest tests/test_text_size_browser.py -q` in a socket-enabled environment.
2. Inspect artifacts/GN-5/gn5-landing-384.png, gn5-reader-384.png, gn5-reader-Aplus-384.png and gn5-landing-1280.png, then run the full pytest suite.
3. Review GN-5 and update the external board through the authorized workflow; commit only when explicitly authorized.

## Blockers / questions for Anil
- Sandbox socket creation blocks browser tests and screenshots. No product clarification needed.

## How to resume
```sh
cd /workspace/repos/.wt/good-news-gn5
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/*.test.js
node --test voice/tests/*.test.js
python3 -m pytest tests/ -q
```
