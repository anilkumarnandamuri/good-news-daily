# Good News Daily 🌻

A free, static, mobile-first digest of the day's **positive** news — English/world plus a **Telugu (తెలుగు)** section and India/AP-Telangana.
Hostable on GitHub Pages; no paid APIs, no backend.

## Structure
- `index.html`, `styles.css`, `app.js` — static front end (Fraunces + Inter + Noto Sans Telugu, light/dark mode, category tabs, hero + cards, ad slot, mailto digest waitlist).
- `scripts/build.py` — fetches RSS, dedupes, scores positivity, writes `data/news.json`.
- `data/news.json` — generated data (headline, source, ≤220-char excerpt, link, time, category, image URL).
- `shots/` — local headless-Chrome screenshots (390px & 1280px, light/dark/Telugu).

## Run
    pip install -r requirements.txt
    python scripts/build.py
    python -m http.server 8000   # open http://localhost:8000  (?theme=dark, ?cat=telugu)

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
