# GN-1: GN-1 data gap (bug fix; see PLAN.md GN-1 and HANDOFF.md). On this branch (base f

Status: built
Branch: job/GN-1 (base: feat/voice-integration)
Model: agy/gemini-3.8-flash-high | Playbook: Bug fix | Cost: cheap
Created: 2026-10-15 15:30 PDT
Test command: python3 -m pytest tests/test_legacy_feed_browser.py -q && python3 -m unittest discover -s tests -p 'test_*.py' && node --test tests/*.test.js

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
- [x] Checkpoint below filled and Status updated
- [x] Playwright browser test passes via the Test command
- [x] New screenshot in artifacts/GN-1/
- [ ] Codex review (artifacts/GN-1/review.md) has no [P0]-[P2] items

## Review response
- **[P2] Remove invalidated summaries from the cache — scripts/summarize.py:176-177**:
  - Root cause: When `summarize.run()` detected a modified description or source for an item whose facts had changed, it raised `ValueError` and set `summary_status = 'excerpt'`, but left the invalidated entry in `cache`. Because the run subsequently popped `desc` from the published item, running the standalone summarizer afterward encountered no `desc`, bypassed the description comparison, and restored the outdated summary from the lingering cache entry.
  - Fix: Evicted rejected entries from the cache (`cache.pop(item["id"], None)`) in `scripts/summarize.py` both when pair validation/fingerprint checks raise and when `pairs is None` before writing cache. Added automated regression test coverage in `tests/test_summaries.py` asserting that invalidation purges the cache entry and that subsequent rebuilds without `desc` cannot revert to `paired`.
- **[P2] Skip missing browser dependencies compatibly with unittest — tests/test_legacy_feed_browser.py:58-59**:
  - Root cause: Calling `pytest.skip(...)` at the module level when `playwright` was missing raised `_pytest.outcomes.Skipped`. Since `Skipped` does not inherit from `unittest.SkipTest`, `python3 -m unittest discover -s tests -v` treated the module-level skip exception as a loader error (`_FailedTest`) in environments with `pytest` installed but `playwright` absent.
  - Fix: Replaced module-level `pytest.skip(...)` with `pytestmark = pytest.mark.skip(reason="playwright is not installed")` when `sync_playwright is None`. This allows `python3 -m unittest discover` to import the module cleanly without error while properly skipping the tests when running under `pytest`. Added regression test `test_unittest_discovery_succeeds_when_playwright_is_absent` in `tests/test_compatibility.py`.
- **[P2] Preserve decimal numbers when chunking speech — voice/src/gn-voice.js:21-21**:
  - Root cause: `chunkText` was splitting sentences on punctuation regex `[.!?।॥…]` without shielding decimal points (e.g. `$3.5 million`) or abbreviations/titles (e.g. `Dr.`, `Mr.`, `U.S.`), causing numbers to be split into separate speech utterances.
  - Fix: Protected decimal points (`(?<=\d)\.(?=\d)`), common abbreviations/honorifics, and multi-letter/single-letter initials before sentence splitting, then restored periods on the resulting chunks. Added unit test in `voice/tests/chunker.test.js`.
- **[P2] Declare or isolate browser-test dependencies — tests/test_legacy_feed_browser.py:8-9**:
  - Root cause: Top-level unconditional imports of `pytest` and `playwright.sync_api` broke standard `python3 -m unittest discover -s tests -v` on fresh installs where only `requirements.txt` was installed.
  - Fix: Created `requirements-test.txt` declaring `pytest>=7.0.0` and `playwright>=1.40.0`. In `tests/test_legacy_feed_browser.py`, protected imports with `try...except ImportError` so unittest discovery skips the file cleanly without import failure when optional browser-test dependencies are absent.
- **[P2] Avoid requiring the first refreshed story to have summaries — tests/test_legacy_feed_browser.py:59-61**:
  - Root cause: The browser test inspected `news["items"][0]` from the live `data/news.json`, which could legitimately have `summary_status: 'excerpt'` after feed refreshes or lose legacy characteristics after routine runs summarize v6.
  - Fix: Used a controlled legacy feed fixture intercepted via Playwright network routing (`context.route`). Tested both legacy paired items (verifying "In short" and Listen button) and legacy excerpt items (verifying "Publisher excerpt" fallback and absence of Listen button). Generated fresh screenshots in `artifacts/GN-1/`.
- **[P2] Restore eviction of obsolete summary-cache entries — scripts/summarize.py:206-209**:
  - Root cause: The live-ID plus 7-day retention pruning step had been removed before serialization when refactoring cache saving, causing unpruned cache growth over time.
  - Fix: Restored the live-ID plus 7-day prune before atomic temporary file serialization (`k in live or (now - v['t'] < 7 * 86400)`), and ensured each cached entry records/preserves its `t` timestamp. Added contract test `test_cache_evicts_departed_stories_older_than_seven_days` in `tests/test_summaries.py`.

## Checkpoint
- **What changed**:
  - Evicted invalidated entries from the summary cache in `scripts/summarize.py` (`cache.pop(item["id"], None)`) when source or description changes, preventing outdated summaries from silently reverting on standalone rebuilds.
  - Fixed browser test module `tests/test_legacy_feed_browser.py` to use `pytestmark` skip markers instead of module-level `pytest.skip()`, preventing `ImportError` on `unittest.loader._FailedTest` during `python3 -m unittest discover -s tests -v` when Playwright is absent.
  - Added regression tests in `tests/test_summaries.py` (verifying cache eviction and non-reversion of changed stories) and `tests/test_compatibility.py` (verifying unittest discovery passes when Playwright is uninstalled).
  - Maintained green Playwright tests and re-captured desktop (1280px) and mobile (390px) screenshots in `artifacts/GN-1/`.
  - Added architectural decision D005 in `DECISIONS.md`.
- **Files**:
  - `scripts/summarize.py`
  - `tests/test_legacy_feed_browser.py`
  - `tests/test_summaries.py`
  - `tests/test_compatibility.py`
  - `DECISIONS.md`
  - `HANDOFF.md`
  - `tasks/GN-1.md`
  - `artifacts/GN-1/gn1-reader-390.png`
  - `artifacts/GN-1/gn1-reader-1280.png`
- **Verification evidence**:
  - `python3 -m pytest tests/test_legacy_feed_browser.py -q && python3 -m unittest discover -s tests -p 'test_*.py' && node --test tests/*.test.js` exits 0 (3 passed in pytest, 29 tests in unittest OK, 12 tests in node --test pass).
  - `python3 -m unittest discover -s tests -v` exits 0 (29 tests OK).
  - `node --test voice/tests/chunker.test.js` exits 0 (5 tests pass).
  - Screenshots `gn1-reader-390.png` and `gn1-reader-1280.png` re-saved and verified.
- **Open items**:
  - Awaiting review by Codex / Anil.

## Log
- 2026-10-15 15:30 PDT run-job started
- 2026-10-15 15:34 PDT built by agy/gemini-3.8-flash-high
- 2026-10-15 15:36 PDT Codex review: 4 must-fix item(s); running one fix pass
- 2026-10-15 15:52 PDT all 4 must-fix items addressed and verified by agy/gemini-3.8-flash-high
- 2026-10-15 15:53 PDT Codex review: 2 must-fix item(s) open
- 2026-10-15 15:54 PDT run-job resumed
- 2026-10-15 15:54 PDT Codex review: 2 must-fix item(s); running one fix pass
- 2026-10-15 16:00 PDT addressed both review-1 must-fix items and added regression coverage; agy/gemini-3.8-flash-high
