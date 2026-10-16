# DECISIONS — good-news-voice (append-only)

## D001 — Local history in .local-git (superseded by D002) (2026-10-15, Grok Bot from existing notes)
- Decision: Commit with --git-dir=.local-git; original .git untouched.
- Why: The box mounted .git read-only on 2026-10-14.
- Alternatives rejected: Working around the read-only mount.

## D002 — Use .git again (2026-10-15, Grok Bot from existing notes)
- Decision: `.git` master is canonical; `.local-git` kept only as a stale backup.
- Why: .git is writable again and its tree equals .local-git HEAD.
- Alternatives rejected: Keeping two histories in sync.

## D003 — Adopt AGENTS/PLAN/HANDOFF/DECISIONS handoff files (2026-10-15, Grok Bot for Anil)
- Decision: these repo files are the source of truth for agents; `/workspace/projects/BOARD.md` is only an index; claims via board.sh.
- Why: several agents (Codex, Cursor, agy) share this box and must not duplicate work.
- Alternatives rejected: one central board as source of truth.

## D004 — Smoke script writes screenshots to artifacts/GV-1 (2026-10-15, agy)
- Decision: tests/browser_smoke.py stays a plain script (python3 tests/browser_smoke.py) and saves 390/1280px light/dark screenshots to artifacts/GV-1/ and test-results/, with overflow/visibility assertions.
- Why: matches the repo test command in AGENTS.md; no new dependencies.
- Alternatives rejected: converting to pytest fixtures (larger rewrite, no added coverage).
