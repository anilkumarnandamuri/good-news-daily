# PLAN — good-news

## Goal
Free, static, mobile-first daily digest of positive news in English and Telugu (India/AP-Telangana), hosted on GitHub Pages with no paid APIs or backend.

## Non-goals
- Paid APIs or a backend server
- Agents editing `data/*.json` or committing to `main` (a routine refreshes and pushes data twice daily)

## Milestones
- [x] **GN-0** Existing work as of 2026-10-15 13:41 PT: Static site, RSS fetch/dedupe/positivity scoring (scripts/build.py); OneSignal web push (send_push.py), digest.py; In-site reader with EN/TE summaries, Listen (Web Speech); summarize step with cache v5; Stickiness features (Today's 5, streak, saved tab, WhatsApp share) — bd8b15d — done (history) 3d0a47a
- [~] **GN-1** Import laptop branch codex/goodnews-20261014 (83c9ad5: paired EN/TE summaries, `pairs` field) onto the box — needs the laptop or a push from it; Anil/Chief of Staff only. — in-review 2026-10-15 16:09 PDT by agy/gemini-3.8-flash-high (job/GN-1 @ 80dbc26)
- [ ] **GN-2** Add an automated Playwright smoke test (list, reader EN/TE, saved tab at 390px/1280px) with screenshots in artifacts/GN-2/; no data-file changes.
- [ ] **GN-3** (superseded by GV-2) Integrate the standalone voice module into the reader's Listen button.
- [~] **GN-4** Summaries fallback: when no LLM hook is configured (GOOD_NEWS_LLM/GOOD_NEWS_LLM_COMMAND), summarize v6 falls back to today's live extract-and-translate method (v5: feed description + og/meta description, free Google translate endpoint with MyMemory fallback), so the routine (`python scripts/build.py`) never regresses stories to excerpt-only. Keep data/summaries.json byte-identical to origin/main (the routine keeps a local uncommitted cache and does `git pull --ff-only`) and untrack scripts/__pycache__. Accept: routine simulation on today's feed yields EN+TE summaries for >= the count on origin/main; unittest, node, voice and browser tests pass. Decided by Anil 2026-10-15 19:23 PT (option b). — in-review 2026-10-15 20:08 PDT by agy/gemini-3.8-flash-high (job/GN-4 @ ab32f51)
- [ ] **GV-2** Integrate voice player into Good News UI using the `pairs` field. Branch `feat/voice-integration` (voice module imported under `voice/` with history; laptop 83c9ad5 merged). Accept: reader Listen uses the voice/ player (MP3 when present, speech fallback) reading EN/TE `pairs` sentence by sentence, behind a flag (default off, `?voice=1`); Playwright test at 390px/1280px with screenshots in artifacts/GV-2/; existing node tests green. Stop if: it requires changing routine-owned data/news.json or scripts/build.py output.

## Definition of done
Tests pass (No automated test suite found (unknown). Screenshots in shots/ are taken manually with headless Chrome.); for web UI a Playwright test passes with screenshots in `artifacts/<task-id>/`; HANDOFF.md rewritten; DECISIONS.md appended for real choices; reviewed; committed on `job/<task-id>`; never pushed.
