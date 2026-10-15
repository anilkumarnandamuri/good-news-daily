# GV-2: GV-2 (see PLAN.md and HANDOFF.md): Integrate the voice player (imported under vo

Status: in-progress
Branch: job/GV-2 (base: feat/voice-integration)
Model: agy/gemini-3.8-flash-high | Playbook: Feature | Cost: cheap
Created: 2026-10-15 13:58 PDT
Test command:

## Task
GV-2 (see PLAN.md and HANDOFF.md): Integrate the voice player (imported under voice/, see voice/INTEGRATION.md and voice/README.md) into the Good News Daily reader (reader.js, index.html, styles.css) using the paired EN/TE summaries in data/summaries.json (the `pairs` field from the laptop branch). The reader Listen button should, when the flag is on (URL ?voice=1 or localStorage gn-voice=1; default OFF so the live site is unchanged), play the story sentence by sentence from `pairs` in the selected language (EN or TE), highlighting the current sentence, using pre-built MP3 when available and Web Speech fallback otherwise. Reuse voice/src code by importing it rather than copy-pasting. Do NOT modify data/news.json, data/summaries.json or scripts/build.py (routine-owned), and do not commit __pycache__ files. Add a Python Playwright pytest (serve the repo with python http.server on a free port, mock speechSynthesis if needed) that opens the reader with ?voice=1 at 390px and 1280px, starts Listen in EN and TE, asserts sentence highlighting advances, and saves screenshots to artifacts/GV-2/. Keep node --test tests/*.test.js green. Note: python3 -m unittest discover -s tests currently fails in tests/test_artifacts.py because routine data predates the new data contract; that is pre-existing and out of scope; do not fix it by editing data.

## Acceptance (definition of done, see .cursor/rules/done.mdc)
- [ ] Checkpoint below filled and Status updated
- [ ] Playwright browser test passes via the Test command
- [ ] New screenshot in artifacts/GV-2/
- [ ] Codex review (artifacts/GV-2/review.md) has no [P0]-[P2] items

## Checkpoint
_(agent fills: what changed, files, verification evidence, open items)_

## Log
- 2026-10-15 13:58 PDT run-job started
- 2026-10-15 14:35 PDT Codex review: 3 must-fix item(s); running one fix pass
- 2026-10-15 14:47 PDT Codex review: 3 must-fix item(s) open
- 2026-10-15 16:14 PDT run-job resumed
