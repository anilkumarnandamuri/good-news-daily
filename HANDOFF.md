# HANDOFF — good-news

## Updated
2026-10-15 13:58 PDT | agy/gemini-3.8-flash-high | branch `job/GV-2` | last commit d787016

## Current task / claim
**GV-2** Integrate voice player into Good News UI using the `pairs` field — status **claimed** by agy/gemini-3.8-flash-high on `job/GV-2` (since 2026-10-15 13:58 PDT). Last note: 2026-10-15 13:58 PDT claimed by agy/gemini-3.8-flash-high

## Done this session
- Added AGENTS.md, PLAN.md, HANDOFF.md, DECISIONS.md and .cursor/rules/agents.mdc from README, file tree and git log.

## Verified (with evidence)
- Site is live on GitHub Pages and the data routine pushes `data/news.json` twice daily (latest 3d0a47a, 2026-10-15 07:00 PT).

## Unverified
- Whether the laptop branch 83c9ad5 conflicts with the current summaries cache (v5).

## Broken / half-done
- On `feat/voice-integration`: `python3 -m unittest discover -s tests` fails 115 checks in tests/test_artifacts.py (KeyError 'summary_status') because routine-built data/news.json (origin/main) predates the laptop branch's data contract; the laptop branch alone passes. Resolve in GN-1 review (routine build must emit the new fields before merge to main).
- Laptop branch added CHECKPOINT.md and decisions.tsv; fold into HANDOFF.md/DECISIONS.md during GN-1 review.
- Box working tree has an uncommitted change to `data/summaries.json` and untracked shots/ — leave them; do not commit on main.

## Next 3 steps (smallest first)
1. GN-1: Import laptop branch codex/goodnews-20261014 (83c9ad5: paired EN/TE summaries, `pairs` field) onto the box — needs the laptop or a push from it; Anil/Chief of Staff only.
2. GN-2: Add an automated Playwright smoke test (list, reader EN/TE, saved tab at 390px/1280px) with screenshots in artifacts/GN-2/; no data-file changes.
3. GN-3: Integrate the standalone voice module (/workspace/good-news-voice) into the reader's Listen button, behind a flag; follow good-news-voice INTEGRATION.md.

## Blockers / questions for Anil
- Laptop-only branch codex/goodnews-20261014 83c9ad5 is not on the box (pending import).
- These docs live on branch docs/agent-handoff-20261015 and need merging into main by Anil/Chief of Staff (avoid conflicts with the data routine).

## How to resume
```sh
cd /workspace/good-news
pip install -r requirements.txt; python scripts/build.py; python -m http.server 8000  # ?theme=dark, ?cat=telugu
/workspace/projects/board.sh status
```
