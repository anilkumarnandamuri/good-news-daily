# GV-1: GV-1 (see PLAN.md and HANDOFF.md): Finish the browser smoke checks for the stand

Status: in-progress
Branch: job/GV-1 (base: docs/agent-handoff-20261015)
Model: agy/claude-sonnet-5-5-medium | Playbook: Feature | Cost: cheap
Created: 2026-10-15 13:45 PDT
Test command:

## Task
GV-1 (see PLAN.md and HANDOFF.md): Finish the browser smoke checks for the standalone Good News voice module. Run tests/browser_smoke.py (Python Playwright; serves the repo on a free port; demo at /demo/), fix any failing check at its root (real MP3 playback, both/radio transitions, mobile layout, dark mode, mock speech fallback, playback rate persistence across source changes). Make the smoke checks save screenshots of the demo at 390px and 1280px in light and dark mode to artifacts/GV-1/ (in addition to or instead of test-results/), and inspect them for layout bugs (overflow, overlapping controls, unreadable Telugu text) and fix what you find. Keep npm test and python3 -m unittest discover -s tests -p "test_*.py" green. Do not touch sample/ source data except to read it. Set the Test command to run the browser smoke checks.

## Acceptance (definition of done, see .cursor/rules/done.mdc)
- [ ] Checkpoint below filled and Status updated
- [ ] Playwright browser test passes via the Test command
- [ ] New screenshot in artifacts/GV-1/
- [ ] Codex review (artifacts/GV-1/review.md) has no [P0]-[P2] items

## Checkpoint
_(agent fills: what changed, files, verification evidence, open items)_

## Log
- 2026-10-15 13:45 PDT run-job started
