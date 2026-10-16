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
- Activation review fix: story opening prefetches Telugu config/manifest and the voice module. Resolved taps invoke speech/play before any await. Pending lookups show Stop, then bilingual Tap to listen when speech needs a new gesture; the next tap speaks synchronously. Stop/navigation invalidate pending work. Failed loads remain retryable.
- Current validation: requested combined command passes (52 Python tests; 30 frontend cases and voice suite green). GN-6 browser retry: six setup errors because sandbox denies AF_INET socket creation; no new screenshots. Data files unchanged; no network, commits, pushes or branch switches.
- Review fixes: preserve the player/audio element after autoplay rejection; show bilingual Tap to play and resume synchronously before awaits. Loading/playing show Stop and stop on tap. Failed, timed-out, invalid or empty Telugu manifests are retried; successful manifests remain cached. Legacy stories with absent summary_status and non-empty English/Telugu summaries now generate audio; explicit excerpts remain excluded.
- Tests: required unittest + frontend Node + voice Node command passed (52 Python tests). Direct Node runs additionally confirm all 26 frontend cases and 5 voice cases pass, including GV-2 and GN-5 regressions. `git diff --check` passed; routine-owned data files match HEAD.
- Browser: six GN-6 cases now include one rejected play followed by synchronous resume on the same element at 390/1280; the autoplay-bypass launch flag was removed. Intended screenshots include `te-tap-to-play-{390,1280}.png` and `te-mp3-resumed-{390,1280}.png` in artifacts/GN-6/.
- Open: the full browser command fails at local server setup (24 setup errors: sandbox denies AF_INET sockets with PermissionError), before browser launch. Screenshots and browser acceptance remain pending execution in a socket-enabled environment.
- Existing GN-6 claim/branch retained. No commits, branch switches, board writes, network, publishing or audio-host creation. Implementation remains built, awaiting browser verification and review.

## Review response
- Latest P1 (Telugu device-speech activation) addressed: prefetch on story open, synchronous resolved speech/MP3 path, and explicit bilingual Tap to listen resume after pending manifest resolution. The resume bypasses manifest requests and invokes speak in the next click; loading Stop cancels instead of restarting. This conservative resume policy applies on all devices, including iOS. Added four Node regressions for prefetched no-clip/offline speech, pending speech resume, prefetched MP3 and Stop during loading; all prior regressions remain green.
- P1 addressed through the review's explicit resume option: the reader handles paused state with a clear bilingual action and reuses the active player's HTMLAudioElement, calling play() synchronously in the next tap. Tests cover both rejected promises and synchronous NotAllowedError throws, same-element identity, invocation before promise flushing, resumed Stop behavior and teardown. The former paused-player Stop test now asserts the deliberately changed resume behavior. Playwright stubs play() to reject once and checks that retry occurs inside the button handler on the same element; execution remains sandbox-blocked.
- P2 addressed by clearing teluguManifestPromise after unsuccessful/empty loads, including the exception fallback. Node coverage exercises offline rejection, HTTP failure, empty/invalid JSON and timeout, then verifies a successful later tap and cached reuse.
- Generation compatibility addressed by accepting legacy bilingual summaries with absent status while excluding explicit excerpts and blank/missing summary text. A fake-only unit test verifies generation, eligibility exclusions and unchanged input stories.
