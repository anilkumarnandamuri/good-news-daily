# HANDOFF — good-news

## Updated
2026-10-15 19:36 PDT | agy/gemini-3.8-flash-high | branch `job/GN-4` | last commit f53816f

## Current task / claim
**GN-4** Summaries fallback: v6 falls back to the live extract-and-translate method when no LLM hook is configured (no excerpt-only regression) — status **in-review** by agy/gemini-3.8-flash-high on `job/GN-4` (since 2026-10-15 19:26 PDT). Last note: built extract-and-translate fallback and summary status support Next: Codex review

## Done this session
- Ported v5 extract-and-translate method (`_get`, `meta`, `translate`, `extract_and_translate`) into `scripts/summarize.py` v6 as fallback when LLM hook is not enabled or fails.
- Sentence pairs built directly from 1:1 aligned per-sentence translation lists without re-splitting, validated with `validate_pairs`, stored in v6 cache, setting `summary_status='paired'`.
- Preserved existing v5 cache entries whose sentence counts cannot be re-paired by `legacy_pairs` under `summary_status='summary'` without network calls.
- Updated `reader.js` and `app.js` to render `summary_status='summary'` like `paired` (showing both summaries and Listen buttons).
- Updated `tests/test_artifacts.py` to accept `summary_status='summary'` items with both summary strings present.
- Added comprehensive unit tests in `tests/test_summaries.py` for no-LLM fallback, translation failure fallback/retry, v5 cache preservation as summary, hook precedence, and hook failure fallback.
- Added Node test in `tests/frontend.test.js` for reader rendering `summary_status='summary'` items.
- Added Playwright browser tests in `tests/test_legacy_feed_browser.py` for `summary_status='summary'` and captured screenshots in `artifacts/GN-4/`.
- Updated `README.md` and appended decision D006 to `DECISIONS.md`.
- Filled checkpoint and updated `tasks/GN-4.md` to `Status: built`.

## Verified (with evidence)
- `python3 -m unittest discover -s tests -p 'test_*.py' && node --test tests/*.test.js && node --test voice/tests/*.test.js && python3 -m pytest tests/test_legacy_feed_browser.py -q` all pass (34 unittest pass, 13 node frontend pass, 5 node voice pass, 5 playwright browser pass).
- `/workspace/tools/agent-workflow/done-check.sh /workspace/repos/.wt/good-news-gn4 GN-4` passes task file, browser test, and screenshot checks.
- Mobile (`artifacts/GN-4/gn4-summary-390.png`) and desktop (`artifacts/GN-4/gn4-summary-1280.png`) screenshots verified.
- `data/news.json`, `data/summaries.json`, `scripts/build.py`, `push.js`, `OneSignalSDKWorker.js`, `scripts/send_push.py`, `scripts/digest.py` verified byte-identical to origin/main baseline.

## Unverified
- None.

## Broken / half-done
- None.

## Next 3 steps (smallest first)
1. Codex review for GN-4 (`artifacts/GN-4/review.md`).
2. GN-2: Add an automated Playwright smoke test (list, reader EN/TE, saved tab at 390px/1280px) with screenshots in artifacts/GN-2/; no data-file changes.
3. GV-2: Integrate voice player into Good News UI using the `pairs` field behind `?voice=1`.

## Blockers / questions for Anil
- None.

## How to resume
```sh
cd /workspace/good-news
python3 -m unittest discover -s tests -p 'test_*.py' && node --test tests/*.test.js && node --test voice/tests/*.test.js && python3 -m pytest tests/test_legacy_feed_browser.py -q
/workspace/projects/board.sh status
```
