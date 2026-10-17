# HANDOFF — good-news

## Updated
2026-10-17 | Codex | branch `job/GN-7` | base/last commit ae82a50

## Current task / claim
**GN-7** — runner implementation built; ready for review locally. Existing claim retained. Shared board checkpoint and git staging/commit blocked by read-only filesystem outside this worktree.

## Done this session
- Added executable `scripts/routine_run.sh`: main-checkout guard; fast-forward pull; audio-enabled build; nonfatal audio publication; path-scoped site commit; ordinary main push; conditional notification.
- Prints six compact step results, suppressing child output to prevent credential/error leaks. Fatal failures skip dependent steps; audio failure continues and reports the warning.
- Added eight offline tests, including real local Git verification that pre-staged summaries/unrelated files stay out of the routine commit. All external build/publication/transport commands are stubbed in tests.
- Filled tasks/GN-7.md Checkpoint and marked Status: built. Appended D015.
- No live routine execution, network publication, deployment, force push or branch deletion. Routine-owned news and summaries remain unchanged.

## Verified (with evidence)
- `python3 -m unittest discover -s tests -p 'test_routine_run.py' -q`: eight tests pass.
- `node --test tests/*.test.js voice/tests/*.test.js`: both suites pass.
- `bash -n scripts/routine_run.sh` and `git diff --check`: pass.
- Full Python discovery: 60 tests ran; nine errors within the existing artifact-contract test due to missing summary-cache entries/pairs. Artifact test and data files are unchanged from HEAD.

## Unverified
- Operator runtime with real remote repositories, Piper/audio checkout and OneSignal credentials.
- No browser run: GN-7 changes only the shell workflow and offline tests; no UI changes.

## Broken / half-done
- Cannot stage/commit: git reports read-only `/workspace/good-news/.git/worktrees/good-news-gn7/index.lock`.
- Board checkpoint attempted with status in-review; failed writing read-only `/workspace/good-news/PLAN.md`. Shared board status was not successfully updated.
- Full Python suite retains the existing artifact/cache errors; data fixes are outside GN-7 and explicitly prohibited here.

## Next 3 steps (smallest first)
1. Review the GN-7 runner and eight offline tests.
2. In a writable environment, checkpoint GN-7 as in-review and commit the five task files on job/GN-7.
3. Operator reviews the unrelated artifact/cache mismatch and runs the routine from main when ready.

## Blockers / questions for Anil
- Shared board metadata and Git worktree metadata need writable access to record the checkpoint and commit. No product clarification needed.

## How to resume
```sh
python3 -m unittest discover -s tests -p 'test_routine_run.py' -q
bash -n scripts/routine_run.sh
node --test tests/*.test.js voice/tests/*.test.js
/workspace/projects/board.sh checkpoint GN-7 'Runner built; offline tests pass; baseline artifact cache errors remain' --status in-review --next 'Review GN-7 runner and offline tests'
git add -- scripts/routine_run.sh tests/test_routine_run.py tasks/GN-7.md HANDOFF.md DECISIONS.md
git commit -m 'Add daily routine runner with offline workflow tests'
```
