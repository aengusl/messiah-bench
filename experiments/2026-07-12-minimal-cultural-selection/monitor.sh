#!/usr/bin/env bash
set -u

PID="$1"
OUT="$2"
LOG="$3"

while kill -0 "$PID" 2>/dev/null; do
  if [[ -f "$OUT/world_state.json" ]]; then
    turn=$(jq -r '.turn' "$OUT/world_state.json" 2>/dev/null || echo '?')
    alive=$(jq -r '[.agents[] | select(.alive)] | length' "$OUT/world_state.json" 2>/dev/null || echo '?')
    cost=$(jq -r '.usage.estimated_cost' "$OUT/world_state.json" 2>/dev/null || echo '?')
    errors=$(jq -r '.usage.errors' "$OUT/world_state.json" 2>/dev/null || echo '?')
    proposals=$(jq -r '[.proposals[] | select(.status == "open")] | length' "$OUT/world_state.json" 2>/dev/null || echo '?')
    echo "[$(date -u +%FT%TZ)] turn=$turn alive=$alive open_proposals=$proposals errors=$errors cost=$cost"
  else
    echo "[$(date -u +%FT%TZ)] waiting for first checkpoint"
  fi
  [[ -f "$OUT/COMPLETE" ]] && break
  sleep 60
done

if [[ -f "$OUT/COMPLETE" ]]; then
  echo "[$(date -u +%FT%TZ)] MONITOR_COMPLETE $(cat "$OUT/COMPLETE")"
else
  echo "[$(date -u +%FT%TZ)] MONITOR_PROCESS_EXITED_WITHOUT_COMPLETE"
  tail -30 "$LOG" 2>/dev/null || true
fi
