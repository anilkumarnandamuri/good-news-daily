# PLAN — good-news

## Goal
Free, static, mobile-first daily digest of positive news in English and Telugu (India/AP-Telangana), hosted on GitHub Pages with no paid APIs or backend.

## Non-goals
- Paid APIs or a backend server
- Agents editing `data/*.json` or committing to `main` (a routine refreshes and pushes data twice daily)

## Milestones
- [x] **GN-0** Existing work as of 2026-10-15 13:41 PT: Static site, RSS fetch/dedupe/positivity scoring (scripts/build.py); OneSignal web push (send_push.py), digest.py; In-site reader with EN/TE summaries, Listen (Web Speech); summarize step with cache v5; Stickiness features (Today's 5, streak, saved tab, WhatsApp share) — bd8b15d — done (history) 3d0a47a
- [ ] **GN-1** Import laptop branch codex/goodnews-20261014 (83c9ad5: paired EN/TE summaries, `pairs` field) onto the box — needs the laptop or a push from it; Anil/Chief of Staff only.
- [ ] **GN-2** Add an automated Playwright smoke test (list, reader EN/TE, saved tab at 390px/1280px) with screenshots in artifacts/GN-2/; no data-file changes.
- [ ] **GN-3** Integrate the standalone voice module (/workspace/good-news-voice) into the reader's Listen button, behind a flag; follow good-news-voice INTEGRATION.md.

## Definition of done
Tests pass (No automated test suite found (unknown). Screenshots in shots/ are taken manually with headless Chrome.); for web UI a Playwright test passes with screenshots in `artifacts/<task-id>/`; HANDOFF.md rewritten; DECISIONS.md appended for real choices; reviewed; committed on `job/<task-id>`; never pushed.
