# PLAN — good-news-voice

## Goal
Standalone bilingual (EN/TE) voice module for Good News Daily: pre-built MP3 per story + intros + combined radio, with a browser player and speech fallback, ready to copy into good-news.

## Non-goals
- Pushing anywhere (no remote)
- Real device lock-screen testing (unavailable on the box)

## Milestones
- [x] **GV-0** Existing work as of 2026-10-15 13:41 PT: Responsive bilingual player + demo (queue, highlight, light/dark); Sample MP3s for 5 stories in both languages, intros, radio mixes; 4 Node chunker/schema tests + 3 Python builder tests; Fixed playback-rate reset on source change; README/API/INTEGRATION docs; first milestone e181290 (in .local-git) — done (history) 993b96b
- [~] **GV-1** Finish browser smoke checks (tests/browser_smoke.py), inspect mobile/dark screenshots in artifacts/GV-1/, fix findings, commit. — in-review 2026-10-15 13:48 PDT by agy/claude-sonnet-5-5-medium (job/GV-1 @ bf99b53)
- [ ] **GV-2** Integrate into good-news (see GN-3) once GV-1 is verified.

## Definition of done
Tests pass (npm test && python3 -m unittest discover -s tests -p 'test_*.py' && python3 tests/browser_smoke.py); for web UI a Playwright test passes with screenshots in `artifacts/<task-id>/`; HANDOFF.md rewritten; DECISIONS.md appended for real choices; reviewed; committed on `job/<task-id>`; never pushed.
