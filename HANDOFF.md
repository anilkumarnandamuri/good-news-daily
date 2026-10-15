# HANDOFF — good-news

## Updated
2026-10-15 15:35 PDT | agy/gemini-3.8-flash-high | branch `job/GN-1` | last commit 4ed6702

## Current task / claim
**GN-1** Import laptop branch codex/goodnews-20261014 (83c9ad5: paired EN/TE summaries, `pairs` field) onto the box — needs the laptop or a push from it; Anil/Chief of Staff only. — status **in-review** by agy/gemini-3.8-flash-high on `job/GN-1` (since 2026-10-15 15:30 PDT). Last note: Built legacy feed adapter, updated artifact contract test, added tests and screenshots Next: Codex review

## Done this session
- Implemented transitional legacy feed adapter in `app.js` when loading `data/news.json` so stories without `summary_status` have it derived ('paired' when `sum_en` and `sum_te` non-empty, otherwise 'excerpt') without modifying routine-owned data files or affecting saved localStorage stories.
- Updated `tests/test_artifacts.py` (`test_published_summaries_have_four_to_six_pairs_or_explicit_excerpt`) to accept legacy feed items lacking `summary_status` while preserving strict cache/pair checks for items with explicit `summary_status=='paired'`.
- Added unit test in `tests/frontend.test.js` verifying legacy feed items without `summary_status` render bilingual summaries and not "Publisher excerpt".
- Added Playwright browser test in `tests/test_legacy_feed_browser.py` testing legacy stories in the reader at 390px and 1280px viewports, saving screenshots in `artifacts/GN-1/`.
- Appended D003 in `DECISIONS.md`.
- Updated `tasks/GN-1.md` with status `built`, test command, and completed checkpoint.

## Verified (with evidence)
- `python3 -m pytest tests/test_legacy_feed_browser.py -q && python3 -m unittest discover -s tests -p 'test_*.py' && node --test tests/*.test.js` all pass (2 Playwright tests pass, 27 Python unittest pass, 12 Node tests pass).
- Screenshots `artifacts/GN-1/gn1-reader-390.png` and `artifacts/GN-1/gn1-reader-1280.png` captured and verified.
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
