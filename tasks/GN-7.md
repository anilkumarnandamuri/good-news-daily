# GN-7: scripts/routine_run.sh daily routine wrapper

Status: in-progress
Branch: job/GN-7 (base: main)
Model: codex/gpt-6.1-sol (medium) | Playbook: Feature | Cost: cheap
Created: 2026-10-17
Test command: python3 -m unittest discover -s tests -p 'test_routine_run.py' -q

## Task
Write `scripts/routine_run.sh` that runs, in order:

1. `git pull --ff-only origin main`
2. `GOOD_NEWS_AUDIO=1 python3 scripts/build.py`
3. `GOOD_NEWS_AUDIO_DIR=/workspace/good-news-audio bash scripts/publish_audio.sh --push` — failure here must NOT block the rest
4. Commit `data/news.json`, plus `data/audio-config.json` only if it changed; never commit `data/summaries.json`
5. Push `main` without force
6. `python3 scripts/send_push.py` — only if the build and (site) push succeeded

Requirements:
- Prints a compact summary of each step (ok/fail + brief reason)
- Never prints secrets (ONESIGNAL_API_KEY, tokens, auth files)
- Comes with an offline unit test that does not need the network (mock/stub git, build, publish, push, send_push)
- The Codex job itself must NOT push, deploy, force-push, or delete branches — only the script's runtime does those things when an operator runs it
- Do not modify `data/news.json` / `data/summaries.json` contents as part of this job
- Update HANDOFF.md, DECISIONS.md if needed, fill Checkpoint, set Status: built
- Commit on `job/GN-7` only

## Acceptance
- [ ] `scripts/routine_run.sh` exists and is executable
- [ ] Offline test covers: order of steps; publish_audio failure does not skip later site commit/push; send_push skipped when build or push fails; summaries.json never staged; audio-config.json committed only when changed; no secrets in output
- [ ] Existing unittest / node suites still pass if run

## Checkpoint
(empty — builder fills)
