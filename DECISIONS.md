# DECISIONS — good-news (append-only)

## D001 — Routine owns main and data files (2026-10-15, Grok Bot from existing notes)
- Decision: Agents never commit to main or touch data/*.json; work on job/<id> branches.
- Why: A routine pushes data twice daily; conflicts would break the live site.
- Alternatives rejected: Agents committing directly to main.

## D002 — Adopt AGENTS/PLAN/HANDOFF/DECISIONS handoff files (2026-10-15, Grok Bot for Anil)
- Decision: these repo files are the source of truth for agents; `/workspace/projects/BOARD.md` is only an index; claims via board.sh.
- Why: several agents (Codex, Cursor, agy) share this box and must not duplicate work.
- Alternatives rejected: one central board as source of truth.
