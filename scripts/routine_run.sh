#!/usr/bin/env bash
# Operator entry point: run from a main checkout with publishing credentials set.
# Child output is intentionally suppressed: git hooks/API errors may contain secrets.
set +x
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
steps=(pull build publish_audio commit push send_push)

stop() {
  local index=$1 reason=$2 next
  printf '%s: fail (%s)\n' "${steps[index]}" "$reason"
  for ((next=index+1; next<${#steps[@]}; next++)); do
    printf '%s: skip (earlier step failed)\n' "${steps[next]}"
  done
  exit 1
}

# Never publish a feature branch as main, even when invoked from another cwd.
branch=$(git symbolic-ref --quiet --short HEAD 2>/dev/null) || stop 0 'main checkout required'
[[ $branch == main ]] || stop 0 'main checkout required'

git pull --ff-only origin main >/dev/null 2>&1 || stop 0 'git pull failed'
printf 'pull: ok\n'
GOOD_NEWS_AUDIO=1 python3 scripts/build.py >/dev/null 2>&1 || stop 1 'build failed'
printf 'build: ok\n'
if GOOD_NEWS_AUDIO_DIR=/workspace/good-news-audio bash scripts/publish_audio.sh --push >/dev/null 2>&1; then
  printf 'publish_audio: ok\n'
else
  printf 'publish_audio: fail (continuing with site publication)\n'
fi

paths=(data/news.json)
config_status=$(git status --porcelain --untracked-files=normal -- data/audio-config.json 2>/dev/null) || stop 3 'config status failed'
if [[ -n $config_status ]]; then paths+=(data/audio-config.json); fi
git add -- "${paths[@]}" >/dev/null 2>&1 || stop 3 'staging failed'
if git diff --cached --quiet -- "${paths[@]}" >/dev/null 2>&1; then
  printf 'commit: ok (no changes)\n'
else
  result=$?
  [[ $result == 1 ]] || stop 3 'change check failed'
  # --only excludes unrelated staged files, including the local summary cache.
  git commit --only -m 'Refresh daily good news' -- "${paths[@]}" >/dev/null 2>&1 || stop 3 'commit failed'
  printf 'commit: ok\n'
fi
git push origin main >/dev/null 2>&1 || stop 4 'site push failed'
printf 'push: ok\n'
python3 scripts/send_push.py >/dev/null 2>&1 || stop 5 'notification failed'
printf 'send_push: ok\n'
