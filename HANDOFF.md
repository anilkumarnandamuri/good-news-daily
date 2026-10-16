# HANDOFF — good-news

## Updated
2026-10-15 20:08 PDT | agy/gemini-3.8-flash-high | branch `job/GN-4` | last commit ab32f51

## Current task / claim
**GN-4** Summaries fallback: v6 falls back to the live extract-and-translate method when no LLM hook is configured (no excerpt-only regression) — status **in-review** by agy/gemini-3.8-flash-high on `job/GN-4` (since 2026-10-15 19:56 PDT). Last note: agy/gemini-3.8-flash-high build + Codex review passed done-check Next: Chief of Staff review/merge of job/GN-4

## Done this session
- Fixed Codex review [P1] finding (Routine regression gate: short new items regress to excerpt-only):
  - Updated `validate_pairs(pairs, min_sentences=MIN_SENTENCES, max_sentences=MAX_SENTENCES)` to accept an optional `min_sentences` parameter while defaulting to 4 (`MIN_SENTENCES`), preserving strict 4–6 sentence pair validation for `llm_pairs()` and `legacy_pairs()`.
  - In `extract_and_translate()`, when 1–3 sentences are extracted and translated, validated the pairs with `validate_pairs(pairs, min_sentences=1)` and marked the item with `summary_status = 'summary'`, while 4–6 sentences are marked `summary_status = 'paired'`.
  - In `run()`, when `status == 'summary'`, stored `generated["en"]`, `generated["te"]`, and `generated["pairs"]` in cache under `summary_status = 'summary'`, enabling instant reuse on subsequent runs without network calls or re-translation.
  - Updated `_tok` in `scripts/summarize.py` to `re.findall(r"[\w\u0C00-\u0C7F]{3,}", text.casefold())` matching the v5 tokenization logic so Telugu sentences with Unicode combining vowel marks are properly recognized and extracted.
  - Added comprehensive offline unit tests in `tests/test_summaries.py` covering: 1-sentence EN fallback -> summary, 2-sentence TE fallback -> summary, 5-sentence fallback -> paired, empty translation -> excerpt, cached summary reuse without translate, and LLM hook 4–6 pair strictness.
  - Appended decision D008 in `DECISIONS.md` and updated `README.md` and `tasks/GN-4.md`.
  - Re-ran Playwright browser tests and regenerated screenshots in `artifacts/GN-4/` (`gn4-summary-390.png` and `gn4-summary-1280.png`).

## Verified (with evidence)
- `python3 -m unittest discover -s tests -p 'test_*.py' && node --test tests/*.test.js && node --test voice/tests/*.test.js && python3 -m pytest tests/test_legacy_feed_browser.py -q` all pass (43 unittest pass, 13 node frontend pass, 5 node voice pass, 5 playwright browser pass).
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
