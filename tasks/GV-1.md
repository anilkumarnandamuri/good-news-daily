# GV-1: Finish browser smoke checks for the standalone Good News voice module

Status: built
Branch: job/GV-1 (base: docs/agent-handoff-20261015)
Model: agy/claude-sonnet-5-5-medium | Playbook: Feature | Cost: cheap
Created: 2026-10-15 13:45 PDT
Test command: python3 tests/browser_smoke.py

## Task
GV-1 (see PLAN.md and HANDOFF.md): Finish the browser smoke checks for the standalone Good News voice module. Run tests/browser_smoke.py (Python Playwright; serves the repo on a free port; demo at /demo/), fix any failing check at its root (real MP3 playback, both/radio transitions, mobile layout, dark mode, mock speech fallback, playback rate persistence across source changes). Make the smoke checks save screenshots of the demo at 390px and 1280px in light and dark mode to artifacts/GV-1/ (in addition to or instead of test-results/), and inspect them for layout bugs (overflow, overlapping controls, unreadable Telugu text) and fix what you find. Keep npm test and python3 -m unittest discover -s tests -p "test_*.py" green. Do not touch sample/ source data except to read it. Set the Test command to run the browser smoke checks.

## Acceptance (definition of done, see .cursor/rules/done.mdc)
- [x] Checkpoint below filled and Status updated
- [x] Playwright browser test passes via the Test command
- [x] New screenshot in artifacts/GV-1/
- [ ] Codex review (artifacts/GV-1/review.md) has no [P0]-[P2] items

## Checkpoint
**What changed:** All existing smoke checks already passed (no product bugs found). Added a 390/1280px x light/dark screenshot matrix (saved to artifacts/GV-1/ and test-results/) with assertions for no horizontal overflow, no player element outside the viewport, and visible Telugu story text; added an explicit playback-rate-persists-across-MP3-source-change check.
**Files:** tests/browser_smoke.py, tasks/GV-1.md, HANDOFF.md, DECISIONS.md.
**Verification:** `python3 tests/browser_smoke.py` all PASS; `npm test` 4/4; unittest 3/3. Screenshots 390-dark and 1280-light inspected: no overflow, overlap, or unreadable Telugu.
**Open items:** none; Codex review pending.

## Log
- 2026-10-15 13:45 PDT run-job started
