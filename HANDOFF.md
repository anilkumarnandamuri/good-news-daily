# HANDOFF — good-news

## Updated
2026-10-15 16:01 PDT | agy/gemini-3.8-flash-high | branch `job/GN-1` | last commit 571386c

## Current task / claim
**GN-1** Import laptop branch codex/goodnews-20261014 (83c9ad5: paired EN/TE summaries, `pairs` field) onto the box — needs the laptop or a push from it; Anil/Chief of Staff only. — status **in-review** by agy/gemini-3.8-flash-high on `job/GN-1` (since 2026-10-15 15:30 PDT). Last note: Addressed review-1 findings (invalidated summary cache eviction, unittest discovery compatibility) Next: Codex review for GN-1

## Done this session
- Evicted invalidated summary cache entries in `scripts/summarize.py` (`cache.pop(item["id"], None)`) when source or description changes, ensuring corrected facts cannot silently revert to outdated summaries during subsequent rebuilds.
- Fixed `tests/test_legacy_feed_browser.py` to use `pytestmark` skip markers instead of module-level `pytest.skip(...)`, ensuring `python3 -m unittest discover -s tests -v` succeeds when Playwright is absent in partially provisioned environments.
- Added regression tests in `tests/test_summaries.py` verifying cache eviction and non-reversion across rebuilds, and in `tests/test_compatibility.py` verifying unittest discovery passes when Playwright is absent.
- Re-verified Playwright tests and re-captured desktop (1280px) and mobile (390px) screenshots in `artifacts/GN-1/`.
- Appended decision D005 to `DECISIONS.md`.
- Documented root causes and resolutions under `## Review response` and updated `## Checkpoint` in `tasks/GN-1.md`.

## Verified (with evidence)
- `python3 -m pytest tests/test_legacy_feed_browser.py -q && python3 -m unittest discover -s tests -p 'test_*.py' && node --test tests/*.test.js` all pass (3 Playwright tests pass, 29 Python unittest pass, 12 Node tests pass).
- `python3 -m unittest discover -s tests -v` passes (29 tests OK).
- `node --test voice/tests/chunker.test.js` passes (5 tests pass).
- Controlled missing-playwright unittest discovery verified via `tests/test_compatibility.py::test_unittest_discovery_succeeds_when_playwright_is_absent`.
- Cache invalidation and non-reversion verified via `tests/test_summaries.py::test_full_description_change_invalidates_cache` and `test_source_change_invalidates_cache`.
- Fresh screenshots `artifacts/GN-1/gn1-reader-390.png` and `artifacts/GN-1/gn1-reader-1280.png` re-saved and verified.
- Routine-owned and push hash files byte-identical to baseline.

## Unverified
- None for GN-1.

## Broken / half-done
- None.

## Next 3 steps (smallest first)
1. Codex review for GN-1 (`artifacts/GN-1/review.md`).
2. GN-2: Add an automated Playwright smoke test (list, reader EN/TE, saved tab at 390px/1280px) with screenshots in artifacts/GN-2/; no data-file changes.
3. GV-2: Integrate voice player into Good News UI using the `pairs` field behind `?voice=1`.

## Blockers / questions for Anil
- None for GN-1.

## How to resume
```sh
cd /workspace/good-news
python3 -m pytest tests/test_legacy_feed_browser.py -q && python3 -m unittest discover -s tests -p 'test_*.py' && node --test tests/*.test.js
/workspace/projects/board.sh status
```
