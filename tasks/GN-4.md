# GN-4: GN-4 (see PLAN.md GN-4; Anil chose this 2026-10-15 19:23 PT). Problem: scripts/s

Status: built
Branch: job/GN-4 (base: merge/gn-main-20261015)
Model: agy/gemini-3.8-flash-high | Playbook: Bug fix | Cost: cheap
Created: 2026-10-15 19:26 PDT
Test command: python3 -m unittest discover -s tests -p 'test_*.py' && node --test tests/*.test.js && node --test voice/tests/*.test.js && python3 -m pytest tests/test_legacy_feed_browser.py -q

## Task
GN-4 (see PLAN.md GN-4; Anil chose this 2026-10-15 19:23 PT). Problem: scripts/summarize.py v6 (from the laptop branch) only produces EN/TE summaries through the opt-in LLM hook (GOOD_NEWS_LLM=1 + GOOD_NEWS_LLM_COMMAND). Without it, the twice-daily routine (`python scripts/build.py`, which calls summarize.run) marks ~107/115 stories 'excerpt' (verified by tools/routine_sim.py: 8/115 on this branch vs 115/115 with origin/main's v5 code). The old v5 summarizer (`git show origin/main:scripts/summarize.py`) does extract-and-translate with no config: one canonical source-language summary (<=6 sentences/~120 words) extracted from the feed description + article og/meta descriptions (never the article body), then sentence-by-sentence machine translation (free Google translate web endpoint, MyMemory fallback), strictly 1:1, cached in data/summaries.json; network calls with short timeouts, retried next run.

Implement (smallest correct change):
1. In scripts/summarize.py v6, when the LLM hook is NOT enabled (or it fails), fall back to the v5 extract-and-translate method, ported from origin/main's summarize.py (reuse its functions: meta(), translate(), the extract/clean logic; keep the BUDGET_S time budget and per-call timeouts). Because v5 translates sentence by sentence, build `pairs` directly from the aligned per-sentence lists (do NOT re-split joined strings), validate with validate_pairs, store a v6 cache entry, set summary_status='paired'.
2. Existing v5 cache entries (the routine's local data/summaries.json has ~200 v5 entries {en, te, ...}) whose joined strings cannot be re-paired by legacy_pairs (sentence-count mismatch) must NOT be dropped to excerpt: keep their en/te as the item's sum_en/sum_te with a new summary_status 'summary' (both summaries present, no sentence pairs), OR re-pair them via the v5 sentence splitter if that is exact. Prefer no network for already-cached stories. Update reader.js/app.js so status 'summary' renders like paired (shows both summaries + Listen; voice falls back to splitting text), and tests/test_artifacts.py to accept 'summary' items (both strings non-empty). Saved legacy items without any status keep the existing excerpt fallback (tests/frontend.test.js).
3. LLM hook behavior unchanged when configured (hook first; on hook failure use the fallback).
4. Do NOT change data/news.json or data/summaries.json in git (they must stay byte-identical to origin/main: the routine runs `git pull --ff-only` with an uncommitted local cache). Do not re-add scripts/__pycache__ to git. scripts/build.py stays byte-identical (hash-pinned).
5. Unit tests (tests/test_summaries.py) with NO network: monkeypatch summarize.meta / summarize.translate (or the HTTP helper) to cover: no-LLM fallback produces paired pairs aligned 1:1; translation failure -> excerpt and retried next run; v5 cache entry kept as 'summary' without network; hook configured -> hook used; hook failure -> fallback. Node test for reader rendering 'summary' status.
6. You have no network: do not run tools/routine_sim.py (the operator runs it after you; it must report >= origin/main's summary count). Update README (summaries section: fallback + hook) and DECISIONS.md, HANDOFF.md.
Test command for the task file: python3 -m unittest discover -s tests -p 'test_*.py' && node --test tests/*.test.js && node --test voice/tests/*.test.js && python3 -m pytest tests/test_legacy_feed_browser.py -q

## Acceptance (definition of done, see .cursor/rules/done.mdc)
- [x] Checkpoint below filled and Status updated
- [x] Playwright browser test passes via the Test command
- [x] New screenshot in artifacts/GN-4/
- [ ] Codex review (artifacts/GN-4/review.md) has no [P0]-[P2] items

## Checkpoint
- **What changed**:
  1. Ported v5 extract-and-translate method into `scripts/summarize.py` (`_get`, `meta`, `translate`, `extract_and_translate`), which runs when `GOOD_NEWS_LLM` is not enabled or when the LLM hook fails. Builds 1:1 aligned sentence pairs directly from translation lists without re-splitting, validates with `validate_pairs`, stores v6 cache entries, and marks items `summary_status='paired'`.
  2. Preserved legacy v5 cache entries whose sentence counts cannot be re-paired by `legacy_pairs` as `summary_status='summary'` with both `sum_en` and `sum_te` preserved and zero network requests.
  3. Updated `reader.js` and `app.js` to render `summary_status='summary'` with full bilingual summaries and Listen buttons like `paired`.
  4. Updated `tests/test_artifacts.py` to accept `summary_status='summary'` items (asserting both summary strings non-empty).
  5. Added unit tests in `tests/test_summaries.py` covering: no-LLM fallback producing 1:1 aligned pairs, translation failure falling back to excerpt and retrying on next run, v5 cache entries kept as `summary` without network, hook configured taking precedence without calling fallback, and hook failure falling back to extract-and-translate.
  6. Added Node test in `tests/frontend.test.js` verifying reader renders `summary` status stories like `paired`.
  7. Added Playwright browser tests in `tests/test_legacy_feed_browser.py` asserting reader display of `summary_status='summary'` items and generated screenshots at mobile (390px) and desktop (1280px) in `artifacts/GN-4/`.
  8. Updated `README.md` and appended decision D006 in `DECISIONS.md`.
- **Files modified**:
  - `scripts/summarize.py`
  - `reader.js`
  - `app.js`
  - `tests/test_artifacts.py`
  - `tests/test_summaries.py`
  - `tests/frontend.test.js`
  - `tests/test_legacy_feed_browser.py`
  - `README.md`
  - `DECISIONS.md`
  - `tasks/GN-4.md`
- **Verification evidence**:
  - `python3 -m unittest discover -s tests -p 'test_*.py'` (34 tests passed)
  - `node --test tests/*.test.js` (13 tests passed)
  - `node --test voice/tests/*.test.js` (5 tests passed)
  - `python3 -m pytest tests/test_legacy_feed_browser.py -q` (5 passed)
  - Full test command passed in 4.40s.
  - Screenshots generated: `artifacts/GN-4/gn4-summary-390.png` and `artifacts/GN-4/gn4-summary-1280.png`.
  - Byte-identical contract verified: `data/news.json`, `data/summaries.json`, `scripts/build.py`, `scripts/send_push.py`, `scripts/digest.py`, `push.js`, `OneSignalSDKWorker.js` completely unmodified.
- **Open items**:
  - Codex review (`artifacts/GN-4/review.md`).
