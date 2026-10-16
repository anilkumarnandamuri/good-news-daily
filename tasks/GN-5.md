# GN-5 — Mobile text-size + landing regressions from the 2026-10-15 merge

Status: in-review

Test command: python3 -m unittest discover -s tests -p 'test_*.py' && node --test tests/*.test.js && node --test voice/tests/*.test.js && python3 -m pytest tests/ -q

Reported by Anil on the live site (Samsung Galaxy S24, Android Chrome, ~384 CSS px):
1. Font is too big overall.
2. A− / A+ appear to change nothing.
3. A very large card dominates the first screen ("in his face").
Phone screenshot: big "Large text" pill in the header next to the streak + theme toggle; whole page in large-text mode; Today's 5 card #1 has huge headline on an opaque black box.

## Measured (Playwright, 384x832 DPR3, live vs pre-merge 9ac7e13)
| | pre-merge 9ac7e13 | live 5bdf08c |
|---|---|---|
| html font-size | 16px | 20px (`html{font-size:125%}` + `data-text=large` default) |
| body | 15px | 20px |
| card h3 / p | 15 / 13.5px | 18.75 / 17.5px |
| reader summary p (default) | 19px | 28.75px (rfs default 1.15 × 1.188rem × 20px) |
| A− range | rfs .85–1.6, default 1 | rfs 1–1.8, default 1.15 → only ONE A− tap possible, then nothing |
| header height | 73px | 142px (Large text pill wraps to a 2nd row) |
| Today's 5 card #1 | 400px, image + gradient overlay, 3-line clamp | 400px+, opaque rgba(14,12,10,.95) body box over the photo, no line clamp, 20px root |

## Root causes
- styles.css: `html{font-size:125%}` raised the whole rem scale by 25%; `html[data-text=standard]{font-size:100%}` only undoes it when the user turns Large text OFF.
- app.js: `setTextSize(GN.LS.get("largeText",true))` → Large text is ON by default and the pill sits front-and-centre in the header (easy to mis-tap, persists in localStorage `gn_largeText`).
- reader.js: A−/A+ scale only the reader (`--rfs`) and the new bounds [1,1.8] with default 1.15 mean A− works once then stops; on a phone the summary text is below the fold under a 46vh image, so A−/A+ looked like "nothing". Two separate text-size systems (header Large text vs reader A−/A+).
- styles.css end-of-file accessibility overrides: `.hero,.t5-c{min-height:400px}`, opaque `.hero .body,.t5-c .body{background:rgba(14,12,10,.95)}`, and `.card h3,.t5-c h3{display:block;overflow:visible}` (removed line clamps) → Today's 5 card #1 is a tall black slab of giant text.

## Goals / acceptance
- Default base text normal: html 16px (100%), body 16px (1rem); card/hero sizes close to pre-merge.
- ONE text-size control: A−/A+ (reader bar), persisted in localStorage (`gn_textScale`), bounds 0.85–1.6, step 0.15, default 1; it scales the whole site (root font-size) so it also affects list text. Buttons disabled at bounds; brief toast/status shows the size %. Header "Large text" pill removed. Migration: ignore/delete `gn_largeText` (it was a default, not a choice); old `gn_rfs`/`rfs` 1.15 (merge default) → 1, other values clamped to bounds.
- Landing page clean at 384px: header one row (~≤90px), Today's 5 card #1 compact (≤ 320px tall at 384 width, fully visible in the first 832px screen), photo visible with a gradient (not an opaque box) while keeping white text contrast; headline line-clamped (3 lines). Desktop 1280 not worse than pre-merge (t5 card ≤ 420px).
- Tests: Playwright assertions (384 and 1280): computed font-size of `.r-sum p` increases after A+, decreases after A−, persists after reload, clamps at bounds; html/body font-size 16px by default; header has no #textSize; first Today's 5 card height ≤ 320px at 384 and its bottom within the viewport. Screenshots in artifacts/GN-5/. Existing unittest, node (tests + voice), voice and browser tests pass (update tests that referenced #textSize/largeText).


## One fix pass — 2026-10-15, Codex
- Addressed review P2: hero/Today's 5 bodies now flow inside growing cards with the existing default minimum heights; hero headlines clamp to three lines and excerpts remain at two.
- Phone reader image height is now `min(30vh,240px)` below 760px.
- Browser coverage presets 160% scale before load for All, Science and Health, checks card/body/heading containment, and checks the first reader summary starts above 832px at default phone scale before scrolling.
- Requested unittest (43 tests), frontend Node and voice Node commands passed. Browser run: five setup errors from sandbox AF_INET socket denial; screenshots and layout acceptance pending. No commit or push; protected paths untouched.

## Checkpoint
- 2026-10-15 21:34 PDT build pass (codex gpt-6.1-sol medium, workspace-write); committed 85e43ff
- 2026-10-15 21:35 PDT Codex review: 1 must-fix item ([P2] hero clipping at 160%); running one fix pass
- 2026-10-15 21:37 PDT fix pass complete (cards grow, hero h2 clamp, phone reader image min(30vh,240px))
- 2026-10-15 21:37 PDT Codex review: 0 must-fix item(s) open (artifacts/GN-5/review.md; first review kept as review-1.md)
- 2026-10-15 21:38 PDT verified on box: unittest 43 OK, node frontend 14/14, node voice 5/5, pytest tests/ 53 passed (incl. Playwright text-size + legacy browser), voice unittest 3 OK, voice browser_smoke PASS
