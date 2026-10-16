# GN-6: Telugu audio via local Piper TTS (pre-generated MP3, hosted outside the site's history)

Status: built
Branch: job/GN-6 (base: job/GV-2 4493f51 — needs the reader's voice-module MP3 mode)
Model: codex/gpt-6.1-sol (medium) | Playbook: Feature | Cost: cheap
Created: 2026-10-15 22:12 PDT
Test command: python3 -m unittest discover -s tests -p 'test_*.py' && node --test tests/*.test.js && node --test voice/tests/*.test.js && python3 -m pytest tests/test_legacy_feed_browser.py tests/test_voice_reader.py tests/test_text_size_browser.py tests/test_te_audio_browser.py -q

## Why
Family feedback: on iPhone and an old Samsung, Telugu Listen says the voice isn't installed (no Telugu speechSynthesis voice). English works. Anil chose the Piper Telugu "maya" voice (free, local).

## Task
1. Generation (scripts/tts_audio.py, called from scripts/build.py after summarize ONLY when GOOD_NEWS_AUDIO=1; default off so the live routine is unchanged until Anil approves):
   - For each story with a non-empty Telugu summary (sum_te; summary_status paired or summary), text = whitespace-normalized sum_te.
   - Key = first 16 hex of sha256(f"{voice_id}\n{rate}\n{text}"), so only new/changed summaries generate audio; existing files are reused.
   - Synthesize with Piper: binary GOOD_NEWS_PIPER (default /workspace/tools/piper/venv/bin/piper), model GOOD_NEWS_PIPER_MODEL (default /workspace/tools/piper/models/te_IN-maya-medium.onnx). Encode with ffmpeg to mono, 22.05 kHz, ~32 kbps MP3. Write to GOOD_NEWS_AUDIO_DIR (default ../good-news-audio, a separate local checkout; never inside this repo) as te/<key>.mp3.
   - Write/refresh a manifest in that dir in the format the voice module's mp3 mode already reads (see voice/INTEGRATION.md, voice/README.md, voice/tools/build_audio.py, reader.js getManifest), plus record per story in news.json only small fields if needed (e.g. audio_te key or URL). No audio bytes in this repo.
   - Rolling 7-day window: delete te/*.mp3 that no current story references AND are older than 7 days (mtime); prune the manifest accordingly.
   - Time budget (env, default 300 s) and per-story error isolation: audio failures never fail the build; missing Piper/ffmpeg => skip with a log line.
   - Base URL for the site to fetch audio: GOOD_NEWS_AUDIO_BASE_URL (default https://anilkumarnandamuri.github.io/good-news-audio/). The site must also work when the manifest/audio is unavailable.
   - scripts/publish_audio.sh: commit the audio dir in its own git repo (no push unless --push; we will NOT run --push). Document the one-time setup (create repo good-news-audio, enable Pages from main) in README; do not create it.
2. Reader (reader.js): Telugu Listen plays the story's pre-generated MP3 via the voice module's mp3 mode whenever it exists — on the default site, not only with ?voice=1. Device speechSynthesis is only the fallback. If neither an MP3 nor a Telugu device voice is available, show a friendly inline message (Telugu + English, e.g. "ఈ వార్తకు ఆడియో ఇంకా అందుబాటులో లేదు / Audio isn't available for this story yet") instead of an error or silent no-op. English Listen is unchanged (device speech). Keep GN-5's single A-/A+ and 16px base. Keep all GV-2 behaviour and tests green.
3. Docs: README section (how audio is generated, hosted, sized, rolling window, licences), DECISIONS.md entry (hosting choice + alternatives), HANDOFF.md.

## Licences
- Piper tool: piper-tts 1.8.0 (GPL-3.0) — used only as an offline tool; generated audio is not covered by the GPL.
- Voice te_IN maya medium: trained on IIT Madras IndicTTS; the IITM EULA grants a perpetual, worldwide, royalty-free licence and allows free distribution of derivative works (copy at /workspace/tts-eval/indictts-license.pdf).

## Acceptance
- [x] Unit tests for key/caching (second run generates nothing), changed text => new file, rolling deletion, budget/missing-binary skip, manifest format — with a fake piper/ffmpeg (no network, fast).
- [x] Node tests: Telugu Listen uses MP3 when present; falls back to device speech when no MP3; friendly message when neither; English unchanged.
- [ ] Playwright test tests/test_te_audio_browser.py with fixed fixtures (fixture news.json + a small real Piper MP3 under tests/fixtures/audio/), screenshots in artifacts/GN-6/ at 390 and 1280: Telugu MP3 playing; friendly message state.
- [x] Data files data/news.json and data/summaries.json unchanged.

## Checkpoint
- Changed: implemented opt-in local Piper/ffmpeg generation after summarization; normalized text/voice/rate hashing, cached reuse, atomic output, current-story manifest, seven-day unreferenced cleanup, shared deadline and isolated failures. Audio output is rejected inside this repo. Added separate-checkout publish helper (not executed).
- Reader: default Telugu uses the real voice module and external manifest/MP3; absent/stale/broken/offline audio falls back to Telugu device speech. Missing both produces a persistent inline bilingual status. Default English and the GV-2 preview stay intact; no GN-5 typography changes.
- Files: `scripts/tts_audio.py`, `scripts/build.py`, `scripts/publish_audio.sh`, `reader.js`, `tests/test_tts_audio.py`, `tests/frontend.test.js`, `tests/test_artifacts.py`, `tests/test_te_audio_browser.py`, `tests/fixtures/te-audio-news.json`, `tests/fixtures/audio/{te-maya.mp3,README.md}`, README/HANDOFF/DECISIONS, and `artifacts/GN-6/verification.txt`.
- Evidence: exact requested unittest + frontend Node + voice Node command passed (51 Python tests, 24 frontend Node cases, 5 voice Node cases). `git diff --check` and `bash -n scripts/publish_audio.sh` passed. Real fixture probed: 2.324898 s, 9526 bytes, mono 22050 Hz / 32000 bps. Both routine-owned data files are byte-identical to HEAD.
- Browser test is written with a free-port local server, fixed routed feed/manifest/real Piper MP3, and no external network. Four screenshot cases target `artifacts/GN-6/te-{mp3-playing,audio-unavailable}-{390,1280}.png` on the default site without a Telugu device voice.
- Open items: browser run failed in server setup with `PermissionError: [Errno 1] Operation not permitted` creating AF_INET sockets; screenshots and real-browser assertions remain pending operator execution. Thus the browser acceptance checkbox remains open. Operator should run the full task Test command and inspect screenshots, then review/commit. No audio repo was created, no publication helper run, no routine enabled, no network used, no branch changed and no commits made. Existing GN-6 claim retained; no board mutation outside the authorized writable repo.
