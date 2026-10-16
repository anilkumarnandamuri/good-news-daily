#!/usr/bin/env bash
# Commit the separate audio checkout. Pushing requires an explicit --push.
set -euo pipefail
push=false
if [[ ${1:-} == --push ]]; then push=true; shift; fi
if [[ $# != 0 ]]; then echo 'Usage: publish_audio.sh [--push]' >&2; exit 2; fi
site=$(cd -- "$(dirname -- "$0")/.." && pwd -P)
audio=$(cd -- "${GOOD_NEWS_AUDIO_DIR:-$site/../good-news-audio}" && pwd -P)
case "$audio/" in "$site/"*) echo 'Audio checkout must be outside the site repository' >&2; exit 1;; esac
[[ $(git -C "$audio" rev-parse --show-toplevel) == "$audio" ]] || { echo 'Expected a separate audio git checkout' >&2; exit 1; }
[[ -f "$audio/manifest.json" && -d "$audio/te" ]]
git -C "$audio" add -- manifest.json te/
if ! git -C "$audio" diff --cached --quiet -- manifest.json te/; then
  git -C "$audio" commit --only -m 'Refresh Telugu narration' -- manifest.json te/
fi
if $push; then git -C "$audio" push; fi
