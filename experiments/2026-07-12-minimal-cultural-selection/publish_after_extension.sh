#!/usr/bin/env bash
set -u

ROOT="/home/aenguslynch/projects/messiah-bench"
SITE="/home/aenguslynch/projects/aengusl.github.io"
OUT="$ROOT/outputs/2026-07-12-minimal-cultural-selection"
LOG="$ROOT/experiments/2026-07-12-minimal-cultural-selection/extension-publish.log"

echo "[$(date -u +%FT%TZ)] waiting for extension completion" >> "$LOG"
while [[ ! -f "$OUT/COMPLETE" ]]; do sleep 60; done

turn=$(jq -r '.turn' "$OUT/world_state.json")
echo "[$(date -u +%FT%TZ)] completion detected at turn=$turn" >> "$LOG"

cd "$SITE"
git pull --rebase origin main >> "$LOG" 2>&1
cd "$ROOT"
UV_CACHE_DIR=/tmp/uv-cache uv run python experiments/2026-07-12-minimal-cultural-selection/publish_website.py >> "$LOG" 2>&1
cd "$SITE"
git add cultural-selection
if ! git diff --cached --quiet; then
  git commit -m "Publish cultural selection extension at turn $turn" >> "$LOG" 2>&1
  git push origin main >> "$LOG" 2>&1
fi
echo "[$(date -u +%FT%TZ)] EXTENSION_WEBSITE_PUBLISHED turn=$turn" >> "$LOG"
