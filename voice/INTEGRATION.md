# Integrate into Good News Daily

This is a copy-in module, not a site rewrite. These instructions describe future integration; no files in the real Good News Daily repository were accessed or changed.

## 1. Copy the module and builder

From this repository, copy:

| Source | Example destination in the site |
| --- | --- |
| `src/gn-voice.js` | `assets/gn-voice.js` |
| `src/gn-voice.css` | `assets/gn-voice.css` |
| `tools/build_audio.py` | `tools/build_audio.py` |
| `tools/requirements.txt` | `tools/voice-requirements.txt` |

The demo is optional and is not required by the component. Do not copy its sample edition into the live news feed. For an initial preview, copy `demo/audio/` along with the exact matching `sample/news.json`; rebuilding against the live feed is required for production.

## 2. Use the existing feed mapping

The inspected sample has an object with `generated`, `count`, `feeds`, and `items`. The module uses `items` and preserves its order. By default, the first five entries are Today's 5. Keep your editorial selection/ranking upstream, or pass a preselected array. The builder and player must receive the same selection and summaries.

| Feed field | Use |
| --- | --- |
| `id` | Stable unique story key in the manifest |
| `title` | Now-playing heading and Media Session title |
| `sum_te` | Telugu narration |
| `sum_en` | English narration |
| `summary` + `lang` | Fallback summary only when `lang` matches `te`/`en` |
| `image` | Optional lock-screen artwork URL |
| `source` | Optional demo source label |
| `published` | Available to the host; not used to select Today's 5 |

No translation is performed. A missing translation produces an actionable message when that language is requested. For language tags like `en-IN`, the `summary` fallback matches the primary `en` language. Titles can contain mixed Telugu and English, as in the sample. Feed HTML is stripped from spoken text and display strings are set with `textContent`.

## 3. Generate recordings before publishing

```sh
python3 -m pip install -r tools/voice-requirements.txt
python3 tools/build_audio.py \
  --input path/to/generated/news.json \
  --out path/to/published/audio \
  --limit 5
```

Use the real generated feed path and your site's published output directory. Publish the MP3s **and** `manifest.json`; all manifest `file` values are relative to that manifest's URL. Defaults are Telugu Shruti and Indian English Neerja. To use Mohan: `--voices te=te-IN-MohanNeural`. `--radio` additionally writes exportable full-edition clips; the component itself uses individual story clips and intros.

Example manifest entry (actual filenames are content hashed):

```json
{
  "version": 1,
  "order": ["story-123"],
  "stories": {
    "story-123": {
      "te": {
        "file": "story-123-hash-te-contenthash.mp3",
        "duration": 24.3,
        "text": "మంచి వార్తలు.",
        "text_hash": "sha256-of-clean-text",
        "cache_key": "sha256-of-text-voice-rate-version",
        "voice": "te-IN-ShrutiNeural",
        "rate": "+0%"
      }
    }
  },
  "intros": {},
  "errors": []
}
```

The component also accepts `{ te: { file: "..." } }` entries without the metadata, and `te: "clip.mp3"` strings, under `stories[id]`. Prefer builder manifests, which include `text`; the player compares it to the current summary and rejects outdated clips. `order` is informational: the actual feed array determines interactive playback order. Do not use a previously generated MP3 with updated news text.

## 4. Add the player to the page

```html
<link rel="stylesheet" href="/assets/gn-voice.css">
<script type="module" src="/assets/gn-voice.js"></script>
<gn-voice-player src="/news.json" manifest="/audio/manifest.json"></gn-voice-player>
```

Adjust URLs for a subdirectory deployment (for example GitHub Pages project sites). Use paths relative to the page or your site's base URL; leading `/` means the domain root. The player performs no autoplay on page load. Place it near Today's 5 rather than hiding it behind a small audio icon. It expands naturally; avoid fixed-height or clipped containers. Load its CSS after broad site styles, and retain visible focus outlines.

If the host already fetches the news, avoid another request:

```js
import '/assets/gn-voice.js';
const element = document.querySelector('gn-voice-player');
const manifestURL = new URL('audio/manifest.json', document.baseURI);
let manifest = {};
try {
  const response = await fetch(manifestURL);
  if (response.ok) manifest = await response.json();
} catch { /* Device speech remains available. */ }
element.setStories(news, { manifest, manifestURL: manifestURL.href, limit: 5 });
```

For constructor settings, create the element programmatically, set `.config` before adding it to the document, then call `.setStories()` or `.load()`:

```js
const element = document.createElement('gn-voice-player');
element.config = { rate: 0.9, radio: false, preferAudio: true, storageKey: 'manchi-voice-v1' };
document.querySelector('#listen-slot').append(element);
await element.load({ newsURL: '/news.json', manifestURL: '/audio/manifest.json' });
```

For a single-story page, pass `[story]` with `limit: 1`, leave radio mode off, and customize the radio label if retaining the stock UI.

## 5. Connect existing story cards

```js
element.addEventListener('gn-storychange', ({ detail }) => {
  document.querySelectorAll('[data-story-id]').forEach(card => {
    const current = card.dataset.storyId === String(detail.story?.id);
    card.classList.toggle('is-listening', current);
    if (current) card.setAttribute('aria-current', 'true');
    else card.removeAttribute('aria-current');
  });
});

// Inside an existing card's click handler:
const index = element.player.stories.findIndex(s => String(s.id) === String(storyId));
if (index >= 0) element.player.select(index);
```

Use a visible border or “Listening” label as well as color. Keep the focused control where the reader left it; do not automatically scroll the entire page at each story transition. See `demo/demo.js` for a complete example.

## 6. Add a build-time GitHub Actions step

Insert these steps after producing `news.json` and before deploying static files. Example paths assume `public/news.json` and deployment of `public/`; change them to match the real workflow. These steps do not commit or push generated files.

```yaml
# Existing checkout and news/site-generation steps above this point.
- uses: actions/setup-python@v5
  with:
    python-version: '3.12'

- name: Install listening audio builder
  run: python -m pip install -r tools/voice-requirements.txt

- name: Restore generated voice clips
  uses: actions/cache@v4
  with:
    path: .voice-audio-cache
    key: voice-v1-${{ runner.os }}-${{ github.run_id }}
    restore-keys: |
      voice-v1-${{ runner.os }}-

- name: Build Today's 5 recordings
  run: |
    python tools/build_audio.py --input public/news.json --out .voice-audio-cache --limit 5 --concurrency 2
    mkdir -p public/audio
    python - <<'PY'
    import json
    from pathlib import Path
    import shutil
    cache = Path('.voice-audio-cache')
    out = Path('public/audio')
    manifest = json.loads((cache / 'manifest.json').read_text())
    entries = list(manifest.get('intros', {}).values())
    for languages in manifest['stories'].values():
        entries.extend(languages.values())
    entries.extend(manifest.get('radio', {}).values())
    for entry in entries:
        shutil.copy2(cache / entry['file'], out / entry['file'])
    shutil.copy2(cache / 'manifest.json', out / 'manifest.json')
    PY

# Existing static-site deployment step follows.
```

The workflow fails on generation errors by default so a partial recording set is visible to maintainers. If uninterrupted publication of text is more important, deliberately handle a nonzero builder exit and still copy its partial manifest; the player falls back to device speech. Without a Telugu device voice, a failed Telugu clip remains unavailable and the reader receives the explicit message. Do not silently claim that audio generation succeeded.

ffprobe adds durations if present. For combined `--radio` output, install ffmpeg on the runner before building (`sudo apt-get update && sudo apt-get install -y ffmpeg` on an Ubuntu runner). The normal individual-clip path does not need ffmpeg.

## Caching and deployment

The cache directory accumulates reusable clips with hashes covering summary text, voice, and synthesis rate. The manifest is rewritten every build. A unique Actions key plus a restore prefix recovers prior clips and saves additions; filenames handle content invalidation. The copied published subset contains only the current manifest's files, keeping releases small. Periodically rotate the cache key prefix to bound stored history.

Publish feed, manifest, and clips as one site release. Serve `manifest.json` and the feed with revalidation/short cache lifetimes, and content-hashed MP3s with a long immutable cache lifetime. A stale manifest with different `text` is rejected; device speech may then be used. Deploying only the manifest before the MP3s would cause avoidable 404s. All narration is public summary text, so never place private data in a feed or audio output directory.

Use correct MIME types (`text/javascript`, `text/css`, `application/json`, `audio/mpeg`) and normal byte-range support for audio seeking. If using a CSP, allow the module/style origin, `connect-src` for feeds/manifests, `media-src` for MP3s, and artwork origins in `img-src`. This implementation uses a static `innerHTML` UI template; a site enforcing Trusted Types must provide a compatible policy or adapt that template to DOM construction.

## Before launch

Run the included tests and open the actual deployment on an Android phone and iPhone. Check initial Play, pause/resume, Telugu/English/Both, speed persistence, radio story transitions, lock-screen/headphone controls, and returning from a call. Test without a Telugu device voice and with an unavailable MP3. Desktop headless Chrome can verify layout and player logic; it cannot establish mobile background or OS lock-screen reliability. The README describes those limits and the optional full-edition MP3 route.
