# MVP checkpoint

## Done

- Read README.md and every script. Confirmed branch `codex/goodnews-20261014` and a clean starting tree.
- Recorded the workflow below before implementation. No pushes, deployments, or notification requests are authorized.
- Found that summary generation currently calls article and translation services unconditionally. Cached summaries often have only two sentences and some have unequal English and Telugu counts.
- Chosen data shape: an ordered list of `{en, te}` sentence pairs. Keep the existing `sum_en` and `sum_te` string fields for consumers. Never invent facts to reach four sentences. Thin sources must be explicitly identified.
- Added six passing compatibility tests for fixture-only RSS builds, push payloads, dry-run modes, missing-key aborts, and digest output paths and escaping. No notification request was made.
- Local Python lacks RSS dependencies and browser automation packages. Build tests inject feedparser and sentiment fixtures and execute the actual build function. The summary test path forbids urllib network calls.
- Skill workflow adaptation: external architecture lanes cannot run under the restricted network profile. One native read-only architecture reviewer is available. The parent owns all edits on the requested branch.
- Local commit attempt failed because `.git/index.lock` cannot be created on the read-only filesystem. Changes remain uncommitted. Do not retry or work around the restriction.
- Implemented version 6 ordered bilingual pairs, 4–6 pair validation, deterministic offline cache reuse, changed-source invalidation, and the opt-in executable LLM hook. Hook failure keeps an explicitly labeled excerpt. Eighteen Python tests pass.
- The independent design review supported paired objects over a separate translation catalog. Structural validation cannot prove translation meaning. The current feed descriptions cannot supply arbitrary new offline translations; retain truthful excerpt fallback instead of inventing facts or adding filler.
- Ran `python3 scripts/summarize.py` offline on the checked-in data and compacted public JSON. No RSS fetch, article fetch, translation service, or OneSignal call was made.
- The checked-in snapshot now has 11 complete bilingual summaries and 101 explicitly labeled publisher excerpts. New complete bilingual summaries require a configured model hook or pretranslated cache. This is a deliberate content limit, not a claim that every story has a 4–6 sentence summary.
- Added lazy dimensioned images, one eager lead image, deferred local scripts before the OneSignal SDK, normal HTTP caching, and breakpoint-only resize rerenders. Kept `push.js`, `OneSignalSDKWorker.js`, `build.py`, `send_push.py`, and `digest.py` byte-identical to the baseline.
- Added large text by default, relative font sizing, a local licensed Telugu font, 44-pixel minimum controls, focus states, a skip link, category focus retention, reader focus containment and restoration, and background inertness. Palette tests require 4.5:1 for the tested text combinations in both themes.
- Current verification passes 24 Python tests and 8 Node tests. Node's default test isolation fails in this sandbox; `--experimental-test-isolation=none` works and is documented.
- Browser verification is NOT VERIFIED. Firefox's snap launcher cannot write its required state paths, and the preview HTTP server cannot bind a socket under this sandbox. Do not work around either restriction. Node tests use a DOM test double and cannot verify layout, zoom, or assistive technology behavior.
- README.md documents the hook protocol, offline limits, test commands, fonts, caching behavior, and manual browser checks.

## Next

1. Read poteto-mode Principles. Complete.
2. Frame. Complete. Offline tests pass, published complete summaries contain 4–6 ordered sentence pairs, hooks require opt-in, and routine script contracts remain compatible.
3. Design the workflow. Complete. Compatibility tests preceded summary and front-end changes. The independent design reviewer agreed with paired objects and truthful excerpt fallback.
4. Run the loop. Complete through front-end changes. All checks pass. Commit attempts stopped after the first read-only `.git` failure.
5. Keep the audit trail. In progress. `decisions.tsv` records meaningful choices; independent final review follows.
6. Verify and hand back. In progress. Final review and a final full test run remain. Rendered browser checks must run later in a session that can start a browser and bind localhost.

## How to resume

```sh
cd /home/grokbot/src/good-news-daily
git status --short --branch
python3 -m unittest discover -s tests -v
node --test --experimental-test-isolation=none tests/*.test.js
git diff --check
python3 -m http.server 8000 --bind 127.0.0.1
```

Preview `http://127.0.0.1:8000/`, `/?theme=dark`, and `/?cat=telugu`.
Do not run the live RSS build or send_push.py without `--dry-run` during verification.
Preview cannot start in the current restricted sandbox. In a normal local session, verify all categories, Saved, reader Back/Next, Escape/Tab/Shift+Tab, dark mode, large text, 200% zoom, and Telugu at 320px, 390px and 1280px widths. Notification tests must continue using an in-memory SDK.
