# Good News Daily 🌻

A free, static, mobile-first digest of the day's **positive** news — English/world plus a **Telugu (తెలుగు)** section and India/AP-Telangana.
Hostable on GitHub Pages; no paid APIs, no backend.

## Structure
- `index.html`, `styles.css`, `app.js` — static front end with system fonts and local Noto Sans Telugu, light/dark mode, large text, category filters, hero + cards, ad slot, mailto digest waitlist.
- `scripts/build.py` — fetches RSS, dedupes, scores positivity, writes `data/news.json`.
- `data/news.json` — generated data (headline, source, ≤220-char excerpt, link, time, category, image URL).
- `scripts/summarize.py` — offline validation and caching of bilingual summaries, with an optional executable LLM hook.
- `fonts/` — Noto Sans Telugu and its SIL Open Font License.
- `tests/` — Python and Node tests with local fixtures and an in-memory notification SDK.

## Run
    pip install -r requirements.txt
    python scripts/build.py
    python -m http.server 8000   # open http://localhost:8000  (?theme=dark, ?cat=telugu)

The static site needs no build step. To preview the checked-in snapshot, run only the HTTP server. The RSS build still needs network access and the packages in `requirements.txt`.

## Test without network access

    python3 -m unittest discover -s tests -v
    node --test --experimental-test-isolation=none tests/*.test.js
    git diff --check

Use Node 22 or newer. The isolation flag lets Node's test runner work in sandboxes that prohibit child-process IPC sockets. Tests never send notifications or contact OneSignal. Python tests use fixture feeds and a sentiment stub because the RSS dependencies are unnecessary for these contract checks. The front-end tests execute the real scripts in a small DOM test double. They check behavior and markup, not rendered layout.

## Bilingual summaries

A complete summary has 4–6 short sentences in each language. The cache stores an ordered `pairs` array of `{en, te}` objects. Each object contains one English sentence and the Telugu sentence for the same fact. The public `sum_en` and `sum_te` strings are derived from those pairs in the same order. Validation rejects missing translations, different counts, multiple sentences inside one pair, repeated sentences, incomplete sentences, wrong-language text, and mismatched numeric figures.

When the opt-in LLM hook is not enabled (or when it fails), summarization falls back to the live extract-and-translate method ported from version 5:
- Extracts up to 6 canonical source-language sentences from the feed description and article og/meta descriptions (never the article body).
- Translates sentence-by-sentence via free endpoints (Google Translate with MyMemory fallback) strictly 1:1.
- Builds aligned `pairs` directly from the sentence lists without re-splitting, validates them with `validate_pairs`, stores a version 6 cache entry, and sets `summary_status='paired'` (for 4–6 sentence pairs) or `summary_status='summary'` (for 1–3 sentence pairs).

Existing version 5 cache entries whose joined strings cannot be re-paired by `legacy_pairs` (due to sentence-count mismatch or shorter length) are retained with `summary_status` set to `'summary'` without network calls. Both `'paired'` and `'summary'` stories render complete bilingual summaries with Listen controls in the reader. If extraction or translation fails, the story falls back to `summary_status='excerpt'` with publisher excerpts, and will be retried on the next run.

Run summarization with:

    python3 scripts/summarize.py

### Optional LLM hook

Set both variables to enable your own model executable. The command is a JSON argv array, executed without a shell. For example, after you supply your hook:

    GOOD_NEWS_LLM=1 \
    GOOD_NEWS_LLM_COMMAND='["python3", "/absolute/path/to/your_hook.py"]' \
    python3 scripts/summarize.py

The same variables apply when the existing `scripts/build.py` routine calls the summarizer. Values such as `0`, `false`, and `true` leave the hook disabled. No provider SDK, endpoint, or API key is built into the repository. Your executable may use an installed local model or a provider you configure. Keep credentials in its environment.

The executable reads one JSON object from standard input. It contains `version: 1`, `instruction`, `story` with `title`, `desc`, `summary`, `source` and `lang`, and `source_sentences` extracted in source order. It must write only this JSON shape to standard output:

```json
{"pairs":[{"en":"One complete English sentence.","te":"ఒక పూర్తి తెలుగు వాక్యం."}]}
```

The example shows one pair to explain the shape. A publishable response needs 4–6 pairs. Put key facts first and use plain language. Translate each sentence at its original index, with the same names, numbers and uncertainty. Return `{"pairs":[]}` if the source is too thin. Invalid output, nonzero exits, missing commands and timeouts fall back to the excerpt. Each call has at most 20 seconds, and new calls stop after the existing 240-second summary budget. Complete results are cached by story ID and a fingerprint of the public source fields. Full descriptions are also checked for changes when both the cache and new input contain them. Failed calls retry on a later opted-in run. Hook output is not logged.

## Reading and static performance

Text starts at the normal browser size. The reader’s A− and A+ controls resize text across the whole site from 85% to 160%, with the chosen size saved on this device. Preferences and saved stories stay on the device. Telugu uses a bundled font with `font-display: swap`. Text uses relative sizes, controls have at least 44-pixel targets, keyboard focus is visible, and the reader contains focus until it closes. Automated palette checks require at least 4.5:1 contrast for the tested text colors in both themes.

Images have reserved dimensions, async decoding, and native lazy loading. The lead image loads eagerly. Local scripts defer in dependency order, with the OneSignal SDK after the local scripts so a slow SDK download does not hold up the feed. Only crossing the desktop layout breakpoint causes a resize rerender. News requests use normal browser HTTP caching, including the host's cache headers and conditional requests. There is no extra service worker competing with OneSignal. The standalone summary command compacts `data/news.json`; the scheduled build retains its original output format.

Before release, preview light and dark themes at 320, 390 and 1280 pixels, repeat at 200% zoom, and check Telugu text and reader keyboard navigation. Rendered layout and assistive technology behavior require browser checks beyond the zero-dependency tests.

## Feeds (verified with curl, Oct 2026)
Good News Network, Positive News, Reasons to be Cheerful, BBC Science & Environment, BBC Health, BBC Technology (intermittent timeouts),
ScienceDaily Science/Health, The Hindu Science / Andhra Pradesh / Telangana, Sakshi, TV9 Telugu, Oneindia Telugu, Namasthe Telangana.
Not usable: Eenadu (RSS returns 0 items), Andhra Jyothy/ABN (404), News18 Telugu (403).

## Scoring
- **English:** VADER compound (title + summary) + positive/negative keyword regexes. Any negative keyword in the headline (death, war, crime, disaster, arrest, politics, etc.) drops the item. Curated positive outlets get a bonus.
- **Telugu:** no translation or model; a substring lexicon (Telugu is agglutinative) of positive cues (గుడ్ న్యూస్, రికార్డు, అవార్డు, వేడుక…) vs. negative cues (మృతి, ప్రమాద, అరెస్ట్…), plus filters for politics, party names, film promotion, gold prices and horoscopes. Needs ≥1 positive cue and 0 negative cues.
- **Limits:** a lexicon misses sarcasm, negation and new vocabulary. Proper names can collide with words (for example విజయ్ vs విజయం), and the Telugu yield is small (about 6 items a day). Category comes from a keyword match, so it is rough. A multilingual transformer (for example `cardiffnlp/twitter-xlm-roberta-base-sentiment`) would help, but it adds about 1 GB of torch to CI.
- **Copyright:** only headlines, a short feed-provided excerpt and the publisher's own feed image URL are shown. Every item links to the original.

## Daily refresh (not set up; nothing deployed)
Add `.github/workflows/build.yml` to a repo with GitHub Pages enabled. For example: `on: schedule: - cron: "30 0,12 * * *"` (06:00/18:00 IST) + `workflow_dispatch`;
steps: checkout → setup-python 3.12 → `pip install -r requirements.txt && python scripts/build.py` → commit `data/news.json` if it changed and push
(needs `permissions: contents: write`). As an alternative, run a cron job on any machine that runs the build and pushes.

## Design references
Apple News (big image-led hero, serif headlines), Particle/Artifact (clean cards, pill category labels), Flipboard (image-first grid),
Positive News / Good News Network (warm, optimistic palette). Placeholders use category gradients when a feed has no image.

## Telugu audio (GN-6, opt-in generation)

Telugu Listen on the default site prefers a matching MP3 through `voice/` and falls
back to a Telugu device voice. If both are unavailable, an inline Telugu/English
message explains that audio is not available yet. English continues to use device
speech; the existing `?voice=1` voice-module preview remains available.

Generation stays **off** until Anil approves changing the routine. After the audio
checkout has been set up, the operator can run:

```sh
GOOD_NEWS_AUDIO=1 python3 scripts/build.py
# Review output, then commit the separate audio checkout (no push):
scripts/publish_audio.sh
# Only the operator should explicitly request publication:
# scripts/publish_audio.sh --push
```

The hook runs after summarization, using every nonempty `sum_te` with status
`paired` or `summary`. It normalizes whitespace and names clips
`te/<first-16-sha256(voice_id + "\n" + rate + "\n" + text)>.mp3`. Unchanged clips
are reused; changed summaries, voice IDs, or synthesis rates get new filenames.
Piper uses maya at normal length scale (`1.0`); ffmpeg creates mono, 22.05 kHz,
32 kbps MP3s (about 240 KB/minute; 100 one-minute stories are about 24 MB).
The version-1 `manifest.json` embeds current summary text so the player rejects
stale recordings. No per-story news fields or audio bytes are needed in this repo.
The small real MP3 under `tests/fixtures/audio/` is a test-only exception.

| Variable | Default |
| --- | --- |
| `GOOD_NEWS_AUDIO` | disabled; only `1` enables generation |
| `GOOD_NEWS_AUDIO_DIR` | `../good-news-audio` relative to the site repo |
| `GOOD_NEWS_PIPER` | `/workspace/tools/piper/venv/bin/piper` |
| `GOOD_NEWS_PIPER_MODEL` | `/workspace/tools/piper/models/te_IN-maya-medium.onnx` |
| `GOOD_NEWS_FFMPEG` | `ffmpeg` on PATH |
| `GOOD_NEWS_AUDIO_BUDGET_S` | `300` seconds shared across all synthesis/encoding calls |
| `GOOD_NEWS_AUDIO_BASE_URL` | `https://anilkumarnandamuri.github.io/good-news-audio/` |

The output directory must be outside the site repo. Temporary WAV/MP3 files are
removed automatically; successful MP3s and the manifest are replaced atomically.
Missing tools, exhausted budget, or a failed story never fail the news build.
Existing cached clips remain usable even without the tools. Each build publishes
only current successful entries in the manifest and removes unreferenced
`te/*.mp3` files whose mtime is older than seven days. Current clips are retained
regardless of age. This bounds the live checkout; git history still retains
previous recordings, so the operator may periodically compact that separate repo.

On an opted-in build, `data/audio-config.json` records the configured base URL.
Publish that small file with the static site. If it is absent, the reader uses the
default host. Config/manifest failures time out after four seconds each and device
speech remains available. Relative clip paths resolve against the manifest URL.

One-time setup (operator only; GN-6 does not create the repo): create the public
`good-news-audio` GitHub repository, initialize a `main` branch, and clone it next
to the site checkout. Generate audio, review it, and use `publish_audio.sh` to
commit that checkout; use `--push` only when ready. Enable GitHub Pages from
`main` at the repository root, including `manifest.json` and `te/`. Verify CORS
access to the manifest from the site, MP3 MIME type/byte ranges, and the Pages URL.
Serve the manifest with revalidation and content-hashed MP3s with long caching.
No publication or routine changes have been performed by GN-6.

Piper (`piper-tts` 1.8.0) is GPL-3.0, used only as an offline tool; generated audio
is not covered by the GPL. The `te_IN-maya-medium` voice was trained on IIT Madras
IndicTTS. Its IITM EULA grants a perpetual, worldwide, royalty-free licence and
allows free distribution of derivative works. The operator's licence copy is
`/workspace/tts-eval/indictts-license.pdf`. Keep the applicable licence notices with
the audio checkout. Public narration uses only the existing public summaries.

Run `python3 -m pytest tests/test_te_audio_browser.py -q` in a socket-enabled
environment for real MP3 playback without a Telugu device voice and the inline
unavailable state at 390/1280 pixels. Screenshots are saved under
`artifacts/GN-6/te-{mp3-playing,audio-unavailable}-{390,1280}.png`.
