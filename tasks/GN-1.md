# GN-1: GN-1 data gap (bug fix; see PLAN.md GN-1 and HANDOFF.md). On this branch (base f

Status: in-progress
Branch: job/GN-1 (base: feat/voice-integration)
Model: agy/gemini-3.8-flash-high | Playbook: Bug fix | Cost: cheap
Created: 2026-10-15 15:30 PDT
Test command:

## Task
GN-1 data gap (bug fix; see PLAN.md GN-1 and HANDOFF.md). On this branch (base feat/voice-integration = laptop 83c9ad5 merged), python3 -m unittest discover -s tests fails 115 checks in tests/test_artifacts.py::test_published_summaries_have_four_to_six_pairs_or_explicit_excerpt because the committed data/news.json (written at 2026-10-15T14:00Z by the main-branch routine, which still runs the OLD summarize v5) has no `summary_status` field. The generator on this branch is already correct: scripts/build.py calls scripts/summarize.run(), which sets summary_status='paired'|'excerpt' on every item, so the next routine run after merge will emit it. Consequence today: reader.js line ~69 (`excerpt=it.summary_status!=="paired"||...`) treats every feed item as an excerpt and hides both summaries and Listen buttons for all 115 stories (live-site regression if merged before the routine refresh).

Investigated facts: only 3/115 items can be re-paired from data/summaries.json via summarize.legacy_pairs (106 raise sentence-count mismatch), so regenerating data offline would wipe 112 summaries: do NOT do that. Do NOT modify data/news.json, data/summaries.json, scripts/build.py, push.js, OneSignalSDKWorker.js, scripts/send_push.py, scripts/digest.py (hash-pinned / routine-owned). Do not commit __pycache__ files.

Smallest correct fix (implement exactly this):
1. Legacy feed adapter in the frontend where the feed (data/news.json) is loaded (app.js, the place DATA items are created): for a FEED item that has no `summary_status` key, derive it like the generator would: 'paired' if both sum_en and sum_te are non-empty strings, else 'excerpt' (and blank sum_en/sum_te in the excerpt case). Apply it only to items from the fetched feed, NOT to saved items from localStorage: the existing node test 'legacy saved summaries use the explicit excerpt fallback' (tests/frontend.test.js) must keep passing unchanged. Keep the change tiny and documented with a one-line comment (transitional until the routine runs summarize v6).
2. tests/test_artifacts.py: make the published-summaries test tolerant of legacy items: if `summary_status` is missing, apply the same derivation and assert consistency (both summaries non-empty, or both empty); keep the strict pairs-vs-cache check only for items that carry summary_status=='paired'; keep assertGreater(complete, 0) counting both. Keep it strict for items that do carry the field.
3. Add a node test in tests/frontend.test.js: a feed item without summary_status but with both summaries renders the summaries (not 'Publisher excerpt').
4. Add a small Python Playwright pytest (tests/test_legacy_feed_browser.py; serve the repo root with python3 -m http.server on a free port from a fixture) that opens a story from the real data/news.json in the reader at 390px and 1280px and asserts the 'In short' EN summary and Listen button are visible (not 'Publisher excerpt'); save screenshots to artifacts/GN-1/ (gn1-reader-390.png, gn1-reader-1280.png).
5. All of these must pass: python3 -m unittest discover -s tests -p 'test_*.py' ; node --test tests/*.test.js ; python3 -m pytest tests/test_legacy_feed_browser.py -q . Test command for the task file: python3 -m pytest tests/test_legacy_feed_browser.py -q && python3 -m unittest discover -s tests -p 'test_*.py' && node --test tests/*.test.js
6. Append a DECISIONS.md entry (legacy feed adapter vs regenerating data vs making the reader trust all legacy items) and update HANDOFF.md.

## Acceptance (definition of done, see .cursor/rules/done.mdc)
- [ ] Checkpoint below filled and Status updated
- [ ] Playwright browser test passes via the Test command
- [ ] New screenshot in artifacts/GN-1/
- [ ] Codex review (artifacts/GN-1/review.md) has no [P0]-[P2] items

## Checkpoint
_(agent fills: what changed, files, verification evidence, open items)_

## Log
- 2026-10-15 15:30 PDT run-job started
