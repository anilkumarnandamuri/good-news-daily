# HANDOFF — good-news

## Updated
2026-10-15 19:56 PDT | agy/gemini-3.8-flash-high | branch `job/GN-4` | last commit e270d51

## Current task / claim
**GN-4** Summaries fallback: v6 falls back to the live extract-and-translate method when no LLM hook is configured (no excerpt-only regression) — status **claimed** by agy/gemini-3.8-flash-high on `job/GN-4` (since 2026-10-15 19:56 PDT). Last note: 2026-10-15 19:56 PDT claimed by agy/gemini-3.8-flash-high

## Done this session
- Ported v5 extract-and-translate method (`_get`, `meta`, `translate`, `extract_and_translate`) into `scripts/summarize.py` v6 as fallback when LLM hook is not enabled or fails.
- Sentence pairs built directly from 1:1 aligned per-sentence translation lists without re-splitting, validated with `validate_pairs`, stored in v6 cache, setting `summary_status='paired'`.
- Preserved existing v5 cache entries whose sentence counts cannot be re-paired by `legacy_pairs` under `summary_status='summary'` without network calls.
- Updated `reader.js` and `app.js` to render `summary_status='summary'` like `paired` (showing both summaries and Listen buttons).
- Updated `tests/test_artifacts.py` to accept `summary_status='summary'` items with both summary strings present.
- Fixed Codex review [P2] finding: enforced remaining time budget in `scripts/summarize.py` fallback by propagating remaining deadline through `meta(url, timeout)` and `translate(text, sl, tl, timeout, deadline)` and checking deadline between requests and endpoints.
- Fixed Codex review [P2] finding: updated `tools/routine_sim.py` routine regression gate to require `n_total > 0` before accepting the all-stories-summarized alternative (`n_sum == n_total`).
- Added comprehensive unit tests in `tests/test_summaries.py` (30 tests: fallback pairs alignment, translation failure retry, v5 cache preservation, hook precedence/fallback, time budget enforcement, and translate deadline skipping) and `tests/test_compatibility.py` (empty feed regression rejection).
- Added Node test in `tests/frontend.test.js` for reader rendering `summary_status='summary'` items.
- Added Playwright browser tests in `tests/test_legacy_feed_browser.py` for `summary_status='summary'` and captured screenshots in `artifacts/GN-4/`.
- Updated `README.md` and appended decisions D006 and D007 to `DECISIONS.md`.
- Filled checkpoint and updated `tasks/GN-4.md` to `Status: built` with `## Review response` section.

## Verified (with evidence)
- `python3 -m unittest discover -s tests -p 'test_*.py' && node --test tests/*.test.js && node --test voice/tests/*.test.js && python3 -m pytest tests/test_legacy_feed_browser.py -q` all pass (37 unittest pass, 13 node frontend pass, 5 node voice pass, 5 playwright browser pass).
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
