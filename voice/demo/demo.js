import { storyText } from '../src/gn-voice.js';

const element = document.querySelector('gn-voice-player');
const list = document.querySelector('#story-list');
const status = document.querySelector('#feed-status');
const newsURL = new URL('../sample/news.json', import.meta.url);
const manifestURL = new URL('./audio/manifest.json', import.meta.url);

function renderStories() {
  list.replaceChildren();
  for (const [index, story] of element.player.stories.entries()) {
    const li = document.createElement('li');
    li.className = 'story';
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'story-button';
    button.dataset.index = index;
    button.setAttribute('aria-label', `వార్త ${index + 1} వినండి · Listen to story ${index + 1}: ${story.title}`);
    const number = document.createElement('span');
    number.className = 'story-number';
    number.textContent = String(index + 1).padStart(2, '0');
    number.setAttribute('aria-hidden', 'true');
    const content = document.createElement('span');
    const title = document.createElement('span');
    title.className = 'story-title';
    title.lang = story.lang || 'en';
    title.textContent = story.title;
    const meta = document.createElement('span');
    meta.className = 'story-meta';
    const seconds = element.player.manifest?.stories?.[story.id]?.te?.duration;
    meta.textContent = [story.source, 'తెలుగు + English', seconds ? `~${Math.ceil(seconds / 60 / element.player.rate)} min` : ''].filter(Boolean).join(' · ');
    content.append(title, meta);
    const icon = document.createElement('span');
    icon.className = 'story-action';
    icon.setAttribute('aria-hidden', 'true');
    icon.textContent = '▶';
    button.append(number, content, icon);
    button.addEventListener('click', () => element.player.select(index));
    const details = document.createElement('details');
    details.className = 'story-summary';
    const summary = document.createElement('summary');
    summary.textContent = 'సారాంశం చదవండి · Read summary';
    details.append(summary);
    for (const lang of ['te', 'en']) {
      const paragraph = document.createElement('p');
      paragraph.lang = lang;
      paragraph.textContent = storyText(story, lang);
      details.append(paragraph);
    }
    li.append(button, details);
    list.append(li);
  }
  highlight();
}
function highlight() {
  const player = element.player;
  for (const button of list.querySelectorAll('.story-button')) {
    const selected = Number(button.dataset.index) === player.index;
    button.setAttribute('aria-current', String(selected));
    button.querySelector('.story-action').textContent = selected && player.isPlaying ? 'Ⅱ' : '▶';
  }
}
element.addEventListener('gn-storychange', highlight);
element.addEventListener('gn-statechange', highlight);
try {
  await element.load({ newsURL, manifestURL });
  renderStories();
  status.textContent = 'Sample edition · First five stories in feed order. Audio is ready in both languages.';
  const response = await fetch(newsURL);
  const data = await response.json();
  const generated = new Date(data.generated);
  if (!Number.isNaN(generated.valueOf())) {
    document.querySelector('.edition-date').textContent = generated.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
  }
} catch (error) {
  status.textContent = 'Could not load the sample. Serve the repository root with python3 -m http.server 8000, then reload /demo/.';
  console.error(error);
}
