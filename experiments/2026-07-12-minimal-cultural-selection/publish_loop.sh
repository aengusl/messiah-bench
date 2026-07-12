#!/usr/bin/env bash
set -u
ROOT="/home/aenguslynch/projects/messiah-bench"
SITE="/home/aenguslynch/projects/aengusl.github.io"
OUT="$ROOT/outputs/2026-07-12-minimal-cultural-selection"
LAST=""
publish() {
  cd "$SITE"
  git pull --rebase origin main
  cd "$ROOT"
  UV_CACHE_DIR=/tmp/uv-cache uv run python experiments/2026-07-12-minimal-cultural-selection/publish_website.py
  cd "$SITE"
  git add cultural-selection
  if ! git diff --cached --quiet; then
    git commit -m "Update cultural selection live page at turn $1"
    git push origin main
  fi
}
while [[ ! -f "$OUT/COMPLETE" ]]; do
  turn=$(jq -r '.turn // 0' "$OUT/world_state.json" 2>/dev/null || echo 0)
  if [[ "$turn" != "$LAST" && "$turn" -ge 1 && $((turn % 10)) -eq 0 ]]; then
    publish "$turn"
    LAST="$turn"
    echo "[$(date -u +%FT%TZ)] PUBLISHED turn=$turn"
  fi
  sleep 20
done
turn=$(jq -r '.turn' "$OUT/world_state.json")
publish "$turn"
echo "[$(date -u +%FT%TZ)] PUBLISH_COMPLETE turn=$turn"
