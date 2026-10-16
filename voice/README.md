# మంచి వార్తలు · Good News Voice

A standalone, zero-dependency listening module for Manchi Vaarthalu / Good News Daily. Telugu and English summaries, large bilingual controls, and a continuous “Today's 5” radio queue. Runs on a static site with no server API or runtime build step.

## Try it

```sh
python3 -m http.server 8000
# Open http://localhost:8000/demo/
```

Real Telugu and English MP3s for the sample's first five stories are included in `demo/audio/`. Choose a language and press Play. Radio mode adds a short recorded introduction, advances through the five stories, and repeats. “Both” reads each story in Telugu, then English. The sample feed is preserved verbatim; “Today's 5” means its first five entries in feed order, rather than a date filter or a new ranking.

## Drop-in component

Copy `src/gn-voice.js` and `src/gn-voice.css`, serve a feed and optional audio manifest, then add:

```html
<link rel="stylesheet" href="/assets/gn-voice.css">
<script type="module" src="/assets/gn-voice.js"></script>
<gn-voice-player
  src="/news.json"
  manifest="/audio/manifest.json">
</gn-voice-player>
```

Serve over HTTP(S), not `file://`. Relative MP3 paths resolve against the manifest URL. The component uses light DOM and scoped `.gn-voice` CSS so it can inherit the site's font. Load the component CSS after broad site styles. There are no CDN scripts, remote font loads, cookies, or analytics. Browser speech services and the build-time TTS service may process summary text; this module does not send microphone audio or request microphone access.

## Playback and preferences

- MP3 is preferred for clear Telugu voices, precise pause/resume, and the best chance of background playback and lock-screen controls.
- When a recording fails or is absent, Web Speech reads the selected summary. Telugu requires an installed `te-IN`/`te` voice; the module does not use an English voice to pronounce Telugu. If unavailable, it uses a matching MP3 even when device speech is preferred, or shows a message asking for a recording, a Telugu voice, or English.
- The voice selectors update on `voiceschanged`. Language, speed, and voice URI selections are saved in localStorage; storage failures are harmless. Radio and playback state are deliberately not restored on reload, and playback always requires an initial user action.
- Speed is 0.6–1.4× with a 0.9× default. The API also supports volume. Device voice selection affects Web Speech only; rebuild recordings to change their voice.
- Stop clears the queue and cancels outstanding speech. Changing languages restarts the story; next/previous wrap around the list. Pause/resume on Web Speech repeats the current short chunk to avoid unreliable mobile pause behavior. MP3 resumes at the same timestamp.
- Sentence chunking includes `. ! ? … । ॥` and splits long text into roughly 160 UTF-16 units without breaking grapheme clusters where `Intl.Segmenter` exists. Progress is per story: MP3 time or completed speech chunks, with equal weighting for the two summaries in Both mode. Intro time is excluded.
- Only one `VoicePlayer` instance plays at a time. `pagehide` stops playback; the component releases listeners and Media Session handlers when removed.

## Programmatic API

```js
import { VoicePlayer } from './src/gn-voice.js';

const player = new VoicePlayer({ language: 'both', rate: 0.9, radio: true });
await player.load({ newsURL: '/news.json', manifestURL: '/audio/manifest.json' });
// Call play from a click handler after loading:
document.querySelector('#listen').addEventListener('click', () => player.play());
player.addEventListener('storychange', ({ detail }) => {
  console.log(detail.index, detail.story.id);
});
```

For already-fetched data:

```js
player.setStories(news, {
  manifest,
  manifestURL: new URL('/audio/manifest.json', location.href).href,
  limit: 5,
});
```

An array or `{ items: [...] }` is accepted. IDs must be present and unique among the selected stories. Required story fields: `id`, `title`, `sum_te`, `sum_en`. `summary` is used only if `lang` matches the requested language; it is never translated. Optional `image` is used for Media Session artwork. Markup is stripped from spoken text. A manifest entry with an embedded `text` that differs from the current summary is rejected to prevent playing stale news.

| Method | Behavior |
| --- | --- |
| `play()`, `pause()`, `stop()` | Start/resume, pause, cancel/reset |
| `next()`, `previous()` | Select and play adjacent story, wrapping |
| `select(index, { autoplay: true })` | Zero-based story selection |
| `setLanguage('te' / 'en' / 'both')` | Restart current story in new language |
| `setRate(0.9)`, `setVolume(1)` | Clamped to 0.6–1.4 and 0–1 |
| `setRadio(true)`, `setPreferAudio(true)` | Queue behavior and audio preference |
| `voicesFor('te')`, `setVoice('te', voiceURI)` | List/set device voices |
| `hasAudio('te')` | Check current story's usable manifest entry |
| `seek(seconds)` | Seek within the current MP3 segment |
| `destroy()` | Stop playback and remove global listeners |

`player.snapshot` includes `state`, `message`, `mode`, `index`, `story`, `count`, `language`, `rate`, `radio`, `progress` (0–1), `intro`, `currentLanguage`, `currentTime`, and `duration`. States: `idle`, `loading`, `playing`, `paused`, `ended`, `error`. Events on the controller are `statechange`, `storychange`, `progress`, `voiceschange`, and `ended`, each with a snapshot in `event.detail`. The custom element forwards these as bubbling `gn-*` events and exposes its controller through `element.player` after connection. `ended` means the queue finished, not each story in continuous radio mode.

For element configuration, set `element.config` **before connecting it**; or use `element.player` setters after connection. Element methods `setStories(data, options)` and `load(options)` mirror the controller. SetStories may be called before connection; call load after connection. The `src` and `manifest` attributes are read on connection, not observed for later changes.

| Constructor option | Default | Meaning |
| --- | --- | --- |
| `language` | saved choice or `te` | `te`, `en`, `both` |
| `rate` | saved choice or `0.9` | Playback speed |
| `volume` | `1` | Volume; some phones defer to hardware volume |
| `preferAudio` | `true` | Prefer MP3 over device voice |
| `radio` | `false` | Auto-advance |
| `loop` | `true` | Repeat after the last story in radio mode |
| `intros` | `true` | Short introduction before radio stories |
| `limit` | `5` | First N stories; `0` selects all |
| `storageKey` | `gn-voice-v1` | Namespace saved preferences |
| `audioElement` | new `Audio()` | Optional existing HTMLAudioElement |

Explicit `language` and `rate` options override saved values. The stock radio label describes the default five-story repeating mode; customize its text if embedding a different queue or disabling looping.

## Build audio

Python is only needed to generate recordings. The browser module has no dependencies.

```sh
python3 -m pip install -r tools/requirements.txt
python3 tools/build_audio.py --input sample/news.json --out demo/audio --limit 5 --radio
# Alternative voices and synthesis rate:
python3 tools/build_audio.py --input sample/news.json --out demo/audio \
  --voices te=te-IN-MohanNeural,en=en-US-AriaNeural --rate=-10%
```

Default voices are `te-IN-ShrutiNeural` and `en-IN-NeerjaNeural`. Other flags: `--all`, `--limit 0`, `--languages te en`, `--concurrency 2`, `--retries 2`, `--timeout 90`, `--force`, `--no-intros`. Use `--rate=-10%` so argparse accepts a negative rate. Synthesis rate and UI playback speed multiply; keep synthesis at `+0%` for the 0.9× elder-friendly UI default.

The builder uses edge-tts's network service, writes temporary files then renames successful outputs, retries failures with backoff, and returns nonzero if any jobs fail. It writes a manifest even on partial failure so successful recordings remain usable. MP3 filenames include a hash of text, voice, and synthesis rate; unchanged files are reused without a network request. The manifest also includes full text, SHA-256 text hash, voice, and duration when ffprobe is available. Missing language summaries are skipped. Output is intended for one builder process per directory.

`--radio` uses ffmpeg to make one combined MP3 per language, with intros. These are optional downloadable/exportable files listed under `manifest.radio`; the interactive player uses individual story clips so navigation, bilingual order, and highlights remain accurate. ffmpeg/ffprobe are optional unless requesting combined files. This repository includes both combined clips and the individual clips, keeping the sample edition small.

## Browser support and limitations

The audio path targets current Chrome/Edge, Safari, and Firefox with ES modules/custom elements and MP3 playback. Only desktop Chromium has been exercised here. Physical iOS/Android, Bluetooth controls, and actual lock-screen continuity require device testing.

Media Session metadata and play/pause/next/previous/seek handlers are registered when playback begins; unsupported actions are ignored. Position state is exposed only for MP3, where a real duration is available. Reliable seeking needs a server with byte-range support; Python’s basic demo server may restart a clip instead of seeking. The same audio element is reused between clips. Browsers decide whether to show notification/lock-screen controls, whether transitions continue in the background, and whether a new clip needs another gesture. If autoplay is denied, the player asks the reader to press Play again.

Web Speech voice availability depends on OS/browser, can arrive asynchronously, and may require a downloaded language pack or network access. Short utterances reduce Chrome's long-utterance cutoff but cannot guarantee background speech or prevent OS interruptions. Media Session handlers are best effort for device speech; there is **no silent-audio hack** claiming to enable reliable lock-screen support. On phones, prefer MP3. For uninterrupted long background listening, the combined radio MP3 can also be opened in a native audio player; it does not have per-story metadata or navigation.

A static `src` feed and recordings must be served with CORS permission if hosted on another origin; HTTPS is recommended for deployment. No playback position survives reload. This is summary narration, not a translation or fact-checking service.

## Elder-friendly design

Primary controls have at least 56px targets; play is larger. Telugu and English labels accompany icons, and color is never the only indication of state. Large type, high contrast, a restrained layout, saved voice/speed choices, and a slow default reduce setup effort. Advanced settings live in a native disclosure. Buttons, selects, and sliders retain standard keyboard behavior; playback status is a polite live region, and rapidly changing progress is not announced. The CSS supports OS dark mode, reduced motion, and forced colors. The demo highlights the selected story without moving keyboard focus or automatically scrolling the page.

## Validate

```sh
npm test
python3 -m unittest discover -s tests -p 'test_*.py'
# Optional real-browser tests (requires Python playwright and /usr/bin/google-chrome):
python3 tests/browser_smoke.py
```

The browser suite serves its own temporary local HTTP server and saves desktop/mobile/dark screenshots to ignored `test-results/`. It exercises real MP3 playback, pause/resume, bilingual order, radio transitions, metadata, persistence, 320px/390px layouts, and a deterministic speech engine for fallback/cancellation checks. See `CHECKPOINT.md` for latest results and workspace-specific Git constraints.
