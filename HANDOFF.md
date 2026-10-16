# HANDOFF — good-news

## Updated
2026-10-15 21:36 PDT | Codex | branch `job/GN-5` | one fix pass, intentionally uncommitted

## Current task / claim
**GN-5** — addressed the P2 review finding and mobile reader image height. Existing claim retained; no board checkpoint or commit under the user's explicit no-commit instruction and workspace limits.

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
cd /workspace/repos/.wt/good-news-gn5
python3 -m pytest tests/test_text_size_browser.py -q
```
