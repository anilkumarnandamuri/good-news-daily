# GN-4: GN-4 (see PLAN.md GN-4; Anil chose this 2026-10-15 19:23 PT). Problem: scripts/s

Status: in-progress
Branch: job/GN-4 (base: merge/gn-main-20261015)
Model: agy/gemini-3.8-flash-high | Playbook: Bug fix | Cost: cheap
Created: 2026-10-15 19:26 PDT
Test command:

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
- [ ] Checkpoint below filled and Status updated
- [ ] Playwright browser test passes via the Test command
- [ ] New screenshot in artifacts/GN-4/
- [ ] Codex review (artifacts/GN-4/review.md) has no [P0]-[P2] items

## Checkpoint
_(agent fills: what changed, files, verification evidence, open items)_

## Log
- 2026-10-15 19:26 PDT run-job started
