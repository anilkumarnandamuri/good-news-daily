/** Good News Daily listening module. No runtime dependencies. */
export const DEFAULTS = Object.freeze({ language: 'te', rate: 0.9, volume: 1,
  preferAudio: true, radio: false, loop: true, intros: true, limit: 5,
  storageKey: 'gn-voice-v1' });
const INTRO = { te: 'మంచి వార్తలు. ఇప్పుడు వార్త వినండి.', en: 'Manchi Vaarthalu. Here is your next story.' };
const LANGUAGE = { te: 'తెలుగు', en: 'English', both: 'తెలుగు → English' };
let activePlayer = null;

export function cleanText(value) {
  return String(value ?? '').replace(/<[^>]*>/g, ' ').replace(/\s+/gu, ' ').trim();
}

export function storyText(story, lang) {
  return cleanText(story?.[`sum_${lang}`] || (String(story?.lang).split('-')[0] === lang ? story.summary : ''));
}

/** Short sentences avoid long-utterance cutoffs; long words preserve grapheme clusters. */
export function chunkText(value, maxLength = 160) {
  if (!Number.isInteger(maxLength) || maxLength < 16) throw new RangeError('maxLength must be at least 16');
  const text = cleanText(value);
  const sentences = text.match(/[^.!?।॥…]+[.!?।॥…]*|[.!?।॥…]+/gu) || [];
  const chunks = [];
  const segmenter = typeof Intl.Segmenter === 'function' ? new Intl.Segmenter(undefined, { granularity: 'grapheme' }) : null;
  for (const sentence of sentences) {
    let chunk = '';
    for (const word of sentence.trim().split(/\s+/u)) {
      if (!word) continue;
      if (chunk && chunk.length + word.length + 1 > maxLength) { chunks.push(chunk); chunk = ''; }
      if (word.length <= maxLength) { chunk += (chunk ? ' ' : '') + word; continue; }
      const units = segmenter ? Array.from(segmenter.segment(word), s => s.segment) : Array.from(word);
      for (const unit of units) {
        if (chunk && chunk.length + unit.length > maxLength) { chunks.push(chunk); chunk = ''; }
        chunk += unit;
      }
    }
    if (chunk) chunks.push(chunk);
  }
  return chunks;
}

export function selectStories(data, limit = 5) {
  if (!Number.isInteger(limit) || limit < 0) throw new RangeError('limit must be a nonnegative integer');
  const items = Array.isArray(data) ? data : data?.items;
  if (!Array.isArray(items)) throw new TypeError('Expected an array or { items: [...] }');
  const selected = limit ? items.slice(0, limit) : items.slice();
  const ids = new Set();
  for (const story of selected) {
    if (!story || !String(story.id ?? '').trim()) throw new TypeError('Every story needs an id');
    if (ids.has(String(story.id))) throw new TypeError(`Duplicate story id: ${story.id}`);
    ids.add(String(story.id));
  }
  return selected;
}

function safeURL(value, base) {
  try {
    const url = new URL(value, base);
    return ['http:', 'https:', 'blob:'].includes(url.protocol) ? url.href : '';
  } catch { return ''; }
}
function clamp(value, min, max, fallback) {
  const number = Number(value);
  return Number.isFinite(number) ? Math.min(max, Math.max(min, number)) : fallback;
}

export class VoicePlayer extends EventTarget {
  constructor(options = {}) {
    super();
    this.options = { ...DEFAULTS, ...options };
    let saved = {};
    try { saved = JSON.parse(localStorage.getItem(this.options.storageKey)) || {}; } catch { /* private browsing */ }
    this.language = options.language ?? saved.language ?? DEFAULTS.language;
    if (!(this.language in LANGUAGE)) this.language = 'te';
    this.rate = clamp(options.rate ?? saved.rate ?? DEFAULTS.rate, 0.6, 1.4, 0.9);
    this.volume = clamp(options.volume ?? DEFAULTS.volume, 0, 1, 1);
    this.voiceIds = { te: '', en: '', ...saved.voiceIds };
    this.radio = Boolean(this.options.radio);
    this.stories = [];
    this.index = 0;
    this.state = 'idle';
    this.message = 'వినడానికి సిద్ధం · Ready to listen';
    this.mode = '';
    this.progress = 0;
    this.queue = [];
    this.queueIndex = 0;
    this.chunkIndex = 0;
    this.runId = 0;
    this.loadId = 0;
    this.destroyed = false;
    this.voices = [];
    this.audio = options.audioElement || new Audio();
    this.audio.preload = 'metadata';
    this.audio.setAttribute('playsinline', '');
    this.synth = globalThis.speechSynthesis;
    this._onVoices = () => {
      this.voices = this.synth?.getVoices() || [];
      this._emit('voiceschange');
    };
    this.synth?.addEventListener('voiceschanged', this._onVoices);
    this._onVoices();
    this._onPageHide = () => this.stop();
    globalThis.addEventListener?.('pagehide', this._onPageHide);
  }

  get story() { return this.stories[this.index]; }
  get isPlaying() { return this.state === 'playing' || this.state === 'loading'; }
  get snapshot() {
    return { state: this.state, message: this.message, mode: this.mode, index: this.index,
      story: this.story, count: this.stories.length, language: this.language, rate: this.rate,
      radio: this.radio, progress: this.progress, intro: Boolean(this.queue[this.queueIndex]?.intro),
      currentLanguage: this.queue[this.queueIndex]?.lang,
      currentTime: this.mode === 'audio' ? this.audio.currentTime || 0 : 0,
      duration: this.mode === 'audio' && Number.isFinite(this.audio.duration) ? this.audio.duration : 0 };
  }
  _emit(type) { this.dispatchEvent(new CustomEvent(type, { detail: this.snapshot })); }
  _save() {
    try { localStorage.setItem(this.options.storageKey, JSON.stringify({ language: this.language, rate: this.rate, voiceIds: this.voiceIds })); } catch { /* storage is optional */ }
  }
  _state(state, message) {
    this.state = state;
    if (message) this.message = message;
    if (activePlayer === this && globalThis.navigator?.mediaSession) {
      navigator.mediaSession.playbackState = this.isPlaying ? 'playing' : state === 'paused' ? 'paused' : 'none';
    }
    this._emit('statechange');
  }

  /** Manifest file paths are relative to manifestURL, not the page. */
  setStories(data, { manifest = {}, manifestURL = globalThis.document?.baseURI, limit = this.options.limit } = {}) {
    const stories = selectStories(data, limit);
    ++this.loadId; // An explicit replacement wins over an older pending fetch.
    this.stop();
    this.stories = stories;
    this.manifest = manifest;
    this.manifestURL = manifestURL;
    this.index = 0;
    this._state('idle', stories.length ? 'వినడానికి సిద్ధం · Ready to listen' : 'వార్తలు లేవు · No stories available');
    this._emit('storychange');
    return this;
  }

  async load({ newsURL, manifestURL, limit = this.options.limit }) {
    const id = ++this.loadId;
    const getJSON = async url => {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP ${response.status}: ${url}`);
      return response.json();
    };
    const [news, audio] = await Promise.allSettled([getJSON(newsURL), manifestURL ? getJSON(manifestURL) : Promise.resolve({})]);
    if (this.destroyed || id !== this.loadId) return this;
    if (news.status === 'rejected') {
      this.stop();
      this._state('error', 'వార్తలు తెరవలేకపోయాము · Could not load stories. Please retry.');
      throw news.reason;
    }
    this.setStories(news.value, { manifest: audio.status === 'fulfilled' ? audio.value : {},
      manifestURL: manifestURL ? new URL(manifestURL, document.baseURI).href : document.baseURI, limit });
    if (audio.status === 'rejected') this._state('idle', 'రికార్డింగ్‌లు అందుబాటులో లేవు · Recordings unavailable; device voices will be used.');
    return this;
  }

  voicesFor(lang) {
    return this.voices.filter(v => lang === 'te' ? /^te(?:[-_]IN)?$/i.test(v.lang) : /^en(?:[-_]|$)/i.test(v.lang));
  }
  voiceFor(lang) {
    const voices = this.voicesFor(lang);
    return voices.find(v => v.voiceURI === this.voiceIds[lang]) || voices.find(v => v.default) || voices[0];
  }
  setVoice(lang, uri) {
    if (!['te', 'en'].includes(lang)) throw new TypeError('Voice language must be te or en');
    this.voiceIds[lang] = String(uri);
    this._save();
    if (this.isPlaying && this.mode === 'speech') { this.pause(); this.play(); }
    this._emit('voiceschange');
  }
  setLanguage(lang) {
    if (!(lang in LANGUAGE)) throw new TypeError('Language must be te, en, or both');
    const wasPlaying = this.isPlaying;
    this.stop();
    this.language = lang;
    this._save();
    this._emit('statechange');
    if (wasPlaying) this.play();
  }
  setRate(value) {
    this.rate = clamp(value, 0.6, 1.4, 0.9);
    this.audio.defaultPlaybackRate = this.rate;
    this.audio.playbackRate = this.rate;
    this._save();
    if (this.isPlaying && this.mode === 'speech') { this.pause(); this.play(); }
    this._position();
    this._emit('statechange');
  }
  setVolume(value) { this.volume = clamp(value, 0, 1, 1); this.audio.volume = this.volume; }
  setRadio(enabled) { this.radio = Boolean(enabled); this._emit('statechange'); }
  setPreferAudio(enabled) {
    const wasPlaying = this.isPlaying;
    this.stop();
    this.options.preferAudio = Boolean(enabled);
    if (wasPlaying) this.play();
  }

  _entry(lang, intro = false) {
    const entry = intro ? this.manifest?.intros?.[lang] : this.manifest?.stories?.[String(this.story?.id)]?.[lang];
    if (!entry) return null;
    const text = intro ? INTRO[lang] : storyText(this.story, lang);
    // A stale build must never read a previous version of a summary.
    if (entry.text !== undefined && cleanText(entry.text) !== text) return null;
    const url = safeURL(typeof entry === 'string' ? entry : entry.file, this.manifestURL);
    return url ? { ...entry, url } : null;
  }
  hasAudio(lang) { return Boolean(this._entry(lang)); }
  _makeQueue() {
    const languages = this.language === 'both' ? ['te', 'en'] : [this.language];
    const queue = languages.map(lang => ({ lang, text: storyText(this.story, lang), audio: this._entry(lang), intro: false }));
    if (queue.some(item => !item.text)) {
      this._state('error', 'ఈ భాషలో సారాంశం లేదు · No summary in the selected language. Choose another language.');
      return false;
    }
    if (this.radio && this.options.intros) {
      const lang = languages[0];
      queue.unshift({ lang, text: INTRO[lang], audio: this._entry(lang, true), intro: true });
    }
    this.queue = queue;
    this.queueIndex = 0;
    this.chunkIndex = 0;
    return true;
  }

  play() {
    if (this.destroyed || !this.story || this.isPlaying) return;
    if (activePlayer && activePlayer !== this) activePlayer.stop();
    activePlayer = this;
    this._mediaSession();
    if (this.state !== 'paused' && !this._makeQueue()) return;
    this._run();
  }
  pause() {
    if (!this.isPlaying) return;
    this._state('paused', 'పాజ్ చేయబడింది · Paused. Press play to continue.');
    if (this.mode === 'audio') this.audio.pause();
    else this._cancelSpeech(); // Android pause is unreliable; replay the current short chunk.
  }
  stop() {
    this._cancel();
    this.queue = [];
    this.queueIndex = 0;
    this.chunkIndex = 0;
    this.progress = 0;
    this.mode = '';
    this._state('idle', 'ఆపివేయబడింది · Stopped');
    this._position();
    this._emit('progress');
  }
  select(index, { autoplay = true } = {}) {
    if (!Number.isInteger(index) || index < 0 || index >= this.stories.length) return;
    this.stop();
    this.index = index;
    this._state('idle', 'వినడానికి సిద్ధం · Ready to listen');
    this._emit('storychange');
    if (autoplay) this.play();
  }
  next() {
    if (!this.stories.length) return;
    this.select((this.index + 1) % this.stories.length);
  }
  previous() {
    if (!this.stories.length) return;
    this.select((this.index - 1 + this.stories.length) % this.stories.length);
  }
  seek(seconds) {
    if (this.mode === 'audio' && Number.isFinite(this.audio.duration)) {
      this.audio.currentTime = clamp(seconds, 0, this.audio.duration, 0);
      this._updateProgress();
    }
  }
  _cancelSpeech() {
    ++this.runId;
    if (this.utterance) {
      this.utterance.onend = this.utterance.onerror = this.utterance.onboundary = null;
      this.utterance = null;
      this.synth?.cancel();
    }
  }
  _cancel() {
    this._cancelSpeech();
    for (const event of ['onended', 'onerror', 'onpause', 'onplaying', 'onwaiting', 'ontimeupdate', 'onloadedmetadata']) this.audio[event] = null;
    this.audio.pause();
    this.audio.removeAttribute('src');
    this.audio.load();
  }

  _run() {
    const item = this.queue[this.queueIndex];
    if (!item || this.destroyed) return;
    const useAudio = item.audio && !item.audioFailed && (this.options.preferAudio || !this.synth || (item.lang === 'te' && !this.voiceFor('te')));
    if (useAudio) this._playAudio(item);
    else this._playSpeech(item);
  }
  _playingMessage(item) {
    return item.intro ? `వార్త ${this.index + 1} / ${this.stories.length} · Story ${this.index + 1} of ${this.stories.length}` :
      `వింటున్నారు · Playing · ${LANGUAGE[item.lang]} · ${this.mode === 'audio' ? 'MP3' : 'Device voice'}`;
  }
  _playAudio(item) {
    const id = ++this.runId;
    this.mode = 'audio';
    this.audio.defaultPlaybackRate = this.rate;
    this.audio.playbackRate = this.rate;
    this.audio.volume = this.volume;
    this.audio.onended = () => { if (id === this.runId) this._advance(); };
    this.audio.onplaying = () => {
      if (id === this.runId && this.state !== 'paused') this._state('playing', this._playingMessage(item));
    };
    this.audio.onpause = () => {
      if (id === this.runId && this.isPlaying && this.audio.paused && !this.audio.ended) this._state('paused', 'పాజ్ చేయబడింది · Paused. Press play to continue.');
    };
    this.audio.onwaiting = () => { if (id === this.runId && this.isPlaying) this._state('loading', 'లోడ్ అవుతోంది · Loading audio…'); };
    this.audio.ontimeupdate = this.audio.onloadedmetadata = () => { if (id === this.runId) this._updateProgress(); };
    const failed = error => {
      if (id !== this.runId || !this.isPlaying) return;
      if (error?.name === 'NotAllowedError') {
        this._state('paused', 'వినడానికి ప్లే నొక్కండి · Tap play to allow audio.');
        return;
      }
      if (error?.name === 'AbortError') return;
      item.audioFailed = true;
      this._cancel();
      this._state('loading', 'రికార్డింగ్ తెరవలేదు · Recording unavailable; trying device voice.');
      this._playSpeech(item);
    };
    this.audio.onerror = failed;
    this._state('loading', 'లోడ్ అవుతోంది · Loading audio…');
    if (this.audio.src !== item.audio.url) this.audio.src = item.audio.url;
    // Loading a new source can reset playbackRate to defaultPlaybackRate.
    this.audio.playbackRate = this.rate;
    try { this.audio.play()?.catch(failed); } catch (error) { failed(error); }
  }
  _playSpeech(item) {
    const voice = this.voiceFor(item.lang);
    if (!this.synth || !globalThis.SpeechSynthesisUtterance || (item.lang === 'te' && !voice)) {
      if (item.intro) { this._advance(); return; }
      this.mode = '';
      this._state('error', item.lang === 'te' ?
        'తెలుగు గొంతు లేదు · No Telugu device voice. A Telugu MP3 is needed; try English or install a Telugu voice.' :
        'గొంతు అందుబాటులో లేదు · Speech is unavailable. A recording is needed on this browser.');
      return;
    }
    const id = ++this.runId;
    this.mode = 'speech';
    item.chunks ||= chunkText(item.text);
    const utterance = new SpeechSynthesisUtterance(item.chunks[this.chunkIndex]);
    this.utterance = utterance; // Keep a strong reference while the browser speaks.
    utterance.lang = item.lang === 'te' ? 'te-IN' : (voice?.lang || 'en-IN');
    if (voice) utterance.voice = voice;
    utterance.rate = this.rate;
    utterance.volume = this.volume;
    utterance.onend = () => {
      if (id !== this.runId || !this.isPlaying) return;
      this.utterance = null;
      this.chunkIndex++;
      this._updateProgress();
      if (this.chunkIndex < item.chunks.length) this._playSpeech(item);
      else this._advance();
    };
    utterance.onerror = event => {
      if (id !== this.runId) return;
      this.utterance = null;
      if (item.audio && !item.audioFailed) { this._playAudio(item); return; }
      if (item.intro) { this._advance(); return; }
      this._state('error', `గొంతు ఆగింది · Device speech stopped (${event.error || 'unavailable'}). Press play to retry, or choose a recording.`);
    };
    this._state('playing', this._playingMessage(item));
    this._position();
    try { this.synth.resume(); this.synth.speak(utterance); }
    catch { utterance.onerror({ error: 'unavailable' }); }
  }
  _advance() {
    this._cancel();
    this.chunkIndex = 0;
    this.queueIndex++;
    if (this.queueIndex < this.queue.length) { this._run(); return; }
    this.progress = 1;
    this._emit('progress');
    if (this.radio && (this.index + 1 < this.stories.length || this.options.loop)) {
      this.select((this.index + 1) % this.stories.length);
    } else {
      this.mode = '';
      this._state('ended', 'వార్త పూర్తయింది · Finished. Play again or choose the next story.');
      this._emit('ended');
    }
  }
  _updateProgress() {
    const item = this.queue[this.queueIndex];
    if (!item) return;
    const summaries = this.queue.filter(q => !q.intro);
    const completed = this.queue.slice(0, this.queueIndex).filter(q => !q.intro).length;
    const fraction = item.intro ? 0 : this.mode === 'audio' ?
      (Number.isFinite(this.audio.duration) && this.audio.duration > 0 ? this.audio.currentTime / this.audio.duration : 0) :
      this.chunkIndex / (item.chunks?.length || 1);
    this.progress = Math.min(1, (completed + fraction) / (summaries.length || 1));
    this._position();
    this._emit('progress');
  }
  _mediaSession() {
    if (!globalThis.navigator?.mediaSession) return;
    const session = navigator.mediaSession;
    if (globalThis.MediaMetadata) {
      const artwork = this.story?.image ? safeURL(this.story.image, document.baseURI) : '';
      session.metadata = new MediaMetadata({ title: this.story?.title || 'మంచి వార్తలు',
        artist: 'మంచి వార్తలు · Manchi Vaarthalu', album: "Today's 5",
        artwork: artwork ? [{ src: artwork }] : [] });
    }
    const handlers = { play: () => this.play(), pause: () => this.pause(), stop: () => this.stop(),
      nexttrack: () => this.next(), previoustrack: () => this.previous(),
      seekto: event => this.seek(event.seekTime),
      seekbackward: event => this.seek(this.audio.currentTime - (event.seekOffset || 10)),
      seekforward: event => this.seek(this.audio.currentTime + (event.seekOffset || 10)) };
    for (const [action, handler] of Object.entries(handlers)) {
      try { session.setActionHandler(action, handler); } catch { /* browser-specific actions */ }
    }
  }
  _position() {
    if (activePlayer !== this || !globalThis.navigator?.mediaSession?.setPositionState) return;
    try {
      if (this.mode === 'audio' && Number.isFinite(this.audio.duration) && this.audio.duration > 0) {
        navigator.mediaSession.setPositionState({ duration: this.audio.duration, playbackRate: this.rate,
          position: Math.min(this.audio.duration, Math.max(0, this.audio.currentTime)) });
      } else navigator.mediaSession.setPositionState();
    } catch { /* unsupported or metadata still loading */ }
  }
  destroy() {
    this.stop();
    this.destroyed = true;
    ++this.loadId;
    this.synth?.removeEventListener('voiceschanged', this._onVoices);
    globalThis.removeEventListener?.('pagehide', this._onPageHide);
    if (activePlayer === this) {
      activePlayer = null;
      if (globalThis.navigator?.mediaSession) {
        for (const action of ['play', 'pause', 'stop', 'nexttrack', 'previoustrack', 'seekto', 'seekforward', 'seekbackward']) {
          try { navigator.mediaSession.setActionHandler(action, null); } catch { /* unsupported */ }
        }
        navigator.mediaSession.metadata = null;
      }
    }
  }
}

const HTMLElementBase = globalThis.HTMLElement || class {};
export class GNVoicePlayer extends HTMLElementBase {
  connectedCallback() {
    if (this.player) return;
    this.player = new VoicePlayer(this.config || {});
    this.classList.add('gn-voice');
    this.innerHTML = `
      <section class="gn-panel" aria-label="వార్తలు వినండి · Listen to the news">
        <div class="gn-topline"><span class="gn-eyebrow">వినండి · LISTEN</span><span class="gn-format">READY WHEN YOU ARE</span></div>
        <h2 class="gn-heading"><span lang="te">కాస్త విశ్రాంతి. మంచి వార్తలు వినండి.</span><span class="gn-subheading">Rest your eyes. Listen to the news.</span></h2>
        <div class="gn-language" role="group" aria-label="భాష · Listening language">
          <button type="button" data-language="te" lang="te" aria-pressed="true">తెలుగు</button>
          <button type="button" data-language="en" aria-pressed="false">English</button>
          <button type="button" data-language="both" aria-pressed="false"><span lang="te">రెండూ</span> · Both</button>
        </div>
        <div class="gn-now"><span class="gn-story-number"></span><h3 class="gn-title">వార్తలు లోడ్ అవుతున్నాయి · Loading stories…</h3></div>
        <div class="gn-progress-row"><progress class="gn-progress" max="1" value="0" aria-label="ఈ వార్త పురోగతి · Current story progress"></progress><span class="gn-time">0%</span></div>
        <div class="gn-transport">
          <button type="button" class="gn-previous" aria-label="మునుపటి వార్త · Previous story"><span aria-hidden="true">❮</span><span lang="te">మునుపటి</span><small>Previous</small></button>
          <button type="button" class="gn-play"><span class="gn-play-icon" aria-hidden="true">▶</span><span class="gn-play-te" lang="te">వినండి</span><small class="gn-play-en">Play</small></button>
          <button type="button" class="gn-next" aria-label="తరువాతి వార్త · Next story"><span aria-hidden="true">❯</span><span lang="te">తరువాతి</span><small>Next</small></button>
          <button type="button" class="gn-stop" aria-label="ఆపండి · Stop"><span aria-hidden="true">■</span><span lang="te">ఆపండి</span><small>Stop</small></button>
        </div>
        <p class="gn-status" role="status" aria-live="polite" aria-atomic="true"></p>
        <label class="gn-radio"><input type="checkbox" class="gn-radio-input"><span><strong><span lang="te">రేడియోలా వినండి</span> · Radio mode</strong><small>Play all five in order, then repeat.</small></span><span class="gn-radio-symbol" aria-hidden="true">↻</span></label>
        <details class="gn-settings"><summary><span lang="te">వేగం & గొంతు</span> · Speed & voice <span aria-hidden="true">＋</span></summary>
          <div class="gn-settings-body">
            <label class="gn-rate-label">వేగం · Listening speed <output class="gn-rate-value">0.9×</output><input class="gn-rate" type="range" min="0.6" max="1.4" step="0.1" value="0.9" aria-label="వేగం · Listening speed"></label>
            <div class="gn-range-ends"><span>0.6× Slower</span><button class="gn-reset-rate" type="button">Reset to 0.9×</button><span>1.4× Faster</span></div>
            <label>తెలుగు గొంతు · Telugu device voice<select class="gn-voice-te"></select></label>
            <label>English device voice<select class="gn-voice-en"></select></label>
            <p class="gn-voice-note"></p>
            <label class="gn-preference"><input class="gn-prefer-audio" type="checkbox" checked><span>Use recordings when available <small>Clearer voices · better lock-screen controls</small></span></label>
            <p class="gn-help">Device voice choices affect live speech only. On phones, resuming device speech repeats the current short sentence. Recordings resume exactly where you paused.</p>
          </div>
        </details>
      </section>`;
    this.$ = selector => this.querySelector(selector);
    this.$$('.gn-language button').forEach(button => button.addEventListener('click', () => this.player.setLanguage(button.dataset.language)));
    this.$('.gn-play').addEventListener('click', () => this.player.isPlaying ? this.player.pause() : this.player.play());
    this.$('.gn-stop').addEventListener('click', () => this.player.stop());
    this.$('.gn-next').addEventListener('click', () => this.player.next());
    this.$('.gn-previous').addEventListener('click', () => this.player.previous());
    this.$('.gn-radio-input').addEventListener('change', event => this.player.setRadio(event.target.checked));
    this.$('.gn-rate').addEventListener('input', event => this.player.setRate(event.target.value));
    this.$('.gn-reset-rate').addEventListener('click', () => this.player.setRate(0.9));
    for (const lang of ['te', 'en']) this.$(`.gn-voice-${lang}`).addEventListener('change', event => this.player.setVoice(lang, event.target.value));
    this.$('.gn-prefer-audio').addEventListener('change', event => this.player.setPreferAudio(event.target.checked));
    for (const type of ['statechange', 'storychange', 'progress', 'voiceschange', 'ended']) {
      this.player.addEventListener(type, event => {
        if (type === 'voiceschange') this._renderVoices();
        this._render();
        this.dispatchEvent(new CustomEvent(`gn-${type}`, { detail: event.detail, bubbles: true }));
      });
    }
    this._renderVoices();
    this._render();
    if (this._pendingStories) this.setStories(this._pendingStories.data, this._pendingStories.options);
    else if (this.hasAttribute('src')) this.load({ newsURL: this.getAttribute('src'), manifestURL: this.getAttribute('manifest') }).catch(() => {});
  }
  $$(selector) { return Array.from(this.querySelectorAll(selector)); }
  _renderVoices() {
    for (const lang of ['te', 'en']) {
      const select = this.$(`.gn-voice-${lang}`);
      const voices = this.player.voicesFor(lang);
      select.replaceChildren();
      const automatic = document.createElement('option');
      automatic.value = '';
      automatic.textContent = voices.length ? 'Automatic · Recommended' : lang === 'te' ? 'No Telugu device voice · Use MP3' : 'System default';
      select.append(automatic);
      for (const voice of voices) {
        const option = document.createElement('option');
        option.value = voice.voiceURI;
        option.textContent = `${voice.name} (${voice.lang})`;
        select.append(option);
      }
      select.value = voices.some(v => v.voiceURI === this.player.voiceIds[lang]) ? this.player.voiceIds[lang] : '';
    }
  }
  _render() {
    const player = this.player;
    const state = player.snapshot;
    this.$$('.gn-language button').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.language === state.language)));
    this.$('.gn-title').textContent = state.story?.title || 'వార్తలు లేవు · No stories loaded';
    this.$('.gn-title').lang = state.story?.lang || 'en';
    this.$('.gn-story-number').textContent = state.count ? `వార్త ${state.index + 1} / ${state.count} · STORY ${state.index + 1} OF ${state.count}` : 'YOUR DAILY LISTEN';
    this.$('.gn-format').textContent = state.mode === 'audio' ? '● RECORDED AUDIO' : state.mode === 'speech' ? '● DEVICE VOICE' : 'AT YOUR PACE';
    this.$('.gn-play-icon').textContent = player.isPlaying ? 'Ⅱ' : '▶';
    this.$('.gn-play-te').textContent = player.isPlaying ? 'పాజ్' : state.state === 'paused' ? 'కొనసాగించండి' : 'వినండి';
    this.$('.gn-play-en').textContent = player.isPlaying ? 'Pause' : state.state === 'paused' ? 'Resume' : 'Play';
    this.$('.gn-play').setAttribute('aria-label', player.isPlaying ? 'పాజ్ · Pause' : state.state === 'paused' ? 'కొనసాగించండి · Resume' : 'వినండి · Play');
    for (const selector of ['.gn-play', '.gn-previous', '.gn-next', '.gn-stop']) this.$(selector).disabled = !state.count;
    this.$('.gn-progress').value = state.progress;
    this.$('.gn-time').textContent = `${Math.round(state.progress * 100)}%`;
    if (this.$('.gn-status').textContent !== state.message) this.$('.gn-status').textContent = state.message;
    this.$('.gn-radio-input').checked = state.radio;
    this.$('.gn-rate').value = state.rate;
    this.$('.gn-rate').setAttribute('aria-valuetext', `${state.rate.toFixed(1)} times normal speed`);
    this.$('.gn-rate-value').textContent = `${state.rate.toFixed(1)}×`;
    this.$('.gn-prefer-audio').checked = player.options.preferAudio;
    this.$('.gn-voice-note').textContent = player.voicesFor('te').length ? 'Device voices are ready. Your choices are saved on this device.' :
      player.hasAudio('te') ? 'తెలుగు MP3 సిద్ధంగా ఉంది · No Telugu device voice is installed. A Telugu recording is ready.' :
        'తెలుగు గొంతు లేదు · No Telugu device voice is installed. Add a Telugu recording, install a voice, or choose English.';
  }
  setStories(data, options = {}) {
    this._pendingStories = { data, options };
    this.player?.setStories(data, options);
    return this;
  }
  async load(options) { await this.player.load(options); return this; }
  disconnectedCallback() {
    if (this.player) {
      this._pendingStories = { data: this.player.stories, options: { manifest: this.player.manifest, manifestURL: this.player.manifestURL, limit: 0 } };
      this.player.destroy();
      this.player = null;
    }
  }
}
if (globalThis.customElements && !customElements.get('gn-voice-player')) customElements.define('gn-voice-player', GNVoicePlayer);
