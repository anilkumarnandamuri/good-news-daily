# AGENTS.md — rules for every coding agent (Codex, Cursor, Antigravity/agy, others)

1. **Read first:** `HANDOFF.md` (current state), then `PLAN.md` (milestones), then skim `DECISIONS.md`. The repo files are the source of truth; `/workspace/projects/BOARD.md` is only an overview index.
2. **Claim before working:** pick the first unchecked, unclaimed milestone in `PLAN.md` and claim it with
   `/workspace/projects/board.sh claim <TASK-ID> <agent> <model> job/<TASK-ID>` (flock-safe; it marks the PLAN.md line `[~] claimed by …`). Exit 3 means someone else holds it: pick another. One active claim per milestone. A claim older than 24h with no HANDOFF update is stale and may be taken over (say so in HANDOFF.md).
3. **Branch:** work only on local branch `job/<TASK-ID>` created from the latest base branch (named in HANDOFF.md). Never push, never change remotes, never deploy, never touch secrets or token files.
4. **At every stop** (done, blocked, out of time/quota): overwrite `HANDOFF.md` (keep its section headings), then run
   `/workspace/projects/board.sh checkpoint <TASK-ID> '<one-line note>' --status claimed|in-review|blocked --next '<next step>'` and commit.
5. **Decisions:** append real choices to `DECISIONS.md` as `## Dnnn — <title> (<date>, <agent>)` with Decision / Why / Alternatives rejected. Never edit old entries; supersede with a new one.
6. **Done means:** tests pass, plus (for web apps) a Playwright browser test and screenshots in `artifacts/<TASK-ID>/`, HANDOFF.md updated, and status set to `in-review`. Only a reviewer (Codex) or Anil moves a task to done.
7. Change `PLAN.md` only for scope changes (besides the claim markers board.sh writes).

## This repo (good-news-voice)
- Path: `/workspace/good-news-voice` | Remote: (none; local only) | Base branch: `master`
- Run: `python3 -m http.server 8000  # http://127.0.0.1:8000/demo/`
- Tests: npm test && python3 -m unittest discover -s tests -p 'test_*.py' && python3 tests/browser_smoke.py
