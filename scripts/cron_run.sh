#!/bin/bash
# 本地 crontab 排程用的進入點：跑一次公告檢查 -> 更新儀表板結果 -> 視情況推送到 GitHub Pages
set -euo pipefail
cd "$(dirname "$0")/.."

docker compose run --rm notifier "$@"

docker compose run --rm --entrypoint python notifier generate_results.py

if ! git diff --quiet -- docs/results.json; then
  git add docs/results.json
  git commit -m "chore: update dashboard results $(date '+%Y-%m-%d %H:%M %Z')"
  git push
fi
